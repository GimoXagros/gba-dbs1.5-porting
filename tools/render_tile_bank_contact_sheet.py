#!/usr/bin/env python3
"""Render labelled ROM-bank tile overviews for visual classification."""

from __future__ import annotations

import argparse
import pathlib

from PIL import Image, ImageDraw


PALETTE = [(index * 17, index * 17, index * 17) for index in range(16)]


def parse_int(value: str) -> int:
    return int(value, 0)


def packed(tile: bytes) -> list[int]:
    return [nibble for value in tile for nibble in (value & 0xF, value >> 4)]


def planar(tile: bytes) -> list[int]:
    pixels = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[p] & mask) != 0) << p for p in range(4)))
    return pixels


def bank_image(data: bytes, mode: str, tiles_per_row: int) -> Image.Image:
    tile_count = len(data) // 32
    rows = (tile_count + tiles_per_row - 1) // tiles_per_row
    image = Image.new("RGB", (tiles_per_row * 8, rows * 8), PALETTE[0])
    for index in range(tile_count):
        tile = data[index * 32:index * 32 + 32]
        values = packed(tile) if mode == "gba4" else planar(tile)
        rendered = Image.new("RGB", (8, 8))
        rendered.putdata([PALETTE[value] for value in values])
        image.paste(rendered, ((index % tiles_per_row) * 8, (index // tiles_per_row) * 8))
    return image


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--mode", choices=("gba4", "wsc4-planar"), required=True)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--bank-size", type=parse_int, default=0x10000)
    parser.add_argument("--tiles-per-row", type=int, default=32)
    parser.add_argument("--columns", type=int, default=4)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    end = min(len(rom), args.end if args.end is not None else len(rom))
    cells = []
    for start in range(args.start, end, args.bank_size):
        rendered = bank_image(rom[start:min(start + args.bank_size, end)], args.mode, args.tiles_per_row)
        cell = Image.new("RGB", (rendered.width, rendered.height + 18), (16, 16, 16))
        ImageDraw.Draw(cell).text((3, 2), f"0x{start:06X}", fill=(255, 255, 255))
        cell.paste(rendered, (0, 18))
        cells.append(cell)
    rows = (len(cells) + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (args.columns * cells[0].width, rows * cells[0].height), (8, 8, 8))
    for index, cell in enumerate(cells):
        sheet.paste(cell, ((index % args.columns) * cell.width, (index // args.columns) * cell.height))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
