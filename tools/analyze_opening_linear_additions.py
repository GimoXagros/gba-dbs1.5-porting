#!/usr/bin/env python3
"""Bound the four WSC 1.5-only linear opening callbacks and dependencies.

This is a static integration ledger.  It identifies the exact commercial GBA
chain-edit sites, the four inserted WSC callback ranges, the two additional
resource records used only by those callbacks, and the commercial
object-constructor lineage needed for a native GBA translation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

import analyze_gba_opening_dispatch as gba_graph
import analyze_wsc_opening_dispatch as wsc_graph


GBA_BASE = 0x08000000
GBA_SHA256 = gba_graph.GBA_SHA256
WSC10_SHA256 = wsc_graph.WSC10_SHA256
WSC15_SHA256 = wsc_graph.WSC15_SHA256

ADDED_CALLBACKS = {
    7: (0x7077, 0x7407, "C3AC134789C3DE1983E8964696851CDEC636F3F95722DD8CF24F0ADD4346554F"),
    8: (0x7407, 0x7698, "4B1F3D651E981A3006E42C642CEFABCDFC5AE455F7B9BAB488FAA5493E8D3991"),
    9: (0x7698, 0x7992, "1A20D0D18BC4AB2E9C1ECDBF57D1BC4D2C959C79A7DF1445B7AC4E101A3DCAD7"),
    10: (0x7992, 0x7D28, "FB46FFCD4F9BD7D50ADDBFE824AD1A70E5295054902C22C0720421B8D3EE542E"),
}
ADDED_SELECTORS = {7: [14], 8: [8], 9: [9], 10: [3]}
ADDED_AUXILIARY_RECORDS = {7: 50, 10: 49}

WSC10_RESOURCE_TABLE = 0x390000
WSC15_RESOURCE_TABLE = 0x740000
RESOURCE_RECORD_BYTES = 0x20
RESOURCE_RECORD_HASHES = {
    49: "3C13689AC83F9F843AF1E3DD5A8AD149B1668DAEF9B50308EAE5DED20485557F",
    50: "FBB3EF67D4457F0BDA6EEB00183A5B206C0117307166E2FD66A363D14391835B",
}
WSC10_RESOURCE_RECORD_HASHES = {
    49: "30E1526075D1788F392C3CDAD83E0716CCA5EF18482917FE15A8965880A1B9C9",
    50: "3063B638AFA5F671D7A097FBC21136CFA27AA8D5747D997C3F2FDEF19158FF4A",
}

GBA_PRESENTATION_RESOURCE_VIEW = 0x0D42B8
GBA_PRESENTATION_RESOURCE_VIEW_HASH = (
    "0BEA8D4B6A937E0414EFC4BFCDC2EDF333F05A28462E708DE96F9E7A883F544D"
)
WSC10_EVOLUTION_TABLE = 0x3903C0
WSC15_EVOLUTION_TABLE = 0x7403C0
WSC10_EVOLUTION_TABLE_HASH = (
    "E049F913F204989EE1AD55F23691DAF09C07E4D040B608FAA64A8564EC44BAE0"
)
WSC15_EVOLUTION_TABLE_HASH = (
    "1E4067E36B203A10EF49A2227E5BE53C47F22591981E1FFBB43EF6F2DDBDC768"
)

WSC10_CREATOR_RANGE = (0x39FC37, 0x39FCDA)
WSC15_CREATOR_RANGE = (0x75A58C, 0x75A62F)
GBA_CONSUMER_RANGE = (0x088250, 0x088310)
CREATOR_HASHES = {
    "wsc_10": "5CF404BA13E908C5AC7AFC2F32466F71E76C01CF4C5D0CBBAE7D771719F6A1F3",
    "wsc_15": "93850B864BB816C3E7E1E2B1DBAB308A30C9F6DFE57B64A29EC2130E4817BEB0",
    "gba": "AAF329B99CD8BABB7A4CC6AE663C59C09C2E05B05C8288ED484FD694870EA27E",
}

GBA_PREDECESSOR = 0x08085118
GBA_EXISTING_SUCCESSOR = 0x08085454
GBA_NEXT_CALLBACK_ASSIGNMENT = 0x08516C
GBA_SELECTOR_ASSIGNMENT = 0x0851CC
EXPECTED_NEXT_CALLBACK_WORD = 0xE28F8E2E
EXPECTED_SELECTOR_WORD = 0xE3A08003


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def wsc_pointer(data: bytes, offset: int, bank_mask: int) -> dict[str, int]:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return {
        "offset": pointer_offset,
        "segment": segment,
        "bank": bank,
        "physical": ((bank & bank_mask) << 16) | bank_offset,
    }


def resource_record(
    data: bytes, table: int, record_id: int, bank_mask: int
) -> dict[str, object]:
    start = table + record_id * RESOURCE_RECORD_BYTES
    return {
        "record_id": record_id,
        "record_offset": start,
        "sha256": sha256(data[start:start + RESOURCE_RECORD_BYTES]),
        "pointer_targets": [
            wsc_pointer(data, start + field * 6, bank_mask)["physical"]
            for field in range(5)
        ],
    }


def find_gba_chain_sites(gba: bytes) -> dict[str, object]:
    start = GBA_PREDECESSOR - GBA_BASE
    end = GBA_EXISTING_SUCCESSOR - GBA_BASE
    setter_calls = gba_graph.find_calls(
        gba, gba_graph.SET_CALLBACK, start, end
    )
    assignments = [
        (call, gba_graph.resolve_r8_assignment(gba, call))
        for call in setter_calls
    ]
    next_edges = [
        (call, assignment)
        for call, assignment in assignments
        if assignment["target_address"] == GBA_EXISTING_SUCCESSOR
    ]
    if len(next_edges) != 1:
        raise ValueError(f"unexpected predecessor next edges: {next_edges}")
    setter_call, assignment = next_edges[0]
    if assignment["assignment_offset"] != GBA_NEXT_CALLBACK_ASSIGNMENT:
        raise ValueError(f"next-callback assignment moved: {assignment}")
    if struct.unpack_from("<I", gba, GBA_NEXT_CALLBACK_ASSIGNMENT)[0] != EXPECTED_NEXT_CALLBACK_WORD:
        raise ValueError("next-callback assignment instruction changed")

    character_calls = gba_graph.find_calls(
        gba, gba_graph.CHARACTER_CONSUMER, start, end
    )
    if len(character_calls) != 1:
        raise ValueError(f"unexpected predecessor character calls: {character_calls}")
    if gba_graph.r8_immediate_for_first_argument(gba, character_calls[0]) != 3:
        raise ValueError("predecessor selector is no longer 3")
    if struct.unpack_from("<I", gba, GBA_SELECTOR_ASSIGNMENT)[0] != EXPECTED_SELECTOR_WORD:
        raise ValueError("predecessor selector assignment instruction changed")
    return {
        "predecessor_callback": GBA_PREDECESSOR,
        "existing_successor": GBA_EXISTING_SUCCESSOR,
        "next_callback_assignment_offset": GBA_NEXT_CALLBACK_ASSIGNMENT,
        "next_callback_assignment_word": EXPECTED_NEXT_CALLBACK_WORD,
        "set_callback_call_offset": setter_call,
        "selector_assignment_offset": GBA_SELECTOR_ASSIGNMENT,
        "selector_assignment_word": EXPECTED_SELECTOR_WORD,
        "selector_before": 3,
        "selector_after": 13,
        "character_consumer_call_offset": character_calls[0],
    }


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
    bank = wsc15[0x75 * 0x10000:0x76 * 0x10000]
    callbacks = []
    for index, (start, end, expected) in ADDED_CALLBACKS.items():
        entry = new["functions"][index]
        if entry["physical_start"] != start:
            raise ValueError(f"WSC 1.5 callback {index} moved")
        if entry["population_targets"] != [new["functions"][index + 1]["physical_start"]]:
            raise ValueError(f"WSC 1.5 callback {index} chain changed")
        if entry["object_selector_arguments"] != ADDED_SELECTORS[index]:
            raise ValueError(f"WSC 1.5 callback {index} selector changed")
        require_hash(bank[start:end], expected, f"WSC 1.5 callback {index}")
        item = {
            "index": index,
            "physical_start": start,
            "physical_end": end,
            "bytes": end - start,
            "sha256": expected,
            "next_callback": entry["population_targets"][0],
            "object_selectors": entry["object_selector_arguments"],
        }
        if index in ADDED_AUXILIARY_RECORDS:
            item["auxiliary_resource_record"] = ADDED_AUXILIARY_RECORDS[index]
        callbacks.append(item)

    # The two complex callbacks index records 50 and 49 as
    # (record 45 + immediate 5/4).  Both invoke the same low-level source
    # loader pair used by the WSC object path.
    for address, immediate in ((0x7281, 5), (0x7B4D, 4)):
        pattern = bytes((0xBF, immediate, 0, 0xC1, 0xE7, 5, 0x81, 0xC7, 0xA0, 5))
        if bank[address:address + len(pattern)] != pattern:
            raise ValueError(f"auxiliary resource selector changed at {address:04X}")
    low_level_calls = {
        "load_primary": bytes.fromhex("9A 6E 22 FF 4F"),
        "load_palette_or_companion": bytes.fromhex("9A 89 23 FF 4F"),
    }
    for index in (7, 10):
        start, end, _ = ADDED_CALLBACKS[index]
        for label, pattern in low_level_calls.items():
            if bank[start:end].count(pattern) != 1:
                raise ValueError(f"callback {index} {label} call count changed")

    old_records = []
    new_records = []
    for record_id in (49, 50):
        old_record = resource_record(
            wsc10, WSC10_RESOURCE_TABLE, record_id, 0x3F
        )
        new_record = resource_record(
            wsc15, WSC15_RESOURCE_TABLE, record_id, 0x7F
        )
        if old_record["sha256"] != WSC10_RESOURCE_RECORD_HASHES[record_id]:
            raise ValueError(f"WSC 1.0 record {record_id} changed")
        if new_record["sha256"] != RESOURCE_RECORD_HASHES[record_id]:
            raise ValueError(f"WSC 1.5 record {record_id} changed")
        if old_record["sha256"] == new_record["sha256"]:
            raise ValueError(f"record {record_id} is not a Ver. 1.5 replacement")
        if any(
            old_target == new_target
            for old_target, new_target in zip(
                old_record["pointer_targets"], new_record["pointer_targets"]
            )
        ):
            raise ValueError(f"record {record_id} did not replace all pointer targets")
        old_records.append(old_record)
        new_records.append(new_record)

    require_hash(
        gba[
            GBA_PRESENTATION_RESOURCE_VIEW:
            GBA_PRESENTATION_RESOURCE_VIEW + 15 * RESOURCE_RECORD_BYTES
        ],
        GBA_PRESENTATION_RESOURCE_VIEW_HASH,
        "commercial GBA presentation resource view",
    )
    require_hash(
        wsc10[WSC10_EVOLUTION_TABLE:WSC10_EVOLUTION_TABLE + 15 * RESOURCE_RECORD_BYTES],
        WSC10_EVOLUTION_TABLE_HASH,
        "WSC 1.0 evolution presentation table",
    )
    require_hash(
        wsc15[WSC15_EVOLUTION_TABLE:WSC15_EVOLUTION_TABLE + 15 * RESOURCE_RECORD_BYTES],
        WSC15_EVOLUTION_TABLE_HASH,
        "WSC 1.5 evolution presentation table",
    )

    for label, data, (start, end) in (
        ("wsc_10", wsc10, WSC10_CREATOR_RANGE),
        ("wsc_15", wsc15, WSC15_CREATOR_RANGE),
        ("gba", gba, GBA_CONSUMER_RANGE),
    ):
        require_hash(data[start:end], CREATOR_HASHES[label], f"{label} object creator")

    if old["functions"][6]["object_selector_arguments"] != [3]:
        raise ValueError("WSC 1.0 predecessor selector changed")
    if new["functions"][6]["object_selector_arguments"] != [13]:
        raise ValueError("WSC 1.5 predecessor selector changed")

    result = {
        "schema": 1,
        "kind": "opening-linear-addition-integration-ledger",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "gba_chain_edit": find_gba_chain_sites(gba),
        "wsc15_added_callbacks": callbacks,
        "presentation_resource_views": {
            "commercial_gba": {
                "offset": GBA_PRESENTATION_RESOURCE_VIEW,
                "records": 15,
                "sha256": GBA_PRESENTATION_RESOURCE_VIEW_HASH,
            },
            "wsc_10": {
                "offset": WSC10_EVOLUTION_TABLE,
                "records": 15,
                "sha256": WSC10_EVOLUTION_TABLE_HASH,
            },
            "wsc_15": {
                "offset": WSC15_EVOLUTION_TABLE,
                "records": 15,
                "sha256": WSC15_EVOLUTION_TABLE_HASH,
            },
            "required_new_selector_records": [11, 12, 13, 14],
        },
        "auxiliary_resource_replacements": {
            "wsc_10": old_records,
            "wsc_15": new_records,
            "callback_7_uses_record": 50,
            "callback_10_uses_record": 49,
            "directly_consumed_pointer_fields": [0, 2],
        },
        "object_constructor_lineage": {
            "wsc_10_range": list(WSC10_CREATOR_RANGE),
            "wsc_15_range": list(WSC15_CREATOR_RANGE),
            "gba_range": list(GBA_CONSUMER_RANGE),
            "wsc_object_base": "0x0300:0x01CE",
            "wsc_object_stride": 0x42,
            "gba_object_base": 0x03002908,
            "gba_object_stride": 0x50,
            "wsc_resource_record_stride": 0x20,
            "gba_resource_record_stride": 0x20,
            "wsc_object_constructor": "4FFF:23F4",
            "gba_object_constructor": 0x080127E4,
            "wsc_companion_loader": "4FFF:2389",
            "gba_companion_loader": 0x080132EC,
            "unmapped_wsc_primary_loader": "4FFF:226E",
        },
        "claim_scope": (
            "Static bounds and native-constructor dependencies for the four "
            "WSC 1.5-only linear opening callbacks. The callbacks and the "
            "replacement resource records 49/50 are not yet translated; no "
            "runtime behavior is claimed."
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
