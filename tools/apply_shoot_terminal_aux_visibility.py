"""Use the terminal auxiliary actor's source hide flag in the late Shoot display guard."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def apply(image, source):
    if digest(source) != "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7":
        raise ValueError("unrecognized Ver. 1.5 source")
    if source[0x7486A9:0x7486BE] != bytes.fromhex("FF4C7E7401CB814C042000C704D87DC744029040CB") or source[0x7486D8] != 0xCB:
        raise ValueError("source auxiliary shutdown and return callback")
    for start, end, expected in (
        (0x5BF400, 0x5BF430, "2CA41960811DFFD2C571720284E9E29CE16337625FBD762219F0A524734F3C15"),
        (0x5BF600, 0x5BF604, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
        (0x6FF9C0, 0x6FFE10, "E5F590F7D5A8DB0595463356BA82637D01018ABE2E95AB56B8A30DC04280D8EF"),
    ):
        if digest(image[start:end]) != expected:
            raise ValueError(f"unexpected terminal code at {start:06X}")
    site = 0x6FFBE4
    # The source hides the auxiliary actor before scheduling its final callback.
    # Its previous animation event survives even when it no longer renders.
    words = (0xE1D600B4, 0xE2000020, 0xE3500020)
    result = bytearray(image)
    struct.pack_into("<3I", result, site, *words)
    manifest = {
        "kind": "shoot-terminal-auxiliary-visibility",
        "input_sha256": digest(image),
        "source_sha256": digest(source),
        "output_sha256": digest(result),
        "writes": [{"offset": site, "before": image[site:site+12].hex(), "after": result[site:site+12].hex()}],
    }
    return bytes(result), manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("image", "source", "output", "manifest"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    image, manifest = apply(args.image.read_bytes(), args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(manifest["output_sha256"])
