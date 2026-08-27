#!/usr/bin/env python3
"""Locate candidate GBA (byte length, ROM pointer) frame tables.

This is an analysis tool: it emits candidates and does not modify either ROM.
Sequences are required to describe contiguous, tile-aligned ROM payloads.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


ROM_BASE = 0x08000000


def parse_int(value: str) -> int:
    return int(value, 0)


def entry_at(rom: bytes, offset: int) -> tuple[int, int] | None:
    if offset < 0 or offset + 8 > len(rom):
        return None
    length, pointer = struct.unpack_from("<II", rom, offset)
    payload = pointer - ROM_BASE
    if not (0x20 <= length <= 0x10000 and length % 0x20 == 0):
        return None
    if not (0 <= payload <= len(rom) - length):
        return None
    if pointer % 4:
        return None
    return length, pointer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--minimum-entries", type=int, default=4)
    parser.add_argument(
        "--mapping",
        action="append",
        default=[],
        metavar="GBA:WSC:LENGTH",
        help="confirmed converted payload mapping; may be repeated",
    )
    args = parser.parse_args()

    rom = args.gba.read_bytes()
    scan_end = len(rom) if args.scan_end is None else min(args.scan_end, len(rom))
    mappings = args.mapping or ["0x2DD720:0x1B0000:0xFD40", "0x2ED460:0x290000:0xB8A0"]
    parsed_mappings = [tuple(parse_int(value) for value in item.split(":")) for item in mappings]
    candidates: list[dict[str, object]] = []
    consumed_until = args.scan_start

    for start in range(args.scan_start, scan_end - 7, 4):
        if start < consumed_until:
            continue
        first = entry_at(rom, start)
        if first is None:
            continue
        entries: list[dict[str, int | None]] = []
        table_offset = start
        expected_pointer: int | None = None
        while table_offset + 8 <= scan_end:
            entry = entry_at(rom, table_offset)
            if entry is None:
                break
            length, pointer = entry
            if expected_pointer is not None and pointer != expected_pointer:
                break
            payload = pointer - ROM_BASE
            wsc_offset: int | None = None
            for gba_base, wsc_base, mapping_length in parsed_mappings:
                delta = payload - gba_base
                if 0 <= delta and delta + length <= mapping_length:
                    wsc_offset = wsc_base + delta
                    break
            entries.append({
                "descriptor_offset": table_offset,
                "length": length,
                "gba_payload_offset": payload,
                "wsc_payload_offset": wsc_offset,
            })
            expected_pointer = pointer + length
            table_offset += 8
        if len(entries) >= args.minimum_entries:
            candidates.append({
                "table_offset": start,
                "entry_count": len(entries),
                "descriptor_bytes": len(entries) * 8,
                "payload_start": entries[0]["gba_payload_offset"],
                "payload_end": entries[-1]["gba_payload_offset"] + entries[-1]["length"],
                "payload_bytes": sum(int(entry["length"]) for entry in entries),
                "entries": entries,
            })
            consumed_until = table_offset

    print(json.dumps({
        "scan_range": [args.scan_start, scan_end],
        "confirmed_mappings": [
            {"gba_offset": gba, "wsc_offset": wsc, "length": length}
            for gba, wsc, length in parsed_mappings
        ],
        "candidate_count": len(candidates),
        "candidates": candidates,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
