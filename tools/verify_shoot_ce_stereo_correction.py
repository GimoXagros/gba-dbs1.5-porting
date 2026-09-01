#!/usr/bin/env python3
"""Independently verify the CE stereo-direction correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


BEFORE_SHA256 = "7BB890FEC50BBAB796B5F94FE7761EAE9C4A284BB8E3CC9FA75A12FD20FB2264"
AFTER_SHA256 = "000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
CE_PAYLOAD_OFFSET = 0x3F88FC
CE_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A2 02 C1 00 A1 72 10 14 A0 09 A7 0A "
    "A0 06 A7 0A A0 03 A7 0A A0 01 A7 0A FF FF"
)
CE_PAYLOAD_SHA256 = "79BB15C2643DA24DAC1A16D7B760977257A7ABCA0B3DAE82383F85EFEF7C80B6"
CE_TRACK = 0x5BA70C
PAN_ARGUMENT = CE_TRACK + 9
D2_SONG = 0x5BA740
D2_SONG_BYTES = 67
D2_SONG_SHA256 = "E85983F5523E73C17A8D3404F98BC0EA8F0A96DA7FF41FB69A254078A1FE662F"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


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
    require_hash(before, BEFORE_SHA256, "v43 D2 candidate")
    require_hash(after, AFTER_SHA256, "v44 CE-stereo candidate")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != 0x800000 or len(after) != len(before):
        raise SystemExit("candidate size changed")
    payload = wsc15[CE_PAYLOAD_OFFSET:CE_PAYLOAD_OFFSET + len(CE_PAYLOAD)]
    require_hash(payload, CE_PAYLOAD_SHA256, "WSC CE payload")
    if payload != CE_PAYLOAD:
        raise SystemExit("WSC CE payload changed")
    stereo_values = [payload[2]] + [payload[offset + 1] for offset in (12, 16, 20, 24)]
    left = [value >> 4 for value in stereo_values]
    right = [value & 0x0F for value in stereo_values]
    if stereo_values != [15, 9, 6, 3, 1] or left != [0] * 5 or right != [15, 9, 6, 3, 1]:
        raise SystemExit("CE source stereo direction changed")
    if before[PAN_ARGUMENT - 1:PAN_ARGUMENT + 1] != bytes((0xBF, 0x40)):
        raise SystemExit("pre-correction CE PAN is not centered")
    if after[PAN_ARGUMENT - 1:PAN_ARGUMENT + 1] != bytes((0xBF, 0x7F)):
        raise SystemExit("post-correction CE PAN is not right")
    changed = [
        offset
        for offset, (left_byte, right_byte) in enumerate(zip(before, after, strict=True))
        if left_byte != right_byte
    ]
    if changed != [PAN_ARGUMENT]:
        raise SystemExit(f"CE stereo correction diff changed: {changed}")
    require_hash(before[D2_SONG:D2_SONG + D2_SONG_BYTES], D2_SONG_SHA256, "pre-correction D2 song")
    require_hash(after[D2_SONG:D2_SONG + D2_SONG_BYTES], D2_SONG_SHA256, "post-correction D2 song")

    result = {
        "schema": 1,
        "kind": "independent-shoot-ce-stereo-correction-verification",
        "claim_scope": (
            "exact one-byte diff from centered to right M4A pan, source-proved by "
            "the CE header and A0 high/low volume nibbles; D2 preservation checked; "
            "runtime and audibility excluded"
        ),
        "before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256,
        "changed_bytes": 1,
        "changed_offset": PAN_ARGUMENT,
        "wsc_ce_payload_sha256": CE_PAYLOAD_SHA256,
        "wsc_stereo_values": stereo_values,
        "left_nibbles": left,
        "right_nibbles": right,
        "before_pan": 64,
        "after_pan": 127,
        "d2_song_sha256": D2_SONG_SHA256,
        "runtime_audibility_verified": False,
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
