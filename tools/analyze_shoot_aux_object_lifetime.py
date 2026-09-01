#!/usr/bin/env python3
"""Prove the Ver. 1.5 Shoot auxiliary-object allocator and storage boundary.

The WSC initializer creates the object referenced by ES:071E through pool 5.
This analyzer exhaustively guards the direct ES:071E consumers, decodes the
source allocator arguments, and proves the matching native GBA allocator ABI
from its implementation and every commercial call site.  It is read-only and
does not use an emulator or the supplied save.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

WSC_ALLOC_CALL_RANGE = (0x7456C5, 0x7456DD)
WSC_ALLOC_CALL_SHA256 = (
    "ECFC0E5FD38BE2042835F9C70E8AFE12B7F8CA2720B290B7FADA5B4B7F7F768C"
)
WSC_ALLOCATOR_RANGE = (0x74202A, 0x74211E)
WSC_ALLOCATOR_SHA256 = (
    "D855573FE2DF49D006A7E8DC022DBEBDD592A9F7DBE4596FACD74B00E1E68755"
)
WSC_RELEASE_RANGE = (0x74211E, 0x742187)
WSC_RELEASE_SHA256 = (
    "EA4B8DFD5E2C23DC194CF4AB8E7432D4223BC843F822F069D45679A66490BBCA"
)
WSC_DIRECT_REFERENCE_BYTES = {
    0x740996: bytes.fromhex("26 8B 3E 1E 07"),
    0x740AEE: bytes.fromhex("26 8B 3E 1E 07"),
    0x7456EA: bytes.fromhex("26 8B 36 1E 07"),
    0x747BCF: bytes.fromhex("26 8B 36 1E 07"),
}
WSC10_LINEAGE_ALLOC_RANGE = (0x394971, 0x394989)
WSC10_LINEAGE_ALLOC_SHA256 = (
    "34EA36FE5F0B298FD1E82889470B7CFE86DEAD887D23A943847B4216902328A5"
)
WSC10_LINEAGE_INIT_RANGE = (0x394971, 0x394A2D)
WSC10_LINEAGE_INIT_SHA256 = (
    "56F542F9B48BBA7E98AD26F1F2896BEEF2E903AE6163C97BDFBD5F9FAE55CE4B"
)
WSC10_CALLBACK_HEAD_RANGE = (0x394CBE, 0x394D52)
WSC10_CALLBACK_HEAD_SHA256 = (
    "E267025309BAE7C1604F985C12827ED54D1FF362E1B01D96C31C3DF2796D62FC"
)
WSC15_LINEAGE_INIT_RANGE = (0x7456C5, 0x74577E)
WSC15_LINEAGE_INIT_SHA256 = (
    "8388F9DD991C930441BF191C95D2761580D71FC8F1996B14BAF59DFA6C82D9B4"
)
WSC15_CALLBACK_HEAD_RANGE = (0x745A34, 0x745AC8)
WSC15_CALLBACK_HEAD_SHA256 = (
    "D8F0DDECA4DAE386799C456D32D8DD45EA5EA9840E07178EFC8D565F2C23839C"
)

GBA_ALLOCATOR = 0x08352374
GBA_RELEASE = 0x083524C4
GBA_ALLOCATOR_RANGE = (0x352374, 0x35249C)
GBA_ALLOCATOR_SHA256 = (
    "B77263F36C749526F81F7620FD64BB5B800D42A291759B786E84BCB888ECBDEA"
)
GBA_RELEASE_RANGE = (0x3524C4, 0x35255C)
GBA_RELEASE_SHA256 = (
    "747F0C5921CB010659008C690597703472E313220A1B809501D90AA82FEA36A8"
)
GBA_LINEAGE_INIT_RANGE = (0x36FE6C, 0x370034)
GBA_LINEAGE_INIT_SHA256 = (
    "76FFA816A5E89667A947B9A046D1B94FE2D1F1AD0F79901A312E7CA4DE3FBF67"
)
GBA_CALLBACK_HEAD_RANGE = (0x3703EC, 0x370490)
GBA_CALLBACK_HEAD_SHA256 = (
    "F50DE6E3F74F5E7DB815EA91804A89CA72CCBF6923D15D30748893533CD0D963"
)
GBA_LINEAGE_STORAGE = 0x03004D3C
GBA_LINEAGE_CALLBACK = 0x083703EC
GBA_LINEAGE_STORAGE_LITERALS = (0x0C98FC, 0x0C9B98, 0x37008C, 0x370098)
GBA_ALLOCATOR_CALLS = (
    0x3411A4, 0x352BAC, 0x352BE8, 0x359424, 0x35CEC8, 0x35D104,
    0x35D388, 0x35D65C, 0x35D870, 0x35DAB4, 0x35DDE8, 0x35DE28,
    0x36D5DC, 0x36FE9C, 0x3727B4, 0x3729A4, 0x372A68, 0x3775E0,
    0x378908, 0x378B04, 0x378CF0, 0x379090,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if expected and actual != expected:
        raise SystemExit(f"{label} SHA-256 changed: expected {expected}, got {actual}")


def all_offsets(data: bytes, needle: bytes) -> list[int]:
    rows = []
    cursor = 0
    while True:
        found = data.find(needle, cursor)
        if found < 0:
            return rows
        rows.append(found)
        cursor = found + 1


def arm_branch_target(address: int, word: int) -> int | None:
    if ((word >> 25) & 7) != 5 or not (word & 0x01000000):
        return None
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def ror32(value: int, shift: int) -> int:
    shift &= 31
    if not shift:
        return value & 0xFFFFFFFF
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF


def producer_value(gba: bytes, offset: int, register: int = 8) -> int | None:
    """Decode the compiler's MOV-immediate or PC-relative LDR producer."""
    word = struct.unpack_from("<I", gba, offset)[0]
    if (
        ((word >> 25) & 7) == 1
        and ((word >> 21) & 0xF) == 13
        and ((word >> 12) & 0xF) == register
    ):
        return ror32(word & 0xFF, ((word >> 8) & 0xF) * 2)
    if (
        (word & 0x0E3F0000) == 0x041F0000
        and word & (1 << 20)
        and ((word >> 12) & 0xF) == register
    ):
        immediate = word & 0xFFF
        address = GBA_BASE + offset + 8
        address += immediate if word & (1 << 23) else -immediate
        raw = address - GBA_BASE
        if not 0 <= raw <= len(gba) - 4:
            raise SystemExit(f"literal for 0x{GBA_BASE + offset:08X} is outside ROM")
        return struct.unpack_from("<I", gba, raw)[0]
    return None


