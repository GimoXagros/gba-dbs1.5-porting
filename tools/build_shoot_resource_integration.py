#!/usr/bin/env python3
"""Install the Ver. 1.5 Shoot child resources under an Expected Writes contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F"
GBA_BASE = 0x08000000
PRIOR_DECLARED_END = 0x5B851C
RESERVED_END = 0x5B9328
ASSETS = {
    "p1": {
        "file": "shoot-spawn-p1.bin",
        "target": 0x5B9000,
        "bytes": 384,
        "sha256": "6E854C5F2138D74B9860843DF8DBC3144AEB71CB04BF5F1875B0E73F26DB4E78",
    },
    "p0": {
        "file": "shoot-spawn-p0.bin",
        "target": 0x5B9200,
        "bytes": 128,
        "sha256": "023A9E47227DC88431A6EE129F40D79944A3173E365DF0B10F615C6D7738D6B8",
    },
    "p2": {
        "file": "shoot-spawn-p2.bin",
        "target": 0x5B9300,
        "bytes": 40,
        "sha256": "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def aligned_pointer_refs(data: bytes, start: int, end: int) -> list[dict[str, int]]:
    address_start = GBA_BASE + start
    address_end = GBA_BASE + end
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if address_start <= value < address_end:
            refs.append({"offset": offset, "value": value})
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    require_hash(source, INPUT_SHA256, "current candidate input")
    if len(source) != 0x800000:
        raise SystemExit("current candidate is not the expected 8 MiB expansion")
    if source[PRIOR_DECLARED_END:RESERVED_END] != bytes([0xFF]) * (
        RESERVED_END - PRIOR_DECLARED_END
    ):
        raise SystemExit("Shoot resource ownership window is not blank")
    refs_before = aligned_pointer_refs(source, 0x5B9000, RESERVED_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches Shoot resource window: {refs_before}")

    placements = []
    blobs = {}
    for kind, spec in ASSETS.items():
        blob = (args.asset_dir / str(spec["file"])).read_bytes()
        if len(blob) != spec["bytes"]:
            raise SystemExit(f"unexpected {kind} resource size")
        require_hash(blob, str(spec["sha256"]), f"Shoot {kind} resource")
        blobs[kind] = blob
        target = int(spec["target"])
        placements.append((target, target + len(blob), kind))
    placements.sort()
    for previous, current in zip(placements, placements[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"Shoot resource placements overlap: {previous[2]} / {current[2]}")

    patched = bytearray(source)
    expected_offsets = set()
    manifest_placements = []
    for start, end, kind in placements:
        blob = blobs[kind]
        before = bytes(patched[start:end])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"Shoot {kind} Expected Write input is not all FF")
        patched[start:end] = blob
        expected_offsets.update(range(start, end))
        manifest_placements.append({
            "kind": kind,
            "file": ASSETS[kind]["file"],
            "target": start,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })

    actual_offsets = {
        offset
        for offset, (before, after) in enumerate(zip(source, patched, strict=True))
        if before != after
    }
    if not actual_offsets <= expected_offsets:
        extra = sorted(actual_offsets - expected_offsets)[:8]
        raise SystemExit(f"Expected Writes mismatch: extra={extra}")
    if patched[PRIOR_DECLARED_END:0x5B9000] != source[PRIOR_DECLARED_END:0x5B9000]:
        raise SystemExit("ownership gap before Shoot resources changed")
    if patched[0x5B9180:0x5B9200] != source[0x5B9180:0x5B9200]:
        raise SystemExit("gap between Shoot P1 and P0 changed")
    if patched[0x5B9280:0x5B9300] != source[0x5B9280:0x5B9300]:
        raise SystemExit("gap between Shoot P0 and P2 changed")

    output = bytes(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-resource-integration-build",
        "claim_scope": (
            "Expected Writes placement of the converted Shoot P1/P0/P2 resources; "
            "no callback points at them yet and runtime consumption is not claimed"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "ownership": {
            "prior_declared_end": PRIOR_DECLARED_END,
            "reserved_end": RESERVED_END,
            "preexisting_aligned_pointer_refs": refs_before,
            "basis": (
                "exact v35 input, 8 MiB builder-owned expansion, all-FF ownership window, "
                "and no aligned GBA ROM pointer into the planned resource interval"
            ),
        },
        "expected_writes": manifest_placements,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-resource-integration] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
