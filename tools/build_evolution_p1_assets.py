#!/usr/bin/env python3
"""Build the four Ver. 1.5 evolution P1 command containers for GBA."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

from build_new_base_p1_assets import (
    GBA_SHA256, RECORD_BYTES, WSC15_SHA256, WSC_TABLE, align, convert_source,
    parse_int, parse_source, read_template_entries, wsc_pointer,
)


EVOLUTION_RECORD_BIAS = 30


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--gba", type=pathlib.Path, required=True)
    parser.add_argument("--target-base", type=parse_int, default=0x560000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")
    gba = args.gba.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA template input")
    evolution_table = 0x0D42A0
    template_evo1 = read_template_entries(
        gba, evolution_table + (1 - 1) * RECORD_BYTES + 7 * 4
    )
    template_evo3 = read_template_entries(
        gba, evolution_table + (3 - 1) * RECORD_BYTES + 7 * 4
    )
    cursor = args.target_base
    blob = bytearray()
    entries = []
    for runtime_id in (11, 12, 13, 14):
        cursor = align(cursor, 4)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        record = WSC_TABLE + (EVOLUTION_RECORD_BIAS + runtime_id) * RECORD_BYTES
        source = wsc_pointer(wsc, record + 6)
        handlers = template_evo3 if runtime_id in (11, 13) else template_evo1
        converted, entry = convert_source(parse_source(wsc, source), cursor, handlers)
        blob.extend(converted)
        cursor += len(converted)
        entry.update({
            "runtime_id": runtime_id,
            "wsc_record": EVOLUTION_RECORD_BIAS + runtime_id,
        })
        entries.append(entry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "candidate-relocatable-gba-evolution-p1",
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
