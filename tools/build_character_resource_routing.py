#!/usr/bin/env python3
"""Repair the native fighter resource ABI after complete P0/P1 conversion.

Native records contain five pointers at +0,+4,+8,+12,+16 followed by twelve
unused zero bytes.  The four 15-row groups retain the retail main/companion
address delta.  Only dynamic fighter evolution consumers are redirected.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct

from build_character_p0_completion import inbound, source_commands, source_layout
from convert_wsc_palette_block import convert_color

BASE = 0x08000000
INPUT = "3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GROUPS = (0x4A80F8, 0x4A82D8, 0x60B000, 0x60B1E0)
EVOLUTION_LITERALS = (0x3534B8, 0xCC230, 0xCC708)
OPENING_LITERALS = (0x850E0, 0x850E4, 0x850E8, 0x85794, 0x86288, 0x862B8,
                    0x87018, 0x87020, 0x8718C, 0x87194, 0x87388, 0x87394)
# Source record, native P0, complete P1, primary/alternate palette, P4.
MAIN = (
    (12, 0x448000, 0x611800, 0x4A12A0, 0x4A12C8, 0x47A000),
    (13, 0x400000, 0x6156B4, 0x60E700, 0x60E748, 0x47A858),
    (14, 0x420AC0, 0x6184A0, 0x4A1340, 0x4A1368, 0x47AEB8),
    (41, 0x4B0000, 0x61B4BC, 0x4A1390, 0x4A1390, 0x568000),
    (42, 0x4CEAE0, 0x61C288, 0x4A13B8, 0x4A13B8, 0x5682E0),
    (43, 0x4E85E0, 0x61CF0C, 0x4A13E0, 0x4A13E0, 0x568550),
    (44, 0x4FB380, 0x61DB48, 0x4A1408, 0x4A1408, 0x5688D8),
)
COMPANIONS = (
    (27, 0x60B400, 0x61E71C, 0x60B880, 0x60B880, 0x0FE400),
    (28, 0x60B8C0, 0x621000, 0x60BE60, 0x60BE60, 0x60E240),
    (29, 0x60BEA0, 0x621158, 0x60C440, 0x60C440, 0x15E9FC),
    (56, 0x60C480, 0x6212C8, 0x60CA40, 0x60CA40, 0x60E2F0),
    (57, 0x60CA80, 0x62154C, 0x60CFA0, 0x60CFA0, 0x60E410),
    (58, 0x60CFE0, 0x6216AC, 0x60D5C0, 0x60D5C0, 0x60E4F8),
    (59, 0x60DB80, 0x621824, 0x60E1C0, 0x60E1C0, 0x60E5E0),
)
P4_REUSE = {27: 12, 29: 14}
NATIVE_GUARDS = (
    (0x353304, 0x3534D8, "98BE1E1DBF1E38E806C03261326AADECAAC3CE2D0F35462BA3E3B4D9CDE83C43", "fighter resource constructor"),
    (0xCBE28, 0xCC110, "D506A6E6C9146EB4B1F3BA2EFB1C1F73C552587DF08408DC3251D0305515A590", "dynamic resource selector 1"),
    (0xCC304, 0xCC708, "26FFE9E293EDAC9440B8F1AC71D4225922ED136C3E11A7412605AA57A796D406", "dynamic resource selector 2"),
    (0x358254, 0x3592BC, "9524C97DE93BBDDC851626A81134A0ABBCD4FD07D9D5A7791E90378F52859FD3", "P4 consumer and timer/motion states"),
    (0x3593E0, 0x359660, "973CA1F3596D91F8491CE70837E60FD7BAF230E216783A97DC286BE503D96192", "companion resource consumer"),
    (0x132EC, 0x133A4, "5EA82F6D3E90C79CD0CCC688180E3A007A67825ABB007462D32235EC595E8CA8", "palette 34-byte block consumer"),
    (0x1297C, 0x129B8, "9F56593FBDB080414AB6C6C04584EF14F7BB8E0747AAE480B6CAF18F4B191506", "P1 A metadata palette selector"),
)
SOURCE_GUARDS = (
    (0x7437B1, 0x7438B5, "D8546F2306688FF192FC6BC2F2AB5DCB5943A64D6112A561BCC4E130C4CA5D9F", "15-row main/evolution/companion routing"),
    (0x781064, 0x78108B, "02E5F2F6D2FEC67A779B72F90AAEC7B6377C192558D6C1ADE38370DD9B739009", "P4 duration producer"),
    (0x781907, 0x781967, "61B53E8B48DFC86F0C59812BC8606A6859966F217149F6A9B8951BE3284FCDD9", "P4 elapsed counter consumers"),
    (0x781831, 0x7818D5, "AB4D30E4DF5B8931FB2DE83AD4127D0FFE06BEA1FECC54E6A740D2082373AC24", "P4 motion input selection"),
    (0x781094, 0x7810D4, "3780A66C4DD52BADE816D63D576F53005A33C6B25D8DBF62F8FC922B9096E7C4", "P4 motion field consumers"),
    (0x780FA8, 0x780FDB, "E57A5EBC5532006B9FE1D632FBCB62BF1E047B236AB19AFD74D5B75646822450", "P4 word4 input mask"),
    (0x781018, 0x78101F, "E227165F2DA33DB7DDBB3EB4BF6CB147F5CC7FFA5204DC709FE19E2B7635DAF9", "P4 word4 class-dependent value"),
    (0x781AFE, 0x781B1D, "7677519D16055181B8DA8AF4C17B14A842B8DC7DB9357F56228CFF4FE19F16AC", "companion pointer consumer"),
    (0x7525D4, 0x7525F5, "F48068EE7B8E524547BC2C6B2EE72E08AE4A0767410299632A5700191D52884F", "source A metadata palette selector"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def word(data, offset):
    need(0 <= offset <= len(data) - 4, "word in ROM")
    return struct.unpack_from("<I", data, offset)[0]


def pointer(data, offset):
    displacement, segment, bank = struct.unpack_from("<3H", data, offset)
    linear = segment * 16 + displacement
    need(0x20000 <= linear < 0x30000, "C2 source pointer")
    return (bank & ((len(data) >> 16) - 1)) * 0x10000 + linear - 0x20000


def p4_source(data, record, table):
    source = pointer(data, table + record * 32 + 24)
    relative, count = struct.unpack_from("<2H", data, source)
    need(relative == 4 and 0 < count <= 128, "source P4 header")
    offsets = struct.unpack_from(f"<{count}H", data, source + 4)
    need(len(set(offsets)) == count, "source P4 distinct records")
    need(min(offsets) == 4 + count * 2 and
         tuple(offsets) == tuple(range(min(offsets), min(offsets) + count * 36, 36)),
         "source P4 complete contiguous population")
    items = [struct.unpack_from("<18H", data, source + offset) for offset in offsets]
    need(all(value == 0 or value in offsets for item in items for value in item[11:]),
         "source P4 links target declared records")
    extent = max(offsets) + 36
    return source, data[source:source + extent], offsets, items


def scale(value, numerator, denominator, mode):
    signed = value - 0x10000 if value & 0x8000 else value
    fraction = Fraction(signed * numerator, denominator)
    sign = -1 if fraction < 0 else 1
    quotient, remainder = divmod(abs(fraction.numerator), fraction.denominator)
    if mode == "truncate":
        result = sign * quotient
    elif mode == "nearest-away":
        result = sign * (quotient + (2 * remainder >= fraction.denominator))
    elif mode == "nearest-even":
        result = round(fraction)
    else:
        raise ValueError("unknown scalar conversion")
    need(-0x8000 <= result < 0x8000, "converted signed motion/counter fits")
    return result & 0xFFFF


def p4_convert(data, record, target, events):
    source, original, relatives, items = p4_source(data, record, 0x740000)
    count = len(items)
    starts = [target + 8 + count * 4 + index * 52 for index in range(count)]
    links = dict(zip(relatives, starts, strict=True))
    output = bytearray(8 + count * 56)
    struct.pack_into("<2I", output, 0, BASE + target + 8, count)
    struct.pack_into(f"<{count}I", output, 8, *(BASE + at for at in starts))
    evidence = []
    for index, item in enumerate(items):
        need(item[0] >> 8 <= 7, "native motion dispatch population")
        need(item[1] & 255 <= 4, "native byte state dispatch population")
        need(item[2] < events, "P4 animation event is within complete P1")
        fields = list(item[:11])
        # Flags/indices/input bitmask fields 0,1,2,4,5,6 are never scaled.
        for field, numerator, denominator, mode in (
                (3, 4, 5, "nearest-away"), (7, 5, 4, "truncate"),
                (8, 5, 4, "truncate"), (9, 25, 16, "nearest-even"),
                (10, 25, 16, "nearest-away")):
            fields[field] = scale(item[field], numerator, denominator, mode)
        at = starts[index] - target
        struct.pack_into("<12H", output, at, *fields, 0)
        struct.pack_into("<7I", output, at + 24,
                         *(BASE + links[v] if v else 0 for v in item[11:]))
        evidence.append({"index": index, "source_words": list(item),
                         "native_scalars": fields, "target": starts[index]})
    return bytes(output), {"record": record, "source": source, "source_bytes": len(original),
                           "source_sha256": sha(original), "target": target,
                           "bytes": len(output), "count": count, "items": evidence}


def complete_palette(data, record, field, target):
    source = pointer(data, 0x740000 + record * 32 + field * 6)
    count, mode = struct.unpack_from("<2H", data, source)
    need((count, mode) == (2, 1), "record13 two-bank palette header")
    original = data[source:source + 4 + count * 34]
    output = bytearray(original)
    rows = []
    for index in range(count):
        at = 4 + index * 34
        bank = struct.unpack_from("<H", original, at)[0]
        need(bank == 8 + index, "source palette bank sequence")
        colors = struct.unpack_from("<16H", original, at + 2)
        converted = [convert_color(color) for color in colors]
        struct.pack_into("<16H", output, at + 2, *converted)
        rows.append({"index": index, "bank": bank, "source_colors": list(colors),
                     "native_colors": converted})
    return bytes(output), {"record": record, "field": field, "source": source,
                           "target": target, "bytes": len(output), "blocks": rows,
                           "source_sha256": sha(original), "sha256": sha(output)}


def validate_added_resource(data, source, spec):
    record, p0, p1, p2, p3, p4 = spec
    src_p0 = pointer(source, 0x740000 + record * 32)
    layouts, _ = source_layout(source, src_p0)
    _, events, frames = source_commands(source, record)
    indexed = bool(struct.unpack_from("<H", source, src_p0 + 14)[0] & 2)
    layout_table, descriptors = word(data, p0) - BASE, word(data, p0 + 4) - BASE
    need(word(data, p1) == BASE + p1 + 8, "native P1 event table")
    checked, palette_selections = 0, []
    palette_counts = [struct.unpack_from("<H", data, palette)[0] for palette in (p2, p3)]
    for event in range(events):
        count, commands, a_metadata, _b = struct.unpack_from("<4I", data, p1 + 8 + event * 16)
        need(count == sum(frame[0] == event for frame in frames), "native event population")
        for index in range(count):
            at = commands - BASE + index * 16
            layout, tile = struct.unpack_from("<2H", data, at + 2)
            if struct.unpack_from("<H", data, at + 6)[0] & 0x200:
                selector = struct.unpack_from("<H", data, a_metadata - BASE + 6)[0]
                need(all(selector < count for count in palette_counts),
                     "native A-selected palette block exists for both variants")
                palette_selections.append({"event": event, "command": index, "selector": selector})
            need(layout < len(layouts), "native P1 layout index")
            parts, items = struct.unpack_from("<2I", data, layout_table + layout * 8)
            need(parts == layouts[layout][0], "native layout count")
            length, pixels = struct.unpack_from("<2I", data, descriptors + (tile if indexed else 0) * 8)
            need(0 < length <= 0x8000 and BASE <= pixels <= BASE + len(data) - length,
                 "native pixel descriptor")
            need(BASE <= items <= BASE + len(data) - parts * 4, "native parts pointer")
            need(max(data[items - BASE + part * 4] for part in range(parts)) * 32 + 32 <= length,
                 "all native parts lie inside selected tile payload")
            checked += 1
    _s, _body, relatives, _items = p4_source(source, record, 0x740000)
    need(word(data, p4 + 4) == len(relatives), "native P4 item count")
    return {"record": record, "fields": [p0, p1, p2, p3, p4],
            "events": events, "commands_checked": checked, "layouts": len(layouts),
            "palette_selections": palette_selections}


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (INPUT, GBA, OLD, WSC),
         "exact complete-P1 predecessor and original input identities")
    need(len(before) == 0x800000, "expanded ROM size")
    for data, contracts in ((before, NATIVE_GUARDS), (source, SOURCE_GUARDS)):
        for start, end, digest, label in contracts:
            need(sha(data[start:end]) == digest, label)
    need(sha(old[0x393386:0x393472]) ==
         "40F2797434DA8E1E7FE7E2739386B628A0A26AD13FA8C2CE2599218F7E16F10D",
         "commercial 12-row constructor lineage")
    need(GROUPS[1] - GROUPS[0] == GROUPS[3] - GROUPS[2] == 15 * 32,
         "same evolution delta for main and companion")
    tables = [bytearray(15 * 32) for _ in GROUPS]
    preserved = []
    for group, count in enumerate((12, 12, 11, 11)):
        for index in range(count):
            retail = 0xD3FB8 + (group * 12 + index) * 32
            original = gba[retail:retail + 32]
            need(original[20:] == bytes(12), "retail record trailing fields are zero")
            tables[group][index * 32:index * 32 + 32] = original
            preserved.append({"group": group, "id": index, "retail": retail,
                              "destination": GROUPS[group] + index * 32, "sha256": sha(original)})
    writes, p4_report, reuse_report, scalar_repairs, palette_report = [], [], [], [], []
    for field, target in ((2, 0x60E700), (3, 0x60E748)):
        blob, details = complete_palette(source, 13, field, target)
        writes.append((target, blob, "complete record13 multi-palette", True))
        palette_report.append(details)
    for spec in MAIN + COMPANIONS:
        record, *fields = spec
        group, index = divmod(record, 15)
        need(group < 4, "source resource group")
        struct.pack_into("<5I", tables[group], index * 32, *(BASE + p for p in fields))
        _, events, _ = source_commands(source, record)
        blob, details = p4_convert(source, record, fields[4], events)
        previous = before[fields[4]:fields[4] + len(blob)]
        if record in P4_REUSE:
            old_record = P4_REUSE[record]
            old_at, old_body, _, _ = p4_source(old, old_record, 0x390000)
            src_at, src_body, _, _ = p4_source(source, record, 0x740000)
            need(src_body == old_body, "complete shared source P4 container identity")
            need(word(gba, 0xD3FB8 + old_record * 32 + 16) == BASE + fields[4],
                 "commercial P4 source/native resource pair")
            need(blob == previous == gba[fields[4]:fields[4] + len(blob)],
                 "reused native P4 matches explicit semantic conversion")
            reuse_report.append({"record": record, "old_record": old_record,
                                 "source": src_at, "old_source": old_at,
                                 "source_bytes": len(src_body), "source_sha256": sha(src_body),
                                 "native": fields[4], "native_sha256": sha(blob)})
        else:
            new = record >= 15 and record not in (41, 42, 43, 44)
            if new:
                need(previous == b"\xff" * len(blob), "Expected Write blank companion P4")
            else:
                need(word(before, fields[4]) == BASE + fields[4] + 8 and
                     word(before, fields[4] + 4) == details["count"], "same resident main P4 population")
                for i in range(0, len(blob), 2):
                    if previous[i:i + 2] != blob[i:i + 2]:
                        scalar_repairs.append({"record": record, "raw": fields[4] + i,
                                               "before": previous[i:i + 2].hex(), "after": blob[i:i + 2].hex()})
            writes.append((fields[4], blob, f"source P4 resource {record}", new))
        p4_report.append(details)
    need(len(scalar_repairs) == 3, "exact three legacy main scalar repairs")
    for group, (target, table) in enumerate(zip(GROUPS, tables, strict=True)):
        need(all(table[i * 32 + 20:i * 32 + 32] == bytes(12) for i in range(15)),
             "all canonical record tails zero")
        writes.append((target, bytes(table), f"canonical resource group {group}", group >= 2))
    for raw in EVOLUTION_LITERALS:
        need(word(before, raw) == 0x080D42B8, "Expected Write dynamic evolution literal")
        writes.append((raw, struct.pack("<I", BASE + GROUPS[2]), "dynamic evolution selector", False))
    for raw in OPENING_LITERALS:
        need(word(before, raw) == 0x080D42B8, "opening selector keeps original view")
    need(word(before, 0x853F4) == 0x085B5400, "previous opening selector13 repair retained")
    allocations = [(raw, raw + len(blob)) for raw, blob, _label, new in writes if new]
    need(not inbound(before, allocations), "new allocation has an incoming candidate")
    after, used, report_writes = bytearray(before), set(), []
    for raw, blob, label, new in writes:
        extent = set(range(raw, raw + len(blob)))
        need(not used.intersection(extent), "Expected Writes cannot overlap")
        used |= extent
        previous = before[raw:raw + len(blob)]
        if new:
            need(previous == b"\xff" * len(blob), "Expected Write unused allocation")
        after[raw:raw + len(blob)] = blob
        report_writes.append({"raw": raw, "bytes": len(blob), "label": label, "new_allocation": new,
                              "before_sha256": sha(previous), "after_sha256": sha(blob)})
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {raw + i for raw, blob, _label, _new in writes
                for i, value in enumerate(blob) if before[raw + i] != value}
    need(changed == expected, "complete ROM diff equals Expected Writes")
    consumed = [validate_added_resource(after, source, spec) for spec in MAIN + COMPANIONS]
    return bytes(after), {"schema": 1, "kind": "canonical-character-resource-routing",
                         "input_sha256": INPUT, "output_sha256": sha(after),
                         "groups": list(GROUPS), "group_rows": 15, "record_bytes": 32,
                         "field_offsets": [0, 4, 8, 12, 16], "zero_tail_bytes": 12,
                         "preserved_retail_rows": preserved, "added_resources": consumed,
                         "P4_resources": p4_report, "P4_reuse": reuse_report,
                         "completed_palettes": palette_report,
                         "main_P4_scalar_repairs": scalar_repairs,
                         "scalar_policy": {"duration_word3": "signed 4/5 nearest-away",
                                           "velocity_words7_8": "signed 5/4 truncate toward zero",
                                           "acceleration_word9": "signed25/16 nearest-even",
                                           "acceleration_word10": "signed25/16 nearest-away",
                                           "other_words": "source bit identity; no per-value oracle inference"},
                         "expected_writes": report_writes, "actual_changed_bytes": len(changed),
                         "new_allocations": allocations, "inbound_candidates": [],
                         "dynamic_evolution_literals": list(EVOLUTION_LITERALS),
                         "preserved_opening_literals": list(OPENING_LITERALS),
                         "source_consumer_guards": SOURCE_GUARDS, "native_consumer_guards": NATIVE_GUARDS,
                         "new_RAM": False, "new_callbacks": False,
                         "limits": "integer timing/motion quantization remains; runtime gameplay is separate verification"}


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
    print("[character-resource-routing] " + report["output_sha256"])


if __name__ == "__main__":
    main()
