#!/usr/bin/env python3
"""Find structurally valid WonderSwan animation-container headers."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_full_asset_poc import parse_wsc_descriptor


def parse_int(value: str) -> int:
    return int(value, 0)


def candidate(rom: bytes, header: int) -> dict[str, int] | None:
    if header + 0x14 > len(rom):
        return None
    table_relative, secondary, constants_a, constants_b = struct.unpack_from("<4I", rom, header)
    if table_relative != 0x10:
        return None
    first_count, first_record_relative = struct.unpack_from("<HH", rom, header + 0x10)
    if not first_count or first_record_relative <= 0x10 or (first_record_relative - 0x10) % 4:
        return None
    layout_entries = (first_record_relative - 0x10) // 4
    if not 1 <= layout_entries <= 256:
        return None
    cursor = first_record_relative
    record_total = 0
    for index in range(layout_entries):
        count, relative = struct.unpack_from("<HH", rom, header + 0x10 + index * 4)
        if not count or count > 0x1000 or relative != cursor:
            return None
        size = count * 4
        cursor += size
        record_total += size
        if header + cursor > len(rom):
            return None
    bank = (secondary >> 16) & 0xFF
    segment = secondary & 0xFFFF
    descriptor_start = ((bank & 0x7F) << 16) | ((segment << 4) & 0xFFFF)
    descriptors = []
    at = descriptor_start
    while True:
        parsed = parse_wsc_descriptor(rom, at)
        if parsed is None:
            break
        if descriptors:
            previous_length, previous_physical = descriptors[-1]
            length, physical = parsed
            if not (physical == previous_physical + previous_length
                    or ((physical & 0xFFFF) == 0 and (physical >> 16) != (previous_physical >> 16))):
                break
        descriptors.append(parsed)
        at += 8
    if not descriptors:
        return None
    return {
        "header": header,
        "layout_entries": layout_entries,
        "layout_record_bytes": record_total,
        "descriptor_start": descriptor_start,
        "descriptor_entries": len(descriptors),
        "tile_payload_bytes": sum(length for length, _ in descriptors),
        "tile_physical_start": descriptors[0][1],
        "tile_physical_end": descriptors[-1][1] + descriptors[-1][0],
        "constants_a": constants_a,
        "constants_b": constants_b,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--alignment", type=parse_int, default=2)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    rom = args.wsc.read_bytes()
    end = len(rom) if args.scan_end is None else min(args.scan_end, len(rom))
    rows = []
    for header in range(args.scan_start, end - 0x14, args.alignment):
        if rom[header:header + 4] != b"\x10\x00\x00\x00":
            continue
        parsed = candidate(rom, header)
        if parsed:
            rows.append(parsed)
    result = {"schema": 1, "scan_range": [args.scan_start, end], "candidates": rows}
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
