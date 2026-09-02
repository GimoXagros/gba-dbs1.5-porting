#!/usr/bin/env python3
"""Bind the two resolved resource segments of the existing Shoot initializer.

These resident entries implement 7394..73A9 and 74A2..74DA, not the whole
tail. The intervening 6D/137 preloads, global clears, palette backup/transition
and outer entry remain unresolved. No caller is installed prematurely.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import (
    GBA_SHA256, WSC15_SHA256, assemble, require_hash, sha256, verify_machine_code,
)
from build_full_asset_poc import build_far_descriptor_payload
from convert_wsc_palette_block import convert_block

INPUT_SHA256 = "93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E"
BASE = 0x08000000
EARLY, LATE, LIMIT = 0x5C1700, 0x5C1800, 0x5C1900
ORACLES = (
    ("wsc15", 0x747C94, 0x747CD6, "0E765563684620CF6D111063F73AAD2C50B9AFAE63AA3263F0B9F6B162246642"),
    ("wsc15", 0x747DA2, 0x747DDA, "5E7435280C26FDFAE5701D912A1F0914BEF5218829A684DD117F6C7D1B644DAE"),
    ("wsc15", 0x74918B, 0x7491BA, "2C1580D4E6EBDF6A27F8C4E0AD854263E85781AB7CFBC92FE830F697A4903CA8"),
    ("wsc15", 0x749CE7, 0x749D15, "513B405B41459A9A13109ACADECFCB4F7E3156FC5A8E54C885416B7260D0A138"),
    ("gba", 0xD161C, 0xD1724, "11A792E2BFE47461E1B37668B924D2A6D5B7DD458CBAE94E93725093D9407C89"),
    ("gba", 0x370138, 0x37016C, "A5EB158EAD122DE826D0A481B3BA15EED79430232351A1A31A1B43A0D775E130"),
    ("gba", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
)


def early_phase() -> tuple[bytes, int]:
    blob = assemble("""
        push {r0-r12, lr}
        ldr r8, palette
        push {r8}
        mov r8, #0
        push {r8}
        push {r8}
        push {r8}
        mov r8, #5
        push {r8}
        mov r11, #0
        bl 0x080132EC
        add sp, sp, #20
        pop {r0-r12, lr}
        bx lr
    palette: .word 0x085DB740
    """, EARLY)
    return blob, len(blob) - 4


def late_phase() -> tuple[bytes, int]:
    # Source direct P0 91 is the exact 128-byte commercial HUD tile payload.
    # The native OAM consumer selects tile 3FC, palette 6, not WS tile 91.
    blob = assemble("""
        push {r0-r12, lr}
        ldr r0, tiles
        ldr r1, tile_destination
        mov r2, #32
    copy_tiles:
        ldr r3, [r0], #4
        str r3, [r1], #4
        subs r2, r2, #1
        bne copy_tiles
        ldr r8, palette
        push {r8}
        mov r8, #0
        push {r8}
        push {r8}
        push {r8}
        push {r8}
        mov r11, #0
        bl 0x080132EC
        add sp, sp, #20
        ldr r0, scroll_state
        mov r1, #0
        strh r1, [r0]
        pop {r0-r12, lr}
        bx lr
    tiles: .word 0x080D2FD0
    tile_destination: .word 0x06017F80
    palette: .word 0x080D3078
    scroll_state: .word 0x03004D40
    """, LATE)
    return blob, len(blob) - 16


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    before = args.input.read_bytes()
    sources = {"gba": args.gba.read_bytes(), "wsc15": args.wsc15.read_bytes()}
    require_hash(before, INPUT_SHA256, "v49")
    for key, digest in (("gba", GBA_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], digest, key)
    for key, start, end, digest in ORACLES:
        require_hash(sources[key][start:end], digest, f"{key} consumer {start:X}")
    if len(before) != 0x800000 or before[EARLY:LIMIT] != b"\xff" * (LIMIT - EARLY):
        raise ValueError("tail resource placement is not free in the exact predecessor")
    for site in range(0, len(before), 4):
        value = struct.unpack_from("<I", before, site)[0]
        if BASE + EARLY <= value < BASE + LIMIT:
            raise ValueError(f"existing pointer into placement at {site:X}")
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if EARLY <= site + 8 + delta * 4 < LIMIT:
                raise ValueError(f"existing ARM branch into placement at {site:X}")
    wsc, gba = sources["wsc15"], sources["gba"]
    tiles, details = build_far_descriptor_payload(wsc, wsc_header=0x3D7D30, target=0x5F5360, count=1)
    if details["tile_bytes"] != 128 or before[0x5F5360:0x5F5360 + len(tiles)] != tiles:
        raise ValueError("installed HUD P0 descriptor/payload differs")
    tile_offset = struct.unpack_from("<I", tiles, 4)[0] - BASE - 0x5F5360
    if tiles[tile_offset:tile_offset + 128] != gba[0xD2FD0:0xD3050]:
        raise ValueError("commercial HUD tile reuse is not byte-identical")
    for source, native in ((0x3D7A90, 0x5DB740), (0x3D6B16, 0xD3078)):
        if convert_block(wsc[source:source + 38]) != before[native:native + 40]:
            raise ValueError("P2 consumer is not bound to the converted source palette")
    if gba[0xD1770:0xD1778] != struct.pack("<II", 0x080D2FD0, 0x06017F80):
        raise ValueError("native HUD producer literals differ")
    plan, code_reports = [], []
    for start, bound, make, label in ((EARLY, LATE, early_phase, "source 7394..73A9 OBJ slot-5 palette"),
                                      (LATE, LIMIT, late_phase, "source 74A2..74DA HUD and scroll reset")):
        blob, code_bytes = make()
        if start + len(blob) > bound:
            raise ValueError("resident resource phase exceeds its declared range")
        code_reports.append(verify_machine_code(blob, start, code_bytes, {0x080132EC}))
        plan.append((start, b"\xff" * len(blob), blob, label))
    allowed = set()
    for site, prior, replacement, label in plan:
        owned = set(range(site, site + len(replacement)))
        if before[site:site + len(prior)] != prior or owned & allowed:
            raise ValueError(f"Expected Write rejected: {label}")
        allowed |= owned
    after = bytearray(before)
    for site, prior, replacement, label in plan:
        after[site:site + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {site + i for site, a, b, label in plan
                for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y}
    if changed != expected:
        raise ValueError("final image changes escape the two planned writes")
    report = {
        "schema": 1, "kind": "shoot-tail-resident-resource-binding",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(after), "output_bytes": len(after),
        "entries": [BASE + EARLY, BASE + LATE], "generated_code": code_reports,
        "expected_writes": [{"offset": site, "bytes": len(b), "label": label,
                             "before_sha256": sha256(a), "after_sha256": sha256(b)}
                            for site, a, b, label in plan],
        "actual_changed_bytes": len(changed),
        "resource_contract": {"early_obj_palette": 5, "late_obj_palette": 6,
                              "hud_tile_indices": [1020, 1024], "hud_tile_bytes": 128,
                              "palette_color_zero_preserved": True, "scroll_state": 0x03004D40,
                              "preserves": "r0-r12 and LR; condition flags not preserved"},
        "unresolved": ["73A9..73D6 P0 preloads 6D/137 and later constructor sites 93E7/888B",
                       "73D6..73F0 source global clear mapping", "74DA..7534 palette backup and white transition",
                       "outer initializer/lifetime, lower rules, controller/menu entry, final runtime/save QA"],
        "claim_scope": "two resident initializer resource segments only; no external caller, complete initializer, palette ownership, gameplay or runtime evidence",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-tail-resources] static build {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
