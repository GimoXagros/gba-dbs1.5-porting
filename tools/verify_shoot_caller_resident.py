#!/usr/bin/env python3
"""Independent source/actual-code verifier for the two resident Shoot callers.

No builder imports, game execution, emulator, save input, or guest writes.
The bounded ARM interpreter executes the inserted code and retained decision/
assignment bodies; only the existing RNG service is modeled at its ABI.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

BASE = 0x08000000
SPANS = ((0x5C6500, 0x5C652C), (0x6FC300, 0x6FC334))
IDENTITIES = (
    "A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F",
    "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
)
DEPENDENCIES = (
    (0x5C6000, 180, "50B090CE223B5B5321F88FD96456B0EFAD263B114E4ED12F7AB77CBFDD4830CF"),
    (0x5C6200, 76, "75240FDF5E47873B21990DDC7568541B14FC458AE9B7D4040099FDDE9A962848"),
    (0x5C6400, 64, "DDFDCEFE5A45221AF27E17F729FD8FCC167418FADBF362F52D5CF4995BD18F94"),
    (0x5CB000, 6432, "50F925198CD5BF6AA23DDC8A94778B24A085BCB292B1B7EC856268E4ACA982C3"),
    (0x5CD000, 160, "488AD379AB04A0CDD47883AEE8C5D87252E4235C98CBC6A23F423558CF5FBFE8"),
    (0x34059C, 600, "B0088F9E6A47A0CEC0B5D6F10473FDB75E9D2EAB573CC8BC51D647583C0D5116"),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def u32(blob, at):
    return struct.unpack_from("<I", blob, at)[0]


def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def rotate(value, amount):
    return ((value >> amount) | (value << ((32 - amount) & 31))) & 0xFFFFFFFF


def decoded(blob, at, size, arch=CS_ARCH_ARM, mode=CS_MODE_ARM):
    rows = list(Cs(arch, mode).disasm(blob[at:at + size], BASE + at if arch == CS_ARCH_ARM else at))
    need(sum(i.size for i in rows) == size, "complete bounded disassembly")
    return [f"{i.mnemonic} {i.op_str}".strip() for i in rows]


def source_contract(gba, wsc, candidate):
    need(wsc[0x772553:0x77256F] == bytes.fromhex(
        "1E57BF00108EDFBF4E0033C08A450E5F1F3D0B0075069A5017F071CB"), "source stage read/branch/call")
    source_rows = decoded(wsc, 0x772553, 28, CS_ARCH_X86, CS_MODE_16)
    need(source_rows[-4:] == ["cmp ax, 0xb", "jne 0x77256f", "lcall 0x71f0, 0x1750", "retf"],
         "source stage11 terminal call and non11 continuation")
    need(sha(wsc[0x74A208:0x74A345]) == "25FB35105253832BDC2377094FE7EDFB3B75F459026B4D4473913C7EE773CEF4",
         "source controller including complete dispatch table and assignment tails")
    targets = struct.unpack_from("<64H", wsc, 0x74A26F)
    tokens = {0x99EF: 0, 0x99F1: 1, 0x9A0E: 2, 0x9A1B: 3}
    need(set(targets) <= tokens.keys(), "source dispatch targets resolved")
    source_table = bytes(tokens[t] for t in targets)
    need(candidate[0x5C6400:0x5C6440] == source_table, "all64 source table entries inverse")
    # Retail stage dispatch reads stage from mode/config base+0E. Its literal
    # is independently resolved rather than accepting a manifest owner string.
    need(decoded(gba, 0xB9E48, 12) == ["ldr r8, [pc, #0xd8]", "ldrb sb, [r8, #0xe]", "cmp sb, #7"],
         "retail stage producer/consumer")
    need(u32(gba, 0xB9E48 + 8 + 0xD8) + 14 == 0x0300231E, "positive native stage owner")
    need(decoded(gba, 0x33FD04, 4) == ["ldr r8, [pc, #0xa8]"] and
         u32(gba, 0x33FD04 + 8 + 0xA8) == 0x0834059C, "original case5 callback lineage")
    need(candidate[0x34059C:0x3407F4] == gba[0x34059C:0x3407F4], "ordinary callback retained retail")
    need(candidate[0x33FCCC:0x33FDC0] == gba[0x33FCCC:0x33FDC0], "native case5 allocation retained")
    return source_table


def code_contract(data):
    saved = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
    need(decoded(data, 0x5C6500, 32) == ["push " + saved, "bl #0x85c6000", "ldr r1, [pc, #0x10]",
        "ldr r2, [pc, #0x10]", "ldr r3, [pc, #0x10]", "bl #0x85c6200", "pop " + saved, "bx lr"],
        "controller same-invocation complete code")
    need(struct.unpack_from("<3I", data, 0x5C6520) == (0x085CB000, 0x085CB970, 0x085CBD80), "three actual lower entries")
    need(decoded(data, 0x6FC300, 48) == ["push {r0, ip, lr}", "mrs ip, apsr", "ldr r0, [pc, #0x20]",
        "ldrb r0, [r0]", "cmp r0, #0xb", "beq #0x86fc324", "msr apsr_nzcvq, ip", "pop {r0, ip, lr}",
        "b #0x834059c", "msr apsr_nzcvq, ip", "pop {r0, ip, lr}", "b #0x85cd000"], "complete terminal router")
    need(u32(data, 0x6FC330) == 0x0300231E, "stage byte address")
    need(u32(data, 0x6FC304) == 0xE10FC000 and
         all(u32(data, a) == 0xE128F00C for a in (0x6FC318, 0x6FC324)), "ARMv4 CPSR exact encodings")


class Arm:
    """Small strict interpreter, limited to instructions actually under review."""

    def __init__(self, rom, seed=0, flags=0x10, rng=0):
        self.rom, self.mem, self.writes, self.reads, self.calls = rom, {}, [], [], []
        self.r = [((0x13579BDF * (i + 1)) ^ (seed * 0x2468ACE1)) & 0xFFFFFFFF for i in range(16)]
        self.r[13], self.r[14] = 0x03007C00 - 4 * (seed % 32), 0x08001234
        self.cpsr, self.rng, self.rng_calls = flags, rng, 0

    def put(self, address, value, size=4, log=False):
        for i in range(size):
            self.mem[address + i] = (value >> (8 * i)) & 255
        if log:
            self.writes.append((address, value & ((1 << (8 * size)) - 1), size))

    def get(self, address, size=4):
        if BASE <= address and address + size <= BASE + len(self.rom):
            return int.from_bytes(self.rom[address - BASE:address - BASE + size], "little")
        need(all(address + i in self.mem for i in range(size)), f"uninitialized read {address:08X}/{size}")
        self.reads.append((address, size))
        return sum(self.mem[address + i] << (8 * i) for i in range(size))

    def operand(self, word):
        if word & 0x02000000:
            return rotate(word & 255, ((word >> 8) & 15) * 2)
        need(not word & 0x10, "register shift by immediate only")
        kind, count = (word >> 5) & 3, (word >> 7) & 31
        value = self.r[word & 15]
        need(kind == 0, "reviewed LSL operand only")
        return (value << count) & 0xFFFFFFFF

    def condition(self, cond):
        n, z, c, v = ((self.cpsr >> i) & 1 for i in (31, 30, 29, 28))
        return (z, not z, c, not c, n, not n, v, not v, c and not z,
                not c or z, n == v, n != v, not z and n == v, z or n != v, True, False)[cond]

    def run(self, start, stops):
        pc = start
        for _ in range(160):
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
                need(w & 0x0FFF0000 in (0x092D0000, 0x08BD0000), "reviewed PUSH/POP only")
                regs = [i for i in range(16) if w & (1 << i)]
                load = bool(w & 0x00100000)
                address = self.r[13] if load else self.r[13] - 4 * len(regs)
                for i, reg in enumerate(regs):
                    if load:
                        self.r[reg] = self.get(address + i * 4)
                    else:
                        self.put(address + i * 4, self.r[reg], log=True)
                self.r[13] += (1 if load else -1) * 4 * len(regs)
            elif w & 0x0E000000 == 0x0A000000:
                nxt = pc + 8 + signed(w & 0xFFFFFF, 24) * 4
                if w & 0x01000000:
                    self.r[14] = pc + 4
                    self.calls.append((pc, nxt, tuple(self.r[:5])))
                    if nxt == 0x08012600:
                        self.rng_calls += 1
                        self.r[0], self.r[8], self.r[9] = self.rng, 0xDEADBEEF, 0xBAD0CAFE
                        nxt = pc + 4
            elif w & 0x0C000000 == 0x04000000:
                need(w & 0x01000000 and not w & 0x00200000, "preindexed no-writeback transfer")
                offset = self.r[w & 15] if w & 0x02000000 else w & 0xFFF
                address = self.r[(w >> 16) & 15] + (offset if w & 0x00800000 else -offset)
                reg, size = (w >> 12) & 15, 1 if w & 0x00400000 else 4
                if w & 0x00100000:
                    self.r[reg] = self.get(address, size)
                else:
                    self.put(address, self.r[reg], size, True)
            elif w & 0x0E000090 == 0x00000090:
                need(w & 0x01400000 == 0x01400000 and not w & 0x00200000, "immediate halfword transfer")
                offset = ((w >> 4) & 0xF0) | (w & 15)
                address = self.r[(w >> 16) & 15] + (offset if w & 0x00800000 else -offset)
                reg, kind = (w >> 12) & 15, (w >> 5) & 3
                if w & 0x00100000:
                    value = self.get(address, 1 if kind == 2 else 2)
                    self.r[reg] = (signed(value, 8) if kind == 2 else value) & 0xFFFFFFFF
                else:
                    need(kind == 1, "STRH only")
                    self.put(address, self.r[reg], 2, True)
            elif w & 0x0C000000 == 0:
                op, dest = (w >> 21) & 15, (w >> 12) & 15
                left, right = self.r[(w >> 16) & 15], self.operand(w)
                if op in (8, 10):
                    result = (left & right) if op == 8 else (left - right) & 0xFFFFFFFF
                    flags = (result & 0x80000000) | (0x40000000 if result == 0 else 0)
                    if op == 10:
                        flags |= (0x20000000 if left >= right else 0) | (((left ^ right) & (left ^ result) & 0x80000000) >> 3)
                        self.cpsr = (self.cpsr & 0x0FFFFFFF) | flags
                    else:
                        self.cpsr = (self.cpsr & 0x3FFFFFFF) | flags
                else:
                    need(op in (0, 4, 13) and not w & 0x00100000, "reviewed AND/ADD/MOV only")
                    self.r[dest] = ((left & right) if op == 0 else left + right if op == 4 else right) & 0xFFFFFFFF
            else:
                raise ValueError(f"unsupported ARM instruction {pc:08X}:{w:08X}")
            pc = nxt
        raise ValueError("bounded ARM execution did not return/tail-call")


def execute_router(data):
    count = 0
    for stage, nzcv, control in itertools.product(range(256), range(16), (0x10, 0xD3)):
        arm = Arm(data, stage + nzcv, (nzcv << 28) | control)
        arm.put(0x0300231E, stage, 1)
        # Adjacent bytes deliberately nonzero: a halfword/word read must fail.
        arm.put(0x0300231F, 0xFF, 1)
        initial, flags = arm.r[:15], arm.cpsr
        end = arm.run(0x086FC300, {0x0834059C, 0x085CD000})
        need(end == (0x085CD000 if stage == 11 else 0x0834059C), "executed stage destination")
        need(arm.r[:15] == initial and arm.cpsr == flags, "router register/SP/LR/CPSR identity")
        need([(a, s) for a, s in arm.reads if a < 0x03007000] == [(0x0300231E, 1)], "only actual stage byte read")
        need(not arm.calls and all(initial[13] - 12 <= a < initial[13] for a, _, _ in arm.writes), "router stack-only effects/tail call")
        count += 1
    return count


def controller_case(data, table, forced, x, y, difficulty, random_value, flag, alias=False, hp=0xFEDC):
    arm = Arm(data, random_value + difficulty, flags=0xA0000010, rng=random_value)
    current, target = 0x02011000, 0x02012000
    linked = current if alias else 0x02013000
    arm.r[4] = current
    arm.put(current, 0xDEAD1234)
    arm.put(current + 0x18, target)
    arm.put(current + 0x28, linked)
    arm.put(current + 0x64, hp, 2)
    arm.put(current + 0x76, forced, 2)
    arm.put(current + 0xA2, 0x4321, 2)
    if not alias:
        arm.put(linked, 0xABCD4321)
    arm.put(target + 0x34, x, 2)
    arm.put(target + 0x36, y, 2)
    arm.put(0x0300231F, difficulty, 1)
    arm.put(0x0300450A, flag, 2)
    original, initial_mem = arm.r[:15], arm.mem.copy()
    if forced:
        action = 2
    elif 0x500 <= x <= 0x900:
        action = 1 if random_value & 3 == 0 else 3 if y < 0xC00 else 2
    else:
        row = min(3, max(0, signed(difficulty, 8)))
        action = table[row * 16 + (random_value & 15)]
    if action == 3 and flag & 0x40:
        action = 2
    effects = {0: [], 1: [(current, 0x085CB000, 4), (current + 0xA2, hp, 2), (linked, 0x085CB970, 4)],
               2: [(linked, 0x085CBD80, 4)], 3: [(linked, 0x085BA800, 4)]}[action]
    arm.run(0x085C6500, {original[14]})
    need(arm.r[:15] == original, "controller all registers/SP/LR restored")
    need(arm.rng_calls == (0 if forced else 1), "actual controller RNG call population")
    need([target for _, target, _ in arm.calls if target != 0x08012600] == [0x085C6000, 0x085C6200], "SELECT then APPLY only")
    need(all(regs[4] == current for _, _, regs in arm.calls), "same current r4 for all calls")
    apply_args = arm.calls[-1][2]
    need(apply_args[:4] == (action, 0x085CB000, 0x085CB970, 0x085CBD80), "real APPLY arguments")
    actual = [(a, v, s) for a, v, s in arm.writes if not 0x03007000 <= a < 0x03008000]
    need(actual == effects, "source-order exact controller write set")
    for a, value, size in effects:
        for i in range(size):
            initial_mem[a + i] = (value >> (8 * i)) & 255
    need(all(arm.mem[a] == value for a, value in initial_mem.items()), "no adjacent state corruption")
    return action


def execute_controller(data, table):
    count, actions = 0, set()
    # All difficulty bytes/low RNG bits, signed/clamp partitions, exact X/Y
    # branch endpoints, both guard bits and no-RNG path; correlated cycling
    # covers every decision partition without a redundant Cartesian explosion.
    for d, random_value, flag in itertools.product(range(256), range(16), (0, 0x40)):
        actions.add(controller_case(data, table, 0, 0x4FF, 0, d, random_value, flag))
        count += 1
    for forced, x, y, random_value, flag, alias, hp in itertools.product(
            (0, 1), (0, 0x4FF, 0x500, 0x501, 0x8FF, 0x900, 0x901, 0xFFFF),
            (0xBFF, 0xC00), (0, 1, 0xFFFF000F), (0, 0x40), (False, True), (0, 0xFFFF)):
        actions.add(controller_case(data, table, forced, x, y, 3, random_value, flag, alias, hp))
        count += 1
    need(actions == {0, 1, 2, 3}, "all four actual actions executed")
    return count


def inbound(data, origin=0):
    """Independent conservative references: no data/interior exemptions."""
    matches = []

    def consider(kind, at, value):
        if 0x08000000 <= value < 0x0E000000:
            raw = value & 0x01FFFFFF
            if any(start <= raw < end for start, end in SPANS):
                matches.append((kind, origin + at, value))

    for alignment in range(4):
        stop = len(data) - (len(data) - alignment) % 4
        for i, (word,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            consider("pointer", alignment + 4 * i, word)
    for i, (word,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at = 4 * i
        pc = BASE + origin + at + 8
        if word & 0x0E000000 == 0x0A000000:
            consider("ARM branch", at, pc + signed(word & 0xFFFFFF, 24) * 4)
        if (word >> 16) & 15 == 15 and word & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            consider("ARM literal", at, pc + (1 if word & 0x800000 else -1) * (word & 0xFFF))
        if word & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            immediate = rotate(word & 255, ((word >> 8) & 15) * 2)
            consider("ARM ADR", at, pc + (immediate if (word >> 21) & 15 == 4 else -immediate))
    for at in range(0, len(data) - 1, 2):
        half = int.from_bytes(data[at:at + 2], "little")
        pc = BASE + origin + at + 4
        if half & 0xF800 in (0x4800, 0xA000):
            consider("Thumb literal/ADR", at, (pc & ~3) + (half & 255) * 4)
        if half & 0xF800 == 0xE000:
            consider("Thumb B", at, pc + signed(half & 0x7FF, 11) * 2)
        if half & 0xF000 == 0xD000 and (half >> 8) & 15 < 14:
            consider("Thumb conditional", at, pc + signed(half & 255, 8) * 2)
        if half & 0xF800 == 0xF000 and at + 4 <= len(data):
            tail = int.from_bytes(data[at + 2:at + 4], "little")
            if tail & 0xF800 in (0xF800, 0xE800):
                destination = pc + (signed(half & 0x7FF, 11) << 12) + ((tail & 0x7FF) << 1)
                consider("Thumb BL/BLX", at, destination & ~3 if tail & 0xF800 == 0xE800 else destination)
    return matches


def mutation_checks(after, table, gba, wsc):
    rejected = []

    def reject(name, check):
        try:
            check()
        except (ValueError, KeyError, IndexError):
            rejected.append(name)
        else:
            raise ValueError("negative control accepted: " + name)

    for at, word, name in ((0x5C6504, 0xE1A00000, "missing SELECT"),
            (0x5C6514, 0xE1A00000, "missing APPLY"), (0x5C6524, 0x085CBD80, "wrong lower family"),
            (0x5C6518, 0xE8BD5FEF, "lost current-r4 restore")):
        bad = bytearray(after)
        struct.pack_into("<I", bad, at, word)
        reject(name, lambda: controller_case(bad, table, 0, 0x500, 0, 3, 0, 0))
    for at, word, name in ((0x6FC30C, 0xE1D000B0, "stage halfword read"),
            (0x6FC310, 0xE3500007, "wrong stage comparison"), (0x6FC314, 0x1A000003, "reversed branch"),
            (0x6FC318, 0xE1A00000, "ordinary flags lost"), (0x6FC324, 0xE1A00000, "terminal flags lost"),
            (0x6FC320, 0xEA000000, "ordinary tail destination"), (0x6FC32C, 0xEA000000, "terminal tail destination"),
            (0x6FC330, 0x0300231F, "wrong stage owner")):
        bad = bytearray(after)
        struct.pack_into("<I", bad, at, word)
        reject(name, lambda: execute_router(bad))
    bad = bytearray(wsc)
    bad[0x772565] ^= 1
    reject("source stage predicate", lambda: source_contract(gba, bad, after))
    bad = bytearray(after)
    bad[0x5C6400] ^= 1
    reject("source table inverse", lambda: source_contract(gba, wsc, bad))
    # Inject each reference form into a small positioned ROM window. These
    # bypass identity guards and exercise the census itself directly.
    for mirror in (BASE, 0x0A000000, 0x0C000000):
        for alignment in range(4):
            fixture = bytearray(b"\xff" * 16)
            struct.pack_into("<I", fixture, alignment, mirror + SPANS[0][0] + 3)
            need(any(row[0] == "pointer" for row in inbound(fixture, 0x1000)), "pointer injection detection")
            rejected.append(f"ownership pointer {mirror:08X} alignment{alignment}")
    forms = (("ARM branch", struct.pack("<I", 0xEA000000), 0x5C6500 - 8),
             ("ARM literal", struct.pack("<I", 0xE59F0000), 0x5C6500 - 8),
             ("ARM ADR", struct.pack("<I", 0xE28F0000), 0x5C6500 - 8),
             ("Thumb literal/ADR", struct.pack("<H", 0x4800), 0x5C6500 - 4),
             ("Thumb literal/ADR", struct.pack("<H", 0xA000), 0x5C6500 - 4),
             ("Thumb B", struct.pack("<H", 0xE000), 0x5C6500 - 4),
             ("Thumb conditional", struct.pack("<H", 0xD000), 0x5C6500 - 4),
             ("Thumb BL/BLX", struct.pack("<HH", 0xF000, 0xF800), 0x5C6500 - 4),
             ("Thumb BL/BLX", struct.pack("<HH", 0xF000, 0xE800), 0x5C6500 - 4))
    for index, (kind, fixture, origin) in enumerate(forms):
        need(any(row[0] == kind for row in inbound(fixture, origin)), "reference form injection " + kind)
        rejected.append(f"ownership instruction{index} {kind}")
    return rejected


def verify(before, after, gba, wsc, manifest):
    need(tuple(map(sha, (before, gba, wsc))) == IDENTITIES, "three exact input identities")
    need(len(after) == len(before), "complete ROM size")
    table = source_contract(gba, wsc, after)
    for at, size, digest in DEPENDENCIES:
        need(sha(before[at:at + size]) == digest and after[at:at + size] == before[at:at + size], "retained dependency " + hex(at))
    code_contract(after)
    need(before[0x5C0A00:0x5C0A04] == after[0x5C0A00:0x5C0A04] == bytes.fromhex("1EFF2FE1"), "controller boundary still closed")
    restored = bytearray(after)
    for start, end in SPANS:
        need(before[start:end] == b"\xff" * (end - start), "actual reservation FF")
        restored[start:end] = before[start:end]
    need(restored == before, "full ROM inverse outside only96 declared bytes")
    references = inbound(before)
    need(not references, "strict predecessor ownership " + repr(references[:10]))
    router_cases = execute_router(after)
    controller_cases = execute_controller(after, table)
    negatives = mutation_checks(after, table, gba, wsc)
    placements = [{"offset": s, "bytes": e - s, "sha256": sha(after[s:e])} for s, e in SPANS]
    changed = sum(x != y for x, y in zip(before, after, strict=True))
    # Manifest is cross-checked last, after deriving the output from source,
    # actual bytes, execution and ownership. No manifest assertion is an oracle.
    need(manifest["kind"] == "shoot-caller-resident" and manifest["status"] == "PASS", "manifest identity")
    need(manifest["input_sha256"] == sha(before) and manifest["output_sha256"] == sha(after), "manifest ROM digests")
    need(manifest["source_sha256"] == sha(wsc) and manifest["gba_sha256"] == sha(gba), "manifest original digests")
    need(manifest["placements"] == placements and manifest["declared_bytes"] == 96 and manifest["changed_bytes"] == changed,
         "manifest independently derived allocations")
    need(manifest["whole_ROM_inverse"] is True and manifest["external_hooks_changed"] is False and
         manifest["controller_boundary_changed"] is False and manifest["runtime_executed"] is False and
         manifest["future_route_default_callback"] == 0x086FC300, "manifest scope matches actual inverse")
    return {"schema": 1, "kind": "independent-shoot-caller-resident", "status": "PASS",
            "inputs_sha256": list(map(sha, (before, gba, wsc))), "output_sha256": sha(after),
            "manifest_sha256": sha((json.dumps(manifest, indent=2) + "\n").encode()),
            "source_stage_entry": "772553..77256E: stage11 calls71F0:1750; others ordinary0653",
            "native_stage_owner": "0300231E, proven from retail base03002310+0E",
            "source_table_inverse_entries": 64, "retained_dependencies": len(DEPENDENCIES),
            "placements": placements, "declared_bytes": 96, "changed_bytes": changed,
            "router_executed_cases": router_cases, "router_state": "r0-r12/LR/SP/fullCPSR preserved before tail",
            "controller_executed_cases": controller_cases,
            "controller_state": "actual SELECT/APPLY; all4actions; same r4; exact writes/order; RNG0or1; r0-r12/LR/SP restored; flags scratch",
            "ownership": {"all_alignment_08_0A_0C_pointers": True, "ARM_Thumb_branches_literals_ADR_BL_BLX": True,
                          "inbound": references, "exemptions": []},
            "whole_ROM_inverse": True, "negative_controls": negatives,
            "scope": "Resident unconnected code only; no gameplay, terminal lifetime or E5 causal-fix claim"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "wsc15", "manifest"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.after.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.wsc15.suffix.lower() == ".wsc", "ROM-only extensions before reads")
    paths = [getattr(args, n) for n in ("before", "after", "gba", "wsc15", "manifest")]
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in {p.resolve() for p in paths}, "distinct JSON output")
    blobs = [p.read_bytes() for p in paths]
    report = verify(*blobs[:4], json.loads(blobs[4]))
    need(report["manifest_sha256"] == sha(blobs[4]), "manifest canonical bytes")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({"status": "PASS", "report_sha256": sha(args.output.read_bytes()),
                      "router_cases": report["router_executed_cases"], "controller_cases": report["controller_executed_cases"],
                      "negative_controls": len(report["negative_controls"])}))


if __name__ == "__main__":
    main()
