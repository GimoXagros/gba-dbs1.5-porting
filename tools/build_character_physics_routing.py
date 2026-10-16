#!/usr/bin/env python3
"""Replace the three misrouted physics payloads over exact v54.

The corrected native pointers and their existing allocation stay in place.
This adds no code, callbacks, or RAM state. Frozen earlier layers are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_character_physics_assets import (
    GBA_SHA256, WSC15_SHA256, converted_record, source_record_offset,
)

BEFORE = "CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69"
BASE = 0x08000000
TABLE = 0x485000
START, END = 0x4850B4, 0x48521C


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def build(before: bytes, gba: bytes, wsc: bytes) -> tuple[bytes, dict]:
    need((sha(before), sha(gba), sha(wsc)) == (BEFORE, GBA_SHA256, WSC15_SHA256),
         "exact v54 and immutable source identities")
    need(len(before) == 0x800000, "expanded ROM extent")
    need(struct.unpack_from("<I", before, 0x3532FC)[0] == BASE + TABLE,
         "actual constructor must select the installed physics table")
    pointers = struct.unpack_from("<15I", before, TABLE)
    need(pointers == tuple(BASE + 0x353508 + n * 0x78 for n in range(12))
         + tuple(BASE + START + n * 0x78 for n in range(3)), "v49 corrected native pointers")
    need(before[TABLE + 60:START] == bytes(120), "existing reserved gap")
    writes = []
    for character in (12, 13, 14):
        at = pointers[character] - BASE
        prior = converted_record(wsc, character, legacy_source_routing=True)
        replacement = converted_record(wsc, character)
        need(len(prior) == len(replacement) == 0x78, "complete physics group")
        need(before[at:at + len(prior)] == prior, f"Expected Write ID {character} prior payload")
        need(prior != replacement, f"ID {character} must correct source routing")
        writes.append((at, prior, replacement, character))
    output = bytearray(before)
    for at, _prior, replacement, _character in writes:
        output[at:at + len(replacement)] = replacement
    changed = {i for i, (a, b) in enumerate(zip(before, output, strict=True)) if a != b}
    expected = {at + n for at, prior, replacement, _ in writes
                for n, (a, b) in enumerate(zip(prior, replacement, strict=True)) if a != b}
    need(changed == expected and changed <= set(range(START, END)), "exact three payload writes")
    details = []
    for at, prior, replacement, character in writes:
        old_values, values = struct.unpack("<60h", prior), struct.unpack("<60h", replacement)
        details.append({
            "character": character, "offset": at, "bytes": len(replacement),
            "source_pointer_site": 0x3B8460 + character * 2,
            "source_offset": source_record_offset(wsc, character),
            "historical_source_offset": source_record_offset(wsc, character, legacy_source_routing=True),
            "before_sha256": sha(prior), "after_sha256": sha(replacement),
            "changed_halfwords": [n for n, (a, b) in enumerate(zip(old_values, values, strict=True)) if a != b],
        })
    return bytes(output), {
        "schema": 1, "kind": "character-physics-source-routing-repair",
        "input_sha256": BEFORE, "output_sha256": sha(output),
        "source_gba_sha256": GBA_SHA256, "source_wsc_sha256": WSC15_SHA256,
        "source_pointer_table": 0x3B8460, "native_pointer_table": BASE + TABLE,
        "expected_writes": details, "actual_changed_bytes": len(changed),
        "pointer_words_changed": 0, "code_bytes_changed": 0,
        "allocation": {"start": START, "end": END, "new_allocation": False},
        "claim_scope": "source character routing and converted complete physics groups; runtime cause and whole-port completion require separate verification",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav"
             for name in ("input", "gba", "wsc15", "output", "manifest")), "save files forbidden")
    output, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[character-physics-routing] {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
