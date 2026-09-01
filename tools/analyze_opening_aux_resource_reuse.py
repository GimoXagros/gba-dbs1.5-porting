#!/usr/bin/env python3
"""Prove native GBA reuse for the two added opening auxiliary resources.

WSC 1.5 callbacks 7 and 10 directly consume fields 0 and 2 of replacement
resource records 50 and 49.  This static checker converts those exact WSC
animation/tile and palette containers with rules independently established
against the commercial port, then requires byte-identical containers already
present in the unmodified USA GBA ROM.  It also proves the complete native GBA
record views and the exact commercial object-consumer ABI that can materialize
those records without translating the WSC low-level loaders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_poc import convert_planar_tile
from convert_wsc_palette_block import WSC_BYTES as WSC_PALETTE_BYTES, convert_block


GBA_BASE = 0x08000000
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"

WSC10_RESOURCE_TABLE = 0x390000
WSC15_RESOURCE_TABLE = 0x740000
RESOURCE_RECORD_BYTES = 0x20
GBA_OBJECT_CONSUMER = (0x088250, 0x088310)
GBA_OBJECT_CONSUMER_SHA256 = (
    "AAF329B99CD8BABB7A4CC6AE663C59C09C2E05B05C8288ED484FD694870EA27E"
)
GBA_OBJECT_BASE = 0x03002908
GBA_OBJECT_STRIDE = 0x50

CASES = {
    49: {
        "wsc10_record": 39,
        "wsc10_p1": 0x2B4870,
        "wsc15_p1": 0x3D5590,
        "p1_identity_bytes": 0x90,
        "p1_identity_sha256": "F495D16DE671B5389A2C8E6DDBDF48EC7CB255EDD47AB2505121E690386EE18F",
        "wsc_p0": 0x3D3E20,
        "wsc_p2": 0x3D7880,
        "wsc_descriptor": 0x33FFE0,
        "wsc_tiles": 0x3C27E0,
        "tile_bytes": 0x420,
        "gba_p0": 0x2D94D8,
        "gba_descriptor": 0x2D95CC,
        "gba_tiles": 0x2D95D4,
        "gba_palette": 0x2D99F4,
        "gba_record_view": 0x0D4498,
        "gba_record_sha256": "19A8182901524E6F36B5EB4BE2B4BD2D32A9BF335576D274EFE5F01BAE4DFAD7",
        "gba_record_fields": (0x2D94D8, 0x2D9428, 0x2D99F4),
        "gba_record_words": (
            0x082D94D8, 0x082D9428, 0x082D99F4, 0x082D99F4,
            0x082D9A1C, 0, 0, 0,
        ),
        "wsc_tiles_sha256": "B2797A45A7FB25A5FDA3D9E6FD7A41366DC7F614F5E9B1354C808CD2FA6BAB5D",
        "gba_asset_sha256": "1765A5FB704FB10A8641A11C61DC9BD8AB5A1CAC6AC2E9D1443942E374E66600",
        "gba_palette_sha256": "5803ECCE4279EF1A7AB011A19EF9EB80F313287DE78B02768BF0867E2D9C5946",
    },
    50: {
        "wsc10_record": 41,
        "wsc10_p1": 0x2B33C0,
        "wsc15_p1": 0x3D3F00,
        "p1_identity_bytes": 0xB4,
        "p1_identity_sha256": "1B6BE10B1532172077510271FD9C5C50A79245C0FEAD02565CB8C57568782AC9",
        "wsc_p0": 0x3D5620,
        "wsc_p2": 0x3D6960,
        "wsc_descriptor": 0x34FFE0,
        "wsc_tiles": 0x3D09A0,
        "tile_bytes": 0x180,
        "gba_p0": 0x2F91CC,
        "gba_descriptor": 0x2F9260,
        "gba_tiles": 0x2F9268,
        "gba_palette": 0x2F93E8,
        "gba_record_view": 0x0D44D8,
        "gba_record_sha256": "1D0712DC206028852BCDEA2477498FFA960EA7992579EBC534A9C7C63B8B8DEA",
        "gba_record_fields": (0x2F91CC, 0x2F90A0, 0x2F93E8),
        "gba_record_words": (
            0x082F91CC, 0x082F90A0, 0x082F93E8, 0x082F93E8,
            0x082F9438, 0, 0, 0,
        ),
        "wsc_tiles_sha256": "EFE7456C860E316C078E6B6E88A7A000898587C78F8A06A490BCA236DF98A658",
        "gba_asset_sha256": "47624C70D8A194F98310C84B5103D158DE5164A041CC3877EC0FAFA9DE55B610",
        "gba_palette_sha256": "4294DEEFE2AD576FD75AAFE01DD660D1413F946211A138588854C569D76AA027",
    },
}

EXPECTED_GBA_POINTER_REFS = {
    0x2D95CC: [0x2D94DC],
    0x2F9260: [0x2F91D0],
    0x2D99F4: [0x0D44A0, 0x0D44A4, 0x0D44C0, 0x0D44C4],
    0x2F93E8: [0x0D44E0, 0x0D44E4],
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 changed: {actual}")


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def wsc_pointer(data: bytes, offset: int) -> int:
    pointer_offset, segment, bank = struct.unpack_from("<3H", data, offset)
    bank_count = len(data) >> 16
    bank_offset = (((segment - 0x2000) << 4) + pointer_offset) & 0xFFFF
    return ((bank & (bank_count - 1)) << 16) | bank_offset


def all_offsets(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        found = data.find(needle, cursor)
        if found < 0:
            return offsets
        offsets.append(found)
        cursor = found + 1


def convert_special_p0(
    wsc: bytes, wsc_header: int, gba_header: int
) -> tuple[bytes, dict[str, int]]:
    """Convert the one-descriptor P0 variant used by records 49/50."""
    table_relative, secondary, constants_a, constants_b = struct.unpack_from(
        "<4I", wsc, wsc_header
    )
    if table_relative != 0x10:
        raise ValueError(f"unexpected WSC P0 header at 0x{wsc_header:X}")

    layout_table = wsc_header + table_relative
    first_count, first_record_relative = struct.unpack_from("<2H", wsc, layout_table)
    if (first_record_relative - table_relative) % 4:
        raise ValueError("WSC P0 layout table is not integral")
    layout_entries = (first_record_relative - table_relative) // 4
    expected_relative = first_record_relative
    layout: list[tuple[int, int]] = []
    for index in range(layout_entries):
        count, relative = struct.unpack_from("<2H", wsc, layout_table + index * 4)
        if not count or relative != expected_relative:
            raise ValueError("WSC P0 layout records are not contiguous")
        layout.append((count, relative))
        expected_relative += count * 4
    layout_records = wsc[
        wsc_header + first_record_relative:wsc_header + expected_relative
    ]

    source_bank = (secondary >> 16) & 0xFF
    descriptor_segment = secondary & 0xFFFF
    descriptor = ((source_bank & 0x7F) << 16) | ((descriptor_segment << 4) & 0xFFFF)
    length, destination, tile_segment, tile_bank = struct.unpack_from(
        "<4H", wsc, descriptor
    )
    tile_source = ((tile_bank & 0x7F) << 16) | ((tile_segment << 4) & 0xFFFF)
    if length < 0x20 or length % 0x20 or tile_source + length > len(wsc):
        raise ValueError("invalid WSC P0 tile descriptor")
    if wsc[descriptor + 8:descriptor + 16] != bytes.fromhex("FF FF FF FF FF FF FF FF"):
        raise ValueError("WSC P0 is no longer the expected one-descriptor variant")

    target_layout_table = gba_header + 0x10
    target_layout_records = target_layout_table + layout_entries * 8
    target_descriptor = align(target_layout_records + len(layout_records), 4)
    target_tiles = target_descriptor + 8
    output = bytearray(target_tiles - gba_header)
    struct.pack_into(
        "<4I",
        output,
        0,
        GBA_BASE + target_layout_table,
        GBA_BASE + target_descriptor,
        constants_a,
        constants_b,
    )
    record_cursor = target_layout_records
    for index, (count, _) in enumerate(layout):
        struct.pack_into(
            "<2I",
            output,
            target_layout_table - gba_header + index * 8,
            count,
            GBA_BASE + record_cursor,
        )
        record_cursor += count * 4
    output[
        target_layout_records - gba_header:
        target_layout_records - gba_header + len(layout_records)
    ] = layout_records
    converted_tiles = b"".join(
        convert_planar_tile(wsc[offset:offset + 32])
        for offset in range(tile_source, tile_source + length, 32)
    )
    struct.pack_into(
        "<2I",
        output,
        target_descriptor - gba_header,
        length,
        GBA_BASE + target_tiles,
    )
    output.extend(converted_tiles)
    return bytes(output), {
        "layout_entries": layout_entries,
        "layout_record_bytes": len(layout_records),
        "wsc_descriptor": descriptor,
        "wsc_tile_destination": destination,
        "wsc_tiles": tile_source,
        "tile_bytes": length,
        "gba_descriptor": target_descriptor,
        "gba_tiles": target_tiles,
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
    wsc = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc, WSC15_SHA256, "WSC 1.5 source")
    require_hash(
        gba[GBA_OBJECT_CONSUMER[0]:GBA_OBJECT_CONSUMER[1]],
        GBA_OBJECT_CONSUMER_SHA256,
        "GBA opening object consumer",
    )
    if struct.unpack_from("<I", gba, 0x08825C)[0] != 0xE0855280:
        raise ValueError("GBA selector*0x20 record addressing changed")
    if struct.unpack_from("<I", gba, 0x088264)[0] != 0xE3A00050:
        raise ValueError("GBA object stride constant changed")
    if struct.unpack_from("<I", gba, 0x088310)[0] != GBA_OBJECT_BASE:
        raise ValueError("GBA object base literal changed")

    cases = []
    for record_id, expected in CASES.items():
        record = WSC15_RESOURCE_TABLE + record_id * RESOURCE_RECORD_BYTES
        wsc_p0 = wsc_pointer(wsc, record)
        wsc_p2 = wsc_pointer(wsc, record + 12)
        if wsc_p0 != expected["wsc_p0"] or wsc_p2 != expected["wsc_p2"]:
            raise ValueError(f"WSC record {record_id} field target changed")

        old_record = (
            WSC10_RESOURCE_TABLE
            + expected["wsc10_record"] * RESOURCE_RECORD_BYTES
        )
        old_p1 = wsc_pointer(wsc10, old_record + 6)
        new_p1 = wsc_pointer(wsc, record + 6)
        if old_p1 != expected["wsc10_p1"] or new_p1 != expected["wsc15_p1"]:
            raise ValueError(f"WSC record {record_id} P1 lineage changed")
        p1_bytes = expected["p1_identity_bytes"]
        old_p1_data = wsc10[old_p1:old_p1 + p1_bytes]
        new_p1_data = wsc[new_p1:new_p1 + p1_bytes]
        require_hash(
            old_p1_data,
            expected["p1_identity_sha256"],
            f"WSC 1.0 auxiliary record {record_id} P1",
        )
        if old_p1_data != new_p1_data:
            raise ValueError(f"WSC record {record_id} P1 identity changed")

        asset, details = convert_special_p0(wsc, wsc_p0, expected["gba_p0"])
        for key in ("wsc_descriptor", "wsc_tiles", "tile_bytes", "gba_descriptor", "gba_tiles"):
            if details[key] != expected[key]:
                raise ValueError(f"record {record_id} {key} changed: {details[key]:X}")
        require_hash(
            wsc[expected["wsc_tiles"]:expected["wsc_tiles"] + expected["tile_bytes"]],
            expected["wsc_tiles_sha256"],
            f"WSC record {record_id} tile payload",
        )
        require_hash(asset, expected["gba_asset_sha256"], f"converted record {record_id} P0")
        resident_asset = gba[expected["gba_p0"]:expected["gba_p0"] + len(asset)]
        if asset != resident_asset:
            raise ValueError(f"converted record {record_id} P0 is not resident in GBA")

        palette = convert_block(wsc[wsc_p2:wsc_p2 + WSC_PALETTE_BYTES])
        require_hash(
            palette,
            expected["gba_palette_sha256"],
            f"converted record {record_id} palette",
        )
        resident_palette = gba[
            expected["gba_palette"]:expected["gba_palette"] + len(palette)
        ]
        if palette != resident_palette:
            raise ValueError(f"converted record {record_id} palette is not resident in GBA")

        gba_record = gba[
            expected["gba_record_view"]:
            expected["gba_record_view"] + RESOURCE_RECORD_BYTES
        ]
        require_hash(
            gba_record,
            expected["gba_record_sha256"],
            f"GBA auxiliary record {record_id}",
        )
        gba_fields = tuple(
            value - GBA_BASE
            for value in struct.unpack_from("<3I", gba_record)
        )
        if gba_fields != expected["gba_record_fields"]:
            raise ValueError(f"GBA auxiliary record {record_id} fields changed")
        if struct.unpack_from("<8I", gba_record) != expected["gba_record_words"]:
            raise ValueError(f"GBA auxiliary record {record_id} words changed")

        cases.append({
            "record_id": record_id,
            "directly_consumed_fields": [0, 2],
            "wsc10_source_record": expected["wsc10_record"],
            "wsc_p1": new_p1,
            "wsc_p1_identity_bytes": p1_bytes,
            "wsc_p1_identity_sha256": expected["p1_identity_sha256"],
            "wsc_p0": wsc_p0,
            "wsc_p2": wsc_p2,
            "gba_record_view": expected["gba_record_view"],
            "gba_record_fields": list(gba_fields),
            "gba_record_sha256": expected["gba_record_sha256"],
            "gba_p0": expected["gba_p0"],
            "gba_palette": expected["gba_palette"],
            "p0_bytes": len(asset),
            "p0_sha256": sha256(asset),
            "palette_bytes": len(palette),
            "palette_sha256": sha256(palette),
            "conversion": details,
            "byte_identical_gba_reuse": True,
        })

    pointer_references = {}
    for target, expected_offsets in EXPECTED_GBA_POINTER_REFS.items():
        offsets = all_offsets(gba, struct.pack("<I", GBA_BASE + target))
        if offsets != expected_offsets:
            raise ValueError(
                f"GBA pointer references to 0x{target:X} changed: {offsets}"
            )
        pointer_references[f"0x{target:06X}"] = offsets

    result = {
        "schema": 1,
        "kind": "opening-auxiliary-resource-reuse-proof",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "cases": cases,
        "gba_pointer_references": pointer_references,
        "native_object_consumer": {
            "range": list(GBA_OBJECT_CONSUMER),
            "sha256": GBA_OBJECT_CONSUMER_SHA256,
            "resource_record_bytes": RESOURCE_RECORD_BYTES,
            "object_base": GBA_OBJECT_BASE,
            "object_stride": GBA_OBJECT_STRIDE,
            "supported_opening_slots": [0, 1],
            "bounded_use": (
                "pass an auxiliary record view with selector 0 and the chosen "
                "opening-object slot; slot activation and cleanup remain part "
                "of the untranslated callback state machine"
            ),
        },
        "conclusion": (
            "Both WSC 1.5 auxiliary resources map to complete native GBA "
            "record views whose P0/P1/P2 inputs are already resident. The "
            "commercial selector*0x20, base+slot*0x50 object consumer can "
            "materialize either record without inserting duplicate assets or "
            "translating the WSC low-level loaders."
        ),
        "claim_scope": (
            "Static asset identity, complete native-record provenance, and "
            "commercial object-consumer ABI only. Slot lifetime, callback "
            "state translation, and runtime behavior remain unverified."
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
