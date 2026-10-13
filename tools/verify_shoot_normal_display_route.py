#!/usr/bin/env python3
"""Independent exact-instruction and branch-domain proof for the normal router."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BASE = 0x08000000
BEFORE = "39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D"
AFTER = "455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(test: bool, message: str) -> None:
    if not test:
        raise ValueError(message)


def target(site: int, word: int) -> int:
    offset = word & 0xFFFFFF
    if offset & 0x800000:
        offset -= 0x1000000
    return site + 8 + 4 * offset


def instructions(data: bytes, raw: int, size: int) -> list[str]:
    rows = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[raw:raw + size], BASE + raw))
    need(len(rows) * 4 == size and all(i.size == 4 for i in rows), "complete ARM decode")
    return [i.mnemonic + " " + i.op_str for i in rows]


def route_contract(data: bytes) -> None:
    need(instructions(data, 0x5E7A00, 20) == [
        "ldr r8, [pc, #0xc]", "ldrh sb, [r8]", "tst sb, #0x400",
        "bne #0x80c97b8", "b #0x85e7400"], "five-instruction branch/ABI contract")
    need(struct.unpack_from("<I", data, 0x5E7A14)[0] == 0x0300450A, "actual Shoot flag literal")
    need(instructions(data, 0x587200, 4) == ["b #0x85e7a00"], "single non-link hook")


def verify(before: bytes, after: bytes, gba: bytes) -> dict:
    need((sha(before), sha(after), sha(gba)) == (BEFORE, AFTER, GBA), "fixed chain and original hashes")
    need(len(before) == len(after) == 0x800000, "ROM length")
    need(sha(before[0x587200:0x5872C0]) == "DCB1B73D6716FABF274F339F8D12249BE38EEEF5667932901811A5A7EBEA13D8", "predecessor full display body")
    need(instructions(before, 0x587200, 16) == ["ldr r8, [pc, #0x9c]", "ldrh sb, [r8]", "tst sb, #0x400", "bne #0x80c97b8"], "original branch boundary")
    need(struct.unpack_from("<I", before, 0x5872A4)[0] == 0x0300450A, "old flag literal")
    need(sha(after[0x5E7400:0x5E7548]) == "019D8C1BCE934C7D91CDC31E8243C7F48A4D26AEC0BAF4BB1E558E3D12C08CDD", "unchanged proved display body")
    need(sha(gba[0x112C0:0x11428]) == "9A4C3C29D7751D7BF97D6B19C856433AE15F1155D27A74AD3FE734E24992E2A3", "native IRQ dispatcher")
    need(instructions(gba, 0x1140C, 24) == ["ldr r8, [pc, #0x10]", "ldr sb, [r8]", "movs sb, sb", "mov lr, pc", "bxne sb", "b #0x8011374"], "callback dispatch and return")
    need(struct.unpack_from("<I", gba, 0x11424)[0] == 0x030012E0, "IRQ callback slot")
    need(before[0x5E7A00:0x5E7A40] == b"\xFF" * 64, "free router owner")
    for raw in range(0, len(before), 4):
        word = struct.unpack_from("<I", before, raw)[0]
        need(not 0x085E7A00 <= (word & ~1) < 0x085E7A40, "preexisting router pointer")
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            need(not 0x5E7A00 <= target(raw, word) < 0x5E7A40, "preexisting router branch")
    route_contract(after)
    need(sha(after[0x5E7A00:0x5E7A18]) == "9DE068243F3D327AB7A568979714854CF9322B603FD74B795EDDB319D3825BC3", "reviewed final router encoding")
    allowed = set(range(0x587200, 0x587204)) | set(range(0x5E7A00, 0x5E7A18))
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    need(len(changed) == 27 and changed <= allowed, "full-ROM exact write ownership")
    destinations = {"normal": 0, "existing_transition": 0}
    for flags in range(65536):
        old_transition = (flags & 0x400) != 0
        new_destination = 0x080C97B8 if flags & 0x400 else 0x085E7400
        need((new_destination == 0x080C97B8) == old_transition, "all-flags transition preservation")
        destinations["existing_transition" if old_transition else "normal"] += 1
    negative = []
    for label, raw, replacement in (
        ("wrong flag mask", 0x5E7A08, 0xE3190A01),
        ("wrong condition", 0x5E7A0C, struct.unpack_from("<I", after, 0x5E7A0C)[0] & 0x0FFFFFFF),
        ("wrong transition target", 0x5E7A0C, struct.unpack_from("<I", after, 0x5E7A0C)[0] + 1),
        ("link changes LR", 0x5E7A10, struct.unpack_from("<I", after, 0x5E7A10)[0] | 0x01000000),
        ("wrong flag owner", 0x5E7A14, 0x03004508),
        ("wrong hook", 0x587200, struct.unpack_from("<I", after, 0x587200)[0] + 1),
    ):
        candidate = bytearray(after)
        struct.pack_into("<I", candidate, raw, replacement)
        try:
            route_contract(candidate)
        except ValueError as error:
            negative.append({"case": label, "rejected": True, "reason": str(error)})
        else:
            raise ValueError("semantic mutation was accepted: " + label)
    return {"status": "PASS", "input_sha256": BEFORE, "output_sha256": AFTER,
        "changed_bytes": len(changed), "router_ARM_instructions": 5,
        "flag_cases": 65536, "destinations": destinations, "semantic_negative_controls": negative,
        "ABI": "no stack or LR operation; old r8/r9/TST effects reproduced",
        "new_display_used_only_when_0400_clear": True, "old_0400_fallback_preserved": True,
        "transition_IRQ_or_terminal_route_opened": False, "runtime_or_save_test": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    need(all(p.suffix.lower() != ".sav" for p in (args.before, args.after, args.gba)), "save paths forbidden")
    report = verify(args.before.read_bytes(), args.after.read_bytes(), args.gba.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[verify-shoot-normal-display-route] PASS " + AFTER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
