#!/usr/bin/env python3
"""Independently verify relocated player spawn reads against source consumers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

BASE = 0x08000000
PRE = "C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)
X86 = Cs(CS_ARCH_X86, CS_MODE_16)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def instruction(data, at, mnemonic, operands, decoder=ARM):
    actual = next(decoder.disasm(data[at:at + 15], BASE + at if decoder is ARM else at), None)
    need(actual is not None and (actual.mnemonic, actual.op_str) == (mnemonic, operands),
         f"instruction {at:06X}: {mnemonic} {operands}")
    return {"raw": at, "mnemonic": actual.mnemonic, "operands": actual.op_str}


def literal(data, at):
    value = word(data, at)
    need(value & 0xFFFFF000 == 0xE59F8000, "unconditional r8 PC-relative load")
    pool = at + 8 + (value & 0xFFF)
    need(0 <= pool <= len(data) - 4, "literal address in ROM")
    return pool, word(data, pool)


def incoming(data, first, end):
    hits = []
    for target in range(first, end):
        offset = data.find(struct.pack("<I", BASE + target))
        if offset >= 0:
            hits.append(("unaligned-inclusive pointer", offset, target))
    for offset in range(0, len(data) - 3, 4):
        value = word(data, offset)
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 1 << 24
            target = offset + 8 + delta * 4
            if first <= target < end:
                hits.append(("ARM-like branch", offset, target))
        # Immediate LDR/LDRB with Rn=PC; ignore condition1111 and register offsets.
        if value >> 28 != 15 and value & 0x0E1F0000 == 0x041F0000:
            delta = value & 0xFFF
            target = offset + 8 + (delta if value & 0x00800000 else -delta)
            if first <= target < end:
                hits.append(("ARM-like literal load", offset, target))
    return hits


def native_spawn(after, stage, variant, player):
    """Evaluate the independently audited straight-line ARM data flow."""
    _pool, owner = literal(after, 0x582F00)
    memory = {owner + 14: stage, owner + 20: variant & 0xFFFF}
    r1 = memory[0x03002310 + 14]
    sb = r1
    r1 <<= 4
    if sb >= 7:
        r1 += 16
    r0 = memory[0x03002310 + 20] & 3
    if sb != 6:
        r0 &= 1
    r0 <<= 3
    r1 += r0
    if player != 0:
        r1 += 4
    _pool, table = literal(after, 0x582F3C)
    x = struct.unpack_from("<H", after, table - BASE + r1)[0]
    y = struct.unpack_from("<H", after, table - BASE + r1 + 2)[0]
    return r1, {0x34: x, 0x38: x, 0x36: y, 0x3A: y}


def source_spawn(source, stage, variant, player):
    # Source's CS table offset2924 with code-bank base740900.
    bx = stage * 16
    if stage >= 7:
        bx += 16
    ax = variant & 3
    if stage != 6:
        ax &= 1
    bx += ax * 8
    if player:
        bx += 4
    x, y = struct.unpack_from("<2H", source, 0x740900 + 0x2924 + bx)
    return bx, {0x26: x, 0x2A: x, 0x28: y, 0x2C: y}


def check(before, after, gba, old, source, identities=True):
    if identities:
        need(sha(before) == PRE and tuple(map(sha, (gba, old, source))) == ORIGINALS,
             "fixed selection-repair predecessor and originals")
    need(len(before) == len(after) == 0x800000, "same ROM length")
    need(literal(before, 0x582F00) == (0x5830D0, 0xFFFFFFFF), "actual erroneous relocated source")
    need(literal(gba, 0x353130) == (0x353300, 0x03002310), "original battle control owner")
    need(literal(after, 0x582F00) == (0x582F68, 0x03002310), "repaired battle control owner")
    need(literal(after, 0x582F3C) == (0x582F64, 0x08583000), "expanded spawn table")
    instruction(after, 0x353130, "b", "#0x8582f00")
    source_contracts = []
    for at, mn, op in (
        (0x743654, "mov", "ax, 0x1000"), (0x743657, "mov", "es, ax"),
        (0x743659, "xor", "bx, bx"),
        (0x74365B, "mov", "bl, byte ptr es:[0x5c]"), (0x743660, "shl", "bx, 4"),
        (0x743663, "cmp", "byte ptr es:[0x5c], 7"), (0x743669, "jb", "0x74366e"),
        (0x74366B, "add", "bx, 0x10"), (0x74366E, "mov", "ax, word ptr es:[0x62]"),
        (0x743672, "and", "ax, 3"), (0x743675, "cmp", "byte ptr es:[0x5c], 6"),
        (0x74367B, "je", "0x743680"), (0x74367D, "and", "ax, 1"),
        (0x743680, "shl", "ax, 3"), (0x743683, "add", "bx, ax"),
        (0x743685, "cmp", "word ptr [bp + 0xa], 0"), (0x743689, "je", "0x74368e"),
        (0x74368B, "add", "bx, 4"), (0x74368E, "mov", "ax, word ptr cs:[bx + 0x2924]"),
        (0x743693, "mov", "word ptr [si + 0x26], ax"),
        (0x743696, "mov", "word ptr [si + 0x2a], ax"),
        (0x743699, "mov", "ax, word ptr cs:[bx + 0x2926]"),
        (0x74369E, "mov", "word ptr [si + 0x28], ax"),
        (0x7436A1, "mov", "word ptr [si + 0x2c], ax")):
        source_contracts.append(instruction(source, at, mn, op, X86))
    native_contracts = []
    operations = (
        ("ldr", "r8, [pc, #0x60]"), ("ldrb", "r1, [r8, #0xe]"),
        ("mov", "sb, r1"), ("lsl", "r1, r1, #4"), ("cmp", "sb, #7"),
        ("addhs", "r1, r1, #0x10"), ("ldrsh", "r0, [r8, #0x14]"),
        ("and", "r0, r0, #3"), ("cmp", "sb, #6"), ("andne", "r0, r0, #1"),
        ("lsl", "r0, r0, #3"), ("add", "r1, r1, r0"),
        ("ldr", "r8, [sp, #0x24]"), ("cmp", "r8, #0"),
        ("addne", "r1, r1, #4"), ("ldr", "r8, [pc, #0x20]"),
        ("add", "sb, r8, #0"), ("ldrh", "r0, [r1, sb]"),
        ("strh", "r0, [r4, #0x34]"), ("strh", "r0, [r4, #0x38]"),
        ("add", "sb, r8, #2"), ("ldrh", "r0, [r1, sb]"),
        ("strh", "r0, [r4, #0x36]"), ("strh", "r0, [r4, #0x3a]"),
        ("b", "#0x8353190"))
    for index, (mnemonic, operands) in enumerate(operations):
        native_contracts.append(instruction(after, 0x582F00 + index * 4, mnemonic, operands))
    need([row["raw"] for row in native_contracts if "pc" in row["operands"]] ==
         [0x582F00, 0x582F3C], "all relocated PC-relative operands audited")
    # All source-backed stage records, plus unchanged legacy placeholder11.
    need(after[0x583000:0x5830C0] == source[0x743224:0x7432E4], "all11source-backedstagepositions")
    need(after[0x583000:0x583090] == gba[0x35326C:0x3532FC] == old[0x392E32:0x392EC2],
         "commercial nine-record table lineage")
    need(after[0x5830C0:0x5830D0] == before[0x5830C0:0x5830D0] == gba[0x3532EC:0x3532FC],
         "stage11 legacy placeholder unchanged and not source-certified")
    need(after[0x353190:0x3531A4] == gba[0x353190:0x3531A4], "retail zero-motion continuation")
    cases = []
    for stage in range(11):
        for variant in range(4):
            for player in range(2):
                source_offset, source_writes = source_spawn(source, stage, variant, player)
                native_offset, native_writes = native_spawn(after, stage, variant, player)
                need(native_offset == source_offset < 0xC0, "same bounded spawn table offset")
                need([source_writes[v] for v in (0x26, 0x2A, 0x28, 0x2C)] ==
                     [native_writes[v] for v in (0x34, 0x38, 0x36, 0x3A)], "same current/previous position pair")
                cases.append({"stage": stage, "raw_variant_low2": variant, "player": player,
                              "table_offset": source_offset, "x": native_writes[0x34],
                              "y": native_writes[0x36]})
    # Nonzero player IDs collapse to the same source branch; upper variant bits
    # are removed before indexing, including signed load boundaries.
    for variant in (0x7FFF, 0x8000, 0xFFFE, 0xFFFF):
        need(native_spawn(after, 6, variant, 0xFFFF) == native_spawn(after, 6, variant & 3, 1),
             "variant high bits and nonzero player equivalence")
    need(before[0x582F68:0x582F6C] == b"\xff" * 4, "Expected Write blank literal")
    inverse = bytearray(after)
    for raw in (0x582F00, 0x582F68):
        inverse[raw:raw + 4] = before[raw:raw + 4]
    need(inverse == before, "whole ROM inverse outside two words")
    need(after[0x582F6C:0x583000] == before[0x582F6C:0x583000], "rest of hook/table gap preserved")
    return {"source_instruction_contracts": source_contracts, "native_instruction_contracts": native_contracts,
            "finite_source_cases": cases, "finite_case_count": len(cases),
            "source_backed_stages": list(range(11)), "stage11": "unchanged dedicated-mode placeholder; no source spawn equivalence claimed",
            "new_literal": {"raw": 0x582F68, "value": 0x03002310},
            "current_previous_native_offsets": [0x34, 0x38, 0x36, 0x3A],
            "new_callbacks": False, "new_RAM": False}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "gba", "wsc10", "wsc15", "report")), "save paths forbidden")
    before, after, gba, old, source = [getattr(args, name).read_bytes()
                                      for name in ("before", "after", "gba", "wsc10", "wsc15")]
    report = check(before, after, gba, old, source)
    need(not incoming(before, 0x582F68, 0x582F6C), "new literal has no prior pointer/branch/literal candidate")
    need(incoming(struct.pack("<I", BASE + 0x582F68), 0x582F68, 0x582F6C), "inbound detector negative case")
    need(incoming(struct.pack("<I", 0xE59F8000), 8, 12) == [("ARM-like literal load", 0, 8)],
         "literal inbound detector negative case")
    cases = ((0x582F00, 0xC8, "old load offset"), (0x582F68, 0x11, "wrong control base"),
             (0x582F17, 0x02, "stage bias condition EQ instead of HS"),
             (0x582F24, 3, "stage non6 variant mask changed"),
             (0x582F38, 8, "wrong player stride"), (0x582F4C, 0xB4, "previous X store aliases current"),
             (0x583010, after[0x583010] ^ 1, "stage1 position data damaged"),
             (0x582F60, after[0x582F60] ^ 1, "wrong continuation"),
             (0x12340, after[0x12340] ^ 1, "unrelated change"))
    negatives = []
    for at, byte, name in cases:
        corrupt = bytearray(after)
        corrupt[at] = byte
        try:
            check(before, corrupt, gba, old, source, False)
        except (ValueError, KeyError) as error:
            negatives.append({"case": name, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("negative accepted: " + name)
    report.update({"schema": 1, "kind": "independent-player-spawn-literal-verification",
                   "status": "PASS", "input_sha256": sha(before), "output_sha256": sha(after),
                   "negative_cases": negatives, "inbound_candidates": [],
                   "builder_imported": False, "runtime_or_save_access": False})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[verify-player-spawn-literal] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
