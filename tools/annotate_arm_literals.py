#!/usr/bin/env python3
"""Resolve ARM-state PC-relative LDR literal pools in a ROM window."""

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
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--size", type=parse_int, required=True)
    parser.add_argument("--address", type=parse_int)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    base = args.address if args.address is not None else 0x08000000 + args.offset
    rows = []
    for relative in range(0, args.size - 3, 4):
        offset = args.offset + relative
        word = struct.unpack_from("<I", rom, offset)[0]
        # Single data transfer, immediate offset, pre-indexed, no writeback,
        # load, with PC as the base register. Byte/word loads are both useful.
        if (word & 0x0E3F0000) != 0x041F0000 or not (word & (1 << 20)):
            continue
        immediate = word & 0xFFF
        instruction_address = base + relative
        literal_address = instruction_address + 8
        literal_address += immediate if word & (1 << 23) else -immediate
        literal_offset = literal_address - (base - args.offset)
        if not 0 <= literal_offset <= len(rom) - 4:
            continue
        value = struct.unpack_from("<I", rom, literal_offset)[0]
        rows.append({
            "instruction_offset": offset,
            "instruction_address": instruction_address,
            "register": (word >> 12) & 0xF,
            "literal_offset": literal_offset,
            "literal_address": literal_address,
            "value": value,
            "rom_target": value - 0x08000000 if 0x08000000 <= value < 0x0A000000 else None,
        })
    result = {"window": [args.offset, args.offset + args.size], "literals": rows}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
