#!/usr/bin/env python3
"""Build internal evolution probes using complete retail GBA P1 templates."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


RECORD_BYTES = 0x20
BASE_TABLE = 0x4A8100
EVOLUTION_TABLE = 0x4A82E0
ORIGINAL_EVOLUTION_TABLE = 0x0D42A0
PROBE_ID = 14


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("integrated_rom", type=pathlib.Path)
    parser.add_argument("output_dir", type=pathlib.Path)
    args = parser.parse_args()
    source = args.integrated_rom.read_bytes()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for evolution_id in (11, 12, 13, 14):
        patched = bytearray(source)
        evo_current = EVOLUTION_TABLE + evolution_id * RECORD_BYTES
        base_current = BASE_TABLE + PROBE_ID * RECORD_BYTES
        for field in (0, 1, 2):
            value = struct.unpack_from("<I", source, evo_current + field * 4)[0]
            struct.pack_into("<I", patched, base_current + field * 4, value)
        evo_previous = EVOLUTION_TABLE + (evolution_id - 1) * RECORD_BYTES
        base_previous = BASE_TABLE + (PROBE_ID - 1) * RECORD_BYTES
        p0 = struct.unpack_from("<I", source, evo_previous + 6 * 4)[0]
        struct.pack_into("<I", patched, base_previous + 6 * 4, p0)
        template_runtime = 1
        template_p4 = struct.unpack_from(
            "<I", source,
            ORIGINAL_EVOLUTION_TABLE + template_runtime * RECORD_BYTES + 2 * 4,
        )[0]
        struct.pack_into("<I", patched, base_current + 2 * 4, template_p4)
        template_p1 = struct.unpack_from(
            "<I", source,
            ORIGINAL_EVOLUTION_TABLE + (template_runtime - 1) * RECORD_BYTES + 7 * 4,
        )[0]
        struct.pack_into("<I", patched, base_previous + 7 * 4, template_p1)
        output = args.output_dir / f"evolution-{evolution_id:02d}-native-p1-p4.gba"
        output.write_bytes(patched)
        entries.append({
            "evolution_id": evolution_id,
            "template_runtime": template_runtime,
            "template_p1": f"0x{template_p1:08X}",
            "template_p4": f"0x{template_p4:08X}",
            "output": output.name,
            "sha256": hashlib.sha256(patched).hexdigest().upper(),
        })
    manifest = {"kind": "internal-evolution-native-p1-smoke", "entries": entries}
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
