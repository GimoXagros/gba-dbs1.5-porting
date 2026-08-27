#!/usr/bin/env python3
"""Render a raw WSC 4bpp planar tile range as an indexed contact sheet."""

from __future__ import annotations

import argparse
import pathlib
import struct

from PIL import Image, ImageDraw


def parse_int(value: str) -> int:
    return int(value, 0)


def color_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 8 & 0xF) * 17, (value >> 4 & 0xF) * 17, (value & 0xF) * 17)


def tile_pixels(tile: bytes) -> bytes:
    pixels = bytearray()
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return bytes(pixels)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--tiles", type=parse_int, required=True)
    parser.add_argument("--count", type=parse_int, default=0x800)
    parser.add_argument("--palette", type=parse_int)
    parser.add_argument("--columns", type=int, default=32)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if args.palette is None:
        palette = [(v * 17, v * 17, v * 17) for v in range(16)]
    else:
        palette = [
            color_rgb(value)
            for value in struct.unpack_from("<16H", rom, args.palette)
        ]
    rows = (args.count + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (args.columns * 8, rows * 8), (0, 0, 0))
    for index in range(args.count):
        start = args.tiles + index * 32
        payload = rom[start:start + 32]
        if len(payload) != 32:
            break
        pixels = tile_pixels(payload)
        tile = Image.new("RGB", (8, 8))
        tile.putdata([palette[pixel] for pixel in pixels])
        sheet.paste(tile, ((index % args.columns) * 8, (index // args.columns) * 8))
    if args.scale != 1:
        sheet = sheet.resize(
            (sheet.width * args.scale, sheet.height * args.scale),
            Image.Resampling.NEAREST,
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    print(f"tiles=0x{args.tiles:X} count={args.count} palette={args.palette}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
