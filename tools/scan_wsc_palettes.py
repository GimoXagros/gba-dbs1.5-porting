#!/usr/bin/env python3
"""List RGB444-like 16-color blocks in a WSC ROM range."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--start", type=parse_int, required=True)
    parser.add_argument("--end", type=parse_int, required=True)
    parser.add_argument("--minimum-colors", type=int, default=8)
    parser.add_argument("--alignment", type=parse_int, default=2)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    candidates = []
    last = -0x20
    for offset in range(args.start, min(args.end, len(rom)) - 31, args.alignment):
        words = list(struct.unpack_from("<16H", rom, offset))
        if any(word > 0xFFF for word in words):
            continue
        colors = len(set(words))
        if colors < args.minimum_colors or 0 not in words:
            continue
        # Collapse heavily overlapping windows to the first aligned candidate.
        if offset < last + 0x20:
            continue
        candidates.append({
            "offset": offset,
            "distinct_colors": colors,
            "words": words,
        })
        last = offset
    result = {"range": [args.start, args.end], "candidates": candidates}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
