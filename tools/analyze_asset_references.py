#!/usr/bin/env python3
"""Enumerate exact references to confirmed animation asset headers.

This is deliberately a candidate generator.  It reports every byte-exact
reference encoding and local context; it does not claim that a match is a
runtime consumer until code or table structure confirms that interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
HEADER_TAIL = bytes.fromhex("05 00 24 00 80 04 0A 00")


def all_offsets(data: bytes, needle: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return result
        result.append(offset)
        start = offset + 1


def contexts(data: bytes, offsets: list[int], width: int, radius: int) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for offset in offsets:
        start = max(0, offset - radius)
        end = min(len(data), offset + width + radius)
        result.append({
            "offset": offset,
            "context_start": start,
            "context_hex": data[start:end].hex(" "),
        })
    return result


def find_headers(data: bytes) -> list[int]:
    result: list[int] = []
    start = 0
    while True:
        tail = data.find(HEADER_TAIL, start)
        if tail < 0:
            return result
        result.append(tail - 8)
        start = tail + 1


def wsc_encodings(physical: int) -> dict[str, bytes]:
    bank = 0x80 | (physical >> 16)
    bank_offset = physical & 0xFFFF
    if physical & 0xF:
        raise ValueError(f"WSC header 0x{physical:X} is not paragraph aligned")
    segment = bank_offset >> 4
    rom_window_segment = 0x2000 + segment
    return {
        "physical_u32": struct.pack("<I", physical),
        "bank_offset_bank_u16": struct.pack("<HH", bank_offset, bank),
        "segment_bank_u16": struct.pack("<HH", segment, bank),
        "rom_window_segment_bank_u16": struct.pack("<HH", rom_window_segment, bank),
        "packed_bank_segment_u32": struct.pack("<I", (bank << 16) | segment),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--context", type=int, default=24)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    gba_headers = find_headers(gba)
    wsc_headers = find_headers(wsc)

    gba_results: list[dict[str, object]] = []
    for header in gba_headers:
        encoded = struct.pack("<I", GBA_BASE + header)
        offsets = all_offsets(gba, encoded)
        gba_results.append({
            "header_offset": header,
            "encoded_pointer": (GBA_BASE + header),
            "reference_count": len(offsets),
            "references": contexts(gba, offsets, len(encoded), args.context),
        })

    wsc_results: list[dict[str, object]] = []
    for header in wsc_headers:
        matches: dict[str, object] = {}
        seen: set[tuple[int, bytes]] = set()
        for name, encoded in wsc_encodings(header).items():
            identity = (len(encoded), encoded)
            if identity in seen:
                continue
            seen.add(identity)
            offsets = all_offsets(wsc, encoded)
            matches[name] = {
                "encoded_hex": encoded.hex(" "),
                "reference_count": len(offsets),
                "references": contexts(wsc, offsets, len(encoded), args.context),
            }
        wsc_results.append({"header_offset": header, "encodings": matches})

    result = {
        "gba_sha256": hashlib.sha256(gba).hexdigest(),
        "wsc_sha256": hashlib.sha256(wsc).hexdigest(),
        "gba_headers": gba_results,
        "wsc_headers": wsc_results,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
