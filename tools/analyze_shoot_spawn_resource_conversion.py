#!/usr/bin/env python3
"""Bound the resource conversion required by WSC 1.5 Shoot helper 9229.

The helper's three far resource arguments are resolved to P1, P0, and P2
containers.  Their WSC 1.0/commercial GBA ancestors are used as conversion
oracles before the same converters are applied to the Ver. 1.5 sources.  The
report deliberately separates exact byte equality from relocatable structural
conversion.
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

from build_full_asset_poc import build_asset  # type: ignore
from convert_wsc_palette_block import convert_block  # type: ignore


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OLD_SOURCES = {"p1": 0x2AE180, "p0": 0x2AD910, "p2": 0x2B5C00}
NEW_SOURCES = {"p1": 0x3D1E30, "p0": 0x22FF80, "p2": 0x3D7AF0}
GBA_SOURCES = {"p1": 0x350248, "p0": 0x3505E8, "p2": 0x352240}
ANALYSIS_TARGETS = {"p1": 0x5BA000, "p0": 0x5BB000, "p2": 0x5BF000}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"refusing unknown {label}: {actual}")


def comparison(actual: bytes, expected: bytes) -> dict[str, int | str | bool | None]:
    if len(actual) != len(expected):
        raise ValueError("comparison lengths differ")
    mismatch_offsets = [
        offset for offset, (left, right) in enumerate(zip(actual, expected, strict=True))
        if left != right
    ]
    return {
        "bytes": len(actual),
        "actual_sha256": sha256(actual),
        "expected_sha256": sha256(expected),
        "exact": not mismatch_offsets,
        "mismatch_bytes": len(mismatch_offsets),
        "first_mismatch": mismatch_offsets[0] if mismatch_offsets else None,
        "exact_prefix_bytes": mismatch_offsets[0] if mismatch_offsets else len(actual),
    }


def convert_shoot_payload_item(item: bytes) -> bytes:
    words = list(struct.unpack("<6H", item))
    if words[0] & 0xFF00 == 0xFF00:
        distance = words[0] & 0xFF
        words[0] = 0xFF00 | ((distance * 4 + 2) // 5)
    tail_a = 0
    tail_b = 0
    if words[5] != 0:
        tail_a = words[5] + 0x032C
        tail_b = 0x0835
        words[5] = 0
    return struct.pack("<8H", *words, tail_a, tail_b)


def parse_shoot_p1(data: bytes, source: int) -> dict[str, object]:
    table_relative, reserved, leading_count, leading_payload_relative = struct.unpack_from(
        "<4H", data, source
    )
    if table_relative != 4 or reserved != 0 or leading_count == 0:
        raise ValueError("unexpected Shoot-lineage P1 header")
    table_bytes = leading_payload_relative - 8 - 4
    if table_bytes <= 0 or table_bytes % 8:
        raise ValueError("cannot derive Shoot-lineage P1 table population")
    table_count = table_bytes // 8
    entries = [
        struct.unpack_from("<4H", data, source + 8 + index * 8)
        for index in range(table_count)
    ]
    terminal_a, terminal_b = struct.unpack_from("<2H", data, source + 8 + table_bytes)
    counts = [leading_count] + [entry[2] for entry in entries]
    payload_relatives = [leading_payload_relative] + [entry[3] for entry in entries]
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
            data[
                source + relative + item * 12:
                source + relative + (item + 1) * 12
            ]
            for item in range(count)
        ]
        for count, relative in zip(counts, payload_relatives, strict=True)
    ]
    if any(len(item) != 12 for payload in payloads for item in payload):
        raise ValueError("Shoot-lineage P1 payload is truncated")
    a_records = {
        relative: data[source + relative:source + relative + 8]
        for relative in sorted(set(a_relatives))
    }
    if any(len(record) != 8 for record in a_records.values()):
        raise ValueError("Shoot-lineage P1 A record is truncated")
    return {
        "table_relative": table_relative,
        "reserved": reserved,
        "leading_count": leading_count,
        "leading_payload_relative": leading_payload_relative,
        "table_command_count": table_count,
        "command_count": len(counts),
        "counts": counts,
        "payload_relatives": payload_relatives,
        "a_relatives": a_relatives,
        "b_relatives": b_relatives,
        "payloads": payloads,
        "a_records": a_records,
    }


def verify_commercial_p1(parsed: dict[str, object], gba: bytes, source: int) -> dict[str, object]:
    table_pointer, reserved = struct.unpack_from("<2I", gba, source)
    if reserved != 0 or table_pointer != GBA_BASE + source + 8:
        raise SystemExit("commercial GBA Shoot-lineage P1 header changed")
    first_payload = struct.unpack_from("<I", gba, source + 8 + 4)[0]
    command_count = (first_payload - (GBA_BASE + source + 8)) // 16
    if command_count != parsed["command_count"]:
        raise SystemExit("commercial Shoot-lineage P1 command population changed")
    payload_checks = []
    a_checks = []
    for index in range(command_count):
        count, payload_pointer, a_pointer, b_pointer = struct.unpack_from(
            "<4I", gba, source + 8 + index * 16
        )
        expected_items = parsed["payloads"][index]
        if count != len(expected_items):
            raise SystemExit("commercial Shoot-lineage P1 payload count changed")
        expected_payload = b"".join(
            convert_shoot_payload_item(item) for item in expected_items
        )
        payload_offset = payload_pointer - GBA_BASE
        actual_payload = gba[payload_offset:payload_offset + len(expected_payload)]
        payload_checks.append(comparison(expected_payload, actual_payload))
        expected_a = parsed["a_records"][parsed["a_relatives"][index]]
        actual_a = gba[a_pointer - GBA_BASE:a_pointer - GBA_BASE + len(expected_a)]
        a_checks.append(comparison(expected_a, actual_a))
        if parsed["b_relatives"][index] != 0 or b_pointer != 0:
            raise SystemExit("unexpected nonzero Shoot-lineage P1 B record")
    return {
        "command_count": command_count,
        "payload_item_count": sum(parsed["counts"]),
        "payloads_exact": all(check["exact"] for check in payload_checks),
        "a_records_exact": all(check["exact"] for check in a_checks),
        "payload_checks": payload_checks,
        "a_record_checks": a_checks,
    }


def convert_shoot_p1(parsed: dict[str, object], target: int) -> tuple[bytes, dict[str, object]]:
    command_count = int(parsed["command_count"])
    cursor = 8 + command_count * 16
    payload_offsets = []
    for payload in parsed["payloads"]:
        payload_offsets.append(cursor)
        cursor += len(payload) * 16
    cursor = (cursor + 3) & ~3
    a_offsets = {}
    for relative, record in parsed["a_records"].items():
        a_offsets[relative] = cursor
        cursor += len(record)
    cursor = (cursor + 3) & ~3
    output = bytearray(cursor)
    struct.pack_into("<2I", output, 0, GBA_BASE + target + 8, 0)
    for index in range(command_count):
        struct.pack_into(
            "<4I", output, 8 + index * 16,
            parsed["counts"][index],
            GBA_BASE + target + payload_offsets[index],
            GBA_BASE + target + a_offsets[parsed["a_relatives"][index]],
            0,
        )
        local = payload_offsets[index]
        for item, source_item in enumerate(parsed["payloads"][index]):
            converted = convert_shoot_payload_item(source_item)
            output[local + item * 16:local + (item + 1) * 16] = converted
    for relative, record in parsed["a_records"].items():
        local = a_offsets[relative]
        output[local:local + len(record)] = record
    details = {
        "command_count": command_count,
        "payload_item_count": sum(parsed["counts"]),
        "a_record_count": len(parsed["a_records"]),
        "b_pointer_rule": "all zero",
        "payload_rule": (
            "12-byte WSC item expands to 16 bytes; FFxx timing scales 4/5; "
            "nonzero word 5 moves to tails (word5+0x032C, 0x0835)"
        ),
        "a_record_rule": "8-byte record identity",
    }
    return bytes(output), details


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    old = args.wsc10.read_bytes()
    new = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(old, WSC10_SHA256, "WSC 1.0 source")
    require_hash(new, WSC15_SHA256, "WSC 1.5 source")

    # The helper call-site encodings prove these resolved physical addresses.
    old_overlay = old[0x390900:0x3A0900]
    new_overlay = new[0x740900:0x750900]
    if old_overlay[0x5B17:0x5B46] != bytes.fromhex(
        "6A 00 68 99 00 68 00 18 68 00 40 68 EB 00 68 C0 25 68 00 00 "
        "68 EA 00 68 91 2D 68 00 00 68 EA 00 68 18 2E 68 00 00 68 00 0C "
        "57 9A 14 24 B2 96"
    ):
        raise SystemExit("WSC 1.0 helper resource arguments changed")
    if new_overlay[0x92A4:0x92D3] != bytes.fromhex(
        "6A 01 68 D1 01 68 00 18 68 00 40 68 BD 00 68 AF 27 68 00 00 "
        "68 A2 00 68 F8 2F 68 00 00 68 BD 00 68 E3 21 68 00 00 68 00 0C "
        "57 9A F4 23 FF 4F"
    ):
        raise SystemExit("WSC 1.5 helper resource arguments changed")

    old_p1_parsed = parse_shoot_p1(old, OLD_SOURCES["p1"])
    old_p1_oracle = verify_commercial_p1(old_p1_parsed, gba, GBA_SOURCES["p1"])
    if not old_p1_oracle["payloads_exact"] or not old_p1_oracle["a_records_exact"]:
        raise SystemExit("Shoot-lineage P1 conversion no longer matches commercial GBA")

    old_p0, old_p0_info = build_asset(
        old,
        wsc_header=OLD_SOURCES["p0"],
        target_header=GBA_SOURCES["p0"],
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    old_p2 = convert_block(old[OLD_SOURCES["p2"]:OLD_SOURCES["p2"] + 38])
    old_p0_oracle = comparison(
        old_p0,
        gba[GBA_SOURCES["p0"]:GBA_SOURCES["p0"] + len(old_p0)],
    )
    if (
        old_p0_oracle["bytes"] != 792
        or old_p0_oracle["exact_prefix_bytes"] != 784
        or old_p0_oracle["mismatch_bytes"] != 5
    ):
        raise SystemExit("Shoot-lineage P0 commercial boundary changed")
    old_p0_oracle["logical_content_bytes"] = 784
    old_p0_oracle["tail_classification"] = (
        "converter alignment padding overlaps the following commercial structure"
    )
    old_p2_oracle = comparison(
        old_p2,
        gba[GBA_SOURCES["p2"]:GBA_SOURCES["p2"] + len(old_p2)],
    )
    if not old_p2_oracle["exact"]:
        raise SystemExit("Shoot-lineage P2 conversion no longer matches commercial GBA")

    new_p1_parsed = parse_shoot_p1(new, NEW_SOURCES["p1"])
    new_p1, new_p1_info = convert_shoot_p1(new_p1_parsed, ANALYSIS_TARGETS["p1"])
    new_p0, new_p0_info = build_asset(
        new,
        wsc_header=NEW_SOURCES["p0"],
        target_header=ANALYSIS_TARGETS["p0"],
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    new_p2 = convert_block(new[NEW_SOURCES["p2"]:NEW_SOURCES["p2"] + 38])

    result = {
        "schema": 1,
        "kind": "digimon-shoot-spawn-resource-conversion-boundary",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "lineage": [
            {
                "kind": kind,
                "wsc10_physical": OLD_SOURCES[kind],
                "wsc15_physical": NEW_SOURCES[kind],
                "commercial_gba": GBA_BASE + GBA_SOURCES[kind],
            }
            for kind in ("p1", "p0", "p2")
        ],
        "commercial_oracle": {
            "p1_shoot_variant": old_p1_oracle,
            "p0_relocatable": old_p0_oracle,
            "p2_palette": old_p2_oracle,
            "p0_conversion": old_p0_info,
        },
        "wsc15_conversion": {
            "p1": {
                "target": ANALYSIS_TARGETS["p1"],
                "converted": True,
                "bytes": len(new_p1),
                "sha256": sha256(new_p1),
                "source_header": {
                    key: value for key, value in new_p1_parsed.items()
                    if key not in ("payloads", "a_records")
                },
                "details": new_p1_info,
            },
            "p0": {
                "target": ANALYSIS_TARGETS["p0"],
                "bytes": len(new_p0),
                "sha256": sha256(new_p0),
                "details": new_p0_info,
            },
            "p2": {
                "target": ANALYSIS_TARGETS["p2"],
                "bytes": len(new_p2),
                "sha256": sha256(new_p2),
            },
        },
        "claim_scope": (
            "source-resolved resource formats and deterministic conversion only; "
            "commercial mismatches remain explicit and no GBA rule callback is installed"
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
