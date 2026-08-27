#!/usr/bin/env python3
"""Map one GBA 512-tile stage payload to decoded WSC tile sources."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def convert_wsc_tile(tile: bytes) -> bytes:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return bytes(pixels[index] | (pixels[index + 1] << 4) for index in range(0, 64, 2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--gba-tiles", type=parse_int, required=True)
    parser.add_argument("--wsc-start", type=parse_int, default=0)
    parser.add_argument("--wsc-end", type=parse_int)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    end = min(len(wsc), args.wsc_end if args.wsc_end is not None else len(wsc))
    index: dict[bytes, list[int]] = collections.defaultdict(list)
    for offset in range(args.wsc_start, end - 31, 32):
        index[convert_wsc_tile(wsc[offset:offset + 32])].append(offset)

    mappings = []
    bank_counts: collections.Counter[int] = collections.Counter()
    unique_bank_counts: collections.Counter[int] = collections.Counter()
    for relative in range(512):
        source = args.gba_tiles + relative * 32
        tile = gba[source:source + 32]
        hits = index.get(tile, [])
        informative = len(set(tile)) > 2
        if informative:
            for hit in hits:
                bank_counts[hit >> 16] += 1
            if len(hits) == 1:
                unique_bank_counts[hits[0] >> 16] += 1
        mappings.append({
            "gba_relative_tile": relative,
            "informative": informative,
            "wsc_offsets": hits[:64],
            "hit_count": len(hits),
        })
    result = {
        "schema": 1,
        "gba_tiles": args.gba_tiles,
        "informative_tiles": sum(row["informative"] for row in mappings),
        "matched_informative_tiles": sum(row["informative"] and row["hit_count"] for row in mappings),
        "unique_informative_tiles": sum(row["informative"] and row["hit_count"] == 1 for row in mappings),
        "bank_hit_counts": [{"bank": bank, "hits": count} for bank, count in bank_counts.most_common()],
        "unique_bank_hit_counts": [{"bank": bank, "hits": count} for bank, count in unique_bank_counts.most_common()],
        "mappings": mappings,
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
