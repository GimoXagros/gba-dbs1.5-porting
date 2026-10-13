#!/usr/bin/env python3
"""Bound Shoot palette representation and source mirror lifetime statically.

This reads only the three declared ROM inputs. It does not inspect a save or
run game code. Native literal/call scans have an explicit finite denominator;
they do not establish the absence of indirect or concurrent mirror writers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

PROFILES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
RANGES = (
    ("wsc15", 0x747DDA, 0x747E34, "0415462B683CD87C9576DE4685A59D4F5BA6D3C201090C4D5B0A7A9F2FA40843", "selective backup and white preparation"),
    ("wsc15", 0x747E34, 0x747E54, "C5605A0084D6DFAB01687645085BD7C4CF07C383421BD5F90541F541681C2738", "source gray table"),
    ("wsc15", 0x772061, 0x77208B, "760581E89D46555951EAD46CC68139A6F4881444F5D28E9A9D432ED1ECF5BE04", "source 71F0:0161 full snapshot"),
    ("wsc15", 0x772F43, 0x77329C, "7757A292434FEABC9B696BD172909FDA0FA33A95AA08336B78C75BFE4CD83C6D", "source snapshot to restore state chain"),
    ("gba", 0x11454, 0x11470, "6F8F5B01001BF386ACE8715E2FB8A857F16F43E907D984940D5C2C2BC4D85E90", "actual BG backdrop read"),
    ("gba", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B", "actual OBJ palette load"),
    ("gba", 0x33FDC0, 0x33FE1C, "6A80E9053418E0F07B8FA389EECC9ABB4F9E65464D58C0BC6FDDAF6DD03BF6CD", "retail shared snapshot"),
    ("gba", 0x340A68, 0x340A8C, "267EB4EF9E47FA0A4AA11ADB93AA6319BE914BDA8093E31B744C61B03C7EF752", "retail snapshot restoration"),
    ("gba", 0x375360, 0x3753C0, "0668FB5046500CB9F7863D190917ED37B208E4C83FC4E87B0D29DDEB346534F3", "pause capture and dim"),
    ("gba", 0x3755E4, 0x3757D0, "C15C9FEF475451B62390A91F58416610AA0660CEBBF973E875DA1FDC41F621E2", "pause restore branches"),
    ("wsc10", 0x394A7E, 0x394A99, "C10629CF823DE4A166573D61C06987F8B3DEC147F34625DAB529B69B6ABB26D9", "retail stride-loop lineage"),
    ("gba", 0x3700CC, 0x3700F0, "5835B7C0C6F8CC668C5080951175CE8787027068F01297D8C095F997EC4578AB", "native stride-loop lineage"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def arm_text(data: bytes, start: int, end: int) -> list[str]:
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[start:end], 0x08000000 + start))
    require(sum(i.size for i in decoded) == end - start, "incomplete consumer decoding")
    return [f"{i.mnemonic} {i.op_str}".strip() for i in decoded]


def channel_contract() -> dict:
    # This specification is independent of the palette builder and converter.
    expand = lambda n: 0 if n == 0 else n * 2 + 1
    down = lambda n: 0 if n <= 3 else n - 2
    up = lambda n, target: target if n >= target else min(target, 3 if n == 0 else n + 2)
    for source in range(16):
        require(down(expand(source)) == expand(max(0, source - 1)), "source decrement differs")
        native = 0
        for step in range(17):
            require(native == expand(min(source, step)), "source restore cadence differs")
            native = up(native, expand(source))
    for target in range(32):
        native = 0
        for _ in range(16):
            native = up(native, target)
        require(native == target, "native exact endpoint lost")
    for current in range(32):
        native = current
        for _ in range(16):
            native = down(native)
        require(native == 0, "native decrement endpoint not black")
    return {"source_channel_values": 16, "source_steps_checked": 17,
            "native_channel_endpoints": 32, "native_steps": 16,
            "source_lattice": [expand(n) for n in range(16)],
            "native_even_endpoint_policy": "exact clamp; never quantize stored target"}


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in PROFILES:
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    sources = {name: getattr(args, name).read_bytes() for name in PROFILES}
    for name, value in sources.items():
        require(digest(value) == PROFILES[name], f"unknown input revision: {name}")
    evidence = []
    for name, start, end, expected, label in RANGES:
        require(digest(sources[name][start:end]) == expected, f"source evidence mismatch: {label}")
        evidence.append({"input": name, "range": [start, end], "sha256": expected, "role": label})
    gba, source = sources["gba"], sources["wsc15"]
    require(arm_text(gba, 0x1145C, 0x11470) == [
        "and sl, r0, #0xff00", "mov r8, #0x5000000", "add sl, r8, sl, lsr #7",
        "ldrh sb, [sl]", "strh sb, [r8]"], "BG row-zero native consumer changed")
    require(arm_text(gba, 0x13308, 0x13328) == [
        "ldrh r8, [r4], #4", "sub r8, r8, #8", "ldr r5, [sp, #0x10]",
        "add r5, r5, r8", "add r5, r5, #0x10", "lsl r5, r5, #5",
        "add r5, r5, #0x5000000", "add r5, r5, #2"], "OBJ row native consumer changed")
    require(source[0x772F73:0x772F78] == bytes.fromhex("9A 61 01 F0 71"), "snapshot no longer precedes destructive transition")
    require(source[0x773143:0x773148] == bytes.fromhex("9A 68 71 90 40"), "initializer call differs")
    require(source[0x773266:0x77326B] == bytes.fromhex("9A F5 1E FF 4F"), "saved target no longer consumed")
    require(struct.unpack_from("<16H", source, 0x747E34) == tuple(i * 0x111 for i in range(16)), "gray levels differ")
    rows = []
    for row in range(16):
        primary = 0x05000000 + row * 32 if row < 8 else 0x05000200 + (row - 8) * 32
        rows.append({"source_hardware": 0xFE00 + row * 32, "source_saved": 0x103EA + row * 32,
                     "native_hardware": primary, "native_saved": primary - 0x05000000 + 0x0203E000,
                     "native_background_zero_alias": 0x05000000 + row * 32 if row >= 8 else None,
                     "selected_copy": row in list(range(8)) + [9, 10, 11, 13]})
    selected_bytes = sum(32 for row in rows if row["selected_copy"])
    require(selected_bytes == 384, "selected copy is no longer 384 bytes")
    literal_refs, captures = [], []
    for site in range(0, len(gba), 4):
        value = struct.unpack_from("<I", gba, site)[0]
        if 0x0203E000 <= value < 0x0203E300:
            literal_refs.append({"site": 0x08000000 + site, "value": value})
        if value >> 28 != 15 and value & 0x0F000000 == 0x0B000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if 0x08000000 + site + 8 + delta * 4 == 0x0833FDC0:
                captures.append(0x08000000 + site)
    require(captures == [0x08340110, 0x083403BC, 0x08340728, 0x08340C18, 0x08340EC0], "retail capture direct-call population changed")
    report = {
        "schema": 1, "kind": "shoot-palette-representation-and-source-lifetime",
        "inputs": {name: {"bytes": len(data), "sha256": PROFILES[name]} for name, data in sources.items()},
        "evidence_ranges": evidence, "row_projection": rows,
        "source_selective_bytes": selected_bytes, "mapped_native_bytes": 528,
        "mirror_ranges": [[0x0203E000, 0x0203E100], [0x0203E200, 0x0203E300]],
        "mirror_bytes": 512, "native_high_bg_mirror": "untouched; hardware zero aliases are restored from OBJ mirror zeros",
        "native_bg_high_rows_colors_1_to_15": "preserved; not aliases of OBJ payload",
        "source_lifetime": {"capture": "71F0:1073 -> 0161", "capture_before_black_fill": True,
                            "initializer": "71F0:1243 -> 4090:7168", "saved_target_consumer": "71F0:1331 -> 4FFF:1EF5",
                            "order": ["capture", "prelude black/white", "initializer selective backup/gray/white", "32 white-to-black", "150 hold with D2 at remaining130", "32 black-to-target", "139C"]},
        "native_shared_mirror_refs": {"scan_denominator": "all 4-byte-aligned words in exact retail USA ROM", "literal_references": literal_refs,
                                      "direct_arm_bl_capture_sites": captures, "indirect_writers_excluded": False,
                                      "competing_owner": "retail pause capture 08375360 and restore 08375624/08375754/083757AC"},
        "bg0_alias_hazard": "08011468 reads selected BG color and 0801146C writes BG0; even fade steps must restore source row0 independently of that hardware echo",
        "channel_contract": channel_contract(),
        "ownership_status": "source interval established; native concurrent lifecycle unresolved until scene scheduler excludes competing mirror writers",
        "permitted_implementation": "resident operations with explicit exclusive scene ownership and exact remaining-count preconditions; no external caller",
        "excluded_claims": ["complete initializer", "native scene-exclusive lifetime", "scene callbacks and audio scheduling", "runtime timing", "visual parity", "emulator/save QA"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-palette-ownership] bounded representation PASS; lifecycle unresolved; report {digest(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
