#!/usr/bin/env python3
"""Compare original WSC and retail GBA P1 command/payload containers."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_BASE = 0x08000000
WSC_RESOURCE_RECORD_BYTES = 0x20
GBA_RESOURCE_RECORD_BYTES = 0x20
WSC_P1_FIELD = 1
GBA_P1_FIELD = 7


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("--wsc-table", type=parse_int, default=0x390000)
    parser.add_argument("--gba-table", type=parse_int, default=0x0D3FC0)
    parser.add_argument("--records", type=int, default=11)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    pairs = []
    handler_maps: dict[tuple[int, int], set[tuple[int, int]]] = {}
    for runtime_id in range(args.records):
        wsc_record = args.wsc_table + runtime_id * WSC_RESOURCE_RECORD_BYTES
        gba_record = args.gba_table + runtime_id * GBA_RESOURCE_RECORD_BYTES
        wsc_target = wsc_pointer(wsc, wsc_record + WSC_P1_FIELD * 6)
        gba_target = gba_pointer(gba, gba_record + GBA_P1_FIELD * 4)

        wsc_table_relative, wsc_reserved, command_count, wsc_data_relative = struct.unpack_from(
            "<4H", wsc, wsc_target
        )
        if wsc_table_relative != 4 or wsc_reserved != 0:
            raise ValueError(f"unexpected WSC P1 header at 0x{wsc_target:X}")
        gba_table_pointer, gba_reserved = struct.unpack_from("<2I", gba, gba_target)
        gba_table_offset = gba_table_pointer - GBA_BASE
        if gba_reserved != 0 or gba_table_offset != gba_target + 8:
            raise ValueError(f"unexpected GBA P1 header at 0x{gba_target:X}")

        commands = []
        for command in range(command_count):
            w_entry = wsc_target + 8 + command * 8
            w_handler_a, w_handler_b, w_count, w_payload_relative = struct.unpack_from(
                "<4H", wsc, w_entry
            )
            # The retail GBA adds one platform-specific leading command.
            g_entry = gba_table_offset + (command + 1) * 16
            g_count, g_payload_pointer, g_handler_a, g_handler_b = struct.unpack_from(
                "<4I", gba, g_entry
            )
            g_payload = g_payload_pointer - GBA_BASE
            if not 0 <= g_payload <= len(gba) - g_count * 16:
                raise ValueError(f"invalid GBA P1 payload pointer at 0x{g_entry:X}")
            w_payload = wsc_target + w_payload_relative
            if not 0 <= w_payload <= len(wsc) - w_count * 12:
                raise ValueError(f"invalid WSC P1 payload relative at 0x{w_entry:X}")

            w_items = [wsc[w_payload + index * 12:w_payload + (index + 1) * 12]
                       for index in range(w_count)]
            g_items = [gba[g_payload + index * 16:g_payload + (index + 1) * 16]
                       for index in range(g_count)]
            item_matches = []
            all_first12_match = True
            all_tail_zero = True
            for g_index, g_item in enumerate(g_items):
                positions = [index for index, w_item in enumerate(w_items)
                             if w_item == g_item[:12]]
                w_same_index = w_items[g_index] if g_index < len(w_items) else None
                w_words = list(struct.unpack("<6H", w_same_index)) if w_same_index else None
                g_words = list(struct.unpack("<8H", g_item))
                all_first12_match &= bool(positions)
                all_tail_zero &= g_item[12:16] == bytes(4)
                item_matches.append({
                    "gba_index": g_index,
                    "wsc_indices": positions,
                    "first12_match": bool(positions),
                    "gba_tail_hex": g_item[12:16].hex(" "),
                    "same_index_wsc_u16": w_words,
                    "gba_u16": g_words,
                    "same_index_field_matches": [
                        w_words[field] == g_words[field] for field in range(6)
                    ] if w_words else None,
                })
            handler_maps.setdefault((w_handler_a, w_handler_b), set()).add(
                (g_handler_a, g_handler_b)
            )
            commands.append({
                "command": command,
                "wsc_entry": w_entry,
                "gba_entry": g_entry,
                "wsc_handlers": [w_handler_a, w_handler_b],
                "gba_handlers": [g_handler_a, g_handler_b],
                "wsc_count": w_count,
                "gba_count": g_count,
                "wsc_payload": w_payload,
                "gba_payload": g_payload,
                "all_gba_first12_found_in_wsc": all_first12_match,
                "all_gba_tail_zero": all_tail_zero,
                "item_matches": item_matches,
            })
        pairs.append({
            "runtime_id": runtime_id,
            "wsc_target": wsc_target,
            "gba_target": gba_target,
            "wsc_data_relative": wsc_data_relative,
            "command_count": command_count,
            "commands": commands,
        })

    commands = [command for pair in pairs for command in pair["commands"]]
    item_matches = [item for command in commands for item in command["item_matches"]]
    result = {
        "schema": 1,
        "gba_sha256": hashlib.sha256(gba).hexdigest().upper(),
        "wsc_sha256": hashlib.sha256(wsc).hexdigest().upper(),
        "pair_count": len(pairs),
        "command_count": len(commands),
        "payload_command_match_count": sum(
            command["all_gba_first12_found_in_wsc"] for command in commands
        ),
        "zero_tail_command_count": sum(command["all_gba_tail_zero"] for command in commands),
        "same_index_field_mismatch_counts": [
            sum(not item["same_index_field_matches"][field] for item in item_matches
                if item["same_index_field_matches"] is not None)
            for field in range(6)
        ],
        "handler_maps": [
            {
                "wsc_handlers": list(wsc_handlers),
                "gba_handler_pairs": [list(pair) for pair in sorted(gba_pairs)],
            }
            for wsc_handlers, gba_pairs in sorted(handler_maps.items())
        ],
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
