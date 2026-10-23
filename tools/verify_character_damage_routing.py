#!/usr/bin/env python3
"""Independent source/retail proof of the 13-to-15 recovery-table repair.

Reads five explicit ROMs only, without builders, analyzers, manifests, emulator
execution or save access. Expected bytes are derived from source rows and the
retail record. The deterministic report describes this bounded routing layer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BEFORE = "F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0"
AFTER = "A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, SITE, RETAIL = 0x08000000, 0x36B23C, 0x36BFF8
TABLE, END, GUARD_START, GUARD_END = 0x629350, 0x62938C, 0x629348, 0x629390
RECORD, CALLBACK = 0x0836C56C, 0x0836BA90
OLD_CS, NEW_CS = 0x3A45B0, 0x75FFD0


def need(value, label):
    if not value:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "ROM extent")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def find_all(data, pattern):
    found, at = [], 0
    while True:
        at = data.find(pattern, at)
        if at < 0:
            return found
        found.append(at)
        at += 1


def sequence(data, start, end, expected, arm=False):
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    decoded = list(decoder.disasm(cut(data, start, end - start), start + (BASE if arm else 0)))
    need(sum(row.size for row in decoded) == end - start, f"instruction extent {start:X}")
    need([f"{row.mnemonic} {row.op_str}".strip() for row in decoded] == expected, f"instruction contract {start:X}")


def source_contract(gba, old, source):
    need(len(gba) == len(old) == 0x400000 and len(source) == 0x800000, "original sizes")
    original = struct.unpack("<13H", cut(old, 0x3A6EB4, 26))
    expanded = struct.unpack("<15H", cut(source, 0x76313A, 30))
    need(original == (0x2E5E,) * 13 and expanded == (0x3848,) * 15, "complete old/new source rows")
    need(struct.unpack("<13I", cut(gba, RETAIL, 52)) == (RECORD,) * 13, "all thirteen retail oracle rows")
    need(cut(old, 0x3A6ECE, 4) == cut(source, 0x763158, 4) == cut(gba, 0x36C02C, 4) == bytes.fromhex("00001500"), "independent adjacent-record boundaries")
    old_record, new_record = OLD_CS + original[0], NEW_CS + expanded[0]
    need((old_record, new_record) == (0x3A740E, 0x763818), "source records resolve through actual CS bases")
    a, b, native = cut(old, old_record, 32), cut(source, new_record, 32), cut(gba, RECORD - BASE, 32)
    need(a[:4] == b[:4] == bytes.fromhex("00004300"), "source flag-zero animation 43")
    need(a[8:] == b[8:] == bytes.fromhex("0c0008000000000000000000800080fe1000000000000000"), "all twelve source metadata words")
    need(struct.unpack("<HH", a[4:8]) == (0x1974, 0xA45B), "old far callback identity")
    need(struct.unpack("<HH", b[4:8]) == (0x2134, 0x5FFD), "new far callback identity")
    need(OLD_CS + 0x1974 == 0x3A5F24 and NEW_CS + 0x2134 == 0x762104, "far callbacks resolve")
    need(native == bytes.fromhex("0000430090ba360809000600000000000000a00020fe19000000000000000000"), "whole converted native retail record")

    # Source stores twelve 16-bit metadata words. The retail native record uses
    # narrower counters and a native pointer, then six signed motion words.
    # Establish actual values without inventing a universal scalar conversion.
    source_words = struct.unpack("<12h", b[8:])
    native_fields = (struct.unpack_from("<h", native, 8)[0], native[10], native[11],
                     u(native, 12), native[16], native[17], *struct.unpack_from("<6h", native, 18))
    need(source_words == (12, 8, 0, 0, 0, 0, 128, -384, 16, 0, 0, 0), "source metadata field values")
    need(native_fields == (9, 6, 0, 0, 0, 0, 160, -480, 25, 0, 0, 0), "native consumed metadata field values")
    need(native[30:32] == bytes(2), "native record trailing padding")
    need(cut(old, 0x3A5F24, 77) == cut(source, 0x762104, 77) and
         sha(cut(source, 0x762104, 77)) == "334404E3B6E770988D57432A1BE0C339D406420B2FE403A9F0D873D8F809C68F", "identical constructor prefix")
    sequence(source, 0x762104, 0x762151, [
        "mov byte ptr [si + 0x5a], 0xb", "cmp word ptr [si + 0x7e], 0", "je 0x762119",
        "or word ptr [si + 8], 1", "mov ax, word ptr [si + 0x7e]", "mov byte ptr [si + 0x5b], al",
        "mov byte ptr [si + 0x5f], al", "mov ax, word ptr [si + 0x8a]", "and word ptr [di + 8], 0xbfff",
        "test word ptr [si + 0xc], 0x4000", "jne 0x762135", "neg ax", "neg bx", "or word ptr [di + 8], 0x4000",
        "mov word ptr [si + 0x32], ax", "mov word ptr [si + 0x36], 0", "mov ax, word ptr [si + 0x8c]",
        "mov bx, word ptr [si + 0x8e]", "mov word ptr [si + 0x34], ax", "mov word ptr [si + 0x38], bx",
        "mov word ptr [si + 0x88], 0xa",
    ])
    tail = [
        "mov al, {bank}", "out 0xc2, al", "mov ax, {physics}", "mov es, ax",
        "mov bx, word ptr [si + 0x4e]", "mov ax, word ptr es:[bx + 2]", "mov word ptr [si + 0x8a], ax",
        "mov bx, word ptr [di + 0x12]", "shl bx, 5", "mov ax, 0xff0", "mov es, ax", "mov cx, 0xf",
        "add bx, 2", "mov word ptr es:[bx], 0xfff", "add bx, 2", "loop {loop}",
        "or word ptr [si + 8], 0x400", "mov word ptr [si], {next}", "mov word ptr [si + 2], {segment}",
    ]
    for data, start, settings in (
        (old, 0x3A5F71, dict(bank="0xea", physics="0x2264", loop="0x3a5f96", next="0x19fe", segment="0xa45b")),
        (source, 0x762151, dict(bank="0xbb", physics="0x2846", loop="0x762176", next="0x21be", segment="0x5ffd")),
    ):
        sequence(data, start, start + 61, [item.format(**settings) for item in tail])
    need(OLD_CS + 0x19FE == 0x3A5FAE and NEW_CS + 0x21BE == 0x76218E, "source continuation targets")

    consumers = []
    for data, starts, displacement, segment in (
        (old, (0x3A58FE,), 0x2904, 0xABDF),
        (source, (0x7614BA, 0x761ADE), 0x316A, 0x668E),
    ):
        encoding = bytes.fromhex("2e8b9f") + struct.pack("<H", displacement)
        need(find_all(data, encoding) == [at + 7 for at in starts], "all encoded source table readers")
        for at in starts:
            sequence(data, at, at + 21, [
                "xor bx, bx", "mov bl, byte ptr [si + 0x11]", "shl bx, 1",
                f"mov bx, word ptr cs:[bx + 0x{displacement:x}]", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2",
            ])
            consumers.append(f"{at:06X}")
    return {"source_rows": len(expanded), "old_rows": len(original), "retail_rows": 13,
            "source_records": ["3A740E", "763818"], "native_record": f"{RECORD:08X}",
            "source_callbacks": ["3A5F24", "762104"], "native_callback": f"{CALLBACK:08X}",
            "source_consumers": consumers, "source_metadata_words": source_words, "native_metadata_fields": native_fields,
            "identical_source_constructor_bytes": 77, "explicit_source_relocation_bytes": 61,
            "source_continuations": ["3A5FAE", "76218E"], "native_continuation": "0836BB6C"}


def native_contract(data, gba):
    for start, end in ((RETAIL, RETAIL + 60), (RECORD - BASE, RECORD - BASE + 32),
                       (0x36B070, 0x36B0D4), (0x36BA90, 0x36BB6C),
                       (0x3555D0, 0x35568C), (0x36F3B8, 0x36F3E8)):
        need(cut(data, start, end - start) == cut(gba, start, end - start), f"unchanged retail native contract {start:X}")
    sequence(data, 0x36B0BC, 0x36B0D4, [
        "ldrb r1, [r4, #0x11]", "ldr r8, [pc, #0x174]", "ldr r1, [r8, r1, lsl #2]",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
    ], arm=True)
    need(0x36B0C0 + 8 + 0x174 == SITE, "actual active literal address")
    loads = []
    for at in range((SITE - 4104) & ~3, SITE + 4096, 4):
        word = u(data, at)
        if word >> 28 != 15 and word & 0x0F7F0000 == 0x051F0000:
            target = at + 8 + (word & 4095) * (1 if word & 0x800000 else -1)
            if target == SITE:
                loads.append((at, (word >> 12) & 15))
    need(loads == [(0x36B0C0, 8)], "all possible native PC-relative literal readers")
    sequence(data, 0x355604, 0x355644, [
        "ldr r0, [r1, #4]", "str r0, [r4]", "stmdb sp!, {r5}", "stmdb sp!, {fp}",
        "ldrh r8, [r1, #2]", "stmdb sp!, {r8}", "bl #0x8012874", "add sp, sp, #0xc",
        "ldrsh r0, [r1, #8]", "ldrsb r3, [r1, #0xa]", "strh r0, [r4, #0x94]", "strh r3, [r4, #0x96]",
        "ldrsb r0, [r1, #0xb]", "ldr r3, [r1, #0xc]", "strh r0, [r4, #0x98]", "str r3, [r4, #0x9c]",
    ], arm=True)
    sequence(data, 0x36BA90, 0x36BB64, [
        "stmdb sp!, {lr}", "mov sb, #0xb", "strb sb, [r4, #0x6e]", "ldrsh r8, [r4, #0x94]",
        "cmp r8, #0", "beq #0x836babc", "ldrh r8, [r4, #8]", "orr r8, r8, #1", "strh r8, [r4, #8]",
        "ldrsh r0, [r4, #0x94]", "strb r0, [r4, #0x6f]", "strb r0, [r4, #0x73]", "ldrsh r0, [r4, #0xa0]",
        "ldrh r8, [r5, #8]", "bic r8, r8, #0x4000", "strh r8, [r5, #8]", "ldrh r8, [r4, #0xc]",
        "tst r8, #0x4000", "bne #0x836baf0", "rsb r0, r0, #0", "rsb r1, r1, #0",
        "ldrh r8, [r5, #8]", "orr r8, r8, #0x4000", "strh r8, [r5, #8]", "strh r0, [r4, #0x42]",
        "mov sb, #0", "strh sb, [r4, #0x46]", "ldrsh r0, [r4, #0xa2]", "ldrsh r1, [r4, #0xa4]",
        "strh r0, [r4, #0x44]", "strh r1, [r4, #0x48]", "mov sb, #8", "strb sb, [r4, #0x9b]",
        "ldr r1, [r4, #0x60]", "ldrsh r0, [r1, #2]", "strh r0, [r4, #0xa0]", "ldrh r1, [r5, #0x10]",
        "lsl r1, r1, #5", "mov r2, #0xf", "ldr r8, [pc, #0x30]", "add r1, r1, r8", "ldr r8, [pc, #0x2c]",
        "strh r8, [r1], #2", "subs r2, r2, #1", "bgt #0x836bb38", "ldrh r8, [r4, #8]",
        "orr r8, r8, #0x400", "strh r8, [r4, #8]", "add r8, pc, #0x14", "str r8, [r4]",
        "bl #0x836bb6c", "ldm sp!, {lr}", "bx lr",
    ], arm=True)
    need((u(data, 0x36BB64), u(data, 0x36BB68)) == (0x05000202, 0x7FFF), "native palette base and converted white")
    # These nearby selectors belong to another dispatcher. Preserve them rather
    # than pretending the recovery table covers the entire damage family.
    for load, literal, table in ((0x36ECEC, 0x36F7C0, 0x0836BF08),
                                 (0x36ED38, 0x36F7C8, 0x0836BF38), (0x36ED90, 0x36F7D4, 0x0836BF68)):
        need(cut(data, load, 8) == cut(gba, load, 8) and u(data, literal) == u(gba, literal) == table, "separate generic selector unchanged")
        need(load + 8 + (u(data, load) & 4095) == literal, "separate generic literal resolves")
        sequence(data, load + 4, load + 8, ["b #0x836f3b8"], arm=True)


def aliases(data, table, rows, expected):
    found = []
    for at in range(len(data) - 3):
        if data[at + 3] == 8:
            target = struct.unpack_from("<I", data, at)[0]
            if BASE + table <= target < BASE + table + rows * 4:
                found.append((at, target))
    need(found == expected, "all aligned/unaligned/interior encoded table aliases")


def reservation(data):
    need(cut(data, GUARD_START, GUARD_END - GUARD_START) == b"\xff" * (GUARD_END - GUARD_START), "new table and guard padding unoccupied")
    for at in range(len(data) - 3):
        if data[at + 3] == 8:
            pointer = struct.unpack_from("<I", data, at)[0]
            need(not BASE + GUARD_START <= pointer < BASE + GUARD_END, "encoded inbound pointer")
    for at in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, at)[0]
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 1 << 24
            need(not GUARD_START <= at + 8 + displacement * 4 < GUARD_END, "ARM inbound branch")
        if word & 0x0E1F0000 == 0x041F0000:
            delta = (word & 4095) * (1 if word & 0x800000 else -1)
            need(not GUARD_START <= at + 8 + delta < GUARD_END, "ARM inbound PC-relative access")
        if word & 0x0E1F0000 == 0x020F0000 and (word >> 21) & 15 in (2, 4):
            immediate, rotate = word & 255, ((word >> 8) & 15) * 2
            value = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF if rotate else immediate
            target = at + 8 + (value if (word >> 21) & 15 == 4 else -value)
            need(not GUARD_START <= target < GUARD_END, "ARM inbound ADR")
    for at in range(0, len(data) - 1, 2):
        word = struct.unpack_from("<H", data, at)[0]
        if word & 0xF800 == 0xA000:
            need(not GUARD_START <= ((at + 4) & ~3) + (word & 255) * 4 < GUARD_END, "Thumb inbound ADR")


def check(before, after, gba, old, source):
    need(len(before) == len(after) == 0x800000, "candidate size")
    proof = source_contract(gba, old, source)
    expected = bytearray(before)
    struct.pack_into("<I", expected, SITE, BASE + TABLE)
    expected[TABLE:END] = struct.pack("<15I", *([RECORD] * proof["source_rows"]))
    need(after == expected, "exact source-backed table and one literal; no other writes")
    need(u(before, SITE) == BASE + RETAIL, "predecessor recovery literal")
    native_contract(before, gba)
    native_contract(after, gba)
    need(u(before, RETAIL + 13 * 4) == 0x00150000 and u(before, RETAIL + 14 * 4) == 0x0836C58C, "actual two old overreads")
    rows = []
    for ident in range(15):
        pointer = u(after, u(after, SITE) - BASE + ident * 4)
        need(pointer == RECORD and u(after, pointer - BASE + 4) == CALLBACK, f"actual ID{ident} record/callback route")
        rows.append({"id": ident, "record": f"{pointer:08X}", "callback": f"{CALLBACK:08X}"})
    inverse = bytearray(after)
    inverse[SITE:SITE + 4] = before[SITE:SITE + 4]
    inverse[TABLE:END] = before[TABLE:END]
    need(inverse == before, "full inverse")
    proof["routes"] = rows
    return proof


def negatives(before, after, gba, old, source):
    results = []

    def reject(label, run):
        try:
            run()
        except ValueError:
            results.append(label)
        else:
            raise ValueError("negative accepted: " + label)

    for ident in range(15):
        bad = bytearray(after); struct.pack_into("<I", bad, TABLE + 4 * ident, 0x0836C58C)
        reject(f"wrong installed row {ident}", lambda: check(before, bad, gba, old, source))
    for at, label in ((SITE, "wrong literal"), (TABLE - 1, "preceding guard write"), (END, "following guard write"),
                      (0x100, "unrelated byte"), (RETAIL, "original table"), (0x36C570, "record callback"),
                      (0x36C574, "record timer"), (0x36B0C4, "ID stride"), (0x36BA90, "native constructor"),
                      (0x36BB64, "palette literal"), (0x36F7C0, "separate damage table")):
        bad = bytearray(after); bad[at] ^= 1
        reject(label, lambda: check(before, bad, gba, old, source))
    reject("truncated candidate", lambda: check(before, after[:-1], gba, old, source))
    for ident in range(13):
        bad = bytearray(old); bad[0x3A6EB4 + 2 * ident] ^= 1
        reject(f"old oracle source row {ident}", lambda: source_contract(gba, bad, source))
    for ident in range(15):
        bad = bytearray(source); bad[0x76313A + 2 * ident] ^= 1
        reject(f"new source row {ident}", lambda: source_contract(gba, old, bad))
    for at, label in ((0x763158, "new source table boundary"), (0x76381C, "new source callback offset"),
                      (0x76381E, "new source callback segment"), (0x762104, "source constructor"),
                      (0x762151, "source physics-bank relocation"), (0x762176, "source palette loop"),
                      (0x7614C1, "first source reader"), (0x761AE5, "second source reader")):
        bad = bytearray(source); bad[at] ^= 1
        reject(label, lambda: source_contract(gba, old, bad))
    for field in range(12):
        bad = bytearray(source); bad[0x763820 + 2 * field] ^= 1
        reject(f"source consumed metadata word {field}", lambda: source_contract(gba, old, bad))
    for at, label in ((0x36B0BC, "native ID source"), (0x355608, "native callback writer"),
                      (0x36C578, "native compressed metadata"), (0x36BB18, "native physics field")):
        bad = bytearray(after); bad[at] ^= 1
        reject(label, lambda: native_contract(bad, gba))
    bad = bytearray(before); bad[TABLE] = 0
    reject("occupied reservation", lambda: reservation(bad))
    for at, label in ((0x100, "aligned inbound pointer"), (0x101, "unaligned inbound pointer")):
        bad = bytearray(before); struct.pack_into("<I", bad, at, BASE + TABLE + 4)
        reject(label, lambda: reservation(bad))
    for word, label in ((0xEA00003E, "ARM branch inbound"), (0xE59F00F8, "ARM literal inbound"),
                        (0xE28F00F8, "ARM ADR inbound")):
        bad = bytearray(before); struct.pack_into("<I", bad, TABLE - 0x100, word)
        reject(label, lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<H", bad, TABLE - 0x100, 0xA03F)
    reject("Thumb ADR inbound", lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, 0x101, BASE + RETAIL + 4)
    reject("hidden old interior alias", lambda: aliases(bad, RETAIL, 13, [(SITE, BASE + RETAIL)]))
    bad = bytearray(after); struct.pack_into("<I", bad, 0x101, BASE + TABLE + 4)
    reject("hidden new interior alias", lambda: aliases(bad, TABLE, 15, [(SITE, BASE + TABLE)]))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("before", "after", "gba", "old", "new", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    paths = [args.before, args.after, args.gba, args.old, args.new]
    need(all(path.suffix.lower() in (".gba", ".wsc") for path in paths) and args.output.suffix.lower() == ".json", "explicit ROM inputs and JSON output")
    before, after, gba, old, source = [path.read_bytes() for path in paths]
    need(tuple(map(sha, (before, after, gba, old, source))) == (BEFORE, AFTER, GBA, OLD, NEW), "five pinned ROM identities")
    proof = check(before, after, gba, old, source)
    reservation(before)
    aliases(before, RETAIL, 13, [(SITE, BASE + RETAIL)])
    aliases(after, TABLE, 15, [(SITE, BASE + TABLE)])
    aliases(after, RETAIL, 13, [])
    tests = negatives(before, after, gba, old, source)
    proof.update({"status": "PASS", "kind": "independent-character-recovery-routing",
                  "input_sha256": dict(zip(("before", "after", "gba", "old", "new"), map(sha, (before, after, gba, old, source)))),
                  "write_spans": [{"raw": f"{SITE:06X}", "bytes": 4}, {"raw": f"{TABLE:06X}", "bytes": 60}],
                  "written_bytes": 64, "changed_bytes": sum(a != b for a, b in zip(before, after)),
                  "full_inverse": True, "all_table_aliases_checked": True,
                  "reservation_checks": ["FF plus 8-byte leading and 4-byte trailing guards", "all-alignment encoded pointers",
                                         "ARM branches/PC-relative accesses/ADR", "Thumb ADR"],
                  "negative_count": len(tests), "negative_tests": tests, "new_instructions": 0, "new_RAM_bytes": 0,
                  "new_action_records": 0, "emulator_executed": False, "save_accessed": False,
                  "limits": ["Only the native 0836BFF8 recovery view is repaired; adjacent generic damage tables are preserved.",
                             "Both source readers are proved, but only the existing native consumer is rerouted.",
                             "Constructor/consumed-record lineage is proved; full callback and service equivalence is not claimed.",
                             "Runtime recovery behavior and battle stability require separate observation."]})
    encoded = (json.dumps(proof, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"PASS: 15 recovery routes, {len(tests)} negatives; report {sha(encoded)}")


if __name__ == "__main__":
    main()
