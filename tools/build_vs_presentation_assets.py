#!/usr/bin/env python3
"""Build expanded VS portraits while relocating the GBA boss sentinel."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
SOURCE_DESCRIPTOR_TABLE = 0x09B920
SOURCE_DESCRIPTOR_COUNT = 13
DESCRIPTOR_BYTES = 0x1C
TARGET_BASE = 0x4A5D00
MAP_COLUMNS = 28
MAP_ROWS = 18
WSC_MAP = 0x0800
WSC_TILE_BASE = 0x8000
FIRST_CHARACTER_TILE = 0x21
GBA_STORED_TILE_BASE = 0x200


def align(value: int, boundary: int = 4) -> int:
    return (value + boundary - 1) & -boundary


def wsc_planar_to_gba(tile: bytes) -> bytes:
    if len(tile) != 32:
        raise ValueError("WSC tile must be 32 bytes")
    output = bytearray()
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        pixels = []
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
        output.extend(pixels[index] | (pixels[index + 1] << 4) for index in range(0, 8, 2))
    return bytes(output)


def expand_channel(value: int) -> int:
    return (value << 1) | int(value != 0)


def convert_palette(source: bytes) -> bytes:
    colors = struct.unpack("<16H", source)
    converted = []
    for value in colors:
        if value & 0xF000:
            raise ValueError(f"invalid WSC BGR444 color 0x{value:04X}")
        blue = expand_channel(value & 0xF)
        green = expand_channel((value >> 4) & 0xF)
        red = expand_channel((value >> 8) & 0xF)
        converted.append(red | (green << 5) | (blue << 10))
    return struct.pack("<16H", *converted)


def convert_map(ram: bytes) -> tuple[bytes, dict[str, int]]:
    words = struct.unpack_from("<1024H", ram, WSC_MAP)
    converted = []
    points = []
    for y in range(MAP_ROWS):
        for x in range(MAP_COLUMNS):
            value = words[y * 32 + x]
            tile = value & 0x01FF
            if not tile:
                converted.append(0)
                continue
            if tile < FIRST_CHARACTER_TILE:
                raise ValueError(f"unexpected shared tile 0x{tile:X} in character map")
            gba_tile = GBA_STORED_TILE_BASE + tile - FIRST_CHARACTER_TILE
            flips = (value & 0xC000) >> 4
            converted.append(gba_tile | flips)
            points.append((x, y, tile))
    if not points:
        raise ValueError("character map is empty")
    max_tile = max(point[2] for point in points)
    metadata = {
        "nonzero_tiles": len(points),
        "min_x": min(point[0] for point in points),
        "max_x": max(point[0] for point in points),
        "min_y": min(point[1] for point in points),
        "max_y": max(point[1] for point in points),
        "min_tile": min(point[2] for point in points),
        "max_tile": max_tile,
        "tile_count": max_tile - FIRST_CHARACTER_TILE + 1,
    }
    return struct.pack(f"<{len(converted)}H", *converted), metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("patamon_ram", type=pathlib.Path)
    parser.add_argument("tailmon_ram", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if hashlib.sha256(wsc).hexdigest().upper() != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC 1.5 input")

    blob = bytearray()
    entries = []
    descriptors: dict[int, tuple[int, ...]] = {}
    for runtime_id, ram_path in ((13, args.patamon_ram), (14, args.tailmon_ram)):
        ram = ram_path.read_bytes()
        if len(ram) != 0x10000:
            raise SystemExit(f"{ram_path} is not a complete 64 KiB WSC RAM dump")
        tilemap, meta = convert_map(ram)
        tile_count = meta["tile_count"]
        tile_source = WSC_TILE_BASE + FIRST_CHARACTER_TILE * 32
        tile_data = b"".join(
            wsc_planar_to_gba(ram[tile_source + index * 32:tile_source + (index + 1) * 32])
            for index in range(tile_count)
        )
        palette = convert_palette(ram[0xFE00:0xFE20])

        palette_target = TARGET_BASE + len(blob)
        blob.extend(palette)
        tile_target = TARGET_BASE + len(blob)
        blob.extend(tile_data)
        map_target = TARGET_BASE + len(blob)
        blob.extend(tilemap)
        while len(blob) % 4:
            blob.append(0)

        width = meta["max_x"] + 1
        horizontal_offset = (width - 16) * 8
        vertical_offset = (16 - meta["max_y"]) * 8
        descriptors[runtime_id] = (
            GBA_BASE + tile_target,
            GBA_BASE + palette_target,
            GBA_BASE + map_target,
            horizontal_offset & 0xFFFF,
            (width << 16) | (vertical_offset & 0xFFFF),
            (tile_count << 16) | MAP_ROWS,
            0,
        )
        entries.append({
            "runtime_id": runtime_id,
            "ram_path": str(ram_path),
            "ram_sha256": hashlib.sha256(ram).hexdigest().upper(),
            "palette_target": palette_target,
            "tile_target": tile_target,
            "map_target": map_target,
            "palette_bytes": len(palette),
            "tile_bytes": len(tile_data),
            "map_bytes": len(tilemap),
            "map": meta,
            "descriptor": [f"0x{value:08X}" for value in descriptors[runtime_id]],
        })

    descriptor_target = TARGET_BASE + len(blob)
    original = gba[
        SOURCE_DESCRIPTOR_TABLE:
        SOURCE_DESCRIPTOR_TABLE + SOURCE_DESCRIPTOR_COUNT * DESCRIPTOR_BYTES
    ]
    # Retail descriptor 12 belongs to the Millenniummon boss sentinel.  Ver.
    # 1.5 assigns playable Extra Guilmon ID 12, so keep retail IDs 0..11,
    # reuse Guilmon's presentation for ID 12, append the two reconstructed
    # portraits, then move the boss presentation to sentinel ID 15.
    blob.extend(original[:12 * DESCRIPTOR_BYTES])
    blob.extend(original[:DESCRIPTOR_BYTES])
    for runtime_id in (13, 14):
        blob.extend(struct.pack("<7I", *descriptors[runtime_id]))
    blob.extend(original[12 * DESCRIPTOR_BYTES:13 * DESCRIPTOR_BYTES])
    if len(blob) % 4:
        raise AssertionError("VS blob is not word aligned")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    result = {
        "schema": 1,
        "source_gba_sha256": GBA_SHA256,
        "source_wsc_sha256": WSC15_SHA256,
        "target_base": TARGET_BASE,
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "descriptor_table_target": descriptor_target,
        "descriptor_count": 16,
        "descriptor_policy": {
            "ID 12": "Extra Guilmon reuses Guilmon VS presentation",
            "IDs 13/14": "reconstructed Patamon/Tailmon presentations",
            "ID 15": "relocated retail Millenniummon boss presentation",
        },
        "entries": entries,
        "claim_scope": "VS presentation palette, packed tiles, and 28x18 maps reconstructed from verified WSC runtime state",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
