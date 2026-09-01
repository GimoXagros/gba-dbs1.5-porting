#!/usr/bin/env python3
"""Recover the WSC 1.0 and 1.5 opening callback graphs statically."""

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


WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
PROLOGUE = bytes.fromhex("50 51 52 53 56 57 06 1E")
CALLBACK_STORE_PREFIX = bytes.fromhex("A1 08 00 8B D8 B8")
CALLBACK_STORE_MIDDLE = bytes.fromhex("89 07 B8")
CALLBACK_STORE_SUFFIX = bytes.fromhex("89 47 02")

PROFILES = {
    "wsc_10": {
        "label": "WSC 1.0",
        "sha256": WSC10_SHA256,
        "bank": 0x39,
        "segment": 0x9C3F,
        "common_initializer": 0xFCDA,
        "object_creator": 0x3847,
        "expected_calls": (
            0xCA55, 0xCD08, 0xCF7D, 0xD2B5, 0xD5D0, 0xD832,
            0xDA52, 0xDCE8, 0xE0A2, 0xE475, 0xE6C3, 0xE876,
            0xEA2F, 0xEC7A, 0xF108, 0xF32B, 0xF58D, 0xF7A6,
        ),
        "root_setup_start": 0xC78A,
        "root_registration_call": 0xC7A0,
        "expected_convergence": 0xF82B,
        "expected_terminal": 0xF8A8,
        "choice_cycle": {
            "state_update": 0xEDFE,
            "modulus": 3,
            "case_starts_by_state": (0xEE2F, 0xEF0F, 0xEFF5),
            "common_tail": 0xF0C6,
            "expected_callbacks_by_state": (0xF1A0, 0xF3E0, 0xF612),
            "expected_selector_pairs": ((5, 7), (1, 8), (0, 9)),
        },
    },
    "wsc_15": {
        "label": "WSC 1.5",
        "sha256": WSC15_SHA256,
        "bank": 0x75,
        "segment": 0x558C,
        "common_initializer": 0xA62F,
        "object_creator": 0x4CCC,
        "expected_calls": (
            0x5FCA, 0x6285, 0x6502, 0x683A, 0x6B55, 0x6DB7,
            0x6FD3, 0x7346, 0x75F7, 0x78D2, 0x7C67, 0x7F1A,
            0x82D4, 0x86AB, 0x88F9, 0x8AAD, 0x8C66, 0x8EB1,
            0x94EA, 0x9717, 0x9979, 0x9B92, 0x9D9F, 0xA067,
        ),
        "root_setup_start": 0x5CF7,
        "root_registration_call": 0x5D0D,
        "expected_convergence": 0xA180,
        "expected_terminal": 0xA1FD,
        "choice_cycle": {
            "state_update": 0x9035,
            "modulus": 5,
            "case_starts_by_state": (0x9071, 0x913A, 0x9209, 0x93B5, 0x92C0),
            "common_tail": 0x94A2,
            "expected_callbacks_by_state": (
                0x958C, 0x97CC, 0x99FE, 0x9E40, 0x9C17,
            ),
            "expected_selector_pairs": (
                (5, 7), (1, 8), (0, 9), (13, 14), (12, 11),
            ),
        },
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def find_near_calls(bank: bytes, target: int) -> list[int]:
    calls = []
    for address in range(len(bank) - 2):
        if bank[address] != 0xE8:
            continue
        displacement = struct.unpack_from("<h", bank, address + 1)[0]
        if (address + 3 + displacement) & 0xFFFF == target:
            calls.append(address)
    return calls


def function_start_before(bank: bytes, call: int) -> int:
    start = bank.rfind(PROLOGUE, max(0, call - 0x600), call)
    if start < 0:
        raise ValueError(f"no callback prologue before {call:04X}")
    return start


def runtime_offset(physical: int, segment: int) -> int:
    return (physical - ((segment << 4) & 0xFFFF)) & 0xFFFF


def physical_offset(offset: int, segment: int) -> int:
    return (((segment << 4) & 0xFFFF) + offset) & 0xFFFF


def callback_stores(
    bank: bytes, start: int, end: int, segment: int
) -> list[dict[str, int]]:
    stores = []
    for source in range(start, max(start, end - 15)):
        if bank[source:source + 6] != CALLBACK_STORE_PREFIX:
            continue
        if bank[source + 8:source + 11] != CALLBACK_STORE_MIDDLE:
            continue
        if bank[source + 13:source + 16] != CALLBACK_STORE_SUFFIX:
            continue
        offset = struct.unpack_from("<H", bank, source + 6)[0]
        target_segment = struct.unpack_from("<H", bank, source + 11)[0]
        if target_segment != segment:
            continue
        stores.append({
            "store_address": source,
            "runtime_offset": offset,
            "segment": target_segment,
            "target_physical_address": physical_offset(offset, target_segment),
        })
    return stores


def immediate_push_before(bank: bytes, call: int) -> int:
    if call >= 2 and bank[call - 2] == 0x6A:
        return bank[call - 1]
    if call >= 3 and bank[call - 3] == 0x68:
        return struct.unpack_from("<H", bank, call - 2)[0]
    raise ValueError(f"no immediate push before object creator at {call:04X}")


def object_selectors(
    bank: bytes, start: int, end: int, segment: int, target: int
) -> list[int]:
    call_pattern = b"\x9A" + struct.pack("<HH", target, segment)
    selectors = []
    cursor = start
    while True:
        call = bank.find(call_pattern, cursor, end)
        if call < 0:
            return selectors
        selectors.append(immediate_push_before(bank, call))
        cursor = call + len(call_pattern)


def reachable(root: int, adjacency: dict[int, list[int]], population: set[int]) -> list[int]:
    seen = set()
    pending = [root]
    while pending:
        node = pending.pop()
        if node in seen or node not in population:
            continue
        seen.add(node)
        pending.extend(adjacency.get(node, ()))
    return sorted(seen)


def population_body_for_target(target: int, body_starts: list[int]) -> int | None:
    for body in body_starts:
        # One callback in each version has a six-byte wrapper before the common
        # preserved-register prologue. Keep the raw entry in evidence while
        # canonicalizing graph topology to the body containing the initializer.
        if 0 <= body - target <= 8:
            return body
    return None


def population_instruction_shapes(
    path: pathlib.Path, analysis: dict[str, object]
) -> list[list[str]]:
    data = path.read_bytes()
    bank_number = int(analysis["bank"])
    bank = data[bank_number * 0x10000:(bank_number + 1) * 0x10000]
    functions = analysis["functions"]
    starts = [int(entry["physical_start"]) for entry in functions]
    terminal = int(analysis["terminal_function"])
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    shapes = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else min(0x10000, terminal + 0x80)
        shapes.append([insn.mnemonic for insn in engine.disasm(bank[start:end], start)])
    return shapes


def monotonic_shape_alignment(
    old_shapes: list[list[str]], new_shapes: list[list[str]]
) -> tuple[list[dict[str, object]], list[int]]:
    """Map every old callback to an ordered new callback, allowing additions."""
    old_count = len(old_shapes)
    new_count = len(new_shapes)
    scores = [
        [difflib.SequenceMatcher(None, old, new).ratio() for new in new_shapes]
        for old in old_shapes
    ]
    impossible = -1.0e9
    best = [[impossible] * (new_count + 1) for _ in range(old_count + 1)]
    previous: list[list[tuple[int, int, str] | None]] = [
        [None] * (new_count + 1) for _ in range(old_count + 1)
    ]
    best[0][0] = 0.0
    for old_index in range(old_count + 1):
        for new_index in range(new_count):
            current = best[old_index][new_index]
            if current <= impossible / 2:
                continue
            if current > best[old_index][new_index + 1]:
                best[old_index][new_index + 1] = current
                previous[old_index][new_index + 1] = (
                    old_index, new_index, "skip-new"
                )
            if old_index < old_count:
                mapped = current + scores[old_index][new_index]
                if mapped > best[old_index + 1][new_index + 1]:
                    best[old_index + 1][new_index + 1] = mapped
                    previous[old_index + 1][new_index + 1] = (
                        old_index, new_index, "map"
                    )

    mapping = []
    skipped = []
    old_index, new_index = old_count, new_count
    while old_index or new_index:
        step = previous[old_index][new_index]
        if step is None:
            raise ValueError("opening instruction-shape alignment is incomplete")
        previous_old, previous_new, operation = step
        if operation == "map":
            mapping.append({
                "wsc_10_index": previous_old,
                "wsc_15_index": previous_new,
                "mnemonic_similarity": round(
                    scores[previous_old][previous_new], 6
                ),
            })
        else:
            skipped.append(previous_new)
        old_index, new_index = previous_old, previous_new
    mapping.reverse()
    skipped.reverse()
    return mapping, skipped


def analyze_choice_cycle(
    bank: bytes,
    profile: dict[str, object],
    population_starts: list[int],
) -> dict[str, object]:
    cycle = profile["choice_cycle"]
    state_update = int(cycle["state_update"])
    base_setup = bytes.fromhex("BB 4E 00 B8 00 10 8E C0")
    if bank[state_update - len(base_setup):state_update] != base_setup:
        raise ValueError(f"choice-cycle state base changed for {profile['label']}")
    update_prefix = bytes.fromhex(
        "33 D2 26 8A 57 20 C0 EA 04 8A F2 FE C6 80 FE"
    )
    update_suffix = bytes.fromhex(
        "72 02 32 F6 C0 E6 04 26 80 67 20 0F 26 08 77 20"
    )
    if bank[state_update:state_update + len(update_prefix)] != update_prefix:
        raise ValueError(f"choice-cycle update prefix changed for {profile['label']}")
    modulus = bank[state_update + len(update_prefix)]
    if modulus != int(cycle["modulus"]):
        raise ValueError(f"choice-cycle modulus changed for {profile['label']}")
    suffix_start = state_update + len(update_prefix) + 1
    if bank[suffix_start:suffix_start + len(update_suffix)] != update_suffix:
        raise ValueError(f"choice-cycle update suffix changed for {profile['label']}")

    segment = int(profile["segment"])
    object_creator = int(profile["object_creator"])
    case_starts = [int(value) for value in cycle["case_starts_by_state"]]
    common_tail = int(cycle["common_tail"])
    cases = []
    for state, case_start in enumerate(case_starts):
        case_end = min(
            value for value in (*case_starts, common_tail) if value > case_start
        )
        stores = callback_stores(bank, case_start, case_end, segment)
        targets = []
        for store in stores:
            body = population_body_for_target(
                store["target_physical_address"], population_starts
            )
            if body is not None:
                targets.append(body)
        if len(targets) != 1:
            raise ValueError(
                f"choice state {state} has {len(targets)} callback targets "
                f"for {profile['label']}"
            )
        selectors = object_selectors(
            bank, case_start, case_end, segment, object_creator
        )
        cases.append({
            "state": state,
            "case_start": case_start,
            "selected_callback": targets[0],
            "object_selector_pair": selectors,
        })

    callbacks = tuple(entry["selected_callback"] for entry in cases)
    selectors = tuple(tuple(entry["object_selector_pair"]) for entry in cases)
    if callbacks != tuple(cycle["expected_callbacks_by_state"]):
        raise ValueError(f"choice callback order changed for {profile['label']}")
    if selectors != tuple(cycle["expected_selector_pairs"]):
        raise ValueError(f"choice selector pairs changed for {profile['label']}")
    return {
        "state_storage": {
            "segment": 0x1000,
            "base_offset": 0x004E,
            "field_offset": 0x20,
            "effective_offset": 0x006E,
            "component": "high_nibble",
        },
        "selection_uses": "old_state_before_increment",
        "update_policy": f"(old_state + 1) modulo {modulus}",
        "modulus": modulus,
        "state_update_address": state_update,
        "cases": cases,
    }


def analyze(path: pathlib.Path, profile: dict[str, object]) -> dict[str, object]:
    data = path.read_bytes()
    actual_hash = sha256(data)
    if actual_hash != profile["sha256"]:
        raise ValueError(f"unexpected SHA-256 for {path}: {actual_hash}")
    bank_number = int(profile["bank"])
    bank = data[bank_number * 0x10000:(bank_number + 1) * 0x10000]
    segment = int(profile["segment"])
    calls = find_near_calls(bank, int(profile["common_initializer"]))
    expected_calls = tuple(profile["expected_calls"])
    if tuple(calls) != expected_calls:
        raise ValueError(f"unexpected initializer calls for {profile['label']}: {calls}")
    starts = [function_start_before(bank, call) for call in calls]
    if len(starts) != len(set(starts)):
        raise ValueError(f"duplicate callback starts for {profile['label']}")

    root = starts[0]
    root_runtime = runtime_offset(root, segment)
    registration_pattern = (
        bytes.fromhex("68 00 10 68")
        + struct.pack("<H", segment)
        + b"\x68"
        + struct.pack("<H", root_runtime)
    )
    setup_start = int(profile["root_setup_start"])
    registration_source = bank.find(registration_pattern, setup_start, root)
    if registration_source < 0:
        raise ValueError(f"root registration not found for {profile['label']}")
    expected_registration_call = int(profile["root_registration_call"])
    if registration_source + len(registration_pattern) != expected_registration_call:
        raise ValueError(
            f"unexpected root registration call for {profile['label']}: "
            f"{registration_source + len(registration_pattern):04X}"
        )

    population = set(starts)
    functions = []
    adjacency: dict[int, list[int]] = {}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else min(0x10000, start + 0x800)
        stores = callback_stores(bank, start, end, segment)
        for store in stores:
            body = population_body_for_target(
                store["target_physical_address"], starts
            )
            store["target_population_body"] = body
        internal = [
            entry["target_population_body"]
            for entry in stores
            if entry["target_population_body"] is not None
        ]
        adjacency[start] = internal
        selectors = object_selectors(
            bank, start, end, segment, int(profile["object_creator"])
        )
        functions.append({
            "index": index,
            "physical_start": start,
            "runtime_offset": runtime_offset(start, segment),
            "initializer_call": calls[index],
            "callback_stores": stores,
            "population_targets": internal,
            "object_selector_arguments": selectors,
        })

    split_indices = [
        entry["index"] for entry in functions if len(entry["population_targets"]) > 1
    ]
    if len(split_indices) != 1:
        raise ValueError(f"expected one choice split for {profile['label']}: {split_indices}")
    split_index = split_indices[0]
    for index in range(split_index):
        if functions[index]["population_targets"] != [starts[index + 1]]:
            raise ValueError(
                f"broken linear chain at {profile['label']} callback {index}"
            )
    choice_starts = starts[split_index + 1:]
    if functions[split_index]["population_targets"] != choice_starts:
        raise ValueError(f"unexpected choice targets for {profile['label']}")

    convergence = int(profile["expected_convergence"])
    terminal = int(profile["expected_terminal"])
    for entry in functions[split_index + 1:]:
        external = [
            store["target_physical_address"]
            for store in entry["callback_stores"]
            if store["target_physical_address"] not in population
        ]
        if convergence not in external or terminal not in external:
            raise ValueError(
                f"choice callback does not converge/terminate for {profile['label']}: "
                f"{entry['physical_start']:04X}"
            )

    reached = reachable(root, adjacency, population)
    if reached != sorted(population):
        raise ValueError(f"unreachable callback population for {profile['label']}")

    selector_population = [
        selector
        for entry in functions
        for selector in entry["object_selector_arguments"]
    ]
    choice_cycle = analyze_choice_cycle(bank, profile, starts)

    return {
        "label": profile["label"],
        "source": {"bytes": len(data), "sha256": actual_hash},
        "bank": bank_number,
        "runtime_segment": segment,
        "physical_to_runtime_bias": (segment << 4) & 0xFFFF,
        "root_registration": {
            "setup_function": setup_start,
            "registration_source": registration_source,
            "registration_call": expected_registration_call,
            "root_physical_start": root,
            "root_runtime_offset": root_runtime,
        },
        "population_count": len(starts),
        "linear_callback_count": split_index + 1,
        "choice_callback_count": len(choice_starts),
        "choice_split_function": starts[split_index],
        "choice_functions": choice_starts,
        "convergence_function": convergence,
        "terminal_function": terminal,
        "reachable_population_count": len(reached),
        "object_selector_population": selector_population,
        "choice_cycle": choice_cycle,
        "functions": functions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    old = analyze(args.wsc10, PROFILES["wsc_10"])
    new = analyze(args.wsc15, PROFILES["wsc_15"])
    alignment, unmatched_new = monotonic_shape_alignment(
        population_instruction_shapes(args.wsc10, old),
        population_instruction_shapes(args.wsc15, new),
    )
    expected_mapping = (
        [(index, index) for index in range(7)]
        + [(index, index + 4) for index in range(7, 18)]
    )
    actual_mapping = [
        (entry["wsc_10_index"], entry["wsc_15_index"])
        for entry in alignment
    ]
    if actual_mapping != expected_mapping or unmatched_new != [7, 8, 9, 10, 22, 23]:
        raise ValueError(
            "unexpected WSC opening instruction-shape alignment: "
            f"mapping={actual_mapping}, unmatched={unmatched_new}"
        )
    new_functions = new["functions"]
    for entry in alignment:
        old_function = old["functions"][entry["wsc_10_index"]]
        new_function = new_functions[entry["wsc_15_index"]]
        entry["wsc_10_function"] = old_function["physical_start"]
        entry["wsc_15_function"] = new_function["physical_start"]
    unmatched_functions = [
        {
            "wsc_15_index": index,
            "physical_start": new_functions[index]["physical_start"],
            "topology_role": (
                "linear" if index < new["linear_callback_count"] else "choice"
            ),
            "object_selector_arguments": new_functions[index][
                "object_selector_arguments"
            ],
        }
        for index in unmatched_new
    ]
    result = {
        "schema": 1,
        "kind": "wsc-opening-callback-graph-comparison",
        "wsc_10": old,
        "wsc_15": new,
        "delta": {
            "population": new["population_count"] - old["population_count"],
            "linear_callbacks": (
                new["linear_callback_count"] - old["linear_callback_count"]
            ),
            "choice_callbacks": (
                new["choice_callback_count"] - old["choice_callback_count"]
            ),
        },
        "monotonic_instruction_shape_alignment": {
            "method": (
                "maximum total SequenceMatcher ratio over x86 mnemonic lists, "
                "preserving order and allowing WSC 1.5-only callbacks"
            ),
            "mapping": alignment,
            "wsc_15_only_callbacks": unmatched_functions,
        },
        "claim_scope": (
            "Static root task registration and callback reachability are "
            "confirmed for both WSC versions. WSC 1.5 adds four callbacks to "
            "the aligned linear opening chain and two choice callbacks. Object "
            "selector arguments and the modulo-3 to modulo-5 choice-cycle "
            "extension are recorded. Runtime presentation behavior is not "
            "established by this static graph."
        ),
    }
    if result["delta"] != {
        "population": 6,
        "linear_callbacks": 4,
        "choice_callbacks": 2,
    }:
        raise ValueError(f"unexpected opening topology delta: {result['delta']}")
    old_selectors = old["object_selector_population"]
    new_selectors = new["object_selector_population"]
    if old_selectors != [
        0, 1, 2, 0, 1, 2, 3, 4, 5, 5, 6, 11, 5, 7, 1, 8, 0, 9
    ]:
        raise ValueError(f"unexpected WSC 1.0 opening selectors: {old_selectors}")
    if new_selectors != [
        0, 1, 2, 0, 1, 2, 13, 14, 8, 9, 3, 4, 5, 5, 6, 11,
        5, 7, 1, 8, 0, 9, 12, 11, 13, 14,
    ]:
        raise ValueError(f"unexpected WSC 1.5 opening selectors: {new_selectors}")

    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
