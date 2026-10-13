#!/usr/bin/env python3
"""Install bounded Shoot palette operations on the commercial palette mirror.

These are resident subroutines, not scene callbacks. The future scene owner
must capture before 71F0:1073 changes colors, retain exclusive mirror ownership,
call prepare after the ordered 7168 object/resource phases, and schedule the
two step entries with remaining counters 32..1. No caller is installed here.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import (
    GBA_SHA256, WSC15_SHA256, assemble, require_hash, sha256, verify_machine_code,
)
from convert_wsc_palette_block import convert_color

INPUT_SHA256 = "FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C"
BASE = 0x08000000
SNAPSHOT, PREPARE, TO_BLACK, TO_TARGET = 0x5C1900, 0x5C1C00, 0x5C1D00, 0x5C1F00
GRAY_TABLE, LIMIT = 0x5C2300, 0x5C2340
ORACLES = (
    ("wsc15", 0x747DDA, 0x747E34, "0415462B683CD87C9576DE4685A59D4F5BA6D3C201090C4D5B0A7A9F2FA40843"),
    ("wsc15", 0x747E34, 0x747E54, "C5605A0084D6DFAB01687645085BD7C4CF07C383421BD5F90541F541681C2738"),
    ("wsc15", 0x772061, 0x77208B, "760581E89D46555951EAD46CC68139A6F4881444F5D28E9A9D432ED1ECF5BE04"),
    ("wsc15", 0x772F43, 0x77329C, "7757A292434FEABC9B696BD172909FDA0FA33A95AA08336B78C75BFE4CD83C6D"),
    ("wsc15", 0x751E8D, 0x751F6B, "205C09848C45077D6D597B44B7224ABF74C9F7EB8E84179DAD8C5B3A2DA98D11"),
    ("gba", 0x11454, 0x11470, "6F8F5B01001BF386ACE8715E2FB8A857F16F43E907D984940D5C2C2BC4D85E90"),
    ("gba", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
    ("gba", 0x33FDC0, 0x33FE1C, "6A80E9053418E0F07B8FA389EECC9ABB4F9E65464D58C0BC6FDDAF6DD03BF6CD"),
    ("gba", 0x340A68, 0x340A8C, "267EB4EF9E47FA0A4AA11ADB93AA6319BE914BDA8093E31B744C61B03C7EF752"),
)


def snapshot() -> tuple[bytes, int]:
    """Capture 512 source bytes, reading high zeros from native BG aliases.

    Native OBJ zero colors are transparent; the source's high-row color zero
    is represented by the native BG backdrop lookup, so copy those aliases
    over the otherwise unused OBJ mirror zero slots after the full OBJ copy.
    The source 03E8 counter belongs to the scene caller, not this color helper.
    """
    blob = assemble("""
        push {r0-r12, lr}
        mov r0, #0x05000000
        ldr r1, mirror
        mov r2, #128
    bg_copy:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne bg_copy
        add r0, r0, #0x100
        add r1, r1, #0x100
        mov r2, #128
    obj_copy:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne obj_copy
        sub r0, r0, #0x200
        sub r1, r1, #0x100
        mov r2, #8
    high_zero_copy:
        ldrh r3, [r0], #0x20
        strh r3, [r1], #0x20
        subs r2, r2, #1
        bne high_zero_copy
        pop {r0-r12, lr}
        bx lr
    mirror: .word 0x0203E000
    """, SNAPSHOT)
    return blob, len(blob) - 4


def prepare() -> tuple[bytes, int]:
    """Selective 384-byte copy, gray targets, then white mapped hardware."""
    blob = assemble(f"""
        push {{r0-r12, lr}}
        mov r0, #0x05000000
        ldr r1, mirror
        mov r2, #128
    bg_copy:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne bg_copy
        add r0, r0, #0x120
        add r1, r1, #0x120
        mov r2, #48
    obj_one_to_three:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne obj_one_to_three
        add r0, r0, #0x20
        add r1, r1, #0x20
        mov r2, #16
    obj_five:
        ldrh r3, [r0], #2
        strh r3, [r1], #2
        subs r2, r2, #1
        bne obj_five
        ldr r0, gray
        ldr r1, mirror
        mov r2, #8
    gray_bg:
        ldrh r3, [r0], #2
        strh r3, [r1], #0x20
        subs r2, r2, #1
        bne gray_bg
        add r1, r1, #0x100
        mov r2, #8
    gray_obj:
        ldrh r3, [r0], #2
        strh r3, [r1], #0x20
        subs r2, r2, #1
        bne gray_obj
        mov r0, #0x05000000
        ldr r3, white
        mov r2, #128
    white_bg:
        strh r3, [r0], #2
        subs r2, r2, #1
        bne white_bg
        add r4, r0, #0x100
        mov r2, #8
    white_bg_high_zero:
        strh r3, [r0], #0x20
        subs r2, r2, #1
        bne white_bg_high_zero
        mov r2, #128
    white_obj:
        strh r3, [r4], #2
        subs r2, r2, #1
        bne white_obj
        pop {{r0-r12, lr}}
        bx lr
    mirror: .word 0x0203E000
    gray: .word 0x{BASE + GRAY_TABLE:08X}
    white: .word 0x00007FFF
    """, PREPARE)
    return blob, len(blob) - 12


def to_black() -> tuple[bytes, int]:
    """One source RGB444 decrement in native BGR555, for one parity half."""
    channels = []
    for shift in (0, 5, 10):
        channels.append(f"""
            {'mov r5, r3' if shift == 0 else f'lsr r5, r3, #{shift}'}
            and r5, r5, #31
            cmp r5, #3
            movls r5, #0
            subhi r5, r5, #2
            orr r4, r4, r5, lsl #{shift or 0}
        """)
    blob = assemble("""
        push {r0-r12, lr}
        cmp r0, #1
        blo done
        cmp r0, #32
        bhi done
        and r7, r0, #1
        mov r1, #0x05000000
        add r1, r1, r7, lsl #9
        mov r2, #128
    colors:
        ldrh r3, [r1]
        mov r4, #0
    """ + "\n".join(channels) + """
        strh r4, [r1], #2
        subs r2, r2, #1
        bne colors
        cmp r7, #0
        beq canonical_bg_zero
        sub r1, r1, #0x100
        sub r2, r1, #0x100
        mov r3, #8
    aliases:
        ldrh r4, [r1], #0x20
        strh r4, [r2], #0x20
        subs r3, r3, #1
        bne aliases
        b done
    canonical_bg_zero:
        cmp r0, #4
        subhi r4, r0, #3
        movls r4, #0
        orr r4, r4, r4, lsl #5
        and r5, r4, #31
        orr r4, r4, r5, lsl #10
        mov r1, #0x05000000
        strh r4, [r1]
    done:
        pop {r0-r12, lr}
        bx lr
    """, TO_BLACK)
    return blob, len(blob)


def to_target() -> tuple[bytes, int]:
    """One source increment with exact endpoints for native retained colors.

    The source lattice is 0,3,5,...31. Retained native even-valued colors are
    never inversely quantized: clamp the final step to their exact 5-bit value.
    """
    channels = []
    for shift in (0, 5, 10):
        channels.append(f"""
            {'mov r5, r3' if shift == 0 else f'lsr r5, r3, #{shift}'}
            and r5, r5, #31
            {'mov r8, r6' if shift == 0 else f'lsr r8, r6, #{shift}'}
            and r8, r8, #31
            cmp r5, r8
            beq channel_{shift}_done
            cmp r5, #0
            moveq r5, #3
            addne r5, r5, #2
            cmp r5, r8
            movhi r5, r8
        channel_{shift}_done:
            orr r4, r4, r5, lsl #{shift or 0}
        """)
    blob = assemble("""
        push {r0-r12, lr}
        cmp r0, #1
        blo done
        cmp r0, #32
        bhi done
        and r7, r0, #1
        mov r1, #0x05000000
        ldr r9, mirror
        add r1, r1, r7, lsl #9
        add r9, r9, r7, lsl #9
        mov r2, #128
    colors:
        ldrh r3, [r1]
        ldrh r6, [r9], #2
        mov r4, #0
    """ + "\n".join(channels) + """
        strh r4, [r1], #2
        subs r2, r2, #1
        bne colors
        cmp r7, #0
        beq canonical_bg_zero
        sub r1, r1, #0x100
        sub r2, r1, #0x100
        mov r3, #8
    aliases:
        ldrh r4, [r1], #0x20
        strh r4, [r2], #0x20
        subs r3, r3, #1
        bne aliases
        b done
    canonical_bg_zero:
        mov r1, #0x05000000
        mov r4, #0
        strh r4, [r1]
    done:
        pop {r0-r12, lr}
        bx lr
    mirror: .word 0x0203E000
    """, TO_TARGET)
    return blob, len(blob) - 4


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    before = args.input.read_bytes()
    sources = {"gba": args.gba.read_bytes(), "wsc15": args.wsc15.read_bytes()}
    require_hash(before, INPUT_SHA256, "palette layer predecessor")
    for key, digest in (("gba", GBA_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], digest, key)
    for key, start, end, digest in ORACLES:
        require_hash(sources[key][start:end], digest, f"{key} palette consumer {start:X}")
    if len(before) != 0x800000 or before[SNAPSHOT:LIMIT] != b"\xff" * (LIMIT - SNAPSHOT):
        raise ValueError("palette placement differs from the owned expansion")
    enclosing_references = []
    for site in range(0, len(before), 4):
        value = struct.unpack_from("<I", before, site)[0]
        if BASE + SNAPSHOT <= value < BASE + LIMIT:
            enclosing_references.append({"site": site, "target": value - BASE, "kind": "aligned pointer"})
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if SNAPSHOT <= site + 8 + delta * 4 < LIMIT:
                enclosing_references.append({"site": site, "target": site + 8 + delta * 4, "kind": "ARM branch encoding"})
    plan, code_reports = [], []
    for start, bound, make, label in (
        (SNAPSHOT, PREPARE, snapshot, "source scene capture projection"),
        (PREPARE, TO_BLACK, prepare, "source selective backup gray targets and white preparation"),
        (TO_BLACK, TO_TARGET, to_black, "source 1267 one-half decrement operation"),
        (TO_TARGET, GRAY_TABLE, to_target, "source 1331 one-half restore operation"),
    ):
        blob, code_bytes = make()
        if start + len(blob) > bound:
            raise ValueError(f"palette routine exceeds placement: {label}")
        code_reports.append({"offset": start, **verify_machine_code(blob, start, code_bytes, set())})
        plan.append((start, b"\xff" * len(blob), blob, label))
    gray = struct.unpack_from("<16H", sources["wsc15"], 0x747E34)
    if gray != tuple(i * 0x111 for i in range(16)):
        raise ValueError("source gray table differs")
    gray_blob = struct.pack("<16H", *(convert_color(color) for color in gray))
    plan.append((GRAY_TABLE, b"\xff" * len(gray_blob), gray_blob, "source gray table converted to BGR555"))
    allowed = set()
    for site, prior, replacement, label in plan:
        region = set(range(site, site + len(replacement)))
        if before[site:site + len(prior)] != prior or region & allowed:
            raise ValueError(f"Expected Write rejected: {label}")
        allowed |= region
    for reference in enclosing_references:
        if reference["target"] in allowed:
            raise ValueError(f"existing {reference['kind']} into a palette write at {reference['site']:X}")
    after = bytearray(before)
    for site, prior, replacement, label in plan:
        after[site:site + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {site + i for site, a, b, label in plan
                for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y}
    if changed != expected:
        raise ValueError("final diff escapes palette Expected Writes")
    report = {
        "schema": 1, "kind": "shoot-resident-palette-operations",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(after), "output_bytes": len(after),
        "entries": {"snapshot": BASE + SNAPSHOT, "prepare": BASE + PREPARE,
                    "to_black": BASE + TO_BLACK, "to_target": BASE + TO_TARGET},
        "generated_code": code_reports,
        "expected_writes": [{"offset": site, "bytes": len(b), "label": label,
                             "before_sha256": sha256(a), "after_sha256": sha256(b)}
                            for site, a, b, label in plan],
        "actual_changed_bytes": len(changed),
        "reference_scan": {"denominator": "all aligned words in exact predecessor", "write_interval_references": 0,
                           "untouched_gap_candidates": enclosing_references,
                           "gap_policy": "preserved byte-for-byte; candidate encodings are not classified as executable code"},
        "contract": {
            "preserves": "r0-r12 and LR; flags clobbered", "new_ram": 0,
            "mirror_ranges": [[0x0203E000, 0x0203E100], [0x0203E200, 0x0203E300]],
            "mirror_bytes": 512,
            "source_rows": "0..7 -> BG0..7; 8..15 -> OBJ0..7 plus BG8..15 color-zero aliases",
            "selective_capture_bytes": 384, "mapped_palette_bytes": 528,
            "step_input": "r0 remaining source callback count 32..1; invalid counts do nothing",
            "native_even_target_channels": "retained exactly by final-step clamp; no inverse quantization",
            "ownership_precondition": "scene-exclusive native mirror and palette ownership from source 1073 capture until source 1331 completes; not established by these uncalled helpers",
            "snapshot_boundary": "before source 1073 destructive transition; scene counter reset remains caller-owned",
            "prepare_boundary": "after source 7394, other-player phase and 74A2 in their original order",
            "schedule": "32 alternating decrement calls, 150 source hold ticks including D2 at remaining 130, 32 alternating restore calls; caller-owned and not installed",
            "bg_zero_alias": "08011468 copies selected background-zero into BG0; on even steps restore canonical source row0 from fixed white-start count or gray target zero",
        },
        "claim_scope": "bounded resident palette operations only; no scene callbacks, sound scheduling, initializer caller, menu, complete ownership lifetime or runtime/save QA",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-palette] static build {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
