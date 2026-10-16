#!/usr/bin/env python3
"""Independent source, inverse-pixel, consumer and ownership P0 checks.

No generator or manifest is imported.  Descriptor populations come from every
source P1 event, not the first event's count or a restricted-segment sentinel.
This layer has no P1/P4/table routing claim and does not execute the ROM.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
BEFORE = "E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D"
AFTER = "973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
# Source record, P0, resident P0, reachable descriptors, valid old prefix,
# new descriptor table, end of exact owned allocation.
COMPLETED = (
    (14, 0x32A5E0, 0x420AC0, 324, 260, 0x7C1100, 0x7C9280),
    (43, 0x350000, 0x4E85E0, 77, 59, 0x7D9440, 0x7DE600),
    (44, 0x23E500, 0x4FB380, 78, 61, 0x7F6200, 0x7FACE0),
    (36, 0x364930, 0x50D000, 88, 79, 0x7FAD00, 0x7FCBC0),
)
COMPANIONS = (
    (27, 0x60B400, 0x60B8A8), (28, 0x60B8C0, 0x60BE88),
    (29, 0x60BEA0, 0x60C468), (56, 0x60C480, 0x60CA68),
    (57, 0x60CA80, 0x60CFC8), (58, 0x60CFE0, 0x60D5E8),
    (59, 0x60DB80, 0x60E1E8),
)
ALLOCATIONS = tuple(sorted([(x[5], x[6]) for x in COMPLETED] +
                           [(x[1], x[2]) for x in COMPANIONS]))
HEADER_WRITES = tuple((x[2] + 4, x[2] + 8) for x in COMPLETED)


def need(condition, label):
    if not condition:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, length):
    need(0 <= at <= len(data) and 0 <= length <= len(data) - at, "bounded ROM slice")
    return data[at:at + length]


def half(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def word(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def pointer(data, at, length=1):
    result = word(data, at) - BASE
    cut(data, result, length)
    return result


def far(wsc, at):
    offset, segment, bank = struct.unpack("<3H", cut(wsc, at, 6))
    physical = segment * 16 + offset
    need(0x80 <= bank <= 0xFF and 0x20000 <= physical < 0x30000, "source C2 far pointer")
    return (bank & 127) * 0x10000 + physical - 0x20000


def source_descriptor(wsc, at):
    length, offset, segment, bank = struct.unpack("<4H", cut(wsc, at, 8))
    physical = segment * 16 + offset
    need(length >= 32 and length % 32 == 0 and 0x80 <= bank <= 0xFF,
         "source tile extent and bank")
    need(0x20000 <= physical < physical + length <= 0x30000,
         "source tile copy stays within C2 window")
    return length, (bank & 127) * 0x10000 + physical - 0x20000


def inverse_pixels(packed):
    """Decode GBA nibbles back to four source bitplanes; no forward converter."""
    need(len(packed) % 32 == 0, "whole native 4bpp tiles")
    result = bytearray(len(packed))
    for row in range(len(packed) // 4):
        values = packed[row * 4:row * 4 + 4]
        pixels = [pixel for value in values for pixel in (value & 15, value >> 4)]
        for plane in range(4):
            result[row * 4 + plane] = sum(((pixel >> plane) & 1) << (7 - x)
                                          for x, pixel in enumerate(pixels))
    return bytes(result)


def source_population(wsc, record):
    p0 = far(wsc, 0x740000 + record * 32)
    p1 = far(wsc, 0x740000 + record * 32 + 6)
    need(word(wsc, p0) == 16 and word(wsc, p1) == 4, "direct P0/P1 headers")
    first_layout = half(wsc, p0 + 18)
    need(first_layout > 16 and (first_layout - 16) % 4 == 0, "source layout table geometry")
    layout_count = (first_layout - 16) // 4
    need(layout_count <= 256, "source layout population")
    layouts, cursor = [], first_layout
    for index in range(layout_count):
        n, offset = struct.unpack("<HH", cut(wsc, p0 + 16 + index * 4, 4))
        need(0 < n <= 128 and offset == cursor, "contiguous source layout entries")
        layouts.append((n, cut(wsc, p0 + offset, n * 4)))
        cursor += n * 4
    segment, bank = struct.unpack("<HH", cut(wsc, p0 + 4, 4))
    need(0x2000 <= segment < 0x3000 and 0x80 <= bank <= 0xFF, "source descriptor table mapping")
    table = (bank & 127) * 0x10000 + segment * 16 - 0x20000
    first_command = half(wsc, p1 + 6)
    need(first_command > 4 and (first_command - 4) % 8 == 0, "all source P1 events geometry")
    events = (first_command - 4) // 8
    need(events <= 256, "source P1 event population")
    indexed = bool(half(wsc, p0 + 14) & 2)
    commands, used = [], set()
    for event in range(events):
        count, offset, _a, _b = struct.unpack("<4H", cut(wsc, p1 + 4 + event * 8, 8))
        need(0 < count <= 512 and offset >= first_command, "source command extent")
        for frame in range(count):
            layout, tile = struct.unpack("<HH", cut(wsc, p1 + offset + frame * 12 + 2, 4))
            need(layout < layout_count, "source command selects an owned layout")
            tile = tile if indexed else 0
            used.add(tile)
            commands.append((event, frame, layout, tile))
    need(used and used == set(range(max(used) + 1)), "complete reachable descriptor domain")
    descriptors = [source_descriptor(wsc, table + i * 8) for i in sorted(used)]
    for _event, _frame, layout, tile in commands:
        n, items = layouts[layout]
        need(max(items[i * 4] for i in range(n)) * 32 + 32 <= descriptors[tile][0],
             "every source sprite tile lies inside selected payload")
    return {"record": record, "p0": p0, "p1": p1, "layouts": layouts,
            "table": table, "descriptors": descriptors, "indexed": indexed,
            "events": events, "commands": commands}


def layout_check(after, native, source, wsc):
    layouts = source["layouts"]
    table = pointer(after, native, len(layouts) * 8)
    need(table == native + 16, "native layout table origin")
    need(cut(after, native + 8, 8) == cut(wsc, source["p0"] + 8, 8), "P0 constants preserved")
    cursor = table + len(layouts) * 8
    for index, (count, items) in enumerate(layouts):
        need(word(after, table + index * 8) == count, "native layout count")
        at = pointer(after, table + index * 8 + 4, len(items))
        need(at == cursor and cut(after, at, len(items)) == items, "source layout part bytes and pointer")
        cursor += len(items)
    return cursor


def palette_check(after, native, wsc, source):
    need(cut(after, native, 6) == cut(wsc, source, 6), "palette header identity")
    need(cut(after, native + 38, 2) == b"\0\0", "native palette padding")
    for index in range(16):
        value = half(after, native + 6 + index * 2)
        need(value < 0x8000, "native palette high bit clear")
        r, g, b = value & 31, (value >> 5) & 31, (value >> 10) & 31
        need(all(x == 0 or x >= 3 and x % 2 for x in (r, g, b)), "native expanded channel encoding")
        original = (r // 2) * 256 + (g // 2) * 16 + b // 2
        need(original == half(wsc, source + 6 + index * 2), "inverse native palette color")


def resources(before, after, wsc):
    report, pixels = [], 0
    for record, source_p0, native, count, prefix, table, limit in COMPLETED:
        source = source_population(wsc, record)
        need(source["p0"] == source_p0 and len(source["descriptors"]) == count,
             "completed source descriptor domain")
        layout_check(after, native, source, wsc)
        need(pointer(after, native + 4, count * 8) == table, "completed P0 points to full table")
        old_table = pointer(before, native + 4, prefix * 8)
        cursor = (table + count * 8 + 31) & ~31
        need(cut(after, table + count * 8, cursor - table - count * 8) == bytes(cursor - table - count * 8),
             "descriptor alignment padding")
        for index, (length, source_tiles) in enumerate(source["descriptors"]):
            need(word(after, table + index * 8) == length, "descriptor byte length")
            target = pointer(after, table + index * 8 + 4, length)
            if index < prefix:
                need(cut(after, table + index * 8, 8) == cut(before, old_table + index * 8, 8),
                     "existing descriptor prefix reused without relocation")
            else:
                need(target == cursor, "missing payloads placed consecutively")
                cursor += length
            need(inverse_pixels(cut(after, target, length)) == cut(wsc, source_tiles, length),
                 f"inverse tile pixels for record {record} descriptor {index}")
            pixels += length * 2
        need(cursor == limit, "exact completed allocation end")
        report.append({"record": record, "p0": native, "source_p0": source_p0,
                       "source_p1": source["p1"], "layouts": len(source["layouts"]),
                       "events": source["events"], "commands": len(source["commands"]),
                       "descriptor_count": count, "reused_prefix": prefix,
                       "missing_restored": count - prefix, "allocation": [table, limit]})
    for record, native, limit in COMPANIONS:
        source = source_population(wsc, record)
        need(not source["indexed"] and len(source["descriptors"]) == 1,
             "companion single descriptor consumer")
        need(cut(wsc, source["table"] + 8, 8) == b"\xff" * 8, "companion bounded table terminator")
        end_layout = layout_check(after, native, source, wsc)
        table = pointer(after, native + 4, 8)
        need(table == end_layout, "companion descriptor follows layouts")
        length, source_tiles = source["descriptors"][0]
        need(word(after, table) == length, "companion descriptor length")
        target = pointer(after, table + 4, length)
        need(target == (table + 8 + 31) & ~31, "companion tile alignment")
        need(cut(after, table + 8, target - table - 8) == bytes(target - table - 8), "companion alignment bytes")
        need(inverse_pixels(cut(after, target, length)) == cut(wsc, source_tiles, length),
             "inverse companion tile pixels")
        pixels += length * 2
        cursor, shared, palettes = target + length, {}, []
        for field in (2, 3):
            original = far(wsc, 0x740000 + record * 32 + field * 6)
            if original not in shared:
                shared[original] = cursor
                cursor += 40
            at = shared[original]
            palette_check(after, at, wsc, original)
            palettes.append({"field": field, "source": original, "native": at})
        need(cursor == limit, "exact companion allocation end")
        report.append({"record": record, "p0": native, "source_p0": source["p0"],
                       "source_p1": source["p1"], "layouts": len(source["layouts"]),
                       "events": source["events"], "commands": len(source["commands"]),
                       "descriptor_count": 1, "palettes": palettes,
                       "allocation": [native, limit]})
    return report, pixels


def consumers(after, gba, wsc):
    need(after[0x127E4:0x12DC8] == gba[0x127E4:0x12DC8], "live native renderer unchanged")
    for at, expected in {
        0x12C8C: 0xE5954048, 0x12C90: 0xE594B004, 0x12C98: 0xE3110002,
        0x12C9C: 0x108BB183, 0x12CA0: 0xE59BB004, 0x12CA4: 0xE594A000,
        0x12CA8: 0xE1D521B8, 0x12CAC: 0xE08AA182, 0x12CB0: 0xE59A2000,
        0x12CB4: 0xE59AA004, 0x12D50: 0xE5DA3000, 0x12D54: 0xE08B3283,
        0x12DA0: 0xE28AA004,
    }.items():
        need(word(after, at) == expected, f"actual P0 renderer instruction {at:X}")
    need(cut(wsc, 0x752E91, 0x24) == bytes.fromhex(
        "8B7C028B44068E4404E6C28B560AC1E20303FA268B15268B7502268B4506268E5D04E6C2"),
        "source descriptor length, offset, segment and C2 reads")


def diff_check(before, after):
    need(len(before) == len(after) == 0x800000, "expanded image size")
    for start, stop in ALLOCATIONS:
        need(cut(before, start, stop - start) == b"\xff" * (stop - start), "Expected Write fresh allocation")
    cursor = 0
    for start, stop in sorted(ALLOCATIONS + HEADER_WRITES):
        need(cursor <= start and before[cursor:start] == after[cursor:start], "unowned bytes preserved")
        cursor = stop
    need(before[cursor:] == after[cursor:], "unowned ROM tail preserved")


def inbound(data):
    starts = tuple(a for a, _ in ALLOCATIONS)
    def inside(target):
        index = bisect_right(starts, target) - 1
        return index >= 0 and target < ALLOCATIONS[index][1]
    hits = []
    for raw in range(len(data) - 3):
        target = struct.unpack_from("<I", data, raw)[0] - BASE
        if inside(target):
            hits.append(["pointer including unaligned", raw, target])
    for raw, (instruction,) in enumerate(struct.iter_unpack("<I", data)):
        if instruction >> 28 != 15 and instruction & 0x0E000000 == 0x0A000000:
            displacement = instruction & 0xFFFFFF
            displacement -= 0x1000000 if displacement & 0x800000 else 0
            target = raw * 4 + 8 + displacement * 4
            if inside(target):
                hits.append(["ARM-like B/BL", raw * 4, target])
    return hits


def rejected(call, label):
    try:
        call()
    except (ValueError, struct.error, IndexError):
        return label
    raise ValueError(f"negative fixture accepted: {label}")


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, n).suffix.lower() != ".sav" for n in vars(args)), "save paths forbidden")
    before, after, gba, wsc = [getattr(args, n).read_bytes() for n in ("before", "after", "gba", "wsc15")]
    need(tuple(map(sha, (before, after, gba, wsc))) == (BEFORE, AFTER, GBA, WSC), "exact input identities")
    diff_check(before, after)
    consumers(after, gba, wsc)
    need(not inbound(before), "new allocation has no pre-existing inbound candidate")
    rows, pixels = resources(before, after, wsc)
    negative = [rejected(lambda: resources(before, before, wsc), "historical incomplete descriptors")]
    for label, at, replacement, check in (
        ("stale descriptor pointer", 0x420AC4, cut(before, 0x420AC4, 4), lambda x: resources(before, x, wsc)),
        ("descriptor shortened", 0x7C1100, struct.pack("<I", 32), lambda x: resources(before, x, wsc)),
        ("descriptor pointer outside ROM", 0x7C1104, struct.pack("<I", 0x03000000), lambda x: resources(before, x, wsc)),
        ("wrong restored tile pixel", 0x7C1B20, bytes([after[0x7C1B20] ^ 1]), lambda x: resources(before, x, wsc)),
        ("companion layout count", 0x60B410, struct.pack("<I", 128), lambda x: resources(before, x, wsc)),
        ("companion layout pointer", 0x60B414, struct.pack("<I", BASE + 0x60B400), lambda x: resources(before, x, wsc)),
        ("companion palette color", 0x60B886, b"\x01\x00", lambda x: resources(before, x, wsc)),
        ("renderer changes descriptor stride", 0x12C9C, struct.pack("<I", 0x108BB103), lambda x: consumers(x, gba, wsc)),
        ("unowned skipped gap", 0x60DB54, b"\0", lambda x: diff_check(before, x)),
    ):
        mutant = bytearray(after)
        mutant[at:at + len(replacement)] = replacement
        negative.append(rejected(lambda: check(mutant), label))
    source = source_population(wsc, 14)
    for label, at, value in (("source far segment outside C2", source["table"] + 4, 0x3000),
                             ("source copy crosses C2", source["table"] + 2, 0xFFFF),
                             ("source P1 event table truncated", source["p1"] + 6, 5)):
        mutant = bytearray(wsc)
        struct.pack_into("<H", mutant, at, value)
        negative.append(rejected(lambda: source_population(mutant, 14), label))
    for label, at, instruction in (("unaligned inbound pointer", 0x600001, BASE + 0x60B400),
                                    ("ARM inbound branch", 0x600008, 0xEA000000 | ((0x60B400 - 0x600010) // 4))):
        mutant = bytearray(before)
        struct.pack_into("<I", mutant, at, instruction)
        need(any(row[1] == at for row in inbound(mutant)), label)
        negative.append(label)
    inverse = bytearray(after)
    for start, stop in ALLOCATIONS + HEADER_WRITES:
        inverse[start:stop] = before[start:stop]
    need(bytes(inverse) == before, "complete Expected Write inverse")
    report = {"schema": 1, "kind": "independent-character-P0-completion-verification",
              "status": "PASS", "before_sha256": BEFORE, "after_sha256": AFTER,
              "source_sha256": WSC, "commercial_gba_sha256": GBA,
              "source_records": rows, "inverse_checked_pixels": pixels,
              "new_allocations": ALLOCATIONS, "header_writes": HEADER_WRITES,
              "predecessor_inbound_candidates": [], "inverse_restores_predecessor": True,
              "changed_bytes": sum(a != b for a, b in zip(before, after, strict=True)),
              "negative_cases": negative,
              "scope": "P0 complete source-selected layouts/descriptor populations/pixels, companion palettes, exact owned writes and unchanged native consumers",
              "not_certified": ["complete P1 conversion", "P4 semantics", "four resource table routing", "runtime rendering or gameplay"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-character-p0-completion] PASS {sha(args.output.read_bytes())}")


if __name__ == "__main__":
    main()
