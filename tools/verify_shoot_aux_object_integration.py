#!/usr/bin/env python3
"""Independently verify the resident Shoot auxiliary-object component."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore


INPUT_SHA256 = "000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB"
OUTPUT_SHA256 = "C8C3AF5DABBE7CCE9F0D124DDEEF3CD6348FCDB085416DBA5E78C65DD5BFB3B4"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OWNERSHIP_START = 0x5BC100
OWNERSHIP_END = 0x5BC700
CONSTRUCTOR = 0x5BC200
CONSTRUCTOR_BYTES = 436
CONSTRUCTOR_SHA256 = "49D24F0D03A38A935E6FC9FA1AA0D43AFEB4EEAA9BFE7CC50FAD5A076422DC9E"
IDLE = 0x5BC600
IDLE_BYTES = bytes.fromhex("1E FF 2F E1")

EXPECTED_CALLS = [0x08352374, 0x080127E4, 0x08012874, 0x080132EC]
EXPECTED_LITERALS = [
    0x03004D3C,
    0x083703EC,
    0x00000343,
    0x0300489C,
    0x030048A0,
    0xFFFFFB00,
    0x085BC600,
    0x085D029C,
    0x085D1100,
    0x085DB700,
]
RESOURCE_SPECS = (
    (0x5D029C, 1968, "5DDE469264E235121F519CCB4DD11D21AB964708941E50F5D3CE93FB6667CE3D", "rules P1"),
    (0x5D1100, 41408, "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91", "rules P0"),
    (0x5DB700, 40, "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD", "rules P2"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def arm_branch_target(address: int, word: int) -> int:
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def aligned_occurrences(data: bytes, value: int) -> list[int]:
    encoded = struct.pack("<I", value)
    return [offset for offset in range(0, len(data) - 3, 4) if data[offset:offset + 4] == encoded]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, INPUT_SHA256, "v44 input")
    require_hash(after, OUTPUT_SHA256, "v45 output")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    if before[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (OWNERSHIP_END - OWNERSHIP_START):
        raise SystemExit("v44 ownership window was not blank")
    constructor = after[CONSTRUCTOR:CONSTRUCTOR + CONSTRUCTOR_BYTES]
    require_hash(constructor, CONSTRUCTOR_SHA256, "auxiliary constructor")
    if after[IDLE:IDLE + 4] != IDLE_BYTES:
        raise SystemExit("translated 88F6 idle callback is not BX LR")

    expected_changed = {
        index
        for start, end in ((CONSTRUCTOR, CONSTRUCTOR + CONSTRUCTOR_BYTES), (IDLE, IDLE + 4))
        for index in range(start, end)
        if before[index] != after[index]
    }
    actual_changed = {index for index, pair in enumerate(zip(before, after)) if pair[0] != pair[1]}
    if actual_changed != expected_changed:
        raise SystemExit("v45 writes escape the two declared placements")
    if len(actual_changed) != 434:
        raise SystemExit(f"changed-byte count changed: {len(actual_changed)}")

    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    instructions = list(engine.disasm(constructor, GBA_BASE + CONSTRUCTOR))
    calls = []
    for instruction in instructions:
        if instruction.mnemonic != "bl":
            continue
        word = struct.unpack_from("<I", instruction.bytes)[0]
        calls.append(arm_branch_target(instruction.address, word))
    if calls != EXPECTED_CALLS:
        raise SystemExit(f"native call population changed: {calls}")

    literal_start = CONSTRUCTOR_BYTES - len(EXPECTED_LITERALS) * 4
    actual_literals = list(struct.unpack_from(f"<{len(EXPECTED_LITERALS)}I", constructor, literal_start))
    if actual_literals != EXPECTED_LITERALS:
        raise SystemExit(f"constructor literal table changed: {actual_literals}")

    mnemonics = [instruction.mnemonic for instruction in instructions]
    if mnemonics.count("strh") < 11 or mnemonics.count("str") < 7:
        raise SystemExit("constructor lost required object/presentation field stores")
    required_words = {
        0xE1C494B2,  # velocity +42
        0xE1C494B4,  # velocity +44
        0xE1C495B2,  # bound +52
        0xE1C495B4,  # bound +54
        0xE5846028,  # primary link
        0xE5847018,  # secondary link
        0xE5864028,  # link object back into active player
        0xE5848000,  # translated 88F6 callback store
    }
    words = {struct.unpack_from("<I", constructor, offset)[0] for offset in range(0, len(constructor), 4)}
    if not required_words <= words:
        raise SystemExit(f"constructor field-store signature changed: {required_words - words}")

    for offset, size, digest, label in RESOURCE_SPECS:
        require_hash(after[offset:offset + size], digest, label)
        if before[offset:offset + size] != after[offset:offset + size]:
            raise SystemExit(f"v45 changed preinstalled {label}")

    constructor_refs = aligned_occurrences(after, GBA_BASE + CONSTRUCTOR)
    idle_refs = aligned_occurrences(after, GBA_BASE + IDLE)
    if constructor_refs:
        raise SystemExit(f"constructor unexpectedly gained a caller: {constructor_refs}")
    if idle_refs != [CONSTRUCTOR + literal_start + 6 * 4]:
        raise SystemExit(f"idle callback pointer population changed: {idle_refs}")

    if wsc10[0x394971:0x394989] != bytes.fromhex(
        "6A 05 6A 00 68 43 03 68 70 90 68 BE 45 68 00 10 68 A2 06 9A 66 16 70 90"
    ):
        raise SystemExit("WSC 1.0 commercial lineage call changed")
    if wsc15[0x7456C5:0x7456DD] != bytes.fromhex(
        "6A 05 6A 00 68 43 03 68 90 40 68 34 51 68 00 10 68 1E 07 9A 2A 17 90 40"
    ):
        raise SystemExit("WSC 1.5 auxiliary allocation call changed")
    if struct.unpack_from("<I", gba, 0x37008C)[0] != 0x03004D3C:
        raise SystemExit("commercial GBA object-slot lineage changed")

    report = {
        "schema": 1,
        "kind": "shoot-auxiliary-object-independent-verification",
        "input_sha256": INPUT_SHA256,
        "output_sha256": OUTPUT_SHA256,
        "constructor": {
            "address": GBA_BASE + CONSTRUCTOR,
            "bytes": CONSTRUCTOR_BYTES,
            "sha256": CONSTRUCTOR_SHA256,
            "native_calls": calls,
            "literal_table": actual_literals,
            "external_callers": constructor_refs,
        },
        "idle_callback": {
            "address": GBA_BASE + IDLE,
            "bytes": 4,
            "sha256": sha256(IDLE_BYTES),
            "pointer_references": idle_refs,
        },
        "diff": {
            "changed_bytes": len(actual_changed),
            "contained_in_declared_placements": True,
        },
        "proved": [
            "exact WSC 1.0/WSC 1.5 ID-0343 pool-5 allocation lineage",
            "native GBA pointer slot 03004D3C and callback 083703EC",
            "exact converted Shoot rules P1/P0/P2 references",
            "native allocator, constructor, event, and P2-loader call targets",
            "object fields, links, position, presentation flags, and idle callback",
            "resident component remains unconnected to menu/stage route",
        ],
        "runtime_or_save_used": False,
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
