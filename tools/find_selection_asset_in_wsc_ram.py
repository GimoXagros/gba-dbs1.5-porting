#!/usr/bin/env python3
"""Find a GBA selection tile block in a captured WSC RAM image."""

from __future__ import annotations

import argparse
import json
import pathlib

from build_full_asset_poc import convert_tile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc_ram", type=pathlib.Path)
    parser.add_argument("--gba-offset", type=lambda value: int(value, 0), required=True)
    parser.add_argument("--length", type=lambda value: int(value, 0), default=0x600)
    args = parser.parse_args()

    gba = args.gba.read_bytes()[args.gba_offset:args.gba_offset + args.length]
    ram = args.wsc_ram.read_bytes()
    converted = b"".join(convert_tile(ram[offset:offset + 32])
                         for offset in range(0, len(ram) - 31, 32))
    target_tiles = [gba[offset:offset + 32] for offset in range(0, len(gba), 32)]
    candidates = []
    for start in range(0, len(converted) - len(gba) + 1, 32):
        source = converted[start:start + len(gba)]
        matches = sum(
            source[index * 32:(index + 1) * 32] == tile
            for index, tile in enumerate(target_tiles)
        )
        if matches:
            candidates.append({"ram_offset": start, "matching_tiles": matches})
    candidates.sort(key=lambda item: (-item["matching_tiles"], item["ram_offset"]))
    print(json.dumps({
        "target_tiles": len(target_tiles),
        "exact_offset": converted.find(gba),
        "best_candidates": candidates[:20],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
