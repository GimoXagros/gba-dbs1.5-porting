#!/usr/bin/env python3
"""Build the source-bound GBA resources used by the Ver. 1.5 Shoot child."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_full_asset_poc import build_asset  # type: ignore
from convert_wsc_palette_block import convert_block  # type: ignore
from shoot_resource_conversion import (  # type: ignore
    GBA_SOURCES,
    NEW_SOURCES,
    OLD_SOURCES,
    comparison,
    convert_shoot_p1,
    parse_shoot_p1,
    sha256,
    verify_commercial_p1,
)


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
TARGETS = {"p1": 0x5B9000, "p0": 0x5B9200, "p2": 0x5B9300}
OUTPUT_NAMES = {
    "p1": "shoot-spawn-p1.bin",
    "p0": "shoot-spawn-p0.bin",
    "p2": "shoot-spawn-p2.bin",
}


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"refusing unknown {label}: {actual}")


def verify_call_sites(old: bytes, new: bytes) -> None:
    old_overlay = old[0x390900:0x3A0900]
    new_overlay = new[0x740900:0x750900]
    if old_overlay[0x5B17:0x5B46] != bytes.fromhex(
        "6A 00 68 99 00 68 00 18 68 00 40 68 EB 00 68 C0 25 68 00 00 "
        "68 EA 00 68 91 2D 68 00 00 68 EA 00 68 18 2E 68 00 00 68 00 0C "
        "57 9A 14 24 B2 96"
    ):
        raise SystemExit("WSC 1.0 helper resource arguments changed")
    if new_overlay[0x92A4:0x92D3] != bytes.fromhex(
        "6A 01 68 D1 01 68 00 18 68 00 40 68 BD 00 68 AF 27 68 00 00 "
        "68 A2 00 68 F8 2F 68 00 00 68 BD 00 68 E3 21 68 00 00 68 00 0C "
        "57 9A F4 23 FF 4F"
    ):
        raise SystemExit("WSC 1.5 helper resource arguments changed")


def verify_commercial_oracle(gba: bytes, old: bytes) -> dict[str, object]:
    parsed = parse_shoot_p1(old, OLD_SOURCES["p1"])
    p1 = verify_commercial_p1(parsed, gba, GBA_SOURCES["p1"])
    if not p1["payloads_exact"] or not p1["a_records_exact"]:
        raise SystemExit("Shoot P1 converter no longer matches the commercial GBA")

    old_p0, _ = build_asset(
        old,
        wsc_header=OLD_SOURCES["p0"],
        target_header=GBA_SOURCES["p0"],
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    p0 = comparison(
        old_p0,
        gba[GBA_SOURCES["p0"]:GBA_SOURCES["p0"] + len(old_p0)],
    )
    if p0["bytes"] != 792 or p0["exact_prefix_bytes"] != 784 or p0["mismatch_bytes"] != 5:
        raise SystemExit("Shoot P0 commercial oracle boundary changed")

    old_p2 = convert_block(old[OLD_SOURCES["p2"]:OLD_SOURCES["p2"] + 38])
    p2 = comparison(
        old_p2,
        gba[GBA_SOURCES["p2"]:GBA_SOURCES["p2"] + len(old_p2)],
    )
    if not p2["exact"]:
        raise SystemExit("Shoot P2 converter no longer matches the commercial GBA")
    return {
        "p1_payload_items": p1["payload_item_count"],
        "p1_payloads_exact": p1["payloads_exact"],
        "p1_a_records_exact": p1["a_records_exact"],
        "p0_bytes": p0["bytes"],
        "p0_exact_prefix_bytes": p0["exact_prefix_bytes"],
        "p0_mismatch_bytes": p0["mismatch_bytes"],
        "p2_exact": p2["exact"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    old = args.wsc10.read_bytes()
    new = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(old, WSC10_SHA256, "WSC 1.0 source")
    require_hash(new, WSC15_SHA256, "WSC 1.5 source")
    verify_call_sites(old, new)
    oracle = verify_commercial_oracle(gba, old)

    parsed = parse_shoot_p1(new, NEW_SOURCES["p1"])
    p1, p1_info = convert_shoot_p1(parsed, TARGETS["p1"])
    p0, p0_info = build_asset(
        new,
        wsc_header=NEW_SOURCES["p0"],
        target_header=TARGETS["p0"],
        expected_layout_entries=2,
        expected_layout_record_bytes=80,
        expected_descriptor_entries=0,
        expected_tile_bytes=0,
    )
    p2 = convert_block(new[NEW_SOURCES["p2"]:NEW_SOURCES["p2"] + 38])
    assets = {"p1": p1, "p0": p0, "p2": p2}
    expected_sizes = {"p1": 384, "p0": 128, "p2": 40}
    if {kind: len(blob) for kind, blob in assets.items()} != expected_sizes:
        raise SystemExit("Shoot resource output sizes changed")
    if (
        p1_info["command_count"] != 3
        or p1_info["payload_item_count"] != 20
        or p1_info["a_record_count"] != 1
    ):
        raise SystemExit("Shoot P1 source population changed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_assets = {}
    for kind, blob in assets.items():
        path = args.output_dir / OUTPUT_NAMES[kind]
        path.write_bytes(blob)
        manifest_assets[kind] = {
            "file": OUTPUT_NAMES[kind],
            "target": TARGETS[kind],
            "bytes": len(blob),
            "sha256": sha256(blob),
            "wsc15_source": NEW_SOURCES[kind],
        }
    manifest = {
        "schema": 1,
        "kind": "digimon-shoot-rule-resource-build",
        "claim_scope": (
            "source-resolved P1/P0/P2 conversion and fixed expansion placement only; "
            "callback connectivity, runtime consumption, and final QA excluded"
        ),
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "commercial_oracle": oracle,
        "p1_population": {
            "commands": p1_info["command_count"],
            "payload_items": p1_info["payload_item_count"],
            "a_records": p1_info["a_record_count"],
        },
        "p0_population": {
            "layouts": p0_info["layout_entries"],
            "layout_record_bytes": p0_info["layout_record_bytes"],
            "descriptors": p0_info["descriptor_entries"],
            "tile_bytes": p0_info["tile_payload_bytes"],
        },
        "assets": manifest_assets,
    }
    (args.output_dir / "shoot-rule-resources.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[shoot-resources] PASS {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
