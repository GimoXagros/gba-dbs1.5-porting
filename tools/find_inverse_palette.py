#!/usr/bin/env python3
"""Convert a selected GBA BGR555 palette back to WSC BGR444 and find it."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def shrink5(value: int) -> int:
    candidate = value >> 1
    if ((candidate << 1) | (candidate >> 3)) != value:
        raise ValueError(f"5-bit channel {value} is not an expanded 4-bit value")
    return candidate


def all_offsets(data: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return result
        result.append(offset)
        start = offset + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--gba-offset", type=parse_int, required=True)
    parser.add_argument("--colors", type=int, default=16)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    converted = bytearray()
    valid_colors = 0
    for index in range(args.colors):
        color = struct.unpack_from("<H", gba, args.gba_offset + index * 2)[0]
        r5, g5, b5 = color & 0x1F, (color >> 5) & 0x1F, (color >> 10) & 0x1F
        try:
            r4, g4, b4 = shrink5(r5), shrink5(g5), shrink5(b5)
        except ValueError:
            break
        converted.extend(struct.pack("<H", b4 | (g4 << 4) | (r4 << 8)))
        valid_colors += 1

    print(json.dumps({
        "gba_offset": args.gba_offset,
        "requested_colors": args.colors,
        "invertible_colors": valid_colors,
        "wsc_bytes_hex": converted.hex(" "),
        "wsc_offsets": all_offsets(wsc, bytes(converted)) if converted else [],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
