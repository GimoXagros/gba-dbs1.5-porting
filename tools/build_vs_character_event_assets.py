#!/usr/bin/env python3
"""Expand VS character events and relocate the retail boss sentinel to 15."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
GBA_BASE = 0x08000000
SOURCE_TABLE = 0x0B77F4
SOURCE_ENTRIES = 13
ENTRY_BYTES = 0x10
COMMON_COMMAND_POINTER = 0x080B7994
TARGET_BASE = 0x485220


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")

    original = gba[SOURCE_TABLE:SOURCE_TABLE + SOURCE_ENTRIES * ENTRY_BYTES]
    for runtime_id in range(SOURCE_ENTRIES):
        one, record, common, zero = struct.unpack_from("<4I", original, runtime_id * ENTRY_BYTES)
        if zero != 0 or one != 1 or common != COMMON_COMMAND_POINTER:
            raise SystemExit(f"unexpected official VS event entry {runtime_id}")
        if record != GBA_BASE + 0x0B78C4 + runtime_id * ENTRY_BYTES:
            raise SystemExit(f"unexpected official VS event record pointer {runtime_id}")

    table_bytes = 16 * ENTRY_BYTES
    custom_ids = (12, 13, 14, 15)
    record_targets = {
        runtime_id: TARGET_BASE + table_bytes + index * ENTRY_BYTES
        for index, runtime_id in enumerate(custom_ids)
    }
    blob = bytearray(original[:12 * ENTRY_BYTES])
    for runtime_id in custom_ids:
        blob.extend(struct.pack(
            "<4I", 1, GBA_BASE + record_targets[runtime_id],
            COMMON_COMMAND_POINTER, 0,
        ))

    # Resource 0 is the Guilmon presentation, 11/12 are the reconstructed new
    # character resources, and resource 10 is the retail boss presentation.
    records = []
    for runtime_id, resource_index in ((12, 0), (13, 11), (14, 12), (15, 10)):
        record = struct.pack("<4BIII", 1, 0xFF, resource_index, 0, runtime_id, 0, 0)
        if len(record) != ENTRY_BYTES:
            raise AssertionError("VS event record size invariant failed")
        blob.extend(record)
        records.append({
            "runtime_id": runtime_id,
            "resource_index": resource_index,
            "target": record_targets[runtime_id],
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    result = {
        "schema": 1,
        "source_gba_sha256": GBA_SHA256,
        "target_base": TARGET_BASE,
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "table_target": TARGET_BASE,
        "entry_count": 16,
        "records": records,
        "claim_scope": "VS event expansion for Extra Guilmon, Patamon, Tailmon, and relocated boss sentinel",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
