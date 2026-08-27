#!/usr/bin/env python3
"""Map exact byte intervals shared by two WonderSwan ROM revisions.

The output is a candidate map, not a semantic content claim.  Matches are
seeded on an explicit alignment and extended byte-for-byte.  Repeated regions
remain marked as ambiguous instead of being silently assigned to one source.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import defaultdict


def parse_int(value: str) -> int:
    return int(value, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def union_length(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    total = 0
    start, end = sorted(intervals)[0]
    for next_start, next_end in sorted(intervals)[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def complement(intervals: list[tuple[int, int]], size: int) -> list[dict[str, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    result: list[dict[str, int]] = []
    cursor = 0
    for start, end in merged:
        if cursor < start:
            result.append({"start": cursor, "end": start, "length": start - cursor})
        cursor = max(cursor, end)
    if cursor < size:
        result.append({"start": cursor, "end": size, "length": size - cursor})
    return result


def map_intervals(
    older: bytes,
    newer: bytes,
    alignment: int,
    seed_size: int,
    minimum: int,
    maximum_occurrences: int,
) -> list[dict[str, int | bool]]:
    if seed_size < alignment or seed_size % alignment:
        raise ValueError("seed size must be a multiple of alignment")
    index: dict[bytes, list[int]] = defaultdict(list)
    for offset in range(0, len(older) - seed_size + 1, alignment):
        index[older[offset:offset + seed_size]].append(offset)

    found: dict[tuple[int, int, int], dict[str, int | bool]] = {}
    for newer_offset in range(0, len(newer) - seed_size + 1, alignment):
        seed = newer[newer_offset:newer_offset + seed_size]
        older_offsets = index.get(seed, [])
        if not older_offsets or len(older_offsets) > maximum_occurrences:
            continue
        for older_offset in older_offsets:
            if older_offset >= alignment and newer_offset >= alignment:
                if (older[older_offset - alignment:older_offset + seed_size]
                        == newer[newer_offset - alignment:newer_offset + seed_size]):
                    continue

            old_start = older_offset
            new_start = newer_offset
            while old_start and new_start and older[old_start - 1] == newer[new_start - 1]:
                old_start -= 1
                new_start -= 1

            old_end = older_offset + seed_size
            new_end = newer_offset + seed_size
            while old_end < len(older) and new_end < len(newer) and older[old_end] == newer[new_end]:
                old_end += 1
                new_end += 1

            length = old_end - old_start
            if length < minimum:
                continue
            key = (old_start, new_start, length)
            found[key] = {
                "older_start": old_start,
                "newer_start": new_start,
                "length": length,
                "delta": new_start - old_start,
                "seed_ambiguous": len(older_offsets) > 1,
            }
    return sorted(found.values(), key=lambda item: (int(item["newer_start"]), -int(item["length"])))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("older", type=pathlib.Path)
    parser.add_argument("newer", type=pathlib.Path)
    parser.add_argument("--alignment", type=parse_int, default=0x10)
    parser.add_argument("--seed-size", type=parse_int, default=0x40)
    parser.add_argument("--minimum", type=parse_int, default=0x100)
    parser.add_argument("--maximum-occurrences", type=int, default=8)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    older = args.older.read_bytes()
    newer = args.newer.read_bytes()
    matches = map_intervals(
        older,
        newer,
        args.alignment,
        args.seed_size,
        args.minimum,
        args.maximum_occurrences,
    )
    older_intervals = [
        (int(item["older_start"]), int(item["older_start"]) + int(item["length"]))
        for item in matches
    ]
    newer_intervals = [
        (int(item["newer_start"]), int(item["newer_start"]) + int(item["length"]))
        for item in matches
    ]
    result = {
        "schema": 1,
        "method": {
            "alignment": args.alignment,
            "seed_size": args.seed_size,
            "minimum_match": args.minimum,
            "maximum_seed_occurrences": args.maximum_occurrences,
            "meaning": "exact-copy candidates only; unmatched does not by itself mean new content",
        },
        "older": {"size": len(older), "sha256": sha256(older)},
        "newer": {"size": len(newer), "sha256": sha256(newer)},
        "summary": {
            "match_count": len(matches),
            "older_covered_bytes": union_length(older_intervals),
            "newer_covered_bytes": union_length(newer_intervals),
        },
        "matches": matches,
        "newer_unmatched_intervals": complement(newer_intervals, len(newer)),
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
