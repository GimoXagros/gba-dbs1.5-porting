#!/usr/bin/env python3
"""Build internal ROM probes that load each new evolution as Tailmon's base form."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


RECORD_BYTES = 0x20
BASE_TABLE = 0x4A8100
EVOLUTION_TABLE = 0x4A82E0
PROBE_ID = 14


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("integrated_rom", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()
    source = args.integrated_rom.read_bytes()
    if len(source) != 0x800000:
        raise SystemExit("expected the 8 MiB internal integration ROM")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for evolution_id in (11, 12, 13, 14):
        patched = bytearray(source)
        evolution_current = EVOLUTION_TABLE + evolution_id * RECORD_BYTES
        base_current = BASE_TABLE + PROBE_ID * RECORD_BYTES
        for field in (0, 1, 2):
            value = struct.unpack_from("<I", source, evolution_current + field * 4)[0]
            struct.pack_into("<I", patched, base_current + field * 4, value)
        evolution_previous = EVOLUTION_TABLE + (evolution_id - 1) * RECORD_BYTES
        base_previous = BASE_TABLE + (PROBE_ID - 1) * RECORD_BYTES
        for field in (6, 7):
            value = struct.unpack_from("<I", source, evolution_previous + field * 4)[0]
            struct.pack_into("<I", patched, base_previous + field * 4, value)
        output = args.output_dir / f"evolution-{evolution_id:02d}-as-id14.gba"
        output.write_bytes(patched)
        entries.append({
            "evolution_id": evolution_id,
            "output": output.name,
            "sha256": hashlib.sha256(patched).hexdigest().upper(),
        })
    manifest = {
        "kind": "internal-evolution-smoke-probes",
        "source_sha256": hashlib.sha256(source).hexdigest().upper(),
        "entries": entries,
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
