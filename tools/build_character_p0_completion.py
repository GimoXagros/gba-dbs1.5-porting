#!/usr/bin/env python3
"""Complete source-bounded P0 tile tables and add missing companion graphics.

Historical layers remain reproducible.  Existing valid tile payloads are reused
only after exact pixel conversion comparison.  This layer adds no callbacks or
RAM state; resource routing and complete P1/P4 handling are separate layers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_full_asset_poc import convert_tile, parse_wsc_far_descriptor
from convert_wsc_palette_block import convert_block

BASE = 0x08000000
INPUT = "E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
# record, source P0, existing native P0, full descriptor count, valid prefix,
# new descriptor/payload start. Counts are checked against the whole source P1.
COMPLETIONS = (
    (14, 0x32A5E0, 0x420AC0, 324, 260, 0x7C1100),
    (43, 0x350000, 0x4E85E0, 77, 59, 0x7D9440),
    (44, 0x23E500, 0x4FB380, 78, 61, 0x7F6200),
    (36, 0x364930, 0x50D000, 88, 79, 0x7FAD00),
)
COMPANIONS = (27, 28, 29, 56, 57, 58, 59)
COMP_START, COMP_END = 0x60B400, 0x610000
RESERVED_TARGETS = (0x60DB54, 0x60E204)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def align(value, boundary=32):
    return (value + boundary - 1) & -boundary


def u32(data, raw):
    need(0 <= raw <= len(data) - 4, "word inside ROM")
    return struct.unpack_from("<I", data, raw)[0]


def source_pointer(wsc, raw):
    offset, segment, bank = struct.unpack_from("<3H", wsc, raw)
    linear = segment * 16 + offset
    need(0x20000 <= linear < 0x30000 and 0x80 <= bank <= 0xFF, "source C2 pointer")
    return (bank & 0x7F) * 0x10000 + linear - 0x20000


def source_commands(wsc, record):
    source = source_pointer(wsc, 0x740000 + record * 32 + 6)
    table, reserved, _first_count, first_payload = struct.unpack_from("<4H", wsc, source)
    need(table == 4 and reserved == 0 and first_payload > table
         and (first_payload - table) % 8 == 0, "complete source P1 event geometry")
    events = (first_payload - table) // 8
    need(0 < events <= 256, "source P1 event population")
    frames = []
    for event in range(events):
        count, relative, _a, _b = struct.unpack_from("<4H", wsc, source + table + event * 8)
        need(0 < count <= 512 and relative >= first_payload, "source P1 event payload")
        for frame in range(count):
            layout, tile = struct.unpack_from("<2H", wsc, source + relative + frame * 12 + 2)
            frames.append((event, frame, layout, tile))
    return source, events, frames


def source_layout(wsc, source):
    need(u32(wsc, source) == 16, "source P0 layout origin")
    first = struct.unpack_from("<H", wsc, source + 18)[0]
    need(first > 16 and (first - 16) % 4 == 0, "source P0 layout population")
    entries, cursor = [], first
    for index in range((first - 16) // 4):
        count, relative = struct.unpack_from("<2H", wsc, source + 16 + index * 4)
        need(0 < count <= 128 and relative == cursor, "source P0 layout extent")
        entries.append((count, wsc[source + relative:source + relative + count * 4]))
        cursor += count * 4
    segment, bank = struct.unpack_from("<2H", wsc, source + 4)
    need(0x2000 <= segment < 0x3000 and 0x80 <= bank <= 0xFF, "source P0 descriptor table")
    descriptors = (bank & 0x7F) * 0x10000 + segment * 16 - 0x20000
    return entries, descriptors


def converted_tiles(wsc, descriptor):
    length, source = parse_wsc_far_descriptor(wsc, descriptor)
    result = b"".join(convert_tile(wsc[raw:raw + 32])
                      for raw in range(source, source + length, 32))
    need(len(result) == length, "tile conversion extent")
    return source, result


def validate_commands(wsc, record, layouts, descriptors):
    source, events, frames = source_commands(wsc, record)
    p0 = source_pointer(wsc, 0x740000 + record * 32)
    indexed = bool(struct.unpack_from("<H", wsc, p0 + 14)[0] & 2)
    used = {frame[3] if indexed else 0 for frame in frames}
    need(used == set(range(len(descriptors))), "exact descriptor population from source consumers")
    for _event, _frame, layout, tile in frames:
        need(layout < len(layouts), "source P1 layout index")
        count, items = layouts[layout]
        length = len(descriptors[tile if indexed else 0][1])
        need(max(items[p * 4] for p in range(count)) * 32 + 32 <= length,
             "source layout tile index inside actual copied payload")
    return {"source_p1": source, "source_events": events, "source_commands": len(frames),
            "descriptor_indexed": indexed, "descriptor_count": len(descriptors)}


def complete_existing(before, wsc, spec):
    record, source, native, count, prefix, target = spec
    need(source_pointer(wsc, 0x740000 + record * 32) == source, "source P0 resource record")
    layouts, table = source_layout(wsc, source)
    descriptors = [converted_tiles(wsc, table + index * 8) for index in range(count)]
    contract = validate_commands(wsc, record, layouts, descriptors)
    old_table = u32(before, native + 4) - BASE
    output = bytearray(align(count * 8))
    rows = []
    for index, (source_tiles, converted) in enumerate(descriptors):
        if index < prefix:
            length, pointer = struct.unpack_from("<2I", before, old_table + index * 8)
            need(length == len(converted) and BASE <= pointer <= BASE + len(before) - length,
                 "existing descriptor prefix")
            need(before[pointer - BASE:pointer - BASE + length] == converted,
                 "existing tile prefix must exactly match source conversion")
            reused = True
        else:
            pointer = BASE + target + len(output)
            output.extend(converted)
            reused = False
        struct.pack_into("<2I", output, index * 8, len(converted), pointer)
        rows.append({"index": index, "source": source_tiles, "bytes": len(converted),
                     "target": pointer - BASE, "reused": reused, "sha256": sha(converted)})
    return bytes(output), {"record": record, "source_p0": source, "native_p0": native,
                           "old_descriptor_table": old_table, "target": target,
                           "bytes": len(output), "source_descriptor_table": table,
                           "valid_prefix": prefix, "entries": rows, **contract}


def companion_blob(wsc, record, target):
    row = 0x740000 + record * 32
    source = source_pointer(wsc, row)
    layouts, table = source_layout(wsc, source)
    need(wsc[table + 8:table + 16] == b"\xff" * 8, "companion one-descriptor terminator")
    tiles = converted_tiles(wsc, table)
    contract = validate_commands(wsc, record, layouts, [tiles])
    need(not contract["descriptor_indexed"], "companion renderer uses one tile payload")
    size = 16 + len(layouts) * 8 + sum(len(items) for _count, items in layouts)
    descriptor = target + size
    tile_target = align(descriptor + 8)
    output = bytearray(tile_target - target)
    struct.pack_into("<4I", output, 0, BASE + target + 16, BASE + descriptor,
                     u32(wsc, source + 8), u32(wsc, source + 12))
    cursor = 16 + len(layouts) * 8
    for index, (count, items) in enumerate(layouts):
        struct.pack_into("<2I", output, 16 + index * 8, count, BASE + target + cursor)
        output[cursor:cursor + len(items)] = items
        cursor += len(items)
    struct.pack_into("<2I", output, descriptor - target, len(tiles[1]), BASE + tile_target)
    output.extend(tiles[1])
    palettes = []
    for field in (2, 3):
        source_palette = source_pointer(wsc, row + field * 6)
        converted = convert_block(wsc[source_palette:source_palette + 38])
        prior = next((p for p in palettes if p["source"] == source_palette), None)
        if prior:
            palette_target = prior["target"]
        else:
            palette_target = target + len(output)
            output.extend(converted)
        palettes.append({"field": field, "source": source_palette,
                         "target": palette_target, "bytes": 40, "sha256": sha(converted)})
    return bytes(output), {"record": record, "source_p0": source, "target": target,
                           "bytes": len(output), "layout_count": len(layouts),
                           "source_descriptor_table": table, "descriptor": descriptor,
                           "source_tiles": tiles[0], "tile_target": tile_target,
                           "tile_bytes": len(tiles[1]), "palettes": palettes, **contract}


def inbound(data, intervals):
    result = []
    def inside(target):
        return any(start <= target < end for start, end in intervals)
    for raw in range(len(data) - 3):
        target = struct.unpack_from("<I", data, raw)[0] - BASE
        if inside(target):
            result.append(("unaligned-inclusive pointer", raw, target))
    for raw in range(0, len(data) - 3, 4):
        instruction = u32(data, raw)
        if instruction >> 28 != 15 and instruction & 0x0E000000 == 0x0A000000:
            displacement = instruction & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            target = raw + 8 + displacement * 4
            if inside(target):
                result.append(("ARM-like B/BL", raw, target))
    return result


def build(before, gba, wsc):
    need((sha(before), sha(gba), sha(wsc)) == (INPUT, GBA, WSC), "exact predecessor and original inputs")
    need(len(before) == 0x800000, "expanded ROM size")
    need(before[0x127E4:0x12DC8] == gba[0x127E4:0x12DC8], "unchanged native P0/P1 renderer consumers")
    writes, complete_rows, companion_rows = [], [], []
    for spec in COMPLETIONS:
        blob, info = complete_existing(before, wsc, spec)
        writes.append((info["target"], blob, "complete native descriptor population", True))
        writes.append((info["native_p0"] + 4, struct.pack("<I", BASE + info["target"]),
                       "P0 descriptor-table pointer", False))
        complete_rows.append(info)
    cursor = COMP_START
    for record in COMPANIONS:
        while True:
            cursor = align(cursor)
            blob, info = companion_blob(wsc, record, cursor)
            conflicts = [target for target in RESERVED_TARGETS if cursor <= target < cursor + len(blob)]
            if not conflicts:
                break
            cursor = align(max(conflicts) + 32)
        need(cursor + len(blob) <= COMP_END, "companion allocation reservation")
        writes.append((cursor, blob, f"source companion resource {record} P0/palette", True))
        companion_rows.append(info)
        cursor += len(blob)
    allocations = [(raw, raw + len(blob)) for raw, blob, _label, new in writes if new]
    need(not inbound(before, allocations), "incoming candidate reaches actual new allocation")
    for raw, blob, _label, new in writes:
        if new:
            need(before[raw:raw + len(blob)] == b"\xff" * len(blob), "Expected Write blank allocation")
    after = bytearray(before)
    details = []
    used = set()
    for raw, blob, label, new in writes:
        extent = set(range(raw, raw + len(blob)))
        need(not used & extent, "overlapping writes")
        used |= extent
        details.append({"raw": raw, "bytes": len(blob), "label": label,
                        "new_allocation": new, "before_sha256": sha(before[raw:raw + len(blob)]),
                        "after_sha256": sha(blob)})
        after[raw:raw + len(blob)] = blob
    changed = {i for i, (old, new) in enumerate(zip(before, after, strict=True)) if old != new}
    expected = {raw + n for raw, blob, _label, _new in writes
                for n, value in enumerate(blob) if before[raw + n] != value}
    need(changed == expected, "complete byte diff matches Expected Writes")
    return bytes(after), {"schema": 1, "kind": "character-P0-source-completion",
                         "input_sha256": INPUT, "output_sha256": sha(after),
                         "completed_existing": complete_rows, "companions": companion_rows,
                         "expected_writes": details, "actual_changed_bytes": len(changed),
                         "new_allocations": allocations, "incoming_candidates": [],
                         "preserved_candidate_targets": list(RESERVED_TARGETS),
                         "code_changed": False, "new_RAM": False,
                         "scope": "complete source-selected P0 layouts/tiles and companion palettes; P1/P4/routing are subsequent layers"}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "wsc15", "output", "manifest")), "save paths forbidden")
    output, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[character-p0-completion] {report['output_sha256']}")


if __name__ == "__main__":
    main()
