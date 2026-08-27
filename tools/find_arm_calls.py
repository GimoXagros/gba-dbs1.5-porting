#!/usr/bin/env python3
"""Enumerate aligned ARM B/BL candidates that resolve to one target.

The scan is deliberately structural: ROM data can resemble an instruction, so
each result remains a candidate until contextual disassembly proves it is code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000


def parse_int(value: str) -> int:
    return int(value, 0)


def branch_target(address: int, word: int) -> int:
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    return address + 8 + immediate * 4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--target", type=parse_int, required=True)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    end = min(len(data), args.end if args.end is not None else len(data))
    start = (args.start + 3) & ~3
    matches = []
    for offset in range(start, end - 3, 4):
        word = struct.unpack_from("<I", data, offset)[0]
        if ((word >> 25) & 7) != 5:
            continue
        address = GBA_BASE + offset
        if branch_target(address, word) != args.target:
            continue
        matches.append({
            "source_offset": offset,
            "source_address": address,
            "link": bool(word & 0x01000000),
            "condition": word >> 28,
            "raw": data[offset:offset + 4].hex(" ").upper(),
        })

    result = {
        "schema": 1,
        "kind": "aligned-arm-branch-candidates",
        "source": {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper(),
        },
        "scan_range": [start, end],
        "target_address": args.target,
        "match_count": len(matches),
        "matches": matches,
        "claim_scope": (
            "structural aligned ARM B/BL candidates only; contextual code "
            "classification is required"
        ),
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
