#!/usr/bin/env python3
"""Bound storage and lifetimes for the two added opening auxiliary objects.

WSC 1.5 constructs both added objects during opening setup, but their callback
use is disjoint.  The commercial GBA opening uses object slots 0..2 at
0x03002908 with a 0x50-byte stride.  This checker proves that the immediately
following slot 3 has no literal reference in the retail ROM, ends exactly at
the unrelated task-count field, and can be reused sequentially for the two
added objects.  It produces an implementation plan, not runtime evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

import analyze_gba_opening_dispatch as gba_graph
import analyze_opening_initializer_population as populations
import analyze_wsc_opening_dispatch as wsc_graph


GBA_SHA256 = gba_graph.GBA_SHA256
WSC10_SHA256 = wsc_graph.WSC10_SHA256
WSC15_SHA256 = wsc_graph.WSC15_SHA256
GBA_BASE = 0x08000000
WSC15_BANK_OFFSET = 0x750000

GBA_CONSUMER = 0x08088250
GBA_CONSUMER_RANGE = (0x088250, 0x088310)
GBA_CONSUMER_SHA256 = (
    "AAF329B99CD8BABB7A4CC6AE663C59C09C2E05B05C8288ED484FD694870EA27E"
)
GBA_OBJECT_BASE = 0x03002908
GBA_OBJECT_STRIDE = 0x50
GBA_EXTRA_SLOT = 3
GBA_EXTRA_OBJECT = GBA_OBJECT_BASE + GBA_EXTRA_SLOT * GBA_OBJECT_STRIDE
GBA_TASK_COUNT = 0x03002A48

WSC_OBJECT_STRIDE = 0x42
WSC_ADDED_OBJECTS = {
    0x0952: {
        "record": 50,
        "gba_record_view": 0x080D44D8,
        "root_range": (0x5B2D, 0x5BBB),
        "root_sha256": "4641884FFAAC7B9534ECCA396DDB39EF5E1F13BE68F13F14C0AA070F011FEB56",
        "word_occurrences": (0x5B67, 0x7124, 0x72E2, 0x73E3),
        "active_callback": 7,
        "active_range": (0x7077, 0x7407),
        "construct_before": "callback 7 (predecessor callback 6 transition)",
        "skip_population": "callback 7 primary plus auxiliary",
    },
    0x0994: {
        "record": 49,
        "gba_record_view": 0x080D4498,
        "root_range": (0x5BBB, 0x5C49),
        "root_sha256": "2AAF89D0F7137BF135631F88D5B68C5AC35AF3FBCF63ED4C2CA18792D30B35B6",
        "word_occurrences": (0x5BF5, 0x7BF7, 0x7C21, 0x7D04),
        "active_callback": 10,
        "active_range": (0x7992, 0x7D28),
        "construct_before": "callback 10 (callback 9 transition)",
        "skip_population": "callback 10 primary plus auxiliary",
    },
}

EXPECTED_TASK_COUNT_REFS = (
    0x083D44, 0x084124, 0x084448, 0x084874, 0x084DEC,
    0x085110, 0x08543C, 0x0857D4, 0x085D30, 0x08630C,
    0x08659C, 0x086800, 0x086A30, 0x086D58, 0x0873C4,
    0x0876C0, 0x087A34, 0x087D84, 0x087ED8,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def all_offsets(data: bytes, needle: bytes, alignment: int = 1) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        found = data.find(needle, cursor)
        if found < 0:
            return offsets
        if found % alignment == 0:
            offsets.append(found)
        cursor = found + 1


def ror32(value: int, shift: int) -> int:
    shift &= 31
    if not shift:
        return value & 0xFFFFFFFF
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF


def mov_r8_immediate_before(data: bytes, offset: int, floor: int) -> int:
    for candidate in range(offset - 4, floor - 1, -4):
        word = struct.unpack_from("<I", data, candidate)[0]
        if ((word >> 25) & 7) != 1:
            continue
        if ((word >> 21) & 0xF) != 13 or ((word >> 12) & 0xF) != 8:
            continue
        return ror32(word & 0xFF, ((word >> 8) & 0xF) * 2)
    raise ValueError(f"no MOV-immediate assignment to r8 before 0x{offset:X}")


def opening_consumer_arguments(gba: bytes) -> list[dict[str, int]]:
    calls = gba_graph.find_calls(
        gba,
        GBA_CONSUMER,
        gba_graph.OPENING_REGION_START,
        gba_graph.OPENING_REGION_END,
    )
    if tuple(calls) != populations.EXPECTED_GBA_CALLS:
        raise ValueError(f"commercial opening consumer calls changed: {calls}")

    push_r8 = 0xE92D0100
    rows = []
    for call in calls:
        pushes = [
            offset
            for offset in range(max(0, call - 0x40), call, 4)
            if struct.unpack_from("<I", gba, offset)[0] == push_r8
        ]
        if len(pushes) < 3:
            raise ValueError(f"consumer call at 0x{call:X} lost its three arguments")
        selector_push, slot_push, _record_push = pushes[-3:]
        selector = mov_r8_immediate_before(
            gba, selector_push, max(0, selector_push - 0x24)
        )
        # The retail compiler reuses r8 without another MOV when selector and
        # slot are equal, so the slot push may share the selector assignment.
        slot = mov_r8_immediate_before(gba, slot_push, max(0, slot_push - 0x30))
        rows.append({"call_offset": call, "selector": selector, "slot": slot})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC 1.5 source")
    require_hash(
        gba[GBA_CONSUMER_RANGE[0]:GBA_CONSUMER_RANGE[1]],
        GBA_CONSUMER_SHA256,
        "GBA opening object consumer",
    )

    wsc15_bank = wsc15[WSC15_BANK_OFFSET:WSC15_BANK_OFFSET + 0x10000]
    lifetimes = []
    for object_address, expected in WSC_ADDED_OBJECTS.items():
        root_start, root_end = expected["root_range"]
        require_hash(
            wsc15_bank[root_start:root_end],
            str(expected["root_sha256"]),
            f"WSC 1.5 auxiliary object 0x{object_address:04X} setup",
        )
        occurrences = tuple(all_offsets(wsc15_bank, struct.pack("<H", object_address)))
        if occurrences != expected["word_occurrences"]:
            raise ValueError(
                f"WSC object 0x{object_address:04X} references changed: {occurrences}"
            )
        lifetimes.append({
            "wsc_object": object_address,
            "record": expected["record"],
            "gba_record_view": expected["gba_record_view"],
            "root_setup_range": list(expected["root_range"]),
            "root_setup_sha256": expected["root_sha256"],
            "all_bank_word_occurrences": list(occurrences),
            "active_callback": expected["active_callback"],
            "active_range": list(expected["active_range"]),
            "construct_before": expected["construct_before"],
            "skip_population": expected["skip_population"],
        })

    first_range = WSC_ADDED_OBJECTS[0x0952]["active_range"]
    second_range = WSC_ADDED_OBJECTS[0x0994]["active_range"]
    if first_range[1] > second_range[0]:
        raise ValueError("added auxiliary callback lifetimes now overlap")

    consumer_calls = opening_consumer_arguments(gba)
    commercial_slots = sorted({row["slot"] for row in consumer_calls})
    if commercial_slots != [0, 1, 2]:
        raise ValueError(f"commercial opening slot population changed: {commercial_slots}")

    extra_refs = all_offsets(gba, struct.pack("<I", GBA_EXTRA_OBJECT), alignment=4)
    if extra_refs:
        raise ValueError(f"candidate GBA slot 3 gained literal references: {extra_refs}")
    task_refs = tuple(
        all_offsets(gba, struct.pack("<I", GBA_TASK_COUNT), alignment=4)
    )
    if task_refs != EXPECTED_TASK_COUNT_REFS:
        raise ValueError(f"GBA task-count references changed: {task_refs}")
    if GBA_EXTRA_OBJECT + GBA_OBJECT_STRIDE != GBA_TASK_COUNT:
        raise AssertionError("candidate object slot no longer ends at task count")

    result = {
        "schema": 1,
        "kind": "opening-auxiliary-object-lifetime-plan",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "commercial_consumer": {
            "address": GBA_CONSUMER,
            "range": list(GBA_CONSUMER_RANGE),
            "sha256": GBA_CONSUMER_SHA256,
            "object_base": GBA_OBJECT_BASE,
            "object_stride": GBA_OBJECT_STRIDE,
            "calls": consumer_calls,
            "slots_used": commercial_slots,
        },
        "candidate_extra_slot": {
            "slot": GBA_EXTRA_SLOT,
            "address": GBA_EXTRA_OBJECT,
            "end": GBA_EXTRA_OBJECT + GBA_OBJECT_STRIDE,
            "next_field": GBA_TASK_COUNT,
            "aligned_literal_references_in_retail_rom": extra_refs,
            "task_count_reference_count": len(task_refs),
        },
        "wsc_object_stride": WSC_OBJECT_STRIDE,
        "source_lifetimes": lifetimes,
        "lifetime_relation": "callback 7 ends before callback 10 begins",
        "sequential_reuse_plan": [
            {
                "record": 50,
                "gba_record_view": 0x080D44D8,
                "action": (
                    "construct selector 0 in slot 3 during callback 6's transition, "
                    "then update/include it only in callback 7"
                ),
            },
            {
                "record": 49,
                "gba_record_view": 0x080D4498,
                "action": (
                    "reconstruct selector 0 in the same slot during callback 9's "
                    "transition, then update/include it only in callback 10"
                ),
            },
        ],
        "conclusion": (
            "The two WSC 1.5 auxiliary objects have disjoint active callback "
            "lifetimes. Commercial GBA opening construction uses slots 0..2; "
            "slot 3 has no aligned literal reference and occupies the exact "
            "0x50 bytes before the task-count field. One slot can therefore "
            "be reused sequentially without clobbering retained commercial "
            "auxiliary objects at 0x03002778/0x030027C8."
        ),
        "claim_scope": (
            "Static storage and lifetime plan only. The slot-3 construction, "
            "callback updates, skip lists, transition cleanup, and runtime "
            "behavior remain unimplemented and unverified."
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
