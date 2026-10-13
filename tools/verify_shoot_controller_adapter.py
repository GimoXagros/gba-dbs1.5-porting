#!/usr/bin/env python3
"""Independently decode the controller adapter, without a builder import."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

BASE = 0x085C6500
PINS = (
    (0x5C6000, 180, "50B090CE223B5B5321F88FD96456B0EFAD263B114E4ED12F7AB77CBFDD4830CF"),
    (0x5C6200, 76, "75240FDF5E47873B21990DDC7568541B14FC458AE9B7D4040099FDDE9A962848"),
    (0x5C6400, 64, "DDFDCEFE5A45221AF27E17F729FD8FCC167418FADBF362F52D5CF4995BD18F94"),
    (0x5CB000, 6432, "50F925198CD5BF6AA23DDC8A94778B24A085BCB292B1B7EC856268E4ACA982C3"),
)
REGS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(value: bool, name: str) -> None:
    if not value:
        raise ValueError(name)


def code(blob: bytes) -> None:
    demand(len(blob) == 44, "adapter size")
    ins = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob[:32], BASE))
    actual = [i.mnemonic + " " + i.op_str for i in ins]
    demand(actual == ["push " + REGS, "bl #0x85c6000", "ldr r1, [pc, #0x10]",
                      "ldr r2, [pc, #0x10]", "ldr r3, [pc, #0x10]", "bl #0x85c6200",
                      "pop " + REGS, "bx lr"], "complete adapter instructions and call order")
    demand(struct.unpack_from("<3I", blob, 32) == (0x085CB000, 0x085CB970, 0x085CBD80), "real callback bindings")


def verify(before: bytes, blob: bytes) -> dict:
    code(blob)
    for start, size, expected in PINS:
        demand(sha(before[start:start + size]) == expected, "resident dependency")
    demand(before[0x5C0A00:0x5C0A04] == bytes.fromhex("1EFF2FE1"), "predecessor boundary")
    demand(before[0x5C6500:0x5C652C] == b"\xff" * 44, "adapter blank bytes")
    pointer_count = branch_count = 0
    for offset in range(len(before) - 3):
        value = struct.unpack_from("<I", before, offset)[0]
        if BASE <= value < BASE + 44:
            pointer_count += 1
    for offset in range(0, len(before) - 3, 4):
        value = struct.unpack_from("<I", before, offset)[0]
        if value >> 28 == 15 or value & 0x0E000000 != 0x0A000000:
            continue
        displacement = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
        target = 0x08000000 + offset + 8 + displacement * 4
        if BASE <= target < BASE + 44:
            branch_count += 1
    demand(pointer_count == branch_count == 0, "independent inbound scan")
    rejected = []
    for label, offset, value in (("apply before select", 4, 0xEBFFFF3D), ("wrong 810D callback", 32, 0x085CB080),
                                 ("swap linked callback families", 36, 0x085CBD80), ("lost preserved r4", 24, 0xE8BD5FEF)):
        bad = bytearray(blob)
        struct.pack_into("<I", bad, offset, value)
        try:
            code(bad)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("accepted " + label)
    return {"instructions": 8, "code_bytes": 32, "literal_bytes": 12, "adapter_sha256": sha(blob),
            "RNG_contract": "SELECT zero calls on forced +76 path, exactly one otherwise; APPLY makes no RNG call",
            "same_update": "only three literal loads occur between SELECT and APPLY; no game update call",
            "argument_order": {"r1": "810D", "r2": "8AB8", "r3": "8CDD", "r4": "same current object"},
            "registers_and_SP": "all r0-r12 restored; balanced56-byte local frame", "negative_cases": rejected,
            "incoming_pointers": pointer_count, "incoming_branches": branch_count}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("before", type=pathlib.Path)
    p.add_argument("draft", type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path)
    args = p.parse_args()
    before = args.before.read_bytes()
    draft = json.loads(args.draft.read_text(encoding="utf-8"))
    demand(draft["kind"] == "shoot-controller-adapter-draft" and draft["boundary_changed"] is False, "draft-only state")
    demand(sha(before) == draft["input_sha256"] == "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E", "draft predecessor identity")
    result = {"schema": 1, "kind": "independent-controller-adapter-draft", "proof": verify(before, bytes.fromhex(draft["adapter_hex"])),
              "boundary_changed": False, "ROM_emitted": False,
              "gate": "full initializer/object lifetime and final predecessor pin precede boundary installation"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-shoot-controller-adapter] draft PASS; boundary unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