def commercial_allocator_calls(gba: bytes) -> list[dict[str, object]]:
    actual = []
    for offset in range(0, len(gba) - 3, 4):
        word = struct.unpack_from("<I", gba, offset)[0]
        if arm_branch_target(GBA_BASE + offset, word) == GBA_ALLOCATOR:
            actual.append(offset)
    if tuple(actual) != GBA_ALLOCATOR_CALLS:
        raise SystemExit(f"commercial allocator call population changed: {actual}")

    rows = []
    for call in actual:
        push_sites = []
        for site in range(call - 0x50, call, 4):
            word = struct.unpack_from("<I", gba, site)[0]
            if (word & 0xFFFF0000) != 0xE92D0000:
                continue
            mask = word & 0xFFFF
            if mask and not (mask & (mask - 1)):
                push_sites.append(site)
        push_sites = push_sites[-7:]
        if len(push_sites) != 7:
            raise SystemExit(f"allocator push shape changed at 0x{GBA_BASE + call:08X}")

        def pushed_value(argument: int) -> int | None:
            site = push_sites[argument]
            word = struct.unpack_from("<I", gba, site)[0]
            register = (word & 0xFFFF).bit_length() - 1
            # The compiler sometimes reuses the same zero-valued register for
            # adjacent arguments, so search to the start of the bounded call
            # setup and take the closest recognized producer.
            for producer in range(site - 4, call - 0x50 - 1, -4):
                value = producer_value(gba, producer, register)
                if value is not None:
                    return value
            return None

        selector = pushed_value(6)
        if selector is None:
            raise SystemExit(f"allocator selector is no longer immediate at 0x{GBA_BASE + call:08X}")
        rows.append({
            "call_offset": call,
            "call_address": GBA_BASE + call,
            "destination_pointer_slot": pushed_value(0),
            "callback": pushed_value(2),
            "allocation_id": pushed_value(4),
            "arg5": pushed_value(5),
            "pool_selector": selector,
        })
    return rows


