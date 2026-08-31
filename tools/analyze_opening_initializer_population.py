#!/usr/bin/env python3
"""Audit the initializer population previously attributed to the opening.

The counts are useful structural evidence, but they do not by themselves prove
that the WSC 1.5-only initializers are dispatched by the cold-boot opening.
This tool therefore reports topology and consumer signatures without assigning
the call sites to a runtime route.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import pathlib
import struct
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_X86, CS_MODE_16, Cs  # type: ignore


GBA_BASE = 0x08000000
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
EXPECTED_GBA_CALLS = (
    0x83B0C, 0x83F38, 0x84248, 0x84F08, 0x84F24, 0x84F40,
    0x851E4, 0x85574, 0x85A78, 0x85EB0, 0x85FD8, 0x86640,
    0x86EB4, 0x86F0C, 0x87060, 0x870B8, 0x871D4, 0x8722C,
)
EXPECTED_WSC10_CALLS = (
    0xCA55, 0xCD08, 0xCF7D, 0xD2B5, 0xD5D0, 0xD832,
    0xDA52, 0xDCE8, 0xE0A2, 0xE475, 0xE6C3, 0xE876,
    0xEA2F, 0xEC7A, 0xF108, 0xF32B, 0xF58D, 0xF7A6,
)
EXPECTED_WSC15_CALLS = (
    0x5FCA, 0x6285, 0x6502, 0x683A, 0x6B55, 0x6DB7,
    0x6FD3, 0x7346, 0x75F7, 0x78D2, 0x7C67, 0x7F1A,
    0x82D4, 0x86AB, 0x88F9, 0x8AAD, 0x8C66, 0x8EB1,
    0x94EA, 0x9717, 0x9979, 0x9B92, 0x9D9F, 0xA067,
)
WSC_CALLBACK_PROLOGUE = bytes.fromhex("50 51 52 53 56 57 06 1E")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_verified(path: pathlib.Path, expected: str) -> bytes:
    data = path.read_bytes()
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"unexpected SHA-256 for {path}: {actual}")
    return data


def arm_branch_target(address: int, word: int) -> int:
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    return address + 8 + immediate * 4


def find_arm_calls(data: bytes, target: int) -> list[int]:
    matches: list[int] = []
    for offset in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, offset)[0]
        if ((word >> 25) & 7) != 5 or not (word & 0x01000000):
            continue
        if arm_branch_target(GBA_BASE + offset, word) == target:
            matches.append(offset)
    return matches


def find_wsc_near_calls(bank: bytes, target: int) -> list[int]:
    matches: list[int] = []
    for address in range(0, len(bank) - 2):
        if bank[address] != 0xE8:
            continue
        displacement = struct.unpack_from("<h", bank, address + 1)[0]
        if (address + 3 + displacement) & 0xFFFF == target:
            matches.append(address)
    return matches


def callback_pair_before(bank: bytes, call: int) -> dict[str, int] | None:
    # mov word ptr [si], imm16; inc si; inc si; mov word ptr [si], imm16
    pattern_prefix = bytes.fromhex("C7 04")
    for start in range(max(0, call - 0x50), call - 9):
        if bank[start:start + 2] != pattern_prefix:
            continue
        if bank[start + 4:start + 8] != bytes.fromhex("46 46 C7 04"):
            continue
        return {
            "first": struct.unpack_from("<H", bank, start + 2)[0],
            "second": struct.unpack_from("<H", bank, start + 8)[0],
            "source_address": start,
        }
    return None


def function_start_before(bank: bytes, call: int) -> int:
    start = bank.rfind(WSC_CALLBACK_PROLOGUE, max(0, call - 0x600), call)
    if start < 0:
        raise ValueError(f"no callback prologue before call at {call:04X}")
    return start


def word_references(bank: bytes, target: int) -> list[int]:
    needle = struct.pack("<H", target)
    refs: list[int] = []
    cursor = 0
    while True:
        cursor = bank.find(needle, cursor)
        if cursor < 0:
            return refs
        refs.append(cursor)
        cursor += 1


def instruction_shape(bank: bytes, start: int, end: int) -> list[str]:
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    return [insn.mnemonic for insn in engine.disasm(bank[start:end], start)]


def wsc_population(
    data: bytes, bank_number: int, target: int, label: str
) -> dict[str, object]:
    bank_start = bank_number * 0x10000
    bank = data[bank_start:bank_start + 0x10000]
    calls = find_wsc_near_calls(bank, target)
    entries = []
    for call in calls:
        function_start = function_start_before(bank, call)
        entries.append({
            "cpu_address": call,
            "rom_offset": bank_start + call,
            "callback_function_start": function_start,
            "start_word_references_in_bank": word_references(bank, function_start),
            "callback_pair_before_call": callback_pair_before(bank, call),
            "_instruction_shape": instruction_shape(bank, function_start, call + 3),
        })
    routine = bank[target:target + 0xBB]
    return {
        "label": label,
        "bank": bank_number,
        "target_cpu_address": target,
        "call_count": len(calls),
        "candidate_pair_count": len(calls) // 2,
        "calls": entries,
        "routine_signature": {
            "sha256_first_0xBB_bytes": sha256(routine),
            "sets_display_flag_es_094a_8000": bytes.fromhex(
                "26 81 0E 4A 09 00 80"
            ) in routine,
            "reads_match_state_ds_0c00_si_390e": bytes.fromhex(
                "BE 00 0C 8E DE BE 0E 39"
            ) in routine,
            "object_setup_call_count": routine.count(bytes.fromhex("9A E0 4E")),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = read_verified(args.gba, GBA_SHA256)
    wsc10 = read_verified(args.wsc10, WSC10_SHA256)
    wsc15 = read_verified(args.wsc15, WSC15_SHA256)

    gba_target = 0x08088250
    gba_calls = find_arm_calls(gba, gba_target)
    result = {
        "schema": 1,
        "kind": "opening-initializer-population-audit",
        "sources": {
            "gba_usa": {"sha256": GBA_SHA256, "bytes": len(gba)},
            "wsc_10": {"sha256": WSC10_SHA256, "bytes": len(wsc10)},
            "wsc_15": {"sha256": WSC15_SHA256, "bytes": len(wsc15)},
        },
        "gba": {
            "consumer_address": gba_target,
            "call_count": len(gba_calls),
            "candidate_pair_count": len(gba_calls) // 2,
            "call_offsets": gba_calls,
        },
        "wsc_10": wsc_population(wsc10, 0x39, 0xFCDA, "WSC 1.0"),
        "wsc_15": wsc_population(wsc15, 0x75, 0xA62F, "WSC 1.5"),
        "observations": {
            "commercial_gba_matches_wsc_10_call_count": len(gba_calls) == 18,
            "wsc_15_additional_calls": 24 - 18,
            "wsc_15_additional_candidate_pairs": (24 - 18) // 2,
        },
        "claim_scope": (
            "The 18/18/24 topology and shared match/presentation signatures are "
            "confirmed. Candidate pair counts are arithmetic only. Static "
            "cold-boot dispatch and runtime reachability of the six WSC 1.5-only "
            "calls remain unproven."
        ),
    }

    correspondence = []
    wsc10_entries = result["wsc_10"]["calls"]  # type: ignore[index]
    wsc15_entries = result["wsc_15"]["calls"]  # type: ignore[index]
    for index, (old, new) in enumerate(zip(wsc10_entries, wsc15_entries)):
        score = difflib.SequenceMatcher(
            None, old["_instruction_shape"], new["_instruction_shape"]
        ).ratio()
        correspondence.append({
            "index": index,
            "wsc_10_function_start": old["callback_function_start"],
            "wsc_15_function_start": new["callback_function_start"],
            "pre_call_mnemonic_similarity": round(score, 6),
        })
    for entry in (*wsc10_entries, *wsc15_entries):
        entry["pre_call_instruction_count"] = len(entry.pop("_instruction_shape"))
    result["first_18_ordered_correspondence"] = correspondence

    if tuple(gba_calls) != EXPECTED_GBA_CALLS:
        raise ValueError(f"unexpected GBA call population: {gba_calls}")
    wsc10_calls = tuple(
        entry["cpu_address"] for entry in result["wsc_10"]["calls"]  # type: ignore[index]
    )
    if wsc10_calls != EXPECTED_WSC10_CALLS:
        raise ValueError(f"unexpected WSC 1.0 call population: {wsc10_calls}")
    wsc15_calls = tuple(
        entry["cpu_address"] for entry in result["wsc_15"]["calls"]  # type: ignore[index]
    )
    if wsc15_calls != EXPECTED_WSC15_CALLS:
        raise ValueError(f"unexpected WSC 1.5 call population: {wsc15_calls}")

    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
