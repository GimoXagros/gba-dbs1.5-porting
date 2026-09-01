#!/usr/bin/env python3
"""Install the bounded Ver. 1.5 Shoot parent callback chain."""

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


INPUT_SHA256 = "9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
GBA_BASE = 0x08000000

PARENT_INIT = 0x5BA800
PARENT_WAIT = 0x5BAC00
PARENT_SPAWN = 0x5BB000
PARENT_FINISH = 0x5BB400
PARENT_CLEANUP = 0x5BB800
PARENT_IDLE = 0x5BBC00
OWNERSHIP_START = 0x5BA800
OWNERSHIP_END = 0x5BC100

PRESENTATION_EVENT = 0x08012874
PRESENTATION_UPDATE = 0x08012A84
TRIG_Y = 0x08012348
CHILD_GENERATOR = 0x085B9400
SOUND_REQUEST = 0x080D15C0
SHOOT_FLAGS = 0x0300450A

WSC_RANGES = {
    "parent_9083": (0x749983, 0x7499F3, "E2F13CA4D554572C9E39C990ECCEBA95590AC62B38A44B69A49849EAA034C1EF"),
    "parent_90F3": (0x7499F3, 0x749A2A, "FC706E9021C458B6CB85B8C212AFA55AE28B72E27C54521E48D8BB892A692F5D"),
    "parent_912A": (0x749A2A, 0x749AAB, "71F987BAD4678D260548F6CBBD17E2B644AC8DFA5DF468108668AFAABE2FBC8B"),
    "parent_91AB": (0x749AAB, 0x749AEF, "6A8E13247F7BCD455F32BD0AABF52FFB5A8F614C08FBE31BFA3FF096617E41DD"),
    "parent_91EF": (0x749AEF, 0x749B29, "5389D0B3AA322CCCEDB896E497643CC12D707EB7A936EE12AAFF1D8FC191F374"),
    "idle_88F7": (0x7491F7, 0x7491F8, "383E5D7D58CAA41CE723CF16AF471B38F6EE9065C032D07FA6BEF1678CB72F1D"),
}
GBA_ORACLE_RANGES = {
    "commercial_child_family": (0x372110, 0x3723D8, "DF86BE1070A859F610416FEA03ECB5EABA1F1EA4E34118EE9DE35255E65793EC"),
    "native_presentation_event": (0x012874, 0x0128A4, "CC3B4B100C5BD7E06609D7C6D409C71481FB5362A86497C23D25A132770E0139"),
    "native_presentation_update": (0x012A84, 0x012AB4, "C3152EF1C9ADE9513E577FE5D5B690F562C2E817856D5F00DD5A76C4017E2EA7"),
    "native_trig_y": (0x012348, 0x012378, "366663ECC1E1BC7E342706C6AA04B8726861DC72FB06809763812337FB9FDF50"),
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


def build_parent_init() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        strh r8, [r4, #0x46]
        strh r8, [r4, #0x48]
        ldr r1, [r4, #0x18]
        ldrsh r0, [r1, #0x34]
        strh r0, [r4, #0x34]
        ldrsh r0, [r1, #0x36]
        sub r0, r0, #0x300
        strh r0, [r4, #0x36]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldrh r8, [r4, #4]
        bic r8, r8, #0x20
        strh r8, [r4, #4]
        ldr r1, [r4, #0x28]
        ldrh r8, [r1, #0xA0]
        orr r8, r8, #1
        strh r8, [r1, #0xA0]
        mov r8, #0x5B
        mov r9, #1
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, callback_wait
        str r8, [r4]
        pop {{lr}}
        bx lr
        .align 2
    callback_wait: .word 0x{GBA_BASE + PARENT_WAIT:08X}
    """, PARENT_INIT)


def build_parent_wait() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        bne complete
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        pop {{lr}}
        bx lr
    complete:
        mov r8, #0
        strh r8, [r4, #0x94]
        mov r8, #0x3C
        strh r8, [r4, #0x96]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r8, callback_spawn
        str r8, [r4]
        pop {{lr}}
        bx lr
        .align 2
    callback_spawn: .word 0x{GBA_BASE + PARENT_SPAWN:08X}
    """, PARENT_WAIT)


def build_parent_spawn() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        push {{r8}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        asr r0, r0, #3
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        sub r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne update
        bl 0x{CHILD_GENERATOR:08X}
        ldr r8, shoot_flags
        ldrh r9, [r8]
        orr r9, r9, #0x40
        strh r9, [r8]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #2
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        mov r8, #0x26
        strh r8, [r4, #0x96]
        mov r8, #0x4A
        mov r9, #1
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, callback_finish
        str r8, [r4]
        pop {{lr}}
        bx lr
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
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    callback_finish: .word 0x{GBA_BASE + PARENT_FINISH:08X}
    """, PARENT_SPAWN)


def build_parent_finish() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        push {{r8}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        asr r0, r0, #3
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        sub r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne update
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #3
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r8, callback_cleanup
        str r8, [r4]
        pop {{lr}}
        bx lr
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
        .align 2
    callback_cleanup: .word 0x{GBA_BASE + PARENT_CLEANUP:08X}
    """, PARENT_FINISH)


def build_parent_cleanup() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        bne complete
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        pop {{lr}}
        bx lr
    complete:
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]
        mov r8, #0xFC00
        strh r8, [r4, #0x34]
        mov r8, #0
        strh r8, [r4, #0xAA]
        ldr r1, [r4, #0x28]
        ldrh r8, [r1, #0xA0]
        bic r8, r8, #1
        strh r8, [r1, #0xA0]
        ldr r8, callback_idle
        str r8, [r4]
        pop {{lr}}
        bx lr
        .align 2
    callback_idle: .word 0x{GBA_BASE + PARENT_IDLE:08X}
    """, PARENT_CLEANUP)


def build_parent_idle() -> bytes:
    return assemble_arm("bx lr", PARENT_IDLE)


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
    require_hash(source, INPUT_SHA256, "v40 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    for label, (start, end, digest) in WSC_RANGES.items():
        require_hash(wsc15[start:end], digest, label)
    for label, (start, end, digest) in GBA_ORACLE_RANGES.items():
        require_hash(gba[start:end], digest, label)

    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (
        OWNERSHIP_END - OWNERSHIP_START
    ):
        raise SystemExit("Shoot parent ownership window is not blank")
    refs_before = aligned_pointer_refs(source, OWNERSHIP_START, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches Shoot parent window: {refs_before}")

    placements = [
        (PARENT_INIT, build_parent_init(), "parent_9083"),
        (PARENT_WAIT, build_parent_wait(), "parent_90F3"),
        (PARENT_SPAWN, build_parent_spawn(), "parent_912A"),
        (PARENT_FINISH, build_parent_finish(), "parent_91AB"),
        (PARENT_CLEANUP, build_parent_cleanup(), "parent_91EF"),
        (PARENT_IDLE, build_parent_idle(), "idle_88F7"),
    ]
    ordered = sorted((start, start + len(blob), label) for start, blob, label in placements)
    for previous, current in zip(ordered, ordered[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"Shoot parent placements overlap: {previous[2]} / {current[2]}")
    if ordered[-1][1] > OWNERSHIP_END:
        raise SystemExit("Shoot parent code exceeds its ownership window")

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
        raise SystemExit("Shoot parent integration contains an unexplained diff")

    output = bytes(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-parent-code-integration-build",
        "claim_scope": (
            "resident 9083->90F3->912A->91AB->91EF->88F7 parent chain using "
            "the commercial GBA object/presentation ABI, connected internally to child "
            "generator 9229 and native sounds 0x5B/0x4A; controller 9908/9A1B entry, "
            "runtime reachability, and audible playback excluded"
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
        "internal_chain": [
            GBA_BASE + PARENT_INIT,
            GBA_BASE + PARENT_WAIT,
            GBA_BASE + PARENT_SPAWN,
            GBA_BASE + PARENT_FINISH,
            GBA_BASE + PARENT_CLEANUP,
            GBA_BASE + PARENT_IDLE,
        ],
        "child_generator": CHILD_GENERATOR,
        "audio_requests": [
            {"wsc_sound_id": 0xCE, "gba_sound_id": 0x5B, "request_type": 1},
            {"wsc_sound_id": 0xA7, "gba_sound_id": 0x4A, "request_type": 1},
        ],
        "external_entry_connected": False,
        "runtime_reachability_verified": False,
        "runtime_audibility_verified": False,
        "known_exclusion": "controller 9908/9A1B callback assignment to parent 9083",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-parent] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
