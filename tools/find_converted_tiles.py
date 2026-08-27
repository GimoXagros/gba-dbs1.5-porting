#!/usr/bin/env python3
"""Look for WSC planar tiles after lossless conversion to GBA packed 4bpp."""

from __future__ import annotations

import argparse
import json
import pathlib


def parse_int(value: str) -> int:
    return int(value, 0)


def wsc_planar_to_indices(tile: bytes) -> list[int]:
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return pixels


def indices_to_gba(tile: list[int]) -> bytes:
    return bytes(tile[index] | (tile[index + 1] << 4) for index in range(0, 64, 2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--wsc-start", type=parse_int, default=0)
    parser.add_argument("--wsc-end", type=parse_int, default=0x4E0000)
    parser.add_argument("--sequence-tiles", type=int, default=4)
    parser.add_argument("--gba-alignment", type=int, default=4)
    parser.add_argument("--minimum-run-tiles", type=int, default=8)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()[args.wsc_start:args.wsc_end]
    converted = bytearray()
    for pos in range(0, len(wsc) - 31, 32):
        converted.extend(indices_to_gba(wsc_planar_to_indices(wsc[pos:pos + 32])))

    window = args.sequence_tiles * 32
    gba_windows: dict[bytes, list[int]] = {}
    for pos in range(0, len(gba) - window + 1, args.gba_alignment):
        key = gba[pos:pos + window]
        gba_windows.setdefault(key, []).append(pos)

    matches: list[dict[str, object]] = []
    converted_tiles = [bytes(converted[pos:pos + 32]) for pos in range(0, len(converted), 32)]
    gba_tiles = [gba[pos:pos + 32] for pos in range(0, len(gba) - 31, 32)]
    for pos in range(0, len(converted) - window + 1, 32):
        key = bytes(converted[pos:pos + window])
        if len(set(key)) <= 2:
            continue
        gba_offsets = gba_windows.get(key)
        if gba_offsets:
            matches.append({
                "wsc_offset": args.wsc_start + pos,
                "gba_offsets": gba_offsets[:16],
                "gba_match_count": len(gba_offsets),
            })

    seed_tiles = args.sequence_tiles
    seed_map: dict[tuple[bytes, ...], list[int]] = {}
    for index in range(0, len(gba_tiles) - seed_tiles + 1):
        seed = tuple(gba_tiles[index:index + seed_tiles])
        if len(set(b"".join(seed))) <= 2:
            continue
        seed_map.setdefault(seed, []).append(index)
    runs: list[dict[str, int]] = []
    for wsc_index in range(0, len(converted_tiles) - seed_tiles + 1):
        seed = tuple(converted_tiles[wsc_index:wsc_index + seed_tiles])
        for gba_index in seed_map.get(seed, []):
            if wsc_index > 0 and gba_index > 0 and converted_tiles[wsc_index - 1] == gba_tiles[gba_index - 1]:
                continue
            length = seed_tiles
            while (wsc_index + length < len(converted_tiles)
                   and gba_index + length < len(gba_tiles)
                   and converted_tiles[wsc_index + length] == gba_tiles[gba_index + length]):
                length += 1
            if length >= args.minimum_run_tiles:
                runs.append({
                    "wsc_offset": args.wsc_start + wsc_index * 32,
                    "gba_offset": gba_index * 32,
                    "tiles": length,
                    "bytes": length * 32,
                })
    runs.sort(key=lambda item: item["tiles"], reverse=True)

    rendered = json.dumps({
        "wsc_range": [args.wsc_start, args.wsc_end],
        "sequence_tiles": args.sequence_tiles,
        "gba_alignment": args.gba_alignment,
        "match_count": len(matches),
        "longest_runs": runs[:200],
    }, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
