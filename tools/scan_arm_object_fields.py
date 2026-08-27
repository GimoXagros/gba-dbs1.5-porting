#!/usr/bin/env python3
"""Scan every ARM-aligned word for accesses to selected structure fields."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--fields", default="0x28,0x2c,0x30")
    args = parser.parse_args()

    data = args.rom.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    fields = {int(value, 0) for value in args.fields.split(",")}
    field_pattern = "|".join(f"{value:x}" for value in sorted(fields))
    pattern = re.compile(rf"\[([^\]]+), #0x(?:{field_pattern})\]")
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)

    for offset in range(args.start & ~3, end - 3, 4):
        decoded = tuple(engine.disasm(data[offset:offset + 4], 0x08000000 + offset, 1))
        if not decoded:
            continue
        insn = decoded[0]
        if pattern.search(insn.op_str):
            raw = insn.bytes.hex(" ").upper()
            print(f"{insn.address:08X}  {raw:<12}  {insn.mnemonic:<8} {insn.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
