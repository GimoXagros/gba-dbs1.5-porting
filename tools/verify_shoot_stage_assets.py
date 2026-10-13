#!/usr/bin/env python3
"""Independent source-loader/native-consumer and inverse Shoot asset checks.

No generator import, CPU execution, image matching, or save access is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

INPUT = "6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
MAPS, DESCRIPTORS = 0x5EF000, 0x5F1F40
WRITES = ((0x5A8000, 222), (0x5A8100, 16384), (MAPS, 12096),
          (DESCRIPTORS, 96), (0x5802B8, 24), (0x5802D0, 24))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def instructions(data: bytes, at: int, texts: list[str], arm: bool = False) -> None:
    md = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    address = at + 0x08000000 if arm else at
    rows = list(md.disasm(data[at:at + 200], address))[:len(texts)]
    need([f"{i.mnemonic} {i.op_str}".strip() for i in rows] == texts, f"consumer instructions {at:X}")


def verify(candidate: bytes, source: bytes, gba: bytes) -> dict:
    # The source initializer has an explicitly nonzero segment offset. The
    # old 490000 assumption is not an alternate interpretation of this code.
    instructions(source, 0x77DD2C, ["mov ax, 0xc9", "out 0xc3, al"])
    instructions(source, 0x77DD44, ["mov ax, 0x383f", "mov ds, ax"])
    instructions(source, 0x77DD51, ["mov si, 0", "mov cx, 0x70", "xor bx, bx",
                                  "inc bx", "inc bx", "add si, bx", "add di, bx", "dec cx",
                                  "rep movsw word ptr es:[di], word ptr [si]"])
    instructions(source, 0x77DD62, ["xor di, di", "mov ax, 0x800", "mov es, ax",
                                  "mov si, 0xe0", "mov cx, 0x2000", "rep movsw word ptr es:[di], word ptr [si]"])
    for at, index, slot in ((0x77DD84, 0x27, 0x1CE), (0x77DDCB, 0x28, 0x20E)):
        instructions(source, at, [f"push 0x{index:x}", "push 0x2497", "push 0x460", "push 0x1000", f"push 0x{slot:x}", "lcall 0x4fff, 0x2f9c"])
    instructions(source, 0x753050, ["mov cx, word ptr es:[si + 6]", "mov ax, word ptr es:[si + 0x16]",
                                   "mov dx, word ptr es:[si + 0xc]", "mul dx", "add ax, word ptr es:[si + 0x14]",
                                   "shl ax, 2", "add ax, word ptr es:[si + 0x28]", "mov dx, ax"])
    instructions(source, 0x753076, ["mov al, byte ptr es:[si]", "out 0xc3, al", "mov dx, word ptr es:[si + 2]",
                                   "mov es, cx", "mov si, dx"])
    # Resource decoder, initial zero-coordinate draw and nonzero-coordinate
    # scrolling use the original commercial engine. Scrolling has 8-byte
    # descriptors; the initial draw's 4-byte shift is used only at (0,0).
    instructions(candidate, 0x13BF8, ["ldr sb, [sp, #8]", "ldr sl, [sp]", "mov r8, #0x18",
                                      "mul sl, r8, sl", "add sb, sb, sl", "ldr r8, [sp, #0x10]",
                                      "ldrb sl, [sb, #4]", "strb sl, [r8, #0x44]", "ldr sl, [sb, #8]",
                                      "str sl, [r8, #0x24]", "ldrh sl, [sb]", "strh sl, [r8, #0xc]",
                                      "ldrh sl, [sb, #2]", "strh sl, [r8, #0xe]"], True)
    instructions(candidate, 0x1483C, ["ldrsh r3, [r5, #0xc]", "mul r0, r3, r0",
                                      "ldrsh r8, [r5, #0x14]", "add r0, r0, r8", "add r0, r0, r2",
                                      "add r4, r4, r0, lsl #3"], True)
    for begin, end in ((0x13BF8, 0x13CD0), (0x13DD4, 0x14550), (0x146E0, 0x14E00)):
        need(candidate[begin:end] == gba[begin:end], f"commercial map consumer changed {begin:X}")
    instructions(candidate, 0x582A5C, ["mov r8, #0x1d", "stmdb sp!, {r8}", "bl #0x8013bf8"], True)
    instructions(candidate, 0x582AD8, ["mov r8, #0x1e", "stmdb sp!, {r8}", "bl #0x8013bf8"], True)
    for at in (0x582B50, 0x582B6C):
        need(struct.unpack_from("<I", candidate, at)[0] == 0x08580000, "actual clone resource table")
    # Independently invert every hardware color; nonzero 5-bit channels must
    # be odd, and FFFF source transparent slots have effective value FFF.
    for i in range(1, 112):
        original = struct.unpack_from("<H", source, 0x4983F0 + 2 * i)[0]
        native = struct.unpack_from("<H", candidate, 0x5A8000 + 2 * (i - 1))[0]
        need(not native & 0x8000, "native palette high bit")
        decoded = 0
        for source_shift, native_shift in ((8, 0), (4, 5), (0, 10)):
            channel = native >> native_shift & 31
            need(channel == 0 or channel & 1, "native nonzero palette channel is not odd")
            decoded |= (channel // 2) << source_shift
        need(decoded == original & 0xFFF, f"palette inverse {i}")
    # Reconstruct all four source bitplanes from packed native pixel nibbles.
    pixels = 0
    for tile in range(512):
        packed = candidate[0x5A8100 + tile * 32:0x5A8120 + tile * 32]
        planar = bytearray(32)
        for y in range(8):
            for x in range(8):
                value = packed[y * 4 + x // 2] >> (4 * (x % 2)) & 15
                for plane in range(4):
                    planar[y * 4 + plane] |= (value >> plane & 1) << (7 - x)
                pixels += 1
        need(planar == source[0x4984D0 + tile * 32:0x4984F0 + tile * 32], f"tile pixel inverse {tile}")
    palettes, blank_bank0 = set(), 0
    for layer in range(2):
        source_record = 0x3B5178 + layer * 24
        record = 0x5802B8 + layer * 24
        need(struct.unpack_from("<HH", source, source_record) == (2, 3), "source two-by-three geometry")
        need(struct.unpack_from("<HH", candidate, record) == (2, 3), "native two-by-three geometry")
        table = struct.unpack_from("<I", candidate, record + 8)[0] - 0x08000000
        need(table == DESCRIPTORS + layer * 48, "native descriptor table")
        need(candidate[record + 4:record + 8] == bytes.fromhex("F6000000"), "native resource consumer mode")
        need(candidate[record + 12:record + 24] == bytes(12), "no invented animation/auxiliary resource")
        for row in range(3):
            for column in range(2):
                index = row * 2 + column
                native_descriptor = table + index * 8
                marker, pointer = struct.unpack_from("<II", candidate, native_descriptor)
                need(marker == 0x101 and pointer == 0x08000000 + MAPS + (layer * 6 + index) * 0x3F0,
                     "native map selector order")
                bank, mode, source_offset = struct.unpack_from("<BBH", source, 0x3B4C88 + (layer * 6 + index) * 4)
                need((bank, mode) == (0xC9, 1), "source map bank/mode")
                source_pointer = 0x490000 + ((0x383F0 + source_offset) & 0xFFFF)
                need(source_pointer == 0x49C4D0 + (layer * 6 + index) * 0x3F0, "source map selector order")
                for element in range(504):
                    original = struct.unpack_from("<H", source, source_pointer + element * 2)[0]
                    native = struct.unpack_from("<H", candidate, pointer - 0x08000000 + element * 2)[0]
                    restored = ((native & 0x1FF) | ((native & 0x200) << 4) |
                                ((native & 0xC00) << 4) | ((native & 0xF000) >> 3))
                    need(restored == original, "map inverse tile/bank/palette/flip")
                    palettes.add(original >> 9 & 15)
                    if not original & 0x2000:
                        need(original & 511 == 0, "unproved common-bank tile")
                        blank_bank0 += 1
    return {"source_maps": 12, "map_cells": 6048, "pixels_inverted": pixels, "palette_colors": 111,
            "palettes_used": sorted(palettes), "common_bank_zero_tile_cells": blank_bank0,
            "source_geometry": [2, 3], "source_extent_pixels": [448, 432]}


def main() -> int:
    p = argparse.ArgumentParser()
    for key in ("candidate", "predecessor", "wsc15", "gba"):
        p.add_argument(key, type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path, required=True)
    args = p.parse_args()
    candidate, predecessor, source, gba = [getattr(args, key).read_bytes() for key in ("candidate", "predecessor", "wsc15", "gba")]
    need(sha(predecessor) == INPUT and sha(source) == SOURCE and sha(gba) == GBA, "unknown inputs")
    need(len(candidate) == len(predecessor), "ROM length changed")
    allowed = {at + i for at, length in WRITES for i in range(length)}
    changed = {i for i, (a, b) in enumerate(zip(candidate, predecessor, strict=True)) if a != b}
    need(changed <= allowed, "write outside six Expected Write intervals")
    proof = verify(candidate, source, gba)
    negatives = []
    for at, bit, label in (
        (0x5A8000 + 2, 1, "palette channel"), (0x5A8100 + 42, 8, "tile pixel"),
        (MAPS + 8, 0x20, "tile index"), (MAPS + 8 + 1, 0x20, "palette index"),
        (MAPS + 8 + 1, 4, "horizontal flip"), (DESCRIPTORS + 52, 4, "second-layer map pointer"),
        (0x5802B8 + 2, 1, "source height"), (0x5802D0 + 8, 8, "resource selector"),
        (0x14850, 1, "commercial scrolling stride"),
    ):
        damaged = bytearray(candidate)
        damaged[at] ^= bit
        try:
            verify(damaged, source, gba)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"semantic mutation survived: {label}")
    report = {"schema": 1, "kind": "independent-shoot-stage-asset-consumer-proof", "candidate_sha256": sha(candidate),
              "predecessor_sha256": INPUT, "source_sha256": SOURCE, "native_sha256": GBA,
              "proof": proof, "actual_changed_bytes": len(changed), "semantic_negatives": negatives,
              "no_CPU_execution": True, "no_save_access": True,
              "scope": "static loader, resource, inverse color/tile/map proof; common-bank tile zero lifetime and rendered scene QA remain runtime work"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-stage-assets-verifier] PASS {sha(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
