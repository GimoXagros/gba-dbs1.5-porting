#!/usr/bin/env python3
"""Install the disconnected, source-ordered Shoot initializer prefix.

Only source 4090:7168..71D1 is represented. The new entry has no caller and
does not satisfy the full initializer's SRAM, object, terminal, or camera
contracts. No existing instruction, table, resource, or RAM allocation changes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, no_inbound

PARENT = "389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1"
ENTRY, END = 0x629700, 0x62975C
CALLS = ((0x08, 0x085C7200), (0x18, 0x085C6800), (0x44, 0x0836D224))
GUARDS = (
    ("source", 0x747A68, 0x747AD1, "DB1395FB28D6E4EEB226D1189145B62403F3E440880070F4ED7D8793B66093C5", "complete source prefix and next-phase segment setup"),
    ("source", 0x77DCB4, 0x77DE62, "F43D8674B2C9CC396250727CD2987FBBC0E5015348839F1771234F0D80A3D2E4", "dedicated graphics source"),
    ("source", 0x743FC0, 0x7440C7, "A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6", "source stage manager"),
    ("source", 0x740C73, 0x740CB3, "EE2E4E79E4C547419CFA1C2B2795B9EE91BF403F1AE26D67986F83F460057F00", "new source timer producer"),
    ("old", 0x390A33, 0x390A73, "0334FF449070DBFEBF0EBA3345F79F0819B6939E5B4164496DAE70EB5810BED9", "commercial source timer producer"),
    ("gba", 0xD17F8, 0xD18A0, "72A2447F55763B6E59941E06367CD144770746BA2D13DA2258378D94C89F5FD9", "native timer constants and owner"),
    ("gba", 0x37500C, 0x37501C, "663FDF6FFEA987EDCE05F57FDA219DE50060117AC914211743440440401A03D0", "native timer decrement"),
    ("gba", 0x373D34, 0x373D4C, "BE55AEF0CD7A8CDCD3BC3C814CCBA58C51AA1EFF1565CB04FD400C037A53DB6E", "native HUD seconds divisor"),
    ("before", 0x5C6800, 0x5C7800, "523710887E9E7DE9F34EF6E52BA466699839AD190A800E0B0D1819654D4E3265", "retained dedicated graphics and preamble family"),
    ("before", 0x5C4300, 0x5C4354, "715D48A742EC4B7046E8822615D2E5A2599A7627FFCEFDC04587D338C72A272D", "native timer and flag owner subset; not called"),
    ("before", 0x36D224, 0x36D38C, "489A5436AB9158296B933F1DE55CD7CDE5BD198C979C866FA17933151B4A8C86", "stage manager with both private priority calls"),
    ("before", 0x629500, 0x629518, "7A42F8C8D7AA3EDFDB669182B498F1EC0A6091BCECA491B2BAD4CF55ECD2F94A", "private actual-stage11 priority helper"),
)


def bl(at: int, target: int) -> int:
    delta = target - (BASE + at + 8)
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM BL range")
    return 0xEB000000 | ((delta // 4) & 0xFFFFFF)


def prefix() -> bytes:
    # 20 ARM instructions, followed by three local literals. The existing
    # 085C4300 subset cannot be called here: it would repeat the stage store
    # after graphics. Keep that immutable subset and emit its timer body.
    words = (
        0xE92D5FFF,                 # preserve r0-r12, lr
        0xE3A0B000,                 # native zero-r11 service convention
        bl(ENTRY + 0x08, 0x085C7200),
        0xE59F803C,                 # stage literal at +50
        0xE3A0900B,
        0xE5C89000,                 # one byte store, before graphics
        bl(ENTRY + 0x18, 0x085C6800),
        0xE59F8030,                 # timer literal at +54
        0xE3A09DE1,                 # 14400 native ticks, source 18000
        0xE1C890B0,
        0xE59F8028,                 # flags literal at +58
        0xE3A09000,
        0xE1C890B0,                 # +0 = 0
        0xE1C890B2,                 # +2 = 0
        0xE1C890B4,                 # +4 = 0
        0xE3A09010,
        0xE1C890B0,                 # +0 = 10 after all three clears
        bl(ENTRY + 0x44, 0x0836D224),
        0xE8BD5FFF,
        0xE12FFF1E,
        0x0300231E, 0x03004500, 0x03004506,
    )
    return struct.pack("<23I", *words)


def dependencies(blobs: dict[str, bytes]) -> None:
    for name, start, end, expected, label in GUARDS:
        need(sha(blobs[name][start:end]) == expected, label)
    source = blobs["source"]
    # Decode the exact source widths/order independently of the new ARM
    # payload construction, including the graphics/manager far calls.
    pieces = (
        (0x747A95, "26c6450e0b"),
        (0x747A9A, "9ac40fcf7c"),
        (0x747AA4, "c706ce035046"),
        (0x747AAA, "c706d4030000"),
        (0x747AB0, "c706d6030000"),
        (0x747AB6, "c706d8030000"),
        (0x747ABC, "810ed4031000"),
        (0x747AC2, "9ac0369040"),
        (0x747AC7, "b8000cba00108ed88ec2"),
    )
    for at, encoded in pieces:
        expected = bytes.fromhex(encoded)
        need(source[at:at + len(expected)] == expected, "source effect order/width at " + hex(at))
    before = blobs["before"]
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer remains absent")
    need(before[ENTRY:END] == b"\xff" * (END - ENTRY), "prefix exact FF ownership")


def validate(before: bytes, after: bytes) -> None:
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB ROM size")
    need(after[ENTRY:END] == prefix(), "exact source-ordered prefix, calls and local literals")
    inverse = bytearray(after)
    inverse[ENTRY:END] = before[ENTRY:END]
    need(bytes(inverse) == before, "full inverse; every existing byte and external route retained")


def negatives(blobs: dict[str, bytes], after: bytes) -> list[dict]:
    rejected = []
    # Each instruction/literal is meaningful: wrong store widths, owners,
    # call/return links, preserved registers, and source order are rejected.
    for offset in range(0, END - ENTRY, 4):
        wrong = bytearray(after)
        wrong[ENTRY + offset] ^= 1
        try:
            validate(blobs["before"], wrong)
        except ValueError:
            rejected.append(dict(kind="prefix_word", offset=f"{ENTRY + offset:06X}"))
        else:
            raise AssertionError("prefix corruption accepted")
    for site in (0x5C4300, 0x5C7800, 0x36D28C, 0x629500, END):
        wrong = bytearray(after)
        wrong[site] ^= 1
        try:
            validate(blobs["before"], wrong)
        except ValueError:
            rejected.append(dict(kind="outside_write", offset=f"{site:06X}"))
        else:
            raise AssertionError("external or adjacent write accepted")
    for name, start, _, _, label in GUARDS:
        changed = bytearray(blobs[name])
        changed[start] ^= 1
        wrong = dict(blobs, **{name: bytes(changed)})
        try:
            dependencies(wrong)
        except ValueError:
            rejected.append(dict(kind="dependency", image=name, offset=f"{start:06X}", label=label))
        else:
            raise AssertionError("changed source or native dependency accepted")
    wrong = dict(blobs)
    occupied = bytearray(wrong["before"])
    occupied[ENTRY] = 0
    wrong["before"] = bytes(occupied)
    try:
        dependencies(wrong)
    except ValueError:
        rejected.append(dict(kind="occupied_reservation", offset=f"{ENTRY:06X}"))
    else:
        raise AssertionError("occupied reservation accepted")
    return rejected


def build(before: bytes, gba: bytes, old: bytes, source: bytes) -> tuple[bytes, dict]:
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW),
         "exact predecessor and three immutable source ROMs")
    blobs = dict(before=before, gba=gba, old=old, source=source)
    dependencies(blobs)
    ownership = no_inbound(before, ((ENTRY, END),))
    payload = prefix()
    need(len(payload) == END - ENTRY == 92, "20 instruction and three literal words")
    after = bytearray(before)
    after[ENTRY:END] = payload
    validate(before, after)
    # Check the completed image too, excluding only this entry's own local
    # literals and instruction encodings. No existing caller is introduced.
    outside = bytearray(after)
    outside[ENTRY:END] = b"\xff" * (END - ENTRY)
    need(bytes(outside) == before, "disconnected prefix with no external caller or pointer")
    rejected = negatives(blobs, bytes(after))
    report = dict(schema=1, status="PASS", kind="disconnected-shoot-initializer-prefix",
        input_sha256=PARENT, output_sha256=sha(after), output_bytes=len(after),
        native_entry=f"{BASE + ENTRY:08X}", source_range=["4090:7168", "4090:71D1"],
        source_raw_half_open=["747A68", "747AD1"],
        source_prefix_sha256=sha(source[0x747A68:0x747AD1]),
        declared_bytes=len(payload), changed_bytes=sum(a != b for a, b in zip(before, after)),
        writes=[dict(start=f"{ENTRY:06X}", end=f"{END:06X}", bytes=len(payload),
                     before_sha256=sha(before[ENTRY:END]), after_sha256=sha(payload))],
        instructions=20, literal_words=3, full_inverse=True, external_callers_added=0,
        new_RAM_bytes=0, full_initializer_absent=True, ownership=ownership,
        calls=[dict(site=f"{BASE + ENTRY + off:08X}", target=f"{target:08X}") for off, target in CALLS],
        direct_memory_writes=[dict(address="0300231E", bytes=1, value=11),
                              dict(address="03004500", bytes=2, value=14400),
                              dict(address="03004506", bytes=2, value=0),
                              dict(address="03004508", bytes=2, value=0),
                              dict(address="0300450A", bytes=2, value=0),
                              dict(address="03004506", bytes=2, value=16)],
        dependencies=[dict(image=n, start=f"{a:06X}", end=f"{b:06X}", sha256=h, purpose=l)
                      for n, a, b, h, l in GUARDS],
        negative_cases=len(rejected), rejected_mutations=rejected,
        abi="preserve r0-r12/LR/SP; flags clobbered; r11 zero only inside saved frame",
        preconditions=["Exclusive scene/display ownership with normal initialized native engine globals.",
                       "Resident graphics, preamble, stage-manager and stage-priority dependencies retain their verified contracts."],
        limits=["Disconnected prefix only; no normal gameplay reachability or runtime claim.",
                "No player/object binding or full initializer at 085C7800 is connected.",
                "Source SRAM observer/storage, terminal DI, camera lifetime, complete scene/controller and campaign gates remain open.",
                "No new proof of unrestricted reused-service or timing equivalence."])
    return bytes(after), report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.old.suffix.lower() == args.source.suffix.lower() == ".wsc",
         "explicit ROM-only input extensions checked before reading")
    inputs = {getattr(args, name).resolve() for name in ("before", "gba", "old", "source")}
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json", "explicit artifact types")
    need(args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve() != args.manifest.resolve(), "input/output aliases rejected before reading")
    after, report = build(*(getattr(args, name).read_bytes() for name in ("before", "gba", "old", "source")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
                         declared_bytes=92, changed_bytes=report["changed_bytes"], negative_cases=report["negative_cases"])))


if __name__ == "__main__":
    main()
