#!/usr/bin/env python3
"""Prove the commercial WSC 1.0/GBA lineage used by a Shoot callback chain.

This report binds three WSC 1.5 callbacks to their WSC 1.0 ancestors and the
corresponding commercial USA GBA callbacks.  It also derives five imported
routine mappings from paired call sites rather than assigning them by name.
No candidate ROM is read or modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
WSC10_OVERLAY_BASE = 0x390900
WSC15_OVERLAY_BASE = 0x740900


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"refusing unknown {label}: {actual}")


def far_call(bank: bytes, offset: int) -> tuple[int, int]:
    if bank[offset] != 0x9A:
        raise SystemExit(f"expected far call at WSC overlay offset 0x{offset:04X}")
    target, segment = struct.unpack_from("<HH", bank, offset + 1)
    return segment, target


def arm_branch_target(rom: bytes, address: int) -> int:
    offset = address - GBA_BASE
    word = struct.unpack_from("<I", rom, offset)[0]
    if word & 0x0F000000 != 0x0B000000:
        raise SystemExit(f"expected ARM BL at 0x{address:08X}")
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def checked_words(rom: bytes, words: dict[int, int]) -> None:
    for address, expected in words.items():
        actual = struct.unpack_from("<I", rom, address - GBA_BASE)[0]
        if actual != expected:
            raise SystemExit(
                f"commercial GBA signature changed at 0x{address:08X}: "
                f"0x{actual:08X} != 0x{expected:08X}"
            )


def range_record(data: bytes, start: int, end: int) -> dict[str, int | str]:
    return {
        "start": start,
        "end": end,
        "bytes": end - start,
        "sha256": sha256(data[start:end]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    old_rom = args.wsc10.read_bytes()
    new_rom = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(old_rom, WSC10_SHA256, "WSC 1.0 source")
    require_hash(new_rom, WSC15_SHA256, "WSC 1.5 source")
    old = old_rom[WSC10_OVERLAY_BASE:WSC10_OVERLAY_BASE + 0x10000]
    new = new_rom[WSC15_OVERLAY_BASE:WSC15_OVERLAY_BASE + 0x10000]

    # These instructions uniquely bind the commercial ARM entry and its two
    # callback stores.  The first body contains the 0x60/0x20 angle clamp,
    # paired trigonometric calls, velocity stores, and animation event 5.
    checked_words(gba, {
        0x08372110: 0xE92D4000,
        0x08372168: 0xE3500060,
        0x08372170: 0xE3500020,
        0x0837218C: 0xE1C404B2,
        0x083721A0: 0xE1C404B4,
        0x083721EC: 0xE28F8008,
        0x083721F0: 0xE5848000,
        0x083721FC: 0xE92D4000,
        0x08372310: 0xE28F8008,
        0x08372314: 0xE5848000,
        0x08372320: 0xE92D4000,
    })

    old_import_sites = {
        "angle": (0x5704, (0x96B2, 0x1C6D)),
        "trig_x": (0x5722, (0x96B2, 0x1A53)),
        "trig_y": (0x5731, (0x96B2, 0x1A3C)),
        "presentation_event": (0x5768, (0x96B2, 0x24EB)),
        "presentation_update": (0x56F0, (0x96B2, 0x2882)),
    }
    new_import_sites = {
        "angle": (0x94F4, (0x4FFF, 0x1BD9)),
        "trig_x": (0x9512, (0x4FFF, 0x19BF)),
        "trig_y": (0x9521, (0x4FFF, 0x19A8)),
        "presentation_event": (0x955E, (0x4FFF, 0x24CB)),
        "presentation_update": (0x94D8, (0x4FFF, 0x2862)),
    }
    gba_import_sites = {
        "angle": 0x0837215C,
        "trig_x": 0x08372180,
        "trig_y": 0x08372194,
        "presentation_event": 0x083721E4,
        "presentation_update": 0x0837213C,
    }

    imports = []
    for name in old_import_sites:
        old_site, expected_old = old_import_sites[name]
        new_site, expected_new = new_import_sites[name]
        actual_old = far_call(old, old_site)
        actual_new = far_call(new, new_site)
        if actual_old != expected_old or actual_new != expected_new:
            raise SystemExit(f"WSC import signature changed for {name}")
        imports.append({
            "role": name,
            "wsc10": {"site": old_site, "segment": actual_old[0], "offset": actual_old[1]},
            "wsc15": {"site": new_site, "segment": actual_new[0], "offset": actual_new[1]},
            "gba": {"site": gba_import_sites[name], "target": arm_branch_target(gba, gba_import_sites[name])},
        })

    expected_gba_targets = {
        "angle": 0x08012560,
        "trig_x": 0x0801233C,
        "trig_y": 0x08012348,
        "presentation_event": 0x08012874,
        "presentation_update": 0x08012A84,
    }
    if {entry["role"]: entry["gba"]["target"] for entry in imports} != expected_gba_targets:
        raise SystemExit("commercial GBA import targets changed")

    # WSC 1.0 callback offsets stored by this overlay are biased by +0x200:
    # CPU 0x597A/0x5A21 select physical 0x577A/0x5821.  GBA PC-relative
    # stores select the corresponding 0x083721FC/0x08372320 entries.
    if old[0x5770:0x5779] != bytes.fromhex("C7 04 7A 59 C7 44 02 70 90"):
        raise SystemExit("WSC 1.0 first callback transition changed")
    if old[0x5817:0x5820] != bytes.fromhex("C7 04 21 5A C7 44 02 70 90"):
        raise SystemExit("WSC 1.0 second callback transition changed")
    if new[0x9566:0x956F] != bytes.fromhex("C7 04 70 95 C7 44 02 90 40"):
        raise SystemExit("WSC 1.5 first callback transition changed")
    if new[0x960D:0x9616] != bytes.fromhex("C7 04 17 96 C7 44 02 90 40"):
        raise SystemExit("WSC 1.5 second callback transition changed")

    callbacks = [
        {
            "role": "initial-vector-and-presentation-state",
            "wsc10_physical_entry": 0x56D9,
            "wsc15_entry": 0x94C1,
            "commercial_gba_entry": 0x08372110,
        },
        {
            "role": "homing-vector-update-state",
            "wsc10_physical_entry": 0x577A,
            "wsc15_entry": 0x9570,
            "commercial_gba_entry": 0x083721FC,
        },
        {
            "role": "completion-and-object-release-state",
            "wsc10_physical_entry": 0x5821,
            "wsc15_entry": 0x9617,
            "commercial_gba_entry": 0x08372320,
        },
    ]
    result = {
        "schema": 1,
        "kind": "digimon-shoot-commercial-callback-lineage",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "callbacks": callbacks,
        "import_mappings": imports,
        "native_object_release": {
            "wsc10_physical_entry": 0x155A,
            "wsc10_cpu_entry": "9070:175A",
            "wsc15_entry": "4090:181E",
            "commercial_gba_entry": 0x083524C4,
            "evidence": "paired completion callbacks call the platform-native object release path",
        },
        "linear_entry_blocks": {
            "wsc10": [
                range_record(old, 0x56D9, 0x577A),
                range_record(old, 0x577A, 0x5821),
                range_record(old, 0x5821, 0x5890),
            ],
            "wsc15": [
                range_record(new, 0x94C1, 0x9570),
                range_record(new, 0x9570, 0x9617),
                range_record(new, 0x9617, 0x966A),
            ],
            "gba": [
                range_record(gba, 0x37110, 0x371FC),
                range_record(gba, 0x371FC, 0x37320),
                range_record(gba, 0x37320, 0x373D8),
            ],
        },
        "claim_scope": (
            "static commercial lineage and imported-routine address proof only; "
            "the WSC 1.5 callback bodies are not yet installed or runtime-verified"
        ),
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
