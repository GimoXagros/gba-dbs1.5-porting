#!/usr/bin/env python3
"""Install the source-backed fifteen-character recovery pointer table.

Only one existing literal and sixty bytes of unused ROM are written. The
thirteen original rows, retail action record, callback, and RAM remain intact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_character_damage_routing import analyze, CURRENT, TABLE, SITE, RECORD
from verify_character_followup_routing import BASE, GBA, OLD, NEW, need, sha, u32

PREDECESSOR = CURRENT
FIRST, LIMIT = 0x629350, 0x62938C
PREVIOUS_LIMIT = 0x629348


def ownership(before: bytes) -> dict:
    need(FIRST == (PREVIOUS_LIMIT + 15) & ~15, "next sixteen-byte aligned allocation")
    need(LIMIT - FIRST == 60 and LIMIT <= len(before), "exact in-bounds table allocation")
    need(before[PREVIOUS_LIMIT:LIMIT] == b"\xff" * (LIMIT - PREVIOUS_LIMIT),
         "recovery table reservation and alignment gap are all FF")
    old_references = []
    for at in range(len(before) - 3):
        if before[at + 3] == 8:
            target = u32(before, at)
            need(not BASE + FIRST <= target < BASE + LIMIT,
                 "no encoded pointer into recovery reservation")
            if BASE + TABLE <= target < BASE + TABLE + 52:
                old_references.append((at, target))
    need(old_references == [(SITE, BASE + TABLE)],
         "only the actual recovery literal refers to any original table byte")
    for at in range(0, len(before) - 3, 4):
        word = u32(before, at)
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 1 << 24
            need(not FIRST <= at + 8 + 4 * delta < LIMIT, "no ARM branch into reservation")
        if word & 0x0E1F0000 == 0x041F0000:
            delta = (word & 4095) * (1 if word & 0x800000 else -1)
            need(not FIRST <= at + 8 + delta < LIMIT, "no ARM PC-relative access into reservation")
        if word & 0x0E0F0000 == 0x020F0000 and (word >> 21) & 15 in (2, 4):
            rotate = ((word >> 8) & 15) * 2
            immediate = word & 255
            if rotate:
                immediate = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF
            target = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
            need(not FIRST <= target < LIMIT, "no ARM PC-relative address into reservation")
    return {"reservation": f"{FIRST:06X}..{LIMIT:06X}", "bytes": LIMIT - FIRST,
            "preceding_layer_end": f"{PREVIOUS_LIMIT:06X}", "alignment": 16,
            "FF": True, "all_alignment_pointer_scan": True,
            "original_table_interior_aliases_excluded": True,
            "ARM_branch_literal_ADR_scan": True}


def build(before: bytes, gba: bytes, old: bytes, source: bytes):
    inputs = (before, gba, old, source)
    need(tuple(map(sha, inputs)) == (PREDECESSOR, GBA, OLD, NEW),
         "fixed predecessor and original ROM identities")
    need(len(before) == 0x800000, "candidate extent")
    proof = analyze(*inputs)
    reservation = ownership(before)
    values = [int(value, 16) for value in proof["minimal_proposal"]["rows"]]
    need(len(values) == 15 and values == [RECORD] * 15, "complete source-derived recovery view")
    need(u32(before, SITE) == BASE + TABLE, "actual native literal predecessor")
    payload = struct.pack("<15I", *values)
    after = bytearray(before)
    after[SITE:SITE + 4] = struct.pack("<I", BASE + FIRST)
    after[FIRST:LIMIT] = payload
    writes = [(SITE, 4), (FIRST, len(payload))]
    need(sum(size for _, size in writes) == 64, "one literal and sixty-byte table only")
    inverse, expected_writes = bytearray(after), []
    for offset, size in writes:
        inverse[offset:offset + size] = before[offset:offset + size]
        expected_writes.append({"raw": f"{offset:06X}", "bytes": size,
                                "before_sha256": sha(before[offset:offset + size]),
                                "after_sha256": sha(after[offset:offset + size])})
    need(inverse == before, "full inverse of declared writes")
    need(len(after) == len(before), "unchanged ROM extent")
    for start, end in [(TABLE, TABLE + 52), (0x36C56C, 0x36C58C),
                       (0x36BA90, 0x36BB60), (0x36B0BC, 0x36B0D4),
                       (0x3555D0, 0x35568C), (0x36F3B8, 0x36F3E8),
                       (0x629000, PREVIOUS_LIMIT)]:
        need(after[start:end] == before[start:end], f"native and prior-layer bytes retained at {start:X}")
    need(after[PREVIOUS_LIMIT:FIRST] == before[PREVIOUS_LIMIT:FIRST], "alignment gap retained")
    manifest = {
        "schema": 1, "kind": "character-damage-routing",
        "input_sha256": PREDECESSOR, "output_sha256": sha(after),
        "source_sha256": {"gba": GBA, "old": OLD, "source": NEW},
        "expected_writes": expected_writes, "declared_write_bytes": 64,
        "changed_bytes": sum(a != b for a, b in zip(before, after)),
        "full_inverse": True, "ownership": reservation,
        "source_old_table": proof["source_old_table"],
        "source_new_table": proof["source_new_table"],
        "native_old_table": proof["native_table"],
        "native_new_table": f"{BASE + FIRST:08X}..{BASE + LIMIT:08X}",
        "native_consumer": proof["native_consumer"],
        "native_literal": proof["native_literal"],
        "native_record": proof["native_record"],
        "callback_lineage": proof["callback_lineage"],
        "rows": [f"{value:08X}" for value in values],
        "retained_original_rows": 13, "added_ID_routes": [13, 14],
        "new_RAM_bytes": 0, "new_instructions": 0, "new_action_descriptors": 0,
        "runtime_claim": False, "provided_save_accessed": False,
    }
    return bytes(after), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("before", "gba", "old", "source", "output"):
        parser.add_argument(field, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    paths = [args.before, args.gba, args.old, args.source]
    need(all(path.suffix.lower() in (".gba", ".wsc") for path in paths), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json", "explicit artifact formats")
    need(args.output.resolve() not in [path.resolve() for path in paths], "output cannot overwrite an input ROM")
    result, report = build(*(path.read_bytes() for path in paths))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"[character-damage-routing] {sha(result)}; fifteen rows, 64 declared write bytes")


if __name__ == "__main__":
    main()
