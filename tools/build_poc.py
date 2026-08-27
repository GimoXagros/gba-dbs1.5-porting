#!/usr/bin/env python3
"""Build the first reversible WSC-to-GBA graphics-path proof of concept.

The output ROM is a local, ignored test artifact.  This script refuses unknown
inputs, validates the exact bytes being replaced, and audits the final diff.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


GBA_SHA256 = "996de33330ac729d10d761d1901e7a335191c9503b0470569e8f294acf6618ed"
WSC_SHA256 = "c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7"

WSC_SOURCE_OFFSET = 0x000000
GBA_TARGET_OFFSET = 0x2DD720
FRAME_LENGTH = 0x460

EXPECTED_GBA_RANGE_SHA256 = (
    "73b0065b3897fce969f8c3acfd428f5706d8db6f7d860d38275cac717731e050"
)
EXPECTED_WSC_RANGE_SHA256 = (
    "17a839bf5bfd9b0cfc5f3be54933ecbff2751d8efa85e438c1f86464a47e7475"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def convert_planar_tile(tile: bytes) -> bytes:
    """Convert one WSC 4bpp planar 8x8 tile to GBA packed 4bpp."""
    if len(tile) != 32:
        raise ValueError("a 4bpp tile must be exactly 32 bytes")
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(
                sum(((planes[plane] & mask) != 0) << plane for plane in range(4))
            )
    return bytes(
        pixels[index] | (pixels[index + 1] << 4)
        for index in range(0, len(pixels), 2)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path, help="exact USA retail GBA ROM")
    parser.add_argument("wsc", type=pathlib.Path, help="exact Japanese 1.5 WSC ROM")
    parser.add_argument("output", type=pathlib.Path, help="local test ROM path")
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if sha256(gba) != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if sha256(wsc) != WSC_SHA256:
        raise SystemExit("refusing unknown WSC input")

    old = gba[GBA_TARGET_OFFSET:GBA_TARGET_OFFSET + FRAME_LENGTH]
    source = wsc[WSC_SOURCE_OFFSET:WSC_SOURCE_OFFSET + FRAME_LENGTH]
    if sha256(old) != EXPECTED_GBA_RANGE_SHA256:
        raise SystemExit("GBA expected-write check failed")
    if sha256(source) != EXPECTED_WSC_RANGE_SHA256:
        raise SystemExit("WSC source-range check failed")
    if FRAME_LENGTH % 32:
        raise SystemExit("frame length is not tile aligned")

    converted = b"".join(
        convert_planar_tile(source[pos:pos + 32])
        for pos in range(0, len(source), 32)
    )
    if len(converted) != FRAME_LENGTH:
        raise SystemExit("converted frame length changed")

    patched = bytearray(gba)
    patched[GBA_TARGET_OFFSET:GBA_TARGET_OFFSET + FRAME_LENGTH] = converted
    differing = [index for index, pair in enumerate(zip(gba, patched)) if pair[0] != pair[1]]
    if not differing:
        raise SystemExit("test write made no change")
    if min(differing) < GBA_TARGET_OFFSET:
        raise SystemExit("unexpected diff before target range")
    if max(differing) >= GBA_TARGET_OFFSET + FRAME_LENGTH:
        raise SystemExit("unexpected diff after target range")
    if len(patched) != len(gba):
        raise SystemExit("ROM size changed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    manifest = {
        "kind": "graphics-path-poc",
        "base_sha256": GBA_SHA256,
        "reference_sha256": WSC_SHA256,
        "output_sha256": sha256(patched),
        "write": {
            "wsc_offset": WSC_SOURCE_OFFSET,
            "gba_offset": GBA_TARGET_OFFSET,
            "length": FRAME_LENGTH,
            "old_sha256": sha256(old),
            "source_sha256": sha256(source),
            "new_sha256": sha256(converted),
            "actual_changed_bytes": len(differing),
            "first_changed_offset": min(differing),
            "last_changed_offset": max(differing),
        },
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
