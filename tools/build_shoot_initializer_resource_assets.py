#!/usr/bin/env python3
"""Build the remaining native P0/P2 resources for Shoot initializer 7168."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_full_asset_poc import build_asset  # type: ignore
from convert_wsc_palette_block import convert_block  # type: ignore


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"

P0_SPECS = (
    ("shoot-init-active-p0.bin", 0x3D5F80, 0x5D1000, 128, 4, 64, 0, 0),
    ("shoot-init-rules-p0.bin", 0x3914E0, 0x5D1100, 41408, 50, 4872, 61, 35616),
    ("shoot-init-extra-6d-p0.bin", 0x3D44E0, 0x5DB300, 224, 8, 136, 0, 0),
    ("shoot-init-extra-137-p0.bin", 0x3D0CA0, 0x5DB400, 448, 18, 288, 0, 0),
    ("shoot-init-extra-91-p0.bin", 0x3D7D30, 0x5DB600, 64, 4, 16, 0, 0),
)
P2_SPECS = (
    ("shoot-init-rules-p2.bin", 0x3D7640, 0x5DB700),
    ("shoot-init-extra-slot5-p2.bin", 0x3D7A90, 0x5DB740),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc15.read_bytes()
    if sha256(gba) != GBA_SHA256:
        raise SystemExit("refusing unknown USA GBA source")
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    assets = []
    for name, source, target, size, layouts, layout_bytes, descriptors, tile_bytes in P0_SPECS:
        blob, details = build_asset(
            wsc,
            wsc_header=source,
            target_header=target,
            expected_layout_entries=layouts,
            expected_layout_record_bytes=layout_bytes,
            expected_descriptor_entries=descriptors,
            expected_tile_bytes=tile_bytes,
        )
        if len(blob) != size:
            raise SystemExit(f"P0 output size changed for {name}")
        (args.output_dir / name).write_bytes(blob)
        assets.append({
            "kind": "p0",
            "file": name,
            "wsc15_source": source,
            "target": target,
            "bytes": len(blob),
            "sha256": sha256(blob),
            "layout_entries": details["layout_entries"],
            "layout_record_bytes": details["layout_record_bytes"],
            "descriptor_entries": details["descriptor_entries"],
            "tile_payload_bytes": details["tile_payload_bytes"],
        })

    for name, source, target in P2_SPECS:
        blob = convert_block(wsc[source:source + 38])
        if len(blob) != 40:
            raise SystemExit(f"P2 output size changed for {name}")
        (args.output_dir / name).write_bytes(blob)
        assets.append({
            "kind": "p2",
            "file": name,
            "wsc15_source": source,
            "target": target,
            "bytes": len(blob),
            "sha256": sha256(blob),
        })

    reused_spawn_p2 = convert_block(wsc[0x3D4B20:0x3D4B20 + 38])
    if reused_spawn_p2 != convert_block(wsc[0x3D7AF0:0x3D7AF0 + 38]):
        raise SystemExit("initializer active P2 no longer matches Shoot spawn P2")
    commercial_p2 = convert_block(wsc[0x3D6B16:0x3D6B16 + 38])
    if gba[0x0D3078:0x0D3078 + 40] != commercial_p2:
        raise SystemExit("initializer offset-26 P2 no longer matches commercial GBA data")

    manifest = {
        "schema": 1,
        "kind": "digimon-shoot-initializer-p0-p2-assets",
        "sources": {"gba_sha256": GBA_SHA256, "wsc15_sha256": WSC15_SHA256},
        "assets": assets,
        "reused": [
            {
                "kind": "p2",
                "wsc15_source": 0x3D4B20,
                "target": 0x5B9300,
                "basis": "byte-identical to already installed Shoot spawn P2 source 0x3D7AF0",
                "sha256": sha256(reused_spawn_p2),
            },
            {
                "kind": "p2",
                "wsc15_source": 0x3D6B16,
                "target": 0x0D3078,
                "basis": "byte-identical commercial USA GBA occurrence",
                "sha256": sha256(commercial_p2),
            },
        ],
        "planned_ownership": [0x5D0000, 0x5DB768],
        "claim_scope": (
            "deterministic P0/P2 conversion and fixed placement mapping only; P1 is built separately, "
            "and no ROM writes, initializer/menu connection, runtime, or supplied-save QA are performed"
        ),
    }
    (args.output_dir / "shoot-initializer-resources.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[shoot-initializer-resources] PASS {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
