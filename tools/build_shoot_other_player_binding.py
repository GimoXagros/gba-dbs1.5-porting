#!/usr/bin/env python3
"""Install the resident 73F0..74A2 other-player phase over exact v48.

This is part of the existing 7168 initializer, not a second object system.
It has no caller until the whole initializer/controller connection is ready.
The native fade palette mirror must be owned by that transition. No emulator
or save is opened; all inputs are immutable ROMs supplied on the command line.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import (
    GBA_SHA256, WSC15_SHA256, assemble, require_hash, sha256, verify_machine_code,
)
from build_character_physics_assets import converted_record

INPUT_SHA256 = "11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E"
BASE = 0x08000000
ENTRY = 0x5C1500
LIMIT = 0x5C1700

ORACLES = (
    ("wsc15", 0x747CF0, 0x747DA2, "993C6E36E3700166E7C837D0E7FC82C1EAC4B497D28D98BB558612EF187B9FA8", "entire source other-player phase"),
    ("gba", 0x3530BC, 0x3530E4, "215E72C00A291A8149C2196AAC903DBC41D42F06F9CD115E1BB70D9D95714DC6", "native physics pointer and bounds"),
    ("gba", 0x35316C, 0x353190, "ECAB0EAB3DC97AEF5E9ADF1A87685380495388193B8D9D58B386E90826152F88", "paired current and previous positions"),
    ("gba", 0x353304, 0x3534E0, "89BC20C60E84CAF18C74B9DA351EB88C0364AC83A70179CAB2BC4406FDAF0E16", "native character resource reconfiguration"),
    ("gba", 0x35A6E8, 0x35A774, "0A1618CAD43FD09377342C055992FA0F1527ECB4AB5BC0777EDB6C615076C282", "native de-evolution caller and pointer subtraction"),
    ("gba", 0x33FDC0, 0x33FE1C, "6A80E9053418E0F07B8FA389EECC9ABB4F9E65464D58C0BC6FDDAF6DD03BF6CD", "existing fade palette mirror producer"),
    ("gba", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B", "native OBJ palette address consumer"),
)


def other_player_phase() -> tuple[bytes, int]:
    source = """
        push {r0-r12, lr}
        ldr r8, other_slot
        ldr r4, [r8]
        ldrh r8, [r4, #8]
        tst r8, #0x4000
        beq reset_fields
        bic r8, r8, #0x4000
        strh r8, [r4, #8]

        ldrb r0, [r4, #0x10]
        ldrb r3, [r4, #0x11]
        push {r0}
        push {r3}
        mov r8, #0
        push {r8}
        mov r11, #0
        bl 0x08353304
        add sp, sp, #12

        ldr r0, obj_palette
        ldr r1, palette_mirror
        mov r2, #16
    copy_slot_zero:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne copy_slot_zero
        add r0, r0, #0x60
        add r1, r1, #0x60
        mov r2, #16
    copy_slot_four:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne copy_slot_four

        add r5, r4, #0xAC
        push {r5}
        mov r8, #0
        push {r8}
        push {r8}
        bl 0x08012874
        add sp, sp, #12

        ldr r8, [r4, #0x60]
        sub r8, r8, #0x50
        str r8, [r4, #0x60]
        ldrsh r0, [r8, #0x24]
        ldrsh r3, [r8, #0x26]
        strh r0, [r4, #0x52]
        strh r3, [r4, #0x54]
    reset_fields:
        mov r8, #0x60
        strh r8, [r4, #0x6A]
        mov r8, #0xE700
        strh r8, [r4, #4]
        mov r8, #0x40
        strh r8, [r4, #6]
        mov r8, #0
        strh r8, [r4, #8]
        strh r8, [r4, #0xA]
        add r5, r4, #0xAC
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r8, #0xE00
        strh r8, [r4, #0x34]
        strh r8, [r4, #0x38]
        mvn r8, #0x7F
        strh r8, [r4, #0x36]
        strh r8, [r4, #0x3A]
        pop {r0-r12, lr}
        bx lr
        .align 2
    other_slot: .word 0x0300489C
    obj_palette: .word 0x05000200
    palette_mirror: .word 0x0203E200
    """
    blob = assemble(source, ENTRY)
    return blob, len(blob) - 12


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    before = args.input.read_bytes()
    sources = {"gba": args.gba.read_bytes(), "wsc15": args.wsc15.read_bytes()}
    require_hash(before, INPUT_SHA256, "exact v48")
    for key, expected in (("gba", GBA_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], expected, key)
    for key, start, end, digest, label in ORACLES:
        require_hash(sources[key][start:end], digest, label)
    if len(before) != 0x800000 or before[ENTRY:LIMIT] != b"\xff" * (LIMIT - ENTRY):
        raise SystemExit("unexpected other-player phase placement")
    for site in range(0, len(before), 4):
        word = struct.unpack_from("<I", before, site)[0]
        if BASE + ENTRY <= word < BASE + LIMIT:
            raise SystemExit(f"existing pointer into placement at {site:X}")
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if ENTRY <= site + 8 + delta * 4 < LIMIT:
                raise SystemExit(f"existing ARM branch into placement at {site:X}")
    if struct.unpack_from("<I", before, 0x3532FC)[0] != 0x08485000:
        raise SystemExit("expanded physics pointer table is not installed")
    if before[0x353324:0x353328] != bytes.fromhex("0F 00 59 E3"):
        raise SystemExit("expanded character reconfiguration sentinel is absent")
    # The native consumer exposed a historical asset placement defect: the
    # three additional records exist, but their pointers are one record early.
    # Reuse the existing converter to identify all payloads; move no data.
    plan = []
    for character in (12, 13, 14):
        old_pointer = 0x0848503C + (character - 12) * 0x78
        new_pointer = old_pointer + 0x78
        # This frozen v49 layer reproduces its historical arithmetic-source
        # payloads. A later routing repair installs the actual source records.
        record = converted_record(sources["wsc15"], character, legacy_source_routing=True)
        start = new_pointer - BASE
        if before[start:start + 0x78] != record:
            raise SystemExit(f"actual physics payload differs for ID {character}")
        plan.append((0x485000 + character * 4, struct.pack("<I", old_pointer),
                     struct.pack("<I", new_pointer), f"correct ID {character} physics record pointer"))
    blob, code_bytes = other_player_phase()
    if ENTRY + len(blob) > LIMIT:
        raise SystemExit("other-player phase exceeds placement")
    code_report = verify_machine_code(blob, ENTRY, code_bytes, {0x08353304, 0x08012874})
    # Validate all four Expected Writes against the immutable predecessor.
    plan.append((ENTRY, b"\xff" * len(blob), blob, "other-player restoration and reset phase"))
    allowed = set()
    for site, expected_before, replacement, label in plan:
        if before[site:site + len(replacement)] != expected_before:
            raise SystemExit(f"Expected Write precondition failed: {label}")
        region = set(range(site, site + len(replacement)))
        if allowed & region:
            raise SystemExit("overlapping Expected Writes")
        allowed |= region
    after = bytearray(before)
    for site, _old, replacement, _label in plan:
        after[site:site + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {site + i for site, prior, replacement, _label in plan
                for i, (a, b) in enumerate(zip(prior, replacement, strict=True)) if a != b}
    if changed != expected:
        raise SystemExit("unexpected final diff")
    report = {
        "schema": 1, "kind": "shoot-other-player-resident-binding",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(after),
        "output_bytes": len(after), "source_range": ["4090:73F0", "4090:74A2"],
        "native_entry": BASE + ENTRY, "generated_code": code_report,
        "expected_writes": [{"offset": site, "bytes": len(replacement),
                             "before_sha256": sha256(prior), "after_sha256": sha256(replacement),
                             "label": label} for site, prior, replacement, label in plan],
        "actual_changed_bytes": len(changed),
        "contract": {"other_player_slot": 0x0300489C, "character_ids": [0, 14],
                     "requires_existing_object": True, "requires_transition_palette_mirror_ownership": True,
                     "preserves": "r0-r12 and LR; condition flags not preserved",
                     "restoration_palette_ranges": [[0x0203E200, 0x0203E220], [0x0203E280, 0x0203E2A0]],
                     "physics_pointer_offset": 0x60, "physics_pointer_bytes": 4},
        "claim_scope": "three native physics pointer repairs and resident source other-player phase; no initializer caller, complete palette transition, global-clear mapping, menu, controller, emulator or supplied-save QA",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-other-player] static build {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
