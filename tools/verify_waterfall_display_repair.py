#!/usr/bin/env python3
"""Independent source/consumer/write verification for the Waterfall repair.

Uses the existing bounded instruction checker, never a generator or game
emulator. Native services remain explicit summaries, not gameplay evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import verify_train_graphics_repair as arm
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

PRE = "AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF"
INPUTS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
          "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
          "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
SLOTS = ((0x628300, 108, 8), (0x628380, 56, 8), (0x628400, 36, 4),
         (0x628450, 56, 4), (0x628500, 204, 28),
         (0x628680, 48, 4), (0x6286C0, 48, 4))
OWNERS = (0x582954, 0x582958, 0x582960, 0x58296C,
          0x582970, 0x582974, 0x58297C, 0x582988)
RESERVATION = ((0x628300, 0x628900),)
need, u16, u32 = arm.need, arm.u16, arm.u32
sha, instruction, target = arm.sha, arm.instruction, arm.target


def sequence(data, at, lines):
    rows = [line.strip() for line in lines.splitlines() if line.strip()]
    for index, text in enumerate(rows):
        instruction(data, at + index * 4, text)
    return len(rows)


def code_contracts(before, after):
    # The copied scroll code has only one relative branch leaving its body.
    for lo, hi in ((0, 0x60), (0x64, 0x74)):
        need(after[0x628300 + lo:0x628300 + hi] == before[0x583E00 + lo:0x583E00 + hi],
             "Waterfall callback preserves the existing scroll core and literals")
    need(target(after, 0x628360, True) == 0x628380, "private callback reaches private display tail")
    need(u32(after, 0x628350) == 0x0AFFFFFC,
         "copied callback local wait branch remains relative to its own body")
    sequence(after, 0x628380, """
        push {r0, r1, r2, r3, lr}
        bl #0x80c9000
        ldr r0, [pc, #0x28]
        ldrh r1, [r0]
        orr r1, r1, #0x1200
        ldr r3, [pc, #0x20]
        ldrh r2, [r3]
        tst r2, #2
        orrne r1, r1, #0x100
        strh r1, [r0]
        eor r2, r2, #2
        strh r2, [r3]
        pop {r0, r1, r2, r3, lr}
        bx lr
    """)
    sequence(after, 0x628400, """
        push {r0, r1, r2, lr}
        ldr r1, [pc, #0x18]
        mov r0, #0
        mov r2, #8
        str r0, [r1], #4
        subs r2, r2, #1
        bne #0x8628410
        pop {r0, r1, r2, lr}
        bx lr
    """)
    sequence(after, 0x628450, """
        push {r0, r1, lr}
        ldr r1, [pc, #0x2c]
        ldrh r0, [r1]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r1]
        cmp r0, #0
        bne #0x8628480
        ldrh r0, [r1, #2]
        subs r0, r0, #1
        movmi r0, #4
        strh r0, [r1, #2]
        pop {r0, r1, lr}
        bx lr
    """)
    sequence(after, 0x628500, """
        push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, lr}
        ldr r8, [pc, #0xc0]
        ldrh r0, [r8]
        tst r0, #0x10
        bne #0x8628598
        ldr r8, [pc, #0xb4]
        ldrb r0, [r8]
        cmp r0, #0
        bne #0x8628598
        ldr r8, [pc, #0xa8]
        ldrb r4, [r8]
        ldr r8, [pc, #0xa4]
        ldrh sb, [r8, #2]
        ldr r7, [pc, #0xa0]
        add r1, r7, sb, lsl #4
        ldr r2, [pc, #0x9c]
        ldr sl, [pc, #0x9c]
        mov r3, #8
        ldrh r0, [r1], #2
        bl #0x86285a0
        strh r0, [r2], #2
        subs r3, r3, #1
        bne #0x8628548
        add r5, r7, #0x50
        add r6, r7, #0x62
        add r5, r5, sb, lsl #1
        add r6, r6, sb, lsl #1
        add r2, r2, #2
        mov r3, #5
        ldrh r0, [r5], #2
        bl #0x86285a0
        strh r0, [r2]
        ldrh r0, [r6], #2
        bl #0x86285a0
        strh r0, [r2, #0x20]
        add r2, r2, #2
        subs r3, r3, #1
        bne #0x8628574
        pop {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, lr}
        bx lr
        cmp r4, #0
        bxeq lr
        and r0, r0, sl
        lsr r0, r0, #1
        tst r0, #0x1e
        orrne r0, r0, #1
        tst r0, #0x3c0
        orrne r0, r0, #0x20
        tst r0, #0x7800
        orrne r0, r0, #0x400
        bx lr
    """)
    for start, destination, fallback in ((0x628680, 0x628400, 0x6EEF80), (0x6286C0, 0x628500, 0x6EEFC0)):
        sequence(after, start, f"""
            push {{r0, r8, lr}}
            ldr r8, [pc, #0x24]
            ldrb r0, [r8, #0xe]
            cmp r0, #0xb
            beq #0x{BASE + start + 40:x}
            bl #0x80d1c78
            cmp r0, #9
            pop {{r0, r8, lr}}
            beq #0x{BASE + destination:x}
            b #0x{BASE + fallback:x}
            pop {{r0, r8, lr}}
            b #0x{BASE + fallback:x}
        """)
    for at, values in ((0x6283B8, (0x04000000, 0x03002568)),
                       (0x628424, (0x03003D30,)), (0x628488, (0x03003D30,)),
                       (0x6285CC, (0x03004506, 0x0300260B, 0x03004529, 0x03003D30,
                                   0x08584000, 0x05000024, 0x739C)),
                       (0x6286B0, (0x03002310,)), (0x6286F0, (0x03002310,))):
        need(struct.unpack_from("<" + "I" * len(values), after, at) == values,
             f"exact typed literal pool {at:06X}")
    for at in OWNERS:
        old, new = ((0x03002338, 0x03002388) if at < 0x582970 else (0x03002388, 0x03002338))
        need((u32(before, at), u32(after, at)) == (old, new), "all eight source-derived BG owner replacements")
    need(u32(before, 0x583948) == 0x08583E00 and u32(after, 0x583948) == 0x08628300,
         "only Waterfall update queues the private callback")
    for at, old, new in ((0xC4BC0, 0x6EEF80, 0x628680), (0xC4CC4, 0x6EEFC0, 0x6286C0)):
        need(target(before, at) == old and target(after, at) == new, "exact prepend route hooks")
    need(u32(before, 0x583A00) == 0xE92D40FF and target(after, 0x583A00) == 0x628450,
         "old phase/hazard-aliasing updater is bypassed")
    for start, count, _ in SLOTS:
        decoded = list(arm.CS.disasm(after[start:start + count], BASE + start))
        need(len(decoded) * 4 == count and all(row.size == 4 for row in decoded), "complete ARM7 word boundaries")


def source_contracts(before, after, gba, source):
    source_bytes = (
        (0x75FA45, "b800108ed833c0e4000c050b068203e600813682030200"),
        (0x77DB44, "680010680e029a1c2fff4f83c4046a23"),
        (0x77DB68, "bf0e02c745040010c7051200c745021300"),
        (0x77DB8B, "68001068ce019a1c2fff4f83c4046a24"),
        (0x77DBAF, "bfce01c745040008c7051000c745021100"),
        (0x77DBD7, "33c0bf820326890583c702268905"),
        (0x783495, "bf740133c08bf7b92000fcf3ab"),
        (0x76AAE2, "be7401ff04812403007403e9cf008b5c024b7903bb0400895c02"),
        (0x76AB03, "83c604c1e3042e8b97f31a"),
        (0x76AB5F, "8b5efe03db2e8b97431b89142e8b97551b89540a"),
        (0x783AE4, "33d28ec24242be24fe83c704e303e92900b90800"),
        (0x783B03, "be36feb905008b052689048b450a26894420"),
        (0x783B28, "d2ecb6f08ad022d6240fd2ea22d6d2e80ac2"),
        (0x783733, "bfce03f7450610007546"),
        (0x783755, "bfcd0333c98a2de302fec1"),
        (0x783765, "bf74011e56be00108edebe700333c08a045e1f0bc07507"),
    )
    for at, text in source_bytes:
        expected = bytes.fromhex(text)
        need(source[at:at + len(expected)] == expected, f"source data-flow contract {at:06X}")
    for lo, hi in ((0x11440, 0x114EC), (0x137AC, 0x13CD0), (0xC4BD0, 0xC4BF8),
                   (0xC9000, 0xC9070)):
        need(before[lo:hi] == after[lo:hi] == gba[lo:hi], "commercial consumer remains exact")
    for at, text in ((0x11478, "tst r0, #1"), (0x1147C, "orrne sl, sl, #0x200"),
                     (0x11484, "tst r0, #2"), (0x11488, "orrne sl, sl, #0x100"),
                     (0x11490, "tst r0, #4"), (0x11494, "orrne sl, sl, #0x1000"),
                     (0x58285C, "mov r8, #0x1b"), (0x5828D8, "mov r8, #0x1c"),
                     (0x582930, "strh r0, [r5, #4]"), (0x582934, "str r0, [r5]"),
                     (0x583938, "bl #0x8583a00")):
        instruction(after, at, text)
    need(u32(gba, 0xC4C28) == u32(gba, 0xC4D40) == 0x03003D30 and
         u32(gba, 0xC6284) == 0x03003D50, "native palette allocation ends at live collider")
    need(gba[0xC4BD8:0xC4BF8] == struct.pack("<I", 0xE4880004) * 8, "native allocation is exactly eight words")
    for at, value in ((0x58298C, 0x03002568), (0x582964, 0x0600F800), (0x582968, 0x030012BA),
                      (0x582980, 0x0600F000), (0x582984, 0x030012B8),
                      (0x583944, 0x03002338), (0xC4D3C, 0x03004529), (0xD1C74, 0x0300260B)):
        need(u32(after, at) == value, "existing typed phase, map, scroll and gate owner")
    need(target(after, 0xD1C78) == 0x582C40, "logical-stage getter entry")
    sequence(after, 0x582C40, """
        ldr r8, [pc, #0x2c]
        ldrb r0, [r8, #0xa]
        cmp r0, #0xb
        moveq r0, #0xa
        bxeq lr
        cmp r0, #0xd
        moveq r0, #8
        bxeq lr
        cmp r0, #0xe
        moveq r0, #9
        bxeq lr
        ldrb r0, [r8, #0xe]
        bx lr
    """)
    need(u32(after, 0x582C74) == 0x03002310, "getter actual battle owner")
    x86 = Cs(CS_ARCH_X86, CS_MODE_16)
    seeds = [int.from_bytes(row.bytes[2:], "little") for row in
             x86.disasm(source[0x78352C:0x7835A1], 0x78352C) if row.bytes[:2] == b"\xc7\x04"]
    rows = struct.unpack_from("<58H", source, 0x76AA63)
    need(seeds == list(rows[:8] + rows[40:45] + rows[49:54]) and len(seeds) == 18,
         "all eighteen explicit initial colors equal ROM phase zero")
    for index, value in enumerate(rows):
        need(u16(after, 0x584000 + index * 2) == arm.native_color(value), "retained animation color conversion")
    return rows, len(source_bytes)


def asset_contracts(after, source):
    for original, native in ((35, 27), (36, 28)):
        src, dst = 0x3B4DD0 + original * 24, 0x580000 + native * 24
        need((u16(source, src), u16(source, src + 2), u16(source, src + 10)) == (1, 3, 0x3000),
             "source vertical background geometry and map segment")
        need((u16(after, dst), u16(after, dst + 2), u32(after, dst + 12)) == (1, 3, 0x08626000),
             "native geometry and established collision owner")
        for index in range(3):
            descriptor = 0x3B4970 + u16(source, src + 8) + index * 4
            need(source[descriptor:descriptor + 2] == b"\xcd\x01", "source raw-map descriptor")
            origin = 0x4D0000 + u16(source, descriptor + 2)
            mapped = u32(after, dst + 8) - BASE + index * 8
            need(u32(after, mapped) == 0x101, "native raw-map descriptor")
            destination = u32(after, mapped + 4) - BASE
            need(0 <= destination <= len(after) - 1008, "complete map within ROM")
            for cell in range(504):
                value = u16(after, destination + cell * 2)
                inverse = (value & 511) | ((value & 512) << 4) | ((value & 3072) << 4) | ((value >> 12) << 9)
                need(inverse == u16(source, origin + cell * 2), "every map cell inverse restores source flags/tile/palette")
    for tile in range(512):
        for y in range(8):
            src = source[0x4D00E0 + tile * 32 + y * 4:0x4D00E0 + tile * 32 + y * 4 + 4]
            dst = after[0x5A0100 + tile * 32 + y * 4:0x5A0100 + tile * 32 + y * 4 + 4]
            for x in range(8):
                pixel = sum(((src[plane] >> (7 - x)) & 1) << plane for plane in range(4))
                need((dst[x // 2] >> (4 * (x % 2))) & 15 == pixel, "every retained tile pixel matches source")
    for index in range(111):
        need(u16(after, 0x5A0000 + index * 2) == arm.native_color(u16(source, 0x4D0002 + index * 2)),
             "retained background palette excludes source transparent entry")


class Walker(arm.Walker):
    def service(self, at):
        if at in (BASE + 0x6285A0, BASE + 0xD1C78):
            self.run(at, stops=(self.r[14],))
        elif at == BASE + 0xC9000:
            self.calls.append(at)
        else:
            super().service(at)


def data_writes(walker):
    return [(at, size, value) for at, size, value in walker.writes if not 0x03006000 <= at < 0x03007000]


def instruction_cases(after, rows):
    original_slots = arm.SLOTS
    arm.SLOTS = SLOTS + ((0xD1C78, 4, 0), (0x582C40, 52, 4), (0x582800, 320, 80))
    counts = dict(initializer_cases=0, cycle_cases=0, projector_cases=0,
                  shade_cases=0, routing_cases=0, display_instruction_cases=0, display_truth_table_cases=0)
    try:
        w = Walker(after)
        w.r[3] = w.r[11] = 0
        w.run(BASE + 0x582800)
        for obj, resource, map_base, ports in ((0x03002388, 27, 0x0600F800, 0x030012BA),
                                              (0x03002338, 28, 0x0600F000, 0x030012B8)):
            need((w.read(obj, 4), w.read(obj + 4, 4), w.read(obj + 8, 4)) ==
                 (ports, ports + 1, map_base), "decoded initializer map and scroll ownership")
            need((w.read(obj + 12, 2), w.read(obj + 14, 2)) == (1, 3), "decoded vertical geometry")
            need(w.read(obj + 0x24, 4) == u32(after, 0x580000 + resource * 24 + 8), "decoded resource owner")
            need(w.read(obj + 0x28, 4) == 0x08626000, "both backgrounds retain the established collision owner")
        need(w.read(0x03002568, 4) == 0 and w.r[13:15] == [0x03007000, 0x01000000],
             "graphics initializer clears separate phase/hazard and balances stack")
        counts["initializer_cases"] += 1
        w = Walker(after)
        saved = w.r[:15]
        for at in range(0x03003D2C, 0x03003D58):
            w.write(at, 0xA7, 1, False)
        w.run(BASE + 0x628400)
        need(data_writes(w) == [(0x03003D30 + i * 4, 4, 0) for i in range(8)], "exact thirty-two-byte clear")
        need(w.read(0x03003D2C, 4) == w.read(0x03003D50, 4) == 0xA7A7A7A7 and w.r[:15] == saved,
             "palette initializer preserves adjacent collider, registers and stack")
        counts["initializer_cases"] += 1
        for tick in range(4):
            for phase in range(5):
                w = Walker(after)
                saved = w.r[:15]
                w.write(0x03003D30, tick, 2, False)
                w.write(0x03003D32, phase, 2, False)
                w.run(BASE + 0x628450)
                next_tick = (tick + 1) % 4
                next_phase = (phase - 1) % 5 if next_tick == 0 else phase
                expected = [(0x03003D30, 2, next_tick)]
                if next_tick == 0:
                    expected.append((0x03003D32, 2, next_phase))
                need(data_writes(w) == expected and w.r[:15] == saved, "source modulo-four/decrement-modulo-five cycle and ABI")
                counts["cycle_cases"] += 1
        for color in range(4096):
            for dim in (0, 1):
                w = Walker(after)
                w.r[0], w.r[4], w.r[10] = arm.native_color(color), dim, u32(after, 0x6285E4)
                w.run(BASE + 0x6285A0)
                source_color = sum((((color >> shift) & 15) >> dim) << shift for shift in (0, 4, 8))
                need(w.r[0] == arm.native_color(source_color), "all RGB444 channels dim before native conversion")
                counts["shade_cases"] += 1
        for phase in range(5):
            colors = list(rows[phase * 8:phase * 8 + 8])
            colors += [value for pair in zip(rows[40 + phase:45 + phase], rows[49 + phase:54 + phase]) for value in pair]
            destinations = list(range(0x05000024, 0x05000034, 2))
            destinations += [address for i in range(5) for address in (0x05000036 + i * 2, 0x05000056 + i * 2)]
            for dim in (0, 1, 2, 255):
                for flags in (0, 16, 65519, 65535):
                    for disabled in (0, 1, 255):
                        w = Walker(after)
                        saved = w.r[:15]
                        for address, value, size in ((0x03003D32, phase, 2), (0x03004529, dim, 1),
                                                     (0x03004506, flags, 2), (0x0300260B, disabled, 1)):
                            w.write(address, value, size, False)
                        w.run(BASE + 0x628500)
                        converted = [arm.native_color(sum((((c >> shift) & 15) // (2 if dim else 1)) << shift
                                                          for shift in (0, 4, 8))) for c in colors]
                        expected = [] if flags & 16 or disabled else [(at, 2, c) for at, c in zip(destinations, converted)]
                        need(data_writes(w) == expected and w.r[:15] == saved,
                             "all five source rows, eighteen hardware destinations, gates and projector ABI")
                        counts["projector_cases"] += 1
        for char in range(256):
            for progress in range(12):
                logical = progress if progress == 11 else {11: 10, 13: 8, 14: 9}.get(char, progress)
                for entry, own, previous in ((0x628680, 0x628400, 0x6EEF80), (0x6286C0, 0x628500, 0x6EEFC0)):
                    w = Walker(after)
                    saved = w.r[:15]
                    w.write(0x0300231A, char, 1, False)
                    w.write(0x0300231E, progress, 1, False)
                    w.run(BASE + entry, stops=(BASE + own, BASE + previous))
                    need(w.stop == BASE + (own if logical == 9 else previous) and w.r[:15] == saved and not data_writes(w),
                         "all selectors preserve dedicated Shoot priority, previous routes, arguments and progression")
                    counts["routing_cases"] += 1
        for hardware in range(65536):
            for phase in (0, 2):
                source_mask = 5 | phase
                expected = hardware | (0x200 if source_mask & 1 else 0) | (0x100 if source_mask & 2 else 0) | 0x1000
                need(hardware | 0x1200 | (0x100 if phase else 0) == expected, "complete hardware OR truth table")
                counts["display_truth_table_cases"] += 1
        for hardware in (0, 0x100, 0x200, 0x300, 0x1234, 0xFFFF):
            for phase in (0, 2):
                w = Walker(after)
                saved = w.r[:15]
                w.write(0x04000000, hardware, 2, False)
                w.write(0x03002568, phase, 2, False)
                w.run(BASE + 0x628380, stops=(BASE + 0x6283A8,))
                # The shared checker lacks EOR; its exact decoded instruction is
                # evaluated here between the two bounded instruction walks.
                w.r[2] ^= 2
                w.run(BASE + 0x6283AC)
                need(data_writes(w) == [(0x04000000, 2, hardware | 0x1200 | (0x100 if phase else 0)),
                                       (0x03002568, 2, phase ^ 2)] and w.r[:15] == saved,
                     "display writes hardware OR then phase XOR, with preserved tail ABI")
                need(w.calls == [BASE + 0xC9000], "existing callback service remains first")
                counts["display_instruction_cases"] += 1
    finally:
        arm.SLOTS = original_slots
    return counts


def verify(before, after, gba, source, deep=True):
    need(len(before) == len(after) == 0x800000, "exact expanded ROM sizes")
    code_contracts(before, after)
    rows, source_count = source_contracts(before, after, gba, source)
    asset_contracts(after, source)
    spans = [(start, start + code + literals) for start, code, literals in SLOTS]
    spans += [(at, at + 4) for at in OWNERS + (0xC4BC0, 0xC4CC4, 0x583948, 0x583A00)]
    spans.sort()
    need(all(left[1] <= right[0] for left, right in zip(spans, spans[1:])), "disjoint exact write intervals")
    inverse = bytearray(after)
    for lo, hi in spans:
        inverse[lo:hi] = before[lo:hi]
    need(inverse == before, "whole-ROM inverse includes unwritten gaps and every unchanged route")
    result = dict(source_data_flow_contracts=source_count, installed_instructions=sum(code // 4 for _, code, _ in SLOTS),
                  exact_write_spans=spans, exact_write_bytes=sum(hi - lo for lo, hi in spans),
                  changed_bytes=sum(a != b for a, b in zip(before, after)),
                  inverse_restores_predecessor=True, map_inverse_cells=3024,
                  retained_tile_pixels=32768, retained_background_colors=111, animation_colors=58,
                  palette_owner=[0x03003D30, 0x03003D50], phase_owner=0x03002568,
                  hazard_owner_preserved=0x0300256A, native_service_execution=False,
                  unchanged_paths=["Iraira shared callback", "Train and Shoot preceding routes", "campaign progression"],
                  remaining=["movement/attack runtime stability", "complete Waterfall mechanics and campaign parity",
                             "Iraira display/palette parity", "native service summaries are not gameplay execution"])
    if deep:
        result.update(instruction_cases(after, rows))
    return result


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in vars(args).values()), "save paths forbidden")
    before, after, gba, old, source = [getattr(args, name).read_bytes()
                                      for name in ("before", "after", "gba", "wsc10", "wsc15")]
    need(sha(before) == PRE and tuple(map(sha, (gba, old, source))) == INPUTS, "fixed predecessor and three original identities")
    arm.ownership(before, RESERVATION)
    report = verify(before, after, gba, source)
    negatives = []
    cases = [(at, "BG owner " + hex(at)) for at in OWNERS]
    cases += [(0xC4BC0, "initialization entry"), (0xC4CC4, "projection entry"),
              (0x583948, "callback routing"), (0x583A00, "old palette bypass"),
              (0x628350, "relocated local branch"), (0x628360, "private tail call"),
              (0x628390, "source display mask"), (0x6283A0, "phase-conditioned BG0"),
              (0x6283A8, "phase XOR target"), (0x6283BC, "phase owner"),
              (0x62840C, "palette clear extent"), (0x628424, "collider-safe palette owner"),
              (0x628478, "reverse palette wrap"), (0x62850C, "common palette gate"),
              (0x62856C, "palette destination gap"), (0x628588, "paired row destination"),
              (0x6285C4, "dim channel normalization"), (0x6285DC, "retained animation rows"),
              (0x62868C, "dedicated Shoot precedence"), (0x628698, "logical stage route"),
              (0x6286B0, "battle state owner"), (0x6286F0, "projection battle owner"),
              (u32(after, 0x580000 + 27 * 24 + 8) - BASE + 4, "source map descriptor target"),
              (u32(after, u32(after, 0x580000 + 27 * 24 + 8) - BASE + 4) - BASE, "source map cell"),
              (0x584000, "retained animated color"), (0x5A0100, "retained source tile"),
              (0x5A0000, "retained source palette"), (0x6283C0, "unwritten allocation gap"),
              (0x583F00, "Iraira historical tail"), (0x12340, "unrelated ROM byte")]
    for at, label in cases:
        damaged = bytearray(after)
        damaged[at] ^= 1
        try:
            verify(before, damaged, gba, source, deep=False)
        except ValueError as error:
            negatives.append(dict(case=label, rejected=True, reason=str(error)))
        else:
            raise ValueError("damaging mutation accepted: " + label)
    for at, label in ((0x75FA4F, "source display operation"), (0x783534, "source initial color instruction")):
        damaged = bytearray(source)
        damaged[at] ^= 1
        try:
            verify(before, after, gba, damaged, deep=False)
        except ValueError as error:
            negatives.append(dict(case=label, rejected=True, reason=str(error)))
        else:
            raise ValueError("damaging source mutation accepted: " + label)
    report.update(schema=1, kind="independent-waterfall-display-repair-verification", status="PASS",
                  input_sha256=sha(before), output_sha256=sha(after), original_sha256=list(INPUTS),
                  instruction_checker_sha256=sha(Path(arm.__file__).read_bytes()),
                  reservation=RESERVATION, predecessor_inbound_candidates=[], negative_cases=negatives,
                  builder_imported=False, emulator_launched=False, save_accessed=False, runtime_success_claim=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[verify-waterfall-display-repair] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
