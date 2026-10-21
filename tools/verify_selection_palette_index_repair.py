#!/usr/bin/env python3
"""Decode the palette cursor adapter and verify its native consumer independently."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

PRE = "99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
BASE, SITE, BRIDGE, END = 0x08000000, 0x831C0, 0x628240, 0x628278
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def decode(data, at, text):
    ins = next(ARM.disasm(data[at:at + 4], BASE + at), None)
    need(ins is not None and ins.mnemonic + " " + ins.op_str == text, f"actual instruction {at:06X}: {text}")


def allocation(before):
    need(before[BRIDGE:END] == b"\xFF" * (END - BRIDGE), "blank new bridge")
    for at in range(len(before) - 3):
        need(not BASE + BRIDGE <= word(before, at) < BASE + END, "prior encoded pointer into bridge")
    for at in range(0, len(before) - 3, 4):
        w = word(before, at)
        if w >> 28 == 15:
            continue
        if w & 0x0E000000 == 0x0A000000:
            n = w & 0xFFFFFF
            n -= 0x1000000 if n & 0x800000 else 0
            need(not BRIDGE <= at + 8 + n * 4 < END, "prior ARM branch into bridge")
        if w & 0x0E1F0000 == 0x041F0000:
            n = (w & 4095) * (1 if w & 0x800000 else -1)
            need(not BRIDGE <= at + 8 + n < END, "prior immediate PC-relative bridge access")


def verify(before, after, gba):
    need(len(before) == len(after) == 0x800000, "expanded ROM sizes")
    need(before[0x83178:0x8322C] == gba[0x83178:0x8322C], "actual retail palette path")
    for at, text in ((0x83178, "ldrh r1, [r4, #4]"), (0x8317C, "ldrh r0, [r4, #6]"),
                     (0x83188, "and r8, r0, #0xff"), (0x8318C, "and sb, r1, #0xff"),
                     (0x83190, "cmp r8, sb"), (0x83194, "bne #0x808322c"),
                     (0x83198, "lsr r8, r0, #8"), (0x8319C, "lsr sb, r1, #8"),
                     (0x831A0, "cmp r8, sb"), (0x831A4, "bne #0x80831ac"),
                     (0x831C4, "lsls r1, r1, #5"), (0x831C8, "ldr r8, [pc, #0xbc]"),
                     (0x831CC, "add r1, r1, r8"), (0x831DC, "ldr r8, [r1, #8]"),
                     (0x83204, "ldr r8, [r1, #0xc]")):
        decode(after, at, text)
    need(word(after, 0x83288) == 0x03004738 and word(after, 0x8328C) == 0x084A80F8,
         "selection state and canonical resource base unchanged")
    decode(before, SITE, "and r1, r1, #0xff")
    decode(after, SITE, "b #0x8628240")
    instructions = ("push {r0, r8}", "and r1, r1, #0xff", "ldr r0, [pc, #0x20]",
                    "ldrb r0, [r0, #0x19]", "and r0, r0, #0x30", "lsl r0, r0, #1",
                    "ldr r8, [pc, #0x14]", "add r8, r8, r0", "add r8, r8, r1, lsl #1",
                    "ldrh r1, [r8]", "pop {r0, r8}", "b #0x80831c4")
    for index, text in enumerate(instructions):
        at = BRIDGE + index * 4
        decode(after, at, text)
        w = word(after, at)
        need(w >> 28 == 14, "adapter independent of incoming condition flags")
        if index in (1, 4, 5, 7, 8):
            need(not w & 0x100000, "adapter preserves every incoming NZCV combination")
    owner_pool = BRIDGE + 8 + 8 + (word(after, BRIDGE + 8) & 4095)
    table_pool = BRIDGE + 24 + 8 + (word(after, BRIDGE + 24) & 4095)
    need(word(after, owner_pool) == 0x03002310 and word(after, table_pool) == 0x08628000,
         "decoded literal addresses retain existing owners")
    need(sha(after[0x628000:0x628080]) == "865C8CC29792AA98C64DEFDCB9B9619325FE54433AFC9F9E0AE264FBC92E5C4A",
         "fixed source-backed roster views")
    cases = 0
    for unlock in range(256):
        expected = list(range(11)) + [13, 14]
        expected += [ident for bit, ident in ((16, 11), (32, 12)) if unlock & bit]
        for index, ident in enumerate(expected):
            for palette in range(2):
                registers = {0: 0xDEAD1234 ^ unlock, 1: index | palette << 8, 8: 0x03004738}
                saved = registers[0], registers[8]
                registers[1] &= word(after, BRIDGE + 4) & 255
                registers[0] = word(after, owner_pool)
                need(registers[0] + (word(after, BRIDGE + 12) & 4095) == 0x03002329,
                     "actual unsigned unlock byte load")
                registers[0] = unlock & (word(after, BRIDGE + 16) & 255)
                registers[0] <<= word(after, BRIDGE + 20) >> 7 & 31
                registers[8] = word(after, table_pool) + registers[0]
                registers[8] += registers[1] << (word(after, BRIDGE + 32) >> 7 & 31)
                registers[1] = struct.unpack_from("<H", after, registers[8] - BASE)[0]
                registers[0], registers[8] = saved
                need(registers[1] == ident and (registers[0], registers[8]) == saved,
                     "decoded adapter output and saved-register restoration")
                resource = word(after, 0x8328C) - BASE + (registers[1] << 5)
                palette_source = word(after, resource + 8 + palette * 4)
                need(BASE <= palette_source <= BASE + len(after) - 38, "real downstream palette lookup remains bounded")
                cases += 1
    inverse = bytearray(after)
    inverse[SITE:SITE + 4] = before[SITE:SITE + 4]
    inverse[BRIDGE:END] = before[BRIDGE:END]
    need(inverse == before, "whole-ROM inverse outside exact hook and adapter")
    return dict(native_instruction_contracts=15, bridge_instruction_contracts=12,
                lookup_cases=cases, unlock_bytes=256, palette_variants=2,
                ABI="only mapped r1 output; r0/r8 restored; eight-byte balanced stack; all16 NZCV, other registers and LR preserved",
                source_policy="established clean-mode roster views only")


def main():
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "report"):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in vars(args).values()), "save paths forbidden")
    before, after, gba = (getattr(args, name).read_bytes() for name in ("before", "after", "gba"))
    need((sha(before), sha(gba)) == (PRE, GBA), "fixed predecessor and retail source")
    allocation(before)
    result = verify(before, after, gba)
    negatives = []
    for at, label in ((SITE, "native hook"), (BRIDGE, "saved-register set"),
                      (BRIDGE + 4, "cursor mask"), (BRIDGE + 16, "unlock mask"),
                      (BRIDGE + 20, "view stride"), (BRIDGE + 32, "index scaling"),
                      (BRIDGE + 40, "register restore"), (BRIDGE + 44, "continuation"),
                      (BRIDGE + 48, "unlock owner"), (BRIDGE + 52, "roster owner"),
                      (0x628018, "ID14 mapping"), (0x12340, "unrelated mutation")):
        damaged = bytearray(after)
        damaged[at] ^= 1
        try:
            verify(before, damaged, gba)
        except ValueError as error:
            negatives.append(dict(case=label, rejected=True, reason=str(error)))
        else:
            raise ValueError("damaging mutation accepted: " + label)
    result.update(schema=1, kind="independent-selection-palette-index-verification", status="PASS",
                  input_sha256=sha(before), output_sha256=sha(after), negative_cases=negatives,
                  generator_imported=False, emulator_or_save_access=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-selection-palette-index] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
