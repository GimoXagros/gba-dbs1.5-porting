#!/usr/bin/env python3
"""Find aligned ARM pointer-table candidates with declared equality pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_pairs(value: str) -> tuple[tuple[int, int], ...]:
    pairs: list[tuple[int, int]] = []
    for item in value.split(","):
        left, right = item.split(":", 1)
        pairs.append((int(left), int(right)))
    return tuple(pairs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--entries", type=int, default=8)
    parser.add_argument("--equal", type=parse_pairs, required=True)
    parser.add_argument("--pointer-start", type=parse_int, default=0x08000000)
    parser.add_argument("--pointer-end", type=parse_int, default=0x08800000)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--min-unique", type=int, default=4)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    end = len(data) if args.scan_end is None else min(args.scan_end, len(data))
    if args.entries <= 0:
        raise SystemExit("entries must be positive")
    for left, right in args.equal:
        if not 0 <= left < args.entries or not 0 <= right < args.entries:
            raise SystemExit("equality-pair index falls outside the table")

    table_bytes = args.entries * 4
    matches: list[dict[str, object]] = []
    for offset in range(args.scan_start, end - table_bytes + 1, 4):
        words = struct.unpack_from(f"<{args.entries}I", data, offset)
        if not all(args.pointer_start <= word < args.pointer_end and word % 4 == 0
                   for word in words):
            continue
        if not all(words[left] == words[right] for left, right in args.equal):
            continue
        if len(set(words)) < args.min_unique:
            continue
        matches.append({
            "offset": offset,
            "address": 0x08000000 + offset,
            "pointers": list(words),
            "unique_pointers": len(set(words)),
        })

    result = {
        "schema": 1,
        "kind": "aligned-arm-pointer-table-candidates",
        "source": {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper(),
        },
        "scan_range": [args.scan_start, end],
        "entries": args.entries,
        "pointer_range": [args.pointer_start, args.pointer_end],
        "equal_pairs": [list(pair) for pair in args.equal],
        "minimum_unique_pointers": args.min_unique,
        "match_count": len(matches),
        "matches": matches,
        "claim_scope": (
            "structural aligned pointer-table candidates only; contextual code and "
            "WSC semantic correspondence are required"
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
