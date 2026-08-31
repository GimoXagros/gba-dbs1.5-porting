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
FIRST_CHARACTER_TILE = 0x21
GBA_STORED_TILE_BASE = 0x200

# The WSC battle transition composes these two VS portraits into screen RAM.
# The palette and planar tiles are exact ROM-backed resources; only the sparse
# 28x18 placement is dynamic.  Keep that observed placement as a compact,
# reviewable build rule so a clean build never depends on an emulator RAM dump.
PATAMON_MAP_ROWS = (
    "", "", "", "", "",
    "3:2021 4:2022 7:2041 8:2042",
    "2:2023 3:2024 4:2025 5:2026 6:2027 7:2028 8:2029 9:202A",
    "2:2043 3:2044 4:2045 5:2046 6:2047 7:2048 8:2049 9:204A 10:204B",
    "2:202C 3:202D 4:202E 5:202F 6:2030 7:2031 8:2032 9:2033 10:2034",
    "1:204C 2:204D 3:204E 4:204F 5:2050 6:2051 7:2052 8:2053 9:2054 10:2055",
    "1:203C 2:203D 4:203B 5:2035 6:2036 7:2037 8:2038 9:2039 10:203A",
    "1:205D 2:205E 5:2056 6:2057 7:2058 8:2059 9:205A 10:205B 11:205C",
    "1:203E 5:2061 6:2062 7:2063 8:2064 9:2065 10:203F 11:206A",
    "1:205F 5:2066 6:2067 7:2068 8:2069 9:2040 10:2060",
    "", "", "", "",
)
TAILMON_MAP_ROWS = (
    "", "",
    "1:2022 7:2023 8:2024 9:2025 10:2026",
    "1:2028 2:2029 6:202A 7:202B 8:202C 9:202D 10:202E 12:202F 13:2030",
    "1:2032 2:2033 3:2034 4:2035 5:2036 6:2037 7:6035 8:2038 9:2039 10:203A 11:203B 12:203C 13:203D",
    "1:203E 2:203F 3:2040 4:2041 5:2042 6:2043 7:2044 8:2045 9:2046 10:2047 11:2048 12:2049 13:204A",
    "2:204B 3:204C 4:204D 5:204E 6:204F 7:2050 8:2051 9:2052 10:2053 11:2054",
    "2:E035 3:2055 4:2056 5:2057 6:2058 7:2059 8:205A 9:205B 10:205C",
    "3:205D 4:205E 5:205F 6:2060 7:2061 8:2062 9:2063",
    "3:2064 4:2065 5:2066 6:2067 7:2068 8:2069 9:206A",
    "3:206B 4:206C 5:206D 6:206E 7:206F 8:2070 9:2071",
    "2:2072 3:2073 4:2074 5:2075 6:2076 7:2077 8:2078 9:2079",
    "1:207A 2:207B 3:207C 4:207D 5:207E 6:207F 7:2080 8:2081 9:2082 10:2083 11:2035",
    "1:2085 2:2086 3:2087 4:2088 5:2089 7:208A 8:208B 9:208C 10:208D 11:208E",
    "3:208F 9:2090",
    "", "", "",
)
VS_RESOURCES = {
    13: {
        "name": "Patamon",
        "palette_source": 0x3D8950,
        "tile_source": 0x36F6A0,
        "tile_count": 74,
        "map_rows": PATAMON_MAP_ROWS,
    },
    14: {
        "name": "Tailmon",
        "palette_source": 0x3D8970,
        "tile_source": 0x39D600,
        "tile_count": 112,
        "map_rows": TAILMON_MAP_ROWS,
    },
}


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


def convert_map(rows: tuple[str, ...]) -> tuple[bytes, dict[str, int], bytes]:
    if len(rows) != MAP_ROWS:
        raise ValueError(f"VS layout must contain {MAP_ROWS} rows")
    words = [0] * (MAP_COLUMNS * MAP_ROWS)
    for y, row in enumerate(rows):
        for token in row.split():
            x_text, value_text = token.split(":", 1)
            x = int(x_text)
            value = int(value_text, 16)
            if not 0 <= x < MAP_COLUMNS:
                raise ValueError(f"VS layout x={x} is outside row {y}")
            if not value & 0x01FF:
                raise ValueError(f"VS layout entry {token} has tile zero")
            slot = y * MAP_COLUMNS + x
            if words[slot]:
                raise ValueError(f"duplicate VS layout entry at ({x}, {y})")
            words[slot] = value
    converted = []
    points = []
    for y in range(MAP_ROWS):
        for x in range(MAP_COLUMNS):
            value = words[y * MAP_COLUMNS + x]
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
    packed_wsc = struct.pack(f"<{len(words)}H", *words)
    return struct.pack(f"<{len(converted)}H", *converted), metadata, packed_wsc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
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
    for runtime_id in (13, 14):
        resource = VS_RESOURCES[runtime_id]
        tilemap, meta, packed_wsc_map = convert_map(resource["map_rows"])
        tile_count = resource["tile_count"]
        if meta["tile_count"] != tile_count:
            raise ValueError(
                f"ID {runtime_id} layout reaches {meta['tile_count']} tiles, expected {tile_count}"
            )
        tile_source = resource["tile_source"]
        tile_data = b"".join(
            wsc_planar_to_gba(wsc[tile_source + index * 32:tile_source + (index + 1) * 32])
            for index in range(tile_count)
        )
        palette_source = resource["palette_source"]
        palette = convert_palette(wsc[palette_source:palette_source + 0x20])

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
            "name": resource["name"],
            "wsc_palette_source": palette_source,
            "wsc_tile_source": tile_source,
            "wsc_layout_sha256": hashlib.sha256(packed_wsc_map).hexdigest().upper(),
            "layout_policy": "sparse 28x18 runtime composition encoded in the generator",
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
