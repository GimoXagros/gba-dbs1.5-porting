#!/usr/bin/env python3
"""Independent actual-ARM check of the narrow static companion clear layer.

No production builder imports, emulator, supplied save or game-state writes.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import itertools
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from verify_shoot_attack_dispatch import Machine as ParentMachine
from verify_shoot_caller_resident import signed, rotate

BASE = 0x08000000
BEFORE = '8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST, LIMIT = 0x6FE800, 0x6FF000
OWNER, CAPTURE, RENDER, EXPIRE = (BASE + FIRST + n for n in (0, 0x100, 0x200, 0x600))
HOOKS = (0x5CD314, 0x12C50, 0x35346C)
PHASES = (0x085CD340, 0x085CD3A0, 0x085CD420, 0x085CD4B0,
          0x085CD510, 0x085CD550, 0x085CD5E0, 0x085CD640,
          0x085CD6A0, 0x085CD710, 0x085CD740)
POOL, PRESENT, SCENE = 0x02010000, 0x0201F000, 0x02010018
GROUPS = (0x4A82D8, 0x60B1E0)

def need(ok, label):
    if not ok:
        raise ValueError(label)

def sha(data): return hashlib.sha256(data).hexdigest().upper()
def u(data, at): return struct.unpack_from('<I', data, at)[0]
def h(data, at): return struct.unpack_from('<H', data, at)[0]

def branch(data, at):
    w = u(data, at)
    need(w & 0x0E000000 == 0x0A000000, 'actual ARM direct branch')
    return BASE + at + 8 + signed(w & 0xFFFFFF, 24) * 4

def listing(data, at, size):
    ins = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[at:at + size], BASE + at))
    need(sum(i.size for i in ins) == size, 'whole instruction decode')
    return [i.mnemonic + ' ' + i.op_str for i in ins]

class Machine(ParentMachine):
    def shifted(self, w):
        if w & 0x02000000:
            return rotate(w & 255, ((w >> 8) & 15) * 2)
        if not w & 16:
            return super().shifted(w)
        need((w >> 5) & 3 == 0 and not w & 128, 'reviewed register LSL only')
        count = self.r[(w >> 8) & 15] & 255
        return (self.r[w & 15] << count) & 0xFFFFFFFF if count < 32 else 0

    def run(self, start, stops, max_steps=16000):
        pc = start
        for _ in range(max_steps):
            if pc in stops:
                return pc
            w = self.get(pc)
            self.r[15] = pc + 8
            nxt = pc + 4
            if not self.condition(w >> 28):
                pc = nxt
                continue
            if w & 0x0FFFFFF0 == 0x012FFF10:
                nxt = self.r[w & 15]
            elif w & 0x0FFF0FFF == 0x010F0000:
                self.r[(w >> 12) & 15] = self.cpsr
            elif w & 0x0FFFFFF0 == 0x0128F000:
                self.cpsr = (self.cpsr & 0x00FFFFFF) | (self.r[w & 15] & 0xFF000000)
            elif w & 0x0E000000 == 0x08000000:
                need(w & 0x0FFF0000 in (0x092D0000, 0x08BD0000), 'reviewed PUSH/POP only')
                regs = [i for i in range(16) if w & (1 << i)]
                load = bool(w & 0x100000)
                address = self.r[13] if load else self.r[13] - 4 * len(regs)
                for i, reg in enumerate(regs):
                    if load:
                        self.r[reg] = self.get(address + 4 * i)
                    else:
                        self.put(address + 4 * i, self.r[reg], log=True)
                self.r[13] += (1 if load else -1) * 4 * len(regs)
                if load and 15 in regs:
                    nxt = self.r[15]
            elif w & 0x0E000000 == 0x0A000000:
                nxt = pc + 8 + signed(w & 0xFFFFFF, 24) * 4
                if w & 0x1000000:
                    self.r[14] = pc + 4
                    self.calls.append((pc, nxt, tuple(self.r[:5])))
                    if nxt in self.services:
                        self.services[nxt](self)
                        nxt = pc + 4
            elif w & 0x0C000000 == 0x04000000:
                offset = self.shifted(w & ~0x02000000) if w & 0x02000000 else w & 0xFFF
                base, reg = (w >> 16) & 15, (w >> 12) & 15
                need(not w & 0x200000 or base != reg, 'bounded non-aliasing writeback')
                updated = (self.r[base] + (offset if w & 0x800000 else -offset)) & 0xFFFFFFFF
                address = updated if w & 0x1000000 else self.r[base]
                size = 1 if w & 0x400000 else 4
                if w & 0x100000:
                    self.r[reg] = self.get(address, size)
                else:
                    self.put(address, self.r[reg], size, True)
                if w & 0x200000 or not w & 0x1000000:
                    self.r[base] = updated
                if reg == 15 and w & 0x100000:
                    nxt = self.r[15]
            elif w & 0x0E000090 == 0x00000090:
                need(w & 0x1400000 == 0x1400000 and not w & 0x200000, 'immediate halfword transfer')
                offset = ((w >> 4) & 0xF0) | (w & 15)
                address = self.r[(w >> 16) & 15] + (offset if w & 0x800000 else -offset)
                reg, kind = (w >> 12) & 15, (w >> 5) & 3
                if w & 0x100000:
                    value = self.get(address, 1 if kind == 2 else 2)
                    self.r[reg] = (signed(value, 8 if kind == 2 else 16) if kind in (2, 3) else value) & 0xFFFFFFFF
                else:
                    need(kind == 1, 'only STRH')
                    self.put(address, self.r[reg], 2, True)
            elif w & 0x0C000000 == 0:
                op, dest = (w >> 21) & 15, (w >> 12) & 15
                left, right = self.r[(w >> 16) & 15], self.shifted(w)
                if op in (2, 10): value = (left - right) & 0xFFFFFFFF
                elif op == 3: value = (right - left) & 0xFFFFFFFF
                elif op in (4, 11): value = (left + right) & 0xFFFFFFFF
                elif op in (0, 8): value = left & right
                elif op == 1: value = left ^ right
                elif op == 12: value = left | right
                elif op == 13: value = right
                elif op == 14: value = left & ~right
                elif op == 15: value = ~right & 0xFFFFFFFF
                else: raise ValueError('unreviewed ARM operation')
                if op in (8, 10, 11) or w & 0x100000:
                    flags = (value & 0x80000000) | (0x40000000 if value == 0 else 0)
                    if op in (2, 10):
                        flags |= (0x20000000 if left >= right else 0) | (((left ^ right) & (left ^ value) & 0x80000000) >> 3)
                        self.cpsr = (self.cpsr & 0x0FFFFFFF) | flags
                    elif op in (4, 11):
                        flags |= (0x20000000 if left + right > 0xFFFFFFFF else 0) | ((~(left ^ right) & (left ^ value) & 0x80000000) >> 3)
                        self.cpsr = (self.cpsr & 0x0FFFFFFF) | flags
                    else:
                        self.cpsr = (self.cpsr & 0x3FFFFFFF) | flags
                if op not in (8, 10, 11):
                    self.r[dest] = value & 0xFFFFFFFF
                    if dest == 15:
                        nxt = self.r[15]
            else:
                raise ValueError(f'unreviewed ARM instruction {pc:08X}:{w:08X}')
            pc = nxt
        raise ValueError('bounded actual ARM execution did not return')

def setup(rom, owner=True, mask=0, index=0, phase=None):
    m = Machine(rom, 3, 0xA0000010)
    for n in range(52):
        m.put(POOL + n * 0x118 + 0x10, 0, 2)
    if owner:
        header = POOL + index * 0x118
        m.put(header, PHASES[0] if phase is None else phase)
        m.put(header + 0x10, 2, 2)
        m.put(header + 0x18 + 0x52, mask, 2)
    return m

def source_order(before, after, gba, source):
    instructions = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[0x7738C6:0x7738DC], 0x7738C6))
    need([i.mnemonic + ' ' + i.op_str for i in instructions][:7] == [
        'xor ax, ax', 'mov es, ax', 'mov di, bx', 'shl di, 6',
        'add di, 0x800', 'mov cx, 0x40', 'rep stosw word ptr es:[di], ax'],
        'source physical clear address, length and zero data')
    for lo, hi in ((0x11D78, 0x11E54), (0x11F90, 0x12008),
                   (0x35227C, 0x352340), (0x35298C, 0x3529DC),
                   (0x37354C, 0x3735BC), (0xD1BBC, 0xD1C24)):
        need(before[lo:hi] == gba[lo:hi] == after[lo:hi], 'retained order owner ' + hex(lo))
    need(listing(after, 0x35298C, 24) == [
        'ldr r8, [pc, #0x40]', 'ldrh r1, [r8]', 'ldr sb, [pc, #0x3c]',
        'str r5, [sb, r1, lsl #2]', 'add sb, r1, #1', 'strh sb, [r8]'],
        'actor queues presentation rather than rendering')
    need((u(after, 0x3529D4), u(after, 0x3529D8), u(after, 0x3735B0), u(after, 0x3735B4)) ==
         (0x0300482A, 0x03004830, 0x0300482A, 0x03004830), 'actual append/drain same list')
    need(listing(after, 0x373560, 32) == [
        'ldr r1, [pc, #0x4c]', 'ldr r0, [r1], #4', 'stmdb sp!, {r0}',
        'stmdb sp!, {fp}', 'bl #0x8012c28', 'add sp, sp, #8',
        'subs r2, r2, #1', 'bgt #0x8373564'], 'actual ordered render drain')
    need(u(after, 0xD1BF0) == 0xE3A08A06 and branch(after, 0xD1BF8) == 0x08011AC4,
         'battle renderer task priority6000')
    need(u(after, 0xD1C1C) == 0x083734F0, 'retail renderer callback lineage')
    # Actor pool2 flags4820..4823 index16..19, FIRST pool3 flag4824 index20.
    priorities = struct.unpack_from('<26H', after, 0x3522FC)
    need(priorities[16:20] == (0x2C00,) * 4 and priorities[20] == 0x3000,
         'positive pool2/FIRST task priorities before6000')
    need(listing(after, 0x11FDC, 16) == [
        'ldr r8, [r4, #4]', 'cmp r1, r8', 'blo #0x8011ff0', 'mov r5, r4'],
        'unsigned ascending task insertion')
    need(listing(after, 0x11DE4, 20) == [
        'ldr r0, [r4, #4]', 'ldr r8, [r5, #4]', 'cmp r8, r0',
        'ldr r5, [r5, #0xc]', 'bhs #0x8011dfc'], 'scheduler follows ascending task links')
    need(listing(after, 0x35345C, 16) == [
        'ldr sb, [sp, #0x20]', 'cmp sb, #0', 'moveq r3, #0x49', 'movne r3, #0x6d'],
        'retained source companion preload tile base')
    need(source[0x743886:0x74388B] == bytes.fromhex('9A6E22FF4F'), 'source actual synchronous companion preload')
    need(listing(after, 0x353348, 12) == [
        'ldr r0, [sp, #0x1c]', 'lsl r0, r0, #5', 'mov r5, r0'],
        'actual preload R5 producer is a byte offset')
    need(listing(after, 0x353370, 20) == [
        'ldr r0, [pc, #0x140]', 'ldr r8, [pc, #0x140]',
        'sub r0, r0, r8', 'add r1, r1, r0', 'add r5, r5, r0'] and
        (u(after, 0x3534B8), u(after, 0x3534BC)) == (0x0860B000, 0x084A80F8),
        'actual evolved preload offset delta')
    return dict(append=0x08352998, consumer=0x08373570,
                actor_priorities=list(priorities[16:21]), renderer_priority=0x6000,
                late_preload_before_actual_draw=True)

def structural(before, after, gba):
    need(len(before) == len(after) == 0x800000, 'complete ROM extents')
    need(before[FIRST:LIMIT] == b'\xff' * (LIMIT - FIRST), 'entire reservation strictly FF')
    need((branch(after, HOOKS[0]), u(after, HOOKS[1]), branch(after, HOOKS[2])) ==
         (CAPTURE, RENDER, EXPIRE), 'actual three installed hooks')
    need(u(after, HOOKS[0]) >> 24 == 0xEB and u(after, HOOKS[2]) >> 24 == 0xEA,
         'capture linked, preload unlinked, preserving call contracts')
    inverse = bytearray(after)
    for lo, hi in ((0x6FE800, 0x6FE888), (0x6FE900, 0x6FE940),
                   (0x6FEA00, 0x6FEC88), (0x6FEE00, 0x6FEE7C)):
        inverse[lo:hi] = before[lo:hi]
    for at in HOOKS:
        inverse[at:at + 4] = before[at:at + 4]
    need(inverse == before, 'complete declared-write inverse and off-target preservation')
    need(after[0x12C58:0x12DD8] == gba[0x12C58:0x12DD8] and
         after[0x13C:0x1A0] == gba[0x13C:0x1A0] and u(after, 0x39C) == 0x08012C58,
         'unchanged boot DMA/copy source for original180byte IWRAM renderer')
    need(u(before, HOOKS[1]) == 0x03000204 and u(before, HOOKS[2]) == 0xE59D0020,
         'positive displaced original renderer entry and preload instruction')
    spec = importlib.util.spec_from_file_location('_static_companion_inbound', ROOT / 'tools/verify_shoot_caller_resident.py')
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    scanner.SPANS = ((FIRST, LIMIT),)
    need(not scanner.inbound(before), 'strict whole-reservation pointer/ARM/Thumb candidate ownership')
    return scanner

def resource_rows(rom):
    rows = []
    for group in GROUPS:
        for ident in range(15):
            p0 = u(rom, group + ident * 32) - BASE
            p1 = u(rom, group + ident * 32 + 4) - BASE
            table = u(rom, p0) - BASE
            n = (u(rom, table + 4) - BASE - table) // 8
            desc = u(rom, p0 + 4) - BASE
            need(0 < n <= 64 and h(rom, p0 + 14) == 8, 'static companion resource domain')
            need(u(rom, desc) % 32 == 0, 'whole companion payload')
            rows.append((p0, p1, table, n, desc))
    return rows

def fixture(rom, resource, layout=0, owner=True, mask=0, base=0x49,
            flags=0x2000, count=0, x=100, y=100, owner_index=0):
    p0, p1, table, layouts, desc = resource
    m = setup(rom, owner, mask, owner_index)
    for at, value in enumerate(rom[0x12C58:0x12DD8]):
        m.put(0x03000200 + at, value, 1)
    m.put(0x030012CA, count, 1)
    for off in range(1024):
        m.put(0x03001428 + off, 0xA5, 1)
    for off in range(128 * 32):
        m.put(0x02000000 + off, 0x5A, 1)
    for off in range(0x50):
        m.put(PRESENT + off, 0, 1)
    m.put(PRESENT, x & 65535, 2)
    m.put(PRESENT + 2, y & 65535, 2)
    m.put(PRESENT + 8, flags, 2)
    m.put(PRESENT + 0x10, 3, 2)
    m.put(PRESENT + 0x14, base, 2)
    m.put(PRESENT + 0x18, layout, 2)
    # An actual source-compatible frame pointer; static renderer ignores its tile index.
    event = u(rom, p1) - BASE
    commands = u(rom, event + 4)
    m.put(PRESENT + 0x20, commands)
    m.put(PRESENT + 0x44, BASE + p1)
    m.put(PRESENT + 0x48, BASE + p0)
    m.put(m.r[13], 0, 4)
    m.put(m.r[13] + 4, PRESENT, 4)
    return m

def buffer(m, address, length):
    return bytes(m.mem[address + i] for i in range(length))

def rendered(before, after, resource, bits=15, alias=False, **kwargs):
    old, new = fixture(before, resource, **kwargs), fixture(after, resource, **kwargs)
    if bits != 15:
        for m in (old, new):
            mask = m.get(SCENE + 0x52, 2)
            m.put(SCENE + 0x52, (mask & 255) | bits << 8, 2)
    if alias:
        for m in (old, new):
            for n, byte in enumerate(m.rom[resource[0]:resource[0] + 16]):
                m.put(0x0202F000 + n, byte, 1)
            m.put(PRESENT + 0x48, 0x0202F000)
    initial = new.r[:15]
    for m in (old, new):
        m.run(0x08012C28, {initial[14]}, max_steps=14000)
    need(new.r[:6] == old.r[:6] == initial[:6] and
         new.r[13:15] == old.r[13:15] == initial[13:15], 'dispatcher single-save/return and caller ABI')
    need(buffer(old, 0x03001428, 1024) == buffer(new, 0x03001428, 1024),
         'all OAM bytes preserved including flips/palettes/priority/index')
    need(old.mem[0x030012CA] == new.mem[0x030012CA], 'exact native dynamic tile count')
    return old, new

def owner_cases(after):
    count = 0
    for index, phase in itertools.product(range(52), PHASES):
        m = setup(after, True, 0xF49, index, phase)
        initial = m.r[:15]
        m.run(OWNER, {initial[14]}, max_steps=16000)
        need(m.r[0] == POOL + index * 0x118 + 0x18 and m.r[1:15] == initial[1:15],
             'owner actual52slot bound and all non-result registers')
        count += 1
    for status, phase in ((0, PHASES[0]), (1, PHASES[0]), (2, 0x085CD300), (2, 0x0834059C)):
        m = setup(after, False)
        m.put(POOL, phase)
        m.put(POOL + 0x10, status, 2)
        initial = m.r[:15]
        m.run(OWNER, {initial[14]}, max_steps=16000)
        need(m.r[0] == 0 and m.r[1:15] == initial[1:15], 'inactive/unrecognized phase excluded')
        count += 1
    # Slot53 is outside the actual native pool, even with a matching owner.
    m = setup(after, True, 0xF49, 52)
    initial = m.r[:15]
    m.run(OWNER, {initial[14]})
    need(m.r[0] == 0, 'owner scan excludes the first out-of-pool slot')
    return count + 1

def capture_cases(after):
    count = 0
    for bx in (*range(224, 290), 0, 65535, 0xFFFFFFFF):
        m = setup(after)
        m.put(0x0300133C, POOL)
        m.r[1] = bx
        initial = m.r[:15]
        stop = m.run(CAPTURE, {0x085CD920})
        expected = (0xF00 | (2 * bx - 448)) if 261 <= bx <= 288 else 0
        need(stop == 0x085CD920 and m.get(SCENE + 0x52, 2) == expected,
             'source common four-tile mask and exact clear tail')
        need(m.r[:15] == initial, 'capture forwards all original arguments/SP/LR')
        need([(a, v, n) for a, v, n in m.writes if a < 0x03007000] ==
             [(SCENE + 0x52, expected, 2)], 'only dead scene case halfword written')
        count += 1
    return count

def renderer_cases(before, after):
    rows = resource_rows(after)
    count, blanked = 0, 0
    for resource in rows:
        p0, p1, table, layouts, desc = resource
        for layout in range(layouts):
            # All original layouts, all28scoped clear positions; retained record21 has9.
            old, new = rendered(before, after, resource, layout=layout, owner=False)
            need(buffer(old, 0x02000000, 4096) == buffer(new, 0x02000000, 4096),
                 'inactive owner exact entire staging')
            count += 1
            for bx in range(261, 289):
                first = 2 * bx - 448
                old, new = rendered(before, after, resource, layout=layout, mask=0xF00 | first)
                parts = u(after, table + layout * 8 + 4) - BASE
                n = u(after, table + layout * 8)
                expected = bytearray(buffer(old, 0x02000000, 4096))
                for part in range(n):
                    tile = after[parts + part * 4]
                    if first <= 0x49 + tile <= first + 3:
                        expected[part * 32:(part + 1) * 32] = bytes(32)
                        blanked += 1
                need(buffer(new, 0x02000000, 4096) == expected,
                     'actual source logical tiles only substitute zero pixels')
                count += 1
    sample = rows[6]
    need(sample[3] == 9, 'record21 retains all nine native layouts')
    for base, flags, owner, mask, start, x, y in (
        (0x6D, 0x2000, True, 0xF49, 0, 100, 100),
        (0x49, 0x2002, True, 0xF49, 0, 100, 100),
        (0x49, 0x2000, True, 0, 0, 100, 100),
        (0x49, 0x2000, True, 0xF49, 127, 100, 100),
        (0x49, 0x2000, True, 0xF49, 0, -100, -100),
    ):
        if flags & 2:
            # The real frame's descriptor index0 makes an indexed no-mask fixture bounded.
            event = u(after, sample[1]) - BASE
            cmd = u(after, event + 4) - BASE
            need(h(after, cmd + 4) == 0, 'indexed exclusion fixture uses owned descriptor0')
        old, new = rendered(before, after, sample, base=base, flags=flags, owner=owner,
                            mask=mask, count=start, x=x, y=y)
        need(buffer(old, 0x02000000, 4096) == buffer(new, 0x02000000, 4096),
             'excluded/empty/clipped/at-capacity renderer path unchanged')
        count += 1
    for flags, start, bits, alias in itertools.product((0, 0x2000, 0x6000, 0xA000, 0xE000),
                                                     (0, 7), (1, 2, 4, 8, 5, 10), (False, True)):
        old, new = rendered(before, after, sample, flags=flags, count=start,
                            mask=0xF49, bits=bits, alias=alias, layout=3)
        expected = bytearray(buffer(old, 0x02000000, 4096))
        parts = u(after, sample[2] + 3 * 8 + 4) - BASE
        for part in range(u(after, sample[2] + 3 * 8)):
            tile = after[parts + 4 * part]
            if not alias and tile < 4 and bits & (1 << tile):
                expected[(start + part) * 32:(start + part + 1) * 32] = bytes(32)
        need(buffer(new, 0x02000000, 4096) == expected,
             'sparse live bits/facing/native count/exact P0 identity')
        count += 1
    # Flag1 selects the separate retained background/DMA renderer, not this clone.
    old, new = fixture(before, sample, flags=0x2001), fixture(after, sample, flags=0x2001)
    for m in (old, new):
        m.run(0x08012C28, {0x08012DCC})
    need(old.r[:15] == new.r[:15] and old.writes == new.writes and
         after[0x12DCC:0x13088] == before[0x12DCC:0x13088], 'flag1 native dispatcher prefix and target retained')
    return dict(actual_ARM_cases=count, source_logical_blank_parts=blanked,
                resources=30, layouts=sum(r[3] for r in rows), background_dispatch_prefix_cases=1)

def expiration_cases(after):
    count = 0
    for resource in resource_rows(after):
        p0, p1, table, layouts, desc = resource
        length = u(after, desc) // 32
        for base, first, bits, nzcv in itertools.product((0x49, 0x6D), (72, 73, 74, 98, 105, 108, 109, 128), (0, 1, 5, 15), range(16)):
            mask = first | bits << 8
            m = setup(after, True, mask)
            preload_producer(m, resource, base)
            m.cpsr = (nzcv << 28) | 0xD3
            m.put(m.r[13] + 0x20, 0x76543210)
            initial, flags = m.r[:15], m.cpsr
            m.run(0x0835346C, {0x08353470}, max_steps=16000)
            expected = mask
            for bit in range(4):
                if base <= first + bit < base + length:
                    expected &= ~(0x100 << bit)
            need(m.get(SCENE + 0x52, 2) == expected, 'only actual preload interval expires')
            initial[0] = 0x76543210
            need(m.r[:15] == initial and m.cpsr == flags,
                 'preload all registers/flags restored and displaced stack load exact')
            need([(a, v, n) for a, v, n in m.writes if a < 0x03007000] ==
                 [(SCENE + 0x52, expected, 2)], 'preload only owned mask halfword changes')
            count += 1
    return count


def preload_producer(m, resource, base):
    """Execute the retained real constructor offset/base producers, not a RAM record."""
    rows = resource_rows(m.rom)
    ordinal = rows.index(resource)
    m.put(m.r[13] + 0x1C, ordinal % 15)
    m.run(0x08353348, {0x08353354})
    if ordinal >= 15:
        m.r[1] = 0
        m.run(0x08353370, {0x08353384})
    need(m.r[5] == ordinal % 15 * 32 +
         (0x60B000 - 0x4A80F8 if ordinal >= 15 else 0), 'real R5 byte-offset fixture')
    need(u(m.rom, 0x4A82D8 + m.r[5]) == BASE + resource[0],
         'real offset resolves actual companion descriptor')
    m.put(m.r[13] + 0x20, int(base == 0x6D))
    m.run(0x0835345C, {0x0835346C})
    need(m.r[3] == base, 'real side-dependent preload base')


def same_frame_cases(before, after):
    count = 0
    for resource, side, reload in itertools.product(resource_rows(after), (0x49, 0x6D), (False, True)):
        m = fixture(after, resource, mask=0xF49)
        pristine = fixture(before, resource, mask=0xF49)
        m.put(0x0300482A, 0, 2)
        m.r[5] = PRESENT
        original_pixels = buffer(m, 0x02000000, 4096)
        m.run(0x0835298C, {0x083529A4})
        need(m.get(0x0300482A, 2) == 1 and m.get(0x03004830) == PRESENT and
             buffer(m, 0x02000000, 4096) == original_pixels,
             'actual companion callback enqueues without rendering')
        if reload:
            preload_producer(m, resource, side)
            m.run(0x0835346C, {0x08353470})
        m.run(0x0837354C, {0x08373580})
        pristine.run(0x08012C28, {pristine.r[14]})
        expected = bytearray(buffer(pristine, 0x02000000, 4096))
        if not reload or side != 0x49:
            parts = u(after, resource[2] + 4) - BASE
            for part in range(u(after, resource[2])):
                if after[parts + part * 4] < 4:
                    expected[part * 32:(part + 1) * 32] = bytes(32)
        need(buffer(m, 0x02000000, 4096) == expected and
             buffer(m, 0x03001428, 1024) == buffer(pristine, 0x03001428, 1024),
             'actual queued draw sees same-frame side0 reload, not side1 reload')
        count += 1
    return count


def mutation_checks(before, after, gba, source, scanner):
    rejected = []

    def reject(name, check):
        try:
            check()
        except (ValueError, KeyError, IndexError, struct.error):
            rejected.append(name)
        else:
            raise ValueError('negative control accepted: ' + name)

    def changed(at, value):
        bad = bytearray(after)
        struct.pack_into('<I', bad, at, value)
        return bytes(bad)

    for at, word, name, check in (
        (0x6FE808, 0xE3A01033, 'owner loses final native slot', owner_cases),
        (0x6FE85C, PHASES[0] + 4, 'wrong terminal phase owner', owner_cases),
        (0x6FE91C, 0xE3510F47, 'clear upper bound becomes284', capture_cases),
        (0x6FE928, 0xE2422D06, 'wrong physical-to-logical tile subtraction', capture_cases),
    ):
        reject(name, lambda at=at, word=word, check=check: check(changed(at, word)))

    def pixels(blob):
        resource = resource_rows(after)[8]
        old, new = rendered(before, blob, resource, mask=0xF49, bits=5)
        expected = bytearray(buffer(old, 0x02000000, 4096))
        parts = u(after, resource[2] + 4) - BASE
        hits = 0
        for part in range(u(after, resource[2])):
            tile = after[parts + part * 4]
            if tile < 4 and 5 & (1 << tile):
                expected[part * 32:(part + 1) * 32] = bytes(32)
                hits += 1
        need(hits > 0 and expected != buffer(old, 0x02000000, 4096), 'positive nonzero pixel oracle')
        need(buffer(new, 0x02000000, 4096) == expected, 'semantic blank pixel oracle')

    pixels(after)
    for at, word, name in (
        (0x6FEA0C, 0xE350004A, 'wrong renderer fixed base'),
        (0x6FEB54, 0xE283804A, 'wrong per-part logical tile'),
        (0x6FEB6C, 0xE1190009, 'ignores individual live blank bit'),
        (0x6FEBF0, 1, 'blank ROM tile contains opaque pixel'),
    ):
        reject(name, lambda at=at, word=word: pixels(changed(at, word)))

    def expired(blob):
        resource = resource_rows(after)[0]
        m = setup(blob, mask=0xF49)
        preload_producer(m, resource, 0x49)
        m.cpsr = 0xA00000D3
        m.put(m.r[13] + 0x20, 0x76543210)
        initial = m.r[:15]
        m.run(0x0835346C, {0x08353470})
        initial[0] = 0x76543210
        need(m.get(SCENE + 0x52, 2) == 0x49 and m.r[:15] == initial and m.cpsr == 0xA00000D3,
             'preload real record offset, upload lifetime and full ABI')

    expired(after)
    reject('legacy preload treats R5 byte offset as a pointer',
           lambda: expired(changed(0x6FEE18, 0xE59541E0)))
    # Locate operations by decoded semantics so this check tolerates relocated literals.
    ops = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(after[0x6FEE00:0x6FEE80], EXPIRE))
    for op, replacement, name in (
        ('biclo r1, r1, r6', 0xE1A01001, 'preload fails to expire overlapping blank'),
        ('msr apsr_nzcvq, ip', 0xE1A0C00C, 'preload loses original condition flags'),
        ('ldr r0, [sp, #0x20]', 0xE59D001C, 'wrong displaced stack argument'),
    ):
        addresses = [i.address - BASE for i in ops if i.mnemonic + ' ' + i.op_str == op]
        need(len(addresses) == 1, 'unique actual operation for semantic mutation: ' + op)
        reject(name, lambda at=addresses[0], replacement=replacement: expired(changed(at, replacement)))
    reject('same-frame reload omitted', lambda: same_frame_cases(before, changed(0x35346C, 0xE1A00000)))
    bad = bytearray(after)
    bad[0x100] ^= 1
    reject('undeclared off-target ROM write', lambda: structural(before, bad, gba))
    bad = bytearray(after)
    bad[0x6FE890] ^= 1
    reject('undeclared write in unused reservation padding', lambda: structural(before, bad, gba))
    bad = bytearray(source)
    bad[0x7738D4] ^= 1
    reject('source physical clear length changed', lambda: source_order(before, after, gba, bad))
    # Exercise each inbound family locally using the same whole-ROM scanner.
    for kind, origin, payload in (
        ('unaligned mirrored pointer', 0, b'\x00' + struct.pack('<I', 0x0A000000 + FIRST) + bytes(3)),
        ('ARM branch', FIRST - 0x100, struct.pack('<I', 0xEA00003E)),
        ('Thumb branch', FIRST - 0x100, struct.pack('<H', 0xE07E)),
    ):
        need(scanner.inbound(payload, origin), 'strict inbound negative detected: ' + kind)
        rejected.append(kind)
    return rejected

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'gba', 'source', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    need(all(getattr(a, name).suffix.lower() not in ('.sav', '.state') for name in vars(a)), 'save/state paths forbidden')
    need(a.output.suffix.lower() == '.json' and
         all(a.output.resolve() != getattr(a, name).resolve() for name in ('before', 'after', 'gba', 'source')),
         'report must be a distinct JSON path')
    before, after, gba, source = [getattr(a, name).read_bytes() for name in ('before', 'after', 'gba', 'source')]
    need(tuple(map(sha, (before, gba, source))) == (BEFORE, GBA, SOURCE), 'exact predecessor and original input identities')
    scanner = structural(before, after, gba)
    order = source_order(before, after, gba, source)
    report = dict(status='PASS', before_sha256=sha(before), after_sha256=sha(after),
                  verifier_sha256=sha(Path(__file__).read_bytes()),
                  ordering=order, owner_cases=owner_cases(after), capture_cases=capture_cases(after),
                  renderer=renderer_cases(before, after), expiration_cases=expiration_cases(after),
                  same_frame_cases=same_frame_cases(before, after),
                  semantic_negatives=mutation_checks(before, after, gba, source, scanner),
                  strict_whole_reservation_inbound=True, full_inverse=True,
                  external_entry_authorized=False, complete_terminal_clear=False,
                  dependencies={name: sha((ROOT / 'tools' / name).read_bytes()) for name in (
                      'verify_shoot_attack_dispatch.py', 'verify_shoot_caller_resident.py')})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(a.output.read_bytes()))

if __name__ == '__main__':
    main()
