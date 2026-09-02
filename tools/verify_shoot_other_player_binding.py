#!/usr/bin/env python3
"""Independently check the v49 initializer phase and its native consumers.

No builder imports, CPU model, emulator, saved state, or supplied save. Fixed
instruction populations are decoded with Capstone. Semantic negative cases
are rejected before any output hash check, so a manifest cannot certify a
wrong argument order, narrow physics pointer, or palette-copy extent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

BEFORE = "11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E"
AFTER = "93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ENTRY, CODE_END, END = 0x5C1500, 0x5C1608, 0x5C1614
BASE = 0x08000000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def word(data: bytes, site: int) -> int:
    return struct.unpack_from("<I", data, site)[0]


def decode(data: bytes, start: int, end: int, x86: bool = False) -> list:
    engine = Cs(CS_ARCH_X86 if x86 else CS_ARCH_ARM, CS_MODE_16 if x86 else CS_MODE_ARM)
    engine.detail = True
    result = list(engine.disasm(data[start:end], start if x86 else BASE + start))
    if sum(i.size for i in result) != end - start:
        raise ValueError(f"incomplete instruction population at {start:X}")
    return result


def sequence(data: bytes, start: int, end: int, expected: list[str], x86: bool = False) -> None:
    actual = [f"{i.mnemonic} {i.op_str}".strip() for i in decode(data, start, end, x86)]
    if actual != expected:
        raise ValueError(f"consumer/phase semantics differ at {start:X}: {actual}")


def literal(data: bytes, site: int, expected: int) -> None:
    i = decode(data, site, site + 4)[0]
    if i.mnemonic != "ldr" or i.reg_name(i.operands[1].mem.base) != "pc":
        raise ValueError("not a PC-relative literal load")
    target = site + 8 + i.operands[1].mem.disp
    if word(data, target) != expected:
        raise ValueError(f"literal target differs at {site:X}")


def check_record(actual: bytes, source: bytes, label: str) -> None:
    """Independent field oracle, checked over all 660 retail halfwords first."""
    if len(actual) != 120 or len(source) != 120:
        raise ValueError("truncated physics record")
    for index, (observed, original) in enumerate(zip(struct.unpack("<60h", actual),
                                                   struct.unpack("<60h", source), strict=True)):
        field = index % 20
        if field in (0, 1, 2, 5, 6, 10):
            numerator, denominator = 5, 4
        elif field in (3, 4, 7, 9, 11, 12, 13, 14):
            numerator, denominator = 25, 16
        elif field == 8:
            numerator, denominator = 4, 5
        else:
            numerator, denominator = 1, 1
        expected = (abs(original) * numerator // denominator) * (-1 if original < 0 else 1)
        if field == 2 and original == -804:
            expected = -1011
        if observed != expected:
            raise ValueError(f"{label} field {index}: observed {observed}, expected {expected}")


def check_physics(data: bytes, gba: bytes, wsc: bytes) -> list[dict]:
    for character in range(11):
        source = wsc[0x3B847E + character * 120:0x3B847E + (character + 1) * 120]
        retail = gba[0x353508 + character * 120:0x353508 + (character + 1) * 120]
        check_record(retail, source, f"retail {character}")
    records = []
    for character in range(15):
        pointer = word(data, 0x485000 + character * 4)
        expected = (0x08353508 + character * 0x78) if character < 12 else (0x084850B4 + (character - 12) * 0x78)
        if pointer != expected:
            raise ValueError(f"unexpected expanded physics pointer for {character}")
        start = pointer - BASE
        source = wsc[0x3B847E + character * 120:0x3B847E + (character + 1) * 120]
        actual = data[start:start + 120]
        if character >= 12:
            check_record(actual, source, f"installed {character}")
        elif actual != gba[start:start + 120]:
            raise ValueError("retail physics record changed")
        bounds = struct.unpack_from("<hh", actual, 0x24)
        if bounds != struct.unpack_from("<hh", source, 0x24):
            raise ValueError(f"base-form bounds differ for {character}")
        records.append({"character": character, "base_pointer": pointer, "bounds": bounds,
                        "payload_sha256": digest(actual)})
    return records


def check_phase(data: bytes) -> None:
    sequence(data, ENTRY, 0x5C1544, [
        "push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}",
        "ldr r8, [pc, #0xfc]", "ldr r4, [r8]", "ldrh r8, [r4, #8]",
        "tst r8, #0x4000", "beq #0x85c15b4", "bic r8, r8, #0x4000",
        "strh r8, [r4, #8]", "ldrb r0, [r4, #0x10]", "ldrb r3, [r4, #0x11]",
        "str r0, [sp, #-4]!", "str r3, [sp, #-4]!", "mov r8, #0",
        "str r8, [sp, #-4]!", "mov fp, #0", "bl #0x8353304", "add sp, sp, #0xc",
    ])
    sequence(data, 0x5C1544, 0x5C157C, [
        "ldr r0, [pc, #0xc0]", "ldr r1, [pc, #0xc0]", "mov r2, #0x10",
        "ldrh r3, [r0], #2", "strh r3, [r1], #2", "subs r2, r2, #1", "bne #0x85c1550",
        "add r0, r0, #0x60", "add r1, r1, #0x60", "mov r2, #0x10",
        "ldrh r3, [r0], #2", "strh r3, [r1], #2", "subs r2, r2, #1", "bne #0x85c156c",
    ])
    sequence(data, 0x5C157C, 0x5C15B4, [
        "add r5, r4, #0xac", "str r5, [sp, #-4]!", "mov r8, #0",
        "str r8, [sp, #-4]!", "str r8, [sp, #-4]!", "bl #0x8012874", "add sp, sp, #0xc",
        "ldr r8, [r4, #0x60]", "sub r8, r8, #0x50", "str r8, [r4, #0x60]",
        "ldrsh r0, [r8, #0x24]", "ldrsh r3, [r8, #0x26]",
        "strh r0, [r4, #0x52]", "strh r3, [r4, #0x54]",
    ])
    sequence(data, 0x5C15B4, CODE_END, [
        "mov r8, #0x60", "strh r8, [r4, #0x6a]", "mov r8, #0xe700", "strh r8, [r4, #4]",
        "mov r8, #0x40", "strh r8, [r4, #6]", "mov r8, #0", "strh r8, [r4, #8]",
        "strh r8, [r4, #0xa]", "add r5, r4, #0xac", "ldrh r8, [r5, #8]",
        "bic r8, r8, #0x4000", "strh r8, [r5, #8]", "mov r8, #0xe00",
        "strh r8, [r4, #0x34]", "strh r8, [r4, #0x38]", "mvn r8, #0x7f",
        "strh r8, [r4, #0x36]", "strh r8, [r4, #0x3a]",
        "pop {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}", "bx lr",
    ])
    literal(data, 0x5C1504, 0x0300489C)
    literal(data, 0x5C1544, 0x05000200)
    literal(data, 0x5C1548, 0x0203E200)


def check_consumers(gba: bytes, wsc: bytes, after: bytes) -> list[dict]:
    sequence(gba, 0x3530CC, 0x3530E4, [
        "ldr r1, [r8, r1, lsl #2]", "str r1, [r4, #0x60]",
        "ldrsh r0, [r1, #0x24]", "strh r0, [r4, #0x52]",
        "ldrsh r0, [r1, #0x26]", "strh r0, [r4, #0x54]",
    ])
    sequence(gba, 0x35A6E8, 0x35A704, [
        "ldr r8, [r4, #0x60]", "sub r8, r8, #0x50", "str r8, [r4, #0x60]",
        "ldr r1, [r4, #0x60]", "ldrsh r0, [r1, #0x24]", "ldrsh r3, [r1, #0x26]",
        "strh r0, [r4, #0x52]",
    ])
    sequence(gba, 0x35A730, 0x35A750, [
        "ldrb r0, [r4, #0x10]", "ldrb r3, [r4, #0x11]",
        "stmdb sp!, {r0}", "stmdb sp!, {r3}", "mov r8, #0", "stmdb sp!, {r8}",
        "bl #0x8353304", "add sp, sp, #0xc",
    ])
    sequence(wsc, 0x74368E, 0x7436A4, [
        "mov ax, word ptr cs:[bx + 0x2924]", "mov word ptr [si + 0x26], ax",
        "mov word ptr [si + 0x2a], ax", "mov ax, word ptr cs:[bx + 0x2926]",
        "mov word ptr [si + 0x28], ax", "mov word ptr [si + 0x2c], ax",
    ], True)
    sequence(gba, 0x353174, 0x353190, [
        "ldrh r0, [r1, sb]", "strh r0, [r4, #0x34]", "strh r0, [r4, #0x38]",
        "add sb, r8, #2", "ldrh r0, [r1, sb]", "strh r0, [r4, #0x36]", "strh r0, [r4, #0x3a]",
    ])
    # Actual DMA producer owns OBJ mirror E200..E300, not a guessed free RAM gap.
    sequence(gba, 0x33FDD0, 0x33FE14, [
        "mov r8, #0x4000000", "mov sb, #0x5000000", "str sb, [r8, #0xd4]",
        "ldr sl, [pc, #0x34]", "str sl, [r8, #0xd8]", "mov fp, #0x78",
        "strh fp, [r8, #0xdc]", "mov ip, #0x8400", "strh ip, [r8, #0xde]",
        "add sb, sb, #0x200", "str sb, [r8, #0xd4]", "add sl, sl, #0x200",
        "str sl, [r8, #0xd8]", "mov fp, #0x40", "strh fp, [r8, #0xdc]",
        "strh ip, [r8, #0xde]", "bx lr",
    ])
    literal(gba, 0x33FDDC, 0x0203E000)
    sequence(gba, 0x13308, 0x13328, [
        "ldrh r8, [r4], #4", "sub r8, r8, #8", "ldr r5, [sp, #0x10]",
        "add r5, r5, r8", "add r5, r5, #0x10", "lsl r5, r5, #5",
        "add r5, r5, #0x5000000", "add r5, r5, #2",
    ])
    if digest(wsc[0x747CF0:0x747DA2]) != "993C6E36E3700166E7C837D0E7FC82C1EAC4B497D28D98BB558612EF187B9FA8":
        raise ValueError("source restoration phase changed")
    if word(after, 0x3532FC) != 0x08485000 or word(after, 0x353324) != 0xE359000F:
        raise ValueError("expanded native physics/character consumers are absent")
    return check_physics(after, gba, wsc)


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    before, after, gba, wsc = (getattr(args, key).read_bytes() for key in ("before", "after", "gba", "wsc15"))
    for data, expected in ((before, BEFORE), (gba, GBA), (wsc, WSC15)):
        if digest(data) != expected:
            raise ValueError("input ROM identity mismatch")
    check_phase(after)
    records = check_consumers(gba, wsc, after)
    negatives = []
    for label, site, value in (
        ("wrong other player", 0x5C1608, 0x030048A0),
        ("wrong OBJ hardware bank", 0x5C160C, 0x05000100),
        ("wrong palette mirror bank", 0x5C1610, 0x0203E100),
        ("partial palette row", 0x5C154C, 0xE3A0200F),
        ("wrong second row stride", 0x5C1560, 0xE2800080),
        ("narrow physics pointer", 0x5C1598, 0xE1D486B0),
        ("wrong physics form", 0x5C159C, 0xE2488028),
        ("wrong previous X", 0x5C15F0, 0xE1C483BA),
        ("reversed constructor argument", 0x5C1528, 0xE52D3004),
        ("unset native zero register", 0x5C1538, 0xE1A0B00B),
        ("restoration not conditionally skipped", 0x5C1514, 0xE1A00000),
    ):
        changed = bytearray(after)
        struct.pack_into("<I", changed, site, value)
        try:
            check_phase(changed)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"semantic negative was accepted: {label}")
    old_record_failures = []
    for character in (12, 13, 14):
        site = 0x485000 + character * 4
        old_pointer = word(before, site)
        start = old_pointer - BASE
        source = wsc[0x3B847E + character * 120:0x3B847E + (character + 1) * 120]
        try:
            check_record(before[start:start + 120], source, f"old ID {character}")
        except ValueError as error:
            old_record_failures.append({"character": character, "old_pointer": old_pointer, "failure": str(error)})
        else:
            raise ValueError("historical physics defect was not reproduced")
        mutated = bytearray(after)
        mutated[site:site + 4] = before[site:site + 4]
        try:
            check_physics(mutated, gba, wsc)
        except ValueError:
            negatives.append(f"reverted physics pointer {character}")
        else:
            raise ValueError("reverted physics pointer accepted")
    if digest(after) != AFTER or len(before) != len(after) or len(after) != 0x800000:
        raise ValueError("candidate identity/size mismatch")
    changed_bytes = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    allowed = set(range(ENTRY, END)) | set(range(0x485030, 0x48503C))
    if not changed_bytes or not set(changed_bytes) <= allowed or before[ENTRY:END] != b"\xff" * (END - ENTRY):
        raise ValueError("candidate diff exceeds the four Expected Writes")
    # No external initializer route may reach this phase until its full caller
    # contract, palette transition and controller have been installed together.
    refs = []
    for site in range(0, len(after), 4):
        value = word(after, site)
        if value == BASE + ENTRY:
            refs.append(site)
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if site + 8 + delta * 4 == ENTRY:
                refs.append(site)
    if refs:
        raise ValueError("other-player phase unexpectedly acquired a caller")
    report = {
        "schema": 1, "kind": "shoot-other-player-native-consumer-verification",
        "input_sha256": BEFORE, "output_sha256": AFTER,
        "source_code_bytes": 0xB2, "native_entry": BASE + ENTRY,
        "native_instructions": len(decode(after, ENTRY, CODE_END)), "literal_bytes": END - CODE_END,
        "native_calls": [0x08353304, 0x08012874],
        "character_call_entry_sp": ["form=0", "character=object+11", "slot=object+10"],
        "palette_copies": [
            {"hardware_start": 0x05000200, "mirror_start": 0x0203E200, "bytes": 32},
            {"hardware_start": 0x05000280, "mirror_start": 0x0203E280, "bytes": 32},
        ],
        "physics_pointer_bytes": 4, "physics_pointer_field": 0x60,
        "verified_base_form_records": records, "negative_regressions_rejected": negatives,
        "retail_conversion_oracle_halfwords": 660, "added_record_halfwords": 180,
        "old_physics_payload_failures": old_record_failures,
        "actual_changed_bytes": len(changed_bytes), "external_callers": refs,
        "claim_scope": "static whole-phase instruction, native consumer, palette extent, fifteen-record bounds, three full added physics records, historical defect reproduction and diff checks; no caller/lifetime proof, complete initializer, menu/controller entry or runtime/save QA",
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
