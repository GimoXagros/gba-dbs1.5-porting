#!/usr/bin/env python3
"""Integrate Ver. 1.5 unlock-state semantics into the expanded GBA build.

Runtime QA is intentionally excluded from this builder.  It only applies
checked ARM hooks and emits a reproducibility manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "FA0A48EC933AB9A2BD8960A61D0BE6F07CD15E2FC0B2037917595BDE154DACED"
GBA_BASE = 0x08000000

CLEAR_EVAL_CALL_SITE = 0x08B364
RETAIL_CLEAR_EVAL_TARGET = 0x08B55C
CLEAR_EVAL_TARGET = 0x5B1000

UNLOCK_COMMIT_SITE = 0x0BF684
UNLOCK_COMMIT_RETURN = 0x0BF698
UNLOCK_COMMIT_TARGET = 0x5B1100

BATTLE_STATE = 0x03002310
SHOOT_COMPLETE_MASK = 0x8000  # free bit 15 in the 16-bit clear/progress field
HARD_DIFFICULTY_NIBBLE = 0x20  # GBA's highest setting represents 1.5 Extreme
EXTRA_GUILMON_SCORE = 600


def arm_branch(source: int, target: int, *, link: bool = False,
               condition: int = 0xE) -> int:
    source += GBA_BASE if source < GBA_BASE else 0
    target += GBA_BASE if target < GBA_BASE else 0
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    return ((condition << 28) | 0x0A000000 | (int(link) << 24)
            | ((delta >> 2) & 0x00FFFFFF))


def build_clear_eval_hook() -> bytes:
    target = GBA_BASE + CLEAR_EVAL_TARGET
    words = [
        0xE92D403F,  # push {r0-r5, lr}
        0,           # ldr r5, [pc, #battle_state]
        0xE1D511BA,  # ldrh r1, [r5, #0x1a] (run flags)
        0xE3110001,  # tst r1, #1 (continued/failed-run flag)
        0,           # bne done
        0xE5D52020,  # ldrb r2, [r5, #0x20] (difficulty packed nibble)
        0xE20220F0,  # and r2, r2, #0xf0
        0xE1D532B2,  # ldrh r3, [r5, #0x22] (D-Spirit score)
        0xE1D541BC,  # ldrh r4, [r5, #0x1c] (clear/progress flags)
        0xE5D50018,  # ldrb r0, [r5, #0x18] (pending unlocks)
        0xE3140902,  # tst r4, #0x8000 (Digimon Shoot completed)
        0x13800010,  # orrne r0, r0, #0x10 (Impmon candidate)
        0xE3520020,  # cmp r2, #0x20 (highest GBA setting / 1.5 Extreme)
        0,           # bne skip_extra
        0,           # ldr r4, [pc, #score_literal]
        0xE1530004,  # cmp r3, r4
        0x23800020,  # orrhs r0, r0, #0x20 (Extra Guilmon candidate)
        0xE5D51019,  # ldrb r1, [r5, #0x19] (permanent unlocks)
        0xE1E01001,  # mvn r1, r1
        0xE0000001,  # and r0, r0, r1
        0xE5D51018,  # ldrb r1, [r5, #0x18]
        0xE1811000,  # orr r1, r1, r0
        0xE5C51018,  # strb r1, [r5, #0x18]
        0xE8BD403F,  # pop {r0-r5, lr}
        0xE12FFF1E,  # bx lr
        BATTLE_STATE,
        EXTRA_GUILMON_SCORE,
    ]
    done_index = 23
    skip_extra_index = 17
    battle_literal_index = 25
    score_literal_index = 26
    words[1] = 0xE59F5000 | (
        (battle_literal_index * 4 - (1 * 4 + 8)) & 0xFFF
    )
    words[4] = arm_branch(
        target + 4 * 4, target + done_index * 4, condition=0x1
    )
    words[13] = arm_branch(
        target + 13 * 4, target + skip_extra_index * 4, condition=0x1
    )
    words[14] = 0xE59F4000 | (
        (score_literal_index * 4 - (14 * 4 + 8)) & 0xFFF
    )
    return struct.pack(f"<{len(words)}I", *words)


def build_unlock_commit_hook() -> bytes:
    target = GBA_BASE + UNLOCK_COMMIT_TARGET
    words = [
        0xE5D18019,  # ldrb r8, [r1, #0x19]
        0xE3100020,  # tst r0, #0x20 (Extra Guilmon pending)
        0x13800A02,  # orrne r0, r0, #0x2000 (commit as permanent bit 5)
        0xE1B08408,  # lsls r8, r8, #8 (displaced retail sequence)
        0xE1988000,  # orrs r8, r8, r0
        0xE1B08428,  # lsrs r8, r8, #8
        0xE5C18019,  # strb r8, [r1, #0x19]
        arm_branch(target + 7 * 4, GBA_BASE + UNLOCK_COMMIT_RETURN),
    ]
    return struct.pack(f"<{len(words)}I", *words)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    digest = hashlib.sha256(source).hexdigest().upper()
    if digest != INPUT_SHA256:
        raise SystemExit("refusing unknown stage-integrated input")
    expected_call = arm_branch(
        CLEAR_EVAL_CALL_SITE, RETAIL_CLEAR_EVAL_TARGET, link=True
    )
    if struct.unpack_from("<I", source, CLEAR_EVAL_CALL_SITE)[0] != expected_call:
        raise SystemExit("clear-evaluation call-site check failed")
    if source[UNLOCK_COMMIT_SITE:UNLOCK_COMMIT_SITE + 20] != bytes.fromhex(
        "1980D1E50884B0E1008098E12884B0E11980C1E5"
    ):
        raise SystemExit("unlock-commit hook-site check failed")

    patched = bytearray(source)
    placements = []
    for target, blob, label in (
        (CLEAR_EVAL_TARGET, build_clear_eval_hook(), "Ver. 1.5 clear evaluator"),
        (UNLOCK_COMMIT_TARGET, build_unlock_commit_hook(), "extended unlock commit"),
    ):
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is not blank expansion space")
        patched[target:target + len(blob)] = blob
        placements.append({"label": label, "target": target, "bytes": len(blob)})

    struct.pack_into(
        "<I", patched, CLEAR_EVAL_CALL_SITE,
        arm_branch(CLEAR_EVAL_CALL_SITE, CLEAR_EVAL_TARGET, link=True),
    )
    struct.pack_into(
        "<I", patched, UNLOCK_COMMIT_SITE,
        arm_branch(UNLOCK_COMMIT_SITE, UNLOCK_COMMIT_TARGET),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-progression-integration-build",
        "claim_scope": (
            "static Ver. 1.5 Impmon/Extra Guilmon pending-and-permanent unlock "
            "semantics; Digimon Shoot completion producer and final QA deferred"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": hashlib.sha256(patched).hexdigest().upper(),
        "output_bytes": len(patched),
        "placements": placements,
        "clear_eval_call_site": CLEAR_EVAL_CALL_SITE,
        "unlock_commit_site": UNLOCK_COMMIT_SITE,
        "state": {
            "pending_unlock_byte": "0x03002328",
            "permanent_unlock_byte": "0x03002329",
            "clear_progress_halfword": "0x0300232C",
            "digimon_shoot_complete_mask": f"0x{SHOOT_COMPLETE_MASK:04X}",
            "difficulty_byte": "0x03002330",
            "extra_guilmon_score": EXTRA_GUILMON_SCORE,
        },
        "policy": {
            "Impmon ID 11": "Digimon Shoot completion flag, then no-continue game clear",
            "Extra Guilmon ID 12": (
                "highest GBA difficulty (the port's 1.5 Extreme equivalent), "
                "600+ D-Spirit, no-continue game clear"
            ),
        },
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