def require_wsc_boundary(wsc10: bytes, wsc15: bytes) -> dict[str, object]:
    start, end = WSC_ALLOC_CALL_RANGE
    require_hash(wsc15[start:end], WSC_ALLOC_CALL_SHA256, "WSC Shoot allocation call")
    expected_call = bytes.fromhex(
        "6A 05 6A 00 68 43 03 68 90 40 68 34 51 68 00 10 68 1E 07 9A 2A 17 90 40"
    )
    if wsc15[start:end] != expected_call:
        raise SystemExit("WSC Shoot allocation arguments changed")
    start, end = WSC_ALLOCATOR_RANGE
    require_hash(wsc15[start:end], WSC_ALLOCATOR_SHA256, "WSC object allocator")
    start, end = WSC_RELEASE_RANGE
    require_hash(wsc15[start:end], WSC_RELEASE_SHA256, "WSC object release")

    expected_refs = sorted(WSC_DIRECT_REFERENCE_BYTES)
    for raw, encoded in WSC_DIRECT_REFERENCE_BYTES.items():
        if wsc15[raw:raw + len(encoded)] != encoded:
            raise SystemExit(f"ES:071E reference changed at 0x{raw:X}")
    discovered = sorted(
        set(all_offsets(wsc15, bytes.fromhex("26 8B 3E 1E 07")))
        | set(all_offsets(wsc15, bytes.fromhex("26 8B 36 1E 07")))
    )
    if discovered != expected_refs:
        raise SystemExit(f"ES:071E direct-reference population changed: {discovered}")
    old = sorted(
        set(all_offsets(wsc10, bytes.fromhex("26 8B 3E 1E 07")))
        | set(all_offsets(wsc10, bytes.fromhex("26 8B 36 1E 07")))
        | set(all_offsets(wsc10, bytes.fromhex("68 1E 07")))
    )
    if old:
        raise SystemExit(f"WSC 1.0 unexpectedly references ES:071E: {old}")
    if wsc15[0x747BCF:0x747BDD] != bytes.fromhex(
        "26 8B 36 1E 07 C7 04 F6 88 C7 44 02 90 40"
    ):
        raise SystemExit("auxiliary object no longer transitions to callback 4090:88F6")
    return {
        "storage": "ES:071E",
        "allocation_call_range": list(WSC_ALLOC_CALL_RANGE),
        "allocation_call_sha256": WSC_ALLOC_CALL_SHA256,
        "arguments": {
            "destination_far_pointer": "1000:071E",
            "callback_far_pointer": "4090:5134",
            "allocation_id": 0x343,
            "arg5": 0,
            "pool_selector": 5,
        },
        "allocator": {
            "entry": "4090:172A",
            "range": list(WSC_ALLOCATOR_RANGE),
            "sha256": WSC_ALLOCATOR_SHA256,
            "proved_parameter_reads": {
                "destination_offset_segment": ["bp+06", "bp+08"],
                "callback_offset_segment": ["bp+0A", "bp+0C"],
                "allocation_id_arg5": ["bp+0E", "bp+10"],
                "pool_selector": "bp+12",
            },
        },
        "direct_consumers": [
            {"raw": 0x740996, "role": "screen-effect interrupt reads object field +BE"},
            {"raw": 0x740AEE, "role": "screen-effect interrupt reads object field +BE"},
            {"raw": 0x7456EA, "role": "initializer configures newly allocated object"},
            {"raw": 0x747BCF, "role": "initializer assigns callback 4090:88F6"},
        ],
        "callback_transition": "4090:5134 -> 4090:88F6 before initializer return",
        "external_release_through_es_071e": False,
        "wsc10_matching_reference_count": 0,
    }


