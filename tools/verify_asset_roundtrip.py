#!/usr/bin/env python3
"""Rebuild one known common WSC asset and require exact GBA byte identity."""

from __future__ import annotations

import argparse
import pathlib

from build_full_asset_poc import GBA_SHA256, WSC_SHA256, build_asset, sha256


WSC_HEADER = 0x34B410
GBA_HEADER = 0x2DA800


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if sha256(gba) != GBA_SHA256 or sha256(wsc) != WSC_SHA256:
        raise SystemExit("input hash mismatch")

    rebuilt, manifest = build_asset(
        wsc,
        wsc_header=WSC_HEADER,
        target_header=GBA_HEADER,
        expected_layout_entries=77,
        expected_layout_record_bytes=10624,
        expected_descriptor_entries=101,
        expected_tile_bytes=112096,
    )
    original = gba[GBA_HEADER:GBA_HEADER + len(rebuilt)]
    if rebuilt != original:
        first = next(index for index, pair in enumerate(zip(rebuilt, original)) if pair[0] != pair[1])
        raise SystemExit(f"roundtrip mismatch at GBA 0x{GBA_HEADER + first:X}")
    print(
        "exact asset roundtrip passed: "
        f"0x{GBA_HEADER:X}-0x{GBA_HEADER + len(rebuilt):X}, "
        f"{len(rebuilt)} bytes, sha256={sha256(rebuilt)}"
    )
    print(f"layout_entries={manifest['layout_entries']} descriptor_entries={manifest['descriptor_entries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
