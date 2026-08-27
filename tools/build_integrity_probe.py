#!/usr/bin/env python3
"""Create a one-byte, trailing-padding mutation to probe ROM integrity checks."""

from __future__ import annotations

import argparse
import hashlib
import pathlib


EXPECTED_SHA256 = "996de33330ac729d10d761d1901e7a335191c9503b0470569e8f294acf6618ed"
OFFSET = 0x3FFFFF


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    data = bytearray(args.gba.read_bytes())
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if data[OFFSET] != 0xFF:
        raise SystemExit("expected-write check failed")
    data[OFFSET] = 0xFE
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"changed 0x{OFFSET:X}: FF -> FE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
