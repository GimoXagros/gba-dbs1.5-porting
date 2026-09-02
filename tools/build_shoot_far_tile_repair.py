#!/usr/bin/env python3
"""Repair five source-proved missing Shoot P0 descriptor/tile populations.

The historical v36/v42 layers mistook a non-0x2000 source segment for the end
of a descriptor table. This dependent layer preserves their P0 layouts and
all code, and replaces only five P0+4 pointers with complete native tables.
It neither installs an initializer tail nor claims runtime/menu reachability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

from build_full_asset_poc import build_far_descriptor_payload
from shoot_resource_conversion import parse_shoot_p1

INPUT_SHA256 = "ECE3D7E6428A81C93767FC72F79BC8EA5BD7E243E814FBEDCC6FFB079CEFDFC0"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
START, END = 0x5F2120, 0x5F5420
# name, source P0, existing native P0, population, tile bytes, paired source P1
CASES = (
    ("child", 0x22FF80, 0x5B9200, 15, 6528, 0x3D1E30),
    ("active", 0x3D5F80, 0x5D1000, 28, 3584, 0x3CF410),
    ("extra-6d", 0x3D44E0, 0x5DB300, 1, 768, None),
    ("extra-137", 0x3D0CA0, 0x5DB400, 1, 1568, None),
    ("extra-91", 0x3D7D30, 0x5DB600, 1, 128, None),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    if sha256(data) != expected:
        raise ValueError(f"{label} identity mismatch: {sha256(data)}")


def check_consumers(gba: bytes, wsc: bytes) -> None:
    # Direct WSC loader: descriptor +2 -> SI, +4 -> DS, +6 -> C2, +0 -> length.
    if wsc[0x752286:0x752295] != bytes.fromhex("26 8B 45 06 26 8B 75 02 26 8E 5D 04 26 8B 15"):
        raise ValueError("source direct-loader descriptor consumer changed")
    # Indexed loader: descriptor index times eight, followed by the same fields.
    if wsc[0x752E9C:0x752EB5] != bytes.fromhex(
        "8B 56 0A C1 E2 03 03 FA 26 8B 15 26 8B 75 02 26 8B 45 06 26 8E 5D 04 E6 C2"
    ):
        raise ValueError("source indexed-loader descriptor consumer changed")
    words = {
        0x12C8C: 0xE5954048, 0x12C90: 0xE594B004,
        0x12C98: 0xE3110002, 0x12C9C: 0x108BB183, 0x12CA0: 0xE59BB004,
        0x12D50: 0xE5DA3000, 0x12D54: 0xE08B3283,
    }
    for offset, expected in words.items():
        if struct.unpack_from("<I", gba, offset)[0] != expected:
            raise ValueError(f"native P0 pixel consumer changed at {offset:X}")


def commercial_oracle(gba: bytes, old: bytes) -> dict[str, object]:
    # Full commercial child population, not the old converter's 784-byte
    # layout-only prefix. It exercises nonzero offsets and segment 0x2E50.
    parsed = parse_shoot_p1(old, 0x2AE180)
    indices = {struct.unpack_from("<H", item, 4)[0]
               for row in parsed["payloads"] for item in row}
    if indices != set(range(21)):
        raise ValueError("commercial child descriptor population changed")
    target = struct.unpack_from("<I", gba, 0x3505EC)[0] - BASE
    converted, details = build_far_descriptor_payload(old, wsc_header=0x2AD910, target=target, count=21)
    if gba[target:target + len(converted)] != converted:
        raise ValueError("full non-0x2000 far descriptor conversion differs from retail GBA")
    return {"source_header": 0x2AD910, "native_table": target,
            "descriptors": 21, "bytes": len(converted), "tile_bytes": details["tile_bytes"],
            "exact": True, "sha256": sha256(converted)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    before, gba, old, source = (path.read_bytes() for path in (args.input, args.gba, args.wsc10, args.wsc15))
    for data, digest, label in ((before, INPUT_SHA256, "v47"), (gba, GBA_SHA256, "USA GBA"),
                                (old, WSC10_SHA256, "WSC 1.0"), (source, WSC15_SHA256, "WSC 1.5")):
        require_hash(data, digest, label)
    check_consumers(gba, source)
    oracle = commercial_oracle(gba, old)
    if len(before) != 0x800000 or before[START:END] != b"\xff" * (END - START):
        raise ValueError("tile repair exceeds unused owned expansion window")
    for offset in range(0, len(before), 4):
        word = struct.unpack_from("<I", before, offset)[0]
        if BASE + START <= word < BASE + END:
            raise ValueError(f"existing aligned pointer into new ownership at {offset:X}")
        # NV / 0xF is not an ARM7TDMI B/BL condition (later-ISA BLX encodings
        # must not turn pixel words such as 0xFB0BEB0B into fictitious callers).
        if word >> 28 != 0xF and word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if START <= offset + 8 + delta * 4 < END:
                raise ValueError(f"existing ARM branch into new ownership at {offset:X}")
    cursor, plan, assets = START, [], []
    for name, src, header, count, tile_bytes, p1 in CASES:
        cursor = (cursor + 31) & ~31
        blob, details = build_far_descriptor_payload(source, wsc_header=src, target=cursor, count=count)
        if details["tile_bytes"] != tile_bytes or cursor + len(blob) > END:
            raise ValueError(f"{name} population/placement changed")
        if p1 is not None:
            parsed = parse_shoot_p1(source, p1)
            indices = {struct.unpack_from("<H", item, 4)[0]
                       for row in parsed["payloads"] for item in row}
            if indices != set(range(count)):
                raise ValueError(f"{name} P1 does not cover the declared descriptor population")
        previous = before[header + 4:header + 8]
        old_table = struct.unpack("<I", previous)[0] - BASE
        if before[old_table:old_table + 8] not in (bytes(8), b"\xff" * 8):
            raise ValueError(f"{name} is not the diagnosed zero-descriptor v47 state")
        plan.extend(((cursor, b"\xff" * len(blob), blob, f"{name} descriptor/tile payload"),
                     (header + 4, previous, struct.pack("<I", BASE + cursor), f"{name} P0 descriptor pointer")))
        details.update({"name": name, "native_header": header, "previous_table": old_table,
                        "sha256": sha256(blob), "paired_source_p1": p1})
        assets.append(details)
        cursor += len(blob)
    allowed: set[int] = set()
    for site, expected, replacement, label in plan:
        owned = set(range(site, site + len(replacement)))
        if len(expected) != len(replacement) or before[site:site + len(expected)] != expected or owned & allowed:
            raise ValueError(f"Expected Write failed: {label}")
        allowed |= owned
    result = bytearray(before)
    for site, expected, replacement, label in plan:
        result[site:site + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, result, strict=True)) if a != b}
    expected_changed = {site + i for site, a, b, _ in plan
                        for i, (left, right) in enumerate(zip(a, b, strict=True)) if left != right}
    if changed != expected_changed or not changed <= allowed:
        raise ValueError("final image diff is not exactly the planned repair")
    report = {"schema": 1, "kind": "shoot-far-tile-descriptor-repair", "input_sha256": INPUT_SHA256,
              "output_sha256": sha256(result), "output_bytes": len(result),
              "commercial_oracle": oracle, "assets": assets, "ownership": [START, END],
              "expected_writes": [{"offset": site, "bytes": len(b), "meaning": label,
                                   "before_sha256": sha256(a), "after_sha256": sha256(b)}
                                  for site, a, b, label in plan],
              "actual_changed_bytes": len(changed),
              "claim_scope": "five native P0 tables and all 46 source descriptors/393 tiles repaired; layouts and code unchanged; initializer tail/menu/controller and all runtime/save QA remain incomplete"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-far-tiles] static repair {report['output_sha256']} ({len(changed)} changed bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
