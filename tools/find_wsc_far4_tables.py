#!/usr/bin/env python3
"""Find runs of four-byte WSC segment/bank pointers in a scan window."""

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
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--target-start", type=parse_int, default=0)
    parser.add_argument("--target-end", type=parse_int)
    parser.add_argument("--minimum-entries", type=int, default=6)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    bank_count = len(rom) >> 16
    scan_end = min(len(rom), args.scan_end if args.scan_end is not None else len(rom))
    target_end = min(len(rom), args.target_end if args.target_end is not None else len(rom))

    def decode(source: int) -> int | None:
        segment, bank = struct.unpack_from("<2H", rom, source)
        if not 0x2000 <= segment <= 0x2FFF or bank > 0xFF:
            return None
        target = ((bank & (bank_count - 1)) << 16) | ((segment - 0x2000) << 4)
        if not args.target_start <= target < target_end:
            return None
        if rom[target:target + 16] in (b"\0" * 16, b"\xFF" * 16):
            return None
        return target

    tables = []
    source = args.scan_start + (args.scan_start & 1)
    while source <= scan_end - 4:
        targets = []
        cursor = source
        while cursor <= scan_end - 4:
            target = decode(cursor)
            if target is None:
                break
            targets.append(target)
            cursor += 4
        if len(targets) >= args.minimum_entries:
            tables.append({"source": source, "entries": len(targets), "targets": targets})
            source = cursor
        else:
            source += 2
    result = {
        "rom": str(args.rom),
        "scan_range": [args.scan_start, scan_end],
        "target_range": [args.target_start, target_end],
        "minimum_entries": args.minimum_entries,
        "tables": tables,
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
