"""Independently replay three relocated MP2K tracks against the frozen original."""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import struct


ORIGINAL = '9EC8B6CD932407537FC364529891AE0FE310EA1FF5E4A5132FDFDBDF8158E49C'
ORIGINAL_MANIFEST = '3F59CECB61F4A1C43DEA8B9A861F790470B5E8BAB913E205AF4DBECF441DB90A'
FRAGMENTED = 'D8F83AA300234C64A6B3963AF2ED4BA0CE32BB52D88CC2F62EC2AABF53FE6CA7'
FRAGMENT_MANIFEST = 'C1F83D6EE13179A856539FEBF2FAB15A9B252EE9FCE106AD8947819FDD32EBD1'
NATIVE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
BLOB = 'mode23-audio-assets.bin'
NATIVE_SPANS = {
    (0x37BA04, 0x37BA1A): '7102BF1C69AD5002C7470D9795C61C70D10BC49A148EAAA4A8784E45C1E75E6D',
    (0x37BA2C, 0x37BA4C): 'B4C137A9F8B801E7515565FBC485668D66B21EF58290B1D063FC3714543789DF',
    (0x37BC9C, 0x37BD00): '8883311BADAB53CC738249149273853D699DD47BF22F32C0ED8B5BAC97B1298D',
}
CONTROLS = {0xBB: 0, 0xBC: 1, 0xBD: 2, 0xBE: 3, 0xBF: 4, 0xC0: 5, 0xC1: 6}


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read_bundle(path, pin, index_pin):
    blob, index = (path / BLOB).read_bytes(), (path / 'manifest.json').read_bytes()
    need((sha(blob), sha(index)) == (pin, index_pin), 'exact frozen bundle and index')
    return blob, json.loads(index)


def address_u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def shape(manifest):
    return [{'label': 'song-table', 'offset': 0, 'size': manifest['table_entries'] * 8},
            *manifest['asset_objects']]


class Scatter:
    """Create a sparse cartridge view whose chunk order can differ from logical order."""
    def __init__(self, data, manifest, region, reverse=False):
        self.chunks = {}
        self.locals = {}
        entries = list(shape(manifest))
        if reverse:
            entries.reverse()
        for entry in entries:
            start, size = entry['offset'], entry['size']
            self.locals[start] = (region, size)
            self.chunks[region] = bytearray(data[start:start + size])
            region += ((size + 3) & ~3) + 0x34
        self.memory_starts = sorted(self.chunks)
        self.offset_starts = sorted(self.locals)
        for item in manifest['local_u32_fixups']:
            field, target = self.address(item['offset']), self.address(item['relative_target'])
            payload, index = self._find(field)
            need(payload[index:index + 4] == bytes(4), 'blank relocatable u32 field')
            struct.pack_into('<I', payload, index, target)

    def _find(self, address):
        i = bisect_right(self.memory_starts, address)
        need(i and 0x08000000 <= address < 0x09000000, 'mapped cartridge address')
        start = self.memory_starts[i - 1]
        return self.chunks[start], address - start

    def address(self, offset):
        i = bisect_right(self.offset_starts, offset)
        need(i, 'nonnegative local offset')
        start = self.offset_starts[i - 1]
        address, size = self.locals[start]
        need(offset - start < size, 'u32 field/target inside owned object')
        return address + offset - start

    def bytes(self, address, length):
        payload, index = self._find(address)
        value = payload[index:index + length]
        need(len(value) == length, f'command inside owned object at {address:08X}')
        return bytes(value)

    def track(self, song, track):
        header = address_u32(self.bytes(self.address(8 * song), 4), 0)
        return address_u32(self.bytes(header + 8 + track * 4, 4), 0)


