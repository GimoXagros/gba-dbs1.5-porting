#!/usr/bin/env python3
"""Build a reversible, deliberately unsafe animation-asset wiring probe.

The selected WSC-only runtime-ID-11 evolution asset is converted into a native
GBA asset object in an unproven FF-filled range. The retail GBA runtime-ID-1
(Terriermon) evolution-header pointer is redirected to it. Placement safety,
palette integration, visual identity, and gameplay semantics are all outside
this deliberately mismatched probe's claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996de33330ac729d10d761d1901e7a335191c9503b0470569e8f294acf6618ed"
WSC_SHA256 = "c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7"
GBA_BASE = 0x08000000

WSC_HEADER = 0x35A860
EXPECTED_LAYOUT_ENTRIES = 79
EXPECTED_LAYOUT_RECORD_BYTES = 10180
EXPECTED_DESCRIPTOR_ENTRIES = 109
EXPECTED_TILE_BYTES = 113952

TARGET_HEADER = 0x388000
POINTER_WRITE_OFFSET = 0x0D42D8
EXPECTED_OLD_POINTER = 0x0828AE34


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & -boundary


def convert_tile(tile: bytes) -> bytes:
    if len(tile) != 32:
        raise ValueError("tile must be 32 bytes")
    pixels: list[int] = []
    for row in range(8):
        planes = tile[row * 4:row * 4 + 4]
        for column in range(8):
            mask = 0x80 >> column
            pixels.append(sum(((planes[plane] & mask) != 0) << plane for plane in range(4)))
    return bytes(pixels[index] | (pixels[index + 1] << 4)
                 for index in range(0, 64, 2))


def parse_wsc_descriptor(rom: bytes, offset: int) -> tuple[int, int] | None:
    """Legacy 0x2000-segment probe recognizer, not a general P0 validator.

    Historical layers depend on this restricted result. In particular, None
    does NOT prove that an asset has no tiles. The source loaders read the
    third word into DS, not a destination register. New source-bound repairs
    use parse_wsc_far_descriptor with an explicit descriptor population.
    """
    if offset < 0 or offset + 8 > len(rom):
        return None
    length, bank_offset, destination, bank = struct.unpack_from("<4H", rom, offset)
    if (length < 0x20 or length % 0x20 or destination != 0x2000
            or not 0x80 <= bank <= 0xFF or bank_offset + length > 0x10000):
        return None
    bank_count = len(rom) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        return None
    physical = ((bank & (bank_count - 1)) << 16) | bank_offset
    if physical + length > len(rom):
        return None
    return length, physical


def parse_wsc_far_descriptor(rom: bytes, offset: int) -> tuple[int, int]:
    """Resolve the length + offset/segment/C2-bank source used by 4FFF:2E6E.

    This supported profile requires the whole copy to stay in the C2-mapped
    0x20000..0x2FFFF window. Reject crossing/unknown mappings instead of masking
    them into a plausible ROM address. A terminal FF record is not a payload.
    """
    if offset < 0 or offset + 8 > len(rom):
        raise ValueError("truncated WSC far tile descriptor")
    length, source_offset, source_segment, bank = struct.unpack_from("<4H", rom, offset)
    banks = len(rom) >> 16
    if len(rom) % 0x10000 or not banks or banks & (banks - 1):
        raise ValueError("WSC image does not have a power-of-two bank population")
    linear = (source_segment << 4) + source_offset
    if (length < 32 or length % 32 or not 0x80 <= bank <= 0xFF
            or not 0x20000 <= linear < linear + length <= 0x30000):
        raise ValueError("unsupported WSC far tile source or copy extent")
    return length, (bank & (banks - 1)) * 0x10000 + linear - 0x20000


def build_far_descriptor_payload(
    rom: bytes, *, wsc_header: int, target: int, count: int
) -> tuple[bytes, dict[str, object]]:
    """Convert an explicitly bounded far-descriptor table without moving P0.

    Layouts, animation metadata and their existing consumers remain in place;
    the integrating layer redirects only P0+4 to this table. Count must come
    from the actual P1/loader population, with the source FF terminator checked.
    """
    if count <= 0 or wsc_header < 0 or wsc_header + 16 > len(rom) or target % 4:
        raise ValueError("invalid bounded descriptor conversion inputs")
    if struct.unpack_from("<I", rom, wsc_header)[0] != 0x10:
        raise ValueError("unsupported P0 layout/descriptor header")
    segment, bank = struct.unpack_from("<2H", rom, wsc_header + 4)
    linear = segment << 4
    banks = len(rom) >> 16
    if (not banks or banks & (banks - 1) or not 0x80 <= bank <= 0xFF
            or not 0x20000 <= linear < linear + (count + 1) * 8 <= 0x30000):
        raise ValueError("unsupported P0 descriptor-table mapping")
    table = (bank & (banks - 1)) * 0x10000 + linear - 0x20000
    if rom[table + count * 8:table + (count + 1) * 8] != b"\xff" * 8:
        raise ValueError("bounded P0 descriptor population has no expected terminator")
    payload_start = align(target + count * 8, 32)
    output = bytearray(payload_start - target)
    entries = []
    for index in range(count):
        length, physical = parse_wsc_far_descriptor(rom, table + index * 8)
        converted = b"".join(convert_tile(rom[pos:pos + 32])
                             for pos in range(physical, physical + length, 32))
        tile_target = target + len(output)
        struct.pack_into("<2I", output, index * 8, length, GBA_BASE + tile_target)
        output.extend(converted)
        entries.append({"index": index, "source": physical, "bytes": length,
                        "target": tile_target, "source_sha256": sha256(rom[physical:physical + length]),
                        "converted_sha256": sha256(converted)})
    return bytes(output), {"source_header": wsc_header, "source_table": table,
                           "target": target, "descriptors": count,
                           "tile_bytes": sum(row["bytes"] for row in entries),
                           "bytes": len(output), "entries": entries}


def build_asset(
    wsc: bytes,
    *,
    wsc_header: int = WSC_HEADER,
    target_header: int = TARGET_HEADER,
    expected_layout_entries: int | None = EXPECTED_LAYOUT_ENTRIES,
    expected_layout_record_bytes: int | None = EXPECTED_LAYOUT_RECORD_BYTES,
    expected_descriptor_entries: int | None = EXPECTED_DESCRIPTOR_ENTRIES,
    expected_tile_bytes: int | None = EXPECTED_TILE_BYTES,
) -> tuple[bytes, dict[str, object]]:
    table_relative, secondary, constants_a, constants_b = struct.unpack_from("<4I", wsc, wsc_header)
    if table_relative != 0x10:
        raise SystemExit("unexpected WSC asset header")

    layout_table = wsc_header + table_relative
    first_count, first_record_relative = struct.unpack_from("<HH", wsc, layout_table)
    if (first_record_relative - table_relative) % 4:
        raise SystemExit("WSC layout table is not integral")
    layout_entries = (first_record_relative - table_relative) // 4
    if expected_layout_entries is not None and layout_entries != expected_layout_entries:
        raise SystemExit("unexpected WSC layout entry count")

    counts: list[int] = []
    relatives: list[int] = []
    expected_relative = first_record_relative
    for index in range(layout_entries):
        count, relative = struct.unpack_from("<HH", wsc, layout_table + index * 4)
        if count == 0 or relative != expected_relative:
            raise SystemExit("WSC layout record offsets are not contiguous")
        counts.append(count)
        relatives.append(relative)
        expected_relative += count * 4
    layout_records = wsc[wsc_header + first_record_relative:wsc_header + expected_relative]
    if expected_layout_record_bytes is not None and len(layout_records) != expected_layout_record_bytes:
        raise SystemExit("unexpected WSC layout record size")

    bank = (secondary >> 16) & 0xFF
    segment = secondary & 0xFFFF
    bank_count = len(wsc) >> 16
    if not bank_count or bank_count & (bank_count - 1):
        raise SystemExit("WSC ROM must contain a power-of-two number of banks")
    descriptor_start = (
        ((bank & (bank_count - 1)) << 16) | ((segment << 4) & 0xFFFF)
    )
    descriptors: list[tuple[int, int]] = []
    cursor = descriptor_start
    while True:
        descriptor = parse_wsc_descriptor(wsc, cursor)
        if descriptor is None:
            break
        if descriptors:
            previous_length, previous_physical = descriptors[-1]
            length, physical = descriptor
            contiguous = physical == previous_physical + previous_length
            new_block = (physical & 0xFFFF) == 0 and (physical >> 16) != (previous_physical >> 16)
            if not (contiguous or new_block):
                break
        descriptors.append(descriptor)
        cursor += 8
    if expected_descriptor_entries is not None and len(descriptors) != expected_descriptor_entries:
        raise SystemExit("unexpected WSC tile descriptor count")
    if expected_tile_bytes is not None and sum(length for length, _ in descriptors) != expected_tile_bytes:
        raise SystemExit("unexpected WSC tile payload size")

    target_layout_table = target_header + 0x10
    target_layout_records = target_layout_table + layout_entries * 8
    target_descriptor_table = align(target_layout_records + len(layout_records), 4)
    target_tile_data = align(target_descriptor_table + len(descriptors) * 8, 32)

    output = bytearray(target_tile_data - target_header)
    struct.pack_into(
        "<4I",
        output,
        0,
        GBA_BASE + target_layout_table,
        GBA_BASE + target_descriptor_table,
        constants_a,
        constants_b,
    )

    record_cursor = target_layout_records
    for index, count in enumerate(counts):
        struct.pack_into(
            "<II",
            output,
            target_layout_table - target_header + index * 8,
            count,
            GBA_BASE + record_cursor,
        )
        record_cursor += count * 4
    output[target_layout_records - target_header:target_layout_records - target_header + len(layout_records)] = layout_records

    converted_tiles = bytearray()
    tile_cursor = target_tile_data
    for index, (length, physical) in enumerate(descriptors):
        source = wsc[physical:physical + length]
        converted = b"".join(convert_tile(source[pos:pos + 32])
                             for pos in range(0, len(source), 32))
        if len(converted) != length:
            raise SystemExit("tile conversion changed a descriptor length")
        struct.pack_into(
            "<II",
            output,
            target_descriptor_table - target_header + index * 8,
            length,
            GBA_BASE + tile_cursor,
        )
        converted_tiles.extend(converted)
        tile_cursor += length
    output.extend(converted_tiles)

    if len(output) != tile_cursor - target_header:
        raise SystemExit("asset placement size mismatch")
    manifest = {
        "wsc_header_offset": wsc_header,
        "target_header_offset": target_header,
        "layout_entries": layout_entries,
        "layout_record_bytes": len(layout_records),
        "descriptor_entries": len(descriptors),
        "tile_payload_bytes": len(converted_tiles),
        "layout_table_offset": target_layout_table,
        "layout_records_offset": target_layout_records,
        "descriptor_table_offset": target_descriptor_table,
        "tile_data_offset": target_tile_data,
        "asset_end_offset": tile_cursor,
        "asset_bytes": len(output),
        "asset_sha256": sha256(output),
    }
    return bytes(output), manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    parser.add_argument(
        "--allow-unproven-ff-space",
        action="store_true",
        help="acknowledge that FF bytes do not prove the target range is free",
    )
    args = parser.parse_args()

    if not args.allow_unproven_ff_space:
        raise SystemExit(
            "refusing unsafe PoC build: pass --allow-unproven-ff-space only for analysis"
        )

    gba = args.gba.read_bytes()
    wsc = args.wsc.read_bytes()
    if sha256(gba) != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if sha256(wsc) != WSC_SHA256:
        raise SystemExit("refusing unknown WSC input")

    asset, asset_manifest = build_asset(wsc)
    target_end = TARGET_HEADER + len(asset)
    old_target = gba[TARGET_HEADER:target_end]
    if old_target != b"\xFF" * len(asset):
        raise SystemExit("target asset range is not the expected FF padding")
    old_pointer = struct.unpack_from("<I", gba, POINTER_WRITE_OFFSET)[0]
    if old_pointer != EXPECTED_OLD_POINTER:
        raise SystemExit("indexed asset-record pointer expected-write check failed")

    patched = bytearray(gba)
    patched[TARGET_HEADER:target_end] = asset
    struct.pack_into("<I", patched, POINTER_WRITE_OFFSET, GBA_BASE + TARGET_HEADER)

    allowed = set(range(TARGET_HEADER, target_end)) | set(range(POINTER_WRITE_OFFSET, POINTER_WRITE_OFFSET + 4))
    differing = {index for index, (before, after) in enumerate(zip(gba, patched)) if before != after}
    if not differing or not differing <= allowed:
        raise SystemExit("final diff contains an unexplained byte")
    if len(patched) != len(gba):
        raise SystemExit("ROM size changed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    manifest = {
        "kind": "full-animation-asset-poc",
        "claim_scope": "format conversion and one deliberately mismatched runtime-ID-1 evolution-header pointer only",
        "warnings": [
            "FF-filled placement range is not proven free space",
            "palette, visual identity, and gameplay behavior are not integrated",
            "this artifact is not a playable port or release candidate",
        ],
        "base_sha256": GBA_SHA256,
        "reference_sha256": WSC_SHA256,
        "output_sha256": sha256(patched),
        "asset": asset_manifest,
        "writes": [
            {
                "meaning": "new native GBA animation asset",
                "offset": TARGET_HEADER,
                "length": len(asset),
                "expected_original": "all FF (not evidence of free space)",
                "new_sha256": sha256(asset),
            },
            {
                "meaning": "runtime ID 1 (Terriermon) evolution-header pointer redirect to the WSC runtime-ID-11 asset",
                "offset": POINTER_WRITE_OFFSET,
                "length": 4,
                "expected_original_u32": EXPECTED_OLD_POINTER,
                "new_u32": GBA_BASE + TARGET_HEADER,
            },
        ],
        "actual_changed_bytes": len(differing),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
