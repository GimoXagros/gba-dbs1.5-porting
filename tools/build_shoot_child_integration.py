#!/usr/bin/env python3
"""Install the bounded Ver. 1.5 Shoot generator and child callback chain."""

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


INPUT_SHA256 = "4028AB75706FDE162E7F247B2AD52CAB20E9B30E487C306B70EE1E1F38E2F45C"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
GBA_BASE = 0x08000000

GENERATOR = 0x5B9400
CALLBACK_INITIAL = 0x5B9800
CALLBACK_HOMING = 0x5B9C00
CALLBACK_COMPLETE = 0x5BA000
OWNERSHIP_START = 0x5B9328
OWNERSHIP_END = 0x5BA400

P1_RESOURCE = 0x085B9000
P0_RESOURCE = 0x085B9200
P2_RESOURCE = 0x085B9300
OBJECT_ALLOCATOR = 0x08352374
PRESENTATION_CONSTRUCTOR = 0x080127E4
PRESENTATION_EVENT = 0x08012874
PRESENTATION_UPDATE = 0x08012A84
ANGLE = 0x08012560
TRIG_X = 0x0801233C
TRIG_Y = 0x08012348
OBJECT_RELEASE = 0x083524C4
SOUND_REQUEST = 0x080D15C0

OBJECT_HANDLE = 0x03004D54
SPAWN_PARENT = 0x03004D58
SPAWN_TARGET = 0x03004D5C
SPAWN_X = 0x03004D60
SPAWN_Y = 0x03004D62
SHOOT_FLAGS = 0x0300450A

