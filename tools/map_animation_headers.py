#!/usr/bin/env python3
"""Map WSC and GBA animation headers by byte-identical layout records."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import struct


GBA_BASE = 0x08000000
HEADER_TAIL = bytes.fromhex("05 00 24 00 80 04 0A 00")


def find_headers(data: bytes) -> list[int]:
    result: list[int] = []
    cursor = 0
    while True:
        tail = data.find(HEADER_TAIL, cursor)
        if tail < 0:
            return result
        result.append(tail - 8)
        cursor = tail + 1


def gba_layout(data: bytes, header: int) -> tuple[int, bytes]:
    table_pointer = struct.unpack_from("<I", data, header)[0]
    table = table_pointer - GBA_BASE
    first_count, first_pointer = struct.unpack_from("<II", data, table)
    first_record = first_pointer - GBA_BASE
    entries = (first_record - table) // 8
    if first_count == 0 or entries <= 0:
        raise ValueError(f"bad GBA layout at 0x{header:X}")
    expected = first_record
    for index in range(entries):
        count, pointer = struct.unpack_from("<II", data, table + index * 8)
        record = pointer - GBA_BASE
        if count == 0 or record != expected:
            raise ValueError(f"non-contiguous GBA layout at 0x{header:X}")
        expected += count * 4
    return entries, data[first_record:expected]


def wsc_layout(data: bytes, header: int) -> tuple[int, bytes]:
    relative = struct.unpack_from("<I", data, header)[0]
    table = header + relative
    first_count, first_relative = struct.unpack_from("<HH", data, table)
    entries = (first_relative - relative) // 4
    if first_count == 0 or entries <= 0:
        raise ValueError(f"bad WSC layout at 0x{header:X}")
    expected = first_relative
    for index in range(entries):
        count, record_relative = struct.unpack_from("<HH", data, table + index * 4)
        if count == 0 or record_relative != expected:
            raise ValueError(f"non-contiguous WSC layout at 0x{header:X}")
        expected += count * 4
    return entries, data[header + first_relative:header + expected]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    args = parser.parse_args()
    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()

    gba_rows = []
    for header in find_headers(gba):
        entries, records = gba_layout(gba, header)
        gba_rows.append((header, entries, records))

    print("WSC_HEADER ENTRIES RECORD_BYTES RECORD_SHA256 GBA_HEADER")
    for header in find_headers(wsc):
        entries, records = wsc_layout(wsc, header)
        matches = [gba_header for gba_header, _, gba_records in gba_rows if gba_records == records]
        match_text = ",".join(f"0x{item:06X}" for item in matches) or "WSC_ONLY"
        print(
            f"0x{header:06X} {entries:7d} {len(records):12d} "
            f"{hashlib.sha256(records).hexdigest()} {match_text}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
