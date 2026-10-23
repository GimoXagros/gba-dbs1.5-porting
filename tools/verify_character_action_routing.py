#!/usr/bin/env python3
"""Independently verify all fourteen source-backed input-action table views.

Only the five explicit ROM inputs are read. No producer, generated manifest,
emulator, save, or service implementation supplies the expected table bytes.
The report is deterministic and deliberately separates routing from runtime.
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

BEFORE = "3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C"
AFTER = "F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, TABLE, END = 0x08000000, 0x629000, 0x629348
RETAIL, OLD_TABLE, NEW_TABLE = 0x35515C, 0x3ADE08, 0x768B4E
OLD_CS, NEW_CS = 0x3ABDF0, 0x7668E0
LITERALS = (
    (0x355AB0,), (0x356B30, 0x356B34), (0x355990,), (0x355980,),
    (0x355988,), (0x355A58,), (0x355A50,), (0x355FEC,),
    (0x356B38,), (0x355994,), (0x355984,), (0x35598C,),
    (0x355A5C,), (0x355A54,),
)
READERS = (
    (0x355A90,), (0x356B00, 0x356B0C), (0x355950,), (0x3558FC,),
    (0x35592C,), (0x355A20,), (0x3559FC,), (0x355F80,),
    (0x356B10,), (0x35595C,), (0x355908,), (0x355938,),
    (0x355A2C,), (0x355A08,),
)
SOURCE_READERS = (
    (0x3AC14A, 0x766C3A), (0x3AD482, 0x767F8A),
    (0x3AC08F, 0x766B7F), (0x3AC05A, 0x766B4A),
    (0x3AC078, 0x766B68), (0x3AC107, 0x766BF7),
    (0x3AC0F0, 0x766BE0), (0x3AC44F, 0x766F3F),
    (0x3AD48E, 0x767F96), (0x3AC097, 0x766B87),
    (0x3AC062, 0x766B52), (0x3AC080, 0x766B70),
    (0x3AC10F, 0x766BFF), (0x3AC0F8, 0x766BE8),
)
CHANGED = ((8, 11, 2, 1), (10, 11, 6, 4), (12, 11, 4, 2), (13, 11, 4, 7))


def need(value, label):
    if not value:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "ROM extent")
    return bytes(data[at:at + size])


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def ptr(data, at, size=1):
    result = u(data, at) - BASE
    cut(data, result, size)
    return result


def positions(data, pattern):
    result, at = [], 0
    while True:
        at = data.find(pattern, at)
        if at < 0:
            return result
        result.append(at)
        at += 1


def sequence(data, start, end, expected, arm=False):
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    decoded = list(decoder.disasm(cut(data, start, end - start), start + (BASE if arm else 0)))
    need(sum(x.size for x in decoded) == end - start, f"instruction extent {start:X}")
    actual = [f"{x.mnemonic} {x.op_str}".strip() for x in decoded]
    need(actual == expected, f"instruction contract {start:X}")


def source_p4(source, ident, evolved):
    offset, segment, bank = struct.unpack("<3H", cut(source, 0x740000 + (ident + 30 * evolved) * 32 + 24, 6))
    physical = segment * 16 + offset
    need(0x20000 <= physical < 0x30000 and 0x80 <= bank <= 0xFF, "source P4 banked pointer")
    at = (bank & 0x7F) * 0x10000 + physical - 0x20000
    count = h(source, at + 2)
    need(h(source, at) == 4 and 0 < count <= 128, "source P4 header")
    offsets = tuple(h(source, at + 4 + i * 2) for i in range(count))
    need(offsets == tuple(4 + count * 2 + i * 36 for i in range(count)), "source P4 complete record population")
    cut(source, at, offsets[-1] + 36)
    return at, offsets


def common_callback(gba, old, new):
    """Establish the flag-zero record beyond its four-byte dispatch header."""
    old_record = OLD_CS + h(old, OLD_TABLE + 7 * 24)
    new_record = NEW_CS + h(new, NEW_TABLE + 7 * 30)
    need((old_record, new_record) == (0x3ADF58, 0x768CF2), "common source record addresses")
    need(cut(old, old_record, 4) == cut(new, new_record, 4) == bytes.fromhex("00000200"), "common source header")
    need(struct.unpack("<HH", cut(old, old_record + 4, 4)) == (0x1312, 0xABDF), "old callback far pointer")
    need(struct.unpack("<HH", cut(new, new_record + 4, 4)) == (0x132A, 0x668E), "new callback far pointer")
    need(OLD_CS + 0x1312 == 0x3AD102 and NEW_CS + 0x132A == 0x767C0A, "callback far pointers resolve")
    need(cut(old, old_record + 8, 24) == cut(new, new_record + 8, 24) == bytes(24), "all consumed source metadata")
    need(cut(gba, 0x3553FC, 32) == bytes.fromhex("000002005C653508") + bytes(24), "whole native common record and consumed metadata")

    # Source constructor ends at the first continuation, before shared service
    # calls. Its only changes are the physics table and relocated state pointer.
    a, b = cut(old, 0x3AD102, 80), cut(new, 0x767C0A, 80)
    need(sha(a) == "447ACBF2042BFC5E81755C41DAFA2E7D414636FD7A73A8CFB8BCA51DF4B26A50", "old constructor pin")
    need(sha(b) == "158D953815465A1CD316629E9A2288BACB5E0CA80F0C347E42BC6122E81953DD", "new constructor pin")
    normalized = bytearray(b)
    for at, size, previous, current in ((0x14, 1, 0xEA, 0xBB), (0x18, 2, 0x2264, 0x2846),
                                       (0x49, 2, 0x1362, 0x137A), (0x4E, 2, 0xABDF, 0x668E)):
        need(int.from_bytes(a[at:at + size], "little") == previous and
             int.from_bytes(b[at:at + size], "little") == current, "explicit constructor relocation")
        normalized[at:at + size] = a[at:at + size]
    need(bytes(normalized) == a, "constructor identity outside four relocations")
    sequence(new, 0x767C0A, 0x767C5A, [
        "mov byte ptr [si + 0x5a], 2", "mov word ptr [si + 0x34], 0", "mov word ptr [si + 0x36], 0",
        "mov word ptr [si + 0x38], 0", "mov al, 0xbb", "out 0xc2, al", "mov ax, 0x2846", "mov es, ax",
        "mov bx, word ptr [si + 0x4e]", "mov ax, word ptr es:[bx + 0xa]", "test word ptr [si + 0x8a], 2",
        "jne 0x767c37", "neg ax", "mov word ptr [si + 0x32], ax", "mov word ptr [si + 0x7e], 0x11",
        "or word ptr [di + 8], 0x4000", "test word ptr [si + 0x8a], 2", "jne 0x767c51",
        "and word ptr [di + 8], 0xbfff", "mov word ptr [si], 0x137a", "mov word ptr [si + 2], 0x668e",
    ])
    sequence(gba, 0x35655C, 0x3565D0, [
        "stmdb sp!, {lr}", "mov sb, #2", "strb sb, [r4, #0x6e]", "mov sb, #0",
        "strh sb, [r4, #0x44]", "strh sb, [r4, #0x46]", "strh sb, [r4, #0x48]",
        "ldr r1, [r4, #0x60]", "ldrsh r0, [r1, #0xa]", "ldrh r8, [r4, #0xa0]", "tst r8, #2",
        "rsbeq r0, r0, #0", "strh r0, [r4, #0x42]", "mov sb, #0xd", "strh sb, [r4, #0x94]",
        "ldrh r8, [r5, #8]", "orr r8, r8, #0x4000", "strh r8, [r5, #8]",
        "ldrh r8, [r4, #0xa0]", "tst r8, #2", "bne #0x83565bc", "ldrh r8, [r5, #8]",
        "bic r8, r8, #0x4000", "strh r8, [r5, #8]", "add r8, pc, #0xc", "str r8, [r4]",
        "bl #0x83565d0", "ldm sp!, {lr}", "bx lr",
    ], arm=True)

    # Bank and six-byte-entry format are independently documented in
    # analyze_shoot_audio_lineage.py. Compare payloads, not shifted IDs.
    sounds = []
    for old_id, new_id, digest in (
        (0x83, 0x85, "5FD15C9F1D84C8A7E0147DE356AE76BC43916BB04E41EBA7115DF4E9DD8E167E"),
        (0x84, 0x86, "C0C71C302F6B877D63012B61B76E057B624A60064DD7BB7FA5722418BE909D49"),
    ):
        entries, payloads = [], []
        for source, bank, ident in ((old, 0x2D0000, old_id), (new, 0x3F0000, new_id)):
            entry = struct.unpack("<3H", cut(source, bank + ident * 6, 6))
            end = h(source, bank + (ident + 1) * 6 + 4)
            need(0x400 <= entry[2] < end <= 0xFFFF, "bounded source sound payload")
            entries.append(entry[:2]); payloads.append(cut(source, bank + entry[2], end - entry[2]))
        need(entries[0] == entries[1] and payloads[0] == payloads[1] and sha(payloads[0]) == digest, "shifted continuation sound identity")
        sounds.append({"old_id": old_id, "new_id": new_id, "payload_bytes": len(payloads[0]), "payload_sha256": digest})
    sequence(gba, 0x356750, 0x35677C, [
        "ldrh r8, [r4, #8]", "tst r8, #0x4000", "moveq r8, #0x29", "moveq sb, #1", "moveq sl, #0",
        "movne r8, #0x2a", "movne sb, #1", "movne sl, #0", "ldrh fp, [r4, #6]", "tst fp, #0x1000", "blne #0x80d15c0",
    ], arm=True)
    for source, first, second, first_id in ((old, 0x3AD227, 0x3AD237, 0x83), (new, 0x767D2F, 0x767D3F, 0x85)):
        sequence(source, first, first + 3, [f"mov ax, 0x{first_id:x}"])
        sequence(source, second, second + 3, [f"mov ax, 0x{first_id + 1:x}"])
    return {"old_record": "3ADF58", "source_record": "768CF2", "native_record": "083553FC",
            "old_callback": "3AD102", "source_callback": "767C0A", "native_callback": "0835655C",
            "source_constructor_bytes": 80, "native_constructor_bytes": 116,
            "source_continuation": "767C5A", "native_continuation": "083565D0",
            "consumed_metadata_bytes": 24, "consumed_metadata": "all zero, including unused trailing padding",
            "physics_tables": ["2A2640", "3B8460"], "source_timer": 17, "retail_native_timer": 13,
            "continuation_sounds": sounds,
            "limit": "Constructor, complete consumed record, and shifted sound payload lineage; not full callback/service behavioral parity."}


def source_contract(gba, old, new):
    need(len(gba) == len(old) == 0x400000 and len(new) == 0x800000, "original ROM sizes")
    common = common_callback(gba, old, new)
    representatives = {}
    for table in range(14):
        for ident in range(12):
            pointer = u(gba, RETAIL + table * 48 + ident * 4)
            header = cut(gba, pointer - BASE, 4)
            representatives.setdefault(header, set()).add(pointer)
    need(len(representatives) == 28, "28 independent native header classes")
    expected, rows, changes, readers = [], [], [], []
    for table in range(14):
        register = "ax" if table in (1, 8) else "bx"
        for version, source, source_table, source_cs, stride in (
            (0, old, OLD_TABLE, OLD_CS, 24), (1, new, NEW_TABLE, NEW_CS, 30),
        ):
            displacement = source_table + table * stride - source_cs
            encoding = bytes.fromhex("2e8b87" if register == "ax" else "2e8b9f") + struct.pack("<H", displacement)
            sites = positions(source, encoding)
            need(sites == [SOURCE_READERS[table][version]], f"all source table aliases {version}/{table}")
            sequence(source, sites[0], sites[0] + 5, [f"mov {register}, word ptr cs:[bx + 0x{displacement:x}]"])
        readers.append({"table": table, "old": f"{SOURCE_READERS[table][0]:06X}", "source": f"{SOURCE_READERS[table][1]:06X}"})
        for ident in range(15):
            source_record = NEW_CS + h(new, NEW_TABLE + table * 30 + ident * 2)
            header = cut(new, source_record, 4)
            flags, event = struct.unpack("<HH", header)
            need(flags in (0, 1) and header in representatives, f"source action has native semantic record {table}/{ident}")
            if flags == 0:
                need(source_record == 0x768CF2 and header == bytes.fromhex("00000200"), "all flag-zero rows share proved complete record")
            previous = None
            if ident < 12:
                previous = u(gba, RETAIL + table * 48 + ident * 4)
                old_record = OLD_CS + h(old, OLD_TABLE + table * 24 + ident * 2)
                old_header = cut(old, old_record, 4)
                need(cut(gba, previous - BASE, 4) == old_header, f"retail oracle row {table}/{ident}")
                if old_header != header:
                    changes.append((table, ident, h(old, old_record + 2), event))
            pointer = previous if previous is not None and cut(gba, previous - BASE, 4) == header else min(representatives[header])
            expected.append(pointer)
            rows.append({"table": table, "id": ident, "source_record": f"{source_record:06X}",
                         "flags": flags, "action": event, "native_record": f"{pointer:08X}",
                         "preserved_pointer": previous == pointer if previous is not None else False})
    need(tuple(changes) == CHANGED, "exact four existing ID11 evolution changes")
    need(sum(r["preserved_pointer"] for r in rows) == 164, "all 164 unchanged original pointer identities retained")
    for at in (0x766B35, 0x766BCB, 0x766C33, 0x766F38, 0x767F83):
        sequence(new, at, at + 7, ["xor bx, bx", "mov bl, byte ptr [si + 0x11]", "shl bx, 1"])
    return {"expected": expected, "rows": rows, "source_readers": readers,
            "common_record_lineage": common, "changed_existing_rows": changes}


def native_contract(before, after, gba):
    # This region includes original tables, records, all fifteen literal loads,
    # their indexed consumers, and the common native callback. Only literals move.
    need(cut(before, RETAIL, 0x356B3C - RETAIL) == cut(gba, RETAIL, 0x356B3C - RETAIL), "predecessor native action region is retail")
    restored = bytearray(cut(after, RETAIL, 0x356B3C - RETAIL))
    for group in LITERALS:
        for site in group:
            restored[site - RETAIL:site - RETAIL + 4] = cut(gba, site, 4)
    need(restored == cut(gba, RETAIL, 0x356B3C - RETAIL), "all native records/instructions retained outside literals")
    need(cut(after, 0x358264, 0x3C) == cut(before, 0x358264, 0x3C) == cut(gba, 0x358264, 0x3C), "native P4 dispatcher retained")
    sequence(after, 0x3555D0, 0x355610, [
        "push {r3, lr}", "ldrh r8, [r1]", "tst r8, #0x8000", "bne #0x8355684",
        "ldrh r8, [r1]", "tst r8, #1", "beq #0x8355604", "bl #0x8356190",
        "ldrh r8, [r1, #2]", "stmdb sp!, {r8}", "bl #0x8358264", "add sp, sp, #4",
        "b #0x8355684", "ldr r0, [r1, #4]", "str r0, [r4]", "stmdb sp!, {r5}",
    ], arm=True)
    sequence(after, 0x358264, 0x35827C, [
        "stmdb sp!, {lr}", "ldr r5, [r4, #0x78]", "ldr r5, [r5]", "ldr r8, [sp, #4]",
        "add r5, r5, r8, lsl #2", "ldr r5, [r5]",
    ], arm=True)
    for at in (0x3558E0, 0x3559E0, 0x355A8C, 0x355F7C, 0x356AFC):
        sequence(after, at, at + 4, ["ldrb r1, [r4, #0x11]"], arm=True)
    sequence(after, 0x356AFC, 0x356B24, [
        "ldrb r1, [r4, #0x11]", "ldr r8, [pc, #0x28]", "ldrh r8, [r4, #8]", "tst r8, #0x4000",
        "ldreq r8, [pc, #0x20]", "ldrne r8, [pc, #0x20]", "ldr r1, [r8, r1, lsl #2]",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
    ], arm=True)
    for table, sites in enumerate(READERS):
        for at in sites:
            if at in (0x356B00, 0x356B0C, 0x356B10):
                continue
            sequence(after, at + 4, at + 8, ["ldr r1, [r8, r1, lsl #2]"], arm=True)


def aliases(data, installed):
    base_table, stride = (TABLE, 60) if installed else (RETAIL, 48)
    expected = sorted((site, BASE + base_table + table * stride)
                      for table, sites in enumerate(LITERALS) for site in sites)
    found = []
    for at in range(len(data) - 3):
        if data[at + 3] == 8:
            pointer = struct.unpack_from("<I", data, at)[0]
            if BASE + base_table <= pointer < BASE + base_table + 14 * stride:
                found.append((at, pointer))
    need(found == expected, "all alignments and interior table-pointer aliases")
    decoded_loads = {}
    for at in range(0x350000, 0x370000, 4):
        word = u(data, at)
        if word >> 28 != 15 and word & 0x0F7F0000 == 0x051F0000:
            target = at + 8 + (word & 4095) * (1 if word & 0x800000 else -1)
            decoded_loads.setdefault(target, []).append((at, (word >> 12) & 15))
    result = []
    for table, sites in enumerate(LITERALS):
        pointer = BASE + base_table + table * stride
        need(positions(data, struct.pack("<I", pointer)) == list(sites), f"all literal aliases for table {table}")
        for site, reader in zip(sites, READERS[table], strict=True):
            need(decoded_loads.get(site) == [(reader, 8)], f"actual unique r8 literal reader {site:X}")
            result.append({"table": table, "literal": f"{BASE + site:08X}", "reader": f"{BASE + reader:08X}",
                           "overwritten_preload": reader == 0x356B00})
    return result


def reservation(before):
    need(cut(before, TABLE, END - TABLE) == b"\xff" * (END - TABLE), "reservation entirely FF")
    # All byte-aligned pointer encodings and aligned ARM branch/literal encodings.
    # This is conservative static evidence, not a whole-program indirect proof.
    for at in range(len(before) - 3):
        if before[at + 3] == 8:
            pointer = struct.unpack_from("<I", before, at)[0]
            need(not BASE + TABLE <= pointer < BASE + END, "predecessor encoded inbound reservation pointer")
    for at in range(0, len(before) - 3, 4):
        word = struct.unpack_from("<I", before, at)[0]
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 1 << 24
            need(not TABLE <= at + 8 + displacement * 4 < END, "predecessor ARM branch into reservation")
        if word & 0x0E1F0000 == 0x041F0000:
            delta = (word & 4095) * (1 if word & 0x800000 else -1)
            need(not TABLE <= at + 8 + delta < END, "predecessor ARM PC-relative access into reservation")


def p4_routes(after, source, rows):
    cache, checked = {}, []
    for row in rows:
        if row["flags"] == 0:
            continue
        ident, evolved, event = row["id"], row["table"] >= 8, row["action"]
        key = (ident, evolved)
        if key not in cache:
            source_at, offsets = source_p4(source, ident, evolved)
            count = len(offsets)
            group = 0x60B000 if evolved else 0x4A80F8
            native_at = ptr(after, group + ident * 32 + 16, 8)
            need(u(after, native_at + 4) == count, f"actual same-ID P4 population {ident}/{evolved}")
            table = ptr(after, native_at, count * 4)
            need(table == native_at + 8, "actual native P4 list follows header")
            targets = [ptr(after, table + i * 4, 52) for i in range(count)]
            need(targets == [table + count * 4 + i * 52 for i in range(count)], "actual native P4 record boundaries")
            cache[key] = source_at, offsets, native_at, targets
        source_at, offsets, native_at, targets = cache[key]
        need(0 <= event < len(offsets), f"action index bounded by actual P4 population {row['table']}/{ident}")
        need(h(after, targets[event] + 4) == h(source, source_at + offsets[event] + 4), "same source/native P4 animation event")
        checked.append({"table": row["table"], "id": ident, "action": event,
                        "source_P4": f"{source_at:06X}", "native_P4": f"{BASE + native_at:08X}",
                        "population": len(offsets), "native_action": f"{BASE + targets[event]:08X}"})
    need(len(checked) == 197 and len(cache) == 30, "all flag-one rows and thirty resource populations")
    return checked


def expected_image(before, proof):
    result = bytearray(before)
    result[TABLE:END] = struct.pack("<210I", *proof["expected"])
    for table, sites in enumerate(LITERALS):
        for site in sites:
            struct.pack_into("<I", result, site, BASE + TABLE + table * 60)
    return bytes(result)


def candidate_check(before, after, gba, source, proof):
    need(len(before) == len(after) == 0x800000, "candidate size")
    need(after == expected_image(before, proof), "exact source-derived 840-byte tables and fifteen literals; no other writes")
    native_contract(before, after, gba)
    consumers = aliases(after, True)
    for table, sites in enumerate(LITERALS):
        for site in sites:
            target = ptr(after, site, 60)
            need(target == TABLE + table * 60, "actual table base and full fifteen-row extent")
            for ident in range(15):
                observed = u(after, target + ident * 4)
                row = proof["rows"][table * 15 + ident]
                need(observed == int(row["native_record"], 16), "actual routed record identity")
                need(cut(after, observed - BASE, 4) == struct.pack("<HH", row["flags"], row["action"]), "actual routed flag/action")
    populations = p4_routes(after, source, proof["rows"])
    inverse = bytearray(after)
    inverse[TABLE:END] = before[TABLE:END]
    for group in LITERALS:
        for site in group:
            inverse[site:site + 4] = before[site:site + 4]
    need(inverse == before, "full inverse preserves predecessor")
    return consumers, populations


def negative_tests(before, after, gba, old, source, proof):
    failures = []

    def reject(label, operation):
        try:
            operation()
        except ValueError:
            failures.append(label)
        else:
            raise ValueError("negative accepted: " + label)

    # Every installed row and every alias must be independently covered.
    for index in range(210):
        bad = bytearray(after)
        struct.pack_into("<I", bad, TABLE + index * 4, 0x083553FC if proof["expected"][index] != 0x083553FC else 0x0835541C)
        reject(f"wrong installed table {index // 15} row {index % 15}", lambda: candidate_check(before, bad, gba, source, proof))
    for group in LITERALS:
        for site in group:
            bad = bytearray(after); struct.pack_into("<I", bad, site, BASE + RETAIL)
            reject(f"unredirected/wrong literal {site:06X}", lambda: candidate_check(before, bad, gba, source, proof))
    for at, label in ((TABLE - 1, "preceding padding"), (END, "following padding"), (0x100, "unrelated byte"),
                      (RETAIL, "original table"), (0x355400, "common callback pointer"),
                      (0x355404, "common metadata"), (0x355608, "callback writer"),
                      (0x35655C, "common constructor"), (0x358274, "P4 dispatcher")):
        bad = bytearray(after); bad[at] ^= 1
        reject(label, lambda: candidate_check(before, bad, gba, source, proof))
    reject("truncated candidate", lambda: candidate_check(before, after[:-1], gba, source, proof))
    # Re-run source derivation to avoid negatives that merely hit the file hash.
    source_sites = [(NEW_TABLE + table * 30 + ident * 2, f"source table {table} row {ident}")
                    for table in range(14) for ident in range(12, 15)]
    source_sites += [(NEW_TABLE + table * 30 + 22, f"existing ID11 source table {table}") for table, _, _, _ in CHANGED]
    source_sites += [(0x768CF6, "source common callback pointer"), (0x768CFA, "source common consumed metadata"),
                     (0x767C0A, "source common constructor"), (0x767C53, "source continuation relocation")]
    source_sites += [(site[1], f"source reader {i}") for i, site in enumerate(SOURCE_READERS)]
    for at, label in source_sites:
        bad = bytearray(source); bad[at] ^= 0x80
        def bad_source():
            changed = source_contract(gba, old, bad)
            candidate_check(before, after, gba, bad, changed)
        reject(label, bad_source)
    # Explicitly test a consumed native metadata byte and each population check,
    # even when a corrupted predecessor and candidate share the same bad data.
    for evolved, group in ((False, 0x4A80F8), (True, 0x60B000)):
        for ident in range(15):
            bad = bytearray(after); native = ptr(after, group + ident * 32 + 16, 8)
            struct.pack_into("<I", bad, native + 4, 0)
            reject(f"P4 population ID{ident} evolved={evolved}", lambda: p4_routes(bad, source, proof["rows"]))
    rows = [dict(row) for row in proof["rows"]]
    rows[0]["action"] = 65535
    reject("out-of-population action index", lambda: p4_routes(after, source, rows))
    bad = bytearray(before); bad[TABLE] = 0
    reject("occupied predecessor reservation", lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, 0x101, BASE + TABLE + 17)
    reject("unaligned predecessor inbound pointer", lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, TABLE - 0x100, 0xEA000000 | ((0x100 - 8) // 4))
    reject("predecessor ARM branch into reservation", lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, TABLE - 0x100, 0xE59F00F8)
    reject("predecessor ARM literal access into reservation", lambda: reservation(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, 0x100, BASE + RETAIL)
    reject("unaccounted old-table alias", lambda: aliases(bad, False))
    bad = bytearray(before); struct.pack_into("<I", bad, 0x101, BASE + RETAIL + 4)
    reject("unaligned old-table interior alias", lambda: aliases(bad, False))
    bad = bytearray(after); struct.pack_into("<I", bad, 0x101, BASE + TABLE + 4)
    reject("unaligned new-table interior alias", lambda: aliases(bad, True))
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("before", "after", "gba", "old", "new", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    paths = [args.before, args.after, args.gba, args.old, args.new]
    need(all(p.suffix.lower() in (".gba", ".wsc") for p in paths), "explicit ROM inputs only")
    before, after, gba, old, new = [p.read_bytes() for p in paths]
    need(tuple(map(sha, (before, after, gba, old, new))) == (BEFORE, AFTER, GBA, OLD, NEW), "five pinned input SHA-256 identities")
    proof = source_contract(gba, old, new)
    reservation(before)
    aliases(before, False)
    consumers, populations = candidate_check(before, after, gba, new, proof)
    failures = negative_tests(before, after, gba, old, new, proof)
    spans = [{"raw": f"{site:06X}", "bytes": 4} for group in LITERALS for site in group]
    spans.append({"raw": f"{TABLE:06X}", "bytes": END - TABLE})
    report = {"status": "PASS", "kind": "independent-character-input-action-routing",
              "input_sha256": dict(zip(("before", "after", "gba", "old", "new"), map(sha, (before, after, gba, old, new)))),
              "native_tables": 14, "retail_oracle_rows": 168, "source_rows": 210, "added_rows": 42,
              "preserved_existing_rows": 164, "changed_existing_rows": proof["changed_existing_rows"],
              "native_semantic_record_classes": 28, "source_readers": proof["source_readers"], "native_consumers": consumers,
              "effective_native_reads": 14, "conservative_overwritten_preloads": 1,
              "rows": proof["rows"], "P4_checked_rows": populations, "common_record_lineage": proof["common_record_lineage"],
              "write_spans": spans, "written_bytes": 900, "changed_bytes": sum(x != y for x, y in zip(before, after)),
              "full_inverse": True, "negative_count": len(failures), "negative_tests": failures,
              "emulator_executed": False, "save_accessed": False, "new_instructions": 0, "new_ram_bytes": 0,
              "limits": ["Proves these fourteen data-only input table routes and actual consumers, not every character callback table.",
                         "Source common constructor and full consumed record are proved; whole shared callback/service parity is not claimed.",
                         "Runtime state transitions, battle stability, and whole-game completion require separate verification."]}
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"PASS: 210 source routes, 197 P4 indices, {len(failures)} negatives; report {sha(encoded)}")


if __name__ == "__main__":
    main()
