#!/usr/bin/env python3
"""Map aligned WSC RAM tiles back to aligned ROM tile sources."""

from __future__ import annotations

import argparse
import json
import pathlib


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("ram", type=pathlib.Path)
    parser.add_argument("--ram-start", type=lambda value: int(value, 0), default=0x4000)
    parser.add_argument("--ram-end", type=lambda value: int(value, 0), default=0x10000)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    ram = args.ram.read_bytes()
    index: dict[bytes, list[int]] = {}
    for offset in range(0, len(rom) - 31, 32):
        index.setdefault(rom[offset:offset + 32], []).append(offset)

    mappings = []
    for ram_offset in range(args.ram_start, min(args.ram_end, len(ram)) - 31, 32):
        tile = ram[ram_offset:ram_offset + 32]
        hits = index.get(tile, [])
        if hits and len(set(tile)) > 2:
            mappings.append({"ram_offset": ram_offset, "rom_offsets": hits[:32]})

    runs = []
    for mapping in mappings:
        ram_start = mapping["ram_offset"]
        for rom_start in mapping["rom_offsets"]:
            length = 1
            while ram_start + length * 32 < min(args.ram_end, len(ram)):
                r0 = ram_start + length * 32
                s0 = rom_start + length * 32
                if s0 + 32 > len(rom) or ram[r0:r0 + 32] != rom[s0:s0 + 32]:
                    break
                length += 1
            if length >= 4:
                runs.append({
                    "ram_offset": ram_start,
                    "rom_offset": rom_start,
                    "tiles": length,
                    "bytes": length * 32,
                })
    runs.sort(key=lambda item: (-item["tiles"], item["ram_offset"], item["rom_offset"]))
    filtered = []
    for run in runs:
        if any(
            run["ram_offset"] >= prior["ram_offset"]
            and run["rom_offset"] >= prior["rom_offset"]
            and run["ram_offset"] + run["bytes"] <= prior["ram_offset"] + prior["bytes"]
            and run["rom_offset"] + run["bytes"] <= prior["rom_offset"] + prior["bytes"]
            for prior in filtered
        ):
            continue
        filtered.append(run)
    print(json.dumps({
        "mapped_tile_count": len(mappings),
        "longest_runs": filtered[:100],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
