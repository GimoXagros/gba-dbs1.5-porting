#!/usr/bin/env python3
"""Find aligned little-endian GBA ROM pointers into a target range."""

from __future__ import annotations

import argparse
import collections
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
    parser.add_argument("--alignment", type=parse_int, default=4)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    end = min(len(rom), args.scan_end if args.scan_end is not None else len(rom))
    refs: collections.defaultdict[int, list[int]] = collections.defaultdict(list)
    for source in range(args.scan_start, end - 3, args.alignment):
        value = struct.unpack_from("<I", rom, source)[0]
        target = value - 0x08000000
        if args.target_start <= target < args.target_end:
            refs[target].append(source)
    targets = [
        {"target": target, "sources": sources}
        for target, sources in sorted(refs.items())
    ]
    result = {
        "rom": str(args.rom),
        "scan_range": [args.scan_start, end],
        "target_range": [args.target_start, args.target_end],
        "alignment": args.alignment,
        "targets": targets,
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
