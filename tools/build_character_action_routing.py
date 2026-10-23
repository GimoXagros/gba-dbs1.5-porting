#!/usr/bin/env python3
"""Install the fifteen-character source views for fourteen input action tables.

Adds only ROM pointer data and redirects existing literals. The source's flag
and action values select existing retail records through their actual readers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_character_action_routing import analyze, LITERALS, NATIVE_TABLE
from verify_character_followup_routing import BASE, GBA, OLD, NEW, need, sha, u32

PREDECESSOR = "3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C"
FIRST, LIMIT = 0x629000, 0x629348


def ownership(before: bytes) -> dict:
    need(before[FIRST:LIMIT] == b"\xff" * (LIMIT - FIRST), "action table reservation is all FF")
    for at in range(len(before) - 3):
        if before[at + 3] == 8:
            need(not BASE + FIRST <= u32(before, at) < BASE + LIMIT,
                 "no encoded pointer into action table reservation")
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
            immediate = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF if rotate else immediate
            target = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
            need(not FIRST <= target < LIMIT, "no ARM PC-relative address into reservation")
    return {"reservation": f"{FIRST:06X}..{LIMIT:06X}", "bytes": LIMIT - FIRST,
            "FF": True, "all_alignment_pointer_scan": True, "ARM_branch_literal_ADR_scan": True}


def build(before: bytes, gba: bytes, old: bytes, source: bytes):
    need(tuple(map(sha, (before, gba, old, source))) == (PREDECESSOR, GBA, OLD, NEW),
         "fixed predecessor and original ROM identities")
    need(len(before) == 0x800000, "candidate extent")
    proof = analyze(before, gba, old, source)
    reservation = ownership(before)
    after = bytearray(before)
    writes, routes = [], []
    for table in proof["input_tables"]:
        index = table["table_id"]
        target = FIRST + index * 60
        values = [int(entry["repair_record"], 16) for entry in table["entries"]]
        need(len(values) == 15, "complete source table")
        payload = struct.pack("<15I", *values)
        after[target:target + 60] = payload
        for site in LITERALS[index]:
            need(u32(before, site) == BASE + NATIVE_TABLE + index * 48, "actual native literal predecessor")
            after[site:site + 4] = struct.pack("<I", BASE + target)
            writes.append((site, 4))
        routes.append({"table_id": index, "source_table": table["source"],
                       "native_old_table": table["native"], "native_new_table": f"{BASE + target:08X}",
                       "literal_sites": [f"{site:06X}" for site in LITERALS[index]],
                       "records": [f"{value:08X}" for value in values]})
    writes.append((FIRST, LIMIT - FIRST))
    writes.sort()
    need(len(writes) == 16 and sum(size for _, size in writes) == 900, "fifteen literals and 840-byte payload only")
    inverse = bytearray(after)
    expected_writes = []
    for offset, size in writes:
        inverse[offset:offset + size] = before[offset:offset + size]
        expected_writes.append({"raw": f"{offset:06X}", "bytes": size,
                                "before_sha256": sha(before[offset:offset + size]),
                                "after_sha256": sha(after[offset:offset + size])})
    need(inverse == before, "full inverse of declared writes")
    need(after[NATIVE_TABLE:NATIVE_TABLE + 14 * 48] == before[NATIVE_TABLE:NATIVE_TABLE + 14 * 48],
         "all original table bytes retained")
    need(after[0x3553FC:0x35568C] == before[0x3553FC:0x35568C], "all reused descriptors and actual helper retained")
    preserved = 0
    for table in proof["input_tables"]:
        for entry in table["entries"][:12]:
            if entry["current_header_matches_source"]:
                need(entry["repair_record"] == entry["current_pointer"], "unchanged in-bounds pointer identity")
                preserved += 1
    need(preserved == 164, "164 original pointer identities retained")
    manifest = {
        "schema": 1, "kind": "character-action-routing", "input_sha256": PREDECESSOR,
        "output_sha256": sha(after), "expected_writes": expected_writes,
        "changed_bytes": sum(a != b for a, b in zip(before, after)), "ownership": reservation,
        "routes": routes, "source_rows": 210, "retail_oracle_rows": 168,
        "preserved_in_bounds_pointer_identities": preserved,
        "added_ID_routes": 42, "source_changed_ID11": proof["source_changes_existing_ID11"],
        "reused_record_classes": 28, "new_RAM_bytes": 0, "new_instructions": 0,
        "new_action_descriptors": 0, "runtime_claim": False, "provided_save_accessed": False,
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
    result, report = build(*(path.read_bytes() for path in paths))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[character-action-routing] {sha(result)}; 210 rows, 900 declared write bytes")


if __name__ == "__main__":
    main()
