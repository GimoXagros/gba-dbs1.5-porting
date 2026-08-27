#!/usr/bin/env python3
"""Compare the five-pointer resource records in two WonderSwan revisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


RECORD_BYTES = 0x20
POINTERS_PER_RECORD = 5


def parse_int(value: str) -> int:
    return int(value, 0)


def decode_pointer(data: bytes, offset: int) -> dict[str, int]:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise ValueError("ROM size must be a power-of-two number of 64 KiB banks")
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    physical = ((bank & (bank_count - 1)) << 16) | bank_offset
    return {
        "pointer_offset": pointer_offset,
        "segment": segment,
        "bank": bank,
        "physical": physical,
    }


def shared_prefix(first: bytes, first_offset: int, second: bytes, second_offset: int) -> int:
    length = 0
    maximum = min(len(first) - first_offset, len(second) - second_offset)
    while length < maximum and first[first_offset + length] == second[second_offset + length]:
        length += 1
    return length


def all_offsets(data: bytes, needle: bytes, limit: int) -> list[int]:
    result: list[int] = []
    cursor = 0
    while len(result) < limit:
        offset = data.find(needle, cursor)
        if offset < 0:
            break
        result.append(offset)
        cursor = offset + 1
    return result


def record(data: bytes, table: int, index: int) -> dict[str, object]:
    offset = table + index * RECORD_BYTES
    if offset < 0 or offset + RECORD_BYTES > len(data):
        raise ValueError(f"record {index} at 0x{offset:X} falls outside ROM")
    return {
        "offset": offset,
        "raw_hex": data[offset:offset + RECORD_BYTES].hex(" "),
        "pointers": [decode_pointer(data, offset + field * 6)
                     for field in range(POINTERS_PER_RECORD)],
        "tail_hex": data[offset + 30:offset + 32].hex(" "),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("older", type=pathlib.Path)
    parser.add_argument("newer", type=pathlib.Path)
    parser.add_argument("--older-table", type=parse_int, required=True)
    parser.add_argument("--newer-table", type=parse_int, required=True)
    parser.add_argument("--records", type=int, default=60)
    parser.add_argument("--seed-size", type=parse_int, default=0x10)
    parser.add_argument("--match-limit", type=int, default=16)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    older = args.older.read_bytes()
    newer = args.newer.read_bytes()
    comparisons: list[dict[str, object]] = []
    for index in range(args.records):
        old_record = record(older, args.older_table, index)
        new_record = record(newer, args.newer_table, index)
        fields: list[dict[str, object]] = []
        for field in range(POINTERS_PER_RECORD):
            old_target = int(old_record["pointers"][field]["physical"])
            new_target = int(new_record["pointers"][field]["physical"])
            seed = newer[new_target:new_target + args.seed_size]
            candidates: list[dict[str, int]] = []
            if len(seed) == args.seed_size:
                for candidate in all_offsets(older, seed, args.match_limit):
                    candidates.append({
                        "older_target": candidate,
                        "shared_prefix": shared_prefix(older, candidate, newer, new_target),
                    })
            fields.append({
                "field": field,
                "older_target": old_target,
                "newer_target": new_target,
                "same_logical_target_prefix": shared_prefix(older, old_target, newer, new_target),
                "newer_seed_matches_in_older": candidates,
                "declared_old_target_is_seed_match": any(
                    item["older_target"] == old_target for item in candidates
                ),
            })
        comparisons.append({
            "record": index,
            "older_record": old_record,
            "newer_record": new_record,
            "fields": fields,
        })

    result = {
        "schema": 1,
        "older": {
            "sha256": hashlib.sha256(older).hexdigest().upper(),
            "size": len(older),
            "table": args.older_table,
        },
        "newer": {
            "sha256": hashlib.sha256(newer).hexdigest().upper(),
            "size": len(newer),
            "table": args.newer_table,
        },
        "record_bytes": RECORD_BYTES,
        "record_count": args.records,
        "seed_size": args.seed_size,
        "comparisons": comparisons,
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
