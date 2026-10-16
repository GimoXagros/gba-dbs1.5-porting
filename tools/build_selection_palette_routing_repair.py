#!/usr/bin/env python3
"""Correct the two PC-relative palette literals in the selection hook."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

INPUT = "A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
BASE = 0x08000000


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, offset):
    return struct.unpack_from("<I", data, offset)[0]


def literal(data, at, destination):
    instruction = word(data, at)
    need(instruction & 0xFFFFF000 == 0xE59F0000 | destination << 12,
         "positive unconditional ARM PC-relative LDR")
    pool = at + 8 + (instruction & 0xFFF)
    return pool, word(data, pool)


def build(before, gba):
    need((sha(before), sha(gba)) == (INPUT, GBA), "fixed callback6 predecessor and USA original")
    need(len(before) == 0x800000, "expanded ROM size")
    need(sha(before[0x4A5C40:0x4A5C94]) ==
         "CA1C91959DF0D9DF0AA3EB087098B019257DD6F3A22A1EA85E0FF1273AE024C0",
         "exact existing selection portrait hook")
    need(sha(before[0xB84:0xBA8]) ==
         "7F3A5BB5C97441ACE990D2F73353C30FB43540ED3E5528A303FF7CC81A4D64C8"
         and before[0xB84:0xBA8] == gba[0xB84:0xBA8], "native DMA count/ABI unchanged")
    need(before[0x4A5BC0:0x4A5C20] == gba[0x832F0:0x83350], "twelve original portrait pairs retained")
    need(literal(before, 0x4A5C44, 8) == (0x4A5C84, 0x05000020) and
         literal(before, 0x4A5C48, 5) == (0x4A5C88, 0x084A5BC4),
         "observed wrong palette literal resolution")
    after = bytearray(before)
    changes = ((0x4A5C44, 0xE59F8038, 0xE59F8034),
               (0x4A5C48, 0xE59F5038, 0xE59F5034))
    for at, expected, replacement in changes:
        need(word(before, at) == expected, "Expected Write old LDR")
        struct.pack_into("<I", after, at, replacement)
    need(literal(after, 0x4A5C44, 8) == (0x4A5C80, 0x084A5BC0) and
         literal(after, 0x4A5C48, 5) == (0x4A5C84, 0x05000020),
         "palette pair table and hardware destination")
    need(literal(after, 0x4A5C58, 8) == (0x4A5C88, 0x084A5BC4) and
         literal(after, 0x4A5C5C, 5) == (0x4A5C8C, 0x06005780),
         "unchanged tile pair table and destination")
    consumers = []
    for character in range(15):
        palette, pixels = struct.unpack_from("<2I", after, 0x4A5BC0 + character * 8)
        need(BASE <= palette <= BASE + len(after) - 32 and
             BASE <= pixels <= BASE + len(after) - 0x1800, "complete ROM portrait payloads")
        consumers.append({"character": character, "palette_source": palette,
                          "palette_destination": 0x05000020, "palette_bytes": 32,
                          "tile_source": pixels, "tile_destination": 0x06005780,
                          "tile_bytes": 0x1800})
    diff = [index for index, (old, new) in enumerate(zip(before, after, strict=True)) if old != new]
    need(diff == [0x4A5C44, 0x4A5C48], "complete ROM two-byte diff")
    return bytes(after), {"schema": 1, "kind": "selection-palette-literal-routing-repair",
                         "input_sha256": INPUT, "output_sha256": sha(after),
                         "expected_writes": [{"raw": at, "before": f"{old:08X}", "after": f"{new:08X}"}
                                             for at, old, new in changes],
                         "changed_bytes": diff, "portrait_DMA_contracts": consumers,
                         "cause": "both first LDR offsets pointed one literal word too far forward",
                         "new_allocations": [], "new_RAM": False, "new_callbacks": False,
                         "scope": "restore native palette DMA source/destination; runtime visuals verified separately"}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "output", "manifest")), "save paths forbidden")
    result, report = build(args.input.read_bytes(), args.gba.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[selection-palette-routing] " + report["output_sha256"])


if __name__ == "__main__":
    main()
