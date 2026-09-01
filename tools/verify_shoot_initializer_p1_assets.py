#!/usr/bin/env python3
"""Independently verify the final-placement Shoot initializer P1 asset blob."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BLOB_SHA256 = "778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2"
TARGET_BASE = 0x5D0000
SPECS = (
    (0x3CF410, 0x5D0000, 668, [7, 8, 2, 7, 2, 8], 1),
    (0x3BD730, 0x5D029C, 1968, [12, 4, 2, 12, 12, 4, 6, 2, 12, 5, 4, 16, 18], 0),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def parse_wsc(data: bytes, source: int) -> dict[str, object]:
    table_relative, reserved, leading_count, leading_payload = struct.unpack_from("<4H", data, source)
    if table_relative != 4 or reserved != 0 or leading_count == 0:
        raise SystemExit(f"unexpected WSC P1 header at 0x{source:X}")
    table_bytes = leading_payload - 12
    if table_bytes <= 0 or table_bytes % 8:
        raise SystemExit(f"invalid WSC P1 table span at 0x{source:X}")
    entries = [
        struct.unpack_from("<4H", data, source + 8 + index * 8)
        for index in range(table_bytes // 8)
    ]
    terminal_a, terminal_b = struct.unpack_from("<2H", data, source + 8 + table_bytes)
    counts = [leading_count] + [entry[2] for entry in entries]
    payload_relatives = [leading_payload] + [entry[3] for entry in entries]
    a_relatives = [entries[0][0]] + [
        entries[index + 1][0] if index + 1 < len(entries) else terminal_a
        for index in range(len(entries))
    ]
    b_relatives = [entries[0][1]] + [
        entries[index + 1][1] if index + 1 < len(entries) else terminal_b
        for index in range(len(entries))
    ]
    payloads = [
        [
            data[source + relative + item * 12:source + relative + (item + 1) * 12]
            for item in range(count)
        ]
        for count, relative in zip(counts, payload_relatives, strict=True)
    ]
    if any(len(item) != 12 for payload in payloads for item in payload):
        raise SystemExit(f"truncated WSC P1 payload at 0x{source:X}")
    return {
        "counts": counts,
        "payloads": payloads,
        "a_relatives": a_relatives,
        "b_relatives": b_relatives,
    }


def convert_item(item: bytes) -> bytes:
    words = list(struct.unpack("<6H", item))
    if words[0] & 0xFF00 == 0xFF00:
        words[0] = 0xFF00 | (((words[0] & 0xFF) * 4 + 2) // 5)
    tail_a = 0
    tail_b = 0
    if words[5]:
        tail_a = words[5] + 0x032C
        tail_b = 0x0835
        words[5] = 0
    return struct.pack("<8H", *words, tail_a, tail_b)


def verify_entry(wsc: bytes, blob: bytes, spec: tuple[object, ...]) -> dict[str, object]:
    source, target, size, expected_counts, expected_non_null_b = spec
    parsed = parse_wsc(wsc, int(source))
    if parsed["counts"] != expected_counts:
        raise SystemExit(f"WSC P1 counts changed at 0x{int(source):X}")
    local = int(target) - TARGET_BASE
    entry = blob[local:local + int(size)]
    if len(entry) != size:
        raise SystemExit(f"P1 output entry is truncated at 0x{int(target):X}")
    table_pointer, reserved = struct.unpack_from("<2I", entry, 0)
    if table_pointer != GBA_BASE + int(target) + 8 or reserved != 0:
        raise SystemExit(f"P1 output header changed at 0x{int(target):X}")

    a_map: dict[int, int] = {}
    b_map: dict[int, int] = {}
    payload_items = 0
    for index, count in enumerate(expected_counts):
        actual_count, payload_pointer, a_pointer, b_pointer = struct.unpack_from(
            "<4I", entry, 8 + index * 16
        )
        if actual_count != count:
            raise SystemExit(f"P1 output count changed at 0x{int(target):X} command {index}")
        payload = payload_pointer - (GBA_BASE + int(target))
        expected_payload = b"".join(convert_item(item) for item in parsed["payloads"][index])
        if entry[payload:payload + len(expected_payload)] != expected_payload:
            raise SystemExit(f"P1 output payload differs at 0x{int(target):X} command {index}")
        payload_items += count

        a_relative = int(parsed["a_relatives"][index])
        a_local = a_pointer - (GBA_BASE + int(target))
        expected_a = wsc[int(source) + a_relative:int(source) + a_relative + 8]
        if entry[a_local:a_local + 8] != expected_a:
            raise SystemExit(f"P1 output A record differs at 0x{int(target):X} command {index}")
        if a_relative in a_map and a_map[a_relative] != a_local:
            raise SystemExit("one WSC A record was duplicated inconsistently")
        a_map[a_relative] = a_local

        b_relative = int(parsed["b_relatives"][index])
        if b_relative == 0:
            if b_pointer != 0:
                raise SystemExit(f"P1 output null B pointer changed at command {index}")
        else:
            b_local = b_pointer - (GBA_BASE + int(target))
            expected_b = wsc[int(source) + b_relative:int(source) + b_relative + 10]
            if entry[b_local:b_local + 10] != expected_b:
                raise SystemExit(f"P1 output B record differs at 0x{int(target):X} command {index}")
            if b_relative in b_map and b_map[b_relative] != b_local:
                raise SystemExit("one WSC B record was duplicated inconsistently")
            b_map[b_relative] = b_local

    if len(b_map) != expected_non_null_b:
        raise SystemExit(f"P1 non-null B population changed at 0x{int(target):X}")
    return {
        "wsc15_source": source,
        "target": target,
        "bytes": size,
        "sha256": sha256(entry),
        "commands": len(expected_counts),
        "payload_items": payload_items,
        "unique_a_records_exact": len(a_map),
        "unique_non_null_b_records_exact": len(b_map),
        "all_internal_pointers_in_entry": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("blob", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc15.read_bytes()
    blob = args.blob.read_bytes()
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    if sha256(blob) != BLOB_SHA256 or len(blob) != 2636:
        raise SystemExit("refusing unexpected Shoot initializer P1 blob")
    entries = [verify_entry(wsc, blob, spec) for spec in SPECS]
    if sum(int(row["payload_items"]) for row in entries) != 143:
        raise SystemExit("Shoot initializer P1 payload aggregate changed")

    result = {
        "schema": 1,
        "kind": "digimon-shoot-initializer-p1-independent-verification",
        "source_wsc15_sha256": WSC15_SHA256,
        "blob_sha256": BLOB_SHA256,
        "target_range": [TARGET_BASE, TARGET_BASE + len(blob)],
        "entries": entries,
        "claim_scope": (
            "independent final-placement pointer, payload, eight-byte A, and ten-byte B verification; "
            "no ROM integration, reachability, runtime, display, audio, or supplied-save QA"
        ),
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
