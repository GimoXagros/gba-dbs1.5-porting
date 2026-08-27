#!/usr/bin/env python3
"""Find x86-16 instructions that compare/load the character-record ID field.

Battle Spirit stores the runtime fighter ID in the byte at resource-record
offset 0x11.  This scanner decodes at every byte because WSC ROM regions mix
code and data; its output is candidate evidence for contextual disassembly.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_X86, CS_MODE_16, CS_OP_IMM, CS_OP_MEM, Cs


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--immediate", type=parse_int, action="append")
    parser.add_argument("--any-immediate", action="store_true")
    args = parser.parse_args()

    data = args.rom.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    immediates = set(args.immediate or (12, 15))
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True
    seen: set[tuple[int, bytes]] = set()
    for raw in range(args.start, end):
        instruction = next(engine.disasm(data[raw:min(raw + 16, end)], raw), None)
        if instruction is None:
            continue
        has_id_field = any(
            operand.type == CS_OP_MEM and operand.mem.disp == 0x11
            for operand in instruction.operands
        )
        has_wanted_immediate = any(
            operand.type == CS_OP_IMM and operand.imm in immediates
            for operand in instruction.operands
        )
        has_any_immediate = any(
            operand.type == CS_OP_IMM for operand in instruction.operands
        )
        if not (has_id_field and (
            has_wanted_immediate or (args.any_immediate and has_any_immediate)
        )):
            continue
        key = (raw, bytes(instruction.bytes))
        if key in seen:
            continue
        seen.add(key)
        encoded = " ".join(f"{value:02X}" for value in instruction.bytes)
        print(f"{raw:08X}  {encoded:<31} {instruction.mnemonic:<8} {instruction.op_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
