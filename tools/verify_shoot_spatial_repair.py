#!/usr/bin/env python3
"""Independent ROM-only collision inverse and terminal order verification.

No generator imports, instruction execution, emulator or save-file access.
Semantic mutation checks run without relying on the final ROM hash.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16, Cs

BASE = 0x08000000
BEFORE = "455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48"
AFTER = "CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69"
ORIGINALS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
             "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
             "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
GRID, ORDER = 0x607000, 0x60A000
INTERVALS = ((GRID, GRID + 12096), (ORDER, ORDER + 12), (0x5CD290, 0x5CD294),
             (0x5802C4, 0x5802C8), (0x5802DC, 0x5802E0))
CONSUMERS = ((0x13BF8, 0x13C64), (0xC86B4, 0xC8E18), (0x373928, 0x373BA4))
RETAIL = ((0, 0x26CB60), (4, 0x270000), (10, 0x271F80), (12, 0x273F00),
          (14, 0x275E80), (16, 0x1F9BA0), (18, 0x1FCAE0))


def need(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def arm(data: bytes, start: int, end: int) -> list:
    out = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[start:end], BASE + start))
    need(sum(x.size for x in out) == end - start, "complete ARM decode")
    return out


def one(data: bytes, at: int) -> tuple[str, str]:
    i = arm(data, at, at + 4)[0]
    return i.mnemonic, i.op_str


def branch(data: bytes, at: int, link: bool) -> int:
    word = struct.unpack_from("<I", data, at)[0]
    need(word >> 24 == (0xEB if link else 0xEA), "unconditional ARM branch kind")
    signed = word & 0xFFFFFF
    if signed & 0x800000:
        signed -= 0x1000000
    return BASE + at + 8 + signed * 4


def source_proof(gba: bytes, old: bytes, new: bytes) -> dict:
    need(tuple(map(sha, (gba, old, new))) == ORIGINALS, "original input identities")
    commercial = []
    for index, source_at in RETAIL:
        record = 0x7F8E0 + 24 * index
        w, h = struct.unpack_from("<HH", gba, record)
        at = struct.unpack_from("<I", gba, record + 12)[0] - BASE
        count = w * h * 28 * 18
        need(gba[at:at + count * 4] == old[source_at:source_at + count * 4], "commercial collision four-byte cell inverse")
        commercial.append({"resource": index, "source": source_at, "native": at, "cells": count})
    expected = {
        0x13C38: ("ldr", "sl, [sb, #0xc]"), 0x13C3C: ("str", "sl, [r8, #0x28]"),
        0xC881C: ("ldr", "r4, [r4, #0x28]"), 0xC8968: ("add", "r4, r4, r0, lsl #2"),
        0xC8988: ("ldrsh", "r8, [r4, #2]"), 0xC8990: ("ldrsh", "r8, [r4], #4"),
    }
    for at, decoded in expected.items():
        need(one(gba, at) == decoded, f"actual native collision consumer {at:X}")
    need(branch(gba, 0x373A08, True) == 0x080C86B4, "native movement pass reaches collision entry")
    # Entire bounded source 193B has a single conditional RETF and no return
    # between its successful callback assignment and the next function.
    code = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(new[0x77383B:0x77387A], 0x193B))
    need(sum(i.size for i in code) == 0x3F, "complete source193B decode")
    returns = [i.address for i in code if i.mnemonic == "retf"]
    need(returns == [0x1960], "source successful193B path must fall through")
    need([(i.mnemonic, i.op_str) for i in code[-2:]] == [("pop", "ds"), ("pop", "bx")], "source193B tail")
    need(new[0x77387A:0x77387D] == bytes.fromhex("B8000C"), "197A immediately follows193B")
    descriptors = []
    for index in (39, 40):
        at = 0x3B4DD0 + index * 24
        w, h = struct.unpack_from("<HH", new, at)
        offset, segment = struct.unpack_from("<HH", new, at + 12)
        bank = new[at + 5]
        physical = segment * 16 + offset
        need(0x20000 <= physical < 0x30000, "C2-selected source collision window")
        raw = ((bank & 127) << 16) | (physical & 65535)
        need((w, h, raw) == (2, 3, 0x33CA20), "source Shoot collision dimensions and pointer")
        descriptors.append({"record": at, "raw": raw, "cells": w * h * 28 * 18})
    return {"commercial_pairs": commercial, "source_descriptors": descriptors,
            "source193B_instructions": len(code), "source193B_returns": returns}


def verify(before: bytes, after: bytes, gba: bytes, new: bytes) -> dict:
    need(len(after) == len(before) == 0x800000, "unchanged ROM size")
    for a, z in CONSUMERS:
        need(after[a:z] == gba[a:z], f"native consumer changed {a:X}")
    for index in (29, 30):
        at = 0x580000 + 24 * index
        need(after[at:at + 12] == before[at:at + 12] and after[at + 16:at + 24] == before[at + 16:at + 24], "only collision pointer field may change")
        need(struct.unpack_from("<HH", after, at) == (2, 3), "2x3 geometry must be retained")
        ptr = struct.unpack_from("<I", after, at + 12)[0]
        need(ptr == BASE + GRID, "both native BG collision pointers select the complete grid")
        cells = struct.iter_unpack("<HH", after[ptr - BASE:ptr - BASE + 12096])
        for ordinal, native_cell in enumerate(cells):
            source_cell = struct.unpack_from("<HH", new, 0x33CA20 + ordinal * 4)
            need(native_cell == source_cell, f"collision cell inverse {ordinal}")
    need(branch(after, 0x5CD290, False) == BASE + ORDER, "success arm enters repair without linking")
    need(branch(after, ORDER, True) == 0x08012008, "callback assignment comes first")
    need(branch(after, ORDER + 4, True) == 0x085CD2B0, "197A runs in the same invocation")
    need(branch(after, ORDER + 8, False) == 0x085CD294, "existing stack-restoring epilogue is reused")
    need(after[0x5CD270:0x5CD290] == before[0x5CD270:0x5CD290], "bit4-false path and original push are preserved")
    need(after[0x5CD294:0x5CD33C] == before[0x5CD294:0x5CD33C], "epilogue,197A body and literals preserved")
    need(one(after, 0x5CD288) == ("beq", "#0x85cd294"), "bit4-false path bypasses new call")
    need(one(after, 0x5CD294)[0] == "pop" and one(after, 0x5CD298) == ("bx", "lr"), "balanced original return")
    need(after[GRID:GRID + 12096] == new[0x33CA20:0x33F960], "complete payload inverse")
    # The floor supports a conditional geometry lemma, not a whole-game bound.
    floor = [struct.unpack_from("<HH", after, GRID + (50 * 56 + x) * 4) for x in range(56)]
    need(all((cell[0] & 3) in (1, 3) and cell[1] == 0 for cell in floor), "row50 complete solid floor")
    need(all(struct.unpack_from("<H", after, GRID + i * 4)[0] <= 3 for i in range(3024)), "no stage7 special collision-kind bits")
    # Compare every preserved segment, including holes within the allocation.
    cursor = 0
    for a, z in sorted(INTERVALS):
        need(after[cursor:a] == before[cursor:a], f"unexpected write outside interval before {a:X}")
        cursor = z
    need(after[cursor:] == before[cursor:], "unexpected trailing write")
    return {"collision_cells_reversed": 3024, "native_collision_resources": 2,
            "new_ARM_instructions": len(arm(after, ORDER, ORDER + 12)),
            "changed_bytes": sum(x != y for x, y in zip(before, after, strict=True)),
            "conditional_geometry": "continuous solid source row50 at Y1900; actor flag, displacement and position-writer reachability remain separate"}


def no_inbound(before: bytes) -> None:
    for p in range(len(before) - 3):
        value = struct.unpack_from("<I", before, p)[0]
        need(not 0x08607000 <= value < 0x0860A100, "inbound pointer encoding")
    for p in range(0, len(before) - 3, 4):
        word = struct.unpack_from("<I", before, p)[0]
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            relative = word & 0xFFFFFF
            if relative & 0x800000:
                relative -= 0x1000000
            target = p + 8 + relative * 4
            need(not 0x607000 <= target < 0x60A100, "inbound ARM-like branch encoding")


def negative_cases(before: bytes, after: bytes, gba: bytes, new: bytes) -> list[str]:
    cases = (
        ("null first BG collision", 0x5802C4, bytes(4)),
        ("null second BG collision", 0x5802DC, bytes(4)),
        ("collision pointer selects interior", 0x5802C4, struct.pack("<I", BASE + GRID + 4)),
        ("floor cell removed", GRID + 50 * 56 * 4, bytes(4)),
        ("top wall cell removed", GRID, bytes(4)),
        ("skip same-call197A", ORDER + 4, bytes.fromhex("0000A0E1")),
        ("skip callback assignment", ORDER, bytes.fromhex("0000A0E1")),
        ("bit4-false path calls next phase", 0x5CD288, bytes.fromhex("0000A0E1")),
        ("wrong native collision pointer field", 0xC881C, bytes.fromhex("244094E5")),
        ("unexpected allocation-gap write", 0x609F40, b"\x00"),
    )
    passed = []
    for label, at, data in cases:
        bad = bytearray(after)
        bad[at:at + len(data)] = data
        try:
            verify(before, bytes(bad), gba, new)
        except ValueError:
            passed.append(label)
        else:
            raise AssertionError(f"semantic negative was accepted: {label}")
    return passed


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        p.add_argument(name, type=pathlib.Path)
    p.add_argument("--output", required=True, type=pathlib.Path)
    a = p.parse_args()
    names = ("before", "after", "gba", "wsc10", "wsc15")
    need(all(getattr(a, k).suffix.lower() != ".sav" for k in names), "save files forbidden")
    before, after, gba, old, new = (getattr(a, k).read_bytes() for k in names)
    need(sha(before) == BEFORE, "exact v53 predecessor")
    need(before[0x607000:0x60A100] == b"\xFF" * 0x3100, "blank allocation")
    source = source_proof(gba, old, new)
    no_inbound(before)
    result = verify(before, after, gba, new)
    negatives = negative_cases(before, after, gba, new)
    need(sha(after) == AFTER, "reviewed final identity")
    report = {"schema": 1, "kind": "independent-shoot-spatial-repair", "input_sha256": BEFORE,
              "output_sha256": AFTER, "source_proof": source, **result,
              "negative_cases": negatives, "expected_write_intervals": INTERVALS,
              "status": "PASS", "remaining": ["197A camera live-in range and task/IRQ ownership", "8EF3 complete actor-position domain"]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-shoot-spatial-repair] PASS; 3024 cell inverses, 7 retail pairs, {len(negatives)} semantic negatives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
