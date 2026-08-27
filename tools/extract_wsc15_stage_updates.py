#!/usr/bin/env python3
"""Extract the proven Ver. 1.5 stage overlay tables and function windows.

This is deliberately a structural extractor rather than an emulator test.  It
pins the exact source bytes that the GBA implementations are derived from.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
OVERLAY_RAW_BASE = 0x768F70
PREP_TABLE_REL = 0x0000
UPDATE_TABLE_REL = 0x043C
STAGE_NAMES = (
    "retail-0", "retail-1", "retail-2", "retail-3",
    "retail-4", "retail-5", "retail-6", "retail-7",
    "train", "waterfall", "iraira-room", "digimon-shoot",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def read_table(data: bytes, relative: int) -> tuple[int, ...]:
    raw = OVERLAY_RAW_BASE + relative
    return struct.unpack_from("<12H", data, raw)


def windows(data: bytes, pointers: tuple[int, ...], final_end: int) -> list[dict[str, object]]:
    result = []
    for index, (name, start) in enumerate(zip(STAGE_NAMES, pointers, strict=True)):
        end = pointers[index + 1] if index + 1 < len(pointers) else final_end
        blob = data[OVERLAY_RAW_BASE + start:OVERLAY_RAW_BASE + end]
        result.append({
            "stage_id": index,
            "stage": name,
            "relative_start": start,
            "relative_end": end,
            "raw_start": OVERLAY_RAW_BASE + start,
            "raw_end": OVERLAY_RAW_BASE + end,
            "bytes": len(blob),
            "sha256": sha256(blob),
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()

    data = args.rom.read_bytes()
    actual = sha256(data)
    if actual != WSC15_SHA256:
        raise SystemExit(f"refusing unknown WSC Ver. 1.5 ROM: {actual}")

    prep = read_table(data, PREP_TABLE_REL)
    update = read_table(data, UPDATE_TABLE_REL)
    expected_prep = (0x0109, 0x0166, 0x0196, 0x01B1, 0x02AE, 0x0371,
                     0x037C, 0x0382, 0x03BE, 0x03E6, 0x03F1, 0x03F7)
    expected_update = (0x04DA, 0x08A2, 0x0BF2, 0x0F27, 0x10C3, 0x1202,
                       0x13E3, 0x1901, 0x195C, 0x1AC3, 0x1D86, 0x2067)
    if prep != expected_prep or update != expected_update:
        raise SystemExit("Ver. 1.5 stage overlay table invariant failed")

    result = {
        "schema": 1,
        "kind": "wsc15-stage-overlay-structural-evidence",
        "source_sha256": actual,
        "overlay_raw_base": OVERLAY_RAW_BASE,
        "stage_id_order": list(STAGE_NAMES),
        "preparation_table": {
            "relative_offset": PREP_TABLE_REL,
            "raw_offset": OVERLAY_RAW_BASE + PREP_TABLE_REL,
            "pointers": list(prep),
            # The last preparation routine ends at the update table itself.
            "windows": windows(data, prep, UPDATE_TABLE_REL),
        },
        "update_table": {
            "relative_offset": UPDATE_TABLE_REL,
            "raw_offset": OVERLAY_RAW_BASE + UPDATE_TABLE_REL,
            "pointers": list(update),
            # ID 11 is followed by the next overlay routine at 0x2305.
            "windows": windows(data, update, 0x2305),
        },
        "new_stage_update_sources": {
            "train": {"stage_id": 8, "raw": OVERLAY_RAW_BASE + update[8], "relative": update[8]},
            "waterfall": {"stage_id": 9, "raw": OVERLAY_RAW_BASE + update[9], "relative": update[9]},
            "iraira-room": {"stage_id": 10, "raw": OVERLAY_RAW_BASE + update[10], "relative": update[10]},
            "digimon-shoot": {"stage_id": 11, "raw": OVERLAY_RAW_BASE + update[11], "relative": update[11]},
        },
        "claim_scope": "static extraction only; no runtime or save-state claim",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
