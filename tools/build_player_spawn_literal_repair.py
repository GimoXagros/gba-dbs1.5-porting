#!/usr/bin/env python3
"""Repair the stage-state literal in the relocated native fighter spawner."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

INPUT = "C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
ENTRY, POOL, TABLE = 0x582F00, 0x582F68, 0x583000


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch_target(data, at):
    instruction = word(data, at)
    need(instruction & 0xFF000000 == 0xEA000000, "unconditional ARM B")
    displacement = instruction & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 1 << 24
    return BASE + at + 8 + displacement * 4


def inbound(data, start, end):
    """Conservative encoded-pointer/ARM branch/literal guard for a new word."""
    pointers, branches, literals = [], [], []
    lo, hi = BASE + start, BASE + end
    for at in range(len(data) - 3):
        value = word(data, at)
        if lo <= value < hi:
            pointers.append(at)
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            displacement = value & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 1 << 24
            target = (BASE + at + 8 + displacement * 4) & 0xFFFFFFFF
            if lo <= target < hi:
                branches.append(at)
        # Immediate single-data-transfer load with Rn=PC. Includes byte loads.
        if value & 0x0E1F0000 == 0x041F0000:
            displacement = value & 0xFFF
            if not value & 0x00800000:
                displacement = -displacement
            target = BASE + at + 8 + displacement
            if lo <= target < hi:
                literals.append(at)
    return {"unaligned_pointer_offsets": pointers, "aligned_ARM_branch_offsets": branches,
            "aligned_ARM_literal_offsets": literals}


def build(before, gba, wsc15):
    need((sha(before), sha(gba), sha(wsc15)) == (INPUT, GBA, WSC15), "fixed input identities")
    need(len(before) == 0x800000, "expanded ROM size")
    need(sha(before[ENTRY:POOL]) ==
         "B7797750AC8ADED7D6901706DE534AF9253EC842E5B9CE58DA947EFC3652C628",
         "exact existing relocated constructor")
    need(word(before, ENTRY) == word(gba, 0x353130) == 0xE59F81C8,
         "observed copied PC-relative load")
    need(0x353130 + 8 + 0x1C8 == 0x353300 and word(gba, 0x353300) == 0x03002310,
         "actual retail stage-state owner")
    wrong_pool = ENTRY + 8 + 0x1C8
    need(wrong_pool == 0x5830D0 and word(before, wrong_pool) == 0xFFFFFFFF,
         "observed relocated load resolves to blank data")
    # The copied block has only two PC-relative loads and a final continuation.
    original_words = struct.unpack_from("<24I", gba, 0x353130)
    relocated_words = struct.unpack_from("<24I", before, ENTRY)
    for index, (original, relocated) in enumerate(zip(original_words, relocated_words, strict=True)):
        expected = {5: 0x22811010, 15: 0xE59F8020}.get(index, original)
        need(relocated == expected, f"retail instruction correspondence {index}")
    need(branch_target(before, 0x353130) == BASE + ENTRY, "native entry routes to relocated block")
    need(branch_target(before, ENTRY + 0x60) == 0x08353190, "retail continuation")
    need(word(before, ENTRY + 0x64) == BASE + TABLE, "second literal already resolves to table")
    need(before[TABLE:TABLE + 0xC0] == wsc15[0x743224:0x7432E4],
         "all source stage0..10 spawn pairs")
    need(before[TABLE:TABLE + 0x90] == gba[0x35326C:0x3532FC],
         "all retail stage0..7 spawn pairs retained")
    need(before[TABLE + 0xC0:TABLE + 0xD0] == gba[0x3532EC:0x3532FC],
         "existing stage11 placeholder retained without source-equivalence claim")
    need(before[POOL:POOL + 4] == b"\xFF" * 4, "new literal word is blank")
    guard = inbound(before, POOL, POOL + 4)
    need(not any(guard.values()), "new literal word has no pre-existing encoded inbound reference")

    after = bytearray(before)
    struct.pack_into("<I", after, ENTRY, 0xE59F8060)
    struct.pack_into("<I", after, POOL, 0x03002310)
    need(ENTRY + 8 + (word(after, ENTRY) & 0xFFF) == POOL, "repaired ARM PC-relative address")
    traces = []
    for stage in range(12):
        for variant in range(4):
            for player in range(2):
                row = stage * 16 + (16 if stage >= 7 else 0)
                masked_variant = variant if stage == 6 else variant & 1
                offset = row + masked_variant * 8 + player * 4
                need(0 <= offset <= 0xCC, "all supported selectors stay in the table")
                x, y = struct.unpack_from("<2H", after, TABLE + offset)
                traces.append({"stage": stage, "variant_low2": variant, "player_nonzero": player,
                               "table_offset": offset, "world_x": x, "world_y": y,
                               "source_equivalence": stage < 11,
                               "ordinary_spawn_permitted": stage < 11})
    inverse = bytearray(after)
    inverse[ENTRY:ENTRY + 4] = before[ENTRY:ENTRY + 4]
    inverse[POOL:POOL + 4] = before[POOL:POOL + 4]
    need(inverse == before, "full ROM inverse outside the two exact words")
    diff = [at for at, (old, new) in enumerate(zip(before, after, strict=True)) if old != new]
    need(diff == [ENTRY, ENTRY + 1, POOL, POOL + 1, POOL + 2, POOL + 3],
         "exact six changed bytes")
    return bytes(after), {
        "schema": 1, "kind": "player-spawn-literal-repair", "input_sha256": INPUT,
        "output_sha256": sha(after), "changed_bytes": diff,
        "expected_writes": [
            {"raw": ENTRY, "before": "E59F81C8", "after": "E59F8060"},
            {"raw": POOL, "before": "FFFFFFFF", "after": "03002310"}],
        "new_literal_interval": [POOL, POOL + 4], "predecessor_inbound_guard": guard,
        "native_stage_state": 0x03002310, "previous_invalid_pool": wrong_pool,
        "table_raw": TABLE, "table_sha256": sha(after[TABLE:TABLE + 0xD0]),
        "selector_traces": traces, "retail_continuation": 0x08353190,
        "source_stage0_through10_bytes": [0x743224, 0x7432E4],
        "stage11": "existing bounded placeholder preserved; dedicated Shoot must not use ordinary fighter spawn",
        "new_RAM": False, "new_callbacks": False,
        "scope": "repair actual-stage input to existing source-backed spawn selector; runtime verification is separate"}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "wsc15", "output", "manifest")), "save paths forbidden")
    result, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[player-spawn-literal-repair] " + report["output_sha256"])


if __name__ == "__main__":
    main()
