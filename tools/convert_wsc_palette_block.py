#!/usr/bin/env python3
"""Convert one confirmed 38-byte WSC palette block to the 40-byte GBA form."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


WSC_BYTES = 38
GBA_BYTES = 40


def parse_int(value: str) -> int:
    return int(value, 0)


def expand_channel(value: int) -> int:
    if not 0 <= value <= 0xF:
        raise ValueError("channel is outside BGR444")
    return (value << 1) | int(value != 0)


def convert_color(value: int) -> int:
    if value & 0xF000:
        raise ValueError(f"WSC color 0x{value:04X} is outside BGR444")
    blue = expand_channel(value & 0xF)
    green = expand_channel((value >> 4) & 0xF)
    red = expand_channel((value >> 8) & 0xF)
    return red | (green << 5) | (blue << 10)


def convert_block(source: bytes) -> bytes:
    if len(source) != WSC_BYTES:
        raise ValueError(f"palette block must be exactly {WSC_BYTES} bytes")
    header = source[:6]
    colors = struct.unpack_from("<16H", source, 6)
    converted = bytearray(header)
    converted.extend(struct.pack("<16H", *(convert_color(value) for value in colors)))
    converted.extend(bytes(2))
    if len(converted) != GBA_BYTES:
        raise AssertionError("palette conversion size invariant failed")
    return bytes(converted)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    data = args.wsc.read_bytes()
    if not 0 <= args.offset <= len(data) - WSC_BYTES:
        raise SystemExit("palette block falls outside input")
    source = data[args.offset:args.offset + WSC_BYTES]
    converted = convert_block(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(converted)
    manifest = {
        "schema": 1,
        "source_sha256": hashlib.sha256(data).hexdigest().upper(),
        "source_offset": args.offset,
        "source_bytes": len(source),
        "output_bytes": len(converted),
        "output_sha256": hashlib.sha256(converted).hexdigest().upper(),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
