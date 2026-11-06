#!/usr/bin/env python3
"""Connect the resident SELECT/APPLY chain while external scene entry stays closed.

The historical --draft-proof path still emits no ROM. Production preserves
the v68 external-route gate; it does not certify unresolved player domains.
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
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

BASE, ADAPTER, BOUNDARY = 0x08000000, 0x5C6500, 0x5C0A00
INPUT_SHA256 = "9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738"
DRAFT_INPUT_SHA256 = "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E"
CONTRACTS = (
    (0x5C6000, 0xB4, "50B090CE223B5B5321F88FD96456B0EFAD263B114E4ED12F7AB77CBFDD4830CF"),
    (0x5C6200, 0x4C, "75240FDF5E47873B21990DDC7568541B14FC458AE9B7D4040099FDDE9A962848"),
    (0x5C6400, 0x40, "DDFDCEFE5A45221AF27E17F729FD8FCC167418FADBF362F52D5CF4995BD18F94"),
    (0x5CB000, 0x1920, "50F925198CD5BF6AA23DDC8A94778B24A085BCB292B1B7EC856268E4ACA982C3"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def adapter() -> bytes:
    source = """
        push {r0-r12, lr}
        bl 0x085C6000
        ldr r1, callback_810d
        ldr r2, callback_8ab8
        ldr r3, callback_8cdd
        bl 0x085C6200
        pop {r0-r12, lr}
        bx lr
    callback_810d: .word 0x085CB000
    callback_8ab8: .word 0x085CB970
    callback_8cdd: .word 0x085CBD80
    """
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + ADAPTER)
    return bytes(encoded)


def inbound(data: bytes, start: int, size: int) -> list[tuple[str, int, int]]:
    result = []
    for site in range(len(data) - 3):
        word = struct.unpack_from("<I", data, site)[0]
        if BASE + start <= word < BASE + start + size:
            result.append(("pointer", site, word))
    for site in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, site)[0]
        if word >> 28 == 15 or word & 0x0E000000 != 0x0A000000:
            continue
        distance = (word & 0xFFFFFF) - (0x1000000 if word & 0x800000 else 0)
        target = site + 8 + distance * 4
        if start <= target < start + size:
            result.append(("branch", site, BASE + target))
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=pathlib.Path)
    p.add_argument("output", nargs="?", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path)
    p.add_argument("--draft-proof", action="store_true")
    args = p.parse_args()
    if not args.draft_proof:
        demand(args.output is not None, "output path required")
    before = args.input.read_bytes()
    expected = DRAFT_INPUT_SHA256 if args.draft_proof else INPUT_SHA256
    demand(sha(before) == expected, "exact adapter predecessor identity")
    for site, size, fingerprint in CONTRACTS:
        demand(sha(before[site:site + size]) == fingerprint, "resident SELECT/APPLY/lower callback dependency")
    blob = adapter()
    demand(len(blob) == 44, "adapter size")
    expected_adapter = b"\xff" * len(blob) if args.draft_proof else blob
    demand(before[ADAPTER:ADAPTER + len(blob)] == expected_adapter, "exact adapter predecessor bytes")
    demand(before[BOUNDARY:BOUNDARY + 4] == bytes.fromhex("1EFF2FE1"), "exact existing BX LR boundary")
    references = inbound(before, ADAPTER, len(blob))
    demand(not references, "inbound reference reaches actual adapter bytes")
    ins = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(blob[:32], BASE + ADAPTER))
    demand(len(ins) == 8 and all(i.size == 4 for i in ins), "complete adapter decode")
    roundtrip, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm("\n".join(i.mnemonic + " " + i.op_str for i in ins), BASE + ADAPTER)
    demand(bytes(roundtrip) == blob[:32], "adapter ARM round trip")
    report = {"schema": 1, "kind": "shoot-controller-adapter-draft" if args.draft_proof else "shoot-controller-adapter",
              "input_sha256": sha(before), "adapter": ADAPTER, "code_bytes": 32, "literal_bytes": 12,
              "adapter_hex": blob.hex().upper(), "adapter_sha256": sha(blob),
              "dependency_contracts": CONTRACTS, "incoming_actual_interval": references,
              "boundary_changed": not args.draft_proof,
              "scope": "resident SELECT/APPLY connection only; external scene/menu entry remains closed and player spatial/terminal lifetimes remain unproved"}
    if not args.draft_proof:
        patch, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(f"b 0x{BASE + ADAPTER:X}", BASE + BOUNDARY)
        result = bytearray(before)
        result[BOUNDARY:BOUNDARY + 4] = bytes(patch)
        changes = [i for i, (a, b) in enumerate(zip(before, result, strict=True)) if a != b]
        demand(changes and all(BOUNDARY <= i < BOUNDARY + 4 for i in changes), "four-byte controller boundary containment")
        restored = bytearray(result)
        restored[BOUNDARY:BOUNDARY + 4] = before[BOUNDARY:BOUNDARY + 4]
        demand(restored == before, "whole-ROM boundary inverse")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(result)
        report.update(output_sha256=sha(result), changed_bytes=len(changes), boundary_patch=bytes(patch).hex().upper(),
                      expected_writes=[{"offset": BOUNDARY, "size": 4,
                                        "before": before[BOUNDARY:BOUNDARY + 4].hex().upper(),
                                        "after": bytes(patch).hex().upper()}])
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-controller-adapter] " + ("draft proof only; no ROM emitted" if args.draft_proof else report["output_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
