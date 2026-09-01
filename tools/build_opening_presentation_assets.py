#!/usr/bin/env python3
"""Build the two nonresident P0 assets for opening selectors 11..14.

The WSC 1.5 presentation records are 35..38. Static lineage proves that all
four P1 containers and P2 palettes, plus the shared P0 used by selectors 11
and 13, are byte-identical to commercial selector resources already resident
in the USA GBA ROM. Only selector 12 and 14 P0 animation/tile containers are
therefore converted and emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_full_asset_poc import build_asset
from build_new_base_p1_assets import wsc_pointer
from convert_wsc_palette_block import WSC_BYTES as WSC_PALETTE_BYTES, convert_block


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
P1_CORPUS_SHA256 = "B9F671AB5FE6E66DA7351AFFFAFD7C6E4D07370E84D231E501A6D8C51B52B887"

WSC10_TABLE = 0x390000
WSC15_TABLE = 0x740000
GBA_PRESENTATION_VIEW = 0x0D42B8
RECORD_BYTES = 0x20
P0_TARGET_BASE = 0x50D000

SELECTOR_RECORDS = {11: 35, 12: 36, 13: 37, 14: 38}
COMMERCIAL_SELECTOR = {11: 5, 12: 6, 13: 7, 14: 8}
EXPECTED_RECORD_HASHES = {
    35: "A72C1E300CC396829F6D83401CF459E4608D19400FBC0437CDBAFA2FBB8B17BC",
    36: "F20514E8795616C9A96B8B7E16906080AFB830EAFF45497B97D5E2D632A56AFD",
    37: "E5040857EF14B2FCCD87734A0ED71C75A696BB3D048017996FAD093E49382BFF",
    38: "EF78A2AC1F72246C181BD0AF51880A91856551DC1DA5F96E6C0665600E478F8D",
}
EXPECTED_TARGETS = {
    11: (0x34B410, 0x3B0000, 0x3D6730),
    12: (0x364930, 0x3B1360, 0x3D74F0),
    13: (0x34B410, 0x3B0000, 0x3D6756),
    14: (0x323C00, 0x3A2560, 0x3D7550),
}
P1_IDENTITY = {
    11: (0x519, "C761D001B02C6F89F3AAC533F198CB35E51761BDA05122A7ACFCC803B124EE1D"),
    12: (0x631, "DCEE7219EC08C3CB14CC372D4E775B582D093F907ED2ED13E721DA7CFECCFFD4"),
    13: (0x519, "C761D001B02C6F89F3AAC533F198CB35E51761BDA05122A7ACFCC803B124EE1D"),
    14: (0x6FD, "D3DD98ED407B98D7D55CD61676247FC133A8A80A78F6D0FE3013EB4EB93B4EBE"),
}
NONRESIDENT_P0_SELECTORS = (12, 14)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def require_p1_corpus(path: pathlib.Path) -> None:
    raw = path.read_bytes()
    require_hash(raw, P1_CORPUS_SHA256, "opening P1 commercial corpus")
    corpus = json.loads(raw)
    required = {
        "pair_count": 11,
        "command_count": 122,
        "zero_tail_command_count": 122,
        "same_index_field_mismatch_counts": [381, 0, 0, 0, 0, 0],
    }
    for key, value in required.items():
        if corpus.get(key) != value:
            raise ValueError(f"opening P1 corpus invariant changed: {key}")


def gba_view_pointer(gba: bytes, selector: int, field: int) -> int:
    value = struct.unpack_from(
        "<I", gba, GBA_PRESENTATION_VIEW + selector * RECORD_BYTES + field * 4
    )[0]
    if not 0x08000000 <= value < 0x08000000 + len(gba):
        raise ValueError(f"invalid GBA presentation pointer 0x{value:08X}")
    return value - 0x08000000


def validate_commercial_palette_rule(
    gba: bytes, wsc10: bytes
) -> list[dict[str, object]]:
    cases = []
    for selector in range(11):
        record = WSC10_TABLE + (24 + selector) * RECORD_BYTES
        source = wsc_pointer(wsc10, record + 12)
        target = gba_view_pointer(gba, selector, 2)
        converted = convert_block(wsc10[source:source + WSC_PALETTE_BYTES])
        if converted != gba[target:target + len(converted)]:
            raise ValueError(f"commercial opening palette {selector} changed")
        cases.append({
            "selector": selector,
            "wsc_record": 24 + selector,
            "wsc_p2": source,
            "gba_p2": target,
            "sha256": sha256(converted),
        })
    return cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("p1_corpus", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC 1.5 source")
    require_p1_corpus(args.p1_corpus)
    palette_corpus = validate_commercial_palette_rule(gba, wsc10)

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    cursor = P0_TARGET_BASE
    blob = bytearray()
    records = []
    placements = []
    for selector, record_id in SELECTOR_RECORDS.items():
        record = WSC15_TABLE + record_id * RECORD_BYTES
        require_hash(
            wsc15[record:record + RECORD_BYTES],
            EXPECTED_RECORD_HASHES[record_id],
            f"WSC 1.5 opening record {record_id}",
        )
        sources = tuple(wsc_pointer(wsc15, record + field * 6) for field in range(3))
        if sources != EXPECTED_TARGETS[selector]:
            raise ValueError(f"opening selector {selector} field target changed")

        old_selector = COMMERCIAL_SELECTOR[selector]
        old_record = WSC10_TABLE + (24 + old_selector) * RECORD_BYTES
        old_sources = tuple(
            wsc_pointer(wsc10, old_record + field * 6) for field in range(3)
        )

        # P1 is byte-identical across revisions before platform conversion, so
        # the corresponding commercial native GBA container is reused.
        length, expected_hash = P1_IDENTITY[selector]
        new_p1 = wsc15[sources[1]:sources[1] + length]
        old_p1 = wsc10[old_sources[1]:old_sources[1] + length]
        require_hash(new_p1, expected_hash, f"opening selector {selector} P1")
        if new_p1 != old_p1:
            raise ValueError(f"opening selector {selector} P1 identity changed")
        p1_target = gba_view_pointer(gba, old_selector, 1)

        # P2 uses the exact commercial BGR444->BGR555 rule and resolves to the
        # corresponding resident commercial palette.
        converted_palette = convert_block(
            wsc15[sources[2]:sources[2] + WSC_PALETTE_BYTES]
        )
        p2_target = gba_view_pointer(gba, old_selector, 2)
        if converted_palette != gba[p2_target:p2_target + len(converted_palette)]:
            raise ValueError(f"opening selector {selector} P2 reuse changed")

        commercial_p0 = gba_view_pointer(gba, old_selector, 0)
        converted_at_commercial, _ = build_asset(
            wsc15,
            wsc_header=sources[0],
            target_header=commercial_p0,
            expected_layout_entries=None,
            expected_layout_record_bytes=None,
            expected_descriptor_entries=None,
            expected_tile_bytes=None,
        )
        resident_p0 = converted_at_commercial == gba[
            commercial_p0:commercial_p0 + len(converted_at_commercial)
        ]
        if selector in NONRESIDENT_P0_SELECTORS:
            if resident_p0:
                raise ValueError(f"opening selector {selector} P0 unexpectedly became resident")
            target = align(cursor, 32)
            blob.extend(bytes(target - (P0_TARGET_BASE + len(blob))))
            converted, details = build_asset(
                wsc15,
                wsc_header=sources[0],
                target_header=target,
                expected_layout_entries=None,
                expected_layout_record_bytes=None,
                expected_descriptor_entries=None,
                expected_tile_bytes=None,
            )
            blob.extend(converted)
            cursor = target + len(converted)
            p0_target = target
            placements.append({
                "selector": selector,
                "wsc_record": record_id,
                "source": sources[0],
                "target": target,
                "bytes": len(converted),
                "sha256": sha256(converted),
                "layout_entries": details["layout_entries"],
                "descriptor_entries": details["descriptor_entries"],
                "tile_payload_bytes": details["tile_payload_bytes"],
            })
        else:
            if not resident_p0:
                raise ValueError(f"opening selector {selector} P0 identity changed")
            p0_target = commercial_p0

        records.append({
            "selector": selector,
            "wsc_record": record_id,
            "commercial_reuse_selector": old_selector,
            "wsc_fields": list(sources),
            "gba_fields": [p0_target, p1_target, p2_target],
            "reuse": {
                "p0": selector not in NONRESIDENT_P0_SELECTORS,
                "p1": True,
                "p2": True,
            },
        })

    binary = output / "opening-p0.bin"
    binary.write_bytes(blob)
    file_entry = {
        "name": binary.name,
        "target_base": P0_TARGET_BASE,
        "target_end": P0_TARGET_BASE + len(blob),
        "bytes": len(blob),
        "sha256": sha256(blob),
    }
    result = {
        "schema": 1,
        "kind": "native-opening-presentation-selector-assets",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "commercial_conversion_evidence": {
            "p1_corpus_sha256": P1_CORPUS_SHA256,
            "p2_exact_case_count": len(palette_corpus),
            "p2_cases": palette_corpus,
        },
        "files": [file_entry],
        "placements": placements,
        "records": records,
        "claim_scope": (
            "Static opening selector 11..14 P0/P1/P2 resources. Resident "
            "commercial assets are reused; only two nonresident P0 containers "
            "are emitted. Table wiring and runtime behavior remain unverified."
        ),
    }
    rendered = json.dumps(result, indent=2) + "\n"
    (output / "opening-presentation.json").write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
