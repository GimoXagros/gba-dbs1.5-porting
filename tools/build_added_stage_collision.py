#!/usr/bin/env python3
"""Bind the three added arenas to their original four-byte collision grids."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

INPUT = "1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
CLASS_TABLE, CLASS_BRIDGE, CLASS_SITE = 0x627800, 0x6278C0, 0xC8438
GRIDS = (
    {"name": "train", "source_records": (33,), "native_records": (21,), "dimensions": (2, 2),
     "source": 0x380000, "target": 0x622000, "bytes": 0x1F80,
     "sha256": "18C8661CB6F449289C41613B2D3201DD9962D82CBBA3159FE71F9A52BFF940CB"},
    {"name": "iraira", "source_records": (37, 38), "native_records": (25, 26), "dimensions": (2, 2),
     "source": 0x381F80, "target": 0x624000, "bytes": 0x1F80,
     "sha256": "2945AA197AD5A16A38295EC0210C04A38E5DA44F39EB93092724D8BB2DE8764E"},
    {"name": "waterfall", "source_records": (35, 36), "native_records": (27, 28), "dimensions": (1, 3),
     "source": 0x38E240, "target": 0x626000, "bytes": 0x17A0,
     "sha256": "4A272554DFEC164F5A98F947E4935821669F80FE86CCB1A0C5F1B910BA2ADEC0"},
)
RETAIL = ((0, 0x26CB60), (4, 0x270000), (10, 0x271F80), (12, 0x273F00),
          (14, 0x275E80), (16, 0x1F9BA0), (18, 0x1FCAE0))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, target):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM branch range/alignment")
    return 0xEA000000 | ((delta // 4) & 0xFFFFFF)


def no_inbound(data, intervals):
    def owned(address):
        return any(BASE + start <= address < BASE + end for start, end in intervals)
    for at in range(len(data) - 3):
        need(not owned(word(data, at)), f"prior encoded pointer into allocation at {at:06X}")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            displacement = value & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 1 << 24
            need(not owned(BASE + at + 8 + displacement * 4), f"prior ARM branch into allocation {at:06X}")
        if value & 0x0E1F0000 == 0x041F0000:
            displacement = value & 0xFFF
            if not value & 0x00800000:
                displacement = -displacement
            need(not owned(BASE + at + 8 + displacement), f"prior ARM literal into allocation {at:06X}")


def build(before, gba, wsc10, wsc15):
    need(sha(before) == INPUT and tuple(map(sha, (gba, wsc10, wsc15))) == ORIGINALS,
         "fixed spawn-repair predecessor and original inputs")
    need(len(before) == 0x800000, "expanded ROM size")
    # These exact live consumers copy descriptor+0C to BG+28 and use four-byte
    # cells. Added data never replaces either collision engine or actor motion.
    consumer_ranges = ((0x13BF8, 0x13C64), (0xC86B4, 0xC8E18), (0x373928, 0x373BA4))
    for start, end in consumer_ranges:
        need(before[start:end] == gba[start:end], "actual retail collision consumer remains exact")
    commercial = []
    for record, source in RETAIL:
        at = 0x7F8E0 + record * 24
        width, height = struct.unpack_from("<2H", gba, at)
        target = word(gba, at + 12) - BASE
        size = width * height * 28 * 18 * 4
        need(gba[target:target + size] == wsc10[source:source + size], "commercial four-byte cell identity")
        commercial.append({"native_record": record, "source_raw": source, "native_raw": target,
                           "bytes": size, "sha256": sha(gba[target:target + size])})
    retail_cells = set()
    for record in range(21):
        at = 0x7F8E0 + record * 24
        width, height = struct.unpack_from("<2H", gba, at)
        pointer = word(gba, at + 12)
        if pointer:
            size = width * height * 28 * 18 * 4
            retail_cells.update(struct.iter_unpack("<2H", gba[pointer - BASE:pointer - BASE + size]))
    retail_masks = [0, 0]
    for pair in retail_cells:
        for field in range(2):
            retail_masks[field] |= pair[field]

    classification = wsc15[0x76F760:0x76F820]
    need(len(classification) == 12 * 16 and max(classification) < 16,
         "complete source classification table uses existing16 handler indices")
    need(classification[:128] == gba[0xC84B8:0xC8538], "all eight retail classification rows retained")
    need(before[0xC842C:0xC863C] == gba[0xC842C:0xC863C], "both native classification dispatchers unchanged")
    need(word(before, CLASS_SITE) == 0xE28F4078, "Expected Write old PC-relative classification table")
    allocations = [(grid["target"], grid["target"] + grid["bytes"]) for grid in GRIDS]
    allocations += [(CLASS_TABLE, CLASS_TABLE + 192), (CLASS_BRIDGE, CLASS_BRIDGE + 12)]
    for start, end in allocations:
        need(before[start:end] == b"\xFF" * (end - start), "exact new allocation is blank")
    no_inbound(before, allocations)
    after = bytearray(before)
    after[CLASS_TABLE:CLASS_TABLE + 192] = classification
    bridge = struct.pack("<3I", 0xE59F4000, branch(CLASS_BRIDGE + 4, CLASS_SITE + 4), BASE + CLASS_TABLE)
    after[CLASS_BRIDGE:CLASS_BRIDGE + 12] = bridge
    struct.pack_into("<I", after, CLASS_SITE, branch(CLASS_SITE, CLASS_BRIDGE))
    reports, pointer_writes = [], []
    for grid in GRIDS:
        width, height = grid["dimensions"]
        size = width * height * 28 * 18 * 4
        need(size == grid["bytes"], "complete source-defined grid extent")
        payload = wsc15[grid["source"]:grid["source"] + size]
        need(sha(payload) == grid["sha256"], "original grid identity")
        for record in grid["source_records"]:
            at = 0x3B4DD0 + record * 24
            need(struct.unpack_from("<2H", wsc15, at) == (width, height), "source resource dimensions")
            offset, segment = struct.unpack_from("<2H", wsc15, at + 12)
            physical = segment * 16 + offset
            need(0x20000 <= physical and physical + size <= 0x30000, "source C2 collision window extent")
            raw = ((wsc15[at + 5] & 127) << 16) | (physical & 65535)
            need(raw == grid["source"], "source resource selects complete collision grid")
        for record in grid["native_records"]:
            at = 0x580000 + record * 24
            need(struct.unpack_from("<2H", before, at) == (width, height), "native matching resource dimensions")
            need(word(before, at + 12) == 0, "Expected Write missing collision pointer")
            struct.pack_into("<I", after, at + 12, BASE + grid["target"])
            pointer_writes.append({"raw": at + 12, "before": 0, "after": BASE + grid["target"],
                                   "native_record": record})
        after[grid["target"]:grid["target"] + size] = payload
        frequencies = Counter(struct.iter_unpack("<2H", payload))
        new_masks = [0, 0]
        for pair in frequencies:
            for field in range(2):
                new_masks[field] |= pair[field]
        need(all(new_masks[k] & ~retail_masks[k] == 0 for k in range(2)),
             "no collision flag bit position absent from commercial corpus")
        reports.append({**grid, "cells": size // 4,
                        "field_bit_masks": new_masks,
                        "distinct_cells": [{"first": first, "second": second, "count": count}
                                           for (first, second), count in sorted(frequencies.items())],
                        "combinations_absent_from_retail": sorted(set(frequencies) - retail_cells)})
    inverse = bytearray(after)
    intervals = allocations + [(item["raw"], item["raw"] + 4) for item in pointer_writes]
    intervals.append((CLASS_SITE, CLASS_SITE + 4))
    for start, end in intervals:
        inverse[start:end] = before[start:end]
    need(inverse == before, "full inverse outside three grids, five pointers and classification bridge")
    return bytes(after), {
        "schema": 1, "kind": "added-stage-collision-binding", "input_sha256": INPUT,
        "output_sha256": sha(after), "source_grids": reports, "commercial_pairs": commercial,
        "retail_field_bit_masks": retail_masks, "pointer_writes": pointer_writes,
        "classification": {"source_raw": 0x76F760, "target_raw": CLASS_TABLE, "bytes": 192,
                           "rows": 12, "kind_count": 16, "sha256": sha(classification),
                           "bridge_raw": CLASS_BRIDGE, "bridge_bytes": 12, "hook_raw": CLASS_SITE,
                           "hook_before": "E28F4078", "hook_after": f"{word(after, CLASS_SITE):08X}",
                           "bridge_ABI": "replace intended r4 only; flags, other registers, LR and SP preserved",
                           "continuation": BASE + CLASS_SITE + 4,
                           "new_stage_rows": [list(classification[index * 16:index * 16 + 16]) for index in range(8, 12)]},
        "allocations": allocations, "predecessor_inbound_candidates": [],
        "changed_bytes": sum(a != b for a, b in zip(before, after, strict=True)),
        "consumer_ranges_unchanged": consumer_ranges, "new_RAM": False, "new_callbacks": False,
        "scope": "exact source grids and12-row class selection through existing native handlers; no new effects or flag clamps",
        "remaining": ["independent source/native handler proof and runtime checks",
                      "Train graphics/initializer geometry repair belongs to its separate layer",
                      "actual-stage lifecycle and ordinary spawn selection remain separate"]}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "wsc10", "wsc15", "output", "manifest")), "save paths forbidden")
    result, report = build(*(getattr(args, name).read_bytes() for name in ("input", "gba", "wsc10", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[added-stage-collision] " + report["output_sha256"])


if __name__ == "__main__":
    main()
