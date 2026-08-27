#!/usr/bin/env python3
"""Locate WSC 28x18 stage maps corresponding to GBA map resources.

The commercial GBA converter reordered tiles but retained the 28x18 map
surface.  We map stage-bank tiles by exact decoded pixels, translate uniquely
mapped GBA entries back to WSC screen entries, then find and score candidate
source windows in the WSC ROM.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import struct


MAP_ENTRIES = 28 * 18
RESOURCE_SIZE = 0x18


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


def gba_to_wsc_entry(entry: int, wsc_relative_tile: int) -> int:
    palette = (entry >> 12) & 0xF
    result = (wsc_relative_tile & 0x1FF) | 0x2000 | (palette << 9)
    if entry & 0x400:
        result |= 0x4000
    if entry & 0x800:
        result |= 0x8000
    return result


def unpack_gba_tile(tile: bytes) -> bytes:
    pixels = bytearray()
    for value in tile:
        pixels.extend((value & 0xF, value >> 4))
    return bytes(pixels)


def flip_tile(tile: bytes, horizontal: bool, vertical: bool) -> bytes:
    output = bytearray(64)
    for y in range(8):
        sy = 7 - y if vertical else y
        for x in range(8):
            sx = 7 - x if horizontal else x
            output[y * 8 + x] = tile[sy * 8 + sx]
    return bytes(output)


def maximal_runs(expected: list[int | None], minimum: int) -> list[tuple[int, bytes]]:
    runs = []
    index = 0
    while index < len(expected):
        if expected[index] is None:
            index += 1
            continue
        start = index
        words = []
        while index < len(expected) and expected[index] is not None:
            words.append(expected[index])
            index += 1
        if len(words) >= minimum:
            runs.append((start, struct.pack(f"<{len(words)}H", *words)))
    return runs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--gba-tiles", type=parse_int, required=True)
    parser.add_argument("--wsc-tiles", type=parse_int, required=True)
    parser.add_argument("--resource-start", type=parse_int, default=0x7F8E0)
    parser.add_argument("--resource-first", type=int, required=True)
    parser.add_argument("--resource-count", type=int, required=True)
    parser.add_argument("--scan-start", type=parse_int, default=0)
    parser.add_argument("--scan-end", type=parse_int)
    parser.add_argument("--minimum-anchor", type=int, default=4)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    scan_end = min(len(wsc), args.scan_end if args.scan_end is not None else len(wsc))

    wsc_by_tile: dict[bytes, list[int]] = collections.defaultdict(list)
    wsc_pixels: list[bytes] = []
    for relative in range(512):
        source = args.wsc_tiles + relative * 32
        converted = convert_wsc_tile(wsc[source:source + 32])
        wsc_by_tile[converted].append(relative)
        wsc_pixels.append(unpack_gba_tile(converted))

    gba_to_wsc: list[list[int]] = []
    gba_pixels: list[bytes] = []
    for relative in range(512):
        source = args.gba_tiles + relative * 32
        raw = gba[source:source + 32]
        gba_to_wsc.append(wsc_by_tile.get(raw, []))
        gba_pixels.append(unpack_gba_tile(raw))

    signature_ids: dict[bytes, int] = {}
    def signature_id(tile: bytes) -> int:
        if tile not in signature_ids:
            signature_ids[tile] = len(signature_ids)
        return signature_ids[tile]

    wsc_visual: dict[tuple[int, bool, bool], int] = {}
    for relative, tile in enumerate(wsc_pixels):
        for horizontal in (False, True):
            for vertical in (False, True):
                wsc_visual[(relative, horizontal, vertical)] = signature_id(
                    flip_tile(tile, horizontal, vertical)
                )

    scan_words = struct.unpack_from(f"<{(scan_end - args.scan_start) // 2}H", wsc, args.scan_start)
    scan_signatures: list[int] = []
    for entry in scan_words:
        if not entry & 0x2000:
            scan_signatures.append(-1)
            continue
        scan_signatures.append(wsc_visual[(entry & 0x1FF, bool(entry & 0x4000), bool(entry & 0x8000))])

    reports = []
    for resource_index in range(args.resource_first, args.resource_first + args.resource_count):
        resource = args.resource_start + resource_index * RESOURCE_SIZE
        width, height = struct.unpack_from("<HH", gba, resource)
        descriptor = struct.unpack_from("<I", gba, resource + 8)[0] - 0x08000000
        for frame in range(width * height):
            count, map_pointer = struct.unpack_from("<II", gba, descriptor + frame * 8)
            map_offset = map_pointer - 0x08000000
            entries = struct.unpack_from(f"<{MAP_ENTRIES}H", gba, map_offset)
            expected: list[int | None] = []
            visual_expected: list[int | None] = []
            for entry in entries:
                tile_index = entry & 0x3FF
                relative = tile_index - 0x200
                candidates = gba_to_wsc[relative] if 0 <= relative < 512 else []
                expected.append(gba_to_wsc_entry(entry, candidates[0]) if len(candidates) == 1 else None)

                if 0 <= relative < 512:
                    visual = flip_tile(gba_pixels[relative], bool(entry & 0x400), bool(entry & 0x800))
                    visual_expected.append(signature_ids.get(visual))
                else:
                    visual_expected.append(None)

            candidate_starts: collections.Counter[int] = collections.Counter()
            anchors = []
            index = 0
            while index < len(visual_expected):
                if visual_expected[index] is None:
                    index += 1
                    continue
                start = index
                values = []
                while index < len(visual_expected) and visual_expected[index] is not None:
                    values.append(visual_expected[index])
                    index += 1
                if len(values) >= args.minimum_anchor:
                    anchors.append((start, values))

            scan_anchor_index: dict[tuple[int, ...], list[int]] = collections.defaultdict(list)
            anchor_size = args.minimum_anchor
            for word_index in range(0, len(scan_signatures) - anchor_size + 1):
                key = tuple(scan_signatures[word_index:word_index + anchor_size])
                if -1 not in key:
                    scan_anchor_index[key].append(word_index)
            for position, values in sorted(anchors, key=lambda row: len(row[1]), reverse=True)[:64]:
                for within in range(0, len(values) - anchor_size + 1, anchor_size):
                    key = tuple(values[within:within + anchor_size])
                    for word_index in scan_anchor_index.get(key, []):
                        start_word = word_index - position - within
                        start = args.scan_start + start_word * 2
                        if args.scan_start <= start <= scan_end - MAP_ENTRIES * 2:
                            candidate_starts[start] += anchor_size

            constrained = sum(item is not None for item in visual_expected)
            scored = []
            for start, anchor_votes in candidate_starts.items():
                word_start = (start - args.scan_start) // 2
                source_signatures = scan_signatures[word_start:word_start + MAP_ENTRIES]
                equal = sum(want is not None and want == got
                            for want, got in zip(visual_expected, source_signatures))
                scored.append({
                    "wsc_map_offset": start,
                    "constrained_entries": constrained,
                    "matching_entries": equal,
                    "match_ratio": round(equal / constrained, 6) if constrained else 0,
                    "anchor_votes": anchor_votes,
                })
            scored.sort(key=lambda row: (-row["matching_entries"], -row["anchor_votes"], row["wsc_map_offset"]))
            reports.append({
                "resource_index": resource_index,
                "frame": frame,
                "descriptor": descriptor + frame * 8,
                "count": count,
                "gba_map_offset": map_offset,
                "unique_tile_constraints": constrained,
                "anchors": len(anchors),
                "candidates": scored[:20],
            })

    result = {
        "schema": 1,
        "gba_to_wsc_unique_tiles": sum(len(candidates) == 1 for candidates in gba_to_wsc),
        "gba_to_wsc_ambiguous_tiles": sum(len(candidates) > 1 for candidates in gba_to_wsc),
        "reports": reports,
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
