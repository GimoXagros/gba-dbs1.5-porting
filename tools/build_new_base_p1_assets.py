#!/usr/bin/env python3
"""Build relocatable GBA P1 command containers from WSC Ver. 1.5 data."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC_TABLE = 0x740000
RECORD_BYTES = 0x20
WSC_PAYLOAD_BYTES = 0x0C
GBA_PAYLOAD_BYTES = 0x10
A_RECORD_BYTES = 8
B_RECORD_BYTES = 10


def parse_int(value: str) -> int:
    return int(value, 0)


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def convert_payload_item(item: bytes) -> bytes:
    """Convert the one platform-scaled P1 word and add the GBA tail."""
    words = list(struct.unpack("<6H", item))
    value = words[0]
    if value & 0xFF00 == 0xFF00:
        distance = value & 0xFF
        words[0] = 0xFF00 | ((distance * 4 + 2) // 5)
    return struct.pack("<8H", *words, 0, 0)


def convert_a_table(table: bytes) -> bytes:
    output = bytearray(table)
    for offset in range(0, len(output), A_RECORD_BYTES):
        first_word = struct.unpack_from("<H", output, offset)[0]
        trailing_flags = struct.unpack_from("<I", output, offset + 4)[0]
        if first_word == 0xFFFF or trailing_flags > 0xFFFF:
            break
        for field in (0, 1):
            value = output[offset + field]
            if value == 8 or value > 10:
                output[offset + field] = (value * 4 + 2) // 5
    return bytes(output)


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def checked_slice(data: bytes, start: int, size: int, label: str) -> bytes:
    if start < 0 or size < 0 or start + size > len(data):
        raise ValueError(f"{label} range 0x{start:X}+0x{size:X} is outside source")
    return data[start:start + size]


def parse_source(data: bytes, source: int) -> dict[str, object]:
    table_relative, reserved, command_count, leading_payload_relative = struct.unpack_from(
        "<4H", data, source
    )
    if table_relative != 4 or reserved != 0 or command_count == 0:
        raise ValueError(f"unexpected WSC P1 header at 0x{source:X}")

    commands: list[dict[str, int]] = []
    for index in range(command_count):
        entry = source + 8 + index * 8
        a_relative, b_relative, count, payload_relative = struct.unpack_from(
            "<4H", data, entry
        )
        if count == 0:
            raise ValueError(f"WSC P1 command {index} has no payload items")
        commands.append({
            "a_relative": a_relative,
            "b_relative": b_relative,
            "count": count,
            "payload_relative": payload_relative,
        })

    first_payload_relative = commands[0]["payload_relative"]
    leading_bytes = first_payload_relative - leading_payload_relative
    if leading_bytes <= 0 or leading_bytes % WSC_PAYLOAD_BYTES:
        raise ValueError("cannot derive WSC leading-command payload count")
    logical_commands = [{
        "a_relative": commands[0]["a_relative"],
        "b_relative": commands[0]["b_relative"] - B_RECORD_BYTES,
        "count": leading_bytes // WSC_PAYLOAD_BYTES,
        "payload_relative": leading_payload_relative,
        "source_kind": "header-leading-command",
    }]
    if logical_commands[0]["b_relative"] < 0:
        raise ValueError("leading-command B record underflows source container")
    for command in commands:
        logical_commands.append({**command, "source_kind": "table-command"})

    payloads: list[list[bytes]] = []
    for index, command in enumerate(logical_commands):
        payload = source + int(command["payload_relative"])
        count = int(command["count"])
        items = [checked_slice(
            data, payload + item * WSC_PAYLOAD_BYTES, WSC_PAYLOAD_BYTES,
            f"P1 command {index} payload item {item}"
        ) for item in range(count)]
        payloads.append(items)
    a_lengths: dict[int, int] = {}
    for command, items in zip(logical_commands, payloads):
        max_index = max(struct.unpack_from("<H", item, 2)[0] for item in items)
        if max_index >= 0x1000:
            raise ValueError(f"P1 command has implausible A index 0x{max_index:X}")
        relative = int(command["a_relative"])
        a_lengths[relative] = max(a_lengths.get(relative, 0), max_index + 1)
    a_tables = {
        relative: checked_slice(
            data, source + relative, count * A_RECORD_BYTES,
            f"P1 A table 0x{relative:X}",
        )
        for relative, count in a_lengths.items()
    }
    b_records = {
        int(command["b_relative"]): checked_slice(
            data, source + int(command["b_relative"]), B_RECORD_BYTES,
            f"P1 B record 0x{int(command['b_relative']):X}"
        )
        for command in logical_commands
    }
    return {
        "source": source,
        "commands": logical_commands,
        "payloads": payloads,
        "a_tables": a_tables,
        "a_lengths": a_lengths,
        "b_records": b_records,
    }


def read_template_entries(gba: bytes, p1_pointer_field: int) -> list[tuple[int, int, int, int]]:
    p1 = struct.unpack_from("<I", gba, p1_pointer_field)[0]
    if not GBA_BASE <= p1 < GBA_BASE + len(gba):
        raise ValueError(f"invalid native P1 template pointer 0x{p1:08X}")
    table = struct.unpack_from("<I", gba, p1 - GBA_BASE)[0]
    if not GBA_BASE <= table <= GBA_BASE + len(gba) - 16:
        raise ValueError(f"invalid native P1 template table 0x{table:08X}")
    first_payload = struct.unpack_from("<I", gba, table - GBA_BASE + 4)[0]
    if not GBA_BASE <= first_payload <= GBA_BASE + len(gba):
        raise ValueError(f"invalid native P1 template payload 0x{first_payload:08X}")
    command_count = (first_payload - table) // 16
    if not 1 <= command_count <= 0x200 or table + command_count * 16 != first_payload:
        raise ValueError(f"cannot derive native P1 template count at 0x{table:08X}")
    return [
        struct.unpack_from("<4I", gba, table - GBA_BASE + index * 16)
        for index in range(command_count)
    ]


def convert_source(parsed: dict[str, object], target: int,
                   template_entries: list[tuple[int, int, int, int]] | None = None
                   ) -> tuple[bytes, dict[str, object]]:
    commands = parsed["commands"]
    payloads = parsed["payloads"]
    a_tables = parsed["a_tables"]
    b_records = parsed["b_records"]
    command_count = len(commands)
    # Retail GBA command i uses the following WSC B record. The final GBA-only
    # command has no WSC counterpart; repeating the last valid B record is a
    # conservative, pointer-safe fallback for Ver. 1.5-only characters.
    gba_b_relatives = [
        int(commands[min(index + 1, command_count - 1)]["b_relative"])
        for index in range(command_count)
    ]

    gba_command_count = max(command_count, len(template_entries or []))
    cursor = 8 + gba_command_count * 16
    cursor = align(cursor, 4)
    payload_targets: list[int] = []
    for items in payloads:
        payload_targets.append(target + cursor)
        cursor += len(items) * GBA_PAYLOAD_BYTES
    cursor = align(cursor, 4)

    a_targets: dict[int, int] = {}
    b_targets: dict[int, int] = {}
    if template_entries is None:
        for relative in sorted(a_tables):
            a_targets[relative] = target + cursor
            cursor += len(a_tables[relative])
        cursor = align(cursor, 2)
        for relative in sorted(set(gba_b_relatives)):
            b_targets[relative] = target + cursor
            cursor += len(b_records[relative])
    cursor = align(cursor, 4)

    output = bytearray(cursor)
    struct.pack_into("<2I", output, 0, GBA_BASE + target + 8, 0)
    for index in range(gba_command_count):
        if index >= command_count:
            if template_entries is None:
                raise AssertionError("missing native entry for expanded P1 table")
            struct.pack_into("<4I", output, 8 + index * 16, *template_entries[index])
            continue
        command = commands[index]
        if template_entries is None:
            a_pointer = GBA_BASE + a_targets[int(command["a_relative"])]
            b_pointer = GBA_BASE + b_targets[gba_b_relatives[index]]
        else:
            _, _, a_pointer, b_pointer = template_entries[index % len(template_entries)]
        struct.pack_into(
            "<4I", output, 8 + index * 16,
            int(command["count"]),
            GBA_BASE + payload_targets[index],
            a_pointer,
            b_pointer,
        )
    for items, payload_target in zip(payloads, payload_targets):
        local = payload_target - target
        for index, item in enumerate(items):
            start = local + index * GBA_PAYLOAD_BYTES
            output[start:start + GBA_PAYLOAD_BYTES] = convert_payload_item(item)
    if template_entries is None:
        for relative, table in a_tables.items():
            local = a_targets[relative] - target
            converted_table = convert_a_table(table)
            output[local:local + len(converted_table)] = converted_table
        for relative in sorted(set(gba_b_relatives)):
            record = b_records[relative]
            local = b_targets[relative] - target
            output[local:local + len(record)] = record

    entry = {
        "source": parsed["source"],
        "target": target,
        "bytes": len(output),
        "logical_command_count": command_count,
        "table_command_count": command_count - 1,
        "payload_item_count": sum(len(items) for items in payloads),
        "a_table_count": len(a_tables),
        "a_record_count": sum(len(table) // A_RECORD_BYTES for table in a_tables.values()),
        "b_record_count": len(b_records),
        "gba_b_record_count": len(b_targets),
        "payload_word0_rule": "FFxx distance scaled 4/5 with nearest rounding",
        "a_table_rule": "stop at FFFF record; scale dimensions 8 or >10 by 4/5",
        "b_record_rule": "GBA command i uses next WSC B; final repeats last valid B",
        "gba_command_count": gba_command_count,
        "native_template_entry_count": len(template_entries or []),
        "sha256": hashlib.sha256(output).hexdigest().upper(),
    }
    return bytes(output), entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--gba", type=pathlib.Path, required=True)
    parser.add_argument("--target-base", type=parse_int, default=0x481000)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc15 = args.wsc15.read_bytes()
    digest = hashlib.sha256(wsc15).hexdigest().upper()
    if digest != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")
    gba = args.gba.read_bytes()
    if hashlib.sha256(gba).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA template input")
    template_entries = read_template_entries(
        gba, 0x0D3FA0 + 1 * RECORD_BYTES + 7 * 4
    )

    cursor = args.target_base
    blob = bytearray()
    entries = []
    for runtime_id in (12, 13, 14):
        cursor = align(cursor, 4)
        blob.extend(bytes(cursor - (args.target_base + len(blob))))
        record = WSC_TABLE + runtime_id * RECORD_BYTES
        source = wsc_pointer(wsc15, record + 6)
        converted, entry = convert_source(
            parse_source(wsc15, source), cursor, template_entries
        )
        blob.extend(converted)
        cursor += len(converted)
        entry["runtime_id"] = runtime_id
        entries.append(entry)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    manifest = {
        "schema": 1,
        "kind": "candidate-relocatable-gba-base-p1",
        "claim_scope": (
            "structural WSC-to-GBA command expansion with source frame indices and "
            "source timing/geometry values preserved; runtime gameplay not yet proven"
        ),
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
