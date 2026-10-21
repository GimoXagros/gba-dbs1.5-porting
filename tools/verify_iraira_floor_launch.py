#!/usr/bin/env python3
"""Independent bounded class14 consumer, ARM ABI and score verification.

No builder is imported. The local walker handles only the five installed
straightforward ARM routines and guarded external call contracts, not a game
or device runtime. No emulator or save file is accessed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

PRE = "96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
ARM, X86 = Cs(CS_ARCH_ARM, CS_MODE_ARM), Cs(CS_ARCH_X86, CS_MODE_16)
SLOTS = ((0x627A00, 120, (0x03004500, 0x08627B00)),
         (0x627B00, 108, (0x8005, 0x08627C00)),
         (0x627C00, 68, (0xFFFFFDD4,)),
         (0x627D00, 56, (0x03002310,)), (0x627D80, 56, (0x03002310,)))
SONG_LITERALS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
NATIVE_RANGES = ((0x354910, 0x35491C), (0x3549E0, 0x354A34),
                 (0x354C98, 0x354D7C), (0x354DD4, 0x354DDC),
                 (0x357670, 0x357978), (0xD15C0, 0xD15F0),
                 (0x12BBC, 0x12C00), (0x12874, 0x129A0),
                 (0x12A84, 0x12B10), (0x35972C, 0x3597D0),
                 (0x3597D4, 0x359800), (0x373D34, 0x373D4C))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u32(data, at):
    return struct.unpack_from("<I", data, at)[0]


def destination(data, at, linked=False):
    w = u32(data, at)
    need(w >> 24 == (0xEB if linked else 0xEA), "exact ARM branch kind")
    delta = w & 0xFFFFFF
    return at + 8 + (delta - (0x1000000 if delta & 0x800000 else 0)) * 4


def listing(data, at, count, arm=True):
    reader, base, length = (ARM, BASE + at, count * 4) if arm else (X86, at, count * 8)
    result = list(reader.disasm(data[at:at + length], base))[:count]
    need(len(result) == count, "complete instruction decode")
    return [i.mnemonic + " " + i.op_str for i in result]


def instruction_contracts(after):
    rows = {
        0x627A00: ["ldrh r8, [r4, #6]", "tst r8, #1", "bne #0x8354dd4",
            "ldrh r8, [r4, #8]", "tst r8, #0x40", "bne #0x8354cb8",
            "orr r8, r8, #0x8000", "strh r8, [r4, #8]", "ldr r1, [pc, #0x50]",
            "ldrh r1, [r1]", "and r1, r1, #7", "add r8, r1, #0x64",
            "ldrh r1, [r4, #6]", "tst r1, #0x1000", "beq #0x8627a48",
            "mov sb, #1", "mov sl, #1", "bl #0x80d15c0", "ldrh r8, [r4, #8]",
            "tst r8, #0x400", "beq #0x8627a70", "stmdb sp!, {r5}",
            "stmdb sp!, {fp}", "bl #0x8012bbc", "add sp, sp, #8",
            "ldrh r8, [r4, #8]", "bic r8, r8, #0x400", "strh r8, [r4, #8]",
            "ldr r8, [pc, #4]", "b #0x8354d20"],
        0x627B00: ["stmdb sp!, {lr}", "mov sb, #3", "strb sb, [r4, #0x6e]",
            "mov sb, #0", "strh sb, [r4, #0xa6]", "strh sb, [r4, #0x42]",
            "strh sb, [r4, #0x44]", "strh sb, [r4, #0x46]", "strh sb, [r4, #0x48]",
            "ldrh r8, [r4, #6]", "orr r8, r8, #1", "strh r8, [r4, #6]",
            "stmdb sp!, {r4}", "stmdb sp!, {fp}", "ldrh r8, [r4, #0x34]",
            "stmdb sp!, {r8}", "ldrh r8, [r4, #0x36]", "stmdb sp!, {r8}",
            "ldr r8, [pc, #0x1c]", "stmdb sp!, {r8}", "bl #0x835972c",
            "add sp, sp, #0x14", "ldr r8, [pc, #0x10]", "str r8, [r4]",
            "bl #0x8627c00", "ldm sp!, {lr}", "bx lr"],
        0x627C00: ["stmdb sp!, {lr}", "ldrh r8, [r5, #0xa]", "tst r8, #0x2000",
            "beq #0x835778c", "ldrh r8, [r4, #4]", "tst r8, #1", "bne #0x835774c",
            "ldrb r8, [r4, #0x70]", "cmp r8, #0x18", "blo #0x835774c",
            "ldr sb, [pc, #0x14]", "strh sb, [r4, #0xa0]", "mov sb, #0x14",
            "strh sb, [r4, #0xa2]", "mov sb, #0xf", "strh sb, [r4, #0xa4]",
            "b #0x835774c"],
    }
    for at, value in ((0x627D00, "r8"), (0x627D80, "r0")):
        saved = "{r0, r1, lr}" if value == "r8" else "{r1, r8, lr}"
        rows[at] = [f"push {saved}", f"mov r1, {value}", "ldr r0, [pc, #0x28]",
                    "ldrb r0, [r0, #0xe]", "cmp r0, #0xb", "blne #0x80d1c78",
                    "cmp r0, #9", f"blo #{BASE + at + 40:#x}", "cmp r0, #0xa",
                    f"bls #{BASE + at + 44:#x}", "orr r1, r1, #0x2000",
                    f"mov {value}, r1", f"pop {saved}", "bx lr"]
    for at, expected in rows.items():
        need(listing(after, at, len(expected)) == expected, f"complete installed code contract {at:06X}")
    for at, size, words in SLOTS:
        need(after[at + size:at + size + len(words) * 4] == struct.pack("<" + "I" * len(words), *words),
             "complete literal pool")
    return sum(len(v) for v in rows.values())


class State:
    """Minimal instruction evaluator for the exact, separately bound words."""
    def __init__(self, rom):
        self.rom, self.mem, self.calls, self.writes = rom, {}, [], []
        self.r = [0x12340000 + i * 0x101 for i in range(16)]
        self.r[4], self.r[5], self.r[11] = 0x02011000, 0x02012000, 0
        self.r[13], self.r[14] = 0x03007000, 0x01000000
        self.z = self.c = False

    def read(self, at, size):
        if BASE <= at <= BASE + len(self.rom) - size:
            return int.from_bytes(self.rom[at - BASE:at - BASE + size], "little")
        return sum(self.mem.get(at + n, 0) << (8 * n) for n in range(size))

    def write(self, at, value, size, log=True):
        need(at < BASE, "bounded helper must not write ROM")
        for n in range(size):
            self.mem[at + n] = (value >> (8 * n)) & 255
        if log:
            self.writes.append((at, size))

    def get(self, reg):
        return self.r[15] + 8 if reg == 15 else self.r[reg]

    def service(self, target):
        if target == 0x080D1C78:
            char, stage = self.read(0x0300231A, 1), self.read(0x0300231E, 1)
            self.r[0], self.r[8] = {11: 10, 13: 8, 14: 9}.get(char, stage), 0x03002310
        elif target == 0x080D15C0:
            self.calls.append((target, self.r[8], self.r[9], self.r[10]))
            self.r[6], self.r[7] = 0x030022F0, self.read(0x030022F6, 2)
            if self.r[7] == 0:
                for off, reg in ((2, 8), (14, 9), (6, 10)):
                    self.write(0x030022F0 + off, self.r[reg], 2)
                self.r[8] = self.read(0x03002300, 2) | 256
                self.write(0x03002300, self.r[8], 2)
        elif target in (0x08012BBC, 0x0835972C):
            size = 2 if target == 0x08012BBC else 5
            args = tuple(self.read(self.r[13] + i * 4, 4) for i in range(size))
            self.calls.append((target, *args))
            # These existing consumers preserve the owning r4/r5 and SP.
            # Their complete native windows are guarded independently.
        else:
            raise ValueError(f"unbound native service {target:08X}")

    def run(self, entry, stops=()):
        self.r[15] = entry
        for _ in range(1024):
            pc = self.r[15]
            if pc in stops or pc == 0x01000000:
                return pc
            need(any(BASE + a <= pc < BASE + a + size for a, size, _ in SLOTS), "control inside exact code slots")
            w, nxt = self.read(pc, 4), pc + 4
            cond = w >> 28
            allowed = {0: self.z, 1: not self.z, 3: not self.c, 9: not self.c or self.z, 14: True}
            need(cond in allowed, "bounded condition set")
            if not allowed[cond]:
                self.r[15] = nxt
                continue
            if w & 0x0FFFFFF0 == 0x012FFF10:
                nxt = self.get(w & 15)
            elif w & 0x0E000000 == 0x0A000000:
                delta = w & 0xFFFFFF
                delta -= 0x1000000 if delta & 0x800000 else 0
                target = pc + 8 + delta * 4
                if w & 0x01000000:
                    self.r[14] = nxt
                    if any(BASE + a == target for a, _, _ in SLOTS):
                        nxt = target
                    else:
                        self.service(target)
                else:
                    nxt = target
            elif w & 0x0E000000 == 0x08000000:
                need(w & 0x0FFF0000 in (0x092D0000, 0x08BD0000), "push/pop only")
                regs = [r for r in range(16) if w & (1 << r)]
                if w & 0x100000:
                    for r in regs:
                        self.r[r] = self.read(self.r[13], 4)
                        self.r[13] += 4
                else:
                    self.r[13] -= 4 * len(regs)
                    for n, r in enumerate(regs):
                        self.write(self.r[13] + n * 4, self.get(r), 4)
            elif w & 0x0C000000 == 0x04000000:
                need(not w & 0x02000000, "immediate word/byte transfer")
                rn, rd, off = (w >> 16) & 15, (w >> 12) & 15, w & 4095
                off *= 1 if w & 0x800000 else -1
                base = self.get(rn)
                at = base + off if w & 0x1000000 else base
                size = 1 if w & 0x400000 else 4
                if w & 0x100000:
                    self.r[rd] = self.read(at, size)
                else:
                    self.write(at, self.get(rd), size)
                if not w & 0x1000000 or w & 0x200000:
                    self.r[rn] = (base + off) & 0xFFFFFFFF
            elif w & 0x0E000090 == 0x90:
                need(w & 0x60 == 0x20 and w & 0x400000, "immediate unsigned halfword transfer")
                rn, rd = (w >> 16) & 15, (w >> 12) & 15
                off = (((w >> 4) & 0xF0) | (w & 15)) * (1 if w & 0x800000 else -1)
                base = self.get(rn)
                at = base + off if w & 0x1000000 else base
                if w & 0x100000:
                    self.r[rd] = self.read(at, 2)
                else:
                    self.write(at, self.get(rd), 2)
                if not w & 0x1000000 or w & 0x200000:
                    self.r[rn] = (base + off) & 0xFFFFFFFF
            else:
                need(w & 0x0C000000 == 0, "data processing encoding")
                op, rn, rd = (w >> 21) & 15, (w >> 16) & 15, (w >> 12) & 15
                if w & 0x02000000:
                    small, shift = w & 255, ((w >> 8) & 15) * 2
                    operand = ((small >> shift) | (small << ((32 - shift) % 32))) & 0xFFFFFFFF
                else:
                    need(w & 0xFF0 == 0, "unshifted register operand")
                    operand = self.get(w & 15)
                left = self.get(rn)
                need(op in (0, 4, 8, 10, 12, 13, 14), "bounded operations")
                result = {0: left & operand, 4: left + operand, 8: left & operand,
                          10: left - operand, 12: left | operand, 13: operand,
                          14: left & ~operand}[op] & 0xFFFFFFFF
                if op in (8, 10):
                    self.z = result == 0
                    if op == 10:
                        self.c = left >= operand
                else:
                    need(not w & 0x100000, "no unmodeled flag-writing arithmetic")
                    self.r[rd] = result
            self.r[15] = nxt
        raise ValueError("bounded path limit")


def finite_cases(after):
    trigger_cases = 0
    for timer in range(8):
        for bits in range(16):
            for busy in (0, 7):
                w = State(after)
                original_sp = w.r[13]
                f6 = (bits & 1) | (0x1000 if bits & 2 else 0)
                f8 = 0x100 | (0x40 if bits & 4 else 0) | (0x400 if bits & 8 else 0)
                for at, val in ((w.r[4] + 6, f6), (w.r[4] + 8, f8), (0x03004500, timer), (0x030022F6, busy)):
                    w.write(at, val, 2, False)
                stop = w.run(0x08627A00, (0x08354DD4, 0x08354CB8, 0x08354D20))
                expected = 0x08354DD4 if f6 & 1 else 0x08354CB8 if f8 & 64 else 0x08354D20
                need(stop == expected and w.r[13] == original_sp, "trigger exits retain parent stack")
                active = expected == 0x08354D20
                need(w.read(w.r[4] + 8, 2) == ((f8 | 0x8000) & ~0x400 if active else f8), "source trigger flags")
                expected_calls = []
                if active and f6 & 0x1000:
                    expected_calls.append((0x080D15C0, 100 + timer, 1, 1))
                    need(w.read(0x030022F6, 2) == (busy or 1), "native busy sound request retention")
                if active and f8 & 0x400:
                    expected_calls.append((0x08012BBC, 0, w.r[5]))
                need(w.calls == expected_calls, "request then release order and real stack arguments")
                if active:
                    need(w.r[8] == 0x08627B00, "native trigger tail receives real callback")
                trigger_cases += 1
    wait_cases = 0
    for frame in range(256):
        for flags in range(4):
            w = State(after)
            f4, f10 = flags & 1, 0x2000 if flags & 2 else 0
            w.write(w.r[4] + 4, f4, 2, False)
            w.write(w.r[4] + 0x70, frame, 1, False)
            w.write(w.r[5] + 10, f10, 2, False)
            for n in range(3):
                w.write(w.r[4] + 0xA0 + 2 * n, 0xA100 + n, 2, False)
            stop = w.run(0x08627C00, (0x0835774C, 0x0835778C))
            need(stop == (0x0835774C if f10 else 0x0835778C), "wait animation gate and native rejoin")
            expected = [0xFDD4, 20, 15] if f10 and not f4 and frame >= 24 else [0xA100, 0xA101, 0xA102]
            need([w.read(w.r[4] + 0xA0 + 2 * n, 2) for n in range(3)] == expected, "conditional source launch parameters")
            need(w.r[13] == 0x03006FFC and w.read(w.r[13], 4) == 0x01000000, "wait tail has exactly native return frame")
            wait_cases += 1
    w = State(after)
    w.write(w.r[4] + 0x34, 0x1200, 2, False)
    w.write(w.r[4] + 0x36, 0x2300, 2, False)
    stop = w.run(0x08627B00, (0x0835774C, 0x0835778C))
    need(stop == 0x0835778C and w.calls == [(0x0835972C, 0x8005, 0x2300, 0x1200, 0, w.r[4])], "effect argument order and same-call first wait")
    need(w.read(w.r[4], 4) == 0x08627C00 and w.read(w.r[4] + 0x6E, 1) == 3, "initializer callback/class")
    need(all(w.read(w.r[4] + off, 2) == 0 for off in (0x42, 0x44, 0x46, 0x48, 0xA6)), "source motion clear fields")
    need(w.r[13] == 0x03006FF8 and w.read(w.r[13], 4) == 0x08627B64, "nested wait tail returns to initializer")
    w.r[14] = w.read(w.r[13], 4)
    w.r[13] += 4
    need(w.run(w.r[14]) == 0x01000000 and w.r[13] == 0x03007000, "initializer final LR/SP restoration")
    effect_cases = 0
    for char in range(256):
        for progress in range(12):
            logical = progress if progress == 11 else {11: 10, 13: 8, 14: 9}.get(char, progress)
            for flags in (0, 0x2000, 0xFFFF, 0x804):
                for entry, reg in ((0x08627D00, 8), (0x08627D80, 0)):
                    w = State(after)
                    w.r[reg] = flags
                    saved = list(w.r[:15])
                    w.write(0x0300231A, char, 1, False)
                    w.write(0x0300231E, progress, 1, False)
                    w.run(entry)
                    want = flags if logical in (9, 10) else flags | 0x2000
                    saved[reg] = want
                    need(w.r[:15] == saved, "effect adapter preserves every unrelated register/LR/SP")
                    need(w.read(0x0300231E, 1) == progress and
                         all(0x03006FF0 <= at < 0x03007000 for at, _ in w.writes), "effect helper writes only own stack")
                    effect_cases += 1
    return dict(trigger_cases=trigger_cases, wait_cases=wait_cases, initializer_nested_return_cases=1,
                effect_selector_ABI_cases=effect_cases)


def source_native(before, after, gba, old, source):
    for a, b in NATIVE_RANGES:
        need(before[a:b] == after[a:b] == gba[a:b], f"existing consumer identity {a:06X}")
    source_checks = {
        0x742EBF: ["test word ptr [si + 6], 1", "je 0x742ecb"],
        0x742ECB: ["test word ptr [si + 8], 0x40", "je 0x742ee0"],
        0x742EEA: ["mov bx, word ptr es:[0x3ce]", "and bx, 7", "shl bx, 3"],
        0x742EFD: ["mov dx, word ptr cs:[bx + 2]", "mov bx, word ptr cs:[bx + 2]"],
        0x742F16: ["cmp word ptr [si + 6], 0", "jne 0x742f2a"],
        0x742F44: ["mov word ptr [si], 0x207b", "mov word ptr [si + 2], 0x668e"],
        0x76895B: ["mov byte ptr [si + 0x5a], 3", "mov word ptr [si + 0x90], 0"],
        0x76897E: ["push 0x8005", "push word ptr [si + 0x28]", "push word ptr [si + 0x26]"],
        0x76899C: ["test word ptr [di + 0xa], 0x2000", "jne 0x7689a6"],
        0x7689A6: ["test word ptr [si + 4], 1", "jne 0x7689c8", "cmp byte ptr [si + 0x5c], 0x1e"],
        0x7689B3: ["mov word ptr [si + 0x8a], 0xfe43", "mov word ptr [si + 0x8c], 0x10", "mov word ptr [si + 0x8e], 0xc"],
        0x786C6D: ["cmp ax, 9", "jb 0x786c77", "cmp ax, 0xa", "jbe 0x786c7c", "or word ptr [bx + 8], 0x2000"],
        0x781C00: ["cmp ax, 9", "jb 0x781c0a", "cmp ax, 0xa", "jbe 0x781c0e", "or dx, 0x2000"],
    }
    for at, text in source_checks.items():
        need(listing(source, at, len(text), False) == text, f"source consumer {at:06X}")
    for a, b, count in ((0x768731, 0x3ADBF7, 0x23), (0x742DCA, 0x392AE2, 0x18),
                        (0x74348F, 0x393064, 0x1D), (0x76877C, 0x3ADC42, 0x1D)):
        need(source[a:a + count] == old[b:b + count], "commercial source/native jump lineage")
    need(source[0x76895B:0x76897E] == source[0x768731:0x768754], "new jump initialization matches common producer")
    need(u32(gba, 0xD15EC) == 0x030022F0, "existing native sound request owner")
    need(destination(after, 0xD1C78) == 0x582C40 and after[0x582C40:0x582C78] == before[0x582C40:0x582C78], "existing route policy unchanged")
    need(listing(after, 0x582C40, 13) == ["ldr r8, [pc, #0x2c]", "ldrb r0, [r8, #0xa]",
        "cmp r0, #0xb", "moveq r0, #0xa", "bxeq lr", "cmp r0, #0xd", "moveq r0, #8", "bxeq lr",
        "cmp r0, #0xe", "moveq r0, #9", "bxeq lr", "ldrb r0, [r8, #0xe]", "bx lr"], "r0/r8-only getter ABI")
    need(u32(after, 0x582C74) == 0x03002310, "getter owner")
    need(listing(gba, 0x354D20, 1) == ["str r8, [r4]"] and
         listing(gba, 0x354D6C, 2) == ["pop {r1, r3, r5, lr}", "bx lr"] and
         listing(gba, 0x354DD4, 2) == ["pop {r1, r3, r5, lr}", "bx lr"] and
         listing(gba, 0x357974, 2) == ["ldm sp!, {lr}", "bx lr"], "native tail frame consumers")
    return sum(len(v) for v in source_checks.values())


def audio(before, after, source):
    need(after[0x686800:0x686B20] == before[0x683200:0x683520], "all100 previous song entries")
    need(after[0x683200:0x683544] == before[0x683200:0x683544], "old table and three voice records preserved")
    spans, records, cursor = [(0x686800, 0x686B60)], [], 0x686B60
    for n in range(8):
        src = 0x3F0000 + struct.unpack_from("<H", source, 0x3F0000 + (0xBE + n) * 6 + 4)[0]
        payload = source[src:src + 26]
        need(src == 0x3F8746 + 26 * n and payload[:8] == bytes.fromhex("00000f00a204c100"), "source sound table and wave/envelope")
        first = [0x29, 0x2B, 0x30, 0x32, 0x34, 0x35, 0x37, 0x39][n]
        need(payload[8:] == bytes((first, 9, 31, 1, 160, 6, first + 16, 9, 31, 1, 160, 2, first + 16, 9, 255, 255, 255, 255)), "full source phrase")
        need(struct.unpack_from("<4H", source, 0x742F89 + n * 8) == (0xBE + n, 1, 0, 0), "source request row")
        ptr, bank, player = struct.unpack_from("<IHH", after, 0x686800 + (100 + n) * 8)
        need((ptr, bank, player) == (BASE + cursor, 4, 4), "new native score table entry")
        need(after[cursor:cursor + 12] == bytes((1, 0, 40, 128)) + struct.pack("<II", 0x08683520, BASE + cursor + 12), "native single-track header and voice owner")
        pos, clock, notes, setup, volume = cursor + 12, 0, [], {}, None
        while True:
            need(pos < cursor + 100, "finite score extent")
            op = after[pos]; pos += 1
            if op == 0xB1:
                break
            if op == 0x81:
                clock += 1
            elif op == 0xD8:
                notes.append((clock, 9, after[pos], after[pos + 1], volume)); pos += 2
            else:
                need(op in (0xBC, 0xBB, 0xBD, 0xBE, 0xBF), "bounded native score opcode")
                setup[op] = after[pos]; pos += 1
                if op == 0xBE:
                    volume = setup[op]
        key = 36 + 12 * (first >> 4) + (first & 15)
        need(notes == [(0, 9, key, 127, 127), (10, 9, key + 12, 127, 51), (20, 9, key + 12, 127, 17)] and clock == 29, "independent complete source/native score schedule")
        need(setup == {0xBC: 0, 0xBB: 75, 0xBF: 127, 0xBD: 2, 0xBE: 17}, "native analogue/keyshift/tempo/pan")
        spans.append((cursor, pos))
        records.append(dict(source_id=0xBE + n, native_id=100 + n, source_raw=src,
                            source_sha256=sha(payload), native_raw=cursor, bytes=pos - cursor,
                            notes=notes, ticks=clock))
        cursor = (pos + 3) & ~3
    need(cursor <= 0x687000, "complete scores inside reserved interval")
    return spans, records


def verify(before, after, gba, old, source, deep=True):
    need(len(before) == len(after) == 0x800000, "ROM geometry")
    instruction_count = instruction_contracts(after)
    source_count = source_native(before, after, gba, old, source)
    need(u32(before, 0x354A34) == 0x08354DD4 and u32(after, 0x354A34) == 0x08627A00, "class14 dispatch slot")
    need(destination(before, 0x359568, True) == 0x584900 and destination(before, 0x3597D0, True) == 0x584940, "prior effect helper routes")
    need(destination(after, 0x359568, True) == 0x627D80 and destination(after, 0x3597D0, True) == 0x627D00, "two typed effect consumers")
    spans = [(a, a + size + 4 * len(words)) for a, size, words in SLOTS]
    spans += [(a, a + 4) for a in (0x354A34, 0x359568, 0x3597D0, *SONG_LITERALS)]
    for at in SONG_LITERALS:
        need(u32(before, at) == 0x08683200 and u32(after, at) == 0x08686800, "five native song table consumers")
    song_spans, songs = audio(before, after, source)
    spans += song_spans
    occupied = set()
    inverse = bytearray(after)
    for lo, hi in spans:
        need(not occupied.intersection(range(lo, hi)), "disjoint complete write intervals")
        occupied.update(range(lo, hi))
        inverse[lo:hi] = before[lo:hi]
    need(inverse == before, "full inverse and untouched gaps")
    report = dict(installed_instruction_contracts=instruction_count, source_instruction_contracts=source_count,
                  expected_write_intervals=spans, old_song_rows_preserved=100, songs=songs)
    if deep:
        report.update(finite_cases(after))
    return report


def allocation(before):
    intervals = ((0x627A00, 0x628000), (0x686800, 0x687000))
    for a, b in intervals:
        need(before[a:b] == b"\xFF" * (b - a), "entire declared reservation FF")
    def inside(raw):
        return any(a <= raw < b for a, b in intervals)
    for at in range(len(before) - 3):
        need(not inside(u32(before, at) - BASE), "prior unaligned pointer into reservation")
    for at in range(0, len(before) - 3, 4):
        word = u32(before, at)
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            delta -= 0x1000000 if delta & 0x800000 else 0
            need(not inside(at + 8 + delta * 4), "prior aligned ARM branch candidate")
        if word & 0x0E1F0000 == 0x041F0000:
            off = (word & 4095) * (1 if word & 0x800000 else -1)
            need(not inside(at + 8 + off), "prior aligned ARM literal candidate")


def main():
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    paths = [getattr(args, name) for name in ("before", "after", "gba", "wsc10", "wsc15", "report")]
    need(all(path.suffix.lower() != ".sav" for path in paths), "save paths forbidden")
    before, after, gba, old, source = [path.read_bytes() for path in paths[:5]]
    need(sha(before) == PRE and tuple(map(sha, (gba, old, source))) == ORIGINALS, "pinned predecessor and three originals")
    allocation(before)
    report = verify(before, after, gba, old, source)
    negatives = []
    for at, label in ((0x354A34, "wrong collision class callback"), (0x627A04, "airborne guard"),
                      (0x627A3C, "request type"), (0x627A40, "request delay"),
                      (0x627A70, "callback literal load"), (0x627B50, "effect stack service"),
                      (0x627B60, "same-call wait"), (0x627C20, "frame threshold"),
                      (0x627C44, "launch velocity"), (0x627D00, "r8 helper stack ABI"),
                      (0x627D14, "dedicated11 priority"), (0x627DB0, "r0 helper stack ABI"),
                      (0x686800, "prior song row"), (0x686B20, "first new song pointer"),
                      (0x686B60 + 4, "score voice owner"), (0x686B60 + 12 + 10, "score volume"),
                      (0x359568, "r0 consumer route"), (0x12340, "unrelated ROM byte")):
        damaged = bytearray(after)
        damaged[at] ^= 1
        try:
            verify(before, damaged, gba, old, source, False)
        except ValueError as error:
            negatives.append(dict(case=label, rejected=True, reason=str(error)))
        else:
            raise ValueError("accepted negative case " + label)
    report.update(schema=1, kind="independent-iraira-floor-launch-verification", status="PASS",
                  input_sha256=sha(before), output_sha256=sha(after), negative_cases=negatives,
                  builder_imported=False, emulator_or_save_access=False,
                  limitations=["Only class14 trigger, first jump state and two named effect consumers are added.",
                      "Source character13 aerial branches remain unimplemented.",
                      "Temporary character route is retained; campaign progression is not ported here.",
                      "Eight native score schedules use existing commercial tempo/wave analogue; hardware timbre parity and audible QA are not proved."])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[verify-iraira-floor-launch] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
