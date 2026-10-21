#!/usr/bin/env python3
"""Independent source/cell/consumer inverse for added-stage collision repair.

No generator imports, CPU emulation, save access, or runtime launches. Semantic
negative checks call the verifier without depending on final-ROM hash equality.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

BASE = 0x08000000
INPUT = "1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995"
OUTPUT = "7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD"
ORIGINALS = (
    "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
)
GRIDS = (
    ("train", (33,), (21,), 2, 2, 0x380000, 0x622000, 8),
    ("iraira", (37, 38), (25, 26), 2, 2, 0x381F80, 0x624000, 10),
    ("waterfall", (35, 36), (27, 28), 1, 3, 0x38E240, 0x626000, 9),
)
RETAIL = ((0, 0x26CB60), (4, 0x270000), (10, 0x271F80), (12, 0x273F00),
          (14, 0x275E80), (16, 0x1F9BA0), (18, 0x1FCAE0))
TABLE, BRIDGE, HOOK = 0x627800, 0x6278C0, 0xC8438
ALLOCATIONS = ((0x622000, 0x623F80), (0x624000, 0x625F80), (0x626000, 0x6277A0),
               (TABLE, TABLE + 192), (BRIDGE, BRIDGE + 12))
CONSUMERS = ((0x13BF8, 0x13C64), (0xC8258, HOOK), (HOOK + 4, 0xC8E0C),
             (0x373928, 0x373BA4), (0x3549E0, 0x354A3C))


def need(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def u16(data: bytes, at: int) -> int:
    return struct.unpack_from("<H", data, at)[0]


def u32(data: bytes, at: int) -> int:
    return struct.unpack_from("<I", data, at)[0]


def branch(data: bytes, at: int, link: bool = False) -> int:
    word = u32(data, at)
    need(word >> 24 == (0xEB if link else 0xEA), f"unconditional ARM branch kind {at:X}")
    displacement = word & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    return BASE + at + 8 + displacement * 4


def insn(data: bytes, at: int) -> tuple[str, str]:
    items = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[at:at + 4], BASE + at))
    need(len(items) == 1 and items[0].size == 4, f"complete ARM instruction {at:X}")
    return items[0].mnemonic, items[0].op_str


def source_insn(data: bytes, ip: int) -> tuple[str, str]:
    raw = 0x76F760 + ip
    items = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(data[raw:raw + 8], ip))
    need(bool(items), f"source collision instruction {ip:X}")
    return items[0].mnemonic, items[0].op_str


def contract_proof(gba: bytes, old: bytes, source: bytes) -> dict:
    pairs = []
    for index, raw in RETAIL:
        descriptor = 0x7F8E0 + index * 24
        width, height = struct.unpack_from("<HH", gba, descriptor)
        target = u32(gba, descriptor + 12) - BASE
        count = width * height * 28 * 18
        need(gba[target:target + count * 4] == old[raw:raw + count * 4], "commercial complete cell inverse")
        pairs.append({"native_record": index, "source_raw": raw, "native_raw": target,
                      "cells": count, "sha256": sha(old[raw:raw + count * 4])})
    native = {
        0x13C38: ("ldr", "sl, [sb, #0xc]"), 0x13C3C: ("str", "sl, [r8, #0x28]"),
        0x13C20: ("ldrh", "sl, [sb]"), 0x13C28: ("ldrh", "sl, [sb, #2]"),
        0xC87F0: ("mov", "r1, #0x12"), 0xC8808: ("mov", "r1, #0x1c"),
        0xC881C: ("ldr", "r4, [r4, #0x28]"),
        0xC8968: ("add", "r4, r4, r0, lsl #2"),
        0xC8988: ("ldrsh", "r8, [r4, #2]"), 0xC8990: ("ldrsh", "r8, [r4], #4"),
        0xC89E0: ("ands", "r3, r3, #3"), 0xC89F0: ("cmp", "r3, #2"),
        0xC8BC4: ("add", "r4, r4, r0, lsl #2"), 0xC8BE4: ("ldrsh", "r8, [r4, #2]"),
        0xC8BF4: ("add", "r4, r4, r1"), 0xC8C3C: ("tst", "r3, #0x8000"),
        0xC8C44: ("ands", "r3, r3, #3"), 0xC8C4C: ("cmp", "r3, #2"),
        0xC8D68: ("tst", "r3, #0x6000"),
        0xC82D0: ("ldr", "r4, [r4, #0x28]"),
        0xC835C: ("ldrh", "r8, [r4, #2]"), 0xC8364: ("ldrh", "r8, [r4], #4"),
        0xC8374: ("tst", "r3, #0x4000"), 0xC837C: ("tst", "r3, #0x2000"),
        0xC83B0: ("add", "r8, r8, #0xa0"), 0xC83C0: ("sub", "r8, r8, #0xa0"),
        0xC83D0: ("strh", "r0, [r5, #0x5c]"), 0xC83D4: ("strh", "r3, [r5, #0x5a]"),
        0xC842C: ("ands", "r2, r3, #0x3c"), 0xC8434: ("lsr", "r2, r2, #2"),
        0xC8440: ("add", "r4, r4, r0, lsl #4"), 0xC8448: ("ldrb", "r2, [r4, r2]"),
        0xC8458: ("bic", "r0, r0, #0x3c"), 0xC8460: ("strh", "r0, [r5, #0x5a]"),
        0xC8470: ("ldr", "sb, [r8, r1, lsl #2]"), 0xC8474: ("bx", "sb"),
        0xC8570: ("ldr", "sb, [r8, r1, lsl #2]"), 0xC8574: ("bx", "sb"),
        0xC8638: ("ldrh", "r0, [r5, #0x5a]"), 0xC863C: ("ldrh", "r3, [r5, #0x5c]"),
        0x373A5C: ("strh", "r0, [r4, #0x56]"), 0x373AA4: ("strh", "r3, [r4, #0x58]"),
        0x373B30: ("strh", "r0, [r4, #0x5a]"), 0x373B34: ("strh", "r3, [r4, #0x5c]"),
    }
    for at, expected in native.items():
        need(insn(gba, at) == expected, f"native field/flag contract {at:X}")
    source_expected = {
        0x4BB: ("mov", "ax, word ptr es:[si + 0xe]"), 0x4BF: ("mov", "bx, 0x12"),
        0x4CA: ("mov", "ax, word ptr es:[si + 0xc]"), 0x4CE: ("mov", "bx, 0x1c"),
        0x4D9: ("mov", "dx, word ptr es:[si + 0xa]"), 0x4DD: ("mov", "si, word ptr es:[si + 0x2a]"),
        0x598: ("mov", "ax, word ptr [bp - 0xe]"), 0x59E: ("mul", "word ptr [bp - 4]"),
        0x5A1: ("add", "ax, word ptr [bp - 2]"),
        0x5BC: ("or", "ax, word ptr es:[si + 2]"), 0x5C0: ("or", "dx, word ptr es:[si]"),
        0x5E8: ("and", "dx, 3"), 0x5F4: ("cmp", "dx, 2"),
        0x72C: ("or", "ax, word ptr es:[si + 2]"), 0x730: ("or", "dx, word ptr es:[si]"),
        0x757: ("test", "dx, 0x8000"), 0x75D: ("and", "dx, 3"), 0x763: ("cmp", "dx, 2"),
        0x818: ("test", "dx, 0x6000"),
        0x1FA: ("or", "ax, word ptr es:[si + 2]"), 0x1FE: ("or", "dx, word ptr es:[si]"),
        0x206: ("test", "dx, 0x4000"), 0x20C: ("test", "dx, 0x2000"),
        0x22B: ("add", "word ptr [di + 0x26], 0xa0"), 0x233: ("sub", "word ptr [di + 0x26], 0xa0"),
        0x23C: ("mov", "word ptr [di + 0x4c], ax"), 0x23F: ("mov", "word ptr [di + 0x4a], dx"),
        0x26F: ("and", "cx, 0x3c"), 0x275: ("shr", "cx, 2"),
        0x278: ("mov", "si, 0"), 0x27E: ("shl", "ax, 4"),
        0x289: ("mov", "cl, byte ptr cs:[si]"), 0x293: ("and", "ax, 0xffc3"),
        0x298: ("mov", "word ptr [di + 0x4a], ax"),
        0x29F: ("jmp", "word ptr cs:[bx + 0xe0]"), 0x2D9: ("jmp", "word ptr cs:[bx + 0xc0]"),
    }
    for at, expected in source_expected.items():
        need(source_insn(source, at) == expected, f"source field/flag contract {at:X}")
    need(source[0x76FD04:0x76FD0C] == bytes.fromhex("03F003F003F003F0"), "source four-byte index scale")
    need(branch(gba, 0x373A08, True) == 0x080C86B4 and branch(gba, 0xC8778, True) == 0x080C87C0,
         "actual movement collision path")
    need(branch(gba, 0x373B24, True) == 0x080C8258, "actual floor-effect path")
    # Classifier dispatch identities are established separately from the later
    # fighter callback dispatcher, where source class14 is a known difference.
    mapped = {0x2D9: 0x080C856C, 0x34F: 0x080C8638, 0x321: 0x080C85FC, 0x2E1: 0x080C85BC}
    dispatches = []
    for source_table, native_table in ((0x76F840, 0xC8478), (0x76F820, 0xC8578)):
        for index in range(16):
            source_target = u16(source, source_table + index * 2)
            native_target = u32(gba, native_table + index * 4)
            need(source_target in mapped and mapped[source_target] == native_target,
                 f"collider dispatcher identity {source_table:X}/{index}")
            dispatches.append({"source_table": source_table, "native_table": native_table,
                               "index": index, "source_ip": source_target, "native_target": native_target})
    need(source[0x76F760:0x76F7E0] == gba[0xC84B8:0xC8538], "eight commercial stage-class rows")
    need(u16(source, 0x742C1F + 14 * 2) == 0x25BF and u32(gba, 0x3549FC + 14 * 4) == 0x08354DD4,
         "explicit later class14 behavior difference")
    return {"commercial_pairs": pairs, "native_instruction_contracts": len(native),
            "source_instruction_contracts": len(source_expected), "collider_dispatcher_entries": dispatches,
            "source_collision_sha256": sha(source[0x76F8B4:0x76FF84]),
            "later_class14_source": 0x742EBF, "later_class14_native": 0x08354DD4,
            "later_class14_parity_claimed": False}


def no_inbound(data: bytes) -> None:
    def owned(value: int) -> bool:
        return any(BASE + lo <= value < BASE + hi for lo, hi in ALLOCATIONS)
    for at in range(len(data) - 3):
        need(not owned(u32(data, at)), f"predecessor byte-aligned pointer into allocation {at:X}")
    for at in range(0, len(data) - 3, 4):
        word = u32(data, at)
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 1 << 24
            need(not owned(BASE + at + 8 + 4 * delta), f"predecessor ARM branch into allocation {at:X}")
        if word & 0x0E1F0000 == 0x041F0000:
            delta = word & 0xFFF
            if not word & 0x800000:
                delta = -delta
            need(not owned(BASE + at + 8 + delta), f"predecessor ARM literal into allocation {at:X}")


def verify(before: bytes, after: bytes, gba: bytes, source: bytes) -> dict:
    need(len(before) == len(after) == 0x800000, "ROM size")
    for lo, hi in CONSUMERS:
        need(after[lo:hi] == gba[lo:hi] == before[lo:hi], f"native consumer preserved {lo:X}")
    for lo, hi in ALLOCATIONS:
        need(before[lo:hi] == b"\xFF" * (hi - lo), f"Expected Write blank region {lo:X}")
    pointer_intervals, reports = [], []
    for name, source_records, native_records, width, height, raw, target, stage in GRIDS:
        count = width * height * 28 * 18
        size = count * 4
        for record in source_records:
            descriptor = 0x3B4DD0 + record * 24
            need(struct.unpack_from("<HH", source, descriptor) == (width, height), "source dimensions")
            offset, segment = struct.unpack_from("<HH", source, descriptor + 12)
            physical = segment * 16 + offset
            need(0x20000 <= physical and physical + size <= 0x30000, "source complete C2 window extent")
            resolved = ((source[descriptor + 5] & 0x7F) << 16) + (physical - 0x20000)
            need(resolved == raw, "source grid bank/segment/offset")
        for record in native_records:
            descriptor = 0x580000 + record * 24
            need(struct.unpack_from("<HH", after, descriptor) == (width, height), "native grid dimensions")
            need(u32(before, descriptor + 12) == 0, "Expected Write null collision field")
            need(u32(after, descriptor + 12) == BASE + target, "actual native collision pointer")
            need(after[descriptor:descriptor + 12] == before[descriptor:descriptor + 12] and
                 after[descriptor + 16:descriptor + 24] == before[descriptor + 16:descriptor + 24],
                 "noncollision descriptor fields preserved")
            pointer_intervals.append((descriptor + 12, descriptor + 16))
        source_cells = list(struct.iter_unpack("<HH", source[raw:raw + size]))
        native_cells = list(struct.iter_unpack("<HH", after[target:target + size]))
        need(len(source_cells) == len(native_cells) == count and source_cells == native_cells,
             f"every {name} four-byte cell inverse")
        kinds = {0}
        for first, second in set(source_cells):
            kinds |= {k | ((first >> 2) & 15) for k in kinds.copy()}
        need(kinds <= {0, 1}, f"{name} arbitrary sampled-cell OR kind closure")
        reports.append({"name": name, "source_raw": raw, "target_raw": target, "cells": count,
                        "source_records": source_records, "native_records": native_records,
                        "sha256": sha(after[target:target + size]),
                        "first_word_frequencies": sorted(Counter(x[0] for x in source_cells).items()),
                        "second_word_frequencies": sorted(Counter(x[1] for x in source_cells).items()),
                        "sampled_cell_or_kind_closure": sorted(kinds),
                        "stage": stage, "classifications": [[k, source[0x76F760 + stage * 16 + k]] for k in sorted(kinds)]})
    need(u32(before, HOOK) == 0xE28F4078, "Expected Write original ADR")
    need(branch(after, HOOK) == BASE + BRIDGE, "hook reaches complete bridge")
    need(insn(after, BRIDGE) == ("ldr", "r4, [pc]"), "bridge only defines intended r4")
    need(branch(after, BRIDGE + 4) == BASE + HOOK + 4, "nonlinking bridge resumes original instruction")
    need(u32(after, BRIDGE + 8) == BASE + TABLE, "bridge table pointer literal")
    need(after[TABLE:TABLE + 192] == source[0x76F760:0x76F820], "all twelve classification rows inverse")
    need(max(after[TABLE:TABLE + 192]) < 16, "both sixteen-entry native dispatcher bounds")
    # Cover each complete first-word value; all unrelated flag bits survive.
    for stage in range(12):
        for flags in range(0x10000):
            index = (flags >> 2) & 15
            expected = (flags & 0xFFC3) | (source[0x76F760 + 16 * stage + index] << 2)
            actual = (flags & ~0x3C) | (after[TABLE + 16 * stage + index] << 2)
            need(actual == expected, "full first-word classifier inverse")
    intervals = sorted(ALLOCATIONS + tuple(pointer_intervals) + ((HOOK, HOOK + 4),))
    cursor = 0
    for lo, hi in intervals:
        need(after[cursor:lo] == before[cursor:lo], f"unexpected write before {lo:X}")
        cursor = hi
    need(after[cursor:] == before[cursor:], "unexpected trailing write")
    return {"grids": reports, "unique_cells_reversed": sum(x["cells"] for x in reports),
            "native_descriptor_bindings": len(pointer_intervals), "classification_bytes_reversed": 192,
            "first_word_classification_cases": 12 * 65536, "bridge_instruction_count": 2,
            "bridge_abi": "r4 set to table; other registers, LR, SP and CPSR preserved",
            "expected_write_intervals": intervals,
            "changed_bytes": sum(a != b for a, b in zip(before, after, strict=True))}


def negative_checks(before: bytes, after: bytes, gba: bytes, source: bytes) -> list[str]:
    cases = (
        ("null Train collision", 0x580000 + 21 * 24 + 12, bytes(4)),
        ("wrong Iraira grid", 0x580000 + 25 * 24 + 12, struct.pack("<I", BASE + 0x622000)),
        ("wrong Waterfall geometry", 0x580000 + 27 * 24, struct.pack("<H", 2)),
        ("altered first cell", 0x622000, bytes((after[0x622000] ^ 1,))),
        ("lost second-word metadata", 0x624002, bytes((after[0x624002] ^ 1,))),
        ("truncated final cell", 0x62779F, bytes((after[0x62779F] ^ 1,))),
        ("missing Train kind1", TABLE + 8 * 16 + 1, bytes(1)),
        ("missing Iraira kind1", TABLE + 10 * 16 + 1, bytes(1)),
        ("out-of-range handler class", TABLE + 10 * 16 + 1, b"\x90"),
        ("bridge wrong register", BRIDGE, struct.pack("<I", 0xE59F5000)),
        ("bridge clobbers LR", BRIDGE + 4, struct.pack("<I", u32(after, BRIDGE + 4) | 0x01000000)),
        ("bridge table interior pointer", BRIDGE + 8, struct.pack("<I", BASE + TABLE + 16)),
        ("unowned gap changed", 0x623F90, bytes(1)),
        ("native low-bit semantics changed", 0xC89E0, struct.pack("<I", 0xE2133001)),
        ("collider handler14 changed", 0xC8578 + 14 * 4, struct.pack("<I", 0x080C85FC)),
        ("unrelated Train descriptor22 changed", 0x580000 + 22 * 24 + 12, struct.pack("<I", BASE + 0x622000)),
    )
    rejected = []
    for label, at, replacement in cases:
        changed = bytearray(after)
        need(changed[at:at + len(replacement)] != replacement, "negative must mutate bytes")
        changed[at:at + len(replacement)] = replacement
        try:
            verify(before, bytes(changed), gba, source)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(f"semantic mutation accepted: {label}")
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    a = parser.parse_args()
    need(all(getattr(a, x).suffix.lower() == ".gba" for x in ("before", "after", "gba")), "GBA paths only")
    need(a.wsc10.suffix.lower() == a.wsc15.suffix.lower() == ".wsc" and a.report.suffix.lower() == ".json", "WSC/report types")
    before, after, gba, old, source = (getattr(a, x).read_bytes() for x in ("before", "after", "gba", "wsc10", "wsc15"))
    need(tuple(map(sha, (gba, old, source))) == ORIGINALS and sha(before) == INPUT, "exact original/predecessor identities")
    contracts = contract_proof(gba, old, source)
    no_inbound(before)
    result = verify(before, after, gba, source)
    negatives = negative_checks(before, after, gba, source)
    need(sha(after) == OUTPUT, "reviewed final artifact")
    report = {"schema": 1, "status": "PASS", "kind": "independent-added-stage-collision",
              "input_sha256": INPUT, "output_sha256": OUTPUT, "source_and_consumer_proof": contracts,
              **result, "semantic_mutations_rejected": negatives, "predecessor_inbounds": [],
              "provided_save_accessed": False, "runtime_launched": False,
              "scope": "complete source grids, native descriptor binding, bounded classification lookup and classifier dispatch",
              "remaining": ["source fighter floor class14 handler742EBF is absent at native dispatcher3549FC index14",
                            "Train graphics geometry, palette and initialization belong to a separate layer",
                            "runtime and full stage-effect parity are not established by static cell inversion"]}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-added-stage-collision] PASS; {result['unique_cells_reversed']} cells, 192 class bytes, {len(negatives)} semantic negatives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
