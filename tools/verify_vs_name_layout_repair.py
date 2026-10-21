#!/usr/bin/env python3
"""Independently verify missing VS name layouts and the observed ID14 overflow.

No builder, manifest, emulator, or save file is used. Source event/layout tables
and inverse font pixels establish the added data; the frozen parent-owned probe
establishes the original failure's exact native consumer chain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
BEFORE = "7DBFA0B464AB9A0E2DA55049855A0BC08AABAAACDA1AF3E21CC780F2864854E9"
AFTER = "99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
PROBE = "9F19C51728E7182FC95F76527FE5E89F119693CEC45085FC97A7D37BE3245F52"
P0, OLD_TABLE, DESCRIPTOR, PIXELS = 0xB799C, 0xB79AC, 0xB7D2C, 0xB7D34
NEW_TABLE, END = 0x628140, 0x628228
OWNED = ((P0, P0 + 4), (NEW_TABLE, END))
NATIVE_FRAMES = (0, 1, 2, 3, 4, 5, 6, 5, 7, 8, 5, 9, 0, 11, 12, 10)
SOURCE_FRAMES = (0, 1, 2, 3, 4, 5, 6, 5, 7, 8, 5, 9, 0, 10, 11, 12)
P0_USERS = (0x8A3AC, 0x8A3BC, 0xB6494, 0xBBAD8, 0xBBAE8,
            0xBBAF0, 0xBBAFC, 0xBBB04, 0xBBB10)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded ROM extent")
    return data[at:at + size]


def u16(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def u32(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def ptr(data, at, size=1):
    raw = u32(data, at) - BASE
    cut(data, raw, size)
    return raw


def inverse_pixels(packed):
    need(len(packed) % 32 == 0, "complete native font tiles")
    result = bytearray(len(packed))
    for at in range(0, len(packed), 4):
        pixels = [n for byte in packed[at:at + 4] for n in (byte & 15, byte >> 4)]
        for plane in range(4):
            result[at + plane] = sum(((n >> plane) & 1) << (7 - x)
                                     for x, n in enumerate(pixels))
    return bytes(result)


def source_p0(data, p0, count, descriptor, pixel_at):
    need(u32(data, p0) == 16, "source direct P0 layout header")
    need((u16(data, p0 + 18) - 16) // 4 == count and
         u16(data, p0 + 18) == 16 + 4 * count, "source layout population geometry")
    rows, cursor = [], 16 + count * 4
    for index in range(count):
        size, offset = struct.unpack("<HH", cut(data, p0 + 16 + index * 4, 4))
        need(0 < size <= 128 and offset == cursor, "contiguous bounded source parts")
        rows.append((size, cut(data, p0 + offset, size * 4)))
        cursor += size * 4
    segment, bank = struct.unpack("<HH", cut(data, p0 + 4, 4))
    mask = len(data) // 0x10000 - 1
    need((bank & mask) * 0x10000 + segment * 16 - 0x20000 == descriptor,
         "source descriptor bank mapping")
    length, offset, segment, bank = struct.unpack("<4H", cut(data, descriptor, 8))
    need(length == 1184 and
         (bank & mask) * 0x10000 + segment * 16 + offset - 0x20000 == pixel_at,
         "source font descriptor extent")
    need(0x20000 <= segment * 16 + offset < segment * 16 + offset + length <= 0x30000,
         "source font stays in the C2 window")
    font = cut(data, pixel_at, length)
    for size, parts in rows:
        need(all(parts[i * 4] < length // 32 for i in range(size)), "source glyph extent")
    return rows, font


def sources(wsc10, wsc15):
    old, old_font = source_p0(wsc10, 0x2AB3A0, 11, 0x2B6450, 0x2A6280)
    new, new_font = source_p0(wsc15, 0x3C3BF0, 13, 0x3D8E70, 0x3BEBC0)
    need(old[:10] == new[:10] and old[10] == new[12], "source version layout correspondence")
    need(old_font == new_font and sha(new_font) ==
         "65A3F441FFAFAC107EF4DEFC758AD5566DF477C81163100E746990F505325282",
         "unchanged complete source font")
    commands = []
    for p1 in (0x3D0F70, 0x3D10C0):
        need(u32(wsc15, p1) == 4 and u16(wsc15, p1 + 6) == 4 + 16 * 8,
             "all sixteen source VS name events")
        family = []
        for event, layout in enumerate(SOURCE_FRAMES):
            n, offset, meta, last = struct.unpack("<4H", cut(wsc15, p1 + 4 + event * 8, 8))
            need((n, offset, meta, last) == (1, 0x84 + event * 12, 0x144, 0),
                 "source name event owner and extent")
            command = cut(wsc15, p1 + offset, 12)
            need(command == struct.pack("<BBHHHI", 1, 255, layout, event, 0, 0),
                 "source ID to name layout selection")
            family.append(command)
        commands.append(family)
    need(commands[0] == commands[1], "both source VS name event families agree")
    return new, new_font, commands[0]


def resources(before, after, gba, source):
    rows, font, commands = source
    need(cut(before, P0, 16) == cut(gba, P0, 16) and ptr(before, P0) == OLD_TABLE,
         "retail predecessor P0")
    need(ptr(after, P0, 13 * 8) == NEW_TABLE, "new thirteen-row layout table")
    need(cut(after, P0 + 4, 0xB81D4 - P0 - 4) == cut(gba, P0 + 4, 0xB81D4 - P0 - 4),
         "all original layout rows, parts, descriptor and pixels preserved")
    need(cut(after, NEW_TABLE, 11 * 8) == cut(gba, OLD_TABLE, 11 * 8),
         "eleven original table rows preserved exactly")
    need(ptr(after, P0 + 4, 8) == DESCRIPTOR and u32(after, DESCRIPTOR) == 1184 and
         ptr(after, DESCRIPTOR + 4, 1184) == PIXELS, "original font descriptor")
    need(inverse_pixels(cut(after, PIXELS, 1184)) == font, "every reused font pixel matches source")
    report = []
    for index in range(13):
        size = u32(after, NEW_TABLE + index * 8)
        at = ptr(after, NEW_TABLE + index * 8 + 4, size * 4)
        parts = cut(after, at, size * 4)
        if index < 10:
            need((size, parts) == rows[index], "original common name source parts")
        elif index == 10:
            need(size == 36 and sha(parts) ==
                 "7C4D17931CBBF1F30E04737EB0768D94135EE6115B7DB31EBD44AF87542E5065",
                 "retail boss name variant remains exact")
            need(parts != rows[12][1], "retail boss variant is not falsely claimed as source identical")
        else:
            need(at == NEW_TABLE + 13 * 8 + (index - 11) * 64 and
                 (size, parts) == rows[index - 1], "two missing source name layouts")
        need(0 < size <= 128 and all(parts[i * 4] < 37 for i in range(size)),
             "every native part is bounded by the shared font")
        report.append({"native_layout": index, "count": size, "parts_raw": at,
                       "source_layout": index if index < 10 else index - 1 if index > 10 else None,
                       "parts_sha256": sha(parts)})
    need(ptr(after, 0xB77EC, 16 * 16) == 0x485220, "resident expanded P1 owner")
    for event, layout in enumerate(NATIVE_FRAMES):
        at = 0x485220 + event * 16
        n, command, meta, last = struct.unpack("<4I", cut(after, at, 16))
        need((n, meta, last) == (1, 0x080B7994, 0), "native VS event extent and metadata")
        source_command = bytearray(commands[event])
        struct.pack_into("<H", source_command, 2, layout)
        need(cut(after, command - BASE, 16) == source_command + b"\0" * 4,
             "all sixteen events select the correct remapped source layout")
        need(layout < len(report), "native event selects an owned layout")
    return report


def consumers(after, gba):
    for start, stop in ((0x127E4, 0x1285C), (0x12874, 0x12930),
                        (0x12C28, 0x12DD8), (0xB6138, 0xB619C),
                        (0xB6AE8, 0xB6B30)):
        need(cut(after, start, stop - start) == cut(gba, start, stop - start),
             "native constructor, event selector and renderer unchanged")
    need(all(u32(after, at) == BASE + P0 for at in P0_USERS), "all shared native P0 users")
    for load, literal, value in ((0xB6138, 0xB648C, 0x03002CC8),
                                  (0xB6144, 0xB6490, 0x080B77EC),
                                  (0xB6154, 0xB6494, 0x080B799C),
                                  (0xB6164, 0xB6498, 0x080B81D4),
                                  (0xB6AE8, 0xB6B28, 0x03002CC8)):
        need(load + 8 + (u32(after, load) & 0xFFF) == literal and u32(after, literal) == value,
             "actual VS presentation constructor and draw literals")
    need(u32(after, 0x127F8) == 0xE5850048 and
         u32(after, 0x1288C) == 0xE0811203 and
         u32(after, 0x1291C) == 0xE1D100B2 and u32(after, 0x12920) == 0xE1C501B8,
         "native P0 ownership, sixteen-byte event stride and frame storage")
    need(sha(cut(after, 0x12C58, 0x180)) ==
         "D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685",
         "complete original dynamic renderer")
    need(u32(after, 0x18C) == 0xE59F4208 and u32(after, 0x39C) == 0x08012C58 and
         u32(after, 0x194) == 0xE3A04060 and u32(after, 0x12C50) == 0x03000204,
         "native boot copy and IWRAM renderer entry")


def overflow(before, probe):
    need(probe["rom_sha256"] == BEFORE and probe["endpoint"]["verified"] and
         probe["loaded_rom_samples"]["verified"] and not probe["monitor_visible"] and
         probe["guest_writes"] == [], "original runtime probe provenance")
    event, = [e for e in probe["events"] if e["stop"] == "T05watch:03001828;"]
    regs = [int(value, 16) for value in event["registers"]]
    obj = bytes.fromhex(event["presentation"]["hex"])
    state = bytes.fromhex(event["renderer_state"]["hex"])
    need(event["presentation"]["address"] == "03002CC8" and regs[5] == 0x03002CC8 and
         tuple(u32(obj, at) for at in (0x44, 0x48, 0x4C)) ==
         (0x080B77EC, 0x080B799C, 0x080B81D4), "observed VS name resource owners")
    need(u16(obj, 0xE) == 14 and u16(obj, 0x18) == 12 and
         u32(obj, 0x20) == u32(obj, 0x24) == 0x08485340 and
         u16(before, 0x485342) == 12, "actual ID14 event selects missing layout twelve")
    entry = ptr(before, P0) + u16(obj, 0x18) * 8
    count, items = struct.unpack("<II", cut(before, entry, 8))
    need((entry, count, items) == (0xB7A0C, 0x0EF80206, 0x16F80207),
         "missing layout reads original part bytes as count and pointer")
    need(event["renderer_state"]["address"] == "030012C8" and state[2] == 31,
         "draw begins after thirty-one existing OAM slots")
    steps = regs[0] - state[2]
    need(steps == 97 and regs[0] == 128 and regs[2] == count - steps == 0x0EF801A5 and
         regs[10] == items + steps * 4 == 0x16F8038B and regs[11] == BASE + PIXELS and
         regs[12] == 0x03001828 and regs[15] == 0x030002A0,
         "exact ninety-seven completed parts before first OAM overflow")
    stack = bytes.fromhex(event["stack"]["hex"])
    need(struct.pack("<I", 0x080B6AF8) in stack and struct.pack("<I", 0x080B73E4) in stack,
         "observed native VS presentation return chain")
    need(u32(before, 0x12DBC) == 0x03001428 and u32(before, 0x12CF4) == 0xE1CC30B0 and
         u32(before, 0x12D98) == 0xE28CC008 and u32(before, 0x12DA0) == 0xE28AA004 and
         u32(before, 0x12DA4) == 0xE2522001 and
         0x03000200 + 0x12CF4 - 0x12C58 + 4 == regs[15], "exact OAM store and native loop")
    need(event["watched_halfword"] == {"address": "03001828", "hex": "b800"},
         "first overflow is the observed attr0 halfword")
    return {"presentation": 0x03002CC8, "event": 14, "layout": 12,
            "bad_entry_raw": entry, "bad_count": count, "bad_items": items,
            "initial_oam_count": state[2], "completed_parts": steps,
            "remaining_count": regs[2], "current_items": regs[10],
            "oam_pointer": regs[12], "watch_pc": regs[15],
            "loaded_rom_identity": "endpoint-verified ROM samples, not a complete loaded-ROM hash"}


def ownership(before, after):
    need(len(before) == len(after) == 0x800000, "ROM extent unchanged")
    need(cut(before, NEW_TABLE, END - NEW_TABLE) == b"\xff" * (END - NEW_TABLE),
         "exact new allocation was blank")
    cursor = 0
    restored = bytearray(after)
    for start, stop in OWNED:
        need(before[cursor:start] == after[cursor:start], "unowned ROM bytes preserved")
        restored[start:stop] = before[start:stop]
        cursor = stop
    need(before[cursor:] == after[cursor:] and bytes(restored) == before,
         "complete owned-write inverse restores predecessor")


def inbound(data):
    hits = []
    for at in range(len(data) - 3):
        target = struct.unpack_from("<I", data, at)[0] - BASE
        if NEW_TABLE <= target < END:
            hits.append(["pointer including unaligned", at, target])
    for index, (word,) in enumerate(struct.iter_unpack("<I", data)):
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            displacement = (word & 0xFFFFFF) - (0x1000000 if word & 0x800000 else 0)
            target = index * 4 + 8 + displacement * 4
            if NEW_TABLE <= target < END:
                hits.append(["ARM-like B/BL", index * 4, target])
    return hits


def rejected(call, label):
    try:
        call()
    except (ValueError, struct.error, IndexError):
        return label
    raise ValueError("negative fixture accepted: " + label)


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "probe", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, key).suffix.lower() != ".sav" for key in vars(args)), "save paths forbidden")
    before, after, gba, wsc10, wsc15, probe_bytes = [getattr(args, key).read_bytes()
        for key in ("before", "after", "gba", "wsc10", "wsc15", "probe")]
    need(tuple(map(sha, (before, after, gba, wsc10, wsc15, probe_bytes))) ==
         (BEFORE, AFTER, GBA, WSC10, WSC15, PROBE), "exact six input identities")
    source = sources(wsc10, wsc15)
    ownership(before, after)
    consumers(after, gba)
    rows = resources(before, after, gba, source)
    dynamic = overflow(before, json.loads(probe_bytes))
    need(not inbound(before), "no prior pointer or ARM-like branch into the allocation")
    negative = [rejected(lambda: resources(before, before, gba, source), "historical missing layouts")]
    for label, at, replacement, check in (
        ("stale layout table", P0, struct.pack("<I", BASE + OLD_TABLE), lambda d: resources(before, d, gba, source)),
        ("oversized added count", NEW_TABLE + 11 * 8, struct.pack("<I", 129), lambda d: resources(before, d, gba, source)),
        ("added parts outside ROM", NEW_TABLE + 12 * 8 + 4, struct.pack("<I", 0x03000000), lambda d: resources(before, d, gba, source)),
        ("wrong added glyph", NEW_TABLE + 13 * 8, b"\xff", lambda d: resources(before, d, gba, source)),
        ("swapped added name rows", NEW_TABLE + 11 * 8 + 4, struct.pack("<I", BASE + NEW_TABLE + 13 * 8 + 64), lambda d: resources(before, d, gba, source)),
        ("changed preserved boss name", 0xB7C9C, b"\x06", lambda d: resources(before, d, gba, source)),
        ("changed shared font pixel", PIXELS, b"\x01", lambda d: resources(before, d, gba, source)),
        ("ID14 selects the wrong name", 0x485342, b"\x0b\0", lambda d: resources(before, d, gba, source)),
        ("changed native event stride", 0x1288C, struct.pack("<I", 0xE0811183), lambda d: consumers(d, gba)),
        ("unowned write before allocation", NEW_TABLE - 1, bytes([after[NEW_TABLE - 1] ^ 1]), lambda d: ownership(before, d)),
    ):
        mutant = bytearray(after)
        mutant[at:at + len(replacement)] = replacement
        negative.append(rejected(lambda: check(mutant), label))
    probe_mutant = json.loads(probe_bytes)
    probe_mutant["events"][1]["renderer_state"]["hex"] = "0000000010005100"
    negative.append(rejected(lambda: overflow(before, probe_mutant), "incorrect 128-part overflow explanation"))
    inbound_mutant = bytearray(before)
    struct.pack_into("<I", inbound_mutant, 0x600001, BASE + NEW_TABLE)
    struct.pack_into("<I", inbound_mutant, 0x600008, 0xEA000000 | ((NEW_TABLE - 0x600010) // 4))
    hits = inbound(inbound_mutant)
    need(any(row[:2] == ["pointer including unaligned", 0x600001] for row in hits) and
         any(row[:2] == ["ARM-like B/BL", 0x600008] for row in hits), "inbound scan negative controls")
    negative.extend(["unaligned prior inbound pointer", "prior ARM-like inbound branch"])
    report = {"schema": 1, "kind": "independent-vs-name-layout-repair-verification", "status": "PASS",
              "before_sha256": BEFORE, "after_sha256": AFTER, "commercial_gba_sha256": GBA,
              "wsc10_sha256": WSC10, "wsc15_sha256": WSC15, "probe_sha256": PROBE,
              "owned_writes": OWNED, "changed_bytes": sum(a != b for a, b in zip(before, after)),
              "inverse_restores_predecessor": True, "source_p0": {"wsc10": 0x2AB3A0, "wsc15": 0x3C3BF0},
              "native_layouts": rows, "native_event_layouts": NATIVE_FRAMES,
              "source_event_layouts": SOURCE_FRAMES, "inverse_checked_font_bytes": 1184,
              "shared_native_p0_users": P0_USERS, "original_overflow": dynamic,
              "predecessor_pointer_and_arm_inbound_candidates": [], "negative_cases": negative,
              "preserved_variant": "retail boss layout10 differs from source row12 and is unchanged",
              "not_certified": ["runtime success after repair", "all aggregate multi-object OAM budgets",
                                "full port completion", "Thumb branch or computed-pointer reachability"],
              "emulator_started": False, "provided_save_accessed": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-vs-name-layout-repair] PASS {sha(args.report.read_bytes())}")


if __name__ == "__main__":
    main()
