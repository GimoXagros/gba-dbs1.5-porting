#!/usr/bin/env python3
"""Pin the confirmed WonderSwan Ver. 1.5 Digimon Shoot runtime regions.

The result is structural evidence for the GBA translation. It deliberately
does not load SRAM and does not claim that any internal GBA build runs the
mode. Each range is tied to an instruction-level observation made in the
fixed Ver. 1.5 source revision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"

REGIONS = (
    ("battle-loop-stage11-dispatch", 0x74583E, 0x745929,
     "stage ID 11 branches to the dedicated loop at raw 0x747E72"),
    ("dedicated-battle-loop", 0x747E72, 0x747FD1,
     "mode-specific battle loop and signed palette-fade state"),
    ("stage-update", 0x76AFD7, 0x76B03B,
     "stage ID 11 update, display callback registration, and helper calls"),
    ("stage-update-data", 0x76B03B, 0x76B1DB,
     "display thresholds and palette-animation tables consumed by the update"),
    ("stage-palette-helper", 0x76B1DB, 0x76B312,
     "three-rate palette animation writer"),
    ("display-callback", 0x75FADA, 0x75FBE2,
     "scanline/display callback 5EEA:0C3A"),
    ("display-transition-helper", 0x75FCAB, 0x75FE03,
     "transition state helper 5EEA:0E0B"),
    ("object-transition-stage11-branch", 0x760229, 0x7602AD,
     "stage ID 11 selects its distinct object/transition payload"),
    ("presentation-stage11-branch", 0x771F73, 0x772048,
     "stage ID 11 selects its presentation path"),
    ("exit-stage11-branch", 0x772553, 0x77256F,
     "stage ID 11 exits through the dedicated 71F0:1750 path"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    actual = sha256(data)
    if actual != WSC15_SHA256:
        raise SystemExit(f"refusing unknown WSC Ver. 1.5 ROM: {actual}")

    # Fixed instruction signatures prevent a plausible but wrong range from
    # silently becoming the build specification.
    signatures = {
        0x745846: bytes.fromhex("1E 57 BF 00 10 8E DF BF 4E 00 33 C0 8A 45 0E 5F 1F 3D 0B 00"),
        0x760229: bytes.fromhex("1E 57 BF 00 10 8E DF BF 4E 00 33 C0 8A 45 0E 5F 1F 3D 0B 00"),
        0x772553: bytes.fromhex("1E 57 BF 00 10 8E DF BF 4E 00 33 C0 8A 45 0E 5F 1F 3D 0B 00"),
        0x76AFD7: bytes.fromhex("55 8B EC 83 C4 FE BB CE 01 8B 57 12"),
        0x75FADA: bytes.fromhex("50 56 57 06 1E 9C E4 B2 24 EF E6 B2"),
        0x75FCAB: bytes.fromhex("50 51 52 53 56 57 06 1E BF 00 03 8E C7"),
    }
    for offset, expected in signatures.items():
        if data[offset:offset + len(expected)] != expected:
            raise SystemExit(f"Digimon Shoot signature failed at 0x{offset:X}")

    items = []
    for region_id, start, end, meaning in REGIONS:
        blob = data[start:end]
        items.append({
            "region_id": region_id,
            "raw_start": start,
            "raw_end": end,
            "bytes": len(blob),
            "sha256": sha256(blob),
            "confirmed_role": meaning,
        })

    result = {
        "schema": 1,
        "kind": "wsc15-digimon-shoot-runtime-structural-evidence",
        "source_sha256": actual,
        "stage_id": 11,
        "regions": items,
        "dependencies": {
            "dedicated_loop": "general battle loop branches away at raw 0x74585C",
            "stage_update": "overlay update-table entry 11 points to relative 0x2067",
            "display_callback": "5EEA:0C3A (physical 0x75FADA)",
            "display_helper": "5EEA:0E0B (physical 0x75FCAB)",
            "completion_bit": "word 1000:03D4 bit 0x8000 is produced by the mode fade path",
            "exit": "stage-11 branch calls 71F0:1750",
        },
        "claim_scope": (
            "static source-boundary evidence only; GBA mode translation and all "
            "emulator/save validation remain pending"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
