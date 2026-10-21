#!/usr/bin/env python3
"""Independent literal, ABI, source-coordinate and full-ROM inverse checks."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

PRE = "7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD"
SRC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u32(data, at):
    return struct.unpack_from("<I", data, at)[0]


def ins(data, at, mnemonic, operands):
    decoded = next(ARM.disasm(data[at:at + 4], 0x08000000 + at), None)
    need(decoded is not None and (decoded.mnemonic, decoded.op_str) == (mnemonic, operands),
         f"decoded instruction {at:06X}: {mnemonic} {operands}")
    return {"raw": at, "mnemonic": mnemonic, "operands": operands}


def pool(data, at, register):
    value = u32(data, at)
    need(value & 0xFFFFF000 == 0xE59F0000 | register << 12, "ARM positive PC-relative LDR")
    address = at + 8 + (value & 0xFFF)
    return address, u32(data, address)


def incoming(data, first, last):
    for target in range(first, last):
        need(data.find(struct.pack("<I", 0x08000000 + target)) == -1, "existing encoded pointer")
    for at in range(0, len(data) - 3, 4):
        value = u32(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta >= 0x800000:
                delta -= 0x1000000
            need(not first <= at + 8 + 4 * delta < last, "existing ARM branch")
        if value & 0x0E1F0000 == 0x041F0000:
            offset = (value & 0xFFF) * (1 if value & 0x800000 else -1)
            need(not first <= at + 8 + offset < last, "existing ARM literal")


def verify(before, after, source, identities=True):
    if identities:
        need((sha(before), sha(source)) == (PRE, SRC), "exact collision predecessor and source")
    need(len(before) == len(after) == 0x800000, "ROM sizes")
    need(before[0x627900:0x62791C] == b"\xFF" * 28, "Expected Write empty bridge")
    need(pool(before, 0x582F00, 8) == (0x582F68, 0x03002310), "previous fixed direct-stage load")
    contracts = []
    for at, mnemonic, operands in (
        (0x582F00, "b", "#0x8627900"), (0x627900, "push", "{r0, lr}"),
        (0x627904, "bl", "#0x80d1c78"), (0x627908, "mov", "r1, r0"),
        (0x62790C, "pop", "{r0, lr}"), (0x627910, "ldr", "r8, [pc]"),
        (0x627914, "b", "#0x8582f08"),
        (0x582F08, "mov", "sb, r1"), (0x582F0C, "lsl", "r1, r1, #4"),
        (0x582F10, "cmp", "sb, #7"), (0x582F14, "addhs", "r1, r1, #0x10"),
        (0x582F18, "ldrsh", "r0, [r8, #0x14]"), (0x582F1C, "and", "r0, r0, #3"),
        (0x582F20, "cmp", "sb, #6"), (0x582F24, "andne", "r0, r0, #1"),
        (0x582F28, "lsl", "r0, r0, #3"), (0x582F2C, "add", "r1, r1, r0"),
        (0x582F30, "ldr", "r8, [sp, #0x24]"), (0x582F34, "cmp", "r8, #0"),
        (0x582F38, "addne", "r1, r1, #4"), (0x582F3C, "ldr", "r8, [pc, #0x20]"),
        (0x582F40, "add", "sb, r8, #0"), (0x582F44, "ldrh", "r0, [r1, sb]"),
        (0x582F48, "strh", "r0, [r4, #0x34]"), (0x582F4C, "strh", "r0, [r4, #0x38]"),
        (0x582F50, "add", "sb, r8, #2"), (0x582F54, "ldrh", "r0, [r1, sb]"),
        (0x582F58, "strh", "r0, [r4, #0x36]"), (0x582F5C, "strh", "r0, [r4, #0x3a]"),
        (0x582F60, "b", "#0x8353190"), (0xD1C78, "b", "#0x8582c40")):
        contracts.append(ins(after, at, mnemonic, operands))
    need(pool(after, 0x627910, 8) == (0x627918, 0x03002310), "original variant-state owner restored")
    need(pool(after, 0x582F3C, 8) == (0x582F64, 0x08583000), "same complete spawn table")
    # Audit all service instructions; only r0/r8 and flags may change.
    for index, (mnemonic, operands) in enumerate((
        ("ldr", "r8, [pc, #0x2c]"), ("ldrb", "r0, [r8, #0xa]"),
        ("cmp", "r0, #0xb"), ("moveq", "r0, #0xa"), ("bxeq", "lr"),
        ("cmp", "r0, #0xd"), ("moveq", "r0, #8"), ("bxeq", "lr"),
        ("cmp", "r0, #0xe"), ("moveq", "r0, #9"), ("bxeq", "lr"),
        ("ldrb", "r0, [r8, #0xe]"), ("bx", "lr"))):
        contracts.append(ins(after, 0x582C40 + index * 4, mnemonic, operands))
    need(pool(after, 0x582C40, 8) == (0x582C74, 0x03002310), "existing temporary stage-policy owner")
    need(after[0x582C40:0x582C78] == before[0x582C40:0x582C78], "temporary routing policy not changed")
    need(after[0x583000:0x5830C0] == source[0x743224:0x7432E4], "all11source stage pairs")
    need(after[0x5830C0:0x5830D0] == before[0x5830C0:0x5830D0], "dedicated Shoot placeholder unchanged")
    # Native policy immediates are decoded from guarded CMP/MOVEQ words.
    rules = [(u32(after, 0x582C48) & 255, u32(after, 0x582C4C) & 255),
             (u32(after, 0x582C54) & 255, u32(after, 0x582C58) & 255),
             (u32(after, 0x582C60) & 255, u32(after, 0x582C64) & 255)]
    cases = source_cases = unchanged_cases = 0
    for character in range(256):
        for progress in range(12):
            stage = next((target for selected, target in rules if character == selected), progress)
            expected_stage = {11: 10, 13: 8, 14: 9}.get(character, progress)
            need(stage == expected_stage, "existing routing policy result")
            for variant in range(4):
                for player in range(2):
                    native_index = stage * 16 + (16 if stage >= 7 else 0)
                    native_index += (variant if stage == 6 else variant & 1) * 8 + player * 4
                    need(native_index <= 0xCC, "all valid logical-stage accesses bounded")
                    x, y = struct.unpack_from("<2H", after, 0x583000 + native_index)
                    if stage < 11:
                        source_index = (stage + (stage >= 7)) * 16
                        source_index += ((variant & (3 if stage == 6 else 1)) << 3) + (4 if player else 0)
                        need((x, y) == struct.unpack_from("<2H", source, 0x743224 + source_index), "actual source coordinate pair")
                        source_cases += 1
                    if character not in (11, 13, 14):
                        need((x, y) == struct.unpack_from("<2H", before, 0x583000 + native_index), "unrouted characters preserve spawn")
                        unchanged_cases += 1
                    cases += 1
    inverse = bytearray(after)
    inverse[0x582F00:0x582F04] = before[0x582F00:0x582F04]
    inverse[0x627900:0x62791C] = before[0x627900:0x62791C]
    need(inverse == before, "whole-ROM inverse outside exact hook/bridge")
    return {"native_instruction_contracts": contracts, "finite_cases": cases,
            "source_backed_coordinate_cases": source_cases, "preserved_default_cases": unchanged_cases,
            "ABI": "r0 andLR saved/restored; r1 stage output; r8 owner restored;8-byte stack balanced; flags overwritten before conditional use",
            "RAM_writes": "only existing paired fighter-coordinate stores and balanced native stack",
            "progress_mutation": False, "campaign_progression_complete": False}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "wsc15", "report")), "save paths forbidden")
    before, after, source = [getattr(args, name).read_bytes() for name in ("before", "after", "wsc15")]
    result = verify(before, after, source)
    incoming(before, 0x627900, 0x62791C)
    negatives = []
    for at, byte, label in ((0x582F00, 0, "wrong bridge branch"),
                            (0x627900, 0, "caller r0 not saved"),
                            (0x627904, 0, "wrong stage-service branch"),
                            (0x627908, 1, "stage result not moved"),
                            (0x62790C, 0, "caller r0 not restored"),
                            (0x627918, 0x14, "wrong variant-state owner"),
                            (0x627914, 0, "wrong continuation"),
                            (0x582F10, 6, "wrong bias threshold"),
                            (0x582F4C, 0xB4, "previous coordinate lost"),
                            (0x12340, after[0x12340] ^ 1, "unrelated mutation")):
        damaged = bytearray(after)
        damaged[at] = byte
        try:
            verify(before, damaged, source, False)
        except ValueError as error:
            negatives.append({"case": label, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("negative mutation accepted: " + label)
    result.update({"schema": 1, "kind": "independent-logical-stage-spawn-verification", "status": "PASS",
                   "input_sha256": sha(before), "output_sha256": sha(after), "negative_cases": negatives,
                   "builder_imported": False, "runtime_or_save_access": False})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-logical-stage-spawn] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
