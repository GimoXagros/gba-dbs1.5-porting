#!/usr/bin/env python3
"""Compare known WSC/GBA P4 behavior-table containers record by record."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
WSC_RECORD_BYTES = 0x20
GBA_RECORD_BYTES = 0x20
WSC_P4_FIELD = 4
GBA_P4_FIELD = 2
WSC_ITEM_BYTES = 0x24
GBA_ITEM_BYTES = 0x34


def parse_int(value: str) -> int:
    return int(value, 0)


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def gba_pointer(data: bytes, offset: int) -> int:
    value = struct.unpack_from("<I", data, offset)[0]
    if not GBA_BASE <= value < GBA_BASE + len(data):
        raise ValueError(f"invalid GBA ROM pointer 0x{value:08X} at 0x{offset:X}")
    return value - GBA_BASE


def parse_wsc_container(data: bytes, offset: int) -> dict[str, object]:
    table_relative, count = struct.unpack_from("<2H", data, offset)
    relatives = list(struct.unpack_from(f"<{count}H", data, offset + table_relative))
    items = []
    for index, relative in enumerate(relatives):
        item_offset = offset + relative
        items.append({
            "index": index,
            "offset": item_offset,
            "relative": relative,
            "u16": list(struct.unpack_from("<18H", data, item_offset)),
            "u32": list(struct.unpack_from("<9I", data, item_offset)),
        })
    return {
        "offset": offset,
        "table_relative": table_relative,
        "count": count,
        "record_relatives": relatives,
        "items": items,
    }


def parse_gba_container(data: bytes, offset: int) -> dict[str, object]:
    table_pointer, count = struct.unpack_from("<2I", data, offset)
    table_offset = table_pointer - GBA_BASE
    if not 0 <= table_offset <= len(data) - count * 4:
        raise ValueError(f"invalid GBA table pointer 0x{table_pointer:08X}")
    pointers = list(struct.unpack_from(f"<{count}I", data, table_offset))
    items = []
    for index, pointer in enumerate(pointers):
        item_offset = pointer - GBA_BASE
        if not 0 <= item_offset <= len(data) - GBA_ITEM_BYTES:
            raise ValueError(f"invalid GBA item pointer 0x{pointer:08X}")
        items.append({
            "index": index,
            "offset": item_offset,
            "u32": list(struct.unpack_from("<13I", data, item_offset)),
        })
    return {
        "offset": offset,
        "table_offset": table_offset,
        "count": count,
        "record_offsets": [value - GBA_BASE for value in pointers],
        "items": items,
    }


def expected_pointer(gba_items: list[dict[str, object]], relative: int,
                     wsc_records_start: int) -> int | None:
    if relative == 0:
        return 0
    delta = relative - wsc_records_start
    if delta < 0 or delta % WSC_ITEM_BYTES:
        return None
    index = delta // WSC_ITEM_BYTES
    if index >= len(gba_items):
        return None
    return GBA_BASE + int(gba_items[index]["offset"])


def compare_item(wsc_item: dict[str, object], gba_item: dict[str, object],
                 wsc_records_start: int, gba_items: list[dict[str, object]]) -> dict[str, object]:
    w16 = [int(value) for value in wsc_item["u16"]]
    w32 = [int(value) for value in wsc_item["u32"]]
    g32 = [int(value) for value in gba_item["u32"]]
    pointer_word_map = ((11, 6), (12, 7), (13, 8), (14, 9), (15, 10), (16, 11), (17, 12))
    pointer_checks = []
    for word_index, gba_index in pointer_word_map:
        expected = expected_pointer(gba_items, w16[word_index], wsc_records_start)
        pointer_checks.append({
            "wsc_u16_index": word_index,
            "gba_u32_index": gba_index,
            "wsc_relative": w16[word_index],
            "expected_gba": expected,
            "actual_gba": g32[gba_index],
            "matches": expected == g32[gba_index],
        })
    return {
        "index": wsc_item["index"],
        "wsc_offset": wsc_item["offset"],
        "gba_offset": gba_item["offset"],
        "wsc_u16": w16,
        "wsc_u32": w32,
        "gba_u32": g32,
        "direct_u32_checks": [
            {"wsc_index": index, "gba_index": index, "wsc": w32[index],
             "gba": g32[index], "matches": w32[index] == g32[index]}
            for index in range(3)
        ],
        "scalar_pairs": [
            {"name": "d1_high", "wsc": w16[3], "gba": g32[1] >> 16},
            {"name": "d3_low", "wsc": w16[6], "gba": g32[3] & 0xFFFF},
            {"name": "d3_high", "wsc": w16[7], "gba": g32[3] >> 16},
            {"name": "d4_low", "wsc": w16[8], "gba": g32[4] & 0xFFFF},
            {"name": "d4_high", "wsc": w16[9], "gba": g32[4] >> 16},
            {"name": "d5_low", "wsc": w16[10], "gba": g32[5] & 0xFFFF},
        ],
        "pointer_checks": pointer_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--wsc-base-table", type=parse_int, default=0x390000)
    parser.add_argument("--gba-base-table", type=parse_int, default=0x0D3FC0)
    parser.add_argument("--wsc-evolution-table", type=parse_int, default=0x3903C0)
    parser.add_argument("--gba-evolution-table", type=parse_int, default=0x0D42A0)
    parser.add_argument("--base-records", type=int, default=12)
    parser.add_argument("--evolution-records", type=int, default=0)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    pairs = []
    groups = (
        ("base", args.wsc_base_table, args.gba_base_table, args.base_records),
        ("evolution", args.wsc_evolution_table, args.gba_evolution_table,
         args.evolution_records),
    )
    for group, wsc_table, gba_table, count in groups:
        for runtime_id in range(count):
            wsc_record = wsc_table + runtime_id * WSC_RECORD_BYTES
            gba_record = gba_table + runtime_id * GBA_RECORD_BYTES
            wsc_target = wsc_pointer(wsc, wsc_record + WSC_P4_FIELD * 6)
            gba_target = gba_pointer(gba, gba_record + GBA_P4_FIELD * 4)
            wsc_container = parse_wsc_container(wsc, wsc_target)
            gba_container = parse_gba_container(gba, gba_target)
            if wsc_container["count"] != gba_container["count"]:
                raise ValueError(
                    f"{group} ID {runtime_id}: count mismatch "
                    f"{wsc_container['count']} != {gba_container['count']}"
                )
            wsc_records_start = min(int(value) for value in wsc_container["record_relatives"])
            items = [
                compare_item(w_item, g_item, wsc_records_start, gba_container["items"])
                for w_item, g_item in zip(wsc_container["items"], gba_container["items"])
            ]
            pairs.append({
                "group": group,
                "runtime_id": runtime_id,
                "wsc_target": wsc_target,
                "gba_target": gba_target,
                "count": wsc_container["count"],
                "wsc_records_start": wsc_records_start,
                "items": items,
            })

    all_items = [item for pair in pairs for item in pair["items"]]
    result = {
        "schema": 1,
        "gba_sha256": hashlib.sha256(gba).hexdigest().upper(),
        "wsc_sha256": hashlib.sha256(wsc).hexdigest().upper(),
        "pair_count": len(pairs),
        "item_count": len(all_items),
        "direct_u32_mismatch_count": sum(
            not check["matches"] for item in all_items for check in item["direct_u32_checks"]
        ),
        "pointer_mismatch_count": sum(
            not check["matches"] for item in all_items for check in item["pointer_checks"]
        ),
        "pairs": pairs,
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