def require_commercial_lineage(
    gba: bytes, wsc10: bytes, wsc15: bytes, calls: list[dict[str, object]]
) -> dict[str, object]:
    for data, byte_range, digest, label in (
        (wsc10, WSC10_LINEAGE_ALLOC_RANGE, WSC10_LINEAGE_ALLOC_SHA256, "WSC 1.0 lineage allocation"),
        (wsc10, WSC10_LINEAGE_INIT_RANGE, WSC10_LINEAGE_INIT_SHA256, "WSC 1.0 lineage initializer"),
        (wsc10, WSC10_CALLBACK_HEAD_RANGE, WSC10_CALLBACK_HEAD_SHA256, "WSC 1.0 lineage callback"),
        (wsc15, WSC15_LINEAGE_INIT_RANGE, WSC15_LINEAGE_INIT_SHA256, "WSC 1.5 lineage initializer"),
        (wsc15, WSC15_CALLBACK_HEAD_RANGE, WSC15_CALLBACK_HEAD_SHA256, "WSC 1.5 lineage callback"),
        (gba, GBA_LINEAGE_INIT_RANGE, GBA_LINEAGE_INIT_SHA256, "GBA lineage initializer"),
        (gba, GBA_CALLBACK_HEAD_RANGE, GBA_CALLBACK_HEAD_SHA256, "GBA lineage callback"),
    ):
        require_hash(data[byte_range[0]:byte_range[1]], digest, label)

    expected_old_call = bytes.fromhex(
        "6A 05 6A 00 68 43 03 68 70 90 68 BE 45 68 00 10 68 A2 06 9A 66 16 70 90"
    )
    if wsc10[WSC10_LINEAGE_ALLOC_RANGE[0]:WSC10_LINEAGE_ALLOC_RANGE[1]] != expected_old_call:
        raise SystemExit("WSC 1.0 lineage allocator arguments changed")

    wsc10_refs = sorted(
        set(all_offsets(wsc10, bytes.fromhex("26 8B 3E A2 06")))
        | set(all_offsets(wsc10, bytes.fromhex("26 8B 36 A2 06")))
    )
    if wsc10_refs != [0x390796, 0x3908EE, 0x394996]:
        raise SystemExit(f"WSC 1.0 ES:06A2 consumers changed: {wsc10_refs}")

    storage_literals = all_offsets(gba, struct.pack("<I", GBA_LINEAGE_STORAGE))
    aligned_storage_literals = [offset for offset in storage_literals if offset % 4 == 0]
    if tuple(aligned_storage_literals) != GBA_LINEAGE_STORAGE_LITERALS:
        raise SystemExit(f"GBA 03004D3C literal population changed: {aligned_storage_literals}")

    lineage_calls = [
        row for row in calls
        if row["allocation_id"] == 0x343 and row["pool_selector"] == 5
    ]
    if lineage_calls != [{
        "call_offset": 0x36FE9C,
        "call_address": 0x0836FE9C,
        "destination_pointer_slot": GBA_LINEAGE_STORAGE,
        "callback": GBA_LINEAGE_CALLBACK,
        "allocation_id": 0x343,
        "arg5": 0,
        "pool_selector": 5,
    }]:
        raise SystemExit(f"commercial GBA ID 0343 lineage changed: {lineage_calls}")

    # The first callback branch proves the platform timing conversion:
    # WonderSwan 75 Hz values 225/400/420 become GBA 60 Hz 180/320/336.
    for data, offset, expected, label in (
        (wsc10, 0x394CE0, 0x00E1, "WSC 1.0 first branch timer"),
        (wsc10, 0x394CEF, 0x0190, "WSC 1.0 second branch timer"),
        (wsc10, 0x394D11, 0x01A4, "WSC 1.0 third timer"),
        (wsc15, 0x745A56, 0x00E1, "WSC 1.5 first branch timer"),
        (wsc15, 0x745A65, 0x0190, "WSC 1.5 second branch timer"),
        (wsc15, 0x745A87, 0x01A4, "WSC 1.5 third timer"),
    ):
        actual = struct.unpack_from("<H", data, offset)[0]
        if actual != expected:
            raise SystemExit(f"{label} changed: 0x{actual:04X}")
    for raw, expected, label in (
        (0x37041C, 0xE3A090B4, "GBA first branch timer 180"),
        (0x370434, 0xE3A09D05, "GBA second branch timer 320"),
        (0x370490, 0xE3A09E15, "GBA third timer 336"),
    ):
        if struct.unpack_from("<I", gba, raw)[0] != expected:
            raise SystemExit(f"{label} signature changed")

    return {
        "wsc10": {
            "storage": "ES:06A2",
            "allocator": "9070:1666",
            "callback": "9070:45BE",
            "allocation_id": 0x343,
            "pool_selector": 5,
            "initializer_range": list(WSC10_LINEAGE_INIT_RANGE),
            "initializer_sha256": WSC10_LINEAGE_INIT_SHA256,
            "direct_consumers": wsc10_refs,
        },
        "wsc15": {
            "storage": "ES:071E",
            "allocator": "4090:172A",
            "callback": "4090:5134",
            "allocation_id": 0x343,
            "pool_selector": 5,
            "initializer_range": list(WSC15_LINEAGE_INIT_RANGE),
            "initializer_sha256": WSC15_LINEAGE_INIT_SHA256,
            "direct_consumers": sorted(WSC_DIRECT_REFERENCE_BYTES),
        },
        "commercial_gba": {
            "storage": GBA_LINEAGE_STORAGE,
            "allocator": GBA_ALLOCATOR,
            "callback": GBA_LINEAGE_CALLBACK,
            "allocation_id": 0x343,
            "pool_selector": 5,
            "initializer_range": list(GBA_LINEAGE_INIT_RANGE),
            "initializer_sha256": GBA_LINEAGE_INIT_SHA256,
            "storage_literal_population": aligned_storage_literals,
            "screen_effect_consumer_instructions": [0x080C97FC, 0x080C9AF8],
        },
        "field_mapping": {
            "velocity_zero": {"wsc": [0x32, 0x34, 0x36, 0x38], "gba": [0x42, 0x44, 0x46, 0x48]},
            "bounds": {"wsc": [0x42, 0x44], "gba": [0x52, 0x54], "values": [8, 16]},
            "primary_link": {"wsc": 0x1C, "gba": 0x28},
            "secondary_link": {"wsc": 0x14, "gba": 0x18},
            "position": {"wsc": [0x26, 0x28], "gba": [0x34, 0x36]},
            "presentation_subobject": {"wsc": 0x96, "gba": 0xAC},
            "screen_effect_field": {"wsc": 0xBE, "gba": [0xE0, 0xE1]},
        },
        "timing_oracle": {
            "wsc_hz": 75,
            "gba_hz": 60,
            "pairs": [[225, 180], [400, 320], [420, 336]],
        },
        "conclusion": (
            "WSC 1.5 ES:071E is the relocated Ver. 1.0 ES:06A2 object lineage. "
            "The commercial GBA port already maps that lineage to pointer slot "
            "03004D3C, callback 083703EC, native screen-effect consumers, ID 0343, "
            "and pool 5. The Shoot initializer can reuse those native locations "
            "without inventing RAM, then replace the callback with the translated "
            "4090:88F6 state as the WSC 1.5 initializer does."
        ),
    }


