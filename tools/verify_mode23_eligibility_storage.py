"""Check the persistent mode 23 eligibility bridge in an isolated ARM fixture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import mode23_eligibility_storage as layer
from mode23_linker import compose
from verify_mode23_completion_save import BUFFER, CONFIG, StorageMachine, dump, fill, need, payload, sha


CODE = 0x08FF0000
READ, WRITE = 0x0837DB60, 0x0837DB54
MARKER = b'BS15M23\x01'
CLOSED = bytes(8)
RECORD = range(25)
FIRST_PRE = 0x08089534
RESULT_STOPS = {0x08089574, 0x08089668}
RECORD_INIT = 0x0801F894
REFERENCE = 'C64741E95CECC53BFE7EFBD61D046BD87EFDE021803E835C5DD7B28EA77FC2AA'
EXACT_CALLS = {
    0x0801F894: [0x15940, 0xC35D4],
    0x0801FCA8: [0x1FC08],
    0x0808B334: [0x8955C],
    READ: [0x1FCC0, 0x629828, 0x629850],
    WRITE: [0x1FC7C, 0x629844, 0x62986C],
}
THUMB_CALLS = {0x0837D7E4: [0x37D998], 0x0837D894: [0x37D9E2],
               0x0837D970: [0x37D9F2], 0x0837D9C8: []}


def source_and_storage(source, image):
    layer.require_authorized_source(source)
    need(sha(image) == REFERENCE, 'exact registered mode 23 predecessor')
    source_call = bytes.fromhex('9a8115f176')
    need(source.find(source_call) == source.rfind(source_call) == 0x777065, 'sole encoded source direct far call')
    need(source.count(source_call[1:]) == 1, 'sole unaligned source far-address representation')
    need(source[0x777049:0x777055] == bytes.fromhex('807d0e0b7406807d0e07751f'),
         'source result gate accepts 11 or 7')
    reference = {target: [] for target in EXACT_CALLS}
    thumb = {target: [] for target in THUMB_CALLS}
    for i, (word,) in enumerate(struct.iter_unpack('<I', image)):
        if word & 0x0E000000 == 0x0A000000:
            target = 0x08000008 + i * 4 + 4 * ((word & 0x7FFFFF) - (word & 0x800000))
            if target in reference:
                reference[target].append(i * 4)
    halves = struct.unpack(f'<{len(image)//2}H', image)
    for i, first in enumerate(halves[:-1]):
        if first & 0xF800 == 0xF000 and halves[i + 1] & 0xF800 == 0xF800:
            displacement = ((first & 0x3FF) - (first & 0x400)) * 0x1000
            target = 0x08000004 + i * 2 + displacement + (halves[i + 1] & 0x7FF) * 2
            if target in thumb:
                thumb[target].append(i * 2)
    need(reference == EXACT_CALLS and thumb == THUMB_CALLS, 'current whole-image encoded EEPROM/reset/win caller census')
    for target, at in ((0x0837D7E5, 0x37DB68), (0x0837D9C9, 0x37DB5C)):
        ptr = struct.pack('<I', target)
        need(image.find(ptr) == image.rfind(ptr) == at, 'sole indirect Thumb EEPROM API veneer pointer')
    for target in (READ, WRITE, 0x0801F894, 0x0808B334):
        need(struct.pack('<I', target) not in image, 'no indirect native entry pointer')
    return dict(source_writer_call=0x777065, source_stage_values=[7, 11],
                ARM_encoded_edges=reference, Thumb_encoded_edges=thumb,
                original_record_blocks=[0, 24], Shoot_block=25, eligibility_block=26,
                physical_capacity=64, area=[208, 216],
                scope='Exact ARM B/BL, Thumb BL and byte-aligned or unaligned literal addresses for these APIs.')


class EEPROMFixture(StorageMachine):
    def __init__(self, image, marker, read_fail=-1, write_fail=-1):
        super().__init__(image)
        self.io = []
        self.read_fail, self.write_fail = read_fail, write_fail
        self.blocks[208:216] = marker
        self.load_model = bytearray(payload(14))
        self.load_model[:0x10] = image[0x1F9D4:0x1F9E4]
        struct.pack_into('<I', self.blocks, 0xC0, sum(self.load_model))
        self.blocks[:0xC0] = self.load_model
        fill(self, BUFFER, bytes(self.blocks[:200]))
        fill(self, CONFIG, bytes(0x40))
        fill(self, 0x02010000, bytes(8))
        self.services = {}
        self.limit_sp = self.r[13]

    def device(self, direction):
        block, pointer = self.r[0], self.r[1]
        need(block in (*RECORD, 26) and pointer % 2 == 0, 'no Shoot or unallocated EEPROM blocks')
        if block in RECORD:
            need(pointer == BUFFER + block * 8, 'retained transfer buffer')
        elif direction == 'read':
            need(pointer == self.r[13] and self.limit_sp - 512 < pointer <= self.limit_sp - 8,
                 'eight-byte private stack destination for eligibility read')
        else:
            need(CODE <= pointer < CODE + 256, 'typed eight-byte constant source for eligibility write')
        lo = block * 8
        failure = block == (self.read_fail if direction == 'read' else self.write_fail)
        if direction == 'read':
            self.io.append((direction, block, None))
            if not failure:
                fill(self, pointer, bytes(self.blocks[lo:lo + 8]))
        else:
            data = dump(self, pointer, 8)
            self.io.append((direction, block, data))
            if not failure:
                self.blocks[lo:lo + 8] = data
        self.r[0] = 0x8000 if failure else 0
        for i in (1, 2, 3, 12):
            self.r[i] = 0x7C00 + i

    def drive(self, pc, stops):
        stops = set(stops)
        legacy_halfword = {0x0801F95C}
        for _ in range(256):
            pc = self.run(pc, stops | {READ, WRITE} | legacy_halfword, max_steps=22000)
            if pc in stops:
                return pc
            if pc in (READ, WRITE):
                self.device('read' if pc == READ else 'write')
                pc = self.r[14]
            else:
                word = self.get(pc)
                need(word == 0xE0D100B2, 'exact retained default-score LDRH post-index')
                self.r[0] = self.get(self.r[1], 2)
                self.r[1] += 2
                pc += 4
        raise ValueError('EEPROM service/return fixture exceeded bound')


def reader(rom, symbols):
    samples = ((MARKER, -1, 1), (CLOSED, -1, 0), (bytes([255]) * 8, -1, 0),
               (MARKER[:-1] + b'\2', -1, 0), (b'\0' + MARKER[1:], -1, 0), (MARKER, 26, 0))
    for marker, fail, result in samples:
        for flags in range(16):
            m = EEPROMFixture(rom, marker, read_fail=fail)
            m.cpsr = (flags << 28) | 31
            initial = m.r[:15]
            old = bytes(m.blocks)
            m.drive(symbols['m23_eligibility_read'], {initial[14]})
            need(m.r[0] == result and m.r[1:15] == initial[1:15], 'strict caller ABI + exact eligibility result')
            need(bytes(m.blocks) == old and m.io == [('read', 26, None)], 'one private read, zero device writes')
    return len(samples) * 16


def result_gate(rom):
    m = EEPROMFixture(rom, CLOSED)
    for stage in range(256):
        m.r[8] = stage
        m.drive(0x08089538, {0x0808953C})
        need(bool(m.cpsr & 0x40000000) == (stage in (7, 11)) and m.r[8] == stage,
             'full LDRB stage domain and compare ABI')
    return 256


def play_result(rom, stage, marker, win=True, continued=False, pending=0, write_fail=-1):
    m = EEPROMFixture(rom, marker, write_fail=write_fail)
    m.r[4], m.r[5], m.r[3], m.r[0] = 0x02010000, CONFIG, pending, 0x10 if win else 8
    m.put(CONFIG + 0xE, stage, 1)
    m.put(CONFIG + 0x1A, int(continued), 2)
    initial = bytes(m.blocks)
    sp = m.r[13]
    end = m.drive(FIRST_PRE, RESULT_STOPS)
    need(m.r[13] == sp, 'native double-call arguments/restored stack')
    need(m.blocks[200:208] == initial[200:208] and m.blocks[216:] == initial[216:], 'Shoot/unallocated storage preserved')
    need(end == (0x08089668 if stage in (7, 11) else 0x08089574), 'source result continuation')
    if stage not in (7, 11) or not win or continued or pending:
        need(not m.io and bytes(m.blocks) == initial, 'no early/continued/loss/nonfinal eligibility')
    else:
        record_count = 25 if write_fail < 0 or write_fail == 26 else write_fail + 1
        expected_io = [('write', n) for n in range(record_count)] * 2
        if write_fail not in RECORD:
            expected_io.append(('read', 26))
            if marker != MARKER:
                expected_io.append(('write', 26))
        need([(direction, block) for direction, block, _ in m.io] == expected_io, f'two ordered native saves before eligibility mark at stage {stage}, fail {write_fail}')
        if len(expected_io) > 50 and marker != MARKER and write_fail != 26:
            need(m.blocks[208:216] == MARKER, 'legitimate clear commits exact tagged source bit')
        else:
            need(m.blocks[208:216] == marker, 'already-enabled or failed transaction stays intact')
    return m


def reset_test(rom, unmodified, symbols, argument, mutation='', fail=-1):
    m = EEPROMFixture(rom, MARKER, write_fail=fail)
    baseline = EEPROMFixture(unmodified, MARKER)
    for vm in (m, baseline):
        if mutation == 'checksum':
            vm.blocks[0xC0] ^= 1
        if mutation == 'signature':
            vm.blocks[0] ^= 1
            struct.pack_into('<I', vm.blocks, 0xC0, sum(vm.blocks[:0xC0]))
        vm.put(vm.r[13], argument)
    initial = bytes(m.blocks)
    sp = m.r[13]
    m.drive(RECORD_INIT, {m.r[14]})
    baseline.drive(RECORD_INIT, {baseline.r[14]})
    need(m.r[13] == sp, 'factory/reset ABI stack restore')
    changed = bool(argument or mutation)
    expected = [('read', n) for n in RECORD]
    if changed:
        expected.append(('write', 26))
        if fail != 26:
            expected.extend(('write', n) for n in RECORD)
    need([(d, b) for d, b, _ in m.io] == expected, 'actual valid load versus exact default-only reset')
    if fail == 26:
        need(bytes(m.blocks) == initial, 'failed clear never commits a new native persistent record')
    else:
        need(m.blocks[:200] == baseline.blocks[:200], 'entire native persistent prefix equals original behavior')
        need(bytes(m.blocks[208:216]) == (CLOSED if changed else MARKER), 'eligible save data survives valid load, reset closes')
    need(m.blocks[200:208] == initial[200:208] and m.blocks[216:] == initial[216:], 'reset leaves Shoot/unallocated blocks')
    m.drive(symbols['m23_eligibility_read'], {m.r[14]})
    need(m.r[0] == int(not changed or fail == 26), 'public consumer sees physical eligibility state')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'native', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    source, native = args.source.read_bytes(), args.native.read_bytes()
    owner = source_and_storage(source, native)
    code, symbols, linker = compose((layer.assembly(source, native),), CODE, layer.EXPORTS)
    mutations = layer.patches(native, symbols)
    need(len(native) == 0x1000000 and set(mutations) == {0x89538, 0x8B394, 0x1F9C4}, 'exact fixture hook sites')
    rom = bytearray(native)
    # The fixture link address is deliberately local to the modeled ROM.
    offset = CODE - 0x08000000
    rom[offset:offset + len(code)] = code
    for at, instruction in mutations.items():
        rom[at:at + 4] = instruction
    read_cases = reader(rom, symbols)
    stage_cases = result_gate(rom)
    results = [(7, CLOSED, True, False, 0, -1), (11, CLOSED, True, False, 0, -1),
               (11, bytes([255]) * 8, True, False, 0, -1), (7, MARKER, True, False, 0, -1),
               (11, CLOSED, False, False, 0, -1), (11, CLOSED, True, True, 0, -1),
               (7, CLOSED, True, False, 1, -1), (10, CLOSED, True, False, 0, -1),
               (15, CLOSED, True, False, 0, -1), (11, CLOSED, True, False, 0, 26)]
    results += [(11, CLOSED, True, False, 0, block) for block in RECORD]
    for scenario in results:
        play_result(rom, *scenario)
    resets = [(0,), (1,), (0, 'checksum'), (0, 'signature'), (1, '', 26)]
    for reset in resets:
        reset_test(rom, native, symbols, *reset)
    report = dict(status='MODE23_ELIGIBILITY_STORAGE_QA_PASS', source_sha256=sha(source), native_sha256=sha(native),
                  checker_sha256=sha(Path(__file__).read_bytes()), adapter_sha256=sha(Path(layer.__file__).read_bytes()),
                  code_bytes=len(code), linked_code_sha256=sha(code), linkage=linker,
                  patched_offsets=list(mutations), ownership=owner, predicate_cases=read_cases,
                  stage_compare_cases=stage_cases, native_result_cases=len(results), actual_ARM_reset_cases=len(resets),
                  marker=MARKER.hex(), no_new_resident_RAM=True, fixture_models_device_only=True,
                  EEPROM_hardware_or_emulator_executed=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()

