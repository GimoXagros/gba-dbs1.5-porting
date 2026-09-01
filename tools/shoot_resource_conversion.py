#!/usr/bin/env python3
"""Shared, source-bound conversion helpers for Digimon Shoot spawn assets."""

from __future__ import annotations

import hashlib
import struct


GBA_BASE = 0x08000000
OLD_SOURCES = {"p1": 0x2AE180, "p0": 0x2AD910, "p2": 0x2B5C00}
NEW_SOURCES = {"p1": 0x3D1E30, "p0": 0x22FF80, "p2": 0x3D7AF0}
GBA_SOURCES = {"p1": 0x350248, "p0": 0x3505E8, "p2": 0x352240}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def comparison(actual: bytes, expected: bytes) -> dict[str, int | str | bool | None]:
    if len(actual) != len(expected):
        raise ValueError("comparison lengths differ")
    mismatch_offsets = [
        offset
        for offset, (left, right) in enumerate(zip(actual, expected, strict=True))
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
    if len(item) != 12:
        raise ValueError("Shoot payload item must be 12 bytes")
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


def verify_commercial_p1(
    parsed: dict[str, object], gba: bytes, source: int
) -> dict[str, object]:
    table_pointer, reserved = struct.unpack_from("<2I", gba, source)
    if reserved != 0 or table_pointer != GBA_BASE + source + 8:
        raise SystemExit("commercial GBA Shoot-lineage P1 header changed")
    first_payload = struct.unpack_from("<I", gba, source + 12)[0]
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


def convert_shoot_p1(
    parsed: dict[str, object], target: int
) -> tuple[bytes, dict[str, object]]:
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
            "<4I",
            output,
            8 + index * 16,
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
