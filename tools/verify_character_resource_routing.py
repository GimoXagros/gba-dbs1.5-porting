#!/usr/bin/env python3
"""Independent four-group ABI, complete palette and typed P4 graph verifier.

Only another independent verifier is reused for complete P1/renderer walks.
No builder or generated manifest supplies expected resource bytes or fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_character_p1_completion import all_resources as verify_complete_p1

BASE = 0x08000000
BEFORE = "3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA"
AFTER = "3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GROUPS = (0x4A80F8, 0x4A82D8, 0x60B000, 0x60B1E0)
EVOLUTION = (0x3534B8, 0xCC230, 0xCC708)
OPENING = (0x850E0, 0x850E4, 0x850E8, 0x85794, 0x86288, 0x862B8,
           0x87018, 0x87020, 0x8718C, 0x87194, 0x87388, 0x87394)
ADDED = (
    (12, 0x448000, 0x611800, 0x4A12A0, 0x4A12C8, 0x47A000),
    (13, 0x400000, 0x6156B4, 0x60E700, 0x60E748, 0x47A858),
    (14, 0x420AC0, 0x6184A0, 0x4A1340, 0x4A1368, 0x47AEB8),
    (41, 0x4B0000, 0x61B4BC, 0x4A1390, 0x4A1390, 0x568000),
    (42, 0x4CEAE0, 0x61C288, 0x4A13B8, 0x4A13B8, 0x5682E0),
    (43, 0x4E85E0, 0x61CF0C, 0x4A13E0, 0x4A13E0, 0x568550),
    (44, 0x4FB380, 0x61DB48, 0x4A1408, 0x4A1408, 0x5688D8),
    (27, 0x60B400, 0x61E71C, 0x60B880, 0x60B880, 0x0FE400),
    (28, 0x60B8C0, 0x621000, 0x60BE60, 0x60BE60, 0x60E240),
    (29, 0x60BEA0, 0x621158, 0x60C440, 0x60C440, 0x15E9FC),
    (56, 0x60C480, 0x6212C8, 0x60CA40, 0x60CA40, 0x60E2F0),
    (57, 0x60CA80, 0x62154C, 0x60CFA0, 0x60CFA0, 0x60E410),
    (58, 0x60CFE0, 0x6216AC, 0x60D5C0, 0x60D5C0, 0x60E4F8),
    (59, 0x60DB80, 0x621824, 0x60E1C0, 0x60E1C0, 0x60E5E0),
)
NEW = ((0x60B000, 0x60B3C0), (0x60E240, 0x60E6C8), (0x60E700, 0x60E790))


def need(value, label):
    if not value:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, pos, n):
    need(0 <= pos <= len(data) and 0 <= n <= len(data) - pos, "ROM extent")
    return data[pos:pos + n]


def h(data, pos):
    return struct.unpack("<H", cut(data, pos, 2))[0]


def u(data, pos):
    return struct.unpack("<I", cut(data, pos, 4))[0]


def pointer(data, pos, n=1):
    result = u(data, pos) - BASE
    cut(data, result, n)
    return result


def far(data, pos):
    offset, segment, bank = struct.unpack("<3H", cut(data, pos, 6))
    physical = segment * 16 + offset
    need(0x20000 <= physical < 0x30000 and 0x80 <= bank <= 0xFF, "source C2 address")
    return (bank & (len(data) // 65536 - 1)) * 65536 + physical - 0x20000


def source_p4(source, record, table=0x740000):
    at = far(source, table + record * 32 + 24)
    need(h(source, at) == 4, "source P4 table starts after header")
    count = h(source, at + 2)
    need(0 < count <= 128, "source P4 item population")
    offsets = tuple(h(source, at + 4 + 2 * n) for n in range(count))
    need(offsets == tuple(4 + count * 2 + index * 36 for index in range(count)), "source P4 item boundaries")
    items = [struct.unpack("<18H", cut(source, at + offset, 36)) for offset in offsets]
    need(all(link == 0 or link in offsets for item in items for link in item[11:]), "source P4 link domain")
    return at, offsets, items, cut(source, at, offsets[-1] + 36)


def scalar(value, field):
    signed = value - 65536 if value >= 32768 else value
    if field not in (3, 7, 8, 9, 10):
        return value
    numerator, denominator = (4, 5) if field == 3 else ((5, 4) if field in (7, 8) else (25, 16))
    q, r = divmod(abs(signed) * numerator, denominator)
    if field in (3, 10):
        q += 2 * r >= denominator
    elif field == 9:
        q += 2 * r > denominator or 2 * r == denominator and q % 2 == 1
    q = q if signed >= 0 else -q
    need(-32768 <= q <= 32767, "converted P4 signed range")
    return q & 65535


def p4_check(after, source, spec, old, gba):
    record, _p0, p1, _p2, _p3, target = spec
    src, relatives, items, original = source_p4(source, record)
    table = pointer(after, target, len(items) * 4)
    need(table == target + 8 and u(after, target + 4) == len(items), "native P4 header and population")
    starts = [pointer(after, table + index * 4, 52) for index in range(len(items))]
    need(starts == [table + len(items) * 4 + index * 52 for index in range(len(items))], "native P4 item boundaries")
    source_p1 = far(source, 0x740000 + record * 32 + 6)
    events = (h(source, source_p1 + 6) - 4) // 8
    need(pointer(after, p1) == p1 + 8, "P4/P1 binding")
    for index, (at, item) in enumerate(zip(starts, items, strict=True)):
        need(item[0] >> 8 < 8 and item[1] & 255 < 5, "native motion and state dispatch bounds")
        need(item[2] < events, "P4 animation selects a complete source P1 event")
        observed = struct.unpack("<12H", cut(after, at, 24))
        expected = tuple(scalar(value, field) for field, value in enumerate(item[:11])) + (0,)
        need(observed == expected, f"typed source P4 scalars for record {record} item {index}")
        for field, relative in enumerate(item[11:]):
            expected_pointer = BASE + starts[relatives.index(relative)] if relative else 0
            need(u(after, at + 24 + field * 4) == expected_pointer, "source P4 graph edge and null identity")
    reused = None
    if record in (27, 29):
        old_record = {27: 12, 29: 14}[record]
        old_source, _, _, old_body = source_p4(old, old_record, 0x390000)
        need(original == old_body, "whole old/new source P4 identity")
        need(pointer(gba, 0xD3FB8 + old_record * 32 + 16) == target, "actual commercial P4 resource pair")
        need(cut(after, target, 8 + len(items) * 56) == cut(gba, target, 8 + len(items) * 56),
             "native P4 commercial reuse identity")
        reused = {"source_record": old_record, "source": old_source}
    return {"record": record, "source": src, "source_bytes": len(original), "source_sha256": sha(original),
            "target": target, "bytes": 8 + len(items) * 56, "items": len(items), "reused": reused}


def palette_check(after, target, source, source_at):
    count, mode = struct.unpack("<HH", cut(source, source_at, 4))
    need(0 < count <= 2 and mode == 1, "source palette profile")
    length = 4 + count * 34
    need(cut(after, target, 4) == cut(source, source_at, 4), "native palette count and mode")
    for block in range(count):
        s, d = source_at + 4 + block * 34, target + 4 + block * 34
        need(h(after, d) == h(source, s), "palette bank preserved")
        for color in range(16):
            value = h(after, d + 2 + color * 2)
            need(value < 32768, "native color high bit")
            channels = (value & 31, value >> 5 & 31, value >> 10 & 31)
            need(all(c == 0 or c >= 3 and c % 2 for c in channels), "expanded native channel profile")
            r, g, b = (c // 2 for c in channels)
            need((r << 8 | g << 4 | b) == h(source, s + 2 + color * 2), "inverse full palette color")
    return count, length


def table_check(after, gba, source, old):
    added = {spec[0]: spec for spec in ADDED}
    retail, added_rows, palette_selectors, p4_rows = 0, [], [], []
    for group, table in enumerate(GROUPS):
        for ident in range(15):
            at, source_record = table + ident * 32, group * 15 + ident
            need(cut(after, at + 20, 12) == bytes(12), "canonical record trailing padding")
            if source_record not in added:
                original = 0xD3FB8 + (group * 12 + ident) * 32
                need(ident < (12 if group < 2 else 11), "retail row population")
                need(cut(after, at, 32) == cut(gba, original, 32), "whole canonical retail row preserved")
                retail += 1
                continue
            spec = added[source_record]
            fields = tuple(pointer(after, at + n * 4) for n in range(5))
            need(fields == spec[1:], "actual same-ID five-field ABI")
            source_p0 = far(source, 0x740000 + source_record * 32)
            need(cut(after, fields[0] + 8, 8) == cut(source, source_p0 + 8, 8), "P0 constants/source identity")
            counts = []
            for field in (2, 3):
                palette = far(source, 0x740000 + source_record * 32 + field * 6)
                counts.append(palette_check(after, fields[field], source, palette)[0])
            source_p1 = far(source, 0x740000 + source_record * 32 + 6)
            events = (h(source, source_p1 + 6) - 4) // 8
            table1 = pointer(after, fields[1])
            for event in range(events):
                row = table1 + event * 16
                command = pointer(after, row + 4)
                metadata = pointer(after, row + 8)
                for frame in range(u(after, row)):
                    if h(after, command + frame * 16 + 6) & 0x200:
                        selector = h(after, metadata + 6)
                        need(all(selector < count for count in counts), "every live palette selector is owned")
                        for palette in fields[2:4]:
                            bank = h(after, palette + 4 + selector * 34)
                            colors = cut(after, palette + 8 + selector * 34, 30)
                            need(0 <= bank <= 15 and len(colors) == 30, "actual native palette bank and15 visible colors")
                        palette_selectors.append({"record": source_record, "event": event,
                                                  "frame": frame, "selector": selector})
            p4_rows.append(p4_check(after, source, spec, old, gba))
            if group in (0, 2):
                _at, _relatives, items, _body = source_p4(source, source_record)
                companion = source_record + 15
                _c_at, c_relatives, _c_items, _c_body = source_p4(source, companion)
                need(all(item[1] >> 8 < len(c_relatives) for item in items), "companion P4 action byte domain")
            added_rows.append({"record": source_record, "group": group, "id": ident,
                               "native_row": at, "fields": fields, "palette_entry_counts": counts})
    need(retail == 46 and len(added_rows) == 14, "complete sixty-row population")
    need(palette_selectors == [{"record": 13, "event": 111, "frame": 0, "selector": 1}],
         "exact noninitial palette-selector population")
    return added_rows, p4_rows, palette_selectors


def native_contract(after, source):
    expected = {
        0x353348: 0xE59D001C, 0x35334C: 0xE1A00280, 0x353370: 0xE59F0140,
        0x353374: 0xE59F8140, 0x353378: 0xE0400008, 0x35337C: 0xE0811000,
        0x353380: 0xE0855000, 0x353394: 0xE0899005, 0x353398: 0xE5998004,
        0x3533A8: 0xE5998000, 0x3533BC: 0xE0899001, 0x3533C0: 0xE5998008,
        0x35340C: 0xE7988005, 0x353438: 0xE7988001, 0x353474: 0xE7988001,
        0x3534A0: 0xE0855008, 0x3534A4: 0xE5815080,
        0x3593E0: 0xE5943080, 0x3594E0: 0xE5985000,
        0x35950C: 0xE5958004, 0x35951C: 0xE5958000, 0x35952C: 0xE5958008,
        0x3595A8: 0xE5958010, 0xCBE30: 0xE1B00280,
        0xCBEA0: 0xE5948004, 0xCBEB0: 0xE5948000, 0xCBEC0: 0xE5918008,
        0xCC378: 0xE5948004, 0xCC388: 0xE5948000, 0xCC398: 0xE5918008,
        0x3584A0: 0xE1D500F6, 0x3584A4: 0xE1C409B4,
        0x358DB8: 0xE5D51002, 0x3590E4: 0xE1D489F4, 0x3590E8: 0xE2588001,
        0x3590EC: 0xE1C489B4, 0x359114: 0xE1D489F4,
        0x359034: 0xE1D500FE, 0x359038: 0xE1D511F0,
        0x35903C: 0xE1D521F2, 0x359040: 0xE1D531F4,
        0x358514: 0xE1C404B2, 0x358534: 0xE1C414B4,
        0x358554: 0xE1C424B6, 0x358574: 0xE1C434B8,
        0x3583BC: 0xE1D580F8, 0x3583C0: 0xE0111008,
        0x358434: 0xE1D500F8, 0x358438: 0xE1C406B4,
        0x129A4: 0xE1D180B6, 0x132F4: 0xE2844004,
        0x132FC: 0xE1A02288, 0x13300: 0xE0822088,
        0x13304: 0xE0844002, 0x13308: 0xE0D480B4,
    }
    for at, value in expected.items():
        need(u(after, at) == value, f"native typed consumer instruction {at:X}")
    for at, value in ((0x3534BC, GROUPS[0]), (0x3534C0, GROUPS[0]), (0x3534C4, GROUPS[0]),
                      (0x3534C8, GROUPS[0] + 16), (0x3534CC, GROUPS[0] + 8),
                      (0x3534D0, GROUPS[1] + 8), (0x3534D4, GROUPS[1]),
                      (0xCC234, GROUPS[0]), (0xCC70C, GROUPS[0])):
        need(u(after, at) == BASE + value, "live constructor base/field literal")
    for at in EVOLUTION:
        need(u(after, at) == BASE + GROUPS[2], "all dynamic evolution views repaired")
    for at in OPENING:
        need(u(after, at) == BASE + 0xD42B8, "opening selector retains separate original view")
    need(u(after, 0x853F4) == BASE + 0x5B5400, "opening selector13 prior repair retained")
    for at, encoded in {
        0x781064: "268B450689447E", 0x781907: "FF4C7E7903",
        0x781926: "FF4C7E791F", 0x78187E: "268B450E268B5D10268B4D12268B5514",
        0x7810A1: "894432", 0x7810B1: "895C34", 0x7810C1: "894C36", 0x7810D1: "895438",
        0x780FBE: "26235D08", 0x781018: "268B4508894450",
        0x7525D4: "268B5D208B4F06", 0x7525E6: "FF7706",
        0x7523A8: "83C6048B460CD3E003460C03460C03F0",
        0x7437B1: "8B4608C1E005", 0x7438B1: "81C7E001",
    }.items():
        raw = bytes.fromhex(encoded)
        need(cut(source, at, len(raw)) == raw, f"source field consumer {at:X}")
    return len(expected)


def simulated_consumers(after):
    delta = u(after, 0x3534B8) - u(after, 0x3534BC)
    need(delta == GROUPS[2] - GROUPS[0] == GROUPS[3] - GROUPS[1], "one evolution delta serves both groups")
    cases = 0
    for ident in range(15):
        for evolved in (0, 1):
            displacement = ident * 32 + evolved * delta
            main, companion = GROUPS[0] + displacement, GROUPS[1] + displacement
            need(main == GROUPS[evolved * 2] + ident * 32 and
                 companion == GROUPS[evolved * 2 + 1] + ident * 32, "same-ID main and companion addresses")
            for alternate in (0, 1):
                main_fields = (u(after, main), u(after, main + 4),
                               u(after, main + 8 + alternate * 4), u(after, main + 16))
                comp_fields = (u(after, companion), u(after, companion + 4),
                               u(after, companion + 8 + alternate * 4), u(after, companion + 16))
                need(all(BASE <= value < BASE + len(after) for value in main_fields + comp_fields),
                     "constructor consumed resource pointers")
                cases += 1
    return cases


def diff_check(before, after, p4_rows):
    need(len(before) == len(after) == 0x800000, "ROM size")
    spans = [(table, table + 480) for table in GROUPS]
    spans += [(at, at + 4) for at in EVOLUTION]
    spans += [(row["target"], row["target"] + row["bytes"]) for row in p4_rows if not row["reused"]]
    spans += [(0x60E700, 0x60E790)]
    cursor = 0
    for start, stop in sorted(spans):
        need(cursor <= start and before[cursor:start] == after[cursor:start], "unowned ROM bytes retained")
        cursor = stop
    need(before[cursor:] == after[cursor:], "unowned ROM tail retained")
    for start, stop in NEW:
        need(before[start:stop] == b"\xff" * (stop - start), "new owned storage Expected Write")
    for at in EVOLUTION:
        need(u(before, at) == BASE + 0xD42B8, "Expected Write prior dynamic evolution view")
    scalar_changes = []
    for row in p4_rows:
        if row["record"] in (12, 13, 14, 41, 42, 43, 44):
            start, stop = row["target"], row["target"] + row["bytes"]
            for at in range(start, stop, 2):
                if h(before, at) != h(after, at):
                    scalar_changes.append((row["record"], at, h(before, at), h(after, at)))
    need(len(scalar_changes) == 3 and sorted((r, old, new) for r, _, old, new in scalar_changes) ==
         [(12, 219, 218), (13, 36, 29), (13, 219, 218)], "exact three former tuning-inference repairs")
    return spans, scalar_changes


def inbound(data):
    result = []
    for at in range(len(data) - 3):
        word = struct.unpack_from("<I", data, at)[0]
        if any(BASE + start <= word < BASE + stop for start, stop in NEW):
            result.append((at, word, "pointer including unaligned"))
        if at % 4 == 0 and word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            d = word & 0xFFFFFF
            d -= 0x1000000 if d & 0x800000 else 0
            destination = at + 8 + d * 4
            if any(start <= destination < stop for start, stop in NEW):
                result.append((at, destination, "ARM branch-like word"))
    return result


def rejects(call, label):
    try:
        call()
    except (ValueError, struct.error, IndexError):
        return label
    raise ValueError(f"negative fixture accepted: {label}")


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in vars(args)), "save paths forbidden")
    before, after, gba, old, source = [getattr(args, name).read_bytes() for name in
                                      ("before", "after", "gba", "wsc10", "wsc15")]
    need(tuple(map(sha, (before, after, gba, old, source))) == (BEFORE, AFTER, GBA, OLD, WSC), "input identities")
    instructions = native_contract(after, source)
    rows, p4_rows, selectors = table_check(after, gba, source, old)
    _p1_rows, p1_totals = verify_complete_p1(after, source)
    finite_cases = simulated_consumers(after)
    spans, scalar_changes = diff_check(before, after, p4_rows)
    need(not inbound(before), "new intervals have no predecessor inbound candidate")
    negatives = [rejects(lambda: table_check(before, gba, source, old), "historical staggered table ABI")]
    for label, at, replacement, contract in (
        ("palette passed as P0", GROUPS[0] + 12 * 32, struct.pack("<I", BASE + 0x4A12A0), "tables"),
        ("companion P1 wrong form", GROUPS[3] + 13 * 32 + 4, struct.pack("<I", BASE + 0x621000), "tables"),
        ("nonzero stale row padding", GROUPS[0] + 11 * 32 + 24, b"\x01", "tables"),
        ("truncated two-entry palette", GROUPS[0] + 13 * 32 + 8, struct.pack("<I", BASE + 0x4A12F0), "tables"),
        ("palette second entry pixel", 0x60E700 + 42, bytes([after[0x60E700 + 42] ^ 2]), "tables"),
        ("P4 packed state high byte lost", 0x47A858 + 8 + 29 * 4 + 18 * 52 + 2, bytes(2), "tables"),
        ("P4 duration old tuned36", scalar_changes[1][1], struct.pack("<H", scalar_changes[1][2]), "tables"),
        ("P4 external graph link", 0x60E240 + 8 + 3 * 4 + 24, struct.pack("<I", BASE + 0x60B400), "tables"),
        ("evolution constructor old table", EVOLUTION[0], struct.pack("<I", BASE + 0xD42B8), "code"),
        ("second dynamic evolution old table", EVOLUTION[2], struct.pack("<I", BASE + 0xD42B8), "code"),
        ("opening view incorrectly redirected", OPENING[0], struct.pack("<I", BASE + GROUPS[2]), "code"),
        ("native P4 word4 treated as velocity", 0x358438, struct.pack("<I", 0xE1C404B2), "code"),
    ):
        mutant = bytearray(after)
        mutant[at:at + len(replacement)] = replacement
        check = (lambda: table_check(mutant, gba, source, old)) if contract == "tables" else (lambda: native_contract(mutant, source))
        negatives.append(rejects(check, label))
    inverse = bytearray(after)
    for start, stop in spans:
        inverse[start:stop] = before[start:stop]
    need(bytes(inverse) == before, "Expected Write inverse restores exact P1 predecessor")
    report = {"schema": 1, "kind": "independent-canonical-character-resource-routing", "status": "PASS",
              "before_sha256": BEFORE, "after_sha256": AFTER, "source_sha256": WSC,
              "native_groups": GROUPS, "rows_per_group": 15, "field_offsets": [0, 4, 8, 12, 16],
              "retail_rows_preserved": 46, "added_rows": rows, "P4_source_graphs": p4_rows,
              "source_palette_selector_domain": selectors, "complete_P1_totals": p1_totals,
              "finite_constructor_form_palette_cases": finite_cases, "guarded_native_instructions": instructions,
              "main_P4_scalar_repairs": scalar_changes, "new_allocations": NEW,
              "predecessor_inbound_candidates": [], "inverse_restores_predecessor": True,
              "negative_cases": negatives,
              "scope_limits": ["typed time/velocity/acceleration conversion uses explicit integer quantization",
                               "commercial rows retain retail tuning", "runtime visual/gameplay verification is separate"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-character-resource-routing] PASS {sha(args.output.read_bytes())}")


if __name__ == "__main__":
    main()
