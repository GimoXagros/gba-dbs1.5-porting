#!/usr/bin/env python3
"""Analyze WSC animation-layout headers and locate raw layout payloads in GBA."""

from __future__ import annotations

import argparse
import json
import hashlib
import pathlib
import struct


HEADER_TAIL = bytes.fromhex("05 00 24 00 80 04 0A 00")
GBA_BASE = 0x08000000


def all_offsets(haystack: bytes, needle: bytes, limit: int = 32) -> list[int]:
    result: list[int] = []
    start = 0
    while len(result) < limit:
        offset = haystack.find(needle, start)
        if offset < 0:
            break
        result.append(offset)
        start = offset + 1
    return result


def wsc_descriptor(rom: bytes, offset: int) -> dict[str, int] | None:
    if offset < 0 or offset + 8 > len(rom):
        return None
    length, bank_offset, destination, bank = struct.unpack_from("<4H", rom, offset)
    if not (0x20 <= length <= 0x2000 and length % 0x20 == 0):
        return None
    if destination != 0x2000 or not (0x80 <= bank <= 0xFF):
        return None
    physical = ((bank & 0x7F) << 16) | bank_offset
    if physical + length > len(rom) or bank_offset + length > 0x10000:
        return None
    return {"length": length, "physical": physical, "bank_offset": bank_offset, "bank": bank}


