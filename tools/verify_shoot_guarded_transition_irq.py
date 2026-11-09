#!/usr/bin/env python3
"""Independent new stationary-family transition IRQ QA; no builder imports."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from verify_shoot_static_companion_clear import Machine as PriorMachine
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
BEFORE = '025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA'
RETAIL = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
LAYOUT = '89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
FIRST, LIMIT, SITE = 0x6FF9C0, 0x6FFED0, 0xD0BE8
ADAPTER, DISPLAY, IRQ, FINAL = 0x086FF600, 0x086FF6B4, 0x086FFE10, 0x086FFEBC
SPANS = ((0x6FF600, 0x6FF800), (FIRST, LIMIT))
WRITES = ((SITE, 4), (0x6FF600, 288), (FIRST, 1092), (0x6FFE10, 192))
STATE, SLOT, RETURN = 0x03004710, 0x030012E0, 0x09000000
OFFSETS = (0, 2, 4, 7, 10, 13, 17, 21)
PRIMITIVES = {
    'verify_shoot_static_companion_clear.py': 'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
    'verify_shoot_attack_dispatch.py': '695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698',
    'verify_shoot_caller_resident.py': '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D',
}


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state'), 'ROM/proof inputs only')
    return path.read_bytes()


def u(data, at):
    return struct.unpack_from('<I', data, at)[0]


def branch(data, at):
    word = u(data, at)
    need(word & 0x0E000000 == 0x0A000000, 'actual direct ARM branch')
    delta = (word & 0xFFFFFF) - (0x1000000 if word & 0x800000 else 0)
    return BASE + at + 8 + delta * 4


def decoded(data, at, length):
    return list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[at:at + length], BASE + at))


def text(data, at, length):
    return [i.mnemonic + ' ' + i.op_str for i in decoded(data, at, length)]


def layout_contract(blob, first=FIRST, limit=LIMIT):
    ledger = json.loads(blob)
    need(sha(blob) == LAYOUT, 'frozen independently normalized component layout')
    need(ledger['predecessor_sha256'] == BEFORE and ledger['retail_bytes'] == 0x400000 and
         ledger['layer_count'] == 70 and ledger['normalized_interval_count'] == 1394,
         'exact original extent and complete70-layer placement ledger')
    layout_disjoint(ledger, first, limit)
    need(ledger['nearest_declared_before'][:2] == [0x6FF240, 0x6FF28C] and
         ledger['nearest_declared_after'][:2] == [0x712680, 0x714680],
         'positive neighboring object extents')
    return ledger


def layout_disjoint(ledger, first, limit):
    need(not any(lo < limit and first < hi for lo, hi in ledger['merged_union']),
         'reservation overlaps a declared object, including an erased live tail')


class Machine(PriorMachine):
    """Run retained native port instructions; only hardware input is sequenced."""
    def __init__(self, rom, seed=0, flags=0x10):
        super().__init__(rom, seed, flags)
        self.compare_inputs = []
        self.compare_reads = []

    def get(self, address, size=4):
        if address == 0x04000004 and size == 2 and self.compare_inputs:
            value = self.compare_inputs.pop(0)
            self.compare_reads.append(value)
            return value
        return super().get(address, size)

    def run(self, start, stops, max_steps=16000):
        # Retained normal/fallback display indexes its halfword table by a
        # register. The inherited strict model otherwise covers this layer.
        for _ in range(32):
            try:
                return super().run(start, stops, max_steps)
            except ValueError as error:
                if str(error) != 'immediate halfword transfer':
                    raise
                pc = self.r[15] - 8
                word = self.get(pc)
                need(word & 0x0E400F90 == 0x00000090 and
                     word & 0x01300060 == 0x01100020,
                     'reviewed pre-indexed unsigned register LDRH only')
                base, target = (word >> 16) & 15, (word >> 12) & 15
                offset = self.r[word & 15]
                address = (self.r[base] + (offset if word & 0x800000 else -offset)) & 0xFFFFFFFF
                self.r[target] = self.get(address, 2)
                start = pc + 4
        raise ValueError('register-halfword instruction bound')


def nonstack_writes(machine, sp):
    return [w for w in machine.writes if not sp - 0x100 <= w[0] < sp]


def irq_case(data, entry, final, index, counter, vertical, match, second, flags, seed=0):
    m = Machine(data, seed, flags)
    sp = m.r[13]
    m.r[14] = RETURN
    original = m.r[:15]
    for off in range(0, 16, 2):
        m.put(STATE + off, (off * 0x123 + 0xAA00) & 65535, 2)
    m.put(STATE + 4, counter, 2)
    m.put(STATE + 6, index, 2)
    m.put(STATE + 8, 0xAB00 | vertical, 2)
    m.put(STATE + 10, 0xCDEF, 2)
    m.put(SLOT, 0x08001234)
    oldstate = bytes(m.mem[STATE + i] for i in range(16))
    expected_compare = ((counter & 255) + OFFSETS[index]) & 255
    first = (expected_compare + (0 if match else 1) + 8) & 255
    # Second C4C result is deliberately unrelated to the first; C10's third
    # read has another low byte, which the real helper must preserve.
    hw = ((second + 8) & 255)
    m.compare_inputs = [(first << 8) | 0x81, (hw << 8) | 0x43, 0x9A51]
    m.run(entry, {RETURN})
    need(m.r[:15] == original and m.cpsr == flags, 'IRQ preserves all live registers, SP, LR and NZCV')
    need(not m.compare_inputs and len(m.compare_reads) == 3, 'two distinct compare reads plus retained C10 read')
    expected = bytearray(oldstate)
    if match:
        struct.pack_into('<H', expected, 4, (counter + 1) & 65535)
        struct.pack_into('<H', expected, 6, index + 1)
    need(bytes(m.mem[STATE + i] for i in range(16)) == expected, 'actual full16bit state counters and untouched adjacent state')
    y = ((vertical - OFFSETS[index]) & 255) if match else 0xEF
    need(m.get(0x030012B9, 1) == y and m.get(0x04000016, 2) == (y - 8) & 65535,
         'retained F44 shadow and actual hardware BG1 vertical projection')
    scheduled = (((second + 1) & 255) + 8)
    need(m.get(0x04000004, 2) == ((scheduled << 8) | 0x51 | 0x20) & 65535,
         'schedule uses independent second compare and actual C10 low-byte contract')
    need(m.get(SLOT) == (final if match and index == 7 else 0x08001234),
         'only eighth matching interrupt replaces callback')
    actual = nonstack_writes(m, sp)
    expected_writes = [(0x030012B9, y, 1), (0x04000016, (y - 8) & 65535, 2)]
    if match:
        expected_writes += [(STATE + 4, (counter + 1) & 65535, 2), (STATE + 6, index + 1, 2)]
        if index == 7:
            expected_writes.append((SLOT, final, 4))
    expected_writes.append((0x04000004, ((scheduled << 8) | 0x51 | 0x20) & 65535, 2))
    need(actual == expected_writes, 'exact IRQ memory/MMIO effects in instruction order')
    return m


def irq_cases(data, entry, final):
    cases = 0
    for index in range(8):
        for counter in (0, 1, 255, 256, 65535):
            for vertical in (0, 21, 255):
                for match in (False, True):
                    for second in (0, 127, 255):
                        flags = ((cases % 16) << 28) | 0x10
                        irq_case(data, entry, final, index, counter, vertical, match, second, flags, cases)
                        cases += 1
    for nibble in range(16):
        m = Machine(data, nibble, (nibble << 28) | 0x10)
        m.r[14] = RETURN
        old = m.r[:15], m.cpsr
        m.run(final, {RETURN})
        need((m.r[:15], m.cpsr) == old and not m.writes and not m.calls,
             'return-only final has no invented DI/r0 ABI or memory effects')
    return {'actual_IRQ_cases': cases, 'actual_final_cases': 16,
            'retained_MMIO_helpers_executed': ['08000C4C', '08000F44', '08000C10'],
            'source_table': list(OFFSETS)}


def fixture(data, flags=0x10, counter=40, vertical=184):
    m = Machine(data, 19, flags)
    # This is a typed native fixture, never a user save or emulator state.
    for start, size in ((0x03000000, 0x8000), (0x02010000, 52 * 0x118),
                        (0x04000000, 0x220), (0x05000000, 0x400),
                        (0x06000000, 32), (0x0600F000, 0x800)):
        for address in range(start, start + size, 4):
            m.put(address, 0)
    # Actual startup DMA copy, including relocated PC-relative literal bytes.
    for offset, value in enumerate(data[0xC9008:0xC9078]):
        m.put(0x03000DB0 + offset, value, 1)
    headers = [0x02010000 + i * 0x118 for i in (0, 51, 20, 21, 22)]
    first, upper, aux = [header + 0x18 for header in headers[2:]]
    for header in headers:
        m.put(header + 0x10, 2, 2)
    for global_address, value in ((0x03004510, headers[0]), (0x03004514, headers[1]),
                                  (0x0300489C, first), (0x030048A0, upper),
                                  (0x03004D3C, aux)):
        m.put(global_address, value)
    m.put(headers[0], 0x08374FAC)
    m.put(headers[1], 0x0837354C)
    for actor, callback, p1, p0, event in (
            (first, 0x0835620C, 0x080D45B8, 0x080D7A58, 0),
            (upper, 0x085BF200, 0x085D0000, 0x085D1000, 1),
            (aux, 0x085BF600, 0x085D029C, 0x085D1100, 0)):
        m.put(actor, callback)
        m.put(actor + 0xF0, p1)
        m.put(actor + 0xF4, p0)
        m.put(actor + 0xBA, event, 2)
    m.put(upper + 0x28, aux)
    m.put(aux + 0x18, upper)
    for offset, value in ((0x34, 0xE00), (0x38, 0xE00), (0x36, 0x1500), (0x3A, 0x1500)):
        m.put(first + offset, value, 2)
    m.put(0x0300231E, 11, 1)
    m.put(0x03002310, 7, 2)
    m.put(0x0300482A, 1, 2)
    m.put(0x03004830, first + 0xAC)
    m.put(0x03004574, 0)
    m.put(0x0300450A, 0x400, 2)
    m.put(0x0400000A, 0x1E00, 2)
    m.put(STATE + 2, counter, 2)
    m.put(STATE + 8, vertical, 2)
    m.put(SLOT, 0x086F1234)
    # Poison old logical shadow and hardware offset. Next display must use
    # prepared camera tuple+2, independently of the omitted prior OUT10.
    m.put(0x030012B8, 0x99, 1)
    for offset, value in enumerate((0x12, 0x34, 0x56, 0x78)):
        m.put(0x0300456C + offset, value, 1)
    m.r[14] = RETURN
    return m, first, upper, aux, headers


def irq_negatives(data, entry, final, table):
    start = entry - BASE
    instructions = decoded(data, start, final - entry)
    def unique(statement):
        matches = [i.address - BASE for i in instructions if i.mnemonic + ' ' + i.op_str == statement]
        need(len(matches) == 1, 'unique semantic mutation anchor: ' + statement)
        return matches[0]
    replacements = [
        ('full16bit counter load', unique('ldrh r0, [r4, #4]'), 0xE5D40004),
        ('eighth match callback', unique('cmp r5, #8'), 0xE3550007),
        ('mismatch fallback low byte', unique('ldrb r0, [r4, #0xa]'), 0xE5D40008),
        ('independent second compare', unique('sub r0, r0, #7'), 0xE2400008),
        ('native compare bridge', unique('add r0, r0, #8'), 0xE2800007),
        ('restored interrupt flags', unique('msr apsr_nzcvq, ip'), 0xE1A00000),
        ('counter adjacent memory', unique('strh r0, [r4, #4]'), 0xE1C400B2),
    ]
    calls = [i.address - BASE for i in instructions if i.mnemonic == 'bl' and i.op_str == '#0x8000c4c']
    need(len(calls) == 2, 'two separately emitted compare calls')
    replacements.append(('second compare removed', calls[1], 0xE1A00000))
    results = []
    for name, address, word in replacements:
        damaged = bytearray(data)
        struct.pack_into('<I', damaged, address, word)
        try:
            irq_cases(bytes(damaged), entry, final)
        except ValueError as error:
            results.append({'mutation': name, 'rejected_by': str(error)})
        else:
            raise ValueError('semantic mutation survived: ' + name)
    damaged = bytearray(data)
    damaged[table - BASE + 1] ^= 1
    try:
        irq_cases(bytes(damaged), entry, final)
    except ValueError as error:
        results.append({'mutation': 'actual offset table value', 'rejected_by': str(error)})
    else:
        raise ValueError('semantic mutation survived: actual offset table')
    return results


def prepared_fixture(data, flags=0x10, counter=40, vertical=184):
    m, first, upper, aux, headers = fixture(data, flags, counter, vertical)
    header = 0x020120D0  # actual native display task slot30, not a forged pointer
    m.put(header + 0x10, 2, 2)
    m.put(header, 0x08352268)
    m.put(header + 4, 0xFFFFF000)
    for address in (0x0300133C, 0x03001344, 0x03004518):
        m.put(address, header)
    m.put(0x03002474, 1, 2)
    m.put(0x03002478, 0x08587200)
    m.put(0x03002518, 1, 2)
    return m, first, upper, aux, header


def native_priority_producer(retail):
    cases = 0
    for value in (0, 0x7FFF, 0x8000, 0xF000, 0xFFFF):
        m = Machine(retail, cases)
        m.r[5] = 0x020120D0
        m.put(m.r[13] + 0x14, value)
        m.run(0x08011AE4, {0x08011AF4})
        expected = value if value < 0x8000 else value | 0xFFFF0000
        need(m.get(0x020120D4) == expected, 'actual native task priority sign extension')
        cases += 1
    return cases


def active_cases(data):
    count = 0
    for index in range(52):
        pointer = 0x02010018 + index * 0x118
        for active in (False, True):
            m = Machine(data, index)
            m.r[0], m.r[14] = pointer, RETURN
            m.put(pointer - 8, 2 if active else 0, 2)
            sp = m.r[13]
            m.run(0x086FFD48, {RETURN})
            need(m.r[0] == (2 if active else 0) and m.r[13] == sp,
                 'actual new helper resolves all52 typed active payloads')
            count += 1
    for pointer in (0, 0x02010017, 0x02010019, 0x020138F8, 0x03000018):
        m = Machine(data)
        m.r[0], m.r[14] = pointer, RETURN
        m.run(0x086FFD48, {RETURN})
        need(m.r[0] == 0, 'new active helper refuses invalid pointer before dereference')
        count += 1
    return count


def check_guard(data, change=None, counter=40, vertical=184):
    m, first, upper, aux, headers = fixture(data, 0xA0000010, counter, vertical)
    if change:
        change(m, first, upper, aux, headers)
    sp, lr = m.r[13], m.r[14]
    m.run(BASE + FIRST, {RETURN}, max_steps=70000)
    need(m.r[13] == sp and m.r[14] == lr, 'boolean checker stack/return ABI')
    need(not nonstack_writes(m, sp), 'predicate does not alter current state or graphics')
    return m.r[0]


def guard_cases(data):
    mutations = []
    def add(name, address, value, size=4):
        mutations.append((name, lambda m, f, u, a, h: m.put(address, value, size)))
    add('wrong stage', 0x0300231E, 7, 1)
    add('active input task', 0x02010000, 0x08374FF4)
    add('active battle task', 0x020137C8, 0x083735BC)
    add('unaligned actor', 0x0300489C, 0x02010019)
    for index, label in ((20, 'FIRST'), (21, 'upper'), (22, 'aux')):
        add('inactive ' + label, 0x02010000 + index * 0x118 + 0x10, 0, 2)
    first = 0x02010018 + 20 * 0x118
    upper = first + 0x118
    aux = upper + 0x118
    for offset in (0x2C, 0x2E, 0x42, 0x44, 0x46, 0x48, 0x4A, 0x4C):
        add('nonzero control/motion ' + hex(offset), first + offset, 1, 2)
    for offset in (0x38, 0x3A):
        add('previous-coordinate mismatch ' + hex(offset), first + offset, 0x1234, 2)
    for actor, callback in ((first, 0x08357670), (upper, 0x085BEA00), (aux, 0x085BF800)):
        add('nonstationary callback ' + hex(actor), actor, callback)
    add('wrong kind', first + 4, 1, 2)
    add('wrong identity', first + 0x11, 1, 1)
    for mask in (1, 2):
        add('air/drop flag ' + hex(mask), first + 6, mask, 2)
    add('unsupported action flag', first + 8, 0x100, 2)
    for actor in (first, upper, aux):
        for offset in (0xF0, 0xF4):
            add('wrong presentation ' + hex(actor + offset), actor + offset, 0x08000000)
    add('wrong FIRST event', first + 0xBA, 1, 2)
    add('wrong upper event', upper + 0xBA, 0, 2)
    add('wrong auxiliary event', aux + 0xBA, 1, 2)
    add('broken upper link', upper + 0x28, first)
    add('broken auxiliary link', aux + 0x18, first)
    add('multiple queued presentations', 0x0300482A, 2, 2)
    add('wrong queued presentation', 0x03004830, aux + 0xAC)
    for address in (0x03002354, 0x03002356, 0x030023A4, 0x030023A6):
        add('moving BG descriptor ' + hex(address), address, 1, 2)
    for value, label in ((0x1F00, 'wrong map'), (0x1E04, 'charbase'),
                         (0x1E80, '8bpp'), (0x5E00, '64x32'),
                         (0x9E00, '32x64'), (0x1E40, 'vertical mosaic')):
        add(label, 0x0400000A, value, 2)
    for mode in range(2, 8):
        add('non-text hardware mode ' + str(mode), 0x04000000, mode, 2)
    count = 1
    need(check_guard(data) == 1, 'valid stationary family accepted')
    for label, change in mutations:
        need(check_guard(data, change) == 0, 'predicate rejects ' + label)
        count += 1
    for offset in range(32):
        need(check_guard(data, lambda m, f, u, a, h: m.put(0x06000000 + offset, 1, 1)) == 0,
             'every byte in common blank tile is current-checked')
        count += 1
    # Independent full160-line oracle: enumerate pixels, then change each
    # sampled row. k=115,b=0 selects a row absent from the old144-line oracle.
    for counter in (1, 40, 114, 115, 122, 123, 143):
        for vertical in (0, 7, 184, 255):
            rows = {((vertical - 29 + line) % 256) // 8 for line in range(counter + 37, 160)}
            need(check_guard(data, counter=counter, vertical=vertical) == 1, 'blank current rows accept')
            count += 1
            for row in rows:
                for column in (0, 31):
                    need(check_guard(data, lambda m, f, u, a, h:
                                     m.put(0x0600F000 + 64 * row + 2 * column, 1, 2),
                                     counter, vertical) == 0, 'all horizontal cells and native bottom8 rows guarded')
                    count += 1
    for value in (0, 144, 255, 256, 65535):
        need(check_guard(data, counter=value) == 0, 'counter outside fixed native recognized domain')
        count += 1
    return {'actual_guard_cases': count, 'distinct_predicate_refusals': len(mutations),
            'all32_blank_tile_bytes': True, 'native_lines_checked': 160}


def postcopy_cases(data):
    changes = [
        ('different current task', lambda m,f,u,a,h: m.put(0x0300133C, 0x02010000)),
        ('different last task', lambda m,f,u,a,h: m.put(0x03001344, 0x02010000)),
        ('different display owner', lambda m,f,u,a,h: m.put(0x03004518, 0x02010000)),
        ('inactive display owner', lambda m,f,u,a,h: m.put(h + 0x10, 0, 2)),
        ('wrong display callback', lambda m,f,u,a,h: m.put(h, 0x0835227C)),
        ('forged unsigned priority', lambda m,f,u,a,h: m.put(h + 4, 0x0000F000)),
        ('different signed priority', lambda m,f,u,a,h: m.put(h + 4, 0xFFFFE000)),
        ('no prepared callback', lambda m,f,u,a,h: m.put(0x03002474, 0, 2)),
        ('multiple prepared callbacks', lambda m,f,u,a,h: m.put(0x03002474, 2, 2)),
        ('wrong prepared callback', lambda m,f,u,a,h: m.put(0x03002478, 0x085E7400)),
        ('transition flag clear', lambda m,f,u,a,h: m.put(0x0300450A, 0, 2)),
        ('wrong stage', lambda m,f,u,a,h: m.put(0x0300231E, 7, 1)),
        ('nonstationary P1', lambda m,f,u,a,h: m.put(f + 0x4A, 1, 2)),
    ]
    for label, change in [('recognized', None)] + changes:
        a, f, u, x, h = prepared_fixture(data)
        b, *_ = prepared_fixture(data)
        if change:
            change(a, f, u, x, h)
            change(b, f, u, x, h)
        sp = a.r[13]
        a.run(ADAPTER, {RETURN}, max_steps=70000)
        b.run(0x08017758, {RETURN}, max_steps=70000)
        need(a.r[:15] == b.r[:15], 'postcopy preserves actual17758 register outputs: ' + label)
        expected = nonstack_writes(b, sp)
        if change is None:
            expected += [(0x03004578, DISPLAY, 4)]
        need(nonstack_writes(a, sp) == expected, 'only existing prepared callback changes: ' + label)
        need(a.get(0x03004574) == (0 if label == 'no prepared callback' else
                                 2 if label == 'multiple prepared callbacks' else 1),
             'copy and selection preserve exact queue count')
    return len(changes) + 1


def queue_chain(data, counter=40, vertical=184):
    m, first, upper, aux, header = prepared_fixture(data, counter=counter, vertical=vertical)
    sp = m.r[13]
    # Execute installed BL, real17758 copy, real adapter/checker, actual copied
    # C9000 pop, line1 scheduling and interrupt enable up to retained tail.
    m.run(0x080D0BE8, {0x080D0C10}, max_steps=70000)
    need(m.get(0x03004574) == 0 and m.get(SLOT) == DISPLAY,
         'real queue consumes one substituted callback before display')
    need(m.get(0x04000004, 2) == 0x012B, 'retained native producer schedules VCOUNT1')
    need(m.r[13] == sp, 'postcopy full-chain stack preserved')
    before = m.r[:15]
    m.run(0x0801140C, {0x08011420}, max_steps=70000)
    for reg in list(range(8)) + [10, 11, 12, 13]:
        need(m.r[reg] == before[reg], 'actual display dispatcher/tiny wrapper preserves live R' + str(reg))
    need(m.r[8] == SLOT and m.r[9] == DISPLAY and m.r[14] == 0x08011420,
         'actual dispatch owns R8/R9/LR; tiny wrapper preserves its incoming values')
    need(m.get(SLOT) == IRQ and m.get(0x03004574) == 0,
         'actual tiny display and empty C9000 preserve source IRQ callback')
    need(m.get(STATE + 4, 2) == counter and m.get(STATE + 6, 2) == 0 and
         m.get(STATE + 2, 2) == ((counter & 0xFF00) | ((counter - 1) & 255)),
         'display uses pre-display old counter, zero index and low-byte decrement')
    need(m.get(0x030012B8, 1) == 0x56 and m.get(0x04000014, 2) == 0x4E,
         'current OUT10 uses prepared tuple and kills prior horizontal shadow')
    first_compare = m.get(0x04000004, 2) >> 8
    need(first_compare == ((counter - 1) & 255) + 8,
         'actual first native compare affine projection')
    interrupts, matching = 0, 0
    while m.get(SLOT) == IRQ:
        prior = m.get(STATE + 6, 2)
        m.run(0x0801140C, {0x08011420}, max_steps=70000)
        matching += m.get(STATE + 6, 2) != prior
        interrupts += 1
        need(interrupts <= 40, 'bounded exact eight-match source IRQ progression')
    need(m.get(SLOT) == FINAL and matching == 8 and interrupts == 30,
         'first mismatch and all source interstitial matches reach return-only final')
    need(m.get(STATE + 4, 2) == (counter + 8) & 65535 and m.get(STATE + 6, 2) == 8,
         'full actual queue-to-final state trajectory')
    before_final = len(m.writes)
    old = m.r[:15]
    m.run(0x0801140C, {0x08011420}, max_steps=70000)
    need(len(m.writes) == before_final and m.r[6] == old[6] and m.r[13] == sp,
         'actual dispatcher return-only final has no RAM/MMIO/stack effect')
    return {'counter': counter, 'vertical': vertical, 'dispatches_to_final': interrupts,
            'matching_dispatches': matching, 'first_hardware_compare': first_compare,
            'scheduled_final_compare': m.get(0x04000004, 2) >> 8}


def stale_wrapper_cases(data):
    count, carry_differences = 0, 0
    for nibble in range(16):
        flags = (nibble << 28) | 0x10
        for mode, stage, transition in ((8, 11, 0xD86), (7, 7, 0x400), (7, 11, 0)):
            for arm in (0, 2, 4):
                a, *_ = fixture(data, flags)
                b, *_ = fixture(data, flags)
                for m in (a, b):
                    m.put(0x03002310, mode, 2)
                    m.put(0x0300231E, stage, 1)
                    m.put(0x0300450A, transition, 2)
                    m.put(0x03004506, arm, 2)
                    m.put(SLOT, IRQ)
                sp = a.r[13]
                a.run(DISPLAY, {RETURN}, max_steps=70000)
                b.run(0x08587200, {RETURN}, max_steps=70000)
                need(a.r[:15] == b.r[:15] and
                     nonstack_writes(a, sp) == nonstack_writes(b, sp),
                     'stale tiny wrapper is exact existing route, registers and memory/MMIO')
                # The IRQ-only callback may change intermediate condition flags. Unconditional
                # 11374..11398 restores saved SPSR after callback, so this is
                # not returned main-program condition state.
                need((a.cpsr ^ b.cpsr) & ~0xF0000000 == 0,
                     'only dead intermediate condition flags may differ in stale IRQ callback')
                carry_differences += a.cpsr != b.cpsr
                need(a.get(SLOT) != IRQ, 'stale callback cannot remain installed')
                count += 1
    return {'actual_stale_wrapper_cases': count, 'dead_intermediate_condition_differences': carry_differences,
            'mode8_stage11_flags0D86_explicitly_covered': True}


def structural(before, after, manifest, ledger_bytes, scan=True):
    need(len(before) == len(after) == 0x800000, 'complete8MiB inverse')
    for first, limit in SPANS:
        need(before[first:limit] == bytes([255]) * (limit - first), 'entire cave erased')
        layout_contract(ledger_bytes, first, limit)
    restored = bytearray(after)
    for at, length in WRITES:
        restored[at:at + length] = before[at:at + length]
    need(restored == before, 'exact four declared write extents and full-ROM inverse')
    need(branch(before, SITE) == 0x08017758 and branch(after, SITE) == ADAPTER and
         u(after, SITE) >> 24 == 0xEB, 'actual displaced17758 BL retargets only late adapter')
    need([(row['raw'], row['bytes']) for row in manifest['writes']] == list(WRITES),
         'manifest records actual four write extents')
    for row in manifest['writes']:
        need(sha(after[row['raw']:row['raw'] + row['bytes']]) == row['sha256'],
             'manifest actual emitted span digest')
    need(manifest['entries'] == {'adapter': ADAPTER, 'display': DISPLAY, 'guard': BASE + FIRST,
                                 'irq': IRQ, 'final': FINAL}, 'all five actual entries')
    need(sha(after[0x6FFE10:0x6FFED0]) ==
         '39B5D48FAC09792EAED50E903ECDE85C0CC17ED3DAF52FAF17C36D3A8BF8767D',
         'previously independently executed exact192B IRQ unit retained')
    need(manifest['external_entry_authorized'] is False and manifest['complete_Shoot'] is False and
         manifest['source_DI_value_emulated'] is False and manifest['new_RAM_or_task'] is False,
         'explicit bounded resident-only scope')
    if scan:
        scanner.SPANS = SPANS
        need(not scanner.inbound(before), 'strict whole-ROM pointer/ARM/Thumb inbound census')
    return {'declared_write_bytes': sum(length for _, length in WRITES),
            'changed_bytes': sum(a != b for a, b in zip(before, after)),
            'whole_ROM_inverse': True, 'reservation_intervals': list(SPANS),
            'retail_neighbor_encodings_explained_by_layout': True}


def source_contract(source, retail, before, after):
    def xs(at, expected):
        rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[at:at + 160], at))[:len(expected)]
        need([i.mnemonic + ' ' + i.op_str for i in rows] == expected, 'actual source typed consumer ' + hex(at))
    xs(0x75FC35, ['mov bx, word ptr es:[di + 6]', 'in al, 3',
                  'mov ah, byte ptr es:[di + 4]', 'add ah, byte ptr cs:[bx + 0xe03]',
                  'cmp al, ah', 'jne 0x75fc79'])
    xs(0x75FC48, ['mov ax, word ptr es:[di + 8]', 'sub al, byte ptr cs:[bx + 0xe03]',
                  'out 0x11, al', 'inc word ptr es:[di + 4]', 'inc word ptr es:[di + 6]',
                  'cmp word ptr es:[di + 6], 8'])
    xs(0x75FC79, ['mov ax, word ptr es:[di + 0xa]', 'out 0x11, al', 'in al, 3', 'inc al', 'out 3, al'])
    xs(0x75FC90, ['mov bx, 0x300', 'mov es, bx', 'mov bx, 0xea',
                  'mov ax, word ptr es:[di + 0xa]', 'out 0x10, al'])
    need(source[0x75FCA3:0x75FCAB] == bytes(OFFSETS), 'actual source eight-entry offset table')
    xs(0x77DD9A, ['mov di, 0x1ce', 'mov word ptr [di + 4], 0x1000',
                  'mov word ptr [di], 0x12', 'mov word ptr [di + 2], 0x13'])
    xs(0x77DDE1, ['mov di, 0x20e', 'mov word ptr [di + 4], 0x800',
                  'mov word ptr [di], 0x10', 'mov word ptr [di + 2], 0x11'])
    need([u(before, at) for at in (0x582B54, 0x582B58, 0x582B5C,
                                   0x582B70, 0x582B74, 0x582B78)] ==
         [0x03002338, 0x0600F800, 0x030012BA, 0x03002388, 0x0600F000, 0x030012B8],
         'Shoot-specific positive source-object/map/hardware mapping, distinct from Waterfall')
    need(text(retail, 0x11AE4, 16) == [
        'ldr r0, [sp, #0x14]', 'lsl r0, r0, #0x10',
        'asr r0, r0, #0x10', 'str r0, [r5, #4]'], 'actual native signed priority producer')
    need(text(before, 0x373AC8, 32) == [
        'ldrsh r0, [r4, #0x4a]', 'ldrsh r3, [r4, #0x4c]',
        'ldrsh r8, [r4, #0x34]', 'add r8, r8, r0', 'strh r8, [r4, #0x34]',
        'ldrsh r8, [r4, #0x36]', 'add r8, r8, r3', 'strh r8, [r4, #0x36]'],
        'actual native displacement/current-coordinate consumers')
    need(text(before, 0x3561D8, 36)[3:9] == [
        'mov sb, #0', 'strh sb, [r4, #0x42]', 'strh sb, [r4, #0x44]',
        'strh sb, [r4, #0x46]', 'strh sb, [r4, #0x48]', 'add r8, pc, #0xc'],
        'actual idle initializer zero-motion and callback producer')
    need(text(before, 0x5BF200, 4) == text(before, 0x5BF600, 4) == ['bx lr'],
         'native upper and auxiliary return-only owners')
    need([u(before, at) for at in (0x4A80F8, 0x4A80FC)] == [0x080D7A58, 0x080D45B8],
         'actual ID0 base P0/P1 producer roles')
    need(u(retail, 0xC9064) == 0x03000DB0 and u(retail, 0x3B4) == 0x080C9008 and
         u(retail, 0xC9068) == 0x03004574, 'actual copied queue helper and count literal')
    adds = [0x200, 0x180, 0x380, 0x120, 0x120, 0x1A0, 0x110, 0x1C0]
    need(sum(adds) == 0xDB0 and text(retail, 0x168, 4) == ['mov r7, #0x3000000'] and
         [text(retail, at, 4)[0] for at in (0x184,0x1A0,0x1BC,0x1D8,0x1F4,0x210,0x228,0x244)] ==
         ['add r7, r7, #' + hex(value) for value in adds],
         'actual cumulative boot DMA destination DB0')
    need(text(retail, 0x254, 12) == ['mov r4, #0x1c', 'strh r4, [r6, #0xdc]', 'strh r8, [r6, #0xde]'] and
         text(retail, 0x160, 4) == ['mov r8, #0x8400'],
         'actual immediate32bit DMA copies1C words, not a stub')
    for lo, hi in ((0xC10, 0xC58), (0xF2C, 0xF8C), (0x11374, 0x11428),
                   (0x11440, 0x114EC), (0x17758, 0x177B0), (0xC9000, 0xC9078),
                   (0xC97B8, 0xC993C)):
        need(after[lo:hi] == before[lo:hi] == retail[lo:hi], 'retained exact native display/queue service')
    epilogue = text(retail, 0x11374, 40)
    need(epilogue[-2:] == ['msr spsr_fc, r0', 'bx lr'] and
         all(u(retail, at) >> 28 == 14 for at in range(0x11374, 0x1139C, 4)),
         'IRQ epilogue restores saved SPSR without a conditional flag consumer')
    need(text(before, 0x5E7434, 16) == ['ldrb r0, [r5, #2]', 'bl #0x8000f2c',
                                       'ldrb r0, [r5, #3]', 'bl #0x8000f44'] and
         u(before, 0x5E7524) == 0x0300456C, 'independent prepared tuple overwrites next OUT10')
    return {'source_irq_table_and_counters': True, 'source_DI_read_not_replaced_by_constant': True,
            'native_bottom8_lines_included': True, 'actual_boot_queue_image': [0xC9008, 0xC9078, 0x03000DB0],
            'native_priority': 'FFFFF000 from actual sign extension',
            'current_map_owner': 'source1000:020E -> native03002388 -> hardware BG1/F000',
            'stale_IRQ_flags': 'intermediate condition flags may differ; unchanged unconditional epilogue restores saved SPSR'}


def semantic_negatives(data):
    checks = [
        ('real queue copy omitted', 0x6FF604, 0xE1A00000, postcopy_cases),
        ('wrong signed priority', 0x6FF65C, 0xE3500A0F, postcopy_cases),
        ('queue substitution writes adjacent slot', 0x6FF6A8, 0xE5801008, postcopy_cases),
    ]
    # Obtain the new mode conditional from actual instructions, not a copied
    # source-program implementation. This survives literal-table relocation.
    display = decoded(data, DISPLAY - BASE, 80)
    mode_branch = next(i.address - BASE for n, i in enumerate(display)
                       if i.mnemonic == 'bne' and n > 0 and
                       display[n - 1].mnemonic == 'cmp' and display[n - 1].op_str == 'r1, #7')
    checks.append(('mode8 stale callback accepted', mode_branch, 0xE1A00000, stale_wrapper_cases))
    guard = decoded(data, FIRST, 900)
    height = next(i.address - BASE for i in guard if i.mnemonic == 'cmp' and i.op_str == 'r6, #0xa0')
    checks.append(('native bottom8 rows omitted', height, 0xE3560098, guard_cases))
    literal = data.find(struct.pack('<I', 0xDFCC), FIRST, IRQ - BASE)
    need(literal >= 0, 'unique emitted no-mosaic hardware mask')
    checks.append(('mosaic enabled without projection', literal, 0xDF8C, guard_cases))
    stale = next(i.address - BASE for i in display if i.mnemonic == 'b' and i.op_str == '#0x8587200')
    checks.append(('stale IRQ slot retained', stale, 0xE12FFF1E, stale_wrapper_cases))
    checks.append(('source active slot52 omitted', 0x6FFD4C, 0xE3A02033, active_cases))
    output = []
    for name, at, word, check in checks:
        damaged = bytearray(data)
        struct.pack_into('<I', damaged, at, word)
        try:
            check(bytes(damaged))
        except ValueError as error:
            output.append({'mutation': name, 'rejected_by': str(error)})
        else:
            raise ValueError('semantic mutation survived: ' + name)
    return output


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'predecessor', 'retail', 'source'):
        p.add_argument(name, type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    for name, digest in PRIMITIVES.items():
        need(sha((ROOT / 'tools' / name).read_bytes()) == digest, 'frozen independent primitive ' + name)
    after, before, retail, source = [read(getattr(args, name)) for name in ('candidate','predecessor','retail','source')]
    need((sha(before), sha(retail), sha(source)) == (BEFORE, RETAIL, SOURCE), 'exact predecessor/retail/source identity')
    manifest_bytes, ledger_bytes = read(args.manifest), read(args.layout)
    manifest = json.loads(manifest_bytes)
    need(manifest['output_sha256'] == sha(after), 'component manifest output matches actual emitted ROM')
    structure = structural(before, after, manifest, ledger_bytes)
    source_proof = source_contract(source, retail, before, after)
    proof = {'native_priority_producer_cases': native_priority_producer(retail),
             'new_active_helper_cases': active_cases(after), 'guard': guard_cases(after),
             'postcopy_cases': postcopy_cases(after),
             'full_queue_chains': [queue_chain(after, counter, vertical)
                                   for counter, vertical in ((1,0),(40,184),(115,255),(143,184))],
             'stale_wrapper': stale_wrapper_cases(after),
             'irq': irq_cases(after, IRQ, FINAL)}
    negatives = semantic_negatives(after) + irq_negatives(after, IRQ, FINAL, 0x086FFEC8)
    # Ownership controls exercise structural semantics separately from hashes.
    damaged = bytearray(after); damaged[0x6FF900] ^= 1
    try:
        structural(before, damaged, manifest, ledger_bytes, False)
    except ValueError as error:
        negatives.append({'mutation': 'undeclared byte between caves', 'rejected_by': str(error)})
    else:
        raise ValueError('undeclared write survived')
    ledger = json.loads(ledger_bytes)
    fake = dict(ledger, merged_union=ledger['merged_union'] + [[0x6FF5F0, 0x6FF620]])
    try:
        layout_disjoint(fake, *SPANS[0])
    except ValueError as error:
        negatives.append({'mutation': 'erased live object tail spans cave', 'rejected_by': str(error)})
    else:
        raise ValueError('erased but owned tail survived reservation check')
    for name, payload in (('unaligned pointer', struct.pack('<I', ADAPTER)),
                          ('ARM branch', struct.pack('<I', 0xEA000000 | (((ADAPTER - (BASE + 0x7F0000) - 8)//4) & 0xFFFFFF)))):
        damaged = bytearray(before)
        site = 0x7F0001 if name == 'unaligned pointer' else 0x7F0000
        damaged[site:site+4] = payload
        scanner.SPANS = SPANS
        need(bool(scanner.inbound(damaged)), 'strict new inbound mutation rejected: ' + name)
        negatives.append({'mutation': 'new inbound ' + name, 'rejected_by': 'strict whole-ROM decoder'})
    report = {'schema': 1, 'status': 'INDEPENDENT_BOUNDED_STATIONARY_IRQ_COMPONENT_PASS',
              'candidate_sha256': sha(after), 'predecessor_sha256': sha(before),
              'retail_sha256': sha(retail), 'source_sha256': sha(source),
              'manifest_sha256': sha(manifest_bytes), 'layout_ledger_sha256': sha(ledger_bytes),
              'verifier_sha256': sha(Path(__file__).read_bytes()),
              'primitive_sha256': PRIMITIVES,
              'structure': structure, 'source_and_native_contract': source_proof,
              'execution': proof, 'negative_controls': negatives,
              'scope': 'Resident stationary ID0 base family under retained normal scene/task ownership; current blank sampled rows and blanktile, exact native IRQ translation. No moving low-Y family or external route completion.',
              'emulator_or_user_save_access': False, 'complete_Shoot': False,
              'source_DI_value_emulated': False, 'main_or_external_entry_changed': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print('PASS bounded stationary IRQ actual native joins; ' + sha(after) + '; negatives=' + str(len(negatives)))


if __name__ == '__main__':
    main()






