#!/usr/bin/env python3
"""Map exact aligned RAM intervals back to a WonderSwan ROM.

This is intended for classifying an already captured RAM image.  It indexes
fixed-size seeds, extends every unique-enough seed in both directions, and
reports maximal exact-copy runs.  The report deliberately excludes long
single-byte padding runs because those do not identify a source asset.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def informative(data: bytes) -> bool:
    return len(set(data)) >= 8 and max(collections.Counter(data).values()) < len(data) * 3 // 4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("ram", type=pathlib.Path)
    parser.add_argument("--seed", type=parse_int, default=0x40)
    parser.add_argument("--alignment", type=parse_int, default=2)
    parser.add_argument("--minimum", type=parse_int, default=0x80)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    ram = args.ram.read_bytes()
    index: dict[bytes, list[int]] = collections.defaultdict(list)
    for offset in range(0, len(rom) - args.seed + 1, args.alignment):
        seed = rom[offset:offset + args.seed]
        if informative(seed):
            index[seed].append(offset)

    candidates: set[tuple[int, int, int]] = set()
    for ram_offset in range(0, len(ram) - args.seed + 1, args.alignment):
        seed = ram[ram_offset:ram_offset + args.seed]
        hits = index.get(seed, [])
        if not hits or len(hits) > 16:
            continue
        for rom_offset in hits:
            left = 0
            while (ram_offset - left - 1 >= 0 and rom_offset - left - 1 >= 0
                   and ram[ram_offset - left - 1] == rom[rom_offset - left - 1]):
                left += 1
            right = args.seed
            while (ram_offset + right < len(ram) and rom_offset + right < len(rom)
                   and ram[ram_offset + right] == rom[rom_offset + right]):
                right += 1
            length = left + right
            if length >= args.minimum:
                candidates.add((ram_offset - left, rom_offset - left, length))

    ordered = sorted(candidates, key=lambda row: (-row[2], row[0], row[1]))
    maximal: list[tuple[int, int, int]] = []
    for row in ordered:
        rs, os, length = row
        if any(rs >= prs and os >= pos and rs + length <= prs + plen
               and os + length <= pos + plen for prs, pos, plen in maximal):
            continue
        maximal.append(row)
    maximal.sort()

    result = {
        "schema": 1,
        "seed": args.seed,
        "alignment": args.alignment,
        "minimum": args.minimum,
        "runs": [
            {"ram_start": rs, "rom_start": os, "length": length}
            for rs, os, length in maximal
        ],
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
