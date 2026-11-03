#!/usr/bin/env python3
"""Extend the disconnected Shoot entry through source 73E2, before SRAM gates.

Retains the existing entry and eight-byte frame, inserts the slot-5 palette
and proven 0660 clear, then moves its original return by eight bytes. P0
preloads use the already-proved native resource/dynamic-renderer contract.
No external entry, full initializer, or unproved SRAM clear is installed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, no_inbound
from analyze_shoot_initializer_lifetime import RESOURCE_ROWS, compare_p1, constructor_arguments
from verify_shoot_far_tile_repair import check_asset, source_pairs, native_pairs
from verify_shoot_tail_resources import check_consumers

PARENT = "2C9C96129EBECF30FCB915E077899CE91FBA979F4AC44C027EE39F4C9A8C4BC7"
ENTRY, START, EXTENSION, END = 0x629800, 0x629810, 0x629818, 0x629820
SOURCE_HASH = "D3BB949DFAC1F1281974822C5A60CEB156FF8BA65226FBFC5E0386CAD32BE2E9"
BEFORE_WORDS = (0xE8BD4800, 0xE12FFF1E, 0xFFFFFFFF, 0xFFFFFFFF)
HEAD_WORDS = (0xE92D4800, 0xE3A0B000, 0xEBFFFFBC, 0xEBFE5DFB)
GUARDS = (
    ("slot-5 palette adapter", 0x5C1700, 0x5C173C, "4D820BC4540F166FE98F6BB2F0E7B7FA6153010A63A373BD9B221C57154612E4"),
    ("slot-5 P2", 0x5DB740, 0x5DB768, "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1"),
    ("0660-only clear", 0x5C4400, 0x5C441C, "9765E2CC0B5B3E473FC00D18FC4FF564D2E0E729237FB2C5AFA0CC1BC67A0E46"),
    ("6D P0 header", 0x5DB300, 0x5DB310, "9E7B9E52D871E2740A1621015196531A7A1812D6DD712143E355EC77CC3F8A83"),
    ("137 P0 header", 0x5DB400, 0x5DB410, "F343F725C771B3D8F8DF92CC1A5BBC0F2A0693767D966AA112470F34258D41F2"),
    ("full dynamic renderer and copied extent", 0x12C28, 0x12DD8, "78B1C64C99CB980EBC60E8950B941B11B118AAE2CD9A7A6A1E15B926C88FA0DB"),
    ("93E7 constructor adapter", 0x5C4500, 0x5C458C, "D9A8CAD358CBF0667D1A5363C75F777267EDB5E8A726783A291E3D29C5A79BFA"),
    ("888B constructor adapter", 0x5C4600, 0x5C468C, "E3DB55773E5CDF3B942176B97A29B0F01918473E22067ABB1FFD7BE97B6E9829"),
)


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def bl(at, target):
    displacement = target - (BASE + at + 8)
    need(displacement % 4 == 0 and -(1 << 25) <= displacement < (1 << 25), "ARM BL range")
    return 0xEB000000 | ((displacement // 4) & 0xFFFFFF)


def payload():
    return struct.pack("<4I", bl(START, 0x085C1700), bl(START + 4, 0x085C4400), 0xE8BD4800, 0xE12FFF1E)


def dependencies(before, source):
    need(sha(source[0x747C94:0x747CE2]) == SOURCE_HASH, "complete source continuation through 0660")
    need(source[0x747CE2:0x747CF0] == bytes.fromhex("26c706d83c000026c706da3c0000"),
         "first omitted instructions are the two distinct unresolved ES1000 SRAM clears")
    need(struct.unpack_from("<4I", before, ENTRY) == HEAD_WORDS, "original entry and first two calls")
    need(struct.unpack_from("<4I", before, START) == BEFORE_WORDS, "exact old return and unused eight-byte extension")
    for label, start, end, expected in GUARDS:
        need(sha(before[start:end]) == expected, label)
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer remains absent")


def source_contract(before, gba, source):
    palette = check_consumers(before, source)["palettes"][0]
    need(palette["entry_sp"] == [5, 0, 0, 0, 0x085DB740] and palette["destination"] == 0x050002A2,
         "source palette selects fifteen nonzero colors in OBJ slot 5")
    p1 = [compare_p1(source, before, row) for row in RESOURCE_ROWS]
    constructors = [constructor_arguments(before, row) for row in RESOURCE_ROWS]
    p0 = [check_asset(before, source, *row) for row in
          ((0x3D44E0, 0x5DB300, 1, None, None), (0x3D0CA0, 0x5DB400, 1, None, None))]
    for src, native, header, layouts in ((0x3D23B0, 0x5C4800, 0x5DB300, 8), (0x0DFEC0, 0x5C4C00, 0x5DB400, 18)):
        pairs = source_pairs(source, src)
        need(native_pairs(before, native) == pairs and all(layout < layouts for layout, _ in pairs),
             "every actual P1 layout selects source-identical bounded pixels")
        # Static descriptor flag: P1 word2 is ignored; each P0 uses its sole descriptor.
        need(struct.unpack_from("<H", before, header + 14)[0] == 8, "dynamic drawing with descriptor-index flag clear")
    for start, end in ((0x160, 0x1A0), (0x127E4, 0x1285C), (0x12C28, 0x12DD8),
                       (0x352B30, 0x352B78), (0x352DC4, 0x352DEC), (0x355EE8, 0x355F0C)):
        need(before[start:end] == gba[start:end], "retained actual native consumer/producer " + hex(start))
    need(word(before, 0x39C) == 0x08012C58 and word(before, 0x12C50) == 0x03000204,
         "native startup renderer copy and callable dispatch identity")
    for at, destination in ((0x5CC3F8, 0x085C4500), (0x5CC278, 0x085C4600)):
        need(word(before, at) == bl(at, destination), "existing lower callback invokes the resource adapter")
    need(source[0x766ECD:0x766ED2] == bytes.fromhex("b800108ec0") and
         source[0x766ED4:0x766EDF] == bytes.fromhex("8a4410c1e002bb600603d8"),
         "second source reader explicitly selects ES1000 and indexes the 0660 owner")
    need(source[0x747CD6:0x747CE2] == bytes.fromhex("b800108ec026c70660060000"),
         "source ES1000 setup and exactly one halfword clear before the hard gate")
    need(struct.unpack_from("<7I", before, 0x5C4400) ==
         (0xE92D5FFF, 0xE59F800C, 0xE3A09000, 0xE1C890B0, 0xE8BD5FFF, 0xE12FFF1E, 0x030048A4),
         "0660 leaf preserves the full frame and clears only its proven halfword")
    owners = []
    for site in (0x352B44, 0x352DCC, 0x355EF0):
        encoded = word(before, site)
        need(encoded & 0x0FFF0000 == 0x059F0000, "0660 producer/consumer literal load")
        literal = site + 8 + (encoded & 0xFFF)
        need(word(before, literal) == 0x030048A4, "producer and both live readers share the exact native owner")
        owners.append(dict(site=f"{BASE + site:08X}", literal=f"{literal:06X}"))
    return dict(palette=palette, P1=p1, P0=p0, later_constructor_arguments=constructors,
                native_0660_owner="030048A4", native_0660_owner_references=owners,
                source_0660_domain_evidence="Second reader 766ECD..766EEE has no intervening call or segment reassignment; the first reader's alternate ES path is not newly proved.",
                fixed_VRAM_uploads_added=0, new_constructors_called_during_initializer=0,
                source_boundaries=["7394", "73A9", "73D6", "73E2"], first_unresolved_instruction="4090:73E2")


def validate(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB ROM")
    need(after[ENTRY:START] == before[ENTRY:START] == struct.pack("<4I", *HEAD_WORDS), "first sixteen bytes unchanged")
    need(after[START:END] == payload(), "exact new call order and relocated original return")
    inverse = bytearray(after)
    inverse[START:END] = before[START:END]
    need(inverse == before, "full inverse: all callers, dependencies, resources and adjacent bytes retained")


def negatives(before, after, source):
    rejected = []
    for at in (*range(START, END), ENTRY, END, 0x5C1700, 0x5C4400, 0x5C7800):
        wrong = bytearray(after); wrong[at] ^= 1
        try:
            validate(before, wrong)
        except ValueError:
            rejected.append(dict(image="after", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed instruction, return, or external byte")
    for at in (ENTRY, START, EXTENSION, 0x5C7800, *(start for _, start, _, _ in GUARDS)):
        wrong = bytearray(before); wrong[at] ^= 1
        try:
            dependencies(wrong, source)
        except ValueError:
            rejected.append(dict(image="before", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed predecessor dependency or reservation")
    for at in (0x747C94, 0x747CA9, 0x747CD6, 0x747CDB, 0x747CE2, 0x747CE9):
        wrong = bytearray(source); wrong[at] ^= 1
        try:
            dependencies(before, wrong)
        except ValueError:
            rejected.append(dict(image="source", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed source or hard-gate boundary")
    return rejected


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW), "exact port predecessor and three originals")
    dependencies(before, source)
    proof = source_contract(before, gba, source)
    ownership = no_inbound(before, ((EXTENSION, END),))
    after = bytearray(before)
    after[START:END] = payload()
    validate(before, after)
    rejected = negatives(before, after, source)
    return bytes(after), dict(schema=1, status="PASS", kind="disconnected-shoot-initializer-front",
        input_sha256=PARENT, output_sha256=sha(after), output_bytes=len(after), native_entry=f"{BASE + ENTRY:08X}",
        source_range=["4090:7168", "4090:73E2"], new_source_range=["747C94", "747CE2"], source_continuation_sha256=SOURCE_HASH,
        declared_bytes=16, new_reservation_bytes=8, entry_bytes=32, changed_bytes=sum(a != b for a, b in zip(before, after)),
        writes=[dict(start=f"{START:06X}", end=f"{END:06X}", before_hex=before[START:END].hex(),
                     after_hex=after[START:END].hex())], first_sixteen_bytes_preserved=True, full_inverse=True,
        call_order=["08629700", "085C1000", "085C1700", "085C4400"], external_entry_added=False,
        full_initializer_absent=True, new_RAM_bytes=0, abi=dict(preserved="r0-r12,LR,SP", flags="clobbered",
        total_entry_stack_bytes=8, stack_increase_from_parent=0, slot5_local_and_callee_stack_bytes=92,
        clear_local_stack_bytes=56, complete_scene_stack_bound_proved=False),
        ownership=ownership, source_contract=proof,
        dependencies=[dict(name=n, start=f"{a:06X}", end=f"{z:06X}", sha256=h) for n, a, z, h in GUARDS],
        negative_cases=len(rejected), rejected_mutations=rejected,
        preconditions=["Retained native engine/renderer startup, valid existing player/auxiliary objects, and native stack.",
                       "Exclusive scene/display ownership; object, full transitive stack and scene lifetimes are not newly proved."],
        limits=["Stops immediately before ES1000:3CD8 at source73E2; neither unresolved SRAM halfword is cleared or assumed dead.",
                "P0 preload correspondence uses the existing source-identical dynamic renderer resources, not a new fixed-VRAM upload.",
                "No external scene/controller route, terminal DI/camera closure, full initializer, emulator or save use."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.old.suffix.lower() == args.source.suffix.lower() == ".wsc", "ROM-only inputs before reading")
    inputs = {getattr(args, n).resolve() for n in ("before", "gba", "old", "source")}
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json" and
         args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve() != args.manifest.resolve(), "distinct ROM/report artifacts before reading")
    after, report = build(*(getattr(args, n).read_bytes() for n in ("before", "gba", "old", "source")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
                         changed_bytes=report["changed_bytes"], negative_cases=report["negative_cases"])))


if __name__ == "__main__":
    main()
