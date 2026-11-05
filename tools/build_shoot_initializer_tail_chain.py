#!/usr/bin/env python3
"""Append three existing source-order tail calls to the disconnected Shoot entry.

The storage cleanup and retained frame stay intact. The earlier scene snapshot
and exclusive palette/object lifetime remain caller preconditions; no scene
hook, new snapshot, allocator, renderer, or storage policy is added.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, no_inbound, branch_target
from verify_shoot_other_player_binding import check_phase, check_consumers as other_consumers
from verify_shoot_tail_resources import check_phases, check_consumers as tail_consumers
from verify_shoot_palette_transition import check_code, check_consumers as palette_consumers

PARENT = "66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF"
ENTRY, START, EXTENSION, END = 0x629800, 0x629878, 0x629880, 0x62988C
SOURCE_HASH = "91EE7DCA7CF669DC17CF74BE804681668D9382FBAC5B45CDE917BC1797C14689"
WORDS = (0xEBFE5F20, 0xEBFE5FDF, 0xEBFE60DE, 0xE8BD4800, 0xE12FFF1E)
BEFORE_WORDS = (0xE8BD4800, 0xE12FFF1E, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF)
CALLS = (0x085C1500, 0x085C1800, 0x085C1C00)
GUARDS = (
    ("complete retained storage/front code", ENTRY, START, "4F77D3C14FD5A514C814049C4F37583869454FEBADC25F858C9C7C278C231C87"),
    ("other-player phase", 0x5C1500, 0x5C1614, "F610E2C891FABD57EEE4DB4BEEA235E1F0DBC30F94961DE074297834EDDF2C21"),
    ("late HUD phase", 0x5C1800, 0x5C186C, "68C995EAA8035508E8646EA0D5DEC7A0DD245742D9A081607BAD24373EA7FC3D"),
    ("selective palette prepare", 0x5C1C00, 0x5C1CDC, "16645A9D5F1CFECC3AB744598F731D67E58111A3B38E3FC1828096DAB8EE59E6"),
    ("earlier scene snapshot, not called here", 0x5C1900, 0x5C1964, "69F3FF9409F6BC2D962DBA51F0166EF00C1F12D9FD1B0CC89B34DAE3421576C1"),
    ("source gray palette", 0x5C2300, 0x5C2320, "F1BD23DD066344C83E9E110E97B61D75CEBC7876CE7717EC624A60B960AF7EAF"),
    ("native HUD pixels", 0xD2FD0, 0xD3050, "FED06ADACACA6083C841FD002EB50BFAAD16CD70BBDC5B7A7C476871B76C70C7"),
    ("native HUD P2", 0xD3078, 0xD30A0, "6410DA9E5AF68D6D44199795D1B2DB6F1E5B7BFB8452017947C2C0BD94B431C0"),
    ("character resource reconfiguration", 0x353304, 0x3534E0, "596381F2ED01DF36F2D2CFFE1D5570473943D847071D478FC49C6F4FA810A6F3"),
    ("native presentation constructor", 0x127E4, 0x1285C, "EF628791EF3580DEAD14EEC7400E44A43A696EF8012D62304FD0C7B6A45FD0C2"),
    ("complete native animation event setter", 0x12874, 0x129C8, "1BBCE2EEE607287D2AEFA2B899D43A9C4C6890BFE5CCAF6533D8FAF6EBF2EBD4"),
    ("event sound request and literal", 0xD15C0, 0xD15F0, "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"),
    ("P4 pointer assignment only", 0x358254, 0x358264, "29922425BF9E209A3F7B1E004C1C7172892EEF080CBE93160740617AC6F4B73B"),
    ("stage flag helper and literal", 0x584940, 0x58496C, "797922C17ECE61A30D1307A67F2CB85BBF3E21203695211E1A49EAFF9DC9DFC6"),
    ("fifteen base-form resource records", 0x4A80F8, 0x4A82D8, "336F628D90606B41CFF9BB6E37B8E0CEE7A5865B5F86EDE285B855E29BA2F627"),
    ("fifteen base companion resource records", 0x4A82D8, 0x4A84B8, "03844B77030B7361D0068AB58AB4B01048CAC32F89FC083D453C6206536B4FFF"),
    ("native P2 loader", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
    ("native BG zero alias", 0x11454, 0x11470, "6F8F5B01001BF386ACE8715E2FB8A857F16F43E907D984940D5C2C2BC4D85E90"),
    ("current source-routed physics blob", 0x485000, 0x48521C, "B1DC4C8BC816DE6EF5952403C75A1BF4140A8F6A01A2051A33A3F65809EC29DF"),
)


def payload():
    return struct.pack("<5I", *WORDS)


def dependencies(before, source):
    need(sha(source[0x747CF0:0x747E34]) == SOURCE_HASH, "complete source tail through RETF at 7533")
    need(before[START:END] == struct.pack("<5I", *BEFORE_WORDS), "original return and twelve unused bytes")
    for label, start, end, expected in GUARDS:
        need(sha(before[start:end]) == expected, label)
    need(before[0x629870:START] == struct.pack("<2I", 0xE28DD008, 0xE8BD100F), "storage block and scratch registers restored before tail")
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "prospective external full-initializer entry remains absent")


def ownership(before):
    need(sha(before[ENTRY:START]) == GUARDS[0][3], "accepted complete ARM storage cleanup owner")
    need(struct.unpack_from("<I", before, 0x629870)[0] == 0xE28DD008,
         "D008 is the low half of the retained ARM ADD SP,#8, not a Thumb branch")
    expected = "pre-existing ownership of proposed writes: [('Thumb conditional B', 6461552, 140679300)]"
    try:
        no_inbound(before, ((EXTENSION, END),))
    except ValueError as error:
        need(str(error) == expected, "unclassified extension ownership: " + str(error))
    else:
        raise ValueError("expected positively owned ARM/Thumb interpretation candidate missing")
    return dict(all_alignment_mirrored_pointers=True, arm_thumb_static_references=True,
        external_references=[], classified_ARM_word="629870:E28DD008",
        false_Thumb_target="08629884", boundary="Finite encoded-reference scan; arbitrary computed aliases are not excluded.")


def source_contract(before, gba, source):
    check_phase(before)
    physics = other_consumers(gba, source, before)
    check_phases(before)
    resources = tail_consumers(before, source)
    check_code(before)
    palette_consumers(before, source)
    return dict(source_intervals=[["73F0", "74A2"], ["74A2", "74DA"], ["74DA", "7534"]],
        native_entries=[f"{entry:08X}" for entry in CALLS], current_physics_records=physics, late_resources=resources,
        other_player="0300489C; existing presentation +AC, character +11 in0..14, valid base/evolved physics +60",
        palette_prepare="384-byte selective capture, sixteen gray zeros, then 528-byte white hardware projection",
        earlier_snapshot="085C1900 before source1073 destructive colors; not repeated inside7168",
        retained_snapshot_rows="8/12/14/15; rows8/12 conditionally refreshed by the other-player phase")


def validate(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB ROM")
    need(after[START:END] == payload(), "exact source-order calls followed by original return")
    for index, target in enumerate(CALLS):
        at = START + index * 4
        encoded = struct.unpack_from("<I", after, at)[0]
        need(encoded >> 24 == 0xEB and branch_target(at, encoded) == target, "ARM BL target and state")
    inverse = bytearray(after)
    inverse[START:END] = before[START:END]
    need(inverse == before, "full inverse: storage cleanup, callers, resources and all other bytes unchanged")


def negatives(before, after, source):
    rejected = []
    for at in (*range(START, END), ENTRY, START - 8, START - 4, END, 0x5C1500, 0x5C1800, 0x5C1C00, 0x5C7800):
        wrong = bytearray(after); wrong[at] ^= 1
        try:
            validate(before, wrong)
        except ValueError:
            rejected.append(dict(image="after", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed call/return, storage cleanup, dependency or unrelated byte")
    for at in (START, EXTENSION, END - 1, 0x5C7800,
               *(at for _, start, end, _ in GUARDS for at in (start, end - 1))):
        wrong = bytearray(before); wrong[at] ^= 1
        try:
            dependencies(wrong, source)
        except ValueError:
            rejected.append(dict(image="before", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed dependency or occupied reservation")
    for at in (0x747CF0, 0x747DA2, 0x747DDA, 0x747E33):
        wrong = bytearray(source); wrong[at] ^= 1
        try:
            dependencies(before, wrong)
        except ValueError:
            rejected.append(dict(image="source", offset=f"{at:06X}"))
        else:
            raise ValueError("accepted changed source phase or return")
    wrong = bytearray(after)
    wrong[START:START + 8] = after[START + 4:START + 8] + after[START:START + 4]
    try:
        validate(before, wrong)
    except ValueError:
        rejected.append(dict(image="after", case="reordered first two tail calls"))
    else:
        raise ValueError("accepted reordered source phases")
    wrong = bytearray(before)
    struct.pack_into("<I", wrong, 0x700001, 0x0A629882)
    try:
        ownership(wrong)
    except ValueError:
        rejected.append(dict(image="before", case="unaligned mirrored pointer into new bytes"))
    else:
        raise ValueError("accepted external extension ownership")
    return rejected


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW), "exact storage predecessor and three original ROMs")
    dependencies(before, source)
    proof = source_contract(before, gba, source)
    owner = ownership(before)
    after = bytearray(before)
    after[START:END] = payload()
    validate(before, after)
    rejected = negatives(before, after, source)
    return bytes(after), dict(schema=1, status="PASS", kind="disconnected-shoot-initializer-tail-chain",
        input_sha256=PARENT, output_sha256=sha(after), output_bytes=len(after), native_entry=f"{BASE + ENTRY:08X}",
        source_range=["4090:7168", "4090:7534"], new_source_range=["747CF0", "747E34"], source_tail_sha256=SOURCE_HASH,
        declared_bytes=20, new_reservation_bytes=12, entry_bytes=140, changed_bytes=sum(a != b for a, b in zip(before, after)),
        writes=[dict(start=f"{START:06X}", end=f"{END:06X}", before_hex=before[START:END].hex(), after_hex=after[START:END].hex())],
        full_inverse=True, call_order=[f"{entry:08X}" for entry in CALLS], new_snapshot_call=False,
        storage_operations_and_cleanup_unchanged=True, external_entry_added=False, prospective_scene_initializer_entry_absent=True,
        new_RAM_bytes=0, abi=dict(preserved="r0-r12,LR,SP", flags="clobbered", retained_entry_stack_bytes=8,
            additional_tail_frame_bytes=0, each_helper_local_frame_bytes=56, late_P2_direct_stack_bytes=92,
            full_transitive_and_live_stack_bound_proved=False), ownership=owner, source_contract=proof,
        dependencies=[dict(name=n, start=f"{a:06X}", end=f"{z:06X}", sha256=h) for n, a, z, h in GUARDS],
        negative_cases=len(rejected), rejected_mutations=rejected,
        preconditions=["Retained front contract: native engine/renderer startup, valid player/auxiliary objects, stack and exclusive scene/display ownership.",
            "Other player at0300489C has valid presentation/resources, native character ID0..14 and matching base/evolved physics pointer.",
            "Full snapshot085C1900 already completed before source1073 destructive colors; canonical mirror remains owned through source1331 restore.",
            "Normal single case5 scene owner retains replaced input/battle tasks; no competing startup/pause/cutscene mirror owner.",
            "Inherited storage contract: initialized functional EEPROM backend and serialized DMA3/timer2/IRQ service; failed-device equivalence is not claimed."],
        limits=["Disconnected initializer composition only; no external scene route, earlier snapshot caller, native callback timing or runtime/save QA.",
            "No full scene-stack or arbitrary computed-alias proof; existing object/palette lifecycle is conditional on the stated owner.",
            "Guards cover synchronous helper code/literals and base resource tables; dynamic resource payload validity remains an inherited precondition.",
            "No fade callbacks, terminal DI/camera completion or gameplay-completion claim."])


def main():
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.old.suffix.lower() == args.source.suffix.lower() == ".wsc", "ROM-only inputs before reading")
    inputs = {getattr(args, name).resolve() for name in ("before", "gba", "old", "source")}
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json" and
         args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve() != args.manifest.resolve(), "distinct output/report paths before reading")
    need(not args.output.exists() and not args.manifest.exists(), "fresh output/report paths before reading")
    after, report = build(*(getattr(args, name).read_bytes() for name in ("before", "gba", "old", "source")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
        changed_bytes=report["changed_bytes"], negative_cases=report["negative_cases"])))


if __name__ == "__main__":
    main()
