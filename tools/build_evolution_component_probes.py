#!/usr/bin/env python3
"""Build internal probes that isolate evolution-ID-11 resource components."""

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
EVOLUTION_ID = 11


def copy_field(patched: bytearray, source: bytes, source_record: int,
               target_record: int, field: int) -> None:
    value = struct.unpack_from("<I", source, source_record + field * 4)[0]
    struct.pack_into("<I", patched, target_record + field * 4, value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("integrated_rom", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()
    source = args.integrated_rom.read_bytes()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    evo_current = EVOLUTION_TABLE + EVOLUTION_ID * RECORD_BYTES
    evo_previous = EVOLUTION_TABLE + (EVOLUTION_ID - 1) * RECORD_BYTES
    base_current = BASE_TABLE + PROBE_ID * RECORD_BYTES
    base_previous = BASE_TABLE + (PROBE_ID - 1) * RECORD_BYTES
    components = {
        "palette": ((evo_current, base_current, 0), (evo_current, base_current, 1)),
        "p4": ((evo_current, base_current, 2),),
        "p0": ((evo_previous, base_previous, 6),),
        "p1": ((evo_previous, base_previous, 7),),
        "p0-p4": (
            (evo_previous, base_previous, 6), (evo_current, base_current, 2),
        ),
        "p0-palette": (
            (evo_previous, base_previous, 6),
            (evo_current, base_current, 0), (evo_current, base_current, 1),
        ),
        "without-p4": (
            (evo_current, base_current, 0), (evo_current, base_current, 1),
            (evo_previous, base_previous, 6), (evo_previous, base_previous, 7),
        ),
        "all": (
            (evo_current, base_current, 0), (evo_current, base_current, 1),
            (evo_current, base_current, 2), (evo_previous, base_previous, 6),
            (evo_previous, base_previous, 7),
        ),
    }
    entries = []
    for name, fields in components.items():
        patched = bytearray(source)
        for source_record, target_record, field in fields:
            copy_field(patched, source, source_record, target_record, field)
        output = args.output_dir / f"evolution-11-{name}-only.gba"
        output.write_bytes(patched)
        entries.append({
            "component": name,
            "output": output.name,
            "sha256": hashlib.sha256(patched).hexdigest().upper(),
        })
    manifest = {"kind": "internal-evolution-component-probes", "entries": entries}
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
