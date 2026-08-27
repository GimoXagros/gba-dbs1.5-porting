#!/usr/bin/env python3
"""Verify WSC-to-GBA palette conversion against the retail 1.0 port corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from convert_wsc_palette_block import GBA_BYTES, WSC_BYTES, convert_block


GBA_BASE = 0x08000000
RECORD_BYTES = 0x20
EXPECTED_EXACT_CASES = {
    ("base", runtime_id, field)
    for runtime_id in (3, 5, 6, 7, 10, 11)
    for field in (2, 3)
}


def parse_int(value: str) -> int:
    return int(value, 0)


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise ValueError("WSC ROM must contain a power-of-two number of banks")
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def gba_pointer(data: bytes, offset: int) -> int:
    value = struct.unpack_from("<I", data, offset)[0]
    if not GBA_BASE <= value <= GBA_BASE + len(data) - GBA_BYTES:
        raise ValueError(f"invalid GBA palette pointer 0x{value:08X}")
    return value - GBA_BASE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--wsc-base-table", type=parse_int, default=0x390000)
    parser.add_argument("--gba-base-table", type=parse_int, default=0x0D3FC0)
    parser.add_argument("--wsc-evolution-table", type=parse_int, default=0x3903C0)
    parser.add_argument("--gba-evolution-table", type=parse_int, default=0x0D42A0)
    parser.add_argument("--base-records", type=int, default=12)
    parser.add_argument("--evolution-records", type=int, default=11)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    cases = []
    groups = (
        ("base", args.wsc_base_table, args.gba_base_table, args.base_records),
        ("evolution", args.wsc_evolution_table, args.gba_evolution_table,
         args.evolution_records),
    )
    for group, wsc_table, gba_table, count in groups:
        for runtime_id in range(count):
            for field in (2, 3):
                wsc_record = wsc_table + runtime_id * RECORD_BYTES
                gba_record = gba_table + runtime_id * RECORD_BYTES
                wsc_target = wsc_pointer(wsc, wsc_record + field * 6)
                gba_target = gba_pointer(gba, gba_record + (field - 2) * 4)
                source = wsc[wsc_target:wsc_target + WSC_BYTES]
                expected = gba[gba_target:gba_target + GBA_BYTES]
                actual = convert_block(source)
                differing_bytes = [index for index, (left, right) in enumerate(zip(actual, expected))
                                     if left != right]
                cases.append({
                    "group": group,
                    "runtime_id": runtime_id,
                    "field": field,
                    "wsc_target": wsc_target,
                    "gba_target": gba_target,
                    "matches": actual == expected,
                    "expected_exact": (group, runtime_id, field) in EXPECTED_EXACT_CASES,
                    "differing_byte_count": len(differing_bytes),
                    "differing_byte_offsets": differing_bytes,
                    "header_matches": actual[:6] == expected[:6],
                    "padding_matches": actual[-2:] == expected[-2:],
                    "actual_sha256": hashlib.sha256(actual).hexdigest().upper(),
                    "expected_sha256": hashlib.sha256(expected).hexdigest().upper(),
                })

    mismatches = [case for case in cases if not case["matches"]]
    classification_errors = [
        case for case in cases if case["matches"] != case["expected_exact"]
    ]
    exact_sources = []
    for case in cases:
        if not case["matches"]:
            continue
        target = int(case["wsc_target"])
        exact_sources.append(wsc[target:target + WSC_BYTES])
    channel_coverage = {"red": set(), "green": set(), "blue": set()}
    for source in exact_sources:
        for value in struct.unpack_from("<16H", source, 6):
            channel_coverage["blue"].add(value & 0xF)
            channel_coverage["green"].add((value >> 4) & 0xF)
            channel_coverage["red"].add((value >> 8) & 0xF)
    result = {
        "schema": 1,
        "gba_sha256": hashlib.sha256(gba).hexdigest().upper(),
        "wsc_sha256": hashlib.sha256(wsc).hexdigest().upper(),
        "case_count": len(cases),
        "match_count": len(cases) - len(mismatches),
        "mismatch_count": len(mismatches),
        "classification_error_count": len(classification_errors),
        "exact_channel_coverage": {
            name: sorted(values) for name, values in channel_coverage.items()
        },
        "exact_channel_coverage_complete": all(
            values == set(range(16)) for values in channel_coverage.values()
        ),
        "cases": cases,
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if classification_errors:
        raise SystemExit(
            f"{len(classification_errors)} palette cases changed exact/divergent classification"
        )
    if not result["exact_channel_coverage_complete"]:
        raise SystemExit("exact corpus does not cover every 4-bit channel value")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
