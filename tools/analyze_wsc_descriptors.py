#!/usr/bin/env python3
"""Locate WSC frame descriptors of the confirmed 8-byte graphics format."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_entry(rom: bytes, offset: int) -> dict[str, int] | None:
    if offset < 0 or offset + 8 > len(rom):
        return None
    length, bank_offset, destination, bank = struct.unpack_from("<4H", rom, offset)
    if not (0x20 <= length <= 0x2000 and length % 0x20 == 0):
        return None
    if destination != 0x2000 or not (0x80 <= bank <= 0xFF):
        return None
    physical = ((bank & 0x7F) << 16) | bank_offset
    if physical + length > len(rom):
        return None
    if bank_offset + length > 0x10000:
        return None
    return {
        "descriptor_offset": offset,
        "length": length,
        "bank_offset": bank_offset,
        "destination": destination,
        "bank": bank,
        "physical_offset": physical,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--minimum-entries", type=int, default=4)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    rom = args.wsc.read_bytes()
    scan_end = len(rom) if args.scan_end is None else min(args.scan_end, len(rom))
    candidates: list[dict[str, object]] = []
    consumed_until = args.scan_start

    for start in range(args.scan_start, scan_end - 7, 2):
        if start < consumed_until:
            continue
        first = parse_entry(rom, start)
        if first is None:
            continue
        entries = [first]
        cursor = start + 8
        while cursor + 8 <= scan_end:
            entry = parse_entry(rom, cursor)
            if entry is None:
                break
            previous = entries[-1]
            contiguous = entry["physical_offset"] == previous["physical_offset"] + previous["length"]
            new_block = entry["bank_offset"] == 0 and entry["bank"] != previous["bank"]
            if not (contiguous or new_block):
                break
            entries.append(entry)
            cursor += 8
        if len(entries) >= args.minimum_entries:
            blocks: list[dict[str, int]] = []
            block_start = 0
            for index in range(1, len(entries) + 1):
                at_end = index == len(entries)
                if at_end or entries[index]["physical_offset"] != entries[index - 1]["physical_offset"] + entries[index - 1]["length"]:
                    block_entries = entries[block_start:index]
                    blocks.append({
                        "entry_start": block_start,
                        "entry_end": index,
                        "physical_start": block_entries[0]["physical_offset"],
                        "physical_end": block_entries[-1]["physical_offset"] + block_entries[-1]["length"],
                        "bytes": sum(entry["length"] for entry in block_entries),
                    })
                    block_start = index
            candidate: dict[str, object] = {
                "table_offset": start,
                "entry_count": len(entries),
                "descriptor_bytes": len(entries) * 8,
                "payload_bytes": sum(entry["length"] for entry in entries),
                "blocks": blocks,
            }
            if not args.summary_only:
                candidate["entries"] = entries
            candidates.append(candidate)
            consumed_until = cursor

    print(json.dumps({
        "scan_range": [args.scan_start, scan_end],
        "candidate_count": len(candidates),
        "candidates": candidates,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
