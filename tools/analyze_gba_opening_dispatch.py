#!/usr/bin/env python3
"""Recover the commercial GBA opening callback graph statically.

The commercial conversion changes the active task callback through
0x08012008.  This tool resolves the PC-relative callback values at every call
in the opening code region and attributes character-resource consumer calls to
their containing callback functions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OPENING_ENTRY = 0x080838A4
OPENING_ROOT_CALLBACK = 0x08083978
OPENING_CONVERGENCE = 0x08087D94
OPENING_TERMINAL = 0x08087E3C
OPENING_REGION_START = 0x0838A4
OPENING_REGION_END = 0x087EE8
TASK_REGISTER = 0x08011AC4
ROOT_REGISTRATION_CALL_OFFSET = 0x0838C8
ROOT_LITERAL_OFFSET = 0x08395C
SET_CALLBACK = 0x08012008
CHARACTER_CONSUMER = 0x08088250
EXPECTED_SET_CALLBACK_CALLS = 39
EXPECTED_CHARACTER_CALLS = 18


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def branch_target(address: int, word: int) -> int:
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    return address + 8 + immediate * 4


def find_calls(data: bytes, target: int, start: int, end: int) -> list[int]:
    calls = []
    for offset in range((start + 3) & ~3, min(end, len(data) - 3), 4):
        word = struct.unpack_from("<I", data, offset)[0]
        if ((word >> 25) & 7) != 5 or not (word & 0x01000000):
            continue
        if branch_target(GBA_BASE + offset, word) == target:
            calls.append(offset)
    return calls


def function_start_before(data: bytes, offset: int) -> int:
    for candidate in range(offset & ~3, max(OPENING_REGION_START - 4, offset - 0x1200), -4):
        word = struct.unpack_from("<I", data, candidate)[0]
        # ARM stmdb sp!, {...,lr}. Argument pushes use the same opcode but do
        # not include LR, so the LR bit separates callback prologues.
        if (word & 0xFFFF0000) == 0xE92D0000 and word & (1 << 14):
            return candidate
    raise ValueError(f"no ARM function prologue before ROM offset {offset:06X}")


def ror32(value: int, shift: int) -> int:
    shift &= 31
    if not shift:
        return value & 0xFFFFFFFF
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF


def resolve_r8_assignment(data: bytes, call_offset: int) -> dict[str, int | str]:
    for offset in range(call_offset - 4, max(call_offset - 0x40, -1), -4):
        word = struct.unpack_from("<I", data, offset)[0]
        address = GBA_BASE + offset

        # ARM data-processing immediate, ADD/SUB r8, pc, #imm.
        if ((word >> 25) & 7) == 1:
            opcode = (word >> 21) & 0xF
            rn = (word >> 16) & 0xF
            rd = (word >> 12) & 0xF
            if rn == 15 and rd == 8 and opcode in (2, 4):
                immediate = ror32(word & 0xFF, ((word >> 8) & 0xF) * 2)
                target = address + 8
                target = target - immediate if opcode == 2 else target + immediate
                return {
                    "assignment_offset": offset,
                    "kind": "sub-pc" if opcode == 2 else "add-pc",
                    "target_address": target & 0xFFFFFFFF,
                }

        # ARM single-data-transfer immediate, LDR r8, [pc, +/-imm12].
        if ((word >> 26) & 3) == 1:
            immediate_form = not bool(word & (1 << 25))
            pre_indexed = bool(word & (1 << 24))
            load = bool(word & (1 << 20))
            rn = (word >> 16) & 0xF
            rd = (word >> 12) & 0xF
            if immediate_form and pre_indexed and load and rn == 15 and rd == 8:
                literal = address + 8
                displacement = word & 0xFFF
                literal = literal + displacement if word & (1 << 23) else literal - displacement
                literal_offset = literal - GBA_BASE
                if not 0 <= literal_offset <= len(data) - 4:
                    raise ValueError(f"literal outside ROM at {offset:06X}")
                target = struct.unpack_from("<I", data, literal_offset)[0]
                return {
                    "assignment_offset": offset,
                    "kind": "ldr-literal",
                    "literal_offset": literal_offset,
                    "target_address": target,
                }
    raise ValueError(f"unresolved r8 callback assignment before {call_offset:06X}")


def reachable(root: int, adjacency: dict[int, list[int]]) -> list[int]:
    seen = set()
    pending = [root]
    while pending:
        node = pending.pop()
        if node in seen or node not in adjacency:
            continue
        seen.add(node)
        pending.extend(adjacency[node])
    return sorted(seen)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    data = args.gba.read_bytes()
    actual_hash = sha256(data)
    if actual_hash != GBA_SHA256:
        raise ValueError(f"unexpected GBA SHA-256: {actual_hash}")

    set_sites = find_calls(data, SET_CALLBACK, OPENING_REGION_START, OPENING_REGION_END)
    if len(set_sites) != EXPECTED_SET_CALLBACK_CALLS:
        raise ValueError(
            f"expected {EXPECTED_SET_CALLBACK_CALLS} callback setters, found {len(set_sites)}"
        )
    edges = []
    for call in set_sites:
        source = function_start_before(data, call)
        assignment = resolve_r8_assignment(data, call)
        edges.append({
            "source_function": GBA_BASE + source,
            "set_callback_call_offset": call,
            **assignment,
        })

    character_sites = find_calls(
        data, CHARACTER_CONSUMER, OPENING_REGION_START, OPENING_REGION_END
    )
    if len(character_sites) != EXPECTED_CHARACTER_CALLS:
        raise ValueError(
            f"expected {EXPECTED_CHARACTER_CALLS} character calls, found {len(character_sites)}"
        )
    character_consumers: dict[int, list[int]] = {}
    for call in character_sites:
        source = GBA_BASE + function_start_before(data, call)
        character_consumers.setdefault(source, []).append(call)

    # The entry schedules OPENING_ROOT_CALLBACK through its first task-register
    # call. Both the call target and callback literal are fixed evidence gates.
    root_literal = struct.unpack_from("<I", data, ROOT_LITERAL_OFFSET)[0]
    if root_literal != OPENING_ROOT_CALLBACK:
        raise ValueError(f"unexpected root callback literal: {root_literal:08X}")
    registration_word = struct.unpack_from(
        "<I", data, ROOT_REGISTRATION_CALL_OFFSET
    )[0]
    if branch_target(GBA_BASE + ROOT_REGISTRATION_CALL_OFFSET, registration_word) != TASK_REGISTER:
        raise ValueError("unexpected GBA opening task-registration call")

    callback_targets = sorted({entry["target_address"] for entry in edges})
    sources = sorted({entry["source_function"] for entry in edges})
    population = [source for source in sources if source != OPENING_TERMINAL]
    population_set = set(population)
    adjacency = {
        source: [
            entry["target_address"]
            for entry in edges
            if entry["source_function"] == source
            and entry["target_address"] in population_set
        ]
        for source in population
    }
    if not population or population[0] != OPENING_ROOT_CALLBACK:
        raise ValueError("GBA opening population is not rooted at the scheduled callback")
    split_functions = [
        source for source, targets in adjacency.items() if len(targets) > 1
    ]
    if split_functions != [0x08086D60]:
        raise ValueError(f"unexpected opening choice split: {split_functions}")
    split = split_functions[0]
    split_index = population.index(split)
    linear = population[:split_index + 1]
    choices = population[split_index + 1:]
    if len(linear) != 15 or len(choices) != 3:
        raise ValueError(
            f"unexpected GBA opening topology: {len(linear)} linear, "
            f"{len(choices)} choices"
        )
    for index, source in enumerate(linear[:-1]):
        if adjacency[source] != [linear[index + 1]]:
            raise ValueError(f"broken GBA linear chain at {source:08X}")
    if adjacency[split] != choices:
        raise ValueError("unexpected GBA choice targets")
    for source in choices:
        targets = [
            entry["target_address"]
            for entry in edges
            if entry["source_function"] == source
        ]
        if OPENING_CONVERGENCE not in targets or OPENING_TERMINAL not in targets:
            raise ValueError(f"GBA choice does not converge/terminate: {source:08X}")
    reached = reachable(OPENING_ROOT_CALLBACK, adjacency)
    if reached != sorted(population):
        raise ValueError("unreachable callback in commercial GBA opening population")
    result = {
        "schema": 1,
        "kind": "gba-opening-callback-graph",
        "source": {"bytes": len(data), "sha256": actual_hash},
        "opening_entry": OPENING_ENTRY,
        "root_callback": OPENING_ROOT_CALLBACK,
        "root_task_registration": {
            "call_offset": ROOT_REGISTRATION_CALL_OFFSET,
            "consumer": TASK_REGISTER,
            "callback_literal_offset": ROOT_LITERAL_OFFSET,
            "callback": root_literal,
        },
        "set_callback_consumer": SET_CALLBACK,
        "set_callback_call_count": len(set_sites),
        "resolved_edge_count": len(edges),
        "edges": edges,
        "unique_callback_targets": callback_targets,
        "topology": {
            "population_count": len(population),
            "linear_callback_count": len(linear),
            "choice_callback_count": len(choices),
            "linear_functions": linear,
            "choice_split_function": split,
            "choice_functions": choices,
            "convergence_function": OPENING_CONVERGENCE,
            "terminal_function": OPENING_TERMINAL,
            "reachable_population_count": len(reached),
        },
        "character_resource_consumer": CHARACTER_CONSUMER,
        "character_call_count": len(character_sites),
        "character_calls_by_function": [
            {"function": function, "call_offsets": calls}
            for function, calls in sorted(character_consumers.items())
        ],
        "claim_scope": (
            "Static commercial-GBA task registration and callback assignments "
            "rooted at the opening entry. Every population callback is graph-"
            "reachable; runtime choice frequencies are not established."
        ),
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
