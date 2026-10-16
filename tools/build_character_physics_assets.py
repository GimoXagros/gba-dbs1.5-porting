#!/usr/bin/env python3
"""Convert WSC 1.5 physics through the source character pointer table.

Explicit legacy modes reproduce the frozen v48/v49 assets, including their
incorrect arithmetic source routing. They are not current physics assets.
"""

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
WSC_POINTER_TABLE = 0x3B8460
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


def source_record_offset(wsc: bytes, runtime_id: int, *, legacy_source_routing: bool = False) -> int:
    if not 0 <= runtime_id < POINTER_COUNT:
        raise ValueError("character ID outside the source pointer table")
    if legacy_source_routing:
        return WSC_TABLE + runtime_id * RECORD_BYTES
    # Source 7435EC..743601 selects ES=2846, C2=BB and loads a 16-bit
    # offset from ES:[character*2]. IDs 12-14 are not in arithmetic ID order.
    relative = struct.unpack_from("<H", wsc, WSC_POINTER_TABLE + runtime_id * 2)[0]
    physical = 0x2846 * 16 + relative
    if not 0x20000 <= physical <= 0x30000 - RECORD_BYTES:
        raise ValueError("physics record leaves its source C2 bank window")
    return (0xBB & 0x7F) * 0x10000 + (physical & 0xFFFF)


def converted_record(wsc: bytes, runtime_id: int, *, legacy_source_routing: bool = False) -> bytes:
    source = struct.unpack_from(
        f"<{RECORD_HALFWORDS}h", wsc,
        source_record_offset(wsc, runtime_id, legacy_source_routing=legacy_source_routing)
    )
    values = [convert_field(index, value) for index, value in enumerate(source)]
    return struct.pack(f"<{RECORD_HALFWORDS}h", *values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    legacy = parser.add_mutually_exclusive_group()
    legacy.add_argument("--legacy-v48-layout", action="store_true",
                        help="reproduce frozen v48 pointer and source-routing errors")
    legacy.add_argument("--legacy-v49-layout", action="store_true",
                        help="reproduce frozen v49 corrected pointers but incorrect source routing")
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if hashlib.sha256(wsc).hexdigest().upper() != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC 1.5 input")
    legacy_source = args.legacy_v48_layout or args.legacy_v49_layout

    mismatches = []
    for runtime_id in range(12):
        expected = gba[
            GBA_RECORD_TABLE + runtime_id * RECORD_BYTES:
            GBA_RECORD_TABLE + (runtime_id + 1) * RECORD_BYTES
        ]
        actual = converted_record(wsc, runtime_id, legacy_source_routing=legacy_source)
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
    # Keep the already installed payload coordinates and reserved hole. The
    # former code padded to record13_target but pointed at record12_target,
    # shifting all three actual records by one 0x78-byte record.
    record12_target = TARGET_BASE + pointer_bytes + RECORD_BYTES
    while record12_target % 4:
        record12_target += 1
    record13_target = record12_target + RECORD_BYTES
    record14_target = record13_target + RECORD_BYTES
    pointers = [GBA_BASE + GBA_RECORD_TABLE + index * RECORD_BYTES for index in range(12)]
    legacy_bias = RECORD_BYTES if args.legacy_v48_layout else 0
    pointers.extend(GBA_BASE + target - legacy_bias
                    for target in (record12_target, record13_target, record14_target))
    blob = bytearray(struct.pack(f"<{POINTER_COUNT}I", *pointers))
    blob.extend(bytes(record12_target - TARGET_BASE - len(blob)))
    records = {}
    for runtime_id, target in ((12, record12_target), (13, record13_target), (14, record14_target)):
        record = converted_record(wsc, runtime_id, legacy_source_routing=legacy_source)
        blob.extend(record)
        records[str(runtime_id)] = {
            "target": target - legacy_bias,
            "bytes": len(record),
            "sha256": hashlib.sha256(record).hexdigest().upper(),
            "source_offset": source_record_offset(wsc, runtime_id, legacy_source_routing=legacy_source),
        }

    if not args.legacy_v48_layout:
        for runtime_id in (12, 13, 14):
            pointer = struct.unpack_from("<I", blob, runtime_id * 4)[0]
            start = pointer - GBA_BASE - TARGET_BASE
            if blob[start:start + RECORD_BYTES] != converted_record(
                    wsc, runtime_id, legacy_source_routing=legacy_source):
                raise SystemExit(f"physics pointer does not reach its record: ID {runtime_id}")

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
    if not legacy_source:
        result["source_pointer_table"] = WSC_POINTER_TABLE
        result["source_routing"] = "ES 2846 / C2 BB, unsigned word at character * 2"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
