#!/usr/bin/env python3
"""Independent Train asset/consumer/ABI verification; no generator imports.

The small instruction walker covers only the explicitly installed ARM routines.
It is not a game emulator: existing native services have separately guarded,
bounded call contracts, and no ROM, save, or peripheral execution is launched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

PRE = "83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD"
INPUTS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
          "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
          "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
CS = Cs(CS_ARCH_ARM, CS_MODE_ARM)
SLOTS = ((0x6EE900, 392, 60), (0x6EED00, 76, 8), (0x6EED80, 92, 8),
         (0x6EEE80, 128, 24), (0x6EEF80, 48, 4), (0x6EEFC0, 48, 4),
         (0x6EF100, 8, 4), (0x6EF110, 8, 4), (0x6EF140, 44, 4))
RESERVATIONS = ((0x6E0EE0, 0x6E51F0), (0x6F56A0, 0x6F843C),
                (0x6F8440, 0x6FAFE4), (0x6EE900, 0x6EF900))


def need(test, reason):
    if not test:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u16(data, at):
    return int.from_bytes(data[at:at + 2], "little")


def u32(data, at):
    return int.from_bytes(data[at:at + 4], "little")


def native_color(value):
    channels = ((value >> 8) & 15, (value >> 4) & 15, value & 15)
    return sum(((2 * c + 1) if c else 0) * (32 ** i) for i, c in enumerate(channels))


def target(data, at, link=False):
    value = u32(data, at)
    need(value >> 24 == (0xEB if link else 0xEA), f"unconditional ARM branch at {at:06X}")
    displacement = value & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    return at + 8 + displacement * 4


def instruction(data, at, text):
    decoded = next(CS.disasm(data[at:at + 4], BASE + at), None)
    need(decoded is not None and decoded.mnemonic + " " + decoded.op_str == text,
         f"native consumer {at:06X}: {text}")


def ownership(data, spans):
    def hit(at):
        return any(lo <= at < hi for lo, hi in spans)
    for lo, hi in spans:
        need(data[lo:hi] == bytes([255]) * (hi - lo), "reservation is entirely FF")
    for at in range(len(data) - 3):
        need(not hit(u32(data, at) - BASE), "existing encoded pointer into reservation")
    for at in range(0, len(data) - 3, 4):
        w = u32(data, at)
        if w >> 28 == 15:
            continue
        if w & 0x0E000000 == 0x0A000000:
            n = w & 0xFFFFFF
            n -= 0x1000000 if n & 0x800000 else 0
            need(not hit(at + 8 + n * 4), "existing ARM branch into reservation")
        if w & 0x0E1F0000 == 0x041F0000:
            n = (w & 0xFFF) * (1 if w & 0x800000 else -1)
            need(not hit(at + 8 + n), "existing ARM literal into reservation")


class Walker:
    """Restricted ARM7 word decoder with explicit service summaries."""
    def __init__(self, rom):
        self.rom, self.memory, self.writes, self.calls = rom, {}, [], []
        self.r = [0x11223300 + i * 0x101 for i in range(16)]
        self.r[13], self.r[14] = 0x03007000, 0x01000000
        self.z = self.c = self.n = self.v = False
        self.steps = 0
        self.stop = None
        self.external = set()

    def read(self, at, size):
        if BASE <= at <= BASE + len(self.rom) - size:
            return int.from_bytes(self.rom[at - BASE:at - BASE + size], "little")
        return sum(self.memory.get(at + i, 0) << (i * 8) for i in range(size))

    def write(self, at, value, size, log=True):
        need(at < BASE or at >= BASE + len(self.rom), "instruction must not write ROM")
        for i in range(size):
            self.memory[at + i] = (value >> (8 * i)) & 255
        if log:
            self.writes.append((at, size, value & ((1 << (size * 8)) - 1)))

    def get(self, index):
        return (self.r[15] + 8) & 0xFFFFFFFF if index == 15 else self.r[index]

    def condition(self, code):
        return (self.z, not self.z, self.c, not self.c, self.n, not self.n,
                self.v, not self.v, self.c and not self.z, not self.c or self.z,
                self.n == self.v, self.n != self.v,
                not self.z and self.n == self.v, self.z or self.n != self.v, True, False)[code]

    @staticmethod
    def rotate(value, shift):
        shift %= 32
        return ((value >> shift) | (value << ((32 - shift) % 32))) & 0xFFFFFFFF

    def operand(self, word):
        if word & (1 << 25):
            return self.rotate(word & 255, ((word >> 8) & 15) * 2)
        need(not word & 16, "only immediate ARM shifts in installed code")
        value, amount, kind = self.get(word & 15), (word >> 7) & 31, (word >> 5) & 3
        if kind == 0:
            return (value << amount) & 0xFFFFFFFF
        if kind == 1:
            return value >> (amount or 32)
        if kind == 2:
            signed = value - (1 << 32) if value & 0x80000000 else value
            return (signed >> (amount or 32)) & 0xFFFFFFFF
        need(amount != 0, "RRX outside installed contract")
        return self.rotate(value, amount)

    def service(self, at):
        sp = self.r[13]
        if at in (BASE + 0x110DC, BASE + 0x110F8):
            size = 2 if at == BASE + 0x110DC else 4
            count, origin, destination = self.r[2], self.r[4], self.r[5]
            self.calls.append((at, origin, destination, count))
            for i in range(count):
                self.write(destination + i * size, self.read(origin + i * size, size), size)
            self.r[2], self.r[4], self.r[5] = 0, origin + count * size, destination + count * size
        elif at == BASE + 0x13BE0:
            obj = self.read(sp + 4, 4)
            self.calls.append((at, self.read(sp, 4), obj))
            for offset in range(0, 76, 4):
                self.write(obj + offset, 0, 4)
        elif at == BASE + 0x13BF8:
            args = tuple(self.read(sp + i * 4, 4) for i in range(5))
            self.calls.append((at, *args))
            row, obj = args[2] + 24 * args[0], args[4]
            for dest, origin, size in ((0x44, 4, 1), (0x24, 8, 4), (0xC, 0, 2),
                                      (0xE, 2, 2), (0x45, 5, 1), (0x28, 12, 4),
                                      (0x46, 6, 1), (0x2C, 16, 4), (0x47, 7, 1), (0x30, 20, 4)):
                self.write(obj + dest, self.read(row + origin, size), size)
            self.r[8], self.r[9], self.r[10] = obj, row, self.read(row + 20, 4)
        elif at == BASE + 0x13C64:
            args = tuple(self.read(sp + i * 4, 4) for i in range(4))
            self.calls.append((at, *args))
            obj = args[3]
            need((self.read(obj + 0x14, 2), self.read(obj + 0x16, 2)) == (0, 0),
                 "initial fill only uses cleared selector zero")
            self.write(self.read(obj, 4), 0, 1)
            self.write(self.read(obj + 4, 4), 0, 1)
            descriptor = self.read(obj + 0x24, 4)
            origin, dest = self.read(descriptor + 4, 4), self.read(obj + 8, 4)
            for y in range(args[0]):
                for x in range(args[1]):
                    self.write(dest + y * 64 + x * 2, self.read(origin + (y * args[1] + x) * 2, 2), 2)
        elif at == BASE + 0x14574:
            args = tuple(self.read(sp + i * 4, 4) for i in range(4))
            self.calls.append((at, *args))
            # The native scroll service is separately checked at its actual
            # arguments and calls. No mock scrolling is presented as execution.
        elif at == BASE + 0xD1C78:
            char, progress = self.read(0x0300231A, 1), self.read(0x0300231E, 1)
            self.r[0], self.r[8] = {11: 10, 13: 8, 14: 9}.get(char, progress), 0x03002310
        elif at in self.external:
            self.calls.append((at, self.r[1], self.r[2], self.r[3], self.r[4], self.r[5], sp))
        else:
            raise ValueError(f"unproved native external call {at:08X}")

    def run(self, entry, stops=(), max_steps=4096):
        self.r[15] = entry
        while self.steps < max_steps:
            pc = self.r[15]
            if pc == 0x01000000 or pc in stops:
                self.stop = pc
                return
            need(any(BASE + a <= pc < BASE + a + size for a, size, _ in SLOTS),
                 f"control left explicitly installed instructions at {pc:08X}")
            w, next_pc = self.read(pc, 4), pc + 4
            self.steps += 1
            if not self.condition(w >> 28):
                self.r[15] = next_pc
                continue
            if w & 0x0FFFFFF0 == 0x012FFF10:
                dest = self.get(w & 15)
                if dest in self.external:
                    self.service(dest)
                    next_pc = self.r[14]
                else:
                    next_pc = dest
            elif w & 0x0E000000 == 0x0A000000:
                delta = w & 0xFFFFFF
                delta -= (1 << 24) if delta & 0x800000 else 0
                dest = pc + 8 + delta * 4
                if w & 0x01000000:
                    self.r[14] = pc + 4
                    self.service(dest)
                else:
                    next_pc = dest
            elif w & 0x0E000000 == 0x08000000:
                mask = [i for i in range(16) if w & (1 << i)]
                need((w & 0x0FFF0000) in (0x092D0000, 0x08BD0000), "only balanced push/pop profile")
                if w & 0x00100000:
                    for i in mask:
                        self.r[i] = self.read(self.r[13], 4)
                        self.r[13] += 4
                else:
                    self.r[13] -= len(mask) * 4
                    for n, i in enumerate(mask):
                        self.write(self.r[13] + n * 4, self.get(i), 4)
            elif w & 0x0C000000 == 0x04000000:
                rn, rd = (w >> 16) & 15, (w >> 12) & 15
                off = self.operand(w & ~(1 << 25)) if w & (1 << 25) else w & 0xFFF
                off = off if w & (1 << 23) else -off
                base = self.get(rn)
                address = base + off if w & (1 << 24) else base
                size = 1 if w & (1 << 22) else 4
                if w & (1 << 20):
                    self.r[rd] = self.read(address, size)
                else:
                    self.write(address, self.get(rd), size)
                if not w & (1 << 24) or w & (1 << 21):
                    self.r[rn] = (base + off) & 0xFFFFFFFF
            elif w & 0x0E000090 == 0x00000090:
                need(w & 0x60 == 0x20, "only unsigned halfword transfer")
                rn, rd = (w >> 16) & 15, (w >> 12) & 15
                off = ((w >> 4) & 0xF0) | (w & 15) if w & 0x400000 else self.get(w & 15)
                off = off if w & 0x800000 else -off
                base = self.get(rn)
                address = base + off if w & 0x1000000 else base
                if w & 0x100000:
                    self.r[rd] = self.read(address, 2)
                else:
                    self.write(address, self.get(rd), 2)
                if not w & 0x1000000 or w & 0x200000:
                    self.r[rn] = (base + off) & 0xFFFFFFFF
            elif w & 0x0C000000 == 0:
                op, rn, rd = (w >> 21) & 15, (w >> 16) & 15, (w >> 12) & 15
                a, b = self.get(rn), self.operand(w)
                need(op in (0, 2, 4, 8, 10, 12, 13), "bounded data-processing profile")
                value = {0: a & b, 2: a - b, 4: a + b, 8: a & b,
                         10: a - b, 12: a | b, 13: b}[op] & 0xFFFFFFFF
                if w & (1 << 20) or op in (8, 10):
                    self.z, self.n = value == 0, bool(value & 0x80000000)
                    if op in (2, 10):
                        self.c = a >= b
                        self.v = bool((a ^ b) & (a ^ value) & 0x80000000)
                    elif op == 4:
                        self.c = a + b > 0xFFFFFFFF
                        self.v = bool(~(a ^ b) & (a ^ value) & 0x80000000)
                if op not in (8, 10):
                    self.r[rd] = value
            else:
                raise ValueError(f"instruction outside bounded profile {pc:08X}:{w:08X}")
            self.r[15] = next_pc
        raise ValueError("instruction path exceeded finite bound")


def asset_checks(before, after, source):
    spans, rows, distinct, map_targets = [], [], [], []
    for source_row, native_row, shape in ((33, 21, (2, 2)), (34, 22, (48, 2))):
        src, dst = 0x3B4DD0 + source_row * 24, 0x580000 + native_row * 24
        need((u16(source, src), u16(source, src + 2)) == shape, "source resource dimensions")
        need((u16(after, dst), u16(after, dst + 2)) == shape, "native resource dimensions")
        need(after[dst + 4:dst + 8] == before[dst + 4:dst + 8] and
             after[dst + 12:dst + 24] == before[dst + 12:dst + 24], "only map dimensions and descriptor pointer change")
        descriptor_base, source_offset, segment = u32(after, dst + 8) - BASE, u16(source, src + 8), u16(source, src + 10)
        need(descriptor_base == 0x6E4DE0 + (32 if native_row == 22 else 0), "native descriptor bases")
        group = []
        for i in range(shape[0] * shape[1]):
            p = 0x3B4970 + source_offset + i * 4
            bank, flag = source[p], source[p + 1]
            physical = segment * 16 + u16(source, p + 2)
            need(bank == 0xC3 and flag == 1 and 0x30000 <= physical < 0x40000, "actual source descriptor address domain")
            raw = (bank & 127) * 65536 + physical % 65536
            d = descriptor_base + i * 8
            need(u32(after, d) == 0x101, "native enabled/raw descriptor flags")
            target_raw = u32(after, d + 4) - BASE
            if raw not in distinct:
                distinct.append(raw)
                map_targets.append(target_raw)
                spans.append((target_raw, target_raw + 1008))
            else:
                need(target_raw == map_targets[distinct.index(raw)], "repeated source descriptor aliases same complete map")
            need(any(a <= target_raw and target_raw + 1008 <= b for a, b in RESERVATIONS), "map extent within proved owner")
            for j in range(504):
                original, native = u16(source, raw + j * 2), u16(after, target_raw + j * 2)
                expected = ((original & 0x1FF) + (512 if original & 0x2000 else 0) +
                            (1024 if original & 0x4000 else 0) + (2048 if original & 0x8000 else 0) +
                            ((original >> 9) & 15) * 4096)
                need(native == expected, "source map cell flags/palette/tile conversion")
                need((native & 1023) == 0 or 512 <= (native & 1023) < 1024, "all map tiles either common blank zero or retained bank")
            group.append(raw)
        rows.append(group)
        spans.append((dst, dst + 24))
    need(len(distinct) == 36 and len(rows[0]) == 4 and len(rows[1]) == 96, "all distinct/aliased Train maps")
    need(u32(after, 0x580000 + 21 * 24 + 12) == 0x08622000 and
         u32(after, 0x580000 + 22 * 24 + 12) == 0, "verified primary collision and background no-collision")
    for tile in range(512):
        for y in range(8):
            source_row = source[0x4300E0 + tile * 32 + y * 4:0x4300E0 + tile * 32 + y * 4 + 4]
            native_row = after[0x590100 + tile * 32 + y * 4:0x590100 + tile * 32 + y * 4 + 4]
            for x in range(8):
                original = sum(((source_row[bit] >> (7 - x)) & 1) << bit for bit in range(4))
                need((native_row[x // 2] >> ((x % 2) * 4)) & 15 == original, "all retained source tile pixels")
    for index in range(1, 112):
        need(u16(after, 0x590000 + (index - 1) * 2) == native_color(u16(source, 0x430000 + index * 2)), "retained palette excludes transparent entry zero")
    need(after[0x6E5100:0x6E5120] == source[0x77CE44:0x77CE64], "Train row8 scroll origins")
    need(after[0x6EF500:0x6EF680] == source[0x77CD44:0x77CEC4], "all12 source camera rows")
    spans.extend(((0x6E4DE0, 0x6E5100), (0x6E5100, 0x6E5120), (0x6EF500, 0x6EF680)))
    return spans, {"map_descriptors": 100, "unique_maps": 36, "cells_in_descriptor_walk": 50400,
                   "retained_tile_pixels": 32768, "retained_palette_entries": 111,
                   "source_descriptor_order": rows}


def native_contracts(before, after, gba, source):
    checks = {
        0x13BF8: "ldr sb, [sp, #8]", 0x13BFC: "ldr sl, [sp]", 0x13C00: "mov r8, #0x18",
        0x13C0C: "ldr r8, [sp, #0x10]", 0x13C18: "ldr sl, [sb, #8]", 0x13C1C: "str sl, [r8, #0x24]",
        0x13C38: "ldr sl, [sb, #0xc]", 0x13C3C: "str sl, [r8, #0x28]",
        0x13C68: "ldr r4, [sp, #0x28]", 0x13C98: "lsl r0, r0, #2", 0x13CA4: "ldr r4, [r4, #4]",
        0x13CA8: "ldr r3, [sp, #0x1c]", 0x13CAC: "ldr r0, [sp, #0x20]",
        0x14578: "ldr r5, [sp, #0x24]", 0x1457C: "ldr r0, [sp, #0x1c]", 0x1460C: "ldr r0, [sp, #0x18]",
        0x145AC: "bl #0x8013dd4", 0x145BC: "bl #0x8013db4", 0x1463C: "bl #0x8013dd4",
        0x1464C: "bl #0x8013db4", 0x14850: "add r4, r4, r0, lsl #3",
        0x14874: "add r4, r4, r1, lsl #3", 0x148F4: "ldrb r0, [r4]", 0x1490C: "ldr r4, [r4, #4]",
        0x3EF18: "lsl r1, r1, #5", 0x3EF24: "and r0, r0, #3", 0x3EF28: "add r1, r1, r0, lsl #3",
        0x3EF30: "ldrb r0, [r4]", 0x3EF3C: "add sb, r8, #4", 0x3EF40: "ldrh r3, [sb, r1]",
        0x3EF44: "ldrh sb, [r8, r1]", 0x3EF54: "add r1, r1, r0", 0x3EF7C: "ldrh r0, [r8, r1]",
        0x3EF8C: "ldrh r2, [r8, r1]", 0x58356C: "mov r1, r1",
        0x583404: "ldr r1, [pc, #0x44]", 0x583408: "ldrh r0, [r1, #0x12]",
        0x58340C: "ldr r8, [pc, #0x40]", 0x583410: "strh r0, [r8]",
        0x583744: "ldr r5, [pc, #0xb4]", 0x583748: "ldrh r1, [r5]",
        0x17768: "ldr r6, [pc, #0x38]", 0x1776C: "ldr r7, [pc, #0x38]",
        0x17770: "mov sb, #0x19", 0x17774: "ldr r8, [r6], #4", 0x17778: "str r8, [r7], #4",
        0x1777C: "ldr r8, [r6], #4", 0x17780: "str r8, [r7], #4",
        0x17784: "ldr r8, [r6], #4", 0x17788: "str r8, [r7], #4",
        0x1778C: "ldr r8, [r6], #4", 0x17790: "str r8, [r7], #4",
        0x17794: "subs sb, sb, #1", 0x17798: "bgt #0x8017774",
        0xD0BE8: "bl #0x8017758", 0xD0BFC: "bl #0x80c9000",
        0x6EF100: "ldr r8, [pc]", 0x6EF104: "b #0x803ef3c",
        0x6EF110: "ldr r8, [pc]", 0x6EF114: "b #0x803ef7c",
    }
    for at, text in checks.items():
        instruction(after, at, text)
    for a, b in ((0x110DC, 0x11114), (0x13BE0, 0x13CD0), (0x14574, 0x146B0),
                 (0x146E0, 0x14BF0)):
        need(after[a:b] == before[a:b] == gba[a:b], "guarded existing native service unchanged")
    need(gba[0x3F078:0x3F158] == source[0x77CD44:0x77CE24], "seven commercial origin rows exact")
    for at, expected in ((0xC4C28, 0x03003D30), (0xC4D40, 0x03003D30),
                         (0xC4D3C, 0x03004529), (0xD1C74, 0x0300260B),
                         (0x3F1A4, 0x03004528), (0x352CC4, 0x03004528)):
        need(u32(gba, at) == expected, "commercial typed state owner")
    need(u32(after, 0x583450) == u32(after, 0x5835B0) == 0x03002388, "both Train BG1 consumers")
    need(u32(after, 0x583454) == 0x03002568 and u32(after, 0x583800) == 0x03004668,
         "Train queue producer and IRQ shadow remain separate owners")
    need((u32(after, 0x177A8), u32(after, 0x177AC)) == (0x03002478, 0x03004578),
         "actual native queue snapshot source and destination")
    need(0x03002568 - 0x03002478 == 0x03004668 - 0x03004578 == 0xF0 < 25 * 16,
         "native snapshot includes complete Train field")
    need(0x330 - 0x2CE == 0xA6 - 0x44 == 0x62 < 81 * 2,
         "source snapshot maps producer0330 to IRQ shadow00A6")
    need(u32(after, 0x6EF108) == u32(after, 0x6EF118) == 0x086EF500,
         "both actual camera adapter literals select complete source table")
    # Source byte contracts include data-flow, not just the entire source hash.
    source_checks = ((0x77D9DF, "b800308ed8"), (0x77DA20, "6a21"), (0x77DA67, "6a22"),
                     (0x77DAA7, "684052"), (0x77DAB0, "9a7432ff4f"),
                     (0x77DAD6, "8b4414250300c1e00303d8"), (0x77DAE6, "becc03"),
                     (0x77DAF3, "2e8b875400"), (0x77DB08, "9a7432ff4f"),
                     (0x75326F, "8e5e088b7e068b460a"), (0x7532C7, "8b460c"),
                     (0x76A8D7, "bb0e02be30038b47128904"), (0x76A957, "be7401ff0481240300"),
                     (0x768FD7, "b900108ed9bece02b900038ec1bf4400b95100fcf3a5"),
                     (0x75F97F, "b800038ed8bfa6008b1d8b4d02"),
                     (0x76A965, "8b5c024383fb02760233db895c02c1e304"),
                     (0x783495, "bf7401"), (0x783507, "c7040400"), (0x783513, "c704ff0f"),
                     (0x783733, "bfce03f745061000"), (0x783755, "bfcd03"),
                     (0x78376F, "be7003"), (0x783AA0, "bec4fe83c704"),
                     (0x783AAB, "b90600"), (0x783AC6, "d2ecb6f08ad022d6240fd2ea22d6d2e80ac2"))
    for at, expected in source_checks:
        raw = bytes.fromhex(expected)
        need(source[at:at + len(raw)] == raw, f"source contract {at:06X}")
    return len(checks), len(source_checks)


def instruction_cases(after, source):
    # Initializer: two owned BG objects, two source scroll calls, real helper ABI.
    init_cases = 0
    for variant in range(4):
        for side in range(2):
            w = Walker(after)
            original = list(w.r[:15])
            w.write(0x03002324, variant, 2, False)
            w.write(0x03004528, side, 1, False)
            w.run(BASE + 0x6EE900)
            need(w.r[:15] == original, "initializer preserves all caller registers/LR/SP")
            origins = struct.unpack_from("<2H", source, 0x77CE44 + variant * 8 + side * 4)
            expected = [(BASE + 0x110DC, 0x08590000, 0x05000002, 111),
                        (BASE + 0x110F8, 0x08590100, 0x06004000, 4096)]
            for record, obj in ((21, 0x03002338), (22, 0x03002388)):
                expected += [(BASE + 0x13BE0, 0, obj),
                             (BASE + 0x13BF8, record, 0, 0x08580000, 0, obj),
                             (BASE + 0x13C64, 18, 28, 0, obj)]
            expected += [(BASE + 0x14574, 0, 0x5240, 0, 0x03002388),
                         (BASE + 0x14574, origins[1], origins[0], 0, 0x03002388)]
            need(w.calls == expected, "exact source/native initialization call order and stack arguments")
            for obj, width, map_pointer, ports in ((0x03002338, 2, 0x0600F800, 0x030012BA),
                                                 (0x03002388, 48, 0x0600F000, 0x030012B8)):
                need((w.read(obj + 12, 2), w.read(obj + 14, 2)) == (width, 2), "initialized BG dimensions")
                need((w.read(obj + 8, 4), w.read(obj, 4), w.read(obj + 4, 4)) ==
                     (map_pointer, ports, ports + 1), "actual BG map and scroll-port pointers")
            need(w.read(0x03002360, 4) == 0x08622000, "real native resource binding preserves collision")
            init_cases += 1
    w = Walker(after)
    saved = list(w.r[:15])
    for at in range(0x03003D2C, 0x03003D54):
        w.write(at, 0xA7, 1, False)
    w.run(BASE + 0x6EED00)
    expected = [0, 0, native_color(4), native_color(4), native_color(0xFFF),
                native_color(0xFFF), native_color(0xFFF), native_color(4)] + [0] * 8
    need([w.read(0x03003D30 + 2 * i, 2) for i in range(16)] == expected, "source stage8 palette initialization")
    need(w.read(0x03003D2C, 4) == w.read(0x03003D50, 4) == 0xA7A7A7A7, "palette32-byte owner boundaries")
    need(w.r[:15] == saved, "palette initializer register preservation")
    cycle_cases = 0
    for tick in range(4):
        for phase in range(3):
            w = Walker(after)
            saved = list(w.r[:15])
            w.write(0x03003D30, tick, 2, False)
            w.write(0x03003D32, phase, 2, False)
            for index in range(6):
                w.write(0x03003D34 + index * 2, 0xA55A, 2, False)
            w.run(BASE + 0x6EED80)
            new_tick = (tick + 1) % 4
            new_phase = (phase + 1) % 3 if new_tick == 0 else phase
            need(w.read(0x03003D30, 2) == new_tick and w.read(0x03003D32, 2) == new_phase, "source modulo4/modulo3 palette cycle")
            wanted = ([native_color(u16(source, 0x76A922 + new_phase * 16 + i * 2)) for i in range(6)]
                      if new_tick == 0 else [0xA55A] * 6)
            need([w.read(0x03003D34 + i * 2, 2) for i in range(6)] == wanted, "six source colors copied in order")
            need(w.r[:15] == saved, "cycle registers preserved")
            cycle_cases += 1
    dim_cases = 0
    for value in range(4096):
        for dim in range(2):
            w = Walker(after)
            saved = list(w.r[:15])
            w.write(0x03004529, dim, 1, False)
            for i in range(6):
                w.write(0x03003D34 + i * 2, native_color(value), 2, False)
            w.run(BASE + 0x6EEE80)
            expected_source = sum((((value >> shift) & 15) // (2 if dim else 1)) << shift for shift in (0, 4, 8))
            need([w.read(0x050000C4 + 2 * i, 2) for i in range(6)] == [native_color(expected_source)] * 6,
                 "all RGB444 inputs obey source dim-then-convert semantics")
            need(w.r[:15] == saved, "palette projector preserves registers")
            need([(at, n) for at, n, _ in w.writes if at < 0x03006000 or at >= 0x03007000] ==
                 [(0x050000C4 + i * 2, 2) for i in range(6)], "only six palette colors written")
            dim_cases += 1
    disabled_cases = 0
    for flags, disable in ((16, 0), (0xFFFF, 0), (0, 1), (0, 255), (16, 255)):
        w = Walker(after)
        saved = list(w.r[:15])
        w.write(0x03004506, flags, 2, False)
        w.write(0x0300260B, disable, 1, False)
        w.run(BASE + 0x6EEE80)
        need(w.r[:15] == saved, "disabled projector preserves registers and stack")
        need(not any(0x05000000 <= at < 0x05000400 for at, _, _ in w.writes), "source disabled paths do not touch palette")
        disabled_cases += 1
    route_cases = 0
    for char in range(256):
        for progress in range(12):
            logical = progress if progress == 11 else {11: 10, 13: 8, 14: 9}.get(char, progress)
            for entry, train, fallback in ((0x6EEF80, 0x6EED00, 0x5C7380), (0x6EEFC0, 0x6EEE80, 0x5C7100)):
                w = Walker(after)
                saved = list(w.r[:15])
                w.write(0x0300231A, char, 1, False)
                w.write(0x0300231E, progress, 1, False)
                w.run(BASE + entry, stops=(BASE + train, BASE + fallback))
                need(w.stop == BASE + (train if logical == 8 else fallback), "palette routes preserve dedicated11 priority")
                need(w.r[:15] == saved, "palette route caller ABI")
                route_cases += 1
            w = Walker(after)
            w.r[1], w.r[2] = progress, 0
            saved = list(w.r[:15])
            w.write(0x0300231A, char, 1, False)
            w.write(0x0300231E, progress, 1, False)
            callback = u32(after, 0x582E40 + logical * 4)
            w.external.add(callback)
            w.run(BASE + 0x6EF140, stops=(BASE + 0x15DAC,))
            need(w.calls == [(callback, logical, 0, saved[3], saved[4], saved[5], saved[13])], "native update callback receives original queue/flag arguments")
            need(w.r[0] == saved[0] and w.r[2:8] == saved[2:8] and w.r[10:14] == saved[10:14], "update routing preserves live arguments")
            need(w.read(0x0300231E, 1) == progress, "no progress write")
            route_cases += 1
    return {"initializer_stack_cases": init_cases, "palette_cycle_cases": cycle_cases,
            "projector_RGB444_cases": dim_cases, "projector_disabled_cases": disabled_cases,
            "routing_cases": route_cases}


def verify(before, after, gba, old, source, deep=True):
    need(len(before) == len(after) == 0x800000, "ROM lengths")
    spans, report = asset_checks(before, after, source)
    native_count, source_count = native_contracts(before, after, gba, source)
    hooks = ((0x582D20, 0x086EE900, "pointer"), (0x583450, 0x03002388, "pointer"),
             (0x5835B0, 0x03002388, "pointer"),
             (0x58356C, 0xE1A01001, "pointer"), (0x583640, 0x6EED80, "branch"),
             (0xC4BC0, 0x6EEF80, "branch"), (0xC4CC4, 0x6EEFC0, "branch"),
             (0x582E00, 0x6EF140, "branch"), (0x3EF38, 0x6EF100, "branch"),
             (0x3EF78, 0x6EF110, "branch"))
    for at, expected, kind in hooks:
        need((target(after, at) if kind == "branch" else u32(after, at)) == expected, "exact active hook and consumer")
        spans.append((at, at + 4))
    for raw, code, literals in SLOTS:
        decoded = list(CS.disasm(after[raw:raw + code], BASE + raw))
        need(len(decoded) * 4 == code and all(q.size == 4 for q in decoded), "complete installed ARM instruction boundaries")
        spans.append((raw, raw + code + literals))
    inverse = bytearray(after)
    for lo, hi in spans:
        inverse[lo:hi] = before[lo:hi]
    need(inverse == before, "full-ROM inverse outside exact owned writes")
    report.update({"native_consumer_contracts": native_count, "source_contracts": source_count,
                   "native_installed_instructions": sum(code // 4 for _, code, _ in SLOTS),
                   "expected_write_spans": spans,
                   "remaining": ["source68F7:2507 Train hazard state/consumer is not implemented by this layer",
                                 "temporary character arena routing does not implement original campaign progression",
                                 "initial fill is validated at selector0; existing initial helper uses stride4 and is not generalized"],
                   "runtime_claim": False})
    if deep:
        report.update(instruction_cases(after, source))
    return report


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "gba", "wsc10", "wsc15", "report")), "save paths forbidden")
    before, after, gba, old, source = [getattr(args, name).read_bytes() for name in ("before", "after", "gba", "wsc10", "wsc15")]
    need(sha(before) == PRE and tuple(map(sha, (gba, old, source))) == INPUTS, "exact originals and logical-spawn predecessor")
    ownership(before, RESERVATIONS)
    result = verify(before, after, gba, old, source)
    negative_cases = []
    for at, label in ((0x6E0EE0, "map cell"), (0x6E4DE4, "first map pointer"),
                      (0x6E50FC, "last map pointer"), (0x580000 + 22 * 24, "BG1 dimensions"),
                      (0x590100, "retained tile pixel"), (0x590000, "retained color"),
                      (0x6E5100, "Train origin"), (0x6EF660, "last camera row"),
                      (0x6EF104, "camera adapter continuation"), (0x6EF118, "camera adapter literal"),
                      (0x583454, "queue producer owner"), (0x5835B0, "BG1 scroll owner"),
                      (0x58356C, "unjustified scroll mode bit"), (0x6EEE90, "projector flag gate"),
                      (0x6EEEE8, "blue dim normalization"), (0x6EEFA0, "palette route target"),
                      (0x6EF148, "dedicated11 update priority"), (0x6EEA30, "constructor argument"),
                      (0x6EEEF0, "projector loop count"), (0x12340, "unrelated byte")):
        damaged = bytearray(after)
        damaged[at] ^= 1
        try:
            verify(before, damaged, gba, old, source, deep=True)
        except ValueError as error:
            negative_cases.append({"case": label, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("negative mutation accepted: " + label)
    result.update({"schema": 1, "kind": "independent-train-graphics-consumer-verification", "status": "PASS",
                   "input_sha256": sha(before), "output_sha256": sha(after), "negative_cases": negative_cases,
                   "builder_imported": False, "emulator_or_save_access": False})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-train-graphics-repair] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
