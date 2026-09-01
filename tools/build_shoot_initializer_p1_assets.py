#!/usr/bin/env python3
"""Build the two Ver. 1.5 Shoot-initializer P1 containers for native GBA.

The source format is the self-delimiting Shoot lineage.  Commercial WSC 1.0
to USA GBA pairs prove the payload expansion, eight-byte A-record identity,
and direct null/non-null ten-byte B behavior used here.  This builder emits
relocatable data only; it does not modify a ROM or claim runtime reachability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from shoot_resource_conversion import (  # type: ignore
    convert_shoot_payload_item,
    parse_shoot_p1,
)


GBA_BASE = 0x08000000
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
TARGET_BASE = 0x5D0000
SOURCES = (
    ("active_player_p1", 0x3CF410, [7, 8, 2, 7, 2, 8]),
    ("rules_object_p1", 0x3BD730, [12, 4, 2, 12, 12, 4, 6, 2, 12, 5, 4, 16, 18]),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def convert_container(parsed: dict[str, object], target: int) -> tuple[bytes, dict[str, object]]:
    commands = len(parsed["counts"])
    cursor = 8 + commands * 16
    payload_offsets = []
    for payload in parsed["payloads"]:
        payload_offsets.append(cursor)
        cursor += len(payload) * 16
    cursor = align(cursor, 4)

    a_offsets = {}
    for relative, record in sorted(parsed["a_records"].items()):
        if len(record) != 8:
            raise SystemExit("Shoot initializer A record is not eight bytes")
        a_offsets[relative] = cursor
        cursor += 8
    cursor = align(cursor, 2)

    b_offsets = {}
    for relative in sorted(set(parsed["b_relatives"])):
        if relative == 0:
            continue
        record = parsed["source_data"][relative:relative + 10]
        if len(record) != 10:
            raise SystemExit("Shoot initializer B record is truncated")
        b_offsets[relative] = cursor
        cursor += 10
    cursor = align(cursor, 4)

    output = bytearray(cursor)
    struct.pack_into("<2I", output, 0, GBA_BASE + target + 8, 0)
    for index, payload in enumerate(parsed["payloads"]):
        a_relative = int(parsed["a_relatives"][index])
        b_relative = int(parsed["b_relatives"][index])
        struct.pack_into(
            "<4I",
            output,
            8 + index * 16,
            len(payload),
            GBA_BASE + target + payload_offsets[index],
            GBA_BASE + target + a_offsets[a_relative],
            0 if b_relative == 0 else GBA_BASE + target + b_offsets[b_relative],
        )
        local = payload_offsets[index]
        for item, source_item in enumerate(payload):
            converted = convert_shoot_payload_item(source_item)
            output[local + item * 16:local + (item + 1) * 16] = converted

    for relative, record in parsed["a_records"].items():
        local = a_offsets[relative]
        output[local:local + 8] = record
    for relative, local in b_offsets.items():
        output[local:local + 10] = parsed["source_data"][relative:relative + 10]

    details = {
        "bytes": len(output),
        "commands": commands,
        "payload_items": sum(parsed["counts"]),
        "a_records": len(a_offsets),
        "non_null_b_records": len(b_offsets),
        "payload_rule": "commercially proved Shoot-lineage 12-byte to 16-byte expansion",
        "a_rule": "commercially proved eight-byte identity",
        "b_rule": "zero remains null; nonzero ten-byte record copied and relocated directly",
        "sha256": sha256(output),
    }
    return bytes(output), details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument("--target-base", type=lambda value: int(value, 0), default=TARGET_BASE)
    args = parser.parse_args()

    wsc15 = args.wsc15.read_bytes()
    if sha256(wsc15) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")

    blob = bytearray()
    cursor = args.target_base
    entries = []
    for label, source, expected_counts in SOURCES:
        cursor = align(cursor, 4)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        parsed = parse_shoot_p1(wsc15, source)
        if list(parsed["counts"]) != expected_counts:
            raise SystemExit(f"Shoot initializer P1 counts changed at 0x{source:X}")
        parsed["source_data"] = wsc15[source:]
        converted, details = convert_container(parsed, cursor)
        blob.extend(converted)
        entries.append({
            "label": label,
            "wsc15_source": source,
            "target": cursor,
            **details,
        })
        cursor += len(converted)

    output = bytes(blob)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    manifest = {
        "schema": 1,
        "kind": "digimon-shoot-initializer-p1-assets",
        "source_wsc15_sha256": WSC15_SHA256,
        "target_base": args.target_base,
        "target_end": args.target_base + len(output),
        "bytes": len(output),
        "sha256": sha256(output),
        "entries": entries,
        "claim_scope": (
            "commercially bounded P1 payload/A/B conversion and fixed relocatable placement only; "
            "no ROM writes, initializer/menu connection, runtime, visual output, or supplied-save QA"
        ),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-initializer-p1] PASS {args.output} {manifest['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
