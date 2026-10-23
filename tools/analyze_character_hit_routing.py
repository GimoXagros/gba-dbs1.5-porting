#!/usr/bin/env python3
"""Read-only source/retail proof of three hit tables and their follow-up view.

No builder, generated manifest, emulator, or save file supplies expected data.
This proves the bounded pointer/record route, not all combat or service parity.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct

from verify_character_followup_routing import BASE, GBA, OLD, NEW, need, sha, u32, sequence
from verify_character_p1_completion import source_events, far

CURRENT = "A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71"
OLD_CS, NEW_CS = 0x3A45B0, 0x75FFD0
# Native table, old/new source table, native record population, old/new records.
SPECS = (
    (0x36BF08, 0x3A6E3C, 0x76304A, 0x36C32C, 0x3A71CE, 0x763458),
    (0x36BF38, 0x3A6E54, 0x763068, 0x36C3AC, 0x3A724E, 0x7634D8),
    (0x36BF68, 0x3A6E6C, 0x763086, 0x36C42C, 0x3A72CE, 0x763558),
    (0x36BF98, 0x3A6E84, 0x7630A4, 0x36C4AC, 0x3A734E, 0x7635D8),
)
ALIASES = ((0x36B238, 0x36F7C0, 0x36FCE0), (0x36F7C8, 0x378838),
           (0x354C84, 0x36F7D4), (0x36C438, 0x36C458, 0x36C478, 0x36C498))
READERS = ((0x36B04C, 0x36ECEC, 0x36FC44), (0x36ED38, 0x3787EC),
           (0x354B00, 0x36ED90))
GROUPS = (0x4A80F8, 0x4A82D8, 0x60B000, 0x60B1E0)


def h(data, at):
    return struct.unpack_from("<H", data, at)[0]


def native_fields(record):
    return [struct.unpack_from("<h", record, 8)[0],
            *struct.unpack_from("<bb", record, 10), u32(record, 12),
            record[16], record[17], *struct.unpack_from("<6h", record, 18)]


def table_contract(current, gba, old, source):
    tables, records = [], []
    need(sha(gba[0x36C32C:0x36C52C]) ==
         "05BC2738F672102357E8D054D112EF23F41B73A2B5B982209EABB6A8477F064C",
         "retail four contiguous record populations")
    need(current[0x36C32C:0x36C52C] == gba[0x36C32C:0x36C52C], "current retail record populations retained")
    for index, (table, old_table, new_table, native_record, old_record, new_record) in enumerate(SPECS):
        old_offset, new_offset = old_record - OLD_CS, new_record - NEW_CS
        need(struct.unpack_from("<12H", old, old_table) == (old_offset,) * 12, "twelve old source rows")
        need(struct.unpack_from("<15H", source, new_table) == (new_offset,) * 15, "fifteen source rows")
        need(h(old, old_table + 24) != old_offset and h(source, new_table + 30) != new_offset,
             "next distinct table fixes both source boundaries")
        need(struct.unpack_from("<12I", gba, table) == (BASE + native_record,) * 12, "twelve retail row oracle")
        need(current[table:table + 48] == gba[table:table + 48], "current original table retained")
        need(u32(gba, table + 48) != BASE + native_record, "next distinct native table boundary")
        for sub in range(4):
            a = old[old_record + sub * 32:old_record + (sub + 1) * 32]
            b = source[new_record + sub * 32:new_record + (sub + 1) * 32]
            c = gba[native_record + sub * 32:native_record + (sub + 1) * 32]
            need(a[:4] == b[:4] == c[:4] and h(a, 0) == 0, "same flag-zero event on all record routes")
            old_cb, new_cb, native_cb = ((0x1062, 0x11FE, 0x0836AC20) if index == 2
                                         else (0x11EF, 0x138B, 0x0836AE94))
            need(struct.unpack_from("<HH", a, 4) == (old_cb, 0xA45B), "old callback far address")
            need(struct.unpack_from("<HH", b, 4) == (new_cb, 0x5FFD), "new callback far address")
            need(u32(c, 4) == native_cb, "native callback lineage")
            if index == 2:
                need(a[8:14] == b[8:14] and a[16:] == b[16:], "all nonpointer hit metadata retained")
                need(h(a, 14) + OLD_CS == SPECS[3][1] and h(b, 14) + NEW_CS == SPECS[3][2],
                     "source metadata selects fifteen-row follow-up dependency")
                need(u32(c, 12) == BASE + SPECS[3][0], "native metadata selects short follow-up table")
            else:
                need(a[8:] == b[8:], "all twelve source metadata words unchanged")
            need(c[30:32] == bytes(2), "native trailing padding")
            records.append({"table": index, "subrecord": sub,
                            "old": f"{old_record + 32 * sub:06X}", "source": f"{new_record + 32 * sub:06X}",
                            "native": f"{BASE + native_record + 32 * sub:08X}",
                            "event": h(b, 2), "native_callback": f"{native_cb:08X}",
                            "source_metadata_words": list(struct.unpack_from("<12h", b, 8)),
                            "native_metadata_fields": native_fields(c), "native_sha256": sha(c)})
        tables.append({"index": index, "native": f"{BASE + table:08X}", "native_rows": 12,
                       "old": f"{old_table:06X}", "old_rows": 12,
                       "source": f"{new_table:06X}", "source_rows": 15,
                       "record_population": f"{BASE + native_record:08X}..{BASE + native_record + 128:08X}",
                       "source_rows_resolve": [f"{new_record:06X}"] * 15,
                       "repair_rows": [f"{BASE + native_record:08X}"] * 15,
                       "aliases": [f"{at:06X}" for at in ALIASES[index]],
                       "overread_ID12_13_14": [f"{u32(current, table + 4 * ident):08X}" for ident in range(12, 15)]})
    found = []
    for at in range(len(current) - 3):
        if current[at + 3] == 8:
            target = u32(current, at)
            if BASE + SPECS[0][0] <= target < BASE + SPECS[-1][0] + 48:
                found.append((at, target))
    expected = sorted((at, BASE + spec[0]) for spec, aliases in zip(SPECS, ALIASES) for at in aliases)
    need(found == expected, "all aligned, unaligned, and interior native table aliases")
    for aliases, readers in zip(ALIASES[:3], READERS):
        for literal, reader in zip(aliases, readers):
            loads = []
            for at in range((literal - 4104) & ~3, literal + 4096, 4):
                word = u32(current, at)
                if word >> 28 != 15 and word & 0x0F7F0000 == 0x051F0000:
                    target = at + 8 + (word & 4095) * (1 if word & 0x800000 else -1)
                    if target == literal:
                        loads.append((at, (word >> 12) & 15))
            need(loads == [(reader, 1)], "actual complete native PC-relative reader set")
    return tables, records


def callback_contract(current, gba, old, source):
    result = []
    for old_at, new_at, count, digest, native, stop, native_digest, continuation in (
        (0x3A5612, 0x7611CE, 75, "99439941AFAA15504BD10B088A57E80043B90E1C9A817510335DE24457B26E6F",
         0x36AC20, 0x36ACC4, "DB5E6EC04014DF2840AB1788127EA3D293F78C141645BE4A1D8E9FF448B89EEC", (0x10C0, 0x125C)),
        (0x3A579F, 0x76135B, 97, "0F65E5C92F15761470305E58DA3BCD1F380EFFAFDBBAD16805371667CC7FC9E6",
         0x36AE94, 0x36AF64, "C2EA73516650DE83363912652882CD006D0585688B96E036A6D8D24615F28AB0", (0x1263, 0x13FF)),
    ):
        need(old[old_at:old_at + count] == source[new_at:new_at + count] and
             sha(source[new_at:new_at + count]) == digest, "source callback constructor identical prefix")
        for data, at, segment, next_offset, hitstop in (
            (old, old_at + count, 0xA45B, continuation[0], 0xD2C),
            (source, new_at + count, 0x5FFD, continuation[1], 0xEC8),
        ):
            sequence(data, at, at + 19, [f"push 0x{segment:x}", f"push 0x{next_offset:x}",
                     "push 0xc00", "push si", f"lcall 0x{segment:x}, 0x{hitstop:x}", "add sp, 0xa", "retf"])
        need(current[native:stop] == gba[native:stop] and sha(gba[native:stop]) == native_digest,
             "retained retail native constructor")
        result.append({"old": f"{old_at:06X}", "source": f"{new_at:06X}", "native": f"{BASE + native:08X}",
                       "identical_source_prefix_bytes": count, "relocated_tail_bytes": 19,
                       "native_constructor_bytes": stop - native})
    return result


def consumer_contract(current, gba, old, source):
    spans = ((0x354B00, 0x354B24), (0x36B04C, 0x36B068), (0x36FC44, 0x36FC64),
             (0x3787EC, 0x378814), (0x36ECEC, 0x36ECF4), (0x36ED38, 0x36ED40),
             (0x36ED78, 0x36ED98), (0x36F3B8, 0x36F414), (0x36AE08, 0x36AE2C),
             (0x3555D0, 0x35568C), (0x36E374, 0x36E394), (0x353BC0, 0x353C24),
             (0x36EE64, 0x36EE70), (0x36EF24, 0x36EF38), (0x36EFC8, 0x36EFDC),
             (0x36EE98, 0x36EEA8), (0x36EF6C, 0x36EF7C), (0x36EB54, 0x36EBF0))
    for start, end in spans:
        need(current[start:end] == gba[start:end], f"native contract retained {start:X}")
    sequence(current, 0x36F3B8, 0x36F3EC, [
        "ldrb r0, [r5, #0x11]", "ldr r1, [r1, r0, lsl #2]", "ldr r8, [pc, #0x480]",
        "ldrb r0, [r8, #6]", "add r1, r1, r0, lsl #5", "stmdb sp!, {r4}", "mov r4, r5",
        "add r5, r5, #0xac", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
        "sub r5, r5, #0xac", "ldm sp!, {r4}",
    ], arm=True)
    need(u32(current, 0x36F848) == 0x03004D20, "actual generic subrecord selector owner")
    sequence(current, 0x36E374, 0x36E394, [
        "ldr r1, [r4, #0x10]", "ldrh r0, [r1]", "ldrh r3, [r1, #2]", "ldrh r2, [r1, #4]",
        "ldr r8, [pc, #0xa4]", "strh r0, [r8, #2]", "strh r3, [r8, #4]", "strh r2, [r8, #6]",
    ], arm=True)
    need(u32(current, 0x36E430) == 0x03004D20, "A metadata producer owner")
    sequence(current, 0x36AE08, 0x36AE2C, [
        "ldr r1, [r4, #0x9c]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
        "ldrsh r0, [r4, #0xaa]", "lsl r0, r0, #5", "add r1, r1, r0",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
    ], arm=True)
    sequence(current, 0x355634, 0x355644, [
        "ldrsb r0, [r1, #0xb]", "ldr r3, [r1, #0xc]", "strh r0, [r4, #0x98]", "str r3, [r4, #0x9c]",
    ], arm=True)
    sequence(source, 0x76694D, 0x76695D, [
        "mov ax, word ptr es:[bx + 0xc]", "mov dx, word ptr es:[bx + 0xe]",
        "mov word ptr [si + 0x82], ax", "mov word ptr [si + 0x84], dx",
    ])
    # Same typed producer in the old and new source; byte BP-2 is A byte4.
    producer = ["mov ax, word ptr es:[bx]", "mov dx, word ptr es:[bx + 2]", "mov cx, word ptr es:[bx + 4]",
                "mov word ptr [bp - 6], ax", "mov word ptr [bp - 4], dx", "mov word ptr [bp - 2], cx"]
    sequence(old, 0x3A45DF, 0x3A45F3, producer)
    sequence(source, 0x75FFFF, 0x760013, producer)
    for data, at, segment in ((old, 0x3A5079, 0xABDF), (source, 0x760C05, 0x668E)):
        sequence(data, at, at + 43, [
            "xor ax, ax", "mov al, byte ptr [di + 0x11]", "shl ax, 1", "add bx, ax",
            "mov bx, word ptr cs:[bx]", "xor ax, ax", "mov al, byte ptr [bp - 2]", "shl ax, 5",
            "add bx, ax", "push si", "mov si, di", "add di, 0x96", "push cs",
            f"lcall 0x{segment:x}, 0", "add sp, 2", "sub di, 0x96", "pop si",
        ])
    # All seven literal readers, including fixed variant3, delayed and initial paths.
    for at, stop, instructions in (
        (0x36B04C, 0x36B068, ["ldr r1, [pc, #0x1e4]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
                             "add r1, r1, #0x60", "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"]),
        (0x36FC44, 0x36FC64, ["ldr r1, [pc, #0x94]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
                             "ldrh r0, [r4, #0xa0]", "add r1, r1, r0, lsl #5", "stmdb sp!, {fp}",
                             "bl #0x83555d0", "add sp, sp, #4"]),
        (0x354B00, 0x354B24, ["ldr r1, [pc, #0x17c]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
                             "mov sb, #0", "strb sb, [r4, #0x6c]", "add r5, r4, #0xac",
                             "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4"]),
        (0x3787EC, 0x378814, ["ldr r1, [pc, #0x44]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
                             "add r1, r1, #0x60", "stmdb sp!, {r5}", "add r5, r4, #0xac",
                             "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4", "ldm sp!, {r5}"]),
    ):
        sequence(current, at, stop, instructions, arm=True)
    for at, displacement in ((0x36ECEC, 0xACC), (0x36ED38, 0xA88), (0x36ED90, 0xA3C)):
        sequence(current, at, at + 8, [f"ldr r1, [pc, #0x{displacement:x}]", "b #0x836f3b8"], arm=True)
    for data, starts, offsets, target in (
        (old, (0x3A4B99, 0x3A4BC0, 0x3A4BEC), (0x288C, 0x28A4, 0x28BC), 0x3A5079),
        (source, (0x760679, 0x7606A0, 0x7606CC), (0x307A, 0x3098, 0x30B6), 0x760C05),
    ):
        for at, offset in zip(starts, offsets):
            sequence(data, at, at + 6, [f"mov bx, 0x{offset:x}", f"jmp 0x{target:x}"])
    source_consumers = []
    for data, starts, offset, segment in (
        (old, (0x3A58BD,), 0x288C, 0xABDF), (source, (0x761479, 0x761A9D), 0x307A, 0x668E),
    ):
        for at in starts:
            sequence(data, at, at + 28, [f"mov bx, 0x{offset:x}", "xor ax, ax", "mov al, byte ptr [si + 0x11]",
                     "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "add bx, 0x60", "push cs",
                     f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
            source_consumers.append(f"{at:06X}")
    for data, at, offset, segment in ((old, 0x3A67D8, 0x288C, 0xABDF), (source, 0x7629C4, 0x307A, 0x668E)):
        sequence(data, at, at + 34, [f"mov bx, 0x{offset:x}", "xor ax, ax", "mov al, byte ptr [di + 0x11]",
                 "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "mov ax, word ptr [si + 0x8a]",
                 "shl ax, 5", "add bx, ax", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
        source_consumers.append(f"{at:06X}")
    for data, at, table, table_segment, action_segment in (
        (old, 0x3B10A2, 0x28A4, 0xA45B, 0xABDF), (source, 0x76C562, 0x3098, 0x5FFD, 0x668E),
    ):
        sequence(data, at, at + 40, [f"mov bx, 0x{table:x}", f"mov ax, 0x{table_segment:x}", "mov es, ax",
                 "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax",
                 "mov bx, word ptr es:[bx]", "add bx, 0x60", "push di", "mov di, si", "add di, 0x96",
                 "push es", f"lcall 0x{action_segment:x}, 0", "add sp, 2", "pop di"])
        source_consumers.append(f"{at:06X}")
    for data, at, table, table_segment, action_segment, target in (
        (old, 0x3929FA, 0x28BC, 0xA45B, 0xABDF, 0x392921),
        (source, 0x742CE2, 0x30B6, 0x5FFD, 0x668E, 0x742C09),
    ):
        sequence(data, at, at + 42, [f"mov ax, 0x{table_segment:x}", f"mov bx, 0x{table:x}", "mov es, ax",
                 "xor ax, ax", "mov al, byte ptr [si + 0x11]", "shl ax, 1", "add bx, ax",
                 "mov bx, word ptr es:[bx]", "mov byte ptr [si + 0x58], 0", "mov di, si", "add di, 0x96",
                 "push es", f"lcall 0x{action_segment:x}, 0", "add sp, 2", f"jmp 0x{target:x}"])
        source_consumers.append(f"{at:06X}")
    for data, at, segment in ((old, 0x3A575B, 0xABDF), (source, 0x761317, 0x668E)):
        sequence(data, at, at + 35, ["mov bx, word ptr [si + 0x84]", "xor ax, ax", "mov al, byte ptr [si + 0x11]",
                 "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "mov ax, word ptr [si + 0x94]",
                 "shl ax, 5", "add bx, ax", "push cs", f"lcall 0x{segment:x}, 0", "add sp, 2", "retf"])
        source_consumers.append(f"{at:06X}")
    # Branch table: collision types9/11,10,12 select the three requested views.
    for typ, target, old_target, new_target in ((9, 0x36EC98, 0x3A4B52, 0x760632),
                                               (10, 0x36ECF4, 0x3A4B9F, 0x76067F),
                                               (11, 0x36EC98, 0x3A4B52, 0x760632),
                                               (12, 0x36ED40, 0x3A4BC6, 0x7606A6)):
        need(u32(current, 0x36EBA8 + (typ - 8) * 4) == BASE + target, "native collision branch table")
        need(h(old, 0x3A4AC3 + (typ - 8) * 2) + OLD_CS == old_target, "old collision branch table")
        need(h(source, 0x76059F + (typ - 8) * 2) + NEW_CS == new_target, "new collision branch table")
    # The two explicit remaps to the second table select variant0 or variant3.
    sequence(current, 0x36EE98, 0x36EEA8, ["ldr r8, [pc, #0x950]", "mov sb, #0", "strb sb, [r8, #6]", "b #0x836ecf4"], arm=True)
    sequence(current, 0x36EF6C, 0x36EF7C, ["ldr r8, [pc, #0x88c]", "mov sb, #3", "strb sb, [r8, #6]", "b #0x836ecf4"], arm=True)
    need(u32(current, 0x36F7F0) == u32(current, 0x36F800) == 0x03004D20, "variant override owner")
    return {"native_literal_readers": [[f"{BASE + at:08X}" for at in row] for row in READERS],
            "generic_consumer": "0836F3B8..0836F3EC", "source_generic_consumers": ["3A5079", "760C05"],
            "other_source_consumers": source_consumers, "selector": "P1 A byte4 -> collision+10 -> 03004D26",
            "metadata_producer": "0836E374..0836E394", "followup_consumer": "0836AE08..0836AE2C",
            "followup_pointer_producer": "descriptor+0C -> fighter+9C at08355638/40",
            "followup_variant_producer": "descriptor+1C -> fighter+AA; generic category2 overwrites from03004D26 at0836F410"}


def p1_population(current, source):
    counts, pairs, source_pairs = Counter(), defaultdict(set), defaultdict(set)
    differences, high, resources = [], [], []
    for record in range(60):
        source_p1 = far(source, 0x740000 + record * 32 + 6)
        events, aa, bb, _end = source_events(source, source_p1)
        native = u32(current, GROUPS[record // 15] + (record % 15) * 32 + 4) - BASE
        table = u32(current, native) - BASE
        need(table == native + 8 and u32(current, native + 4) == 0, "actual canonical P1 header")
        first = u32(current, table + 4) - BASE
        need(first == table + len(events) * 16, "same complete source/native P1 event population")
        local, native_types = Counter(), defaultdict(set)
        for event, (_relative, ar, br, source_commands) in enumerate(events):
            commands, payload, ap, bp = struct.unpack_from("<4I", current, table + 16 * event)
            need(commands == len(source_commands), "P1 complete command population")
            need(BASE <= ap <= BASE + len(current) - 8, "actual A8 pointer")
            selector, source_selector = current[ap - BASE + 4], aa[ar][4]
            counts[selector] += 1; local[selector] += 1
            if selector != source_selector:
                differences.append([record, event, source_selector, selector])
            collision_pointers = {bp}
            for command in range(commands):
                collision_pointers.add(u32(current, payload - BASE + 16 * command + 12))
            kinds = set()
            for pointer in collision_pointers - {0}:
                need(BASE <= pointer <= BASE + len(current) - 10, "actual B10 pointer")
                kind = h(current, pointer - BASE)
                kinds.add(kind); pairs[kind].add(selector); native_types[kind].add(selector)
            for relative in ({br} | {words[5] for words in source_commands}) - {0}:
                source_pairs[h(bb[relative], 0)].add(source_selector)
            if selector > 3:
                need(selector == source_selector == 8, "source-prescribed cross-block variant8")
                high.append({"record": record, "event": event, "native_A": f"{ap:08X}",
                             "source_A": f"{source_p1 + ar:06X}", "selector": selector, "B_types": sorted(kinds)})
        resources.append({"record": record, "source_P1": f"{source_p1:06X}", "native_P1": f"{BASE + native:08X}",
                          "events": len(events), "variant_counts": dict(sorted(local.items()))})
    need(dict(counts) == {0: 2365, 1: 125, 2: 5, 8: 3}, "all2498 canonical event variants enumerated")
    need([(x["record"], x["event"]) for x in high] == [(13, 108), (44, 26), (44, 27)], "all cross-block events")
    need(pairs == source_pairs, "native/source collision-type and variant upper-bound sets agree")
    need(pairs[9] == {0, 1, 2, 8} and not pairs[11] and pairs[10] == pairs[12] == {0, 1},
         "actual canonical variant domains for the requested generic readers")
    need(differences == [[0, 91, 1, 0], [3, 91, 1, 0], [3, 96, 1, 0], [3, 98, 1, 0],
                         [5, 109, 1, 0], [7, 109, 1, 0], [10, 109, 1, 0], [32, 28, 0, 1]],
         "eight pre-existing retail/source P1 variant edits recorded, not promoted into conversion rules")
    return {"canonical_resources": 60, "events": sum(counts.values()), "variant_counts": dict(sorted(counts.items())),
            "collision_type_variants": {str(k): sorted(v) for k, v in sorted(pairs.items()) if v},
            "source_unchanged_variant8_events": high, "existing_variant_edits": differences,
            "resources": resources, "scope": "all canonical character P1 event and command B references; noncanonical producers not exhausted"}


def analyze(current, gba, old, source):
    tables, records = table_contract(current, gba, old, source)
    callbacks = callback_contract(current, gba, old, source)
    consumers = consumer_contract(current, gba, old, source)
    population = p1_population(current, source)
    # Variant8 is deliberately a cross-block route, not an invalid index.
    need(SPECS[0][3] + 8 * 32 == SPECS[2][3] and SPECS[0][5] + 8 * 32 == SPECS[2][5],
         "source/native variant8 selects the same third population")
    return {"status": "PROVED", "scope": "three requested hit tables plus their required BF98 follow-up dependency",
            "tables": tables, "records": records, "callbacks": callbacks, "consumers": consumers,
            "P1_population": population, "variant8_native_record": "0836C42C", "variant8_source_record": "763558",
            "minimal_proposal": {"table_bytes": 240, "tables": 4, "rows": 60,
                                 "literal_redirects": 7, "metadata_pointer_redirects": 4,
                                 "declared_write_bytes": 284, "new_RAM": 0, "new_instructions": 0,
                                 "new_descriptors": 0, "preserve_old_tables": True,
                                 "preserve_descriptors_except_four_followup_pointer_words": True,
                                 "allocation": "not assigned; no repair built"},
            "limits": ["No emulator or save access", "No runtime failure or success claimed",
                       "Full callback/service and noncanonical collision-producer parity not proved",
                       "Other adjacent hit tables and three source-only record groups are outside this task"]}


def negatives(current, gba, old, source):
    results = []
    cases = [(0, 0x36BF08 + 44, "native last row"), (2, 0x3A6E3C + 22, "old last row"),
             (3, 0x76304A + 28, "new ID14 row"), (3, 0x7630A4 + 28, "follow-up ID14 row"),
             (3, 0x763458 + 8, "consumed source metadata"), (3, 0x763558 + 14, "source follow-up producer"),
             (0, 0x36C438, "native follow-up producer"), (0, 0x36F3C4, "actual generic selector"),
             (0, 0x36FC50, "delayed selector"), (0, 0x354B08, "initial table index"),
             (0, 0x36AE10, "follow-up table index"), (3, 0x7611CE, "source callback constructor"),
             (0, 0x61E658 + 4, "source-prescribed variant8 event26"),
             (3, 0x7605A1, "source type9 dispatch"), (0, 0x36EF70, "forced variant3")]
    for index, at, label in cases:
        values = [current, gba, old, source]
        changed = bytearray(values[index]); changed[at] ^= 1; values[index] = bytes(changed)
        try:
            analyze(*values)
        except (ValueError, IndexError, struct.error):
            results.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    values = bytearray(current)
    values[0x629400:0x629404] = struct.pack("<I", BASE + SPECS[1][0] + 1)
    try:
        analyze(bytes(values), gba, old, source)
    except ValueError:
        results.append("unexpected interior alias")
    else:
        raise ValueError("negative accepted: unexpected interior alias")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("current", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    inputs = [args.current, args.gba, args.old, args.source]
    need(all(path.suffix.lower() in (".gba", ".wsc") for path in inputs), "explicit ROM inputs only")
    need(args.output.suffix.lower() == ".json", "analysis JSON output only")
    data = [path.read_bytes() for path in inputs]
    need(tuple(map(sha, data)) == (CURRENT, GBA, OLD, NEW), "pinned original and current input identities")
    report = analyze(*data)
    report["negative_tests"] = negatives(*data)
    report["input_sha256"] = dict(zip(("current", "gba", "old", "source"), map(sha, data)))
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded)
    print(f"PROVED: four dependent hit views,2498 events,{len(report['negative_tests'])} negatives; report {sha(encoded)}")


if __name__ == "__main__":
    main()
