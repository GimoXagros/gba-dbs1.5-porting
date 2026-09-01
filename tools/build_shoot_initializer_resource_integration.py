#!/usr/bin/env python3
"""Install all converted Shoot-initializer resources under Expected Writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06"
GBA_BASE = 0x08000000
OWNERSHIP_START = 0x5D0000
OWNERSHIP_END = 0x5DB768
ASSETS = (
    ("shoot-initializer-p1.bin", 0x5D0000, 2636, "778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2"),
    ("shoot-init-active-p0.bin", 0x5D1000, 128, "04F248F48F22DC66BEB965ADBCB72DDA271534A5BE9A8EB0B5F04CB373BD97BB"),
    ("shoot-init-rules-p0.bin", 0x5D1100, 41408, "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91"),
    ("shoot-init-extra-6d-p0.bin", 0x5DB300, 224, "D17DAC9D4464BF0E8D1577F4C98463B15CAC5F53D043F40DE61BC70851BC159B"),
    ("shoot-init-extra-137-p0.bin", 0x5DB400, 448, "716C3A7042A4DD9A7D6B9C12F172D08693DB264AE99D7AEBDFD886BC92CE0B62"),
    ("shoot-init-extra-91-p0.bin", 0x5DB600, 64, "7EFAC4D8ADF7A00450DBE2603187C4A3EF556FBC252BAE210D911934AC979214"),
    ("shoot-init-rules-p2.bin", 0x5DB700, 40, "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD"),
    ("shoot-init-extra-slot5-p2.bin", 0x5DB740, 40, "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def aligned_pointer_refs(data: bytes, start: int, end: int) -> list[dict[str, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + start <= value < GBA_BASE + end:
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
    if sha256(source) != INPUT_SHA256 or len(source) != 0x800000:
        raise SystemExit("refusing unexpected v41 candidate input")
    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (OWNERSHIP_END - OWNERSHIP_START):
        raise SystemExit("Shoot initializer resource ownership window is not blank")
    refs_before = aligned_pointer_refs(source, OWNERSHIP_START, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches Shoot initializer resource window: {refs_before}")

    placements = []
    for name, target, size, expected_hash in ASSETS:
        blob = (args.asset_dir / name).read_bytes()
        if len(blob) != size or sha256(blob) != expected_hash:
            raise SystemExit(f"unexpected Shoot initializer resource asset: {name}")
        placements.append((target, target + size, name, blob))
    placements.sort()
    for previous, current in zip(placements, placements[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"resource placements overlap: {previous[2]} / {current[2]}")
    if placements[0][0] != OWNERSHIP_START or placements[-1][1] != OWNERSHIP_END:
        raise SystemExit("resource ownership boundary changed")

    patched = bytearray(source)
    allowed = set()
    manifest_rows = []
    for start, end, name, blob in placements:
        before = bytes(patched[start:end])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"Expected Write input is not FF for {name}")
        patched[start:end] = blob
        allowed.update(range(start, end))
        manifest_rows.append({
            "file": name,
            "target": start,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })

    output = bytes(patched)
    actual = {
        offset for offset, (before, after) in enumerate(zip(source, output, strict=True))
        if before != after
    }
    if not actual or not actual <= allowed:
        raise SystemExit("Shoot initializer resource Expected Writes mismatch")
    for previous, current in zip(placements, placements[1:]):
        if output[previous[1]:current[0]] != source[previous[1]:current[0]]:
            raise SystemExit("resource placement gap changed")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-initializer-resource-integration-build",
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "ownership": {
            "start": OWNERSHIP_START,
            "end": OWNERSHIP_END,
            "preexisting_aligned_pointer_refs": refs_before,
            "basis": "exact v41 input, all-FF window, and zero aligned pre-existing pointers",
        },
        "expected_writes": manifest_rows,
        "actual_changed_bytes": len(actual),
        "claim_scope": (
            "resource bytes only; no code/menu pointer reaches the new window yet, and initializer "
            "reachability, runtime, visual output, audio, and supplied-save QA are excluded"
        ),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-initializer-resource-integration] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
