#!/usr/bin/env python3
"""Bound the resources and native ABI dependencies of Shoot initializer 7168.

This analyzer resolves every far P0/P1/P2 argument used directly by the
initializer, converts only the already-proved P0/P2 formats, and records the
distinct self-delimiting P1 boundary without pretending that the existing
Shoot-spawn converter applies.  It reads the three original ROMs only and
does not install data or perform runtime validation.
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

from build_full_asset_poc import build_asset  # type: ignore
from build_new_base_p1_assets import parse_source  # type: ignore
from convert_wsc_palette_block import convert_block  # type: ignore
from shoot_resource_conversion import parse_shoot_p1  # type: ignore


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
OVERLAY_BASE = 0x740900

ROOT_START = 0x747A68
ROOT_END = 0x747E72
ROOT_SHA256 = "F0F825AE96C188F14EA8ED89A78C18D9F5D752EAD123FE2C02FD0056AB51B8C3"
MENU_CALL_RAW = 0x773143

ANALYSIS_P0_TARGET = 0x600000
P0_EXPECTED = {
    0x3D5F80: (128, 4, 64, 0, 0, "5ACD83AA00C725C4CAEA57D848D396293C97F4E3855B9EE93A99ADEDD3EBDA84"),
    0x3914E0: (41408, 50, 4872, 61, 35616, "619ED6DF786883776019D3BB577110FE395CF460EF062DAC770796E2FA5434CD"),
    0x3D44E0: (224, 8, 136, 0, 0, "0A230748962D9D8B4A59033E85124F4CBC9EA5CF532CB637C1A1BE23E1EA8E97"),
    0x3D0CA0: (448, 18, 288, 0, 0, "3C38F749BFABB4FE0C4F1007355B6E6B53CE2A1BD224532FCD83948483927D05"),
    0x3D7D30: (64, 4, 16, 0, 0, "4B55A39D883D0E8C2FBCD0987259585DA9843A2BE2D8FF545F3BA6864A452EA0"),
}
P2_EXPECTED = {
    0x3D4B20: "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C",
    0x3D7640: "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD",
    0x3D7A90: "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1",
    0x3D6B16: "6410DA9E5AF68D6D44199795D1B2DB6F1E5B7BFB8452017947C2C0BD94B431C0",
}
P1_EXPECTED = {
    0x3CF410: {
        "counts": [7, 8, 2, 7, 2, 8],
        "a_relative": 0x1D6,
        "a_records": 4,
        "a_sha256": "288E4E622381DA37DE78603185535B635CB0532FC289C15EDB9A0A84B201D4DE",
        "b_relatives": [0, 0x1CC],
        "b_1cc_sha256": "FCFBC8BCD43B13D0EC8F598145BDEBD2090350FD054156C7F7B1EE64259356C1",
        "generic_rejection": "WSC P1 command 6 has no payload items",
    },
    0x3BD730: {
        "counts": [12, 4, 2, 12, 12, 4, 6, 2, 12, 5, 4, 16, 18],
        "a_relative": 0x588,
        "a_records": 50,
        "a_sha256": "A213B4389946673C53C416F17A139BAD66354ABEE5C15437C638DBC829B6C30B",
        "b_relatives": [0],
        "generic_rejection": "leading-command B record underflows source container",
    },
}


# Each signature includes the argument pushes and far call.  Pointer triples
# below are stored in natural (offset, segment, bank) order; the x86 pushes
# appear in reverse order because of the calling convention.
CONSTRUCTORS = (
    {
        "label": "active_player_presentation",
        "range": (0x7270, 0x729F),
        "sha256": "B5F9EC6CB75D4EAFDFF2A8FA9A8E0464F63ECAB34FBB33D4B7FB2F602774E71A",
        "call": "4FFF:23F4",
        "resources": {
            "p2": (0x0000, 0x24B2, 0x00BD),
            "p0": (0x0000, 0x25F8, 0x00BD),
            "p1": (0x0000, 0x2F41, 0x00BC),
        },
    },
    {
        "label": "rules_object_presentation",
        "range": (0x7329, 0x7358),
        "sha256": "85927098EE897B2724D037DD5F45AD750B349FC56ED7617A8D3C82B25E257859",
        "call": "4FFF:23F4",
        "resources": {
            "p2": (0x0000, 0x2764, 0x00BD),
            "p0": (0x0000, 0x214E, 0x00B9),
            "p1": (0x0000, 0x2D73, 0x00BB),
        },
    },
)

DIRECT_LOADS = (
    ("active_p2_initial", "p2", 0x72B5, 0x72C7, "725398D6539224768C761E625EF9E9FC2BD4A2CB9E17CDA4CB03FBC254D2F365", (0, 0x24B2, 0xBD), "4FFF:2389"),
    ("rules_p2_initial", "p2", 0x736E, 0x7380, "E8B474A6A788A476DC942B24A9AEEE67626DA72CAE7F7389A8F42842DCBAA01A", (0, 0x2764, 0xBD), "4FFF:2389"),
    ("extra_p2_slot_5", "p2", 0x7394, 0x73A6, "C78AF345F58B6110AC0B521CB844A8FE57CDE633754CC8E66CC0C845585EAB15", (0, 0x27A9, 0xBD), "4FFF:2389"),
    ("extra_p0_6d", "p0", 0x73A9, 0x73BC, "47D92B70D672EC56607CD907A6878EB35FAD0152C954211E8AEC79EF490EBC88", (0, 0x244E, 0xBD), "4FFF:226E"),
    ("extra_p0_137", "p0", 0x73BF, 0x73D3, "B807E8422C27FD2CE3EB3F6EE6C89A1A6F31EC355571B848FCF9245DE1630EFF", (0, 0x20CA, 0xBD), "4FFF:226E"),
    ("extra_p0_91", "p0", 0x74A2, 0x74B6, "578A67E47CA58D225C3E9D932BD54A8379CE53C52DBDF89F8102B1CAA3C246AF", (0, 0x27D3, 0xBD), "4FFF:226E"),
    ("extra_p2_offset_26", "p2", 0x74B9, 0x74CB, "6E07B73E87EB63E4B9CBA26E67565151CF462BC0485B6D810F7835759F5654E1", (0x26, 0x26AF, 0xBD), "4FFF:2389"),
)

CREATOR_ORACLE_RANGES = {
    "wsc_10": (0x39FC37, 0x39FCDA, "5CF404BA13E908C5AC7AFC2F32466F71E76C01CF4C5D0CBBAE7D771719F6A1F3"),
    "wsc_15": (0x75A58C, 0x75A62F, "93850B864BB816C3E7E1E2B1DBAB308A30C9F6DFE57B64A29EC2130E4817BEB0"),
    "gba": (0x088250, 0x088310, "AAF329B99CD8BABB7A4CC6AE663C59C09C2E05B05C8288ED484FD694870EA27E"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 changed: expected {expected}, got {actual}")


def resolve_pointer(rom: bytes, triple: tuple[int, int, int]) -> int:
    pointer_offset, segment, bank = triple
    bank_count = len(rom) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise SystemExit("WSC ROM bank population is not a power of two")
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def occurrences(data: bytes, needle: bytes) -> list[int]:
    result = []
    cursor = 0
    while True:
        found = data.find(needle, cursor)
        if found < 0:
            return result
        result.append(found)
        cursor = found + 1


def verify_initializer_signatures(wsc15: bytes) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    require_hash(wsc15[ROOT_START:ROOT_END], ROOT_SHA256, "Shoot initializer and local tables")
    if wsc15[MENU_CALL_RAW:MENU_CALL_RAW + 5] != bytes.fromhex("9A 68 71 90 40"):
        raise SystemExit("menu route no longer calls 4090:7168")
    overlay = wsc15[OVERLAY_BASE:OVERLAY_BASE + 0x10000]

    constructors = []
    for spec in CONSTRUCTORS:
        start, end = spec["range"]
        require_hash(overlay[start:end], spec["sha256"], spec["label"])
        resolved = {
            kind: {
                "pointer_offset": triple[0],
                "segment": triple[1],
                "bank": triple[2],
                "physical": resolve_pointer(wsc15, triple),
            }
            for kind, triple in spec["resources"].items()
        }
        constructors.append({
            "label": spec["label"],
            "overlay_range": [start, end],
            "physical_range": [OVERLAY_BASE + start, OVERLAY_BASE + end],
            "signature_sha256": spec["sha256"],
            "call": spec["call"],
            "resources": resolved,
        })

    direct = []
    for label, kind, start, end, expected, triple, call in DIRECT_LOADS:
        require_hash(overlay[start:end], expected, label)
        direct.append({
            "label": label,
            "kind": kind,
            "overlay_range": [start, end],
            "physical_range": [OVERLAY_BASE + start, OVERLAY_BASE + end],
            "signature_sha256": expected,
            "call": call,
            "pointer": {
                "pointer_offset": triple[0],
                "segment": triple[1],
                "bank": triple[2],
                "physical": resolve_pointer(wsc15, triple),
            },
        })
    return constructors, direct


def analyze_p0(wsc15: bytes) -> list[dict[str, object]]:
    rows = []
    for source, expected in sorted(P0_EXPECTED.items()):
        blob, details = build_asset(
            wsc15,
            wsc_header=source,
            target_header=ANALYSIS_P0_TARGET,
            expected_layout_entries=None,
            expected_layout_record_bytes=None,
            expected_descriptor_entries=None,
            expected_tile_bytes=None,
        )
        expected_bytes, layouts, layout_bytes, descriptors, tile_bytes, digest = expected
        actual = (
            len(blob),
            details["layout_entries"],
            details["layout_record_bytes"],
            details["descriptor_entries"],
            details["tile_payload_bytes"],
            sha256(blob),
        )
        if actual != expected:
            raise SystemExit(f"P0 topology changed at 0x{source:X}: {actual}")
        rows.append({
            "source": source,
            "analysis_target": ANALYSIS_P0_TARGET,
            "bytes": expected_bytes,
            "layout_entries": layouts,
            "layout_record_bytes": layout_bytes,
            "descriptor_entries": descriptors,
            "tile_payload_bytes": tile_bytes,
            "relocatable_sha256": digest,
        })
    return rows


def analyze_p2(gba: bytes, wsc15: bytes) -> list[dict[str, object]]:
    spawn = convert_block(wsc15[0x3D7AF0:0x3D7AF0 + 38])
    rows = []
    for source, expected in sorted(P2_EXPECTED.items()):
        blob = convert_block(wsc15[source:source + 38])
        require_hash(blob, expected, f"converted P2 0x{source:X}")
        rows.append({
            "source": source,
            "source_bytes": 38,
            "converted_bytes": 40,
            "converted_sha256": expected,
            "commercial_gba_exact_occurrences": occurrences(gba, blob),
            "commercial_gba_exact_addresses": [
                GBA_BASE + offset for offset in occurrences(gba, blob)
            ],
            "byte_identical_to_shoot_spawn_p2_source_3d7af0": blob == spawn,
        })
    if rows[0]["source"] != 0x3D4B20 or not rows[0]["byte_identical_to_shoot_spawn_p2_source_3d7af0"]:
        raise SystemExit("active initializer P2 no longer matches the installed Shoot-spawn source")
    return rows


def analyze_p1(wsc15: bytes) -> list[dict[str, object]]:
    rows = []
    for source, expected in sorted(P1_EXPECTED.items()):
        parsed = parse_shoot_p1(wsc15, source)
        counts = list(parsed["counts"])
        if counts != expected["counts"]:
            raise SystemExit(f"P1 command counts changed at 0x{source:X}: {counts}")
        a_relatives = sorted(set(parsed["a_relatives"]))
        if a_relatives != [expected["a_relative"]]:
            raise SystemExit(f"P1 A table base changed at 0x{source:X}: {a_relatives}")
        word1_indices = [
            struct.unpack_from("<H", item, 2)[0]
            for payload in parsed["payloads"]
            for item in payload
        ]
        a_records = max(word1_indices) + 1
        if a_records != expected["a_records"]:
            raise SystemExit(f"P1 A record population changed at 0x{source:X}")
        a_start = source + expected["a_relative"]
        a_table = wsc15[a_start:a_start + a_records * 8]
        require_hash(a_table, expected["a_sha256"], f"P1 A table 0x{source:X}")
        b_relatives = sorted(set(parsed["b_relatives"]))
        if b_relatives != expected["b_relatives"]:
            raise SystemExit(f"P1 B record population changed at 0x{source:X}: {b_relatives}")
        b_records = []
        for relative in b_relatives:
            if relative == 0:
                continue
            record = wsc15[source + relative:source + relative + 10]
            digest = sha256(record)
            key = f"b_{relative:x}_sha256"
            if digest != expected[key]:
                raise SystemExit(f"P1 B record changed at 0x{source + relative:X}")
            b_records.append({"relative": relative, "bytes": 10, "sha256": digest})

        rejection = None
        try:
            parse_source(wsc15, source)
        except ValueError as error:
            rejection = str(error)
        if rejection != expected["generic_rejection"]:
            raise SystemExit(f"generic P1 converter boundary changed at 0x{source:X}: {rejection}")

        payload_blob = b"".join(item for payload in parsed["payloads"] for item in payload)
        rows.append({
            "source": source,
            "variant": "self-delimiting Shoot-lineage P1",
            "logical_commands": len(counts),
            "counts": counts,
            "payload_items": sum(counts),
            "payload_bytes": len(payload_blob),
            "payload_sha256": sha256(payload_blob),
            "max_word1_index": max(word1_indices),
            "a_table": {
                "relative": expected["a_relative"],
                "records": a_records,
                "bytes": len(a_table),
                "sha256": expected["a_sha256"],
            },
            "null_b_pointer_commands": list(parsed["b_relatives"]).count(0),
            "non_null_b_records": b_records,
            "existing_generic_converter_rejection": rejection,
            "existing_spawn_converter_compatible": False,
            "required_before_conversion": [
                "preserve null B pointers and relocate any non-null 10-byte B record",
                "copy/convert the complete A table sized by the largest payload word-1 index",
                "prove the 12-byte to 16-byte payload and A-table rules against a commercial direct-format oracle",
            ],
        })
    return rows


def analyze_native_boundaries(gba: bytes, wsc10: bytes, wsc15: bytes) -> dict[str, object]:
    for label, data in (("wsc_10", wsc10), ("wsc_15", wsc15), ("gba", gba)):
        start, end, digest = CREATOR_ORACLE_RANGES[label]
        require_hash(data[start:end], digest, f"{label} constructor oracle")

    wsc_global_signature = wsc15[0x747E72:0x747E84]
    require_hash(
        wsc_global_signature,
        "06E74CC5EE7B7899348E9415C313BF2167B89CFA5C64D88ADC37D9552C05A8F6",
        "WSC Shoot player-global load",
    )
    require_hash(
        gba[0x370104:0x370114],
        "691C5248D4D14DB6B42A0DFE8CA03022526228EADF2B5472A3982AFB351C9DB3",
        "GBA player-global load",
    )
    globals_gba = struct.unpack_from("<II", gba, 0x370254)
    if globals_gba != (0x0300489C, 0x030048A0):
        raise SystemExit(f"GBA player-global literals changed: {globals_gba}")

    allocator = wsc15[0x7456C5:0x7456DD]
    require_hash(
        allocator,
        "ECFC0E5FD38BE2042835F9C70E8AFE12B7F8CA2720B290B7FADA5B4B7F7F768C",
        "WSC ES:071E allocation call",
    )
    old_071e_refs = sum(
        wsc10.count(pattern)
        for pattern in (
            bytes.fromhex("26 8B 36 1E 07"),
            bytes.fromhex("26 8B 3E 1E 07"),
            bytes.fromhex("68 1E 07"),
        )
    )
    if old_071e_refs != 0:
        raise SystemExit("WSC 1.0 unexpectedly contains an ES:071E object reference")

    return {
        "proved_imports": [
            {"wsc15": "4FFF:23F4", "gba": 0x080127E4, "role": "presentation constructor"},
            {"wsc15": "4FFF:24CB", "gba": 0x08012874, "role": "presentation event"},
            {"wsc15": "4FFF:2389", "gba": 0x080132EC, "role": "companion/palette loader"},
        ],
        "constructor_lineage_oracles": {
            label: {
                "range": [row[0], row[1]],
                "sha256": row[2],
            }
            for label, row in CREATOR_ORACLE_RANGES.items()
        },
        "player_globals": [
            {"wsc15": "ES:065C", "gba_pointer_slot": globals_gba[0]},
            {"wsc15": "ES:065E", "gba_pointer_slot": globals_gba[1]},
        ],
        "ver15_only_aux_object": {
            "wsc_storage": "ES:071E",
            "allocator_call_raw_range": [0x7456C5, 0x7456DD],
            "allocator_call_sha256": sha256(allocator),
            "allocator": "4090:172A",
            "callback": "4090:5134",
            "allocation_id": 0x343,
            "wsc10_matching_storage_references": old_071e_refs,
            "candidate_native_gba_allocator": 0x08352374,
            "status": "unresolved: storage lifetime and allocator arguments must be bound without guessing a GBA RAM address",
        },
        "unresolved_initializer_calls": [
            "7CCF:0FC4 hardware/global preparation",
            "4090:36C0 common fighter/stage setup",
            "4090:2E74 character presentation setup",
            "4FFF:226E primary P0 loader (may be bypassed only through a proved native constructor path)",
        ],
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
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    constructors, direct_loads = verify_initializer_signatures(wsc15)
    result = {
        "schema": 1,
        "kind": "digimon-shoot-7168-initializer-resource-boundary",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "initializer": {
            "entry": "4090:7168",
            "raw_range": [ROOT_START, ROOT_END],
            "bytes": ROOT_END - ROOT_START,
            "sha256": ROOT_SHA256,
            "menu_call_raw": MENU_CALL_RAW,
            "assigned_callbacks": ["4090:7792", "4090:88F6"],
        },
        "constructors": constructors,
        "direct_loads": direct_loads,
        "converted_format_boundaries": {
            "p0": analyze_p0(wsc15),
            "p2": analyze_p2(gba, wsc15),
            "p1": analyze_p1(wsc15),
        },
        "native_abi_boundaries": analyze_native_boundaries(gba, wsc10, wsc15),
        "integration_status": {
            "assets_installed_by_this_analyzer": False,
            "gba_menu_route_installed": False,
            "initializer_translated": False,
            "upper_state_graph_translated": False,
            "controller_9908_translated": False,
            "runtime_or_save_used": False,
        },
        "claim_scope": (
            "exact source pointer resolution, deterministic P0/P2 conversion, P1 topology, "
            "and native ABI/unresolved boundaries only; no ROM writes, menu reachability, "
            "initializer/controller implementation, visual output, runtime, or supplied-save QA"
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