def structural_delta(old, old_meta, new, new_meta):
    before = {row['label']: row for row in shape(old_meta)}
    after = {row['label']: row for row in shape(new_meta)}
    need(len(before) == len(old_meta['asset_objects']) + 1 and len(after) == len(new_meta['asset_objects']) + 1,
         'all object names unique')
    new_to_old = []
    new_jumps = {}
    affected = {}
    expected_names = set(before)
    tracks_old = old_meta['song_map'][-1]['tracks']
    tracks_new = new_meta['song_map'][-1]['tracks']
    need(old_meta['song_map'][-1]['native_id'] == new_meta['song_map'][-1]['native_id'] == 0x79,
         'frozen song 79 ownership')
    for index in range(3):
        name = f'song-79-track-{index}'
        row, prev = tracks_new[index], tracks_old[index]
        pieces = row['fragments']
        need(row['offset'] == pieces[0]['offset'] and row['bytes'] == pieces[0]['size'], 'track header selects first fragment')
        need(prev['offset'] == before[name]['offset'] and
             (row['logical_bytes'], row['logical_sha256']) == (prev['bytes'], prev['sha256']), 'track logical identity')
        expected = bytearray()
        for i, part in enumerate(pieces):
            label, off, size = (part[k] for k in ('label', 'offset', 'size'))
            need(after[label] == dict(label=label, offset=off, size=size), 'fragment object agreement')
            need(size <= 12000 and sha(new[off:off + size]) == part['sha256'], 'frozen fragment hash and maximum extent')
            start, stop = part['original_start'], part['original_end']
            need(start == len(expected) and stop > start, 'exact source-range sequence')
            expected.extend(new[off:off + stop - start])
            new_to_old.append((off, off + stop - start, prev['offset'] + start))
            if i < len(pieces) - 1:
                branch = off + stop - start
                need(size == stop - start + 5 and new[branch:branch + 5] == b'\xB2\0\0\0\0',
                     'only a zero-target GOTO appended')
                new_jumps[branch + 1] = pieces[i + 1]['offset']
            else:
                need(size == stop - start, 'last fragment ends in original loop')
            expected_names.add(label)
        need(expected == old[prev['offset']:prev['offset'] + prev['bytes']], 'invert completely to original contiguous track')
        affected[name] = pieces
    need(set(after) == expected_names, 'exact named object delta')
    for name, row in before.items():
        if name in affected:
            continue
        new_row = after[name]
        start, off, n = row['offset'], new_row['offset'], row['size']
        need(n == new_row['size'] and old[start:start + n] == new[off:off + n], f'untouched {name}')
        new_to_old.append((off, off + n, start))
    need(new[:112 * 8] == old[:112 * 8], 'all existing 112 song rows retain exact bytes')

    def old_address(new_offset):
        hits = [source + new_offset - off for off, end, source in new_to_old if off <= new_offset < end]
        need(len(hits) == 1, 'one originating address for a retained pointer')
        return hits[0]

    original_fixups = {row['offset']: row['relative_target'] for row in old_meta['local_u32_fixups']}
    latest_fixups = {row['offset']: row['relative_target'] for row in new_meta['local_u32_fixups']}
    need(len(latest_fixups) == len(new_meta['local_u32_fixups']) and len(new_jumps) == 7
         and len(latest_fixups) == len(original_fixups) + len(new_jumps), '50 original and seven fragment pointer fields')
    got = {}
    for field, target in latest_fixups.items():
        if field in new_jumps:
            need(target == new_jumps[field], 'exact next-fragment relative target')
        else:
            got[old_address(field)] = old_address(target)
    need(got == original_fixups, 'complete translated relative target inverse')
    return affected, new_jumps


