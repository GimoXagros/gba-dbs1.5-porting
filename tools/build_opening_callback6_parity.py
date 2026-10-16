#!/usr/bin/env python3
"""Apply the remaining WSC1.5 callback-6 position/event/flag/palette changes.

This layer follows the resource ABI repair and preserves every prior layer.
The six-instruction flag adapter preserves the source's two distinct writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
INPUT_SHA256 = "3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ENTRY, END = 0x621C00, 0x621C20
ADAPTER = bytes.fromhex("b880d4e10189c8e3b880c4e1028b88e3b880c4e17b8de9ea")


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def word(data: bytes, raw: int) -> int:
    return struct.unpack_from("<I", data, raw)[0]


def half(data: bytes, raw: int) -> int:
    return struct.unpack_from("<H", data, raw)[0]


def branch(at: int, target: int) -> int:
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM B range")
    return 0xEA000000 | ((delta >> 2) & 0xFFFFFF)


def inbounds(data: bytes, first: int, last: int) -> dict:
    pointers, branches = [], []
    # Every possible little-endian pointer, including unaligned addresses.
    for raw in range(len(data) - 3):
        if BASE + first <= word(data, raw) < BASE + last:
            pointers.append(raw)
    for raw in range(0, len(data) - 3, 4):
        value = word(data, raw)
        if value & 0x0E000000 == 0x0A000000 and value >> 28 != 15:
            immediate = value & 0xFFFFFF
            if immediate & 0x800000:
                immediate -= 0x1000000
            if first <= raw + 8 + immediate * 4 < last:
                branches.append(raw)
    return {"unaligned_pointer_hits": pointers, "aligned_ARM_branch_like_hits": branches}


def palette_contract(before: bytes, wsc15: bytes) -> dict:
    row = 0x3CEC40 + 13 * 32
    tile_window = half(wsc15, row + 2) * 16
    palette_window = half(wsc15, row + 8) * 16 + half(wsc15, row + 6)
    need(0x20000 <= tile_window < 0x30000 and 0x20000 <= palette_window < 0x30000,
         "source C2-mapped 64 KiB window")
    tile_raw = (half(wsc15, row + 4) & 0x7F) * 0x10000 + tile_window - 0x20000
    palette_raw = (half(wsc15, row + 10) & 0x7F) * 0x10000 + palette_window - 0x20000
    count = half(wsc15, row + 28)
    need((tile_raw, palette_raw, count) == (0x36F6A0, 0x3D8950, 74), "source VS selector 13")
    need(word(before, 0x88244) == BASE + 0x4A7C60, "native VS view literal")
    native = 0x4A7C60 + 13 * 28
    native_tiles, native_palette = word(before, native) - BASE, word(before, native + 4) - BASE
    need((native_tiles, native_palette, half(before, native + 22)) ==
         (0x4A5D20, 0x4A5D00, count), "native VS selector 13 pointers/count")
    need((word(before, 0x88248), word(before, 0x8824C)) ==
         (0x06004000, 0x02018020), "native VRAM/palette-shadow destinations")
    colors = []
    expand = lambda component: component * 2 + int(component != 0)
    for color in struct.unpack_from("<16H", wsc15, palette_raw):
        need(color < 0x1000, "source RGB444 palette range")
        colors.append(expand(color >> 8 & 15) | expand(color >> 4 & 15) << 5 |
                      expand(color & 15) << 10)
    need(before[native_palette:native_palette + 32] == struct.pack("<16H", *colors),
         "exact converted selector-13 palette")
    converted = bytearray()
    for tile in range(count):
        for y in range(8):
            planes = wsc15[tile_raw + tile * 32 + y * 4:tile_raw + tile * 32 + y * 4 + 4]
            pixels = [sum(((planes[k] >> (7 - x)) & 1) << k for k in range(4)) for x in range(8)]
            converted.extend(pixels[x] | pixels[x + 1] << 4 for x in range(0, 8, 2))
    need(before[native_tiles:native_tiles + count * 32] == converted, "all 74 VS tiles")
    return {"selector": 13, "source_descriptor": row, "source_tiles": tile_raw,
            "source_palette": palette_raw, "tile_count": count, "pixels_checked": count * 64,
            "native_descriptor": native, "native_tiles": BASE + native_tiles,
            "native_palette": BASE + native_palette, "consumer": BASE + 0x881F0,
            "tile_destination": 0x06004000, "palette_destination": 0x05000000,
            "palette_shadow": 0x02018020, "source_tiles_sha256": sha(wsc15[tile_raw:tile_raw + count * 32]),
            "source_palette_sha256": sha(wsc15[palette_raw:palette_raw + 32])}


def build(before: bytes, gba: bytes, wsc10: bytes, wsc15: bytes) -> tuple[bytes, dict]:
    need(len(before) == 0x800000 and sha(before) == INPUT_SHA256, "fixed post-ABI predecessor")
    need(tuple(map(sha, (gba, wsc10, wsc15))) ==
         (GBA_SHA256, WSC10_SHA256, WSC15_SHA256), "original ROM identities")
    guards = (
        (wsc15, 0x756F05, 0x756F3D, "2A8A7601DDAD0258BCF2B60CB9C72FC1D41E60794FE11455EC58641B5C35E953", "source15 callback 6"),
        (wsc10, 0x39D97C, 0x39D9AC, "9A079FF265B17CBBF3BF84C3D506225F6CB6E522893B3E4164AC955EB36A1FB9", "source10 callback 6"),
        (gba, 0x851CC, 0x85230, "416157CE3BD557594A00238C429F2A42EE0257E6799761B959F5DEB756AFB033", "commercial callback 6"),
        (before, 0x851CC, 0x85230, "4C527246055A4B5C0438E32ECAFDE4224A86DE8C25EC6C004C21ECAC1FA6FF36", "integrated callback 6"),
        (wsc15, 0x75A51C, 0x75A58C, "8A57C664C482BED9E7D2061B815F700344DEA5A7569AB3636AD99D265694AB2C", "source15 VS palette helper"),
        (wsc10, 0x39FBC7, 0x39FC37, "04129885ABB2DF916815786EAFC05BCEE57CFE19FB88CC76B728143D01F4FE59", "source10 VS palette helper"),
        (before, 0x881F0, 0x88244, "203365C08099ABB76D51A94ABF52C583BE9836631E54DBAC9D696F9EE710B081", "native VS palette helper"),
        (before, 0x5B8040, 0x5B8054, "197FB1080B7C8EAA8C6965B3D4BFE69DCCBB895E2819F353058A8EF7DF2E3762", "existing auxiliary bridge"),
    )
    for data, first, last, digest, label in guards:
        need(sha(data[first:last]) == digest, label)
    need(before[0x881F0:0x88244] == gba[0x881F0:0x88244], "preserved native palette consumer")
    need(word(before, 0x853F4) == BASE + 0x5B5400, "already repaired opening resource view")
    need(before[ENTRY:END] == b"\xFF" * (END - ENTRY), "blank reserved adapter allocation")
    inbound = inbounds(before, ENTRY, END)
    need(not any(inbound.values()), "possible inbound into adapter allocation")
    interior = inbounds(before, 0x851FC, 0x85208)
    need(not any(interior.values()), "unexpected external entry into replaced flag block")
    palette = palette_contract(before, wsc15)
    patches = (
        (0x851EC, struct.pack("<I", 0xE3A09096), struct.pack("<I", 0xE3A0909E), "source X = 0x9E"),
        (0x851FC, struct.pack("<I", 0xE1D480B8), struct.pack("<I", branch(0x851FC, ENTRY)), "ordered source flag writes"),
        (0x85210, struct.pack("<I", 0xE3A08002), struct.pack("<I", 0xE3A08000), "source initial event 0"),
        (0x85220, struct.pack("<I", 0xE3A08003), struct.pack("<I", 0xE3A0800D), "source VS palette selector 13"),
        (ENTRY, b"\xFF" * len(ADAPTER), ADAPTER, "ARM7TDMI ordered flags adapter"),
    )
    after = bytearray(before)
    for raw, expected, replacement, label in patches:
        need(before[raw:raw + len(expected)] == expected, "Expected Write: " + label)
        after[raw:raw + len(expected)] = replacement
    allowed = {raw + k for raw, expected, replacement, _ in patches
               for k, (old, new) in enumerate(zip(expected, replacement, strict=True)) if old != new}
    changed = {i for i, (old, new) in enumerate(zip(before, after, strict=True)) if old != new}
    need(changed == allowed, "complete-ROM Expected Write diff")
    return bytes(after), {
        "schema": 1, "kind": "opening-callback6-parity", "input_sha256": INPUT_SHA256,
        "output_sha256": sha(after), "changed_bytes": len(changed), "output_bytes": len(after),
        "expected_writes": [{"raw": raw, "bytes": len(expected), "before_hex": expected.hex(),
                             "after_hex": replacement.hex(), "label": label}
                            for raw, expected, replacement, label in patches],
        "allocation_inbound_scan": inbound, "replaced_flag_block_inbound_scan": interior,
        "adapter": {"entry": BASE + ENTRY, "bytes": len(ADAPTER), "instructions": 6,
                    "live_in": "r4 = current presentation", "clobbers": ["r8"],
                    "preserves": "all other registers, SP, LR, CPSR flags",
                    "ordered_writes": ["flags &= 0xBFFF", "flags |= 0x0800"],
                    "return_branch": BASE + 0x85208},
        "source_guards": [{"raw": first, "end_exclusive": last, "sha256": digest, "label": label}
                          for _, first, last, digest, label in guards],
        "palette_consumer": palette, "new_RAM_owner": False,
        "runtime_status": "not launched by this builder; separate root-owned validation",
        "language_selection_changed": False, "provided_save_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    paths = [getattr(args, key) for key in ("input", "gba", "wsc10", "wsc15", "output", "manifest")]
    need(all(path.suffix.lower() != ".sav" for path in paths), "save paths forbidden")
    result, report = build(*(path.read_bytes() for path in paths[:4]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[opening-callback6-parity] " + report["output_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
