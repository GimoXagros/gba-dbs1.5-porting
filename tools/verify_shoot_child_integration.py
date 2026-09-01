#!/usr/bin/env python3
"""Independently verify the resident Shoot generator/child callback chain."""

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


INPUT_SHA256 = "4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C"
OUTPUT_SHA256 = "35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

PLACEMENTS = {
    "generator_9229": (0x5B9400, 420, "A3A8103CF0E20334F0B3B5189C5BA082F4596D306A07D2ADE492C1CA665FEA60"),
    "callback_94C1": (0x5B9800, 324, "2F1CAA67C063C861ACBCFA63929819DF7A8CC9F273AF05B0924E6F0E5CE4211D"),
    "callback_9570": (0x5B9C00, 300, "98A88B39878D9D2FBB34624A68F5E691C499E7B11AC6A67B084071446383B924"),
    "callback_9617": (0x5BA000, 100, "57AB76D9D28313DF1F0CA183350679BEA57107A79BD45E1B5BFB9528D36E769C"),
}
CODE_BYTES = {
    "generator_9229": 0x180,
    "callback_94C1": 0x140,
    "callback_9570": 0x128,
    "callback_9617": 0x60,
}
EXPECTED_CALLS = {
    "generator_9229": [0x08352374, 0x080127E4, 0x08012874, 0x080D15C0],
    "callback_94C1": [0x08012560, 0x0801233C, 0x08012348, 0x08012874, 0x08012A84],
    "callback_9570": [0x08012560, 0x0801233C, 0x08012348, 0x08012A84, 0x08012874],
    "callback_9617": [0x08012A84, 0x083524C4],
}
AUDIO_REQUEST_OFFSET = 0x5B9560
AUDIO_REQUEST_WORDS = (0xE3A0804A, 0xE3A09001, 0xE3A0A000)
WSC_RANGES = {
    "generator_9229": (0x749B29, 0x749C3B, "51F802FADB6AFD59D77DE51189CBA0124D814BA531A1E93C7EFEAD8B59622E69"),
    "callback_94C1": (0x749DC1, 0x749E70, "CDB4D863FB669D8BB11564531CF3592F4F31688D63DF0CB1DC451CA7119F5572"),
    "callback_9570": (0x749E70, 0x749F17, "AE839141C3B6A7F2BFABA82E8AE1E27C6BD091D8C768B67EAB965F043024FA2D"),
    "callback_9617": (0x749F17, 0x749F6A, "F5D557B0C3D16B2ECB2DA97948E81C6568EEED89E47F69F8F91392B16F87A65E"),
}
GBA_ORACLE_RANGES = {
    "commercial_generator": (0x37273C, 0x372920, "7E087397E772C0293D458FBFEAB13FF3BC04DFD42D90F44AE453738C8CEF4B7C"),
    "commercial_callback_initial": (0x372110, 0x3721FC, "F72DFA2038E330EB0A8640F130B126C2CDB495399CDFAAE9530DE3BEE61BD460"),
    "commercial_callback_homing": (0x3721FC, 0x372320, "12C951CD935FDC2DFAC99F3A67E52B0010A45644E8B21A3433F61BC43A39938A"),
    "commercial_callback_complete": (0x372320, 0x3723D8, "B5E810B434A99459C8B0BDB5E64F69282B577755CBBF00A1EDE3BF85A82B6398"),
    "native_sound_request": (0x0D15C0, 0x0D15F0, "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"),
}


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


def disassemble_function(blob: bytes, address: int) -> tuple[list[dict[str, object]], list[int]]:
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    instructions = list(engine.disasm(blob, address))
    if sum(instruction.size for instruction in instructions) != len(blob):
        raise SystemExit(f"ARM disassembly does not cover 0x{address:08X}")
    forbidden = {"movw", "movt", "blx", "bxj", "ldrex", "strex", "clz"}
    bad = [instruction.mnemonic for instruction in instructions if instruction.mnemonic in forbidden]
    if bad:
        raise SystemExit(f"non-ARM7TDMI instruction in 0x{address:08X}: {bad}")
    calls = []
    rendered = []
    for instruction in instructions:
        word = struct.unpack("<I", instruction.bytes)[0]
        if word & 0x0F000000 == 0x0B000000:
            calls.append(arm_branch_target(instruction.address, word))
        rendered.append({
            "address": instruction.address,
            "mnemonic": instruction.mnemonic,
            "op_str": instruction.op_str,
        })
    return rendered, calls


