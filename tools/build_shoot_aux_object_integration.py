#!/usr/bin/env python3
"""Install the resident native constructor for Shoot's ES:071E object.

The component reuses the exact commercial GBA storage/callback lineage for
WSC 1.0 ES:06A2 and populates it with the converted Ver. 1.5 rules-object
resources.  It is deliberately resident but unconnected: the later stage-11
initializer layer will call it and replace the idle callback with the upper
state graph.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks  # type: ignore


INPUT_SHA256 = "000683972B02F1E58369517F6AC32B270854ED2BBA4FC292BCA54E9E9700FBEB"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OWNERSHIP_START = 0x5BC100
OWNERSHIP_END = 0x5BC700
AUX_CONSTRUCTOR = 0x5BC200
AUX_IDLE = 0x5BC600

OBJECT_ALLOCATOR = 0x08352374
PRESENTATION_CONSTRUCTOR = 0x080127E4
PRESENTATION_EVENT = 0x08012874
P2_LOADER = 0x080132EC
COMMERCIAL_CALLBACK = 0x083703EC
OBJECT_SLOT = 0x03004D3C
PLAYER_0_SLOT = 0x0300489C
PLAYER_1_SLOT = 0x030048A0

RULES_P1 = 0x085D029C
RULES_P0 = 0x085D1100
RULES_P2 = 0x085DB700
RULES_P1_SHA256 = "5DDE469264E235121F519CCB4DD11D21AB964708941E50F5D3CE93FB6667CE3D"
RULES_P0_SHA256 = "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91"
RULES_P2_SHA256 = "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD"
RULES_P1_BYTES = 1968
RULES_P0_BYTES = 41408
RULES_P2_BYTES = 40

ORACLE_RANGES = {
    "wsc10_lineage_initializer": (0x394971, 0x394A2D, "56F542F9B48BBA7E98AD26F1F2896BEEF2E903AE6163C97BDFBD5F9FAE55CE4B"),
    "wsc15_aux_population": (0x747BCF, 0x747C6E, "EA82958918CFFC3F39B4434EBA71DB038A6C13D962A98D8DB3D6B97DC1BC00EF"),
    "gba_lineage_initializer": (0x36FE6C, 0x370034, "76FFA816A5E89667A947B9A046D1B94FE2D1F1AD0F79901A312E7CA4DE3FBF67"),
    "gba_allocator": (0x352374, 0x35249C, "B77263F36C749526F81F7620FD64BB5B800D42A291759B786E84BCB888ECBDEA"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if expected and actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def assemble_arm(source: str, offset: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(
        source, GBA_BASE + offset
    )
    return bytes(encoded)


def aligned_pointer_refs(data: bytes, start: int, end: int) -> list[dict[str, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + start <= value < GBA_BASE + end:
            refs.append({"offset": offset, "value": value})
    return refs


def build_constructor() -> bytes:
    return assemble_arm(f"""
        push {{r0-r7, lr}}

        ldr r8, object_slot
        push {{r8}}
        mov r8, #0
        push {{r8}}
        ldr r8, commercial_callback
        push {{r8}}
        mov r8, #0
        push {{r8}}
        ldr r8, allocation_id
        push {{r8}}
        mov r8, #0
        push {{r8}}
        mov r8, #5
        push {{r8}}
        bl 0x{OBJECT_ALLOCATOR:08X}
        add sp, sp, #28

        ldr r8, object_slot
        ldr r4, [r8]
        mov r9, #0
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        strh r9, [r4, #0x46]
        strh r9, [r4, #0x48]
        mov r9, #0x20
        strh r9, [r4, #0x52]
        mov r9, #8
        strh r9, [r4, #0x54]

        ldrh r8, [r4, #4]
        bic r8, r8, #0xF
        orr r8, r8, #0x26
        bic r8, r8, #0x6000
        bic r8, r8, #0x40
        strh r8, [r4, #4]
        ldrh r8, [r4, #8]
        orr r8, r8, #4
        strh r8, [r4, #8]

        ldr r8, player_0_slot
        ldr r6, [r8]
        str r6, [r4, #0x28]
        ldr r8, player_1_slot
        ldr r7, [r8]
        str r7, [r4, #0x18]
        ldr r9, initial_position
        strh r9, [r4, #0x34]
        strh r9, [r4, #0x36]
        ldr r8, idle_callback
        str r8, [r4]

        add r5, r4, #0xAC
        push {{r5}}
        mov r8, #0
        push {{r8}}
        ldr r8, rules_p2
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, rules_p0
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, rules_p1
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        mov r8, #0x4000
        push {{r8}}
        mov r8, #0x1800
        push {{r8}}
        mov r8, #0x99
        push {{r8}}
        mov r8, #3
        push {{r8}}
        bl 0x{PRESENTATION_CONSTRUCTOR:08X}
        add sp, sp, #60

        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldrh r8, [r5, #8]
        orr r8, r8, #0x2400
        strh r8, [r5, #8]

        ldr r8, rules_p2
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        push {{r8}}
        mov r8, #3
        push {{r8}}
        bl 0x{P2_LOADER:08X}
        add sp, sp, #20

        str r4, [r6, #0x28]
        pop {{r0-r7, lr}}
        bx lr

        .align 2
    object_slot: .word 0x{OBJECT_SLOT:08X}
    commercial_callback: .word 0x{COMMERCIAL_CALLBACK:08X}
    allocation_id: .word 0x00000343
    player_0_slot: .word 0x{PLAYER_0_SLOT:08X}
    player_1_slot: .word 0x{PLAYER_1_SLOT:08X}
    initial_position: .word 0xFFFFFB00
    idle_callback: .word 0x{GBA_BASE + AUX_IDLE:08X}
    rules_p1: .word 0x{RULES_P1:08X}
    rules_p0: .word 0x{RULES_P0:08X}
    rules_p2: .word 0x{RULES_P2:08X}
    """, AUX_CONSTRUCTOR)


def build_idle() -> bytes:
    return assemble_arm("bx lr", AUX_IDLE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(source, INPUT_SHA256, "v44 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    for label, (start, end, digest) in ORACLE_RANGES.items():
        data = gba if label.startswith("gba") else (wsc10 if label.startswith("wsc10") else wsc15)
        require_hash(data[start:end], digest, label)

    for address, size, digest, label in (
        (RULES_P1, RULES_P1_BYTES, RULES_P1_SHA256, "rules P1"),
        (RULES_P0, RULES_P0_BYTES, RULES_P0_SHA256, "rules P0"),
        (RULES_P2, RULES_P2_BYTES, RULES_P2_SHA256, "rules P2"),
    ):
        start = address - GBA_BASE
        require_hash(source[start:start + size], digest, label)

    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (OWNERSHIP_END - OWNERSHIP_START):
        raise SystemExit("Shoot auxiliary-object ownership window is not blank")
    refs_before = aligned_pointer_refs(source, OWNERSHIP_START, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointers reach auxiliary-object window: {refs_before}")

    constructor = build_constructor()
    idle = build_idle()
    if AUX_CONSTRUCTOR + len(constructor) > AUX_IDLE:
        raise SystemExit("auxiliary constructor overlaps idle callback")
    if AUX_IDLE + len(idle) > OWNERSHIP_END:
        raise SystemExit("auxiliary idle callback exceeds ownership window")

    output = bytearray(source)
    placements = (
        (AUX_CONSTRUCTOR, constructor, "shoot_aux_constructor"),
        (AUX_IDLE, idle, "shoot_aux_idle_88F6"),
    )
    expected_writes = []
    for offset, blob, label in placements:
        before = bytes(output[offset:offset + len(blob)])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is no longer blank")
        output[offset:offset + len(blob)] = blob
        expected_writes.append({
            "label": label,
            "offset": offset,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })

    changed = [index for index, (before, after) in enumerate(zip(source, output)) if before != after]
    allowed = {
        index
        for offset, blob, _label in placements
        for index in range(offset, offset + len(blob))
        if source[index] != blob[index - offset]
    }
    if set(changed) != allowed:
        raise SystemExit("actual writes exceed declared auxiliary-object placements")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    manifest = {
        "schema": 1,
        "kind": "internal-shoot-auxiliary-object-integration-build",
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "ownership": {
            "start": OWNERSHIP_START,
            "end": OWNERSHIP_END,
            "preexisting_aligned_pointer_refs": refs_before,
        },
        "expected_writes": expected_writes,
        "actual_changed_bytes": len(changed),
        "native_lineage": {
            "wsc10_storage": "ES:06A2",
            "wsc15_storage": "ES:071E",
            "gba_pointer_slot": OBJECT_SLOT,
            "commercial_callback": COMMERCIAL_CALLBACK,
            "allocation_id": 0x343,
            "pool_selector": 5,
        },
        "installed_resources": {
            "p1": RULES_P1,
            "p0": RULES_P0,
            "p2": RULES_P2,
        },
        "component_entry": GBA_BASE + AUX_CONSTRUCTOR,
        "idle_callback": GBA_BASE + AUX_IDLE,
        "claim_scope": (
            "resident native auxiliary-object constructor and WSC 88F6 idle state only; "
            "no menu/stage-11 call reaches this component yet, upper callbacks and runtime "
            "remain unverified, and neither an emulator nor the supplied save was used"
        ),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-aux-object] PASS {args.output} {manifest['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
