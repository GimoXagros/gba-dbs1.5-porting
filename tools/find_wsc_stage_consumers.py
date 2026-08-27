#!/usr/bin/env python3
"""Locate WSC functions that read battle_state.stage at structure offset +0x0e."""

from __future__ import annotations

import argparse
import pathlib
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_X86, CS_MODE_16, Cs  # type: ignore


# Compiler idiom: save DS/DI, select RAM segment 0x1000, set DI to battle
# state at 0x004e, zero AX, read stage byte at [DI+0x0e], restore DI/DS.
PATTERN = bytes.fromhex(
    "1E 57 BF 00 10 8E DF BF 4E 00 33 C0 8A 45 0E 5F 1F"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--before", type=lambda value: int(value, 0), default=0x20)
    parser.add_argument("--after", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    data = args.rom.read_bytes()
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    cursor = 0
    hits: list[int] = []
    while True:
        offset = data.find(PATTERN, cursor)
        if offset < 0:
            break
        hits.append(offset)
        cursor = offset + 1

    print(f"stage-reader idiom count: {len(hits)}")
    for offset in hits:
        start = max(0, offset - args.before)
        end = min(len(data), offset + len(PATTERN) + args.after)
        decoded = tuple(engine.disasm(data[start:end], start))
        relevant = any(
            insn.mnemonic in {"lcall", "call", "jmp"}
            or (
                insn.mnemonic == "cmp"
                and any(value in insn.op_str for value in (", 8", ", 9", ", 0xa", ", 0xb"))
            )
            for insn in decoded
        )
        if not relevant:
            continue
        if args.summary:
            selected = [
                insn for insn in decoded
                if insn.mnemonic in {"lcall", "call", "jmp"}
                or insn.mnemonic in {"cmp", "shl", "sal"}
                or "cs:[" in insn.op_str
            ]
            rendered = "; ".join(
                f"{insn.address:08X} {insn.mnemonic} {insn.op_str}"
                for insn in selected
            )
            print(f"{offset:08X}: {rendered}")
            continue
        print(f"\nWINDOW {offset:08X}")
        for insn in decoded:
            raw = bytes(insn.bytes).hex(" ").upper()
            marker = "*" if offset <= insn.address < offset + len(PATTERN) else " "
            print(
                f"{marker}{insn.address:08X}  {raw:<24}  "
                f"{insn.mnemonic:<10} {insn.op_str}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
