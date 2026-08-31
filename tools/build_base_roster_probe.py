#!/usr/bin/env python3
"""Build the expanded Ver. 1.5 playable-character integration layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
GBA_BASE = 0x08000000
EXPANDED_BYTES = 0x800000
# The engine's canonical 0x20-byte record begins eight bytes before the
# palette/P4-facing pointer used by a few consumers.  Starting at 0x0D3FC0
# drops fields 0 and 1 from every relocated record and makes the opening demo
# dereference 0xFFFFFFFF through the consumer at ROM offset 0x83CF8.
RECORD_TABLE = 0x0D3FB8
RECORD_BYTES = 0x20
RESOURCE_ENTRY_COUNT = 15
EVOLUTION_RECORD_TABLE = RECORD_TABLE + 12 * RECORD_BYTES
EXPANDED_BASE_TABLE = 0x4A80F8
EXPANDED_EVOLUTION_TABLE = EXPANDED_BASE_TABLE + RESOURCE_ENTRY_COUNT * RECORD_BYTES
HOOK_SITE = 0x08170C
HOOK_TARGET = 0x5B0000
HOOK_RETURN = 0x081710
EXPECTED_HOOK_WORD = 0xE8BD0010
SELECTION_HOOK_SITE = 0x08329C
SELECTION_TABLE_TARGET = 0x4A5BC0
SELECTION_HOOK_TARGET = 0x4A5C40
EXPECTED_SELECTION_HOOK_WORD = 0xE92D4000
VS_TABLE_POINTER_SITES = (0x088244, 0x0B64B4, 0x0B64D8)
EXPECTED_VS_TABLE_POINTER = 0x0809B920
PHYSICS_TABLE_POINTER_SITE = 0x3532FC
EXPECTED_PHYSICS_TABLE_POINTER = 0x083534D8
VS_EVENT_TABLE_POINTER_SITE = 0x0B77EC
EXPECTED_VS_EVENT_TABLE_POINTER = 0x080B77F4
BOSS_CHARACTER_COMPARE_PATCHES = {
    # Character IDs are sourced either from the loader argument or from the
    # per-character resource record at object->0x18 + 0x11.  Do not include
    # unrelated immediate 12 values used for frame counters/object kinds.
    0x3416F8: (0xE358000C, 0xE358000F),
    0x3417E8: (0xE358000C, 0xE358000F),
    0x353220: (0xE358000C, 0xE358000F),
    0x353324: (0xE359000C, 0xE359000F),
    0x35473C: (0xE358000C, 0xE358000F),
    0x36CB30: (0xE358000C, 0xE358000F),
}
FINAL_OPPONENT_TABLE_SITE = 0x08B616
EXPECTED_FINAL_OPPONENT_ID = 0x0C
RELOCATED_FINAL_OPPONENT_ID = 0x0F
RESOURCE_POINTER_RELOCATIONS = {
    GBA_BASE + RECORD_TABLE: (
        GBA_BASE + EXPANDED_BASE_TABLE,
        (0x1F4A0, 0x1F518, 0x82428, 0x8328C, 0x83CF8, 0x840E8,
         0x8440C, 0x85CE8, 0x867B8, 0xB9620, 0xBBAC4, 0xBBB38,
         0xBBB50, 0xBD528, 0xBFAB8, 0xCC234, 0xCC70C, 0x33F1A4,
         0x33F1A8, 0x33F1B4, 0x33F1B8, 0x33F1C4, 0x33F1C8,
         0x3534BC, 0x3534C0, 0x3534C4),
    ),
    GBA_BASE + RECORD_TABLE + 8: (
        GBA_BASE + EXPANDED_BASE_TABLE + 8,
        (0x3534CC,),
    ),
    GBA_BASE + RECORD_TABLE + 16: (
        GBA_BASE + EXPANDED_BASE_TABLE + 16,
        (0x3534C8,),
    ),
    GBA_BASE + EVOLUTION_RECORD_TABLE: (
        GBA_BASE + EXPANDED_EVOLUTION_TABLE,
        (0xBFABC, 0x3534D4, 0x377D18),
    ),
    GBA_BASE + EVOLUTION_RECORD_TABLE + 8: (
        GBA_BASE + EXPANDED_EVOLUTION_TABLE + 8,
        (0x3534D0,),
    ),
}


ASSETS = (
    ("id12-base.bin", "id12-base.json"),
    ("id13-base.bin", "id13-base.json"),
    ("id14-base.bin", "id14-base.json"),
    ("character-palettes.bin", "character-palettes.json"),
    ("new-base-p4.bin", "new-base-p4.json"),
    ("new-base-p1.bin", "new-base-p1.json"),
    ("selection-portraits.bin", "selection-portraits.json"),
    ("vs-presentation.bin", "vs-presentation.json"),
    ("character-physics.bin", "character-physics.json"),
    ("vs-character-events.bin", "vs-character-events.json"),
    ("evolution-p0.bin", "evolution-p0.json"),
    ("evolution-p1.bin", "evolution-p1.json"),
    ("evolution-p4.bin", "evolution-p4.json"),
)


def arm_branch(source: int, target: int, condition: int = 0xE) -> int:
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    return (condition << 28) | 0x0A000000 | ((delta >> 2) & 0x00FFFFFF)


def arm_link_branch(source: int, target: int) -> int:
    return arm_branch(source, target) | 0x01000000


def build_hook() -> bytes:
    # Retail has already built IDs 0..6 plus whichever of IDs 7..11 its
    # original save flags expose. Rebuild the list in the exact Ver. 1.5
    # order: 0..10, 13, 14, followed by gated IDs 11 and 12. r4 is the list
    # end, r2 the retail item count, and r5 the persistent-state mirror.
    words = [
        0xE044C082,  # sub ip, r4, r2, lsl #1 (list base)
        0xE1A0400C,  # mov r4, ip
        0xE3A00000,  # mov r0, #0
        0xE3A0200B,  # mov r2, #11
        0xE0C400B2,  # loop: strh r0, [r4], #2
        0xE2800001,  # add r0, r0, #1
        0xE2522001,  # subs r2, r2, #1
        0,           # bgt loop (fixed below)
        0xE3A0000D,  # mov r0, #13
        0xE0C400B2,  # strh r0, [r4], #2
        0xE3A0000E,  # mov r0, #14
        0xE0C400B2,  # strh r0, [r4], #2
        0xE3A0200D,  # mov r2, #13
        0xE5D50019,  # ldrb r0, [r5, #0x19] (persistent unlock byte)
        0xE3100010,  # tst r0, #0x10 (Impmon)
        0x13A0100B,  # movne r1, #11
        0x10C410B2,  # strhne r1, [r4], #2
        0x12822001,  # addne r2, r2, #1
        0xE3100020,  # tst r0, #0x20 (Extra Guilmon)
        0x13A0100C,  # movne r1, #12
        0x10C410B2,  # strhne r1, [r4], #2
        0x12822001,  # addne r2, r2, #1
    ]
    words[7] = arm_branch(HOOK_TARGET + 7 * 4, HOOK_TARGET + 4 * 4, condition=0xC)
    displaced_address = HOOK_TARGET + len(words) * 4
    words.extend([
        0xE8BD0010,  # pop {r4} (displaced retail instruction)
        arm_branch(displaced_address + 4, HOOK_RETURN),
    ])
    return struct.pack(f"<{len(words)}I", *words)


def build_selection_hook() -> bytes:
    words = [
        0xE92D4000,  # push {lr}
        0xE59F8038,  # ldr r8, [pc, #0x38] (pair table)
        0xE59F5038,  # ldr r5, [pc, #0x38] (palette destination)
        0xE7984181,  # ldr r4, [r8, r1, lsl #3]
        0xE3A02008,  # mov r2, #8
        arm_link_branch(SELECTION_HOOK_TARGET + 0x14, 0x000B84),
        0xE59F8028,  # ldr r8, [pc, #0x28] (pair table + 4)
        0xE59F5028,  # ldr r5, [pc, #0x28] (tile destination)
        0xE7984181,  # ldr r4, [r8, r1, lsl #3]
        0xE3A02C06,  # mov r2, #0x600
        arm_link_branch(SELECTION_HOOK_TARGET + 0x28, 0x000B84),
        0xE59F401C,  # ldr r4, [pc, #0x1c] (selection state)
        0xE2811001,  # add r1, r1, #1
        0xE1C411BE,  # strh r1, [r4, #0x1e]
        0xE8BD4000,  # pop {lr}
        0xE12FFF1E,  # bx lr
        SELECTION_TABLE_TARGET + GBA_BASE,
        0x05000020,
        SELECTION_TABLE_TARGET + GBA_BASE + 4,
        0x06005780,
        0x03004710,
    ]
    return struct.pack(f"<{len(words)}I", *words)


def verified_asset(asset_dir: pathlib.Path, binary_name: str,
                   manifest_name: str) -> tuple[bytes, dict[str, object]]:
    blob = (asset_dir / binary_name).read_bytes()
    manifest = json.loads((asset_dir / manifest_name).read_text(encoding="utf-8"))
    expected = manifest.get("blob_sha256", manifest.get("asset_sha256"))
    if hashlib.sha256(blob).hexdigest().upper() != str(expected).upper():
        raise ValueError(f"{binary_name} does not match its manifest")
    target = int(manifest.get("target_base", manifest.get("target_header_offset")))
    return blob, {"name": binary_name, "target": target, "bytes": len(blob)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.gba.read_bytes()
    if hashlib.sha256(source).hexdigest().upper() != GBA_SHA256:
        raise SystemExit("refusing unknown GBA input")
    if struct.unpack_from("<I", source, HOOK_SITE)[0] != EXPECTED_HOOK_WORD:
        raise SystemExit("roster initialization hook-site check failed")
    if struct.unpack_from("<I", source, SELECTION_HOOK_SITE)[0] != EXPECTED_SELECTION_HOOK_WORD:
        raise SystemExit("selection portrait hook-site check failed")
    for site in VS_TABLE_POINTER_SITES:
        if struct.unpack_from("<I", source, site)[0] != EXPECTED_VS_TABLE_POINTER:
            raise SystemExit(f"VS descriptor pointer check failed at 0x{site:X}")
    if struct.unpack_from("<I", source, PHYSICS_TABLE_POINTER_SITE)[0] != EXPECTED_PHYSICS_TABLE_POINTER:
        raise SystemExit("character-physics pointer check failed")
    if struct.unpack_from("<I", source, VS_EVENT_TABLE_POINTER_SITE)[0] != EXPECTED_VS_EVENT_TABLE_POINTER:
        raise SystemExit("VS character-event pointer check failed")
    for site, (expected, _) in BOSS_CHARACTER_COMPARE_PATCHES.items():
        if struct.unpack_from("<I", source, site)[0] != expected:
            raise SystemExit(f"boss-sentinel character check failed at 0x{site:X}")
    if source[FINAL_OPPONENT_TABLE_SITE] != EXPECTED_FINAL_OPPONENT_ID:
        raise SystemExit("final-opponent table check failed")
    for expected, (_, sites) in RESOURCE_POINTER_RELOCATIONS.items():
        actual_sites = tuple(
            index for index in range(len(source) - 3)
            if struct.unpack_from("<I", source, index)[0] == expected
        )
        if actual_sites != sites:
            raise SystemExit(
                f"resource-pointer occurrence check failed for 0x{expected:08X}: "
                f"{actual_sites}"
            )

    patched = bytearray(source)
    patched.extend(bytes([0xFF]) * (EXPANDED_BYTES - len(patched)))
    # Retail ID 12 is a non-playable Millenniummon sentinel. Ver. 1.5 assigns
    # ID 12 to Extra Guilmon, so move the sentinel to the next unused ID 15.
    for site, (_, replacement) in BOSS_CHARACTER_COMPARE_PATCHES.items():
        struct.pack_into("<I", patched, site, replacement)
    patched[FINAL_OPPONENT_TABLE_SITE] = RELOCATED_FINAL_OPPONENT_ID
    placements = []
    for binary_name, manifest_name in ASSETS:
        blob, placement = verified_asset(args.asset_dir, binary_name, manifest_name)
        target = placement["target"]
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"asset target for {binary_name} is not blank expansion space")
        patched[target:target + len(blob)] = blob
        placements.append(placement)

    palettes = json.loads((args.asset_dir / "character-palettes.json").read_text())
    p4 = json.loads((args.asset_dir / "new-base-p4.json").read_text())
    p1 = json.loads((args.asset_dir / "new-base-p1.json").read_text())
    evolution_p0 = json.loads((args.asset_dir / "evolution-p0.json").read_text())
    evolution_p1 = json.loads((args.asset_dir / "evolution-p1.json").read_text())
    evolution_p4 = json.loads((args.asset_dir / "evolution-p4.json").read_text())
    selection = json.loads((args.asset_dir / "selection-portraits.json").read_text())
    animation = {
        12: json.loads((args.asset_dir / "id12-base.json").read_text()),
        13: json.loads((args.asset_dir / "id13-base.json").read_text()),
        14: json.loads((args.asset_dir / "id14-base.json").read_text()),
    }
    palette_targets = {
        (int(item["runtime_id"]), item["group"], int(item["wsc_field"])): int(item["target"])
        for item in palettes["references"]
    }
    p4_targets = {int(item["runtime_id"]): int(item["target"]) for item in p4["entries"]}
    p1_targets = {int(item["runtime_id"]): int(item["target"]) for item in p1["entries"]}
    evolution_p0_targets = {
        int(item["runtime_id"]): int(item["target_header_offset"])
        for item in evolution_p0["entries"]
    }
    evolution_p1_targets = {
        int(item["runtime_id"]): int(item["target"])
        for item in evolution_p1["entries"]
    }
    evolution_p4_targets = {
        int(item["runtime_id"]): int(item["target"])
        for item in evolution_p4["entries"]
    }

    base_table = bytearray(source[
        RECORD_TABLE:RECORD_TABLE + RESOURCE_ENTRY_COUNT * RECORD_BYTES
    ])
    evolution_table = bytearray(source[
        EVOLUTION_RECORD_TABLE:EVOLUTION_RECORD_TABLE + RESOURCE_ENTRY_COUNT * RECORD_BYTES
    ])
    record_writes = []

    def set_resource_field(table: bytearray, *, group: str, runtime_id: int,
                           record_id: int, field: int, target: int) -> None:
        local = record_id * RECORD_BYTES + field * 4
        old = struct.unpack_from("<I", table, local)[0]
        new = GBA_BASE + target
        struct.pack_into("<I", table, local, new)
        source_base = RECORD_TABLE if group == "base" else EVOLUTION_RECORD_TABLE
        target_base = EXPANDED_BASE_TABLE if group == "base" else EXPANDED_EVOLUTION_TABLE
        record_writes.append({
            "group": group,
            "runtime_id": runtime_id,
            "record_id": record_id,
            "field": field,
            "source_field": source_base + local,
            "target_field": target_base + local,
            "old": f"0x{old:08X}",
            "new": f"0x{new:08X}",
        })

    # The retail engine deliberately indexes palette/P4 by runtime ID, while
    # P0/P1 are read from the preceding record. Preserve that staggered ABI.
    for runtime_id in (12, 13, 14):
        set_resource_field(
            base_table, group="base", runtime_id=runtime_id,
            record_id=runtime_id, field=0,
            target=palette_targets[(runtime_id, "base", 2)],
        )
        set_resource_field(
            base_table, group="base", runtime_id=runtime_id,
            record_id=runtime_id, field=1,
            target=palette_targets[(runtime_id, "base", 3)],
        )
        set_resource_field(
            base_table, group="base", runtime_id=runtime_id,
            record_id=runtime_id, field=2, target=p4_targets[runtime_id],
        )
        set_resource_field(
            base_table, group="base", runtime_id=runtime_id,
            record_id=runtime_id - 1, field=6,
            target=int(animation[runtime_id]["target_header_offset"]),
        )
        set_resource_field(
            base_table, group="base", runtime_id=runtime_id,
            record_id=runtime_id - 1, field=7, target=p1_targets[runtime_id],
        )

    for runtime_id in (11, 12, 13, 14):
        set_resource_field(
            evolution_table, group="evolution", runtime_id=runtime_id,
            record_id=runtime_id, field=0,
            target=palette_targets[(runtime_id, "evolution", 2)],
        )
        set_resource_field(
            evolution_table, group="evolution", runtime_id=runtime_id,
            record_id=runtime_id, field=1,
            target=palette_targets[(runtime_id, "evolution", 3)],
        )
        set_resource_field(
            evolution_table, group="evolution", runtime_id=runtime_id,
            record_id=runtime_id, field=2, target=evolution_p4_targets[runtime_id],
        )
        set_resource_field(
            evolution_table, group="evolution", runtime_id=runtime_id,
            record_id=runtime_id - 1, field=6, target=evolution_p0_targets[runtime_id],
        )
        set_resource_field(
            evolution_table, group="evolution", runtime_id=runtime_id,
            record_id=runtime_id - 1, field=7, target=evolution_p1_targets[runtime_id],
        )

    if base_table[:11 * RECORD_BYTES] != source[
        RECORD_TABLE:RECORD_TABLE + 11 * RECORD_BYTES
    ]:
        raise AssertionError("unchanged base records 0..10 moved or changed")
    if evolution_table[:10 * RECORD_BYTES] != source[
        EVOLUTION_RECORD_TABLE:EVOLUTION_RECORD_TABLE + 10 * RECORD_BYTES
    ]:
        raise AssertionError("unchanged evolution records 0..9 moved or changed")

    for target, table, label in (
        (EXPANDED_BASE_TABLE, base_table, "expanded base resource table"),
        (EXPANDED_EVOLUTION_TABLE, evolution_table, "expanded evolution resource table"),
    ):
        if patched[target:target + len(table)] != bytes([0xFF]) * len(table):
            raise SystemExit(f"{label} target is not blank expansion space")
        patched[target:target + len(table)] = table
    for _, (replacement, sites) in RESOURCE_POINTER_RELOCATIONS.items():
        for site in sites:
            struct.pack_into("<I", patched, site, replacement)

    hook = build_hook()
    if patched[HOOK_TARGET:HOOK_TARGET + len(hook)] != bytes([0xFF]) * len(hook):
        raise SystemExit("roster hook target is not blank expansion space")
    patched[HOOK_TARGET:HOOK_TARGET + len(hook)] = hook
    struct.pack_into("<I", patched, HOOK_SITE, arm_branch(HOOK_SITE, HOOK_TARGET))

    selection_targets = {
        int(item["runtime_id"]): (int(item["palette_target"]), int(item["tile_target"]))
        for item in selection["entries"]
    }
    original_pairs = source[0x0832F0:0x0832F0 + 12 * 8]
    selection_table = bytearray(original_pairs)
    for runtime_id in (12, 13, 14):
        palette_target, tile_target = selection_targets[runtime_id]
        selection_table.extend(struct.pack(
            "<2I", GBA_BASE + palette_target, GBA_BASE + tile_target
        ))
    if len(selection_table) != 15 * 8:
        raise AssertionError("selection table size invariant failed")
    selection_hook = build_selection_hook()
    for target, data, label in (
        (SELECTION_TABLE_TARGET, selection_table, "selection table"),
        (SELECTION_HOOK_TARGET, selection_hook, "selection hook"),
    ):
        if patched[target:target + len(data)] != bytes([0xFF]) * len(data):
            raise SystemExit(f"{label} target is not blank expansion space")
        patched[target:target + len(data)] = data
    struct.pack_into(
        "<I", patched, SELECTION_HOOK_SITE,
        arm_branch(SELECTION_HOOK_SITE, SELECTION_HOOK_TARGET)
    )

    vs = json.loads((args.asset_dir / "vs-presentation.json").read_text())
    vs_descriptor_target = int(vs["descriptor_table_target"])
    for site in VS_TABLE_POINTER_SITES:
        struct.pack_into("<I", patched, site, GBA_BASE + vs_descriptor_target)

    physics = json.loads((args.asset_dir / "character-physics.json").read_text())
    physics_table_target = int(physics["pointer_table_target"])
    struct.pack_into(
        "<I", patched, PHYSICS_TABLE_POINTER_SITE,
        GBA_BASE + physics_table_target,
    )

    vs_events = json.loads((args.asset_dir / "vs-character-events.json").read_text())
    vs_event_table_target = int(vs_events["table_target"])
    struct.pack_into(
        "<I", patched, VS_EVENT_TABLE_POINTER_SITE,
        GBA_BASE + vs_event_table_target,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-base-roster-probe",
        "claim_scope": "playable IDs 12-14, evolutions, presentation, physics, and boss-sentinel relocation; final QA excluded",
        "source_sha256": GBA_SHA256,
        "output_sha256": hashlib.sha256(patched).hexdigest().upper(),
        "output_bytes": len(patched),
        "placements": placements,
        "record_writes": record_writes,
        "expanded_base_table": EXPANDED_BASE_TABLE,
        "expanded_evolution_table": EXPANDED_EVOLUTION_TABLE,
        "record_origin_correction": {
            "base_source": RECORD_TABLE,
            "evolution_source": EVOLUTION_RECORD_TABLE,
            "record_bytes": RECORD_BYTES,
            "opening_consumer_literal_site": 0x83CF8,
        },
        "resource_pointer_relocations": [
            {
                "old": f"0x{old:08X}",
                "new": f"0x{replacement:08X}",
                "sites": [f"0x{site:X}" for site in sites],
            }
            for old, (replacement, sites) in RESOURCE_POINTER_RELOCATIONS.items()
        ],
        "roster_policy": (
            "Ver. 1.5 clean roster IDs 0..10,13,14; IDs 11/12 gated by "
            "persistent unlock bits 4/5"
        ),
        "boss_sentinel": {
            "retail_id": 12,
            "relocated_id": 15,
            "character_compare_sites": [
                f"0x{site:X}" for site in BOSS_CHARACTER_COMPARE_PATCHES
            ],
            "final_opponent_table_site": FINAL_OPPONENT_TABLE_SITE,
        },
        "hook_site": HOOK_SITE,
        "hook_target": HOOK_TARGET,
        "hook_return": HOOK_RETURN,
        "selection_table_target": SELECTION_TABLE_TARGET,
        "selection_hook_site": SELECTION_HOOK_SITE,
        "selection_hook_target": SELECTION_HOOK_TARGET,
        "vs_descriptor_table_target": vs_descriptor_target,
        "vs_table_pointer_sites": list(VS_TABLE_POINTER_SITES),
        "physics_table_pointer_site": PHYSICS_TABLE_POINTER_SITE,
        "physics_table_target": physics_table_target,
        "vs_event_table_pointer_site": VS_EVENT_TABLE_POINTER_SITE,
        "vs_event_table_target": vs_event_table_target,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