def aligned_refs(data: bytes, start: int, end: int) -> list[tuple[int, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + start <= value < GBA_BASE + end:
            refs.append((offset, value))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    gba = args.gba.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, INPUT_SHA256, "v36 candidate")
    require_hash(after, OUTPUT_SHA256, "Shoot child candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != len(after) or len(after) != 0x800000:
        raise SystemExit("candidate size changed")
    for label, (start, end, digest) in WSC_RANGES.items():
        require_hash(wsc15[start:end], digest, label)
    for label, (start, end, digest) in GBA_ORACLE_RANGES.items():
        require_hash(gba[start:end], digest, label)

    allowed = set()
    functions = {}
    for label, (offset, size, digest) in PLACEMENTS.items():
        if before[offset:offset + size] != bytes([0xFF]) * size:
            raise SystemExit(f"{label} preimage is not blank")
        blob = after[offset:offset + size]
        require_hash(blob, digest, label)
        instructions, calls = disassemble_function(
            blob[:CODE_BYTES[label]], GBA_BASE + offset
        )
        if calls != EXPECTED_CALLS[label]:
            raise SystemExit(f"{label} call graph changed: {calls}")
        functions[label] = {
            "target": offset,
            "bytes": size,
            "code_bytes": CODE_BYTES[label],
            "literal_bytes": size - CODE_BYTES[label],
            "sha256": digest,
            "instruction_count": len(instructions),
            "call_targets": calls,
            "first_instruction": instructions[0],
            "last_instruction": instructions[-1],
        }
        allowed.update(range(offset, offset + size))
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("Shoot child layer has an unexplained diff")

    resource_refs = aligned_refs(after, 0x5B9000, 0x5B9328)
    code_refs_before = aligned_refs(before, 0x5B9400, 0x5BA400)
    code_refs_after = aligned_refs(after, 0x5B9400, 0x5BA400)
    expected_resource_refs = [
        (0x5B9594, 0x085B9000),
        (0x5B9598, 0x085B9200),
        (0x5B959C, 0x085B9300),
    ]
    expected_code_refs = [
        (0x5B95A0, 0x085B9800),
        (0x5B9940, 0x085B9C00),
        (0x5B9D28, 0x085BA000),
    ]
    if resource_refs[-3:] != expected_resource_refs:
        raise SystemExit(f"Shoot resource consumer pointers changed: {resource_refs}")
    if code_refs_before:
        raise SystemExit("v36 already references the Shoot child code window")
    if code_refs_after != expected_code_refs:
        raise SystemExit(f"Shoot callback pointer chain changed: {code_refs_after}")
    if struct.unpack_from("<III", after, AUDIO_REQUEST_OFFSET) != AUDIO_REQUEST_WORDS:
        raise SystemExit("Shoot generator sound-request arguments changed")
    audio_call_word = struct.unpack_from("<I", after, AUDIO_REQUEST_OFFSET + 12)[0]
    if arm_branch_target(GBA_BASE + AUDIO_REQUEST_OFFSET + 12, audio_call_word) != 0x080D15C0:
        raise SystemExit("Shoot generator sound-request target changed")

    result = {
        "schema": 1,
        "kind": "independent-shoot-child-integration-verification",
        "claim_scope": (
            "exact diff containment, ARM7TDMI final-placement disassembly, native "
            "call graph including the payload-proved A7-to-0x4A sound request, resource "
            "consumers, and internal callback chain; external entry, audible "
            "playback, and runtime reachability excluded"
        ),
        "before_sha256": INPUT_SHA256,
        "after_sha256": OUTPUT_SHA256,
        "changed_bytes": len(changed),
        "functions": functions,
        "resource_refs_from_child_layer": [
            {"offset": offset, "value": value} for offset, value in expected_resource_refs
        ],
        "code_refs_before": [],
        "code_refs_after": [
            {"offset": offset, "value": value} for offset, value in code_refs_after
        ],
        "external_entry_connected": False,
        "audio_request": {
            "offset": AUDIO_REQUEST_OFFSET,
            "target": 0x080D15C0,
            "wsc_sound_id": 0xA7,
            "exact_wsc_10_payload_id": 0xA5,
            "gba_sound_id": 0x4A,
            "request_type": 1,
            "third_argument": 0,
            "runtime_audibility_verified": False,
        },
        "known_exclusion": "external 9083/912A parent/controller connection",
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
