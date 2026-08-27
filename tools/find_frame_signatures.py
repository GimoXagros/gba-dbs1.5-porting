#!/usr/bin/env python3
"""Search WSC metadata for signatures derived from a GBA frame table."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def all_offsets(haystack: bytes, needle: bytes, limit: int = 64) -> list[int]:
    offsets: list[int] = []
    start = 0
    while len(offsets) < limit:
        offset = haystack.find(needle, start)
        if offset < 0:
            break
        offsets.append(offset)
        start = offset + 1
    return offsets


def strided_matches(
    data: bytes,
    values: list[int],
    width: int,
    stride: int,
    limit: int = 64,
) -> list[int]:
    if stride < width:
        return []
    fmt = {1: "B", 2: "<H", 4: "<I"}[width]
    matches: list[int] = []
    span = (len(values) - 1) * stride + width
    first = struct.pack(fmt, values[0])
    start = data.find(first)
    while 0 <= start <= len(data) - span:
        if all(struct.unpack_from(fmt, data, start + index * stride)[0] == value
               for index, value in enumerate(values[1:], start=1)):
            matches.append(start)
            if len(matches) >= limit:
                break
        start = data.find(first, start + 1)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--table", type=parse_int, default=0x2DD3F8)
    parser.add_argument("--entries", type=int, default=101)
    parser.add_argument("--signature-entries", type=int, default=12)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    lengths = [struct.unpack_from("<I", gba, args.table + index * 8)[0]
               for index in range(args.entries)]
    sample = lengths[:args.signature_entries]
    variants = {
        "byte_lengths": sample,
        "tile_counts": [value // 32 for value in sample],
    }
    results: list[dict[str, object]] = []
    for name, values in variants.items():
        for width in (1, 2, 4):
            maximum = (1 << (width * 8)) - 1
            if any(value > maximum for value in values):
                continue
            fmt = {1: "B", 2: "<H", 4: "<I"}[width]
            packed = b"".join(struct.pack(fmt, value) for value in values)
            direct = all_offsets(wsc, packed)
            if direct:
                results.append({
                    "variant": name,
                    "width": width,
                    "stride": width,
                    "offsets": direct,
                })
            for stride in range(width + 1, 17):
                offsets = strided_matches(wsc, values, width, stride)
                if offsets:
                    results.append({
                        "variant": name,
                        "width": width,
                        "stride": stride,
                        "offsets": offsets,
                    })

    print(json.dumps({
        "gba_table_offset": args.table,
        "entry_count": args.entries,
        "signature_entries": args.signature_entries,
        "first_lengths": sample,
        "results": results,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
