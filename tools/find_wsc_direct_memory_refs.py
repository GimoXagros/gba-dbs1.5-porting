#!/usr/bin/env python3
"""Find 16-bit x86 instructions that directly reference one memory offset.

The WonderSwan executable mixes code and data, so this deliberately decodes
at every byte and reports candidates for later contextual disassembly.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_X86, CS_MODE_16, CS_OP_MEM, Cs


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True

    seen: set[tuple[int, bytes]] = set()
    for raw in range(args.start, end):
        decoded = next(engine.disasm(data[raw : min(raw + 16, end)], raw), None)
        if decoded is None:
            continue
        if not any(
            operand.type == CS_OP_MEM
            and operand.mem.base == 0
            and operand.mem.index == 0
            and operand.mem.disp == args.offset
            for operand in decoded.operands
        ):
            continue
        key = (raw, bytes(decoded.bytes))
        if key in seen:
            continue
        seen.add(key)
        encoded = " ".join(f"{value:02X}" for value in decoded.bytes)
        print(f"{raw:08X}  {encoded:<31} {decoded.mnemonic:<8} {decoded.op_str}")


if __name__ == "__main__":
    main()
