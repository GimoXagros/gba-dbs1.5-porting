#!/usr/bin/env python3
"""Map the selection cursor to its fighter before the palette-only table lookup."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

PRE = "99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
BASE, SITE, BRIDGE, END = 0x08000000, 0x831C0, 0x628240, 0x628278


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, target):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM branch range")
    return 0xEA000000 | (delta // 4 & 0xFFFFFF)


def ownership(before):
    need(before[BRIDGE:END] == b"\xFF" * (END - BRIDGE), "exact bridge allocation is FF")
    site_refs, site_branches = [], []
    for at in range(len(before) - 3):
        value = word(before, at)
        need(not BASE + BRIDGE <= value < BASE + END, "existing encoded pointer into bridge")
        if value in (BASE + SITE, BASE + SITE + 4):
            site_refs.append(at)
    for at in range(0, len(before) - 3, 4):
        value = word(before, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            offset = value & 0xFFFFFF
            offset -= 0x1000000 if offset & 0x800000 else 0
            target = at + 8 + offset * 4
            need(not BRIDGE <= target < END, "existing ARM branch into bridge")
            if target in (SITE, SITE + 4):
                site_branches.append(at)
        if value & 0x0E1F0000 == 0x041F0000:
            offset = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not BRIDGE <= at + 8 + offset < END, "existing PC-relative access into bridge")
    need(not site_refs and not site_branches, "hook and continuation are reached by this native fallthrough only")


def build(before, gba):
    need((sha(before), sha(gba)) == (PRE, GBA) and len(before) == 0x800000, "fixed source identities")
    need(before[0x83178:0x8322C] == gba[0x83178:0x8322C] and
         sha(before[0x83178:0x8322C]) == "C36735270ADBA3C89423DDECCA728F2534043721F0B605B5440107121F477ED1",
         "actual same-cursor/different-palette consumer and both palette branches")
    need(word(before, SITE) == 0xE20110FF and word(before, SITE + 4) == 0xE1B01281,
         "Expected Write cursor mask followed by resource-record scaling")
    need(word(before, 0x83288) == 0x03004738 and word(before, 0x8328C) == 0x084A80F8,
         "native selection-state and canonical resource owners")
    need(sha(before[0x628000:0x628080]) == "865C8CC29792AA98C64DEFDCB9B9619325FE54433AFC9F9E0AE264FBC92E5C4A",
         "existing source-backed immutable roster views")
    ownership(before)
    words = (0xE92D0101, 0xE20110FF, 0xE59F0020, 0xE5D00019,
             0xE2000030, 0xE1A00080, 0xE59F8014, 0xE0888000,
             0xE0888081, 0xE1D810B0, 0xE8BD0101,
             branch(BRIDGE + 44, SITE + 4), 0x03002310, 0x08628000)
    bridge = struct.pack("<14I", *words)
    need(len(bridge) == END - BRIDGE, "exact bridge extent")
    after = bytearray(before)
    struct.pack_into("<I", after, SITE, branch(SITE, BRIDGE))
    after[BRIDGE:END] = bridge
    need(word(after, BRIDGE + 8 + 8 + (word(after, BRIDGE + 8) & 4095)) == 0x03002310 and
         word(after, BRIDGE + 24 + 8 + (word(after, BRIDGE + 24) & 4095)) == 0x08628000,
         "actual bridge PC-relative owners")
    cases = 0
    for unlock in range(256):
        expected = list(range(11)) + [13, 14] + ([11] if unlock & 0x10 else []) + ([12] if unlock & 0x20 else [])
        table = 0x628000 + ((unlock & 0x30) << 1)
        for index, ident in enumerate(expected):
            for palette in (0, 1):
                cursor = index | palette << 8
                actual = struct.unpack_from("<H", after, table + (cursor & 255) * 2)[0]
                need(actual == ident and actual < 15, "every live cursor/palette maps to its actual fighter")
                row = 0x4A80F8 + actual * 32
                pointer = word(after, row + (12 if palette else 8))
                need(BASE <= pointer <= BASE + len(after) - 38, "mapped native palette source in ROM")
                cases += 1
    inverse = bytearray(after)
    inverse[SITE:SITE + 4] = before[SITE:SITE + 4]
    inverse[BRIDGE:END] = before[BRIDGE:END]
    need(inverse == before, "complete inverse outside exact hook and bridge")
    return bytes(after), dict(schema=1, kind="selection-palette-index-repair", input_sha256=PRE,
        output_sha256=sha(after), changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        expected_writes=[dict(raw=SITE, bytes=4, before="E20110FF", after=f"{word(after, SITE):08X}"),
                         dict(raw=BRIDGE, bytes=len(bridge), sha256=sha(bridge))],
        finite_lookup_cases=cases, unlock_bytes=256, palette_variants=2,
        ABI="r1 becomes fighter ID; r0/r8 saved and restored; other registers, incoming NZCV, LR and SP preserved",
        cause="palette-only path used cursor index directly as canonical fighter index",
        source_policy="existing clean-mode ROM views; alternate source policy unchanged",
        provided_save_accessed=False, runtime_claim=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "gba", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in vars(args).values()), "save paths forbidden")
    after, manifest = build(args.before.read_bytes(), args.gba.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("[selection-palette-index-repair] " + manifest["output_sha256"])


if __name__ == "__main__":
    main()
