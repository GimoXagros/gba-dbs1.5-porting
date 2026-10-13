#!/usr/bin/env python3
"""Verify final initializer instructions, write ownership and P2 inverse.

This uses the independent resource reader, never a generator or converter.
No CPU instructions or game callbacks are executed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct

from analyze_shoot_initializer_lifetime import analyze, decode, demand, digest

BEFORE_SHA256 = "2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE"
BASE = 0x08000000
REGISTERS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
PUSH, POP = "push " + REGISTERS, "pop " + REGISTERS
WINDOWS = ((0x5C4000, 120, 100), (0x5C4300, 84, 72), (0x5C4400, 28, 24),
           (0x5C4500, 140, 124), (0x5C4600, 140, 124), (0x5C4800, 332, 0),
           (0x5C4C00, 404, 0), (0x5C5000, 40, 0))


def word(rom: bytes, site: int) -> int:
    return struct.unpack_from("<I", rom, site)[0]


def instructions(rom: bytes, site: int, size: int) -> list[str]:
    return [f"{i.mnemonic} {i.op_str}" for i in decode(rom, site, size)]


def code_contract(rom: bytes) -> None:
    graphics = [PUSH, "mov fp, #0", "bl #0x807fbf8", "ldr r8, [pc, #0x50]",
                "add sb, r8, #1", "ldr r5, [pc, #0x4c]", "str r8, [r5]", "str sb, [r5, #4]",
                "ldr r5, [pc, #0x44]", "str r8, [r5]", "str sb, [r5, #4]",
                "ldr r5, [pc, #0x3c]", "str r8, [r5]", "str sb, [r5, #4]",
                "ldr r5, [pc, #0x34]", "str r8, [r5]", "str sb, [r5, #4]",
                "bl #0x8000cd8", "and r0, r0, #0xff", "strh r0, [r8]",
                "bl #0x8015d38", "bl #0x801369c", "bl #0x8582a00", POP, "bx lr"]
    manager = [PUSH, "mov fp, #0", "ldr r8, [pc, #0x38]", "mov sb, #0xb", "strb sb, [r8]",
               "ldr r8, [pc, #0x30]", "mov sb, #0x3840", "strh sb, [r8]",
               "ldr r8, [pc, #0x28]", "mov sb, #0", "strh sb, [r8]",
               "strh sb, [r8, #2]", "strh sb, [r8, #4]", "mov sb, #0x10",
               "strh sb, [r8]", "bl #0x836d224", POP, "bx lr"]
    clear = [PUSH, "ldr r8, [pc, #0xc]", "mov sb, #0", "strh sb, [r8]", POP, "bx lr"]
    adapter = [PUSH, "str r5, [sp, #-4]!", "mov r8, #0", "str r8, [sp, #-4]!",
               "ldr r8, [pc, #0x64]", "str r8, [sp, #-4]!", "mov r8, #0",
               "str r8, [sp, #-4]!", "str r8, [sp, #-4]!", "ldr r8, [pc, #0x54]",
               "str r8, [sp, #-4]!", "mov r8, #0", "str r8, [sp, #-4]!", "str r8, [sp, #-4]!",
               "ldr r8, [pc, #0x44]", "str r8, [sp, #-4]!", "mov r8, #0",
               "str r8, [sp, #-4]!", "str r8, [sp, #-4]!", "mov r8, #0x4000", "str r8, [sp, #-4]!",
               "mov r8, #0x1800", "str r8, [sp, #-4]!", "ldr r8, [pc, #0x24]", "str r8, [sp, #-4]!",
               "mov r8, #5", "str r8, [sp, #-4]!", "bl #0x80127e4", "add sp, sp, #0x3c", POP, "bx lr"]
    for site, sequence in ((0x5C4000, graphics), (0x5C4300, manager), (0x5C4400, clear),
                           (0x5C4500, adapter), (0x5C4600, adapter)):
        demand(instructions(rom, site, len(sequence) * 4) == sequence,
               f"complete initializer instruction contract at {site:X}")
    for site, expected in (
        (0x5C4064, (0x030012B8, 0x03002338, 0x03002388, 0x030023D8, 0x03002428)),
        (0x5C4348, (0x0300231E, 0x03004500, 0x03004506)), (0x5C4418, (0x030048A4,)),
        (0x5C457C, (0x085C4800, 0x085DB300, 0x085C5000, 0x6D)),
        (0x5C467C, (0x085C4C00, 0x085DB400, 0x085DB740, 0x137)),
    ):
        demand(struct.unpack_from(f"<{len(expected)}I", rom, site) == expected,
               f"initializer literal consumer at {site:X}")


def palette_inverse(rom: bytes, source: bytes) -> None:
    native = struct.unpack_from("<20H", rom, 0x5C5000)
    compact = struct.unpack_from("<19H", source, 0x3D7AC0)
    demand(native[:3] == compact[:3] and native[-1] == 0, "P2 header/padding")
    # Derive inverse channel values from the established 4-bit/5-bit lattice.
    lattice = (0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
    inverse = []
    for value in native[3:19]:
        channels = (value & 31, (value >> 5) & 31, (value >> 10) & 31)
        demand(value < 0x8000 and all(c in lattice for c in channels), "P2 source color lattice")
        inverse.append((lattice.index(channels[0]) << 8) |
                       (lattice.index(channels[1]) << 4) | lattice.index(channels[2]))
    demand(tuple(inverse) == compact[3:], "P2 inverse source identity")


def consumers(gba: bytes) -> None:
    # The graphics helper intentionally retains the retail CD8 clobber of r8.
    demand(instructions(gba, 0xCD8, 12) == ["ldr r8, [pc, #4]", "ldrh r0, [r8]", "bx lr"]
           and word(gba, 0xCE4) == 0x030012B6, "display shadow call clobber")
    demand(instructions(gba, 0x3EE48, 20) == ["bl #0x8000cd8", "and r0, r0, #0xff",
           "strh r0, [r8]", "bl #0x8015d38", "bl #0x801369c"], "retail graphics continuation")
    demand(instructions(gba, 0xD1840, 8) == ["mov sb, #0x3840", "strh sb, [r8]"], "native timer producer")
    demand(instructions(gba, 0x375010, 12) == ["ldrh sb, [r8]", "subs sb, sb, #1", "strh sb, [r8]"],
           "native timer decrement")
    demand(instructions(gba, 0x373D38, 20) == ["ldrh r0, [r8]", "mov r1, #0x3c", "bl #0x837db3c",
           "mov r1, #0x3c", "bl #0x837db3c"] and word(gba, 0x373DA4) == 0x03004500,
           "native timer HUD divisor and pointer")


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    before, after = args.before.read_bytes(), args.after.read_bytes()
    sources = {k: getattr(args, k).read_bytes() for k in ("gba", "wsc10", "wsc15")}
    demand(digest(before) == BEFORE_SHA256 and len(before) == len(after) == 0x800000, "exact predecessor/extent")
    resource_report = analyze(sources, after)
    code_contract(after)
    palette_inverse(after, sources["wsc15"])
    consumers(sources["gba"])
    allowed = {p for start, size, _ in WINDOWS for p in range(start, start + size)}
    demand(all(before[p] == 255 for p in allowed), "Expected Write before bytes")
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    demand(bool(changed) and changed <= allowed, "full ROM diff containment")
    gap_candidates = []
    for site in range(0, len(before), 4):
        value = word(before, site)
        targets = [value - BASE]
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            targets.append(site + 8 + delta * 4)
        for target in targets:
            demand(target not in allowed, f"preexisting pointer/branch into new code at {site:X}")
            if 0x5C4000 <= target < 0x5C6000:
                demand(after[target] == before[target] == 255, "referenced gap must remain untouched")
                gap_candidates.append({"site": site, "target": target})
    negatives = []
    for label, site, value in (
        ("timer incorrectly cleared", 0x5C4318, 0xE3A09000),
        ("initial flag clear omitted", 0x5C4328, 0xE1A00000),
        ("0660 clear widens to adjacent field", 0x5C440C, 0xE5889000),
        ("graphics stage clone replaced by unsafe common HUD", 0x5C4058, 0xEBE9EB6A),
        ("constructor stack cleanup loses one word", 0x5C4570, 0xE28DD038),
    ):
        mutated = bytearray(after)
        struct.pack_into("<I", mutated, site, value)
        try:
            code_contract(mutated)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"negative initializer regression accepted: {label}")
    report = {"schema": 1, "kind": "independent-shoot-initializer-final-code-verification",
              "before_sha256": digest(before), "after_sha256": digest(after),
              "resource_consumers": resource_report, "actual_changed_bytes": len(changed),
              "decoded_instructions": sum(n // 4 for _, _, n in WINDOWS),
              "expected_write_intervals": [[p, p + n] for p, n, _ in WINDOWS],
              "unclassified_references_to_preserved_gaps": gap_candidates,
              "negative_regressions_rejected": negatives,
              "claim_scope": "resident component instruction/ABI/resource identity only; full initializer order, native scene lifecycle and runtime remain unproved"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
