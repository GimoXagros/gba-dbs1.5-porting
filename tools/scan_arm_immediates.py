#!/usr/bin/env python3
"""Scan every aligned ARM word for selected immediate operands."""

from __future__ import annotations

import argparse
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, CS_OP_IMM, Cs


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--immediate", type=parse_int, required=True)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--mnemonics", default="cmp,mov,movne,moveq")
    args = parser.parse_args()
    data = args.rom.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    wanted = set(args.mnemonics.split(","))
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    engine.detail = True
    for offset in range((args.start + 3) & ~3, end - 3, 4):
        decoded = tuple(engine.disasm(data[offset:offset + 4], 0x08000000 + offset, 1))
        if not decoded:
            continue
        insn = decoded[0]
        if insn.mnemonic not in wanted:
            continue
        if not any(op.type == CS_OP_IMM and op.imm == args.immediate for op in insn.operands):
            continue
        print(f"{offset:08X}  {insn.bytes.hex(' ').upper():<12}  {insn.mnemonic:<8} {insn.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
