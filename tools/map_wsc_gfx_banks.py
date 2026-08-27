#!/usr/bin/env python3
"""Measure converted WSC 4bpp tile overlap against the GBA ROM by 64 KiB bank."""

from __future__ import annotations

import argparse
import collections
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def convert_tile(tile: bytes) -> bytes:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return bytes(pixels[index] | (pixels[index + 1] << 4)
                 for index in range(0, 64, 2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--start", type=parse_int, default=0)
    parser.add_argument("--end", type=parse_int, default=0x340000)
    parser.add_argument("--bank-size", type=parse_int, default=0x10000)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    gba_tiles: dict[bytes, list[int]] = collections.defaultdict(list)
    for offset in range(0, len(gba) - 31, 32):
        gba_tiles[gba[offset:offset + 32]].append(offset)

    results: list[dict[str, object]] = []
    for bank_start in range(args.start, min(args.end, len(wsc)), args.bank_size):
        bank = wsc[bank_start:min(bank_start + args.bank_size, len(wsc))]
        converted = [convert_tile(bank[offset:offset + 32])
                     for offset in range(0, len(bank) - 31, 32)]
        informative = 0
        matched = 0
        deltas: collections.Counter[int] = collections.Counter()
        for index, tile in enumerate(converted):
            if len(set(tile)) <= 2:
                continue
            informative += 1
            positions = gba_tiles.get(tile, [])
            if positions:
                matched += 1
            if len(positions) <= 16:
                for gba_offset in positions:
                    deltas[gba_offset - index * 32] += 1
        best = deltas.most_common(1)
        best_delta = best[0][0] if best else None
        best_votes = best[0][1] if best else 0
        longest_run = 0
        run = 0
        if best_delta is not None:
            for index, tile in enumerate(converted):
                gba_offset = best_delta + index * 32
                equal = 0 <= gba_offset <= len(gba) - 32 and gba[gba_offset:gba_offset + 32] == tile
                run = run + 1 if equal else 0
                longest_run = max(longest_run, run)
        results.append({
            "wsc_bank_offset": bank_start,
            "tiles": len(converted),
            "informative_tiles": informative,
            "matched_informative_tiles": matched,
            "match_ratio": round(matched / informative, 6) if informative else 0.0,
            "best_gba_delta": best_delta,
            "best_delta_votes": best_votes,
            "best_gba_start": best_delta,
            "longest_exact_run_tiles": longest_run,
        })

    print(json.dumps({"banks": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