def play(memory, start, waits, branches):
    pc, tick, running, note = start, 0, 0, -1
    state = [-1] * len(CONTROLS)
    ledger, loop_times, extra = [], [], []
    for _ in range(240000):
        cursor = pc
        opcode = memory.bytes(pc, 1)[0]
        pc += 1
        if opcode in CONTROLS:
            operand = memory.bytes(pc, 1)
            need(operand[0] < 128, 'explicit control operand')
            pc += 1
            state[CONTROLS[opcode]] = operand[0]
        elif opcode == 0xCF:
            operand = memory.bytes(pc, 2)
            need(note == -1 and operand[0] < 128 and operand[1] == 127 and min(state) >= 0,
                 'explicit voice, level and bend state before starting native note')
            note = operand[0]
            pc += 2
        elif opcode == 0xCE:
            operand = memory.bytes(pc, 1)
            need(note == operand[0], 'explicit exact end key')
            note = -1
            pc += 1
        elif 0x81 <= opcode <= 0xB0:
            operand = b''
        elif opcode == 0xB2:
            need(note == -1, 'all original and inserted jumps at quiet boundary')
            target = address_u32(memory.bytes(pc, 4), 0)
            if cursor in branches:
                need(target == branches[cursor], 'exact physically scattered forward logical edge')
                extra.append((cursor, target, tick, running))
                pc = target
                continue
            loop_times.append(tick)
            operand = b''
            pc = target
        else:
            raise ValueError(f'unreviewed native command {opcode:02X}')
        if opcode >= 0xBD:
            running = opcode
        ledger.append((tick, opcode, operand, running, note, tuple(state)))
        if 0x81 <= opcode <= 0xB0:
            tick += waits[opcode - 0x80]
        if len(loop_times) == 3:
            return ledger, loop_times, extra
    raise ValueError('track exceeded checked playback bound')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('original', 'fragmented', 'native', 'report'):
        parser.add_argument('--' + field, type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh QA report')
    native = args.native.read_bytes()
    need(sha(native) == NATIVE and address_u32(native, 0x37DBD4) == 0x0837BA2D, 'actual 16 MiB native GOTO slot')
    for (start, stop), pin in NATIVE_SPANS.items():
        need(sha(native[start:stop]) == pin, 'exact MP2K GOTO handler and run status owner')
    waits = native[0x37DE44:0x37DE44 + 49]
    need(waits[0] == 0 and waits[-1] == 96 and all(x < y for x, y in zip(waits, waits[1:])), 'physical native wait table')
    old, old_meta = read_bundle(args.original, ORIGINAL, ORIGINAL_MANIFEST)
    new, new_meta = read_bundle(args.fragmented, FRAGMENTED, FRAGMENT_MANIFEST)
    affected, links = structural_delta(old, old_meta, new, new_meta)
    original = Scatter(old, old_meta, 0x08C00000)
    old_at = [play(original, original.track(0x79, i), waits, {}) for i in range(3)]
    summary = []
    for reverse in (False, True):
        placed = Scatter(new, new_meta, 0x08E00000, reverse)
        branches = {placed.address(field - 1): placed.address(target) for field, target in links.items()}
        need(all((a > b) == reverse for a, b in branches.items()), 'both physically forward and backward fixture layouts')
        for i, pieces in enumerate(affected.values()):
            original_trace, original_loops, _ = old_at[i]
            check_trace, check_loops, crossed = play(placed, placed.track(0x79, i), waits, branches)
            need(check_trace == original_trace and check_loops == original_loops == [28313, 51865, 75417],
                 'complete note/control/wait/running-status identity across initial pass and two repeats')
            need(len(crossed) == 3 * (len(pieces) - 1), 'every inserted edge physically reached in each iteration')
            summary.append(dict(track=i, physically_reversed=reverse, fragments=len(pieces),
                                compared_commands=len(original_trace), loop_end_ticks=check_loops,
                                physical_gotos=len(crossed)))
    result = dict(status='MODE23_FRAGMENTED_MP2K_TRACKS_INDEPENDENT_PASS',
                  original_bundle=ORIGINAL, fragmented_bundle=FRAGMENTED, manifest=FRAGMENT_MANIFEST,
                  verifier_sha256=sha(Path(__file__).read_bytes()), native_sha256=NATIVE,
                  original_song_table_rows_unchanged=112, inserted_gotos=len(links),
                  observed_goto_handler='0837BA2D Thumb, pointer-only track store at +40',
                  retained_running_status='0837BCAC only updates +7 for opcode >= BD',
                  resimulated=summary, native_game_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()

