#!/usr/bin/env python3
"""Independently verify the bounded Shoot resource integration layer.

This verifier intentionally does not import the resource converter.  It checks
fixed source/output identities, exact diff boundaries, and the native GBA
container topology directly from the installed bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F"
OUTPUT_SHA256 = "4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
PLACEMENTS = {
    "p1": (0x5B9000, 384, "6E854C5F2138D74B9860843DF8DBC3144AEB71CB04BF5F1875B0E73F26DB4E78"),
    "p0": (0x5B9200, 128, "023A9E47227DC88431A6EE129F40D79944A3173E365DF0B10F615C6D7738D6B8"),
    "p2": (0x5B9300, 40, "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def refs_into_window(data: bytes) -> list[tuple[int, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if 0x085B9000 <= value < 0x085B9328:
            refs.append((offset, value))
    return refs


def verify_p1(blob: bytes) -> dict[str, object]:
    header = struct.unpack_from("<2I", blob, 0)
    if header != (0x085B9008, 0):
        raise SystemExit("Shoot P1 header topology changed")
    commands = [struct.unpack_from("<4I", blob, 8 + index * 16) for index in range(3)]
    expected = [
        (6, 0x085B9038, 0x085B9178, 0),
        (8, 0x085B9098, 0x085B9178, 0),
        (6, 0x085B9118, 0x085B9178, 0),
    ]
    if commands != expected:
        raise SystemExit("Shoot P1 command table changed")
    payloads = [blob[0x38:0x98], blob[0x98:0x118], blob[0x118:0x178]]
    if [len(payload) // 16 for payload in payloads] != [6, 8, 6]:
        raise SystemExit("Shoot P1 payload boundaries changed")
    if any(len(payload) % 16 for payload in payloads):
        raise SystemExit("Shoot P1 payload item width changed")
    a_record = blob[0x178:0x180]
    if a_record != bytes.fromhex("0A 0A 01 14 00 00 00 00"):
        raise SystemExit("Shoot P1 A record changed")
    return {
        "commands": len(commands),
        "payload_items": sum(len(payload) // 16 for payload in payloads),
        "a_records": 1,
        "internal_pointer_targets": sorted({
            value for command in commands for value in command[1:3]
        } | {header[0]}),
    }


def verify_p0(blob: bytes) -> dict[str, object]:
    header = struct.unpack_from("<4I", blob, 0)
    if header != (0x085B9210, 0x085B9270, 0x00100005, 0x000A0200):
        raise SystemExit("Shoot P0 header topology changed")
    layouts = [struct.unpack_from("<2I", blob, 0x10 + index * 8) for index in range(2)]
    if layouts != [(4, 0x085B9220), (16, 0x085B9230)]:
        raise SystemExit("Shoot P0 layout table changed")
    if len(blob[0x20:0x70]) != 80:
        raise SystemExit("Shoot P0 layout record boundary changed")
    if blob[0x70:0x80] != bytes(16):
        raise SystemExit("Shoot P0 zero-descriptor tail changed")
    return {
        "layouts": len(layouts),
        "layout_records_bytes": 80,
        "descriptors": 0,
        "tile_bytes": 0,
        "internal_pointer_targets": [header[0], header[1], layouts[0][1], layouts[1][1]],
    }


def verify_p2(blob: bytes) -> dict[str, object]:
    words = struct.unpack("<20H", blob)
    if words[:4] != (1, 1, 8, 31) or words[-4:] != (0x02BF, 0x03BF, 0x7FFF, 0):
        raise SystemExit("Shoot P2 palette boundary values changed")
    return {"words": len(words), "first_four": list(words[:4]), "last_four": list(words[-4:])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, INPUT_SHA256, "pre-resource candidate")
    require_hash(after, OUTPUT_SHA256, "resource-integrated candidate")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != len(after) or len(after) != 0x800000:
        raise SystemExit("candidate size changed")
    if refs_into_window(before):
        raise SystemExit("pre-resource candidate already references the Shoot window")

    allowed = set()
    blobs = {}
    for kind, (target, size, expected_hash) in PLACEMENTS.items():
        old = before[target:target + size]
        if old != bytes([0xFF]) * size:
            raise SystemExit(f"pre-resource {kind} target is not blank")
        blob = after[target:target + size]
        require_hash(blob, expected_hash, f"installed Shoot {kind}")
        blobs[kind] = blob
        allowed.update(range(target, target + size))
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("resource integration has an unexplained diff")

    expected_refs = [
        (0x5B9000, 0x085B9008),
        (0x5B900C, 0x085B9038),
        (0x5B9010, 0x085B9178),
        (0x5B901C, 0x085B9098),
        (0x5B9020, 0x085B9178),
        (0x5B902C, 0x085B9118),
        (0x5B9030, 0x085B9178),
        (0x5B9200, 0x085B9210),
        (0x5B9204, 0x085B9270),
        (0x5B9214, 0x085B9220),
        (0x5B921C, 0x085B9230),
    ]
    refs_after = refs_into_window(after)
    if refs_after != expected_refs:
        raise SystemExit(f"unexpected Shoot resource pointer population: {refs_after}")

    result = {
        "schema": 1,
        "kind": "independent-shoot-resource-integration-verification",
        "claim_scope": (
            "fixed identities, exact diff containment, native container topology, and "
            "disconnected internal pointer population; runtime reachability excluded"
        ),
        "before_sha256": INPUT_SHA256,
        "after_sha256": OUTPUT_SHA256,
        "wsc15_sha256": WSC15_SHA256,
        "changed_bytes": len(changed),
        "placements": {
            kind: {"target": target, "bytes": size, "sha256": digest}
            for kind, (target, size, digest) in PLACEMENTS.items()
        },
        "p1": verify_p1(blobs["p1"]),
        "p0": verify_p0(blobs["p0"]),
        "p2": verify_p2(blobs["p2"]),
        "aligned_pointer_refs_before": [],
        "aligned_pointer_refs_after": [
            {"offset": offset, "value": value} for offset, value in refs_after
        ],
        "runtime_reachable": False,
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
