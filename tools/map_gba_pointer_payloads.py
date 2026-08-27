#!/usr/bin/env python3
"""Map payloads referenced by a GBA pointer-record table into the WSC ROM.

Only byte-exact matches are reported.  Graphics that require planar conversion
are intentionally outside this tool's claim.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


GBA_BASE = 0x08000000
RECORD_BYTES = 32


def parse_int(value: str) -> int:
    return int(value, 0)


def all_offsets(data: bytes, needle: bytes, limit: int = 64) -> list[int]:
    result: list[int] = []
    start = 0
    while len(result) < limit:
        offset = data.find(needle, start)
        if offset < 0:
            break
        result.append(offset)
        start = offset + 1
    return result


def maximal_match(first: bytes, first_offset: int, second: bytes, second_offset: int,
                  seed_bytes: int) -> tuple[int, int, int]:
    before = 0
    while (first_offset - before > 0 and second_offset - before > 0
           and first[first_offset - before - 1] == second[second_offset - before - 1]):
        before += 1
    after = seed_bytes
    while (first_offset + after < len(first) and second_offset + after < len(second)
           and first[first_offset + after] == second[second_offset + after]):
        after += 1
    return first_offset - before, second_offset - before, before + after


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--table", type=parse_int, default=0xD3FC0)
    parser.add_argument("--records", type=int, default=47)
    parser.add_argument("--seed", type=int, default=24)
    parser.add_argument("--minimum-match", type=int, default=32)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    targets: dict[int, list[dict[str, int]]] = {}
    for record in range(args.records):
        record_offset = args.table + record * RECORD_BYTES
        fields = struct.unpack_from("<8I", gba, record_offset)
        for field, value in enumerate(fields):
            target = value - GBA_BASE
            if 0 <= target <= len(gba) - args.seed:
                targets.setdefault(target, []).append({
                    "record": record,
                    "record_offset": record_offset,
                    "field": field,
                })

    results: list[dict[str, object]] = []
    for target, references in sorted(targets.items()):
        seed = gba[target:target + args.seed]
        if len(set(seed)) <= 2:
            continue
        matches: list[dict[str, int]] = []
        for wsc_offset in all_offsets(wsc, seed):
            gba_start, wsc_start, length = maximal_match(gba, target, wsc, wsc_offset, args.seed)
            if length >= args.minimum_match:
                matches.append({
                    "gba_start": gba_start,
                    "wsc_start": wsc_start,
                    "length": length,
                    "target_delta": target - gba_start,
                })
        if matches:
            unique = {(item["gba_start"], item["wsc_start"], item["length"], item["target_delta"]): item
                      for item in matches}
            results.append({
                "gba_target": target,
                "references": references,
                "matches": sorted(unique.values(), key=lambda item: item["length"], reverse=True),
            })

    print(json.dumps({
        "table_offset": args.table,
        "record_count": args.records,
        "unique_pointer_targets": len(targets),
        "mapped_targets": len(results),
        "results": results,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
