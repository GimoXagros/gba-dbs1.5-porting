#!/usr/bin/env python3
"""Independently decode native Options pixels, callers and final writes.

Does not import or rerun the resource builder. This is artifact verification,
not evidence that an emulator has rendered or persisted a language selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

BASE, RAW = 0x08000000, 0x632000
GBA_SHA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
FONT_SHA = "4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u32(data, at):
    need(0 <= at <= len(data) - 4, f"in-bounds word {at:X}")
    return int.from_bytes(data[at:at + 4], "little")


def u16(data, at):
    return int.from_bytes(data[at:at + 2], "little")


def layouts(data, p0):
    table, descriptor = u32(data, p0) - BASE, u32(data, p0 + 4) - BASE
    size, pixels = u32(data, descriptor), u32(data, descriptor + 4) - BASE
    need(size % 32 == 0 and 0 < size <= 256*32 and pixels + size <= len(data), "eight-bit source tile pool")
    decoded = []
    for index in range(32):
        count, address = u32(data, table + index*8), u32(data, table + index*8 + 4) - BASE
        need(0 < count <= 20 and address + count*4 <= len(data), "complete bounded P0 layout")
        parts = [struct.unpack_from("<Hbb", data, address + i*4) for i in range(count)]
        image = {}
        for flags, y0, x0 in parts:
            tile = flags & 0x3FFF
            need(tile < size//32 and tile < 256, "every tile accepted by actual native eight-bit lookup")
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if flags & 0x4000 else x), (7 - y if flags & 0x8000 else y)
                    value = data[pixels + tile*32 + sy*4 + sx//2] >> (4*(sx % 2)) & 15
                    if value:
                        need((x0 + x, y0 + y) not in image, "nonoverlapping visible sprite parts")
                        image[x0 + x, y0 + y] = value
        decoded.append((parts, image))
    return decoded, size, pixels


def expected_text(font, text):
    font = font.replace("\r\n", "\n")
    cursor, points = 0, set()
    for ch in text:
        found = re.search(r"^ENCODING " + str(ord(ch)) + r"\n(.*?)^ENDCHAR$", font, re.M | re.S)
        need(found is not None, f"independent required glyph {ch!r}")
        block = found.group(1)
        advance = int(re.search(r"^DWIDTH (\d+) 0$", block, re.M).group(1))
        width, height, left, bottom = map(int, re.search(r"^BBX (\d+) (\d+) (-?\d+) (-?\d+)$", block, re.M).groups())
        bitmap = block.split("BITMAP\n", 1)[1].splitlines()
        need(len(bitmap) == height, "independent complete BDF bitmap")
        for y, row in enumerate(bitmap):
            bits = bin(int(row, 16))[2:].zfill((width + 7)//8*8)
            for x in range(width):
                if bits[x] == "1":
                    points.add((cursor + left + x + 1, y - height - bottom))
        cursor += advance
    need(points, "independent nonempty text")
    image = {}
    for x, y in points:
        for yy in range(y - 1, y + 2):
            for xx in range(x - 1, x + 2):
                image[xx, yy] = 2
    for point in points:
        image[point] = 1
    return image, max(x for x, _ in image) + 1


def verify(before, after, gba, font_bytes, draft, manifest):
    need(sha(gba) == GBA_SHA and sha(font_bytes) == FONT_SHA, "exact source and licensed font")
    need(len(before) == len(after) == 0x800000 and manifest["input_sha256"] == sha(before) and
         manifest["output_sha256"] == sha(after), "exact before/after manifest identities")
    source, _, source_pixels = layouts(gba, 0x9F980)
    result, tile_bytes, result_pixels = layouts(after, RAW)
    need(after[result_pixels:result_pixels + 1600] == gba[source_pixels:source_pixels + 1600],
         "all fifty original atlas tiles preserved inside the new pool")
    need((u16(after, RAW + 8), u16(after, RAW + 10), u16(after, RAW + 12), u16(after, RAW + 14)) ==
         (5, tile_bytes//32 - 1, tile_bytes - 32, 8), "P0 native header agrees with descriptor")
    event_table = u32(gba, 0xA02E8) - BASE
    event_layouts = []
    for event in range(12):
        count = u16(gba, event_table + event*16)
        commands = u32(gba, event_table + event*16 + 4) - BASE
        event_layouts.append([u16(gba, commands + frame*16 + 2) for frame in range(count)])
    replaced = set()
    for row in draft["entries"]:
        event, frame = row["event"], row.get("frame", 0)
        layout = event_layouts[event][frame]
        need(layout not in replaced, "one owner per translated layout")
        replaced.add(layout)
        expected, width = expected_text(font_bytes.decode("utf-8"), row["ko_draft"])
        left = 8 if event in (0, 2, 4, 6, 7) else ((24 if event == 11 else 40) - width)//2
        expected = {(x + left, y): color for (x, y), color in expected.items()}
        if event in (0, 2, 4, 6, 7):
            expected.update({point: color for point, color in source[layout][1].items() if point[0] < 8})
        need(result[layout][1] == expected, f"every native-decoded Korean pixel matches BDF ink/edge {event}:{frame}")
    need(replaced == {0, 4, 5, 6, 7, 8, 19, 20, 30, 31}, "exact ten translated layouts")
    for layout in set(range(32)) - replaced:
        need(result[layout] == source[layout], f"untouched numeric/decorative layout {layout}")

    # Recover all fifteen object/event pairs from the fixed native constructor.
    creations, events = [], []
    for at in range(0xC2564, 0xC315C, 4):
        value = u32(gba, at)
        if value >> 24 != 0xEB:
            continue
        delta = value & 0xFFFFFF
        delta -= 0x1000000 if delta & 0x800000 else 0
        target = at + 8 + delta*4
        if target == 0x127E4:
            creations.append(at)
        if target in (0x12874, 0x129C8):
            mov = u32(gba, at - (8 if target == 0x12874 else 12))
            need(mov & 0xFFFFFF00 == 0xE3A08000 and mov & 255 < 12, "native event immediate")
            events.append(mov & 255)
    need(len(creations) == len(events) == 15, "complete native constructor population")
    maximum = sum(max(len(result[index][0]) for index in event_layouts[event]) for event in events)
    need(maximum <= 127 and maximum*32 <= 4096, "aggregate OAM and active tile staging capacity")
    need(sha(after[0x12C58:0x12DD8]) == "D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685" and
         sha(after[0x11708:0x117D0]) == "8DF91F3DAAE3338D93CFF394FC8AB93504CEE271E522D860843BAFEEF563CBBB",
         "actual low-byte tile lookup, tile-per-OAM staging, VBlank transfer consumers unchanged")
    # The only old-image writes are the complete constructor literal population
    # and its matching palette preload; executable instructions are unchanged.
    mapping = {BASE + 0xA0D68: BASE + 0xA02E8, BASE + 0xA05E0: BASE + RAW,
               BASE + 0xA1038: BASE + 0xA05B8}
    sites = [at for at in range(0xC315C, 0xC3234, 4) if u32(gba, at) in mapping]
    need(len(sites) == 45, "complete fifteen P1/P0/P2 literal triples")
    for at in sites:
        need(u32(before, at) == u32(gba, at) and u32(after, at) == mapping[u32(gba, at)], "every native presentation routed")
        refs = [pc for pc in range(0xC2564, 0xC315C, 4)
                if u32(gba, pc) & 0xFFFFF000 == 0xE59F8000 and pc + 8 + (u32(gba, pc) & 4095) == at]
        need(len(refs) == 1, "literal has its actual native LDR consumer")
    sites.append(0xC1784)
    need(u32(before, 0xC1784) == BASE + 0xA1038 and u32(after, 0xC1784) == BASE + 0xA05B8,
         "matching initial palette preload")
    end = result_pixels + tile_bytes
    need(before[RAW:end] == b"\xff"*(end - RAW), "immutable new resource source condition")
    inverse = bytearray(after)
    inverse[RAW:end] = before[RAW:end]
    for at in sites:
        inverse[at:at + 4] = before[at:at + 4]
    need(inverse == before, "complete final diff explained; original code/assets/persistence untouched")
    planned = {(w["raw"], w["bytes"]) for w in manifest["expected_writes"]}
    need(planned == {(RAW, end - RAW)} | {(at, 4) for at in sites}, "manifest exact write population")
    for write in manifest["expected_writes"]:
        at, size = write["raw"], write["bytes"]
        need(write["before_sha256"] == sha(before[at:at + size]) and write["after_sha256"] == sha(after[at:at + size]),
             "every Expected Write byte range and identity")
    return dict(schema=1, status="PASS", kind="independent-korean-options-native-artifact-verification",
                output_sha256=sha(after), translated_frames=len(replaced), preserved_frames=32 - len(replaced),
                native_presentations=len(creations), recovered_events=events,
                maximum_oam_parts=maximum, maximum_active_tile_bytes=maximum*32,
                atlas_tiles=tile_bytes//32, checked_glyph_pixels="all ten decoded text frames against exact BDF",
                runtime_claim=False, supplied_save_accessed=False, four_language_feature_complete=False)


def verify_capture(directory, after, gba):
    from verify_native_capture_invariants import inspect
    invariants = inspect(directory, gba)
    capture = json.loads((directory/"capture.json").read_text(encoding="utf-8"))
    need(capture["rom"]["sha256"] == sha(after), "runtime observation belongs to this exact Korean PoC")
    iwram, ewram, vram, oam = ((directory/name).read_bytes() for name in
                              ("iwram.bin", "ewram.bin", "vram.bin", "oam.bin"))
    need(u16(iwram, 0x2310) == 14, "natural route reached actual Options mode")
    objects = []
    for at in range(0x48, len(ewram) - 4, 4):
        if u32(ewram, at) != BASE + RAW:
            continue
        start = at - 0x48
        need(u32(ewram, start + 0x44) == BASE + 0xA02E8 and
             u32(ewram, start + 0x4C) == BASE + 0xA05B8 and
             u16(ewram, start + 0x18) < 32, "live native object binds complete Korean resource tuple")
        objects.append(dict(address=0x02000000 + start, x=u16(ewram, start), y=u16(ewram, start + 2),
                            event=u16(ewram, start + 0xE), layout=u16(ewram, start + 0x18)))
    need(len(objects) == 15, "all fifteen actual native presentation objects present")
    active = invariants["enabled_objects_at_capture"]
    need(invariants["affine_objects_at_capture"] == 0 and 0 < active <= 107 and
         u16(iwram, 0x12D6) == active, "bounded actual native/physical OAM population")
    need([u16(oam, i*8 + 4) & 1023 for i in range(active)] == list(range(active)),
         "native tile-per-OAM hardware indices")
    need(vram[0x10000:0x10000 + active*32] == ewram[:active*32],
         "actual active tile queue reached hardware OBJ VRAM")
    return dict(status="PASS", capture_manifest_sha256=sha((directory/"capture.json").read_bytes()),
                rom_sha256=sha(after), mode=14, current_row=u16(iwram, 0x473E),
                time=u16(iwram, 0x2320), level=iwram[0x231F], live_presentations=objects,
                enabled_oam=active, active_vram_bytes=active*32,
                native_staging_matches_hardware=True, original_renderer_intact=True,
                scope="one natural-entry Options snapshot; language switching/persistence and complete interaction QA excluded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "font", "manifest", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--draft", type=Path, default=Path(__file__).resolve().parents[1]/"localization/options-draft.json")
    parser.add_argument("--capture-directory", type=Path)
    args = parser.parse_args()
    need(all(p is None or p.suffix.lower() != ".sav" for p in vars(args).values()), "save paths forbidden")
    report = verify(args.before.read_bytes(), args.after.read_bytes(), args.gba.read_bytes(), args.font.read_bytes(),
                    json.loads(args.draft.read_text(encoding="utf-8")), json.loads(args.manifest.read_text(encoding="utf-8")))
    if args.capture_directory:
        report["runtime_observation"] = verify_capture(args.capture_directory, args.after.read_bytes(), args.gba.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[Korean Options independent verification] PASS")


if __name__ == "__main__":
    main()
