#!/usr/bin/env python3
"""Build all Ver. 1.5-only character palette blocks as one relocatable GBA blob."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from convert_wsc_palette_block import GBA_BYTES, WSC_BYTES, convert_block


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC_TABLE = 0x740000
RECORD_BYTES = 0x20


def parse_int(value: str) -> int:
    return int(value, 0)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise ValueError("WSC ROM must contain a power-of-two number of banks")
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target-base", type=parse_int, default=0x4A12A0)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc.read_bytes()
    digest = hashlib.sha256(wsc).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    specs = [
        ("base", runtime_id, runtime_id, field)
        for runtime_id in (12, 13, 14) for field in (2, 3)
    ] + [
        ("evolution", runtime_id, 30 + runtime_id, field)
        for runtime_id in (11, 12, 13, 14) for field in (2, 3)
    ]
    cursor = args.target_base
    output = bytearray()
    unique: dict[int, dict[str, object]] = {}
    references = []
    for group, runtime_id, record, field in specs:
        record_offset = WSC_TABLE + record * RECORD_BYTES
        source_target = wsc_pointer(wsc, record_offset + field * 6)
        entry = unique.get(source_target)
        if entry is None:
            aligned = align(cursor, 4)
            if aligned > cursor:
                output.extend(bytes(aligned - cursor))
            source = wsc[source_target:source_target + WSC_BYTES]
            converted = convert_block(source)
            target = aligned
            output.extend(converted)
            cursor = target + len(converted)
            entry = {
                "source_target": source_target,
                "target": target,
                "source_header_u16": list(struct.unpack_from("<3H", source)),
                "bytes": len(converted),
                "sha256": hashlib.sha256(converted).hexdigest().upper(),
            }
            unique[source_target] = entry
        references.append({
            "group": group,
            "runtime_id": runtime_id,
            "wsc_record": record,
            "wsc_field": field,
            "source_target": source_target,
            "gba_record_field": field - 2,
            "target": entry["target"],
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    manifest = {
        "schema": 1,
        "kind": "relocatable-gba-character-palettes",
        "source_wsc_sha256": digest,
        "target_base": args.target_base,
        "target_end": args.target_base + len(output),
        "blob_bytes": len(output),
        "blob_sha256": hashlib.sha256(output).hexdigest().upper(),
        "unique_block_count": len(unique),
        "reference_count": len(references),
        "unique_blocks": list(unique.values()),
        "references": references,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
