#!/usr/bin/env python3
"""Repair source-addressed Train maps and their existing native consumers.

The temporary character-to-arena route remains explicit. Battle progression is
never rewritten. The source-only Train hazard seed is a separate open component;
this layer adds no speculative RAM owner for its five private halfwords.
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
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

INPUT = "83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
MAP_PLACEMENTS = ([0x6E0EE0 + n * 0x3F0 for n in range(16)] +
                  [0x6F56A0 + n * 0x3F0 for n in range(10)] +
                  [0x6F8440 + n * 0x3F0 for n in range(10)])
DESCRIPTORS, TRAIN_ORIGINS = 0x6E4DE0, 0x6E5100
INIT, PAL_INIT, CYCLE, PROJECT = 0x6EE900, 0x6EED00, 0x6EED80, 0x6EEE80
PAL_INIT_ROUTE, PAL_PROJECT_ROUTE = 0x6EEF80, 0x6EEFC0
CAMERA_A, CAMERA_B, UPDATE_ROUTE, CAMERA_TABLE = 0x6EF100, 0x6EF110, 0x6EF140, 0x6EF500
RESERVATIONS = ((0x6E0EE0, 0x6E51F0), (0x6F56A0, 0x6F843C),
                (0x6F8440, 0x6FAFE4), (0x6EE900, 0x6EF900))
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)
KS = Ks(KS_ARCH_ARM, KS_MODE_ARM)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, target):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM B range")
    return struct.pack("<I", 0xEA000000 | ((delta // 4) & 0xFFFFFF))


def color(value):
    # Commercial RGB444 to RGB555: zero stays zero, nonzero becomes 2*c+1.
    return sum((0 if (value >> shift) & 15 == 0 else 2 * ((value >> shift) & 15) + 1) << dst
               for shift, dst in ((8, 0), (4, 5), (0, 10)))


def convert_map(raw):
    return struct.pack("<504H", *((entry & 511) | (512 if entry & 0x2000 else 0) |
                                 ((entry & 0x4000) >> 4) | ((entry & 0x8000) >> 4) |
                                 (((entry >> 9) & 15) << 12)
                                 for entry in struct.unpack("<504H", raw)))


def convert_tiles(raw):
    need(len(raw) == 0x4000, "512 complete source tiles")
    result = bytearray()
    for tile in range(0, len(raw), 32):
        for y in range(8):
            planes = raw[tile + y * 4:tile + y * 4 + 4]
            pixels = [sum(((planes[p] >> (7 - x)) & 1) << p for p in range(4))
                      for x in range(8)]
            result.extend(pixels[x] | pixels[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(result)


def no_inbound(data, intervals):
    def owned(raw):
        return any(a <= raw < b for a, b in intervals)
    for at in range(len(data) - 3):
        need(not owned(word(data, at) - BASE), f"prior unaligned pointer at {at:06X}")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            displacement = value & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 1 << 24
            need(not owned(at + 8 + displacement * 4), f"prior ARM-like branch at {at:06X}")
        if value & 0x0E1F0000 == 0x041F0000:
            displacement = value & 0xFFF
            if not value & 0x00800000:
                displacement = -displacement
            need(not owned(at + 8 + displacement), f"prior ARM-like literal at {at:06X}")


def asm(text, at, literals=0):
    raw = bytes(KS.asm(text, BASE + at)[0])
    code_size = len(raw) - literals
    instructions = list(ARM.disasm(raw[:code_size], BASE + at))
    need(sum(q.size for q in instructions) == code_size, "complete ARM decode")
    return raw, {"raw": at, "code_bytes": code_size, "literal_bytes": literals,
                 "instructions": [{"address": q.address, "mnemonic": q.mnemonic, "operands": q.op_str}
                                  for q in instructions]}


def initializer():
    text = """
        push {r0-r12, lr}
        mov r11, #0
        ldr r5, palette
        ldr r4, colors
        mov r2, #0x6F
        bl 0x080110DC
        ldr r5, vram
        ldr r4, tiles
        mov r2, #0x1000
        bl 0x080110F8
    """
    for index, name in ((21, "primary"), (22, "secondary")):
        text += f"""
        ldr r8, {name}
        push {{r8}}
        push {{r11}}
        bl 0x08013BE0
        add sp, sp, #8
        ldr r8, {name}
        push {{r8}}
        push {{r11}}
        ldr r8, resources
        push {{r8}}
        push {{r11}}
        mov r8, #{index}
        push {{r8}}
        bl 0x08013BF8
        add sp, sp, #20
        ldr r5, {name}
        ldr r8, {name}_map
        str r8, [r5, #8]
        ldr r8, {name}_scroll
        str r8, [r5]
        add r8, r8, #1
        str r8, [r5, #4]
        push {{r5}}
        push {{r11}}
        mov r8, #28
        push {{r8}}
        mov r8, #18
        push {{r8}}
        bl 0x08013C64
        add sp, sp, #16
        """
    # Source3274's stack order is BG, segment, X, Y.  Native14574 uses the
    # existing BG object, a zero segment placeholder, X, Y in the same order.
    text += """
        ldr r8, secondary
        push {r8}
        push {r11}
        ldr r8, initial_scroll
        push {r8}
        push {r11}
        bl 0x08014574
        add sp, sp, #16
        ldr r8, battle
        ldrh r0, [r8, #0x14]
        and r0, r0, #3
        lsl r0, r0, #3
        ldr r8, side
        ldrb r1, [r8]
        add r0, r0, r1, lsl #2
        ldr r8, origins
        add r8, r8, r0
        ldrh r0, [r8]
        ldrh r1, [r8, #2]
        ldr r8, secondary
        push {r8}
        push {r11}
        push {r0}
        push {r1}
        bl 0x08014574
        add sp, sp, #16
        pop {r0-r12, lr}
        bx lr
    palette: .word 0x05000002
    colors: .word 0x08590000
    vram: .word 0x06004000
    tiles: .word 0x08590100
    primary: .word 0x03002338
    secondary: .word 0x03002388
    resources: .word 0x08580000
    primary_map: .word 0x0600F800
    secondary_map: .word 0x0600F000
    primary_scroll: .word 0x030012BA
    secondary_scroll: .word 0x030012B8
    initial_scroll: .word 0x5240
    battle: .word 0x03002310
    side: .word 0x03004528
    """ + f"origins: .word 0x{BASE + TRAIN_ORIGINS:08X}"
    return asm(text, INIT, 60)


def palette_init():
    return asm("""
        push {r0-r3, r8, lr}
        ldr r8, owner
        mov r0, #0
        mov r1, #8
        mov r2, r8
    clear:
        str r0, [r2], #4
        subs r1, r1, #1
        bne clear
        mov r0, #0x2400
        strh r0, [r8, #4]
        strh r0, [r8, #6]
        ldr r0, white
        strh r0, [r8, #8]
        strh r0, [r8, #10]
        strh r0, [r8, #12]
        mov r0, #0x2400
        strh r0, [r8, #14]
        pop {r0-r3, r8, lr}
        bx lr
    owner: .word 0x03003D30
    white: .word 0x7FFF
    """, PAL_INIT, 8)


def palette_cycle():
    return asm("""
        push {r0-r4, lr}
        ldr r4, owner
        ldrh r0, [r4]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r4]
        cmp r0, #0
        bne done
        ldrh r0, [r4, #2]
        add r0, r0, #1
        cmp r0, #3
        movhs r0, #0
        strh r0, [r4, #2]
        ldr r1, rows
        add r1, r1, r0, lsl #4
        add r2, r4, #4
        mov r3, #6
    copy:
        ldrh r0, [r1], #2
        strh r0, [r2], #2
        subs r3, r3, #1
        bne copy
    done:
        pop {r0-r4, lr}
        bx lr
    owner: .word 0x03003D30
    rows: .word 0x08583840
    """, CYCLE, 8)


def palette_project():
    return asm("""
        push {r0-r8, lr}
        ldr r8, flags
        ldrh r0, [r8]
        tst r0, #0x10
        bne done
        ldr r8, disabled
        ldrb r0, [r8]
        cmp r0, #0
        bne done
        ldr r8, dimmed
        ldrb r7, [r8]
        ldr r4, owner
        add r4, r4, #4
        ldr r5, destination
        ldr r6, dim_mask
        mov r2, #6
    copy:
        ldrh r0, [r4], #2
        cmp r7, #0
        beq store
        and r0, r0, r6
        lsr r0, r0, #1
        tst r0, #0x1E
        orrne r0, r0, #1
        tst r0, #0x3C0
        orrne r0, r0, #0x20
        tst r0, #0x7800
        orrne r0, r0, #0x400
    store:
        strh r0, [r5], #2
        subs r2, r2, #1
        bne copy
    done:
        pop {r0-r8, lr}
        bx lr
    flags: .word 0x03004506
    disabled: .word 0x0300260B
    dimmed: .word 0x03004529
    owner: .word 0x03003D30
    destination: .word 0x050000C4
    dim_mask: .word 0x739C
    """, PROJECT, 24)


def palette_route(at, target, previous):
    # Dedicated Shoot takes precedence over the temporary character route.
    return asm(f"""
        push {{r0, r8, lr}}
        ldr r8, battle
        ldrb r0, [r8, #14]
        cmp r0, #11
        beq legacy
        bl 0x080D1C78
        cmp r0, #8
        pop {{r0, r8, lr}}
        beq 0x{BASE + target:08X}
        b 0x{BASE + previous:08X}
    legacy:
        pop {{r0, r8, lr}}
        b 0x{BASE + previous:08X}
    battle: .word 0x03002310
    """, at, 4)


def update_route():
    return asm("""
        push {r0, r3, r8, lr}
        cmp r1, #11
        beq selected
        bl 0x080D1C78
        mov r1, r0
    selected:
        pop {r0, r3, r8, lr}
        ldr r8, table
        ldr r9, [r8, r1, lsl #2]
        mov lr, pc
        bx r9
        b 0x08015DAC
    table: .word 0x08582E40
    """, UPDATE_ROUTE, 4)


def build(before, gba, old, source):
    need(sha(before) == INPUT and tuple(map(sha, (gba, old, source))) == ORIGINALS,
         "fixed logical-spawn predecessor and originals")
    need(len(before) == 0x800000, "expanded ROM length")
    for a, b in RESERVATIONS:
        need(before[a:b] == b"\xff" * (b - a), "exact reservation is FF")
    no_inbound(before, RESERVATIONS)
    # Source stage bank and initializer select C3 / segment3000, not a guessed
    # file-bank boundary. Retained palette and tiles are already correct.
    need(source[0x77CD28] == 0xC3 and struct.unpack_from("<H", source, 0x77CD3C)[0] == 0xCEF,
         "source stage8 bank and initializer")
    need(source[0x77D9DF:0x77D9E4] == bytes.fromhex("B800308ED8"), "source DS3000")
    expected_palette = struct.pack("<111H", *(color(x) for x in struct.unpack_from("<112H", source, 0x430000)[1:]))
    need(before[0x590000:0x5900DE] == expected_palette, "retained source palette")
    need(before[0x590100:0x594100] == convert_tiles(source[0x4300E0:0x4340E0]),
         "all512 retained source tiles")
    source_maps, descriptor_sources = [], []
    for record, shape in ((33, (2, 2)), (34, (48, 2))):
        at = 0x3B4DD0 + record * 24
        width, height = struct.unpack_from("<2H", source, at)
        descriptor, segment = struct.unpack_from("<2H", source, at + 8)
        need((width, height) == shape and segment == 0x3000, "source map geometry/segment")
        rows = []
        for index in range(width * height):
            bank, mode, offset = struct.unpack_from("<BBH", source, 0x3B4970 + descriptor + index * 4)
            need((bank, mode) == (0xC3, 1), "source C3 raw map descriptor")
            raw = (bank & 127) * 0x10000 + (((segment << 4) + offset) & 0xFFFF)
            need(0x430000 <= raw and raw + 0x3F0 <= 0x440000, "map inside bank43")
            rows.append(raw)
            if raw not in source_maps:
                source_maps.append(raw)
        descriptor_sources.append(rows)
    need(source_maps == [0x4340E0 + n * 0x3F0 for n in range(36)], "all36 distinct source maps")
    # Commercial camera tables have seven ordinary rows; native stage7 uses a
    # special constant path. Source1.5 adds eight through eleven after row7.
    need(gba[0x3F078:0x3F158] == source[0x77CD44:0x77CE24], "seven commercial origin rows")
    need(before[0x3EF18:0x3EFCC] == gba[0x3EF18:0x3EFCC], "actual origin consumers intact")
    need(before[0x14574:0x146B0] == gba[0x14574:0x146B0], "native source3274 scroll counterpart")
    need(before[0x13BE0:0x13CD0] == gba[0x13BE0:0x13CD0], "native BG create/fill consumers")
    need(before[0x17758:0x177B0] == gba[0x17758:0x177B0], "native display state copy bridge")
    need(word(before, 0x177A8) == 0x03002478 and word(before, 0x177AC) == 0x03004578
         and word(before, 0x583454) == 0x03002568 and word(before, 0x583800) == 0x03004668,
         "producer and IRQ shadow retain the common copy bridge")
    need(word(gba, 0xC4C28) == word(gba, 0xC4D40) == 0x03003D30, "commercial palette owner")
    need(word(gba, 0x3F1A4) == word(gba, 0x352CC4) == 0x03004528,
         "camera side and fighter producer share source03CC owner")
    need(word(gba, 0xC4D3C) == 0x03004529 and word(gba, 0xD1C74) == 0x0300260B,
         "native palette dim and disable consumers")
    need(word(before, 0x582C74) == 0x03002310,
         "existing logical getter control owner")
    need(word(before, 0x580000 + 21 * 24 + 12) == 0x08622000, "retain verified Train collision")
    need(word(before, 0x580000 + 22 * 24 + 12) == 0, "source background has no collision")
    source_cycle = struct.unpack_from("<24H", source, 0x76A922)
    need(before[0x583840:0x583870] == struct.pack("<24H", *(color(x) for x in source_cycle)),
         "existing source-addressed palette cycle")
    for value in range(4096):
        native = (color(value) & 0x739C) >> 1
        native |= int(bool(native & 0x1E)) | (int(bool(native & 0x3C0)) << 5) | (int(bool(native & 0x7800)) << 10)
        half = sum((((value >> bit) & 15) // 2) << bit for bit in (0, 4, 8))
        need(native == color(half), "all4096 source dim conversions")

    writes, machine = [], {}
    for raw, target in zip(source_maps, MAP_PLACEMENTS, strict=True):
        writes.append((target, convert_map(source[raw:raw + 0x3F0]), f"source Train map{raw:06X}"))
    map_lookup = dict(zip(source_maps, MAP_PLACEMENTS, strict=True))
    descriptors = b"".join(struct.pack("<II", 0x101, BASE + map_lookup[raw])
                           for group in descriptor_sources for raw in group)
    need(len(descriptors) == 800, "four plus96 native descriptors")
    writes.append((DESCRIPTORS, descriptors, "source100 descriptor selectors"))
    for record, width, pointer in ((21, 2, DESCRIPTORS), (22, 48, DESCRIPTORS + 32)):
        at = 0x580000 + record * 24
        row = bytearray(before[at:at + 24])
        need(struct.unpack_from("<2H", row) == (2, 2), "old bounded map geometry")
        struct.pack_into("<2H", row, 0, width, 2)
        struct.pack_into("<I", row, 8, BASE + pointer)
        writes.append((at, bytes(row), f"Train native resource{record}"))
    writes.append((TRAIN_ORIGINS, source[0x77CE44:0x77CE64], "source stage8 origin row"))
    writes.append((CAMERA_TABLE, source[0x77CD44:0x77CEC4], "complete source12 camera-origin rows"))
    for label, at, limit, payload in (
        ("initializer", INIT, PAL_INIT, initializer()),
        ("palette_init", PAL_INIT, CYCLE, palette_init()),
        ("palette_cycle", CYCLE, PROJECT, palette_cycle()),
        ("palette_project", PROJECT, PAL_INIT_ROUTE, palette_project()),
        ("palette_init_route", PAL_INIT_ROUTE, PAL_PROJECT_ROUTE, palette_route(PAL_INIT_ROUTE, PAL_INIT, 0x5C7380)),
        ("palette_project_route", PAL_PROJECT_ROUTE, 0x6EF000, palette_route(PAL_PROJECT_ROUTE, PROJECT, 0x5C7100)),
        ("update_route", UPDATE_ROUTE, CAMERA_TABLE, update_route()),
    ):
        blob, contract = payload
        need(at + len(blob) <= limit, f"{label} code slot")
        writes.append((at, blob, label))
        machine[label] = contract
    for at, ret in ((CAMERA_A, 0x3EF3C), (CAMERA_B, 0x3EF7C)):
        blob, contract = asm(f"ldr r8, pointer; b 0x{BASE+ret:08X}; pointer: .word 0x{BASE+CAMERA_TABLE:08X}", at, 4)
        writes.append((at, blob, "native camera-origin address adapter"))
        machine[f"camera_{at:06X}"] = contract
    replacements = (
        (0x582D20, struct.pack("<I", 0x08582000), struct.pack("<I", BASE + INIT), "Train initializer dispatch"),
        (0x583450, struct.pack("<I", 0x03002378), struct.pack("<I", 0x03002388), "update actual native BG1"),
        (0x5835B0, struct.pack("<I", 0x03002378), struct.pack("<I", 0x03002388), "scroll actual native BG1"),
        (0x58356C, struct.pack("<I", 0xE3811080), struct.pack("<I", 0xE1A01001), "source2or8 scroll mode"),
        (0x583640, struct.pack("<I", 0xE92D401F), branch(0x583640, CYCLE), "source palette cycle state"),
        (0xC4BC0, branch(0xC4BC0, 0x5C7380), branch(0xC4BC0, PAL_INIT_ROUTE), "Train palette init route"),
        (0xC4CC4, branch(0xC4CC4, 0x5C7100), branch(0xC4CC4, PAL_PROJECT_ROUTE), "Train palette output route"),
        (0x582E00, struct.pack("<I", 0xE59F8010), branch(0x582E00, UPDATE_ROUTE), "logical stage update dispatch"),
        (0x3EF38, struct.pack("<I", 0xE28F8F4E), branch(0x3EF38, CAMERA_A), "first full camera table consumer"),
        (0x3EF78, struct.pack("<I", 0xE28F80F8), branch(0x3EF78, CAMERA_B), "second full camera table consumer"),
    )
    for at, expected, replacement, label in replacements:
        need(before[at:at + len(expected)] == expected, f"Expected Write: {label}")
        writes.append((at, replacement, label))

    output, occupied, report_writes = bytearray(before), set(), []
    for at, blob, label in writes:
        indices = set(range(at, at + len(blob)))
        need(not indices & occupied, "non-overlapping Expected Writes")
        occupied |= indices
        output[at:at + len(blob)] = blob
        report_writes.append({"raw": at, "bytes": len(blob), "label": label,
                              "before_sha256": sha(before[at:at + len(blob)]), "after_sha256": sha(blob)})
    inverse = bytearray(output)
    for at, blob, _label in writes:
        inverse[at:at + len(blob)] = before[at:at + len(blob)]
    need(inverse == before, "whole ROM inverse")
    need(output[0x580000 + 21 * 24 + 12:0x580000 + 21 * 24 + 16] == struct.pack("<I", 0x08622000),
         "collision pointer preserved")
    # Runtime state addresses are literal operands only; no route writes the
    # battle progress byte. Source-only Train hazard state is not fabricated.
    report = {"schema": 1, "kind": "train-graphics-consumer-repair", "input_sha256": INPUT,
              "output_sha256": sha(output), "expected_writes": report_writes, "machine": machine,
              "reservations": RESERVATIONS, "inbound_candidates_in_reservations": [],
              "unique_source_maps": source_maps, "map_targets": MAP_PLACEMENTS,
              "descriptor_source_order": descriptor_sources, "map_resource_records": [21, 22],
              "source_map_resource_records": [33, 34], "dimensions": [[2, 2], [48, 2]],
              "retained_palette_tiles": [0x590000, 0x590100], "collision_preserved": 0x08622000,
              "palette_state_owner": [0x03003D30, 32], "palette_output": [0x050000C4, 12],
              "native_backgrounds": [0x03002338, 0x03002388],
              "source_evidence_ranges": [{"start": a, "end": b, "sha256": sha(source[a:b])} for a, b in
                  ((0x77CCF0, 0x77CEC4), (0x77D9DF, 0x77DB11), (0x752F8C, 0x75301E),
                   (0x753264, 0x753357), (0x76A8CC, 0x76AA33), (0x783488, 0x783529),
                   (0x783726, 0x78378C), (0x783A9A, 0x783AE4))],
              "route_policy": "existing temporary character11/13/14 to arena10/8/9; progress231E unchanged; dedicated11 takes priority",
              "source_cadence": "one source palette-cycle update per native callback; no virtual phase state",
              "remaining_component": "source68F7:2507 hazard seed376/378/37A/37C and its76B3xx private-state consumer have no native ownership proof in this layer",
              "runtime_claim": False, "save_access": False}
    return bytes(output), report


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "wsc10", "wsc15", "output", "manifest")), "save paths forbidden")
    output, report = build(*(getattr(args, name).read_bytes() for name in ("input", "gba", "wsc10", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[train-graphics-repair] " + report["output_sha256"])


if __name__ == "__main__":
    main()
