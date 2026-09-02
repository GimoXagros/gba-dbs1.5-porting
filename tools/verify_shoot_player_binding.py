#!/usr/bin/env python3
"""Verify v47 against native consumers, not only builder hashes/literals.

The bounded call-site recognizer recovers the fifteen actual pushed arguments
after Capstone decoding; it is not an ARM CPU interpreter. Unknown producer
shapes are errors. The real GBA constructor's stack loads determine the roles.
No emulator, object allocation, saved state, or supplied save is used.
"""

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

BEFORE_SHA256 = "034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC"
AFTER_SHA256 = "ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
PHASE = 0x5C1000
CODE_END = 0x5C1180
PHASE_END = 0x5C11A4
HP_VALUES = (30, 50, 20, 30, 20, 30, 20, 30, 50, 30, 30, 40, 30, 20, 30)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    if sha256(data) != expected:
        raise ValueError(f"{label}: unexpected hash {sha256(data)}")


def decode(data: bytes, start: int, end: int) -> list:
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    engine.detail = True
    instructions = list(engine.disasm(data[start:end], BASE + start))
    if sum(item.size for item in instructions) != end - start or any(item.size != 4 for item in instructions):
        raise ValueError(f"incomplete instruction population at {start:X}..{end:X}")
    return instructions


def word(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def literal_value(data: bytes, site: int) -> int:
    item = decode(data, site, site + 4)[0]
    if item.mnemonic != "ldr" or item.reg_name(item.operands[0].reg) != "r8" or item.reg_name(item.operands[1].mem.base) != "pc":
        raise ValueError(f"expected r8 PC-relative literal at {site:X}")
    target = site + 8 + item.operands[1].mem.disp
    if target & 3 or not 0 <= target <= len(data) - 4:
        raise ValueError("unaligned/out-of-range literal")
    return word(data, target)


def pushed_arguments(data: bytes, start: int, call: int) -> list[int | str]:
    """Recognize only the fixed retail/generated constructor producer shape."""
    pushed: list[int | str] = []
    producer: int | None = None
    for item in decode(data, start, call):
        text = f"{item.mnemonic} {item.op_str}"
        if text in ("str r5, [sp, #-4]!", "stmdb sp!, {r5}"):
            pushed.append("presentation")
        elif text == "stmdb sp!, {fp}":
            pushed.append(0)
        elif text in ("str r8, [sp, #-4]!", "stmdb sp!, {r8}"):
            if producer is None:
                raise ValueError("constructor pushes an unresolved value")
            pushed.append(producer)
        elif item.mnemonic == "ldr":
            producer = literal_value(data, item.address - BASE)
        elif item.mnemonic == "mov" and item.reg_name(item.operands[0].reg) == "r8":
            producer = item.operands[1].imm
        elif item.mnemonic == "orr" and item.op_str.startswith("r8, r8, #") and producer is not None:
            producer |= item.operands[2].imm
        else:
            raise ValueError(f"unrecognized constructor argument producer at {item.address:X}: {text}")
    call_item = decode(data, call, call + 4)[0]
    if call_item.mnemonic != "bl" or call_item.operands[0].imm != 0x080127E4 or len(pushed) != 15:
        raise ValueError("constructor call target/argument count changed")
    return list(reversed(pushed))


def check_constructor(data: bytes, start: int, call: int, resources: tuple[int, int, int], tile: int, slot: int) -> dict:
    arguments = pushed_arguments(data, start, call)
    p1, p0, p2 = resources
    # These entry-SP offsets are proved independently from 080127E4's loads.
    expected = [slot, tile, 0x1800, 0x4000, 0, 0, p2, 0, 0, p0, 0, 0, p1, 0, "presentation"]
    if arguments != expected:
        raise ValueError(f"constructor at {call:X}: actual stack resource roles differ")
    return {"call": BASE + call, "entry_sp_arguments": arguments,
            "p1_to_presentation_44": arguments[12], "p0_to_presentation_48": arguments[9],
            "p2_to_presentation_4c": arguments[6]}


def check_aux_links(data: bytes) -> None:
    if literal_value(data, 0x5BC294) != 0x030048A0 or literal_value(data, 0x5BC2A0) != 0x0300489C:
        raise ValueError("auxiliary primary/secondary player slots are reversed")
    if tuple(word(data, site) for site in (0x5BC298, 0x5BC29C, 0x5BC2A4, 0x5BC2A8, 0x5BC380)) != (
        0xE5986000, 0xE5846028, 0xE5987000, 0xE5847018, 0xE5864028
    ):
        raise ValueError("auxiliary pointer-load/link-store sequence changed")


def semantic_checks(data: bytes) -> list[dict]:
    reports = [
        check_constructor(data, 0x5B94B0, 0x5B951C, (0x085B9000, 0x085B9200, 0x085B9300), 0x1D1, 1),
        check_constructor(data, 0x5BC2C4, 0x5BC32C, (0x085D029C, 0x085D1100, 0x085DB700), 0x99, 3),
        check_constructor(data, 0x5C10B4, 0x5C111C, (0x085D0000, 0x085D1000, 0x085B9300), 0x1F1, 1),
    ]
    check_aux_links(data)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    before, after = args.before.read_bytes(), args.after.read_bytes()
    gba, wsc10, wsc15 = args.gba.read_bytes(), args.wsc10.read_bytes(), args.wsc15.read_bytes()
    for data, digest, label in ((before, BEFORE_SHA256, "v46"), (after, AFTER_SHA256, "v47"),
                                (gba, GBA_SHA256, "GBA"), (wsc10, WSC10_SHA256, "WSC10"), (wsc15, WSC15_SHA256, "WSC15")):
        require_hash(data, digest, label)
    if len(before) != len(after) or len(after) != 0x800000:
        raise ValueError("ROM length changed")

    # Recover roles from the real consumer, independent of both port builders.
    consumer = decode(gba, 0x127E4, 0x1285C)
    observed = [(i.mnemonic, i.op_str) for i in consumer[:8]]
    if observed != [
        ("push", "{r0, r3, r4, r5}"), ("ldr", "r5, [sp, #0x48]"),
        ("ldr", "r0, [sp, #0x40]"), ("str", "r0, [r5, #0x44]"),
        ("ldr", "r0, [sp, #0x34]"), ("str", "r0, [r5, #0x48]"),
        ("ldr", "r0, [sp, #0x28]"), ("str", "r0, [r5, #0x4c]"),
    ]:
        raise ValueError("native constructor resource-consumer mapping changed")
    commercial = check_constructor(gba, 0x372810, 0x372868, (0x08350248, 0x083505E8, 0x08352240), 0x99, 0)
    # Exact commercial P1/P0/P2 conversion lineage is separately checked by
    # the existing main build's Shoot resource conversion, not reimplemented.
    if wsc10[0x396417:0x396446] != bytes.fromhex(
        "6A 00 68 99 00 68 00 18 68 00 40 68 EB 00 68 C0 25 68 00 00 "
        "68 EA 00 68 91 2D 68 00 00 68 EA 00 68 18 2E 68 00 00 68 00 0C "
        "57 9A 14 24 B2 96"
    ):
        raise ValueError("WSC10 constructor lineage changed")
    if wsc15[0x747AD1:0x747AE1] != bytes.fromhex("26 8B 36 5E 06 89 76 FA 26 8B 3E 5C 06 89 7E F8"):
        raise ValueError("source active/other assignment changed")
    if wsc15[0x747C0F:0x747C1B] != bytes.fromhex("8B 46 FA 89 44 1C 8B 46 F8 89 44 14"):
        raise ValueError("source auxiliary primary/secondary link changed")
    if wsc15[0x747C88:0x747C94] != bytes.fromhex("8B 76 FA 89 44 1C 8B 46 F8 89 44 14"):
        raise ValueError("source active player back-links changed")
    if struct.unpack_from("<III", gba, 0x37005C) != (0x030048A0, 0x0300489C, 0x03002310):
        raise ValueError("commercial player/difficulty literals changed")
    if (literal_value(after, 0x5C1004), literal_value(after, 0x5C100C), literal_value(after, 0x5C1034)) != (
        0x030048A0, 0x0300489C, 0x03002310
    ):
        raise ValueError("new phase active/other/difficulty binding changed")

    calls = semantic_checks(after)
    # Reproduce all three original defects without relying on a failed hash.
    defects = []
    for label, check in (
        ("v46 child P1/P2 inversion", lambda: check_constructor(before, 0x5B94B0, 0x5B951C, (0x085B9000, 0x085B9200, 0x085B9300), 0x1D1, 1)),
        ("v46 auxiliary P1/P2 inversion", lambda: check_constructor(before, 0x5BC2C4, 0x5BC32C, (0x085D029C, 0x085D1100, 0x085DB700), 0x99, 3)),
        ("v46 auxiliary active/other inversion", lambda: check_aux_links(before)),
    ):
        try:
            check()
        except ValueError as error:
            defects.append({"case": label, "detected": str(error)})
        else:
            raise ValueError(f"original defect was not detected: {label}")

    correction_sites = (0x5B94BC, 0x5B94E4, 0x5BC2D0, 0x5BC2F8, 0x5BC398, 0x5BC39C)
    rejected = []
    for site in correction_sites:
        mutated = bytearray(after)
        mutated[site:site + 4] = before[site:site + 4]
        try:
            semantic_checks(mutated)
        except ValueError:
            rejected.append(site)
        else:
            raise ValueError(f"semantic check accepts reverted correction at {site:X}")

    # Full native HP block: unsigned difficulty >=2, an additional quarter
    # only at difficulty 3, and logical half/quarter thresholds. Each source
    # instruction lives in the guarded source initializer, not a guessed table.
    hp_instructions = [(i.mnemonic, i.op_str) for i in decode(after, 0x5C1038, 0x5C106C)]
    if hp_instructions != [
        ("ldrb", "r3, [r8, #0xf]"), ("cmp", "r3, #0"), ("subeq", "r1, r1, r2"),
        ("beq", "#0x85c1058"), ("cmp", "r3, #2"), ("addhs", "r1, r1, r2"),
        ("cmp", "r3, #3"), ("addeq", "r1, r1, r2"), ("strh", "r1, [r4, #0x64]"),
        ("lsr", "r0, r1, #1"), ("strh", "r0, [r4, #0x68]"),
        ("lsr", "r0, r0, #1"), ("strh", "r0, [r4, #0x6a]"),
    ]:
        raise ValueError("source HP difficulty/threshold semantics changed")
    hp_data = struct.pack("<15H", *HP_VALUES)
    if after[0x5C1400:0x5C141E] != hp_data or wsc15[0x747E54:0x747E72] != hp_data:
        raise ValueError("source 15-entry HP population changed")
    if literal_value(after, 0x5C1028) != 0x085C1400 or word(after, 0x5C102C) != 0xE19810B0:
        raise ValueError("HP halfword lookup does not reach the installed table")
    for site, expected in (
        (0x5C1030, 0xE1A02141), (0x5C107C, 0xE3C88B2F),
        (0x5C1070, 0xE1C494BE), (0x5C1074, 0xE1C495B0),
        (0x5C1084, 0xE1C493B4), (0x5C1088, 0xE1C493B6),
        (0x5C108C, 0xE1C494B2), (0x5C1090, 0xE1C494B4),
        (0x5C1094, 0xE1C494B6), (0x5C1098, 0xE1C494B8),
        (0x5C10A0, 0xE1C495B2), (0x5C10A4, 0xE1C495B4),
        (0x5C10AC, 0xE5848000), (0x5C1174, 0xE5847018),
        (0x5C1000, 0xE92D5FFF), (0x5C1178, 0xE8BD5FFF), (0x5C117C, 0xE12FFF1E),
    ):
        if word(after, site) != expected:
            raise ValueError(f"player field/ABI safeguard changed at {site:X}")
    if literal_value(after, 0x5C10A8) != 0x085BC800 or literal_value(after, 0x5C1148) != 0x085B9300 or literal_value(after, 0x5BC358) != 0x085DB700:
        raise ValueError("callback/direct palette load was changed by constructor correction")
    reuse = decode(after, 0x5C1300, 0x5C1308)
    if word(after, 0x5C1300) != 0xE92D40FF or reuse[1].mnemonic != "b" or reuse[1].operands[0].imm != 0x085BC244:
        raise ValueError("reuse entry does not skip the native allocation call")
    if word(after, 0x5BC384) != 0xE8BD40FF or word(after, 0x5BC388) != 0xE12FFF1E:
        raise ValueError("reuse entry and existing return no longer have matching stack frames")

    placements = ((PHASE, PHASE_END, "AEF73AB400F8B6611201CBAF3F24E19693D62BA7D84976A8479FFA33A46D2843"),
                  (0x5C1300, 0x5C1308, "57DC8F64037C3351974AD77B27E4300F2149CE6B7FDA13F8CA9B9985163EB9FD"),
                  (0x5C1400, 0x5C141E, "F19BB19802488BA10E6948937E946AF4385760BF7E88CE4FBDC4A7006346B98E"))
    allowed = {site + i for site in correction_sites for i in range(4)}
    for start, end, digest in placements:
        require_hash(after[start:end], digest, f"placement {start:X}")
        if before[start:end] != b"\xff" * (end - start):
            raise ValueError("placement did not originate in unused expansion")
        allowed.update(range(start, end))
    actual = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if len(actual) != 459 or not actual <= allowed:
        raise ValueError("v47 changed-byte population escapes the declared nine writes")
    phase_code = decode(after, PHASE, CODE_END)
    native_calls = [i.operands[0].imm for i in phase_code if i.mnemonic == "bl"]
    if native_calls != [0x080127E4, 0x08012874, 0x080132EC, 0x085C1300]:
        raise ValueError("phase native-call graph changed")
    entry_references = []
    for site in range(0, len(after) - 3, 4):
        value = word(after, site)
        if value == BASE + PHASE:
            entry_references.append(site)
        if value & 0x0E000000 == 0x0A000000:
            displacement = value & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            if site + 8 + displacement * 4 == PHASE:
                entry_references.append(site)
    if entry_references:
        raise ValueError("phase unexpectedly acquired a menu/controller caller")
    report = {
        "schema": 1, "kind": "shoot-player-binding-consumer-verification",
        "input_sha256": BEFORE_SHA256, "output_sha256": AFTER_SHA256,
        "consumer": {"entry": 0x080127E4, "entry_sp_offsets": [48, 36, 24], "destination_offsets": [68, 72, 76]},
        "commercial_constructor": commercial, "installed_constructors": calls,
        "source_player_mapping": {"ES:065E": 0x030048A0, "ES:065C": 0x0300489C},
        "old_defects_reproduced": defects, "individually_reverted_corrections_rejected": rejected,
        "player_phase": {"address": BASE + PHASE, "source_code_bytes": 0x7394 - 0x71D1,
                         "native_code_bytes": CODE_END - PHASE, "native_instructions": len(phase_code),
                         "literal_bytes": PHASE_END - CODE_END, "calls": native_calls,
                         "hp_values": HP_VALUES, "requires_existing_objects": True, "external_callers": entry_references},
        "aux_reuse": {"entry": 0x085C1300, "body": 0x085BC244, "allocator_is_bypassed": True},
        "actual_changed_bytes": len(actual), "original_rom_and_supplied_save_written": False,
        "claim_scope": "static native-consumer/argument/link/HP/diff verification and negative regression checks only; no normal-play reachability, runtime, visuals, audio, or supplied-save QA",
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
