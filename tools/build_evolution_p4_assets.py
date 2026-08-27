#!/usr/bin/env python3
"""Build the four Ver. 1.5 evolution P4 behavior containers for GBA."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

from build_new_base_p4_assets import (
    RECORD_BYTES, WSC15_SHA256, WSC_TABLE, align, convert_container,
    learn, parse_int, wsc_pointer,
)


EVOLUTION_RECORD_BIAS = 30


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target-base", type=parse_int, default=0x568000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    learned = learn(corpus)
    wsc = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")
    cursor = args.target_base
    blob = bytearray()
    entries = []
    for runtime_id in (11, 12, 13, 14):
        cursor = align(cursor, 4)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        record = WSC_TABLE + (EVOLUTION_RECORD_BIAS + runtime_id) * RECORD_BYTES
        source = wsc_pointer(wsc, record + 24)
        converted, entry = convert_container(wsc, source, cursor, learned)
        blob.extend(converted)
        cursor += len(converted)
        entry.update({
            "runtime_id": runtime_id,
            "wsc_record": EVOLUTION_RECORD_BIAS + runtime_id,
            "sha256": hashlib.sha256(converted).hexdigest().upper(),
        })
        entries.append(entry)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "candidate-relocatable-gba-evolution-p4",
        "source_wsc_sha256": digest,
        "corpus_sha256": hashlib.sha256(args.corpus.read_bytes()).hexdigest().upper(),
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
