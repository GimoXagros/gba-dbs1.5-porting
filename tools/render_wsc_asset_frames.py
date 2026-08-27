#!/usr/bin/env python3
"""Assemble WSC animation layouts into grayscale sprite-frame sheets."""

from __future__ import annotations

import argparse
import pathlib
import struct

from PIL import Image, ImageDraw

from render_wsc_asset_tiles import descriptor_payloads, parse_int, tile_pixels


COLORS = [(0, 0, 0, 0)] + [
    (24 + index * 15, 24 + index * 15, 24 + index * 15, 255)
    for index in range(1, 16)
]


def layout_frames(rom: bytes, header: int) -> list[list[tuple[int, int, int]]]:
    table_relative = struct.unpack_from("<I", rom, header)[0]
    table = header + table_relative
    first_count, first_relative = struct.unpack_from("<HH", rom, table)
    entries = (first_relative - table_relative) // 4
    if first_count == 0 or entries <= 0:
        raise ValueError(f"bad layout table at 0x{header:X}")
    frames: list[list[tuple[int, int, int]]] = []
    for index in range(entries):
        count, relative = struct.unpack_from("<HH", rom, table + index * 4)
        records: list[tuple[int, int, int]] = []
        for record in range(count):
            tile, vertical, horizontal = struct.unpack_from(
                "<Hbb", rom, header + relative + record * 4
            )
            records.append((tile, horizontal, vertical))
        frames.append(records)
    return frames


def tile_image(data: bytes, horizontal_flip: bool, vertical_flip: bool) -> Image.Image:
    image = Image.new("RGBA", (8, 8))
    image.putdata([COLORS[value] for value in tile_pixels(data)])
    if horizontal_flip:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if vertical_flip:
        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return image


def render_sheet(rom: bytes, header: int, limit: int, scale: int) -> Image.Image:
    layouts = layout_frames(rom, header)
    payloads = descriptor_payloads(rom, header)
    count = min(len(layouts), len(payloads), limit)
    cell_width = 112
    cell_height = 112
    columns = 5
    rows = (count + columns - 1) // columns
    sheet = Image.new("RGBA", (columns * cell_width, rows * cell_height), (18, 18, 26, 255))
    draw = ImageDraw.Draw(sheet)

    for frame_index in range(count):
        payload = payloads[frame_index][1]
        tiles = [payload[offset:offset + 32] for offset in range(0, len(payload), 32)]
        frame = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        for encoded_tile, horizontal, vertical in layouts[frame_index]:
            tile_index = encoded_tile & 0x3FFF
            if tile_index >= len(tiles):
                continue
            image = tile_image(
                tiles[tile_index],
                bool(encoded_tile & 0x4000),
                bool(encoded_tile & 0x8000),
            )
            frame.alpha_composite(image, (horizontal + 48, vertical + 72))
        left = (frame_index % columns) * cell_width
        top = (frame_index // columns) * cell_height
        sheet.alpha_composite(frame, (left + 8, top + 12))
        draw.text((left + 4, top + 2), f"{frame_index:02d}", fill=(255, 220, 80, 255))

    if scale != 1:
        sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.Resampling.NEAREST)
    return sheet.convert("RGB")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--header", type=parse_int, action="append", required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()
    rom = args.wsc.read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    for header in args.header:
        image = render_sheet(rom, header, args.limit, args.scale)
        path = args.output / f"wsc-asset-{header:06X}-frames.png"
        image.save(path)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
