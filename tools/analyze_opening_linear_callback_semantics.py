#!/usr/bin/env python3
"""Recover implementation-facing semantics for the four added callbacks.

The graph/dependency ledgers prove where the callbacks belong and which
resources they consume.  This checker adds the bounded state-machine facts
needed by the ARM translation: timers, event triggers, primary/auxiliary
object lifetimes, selector records, normal successors, and skip populations.
It deliberately does not claim that an ARM translation exists.
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

import analyze_gba_opening_dispatch as gba_graph
import analyze_opening_linear_additions as additions
import analyze_wsc_opening_dispatch as wsc_graph


GBA_SHA256 = gba_graph.GBA_SHA256
WSC10_SHA256 = wsc_graph.WSC10_SHA256
WSC15_SHA256 = wsc_graph.WSC15_SHA256

GBA_TEMPLATE_FUNCTIONS = {
    7: 0x08085454,
    8: 0x080857E4,
    9: 0x08085D44,
}

CALLBACKS = {
    7: {
        "range": (0x7077, 0x7407),
        "sha256": "C3AC134789C3DE1983E8964696851CDEC636F3F95722DD8CF24F0ADD4346554F",
        "selector": 14,
        "next": 0x7407,
        "closest_old_index": 7,
        "translation_class": "template-guided plus auxiliary object",
        "sound": 0x02,
        "timer_events": [(0x5A, 0x21), (0x34, 0x22), (0x2A, 0x23)],
        "fade_setup_timer": 0x0A,
        "fade_motion": {"through_timer": 0x68, "subtract": [8], "clamp": 0x40},
        "initial_timer": 0x6E,
        "primary_position": [0x40, 0x68],
        "initial_event": 0,
        "auxiliary": {
            "wsc_record": 50,
            "gba_record_view": 0x080D44D8,
            "wsc_object": 0x0952,
            "position_on_event_0x22": [0x83, 0x44],
            "motion_on_event_0x23": [-2, 1],
            "event_when_flag_0x2000": 1,
        },
        "skip_object_population": [0x01CE, 0x0952],
        "evidence": {
            0x709C: "83 3E 4C 09 0A",
            0x70F7: "83 3E 4C 09 5A",
            0x7101: "6A 21",
            0x710D: "83 3E 4C 09 34",
            0x7117: "6A 22",
            0x7123: "BE 52 09 C7 04 83 00 C7 44 02 44 00",
            0x712F: "83 3E 4C 09 2A",
            0x7139: "6A 23",
            0x7145: "83 3E 4C 09 68",
            0x714C: "26 83 2E EA 01 08",
            0x71C5: "C7 06 4C 09 6E 00",
            0x71CF: "68 C0 03 6A 00 6A 0E",
            0x71DE: "C7 04 40 00 C7 44 02 68 00",
            0x7281: "BF 05 00 C1 E7 05 81 C7 A0 05",
            0x72DD: "8B 44 0E",
            0x72E4: "3D 22 00 74 0C 3D 23 00",
            0x72EE: "83 04 FE 83 44 02 01",
            0x72F5: "F7 44 0A 00 20",
            0x73CE: "26 C7 06 32 09 02 00",
            0x73D5: "BB 34 09 26 C7 07 CE 01 83 C3 02 26 C7 07 52 09",
        },
    },
    8: {
        "range": (0x7407, 0x7698),
        "sha256": "4B1F3D651E981A3006E42C642CEFABCDFC5AE455F7B9BAB488FAA5493E8D3991",
        "selector": 8,
        "next": 0x7698,
        "closest_old_index": 8,
        "translation_class": "template-guided single object",
        "sound": 0x89,
        "timer_events": [(0x43, 0x1A)],
        "fade_setup_timer": 0x0A,
        "fade_motion": {"through_timer": 0x5F, "subtract": [12, 12], "clamp": 0x40},
        "initial_timer": 0xAA,
        "primary_position": [0x9E, 0x68],
        "initial_event": 0,
        "skip_object_population": [0x01CE],
        "evidence": {
            0x741C: "68 89 00",
            0x7430: "83 3E 4C 09 43",
            0x7437: "6A 1A",
            0x7443: "83 3E 4C 09 0A",
            0x7485: "83 3E 4C 09 5F",
            0x748C: "26 83 2E EA 01 0C",
            0x74A1: "26 83 2E EC 01 0C",
            0x74D9: "C7 06 4C 09 AA 00",
            0x7521: "68 C0 03 6A 00 6A 08",
            0x7530: "C7 04 9E 00 C7 44 02 68 00",
            0x7667: "26 C7 06 32 09 01 00",
            0x766E: "BB 34 09 26 C7 07 CE 01",
        },
    },
    9: {
        "range": (0x7698, 0x7992),
        "sha256": "1A20D0D18BC4AB2E9C1ECDBF57D1BC4D2C959C79A7DF1445B7AC4E101A3DCAD7",
        "selector": 9,
        "next": 0x7992,
        "closest_old_index": 9,
        "translation_class": "template-guided event-table object",
        "sound": 0x8C,
        "timer_events": [(0x96, 0x1D)],
        "fade_setup_timer": 0x0A,
        "fade_motion": {"through_timer": 0x87, "subtract": [10, 10], "clamp": 0x40},
        "initial_timer": 0xB4,
        "primary_position": [0x40, 0x68],
        "initial_event": 0,
        "event_table": 0x7976,
        "skip_object_population": [0x01CE],
        "evidence": {
            0x76AD: "68 8C 00",
            0x76BE: "81 3E 4C 09 87 00",
            0x76C6: "26 83 2E EA 01 0A",
            0x76DB: "26 83 2E EC 01 0A",
            0x7706: "81 3E 4C 09 96 00",
            0x770E: "6A 1D",
            0x771C: "83 3E 4C 09 0A",
            0x77A8: "C7 06 4C 09 B4 00",
            0x77EC: "68 C0 03 6A 00 6A 09",
            0x77FB: "C7 04 40 00 C7 44 02 68 00",
            0x7945: "26 C7 06 32 09 01 00",
            0x794C: "BB 34 09 26 C7 07 CE 01",
        },
    },
    10: {
        "range": (0x7992, 0x7D28),
        "sha256": "FB46FFCD4F9BD7D50ADDBFE824AD1A70E5295054902C22C0720421B8D3EE542E",
        "selector": 3,
        "next": 0x7D28,
        "closest_old_index": 9,
        "translation_class": "bespoke event-table plus auxiliary object",
        "sound": 0x88,
        "timer_events": [],
        "fade_setup_timer": 0x0A,
        "fade_motion": {"through_timer": 0xA5, "subtract": [5, 5], "clamp": 0x40},
        "initial_timer": 0x64,
        "primary_position": [0x96, 0x68],
        "initial_event": 2,
        "event_table": 0x7976,
        "auxiliary": {
            "wsc_record": 49,
            "gba_record_view": 0x080D4498,
            "wsc_object": 0x0994,
            "activation_event": 0x25,
            "position": [0x54, 0x58],
            "motion": [2, 2],
            "clamp": [0xF0, 0xA0],
        },
        "skip_object_population": [0x01CE, 0x0994],
        "evidence": {
            0x79A7: "68 88 00",
            0x79B8: "81 3E 4C 09 A5 00",
            0x79C0: "26 83 2E EA 01 05",
            0x79D5: "26 83 2E EC 01 05",
            0x79EA: "83 3E 4C 09 0A",
            0x7AA6: "C7 06 4C 09 64 00",
            0x7AB0: "68 C0 03 6A 00 6A 03",
            0x7ABF: "C7 04 96 00 C7 44 02 68 00",
            0x7ACD: "6A 02",
            0x7B4D: "BF 04 00 C1 E7 05 81 C7 A0 05",
            0x7BC9: "26 8B 3F 26 FF 07 C1 E7 02",
            0x7BEB: "3D 25 00",
            0x7BF0: "26 C7 47 04 01 00",
            0x7BF6: "BF 94 09 C7 05 54 00 C7 45 02 58 00",
            0x7C20: "BE 94 09 83 04 02",
            0x7C30: "83 44 02 02",
            0x7CEF: "26 C7 06 32 09 02 00",
            0x7CF6: "BB 34 09 26 C7 07 CE 01 83 C3 02 26 C7 07 94 09",
        },
    },
}

EVENT_TABLE = [
    (0x0B, 0x0006),
    (0x0C, 0x0009),
    (0x0D, 0x001E),
    (0x0E, 0x0018),
    (0x23, 0x0018),
    (0x24, 0x0008),
    (0x25, 0x01F4),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def instruction_shapes(
    bank: bytes, starts: list[int], terminal: int
) -> list[list[str]]:
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    shapes = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else terminal + 0x80
        shapes.append([item.mnemonic for item in engine.disasm(bank[start:end], start)])
    return shapes


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

    old = wsc_graph.analyze(args.wsc10, wsc_graph.PROFILES["wsc_10"])
    new = wsc_graph.analyze(args.wsc15, wsc_graph.PROFILES["wsc_15"])
    old_bank = wsc10[0x390000:0x3A0000]
    new_bank = wsc15[0x750000:0x760000]
    old_starts = [int(item["physical_start"]) for item in old["functions"]]
    new_starts = [int(item["physical_start"]) for item in new["functions"]]
    old_shapes = instruction_shapes(old_bank, old_starts, int(old["terminal_function"]))
    new_shapes = instruction_shapes(new_bank, new_starts, int(new["terminal_function"]))

    callbacks = []
    for index, expected in CALLBACKS.items():
        start, end = expected["range"]
        require_hash(new_bank[start:end], expected["sha256"], f"WSC 1.5 callback {index}")
        graph_entry = new["functions"][index]
        if graph_entry["physical_start"] != start:
            raise ValueError(f"callback {index} graph start changed")
        if graph_entry["population_targets"] != [expected["next"]]:
            raise ValueError(f"callback {index} successor changed")
        if graph_entry["object_selector_arguments"] != [expected["selector"]]:
            raise ValueError(f"callback {index} selector changed")
        for offset, raw in expected["evidence"].items():
            value = bytes.fromhex(raw)
            if new_bank[offset:offset + len(value)] != value:
                raise ValueError(f"callback {index} evidence changed at {offset:04X}")

        similarities = [
            difflib.SequenceMatcher(None, shape, new_shapes[index]).ratio()
            for shape in old_shapes[:15]
        ]
        closest = max(range(len(similarities)), key=similarities.__getitem__)
        if closest != expected["closest_old_index"]:
            raise ValueError(f"callback {index} closest old template changed: {closest}")
        item = {key: value for key, value in expected.items() if key != "evidence"}
        item["index"] = index
        item["bytes"] = end - start
        item["closest_old_callback"] = old_starts[closest]
        item["closest_old_mnemonic_similarity"] = round(similarities[closest], 6)
        item["gba_template_function"] = GBA_TEMPLATE_FUNCTIONS.get(closest)
        item["source_evidence"] = [
            {"offset": offset, "bytes": raw}
            for offset, raw in expected["evidence"].items()
        ]
        callbacks.append(item)

    event_table = [
        struct.unpack_from("<HH", new_bank, 0x7976 + index * 4)
        for index in range(len(EVENT_TABLE))
    ]
    if event_table != EVENT_TABLE:
        raise ValueError(f"shared callback event table changed: {event_table}")

    if additions.find_gba_chain_sites(gba)["selector_after"] != 13:
        raise ValueError("aligned predecessor selector change is no longer 3->13")

    result = {
        "schema": 1,
        "kind": "opening-linear-callback-translation-semantics",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "insertion": additions.find_gba_chain_sites(gba),
        "callbacks": callbacks,
        "shared_event_table": {
            "physical_start": 0x7976,
            "entries": [list(item) for item in event_table],
            "sha256": sha256(new_bank[0x7976:0x7992]),
        },
        "translation_boundary": {
            "template_guided_callbacks": [7, 8, 9],
            "bespoke_callback": 10,
            "complex_auxiliary_callbacks": [7, 10],
            "remaining_decisions": [
                "derive the commercial GBA timing/motion conversion for each changed constant",
                "construct and reuse the separately bounded extra GBA opening-object slot on normal and skip paths",
                "assemble the four ARM callbacks and splice the predecessor edge",
            ],
        },
        "claim_scope": (
            "Exact WSC 1.5 callback state-machine semantics and commercial "
            "template attribution only. No ARM callback, chain splice, runtime "
            "behavior, or completion is claimed."
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
