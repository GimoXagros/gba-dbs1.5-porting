#!/usr/bin/env python3
"""Prove direct P1 payload/B rules without claiming an A-target converter.

The WSC 1.0 and USA GBA releases contain source-lineage P1 container pairs.
This analyzer guards twelve exact pairs, proves their 12-byte to 16-byte
payload expansion and null/non-null B-pointer behavior, then checks whether
the two Ver. 1.5 Shoot-initializer payload populations stay inside that proved
rule.  A targets are recorded only as platform-specific mapping boundaries.
No ROM is written and no runtime or save is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_new_base_p1_assets import convert_payload_item  # type: ignore
from shoot_resource_conversion import (  # type: ignore
    convert_shoot_payload_item,
    parse_shoot_p1,
)


GBA_BASE = 0x08000000
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


PAIR_SPECS = (
    ("base_0efec0", 0x0EFEC0, 0x019028, [3, 3, 3, 3, 3, 3], "generic-zero-tail"),
    ("base_22ff80", 0x22FF80, 0x08FC58, [1, 1, 1, 1, 1], "generic-zero-tail"),
    ("base_2ac750", 0x2AC750, 0x0D1C88, [5, 4, 4, 4, 4, 7, 6, 21, 4], "generic-zero-tail"),
    ("shoot_spawn", 0x2AE180, 0x350248, [5, 3, 1, 5, 10, 8, 10], "shoot-tail-relocation"),
    ("base_2b05e0", 0x2B05E0, 0x0A02E8, [1, 3, 1, 3, 1, 10, 1, 1, 3, 5, 1, 2], "generic-zero-tail"),
    ("non_null_b_oracle", 0x2B09C0, 0x34DFE0, [1, 1, 1, 7, 6, 6, 2, 2, 2], "generic-zero-tail"),
    ("base_2b1120", 0x2B1120, 0x09D958, [1, 1, 1, 5, 5, 8, 8, 1, 1], "generic-zero-tail"),
    ("base_2b1820", 0x2B1820, 0x341C00, [4, 4, 2, 5, 3, 4, 1, 3, 3], "generic-zero-tail"),
    ("base_2b2930", 0x2B2930, 0x0B77EC, [1] * 13, "generic-zero-tail"),
    ("base_2b3c10", 0x2B3C10, 0x09E900, [1] * 9, "generic-zero-tail"),
    ("base_2b4b40", 0x2B4B40, 0x01B650, [7, 2], "generic-zero-tail"),
    ("base_2b4ee0", 0x2B4EE0, 0x01BEAC, [6, 2], "generic-zero-tail"),
)

INITIALIZER_SOURCES = (0x3CF410, 0x3BD730)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 changed: expected {expected}, got {actual}")


def read_gba_commands(gba: bytes, source: int) -> list[tuple[int, int, int, int]]:
    table_pointer, reserved = struct.unpack_from("<2I", gba, source)
    if reserved != 0 or table_pointer != GBA_BASE + source + 8:
        raise SystemExit(f"commercial GBA P1 header changed at 0x{source:X}")
    table = table_pointer - GBA_BASE
    first_payload_pointer = struct.unpack_from("<I", gba, table + 4)[0]
    first_payload = first_payload_pointer - GBA_BASE
    command_bytes = first_payload - table
    if command_bytes <= 0 or command_bytes % 16:
        raise SystemExit(f"cannot derive GBA P1 command population at 0x{source:X}")
    commands = [
        struct.unpack_from("<4I", gba, table + index * 16)
        for index in range(command_bytes // 16)
    ]
    for index, (count, payload, a_pointer, b_pointer) in enumerate(commands):
        if count == 0 or not GBA_BASE <= payload <= GBA_BASE + len(gba) - count * 16:
            raise SystemExit(f"invalid GBA P1 payload at 0x{source:X} command {index}")
        if not GBA_BASE <= a_pointer < GBA_BASE + len(gba):
            raise SystemExit(f"invalid GBA P1 A pointer at 0x{source:X} command {index}")
        if b_pointer and not GBA_BASE <= b_pointer <= GBA_BASE + len(gba) - 10:
            raise SystemExit(f"invalid GBA P1 B pointer at 0x{source:X} command {index}")
    return commands


def analyze_pair(gba: bytes, wsc10: bytes, spec: tuple[object, ...]) -> dict[str, object]:
    label, wsc_source, gba_source, expected_counts, expected_rule = spec
    parsed = parse_shoot_p1(wsc10, int(wsc_source))
    counts = list(parsed["counts"])
    if counts != expected_counts:
        raise SystemExit(f"commercial WSC P1 counts changed for {label}: {counts}")
    gba_commands = read_gba_commands(gba, int(gba_source))
    if [command[0] for command in gba_commands] != counts:
        raise SystemExit(f"commercial GBA P1 counts changed for {label}")

    generic_exact = 0
    shoot_exact = 0
    nonzero_word5 = 0
    null_b = 0
    non_null_b = 0
    a_mappings: set[tuple[int, int]] = set()
    b_mappings = []
    for index, (items, command) in enumerate(zip(parsed["payloads"], gba_commands, strict=True)):
        count, payload_pointer, a_pointer, b_pointer = command
        payload = payload_pointer - GBA_BASE
        actual_items = [
            gba[payload + item * 16:payload + (item + 1) * 16]
            for item in range(count)
        ]
        generic_items = [convert_payload_item(item) for item in items]
        shoot_items = [convert_shoot_payload_item(item) for item in items]
        generic_exact += sum(left == right for left, right in zip(generic_items, actual_items, strict=True))
        shoot_exact += sum(left == right for left, right in zip(shoot_items, actual_items, strict=True))
        nonzero_word5 += sum(struct.unpack_from("<H", item, 10)[0] != 0 for item in items)

        a_relative = int(parsed["a_relatives"][index])
        a_mappings.add((int(wsc_source) + a_relative, a_pointer - GBA_BASE))
        b_relative = int(parsed["b_relatives"][index])
        if b_relative == 0:
            if b_pointer != 0:
                raise SystemExit(f"commercial null B pointer changed for {label} command {index}")
            null_b += 1
        else:
            if b_pointer == 0:
                raise SystemExit(f"commercial non-null B pointer changed for {label} command {index}")
            wsc_b = wsc10[int(wsc_source) + b_relative:int(wsc_source) + b_relative + 10]
            gba_b_offset = b_pointer - GBA_BASE
            gba_b = gba[gba_b_offset:gba_b_offset + 10]
            if wsc_b != gba_b:
                raise SystemExit(f"commercial B record differs for {label} command {index}")
            non_null_b += 1
            b_mappings.append({
                "wsc_relative": b_relative,
                "wsc_physical": int(wsc_source) + b_relative,
                "gba_physical": gba_b_offset,
                "bytes": 10,
                "sha256": sha256(wsc_b),
                "exact": True,
            })

    item_count = sum(counts)
    if expected_rule == "generic-zero-tail" and generic_exact != item_count:
        raise SystemExit(f"generic payload oracle failed for {label}")
    if shoot_exact != item_count:
        raise SystemExit(f"complete Shoot-lineage payload oracle failed for {label}")

    a_rows = []
    for wsc_a, gba_a in sorted(a_mappings):
        a_rows.append({
            "wsc_physical": wsc_a,
            "gba_physical": gba_a,
            "common_prefix_8_exact": wsc10[wsc_a:wsc_a + 8] == gba[gba_a:gba_a + 8],
            "following_8_exact": wsc10[wsc_a + 8:wsc_a + 16] == gba[gba_a + 8:gba_a + 16],
            "conversion_proved": False,
        })

    return {
        "label": label,
        "wsc_source": wsc_source,
        "gba_source": gba_source,
        "command_count": len(counts),
        "counts": counts,
        "payload_items": item_count,
        "nonzero_wsc_word5_items": nonzero_word5,
        "expected_payload_rule": expected_rule,
        "generic_payload_items_exact": generic_exact,
        "shoot_lineage_payload_items_exact": shoot_exact,
        "null_b_commands_exact": null_b,
        "non_null_b_commands_exact": non_null_b,
        "non_null_b_mappings": b_mappings,
        "a_target_mappings": a_rows,
    }


def analyze_initializer_payloads(wsc15: bytes) -> list[dict[str, object]]:
    rows = []
    for source in INITIALIZER_SOURCES:
        parsed = parse_shoot_p1(wsc15, source)
        items = [item for payload in parsed["payloads"] for item in payload]
        nonzero_word5 = sum(struct.unpack_from("<H", item, 10)[0] != 0 for item in items)
        if nonzero_word5 != 0:
            raise SystemExit(f"initializer P1 word-5 population changed at 0x{source:X}")
        rows.append({
            "source": source,
            "command_count": parsed["command_count"],
            "counts": parsed["counts"],
            "payload_items": len(items),
            "nonzero_word5_items": nonzero_word5,
            "payload_rule_supported_by_commercial_oracle": True,
            "a_target_conversion_proved": False,
            "installed": False,
        })
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
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    pairs = [analyze_pair(gba, wsc10, spec) for spec in PAIR_SPECS]
    payload_items = sum(int(row["payload_items"]) for row in pairs)
    generic_exact = sum(int(row["generic_payload_items_exact"]) for row in pairs)
    shoot_exact = sum(int(row["shoot_lineage_payload_items_exact"]) for row in pairs)
    non_null_b = sum(int(row["non_null_b_commands_exact"]) for row in pairs)
    if (len(pairs), payload_items, generic_exact, shoot_exact, non_null_b) != (12, 283, 266, 283, 6):
        raise SystemExit("commercial P1 aggregate oracle changed")

    result = {
        "schema": 1,
        "kind": "digimon-direct-p1-commercial-oracle",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "aggregate": {
            "pair_count": len(pairs),
            "command_count": sum(int(row["command_count"]) for row in pairs),
            "payload_items": payload_items,
            "generic_zero_tail_items_exact": generic_exact,
            "shoot_lineage_items_exact": shoot_exact,
            "non_null_b_records_exact": non_null_b,
            "a_target_conversion_proved": False,
        },
        "pairs": pairs,
        "initializer_payload_applicability": analyze_initializer_payloads(wsc15),
        "claim_scope": (
            "commercial source-lineage proof for P1 command counts, 12-to-16-byte payload expansion, "
            "Shoot word-5 tail relocation, and null/non-null 10-byte B behavior; A-target conversion, "
            "initializer installation, runtime, visual output, audio, and supplied-save QA are excluded"
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
