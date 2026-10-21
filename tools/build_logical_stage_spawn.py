#!/usr/bin/env python3
"""Make fighter spawn consume the same existing logical stage as stage setup."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BEFORE = "7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, SITE, BRIDGE, END = 0x08000000, 0x582F00, 0x627900, 0x62791C
POLICY = (0xE59F802C, 0xE5D8000A, 0xE350000B, 0x03A0000A,
          0x012FFF1E, 0xE350000D, 0x03A00008, 0x012FFF1E,
          0xE350000E, 0x03A00009, 0x012FFF1E, 0xE5D8000E,
          0xE12FFF1E, 0x03002310)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, target, link=False):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM branch range")
    return (0xEB000000 if link else 0xEA000000) | ((delta // 4) & 0xFFFFFF)


def inbound(data):
    for at in range(len(data) - 3):
        need(not BASE + BRIDGE <= word(data, at) < BASE + END, "existing encoded pointer into bridge")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            if delta & 0x800000:
                delta -= 1 << 24
            need(not BRIDGE <= at + 8 + delta * 4 < END, "existing ARM branch into bridge")
        if value & 0x0E1F0000 == 0x041F0000:
            delta = value & 0xFFF
            if not value & 0x00800000:
                delta = -delta
            need(not BRIDGE <= at + 8 + delta < END, "existing ARM literal into bridge")


def build(before, source):
    need((sha(before), sha(source)) == (BEFORE, SOURCE), "fixed collision predecessor and source")
    need(len(before) == 0x800000, "expanded ROM length")
    need(word(before, SITE) == 0xE59F8060 and word(before, SITE + 4) == 0xE5D8100E,
         "Expected Write repaired direct progression-stage load")
    need(word(before, 0xD1C78) == branch(0xD1C78, 0x582C40), "existing logical-stage service entry")
    need(before[0x582C40:0x582C78] == struct.pack("<14I", *POLICY), "exact temporary routing policy")
    need(before[0x583000:0x5830C0] == source[0x743224:0x7432E4], "source-backed spawn table")
    need(before[BRIDGE:END] == b"\xFF" * (END - BRIDGE), "new bridge bytes blank")
    inbound(before)
    payload = struct.pack("<7I", 0xE92D4001, branch(BRIDGE + 4, 0xD1C78, True),
                          0xE1A01000, 0xE8BD4001, 0xE59F8000,
                          branch(BRIDGE + 20, SITE + 8), 0x03002310)
    after = bytearray(before)
    after[BRIDGE:END] = payload
    struct.pack_into("<I", after, SITE, branch(SITE, BRIDGE))
    inverse = bytearray(after)
    for start, end in ((SITE, SITE + 4), (BRIDGE, END)):
        inverse[start:end] = before[start:end]
    need(inverse == before, "whole-ROM inverse outside exact hook and bridge")
    cases = []
    for character, stage in ((0x0B, 10), (0x0D, 8), (0x0E, 9)):
        for variant in range(4):
            for player in range(2):
                offset = stage * 16 + 16 + (variant & 1) * 8 + player * 4
                x, y = struct.unpack_from("<2H", source, 0x743224 + offset)
                cases.append({"character": character, "logical_stage": stage,
                              "variant_low2": variant, "player_nonzero": player,
                              "table_offset": offset, "world_x": x, "world_y": y})
    return bytes(after), {"schema": 1, "kind": "logical-stage-spawn-consumer", "input_sha256": BEFORE,
                         "output_sha256": sha(after), "expected_write": {"raw": SITE,
                         "before": "E59F8060", "after": f"{word(after, SITE):08X}"},
                         "new_interval": [BRIDGE, END], "bridge_sha256": sha(payload),
                         "existing_service": 0x080D1C78, "continuation": BASE + SITE + 8,
                         "source_stage_cases": cases, "stage_state_address": 0x03002310,
                         "progress_write": False, "new_RAM": False,
                         "ABI": {"replaced_outputs": ["r1=logical stage", "r8=03002310"],
                                 "preserved": ["r0", "r2-r7", "r9-r12", "LR", "SP"],
                                 "flags": "temporary service flags are overwritten by original CMP582F10 before conditional use"},
                         "changed_bytes": sum(a != b for a, b in zip(before, after, strict=True)),
                         "limitation": "adopts existing temporary character routing; does not implement source campaign progression"}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "wsc15", "output", "manifest")), "save paths forbidden")
    result, report = build(args.input.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[logical-stage-spawn] " + report["output_sha256"])


if __name__ == "__main__":
    main()
