#!/usr/bin/env python3
"""Convert one confirmed WSC animation container to a relocatable GBA blob."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

from build_full_asset_poc import build_asset


def parse_int(value: str) -> int:
    return int(value, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--header", type=parse_int, required=True)
    parser.add_argument("--target-header", type=parse_int, required=True)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    wsc = args.wsc.read_bytes()
    asset, manifest = build_asset(
        wsc,
        wsc_header=args.header,
        target_header=args.target_header,
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    manifest.update({
        "kind": "relocatable-gba-animation-asset",
        "source_wsc_sha256": hashlib.sha256(wsc).hexdigest(),
        "warning": "This blob is one resource only; supporting palette/command bundles and record wiring are not included.",
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(asset)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
