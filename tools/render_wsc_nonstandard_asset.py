#!/usr/bin/env python3
"""Render a WSC animation asset whose descriptor uses a non-0x2000 destination."""

from __future__ import annotations

import argparse
import pathlib
import struct

from PIL import Image, ImageDraw

from render_wsc_asset_frames import COLORS, layout_frames, tile_image


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--header", type=parse_int, required=True)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    rom = args.wsc.read_bytes()
    layouts = layout_frames(rom, args.header)
    secondary = struct.unpack_from("<I", rom, args.header + 4)[0]
    # WonderSwan ROM-bank pointers retain mapper bits in the high byte.  The
    # physical bank mask follows the cartridge size (4 MiB=0x3f, 8 MiB=0x7f).
    bank_mask = len(rom) // 0x10000 - 1
    table = (((secondary >> 16) & bank_mask) << 16) | (((secondary & 0xFFFF) << 4) & 0xFFFF)
    length, bank_offset, destination, bank = struct.unpack_from("<4H", rom, table)
    physical = ((bank & bank_mask) << 16) | bank_offset
    payload = rom[physical:physical + length]
    tiles = [payload[pos:pos + 32] for pos in range(0, len(payload), 32)]
    encoded = [tile & 0x3FFF for frame in layouts for tile, _, _ in frame]
    tile_base = min(encoded)

    cell = 128
    columns = 4
    rows = (len(layouts) + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * cell, rows * cell), (18, 18, 26, 255))
    draw = ImageDraw.Draw(sheet)
    for frame_index, layout in enumerate(layouts):
        frame = Image.new("RGBA", (112, 112), (0, 0, 0, 0))
        for encoded_tile, horizontal, vertical in layout:
            index = (encoded_tile & 0x3FFF) - tile_base
            if not 0 <= index < len(tiles):
                continue
            frame.alpha_composite(
                tile_image(
                    tiles[index], bool(encoded_tile & 0x4000), bool(encoded_tile & 0x8000)
                ),
                (horizontal + 56, vertical + 80),
            )
        left = (frame_index % columns) * cell
        top = (frame_index // columns) * cell
        sheet.alpha_composite(frame, (left + 8, top + 12))
        draw.text((left + 4, top + 2), f"{frame_index:02d}", fill=COLORS[-1])
    if args.scale != 1:
        sheet = sheet.resize((sheet.width * args.scale, sheet.height * args.scale), Image.Resampling.NEAREST)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(args.output)
    print(
        f"header=0x{args.header:X} descriptor=0x{table:X} destination=0x{destination:X} "
        f"physical=0x{physical:X} tiles={len(tiles)} tile_base=0x{tile_base:X}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
