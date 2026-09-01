#!/usr/bin/env python3
"""Derive a bounded WSC-to-GBA timing plan for the four added callbacks.

The retail port did not apply one universal arithmetic rule to every linear
opening constant.  This checker therefore anchors three template families to
exact WSC 1.0/GBA instruction pairs, then uses same-template deltas or ratios
for the new WSC 1.5 values.  The result is an implementation plan, not runtime
evidence and not proof that the inferred constants are perceptually final.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

import analyze_gba_opening_dispatch as gba_graph
import analyze_wsc_opening_dispatch as wsc_graph


GBA_SHA256 = gba_graph.GBA_SHA256
WSC10_SHA256 = wsc_graph.WSC10_SHA256
WSC15_SHA256 = wsc_graph.WSC15_SHA256

TEMPLATES = {
    7: {
        "wsc_callback": 0xDAF6,
        "gba_callback": 0x08085454,
        "timer_pairs": {
            "fade_setup": (10, 8),
            "timed_event": (60, 48),
            "fade_threshold": (104, 83),
            "successor_initial_timer": (120, 94),
        },
        "motion_pair": (14, 20),
        "wsc_evidence": {
            0xDB1B: "83 3E 4C 09 0A",
            0xDB5D: "83 3E 4C 09 3C",
            0xDB73: "83 3E 4C 09 68",
            0xDB7A: "26 83 2E 86 01 0E",
            0xDBF3: "C7 06 4C 09 78 00",
        },
        "gba_evidence": {
            0x085484: "08 00 59 E3",
            0x0854BC: "30 00 59 E3",
            0x0854E8: "53 00 59 E3",
            0x0854F8: "14 90 49 E2",
            0x085554: "5E 90 A0 E3",
        },
    },
    8: {
        "wsc_callback": 0xDD81,
        "gba_callback": 0x080857E4,
        "timer_pairs": {
            "timed_event": (67, 53),
            "motion_stop": (47, 37),
            "fade_setup": (10, 8),
            "fade_threshold": (105, 84),
            "successor_initial_timer": (170, 136),
        },
        "motion_pair": (14, 19),
        "wsc_evidence": {
            0xDDA6: "83 3E 4C 09 43",
            0xDE43: "83 3E 4C 09 2F",
            0xDEB1: "83 3E 4C 09 0A",
            0xDEF3: "83 3E 4C 09 69",
            0xDEFA: "26 83 2E 86 01 0E",
            0xDF61: "C7 06 4C 09 AA 00",
        },
        "gba_evidence": {
            0x085814: "35 00 59 E3",
            0x0858DC: "25 00 59 E3",
            0x085984: "08 00 59 E3",
            0x0859BC: "54 00 59 E3",
            0x0859CC: "13 90 49 E2",
            0x085A30: "88 90 A0 E3",
        },
    },
    9: {
        "wsc_callback": 0xE163,
        "gba_callback": 0x08085D44,
        "timer_pairs": {
            "fade_threshold": (145, 116),
            "timed_event_a": (150, 120),
            "timed_event_b": (135, 108),
            "timed_event_c": (90, 72),
            "fade_setup": (10, 8),
            "successor_initial_timer": (180, 136),
        },
        "motion_pair": (7, 10),
        "wsc_evidence": {
            0xE189: "81 3E 4C 09 91 00",
            0xE191: "26 83 2E 84 01 07",
            0xE1D1: "81 3E 4C 09 96 00",
            0xE202: "81 3E 4C 09 87 00",
            0xE217: "83 3E 4C 09 5A",
            0xE274: "83 3E 4C 09 0A",
            0xE316: "C7 06 4C 09 B4 00",
        },
        "gba_evidence": {
            0x085D84: "74 00 59 E3",
            0x085D94: "0A 90 49 E2",
            0x085DCC: "78 00 59 E3",
            0x085E28: "6C 00 59 E3",
            0x085E50: "48 00 59 E3",
            0x085EFC: "08 00 59 E3",
            0x085F8C: "88 90 A0 E3",
        },
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def require_bytes(data: bytes, offset: int, expected: str, label: str) -> None:
    raw = bytes.fromhex(expected)
    if data[offset:offset + len(raw)] != raw:
        raise ValueError(f"{label} evidence changed at 0x{offset:X}")


def duration(value: int) -> int:
    return value * 4 // 5


def relative_timer(value: int, source: int, target: int) -> int:
    delta = value - source
    scaled = abs(delta) * 4 // 5
    return target + (scaled if delta >= 0 else -scaled)


def template_motion(value: int, source: int, target: int) -> int:
    return (value * target + source // 2) // source


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
    old_bank = wsc10[0x390000:0x3A0000]

    templates = []
    for index, template in TEMPLATES.items():
        for offset, raw in template["wsc_evidence"].items():
            require_bytes(old_bank, offset, raw, f"WSC template {index}")
        for offset, raw in template["gba_evidence"].items():
            require_bytes(gba, offset, raw, f"GBA template {index}")
        templates.append({
            key: value
            for key, value in template.items()
            if key not in ("wsc_evidence", "gba_evidence")
        } | {"template": index})

    motion7 = TEMPLATES[7]["motion_pair"]
    motion8 = TEMPLATES[8]["motion_pair"]
    motion9 = TEMPLATES[9]["motion_pair"]
    initial7 = TEMPLATES[7]["timer_pairs"]["successor_initial_timer"]
    initial8 = TEMPLATES[8]["timer_pairs"]["successor_initial_timer"]
    initial9 = TEMPLATES[9]["timer_pairs"]["successor_initial_timer"]
    plans = [
        {
            "callback": 7,
            "template": 7,
            "timers": {
                "fade_setup": duration(0x0A),
                "event_0x21": duration(0x5A),
                "event_0x22": duration(0x34),
                "event_0x23": duration(0x2A),
                "fade_threshold": duration(0x68),
                "successor_initial": relative_timer(0x6E, *initial7),
            },
            "fade_subtract": template_motion(8, *motion7),
            "method": "template-7 absolute event scaling plus relative successor-timer delta",
        },
        {
            "callback": 8,
            "template": 8,
            "timers": {
                "fade_setup": duration(0x0A),
                "event_0x1A": duration(0x43),
                "fade_threshold": duration(0x5F),
                "successor_initial": relative_timer(0xAA, *initial8),
            },
            "fade_subtract": template_motion(12, *motion8),
            "method": "template-8 absolute event scaling and unchanged successor timer",
        },
        {
            "callback": 9,
            "template": 9,
            "timers": {
                "fade_setup": duration(0x0A),
                "event_0x1D": duration(0x96),
                "fade_threshold": duration(0x87),
                "successor_initial": relative_timer(0xB4, *initial9),
            },
            "fade_subtract": template_motion(10, *motion9),
            "method": "template-9 absolute event scaling and unchanged successor timer",
        },
        {
            "callback": 10,
            "template": None,
            "timers": {
                "fade_setup": duration(0x0A),
                "fade_threshold": duration(0xA5),
                "successor_initial": relative_timer(0x64, *initial7),
            },
            "fade_subtract": template_motion(5, *motion9),
            "event_table_durations": [
                duration(value) for value in (6, 9, 30, 24, 24, 8, 500)
            ],
            "method": (
                "absolute 4/5 event scaling; destination callback-7 relative "
                "successor timer; template-9 motion ratio as the nearest family"
            ),
        },
    ]
    expected_plans = [
        ({"fade_setup": 8, "event_0x21": 72, "event_0x22": 41,
          "event_0x23": 33, "fade_threshold": 83, "successor_initial": 86}, 11),
        ({"fade_setup": 8, "event_0x1A": 53, "fade_threshold": 76,
          "successor_initial": 136}, 16),
        ({"fade_setup": 8, "event_0x1D": 120, "fade_threshold": 108,
          "successor_initial": 136}, 14),
        ({"fade_setup": 8, "fade_threshold": 132, "successor_initial": 78}, 7),
    ]
    for plan, (timers, motion) in zip(plans, expected_plans):
        if plan["timers"] != timers or plan["fade_subtract"] != motion:
            raise AssertionError(f"timing plan changed for callback {plan['callback']}")
    if plans[3]["event_table_durations"] != [4, 7, 24, 19, 19, 6, 400]:
        raise AssertionError("callback-10 event-table conversion changed")

    result = {
        "schema": 1,
        "kind": "opening-linear-callback-timing-translation-plan",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "commercial_templates": templates,
        "plans": plans,
        "rules": {
            "absolute_timers": "floor(WSC * 4 / 5)",
            "changed_successor_timers": (
                "commercial GBA template value plus signed floor(abs(WSC delta) * 4 / 5)"
            ),
            "fade_motion": (
                "nearest commercial template ratio, rounded to nearest integer"
            ),
        },
        "claim_scope": (
            "Static implementation plan anchored to exact commercial WSC/GBA "
            "instruction pairs. Added-callback constants remain an inference "
            "until non-displaying runtime timing and transition QA."
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
