#!/usr/bin/env python3
"""Install four source-backed fifteen-row hit and dependent follow-up views.

Seven native literals and four embedded follow-up pointers are redirected.
Variant8 still reaches its original contiguous native record population.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_character_hit_routing import analyze, SPECS, ALIASES
from verify_character_followup_routing import BASE, GBA, OLD, NEW, need, sha, u32

PREDECESSOR = "143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80"
PREVIOUS_LIMIT, FIRST, LIMIT = 0x62938C, 0x629390, 0x629480


def ownership(before: bytes) -> dict:
    need(FIRST == ((PREVIOUS_LIMIT + 15) & ~15), "next sixteen-byte aligned reservation")
    need(LIMIT - FIRST == 240 and LIMIT <= len(before), "exact in-bounds four-table reservation")
    need(before[PREVIOUS_LIMIT:LIMIT] == b"\xff" * (LIMIT - PREVIOUS_LIMIT),
         "new tables and preceding alignment gap are FF")
    for at in range(len(before) - 3):
        if before[at + 3] == 8:
            need(not BASE + FIRST <= u32(before, at) < BASE + LIMIT,
                 "no aligned, unaligned, or interior encoded inbound pointer")
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
            rotate, immediate = ((word >> 8) & 15) * 2, word & 255
            if rotate:
                immediate = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF
            target = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
            need(not FIRST <= target < LIMIT, "no ARM PC-relative address into reservation")
    for at in range(0, len(before) - 1, 2):
        word = struct.unpack_from("<H", before, at)[0]
        if word & 0xF800 == 0xA000:
            target = ((at + 4) & ~3) + (word & 255) * 4
            need(not FIRST <= target < LIMIT, "no Thumb PC-relative address into reservation")
    return {"reservation": f"{FIRST:06X}..{LIMIT:06X}", "bytes": LIMIT - FIRST,
            "previous_layer_end": f"{PREVIOUS_LIMIT:06X}", "FF": True,
            "all_alignment_interior_pointer_scan": True, "ARM_branch_literal_ADR_scan": True,
            "Thumb_ADR_scan": True}


def build(before: bytes, gba: bytes, old: bytes, source: bytes):
    inputs = (before, gba, old, source)
    need(tuple(map(sha, inputs)) == (PREDECESSOR, GBA, OLD, NEW), "pinned title predecessor and original ROMs")
    need(len(before) == 0x800000, "candidate extent")
    # Re-run source, actual reader, metadata, callback and P1 contracts on the
    # actual title predecessor; no earlier layer's hash or manifest substitutes.
    proof = analyze(*inputs)
    reservation = ownership(before)
    after, writes, routes = bytearray(before), [], []
    for index, table in enumerate(proof["tables"]):
        target = FIRST + index * 60
        values = [int(value, 16) for value in table["repair_rows"]]
        need(len(values) == 15 and values == [BASE + SPECS[index][3]] * 15,
             "complete source-prescribed row population")
        after[target:target + 60] = struct.pack("<15I", *values)
        for site in ALIASES[index]:
            need(u32(before, site) == BASE + SPECS[index][0], "actual old literal or metadata pointer")
            after[site:site + 4] = struct.pack("<I", BASE + target)
            writes.append((site, 4))
        routes.append({"index": index, "source_table": table["source"], "native_old_table": table["native"],
                       "native_new_table": f"{BASE + target:08X}", "rows": table["repair_rows"],
                       "redirects": [f"{site:06X}" for site in ALIASES[index]],
                       "kind": "embedded follow-up pointers" if index == 3 else "native literals"})
    writes.append((FIRST, LIMIT - FIRST)); writes.sort()
    need(len(writes) == 12 and sum(size for _, size in writes) == 284,
         "seven literals, four embedded words, and240 table bytes only")
    inverse, expected_writes = bytearray(after), []
    for offset, size in writes:
        inverse[offset:offset + size] = before[offset:offset + size]
        expected_writes.append({"raw": f"{offset:06X}", "bytes": size,
                                "before_sha256": sha(before[offset:offset + size]),
                                "after_sha256": sha(after[offset:offset + size])})
    need(inverse == before, "full inverse of declared writes")
    need(len(after) == len(before), "unchanged ROM extent")
    need(after[SPECS[0][0]:SPECS[-1][0] + 48] == before[SPECS[0][0]:SPECS[-1][0] + 48],
         "all four original twelve-row tables retained")
    restored_records = bytearray(after[0x36C32C:0x36C52C])
    for site in ALIASES[3]:
        restored_records[site - 0x36C32C:site - 0x36C32C + 4] = before[site:site + 4]
    need(restored_records == before[0x36C32C:0x36C52C], "all record bytes retained except four declared follow-up words")
    need(after[0x36AC20:0x36AF64] == before[0x36AC20:0x36AF64], "native callback and downstream consumer code retained")
    need(after[0x629000:PREVIOUS_LIMIT] == before[0x629000:PREVIOUS_LIMIT], "preceding action and recovery tables retained")
    need(after[PREVIOUS_LIMIT:FIRST] == before[PREVIOUS_LIMIT:FIRST], "alignment gap retained")
    # The original contiguous layout is essential: source variant8 crosses from
    # the first population into the third, including its now repaired dependency.
    need(u32(after, FIRST) + 8 * 32 == BASE + 0x36C42C, "variant8 original record identity")
    need(u32(after, 0x36C438) == BASE + FIRST + 180, "variant8 downstream pointer is repaired")
    manifest = {
        "schema": 1, "kind": "character-hit-routing", "input_sha256": PREDECESSOR,
        "output_sha256": sha(after), "source_sha256": {"gba": GBA, "old": OLD, "source": NEW},
        "expected_writes": expected_writes, "declared_write_bytes": 284,
        "changed_bytes": sum(a != b for a, b in zip(before, after)), "full_inverse": True,
        "ownership": reservation, "routes": routes, "source_rows": 60, "retail_oracle_rows": 48,
        "retail_record_populations": 4, "retail_action_records": 16,
        "canonical_P1_resources": proof["P1_population"]["canonical_resources"],
        "canonical_P1_events": proof["P1_population"]["events"],
        "source_variant8_events": proof["P1_population"]["source_unchanged_variant8_events"],
        "variant8_native_record": proof["variant8_native_record"],
        "predecessor_combat_contracts_rechecked": True, "predecessor_component_review_claim": False,
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
    inputs = [args.before, args.gba, args.old, args.source]
    need(all(path.suffix.lower() in (".gba", ".wsc") for path in inputs), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json", "explicit artifact formats")
    need(args.output.resolve() not in [path.resolve() for path in inputs], "output cannot overwrite an input ROM")
    result, report = build(*(path.read_bytes() for path in inputs))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_bytes((json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    print(f"[character-hit-routing] {sha(result)};60 rows,284 declared write bytes")


if __name__ == "__main__":
    main()
