#!/usr/bin/env python3
"""Supply the two source-backed name layouts selected by the expanded VS events."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

PRE = "7DBFA0B464AB9A0E2DA55049855A0BC08AABAAACDA1AF3E21CC780F2864854E9"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, P0, TABLE, END = 0x08000000, 0xB799C, 0x628140, 0x628228
P0_REFS = (0x8A3AC, 0x8A3BC, 0xB6494, 0xBBAD8, 0xBBAE8,
           0xBBAF0, 0xBBAFC, 0xBBB04, 0xBBB10)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def half(data, at):
    return struct.unpack_from("<H", data, at)[0]


def ownership(before):
    need(before[TABLE:END] == b"\xFF" * (END - TABLE), "exact new allocation is FF")
    refs, layout_refs = [], []
    for at in range(len(before) - 3):
        value = word(before, at)
        need(not BASE + TABLE <= value < BASE + END, "existing encoded pointer into new allocation")
        if value == BASE + P0:
            refs.append(at)
        if value == 0x080B79AC:
            layout_refs.append(at)
    need(tuple(refs) == P0_REFS and layout_refs == [P0], "complete encoded P0/layout reference population")
    for at in range(0, len(before) - 3, 4):
        value = word(before, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            delta -= 0x1000000 if delta & 0x800000 else 0
            need(not TABLE <= at + 8 + delta * 4 < END, "existing ARM branch into new allocation")
        if value & 0x0E1F0000 == 0x041F0000:
            delta = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not TABLE <= at + 8 + delta < END, "existing immediate PC-relative access into new allocation")


def source_layouts(data, at, count):
    need(word(data, at) == 16 and half(data, at + 18) == 16 + count * 4,
         "source layout population")
    rows, cursor = [], 16 + count * 4
    for index in range(count):
        size, offset = struct.unpack_from("<HH", data, at + 16 + index * 4)
        need(0 < size <= 36 and offset == cursor, "source contiguous bounded part records")
        rows.append((size, data[at + offset:at + offset + size * 4]))
        cursor += size * 4
    return rows


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PRE, GBA, OLD, SOURCE),
         "fixed predecessor and three commercial source identities")
    need(len(before) == 0x800000, "expanded ROM size")
    need(before[P0:0xB81D4] == gba[P0:0xB81D4] and word(before, P0) == 0x080B79AC,
         "unchanged actual eleven-layout native name resource")
    need(before[P0 + 8:P0 + 16] == source[0x3C3BF8:0x3C3C00], "source/native P0 constants")
    previous = source_layouts(old, 0x2AB3A0, 11)
    expanded = source_layouts(source, 0x3C3BF0, 13)
    for index, source_index in enumerate(tuple(range(10)) + (12,)):
        count, items = previous[index]
        native_count, native_parts = struct.unpack_from("<II", before, 0xB79AC + index * 8)
        need((count, items) == expanded[source_index] and native_count == count,
             "commercial source layout lineage and native part counts")
        # The retail boss changes its first twelve parts; retain that native variant.
        if index < 10:
            need(before[native_parts - BASE:native_parts - BASE + count * 4] == items,
                 "first ten native/source name layouts")
    # All new letters already use the unchanged commercial 37-tile atlas.
    need(old[0x2A6280:0x2A6720] == source[0x3BEBC0:0x3BF060], "source font atlas identity")
    packed = before[0xB7D34:0xB81D4]
    planar = bytearray()
    for row in range(len(packed) // 4):
        pixels = [n for value in packed[row * 4:row * 4 + 4] for n in (value & 15, value >> 4)]
        planar.extend(sum(((n >> plane) & 1) << (7 - x) for x, n in enumerate(pixels)) for plane in range(4))
    need(planar == source[0x3BEBC0:0x3BF060], "native atlas inverse matches the actual source pixels")
    for at in (0x3D0F70, 0x3D10C0):
        need(word(source, at) == 4 and half(source, at + 6) == 0x84, "source sixteen-event name family")
        for ident, layout in ((12, 0), (13, 10), (14, 11), (15, 12)):
            row = at + 4 + ident * 8
            command = at + half(source, row + 2)
            need(half(source, row) == 1 and half(source, command + 2) == layout and
                 half(source, command + 4) == ident, "source fighter-to-name mapping")
    ownership(before)
    payload = bytearray(before[0xB79AC:0xB7A04])
    parts = bytearray()
    for count, items in expanded[10:12]:
        need(count == 16 and all(items[index * 4] < 37 for index in range(count)), "new names fit existing atlas")
        payload.extend(struct.pack("<II", count, BASE + TABLE + 13 * 8 + len(parts)))
        parts.extend(items)
    payload.extend(parts)
    need(len(payload) == END - TABLE, "exact two-layout allocation extent")
    after = bytearray(before)
    struct.pack_into("<I", after, P0, BASE + TABLE)
    after[TABLE:END] = payload
    event_table = word(after, 0xB77EC) - BASE
    need(event_table == 0x485220, "installed expanded VS event table")
    cases = []
    for ident in range(16):
        row = event_table + ident * 16
        command = word(after, row + 4) - BASE
        layout = half(after, command + 2)
        need(word(after, row) == 1 and layout < 13, "every installed fighter event selects an owned layout")
        count, items = struct.unpack_from("<II", after, TABLE + layout * 8)
        need(0 < count <= 36 and BASE <= items <= BASE + len(after) - count * 4,
             "every live native name part extent")
        if ident >= 12:
            need(layout == (0, 11, 12, 10)[ident - 12], "retained expanded/boss event mapping")
        cases.append(dict(id=ident, layout=layout, parts=count, items=items))
    inverse = bytearray(after)
    inverse[P0:P0 + 4] = before[P0:P0 + 4]
    inverse[TABLE:END] = before[TABLE:END]
    need(inverse == before, "complete inverse outside layout pointer and new table/parts")
    return bytes(after), dict(schema=1, kind="vs-name-layout-repair", input_sha256=PRE,
        output_sha256=sha(after), changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        expected_writes=[dict(raw=P0, bytes=4, before="080B79AC", after=f"{BASE + TABLE:08X}"),
                         dict(raw=TABLE, bytes=END - TABLE, sha256=sha(payload))],
        source_p0=0x3C3BF0, source_new_layouts=[10, 11], native_new_layouts=[11, 12],
        preserved_native_layouts=11, shared_atlas_tiles=37, event_cases=cases,
        p0_pointer_sites=P0_REFS, old_layout_pointer_sites=[P0],
        cause="expanded events13/14 selected absent native name layouts11/12; part bytes became count/pointer",
        provided_save_accessed=False, runtime_claim=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in vars(args).values()), "save paths forbidden")
    after, manifest = build(*(getattr(args, name).read_bytes() for name in ("before", "gba", "wsc10", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("[vs-name-layout-repair] " + manifest["output_sha256"])


if __name__ == "__main__":
    main()
