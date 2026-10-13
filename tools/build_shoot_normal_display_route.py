#!/usr/bin/env python3
"""Connect the proved normal display while preserving the existing 0400 path."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

BASE, SITE, START, END = 0x08000000, 0x587200, 0x5E7A00, 0x5E7A40
INPUT_SHA256 = "39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
DISPLAY_SHA256 = "019D8C1BCE934C7D91CDC31E8243C7F48A4D26AEC0BAF4BB1E558E3D12C08CDD"
OLD_DISPLAY_SHA256 = "DCB1B73D6716FABF274F339F8D12249BE38EEEF5667932901811A5A7EBEA13D8"
IRQ_SHA256 = "9A4C3C29D7751D7BF97D6B19C856433AE15F1155D27A74AD3FE734E24992E2A3"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def branch_target(site: int, word: int) -> int:
    offset = word & 0xFFFFFF
    if offset & 0x800000:
        offset -= 0x1000000
    return site + 8 + offset * 4


def assemble(source: str, offset: int) -> bytes:
    data, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + offset)
    return bytes(data)


def build(before: bytes, gba: bytes) -> tuple[bytes, dict]:
    need(INPUT_SHA256 is not None and sha(before) == INPUT_SHA256, "fixed terminal predecessor")
    need(sha(gba) == GBA_SHA256, "commercial GBA identity")
    need(len(before) == 0x800000, "ROM size")
    need(sha(before[SITE:SITE + 0xC0]) == OLD_DISPLAY_SHA256, "existing display body")
    need(sha(before[0x5E7400:0x5E7548]) == DISPLAY_SHA256, "proved resident display")
    need(sha(gba[0x112C0:0x11428]) == IRQ_SHA256, "native IRQ dispatcher")
    need(before[START:END] == b"\xFF" * (END - START), "router reservation not blank")
    for raw in range(0, len(before), 4):
        word = struct.unpack_from("<I", before, raw)[0]
        need(not BASE + START <= (word & ~1) < BASE + END, "preexisting router pointer")
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            need(not START <= branch_target(raw, word) < END, "preexisting router branch")
    router = assemble("""
        ldr r8, flags
        ldrh r9, [r8]
        tst r9, #0x400
        bne 0x080C97B8
        b 0x085E7400
    flags: .word 0x0300450A
    """, START)
    need(len(router) == 24, "router geometry")
    hook = assemble(f"b 0x{BASE + START:08X}", SITE)
    writes = [(SITE, before[SITE:SITE + 4], hook, "normal_display_router"),
              (START, b"\xFF" * len(router), router, "conditional_display_route")]
    after = bytearray(before)
    for raw, previous, replacement, label in writes:
        need(before[raw:raw + len(previous)] == previous, "Expected Write " + label)
        after[raw:raw + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {raw + i for raw, previous, replacement, _ in writes
                for i, (a, b) in enumerate(zip(previous, replacement, strict=True)) if a != b}
    need(changed == expected, "complete Expected Write diff")
    return bytes(after), {"input_sha256": INPUT_SHA256, "output_sha256": sha(after),
        "changed_bytes": len(changed), "router_entry": BASE + START,
        "expected_writes": [{"raw": raw, "bytes": len(replacement), "label": label,
            "before_sha256": sha(previous), "after_sha256": sha(replacement)}
            for raw, previous, replacement, label in writes],
        "normal_target": "085E7400 only when Shoot0400 is clear",
        "transition_target": "080C97B8, identical to predecessor",
        "ABI": "r8/r9 and CPSR match the old initial test; LR/SP unchanged; other registers unchanged",
        "remaining_gate": "0D87/0DEC transition IRQ unresolved; no new scene, menu or terminal entry",
        "runtime_or_save_test": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()
    need(all(p.suffix.lower() != ".sav" for p in (args.input, args.gba, args.output)), "save paths forbidden")
    result, report = build(args.input.read_bytes(), args.gba.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-normal-display-route] " + report["output_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
