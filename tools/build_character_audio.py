"""Install five finite native scores needed by complete character animations.

Like the existing CE/D2 layers, this preserves the discrete score but does not
claim WonderSwan timbre, hardware sweep, or noise-frequency parity.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

INPUT = "973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
START, END = 0x683200, 0x683A00
OLD_TABLE = 0x5BA400
SITES = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
SCORES = (
    (0xBC, 0x3F872C, "00000f00a201c100a1073014ffff"),
    (0xC6, 0x3F8816, "00000f001f08a204a00f7904770475047304a0097904770475047304a00679047704ffffffff"),
    (0xC8, 0x3F8848, "00000f01a202c100a10950053028ffff"),
    (0xCB, 0x3F88BE, "00000f01a201c100a107200aa109390affff"),
    (0xCC, 0x3F88D0, "00000f01a201c100a107600aa10aa006400aa004400aa002400aa001400affff"),
)
VOICES = (0x37EA54, 0x37E9D0, 0x37EB08)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


def need(ok, label):
    if not ok:
        raise ValueError(label)


def compile_score(payload, shift):
    need(payload[:3] == bytes((0, 0, 15)), "bounded initial source volume")
    wave, volume, sweep, ticks, cursor = 0, 15, 0, 0, 4
    stream = bytearray((0xBC, shift, 0xBB, 75, 0xBF, 127))
    schedule = []
    while True:
        op, arg = payload[cursor:cursor + 2]
        cursor += 2
        if (op, arg) == (255, 255):
            need(all(x == 255 for x in payload[cursor:]), "only terminal FF padding")
            break
        if op == 0xA0:
            need(arg <= 15, "right-only source volume")
            volume = arg
        elif op == 0xA1:
            sweep = arg
        elif op == 0xA2:
            need(arg in (1, 2, 4), "bounded waveform set")
            wave = arg
        elif op == 0xC1:
            need(arg == 0, "zero-period envelope only")
        elif op < 0xA0:
            need(arg in range(1, 25) or arg == 40, "bounded note/rest duration")
            note = None if op & 15 >= 12 else 36 + 12 * (op >> 4) + (op & 15)
            if note is not None:
                encoded = note - shift
                need(0 <= encoded < 128 and wave in (1, 2, 4), "native note and voice")
                voice = {1: 0, 2: 1, 4: 2}[wave]
                stream.extend((0xBD, voice, 0xBE, (volume * 127 + 7) // 15,
                               0xEC if arg == 40 else 0xCF + arg, encoded, 127))
            stream.extend([0x81] * arg)
            schedule.append(dict(time=ticks, duration=arg, source_note=op,
                                 score_key=note, waveform=wave, volume=volume,
                                 source_sweep=sweep))
            ticks += arg
        else:
            raise ValueError(f"unproved score opcode {op:02X}")
    stream.append(0xB1)
    return bytes(stream), schedule, ticks


def incoming(data):
    refs = []
    for at in range(len(data) - 3):
        word = struct.unpack_from('<I', data, at)[0]
        if BASE + START <= word < BASE + END:
            refs.append((at, word, 'unaligned pointer'))
    for at in range(0, len(data) - 3, 4):
        word = struct.unpack_from('<I', data, at)[0]
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            d = word & 0xFFFFFF
            if d & 0x800000:
                d -= 0x1000000
            target = at + 8 + d * 4
            if START <= target < END:
                refs.append((at, target, 'ARM-like branch'))
    return refs


def build(before, gba, wsc):
    need((sha(before), sha(gba), sha(wsc)) == (INPUT, GBA, WSC), "input identities")
    need(before[START:END] == bytes([255]) * (END - START), "blank reserved footprint")
    need(not incoming(before), "reserved footprint has incoming encoding")
    old_pointer = struct.pack('<I', BASE + OLD_TABLE)
    occurrences = tuple(n for n in range(len(before) - 3) if before[n:n+4] == old_pointer)
    need(occurrences == SITES, "all actual song-table references")
    # The 100-entry table must be relocated: old slot60 overlaps the CE song.
    table = bytearray(before[OLD_TABLE:OLD_TABLE + 0x5F * 8] + bytes(5 * 8))
    voice_at = START + len(table)
    voices = bytearray()
    for at in VOICES:
        voices.extend(gba[at:at+8] + bytes((0, 0, 15, 0)))
    cursor = (voice_at + len(voices) + 3) & ~3
    placements = [(voice_at, bytes(voices), 'voices')]
    details = []
    for index, (source_id, raw, expected) in enumerate(SCORES):
        payload = bytes.fromhex(expected)
        need(wsc[raw:raw+len(payload)] == payload, "source score identity")
        source_offset = struct.unpack_from('<H', wsc, 0x3F0000 + source_id * 6 + 4)[0]
        need(0x3F0000 + source_offset == raw, "actual source sound-table consumer")
        shift = 12 if source_id == 0xC6 else 0
        track, schedule, ticks = compile_score(payload, shift)
        song = bytes((1, 0, 40, 128)) + struct.pack('<II', BASE + voice_at, BASE + cursor + 12) + track
        sid = 0x5F + index
        struct.pack_into('<IHH', table, sid * 8, BASE + cursor, 4, 4)
        placements.append((cursor, song, f'song_{sid:02X}'))
        details.append(dict(source_id=source_id, native_id=sid, source_raw=raw,
                            target=cursor, bytes=len(song), sha256=sha(song),
                            key_shift=shift, ticks=ticks, schedule=schedule))
        cursor = (cursor + len(song) + 3) & ~3
    need(cursor <= END, "score allocation extent")
    placements.append((START, bytes(table), 'song_table_00_63'))
    after = bytearray(before)
    allowed = set()
    writes = []
    for at, blob, label in placements:
        need(before[at:at+len(blob)] == bytes([255]) * len(blob), 'Expected Write ' + label)
        after[at:at+len(blob)] = blob
        allowed.update(range(at, at+len(blob)))
        writes.append(dict(offset=at, bytes=len(blob), label=label, sha256=sha(blob)))
    for at in SITES:
        need(before[at:at+4] == old_pointer, "Expected Write table literal")
        after[at:at+4] = struct.pack('<I', BASE + START)
        allowed.update(range(at, at+4))
    changed = [n for n, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    need(changed and all(n in allowed for n in changed), "whole-ROM diff containment")
    return bytes(after), dict(input_sha256=INPUT, output_sha256=sha(after), writes=writes,
        literal_sites=SITES, actual_changed_bytes=len(changed), songs=details,
        preserved_old_song_entries=95, new_table=START, allocation=[START, END],
        fidelity_limits=['commercial waveform analogues', 'A1 hardware sweep not emulated',
                         'native CGB noise frequency clamp differs from source; encoded score keys retained',
                         'audible parity and final sound QA not established'])


def main():
    p = argparse.ArgumentParser()
    for name in ('input', 'gba', 'wsc15', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    a = p.parse_args()
    need(all(v.suffix.lower() != '.sav' for v in vars(a).values()), 'provided saves forbidden')
    result, report = build(a.input.read_bytes(), a.gba.read_bytes(), a.wsc15.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(result)
    a.manifest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(report['output_sha256'])


if __name__ == '__main__':
    main()
