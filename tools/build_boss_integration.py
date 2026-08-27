#!/usr/bin/env python3
"""Integrate the Ver. 1.5 ZeedMillenniummon second boss phase.

This builder performs static integration only.  The first zero-HP event for
the relocated final-boss sentinel restarts the retail boss object in place
with the Zeed graphics bundle when the run is Normal-or-harder and has not
used a continue.  The second zero-HP event clears the private phase bit and
falls through to the retail match-completion path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "946EFB9396650B8C24F4BDA236D513FFE08B61DFE3CBFD050B4BB0316A5F410E"
ZEE_BLOB_SHA256 = "57E7393D51163A537E705D0F05EE203357CFF9922B23C47FBDC95B32785EE8BC"
GBA_BASE = 0x08000000

ZEE_HEADER = 0x5B2000
HEADER_SELECTOR = 0x5B3600
DEATH_HOOK = 0x5B3700

BOSS_HP_SITE = 0x340344
BOSS_HEADER_SITE = 0x36FDE8
BOSS_ID_SITE = 0x36FD84
BOSS_SETUP = 0x36FCE4
RETAIL_BOSS_HEADER = 0x34E27C
BATTLE_STATE = 0x03002310
PHASE_MASK = 0x8000
CONTINUE_MASK = 0x0001
NORMAL_DIFFICULTY_NIBBLE = 0x10
BOSS_SENTINEL_ID = 15


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def arm_branch(source: int, target: int, *, link: bool = False,
               condition: int = 0xE) -> int:
    source += GBA_BASE if source < GBA_BASE else 0
    target += GBA_BASE if target < GBA_BASE else 0
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    return ((condition << 28) | 0x0A000000 | (int(link) << 24)
            | ((delta >> 2) & 0x00FFFFFF))


def pc_ldr(rd: int, instruction_index: int, literal_index: int,
           *, condition: int = 0xE) -> int:
    displacement = literal_index * 4 - (instruction_index * 4 + 8)
    if not 0 <= displacement <= 0xFFF:
        raise ValueError("literal is outside positive ARM PC-relative range")
    return (condition << 28) | 0x059F0000 | (rd << 12) | displacement


def build_header_selector() -> bytes:
    # Called in place of the retail `ldr r8, =boss_header`; only r0/r1 are
    # temporary and the caller does not carry either value across this site.
    words = [
        0,           # ldr r0, =battle_state
        0xE1D011BA,  # ldrh r1, [r0, #0x1a] (run flags/private phase)
        0xE3110902,  # tst r1, #0x8000
        0,           # ldrne r8, =Zeed header
        0,           # ldreq r8, =retail boss header
        0xE12FFF1E,  # bx lr
        BATTLE_STATE,
        GBA_BASE + RETAIL_BOSS_HEADER,
        GBA_BASE + ZEE_HEADER,
    ]
    words[0] = pc_ldr(0, 0, 6)
    words[3] = pc_ldr(8, 3, 8, condition=0x1)
    words[4] = pc_ldr(8, 4, 7, condition=0x0)
    return struct.pack(f"<{len(words)}I", *words)


def build_death_hook() -> bytes:
    target = GBA_BASE + DEATH_HOOK
    words = [
        0xE1D586B4,  # ldrh r8, [r5, #0x64] (displaced boss HP read)
        0xE3580000,  # cmp r8, #0
        0,           # bne return
        0xE5950018,  # ldr r0, [r5, #0x18]
        0xE5D00011,  # ldrb r0, [r0, #0x11]
        0xE350000F,  # cmp r0, #15 (relocated final-boss sentinel)
        0,           # bne return
        0,           # ldr r2, =battle_state
        0xE1D211BA,  # ldrh r1, [r2, #0x1a]
        0xE3110001,  # tst r1, #1 (continue used)
        0,           # bne return
        0xE5D23020,  # ldrb r3, [r2, #0x20] (difficulty nibble)
        0xE3530010,  # cmp r3, #0x10 (Normal or harder)
        0,           # blo return
        0xE3110902,  # tst r1, #0x8000 (already in Zeed phase)
        0,           # bne second_defeat
        0xE3811902,  # orr r1, r1, #0x8000
        0xE1C211BA,  # strh r1, [r2, #0x1a]
        0xE92D5EFF,  # push {r0-r7,r9-r12,lr}
        0,           # bl retail boss setup (selector now chooses Zeed)
        0xE8BD5EFF,  # pop {r0-r7,r9-r12,lr}
        0xE1D586B4,  # ldrh r8, [r5, #0x64]
        0xE12FFF1E,  # bx lr
        0xE3C11902,  # second_defeat: bic r1, r1, #0x8000
        0xE1C211BA,  # strh r1, [r2, #0x1a]
        0xE3A08000,  # mov r8, #0
        0xE12FFF1E,  # return: bx lr
        BATTLE_STATE,
    ]
    return_index = 26
    second_index = 23
    literal_index = 27
    for index in (2, 6, 10):
        words[index] = arm_branch(
            target + index * 4, target + return_index * 4, condition=0x1
        )
    words[13] = arm_branch(
        target + 13 * 4, target + return_index * 4, condition=0x3
    )
    words[15] = arm_branch(
        target + 15 * 4, target + second_index * 4, condition=0x1
    )
    words[7] = pc_ldr(2, 7, literal_index)
    words[19] = arm_branch(
        target + 19 * 4, GBA_BASE + BOSS_SETUP, link=True
    )
    return struct.pack(f"<{len(words)}I", *words)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    if sha256(source) != INPUT_SHA256:
        raise SystemExit("refusing unknown progression-integrated input")
    expected_words = {
        BOSS_HP_SITE: 0xE1D586B4,
        BOSS_HEADER_SITE: 0xE59F8294,
        BOSS_ID_SITE: 0xE3A0900C,
    }
    for site, expected in expected_words.items():
        if struct.unpack_from("<I", source, site)[0] != expected:
            raise SystemExit(f"boss hook-site check failed at 0x{site:X}")

    zeed = (args.asset_dir / "zeed-boss.bin").read_bytes()
    zeed_manifest = json.loads(
        (args.asset_dir / "zeed-boss.json").read_text(encoding="utf-8")
    )
    if sha256(zeed) != ZEE_BLOB_SHA256 or sha256(zeed) != zeed_manifest["blob_sha256"]:
        raise SystemExit("Zeed asset does not match its deterministic manifest")
    if int(zeed_manifest["target_header"]) != ZEE_HEADER:
        raise SystemExit("unexpected Zeed asset destination")
    if not zeed_manifest.get("layout_records_match_retail_gba", False):
        raise SystemExit("Zeed manifest lacks the layout ABI proof")

    patched = bytearray(source)
    placements = []
    for target, blob, label in (
        (ZEE_HEADER, zeed, "ZeedMillenniummon sprite bundle"),
        (HEADER_SELECTOR, build_header_selector(), "phase-aware boss header selector"),
        (DEATH_HOOK, build_death_hook(), "two-phase final-boss death hook"),
    ):
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is not blank expansion space")
        patched[target:target + len(blob)] = blob
        placements.append({"label": label, "target": target, "bytes": len(blob)})

    struct.pack_into(
        "<I", patched, BOSS_HP_SITE,
        arm_branch(BOSS_HP_SITE, DEATH_HOOK, link=True),
    )
    struct.pack_into(
        "<I", patched, BOSS_HEADER_SITE,
        arm_branch(BOSS_HEADER_SITE, HEADER_SELECTOR, link=True),
    )
    # Complete the earlier sentinel relocation: the dedicated boss setup was
    # not part of the generic ID-indexed loader and therefore needs its own
    # assignment patch from retail ID 12 to Ver. 1.5 ID 15.
    struct.pack_into("<I", patched, BOSS_ID_SITE, 0xE3A0900F)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-zeed-final-boss-integration-build",
        "claim_scope": (
            "static Zeed graphics and Normal-or-harder/no-continue two-phase "
            "final-boss route; integrated runtime QA deferred"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(patched),
        "output_bytes": len(patched),
        "placements": placements,
        "patch_sites": {
            "boss_hp_read": BOSS_HP_SITE,
            "boss_header_load": BOSS_HEADER_SITE,
            "boss_sentinel_assignment": BOSS_ID_SITE,
        },
        "route": {
            "eligibility": "Normal-or-harder and no continue",
            "first_defeat": "set private run bit 0x8000 and restart boss object with Zeed header",
            "second_defeat": "clear private run bit and resume retail match completion",
            "easy_or_continued": "retail Millenniummon-only completion",
        },
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
