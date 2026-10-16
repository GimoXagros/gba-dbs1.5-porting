#!/usr/bin/env python3
"""Independent ARM literal/DMA consumer and complete inverse verification."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BASE = 0x08000000
PRE = "A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949"
POST = "C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017"
ORIGINAL = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
DIS = Cs(CS_ARCH_ARM, CS_MODE_ARM)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def decode(data, at, mnemonic, operands):
    actual = next(DIS.disasm(data[at:at + 4], BASE + at), None)
    need(actual is not None and (actual.mnemonic, actual.op_str) == (mnemonic, operands),
         f"native instruction {at:06X} expected {mnemonic} {operands}")
    return {"raw": at, "mnemonic": actual.mnemonic, "operands": actual.op_str}


def literal(data, at):
    value = word(data, at)
    need(value & 0xFFFF0000 == 0xE59F0000, "unconditional positive PC-relative word load")
    address = at + 8 + (value & 0xFFF)
    need(0 <= address < len(data) - 4, "literal pool in ROM")
    return (value >> 12 & 15), address, word(data, address)


def check(before, after, gba, identities=True):
    if identities:
        need((sha(before), sha(after), sha(gba)) == (PRE, POST, ORIGINAL), "exact artifact identities")
    need(len(before) == len(after) == 0x800000, "same expanded ROM size")
    rows = []
    # The existing caller enters the exact hook being repaired.
    rows.append(decode(after, 0x8329C, "b", "#0x84a5c40"))
    for at, mnemonic, operands in (
        (0x4A5C40, "stmdb", "sp!, {lr}"),
        (0x4A5C44, "ldr", "r8, [pc, #0x34]"),
        (0x4A5C48, "ldr", "r5, [pc, #0x34]"),
        (0x4A5C4C, "ldr", "r4, [r8, r1, lsl #3]"),
        (0x4A5C50, "mov", "r2, #8"), (0x4A5C54, "bl", "#0x8000b84"),
        (0x4A5C58, "ldr", "r8, [pc, #0x28]"),
        (0x4A5C5C, "ldr", "r5, [pc, #0x28]"),
        (0x4A5C60, "ldr", "r4, [r8, r1, lsl #3]"),
        (0x4A5C64, "mov", "r2, #0x600"), (0x4A5C68, "bl", "#0x8000b84"),
        (0x4A5C6C, "ldr", "r4, [pc, #0x1c]"),
        (0x4A5C70, "add", "r1, r1, #1"),
        (0x4A5C74, "strh", "r1, [r4, #0x1e]"),
        (0x4A5C78, "ldm", "sp!, {lr}"), (0x4A5C7C, "bx", "lr"),
        (0xB84, "mov", "r8, #0x4000000"), (0xB88, "str", "r4, [r8, #0xd4]"),
        (0xB8C, "str", "r5, [r8, #0xd8]"), (0xB90, "strh", "r2, [r8, #0xdc]"),
        (0xB94, "mov", "ip, #0x8400"), (0xB98, "strh", "ip, [r8, #0xde]"),
        (0xB9C, "add", "r4, r4, r2, lsl #2"),
        (0xBA0, "add", "r5, r5, r2, lsl #2"), (0xBA4, "bx", "lr")):
        rows.append(decode(after, at, mnemonic, operands))
    need(before[0xB84:0xBA8] == after[0xB84:0xBA8] == gba[0xB84:0xBA8], "actual retail DMA ABI")
    need(literal(before, 0x4A5C44) == (8, 0x4A5C84, 0x05000020) and
         literal(before, 0x4A5C48) == (5, 0x4A5C88, 0x084A5BC4), "two original invalid palette loads")
    r8, pool8, table = literal(after, 0x4A5C44)
    r5, pool5, destination = literal(after, 0x4A5C48)
    need((r8, pool8, table, r5, pool5, destination) ==
         (8, 0x4A5C80, 0x084A5BC0, 5, 0x4A5C84, 0x05000020), "repaired palette operands")
    _r8, tile_pool, tile_table = literal(after, 0x4A5C58)
    _r5, tile_dest_pool, tile_destination = literal(after, 0x4A5C5C)
    need((tile_pool, tile_table, tile_dest_pool, tile_destination) ==
         (0x4A5C88, table + 4, 0x4A5C8C, 0x06005780), "tile operands unchanged")
    need(literal(after, 0x4A5C6C) == (4, 0x4A5C90, 0x03004710), "selection-state consumer")
    need(after[table - BASE:table - BASE + 96] == gba[0x832F0:0x83350], "all12retailportraitpairs")
    traces = []
    # Both BLs call an audited nine-instruction routine with no r1 write.
    # Thus the same selector reaches both indexed loads and the final +1.
    for character in range(15):
        palette = word(after, table - BASE + character * 8)
        pixels = word(after, tile_table - BASE + character * 8)
        need(BASE <= palette <= BASE + len(after) - 32, "palette source in ROM for every selector")
        need(BASE <= pixels <= BASE + len(after) - 0x1800, "tile source in ROM for every selector")
        traces.append({"id": character,
                       "palette_DMA": [palette, destination, 8, 0x8400],
                       "tile_DMA": [pixels, tile_destination, 0x600, 0x8400],
                       "selection_state_write": [0x0300472E, character + 1]})
    # Restoring precisely the two instruction words must recover the input.
    inverse = bytearray(after)
    for at in (0x4A5C44, 0x4A5C48):
        inverse[at:at + 4] = before[at:at + 4]
    need(inverse == before, "full inverse outside the two LDR words")
    changed = [at for at, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    need(changed == [0x4A5C44, 0x4A5C48], "only two encoded immediate bytes changed")
    return {"native_instruction_contracts": rows, "selector_traces": traces,
            "changed_bytes": changed, "new_allocation": False,
            "r1_survives_both_DMA_calls": True, "SP_LR_balance_preserved": True}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "gba", "report")), "save paths forbidden")
    before, after, gba = (getattr(args, name).read_bytes() for name in ("before", "after", "gba"))
    result = check(before, after, gba)
    tests = ((0x4A5C44, 0x38, "first original offset"), (0x4A5C48, 0x38, "second original offset"),
             (0x4A5C50, 7, "palette count truncated"), (0x4A5C64, 7, "tile count changed"),
             (0xB9C, after[0xB9C] ^ 1, "DMA clobber contract changed"),
             (0x4A5C84, after[0x4A5C84] ^ 4, "wrong palette hardware address"),
             (0x4A5C20 + 3, 5, "selector12 points outsideROM"),
             (0x12340, after[0x12340] ^ 1, "unrelated code changed"))
    rejected = []
    for at, replacement, label in tests:
        corrupted = bytearray(after)
        corrupted[at] = replacement
        try:
            check(before, corrupted, gba, False)
        except ValueError as error:
            rejected.append({"case": label, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("negative case accepted: " + label)
    result.update({"schema": 1, "kind": "independent-selection-palette-routing-verification",
                   "status": "PASS", "input_sha256": sha(before), "output_sha256": sha(after),
                   "negative_cases": rejected, "builder_imported": False,
                   "runtime_or_save_access": False})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-selection-palette-routing] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
