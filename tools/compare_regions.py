#!/usr/bin/env python3
"""Find exact byte runs shared by two explicitly selected ROM regions."""

from __future__ import annotations

import argparse
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=pathlib.Path)
    parser.add_argument("second", type=pathlib.Path)
    parser.add_argument("--first-start", type=parse_int, required=True)
    parser.add_argument("--first-end", type=parse_int, required=True)
    parser.add_argument("--second-start", type=parse_int, required=True)
    parser.add_argument("--second-end", type=parse_int, required=True)
    parser.add_argument("--seed", type=int, default=8)
    parser.add_argument("--minimum", type=int, default=16)
    args = parser.parse_args()

    first = args.first.read_bytes()[args.first_start:args.first_end]
    second = args.second.read_bytes()[args.second_start:args.second_end]
    index: dict[bytes, list[int]] = {}
    for offset in range(0, len(first) - args.seed + 1):
        index.setdefault(first[offset:offset + args.seed], []).append(offset)

    matches: list[dict[str, int]] = []
    for second_offset in range(0, len(second) - args.seed + 1):
        seed = second[second_offset:second_offset + args.seed]
        if len(set(seed)) <= 2:
            continue
        for first_offset in index.get(seed, []):
            if first_offset and second_offset and first[first_offset - 1] == second[second_offset - 1]:
                continue
            length = args.seed
            while (first_offset + length < len(first)
                   and second_offset + length < len(second)
                   and first[first_offset + length] == second[second_offset + length]):
                length += 1
            if length >= args.minimum:
                matches.append({
                    "first_offset": args.first_start + first_offset,
                    "second_offset": args.second_start + second_offset,
                    "length": length,
                })
    matches.sort(key=lambda item: item["length"], reverse=True)
    print(json.dumps({"matches": matches[:200]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
