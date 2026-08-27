#!/usr/bin/env python3
"""Match captured WonderSwan screen maps to ROM-resident 32x32 maps.

The WonderSwan tile-map hardware wraps a 32x32 screen.  This tool scores every
cyclic X/Y displacement, which makes the runtime scroll/crop relationship
explicit without starting an emulator again.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


MAP_SIDE = 32
MAP_WORDS = MAP_SIDE * MAP_SIDE
MAP_BYTES = MAP_WORDS * 2


def parse_int(value: str) -> int:
    return int(value, 0)


def words(blob: bytes, offset: int) -> tuple[int, ...]:
    return struct.unpack_from(f"<{MAP_WORDS}H", blob, offset)


def score(runtime: tuple[int, ...], source: tuple[int, ...], dx: int, dy: int) -> int:
    matched = 0
    for y in range(MAP_SIDE):
        sy = (y + dy) & (MAP_SIDE - 1)
        for x in range(MAP_SIDE):
            sx = (x + dx) & (MAP_SIDE - 1)
            matched += runtime[y * MAP_SIDE + x] == source[sy * MAP_SIDE + sx]
    return matched


def linear_score(runtime: tuple[int, ...], source: tuple[int, ...], shift: int) -> int:
    return sum(
        value == source[(index + shift) & (MAP_WORDS - 1)]
        for index, value in enumerate(runtime)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("ram", type=pathlib.Path)
    parser.add_argument("--rom-map-base", type=parse_int, required=True)
    parser.add_argument("--rom-map-count", type=parse_int, required=True)
    parser.add_argument("--ram-map-offset", type=parse_int, action="append", required=True)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    ram = args.ram.read_bytes()
    rows: list[dict[str, int | str]] = []
    linear_rows: list[dict[str, int | str]] = []
    for ram_offset in args.ram_map_offset:
        runtime = words(ram, ram_offset)
        for map_index in range(args.rom_map_count):
            rom_offset = args.rom_map_base + map_index * MAP_BYTES
            source = words(rom, rom_offset)
            for shift in range(MAP_WORDS):
                matched = linear_score(runtime, source, shift)
                linear_rows.append({
                    "ram_offset": f"0x{ram_offset:X}",
                    "rom_offset": f"0x{rom_offset:X}",
                    "map_index": map_index,
                    "source_word_at_runtime_0": shift,
                    "matched_words": matched,
                    "total_words": MAP_WORDS,
                })
            for dy in range(MAP_SIDE):
                for dx in range(MAP_SIDE):
                    matched = score(runtime, source, dx, dy)
                    rows.append({
                        "ram_offset": f"0x{ram_offset:X}",
                        "rom_offset": f"0x{rom_offset:X}",
                        "map_index": map_index,
                        "source_x_at_runtime_0": dx,
                        "source_y_at_runtime_0": dy,
                        "matched_words": matched,
                        "total_words": MAP_WORDS,
                    })
    rows.sort(key=lambda row: int(row["matched_words"]), reverse=True)
    linear_rows.sort(key=lambda row: int(row["matched_words"]), reverse=True)
    result = {
        "schema": 1,
        "interpretation": "runtime[x,y] == source[(x+dx)%32,(y+dy)%32]",
        "best": rows[:args.top],
        "best_linear": linear_rows[:args.top],
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
