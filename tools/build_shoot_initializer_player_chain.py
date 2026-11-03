#!/usr/bin/env python3
"""Compose the disconnected Shoot prefix and existing player phase in order.

Only a 24-byte, two-call wrapper is added. Existing object handles, a valid
native stack, and exclusive scene/display ownership are preconditions, not
newly proved entry invariants. No complete initializer or scene hook is added.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, no_inbound
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from verify_shoot_player_binding import semantic_checks, decode
from verify_shoot_initializer_p1_assets import verify_entry, SPECS
from verify_shoot_far_tile_repair import check_asset

PARENT = "4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC"
ENTRY, END = 0x629800, 0x629818
SOURCE_START, SOURCE_END = 0x747AD1, 0x747C94
SOURCE_PHASE = "9B65CB9B0866AB0B2137B34BBAEAD2B367760B276C9EB3C6666575AA2D428774"
GUARDS = (
    ("prefix", 0x629700, 0x62975C, "F139BF6F77A01C884D70207AE0B13D5E52998411025DCE531BE1B96E6755FC0A"),
    ("player phase", 0x5C1000, 0x5C11A4, "AEF73AB400F8B6611201CBAF3F24E19693D62BA7D84976A8479FFA33A46D2843"),
    ("auxiliary reuse", 0x5C1300, 0x5C1308, "57DC8F64037C3351974AD77B27E4300F2149CE6B7FDA13F8CA9B9985163EB9FD"),
    ("HP table", 0x5C1400, 0x5C141E, "F19BB19802488BA10E6948937E946AF4385760BF7E88CE4FBDC4A7006346B98E"),
    ("auxiliary body and literals", 0x5BC244, 0x5BC3B4, "BA5A9707BB6C8F1285251AFAA53ED0F98135A1FEA1107FDF858AD9CC3CE0F2A2"),
    ("auxiliary idle", 0x5BC600, 0x5BC604, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("both P1 containers", 0x5D0000, 0x5D0A4C, "778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2"),
    ("active P0 with repaired pointer", 0x5D1000, 0x5D1080, "5A2C5CC07776A7100216F2E9F34E4E858EFB46389F1981D71D19F3336864FE0C"),
    ("active P0 repaired descriptors and pixels", 0x5F3B20, 0x5F4A00, "C943F1CE481B5BC2B18F2DABD9EAB2D78C891218A6C0B022A3CF390CE1027662"),
    ("auxiliary P0", 0x5D1100, 0x5DB2C0, "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91"),
    ("active P2", 0x5B9300, 0x5B9328, "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C"),
    ("auxiliary P2", 0x5DB700, 0x5DB728, "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD"),
    ("native presentation constructor", 0x127E4, 0x12874, "7318C6DA564B699897D6E9EE7B22EA26540EE84F8492D3CCD247DF8E8A4EB94D"),
    ("native event entry", 0x12874, 0x1290C, "39A09A7E39AA497CE1B6487C3E2D328362DF5D5694001CE3EB1E2D3A85D3A488"),
    ("native P2 loader", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
)


def bl(at, target):
    displacement = target - (BASE + at + 8)
    need(displacement % 4 == 0 and -(1 << 25) <= displacement < (1 << 25), "ARM BL range")
    return 0xEB000000 | ((displacement // 4) & 0xFFFFFF)


def wrapper():
    # Both callees already preserve r0-r12; only our r11 change and LR need saving.
    return struct.pack("<6I", 0xE92D4800, 0xE3A0B000,
                       bl(ENTRY + 8, 0x08629700), bl(ENTRY + 12, 0x085C1000),
                       0xE8BD4800, 0xE12FFF1E)


def dependencies(before, source):
    need(sha(source[SOURCE_START:SOURCE_END]) == SOURCE_PHASE, "complete actual source player phase")
    for label, start, end, expected in GUARDS:
        need(sha(before[start:end]) == expected, label)
    need(before[ENTRY:END] == b"\xff" * 24, "exact wrapper reservation is erased")
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer remains absent")


def resources(before, gba, source):
    instructions = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[SOURCE_START:SOURCE_END], 0x71D1))
    need(len(instructions) == 129 and sum(i.size for i in instructions) == SOURCE_END - SOURCE_START,
         "all actual source player-phase instructions decoded")
    need(len(decode(before, 0x5C1000, 0x5C1180)) == 96, "complete retained native player phase")
    for label, start, end, _ in GUARDS[-3:]:
        need(before[start:end] == gba[start:end], label + " retains original instructions")
    consumers = [(i.mnemonic, i.op_str) for i in decode(gba, 0x127E4, 0x12804)]
    need(consumers == [("push", "{r0, r3, r4, r5}"), ("ldr", "r5, [sp, #0x48]"),
         ("ldr", "r0, [sp, #0x40]"), ("str", "r0, [r5, #0x44]"),
         ("ldr", "r0, [sp, #0x34]"), ("str", "r0, [r5, #0x48]"),
         ("ldr", "r0, [sp, #0x28]"), ("str", "r0, [r5, #0x4c]")],
         "actual constructor stack slots consume P1/P0/P2 in that order")
    constructors = semantic_checks(before)
    source_resources = []
    for start, end, native in ((0x7270, 0x729A, constructors[2]), (0x7329, 0x7353, constructors[1])):
        pushes = [int(i.op_str, 0) for i in instructions if start <= i.address < end and
                  i.mnemonic == "push" and i.op_str != "si"]
        need(len(pushes) == 14 and pushes[:4] == native["entry_sp_arguments"][:4],
             "actual source/native constructor slot, tile and geometry arguments")
        addresses = []
        for at in (10, 7, 4):
            bank, segment, offset = pushes[at:at + 3]
            need(offset == 0 and 0x2000 <= segment < 0x3000, "source resource far address")
            addresses.append((bank % 128) * 65536 + segment * 16 - 0x20000)
        source_resources.append(addresses)
    need(source_resources == [[0x3CF410, 0x3D5F80, 0x3D4B20], [0x3BD730, 0x3914E0, 0x3D7640]],
         "source pushes select the independently checked resource bodies")
    p1 = [verify_entry(source, before[0x5D0000:0x5D0A4C], spec) for spec in SPECS]
    p0 = [check_asset(before, source, *spec) for spec in
          ((0x3D5F80, 0x5D1000, 28, 0x3CF410, 0x5D0000),
           (0x3914E0, 0x5D1100, 61, 0x3BD730, 0x5D029C))]
    for src, native in ((0x3D4B20, 0x5B9300), (0x3D7640, 0x5DB700)):
        need(before[native:native + 6] == source[src:src + 6], "P2 source header identity")
        for index, color in enumerate(struct.unpack_from("<16H", before, native + 6)):
            channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
            need(not color & 0x8000 and all(c == 0 or c >= 3 and c % 2 for c in channels), "P2 source color lattice")
            original = (channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2
            need(original == struct.unpack_from("<H", source, src + 6 + index * 2)[0], "P2 source inverse")
    values = struct.unpack_from("<15H", source, 0x747E54)
    need(values == struct.unpack_from("<15H", before, 0x5C1400) and all(0 < v < 0x8000 for v in values),
         "all fifteen source HP values and signed-quarter domain")
    for value in values:
        for difficulty in range(256):
            hp = value
            if difficulty == 0:
                hp -= value >> 2
            elif difficulty >= 2:
                hp += value >> 2
                if difficulty == 3:
                    hp += value >> 2
            native = value - (value >> 2) if difficulty == 0 else value + (value >> 2 if difficulty >= 2 else 0) + (value >> 2 if difficulty == 3 else 0)
            need((hp, hp >> 1, hp >> 2) == (native, native >> 1, native >> 2), "all native/source HP and threshold cases")
    for flags in range(65536):
        need(((flags | 0x20) & 0x43FF) == ((flags | 0x20) & ~0xBC00), "active flag mask equivalence")
        need((((flags & 0xFFF0) | 0x26) & 0x9FBF) == (((flags & ~0xF) | 0x26) & ~0x6000 & ~0x40),
             "auxiliary flag mask equivalence")
    return dict(source_instructions=129, native_player_instructions=96, constructors=constructors,
                source_P1_P0_P2=source_resources, P1=p1, P0=p0, P2_colors_inversed=32,
                HP_difficulty_cases=3840, object_flag_cases=131072)


def validate(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB ROM size")
    need(after[ENTRY:END] == wrapper(), "exact two-call order and r11/LR save/restore")
    inverse = bytearray(after)
    inverse[ENTRY:END] = before[ENTRY:END]
    need(inverse == before, "full inverse preserves every existing byte and external route")


def negatives(before, after, source):
    rejected = []
    for at in (*range(ENTRY, END), ENTRY - 1, END, 0x629700, 0x5C1000, 0x5C7800, 0x5D1004):
        wrong = bytearray(after); wrong[at] ^= 1
        try:
            validate(before, wrong)
        except ValueError:
            rejected.append(dict(kind="output", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted output corruption")
    for at in (*(start for _, start, _, _ in GUARDS), ENTRY, 0x5C7800):
        wrong = bytearray(before); wrong[at] ^= 1
        try:
            dependencies(wrong, source)
        except ValueError:
            rejected.append(dict(kind="predecessor", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed dependency or ownership")
    wrong = bytearray(source); wrong[SOURCE_START] ^= 1
    try:
        dependencies(before, wrong)
    except ValueError:
        rejected.append(dict(kind="source", offset=f"{SOURCE_START:06X}"))
    else:
        raise ValueError("accepted changed source phase")
    return rejected


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW), "exact predecessor and three originals")
    dependencies(before, source)
    proof = resources(before, gba, source)
    ownership = no_inbound(before, ((ENTRY, END),))
    after = bytearray(before)
    after[ENTRY:END] = wrapper()
    validate(before, after)
    # The full inverse preserves every possible outside reference; both reviewed BLs leave this wrapper.
    rejected = negatives(before, after, source)
    return bytes(after), dict(schema=1, status="PASS", kind="disconnected-shoot-initializer-player-chain",
        input_sha256=PARENT, output_sha256=sha(after), output_bytes=len(after), native_entry=f"{BASE + ENTRY:08X}",
        source_range=["4090:7168", "4090:7394"], source_player_range=["747AD1", "747C94"],
        source_player_sha256=SOURCE_PHASE, declared_bytes=24,
        changed_bytes=sum(a != b for a, b in zip(before, after)), full_inverse=True,
        writes=[dict(start=f"{ENTRY:06X}", end=f"{END:06X}", bytes=24,
                     before_sha256=sha(before[ENTRY:END]), after_sha256=sha(after[ENTRY:END]))],
        call_order=["08629700", "085C1000"], entry_external_callers_added=0, new_internal_calls=2,
        new_RAM_bytes=0, full_initializer_absent=True, ownership=ownership, resource_contract=proof,
        dependencies=[dict(name=n, start=f"{a:06X}", end=f"{z:06X}", sha256=h) for n, a, z, h in GUARDS],
        abi=dict(preserved="r0-r12,LR,SP", saved_here="r11,LR", additional_stack_bytes=8,
                 flags="clobbered", internal_r11=0, known_direct_constructor_path_bytes=176,
                 complete_transitive_stack_bound_proved=False),
        negative_cases=len(rejected), rejected_mutations=rejected,
        preconditions=["Valid native stack with eight bytes beyond retained callees' requirements; actual scene stack ownership remains unproved.",
                       "Existing valid objects at 030048A0, 0300489C, 03004D3C; other character ID in 0..14.",
                       "Exclusive scene/display ownership throughout both calls."],
        limits=["Only retained component/service order is composed; existing player intermediate store timing is not newly proved.",
                "No external scene/controller caller, full initializer, game execution, save access or gameplay claim.",
                "SRAM 1000:3CD8/3CDA, terminal DI, camera lifetime and the remaining initializer phases stay open."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.old.suffix.lower() == args.source.suffix.lower() == ".wsc", "ROM-only extensions before reading")
    inputs = {getattr(args, name).resolve() for name in ("before", "gba", "old", "source")}
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json" and
         args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve() != args.manifest.resolve(), "distinct output artifact paths before reading")
    after, report = build(*(getattr(args, name).read_bytes() for name in ("before", "gba", "old", "source")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
                         changed_bytes=report["changed_bytes"], negative_cases=report["negative_cases"])))


if __name__ == "__main__":
    main()
