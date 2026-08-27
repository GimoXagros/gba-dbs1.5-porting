#!/usr/bin/env python3
"""Summarize fixed-size WSC ROM banks without assigning semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
from collections import Counter


def parse_int(value: str) -> int:
    return int(value, 0)


def entropy(data: bytes) -> float:
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--bank-size", type=parse_int, default=0x10000)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    end = min(len(rom), args.end if args.end is not None else len(rom))
    rows = []
    for start in range(args.start, end, args.bank_size):
        data = rom[start:min(start + args.bank_size, end)]
        non_ff = [index for index, value in enumerate(data) if value != 0xFF]
        non_zero = sum(value != 0 for value in data)
        rows.append({
            "offset": start,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper(),
            "entropy": round(entropy(data), 6),
            "distinct_bytes": len(set(data)),
            "nonzero_bytes": non_zero,
            "non_ff_bytes": len(non_ff),
            "first_non_ff": None if not non_ff else start + non_ff[0],
            "last_non_ff": None if not non_ff else start + non_ff[-1],
        })
    result = {
        "rom": str(args.rom),
        "size": len(rom),
        "bank_size": args.bank_size,
        "range": [args.start, end],
        "banks": rows,
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
