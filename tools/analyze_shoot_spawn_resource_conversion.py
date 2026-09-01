#!/usr/bin/env python3
"""Bound the resource conversion required by WSC 1.5 Shoot helper 9229.

The helper's three far resource arguments are resolved to P1, P0, and P2
containers.  Their WSC 1.0/commercial GBA ancestors are used as conversion
oracles before the same converters are applied to the Ver. 1.5 sources.  The
report deliberately separates exact byte equality from relocatable structural
conversion.
"""

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
    GBA_BASE,
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
ANALYSIS_TARGETS = {"p1": 0x5BA000, "p0": 0x5BB000, "p2": 0x5BF000}


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"refusing unknown {label}: {actual}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    old = args.wsc10.read_bytes()
    new = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(old, WSC10_SHA256, "WSC 1.0 source")
    require_hash(new, WSC15_SHA256, "WSC 1.5 source")

    # The helper call-site encodings prove these resolved physical addresses.
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

    old_p1_parsed = parse_shoot_p1(old, OLD_SOURCES["p1"])
    old_p1_oracle = verify_commercial_p1(old_p1_parsed, gba, GBA_SOURCES["p1"])
    if not old_p1_oracle["payloads_exact"] or not old_p1_oracle["a_records_exact"]:
        raise SystemExit("Shoot-lineage P1 conversion no longer matches commercial GBA")

    old_p0, old_p0_info = build_asset(
        old,
        wsc_header=OLD_SOURCES["p0"],
        target_header=GBA_SOURCES["p0"],
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    old_p2 = convert_block(old[OLD_SOURCES["p2"]:OLD_SOURCES["p2"] + 38])
    old_p0_oracle = comparison(
        old_p0,
        gba[GBA_SOURCES["p0"]:GBA_SOURCES["p0"] + len(old_p0)],
    )
    if (
        old_p0_oracle["bytes"] != 792
        or old_p0_oracle["exact_prefix_bytes"] != 784
        or old_p0_oracle["mismatch_bytes"] != 5
    ):
        raise SystemExit("Shoot-lineage P0 commercial boundary changed")
    old_p0_oracle["logical_content_bytes"] = 784
    old_p0_oracle["tail_classification"] = (
        "converter alignment padding overlaps the following commercial structure"
    )
    old_p2_oracle = comparison(
        old_p2,
        gba[GBA_SOURCES["p2"]:GBA_SOURCES["p2"] + len(old_p2)],
    )
    if not old_p2_oracle["exact"]:
        raise SystemExit("Shoot-lineage P2 conversion no longer matches commercial GBA")

    new_p1_parsed = parse_shoot_p1(new, NEW_SOURCES["p1"])
    new_p1, new_p1_info = convert_shoot_p1(new_p1_parsed, ANALYSIS_TARGETS["p1"])
    new_p0, new_p0_info = build_asset(
        new,
        wsc_header=NEW_SOURCES["p0"],
        target_header=ANALYSIS_TARGETS["p0"],
        expected_layout_entries=None,
        expected_layout_record_bytes=None,
        expected_descriptor_entries=None,
        expected_tile_bytes=None,
    )
    new_p2 = convert_block(new[NEW_SOURCES["p2"]:NEW_SOURCES["p2"] + 38])

    result = {
        "schema": 1,
        "kind": "digimon-shoot-spawn-resource-conversion-boundary",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "lineage": [
            {
                "kind": kind,
                "wsc10_physical": OLD_SOURCES[kind],
                "wsc15_physical": NEW_SOURCES[kind],
                "commercial_gba": GBA_BASE + GBA_SOURCES[kind],
            }
            for kind in ("p1", "p0", "p2")
        ],
        "commercial_oracle": {
            "p1_shoot_variant": old_p1_oracle,
            "p0_relocatable": old_p0_oracle,
            "p2_palette": old_p2_oracle,
            "p0_conversion": old_p0_info,
        },
        "wsc15_conversion": {
            "p1": {
                "target": ANALYSIS_TARGETS["p1"],
                "converted": True,
                "bytes": len(new_p1),
                "sha256": sha256(new_p1),
                "source_header": {
                    key: value for key, value in new_p1_parsed.items()
                    if key not in ("payloads", "a_records")
                },
                "details": new_p1_info,
            },
            "p0": {
                "target": ANALYSIS_TARGETS["p0"],
                "bytes": len(new_p0),
                "sha256": sha256(new_p0),
                "details": new_p0_info,
            },
            "p2": {
                "target": ANALYSIS_TARGETS["p2"],
                "bytes": len(new_p2),
                "sha256": sha256(new_p2),
            },
        },
        "claim_scope": (
            "source-resolved resource formats and deterministic conversion only; "
            "commercial mismatches remain explicit and no GBA rule callback is installed"
        ),
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
