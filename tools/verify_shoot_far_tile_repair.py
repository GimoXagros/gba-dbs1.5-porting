#!/usr/bin/env python3
"""Check the Shoot far-tile repair against source consumers and every pixel.

No converter or integration builder is imported. This checks actual installed
P0 pointers, source far addresses, all descriptor lengths, inverse pixel data,
all P1/layout/descriptor pairs, preservation, and semantic negative controls.
It does not execute the game or use a save, and does not prove reachability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

BASE = 0x08000000
BEFORE_SHA256 = "ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0"
AFTER_SHA256 = "11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E"
SOURCES = (
    "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
)
# name, source P0, native P0, count, source P1, native P1, exact table placement
CASES = (
    ("child", 0x22FF80, 0x5B9200, 15, 0x3D1E30, 0x5B9000, 0x5F2120),
    ("active", 0x3D5F80, 0x5D1000, 28, 0x3CF410, 0x5D0000, 0x5F3B20),
    ("extra-6d", 0x3D44E0, 0x5DB300, 1, None, None, 0x5F4A00),
    ("extra-137", 0x3D0CA0, 0x5DB400, 1, None, None, 0x5F4D20),
    ("extra-91", 0x3D7D30, 0x5DB600, 1, None, None, 0x5F5360),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def u16(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos:pos + 2], "little")


def u32(data: bytes, pos: int) -> int:
    return int.from_bytes(data[pos:pos + 4], "little")


def far_source(data: bytes, pos: int, length: int) -> int:
    # Source instructions explicitly load SI, DS, and C2 from these fields.
    offset, segment, bank = struct.unpack_from("<3H", data, pos)
    linear = segment * 16 + offset
    if not 0x20000 <= linear < linear + length <= 0x30000 or not 0x80 <= bank <= 0xFF:
        raise ValueError("source far copy escapes the verified C2 memory window")
    return (bank % (len(data) // 65536)) * 65536 + linear - 0x20000


def inverse_pixels(packed: bytes) -> bytes:
    """Recover WSC bitplanes from GBA nibbles; independent of the converter."""
    if len(packed) % 32:
        raise ValueError("partial native tile")
    result = bytearray(len(packed))
    for tile in range(0, len(packed), 32):
        for row in range(8):
            for column in range(8):
                value = packed[tile + row * 4 + column // 2]
                value = (value >> (4 * (column % 2))) & 15
                for plane in range(4):
                    result[tile + row * 4 + plane] |= ((value >> plane) & 1) << (7 - column)
    return bytes(result)


def source_pairs(data: bytes, header: int) -> list[tuple[int, int]]:
    if u32(data, header) != 4:
        raise ValueError("unexpected P1 header")
    first = u16(data, header + 6)
    if first < 12 or (first - 4) % 8:
        raise ValueError("invalid P1 table boundary")
    pairs = []
    for event in range((first - 4) // 8):
        count, relative = struct.unpack_from("<2H", data, header + 4 + event * 8)
        for frame in range(count):
            pairs.append(struct.unpack_from("<2H", data, header + relative + frame * 12 + 2))
    return pairs


def native_pairs(data: bytes, header: int) -> list[tuple[int, int]]:
    table = u32(data, header) - BASE
    first = u32(data, table + 4) - BASE
    if table != header + 8 or first <= table or (first - table) % 16:
        raise ValueError("invalid native P1 table boundary")
    pairs = []
    for command in range(table, first, 16):
        count, pointer = struct.unpack_from("<2I", data, command)
        for frame in range(count):
            pairs.append(struct.unpack_from("<2H", data, pointer - BASE + frame * 16 + 2))
    return pairs


def check_asset(image: bytes, source: bytes, src: int, header: int, count: int,
                p1: int | None, native_p1: int | None) -> dict[str, object]:
    table = u32(image, header + 4) - BASE
    source_table = far_source(source, src + 2, count * 8 + 8)
    if source[source_table + count * 8:source_table + count * 8 + 8] != b"\xff" * 8:
        raise ValueError("source descriptor terminator changed")
    lengths, payload_ranges = [], []
    for index in range(count):
        descriptor = source_table + index * 8
        length = u16(source, descriptor)
        if not length or length % 32:
            raise ValueError("invalid source descriptor length")
        physical = far_source(source, descriptor + 2, length)
        if not 0 <= table + index * 8 <= len(image) - 8:
            raise ValueError("native descriptor pointer is outside the image")
        actual_length, pointer = struct.unpack_from("<2I", image, table + index * 8)
        if actual_length != length:
            raise ValueError(f"descriptor {index} length {actual_length} != source {length}")
        start = pointer - BASE
        if not 0 <= start < start + length <= len(image) or start % 4:
            raise ValueError("native tile payload is not addressable/aligned")
        if inverse_pixels(image[start:start + length]) != source[physical:physical + length]:
            raise ValueError(f"descriptor {index} pixels do not recover the source")
        lengths.append(length)
        payload_ranges.append((start, start + length))
    if image[header + 8:header + 16] != source[src + 8:src + 16]:
        raise ValueError("P0 shift/size/flags changed")
    layout_count = (u16(source, src + 18) - 16) // 4
    layout_table = u32(image, header) - BASE
    layouts = []
    for index in range(layout_count):
        n, relative = struct.unpack_from("<2H", source, src + 16 + index * 4)
        actual_n, pointer = struct.unpack_from("<2I", image, layout_table + index * 8)
        records = image[pointer - BASE:pointer - BASE + n * 4]
        if actual_n != n or records != source[src + relative:src + relative + n * 4]:
            raise ValueError("layout record identity/extent changed")
        # Native 12D50 loads only the low tile byte; high flip/palette bits
        # remain in their existing layout bytes and must not become an index.
        layouts.append([records[i * 4] for i in range(n)])
    if p1 is not None:
        pairs = source_pairs(source, p1)
        if native_pairs(image, native_p1) != pairs or {d for _, d in pairs} != set(range(count)):
            raise ValueError("P1 layout/descriptor selection differs from source")
        if not u16(image, header + 14) & 2:
            raise ValueError("indexed P0 lacks its dynamic descriptor flag")
    else:
        if u16(image, header + 14) & 2:
            raise ValueError("static P0 unexpectedly uses dynamic descriptor selection")
        pairs = [(layout, 0) for layout in range(layout_count)]
    tile_reads = 0
    for layout, descriptor in pairs:
        if layout >= len(layouts) or descriptor >= len(lengths):
            raise ValueError("animation pair escapes its layout/descriptor population")
        for tile in layouts[layout]:
            if (tile + 1) * 32 > lengths[descriptor]:
                raise ValueError("native tile read escapes the selected source payload")
            tile_reads += 1
    return {"native_table": table, "source_table": source_table, "descriptors": count,
            "tile_bytes": sum(lengths), "layouts": layout_count, "animation_or_static_pairs": len(pairs),
            "bounded_tile_reads": tile_reads, "payload_ranges": payload_ranges,
            "all_pixels_roundtrip": True, "all_layout_bytes_identical": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    before, after, gba, old, source = (getattr(args, key).read_bytes()
                                      for key in ("before", "after", "gba", "wsc10", "wsc15"))
    if sha256(before) != BEFORE_SHA256 or [sha256(x) for x in (gba, old, source)] != list(SOURCES):
        raise ValueError("input identity changed")
    # Independently verify the actual operand signatures, not the builder's
    # interpretation alone. No instruction interpreter or runtime is used.
    for pos, signature in (
        (0x75228A, "26 8B 75 02 26 8E 5D 04"),
        (0x752E9F, "C1 E2 03 03 FA"),
        (0x752EA7, "26 8B 75 02 26 8B 45 06 26 8E 5D 04 E6 C2"),
    ):
        expected = bytes.fromhex(signature)
        if source[pos:pos + len(expected)] != expected:
            raise ValueError("source DS/SI/C2 or index-stride instruction changed")
    for pos, signature in (
        (0x12C80, "BA A1 D5 E1 0A 42 84 E0 B4 30 D4 E1 48 40 95 E5 04 B0 94 E5"),
        (0x12C98, "02 00 11 E3 83 B1 8B 10 04 B0 9B E5"),
        (0x12D50, "00 30 DA E5 83 32 8B E0"),
    ):
        expected = bytes.fromhex(signature)
        if gba[pos:pos + len(expected)] != expected or after[pos:pos + len(expected)] != expected:
            raise ValueError("native pixel/descriptor-selection consumer changed")
    oracle = check_asset(gba, old, 0x2AD910, 0x3505E8, 21, 0x2AE180, 0x350248)
    results, negatives, allowed = [], [], set()
    for name, src, header, count, p1, native_p1, target in CASES:
        result = check_asset(after, source, src, header, count, p1, native_p1)
        if result["native_table"] != target:
            raise ValueError("unexpected repair table placement")
        end = result["payload_ranges"][-1][1]
        # Tables + zero alignment padding + contiguous payloads are wholly
        # owned; original code/layout/P1 bytes are outside the five pointers.
        first_payload = result["payload_ranges"][0][0]
        if after[target + count * 8:first_payload] != bytes(first_payload - target - count * 8):
            raise ValueError("unexpected descriptor-table padding")
        if any(a[1] != b[0] for a, b in zip(result["payload_ranges"], result["payload_ranges"][1:])):
            raise ValueError("tile payloads are not contiguous")
        if before[target:end] != b"\xff" * (end - target):
            raise ValueError("repair overwrites pre-existing data")
        allowed.update(range(target, end))
        allowed.update(range(header + 4, header + 8))
        for mutation in ("old-pointer", "last-pixel"):
            damaged = bytearray(after)
            if mutation == "old-pointer":
                damaged[header + 4:header + 8] = before[header + 4:header + 8]
            else:
                damaged[end - 1] ^= 1
            try:
                check_asset(damaged, source, src, header, count, p1, native_p1)
            except ValueError as error:
                negatives.append({"asset": name, "mutation": mutation, "rejected": True, "reason": str(error)})
            else:
                raise ValueError("semantic negative control unexpectedly passed")
        result.update({"name": name, "payload_sha256": sha256(after[target:end])})
        results.append(result)
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if len(after) != 0x800000 or len(changed) != 12400 or not changed <= allowed:
        raise ValueError("unexpected final repair extent/diff")
    if sha256(after) != AFTER_SHA256:
        raise ValueError("final image identity differs after semantic verification")
    report = {"schema": 1, "kind": "independent-shoot-far-tile-repair-verification",
              "before_sha256": BEFORE_SHA256, "after_sha256": AFTER_SHA256,
              "commercial_oracle": oracle, "assets": results, "negative_controls": negatives,
              "actual_changed_bytes": len(changed), "descriptors": sum(r["descriptors"] for r in results),
              "tile_bytes": sum(r["tile_bytes"] for r in results), "runtime_executed": False,
              "claim_scope": "source/native consumers, all five repaired P0 populations, every pixel, P1 selection, layout identity and exact diff only; no runtime, initializer tail or save QA"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-far-tiles-verify] PASS {report['descriptors']} descriptors, {report['tile_bytes']} tile bytes, 10 rejected mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
