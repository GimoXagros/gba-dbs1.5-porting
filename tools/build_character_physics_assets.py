#!/usr/bin/env python3
"""Convert the WSC 1.5 character-physics records for GBA IDs 12 through 14."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
WSC_TABLE = 0x3B847E
GBA_RECORD_TABLE = 0x353508
RECORD_BYTES = 0x78
RECORD_HALFWORDS = RECORD_BYTES // 2
TARGET_BASE = 0x485000
POINTER_COUNT = 15


def trunc_div(numerator: int, denominator: int) -> int:
    return (abs(numerator) // denominator) * (-1 if numerator < 0 else 1)


def convert_field(index: int, value: int) -> int:
    field = index % 20
    if field in {0, 1, 2, 5, 6, 10}:
        # One shared third-form vertical constant is the sole systematic
        # exception in IDs 0-10 of the official GBA conversion.
        if field == 2 and value == -804:
            return -1011
        return trunc_div(value * 5, 4)
    if field in {3, 4, 7, 9, 11, 12, 13, 14}:
        return trunc_div(value * 25, 16)
    if field == 8:
        return trunc_div(value * 4, 5)
    return value


def converted_record(wsc: bytes, runtime_id: int) -> bytes:
    source = struct.unpack_from(
        f"<{RECORD_HALFWORDS}h", wsc, WSC_TABLE + runtime_id * RECORD_BYTES
    )
    values = [convert_field(index, value) for index, value in enumerate(source)]
    return struct.pack(f"<{RECORD_HALFWORDS}h", *values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if hashlib.sha256(wsc).hexdigest().upper() != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC 1.5 input")

    mismatches = []
    for runtime_id in range(12):
        expected = gba[
            GBA_RECORD_TABLE + runtime_id * RECORD_BYTES:
            GBA_RECORD_TABLE + (runtime_id + 1) * RECORD_BYTES
        ]
        actual = converted_record(wsc, runtime_id)
        for index, (left, right) in enumerate(zip(
            struct.unpack(f"<{RECORD_HALFWORDS}h", actual),
            struct.unpack(f"<{RECORD_HALFWORDS}h", expected),
        )):
            if left != right:
                mismatches.append({
                    "runtime_id": runtime_id,
                    "halfword_index": index,
                    "converted": left,
                    "official": right,
                })
    non_special = [item for item in mismatches if item["runtime_id"] != 11]
    if non_special:
        raise SystemExit("physics conversion does not reproduce official IDs 0-10")
    if len(mismatches) != 13:
        raise SystemExit("unexpected official ID-11 special-form mismatch pattern")

    pointer_bytes = POINTER_COUNT * 4
    record12_target = TARGET_BASE + pointer_bytes
    while record12_target % 4:
        record12_target += 1
    record13_target = record12_target + RECORD_BYTES
    record14_target = record13_target + RECORD_BYTES
    pointers = [GBA_BASE + GBA_RECORD_TABLE + index * RECORD_BYTES for index in range(12)]
    pointers.extend((GBA_BASE + record12_target, GBA_BASE + record13_target, GBA_BASE + record14_target))
    blob = bytearray(struct.pack(f"<{POINTER_COUNT}I", *pointers))
    blob.extend(bytes(record13_target - TARGET_BASE - len(blob)))
    records = {}
    for runtime_id, target in ((12, record12_target), (13, record13_target), (14, record14_target)):
        record = converted_record(wsc, runtime_id)
        blob.extend(record)
        records[str(runtime_id)] = {
            "target": target,
            "bytes": len(record),
            "sha256": hashlib.sha256(record).hexdigest().upper(),
            "source_offset": WSC_TABLE + runtime_id * RECORD_BYTES,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    result = {
        "schema": 1,
        "source_gba_sha256": GBA_SHA256,
        "source_wsc_sha256": WSC15_SHA256,
        "target_base": TARGET_BASE,
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "pointer_table_target": TARGET_BASE,
        "pointer_count": POINTER_COUNT,
        "records": records,
        "official_corpus_exact_ids": list(range(11)),
        "official_id11_special_form_mismatch_fields": mismatches,
        "claim_scope": "character physics/hitbox records; conversion exactly reproduces official GBA IDs 0-10",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
