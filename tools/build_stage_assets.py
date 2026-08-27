#!/usr/bin/env python3
"""Build deterministic GBA-format bundles for the three Ver. 1.5 arenas."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_poc import convert_planar_tile
from convert_wsc_palette_block import convert_color


WSC_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


STAGES = {
    "train": {
        "palette": 0x430000,
        "tiles": 0x4300E0,
        "maps": 0x435000,
        "map_count": 16,
        "target_palette": 0x590000,
        "target_tiles": 0x590100,
        "target_maps": 0x594100,
    },
    "impmon": {
        # The dedicated Iraira Room reuses the retail digital-stage tile
        # payload and appends eight new 28x18 maps after its eight old maps.
        "palette": 0x4C0000,
        "tiles": 0x4C0160,
        "maps": 0x4C60E0,
        "map_count": 8,
        "target_palette": 0x598000,
        "target_tiles": 0x598100,
        "target_maps": 0x59C100,
    },
    "waterfall": {
        "palette": 0x4D0000,
        "tiles": 0x4D00E0,
        "maps": 0x4D40E0,
        "map_count": 6,
        "target_palette": 0x5A0000,
        "target_tiles": 0x5A0100,
        "target_maps": 0x5A4100,
    },
    "shoot": {
        # Digimon Shoot uses the bank-49 graphics set and eight 28x18 maps.
        "palette": 0x490000,
        "tiles": 0x4900E0,
        "maps": 0x495000,
        "map_count": 8,
        "target_palette": 0x5A8000,
        "target_tiles": 0x5A8100,
        "target_maps": 0x5AC100,
    },
}


def convert_palette(source: bytes) -> bytes:
    """Convert the 111 colors copied by retail stage initializers.

    Retail starts at source color 1 and writes to BG palette color 1.  Keeping
    color 0 in palette RAM untouched preserves the engine's transparent color.
    """
    values = struct.unpack("<112H", source)
    return struct.pack("<111H", *(convert_color(value) for value in values[1:]))


def convert_map(source: bytes) -> bytes:
    entries = struct.unpack("<504H", source)
    converted: list[int] = []
    for entry in entries:
        # WSC screen-bank 0 is the common stage tile bank already resident in
        # GBA charblock 0; screen-bank 1 is the stage-specific payload loaded
        # into GBA tiles 0x200..0x3ff.  The commercial port uses this exact
        # translation for its retained stages.
        tile = (0x200 if entry & 0x2000 else 0) + (entry & 0x1FF)
        horizontal = (entry >> 14) & 1
        vertical = (entry >> 15) & 1
        palette = (entry >> 9) & 15
        converted.append(tile | (horizontal << 10) | (vertical << 11) | (palette << 12))
    if len(converted) != 28 * 18:
        raise AssertionError("stage-map crop invariant failed")
    return struct.pack("<504H", *converted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc.read_bytes()
    if hashlib.sha256(wsc).hexdigest().upper() != WSC_SHA256:
        raise SystemExit("refusing unknown WonderSwan Ver. 1.5 input")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {
        "schema": 1,
        "source_sha256": WSC_SHA256,
        "map_format": (
            "direct 28x18 WSC maps converted to GBA text-bg entries; "
            "WSC bank 0 preserved as common GBA tiles and bank 1 rebased to tile 0x200"
        ),
        "stages": {},
    }
    for name, spec in STAGES.items():
        palette = convert_palette(wsc[spec["palette"]:spec["palette"] + 0xE0])
        tiles = b"".join(
            convert_planar_tile(wsc[pos:pos + 32])
            for pos in range(spec["tiles"], spec["tiles"] + 0x4000, 32)
        )
        maps = b"".join(
            convert_map(wsc[
                spec["maps"] + index * 0x3F0:
                spec["maps"] + (index + 1) * 0x3F0
            ])
            for index in range(spec["map_count"])
        )
        blobs = {
            "palette": (palette, spec["target_palette"]),
            "tiles": (tiles, spec["target_tiles"]),
            "maps": (maps, spec["target_maps"]),
        }
        stage_manifest: dict[str, object] = {
            "source": {
                "palette": spec["palette"],
                "tiles": spec["tiles"],
                "maps": spec["maps"],
                "map_count": spec["map_count"],
            },
            "outputs": {},
        }
        for kind, (blob, target) in blobs.items():
            filename = f"stage-{name}-{kind}.bin"
            (args.output_dir / filename).write_bytes(blob)
            stage_manifest["outputs"][kind] = {
                "file": filename,
                "target": target,
                "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest().upper(),
            }
        summary["stages"][name] = stage_manifest

    manifest_path = args.output_dir / "stage-assets.json"
    manifest_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
