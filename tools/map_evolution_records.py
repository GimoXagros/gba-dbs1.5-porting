#!/usr/bin/env python3
"""Report aligned WSC/GBA ID-indexed evolution resource records."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
WSC_TABLE = 0x7403C0
GBA_TABLE = 0x0D42A0
RECORD_BYTES = 0x20
RECORDS = 16


def wsc_pointer(data: bytes, offset: int) -> dict[str, int]:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    physical = ((bank & 0x7F) << 16) | bank_offset
    return {
        "offset": pointer_offset,
        "segment": segment,
        "bank": bank,
        "physical": physical,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    args = parser.parse_args()
    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()

    records = []
    for runtime_id in range(RECORDS):
        wsc_offset = WSC_TABLE + runtime_id * RECORD_BYTES
        gba_offset = GBA_TABLE + runtime_id * RECORD_BYTES
        pointers = [wsc_pointer(wsc, wsc_offset + index * 6) for index in range(5)]
        fields = struct.unpack_from("<8I", gba, gba_offset)
        records.append({
            "runtime_id": runtime_id,
            "wsc_record_offset": wsc_offset,
            "wsc_pointer_targets": [item["physical"] for item in pointers],
            "wsc_pointers": pointers,
            "gba_record_offset": gba_offset,
            "gba_pointer_targets": [
                value - GBA_BASE if GBA_BASE <= value < GBA_BASE + len(gba) else None
                for value in fields
            ],
            "gba_fields_u32": list(fields),
        })

    print(json.dumps({
        "gba_sha256": hashlib.sha256(gba).hexdigest(),
        "wsc_sha256": hashlib.sha256(wsc).hexdigest(),
        "wsc_table_offset": WSC_TABLE,
        "gba_table_offset": GBA_TABLE,
        "record_bytes": RECORD_BYTES,
        "record_count": RECORDS,
        "records": records,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
