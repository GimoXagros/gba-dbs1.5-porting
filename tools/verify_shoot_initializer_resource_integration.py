#!/usr/bin/env python3
"""Independently verify the v42 Shoot-initializer resource-only ROM write."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


BEFORE_SHA256 = "B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06"
AFTER_SHA256 = "AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E"
GBA_BASE = 0x08000000
OWNERSHIP_START = 0x5D0000
OWNERSHIP_END = 0x5DB768
EXPECTED_CHANGED_BYTES = 44696
POST_POINTER_COUNT = 198
POST_POINTER_SHA256 = "3323C2B39379282766D682877260B232B273D665AD0F3BA3901141B20DCAB6C6"
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


def pointer_refs(data: bytes) -> list[tuple[int, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + OWNERSHIP_START <= value < GBA_BASE + OWNERSHIP_END:
            refs.append((offset, value))
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    if len(before) != 0x800000 or len(after) != len(before):
        raise SystemExit("unexpected ROM size")
    if sha256(before) != BEFORE_SHA256 or sha256(after) != AFTER_SHA256:
        raise SystemExit("refusing unexpected resource integration pair")
    if before[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (OWNERSHIP_END - OWNERSHIP_START):
        raise SystemExit("pre-write ownership window is not blank")
    if pointer_refs(before):
        raise SystemExit("pre-write aligned pointer reaches ownership window")

    allowed = set()
    placements = []
    for name, target, size, digest in ASSETS:
        blob = (args.asset_dir / name).read_bytes()
        if len(blob) != size or sha256(blob) != digest:
            raise SystemExit(f"unexpected independent asset input: {name}")
        if after[target:target + size] != blob:
            raise SystemExit(f"final ROM asset differs: {name}")
        allowed.update(range(target, target + size))
        placements.append({"file": name, "target": target, "bytes": size, "sha256": digest})

    changed = {
        offset for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if len(changed) != EXPECTED_CHANGED_BYTES or not changed <= allowed:
        raise SystemExit("final ROM diff escapes the declared resource placements")
    ordered = sorted((target, target + size) for _, target, size, _ in ASSETS)
    for previous, current in zip(ordered, ordered[1:]):
        if after[previous[1]:current[0]] != before[previous[1]:current[0]]:
            raise SystemExit("final ROM changed a placement gap")

    refs = pointer_refs(after)
    rendered_refs = b"".join(struct.pack("<II", offset, value) for offset, value in refs)
    if len(refs) != POST_POINTER_COUNT or sha256(rendered_refs) != POST_POINTER_SHA256:
        raise SystemExit("final internal pointer population changed")
    external_refs = [(offset, value) for offset, value in refs if not OWNERSHIP_START <= offset < OWNERSHIP_END]
    if external_refs:
        raise SystemExit("resource-only layer unexpectedly gained an external pointer")

    result = {
        "schema": 1,
        "kind": "internal-shoot-initializer-resource-integration-independent-verification",
        "before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256,
        "ownership": [OWNERSHIP_START, OWNERSHIP_END],
        "actual_changed_bytes": len(changed),
        "placements": placements,
        "post_internal_pointer_count": len(refs),
        "post_internal_pointer_population_sha256": POST_POINTER_SHA256,
        "post_external_pointer_count": len(external_refs),
        "claim_scope": (
            "exact resource-only diff containment, placed-asset hashes, preserved gaps, and internal "
            "pointer population; no code reachability, runtime, display, audio, or supplied-save QA"
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
