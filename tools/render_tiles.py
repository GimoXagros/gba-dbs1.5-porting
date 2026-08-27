#!/usr/bin/env python3
"""Render raw tile candidates without extracting or redistributing ROM data."""

from __future__ import annotations

import argparse
import pathlib

from PIL import Image


PALETTE = [
    (0, 0, 0), (32, 32, 32), (64, 64, 64), (96, 96, 96),
    (128, 128, 128), (160, 160, 160), (192, 192, 192), (224, 224, 224),
    (0, 48, 96), (0, 96, 160), (0, 144, 192), (48, 192, 192),
    (96, 224, 160), (160, 240, 96), (224, 240, 48), (255, 255, 255),
]


def parse_int(value: str) -> int:
    return int(value, 0)


def packed_4bpp(tile: bytes, high_first: bool) -> list[int]:
    pixels: list[int] = []
    for value in tile:
        low, high = value & 0x0F, value >> 4
        pixels.extend((high, low) if high_first else (low, high))
    return pixels


def planar_4bpp(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            value = sum(((planes[plane] & mask) != 0) << plane for plane in range(4))
            pixels.append(value)
    return pixels


def planar_2bpp(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 2:row * 2 + 2]
        for column in range(8):
            mask = 0x80 >> column
            value = ((planes[0] & mask) != 0) | (((planes[1] & mask) != 0) << 1)
            pixels.append(int(value) * 5)
    return pixels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--length", type=parse_int, default=0x10000)
    parser.add_argument("--mode", choices=("gba4", "wsc4-packed", "wsc4-planar", "wsc2-planar"), required=True)
    parser.add_argument("--tiles-per-row", type=int, default=32)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    data = args.rom.read_bytes()[args.offset:args.offset + args.length]
    tile_size = 16 if args.mode == "wsc2-planar" else 32
    tile_count = len(data) // tile_size
    rows = (tile_count + args.tiles_per_row - 1) // args.tiles_per_row
    image = Image.new("RGB", (args.tiles_per_row * 8, rows * 8), PALETTE[0])
    for index in range(tile_count):
        tile = data[index * tile_size:(index + 1) * tile_size]
        if args.mode == "gba4":
            pixels = packed_4bpp(tile, high_first=False)
        elif args.mode == "wsc4-packed":
            pixels = packed_4bpp(tile, high_first=True)
        elif args.mode == "wsc4-planar":
            pixels = planar_4bpp(tile)
        else:
            pixels = planar_2bpp(tile)
        tile_image = Image.new("RGB", (8, 8))
        tile_image.putdata([PALETTE[value] for value in pixels])
        x = (index % args.tiles_per_row) * 8
        y = (index // args.tiles_per_row) * 8
        image.paste(tile_image, (x, y))
    if args.scale != 1:
        image = image.resize((image.width * args.scale, image.height * args.scale), Image.Resampling.NEAREST)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