def require_gba_boundary(gba: bytes) -> tuple[dict[str, object], list[dict[str, object]]]:
    start, end = GBA_ALLOCATOR_RANGE
    require_hash(gba[start:end], GBA_ALLOCATOR_SHA256, "native GBA object allocator")
    start, end = GBA_RELEASE_RANGE
    require_hash(gba[start:end], GBA_RELEASE_SHA256, "native GBA object release")
    parameter_signature = {
        0x352378: 0xE59D1014,
        0x352434: 0xE59D0024,
        0x35243C: 0xE59D001C,
        0x352440: 0xE59D2018,
        0x35248C: 0xE59D002C,
        0x352490: 0xE5805000,
    }
    for raw, expected in parameter_signature.items():
        actual = struct.unpack_from("<I", gba, raw)[0]
        if actual != expected:
            raise SystemExit(f"native allocator ABI signature changed at 0x{GBA_BASE + raw:08X}")
    if struct.unpack_from("<I", gba, 0x3524B0)[0] != 0x03004826:
        raise SystemExit("native selector-5 pool flag base changed")
    if struct.unpack_from("<I", gba, 0x3524B4)[0] != 0x03004810:
        raise SystemExit("native pool flag origin changed")
    if struct.unpack_from("<I", gba, 0x3524B8)[0] != 0x030047A8:
        raise SystemExit("native object-block pointer table changed")

    calls = commercial_allocator_calls(gba)
    pool5 = [row for row in calls if row["pool_selector"] == 5]
    return ({
        "allocator_entry": GBA_ALLOCATOR,
        "release_entry": GBA_RELEASE,
        "allocator_range": list(GBA_ALLOCATOR_RANGE),
        "allocator_sha256": sha256(gba[GBA_ALLOCATOR_RANGE[0]:GBA_ALLOCATOR_RANGE[1]]),
        "release_range": list(GBA_RELEASE_RANGE),
        "release_sha256": sha256(gba[GBA_RELEASE_RANGE[0]:GBA_RELEASE_RANGE[1]]),
        "proved_parameter_reads": {
            "destination_pointer_arg0": "sp+2C after five-register prologue",
            "callback_arg2": "sp+24 after five-register prologue",
            "allocation_id_arg4": "sp+1C after five-register prologue",
            "arg5": "sp+18 after five-register prologue",
            "pool_selector_arg6": "sp+14 after five-register prologue",
            "unused_lineage_placeholders": ["arg1", "arg3"],
        },
        "selector_5_pool": {
            "flag_range": [0x03004826, 0x03004828],
            "capacity": 2,
            "object_block_pointer_slots": [0x03004800, 0x03004804],
            "returned_object_offset_inside_block": 0x18,
        },
        "commercial_call_count": len(calls),
        "commercial_pool5_call_count": len(pool5),
    }, calls)


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

    wsc = require_wsc_boundary(wsc10, wsc15)
    gba_boundary, calls = require_gba_boundary(gba)
    lineage = require_commercial_lineage(gba, wsc10, wsc15, calls)
    pool5_calls = [row for row in calls if row["pool_selector"] == 5]
    destination_population = sorted({
        row["destination_pointer_slot"]
        for row in pool5_calls
        if isinstance(row["destination_pointer_slot"], int)
    })
    result = {
        "schema": 1,
        "kind": "digimon-shoot-auxiliary-object-lifetime-boundary",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "wsc15": wsc,
        "native_gba": gba_boundary,
        "commercial_lineage": lineage,
        "commercial_gba_allocator_calls": calls,
        "commercial_pool5_destination_population": destination_population,
        "integration_boundary": {
            "proved": [
                "native allocator and release entry points",
                "seven-argument native allocator ABI",
                "pool selector 5 capacity and backing pointer-table derivation",
                "all direct WSC ES:071E consumers",
                "no ES:071E-based external release path",
                "WSC 1.0 ES:06A2 -> GBA 03004D3C storage lineage",
                "WSC 1.5 callback 5134 -> native GBA callback 083703EC lineage",
                "native GBA screen-effect consumers for the same object slot",
            ],
            "not_yet_proved": [
                "dedicated stage-11 route that bypasses the commercial stage initializer",
                "final auxiliary-object implementation",
            ],
            "runtime_or_save_used": False,
        },
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
