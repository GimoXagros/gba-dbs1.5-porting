#!/usr/bin/env python3
"""Render WonderSwan 32x32 screen maps from a captured 64 KiB RAM image."""

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
    return ((value >> 8 & 15) * 17, (value >> 4 & 15) * 17, (value & 15) * 17)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ram", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    parser.add_argument("--map", type=parse_int, action="append", default=[0, 0x800])
    args = parser.parse_args()

    ram = args.ram.read_bytes()
    if len(ram) < 0x10000:
        raise SystemExit("expected a complete 64 KiB WonderSwan RAM image")
    palettes = [
        [color_rgb(value) for value in struct.unpack_from("<16H", ram, 0xFE00 + i * 32)]
        for i in range(16)
    ]
    banks = {
        False: [tile_pixels(ram[0x4000 + i * 32:0x4000 + (i + 1) * 32]) for i in range(512)],
        True: [tile_pixels(ram[0x8000 + i * 32:0x8000 + (i + 1) * 32]) for i in range(512)],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for map_offset in args.map:
        entries = struct.unpack_from("<1024H", ram, map_offset)
        rgb = bytearray(256 * 256 * 3)
        for entry_index, entry in enumerate(entries):
            tile = banks[bool(entry & 0x2000)][entry & 0x1FF]
            palette = palettes[(entry >> 9) & 15]
            horizontal = bool(entry & 0x4000)
            vertical = bool(entry & 0x8000)
            tx = (entry_index & 31) * 8
            ty = (entry_index >> 5) * 8
            for y in range(8):
                sy = 7 - y if vertical else y
                for x in range(8):
                    sx = 7 - x if horizontal else x
                    rgb[((ty + y) * 256 + tx + x) * 3:((ty + y) * 256 + tx + x) * 3 + 3] = bytes(
                        palette[tile[sy * 8 + sx]]
                    )
        Image.frombytes("RGB", (256, 256), bytes(rgb)).save(
            args.output_dir / f"screen-{map_offset:04X}.png"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
