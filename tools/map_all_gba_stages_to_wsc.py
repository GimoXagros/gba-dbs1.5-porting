#!/usr/bin/env python3
"""Map all eight retail GBA stage tile payloads to two WSC revisions."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib

from map_gba_stage_tiles_to_wsc import convert_wsc_tile


GBA_STAGE_TILES = (
    0x020168, 0x024248, 0x028328, 0x02C488,
    0x030648, 0x034808, 0x0388E8, 0x03C988,
)


def build_index(data: bytes) -> dict[bytes, list[int]]:
    result: dict[bytes, list[int]] = collections.defaultdict(list)
    for offset in range(0, len(data) - 31, 32):
        result[convert_wsc_tile(data[offset:offset + 32])].append(offset)
    return result


def map_stage(gba: bytes, start: int, index: dict[bytes, list[int]]) -> dict[str, object]:
    bank_counts: collections.Counter[int] = collections.Counter()
    exact_relative_runs: collections.Counter[tuple[int, int]] = collections.Counter()
    informative = matched = unique = 0
    for relative in range(512):
        tile = gba[start + relative * 32:start + (relative + 1) * 32]
        if len(set(tile)) <= 2:
            continue
        informative += 1
        hits = index.get(tile, ())
        if hits:
            matched += 1
        if len(hits) == 1:
            unique += 1
        for hit in hits:
            bank_counts[hit >> 16] += 1
            # A repeated value of hit-relative*32 identifies an order-preserving
            # source payload and is stronger than visual or per-tile similarity.
            exact_relative_runs[(hit >> 16, hit - relative * 32)] += 1
    return {
        "gba_tiles": start,
        "informative_tiles": informative,
        "matched_tiles": matched,
        "unique_tiles": unique,
        "bank_hit_counts": [
            {"bank": bank, "hits": count}
            for bank, count in bank_counts.most_common(12)
        ],
        "ordered_source_candidates": [
            {"bank": bank, "source_base": base, "ordered_tiles": count}
            for (bank, base), count in exact_relative_runs.most_common(12)
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    revisions = {"1.0": args.wsc10.read_bytes(), "1.5": args.wsc15.read_bytes()}
    result: dict[str, object] = {
        "schema": 1,
        "gba_sha256": hashlib.sha256(gba).hexdigest().upper(),
        "revisions": {},
    }
    for name, data in revisions.items():
        index = build_index(data)
        result["revisions"][name] = {
            "sha256": hashlib.sha256(data).hexdigest().upper(),
            "stages": [map_stage(gba, start, index) for start in GBA_STAGE_TILES],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for revision, detail in result["revisions"].items():
        for stage, row in enumerate(detail["stages"]):
            top = row["ordered_source_candidates"][:3]
            rendered = ", ".join(
                f"bank {item['bank']:02X} base {item['source_base']:06X} ({item['ordered_tiles']})"
                for item in top
            )
            print(f"WSC {revision} GBA stage {stage}: {rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
