#!/usr/bin/env python3
"""Independent source, native instruction and inverse check for callback 6."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

PRE = "3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065"
POST = "A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BASE = 0x08000000
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)
X86 = Cs(CS_ARCH_X86, CS_MODE_16)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u32(data, raw):
    return struct.unpack_from("<I", data, raw)[0]


def instruction(data, at, mnemonic, operands, decoder=ARM):
    result = next(decoder.disasm(data[at:at + 15], BASE + at if decoder is ARM else at), None)
    need(result is not None and (result.mnemonic, result.op_str) == (mnemonic, operands),
         f"consumer instruction {at:06X}: {mnemonic} {operands}")
    return {"raw": at, "mnemonic": result.mnemonic, "operands": result.op_str}


def branch_target(data, at):
    value = u32(data, at)
    need(value & 0xFF000000 == 0xEA000000, "unconditional ARM branch without LR change")
    delta = value & 0xFFFFFF
    if delta & 0x800000:
        delta -= 1 << 24
    return at + 8 + delta * 4


def potential_inbound(data):
    intervals = ((0x621C00, 0x621C20), (0x851FC, 0x85208))
    hits = []
    for start, end in intervals:
        for target in range(start, end):
            at = data.find(struct.pack("<I", BASE + target))
            if at >= 0:
                hits.append(("unaligned-inclusive pointer", at, target))
    for at in range(0, len(data) - 3, 4):
        value = u32(data, at)
        if value >> 28 == 15 or value & 0x0E000000 != 0x0A000000:
            continue
        displacement = value & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 1 << 24
        target = at + 8 + displacement * 4
        if any(start <= target < end for start, end in intervals):
            hits.append(("ARM-like branch", at, target))
    return hits


def check(before, after, gba, old, source, identities=True):
    if identities:
        need((sha(before), sha(after)) == (PRE, POST), "fixed layer identities")
        need(tuple(map(sha, (gba, old, source))) == ORIGINALS, "fixed original inputs")
    need(len(before) == len(after) == 0x800000, "ROM length")
    source_rows = []
    for at, mn, op in (
        (0x756F0A, "push", "0xd"), (0x756F14, "mov", "word ptr [si], 0x9e"),
        (0x756F18, "mov", "word ptr [si + 2], 0x68"),
        (0x756F1D, "and", "word ptr [si + 8], 0xbfff"),
        (0x756F22, "or", "word ptr [si + 8], 0x800"),
        (0x756F27, "push", "0"), (0x756F33, "push", "0xd")):
        source_rows.append(instruction(source, at, mn, op, X86))
    instruction(old, 0x39D98B, "mov", "word ptr [si], 0x96", X86)
    instruction(gba, 0x851EC, "mov", "sb, #0x96")
    native_rows = []
    contracts = (
        (0x851CC, "mov", "r8, #0xd"), (0x851EC, "mov", "sb, #0x9e"),
        (0x851F0, "strh", "sb, [r4]"), (0x851F4, "mov", "sb, #0x68"),
        (0x851F8, "strh", "sb, [r4, #2]"),
        (0x621C00, "ldrh", "r8, [r4, #8]"),
        (0x621C04, "bic", "r8, r8, #0x4000"),
        (0x621C08, "strh", "r8, [r4, #8]"),
        (0x621C0C, "orr", "r8, r8, #0x800"),
        (0x621C10, "strh", "r8, [r4, #8]"),
        (0x85208, "stmdb", "sp!, {r4}"), (0x8520C, "stmdb", "sp!, {r4}"),
        (0x85210, "mov", "r8, #0"), (0x85214, "stmdb", "sp!, {r8}"),
        (0x85218, "bl", "#0x8012874"), (0x8521C, "add", "sp, sp, #0xc"),
        (0x85220, "mov", "r8, #0xd"), (0x85224, "stmdb", "sp!, {r8}"),
        (0x85228, "bl", "#0x80881f0"), (0x8522C, "add", "sp, sp, #4"),
        (0x881FC, "mov", "r8, #0x1c"), (0x88208, "ldr", "r4, [sb]"),
        (0x8820C, "ldrsh", "r2, [sb, #0x16]"), (0x88210, "lsl", "r2, r2, #3"),
        (0x88218, "bl", "#0x8000b84"), (0x8821C, "ldr", "r4, [sb, #4]"),
        (0x88220, "mov", "r5, #0x5000000"), (0x88224, "mov", "r2, #8"),
        (0x88228, "bl", "#0x8000b84"), (0x8822C, "mov", "r4, #0x5000000"),
        (0x88238, "bl", "#0x8000b84"),
    )
    for at, mnemonic, operands in contracts:
        native_rows.append(instruction(after, at, mnemonic, operands))
    need(branch_target(after, 0x851FC) == 0x621C00 and
         branch_target(after, 0x621C14) == 0x85208, "flag bridge control flow")
    need(after[0x881F0:0x88244] == gba[0x881F0:0x88244], "unchanged commercial palette consumer")
    need(u32(after, 0x853F4) == 0x085B5400, "correct presentation view retained")
    need(after[0x5B8040:0x5B8054] == before[0x5B8040:0x5B8054], "auxiliary bridge retained")
    # Derive the two ordered writes for all possible halfword live-ins.
    for flags in range(0x10000):
        source_writes = (flags & 0xBFFF, (flags & 0xBFFF) | 0x0800)
        native_writes = (flags & ~0x4000, (flags & ~0x4000) | 0x0800)
        need(source_writes == native_writes, "ordered flag effects")
    # The consumer's 28-byte VS row, positive tile count and all pixels.
    need(u32(after, 0x88244) == 0x084A7C60, "native VS view")
    need((u32(after, 0x88248), u32(after, 0x8824C)) == (0x06004000, 0x02018020),
         "actual native DMA destinations")
    row = 0x4A7C60 + 13 * 28
    pixels, palette = u32(after, row) - BASE, u32(after, row + 4) - BASE
    count = struct.unpack_from("<h", after, row + 22)[0]
    need(count == 74 and (pixels, palette) == (0x4A5D20, 0x4A5D00), "native VS selector13")
    sr = 0x3CEC40 + 13 * 32
    length, segment, bank, offset, pal_segment, pal_bank = struct.unpack_from("<6H", source, sr)
    source_pixels = (bank & 127) * 65536 + segment * 16 - 0x20000
    source_palette = (pal_bank & 127) * 65536 + pal_segment * 16 + offset - 0x20000
    need((source_pixels, source_palette, struct.unpack_from("<H", source, sr + 28)[0]) ==
         (0x36F6A0, 0x3D8950, count), "source VS selector13")
    # Inverse native packed pixels against the four independent source planes.
    for tile in range(count):
        for y in range(8):
            for x in range(8):
                packed = after[pixels + tile * 32 + y * 4 + x // 2]
                pixel = packed >> ((x & 1) * 4) & 15
                planes = source[source_pixels + tile * 32 + y * 4:source_pixels + tile * 32 + y * 4 + 4]
                expected = sum(((plane >> (7 - x)) & 1) << bit for bit, plane in enumerate(planes))
                need(pixel == expected, "all source/native VS pixels")
    for index in range(16):
        color = struct.unpack_from("<H", source, source_palette + index * 2)[0]
        native = struct.unpack_from("<H", after, palette + index * 2)[0]
        components = ((color >> 8) & 15, (color >> 4) & 15, color & 15)
        expected = [0 if v == 0 else 2 * v + 1 for v in components]
        need([native & 31, native >> 5 & 31, native >> 10 & 31] == expected,
             "all source/native VS colors")
    windows = ((0x851EC, 4), (0x851FC, 4), (0x85210, 4), (0x85220, 4), (0x621C00, 24))
    need(before[0x621C00:0x621C20] == b"\xff" * 32 and
         after[0x621C18:0x621C20] == b"\xff" * 8, "bounded new code allocation")
    inverse = bytearray(after)
    for at, size in windows:
        inverse[at:at + size] = before[at:at + size]
    need(inverse == before, "complete ROM inverse outside five Expected Writes")
    return {"source_instruction_contracts": source_rows, "native_instruction_contracts": native_rows,
            "all_flag_inputs": 65536, "ordered_flag_writes": 2, "VS_pixels": 4736,
            "VS_palette_colors": 16, "VS_selector": 13, "source_x": 158,
            "source_y": 104, "source_initial_event": 0, "adapter_clobbers": ["r8"],
            "adapter_preserves": "all other registers, SP, LR and CPSR flags",
            "expected_write_intervals": windows}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "gba", "wsc10", "wsc15", "report")), "save paths forbidden")
    before, after, gba, old, source = [getattr(args, name).read_bytes()
                                       for name in ("before", "after", "gba", "wsc10", "wsc15")]
    result = check(before, after, gba, old, source)
    need(not potential_inbound(before), "external inbound candidate into new code or replaced block")
    need(potential_inbound(struct.pack("<I", BASE + 0x621C00)),
         "inbound detector rejects a pointer to the new helper")
    cases = ((0x851EC, 0x96, "old X"), (0x85210, 2, "old event"),
             (0x85220, 3, "wrong palette selector"), (0x621C04, 2, "wrong cleared flag"),
             (0x621C0C, 3, "wrong set flag"), (0x621C14, 0, "wrong adapter return"),
             (0x4A5D20, after[0x4A5D20] ^ 1, "pixel damage"),
             (0x4A5D00, after[0x4A5D00] ^ 1, "palette damage"),
             (0x621C1C, 0, "reserved gap changed"), (0x123400, after[0x123400] ^ 1, "unrelated byte"))
    negatives = []
    for at, byte, name in cases:
        damaged = bytearray(after)
        damaged[at] = byte
        try:
            check(before, damaged, gba, old, source, False)
        except ValueError as error:
            negatives.append({"case": name, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("negative case accepted: " + name)
    result.update({"schema": 1, "kind": "independent-opening-callback6-parity-verification",
                   "status": "PASS", "input_sha256": sha(before), "output_sha256": sha(after),
                   "negative_cases": negatives, "builder_imported": False,
                   "allocation_and_replaced_block_inbound_candidates": [],
                   "inbound_detector_negative_case": "new helper pointer rejected",
                   "runtime_or_save_access": False})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-opening-callback6-parity] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
