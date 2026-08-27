#!/usr/bin/env python3
"""Render every tile payload referenced by selected WSC asset headers."""

from __future__ import annotations

import argparse
import pathlib
import struct

from PIL import Image, ImageDraw


PALETTE = [(0, 0, 0)] + [
    (24 + index * 15, 24 + index * 15, 24 + index * 15)
    for index in range(1, 16)
]


def parse_int(value: str) -> int:
    return int(value, 0)


def tile_pixels(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return pixels


def descriptor_payloads(rom: bytes, header: int) -> list[tuple[int, bytes]]:
    secondary = struct.unpack_from("<I", rom, header + 4)[0]
    bank = (secondary >> 16) & 0xFF
    segment = secondary & 0xFFFF
    cursor = ((bank & 0x7F) << 16) | ((segment << 4) & 0xFFFF)
    payloads: list[tuple[int, bytes]] = []
    previous_end: int | None = None
    previous_bank: int | None = None
    while cursor + 8 <= len(rom):
        length, bank_offset, destination, tile_bank = struct.unpack_from("<4H", rom, cursor)
        physical = ((tile_bank & 0x7F) << 16) | bank_offset
        valid = (
            length >= 0x20
            and length % 0x20 == 0
            and destination == 0x2000
            and 0x80 <= tile_bank <= 0xFF
            and bank_offset + length <= 0x10000
            and physical + length <= len(rom)
        )
        contiguous = previous_end is None or physical == previous_end
        new_block = previous_end is not None and bank_offset == 0 and tile_bank != previous_bank
        if not valid or not (contiguous or new_block):
            break
        payloads.append((physical, rom[physical:physical + length]))
        previous_end = physical + length
        previous_bank = tile_bank
        cursor += 8
    if not payloads:
        raise ValueError(f"no descriptors found for 0x{header:X}")
    return payloads


def render(rom: bytes, header: int, tiles_per_row: int, scale: int) -> Image.Image:
    payloads = descriptor_payloads(rom, header)
    tiles = [payload[index:index + 32]
             for _, payload in payloads
             for index in range(0, len(payload), 32)]
    rows = (len(tiles) + tiles_per_row - 1) // tiles_per_row
    margin = 24
    sheet = Image.new("RGB", (tiles_per_row * 8, rows * 8 + margin), (20, 20, 28))
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 4), f"WSC 0x{header:06X}  {len(payloads)} chunks  {len(tiles)} tiles", fill=(255, 255, 255))
    for index, tile in enumerate(tiles):
        tile_image = Image.new("RGB", (8, 8))
        tile_image.putdata([PALETTE[value] for value in tile_pixels(tile)])
        x = (index % tiles_per_row) * 8
        y = margin + (index // tiles_per_row) * 8
        sheet.paste(tile_image, (x, y))
    if scale != 1:
        sheet = sheet.resize((sheet.width * scale, sheet.height * scale), Image.Resampling.NEAREST)
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--header", type=parse_int, action="append", required=True)
    parser.add_argument("--tiles-per-row", type=int, default=32)
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()
    rom = args.wsc.read_bytes()
    args.output.mkdir(parents=True, exist_ok=True)
    for header in args.header:
        image = render(rom, header, args.tiles_per_row, args.scale)
        path = args.output / f"wsc-asset-{header:06X}-tiles.png"
        image.save(path)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
