#!/usr/bin/env python3
"""Find candidate WSC RGB444 palettes converted to GBA BGR555."""

from __future__ import annotations

import argparse
import json
import pathlib


def expand4(value: int) -> int:
    return (value << 1) | (value >> 3)


def convert_palette(raw: bytes, order: str) -> bytes:
    output = bytearray()
    for index in range(0, 32, 2):
        color = int.from_bytes(raw[index:index + 2], "little")
        a, g, c = color & 0xF, (color >> 4) & 0xF, (color >> 8) & 0xF
        if order == "rgb":
            r, b = a, c
        else:
            b, r = a, c
        gba = expand4(r) | (expand4(g) << 5) | (expand4(b) << 10)
        output.extend(gba.to_bytes(2, "little"))
    return bytes(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--wsc-start", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--wsc-end", type=lambda value: int(value, 0), default=0x4E0000)
    args = parser.parse_args()
    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    gba_windows: dict[bytes, list[int]] = {}
    for offset in range(0, len(gba) - 31, 2):
        gba_windows.setdefault(gba[offset:offset + 32], []).append(offset)
    matches: list[dict[str, object]] = []
    for offset in range(args.wsc_start, min(args.wsc_end, len(wsc)) - 31, 2):
        raw = wsc[offset:offset + 32]
        words = [int.from_bytes(raw[index:index + 2], "little") for index in range(0, 32, 2)]
        if sum(word <= 0x0FFF for word in words) < 15 or len(set(words)) < 5:
            continue
        for order in ("rgb", "bgr"):
            converted = convert_palette(raw, order)
            hits = gba_windows.get(converted)
            if hits:
                matches.append({
                    "wsc_offset": offset,
                    "gba_offsets": hits[:16],
                    "order": order,
                    "colors": len(set(words)),
                })
    print(json.dumps({"match_count": len(matches), "matches": matches[:500]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
