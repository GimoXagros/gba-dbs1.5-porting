#!/usr/bin/env python3
"""Read-only source/native analysis of the short fighter action pointer tables.

The independent follow-up verifier supplies only its own source contracts;
neither this analyzer nor that verifier imports a builder or a manifest.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from verify_character_followup_routing import (
    BEFORE, GBA, OLD, NEW, BASE, need, sha, u32, refs, sequence, source_proof,
)

NATIVE_TABLE = 0x35515C
OLD_TABLE, OLD_CS = 0x3ADE08, 0x3ABDF0
NEW_TABLE, NEW_CS = 0x768B4E, 0x7668E0
LITERALS = (
    (0x355AB0,), (0x356B30, 0x356B34), (0x355990,), (0x355980,),
    (0x355988,), (0x355A58,), (0x355A50,), (0x355FEC,),
    (0x356B38,), (0x355994,), (0x355984,), (0x35598C,),
    (0x355A5C,), (0x355A54,),
)


def find_all(data, pattern):
    found, pos = [], 0
    while True:
        pos = data.find(pattern, pos)
        if pos < 0:
            return found
        found.append(pos)
        pos += 1


def source_loads(data, displacement):
    result = []
    for register, encoding in (("bx", "2e8b9f"), ("ax", "2e8b87")):
        pattern = bytes.fromhex(encoding) + struct.pack("<H", displacement)
        for at in find_all(data, pattern):
            sequence(data, at, at + 5,
                     [f"mov {register}, word ptr cs:[bx + 0x{displacement:x}]"])
            result.append({"raw": f"{at:06X}", "register": register})
    need(len(result) == 1, f"unique source action table reader {displacement:X}")
    return result


def literal_loads(data, literal):
    result = []
    for at in range(0x350000, 0x370000, 4):
        word = u32(data, at)
        if word & 0x0F7F0000 != 0x051F0000:
            continue
        offset = (word & 4095) * (1 if word & 0x800000 else -1)
        if at + 8 + offset == literal:
            need((word >> 12) & 15 == 8, "native table loaded into r8")
            result.append(f"{BASE + at:08X}")
    need(len(result) == 1, f"unique native literal reader {literal:X}")
    return result


def source_pointer(data, address):
    offset, segment, bank = struct.unpack_from("<3H", data, address)
    linear = segment * 16 + offset
    need(0x20000 <= linear < 0x30000, "source C2 pointer window")
    return (bank & 0x7F) * 0x10000 + linear - 0x20000


def action_population(source, current, ident, evolved, event):
    source_id = ident + (30 if evolved else 0)
    p4 = source_pointer(source, 0x740000 + source_id * 32 + 24)
    displacement, count = struct.unpack_from("<HH", source, p4)
    need(displacement == 4 and event < count, "source action index inside P4 population")
    group = 0x60B000 if evolved else 0x4A80F8
    native = u32(current, group + ident * 32 + 16) - BASE
    native_count = u32(current, native + 4)
    need(native_count == count, "actual native resource P4 count equals source")
    table = u32(current, native) - BASE
    record = u32(current, table + 4 * event)
    need(BASE <= record <= BASE + len(current) - 52, "native P4 record is in ROM")
    return {"source_P4": f"{p4:06X}", "native_P4": f"{BASE + native:08X}",
            "count": count, "native_action": f"{record:08X}"}


def analyze(current, gba, old, new):
    proof = source_proof(old, new, gba)
    need(current[0x35515C:0x35568C] == gba[0x35515C:0x35568C], "native action tables/helper are retail unchanged")
    sequence(current, 0x3555D0, 0x355610, [
        "push {r3, lr}", "ldrh r8, [r1]", "tst r8, #0x8000", "bne #0x8355684",
        "ldrh r8, [r1]", "tst r8, #1", "beq #0x8355604", "bl #0x8356190",
        "ldrh r8, [r1, #2]", "stmdb sp!, {r8}", "bl #0x8358264", "add sp, sp, #4",
        "b #0x8355684", "ldr r0, [r1, #4]", "str r0, [r4]", "stmdb sp!, {r5}",
    ], arm=True)
    sequence(current, 0x358264, 0x35827C, [
        "stmdb sp!, {lr}", "ldr r5, [r4, #0x78]", "ldr r5, [r5]",
        "ldr r8, [sp, #4]", "add r5, r5, r8, lsl #2", "ldr r5, [r5]",
    ], arm=True)
    reusable = {}
    for table_id in range(14):
        for ident in range(12):
            pointer = u32(current, NATIVE_TABLE + table_id * 48 + ident * 4)
            header = current[pointer - BASE:pointer - BASE + 4]
            reusable.setdefault(header, []).append(pointer)
    need(len(reusable) == 28, "28 native input action header classes")
    rows, changed_existing, legacy_count, population_count = [], [], 0, 0
    for table_id in range(14):
        native = NATIVE_TABLE + table_id * 48
        source_old = OLD_TABLE + table_id * 24
        source_new = NEW_TABLE + table_id * 30
        need(refs(current, BASE + native) == list(LITERALS[table_id]), "all aligned native table references")
        old_offsets = struct.unpack_from("<12H", old, source_old)
        new_offsets = struct.unpack_from("<15H", new, source_new)
        table = {"table_id": table_id, "native": f"{BASE + native:08X}",
                 "old": f"{source_old:06X}", "source": f"{source_new:06X}",
                 "native_rows": 12, "source_rows": 15, "native_readers": [],
                 "source_readers": source_loads(new, source_new - NEW_CS),
                 "old_readers": source_loads(old, source_old - OLD_CS), "entries": []}
        for literal in LITERALS[table_id]:
            table["native_readers"].append({"literal": f"{BASE + literal:08X}",
                                           "instructions": literal_loads(current, literal),
                                           "overwritten_preload": literal == 0x356B30})
        for ident in range(15):
            source_record = NEW_CS + new_offsets[ident]
            header = new[source_record:source_record + 4]
            flags, event = struct.unpack("<HH", header)
            need(flags in (0, 1), "input action record format")
            native_pointer = u32(current, native + ident * 4)
            native_raw = native_pointer - BASE
            in_rom = 0 <= native_raw <= len(current) - 4
            native_header = current[native_raw:native_raw + 4] if in_rom else b""
            entry = {"id": ident, "source_record": f"{source_record:06X}", "flags": flags,
                     "action": event, "current_pointer": f"{native_pointer:08X}",
                     "current_header": native_header.hex().upper(),
                     "current_header_matches_source": native_header == header,
                     "out_of_native_table": ident >= 12}
            need(header in reusable, "source action has existing native semantic record")
            # Keep an existing in-bounds row's identity if its source action is
            # unchanged. Added/changed rows can use the lowest retail address
            # whose consumed flag/action header is identical.
            repair_pointer = native_pointer if ident < 12 and native_header == header else min(reusable[header])
            entry["repair_record"] = f"{repair_pointer:08X}"
            if ident < 12:
                old_record = OLD_CS + old_offsets[ident]
                need(old[old_record:old_record + 4] == native_header, "all 168 original action headers match retail")
                legacy_count += 1
                if header != native_header:
                    changed_existing.append({"table_id": table_id, "id": ident,
                                             "old_event": struct.unpack("<HH", native_header)[1], "new_event": event})
            if flags == 0:
                need(header == bytes.fromhex("00000200"), "shared native animation action")
                old_reference = OLD_CS + struct.unpack_from("<H", old, OLD_TABLE + 7 * 24)[0]
                need(new[source_record + 8:source_record + 32] == old[old_reference + 8:old_reference + 32],
                     "shared animation action metadata retained")
                need(repair_pointer == 0x083553FC, "shared animation record lineage")
            elif ident >= 12 or (ident == 11 and table_id >= 8):
                entry["resource_population"] = action_population(new, current, ident, table_id >= 8, event)
                population_count += 1
            table["entries"].append(entry)
        rows.append(table)
    need(changed_existing == [
        {"table_id": 8, "id": 11, "old_event": 2, "new_event": 1},
        {"table_id": 10, "id": 11, "old_event": 6, "new_event": 4},
        {"table_id": 12, "id": 11, "old_event": 4, "new_event": 2},
        {"table_id": 13, "id": 11, "old_event": 4, "new_event": 7},
    ], "exact four source changes in existing ID11 evolution input rows")
    need(u32(current, 0x3553CC + 14 * 4) == 0, "last input table ID14 null overread")
    need(u32(current, 0x36A62C + 14 * 4) == 0x063C0000, "observed follow-up ID14 invalid pointer")
    return {"status": "ANALYZED", "scope": "14 input action tables and one observed follow-up failure",
            "input_tables": rows, "retail_header_oracle_rows": legacy_count,
            "source_input_rows": 14 * 15, "added_ID_routes": 14 * 3,
            "checked_new_resource_routes": population_count, "source_changes_existing_ID11": changed_existing,
            "reusable_native_record_classes": 28,
            "added_ID_header_mismatches": sum(not e["current_header_matches_source"] for t in rows for e in t["entries"][12:]),
            "followup": proof,
            "followup_failure_chain": ["P1 +9C=0836A62C", "ID14 indexes 0836A664",
                                       "word 063C0000 is action data outside the 12-row table",
                                       "08355604 loads zero callback at 063C0004",
                                       "08355608 writes zero to02011710", "083525C4 dispatches the state callback"],
            "repair_boundaries": [
                "Follow-up repair relocates only fifteen identical native record pointers and its metadata producer.",
                "Initial 0836A5FC table has one literal reference and its actual consumer reads row zero only.",
                "Input tables need fourteen 15-row views and all fifteen literal redirects; all source actions reuse existing native records.",
                "The literal load at08356B00 is overwritten by08356B04; the other fourteen table loads feed actual indexed consumers.",
                "Four existing ID11 evolution input actions also change in WSC1.5.",
                "This analysis does not prove every other damage/character callback table is complete.",
            ], "emulator_executed": False, "save_accessed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("current", "gba", "old", "new", "output"):
        parser.add_argument(field, type=Path)
    args = parser.parse_args()
    paths = [args.current, args.gba, args.old, args.new]
    need(all(p.suffix.lower() in (".gba", ".wsc") for p in paths), "explicit ROM inputs only")
    data = [p.read_bytes() for p in paths]
    need(tuple(map(sha, data)) == (BEFORE, GBA, OLD, NEW), "four pinned input identities")
    report = analyze(*data)
    report["input_sha256"] = dict(zip(("current", "gba", "old", "new"), map(sha, data)))
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"ANALYZED: 14 input tables, 168 retail oracle rows; report {sha(encoded)}")


if __name__ == "__main__":
    main()
