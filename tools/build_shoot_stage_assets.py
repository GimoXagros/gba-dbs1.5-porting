#!/usr/bin/env python3
"""Repair Shoot assets from the actual bank/segment/descriptor consumers.

This layer preserves the older stage builder and its reproducible outputs.
Only Shoot palette/tiles and resource records 29/30 are replaced; twelve
source-addressed maps and their native descriptors occupy a checked ROM hole.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_poc import convert_planar_tile
from build_stage_assets import convert_map, convert_palette

INPUT_SHA256 = "6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29"
WSC_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, START, END = 0x08000000, 0x5EF000, 0x5F2000
MAPS, DESCRIPTORS = START, START + 12 * 0x3F0
SOURCE_GUARDS = (
    (0x77DD29, 0x77DDFC, "9CF033AB8422CE655BDE1BC2F08F46548C89CA3540E598273E8B285259DBB284"),
    (0x752F8C, 0x75301E, "D81BB04710329235EC05FE021E0B1A6996CDEA9430F91E7CF55D05716198C385"),
    (0x75301E, 0x7530B9, "7BB87B6548EA7C1C8633D85EE251EEC29DEA68519DFD27AC371892158A7DB252"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_layout(source: bytes) -> tuple[int, list[int]]:
    for start, end, expected in SOURCE_GUARDS:
        require(sha(source[start:end]) == expected, f"source consumer {start:X} changed")
    # 77DD2C C3=C9; 77DD44 DS=383F. C3 selects physical 30000..3FFFF.
    bank = struct.unpack_from("<H", source, 0x77DD2D)[0]
    segment = struct.unpack_from("<H", source, 0x77DD45)[0]
    require((bank, segment) == (0xC9, 0x383F), "Shoot bank/segment differs")
    asset_base = (bank & 0x7F) * 0x10000 + ((segment << 4) & 0xFFFF)
    maps = []
    for index in (0x27, 0x28):
        record = 0x3B4DD0 + index * 24
        width, height = struct.unpack_from("<HH", source, record)
        descriptor, map_segment = struct.unpack_from("<HH", source, record + 8)
        require((width, height, map_segment) == (2, 3, segment), "Shoot source resource geometry differs")
        for ordinal in range(width * height):
            at = 0x3B4970 + descriptor + ordinal * 4
            selected_bank, mode, offset = struct.unpack_from("<BBH", source, at)
            require((selected_bank, mode) == (bank, 1), "source map descriptor differs")
            linear = (map_segment << 4) + offset
            require(0x30000 <= linear and linear + 0x3F0 <= 0x40000, "map crosses C3 window")
            maps.append((selected_bank & 0x7F) * 0x10000 + (linear & 0xFFFF))
    require(maps == [0x49C4D0 + i * 0x3F0 for i in range(12)], "source descriptor order changed")
    return asset_base, maps


def build(original: bytes, source: bytes) -> tuple[bytes, dict]:
    require(sha(original) == INPUT_SHA256, "wrong graphics predecessor")
    require(sha(source) == WSC_SHA256, "wrong WSC1.5 original")
    require(original[START:END] == b"\xFF" * (END - START), "asset relocation hole is not blank")
    for at in range(0, len(original) - 3, 4):
        word = struct.unpack_from("<I", original, at)[0]
        require(not BASE + START <= word < BASE + END, f"inbound ROM pointer {at:X}")
        if word & 0x0E000000 == 0x0A000000:
            relative = word & 0xFFFFFF
            if relative & 0x800000:
                relative -= 0x1000000
            require(not START <= at + 8 + relative * 4 < END, f"inbound ARM-like branch {at:X}")
    asset_base, addresses = source_layout(source)
    source_colors = struct.unpack_from("<112H", source, asset_base)
    require(all(value <= 0xFFF or (i % 16 == 0 and value == 0xFFFF)
                for i, value in enumerate(source_colors)), "source palette has unexpected high bits")
    # The source writes FFFF into each transparent slot; palette hardware
    # consumes only the twelve color bits. Native representation is 7FFF.
    palette = convert_palette(struct.pack("<112H", *(value & 0xFFF for value in source_colors)))
    tiles = b"".join(convert_planar_tile(source[p:p + 32]) for p in range(asset_base + 0xE0, asset_base + 0x40E0, 32))
    maps = b"".join(convert_map(source[p:p + 0x3F0]) for p in addresses)
    descriptors = b"".join(struct.pack("<II", 0x101, BASE + MAPS + i * 0x3F0) for i in range(12))
    rows = [
        (0x5A8000, palette, "source-addressed Shoot palette"),
        (0x5A8100, tiles, "source-addressed Shoot 512 tiles"),
        (MAPS, maps, "twelve source-addressed Shoot maps"),
        (DESCRIPTORS, descriptors, "twelve native map descriptors"),
    ]
    for layer, resource in enumerate((29, 30)):
        at = 0x580000 + resource * 24
        before = original[at:at + 24]
        require(struct.unpack_from("<HH", before) == (2, 2), "prior bounded Shoot geometry differs")
        require(struct.unpack_from("<I", before, 8)[0] == BASE + 0x5804F0 + layer * 32, "prior Shoot descriptor pointer differs")
        after = bytearray(before)
        struct.pack_into("<HH", after, 0, 2, 3)
        struct.pack_into("<I", after, 8, BASE + DESCRIPTORS + layer * 48)
        rows.append((at, bytes(after), f"Shoot resource {resource} original 2x3 geometry"))
    output = bytearray(original)
    allowed = set()
    writes = []
    for at, blob, label in rows:
        positions = set(range(at, at + len(blob)))
        require(not allowed & positions, "overlapping Expected Writes")
        allowed |= positions
        before = original[at:at + len(blob)]
        output[at:at + len(blob)] = blob
        writes.append({"offset": at, "bytes": len(blob), "label": label,
                       "before_sha256": sha(before), "after_sha256": sha(blob)})
    changed = {i for i, (a, b) in enumerate(zip(original, output, strict=True)) if a != b}
    expected = {at + i for at, blob, _ in rows for i, value in enumerate(blob) if original[at + i] != value}
    require(changed == expected, "complete-ROM Expected Write mismatch")
    return bytes(output), {
        "schema": 1, "kind": "shoot-source-addressed-stage-assets", "input_sha256": INPUT_SHA256,
        "source_sha256": WSC_SHA256, "output_sha256": sha(output),
        "source_palette": asset_base, "source_tiles": asset_base + 0xE0, "source_maps": addresses,
        "map_geometry_each_layer": [2, 3], "map_count": 12, "tiles": 512,
        "source_bank": 0xC9, "source_segment": 0x383F,
        "expected_writes": writes, "actual_changed_bytes": len(changed),
        "claim_scope": "actual source and commercial-native consumers; no CPU execution, no scene entry, no playability claim",
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for key in ("input", "wsc15", "output"):
        p.add_argument(key, type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path, required=True)
    args = p.parse_args()
    output, report = build(args.input.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-stage-assets] {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
