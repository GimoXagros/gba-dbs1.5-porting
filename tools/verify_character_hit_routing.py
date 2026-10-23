#!/usr/bin/env python3
"""Independent four-view hit-routing proof against explicit source/retail ROMs.

No builder, analyzer, generated manifest, target execution or save supplies
expected data. This checks the descriptor graph, consumed selector population,
actual reader instructions, source relocation lineage and exact data-only edits.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BEFORE = "143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80"
AFTER = "A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, TABLE, END = 0x08000000, 0x629390, 0x629480
OLD_CS, NEW_CS = 0x3A45B0, 0x75FFD0
NATIVE_TABLE, OLD_TABLE, NEW_TABLE = 0x36BF08, 0x3A6E3C, 0x76304A
NATIVE_RECORD, OLD_RECORD, NEW_RECORD = 0x36C32C, 0x3A71CE, 0x763458
SITES = ((0x36B238, 0x36F7C0, 0x36FCE0), (0x36F7C8, 0x378838),
         (0x354C84, 0x36F7D4), (0x36C438, 0x36C458, 0x36C478, 0x36C498))
READERS = ((0x36B04C, 0x36ECEC, 0x36FC44), (0x36ED38, 0x3787EC), (0x354B00, 0x36ED90))
GROUPS = (0x4A80F8, 0x4A82D8, 0x60B000, 0x60B1E0)
EXISTING_SELECTOR_EDITS = ((0, 91, 1, 0), (3, 91, 1, 0), (3, 96, 1, 0), (3, 98, 1, 0),
                           (5, 109, 1, 0), (7, 109, 1, 0), (10, 109, 1, 0), (32, 28, 0, 1))


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded ROM extent")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def ptr(data, at, size=1):
    value = u(data, at) - BASE
    cut(data, value, size)
    return value


def far(data, at):
    offset, segment, bank = struct.unpack("<3H", cut(data, at, 6))
    physical = segment * 16 + offset
    need(0x20000 <= physical < 0x30000 and 0x80 <= bank <= 255, "source banked resource address")
    return (bank & (len(data) // 65536 - 1)) * 65536 + physical - 0x20000


def sequence(data, at, end, expected, arm=False):
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    decoded = list(decoder.disasm(cut(data, at, end - at), at + (BASE if arm else 0)))
    actual = [f"{i.mnemonic} {i.op_str}".strip() for i in decoded]
    need(sum(i.size for i in decoded) == end - at and actual == expected, f"actual instruction contract {at:X}")


def native_fields(record):
    return (struct.unpack_from("<h", record, 8)[0], *struct.unpack_from("<bb", record, 10),
            u(record, 12), record[16], record[17], *struct.unpack_from("<6h", record, 18))


def source_records(gba, old, new):
    need(len(gba) == len(old) == 0x400000 and len(new) == 0x800000, "original ROM sizes")
    oracle = cut(gba, NATIVE_RECORD, 512)
    need(sha(oracle) == "05BC2738F672102357E8D054D112EF23F41B73A2B5B982209EABB6A8477F064C", "complete sixteen-record retail oracle")
    rows, records = [], []
    for group in range(4):
        ot, nt, gt = OLD_TABLE + 24 * group, NEW_TABLE + 30 * group, NATIVE_TABLE + 48 * group
        orec, nrec, grec = OLD_RECORD + 128 * group, NEW_RECORD + 128 * group, NATIVE_RECORD + 128 * group
        old_rows, new_rows = struct.unpack("<12H", cut(old, ot, 24)), struct.unpack("<15H", cut(new, nt, 30))
        original_rows = struct.unpack("<12I", cut(gba, gt, 48))
        need(all(value + OLD_CS == orec for value in old_rows), "all twelve original source row identities")
        need(all(value + NEW_CS == nrec for value in new_rows), "all fifteen new source row identities")
        need(original_rows == (BASE + grec,) * 12, "twelve paired native oracle pointers")
        need(h(old, ot + 24) != old_rows[0] and h(new, nt + 30) != new_rows[0] and u(gba, gt + 48) != original_rows[0], "distinct following tables establish exact boundaries")
        rows.append(dict(group=group, old_table=ot, source_table=nt, original_native_table=gt,
                         new_native_table=TABLE + 60 * group, record=BASE + grec, added_ids=[12, 13, 14]))
        for variant in range(4):
            a = cut(old, orec + variant * 32, 32)
            b = cut(new, nrec + variant * 32, 32)
            c = cut(gba, grec + variant * 32, 32)
            need(a[:4] == b[:4] == c[:4] and h(b, 0) == 0, "every source/native flag-zero event identity")
            old_cb, new_cb, native_cb = ((0x1062, 0x11FE, 0x36AC20) if group == 2 else (0x11EF, 0x138B, 0x36AE94))
            need(struct.unpack_from("<HH", a, 4) == (old_cb, 0xA45B) and struct.unpack_from("<HH", b, 4) == (new_cb, 0x5FFD), "explicit callback far-pointer relocation")
            need(u(c, 4) == BASE + native_cb, "paired native callback identity")
            if group == 2:
                need(a[8:14] == b[8:14] and a[16:] == b[16:], "all nonpointer source metadata words")
                need(h(a, 14) + OLD_CS == OLD_TABLE + 72 and h(b, 14) + NEW_CS == NEW_TABLE + 90, "source follow-up pointer resolves fourth table")
                need(u(c, 12) == BASE + NATIVE_TABLE + 144, "retail descriptor follow-up pointer")
            else:
                need(a[8:] == b[8:], "all twelve consumed source metadata words unchanged")
            need(c[30:] == bytes(2), "native descriptor trailing padding")
            records.append(dict(group=group, variant=variant, native=BASE + grec + variant * 32,
                old=orec + variant * 32, source=nrec + variant * 32, event=h(b, 2),
                source_callback=NEW_CS + new_cb, old_callback=OLD_CS + old_cb, native_callback=BASE + native_cb,
                source_metadata=list(struct.unpack_from("<12h", b, 8)), native_retail_metadata=list(native_fields(c)),
                native_retail_sha256=sha(c)))
    return dict(rows=rows, records=records, oracle=oracle)


def constructors(gba, old, new):
    report = []
    for old_at, new_at, size, native, end, continuation_old, continuation_new in (
        (0x3A5612, 0x7611CE, 75, 0x36AC20, 0x36ACC4, 0x10C0, 0x125C),
        (0x3A579F, 0x76135B, 97, 0x36AE94, 0x36AF64, 0x1263, 0x13FF),
    ):
        need(cut(old, old_at, size) == cut(new, new_at, size), "whole old/new constructor prefix identity")
        prefix_digest = ("99439941AFAA15504BD10B088A57E80043B90E1C9A817510335DE24457B26E6F" if size == 75 else
                         "0F65E5C92F15761470305E58DA3BCD1F380EFFAFDBBAD16805371667CC7FC9E6")
        need(sha(cut(new, new_at, size)) == prefix_digest, "typed constructor prefix identity")
        for data, at, segment, offset, service in ((old, old_at + size, 0xA45B, continuation_old, 0xD2C),
                                                   (new, new_at + size, 0x5FFD, continuation_new, 0xEC8)):
            sequence(data, at, at + 19, [f"push 0x{segment:x}", f"push 0x{offset:x}", "push 0xc00", "push si",
                f"lcall 0x{segment:x}, 0x{service:x}", "add sp, 0xa", "retf"])
        need(OLD_CS + continuation_old == old_at + size + 19 and NEW_CS + continuation_new == new_at + size + 19, "source continuation is constructor successor")
        native_digest = ("DB5E6EC04014DF2840AB1788127EA3D293F78C141645BE4A1D8E9FF448B89EEC" if size == 75 else
                         "C2EA73516650DE83363912652882CD006D0585688B96E036A6D8D24615F28AB0")
        need(sha(cut(gba, native, end - native)) == native_digest, "complete retail constructor oracle")
        tail = end - 44
        sequence(gba, tail, end, ["stmdb sp!, {r4}", "stmdb sp!, {fp}", "add r8, pc, #0x1c", "stmdb sp!, {r8}",
            "stmdb sp!, {fp}", "ldrh r8, [r4, #0x94]", "stmdb sp!, {r8}", "bl #0x836a69c", "add sp, sp, #0x14",
            "ldm sp!, {lr}", "bx lr"], True)
        need(tail + 8 + 8 + 0x1C == end, "native continuation is constructor successor")
        report.append(dict(old=old_at, source=new_at, prefix_bytes=size, relocation_bytes=19,
                           native=BASE + native, native_bytes=end - native, native_sha256=native_digest,
                           source_continuation=NEW_CS + continuation_new, native_continuation=BASE + end))
    return report


def consumer_contract(before, after, gba, old, new):
    spans = ((0x354B00, 0x354B24), (0x36B04C, 0x36B068), (0x36FC44, 0x36FC64), (0x3787EC, 0x378814),
             (0x36ECEC, 0x36ECF4), (0x36ED38, 0x36ED40), (0x36ED78, 0x36ED98), (0x36F3B8, 0x36F414),
             (0x36AE08, 0x36AE2C), (0x3555D0, 0x35568C), (0x36E374, 0x36E394), (0x353BC0, 0x353C24),
             (0x36EE98, 0x36EEA8), (0x36EF6C, 0x36EF7C), (0x36EB54, 0x36EBF0),
             (0x36AC20, 0x36ACC4), (0x36AE94, 0x36AF64))
    for start, end in spans:
        need(cut(before, start, end - start) == cut(after, start, end - start) == cut(gba, start, end - start), "entire native reader/constructor retained")
    sequence(after, 0x36F3B8, 0x36F3EC, ["ldrb r0, [r5, #0x11]", "ldr r1, [r1, r0, lsl #2]", "ldr r8, [pc, #0x480]",
        "ldrb r0, [r8, #6]", "add r1, r1, r0, lsl #5", "stmdb sp!, {r4}", "mov r4, r5", "add r5, r5, #0xac",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4", "sub r5, r5, #0xac", "ldm sp!, {r4}"], True)
    sequence(after, 0x36AE08, 0x36AE2C, ["ldr r1, [r4, #0x9c]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
        "ldrsh r0, [r4, #0xaa]", "lsl r0, r0, #5", "add r1, r1, r0", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"], True)
    sequence(after, 0x36E374, 0x36E394, ["ldr r1, [r4, #0x10]", "ldrh r0, [r1]", "ldrh r3, [r1, #2]", "ldrh r2, [r1, #4]",
        "ldr r8, [pc, #0xa4]", "strh r0, [r8, #2]", "strh r3, [r8, #4]", "strh r2, [r8, #6]"], True)
    need(u(after, 0x36E430) == u(after, 0x36F848) == 0x03004D20, "A byte4 reaches actual selector03004D26")
    sequence(after, 0x355604, 0x35568C, ["ldr r0, [r1, #4]", "str r0, [r4]", "stmdb sp!, {r5}", "stmdb sp!, {fp}",
        "ldrh r8, [r1, #2]", "stmdb sp!, {r8}", "bl #0x8012874", "add sp, sp, #0xc", "ldrsh r0, [r1, #8]",
        "ldrsb r3, [r1, #0xa]", "strh r0, [r4, #0x94]", "strh r3, [r4, #0x96]", "ldrsb r0, [r1, #0xb]",
        "ldr r3, [r1, #0xc]", "strh r0, [r4, #0x98]", "str r3, [r4, #0x9c]", "ldrb r0, [r1, #0x10]",
        "ldrb r3, [r1, #0x11]", "strb r0, [r4, #0x9a]", "strb r3, [r4, #0x9b]", "ldrsh r0, [r1, #0x12]",
        "ldrsh r3, [r1, #0x14]", "strh r0, [r4, #0xa0]", "strh r3, [r4, #0xa2]", "ldrsh r0, [r1, #0x16]",
        "ldrsh r3, [r1, #0x18]", "strh r0, [r4, #0xa4]", "strh r3, [r4, #0xa6]", "ldrsh r0, [r1, #0x1a]",
        "ldrsh r3, [r1, #0x1c]", "strh r0, [r4, #0xa8]", "strh r3, [r4, #0xaa]", "pop {r3, lr}", "bx lr"], True)
    sequence(after, 0x36F3EC, 0x36F414, ["ldr r8, [pc, #0x458]", "ldrh sb, [r8]", "cmp sb, #2", "bne #0x836f414",
        "ldr r8, [pc, #0x44c]", "ldrb r0, [r8, #4]", "strh r0, [r5, #0xa0]", "ldr r8, [pc, #0x444]",
        "ldrb r0, [r8, #6]", "strh r0, [r5, #0xaa]"], True)
    need(u(after, 0x36F84C) == u(after, 0x36F7D0) == 0x03004D32 and u(after, 0x36F850) == u(after, 0x36F854) == 0x03004D20, "category and metadata override owners")
    sequence(after, 0x36ED78, 0x36ED84, ["ldr r8, [pc, #0xa50]", "mov sb, #2", "strh sb, [r8]"], True)
    fixed = (
        (0x36B04C, 0x36B068, ["ldr r1, [pc, #0x1e4]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]", "add r1, r1, #0x60", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"]),
        (0x36FC44, 0x36FC64, ["ldr r1, [pc, #0x94]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]", "ldrh r0, [r4, #0xa0]", "add r1, r1, r0, lsl #5", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"]),
        (0x354B00, 0x354B24, ["ldr r1, [pc, #0x17c]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]", "mov sb, #0", "strb sb, [r4, #0x6c]", "add r5, r4, #0xac", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"]),
        (0x3787EC, 0x378814, ["ldr r1, [pc, #0x44]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]", "add r1, r1, #0x60", "stmdb sp!, {r5}", "add r5, r4, #0xac", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4", "ldm sp!, {r5}"]),
    )
    for start, end, expected in fixed:
        sequence(after, start, end, expected, True)
    for at, displacement in ((0x36ECEC, 0xACC), (0x36ED38, 0xA88), (0x36ED90, 0xA3C)):
        sequence(after, at, at + 8, [f"ldr r1, [pc, #0x{displacement:x}]", "b #0x836f3b8"], True)
    sequence(after, 0x36EE98, 0x36EEA8, ["ldr r8, [pc, #0x950]", "mov sb, #0", "strb sb, [r8, #6]", "b #0x836ecf4"], True)
    sequence(after, 0x36EF6C, 0x36EF7C, ["ldr r8, [pc, #0x88c]", "mov sb, #3", "strb sb, [r8, #6]", "b #0x836ecf4"], True)
    need(u(after, 0x36F7F0) == u(after, 0x36F800) == 0x03004D20, "forced variant owner")
    producer = ["mov ax, word ptr es:[bx]", "mov dx, word ptr es:[bx + 2]", "mov cx, word ptr es:[bx + 4]",
                "mov word ptr [bp - 6], ax", "mov word ptr [bp - 4], dx", "mov word ptr [bp - 2], cx"]
    sequence(old, 0x3A45DF, 0x3A45F3, producer); sequence(new, 0x75FFFF, 0x760013, producer)
    for data, at, segment in ((old, 0x3A5079, 0xABDF), (new, 0x760C05, 0x668E)):
        sequence(data, at, at + 43, ["xor ax, ax", "mov al, byte ptr [di + 0x11]", "shl ax, 1", "add bx, ax",
            "mov bx, word ptr cs:[bx]", "xor ax, ax", "mov al, byte ptr [bp - 2]", "shl ax, 5", "add bx, ax", "push si",
            "mov si, di", "add di, 0x96", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "sub di, 0x96", "pop si"])
    for data, starts, cs, target in ((old, (0x3A4B99, 0x3A4BC0, 0x3A4BEC), OLD_CS, 0x3A5079),
                                   (new, (0x760679, 0x7606A0, 0x7606CC), NEW_CS, 0x760C05)):
        for group, at in enumerate(starts):
            offset = (OLD_TABLE + 24 * group if data is old else NEW_TABLE + 30 * group) - cs
            sequence(data, at, at + 6, [f"mov bx, 0x{offset:x}", f"jmp 0x{target:x}"])
    source_readers = []
    for data, starts, offset, segment in ((old, (0x3A58BD,), 0x288C, 0xABDF), (new, (0x761479, 0x761A9D), 0x307A, 0x668E)):
        for at in starts:
            sequence(data, at, at + 28, [f"mov bx, 0x{offset:x}", "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "add bx, 0x60", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
            source_readers.append(at)
    for data, at, offset, segment in ((old, 0x3A67D8, 0x288C, 0xABDF), (new, 0x7629C4, 0x307A, 0x668E)):
        sequence(data, at, at + 34, [f"mov bx, 0x{offset:x}", "xor ax, ax", "mov al, byte ptr [di + 0x11]", "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "mov ax, word ptr [si + 0x8a]", "shl ax, 5", "add bx, ax", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
        source_readers.append(at)
    for data, at, table, seg, service in ((old, 0x3B10A2, 0x28A4, 0xA45B, 0xABDF), (new, 0x76C562, 0x3098, 0x5FFD, 0x668E)):
        sequence(data, at, at + 40, [f"mov bx, 0x{table:x}", f"mov ax, 0x{seg:x}", "mov es, ax", "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax", "mov bx, word ptr es:[bx]", "add bx, 0x60", "push di", "mov di, si", "add di, 0x96", "push es", f"lcall 0x{service:x}, 0", "add sp, 2", "pop di"])
        source_readers.append(at)
    for data, at, table, seg, service, target in ((old, 0x3929FA, 0x28BC, 0xA45B, 0xABDF, 0x392921), (new, 0x742CE2, 0x30B6, 0x5FFD, 0x668E, 0x742C09)):
        sequence(data, at, at + 42, [f"mov ax, 0x{seg:x}", f"mov bx, 0x{table:x}", "mov es, ax", "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax", "mov bx, word ptr es:[bx]", "mov byte ptr [si + 0x58], 0", "mov di, si", "add di, 0x96", "push es", f"lcall 0x{service:x}, 0", "add sp, 2", f"jmp 0x{target:x}"])
        source_readers.append(at)
    for data, at, segment in ((old, 0x3A575B, 0xABDF), (new, 0x761317, 0x668E)):
        sequence(data, at, at + 35, ["mov bx, word ptr [si + 0x84]", "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "mov ax, word ptr [si + 0x94]", "shl ax, 5", "add bx, ax", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
        source_readers.append(at)
    sequence(new, 0x76694D, 0x76695D, ["mov ax, word ptr es:[bx + 0xc]", "mov dx, word ptr es:[bx + 0xe]", "mov word ptr [si + 0x82], ax", "mov word ptr [si + 0x84], dx"])
    for typ, gn, go, gs in ((9, 0x36EC98, 0x3A4B52, 0x760632), (10, 0x36ECF4, 0x3A4B9F, 0x76067F),
                           (11, 0x36EC98, 0x3A4B52, 0x760632), (12, 0x36ED40, 0x3A4BC6, 0x7606A6)):
        need(u(after, 0x36EBA8 + (typ - 8) * 4) == BASE + gn and h(old, 0x3A4AC3 + (typ - 8) * 2) + OLD_CS == go and h(new, 0x76059F + (typ - 8) * 2) + NEW_CS == gs, "same actual collision dispatch classes")
    return dict(native_readers=[list(group) for group in READERS], source_other_readers=source_readers,
        generic_native=0x0836F3B8, generic_source=0x760C05, followup_consumer=0x0836AE08,
        metadata_fields="Full callback/event + all twelve typed fields read by08355604..08355680; descriptor+0C ->fighter+9C, descriptor+1C ->fighter+AA.",
        selector_flow="P1 A byte4 -> collision+10 ->03004D26 -> variant*32; category2 preserves A byte4 in fighter+AA.",
        preserved_native_spans=[dict(start=a, end=b, sha256=sha(cut(after, a, b-a))) for a,b in spans])


def p1_graph(after, new):
    counts, type_variants = Counter(), defaultdict(set)
    edits, high, resources = [], [], []
    event_total = command_total = references = nonnull = 0
    for record in range(60):
        source = far(new, 0x740000 + record * 32 + 6)
        need(u(new, source) == 4, "direct source P1")
        first = h(new, source + 6)
        need(first > 4 and (first - 4) % 8 == 0, "exact source event boundary")
        count = (first - 4) // 8
        need(count <= 256, "bounded source event population")
        native = ptr(after, GROUPS[record // 15] + record % 15 * 32 + 4, 8)
        table = ptr(after, native, count * 16)
        need(table == native + 8 and u(after, native + 4) == 0 and ptr(after, table + 4) == table + count * 16, "actual same complete native event population")
        local = Counter()
        for event in range(count):
            n, commands, a, b = struct.unpack("<4H", cut(new, source + 4 + event * 8, 8))
            need(0 < n <= 255 and commands >= first and a != 0, "complete source event")
            row = table + event * 16
            need(u(after, row) == n, "same command count for every source event")
            cp, ap = ptr(after, row + 4, n * 16), ptr(after, row + 8, 8)
            value, original = after[ap + 4], new[source + a + 4]
            if value != original:
                edits.append((record, event, original, value))
            counts[value] += 1; local[value] += 1
            pairs = [(b, u(after, row + 12))]
            pairs.extend((h(new, source + commands + j * 12 + 10), u(after, cp + j * 16 + 12)) for j in range(n))
            kinds = set()
            for source_b, native_b in pairs:
                references += 1
                need(bool(source_b) == bool(native_b), "each event/command collision-null edge preserved")
                if source_b:
                    cut(new, source + source_b, 10); cut(after, native_b - BASE, 10)
                    kind = h(new, source + source_b)
                    need(kind == h(after, native_b - BASE), "each collision edge preserves its own source type, not only global sets")
                    nonnull += 1; kinds.add(kind); type_variants[kind].add(value)
            if value > 3:
                need(value == original == 8, "source-prescribed selector8")
                high.append(dict(record=record, event=event, selector=value, source_a=source + a, native_a=BASE + ap, collision_types=sorted(kinds)))
            event_total += 1; command_total += n
        resources.append(dict(record=record, source=source, native=BASE + native, events=count, variants=dict(sorted(local.items()))))
    need(dict(counts) == {0:2365, 1:125, 2:5, 8:3} and (event_total, command_total, references) == (2498,12506,15004), "complete canonical event/command/reference census")
    need(edits == list(EXISTING_SELECTOR_EDITS), "eight explicit pre-existing selector edits; no inferred conversion rule")
    need([(r["record"],r["event"]) for r in high] == [(13,108),(44,26),(44,27)], "all source selector8 producers")
    need(type_variants[9] == {0,1,2,8} and not type_variants[11] and type_variants[10] == type_variants[12] == {0,1}, "actual domains of the three generic table selectors")
    need(high[0]["collision_types"] == [0,8] and all(row["collision_types"] == [3,9] for row in high[1:]), "base13 type8 excluded, evolved14 type9 cross-block routes included")
    return dict(canonical_resources=60, events=event_total, commands=command_total, collision_reference_edges=references,
        nonnull_collision_edges=nonnull, variants=dict(sorted(counts.items())), type_variants={k:sorted(v) for k,v in sorted(type_variants.items()) if v},
        existing_selector_edits=edits, selector8=high, resources=resources)


def aliases(data, patched):
    target_start, target_end = (TABLE, END) if patched else (NATIVE_TABLE, NATIVE_TABLE + 192)
    found = []
    for alignment in range(4):
        end = len(data) - ((len(data) - alignment) % 4)
        for index, (value,) in enumerate(struct.iter_unpack("<I", memoryview(data)[alignment:end])):
            if BASE + target_start <= value < BASE + target_end:
                found.append((alignment + 4 * index, value))
    expected = sorted((site, BASE + (TABLE + 60 * group if patched else NATIVE_TABLE + 48 * group)) for group, group_sites in enumerate(SITES) for site in group_sites)
    need(sorted(found) == expected, "exact eleven all-alignment aliases; no interior pointers")
    if patched:
        for alignment in range(4):
            end = len(data) - ((len(data) - alignment) % 4)
            need(not any(BASE + NATIVE_TABLE <= value < BASE + NATIVE_TABLE + 192 for value, in struct.iter_unpack("<I", memoryview(data)[alignment:end])), "no old-table aliases remain")
    for group_sites, readers in zip(SITES[:3], READERS):
        for site, reader in zip(group_sites, readers):
            actual = []
            for at in range((site - 4104) & ~3, site + 4096, 4):
                word = u(data, at)
                if word >> 28 != 15 and word & 0x0F7F0000 == 0x051F0000:
                    target = at + 8 + (1 if word & 0x800000 else -1) * (word & 4095)
                    if target == site:
                        actual.append((at, word >> 12 & 15))
            need(actual == [(reader, 1)], "all actual readers of each literal use r1")
    return [dict(site=s, pointer=p) for s,p in expected]


def reservation(before):
    need(cut(before, TABLE - 4, END - TABLE + 4) == b"\xff" * (END - TABLE + 4), "empty allocation and four-byte recovery gap")
    for alignment in range(4):
        end = len(before) - ((len(before) - alignment) % 4)
        need(not any(BASE + TABLE <= w < BASE + END for w, in struct.iter_unpack("<I", memoryview(before)[alignment:end])), "no encoded inbound pointer at any alignment")
    for index, (word,) in enumerate(struct.iter_unpack("<I", before)):
        if word == 0xFFFFFFFF:
            continue
        at, target = index * 4, None
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            displacement -= 0x1000000 if displacement & 0x800000 else 0
            target = at + 8 + displacement * 4
        elif word & 0x0F7F0000 == 0x051F0000:
            target = at + 8 + (1 if word & 0x800000 else -1) * (word & 4095)
        elif word & 0x0E1F0000 == 0x020F0000 and (word >> 21) & 15 in (2,4):
            rotate, value = ((word >> 8) & 15) * 2, word & 255
            immediate = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF if rotate else value
            target = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
        need(target is None or not TABLE <= target < END, "no ARM branch/literal/ADR allocation owner")
    for index, (word,) in enumerate(struct.iter_unpack("<H", before)):
        if word & 0xF800 in (0x4800, 0xA000):
            target = ((index * 2 + 4) & ~3) + (word & 255) * 4
            need(not TABLE <= target < END, "no Thumb PC-relative/ADR allocation owner")


def candidate(before, after, gba, proof):
    need(len(before) == len(after) == 0x800000, "candidate extent")
    expected = bytearray(before)
    for group, row in enumerate(proof["rows"]):
        expected[TABLE + group * 60:TABLE + (group + 1) * 60] = struct.pack("<15I", *([row["record"]] * 15))
        for site in SITES[group]:
            struct.pack_into("<I", expected, site, BASE + TABLE + group * 60)
    need(after == expected, "exact source-derived four tables and eleven pointers; no other writes")
    need(cut(after, NATIVE_TABLE, 192) == cut(gba, NATIVE_TABLE, 192), "all 48 original table entries retained")
    native_expected = bytearray(proof["oracle"])
    for index in range(4):
        struct.pack_into("<I", native_expected, 256 + index * 32 + 12, BASE + TABLE + 180)
    need(cut(before, NATIVE_RECORD, 512) == proof["oracle"] and cut(after, NATIVE_RECORD, 512) == native_expected, "all sixteen complete descriptors retained except exactly four follow-up words")
    inverse = bytearray(after)
    inverse[TABLE:END] = before[TABLE:END]
    for sites in SITES:
        for site in sites:
            inverse[site:site + 4] = before[site:site + 4]
    need(inverse == before, "full-image inverse")
    graph = []
    for ident in range(15):
        for group in range(4):
            record = ptr(after, TABLE + group * 60 + ident * 4, 128)
            need(record == NATIVE_RECORD + 128 * group, "actual installed row resolves source-matched record population")
            for variant in range(4):
                selected = record + variant * 32
                need(h(after, selected) == 0 and h(after, selected + 2) == proof["records"][group * 4 + variant]["event"], "all 240 nominal subrecord routes preserve typed actions")
                if group == 2:
                    followup = ptr(after, selected + 12, 60)
                    need(followup == TABLE + 180 and ptr(after, followup + ident * 4, 128) == NATIVE_RECORD + 384, "all60HitC descriptor routes resolve full follow-up population")
        crossed = ptr(after, TABLE + ident * 4, 32) + 8 * 32
        source_crossed = NEW_CS + h_from_rows(proof, 0) + 8 * 32
        need(crossed == NATIVE_RECORD + 256 and source_crossed == NEW_RECORD + 256, "variant8 selects original HitC descriptor on both platforms")
        followup = ptr(after, crossed + 12, 60)
        destination = ptr(after, followup + ident * 4, 32)
        need(destination == NATIVE_RECORD + 384 and h(after, crossed + 28) == 0, "variant8 complete graph reaches expanded follow-up; default selector0 retained")
        graph.append(dict(id=ident, hit_a8=BASE + crossed, followup_table=BASE + followup, default_followup_record=BASE + destination))
    return graph


def h_from_rows(proof, group):
    # Explicit source record offset, recovered from the verified source row.
    return proof["records"][group * 4]["source"] - NEW_CS


def negatives(before, after, gba, old, new, proof, population):
    rejected = []
    def reject(label, function):
        try:
            function()
        except (ValueError, KeyError, IndexError, struct.error):
            rejected.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    def changed(data, at, mask=1):
        result = bytearray(data); result[at] ^= mask; return result
    for row in range(60):
        reject(f"installed row {row // 15}/{row % 15}", lambda row=row: candidate(before, changed(after, TABLE + row * 4), gba, proof))
    for sites in SITES:
        for site in sites:
            reject(f"redirect {site:X}", lambda site=site: candidate(before, changed(after, site), gba, proof))
    for record in range(16):
        for offset in (2,4,8,10,11,12,16,17,18,20,22,24,26,28):
            at = NATIVE_RECORD + record * 32 + offset
            reject(f"native record{record} consumed field{offset}", lambda at=at: candidate(before, changed(after, at), gba, proof))
    for at in (TABLE-1, END, NATIVE_TABLE, 0x629350, 0x629000, 0x90A18, 0x63E000, 0x36F3C4, 0x36AE08):
        reject(f"outside-layer byte {at:X}", lambda at=at: candidate(before, changed(after, at), gba, proof))
    reject("truncated candidate", lambda: candidate(before, after[:-1], gba, proof))
    for group in range(4):
        for ident in (0,11,12,13,14):
            at = NEW_TABLE + group * 30 + ident * 2
            reject(f"source row {group}/{ident}", lambda at=at: source_records(gba, old, changed(new, at)))
    for record in range(16):
        for offset in (4,8,14,28):
            at = NEW_RECORD + record * 32 + offset
            reject(f"source record{record} callback/metadata{offset}", lambda at=at: source_records(gba, old, changed(new, at)))
    for at in (0x7611CE,0x761219,0x76135B,0x7613BC):
        reject(f"source constructor/relocation {at:X}", lambda at=at: constructors(gba, old, changed(new, at)))
    for row in population["selector8"]:
        at = row["native_a"] - BASE + 4
        reject(f"actual high selector {row['record']}/{row['event']}", lambda at=at: p1_graph(changed(after, at), new))
        at = row["source_a"] + 4
        reject(f"source high selector {row['record']}/{row['event']}", lambda at=at: p1_graph(after, changed(new, at)))
    for target in (NATIVE_TABLE, NATIVE_TABLE + 1):
        bad = bytearray(before); struct.pack_into("<I", bad, 0x101, BASE + target)
        reject("unaccounted old alias " + hex(target), lambda bad=bad: aliases(bad, False))
    bad = bytearray(after); struct.pack_into("<I", bad, 0x101, BASE + TABLE + 1)
    reject("unaligned new interior alias", lambda: aliases(bad, True))
    bad = changed(before, TABLE)
    reject("occupied allocation", lambda: reservation(bad))
    for name, at, value, half in (("unaligned inbound pointer",0x101,BASE+TABLE+1,False),
                                  ("ARM branch",TABLE-0x100,0xEA00003E,False),
                                  ("ARM literal",TABLE-0x100,0xE59F00F8,False),
                                  ("ARM ADR",TABLE-0x100,0xE28F00F8,False),
                                  ("Thumb literal",TABLE-0x100,0x483F,True),
                                  ("Thumb ADR",TABLE-0x100,0xA03F,True)):
        bad = bytearray(before); struct.pack_into("<H" if half else "<I", bad, at, value)
        reject(name + " allocation owner", lambda bad=bad: reservation(bad))
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("before", "after", "gba", "old", "new", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    inputs = [args.before,args.after,args.gba,args.old,args.new]
    need(all(p.suffix.lower() in (".gba",".wsc") for p in inputs), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".json", "JSON report only")
    before, after, gba, old, new = [p.read_bytes() for p in inputs]
    need(tuple(map(sha,(before,after,gba,old,new))) == (BEFORE,AFTER,GBA,OLD,NEW), "five pinned input identities")
    proof = source_records(gba, old, new)
    lineage = constructors(gba, old, new)
    consumers = consumer_contract(before, after, gba, old, new)
    population = p1_graph(after, new)
    reservation(before)
    before_aliases, after_aliases = aliases(before, False), aliases(after, True)
    graph = candidate(before, after, gba, proof)
    rejected = negatives(before, after, gba, old, new, proof, population)
    installed_records = []
    for record in proof["records"]:
        installed = cut(after, record["native"] - BASE, 32)
        installed_records.append(dict(record, native_installed_metadata=list(native_fields(installed)),
                                      native_installed_sha256=sha(installed)))
    spans = [(site,site+4) for sites in SITES for site in sites] + [(TABLE,END)]
    report = dict(status="PASS", kind="independent-character-hit-routing",
        inputs=dict(zip(("before","after","gba","old","new"), map(sha,(before,after,gba,old,new)))),
        tables=proof["rows"], native_records=installed_records, callback_lineage=lineage, consumers=consumers,
        p1_population=population, variant8_graph_all15_ids=graph, nominal_subrecord_routes=240,
        original_rows_retained=48, added_rows=12, source_rows=60, aliases_before=before_aliases, aliases_after=after_aliases,
        exact_writes=[dict(start=a,end=b,bytes=b-a,before_sha256=sha(before[a:b]),after_sha256=sha(after[a:b])) for a,b in spans],
        declared_bytes=sum(b-a for a,b in spans), changed_bytes=sum(a!=b for a,b in zip(before,after)), full_inverse=True,
        reservation=dict(start=TABLE,end=END,guard_start=TABLE-4,empty=True,all_alignment_pointer_scan=True,arm_branch_literal_adr_scan=True,thumb_literal_adr_scan=True),
        negative_count=len(rejected), negative_cases=rejected,
        limits=["Canonical P1 producer census covers60resources; noncanonical producers, other adjacent hit tables and later source-only record groups remain outside this layer.",
                "Record fields reuse the paired retail conversion; no universal temporal/spatial conversion or full downstream callback/service parity is claimed.",
                "No emulator, save access or target execution. Runtime validation is separate."])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="PASS",report_sha256=sha(args.output.read_bytes()),negatives=len(rejected),events=population["events"],collision_edges=population["collision_reference_edges"])))


if __name__ == "__main__":
    main()
