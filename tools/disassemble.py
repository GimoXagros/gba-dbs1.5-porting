#!/usr/bin/env python3
"""Small deterministic disassembly helper for confirmed code windows."""

from __future__ import annotations

import argparse
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import (  # type: ignore  # local pinned analysis dependency
    CS_ARCH_ARM,
    CS_ARCH_X86,
    CS_MODE_16,
    CS_MODE_ARM,
    CS_MODE_LITTLE_ENDIAN,
    CS_MODE_THUMB,
    Cs,
)


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--size", type=parse_int, default=0x100)
    parser.add_argument("--address", type=parse_int)
    parser.add_argument("--mode", choices=("arm", "thumb", "x86-16"), required=True)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    window = data[args.offset:args.offset + args.size]
    address = args.address if args.address is not None else args.offset
    if args.mode == "arm":
        engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    elif args.mode == "thumb":
        engine = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    else:
        engine = Cs(CS_ARCH_X86, CS_MODE_16)
    for insn in engine.disasm(window, address):
        raw = insn.bytes.hex(" ").upper()
        print(f"{insn.address:08X}  {raw:<24}  {insn.mnemonic:<10} {insn.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
