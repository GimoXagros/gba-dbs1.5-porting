#!/usr/bin/env python3
"""Find four-byte segment/bank WonderSwan far pointers into a ROM range."""

from __future__ import annotations

import argparse
import json
import pathlib
import struct


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("--target-start", type=parse_int, required=True)
    parser.add_argument("--target-end", type=parse_int, required=True)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--alignment", type=parse_int, default=2)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    bank_count = len(rom) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise ValueError("ROM size must be a power-of-two number of 64 KiB banks")
    end = min(len(rom), args.scan_end if args.scan_end is not None else len(rom))
    matches = []
    for source in range(args.scan_start, end - 3, args.alignment):
        segment, bank = struct.unpack_from("<2H", rom, source)
        if not 0x2000 <= segment <= 0x2FFF or bank > 0xFF:
            continue
        physical = ((bank & (bank_count - 1)) << 16) | ((segment - 0x2000) << 4)
        if args.target_start <= physical < args.target_end:
            matches.append({
                "source": source,
                "target": physical,
                "segment": segment,
                "bank": bank,
                "raw": rom[source:source + 4].hex(" "),
            })
    result = {
        "rom": str(args.rom),
        "scan_range": [args.scan_start, end],
        "target_range": [args.target_start, args.target_end],
        "matches": matches,
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