def summarize_blocks(entries: list[dict[str, int]], location_key: str) -> list[dict[str, int]]:
    blocks: list[dict[str, int]] = []
    block_start = 0
    for index in range(1, len(entries) + 1):
        at_end = index == len(entries)
        if at_end or entries[index][location_key] != entries[index - 1][location_key] + entries[index - 1]["length"]:
            group = entries[block_start:index]
            blocks.append({
                "entry_start": block_start,
                "entry_end": index,
                "payload_start": group[0][location_key],
                "payload_end": group[-1][location_key] + group[-1]["length"],
                "bytes": sum(entry["length"] for entry in group),
            })
            block_start = index
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    headers: list[dict[str, object]] = []
    tail_start = 0
    while True:
        tail_offset = wsc.find(HEADER_TAIL, tail_start)
        if tail_offset < 0:
            break
        header = tail_offset - 8
        table_relative, secondary = struct.unpack_from("<II", wsc, header)
        bank = (secondary >> 16) & 0xFF
        segment = secondary & 0xFFFF
        decoded_secondary = ((bank & 0x7F) << 16) | ((segment << 4) & 0xFFFF)
        table = header + table_relative
        first_count, first_record_relative = struct.unpack_from("<HH", wsc, table)
        valid = table_relative >= 0x10 and first_record_relative > table_relative
        valid = valid and (first_record_relative - table_relative) % 4 == 0
        entry_count = (first_record_relative - table_relative) // 4 if valid else 0
        counts: list[int] = []
        relatives: list[int] = []
        if valid and table + entry_count * 4 <= len(wsc):
            for index in range(entry_count):
                count, relative = struct.unpack_from("<HH", wsc, table + index * 4)
                counts.append(count)
                relatives.append(relative)
            expected = first_record_relative
            for count, relative in zip(counts, relatives):
                if count == 0 or relative != expected:
                    valid = False
                    break
                expected += count * 4
        record_start = header + first_record_relative if valid else None
        record_end = header + expected if valid else None
        payload = wsc[record_start:record_end] if valid else b""
        headers.append({
            "header_offset": header,
            "secondary_value": secondary,
            "decoded_secondary_offset": decoded_secondary,
            "valid_layout_table": valid,
            "entry_count": entry_count,
            "record_start": record_start,
            "record_end": record_end,
            "record_bytes": len(payload),
            "record_count": sum(counts) if valid else None,
            "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
            "gba_exact_payload_offsets": all_offsets(gba, payload) if payload else [],
        })
        tail_start = tail_offset + 1

    decoded_starts = {int(item["decoded_secondary_offset"]) for item in headers}
    for item in headers:
        start = int(item["decoded_secondary_offset"])
        entries: list[dict[str, int]] = []
        cursor = start
        while cursor + 8 <= len(wsc):
            if cursor != start and cursor in decoded_starts:
                break
            entry = wsc_descriptor(wsc, cursor)
            if entry is None:
                break
            if entries:
                previous = entries[-1]
                contiguous = entry["physical"] == previous["physical"] + previous["length"]
                new_block = entry["bank_offset"] == 0 and entry["bank"] != previous["bank"]
                if not (contiguous or new_block):
                    break
            entries.append(entry)
            cursor += 8
        lengths = b"".join(struct.pack("<I", entry["length"]) for entry in entries)
        item["descriptor_entry_count"] = len(entries)
        item["descriptor_bytes"] = len(entries) * 8
        item["descriptor_lengths_sha256"] = hashlib.sha256(lengths).hexdigest()
        item["tile_payload_bytes"] = sum(entry["length"] for entry in entries)
        item["tile_blocks"] = summarize_blocks(entries, "physical") if entries else []

    gba_headers: list[dict[str, object]] = []
    tail_start = 0
    while True:
        tail_offset = gba.find(HEADER_TAIL, tail_start)
        if tail_offset < 0:
            break
        header = tail_offset - 8
        table_pointer, descriptor_pointer = struct.unpack_from("<II", gba, header)
        table = table_pointer - GBA_BASE
        valid = 0 <= table <= len(gba) - 8
        entry_count = 0
        counts: list[int] = []
        pointers: list[int] = []
        if valid:
            first_count, first_pointer = struct.unpack_from("<II", gba, table)
            first_record = first_pointer - GBA_BASE
            valid = first_record > table and (first_record - table) % 8 == 0
            entry_count = (first_record - table) // 8 if valid else 0
        if valid and table + entry_count * 8 <= len(gba):
            for index in range(entry_count):
                count, pointer = struct.unpack_from("<II", gba, table + index * 8)
                counts.append(count)
                pointers.append(pointer - GBA_BASE)
            expected = pointers[0]
            for count, pointer in zip(counts, pointers):
                if count == 0 or pointer != expected:
                    valid = False
                    break
                expected += count * 4
        record_start = pointers[0] if valid else None
        record_end = expected if valid else None
        payload = gba[record_start:record_end] if valid else b""
        descriptor_table = descriptor_pointer - GBA_BASE
        descriptor_entries: list[dict[str, int]] = []
        if 0 <= descriptor_table <= len(gba) - 8:
            first_length, first_pointer = struct.unpack_from("<II", gba, descriptor_table)
            first_payload = first_pointer - GBA_BASE
            descriptor_count = ((first_payload - descriptor_table) // 8
                                if first_payload > descriptor_table and (first_payload - descriptor_table) % 8 == 0
                                else 0)
            expected_payload = first_payload
            for index in range(descriptor_count):
                length, pointer = struct.unpack_from("<II", gba, descriptor_table + index * 8)
                payload_offset = pointer - GBA_BASE
                if (length < 0x20 or length % 0x20 or payload_offset != expected_payload
                        or payload_offset + length > len(gba)):
                    descriptor_entries = []
                    break
                descriptor_entries.append({"length": length, "payload": payload_offset})
                expected_payload += length
        descriptor_lengths = b"".join(struct.pack("<I", entry["length"])
                                      for entry in descriptor_entries)
        gba_headers.append({
            "header_offset": header,
            "layout_table_offset": table if valid else None,
            "descriptor_table_offset": descriptor_pointer - GBA_BASE,
            "valid_layout_table": valid,
            "entry_count": entry_count,
            "record_start": record_start,
            "record_end": record_end,
            "record_bytes": len(payload),
            "record_count": sum(counts) if valid else None,
            "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
            "descriptor_entry_count": len(descriptor_entries),
            "descriptor_bytes": len(descriptor_entries) * 8,
            "descriptor_lengths_sha256": hashlib.sha256(descriptor_lengths).hexdigest(),
            "tile_payload_bytes": sum(entry["length"] for entry in descriptor_entries),
            "tile_blocks": summarize_blocks(descriptor_entries, "payload") if descriptor_entries else [],
        })
        tail_start = tail_offset + 1

    print(json.dumps({"wsc_headers": headers, "gba_headers": gba_headers}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
