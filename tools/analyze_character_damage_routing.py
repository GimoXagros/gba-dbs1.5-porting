#!/usr/bin/env python3
"""Read-only proof of the thirteen-row native recovery table at0836BFF8.

This is a bounded analysis, not a ROM builder or a full damage-state audit.
No emulator, save files, builder imports, or external manifests are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from verify_character_followup_routing import BASE, GBA, OLD, NEW, need, sha, u32, refs, sequence

CURRENT = "F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0"
TABLE, SITE, RECORD, CALLBACK = 0x36BFF8, 0x36B23C, 0x0836C56C, 0x0836BA90


def analyze(current, gba, old, source):
    need(struct.unpack_from("<13I", gba, TABLE) == (RECORD,) * 13, "thirteen retail native recovery rows")
    need(current[TABLE:TABLE + 52] == gba[TABLE:TABLE + 52], "current table remains retail")
    need(struct.unpack_from("<13H", old, 0x3A6EB4) == (0x2E5E,) * 13, "thirteen original source rows")
    need(struct.unpack_from("<15H", source, 0x76313A) == (0x3848,) * 15, "fifteen new source rows")
    need(0x3A6EB4 + 13 * 2 == 0x3A6ECE and 0x76313A + 15 * 2 == 0x763158, "exact source table boundaries")
    need(old[0x3A6ECE:0x3A6ED2] == source[0x763158:0x76315C] == bytes.fromhex("00001500"), "next data record begins after table")
    need(gba[0x36C02C:0x36C030] == bytes.fromhex("00001500"), "next native data record boundary")
    need(0x3A45B0 + 0x2E5E == 0x3A740E and 0x75FFD0 + 0x3848 == 0x763818, "source CS-relative records resolve")
    a, b = old[0x3A740E:0x3A742E], source[0x763818:0x763838]
    need(a[:4] == b[:4] == bytes.fromhex("00004300"), "source flag0 event43")
    need(a[8:] == b[8:] == bytes.fromhex("0c0008000000000000000000800080fe1000000000000000"), "all consumed source metadata unchanged")
    need(struct.unpack_from("<HH", a, 4) == (0x1974, 0xA45B), "old callback far pointer")
    need(struct.unpack_from("<HH", b, 4) == (0x2134, 0x5FFD), "new callback far pointer")
    need(0x3A45B0 + 0x1974 == 0x3A5F24 and 0x75FFD0 + 0x2134 == 0x762104, "source callbacks resolve")
    prefix_old, prefix_new = old[0x3A5F24:0x3A5F71], source[0x762104:0x762151]
    need(prefix_old == prefix_new and sha(prefix_new) == "334404E3B6E770988D57432A1BE0C339D406420B2FE403A9F0D873D8F809C68F", "77 identical constructor bytes")
    sequence(source, 0x762104, 0x762151, [
        "mov byte ptr [si + 0x5a], 0xb", "cmp word ptr [si + 0x7e], 0", "je 0x762119",
        "or word ptr [si + 8], 1", "mov ax, word ptr [si + 0x7e]", "mov byte ptr [si + 0x5b], al",
        "mov byte ptr [si + 0x5f], al", "mov ax, word ptr [si + 0x8a]",
        "and word ptr [di + 8], 0xbfff", "test word ptr [si + 0xc], 0x4000", "jne 0x762135",
        "neg ax", "neg bx", "or word ptr [di + 8], 0x4000", "mov word ptr [si + 0x32], ax",
        "mov word ptr [si + 0x36], 0", "mov ax, word ptr [si + 0x8c]", "mov bx, word ptr [si + 0x8e]",
        "mov word ptr [si + 0x34], ax", "mov word ptr [si + 0x38], bx", "mov word ptr [si + 0x88], 0xa",
    ])
    tail = [
        "mov al, {bank}", "out 0xc2, al", "mov ax, {physics}", "mov es, ax",
        "mov bx, word ptr [si + 0x4e]", "mov ax, word ptr es:[bx + 2]", "mov word ptr [si + 0x8a], ax",
        "mov bx, word ptr [di + 0x12]", "shl bx, 5", "mov ax, 0xff0", "mov es, ax", "mov cx, 0xf",
        "add bx, 2", "mov word ptr es:[bx], 0xfff", "add bx, 2", "loop {loop}",
        "or word ptr [si + 8], 0x400", "mov word ptr [si], {next}", "mov word ptr [si + 2], {segment}",
    ]
    sequence(old, 0x3A5F71, 0x3A5FAE, [text.format(bank="0xea", physics="0x2264", loop="0x3a5f96",
             next="0x19fe", segment="0xa45b") for text in tail])
    sequence(source, 0x762151, 0x76218E, [text.format(bank="0xbb", physics="0x2846", loop="0x762176",
             next="0x21be", segment="0x5ffd") for text in tail])
    native_record = gba[0x36C56C:0x36C58C]
    need(native_record == bytes.fromhex("0000430090ba360809000600000000000000a00020fe19000000000000000000"), "native retail converted record oracle")
    need(u32(gba, 0x36C570) == CALLBACK, "native callback pointer")
    for start, end in [(0x36C56C, 0x36C58C), (0x36BA90, 0x36BB60), (0x36B0BC, 0x36B0D4),
                       (0x355604, 0x355684), (0x36F3B8, 0x36F3E8)]:
        need(current[start:end] == gba[start:end], f"retained native contract {start:X}")
    need(sha(gba[0x36BA90:0x36BB60]) == "4EBFD162FC8EC78CFA9358684C324A097E22BC91EA85E8F6DF299A75AF8A59D0", "native recovery constructor pin")
    sequence(current, 0x36B0BC, 0x36B0D4, [
        "ldrb r1, [r4, #0x11]", "ldr r8, [pc, #0x174]", "ldr r1, [r8, r1, lsl #2]",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
    ], arm=True)
    need(0x36B0C0 + 8 + 0x174 == SITE and u32(current, SITE) == BASE + TABLE, "exact active recovery literal")
    need(refs(current, BASE + TABLE) == [SITE], "one aligned encoded recovery table reference")
    for data, start, end, displacement, segment in [
        (old, 0x3A58FE, 0x3A5913, 0x2904, 0xABDF),
        (source, 0x7614BA, 0x7614CF, 0x316A, 0x668E),
        (source, 0x761ADE, 0x761AF3, 0x316A, 0x668E),
    ]:
        sequence(data, start, end, [
            "xor bx, bx", "mov bl, byte ptr [si + 0x11]", "shl bx, 1",
            f"mov bx, word ptr cs:[bx + 0x{displacement:x}]", "push cs",
            f"lcall 0x{segment:x}, 0", "add sp, 2",
        ])
    # The generic damage call is a different consumer: these three preceding
    # selectors reach it, but none supplies the BFF8 recovery table.
    adjacent = []
    for load, literal, table in [(0x36ECEC, 0x36F7C0, 0x0836BF08),
                                  (0x36ED38, 0x36F7C8, 0x0836BF38),
                                  (0x36ED90, 0x36F7D4, 0x0836BF68)]:
        need(u32(current, literal) == table, "adjacent generic table literal")
        instruction = u32(current, load)
        need(load + 8 + (instruction & 4095) == literal, "adjacent literal reader")
        sequence(current, load + 4, load + 8, ["b #0x836f3b8"], arm=True)
        adjacent.append({"selector": f"{BASE + load:08X}", "literal": f"{BASE + literal:08X}",
                         "table": f"{table:08X}", "scope": "separate table; source mapping not claimed here"})
    sequence(current, 0x36F3B8, 0x36F3E8, [
        "ldrb r0, [r5, #0x11]", "ldr r1, [r1, r0, lsl #2]", "ldr r8, [pc, #0x480]",
        "ldrb r0, [r8, #6]", "add r1, r1, r0, lsl #5", "stmdb sp!, {r4}",
        "mov r4, r5", "add r5, r5, #0xac", "stmdb sp!, {fp}", "bl #0x83555d0",
        "add sp, sp, #4", "sub r5, r5, #0xac",
    ], arm=True)
    observed = [u32(current, TABLE + ident * 4) for ident in range(15)]
    need(observed[13:] == [0x00150000, 0x0836C58C], "two invalid added-ID record pointers")
    return {
        "status": "PROVED", "scope": "recovery view at0836BFF8 only",
        "source_old_table": "3A6EB4..3A6ECE", "source_old_rows": 13,
        "source_new_table": "76313A..763158", "source_new_rows": 15,
        "native_table": "0836BFF8..0836C02C", "native_rows": 13,
        "source_old_record": "3A740E", "source_new_record": "763818", "native_record": "0836C56C",
        "callback_lineage": {"old": "3A5F24", "new": "762104", "native": "0836BA90",
                             "identical_prefix_bytes": 77, "relocation_checked_tail_bytes": 61,
                             "full_callback_service_equivalence": False},
        "source_consumers": ["3A58FE..3A5913", "7614BA..7614CF", "761ADE..761AF3"],
        "native_consumer": "0836B0BC..0836B0D4", "native_literal": "0836B23C",
        "record_fields": {"flags": 0, "event": 67, "native_callback": "0836BA90",
                          "source_timers": [12, 8], "retail_native_timers": [9, 6],
                          "source_motion": [128, -384, 16], "retail_native_motion": [160, -480, 25]},
        "existing_ID13_record_pointer": "00150000", "existing_ID14_record_pointer": "0836C58C",
        "minimal_proposal": {"new_table_bytes": 60, "rows": ["0836C56C"] * 15,
                             "redirect_literal_raw": "36B23C", "preserve_old_table": True,
                             "new_RAM": 0, "new_instructions": 0, "new_action_records": 0,
                             "allocation": "not assigned; no repair built"},
        "adjacent_generic_call": {"consumer": "0836F3DC", "selected_tables": adjacent,
                                  "not_a_BFF8_consumer": True},
        "runtime": "not executed; no capture of this failure is claimed",
    }


def negatives(current, gba, old, source):
    tested = []
    for index, at, label in [(0, TABLE + 48, "wrong native ID12"), (0, SITE, "wrong native literal"),
                             (0, 0x36B0C4, "wrong native index"), (0, 0x36C570, "wrong native callback"),
                             (2, 0x3A6EB4 + 24, "old thirteenth row lost"),
                             (3, 0x76313A + 28, "wrong source ID14"),
                             (3, 0x763818 + 4, "wrong source far callback"),
                             (3, 0x762104, "changed source callback constructor")]:
        variants = [current, gba, old, source]
        changed = bytearray(variants[index]); changed[at] ^= 1; variants[index] = bytes(changed)
        try:
            analyze(*variants)
        except ValueError:
            tested.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    return tested


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("current", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    paths = [args.current, args.gba, args.old, args.source]
    need(all(p.suffix.lower() in (".gba", ".wsc") for p in paths), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".json", "analysis output must be JSON")
    data = [p.read_bytes() for p in paths]
    need(tuple(map(sha, data)) == (CURRENT, GBA, OLD, NEW), "pinned source/native input identities")
    report = analyze(*data)
    report["negative_tests"] = negatives(*data)
    report["input_sha256"] = dict(zip(("current", "gba", "old", "source"), map(sha, data)))
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"PROVED: thirteen-to-fifteen recovery table; 8 negatives; report {sha(encoded)}")


if __name__ == "__main__":
    main()
