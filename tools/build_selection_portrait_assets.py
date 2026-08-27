#!/usr/bin/env python3
"""Build GBA selection portraits for the Ver. 1.5 base additions."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
PALETTE_BYTES = 0x20
TILE_BYTES = 0x1800
SOURCES = {
    12: {"palette": 0x449060, "tiles": 0x449080, "character": "Extra Guilmon"},
    13: {"palette": 0x469060, "tiles": 0x469080, "character": "Patamon"},
    14: {"palette": 0x459060, "tiles": 0x459080, "character": "Tailmon/Gatomon"},
}


def parse_int(value: str) -> int:
    return int(value, 0)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target-base", type=parse_int, default=0x47C000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    blob = bytearray()
    entries = []
    cursor = args.target_base
    for runtime_id, source in SOURCES.items():
        cursor = align(cursor, 0x10)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        palette_values = struct.unpack_from("<16H", wsc, source["palette"])
        palette = struct.pack("<16H", *(convert_color(value) for value in palette_values))
        if len(palette) != PALETTE_BYTES:
            raise AssertionError("selection portrait palette size invariant failed")
        tile_source = wsc[source["tiles"]:source["tiles"] + TILE_BYTES]
        if len(tile_source) != TILE_BYTES:
            raise ValueError("selection portrait tile source is truncated")
        tiles = b"".join(convert_tile(tile_source[index:index + 32])
                         for index in range(0, len(tile_source), 32))
        palette_target = cursor
        tile_target = cursor + len(palette)
        blob.extend(palette)
        blob.extend(tiles)
        cursor += len(palette) + len(tiles)
        entries.append({
            "runtime_id": runtime_id,
            "character": source["character"],
            "source_palette": source["palette"],
            "source_tiles": source["tiles"],
            "palette_target": palette_target,
            "tile_target": tile_target,
            "palette_bytes": len(palette),
            "tile_bytes": len(tiles),
            "palette_sha256": hashlib.sha256(palette).hexdigest().upper(),
            "tile_sha256": hashlib.sha256(tiles).hexdigest().upper(),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "relocatable-gba-selection-portraits",
        "claim_scope": "direct WSC selection portrait and palette conversion",
        "source_wsc_sha256": digest,
        "target_base": args.target_base,
        "target_end": args.target_base + len(blob),
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "entries": entries,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
