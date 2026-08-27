#!/usr/bin/env python3
"""Find tables shaped like the confirmed 32-byte GBA roster records."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


RECORD_BYTES = 32


def values(data: bytes, offset: int) -> list[int]:
    return list(struct.unpack_from("<8I", data, offset))


def record_shape(data: bytes, offset: int) -> bool:
    if offset < 0 or offset + RECORD_BYTES > len(data):
        return False
    fields = values(data, offset)
    return (
        fields[0] != 0
        and fields[1] != 0
        and fields[2] != 0
        and fields[3:6] == [0, 0, 0]
        and fields[6] != 0
        and fields[7] != 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--minimum-records", type=int, default=4)
    args = parser.parse_args()
    data = args.rom.read_bytes()

    tables: list[dict[str, object]] = []
    consumed = 0
    for start in range(0, len(data) - RECORD_BYTES + 1, 4):
        if start < consumed or not record_shape(data, start):
            continue
        records: list[dict[str, object]] = []
        cursor = start
        while record_shape(data, cursor):
            records.append({"offset": cursor, "u32": values(data, cursor)})
            cursor += RECORD_BYTES
        if len(records) >= args.minimum_records:
            tables.append({
                "start": start,
                "end": cursor,
                "record_count": len(records),
                "records": records,
            })
            consumed = cursor

    print(json.dumps({"record_bytes": RECORD_BYTES, "tables": tables}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
