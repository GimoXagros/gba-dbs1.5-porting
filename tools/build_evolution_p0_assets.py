#!/usr/bin/env python3
"""Build the four Ver. 1.5 evolution animation containers for GBA."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_full_asset_poc import build_asset


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC_TABLE = 0x740000
RECORD_BYTES = 0x20
EVOLUTION_RECORD_BIAS = 30


def parse_int(value: str) -> int:
    return int(value, 0)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target-base", type=parse_int, default=0x4B0000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    cursor = args.target_base
    blob = bytearray()
    entries = []
    for runtime_id in (11, 12, 13, 14):
        cursor = align(cursor, 32)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        record = WSC_TABLE + (EVOLUTION_RECORD_BIAS + runtime_id) * RECORD_BYTES
        source = wsc_pointer(wsc, record)
        converted, entry = build_asset(
            wsc,
            wsc_header=source,
            target_header=cursor,
            expected_layout_entries=None,
            expected_layout_record_bytes=None,
            expected_descriptor_entries=None,
            expected_tile_bytes=None,
        )
        blob.extend(converted)
        entry.update({
            "runtime_id": runtime_id,
            "wsc_record": EVOLUTION_RECORD_BIAS + runtime_id,
            "sha256": hashlib.sha256(converted).hexdigest().upper(),
        })
        entries.append(entry)
        cursor += len(converted)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "relocatable-gba-evolution-p0",
        "source_wsc_sha256": digest,
        "target_base": args.target_base,
        "target_end": args.target_base + len(blob),
        "blob_bytes": len(blob),
        "blob_sha256": hashlib.sha256(blob).hexdigest().upper(),
        "entries": entries,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
