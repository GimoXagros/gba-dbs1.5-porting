#!/usr/bin/env python3
"""Build a relocatable GBA ZeedMillenniummon sprite bundle.

The retail GBA Millenniummon header and the Ver. 1.5 ZeedMillenniummon
header have the same 17-layout/eight-payload ABI.  Keep the GBA-native layout
records and replace only their eight planar source payloads with losslessly
converted Ver. 1.5 graphics.  Runtime routing is deliberately handled by the
separate boss-integration builder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

GBA_HEADER = 0x34E27C
GBA_DESCRIPTOR = 0x34E770
GBA_FIRST_PAYLOAD = 0x34E7B0
GBA_DESCRIPTOR_COUNT = 8
GBA_FIRST_LAYOUT_RECORD = 0x34E314

WSC_HEADER = 0x3BE710
WSC_DESCRIPTOR = 0x3D6ED0
WSC_TILE_START = 0x390000
WSC_PALETTE = 0x7459B3
WSC_FIRST_LAYOUT_RECORD = WSC_HEADER + 0x54
WSC_LAYOUT_END = WSC_HEADER + 0x4B0

DEFAULT_TARGET = 0x5B2000


def parse_int(value: str) -> int:
    return int(value, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def convert_tile(tile: bytes) -> bytes:
    if len(tile) != 32:
        raise ValueError("WSC tile must be 32 bytes")
    result = bytearray()
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        pixels = []
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
        result.extend(pixels[index] | (pixels[index + 1] << 4) for index in range(0, 8, 2))
    return bytes(result)


def convert_payload(payload: bytes) -> bytes:
    if len(payload) % 32:
        raise ValueError("WSC payload is not tile aligned")
    return b"".join(convert_tile(payload[offset:offset + 32])
                    for offset in range(0, len(payload), 32))


def expand_channel(value: int) -> int:
    return (value << 1) | int(value != 0)


def convert_color(value: int) -> int:
    if value & 0xF000:
        raise ValueError("WSC color is outside RGB444")
    blue = expand_channel(value & 0xF)
    green = expand_channel((value >> 4) & 0xF)
    red = expand_channel((value >> 8) & 0xF)
    return red | (green << 5) | (blue << 10)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--target", type=parse_int, default=DEFAULT_TARGET)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc = args.wsc15.read_bytes()
    if sha256(gba) != GBA_SHA256:
        raise SystemExit("refusing unknown USA GBA input")
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 input")

    layout_pointer, descriptor_pointer = struct.unpack_from("<II", gba, GBA_HEADER)
    if layout_pointer != GBA_BASE + GBA_HEADER + 0x10:
        raise SystemExit("unexpected retail boss layout pointer")
    if descriptor_pointer != GBA_BASE + GBA_DESCRIPTOR:
        raise SystemExit("unexpected retail boss descriptor pointer")
    first_length, first_pointer = struct.unpack_from("<II", gba, GBA_DESCRIPTOR)
    if first_pointer != GBA_BASE + GBA_FIRST_PAYLOAD:
        raise SystemExit("unexpected retail boss payload boundary")
    if (GBA_FIRST_PAYLOAD - GBA_DESCRIPTOR) // 8 != GBA_DESCRIPTOR_COUNT:
        raise SystemExit("unexpected retail boss descriptor population")

    wsc_layout_relative, wsc_secondary = struct.unpack_from("<II", wsc, WSC_HEADER)
    if wsc_layout_relative != 0x10 or wsc_secondary != 0x00BD26ED:
        raise SystemExit("unexpected Ver. 1.5 Zeed header")
    # The 17 Zeed layout records are byte-identical to the native GBA boss
    # records.  This is stronger than matching only the table population: it
    # proves that the existing GBA record ABI places every converted tile in
    # the same frame coordinates as the Ver. 1.5 source.
    wsc_layout_records = wsc[WSC_FIRST_LAYOUT_RECORD:WSC_LAYOUT_END]
    gba_layout_records = gba[GBA_FIRST_LAYOUT_RECORD:GBA_DESCRIPTOR]
    if wsc_layout_records != gba_layout_records:
        raise SystemExit("Ver. 1.5 Zeed layout records differ from the GBA boss ABI")

    prefix = bytearray(gba[GBA_HEADER:GBA_FIRST_PAYLOAD])
    delta = args.target - GBA_HEADER
    # Relocate all GBA-native absolute pointers inside the cloned header,
    # layout table, layout records, and descriptor table.
    for offset in range(0, len(prefix) - 3, 4):
        value = struct.unpack_from("<I", prefix, offset)[0]
        if GBA_BASE + GBA_HEADER <= value < GBA_BASE + GBA_FIRST_PAYLOAD:
            struct.pack_into("<I", prefix, offset, value + delta)

    payloads: list[bytes] = []
    entries: list[dict[str, object]] = []
    cursor = args.target + len(prefix)
    for index in range(GBA_DESCRIPTOR_COUNT):
        gba_length, _ = struct.unpack_from("<II", gba, GBA_DESCRIPTOR + index * 8)
        length, bank_offset, destination, bank = struct.unpack_from(
            "<4H", wsc, WSC_DESCRIPTOR + index * 8
        )
        physical = ((bank & 0x7F) << 16) | bank_offset
        if length != gba_length:
            raise SystemExit(f"descriptor {index} length differs between GBA and Ver. 1.5")
        if physical != WSC_TILE_START + sum(len(item) for item in payloads):
            raise SystemExit(f"descriptor {index} is not contiguous in the Zeed tile bank")
        converted = convert_payload(wsc[physical:physical + length])
        payloads.append(converted)
        struct.pack_into(
            "<II", prefix, GBA_DESCRIPTOR - GBA_HEADER + index * 8,
            length, GBA_BASE + cursor,
        )
        entries.append({
            "index": index,
            "bytes": length,
            "wsc_source": physical,
            "wsc_destination": destination,
            "target": cursor,
            "sha256": sha256(converted),
        })
        cursor += length

    blob = bytes(prefix) + b"".join(payloads)
    palette = b"".join(
        struct.pack("<H", convert_color(value))
        for value in struct.unpack_from("<16H", wsc, WSC_PALETTE)
    )
    retail_palette = gba[0x37036C:0x37038C]
    if palette != retail_palette:
        raise SystemExit("Zeed palette no longer matches the GBA boss palette ABI")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(blob)
    result = {
        "schema": 1,
        "kind": "relocatable-gba-zeedmillenniummon-sprite-bundle",
        "source_gba_sha256": GBA_SHA256,
        "source_wsc15_sha256": WSC15_SHA256,
        "source_gba_header": GBA_HEADER,
        "source_wsc_header": WSC_HEADER,
        "target_header": args.target,
        "layout_count": 17,
        "layout_record_bytes": len(wsc_layout_records),
        "layout_record_sha256": sha256(wsc_layout_records),
        "layout_records_match_retail_gba": True,
        "descriptor_count": GBA_DESCRIPTOR_COUNT,
        "entries": entries,
        "palette_source": WSC_PALETTE,
        "palette_matches_retail_gba": True,
        "blob_bytes": len(blob),
        "blob_sha256": sha256(blob),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
