#!/usr/bin/env python3
"""Render raw 32x32 WonderSwan Color stage maps from a stage pack."""

from __future__ import annotations

import argparse
import pathlib
import struct

from PIL import Image


def parse_int(value: str) -> int:
    return int(value, 0)


def tile_pixels(tile: bytes) -> bytes:
    pixels = bytearray()
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return bytes(pixels)


def color_rgb(value: int) -> tuple[int, int, int]:
    return ((value >> 8 & 0xF) * 17, (value >> 4 & 0xF) * 17, (value & 0xF) * 17)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    parser.add_argument("--palette", type=parse_int, required=True)
    parser.add_argument("--tiles", type=parse_int, required=True)
    parser.add_argument("--tiles-bank0", type=parse_int)
    parser.add_argument("--maps", type=parse_int, required=True)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--stride", type=parse_int)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    palettes = [
        [color_rgb(value) for value in struct.unpack_from("<16H", rom, args.palette + index * 32)]
        for index in range(16)
    ]
    tiles = [tile_pixels(rom[args.tiles + index * 32:args.tiles + (index + 1) * 32])
             for index in range(512)]
    tiles_bank0 = (
        [tile_pixels(rom[args.tiles_bank0 + index * 32:
                         args.tiles_bank0 + (index + 1) * 32])
         for index in range(512)]
        if args.tiles_bank0 is not None else None
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stride = args.stride if args.stride is not None else args.width * args.height * 2
    for map_index in range(args.count):
        map_offset = args.maps + map_index * stride
        entry_count = args.width * args.height
        entries = struct.unpack_from(f"<{entry_count}H", rom, map_offset)
        rgb = bytearray(args.width * 8 * args.height * 8 * 3)
        for entry_index, entry in enumerate(entries):
            if entry & 0x2000:
                tile = tiles[entry & 0x1FF]
            elif tiles_bank0 is not None:
                tile = tiles_bank0[entry & 0x1FF]
            else:
                continue
            palette = palettes[(entry >> 9) & 0xF]
            horizontal = bool(entry & 0x4000)
            vertical = bool(entry & 0x8000)
            tx = (entry_index % args.width) * 8
            ty = (entry_index // args.width) * 8
            for y in range(8):
                sy = 7 - y if vertical else y
                for x in range(8):
                    sx = 7 - x if horizontal else x
                    red, green, blue = palette[tile[sy * 8 + sx]]
                    out = ((ty + y) * args.width * 8 + tx + x) * 3
                    rgb[out:out + 3] = bytes((red, green, blue))
        image = Image.frombytes("RGB", (args.width * 8, args.height * 8), bytes(rgb))
        image.save(args.output_dir / f"map-{map_index:02d}-{map_offset:06X}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
