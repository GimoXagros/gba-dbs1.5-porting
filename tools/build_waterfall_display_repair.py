#!/usr/bin/env python3
"""Restore Waterfall layer ownership, display phase and compact palette state.

The retained phase belongs to the existing Waterfall graphics initializer.
Palette state uses only the existing 32-byte palette owner; its eighteen colors
are selected from proven ROM rows instead of overwriting the adjacent collider.
Iraira's shared historical display callback is left on its existing path.
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

INPUT = "AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
CALLBACK, DISPLAY = 0x628300, 0x628380
PAL_INIT, PAL_CYCLE, PAL_PROJECT = 0x628400, 0x628450, 0x628500
INIT_ROUTE, PROJECT_ROUTE = 0x628680, 0x6286C0
RESERVATION = (0x628300, 0x628900)
OWNER_SITES = (0x582954, 0x582958, 0x582960, 0x58296C,
               0x582970, 0x582974, 0x58297C, 0x582988)
SOURCE_GUARDS = (
    (0x75F9EE, 0x75FA64, "4CFF501C4D32AFAFA23AEB9E70E8E861FE89D3F9D1EAA02D16231D9087920A08", "display callback"),
    (0x77DB11, 0x77DBE6, "583DB88060CE980F3FD5CB1EF635CB6A28D5BAC470B8D01E94958946BFB9B40F", "graphics initializer"),
    (0x78352C, 0x7835A1, "D0F156BFFC21C6CD98D32DCCA91CFA00C49C7CF3EE83A8D03FB6B53661859F06", "palette initialization"),
    (0x76AAD7, 0x76ABC3, "60C6EAD94B3CD8C45A2794BCD12A056369FC5068D620D611A0AC85A380C59F42", "palette cycle"),
    (0x783AE4, 0x783B90, "23E5B4C034D6BF41A3260C3E0B0098046252EE4AABCED80483678700212690DE", "palette projection"),
    (0x783726, 0x78378C, "2D7A9CD2BEB6F83BD199DC60B94B684A5BE36888D40D6616E6601A834B615A6D", "projection gates"),
)
NATIVE_GUARDS = (
    (0x582800, 0x582990, "CC36D4961686AEA5D3983DE815EEFF36B87EC6D53BD2CC7CB6EC8C56A08D1606", "old Waterfall initializer"),
    (0x583900, 0x58394C, "6C3D327AD3141BDDF34430572F5FB79F5C3C7C963F317887E4315372879163C2", "Waterfall update"),
    (0x583E00, 0x583E74, "76C3C2A38B4BED4E877DABFFD4D0F4AC01AC65FFC4CB75CF089854EF132BC83B", "shared scroll callback"),
    (0x583F00, 0x583F2C, "A101D3CA0684571129FC9C16747AA239EF8B2A59D73D4A0DD80C715570557DB3", "historical shared display tail"),
    (0x583A00, 0x583AA8, "551734AA0C163F2830AFEDB2005EB601EA8E3E08590290F31265CEBEFD3B29EA", "old palette updater"),
    (0x6EEF80, 0x6EEFB4, "FCD33DBC6A0C25B2B32E6084629CDBB19610A3E867142A4EC7AF7351947214D5", "preceding init route"),
    (0x6EEFC0, 0x6EEFF4, "F20305C5AF674431D02C60B7BE1AEA19A00F7B5CC133026A9187FB81337EBDF3", "preceding project route"),
    (0x11440, 0x114EC, "4E20FAE64CBFC70BD81EA3A3991BFB06838E38C5FD77782937F0490F4C9D9186", "commercial display bit translation"),
)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u16(data, at):
    return struct.unpack_from("<H", data, at)[0]


def u32(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, destination, link=False):
    displacement = destination - at - 8
    need(displacement % 4 == 0 and -(1 << 25) <= displacement < 1 << 25, "ARM branch extent")
    return struct.pack("<I", (0xEB000000 if link else 0xEA000000) | ((displacement // 4) & 0xFFFFFF))


def color(value):
    return sum((0 if not (value >> s) & 15 else 2 * ((value >> s) & 15) + 1) << d
               for s, d in ((8, 0), (4, 5), (0, 10)))


def asm(source, at, literals=0):
    data = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + at)[0])
    code = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[:len(data) - literals], BASE + at))
    need(sum(row.size for row in code) == len(data) - literals, "complete installed ARM decoding")
    return data, {"raw": at, "code_bytes": len(data) - literals, "literal_bytes": literals,
                  "instructions": [{"address": row.address, "mnemonic": row.mnemonic,
                                    "operands": row.op_str} for row in code]}


def no_inbound(data):
    lo, hi = RESERVATION
    for at in range(len(data) - 3):
        need(not lo <= u32(data, at) - BASE < hi, f"predecessor pointer into allocation {at:06X}")
    for at in range(0, len(data) - 3, 4):
        value = u32(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            displacement = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
            need(not lo <= at + 8 + displacement * 4 < hi, f"predecessor ARM-like branch {at:06X}")
        if value & 0x0E1F0000 == 0x041F0000:
            displacement = (value & 0xFFF) * (1 if value & 0x800000 else -1)
            need(not lo <= at + 8 + displacement < hi, f"predecessor ARM-like literal {at:06X}")


def display_tail():
    # Source reads hardware, ORs retained phase into it, then XORs the phase.
    # Do not XOR DISPCNT or read the logical shadow: neither is the source op.
    return asm("""
        push {r0-r3, lr}
        bl 0x080C9000
        ldr r0, display
        ldrh r1, [r0]
        orr r1, r1, #0x1200
        ldr r3, phase
        ldrh r2, [r3]
        tst r2, #2
        orrne r1, r1, #0x100
        strh r1, [r0]
        eor r2, r2, #2
        strh r2, [r3]
        pop {r0-r3, lr}
        bx lr
    display: .word 0x04000000
    phase: .word 0x03002568
    """, DISPLAY, 8)


def palette_init():
    # Phase zero's ROM slices exactly equal the eighteen explicit initial colors.
    return asm("""
        push {r0-r2, lr}
        ldr r1, owner
        mov r0, #0
        mov r2, #8
    clear:
        str r0, [r1], #4
        subs r2, r2, #1
        bne clear
        pop {r0-r2, lr}
        bx lr
    owner: .word 0x03003D30
    """, PAL_INIT, 4)


def palette_cycle():
    return asm("""
        push {r0-r1, lr}
        ldr r1, owner
        ldrh r0, [r1]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r1]
        cmp r0, #0
        bne done
        ldrh r0, [r1, #2]
        subs r0, r0, #1
        movmi r0, #4
        strh r0, [r1, #2]
    done:
        pop {r0-r1, lr}
        bx lr
    owner: .word 0x03003D30
    """, PAL_CYCLE, 4)


def palette_project():
    return asm("""
        push {r0-r10, lr}
        ldr r8, flags
        ldrh r0, [r8]
        tst r0, #0x10
        bne done
        ldr r8, disabled
        ldrb r0, [r8]
        cmp r0, #0
        bne done
        ldr r8, dimmed
        ldrb r4, [r8]
        ldr r8, owner
        ldrh r9, [r8, #2]
        ldr r7, rows
        add r1, r7, r9, lsl #4
        ldr r2, destination
        ldr r10, dim_mask
        mov r3, #8
    main_copy:
        ldrh r0, [r1], #2
        bl shade
        strh r0, [r2], #2
        subs r3, r3, #1
        bne main_copy
        add r5, r7, #0x50
        add r6, r7, #0x62
        add r5, r5, r9, lsl #1
        add r6, r6, r9, lsl #1
        add r2, r2, #2
        mov r3, #5
    pair_copy:
        ldrh r0, [r5], #2
        bl shade
        strh r0, [r2]
        ldrh r0, [r6], #2
        bl shade
        strh r0, [r2, #0x20]
        add r2, r2, #2
        subs r3, r3, #1
        bne pair_copy
    done:
        pop {r0-r10, lr}
        bx lr
    shade:
        cmp r4, #0
        bxeq lr
        and r0, r0, r10
        lsr r0, r0, #1
        tst r0, #0x1E
        orrne r0, r0, #1
        tst r0, #0x3C0
        orrne r0, r0, #0x20
        tst r0, #0x7800
        orrne r0, r0, #0x400
        bx lr
    flags: .word 0x03004506
    disabled: .word 0x0300260B
    dimmed: .word 0x03004529
    owner: .word 0x03003D30
    rows: .word 0x08584000
    destination: .word 0x05000024
    dim_mask: .word 0x739C
    """, PAL_PROJECT, 28)


def palette_route(at, target, previous):
    return asm(f"""
        push {{r0, r8, lr}}
        ldr r8, battle
        ldrb r0, [r8, #14]
        cmp r0, #11
        beq legacy
        bl 0x080D1C78
        cmp r0, #9
        pop {{r0, r8, lr}}
        beq 0x{BASE + target:08X}
        b 0x{BASE + previous:08X}
    legacy:
        pop {{r0, r8, lr}}
        b 0x{BASE + previous:08X}
    battle: .word 0x03002310
    """, at, 4)


def build(before, gba, wsc10, source):
    need(tuple(map(sha, (before, gba, wsc10, source))) == (INPUT, GBA, WSC10, WSC15),
         "fixed predecessor and three commercial source identities")
    need(len(before) == 0x800000, "expanded ROM extent")
    for data, guards in ((source, SOURCE_GUARDS), (before, NATIVE_GUARDS)):
        for at, end, digest, label in guards:
            need(sha(data[at:end]) == digest, "source/native guard: " + label)
    need(before[RESERVATION[0]:RESERVATION[1]] == b"\xff" * (RESERVATION[1] - RESERVATION[0]),
         "entire reservation is blank")
    no_inbound(before)
    # Original RAM owners are distinct. Collider state begins exactly at3D50;
    # no extended source color cache may be laid out past the32-byte owner.
    need(u32(gba, 0xC4C28) == u32(gba, 0xC4D40) == 0x03003D30 and
         u32(gba, 0xC6284) == 0x03003D50, "native palette and adjacent collider owners")
    need(before[0xC4BD8:0xC4BF8] == gba[0xC4BD8:0xC4BF8] ==
         struct.pack("<I", 0xE4880004) * 8, "existing32-byte palette clear")
    need(before[0x13BE0:0x13CD0] == gba[0x13BE0:0x13CD0] and
         before[0x137AC:0x13BE0] == gba[0x137AC:0x13BE0], "native BG owners and camera consumers")
    need(before[0x582928:0x582938] == bytes.fromhex("5C509FE50000A0E3B400C5E1000085E5") and
         u32(before, 0x58298C) == 0x03002568, "existing Waterfall phase/hazard initialization")
    need(source[0x77DBD9:0x77DBE5] == bytes.fromhex("BF820326890583C702268905"),
         "source phase0382 and hazard0384 are distinct from palette0174")
    source_colors = struct.unpack_from("<58H", source, 0x76AA63)
    need(before[0x584000:0x584074] == struct.pack("<58H", *(color(x) for x in source_colors)),
         "complete retained source palette rows")
    initial_colors = [u16(source, at + 2) for at in range(0x78352C, 0x7835A1)
                      if source[at:at + 2] == b"\xc7\x04"]
    row_zero = list(source_colors[:8]) + list(source_colors[40:45]) + list(source_colors[49:54])
    need(initial_colors == row_zero and len(initial_colors) == 18,
         "compact phase zero is every explicit source initial color")
    # Source BG35/36 descriptors and every retained map still have exact source
    # contents. This repair changes native owners, not the correct graphic data.
    for record, native in ((35, 27), (36, 28)):
        at = 0x3B4DD0 + record * 24
        need(struct.unpack_from("<2H", source, at) == (1, 3), "source vertical geometry")
        table = 0x3B4970 + u16(source, at + 8)
        native_table = u32(before, 0x580000 + native * 24 + 8) - BASE
        for index in range(3):
            bank, mode, offset = struct.unpack_from("<BBH", source, table + index * 4)
            need((bank, mode) == (0xCD, 1), "source raw map bank")
            raw = 0x4D0000 + offset
            converted = struct.pack("<504H", *((v & 511) | (512 if v & 0x2000 else 0) |
                ((v & 0xC000) >> 4) | (((v >> 9) & 15) << 12)
                for (v,) in struct.iter_unpack("<H", source[raw:raw + 0x3F0])))
            pointer = u32(before, native_table + index * 8 + 4) - BASE
            need(before[pointer:pointer + 0x3F0] == converted, "all retained Waterfall source map cells")
    need(u32(before, 0xC4BC0) == int.from_bytes(branch(0xC4BC0, 0x6EEF80), "little") and
         u32(before, 0xC4CC4) == int.from_bytes(branch(0xC4CC4, 0x6EEFC0), "little"),
         "preceding Train/Shoot palette routes")

    writes, instructions = [], []
    callback = bytearray(before[0x583E00:0x583E74])
    callback[0x60:0x64] = branch(CALLBACK + 0x60, DISPLAY, True)
    writes.append((CALLBACK, bytes(callback), "Waterfall-only scroll and display callback"))
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    decoded = list(decoder.disasm(callback[:0x6C], BASE + CALLBACK))
    need(sum(row.size for row in decoded) == 0x6C, "complete copied callback decode")
    instructions.append({"raw": CALLBACK, "code_bytes": 0x6C, "literal_bytes": 8,
                         "instructions": [{"address": row.address, "mnemonic": row.mnemonic,
                                           "operands": row.op_str} for row in decoded]})
    routines = (
        (DISPLAY, 0x628400, display_tail(), "retained source display phase"),
        (PAL_INIT, 0x628450, palette_init(), "compact Waterfall palette initialization"),
        (PAL_CYCLE, 0x628500, palette_cycle(), "compact Waterfall palette cycle"),
        (PAL_PROJECT, INIT_ROUTE, palette_project(), "source eighteen-color projection"),
        (INIT_ROUTE, PROJECT_ROUTE, palette_route(INIT_ROUTE, PAL_INIT, 0x6EEF80), "Waterfall init routing"),
        (PROJECT_ROUTE, 0x628740, palette_route(PROJECT_ROUTE, PAL_PROJECT, 0x6EEFC0), "Waterfall projection routing"),
    )
    for at, limit, (payload, machine), name in routines:
        need(at + len(payload) <= limit, "bounded routine allocation: " + name)
        writes.append((at, payload, name))
        instructions.append(machine)
    for at in OWNER_SITES:
        old = u32(before, at)
        expected = 0x03002338 if at < 0x582970 else 0x03002388
        need(old == expected, "Expected Write initializer BG owner")
        writes.append((at, struct.pack("<I", 0x03002388 if old == 0x03002338 else 0x03002338),
                       "source Waterfall background object owner"))
    need(u32(before, 0x583948) == BASE + 0x583E00 and u32(before, 0x583A00) == 0xE92D40FF,
         "Expected Write Waterfall callback and palette cycle")
    writes += [
        (0x583948, struct.pack("<I", BASE + CALLBACK), "only Waterfall display callback route"),
        (0x583A00, branch(0x583A00, PAL_CYCLE), "stop palette writes to the phase and hazard owner"),
        (0xC4BC0, branch(0xC4BC0, INIT_ROUTE), "prepend Waterfall palette init route"),
        (0xC4CC4, branch(0xC4CC4, PROJECT_ROUTE), "prepend Waterfall palette projection route"),
    ]
    after, manifest_writes = bytearray(before), []
    end = 0
    for at, payload, label in sorted(writes):
        need(at >= end, "nonoverlapping exact writes")
        end = at + len(payload)
        old = before[at:end]
        after[at:end] = payload
        manifest_writes.append({"raw": at, "bytes": len(payload), "label": label,
                                "expected_sha256": sha(old), "replacement_sha256": sha(payload)})
    inverse = bytearray(after)
    for at, payload, _ in writes:
        inverse[at:at + len(payload)] = before[at:at + len(payload)]
    need(bytes(inverse) == before, "complete Expected Write inverse")
    manifest = {"schema": 1, "kind": "waterfall-display-owner-palette-repair",
                "input_sha256": INPUT, "output_sha256": sha(after), "gba_sha256": GBA,
                "wsc10_sha256": WSC10, "wsc15_sha256": WSC15,
                "source_guards": SOURCE_GUARDS, "native_guards": NATIVE_GUARDS,
                "reservation": RESERVATION, "predecessor_inbound_candidates": [],
                "writes": manifest_writes, "machine_code": instructions,
                "inverse_restores_predecessor": True,
                "palette_state": {"start": 0x03003D30, "bytes": 32, "used_counters": [0, 2],
                                  "colors": 18, "rom_rows": 0x08584000},
                "phase_state": 0x03002568, "hazard_state_preserved": 0x0300256A,
                "source_BG_owners": {"waterfall": "1000:020E", "scenery": "1000:01CE"},
                "native_BG_owners": {"waterfall": 0x03002388, "scenery": 0x03002338},
                "unchanged_paths": ["Iraira shared callback and palette", "Train and Shoot routes", "progression byte"],
                "not_claimed": ["Iraira display/palette parity", "complete Waterfall mechanics", "runtime gameplay success"],
                "provided_save_accessed": False}
    return bytes(after), manifest


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in vars(args)), "save paths forbidden")
    result, manifest = build(*(getattr(args, name).read_bytes() for name in ("before", "gba", "wsc10", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[waterfall-display-repair] {sha(result)}")


if __name__ == "__main__":
    main()
