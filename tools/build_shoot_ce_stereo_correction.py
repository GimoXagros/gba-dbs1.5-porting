#!/usr/bin/env python3
"""Correct the bounded CE reconstruction's source-proved stereo direction."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


INPUT_SHA256 = "7BB890FEC50BBAB796B5F94FE7761EAE9C4A284BB8E3CC9FA75A12FD20FB2264"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
CE_PAYLOAD_OFFSET = 0x3F88FC
CE_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A2 02 C1 00 A1 72 10 14 A0 09 A7 0A "
    "A0 06 A7 0A A0 03 A7 0A A0 01 A7 0A FF FF"
)
CE_PAYLOAD_SHA256 = "79BB15C2643DA24DAC1A16D7B760977257A7ABCA0B3DAE82383F85EFEF7C80B6"
CE_TRACK = 0x5BA70C
PAN_ARGUMENT = CE_TRACK + 9
BEFORE_PAN = 0x40
AFTER_PAN = 0x7F


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(source, INPUT_SHA256, "v43 D2 candidate")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    payload = wsc15[CE_PAYLOAD_OFFSET:CE_PAYLOAD_OFFSET + len(CE_PAYLOAD)]
    require_hash(payload, CE_PAYLOAD_SHA256, "WSC CE payload")
    if payload != CE_PAYLOAD:
        raise SystemExit("WSC CE payload changed")
    stereo_values = [payload[2]] + [payload[offset + 1] for offset in (12, 16, 20, 24)]
    if stereo_values != [0x0F, 9, 6, 3, 1]:
        raise SystemExit(f"CE stereo schedule changed: {stereo_values}")
    if any(value >> 4 for value in stereo_values) or any((value & 0x0F) == 0 for value in stereo_values):
        raise SystemExit("CE no longer has a right-only source volume schedule")
    if source[PAN_ARGUMENT - 1:PAN_ARGUMENT + 1] != bytes((0xBF, BEFORE_PAN)):
        raise SystemExit("CE M4A PAN command changed")

    patched = bytearray(source)
    patched[PAN_ARGUMENT] = AFTER_PAN
    output = bytes(patched)
    changed = [
        offset
        for offset, (left, right) in enumerate(zip(source, output, strict=True))
        if left != right
    ]
    if changed != [PAN_ARGUMENT]:
        raise SystemExit(f"CE stereo correction diff changed: {changed}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-ce-stereo-correction",
        "claim_scope": (
            "one-byte M4A pan correction from center to right, derived from the CE "
            "header and all four A0 volume commands having zero left/high nibbles; "
            "runtime playback and audible parity excluded"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "changed_bytes": 1,
        "expected_write": {
            "target": PAN_ARGUMENT,
            "before": BEFORE_PAN,
            "after": AFTER_PAN,
            "before_sha256": sha256(bytes((BEFORE_PAN,))),
            "after_sha256": sha256(bytes((AFTER_PAN,))),
        },
        "wsc_ce_payload_sha256": CE_PAYLOAD_SHA256,
        "wsc_stereo_values": stereo_values,
        "left_nibbles": [value >> 4 for value in stereo_values],
        "right_nibbles": [value & 0x0F for value in stereo_values],
        "runtime_audibility_verified": False,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-ce-stereo] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