WSC_RANGES = {
    "generator_9229": (0x749B29, 0x749C3B, "51F802FADB6AFD59D77DE51189CBA0124D814BA531A1E93C7EFEAD8B59622E69"),
    "callback_94C1": (0x749DC1, 0x749E70, "CDB4D863FB669D8BB11564531CF3592F4F31688D63DF0CB1DC451CA7119F5572"),
    "callback_9570": (0x749E70, 0x749F17, "AE839141C3B6A7F2BFABA82E8AE1E27C6BD091D8C768B67EAB965F043024FA2D"),
    "callback_9617": (0x749F17, 0x749F6A, "F5D557B0C3D16B2ECB2DA97948E81C6568EEED89E47F69F8F91392B16F87A65E"),
}
GBA_ORACLE_RANGES = {
    "commercial_generator": (0x37273C, 0x372920, "7E087397E772C0293D458FBFEAB13FF3BC04DFD42D90F44AE453738C8CEF4B7C"),
    "commercial_callback_initial": (0x372110, 0x3721FC, "F72DFA2038E330EB0A8640F130B126C2CDB495399CDFAAE9530DE3BEE61BD460"),
    "commercial_callback_homing": (0x3721FC, 0x372320, "12C951CD935FDC2DFAC99F3A67E52B0010A45644E8B21A3433F61BC43A39938A"),
    "commercial_callback_complete": (0x372320, 0x3723D8, "B5E810B434A99459C8B0BDB5E64F69282B577755CBBF00A1EDE3BF85A82B6398"),
    "native_sound_request": (0x0D15C0, 0x0D15F0, "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
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


def build_generator() -> bytes:
    return assemble_arm(f"""
        push {{r0-r7, lr}}
        mov r6, r4
        ldrsh r0, [r6, #0x34]
        ldrsh r3, [r6, #0x36]
        ldr r8, spawn_x
        strh r0, [r8]
        ldr r8, spawn_y
        strh r3, [r8]
        ldr r7, [r6, #0x18]
        ldr r8, spawn_parent
        str r6, [r8]
        ldr r8, spawn_target
        str r7, [r8]

        ldr r8, object_handle
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        push {{r8}}
        mov r0, #0x0B
        orr r0, r0, #0x4100
        push {{r0}}
        mov r8, #1
        push {{r8}}
        mov r8, #2
        push {{r8}}
        bl 0x{OBJECT_ALLOCATOR:08X}
        add sp, sp, #28

        ldr r8, object_handle
        ldr r4, [r8]
        mov r9, #1
        strb r9, [r4, #0x10]
        str r6, [r4, #0x14]
        str r7, [r4, #0x18]
        ldrsh r0, [r6, #0x34]
        ldrsh r3, [r6, #0x36]
        add r3, r3, #0x200
        strh r0, [r4, #0x34]
        strh r3, [r4, #0x36]
        mov r9, #8
        strh r9, [r4, #0x52]
        mov r9, #0x10
        strh r9, [r4, #0x54]

        add r5, r4, #0xAC
        push {{r5}}
        mov r8, #0
        push {{r8}}
        ldr r8, p2_resource
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, p0_resource
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, p1_resource
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        mov r8, #0x4000
        push {{r8}}
        mov r8, #0x1800
        push {{r8}}
        mov r8, #0xD1
        orr r8, r8, #0x100
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_CONSTRUCTOR:08X}
        add sp, sp, #60

        ldrh r8, [r5, #8]
        orr r8, r8, #0x2000
        strh r8, [r5, #8]
        str r4, [r6, #0x20]
        mov r9, #0
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        mov r9, #1
        strh r9, [r4, #0x64]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        mov r8, #0x4C
        mov r9, #1
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, callback_initial
        str r8, [r4]
        pop {{r0-r7, lr}}
        bx lr
        .align 2
    object_handle: .word 0x{OBJECT_HANDLE:08X}
    spawn_parent: .word 0x{SPAWN_PARENT:08X}
    spawn_target: .word 0x{SPAWN_TARGET:08X}
    spawn_x: .word 0x{SPAWN_X:08X}
    spawn_y: .word 0x{SPAWN_Y:08X}
    p1_resource: .word 0x{P1_RESOURCE:08X}
    p0_resource: .word 0x{P0_RESOURCE:08X}
    p2_resource: .word 0x{P2_RESOURCE:08X}
    callback_initial: .word 0x{GBA_BASE + CALLBACK_INITIAL:08X}
    """, GENERATOR)


def build_callback_initial() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        mov r9, #0
        strh r9, [r4, #0x56]
        strh r9, [r4, #0x58]
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        beq presentation_wait

        ldr r1, [r4, #0x18]
        ldrsh r0, [r4, #0x34]
        ldrsh r8, [r1, #0x34]
        sub r0, r0, r8
        ldrsh r3, [r4, #0x36]
        ldrsh r8, [r1, #0x36]
        sub r3, r3, r8
        push {{r3}}
        push {{r0}}
        bl 0x{ANGLE:08X}
        add sp, sp, #8
        and r0, r0, #0xFF
        cmp r0, #0x60
        movgt r0, #0x60
        cmp r0, #0x20
        movlt r0, #0x20
        mov r3, r0
        push {{r3}}
        bl 0x{TRIG_X:08X}
        add sp, sp, #4
        asr r0, r0, #2
        strh r0, [r4, #0x42]
        push {{r3}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        asr r0, r0, #2
        strh r0, [r4, #0x44]
        and r3, r3, #0xFF
        add r3, r3, #0x40
        strh r3, [r4, #0xA0]
        sub r3, r3, #0x80
        strh r3, [r4, #0xA2]
        mov r9, #0x14
        strh r9, [r4, #0x94]
        mov r9, #3
        strh r9, [r4, #0xA0]
        mov r9, #0x4B
        strh r9, [r4, #0x96]
        ldrh r8, [r4, #4]
        orr r8, r8, #0x8000
        strh r8, [r4, #4]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r8, callback_homing
        str r8, [r4]
        pop {{lr}}
        bx lr

    presentation_wait:
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldr r1, [r4, #0x14]
        ldrh r0, [r1, #0xB4]
        and r0, r0, #0x4000
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        orr r8, r8, r0
        strh r8, [r5, #8]
        ldrsh r0, [r1, #0x34]
        strh r0, [r4, #0x34]
        ldrsh r0, [r1, #0x36]
        sub r0, r0, #0x100
        strh r0, [r4, #0x36]
        pop {{lr}}
        bx lr
        .align 2
    callback_homing: .word 0x{GBA_BASE + CALLBACK_HOMING:08X}
    """, CALLBACK_INITIAL)


def build_callback_homing() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r4, #0x58]
        tst r8, #3
        bne transition
        ldrh r8, [r4, #0x56]
        tst r8, #1
        bne transition
        ldrsh r8, [r4, #0x36]
        cmn r8, #0x200
        bmi transition
        ldrsh r8, [r4, #0xA0]
        cmp r8, #6
        bge update

        ldr r1, [r4, #0x18]
        ldrsh r0, [r1, #0x34]
        ldrsh r3, [r1, #0x36]
        sub r3, r3, #0x100
        ldrsh r8, [r4, #0x34]
        sub r0, r0, r8
        ldrsh r8, [r4, #0x36]
        sub r3, r3, r8
        push {{r3}}
        push {{r0}}
        bl 0x{ANGLE:08X}
        add sp, sp, #8
        mov r3, r0
        ldrsh r8, [r4, #0x94]
        sub r8, r8, #1
        strh r8, [r4, #0x94]
        cmp r8, #0
        bne timer_done
        mov r9, #0x14
        strh r9, [r4, #0x94]
        ldrsh r8, [r4, #0xA0]
        add r8, r8, #1
        strh r8, [r4, #0xA0]
    timer_done:
        ldrsh r2, [r4, #0xA0]
        push {{r3}}
        bl 0x{TRIG_X:08X}
        add sp, sp, #4
        asr r1, r0, r2
        ldrsh r8, [r4, #0x42]
        add r8, r8, r1
        strh r8, [r4, #0x42]
        push {{r3}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        asr r1, r0, r2
        ldrsh r8, [r4, #0x44]
        add r8, r8, r1
        strh r8, [r4, #0x44]
    update:
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        pop {{lr}}
        bx lr

    transition:
        mov r9, #0
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #2
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r8, callback_complete
        str r8, [r4]
        pop {{lr}}
        bx lr
        .align 2
    callback_complete: .word 0x{GBA_BASE + CALLBACK_COMPLETE:08X}
    """, CALLBACK_HOMING)


def build_callback_complete() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        bne release
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        pop {{lr}}
        bx lr
    release:
        push {{r4}}
        mov r8, #0
        push {{r8}}
        bl 0x{OBJECT_RELEASE:08X}
        add sp, sp, #8
        ldr r8, shoot_flags
        ldrh r9, [r8]
        bic r9, r9, #0x40
        strh r9, [r8]
        pop {{lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    """, CALLBACK_COMPLETE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    gba = args.gba.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(source, INPUT_SHA256, "v36 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    for label, (start, end, digest) in WSC_RANGES.items():
        require_hash(wsc15[start:end], digest, label)
    for label, (start, end, digest) in GBA_ORACLE_RANGES.items():
        require_hash(gba[start:end], digest, label)

    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (
        OWNERSHIP_END - OWNERSHIP_START
    ):
        raise SystemExit("Shoot child code ownership window is not blank")
    refs_before = aligned_pointer_refs(source, GENERATOR, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches Shoot child code window: {refs_before}")

    placements = [
        (GENERATOR, build_generator(), "generator_9229"),
        (CALLBACK_INITIAL, build_callback_initial(), "callback_94C1"),
        (CALLBACK_HOMING, build_callback_homing(), "callback_9570"),
        (CALLBACK_COMPLETE, build_callback_complete(), "callback_9617"),
    ]
    ordered = sorted((start, start + len(blob), label) for start, blob, label in placements)
    for previous, current in zip(ordered, ordered[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"Shoot child code placements overlap: {previous[2]} / {current[2]}")
    if ordered[-1][1] > OWNERSHIP_END:
        raise SystemExit("Shoot child code exceeds its ownership window")

    patched = bytearray(source)
    allowed = set()
    manifest_placements = []
    for start, blob, label in placements:
        end = start + len(blob)
        before = bytes(patched[start:end])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} Expected Write input is not all FF")
        patched[start:end] = blob
        allowed.update(range(start, end))
        manifest_placements.append({
            "label": label,
            "target": start,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(source, patched, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("Shoot child integration contains an unexplained diff")

    output = bytes(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-child-code-integration-build",
        "claim_scope": (
            "resident generator 9229 and internally connected 94C1/9570/9617 "
            "child callbacks using the commercial GBA object ABI, including the "
            "proved WSC A7 to GBA 0x4C sound request; parent 912A connection and "
            "runtime reachability excluded"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "source_ranges": WSC_RANGES,
        "commercial_oracle_ranges": GBA_ORACLE_RANGES,
        "ownership": {
            "start": OWNERSHIP_START,
            "end": OWNERSHIP_END,
            "preexisting_aligned_pointer_refs": refs_before,
        },
        "expected_writes": manifest_placements,
        "external_entry_connected": False,
        "audio_request": {
            "target": SOUND_REQUEST,
            "wsc_sound_id": 0xA7,
            "gba_sound_id": 0x4C,
            "request_type": 1,
            "third_argument": 0,
            "runtime_audibility_verified": False,
        },
        "known_exclusion": "external 9083/912A parent/controller connection",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-child] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
