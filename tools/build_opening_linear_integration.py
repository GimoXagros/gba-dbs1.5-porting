#!/usr/bin/env python3
"""Integrate the four WSC 1.5-only linear opening callbacks.

This layer consumes the exact static v34 candidate.  It splices the commercial
callback-6 edge into four ARM callbacks, changes the aligned selector 3 to 13,
and sequentially reuses the bounded extra opening object slot for resident
records 50 and 49.  Runtime verification remains deliberately deferred.
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

from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks


INPUT_SHA256 = "33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

CALLBACK_7 = 0x5B6000
CALLBACK_8 = 0x5B6800
CALLBACK_9 = 0x5B7000
CALLBACK_10 = 0x5B7800
PREDECESSOR_SUCCESSOR_HOOK = 0x5B8000
PREDECESSOR_AUX_HOOK = 0x5B8040
CONSTRUCT_PRIMARY = 0x5B8100
CONSTRUCT_AUXILIARY = 0x5B8200
UPDATE_OBJECT = 0x5B8300
MAYBE_SKIP = 0x5B8400
CALLBACK_10_EVENT_TABLE = 0x5B8500

PREDECESSOR_SUCCESSOR_SITE = 0x08516C
PREDECESSOR_SELECTOR_SITE = 0x0851CC
PREDECESSOR_AUX_SITE = 0x0851E8
EXPECTED_SUCCESSOR_WORD = 0xE28F8E2E
EXPECTED_SELECTOR_WORD = 0xE3A08003
EXPECTED_AUX_SITE_WORD = 0xE28DD00C

TASK_SET_CALLBACK = 0x012008
TASK_STATE = 0x01201C
TASK_FRAME = 0x013DD4
CHARACTER_CONSUMER = 0x088250
DISPLAY_EVENT = 0x012874
DISPLAY_MOTION = 0x012A84
DISPLAY_UPDATE = 0x012C28
SELECTOR_PALETTE_SETUP = 0x0881F0
SKIP_CLEANUP = 0x088314
RETAIL_SUCCESSOR = 0x085454
RETAIL_TERMINAL = 0x087E3C

PRESENTATION_TIMER = 0x03002674
PRESENTATION_PARAMS = 0x0300267C
DISPLAY_CONTROL = 0x030012CB
FADE_STATE = 0x03002338
INPUT_STATE = 0x0300130A
TASK_COUNT = 0x03002A48
TASK_OBJECT_LIST = 0x030026B8
PRIMARY_OBJECT = 0x03002908
AUXILIARY_OBJECT = 0x030029F8
PRESENTATION_RESOURCE = 0x085B5400
RECORD_49 = 0x080D4498
RECORD_50 = 0x080D44D8

WSC_RANGES = {
    "callback_7": (0x7077, 0x7407, "C3AC134789C3DE1983E8964696851CDEC636F3F95722DD8CF24F0ADD4346554F"),
    "callback_8": (0x7407, 0x7698, "4B1F3D651E981A3006E42C642CEFABCDFC5AE455F7B9BAB488FAA5493E8D3991"),
    "callback_9": (0x7698, 0x7992, "1A20D0D18BC4AB2E9C1ECDBF57D1BC4D2C959C79A7DF1445B7AC4E101A3DCAD7"),
    "callback_10": (0x7992, 0x7D28, "FB46FFCD4F9BD7D50ADDBFE824AD1A70E5295054902C22C0720421B8D3EE542E"),
}
REUSED_GBA_RANGES = {
    "integrated_predecessor": (0x085118, 0x085454, "07DE27CD1956A099607D33045D8AE08B9DDA9C47228C8EFBC2B4C6AF685958BE"),
    "native_record_49": (0x0D4498, 0x0D44B8, "19A8182901524E6F36B5EB4BE2B4BD2D32A9BF335576D274EFE5F01BAE4DFAD7"),
    "native_record_50": (0x0D44D8, 0x0D44F8, "1D0712DC206028852BCDEA2477498FFA960EA7992579EBC534A9C7C63B8B8DEA"),
    "expanded_presentation_table": (0x5B5400, 0x5B55E0, "8EFF8EC1B0CBBD7334563D8EA55B920E67BA8D88883FD334F7929E29B615DBD3"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def assemble_arm(source: str, offset: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(
        source, GBA_BASE + offset
    )
    return bytes(encoded)


def arm_branch(source: int, target: int, link: bool = False) -> int:
    source += GBA_BASE if source < GBA_BASE else 0
    target += GBA_BASE if target < GBA_BASE else 0
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    opcode = 0xEB000000 if link else 0xEA000000
    return opcode | ((delta >> 2) & 0x00FFFFFF)


def callback_header(sound: int) -> str:
    return f"""
        push {{r0-r5, lr}}
        ldr r5, fade_state
        push {{r5}}
        push {{r11}}
        mov r8, #0x{sound:X}
        push {{r8}}
        bl 0x{GBA_BASE + TASK_FRAME:X}
        add sp, sp, #12
        ldr r8, presentation_timer
        ldrsh r9, [r8]
        sub r9, r9, #1
        strh r9, [r8]
        cmp r9, #8
        bne setup_done
        mov r0, #0
        ldr r8, presentation_params
        mov r3, #9
        strh r3, [r8]
        strh r0, [r8, #2]
        ldr r8, display_control
        mov r3, #2
        strb r3, [r8], #1
        strh r0, [r8]
    setup_done:
    """


def fade_source(threshold: int, decrement: int, both: bool) -> str:
    first = "" if not both else f"""
        ldrsh r0, [r4, #0x1C]
        sub r0, r0, #{decrement}
        cmp r0, #0x40
        movlt r0, #0x40
        strh r0, [r4, #0x1C]
    """
    return f"""
        cmp r9, #{threshold}
        bgt fade_done
        ldr r4, fade_state
        {first}
        ldrsh r0, [r4, #0x1E]
        sub r0, r0, #{decrement}
        cmp r0, #0x40
        movlt r0, #0x40
        strh r0, [r4, #0x1E]
    fade_done:
    """


def event_source(timer: int, event: int, suffix: str) -> str:
    return f"""
        cmp r9, #{timer}
        bne event_done_{suffix}
        ldr r4, primary_object
        push {{r4}}
        push {{r4}}
        mov r8, #0x{event:X}
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
    event_done_{suffix}:
    """


def callback_literals() -> str:
    return f"""
        .align 2
    presentation_timer: .word 0x{PRESENTATION_TIMER:08X}
    presentation_params: .word 0x{PRESENTATION_PARAMS:08X}
    display_control: .word 0x{DISPLAY_CONTROL:08X}
    fade_state: .word 0x{FADE_STATE:08X}
    primary_object: .word 0x{PRIMARY_OBJECT:08X}
    auxiliary_object: .word 0x{AUXILIARY_OBJECT:08X}
    record_49: .word 0x{RECORD_49:08X}
    """


def transition_source(next_callback: int, timer: int, selector: int,
                      x: int, y: int, event: int,
                      construct_aux_record: int | None = None,
                      set_primary_0x4000: bool = False) -> str:
    aux = ""
    if construct_aux_record is not None:
        aux = f"""
        ldr r0, record_{construct_aux_record}
        bl 0x{GBA_BASE + CONSTRUCT_AUXILIARY:X}
        """
    extra_flag = "" if not set_primary_0x4000 else f"""
        ldr r4, primary_object
        ldrh r0, [r4, #8]
        orr r0, r0, #0x4000
        strh r0, [r4, #8]
    """
    return f"""
        ldr r8, next_callback
        bl 0x{GBA_BASE + TASK_SET_CALLBACK:X}
        ldr r8, presentation_timer
        mov r0, #{timer}
        strh r0, [r8]
        mov r0, #{selector}
        mov r1, #{x}
        mov r2, #{y}
        mov r3, #{event}
        bl 0x{GBA_BASE + CONSTRUCT_PRIMARY:X}
        {extra_flag}
        {aux}
        mov r8, #{selector}
        push {{r8}}
        bl 0x{GBA_BASE + SELECTOR_PALETTE_SETUP:X}
        add sp, sp, #4
        b check_skip
        .align 2
    next_callback: .word 0x{GBA_BASE + next_callback:08X}
    """


def finish_source(skip_count: int) -> str:
    return f"""
    check_skip:
        mov r0, #{skip_count}
        bl 0x{GBA_BASE + MAYBE_SKIP:X}
    callback_return:
        pop {{r0-r5, lr}}
        bx lr
    """ + callback_literals()


def build_callback_7() -> bytes:
    source = callback_header(0x02)
    source += event_source(72, 0x21, "21")
    source += event_source(41, 0x22, "22")
    source += f"""
        cmp r9, #41
        bne aux_position_done
        ldr r4, auxiliary_object
        mov r0, #0x83
        strh r0, [r4]
        mov r0, #0x44
        strh r0, [r4, #2]
    aux_position_done:
    """
    source += event_source(33, 0x23, "23")
    source += fade_source(83, 11, False)
    source += f"""
        cmp r9, #0
        ble transition
        ldr r4, primary_object
        push {{r4}}
        push {{r4}}
        mov r8, #1
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_MOTION:X}
        add sp, sp, #12
        push {{r4}}
        push {{r11}}
        bl 0x{GBA_BASE + DISPLAY_UPDATE:X}
        add sp, sp, #8

        ldr r5, auxiliary_object
        ldrh r0, [r4, #0xE]
        cmp r0, #0x23
        bne aux_no_move
        ldrsh r0, [r5]
        sub r0, r0, #2
        strh r0, [r5]
        ldrsh r0, [r5, #2]
        add r0, r0, #1
        strh r0, [r5, #2]
    aux_no_move:
        ldrh r0, [r5, #0xA]
        tst r0, #0x2000
        beq aux_event_done
        push {{r5}}
        push {{r5}}
        mov r8, #1
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
    aux_event_done:
        mov r0, r5
        bl 0x{GBA_BASE + UPDATE_OBJECT:X}
        b check_skip
    transition:
    """
    source += transition_source(CALLBACK_8, 86, 14, 0x40, 0x68, 0)
    source += finish_source(2)
    return assemble_arm(source, CALLBACK_7)


def build_callback_8() -> bytes:
    source = callback_header(0x89)
    source += event_source(53, 0x1A, "1a")
    source += fade_source(76, 16, True)
    source += f"""
        cmp r9, #0
        ble transition
        ldr r0, primary_object
        bl 0x{GBA_BASE + UPDATE_OBJECT:X}
        b check_skip
    transition:
    """
    source += transition_source(CALLBACK_9, 136, 8, 0x9E, 0x68, 0)
    source += finish_source(1)
    return assemble_arm(source, CALLBACK_8)


def build_callback_9() -> bytes:
    source = callback_header(0x8C)
    source += event_source(120, 0x1D, "1d")
    source += fade_source(108, 14, True)
    source += f"""
        cmp r9, #0
        ble transition
        ldr r4, primary_object
        ldrh r0, [r4, #0xA]
        tst r0, #0x2000
        beq primary_event_done
        push {{r4}}
        push {{r4}}
        mov r8, #0x1E
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
    primary_event_done:
        mov r0, r4
        bl 0x{GBA_BASE + UPDATE_OBJECT:X}
        b check_skip
    transition:
        bl 0x{GBA_BASE + TASK_STATE:X}
        mov r1, r0
        mov r0, #0
        strh r0, [r1, #0x10]
        mov r2, #16
        strh r2, [r1, #0x12]
        strh r0, [r1, #0x14]
    """
    source += transition_source(
        CALLBACK_10, 136, 9, 0x40, 0x68, 0,
        construct_aux_record=49, set_primary_0x4000=True,
    )
    source += finish_source(1)
    return assemble_arm(source, CALLBACK_9)


def build_callback_10() -> bytes:
    source = callback_header(0x88)
    source += fade_source(132, 7, True)
    source += f"""
        cmp r9, #0
        ble transition
        bl 0x{GBA_BASE + TASK_STATE:X}
        mov r5, r0
        ldr r4, primary_object
        ldrh r0, [r5, #0x12]
        sub r0, r0, #1
        strh r0, [r5, #0x12]
        cmp r0, #0
        bne primary_sequence_done
        ldrh r2, [r5, #0x10]
        add r0, r2, #1
        strh r0, [r5, #0x10]
        ldr r3, event_table
        add r3, r3, r2, lsl #2
        ldrh r0, [r3]
        ldrh r2, [r3, #2]
        strh r2, [r5, #0x12]
        cmp r0, #0x25
        bne primary_send_event
        mov r2, #1
        strh r2, [r5, #0x14]
        ldr r2, auxiliary_object
        mov r3, #0x54
        strh r3, [r2]
        mov r3, #0x58
        strh r3, [r2, #2]
    primary_send_event:
        push {{r4}}
        push {{r4}}
        push {{r0}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
    primary_sequence_done:
        mov r0, r4
        bl 0x{GBA_BASE + UPDATE_OBJECT:X}
        bl 0x{GBA_BASE + TASK_STATE:X}
        mov r5, r0
        ldrh r0, [r5, #0x14]
        cmp r0, #0
        beq aux_done
        ldr r5, auxiliary_object
        ldrsh r0, [r5]
        add r0, r0, #2
        cmp r0, #0xF0
        movgt r0, #0xF0
        strh r0, [r5]
        ldrsh r0, [r5, #2]
        add r0, r0, #2
        cmp r0, #0xA0
        movgt r0, #0xA0
        strh r0, [r5, #2]
        mov r0, r5
        bl 0x{GBA_BASE + UPDATE_OBJECT:X}
    aux_done:
        b check_skip
    transition:
    """
    source += transition_source(
        RETAIL_SUCCESSOR, 78, 3, 0x96, 0x68, 2,
        set_primary_0x4000=True,
    )
    source += finish_source(2)
    source += f"event_table: .word 0x{GBA_BASE + CALLBACK_10_EVENT_TABLE:08X}\n"
    return assemble_arm(source, CALLBACK_10)


def build_callback_10_event_table() -> bytes:
    entries = (
        (0x0B, 4), (0x0C, 7), (0x0D, 24), (0x0E, 19),
        (0x23, 19), (0x24, 6), (0x25, 400),
    )
    return b"".join(struct.pack("<2H", *entry) for entry in entries)


def build_predecessor_successor_hook() -> bytes:
    return assemble_arm(f"""
        ldr r8, callback_7
        bl 0x{GBA_BASE + TASK_SET_CALLBACK:X}
        b 0x{GBA_BASE + 0x085174:X}
        .align 2
    callback_7: .word 0x{GBA_BASE + CALLBACK_7:08X}
    """, PREDECESSOR_SUCCESSOR_HOOK)


def build_predecessor_aux_hook() -> bytes:
    return assemble_arm(f"""
        add sp, sp, #12
        ldr r0, record_50
        bl 0x{GBA_BASE + CONSTRUCT_AUXILIARY:X}
        b 0x{GBA_BASE + 0x0851EC:X}
        .align 2
    record_50: .word 0x{RECORD_50:08X}
    """, PREDECESSOR_AUX_HOOK)


def build_construct_primary() -> bytes:
    return assemble_arm(f"""
        push {{r4-r7, lr}}
        mov r4, r0
        mov r5, r1
        mov r6, r2
        mov r7, r3
        push {{r4}}
        mov r8, #0
        push {{r8}}
        ldr r8, presentation_resource
        push {{r8}}
        bl 0x{GBA_BASE + CHARACTER_CONSUMER:X}
        add sp, sp, #12
        ldr r4, primary_object
        strh r5, [r4]
        strh r6, [r4, #2]
        ldrh r0, [r4, #8]
        bic r0, r0, #0x4000
        orr r0, r0, #0x0800
        strh r0, [r4, #8]
        push {{r4}}
        push {{r4}}
        push {{r7}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
        pop {{r4-r7, lr}}
        bx lr
        .align 2
    presentation_resource: .word 0x{PRESENTATION_RESOURCE:08X}
    primary_object: .word 0x{PRIMARY_OBJECT:08X}
    """, CONSTRUCT_PRIMARY)


def build_construct_auxiliary() -> bytes:
    return assemble_arm(f"""
        push {{r4-r6, lr}}
        mov r6, r0
        mov r8, #0
        push {{r8}}
        mov r8, #3
        push {{r8}}
        push {{r6}}
        bl 0x{GBA_BASE + CHARACTER_CONSUMER:X}
        add sp, sp, #12
        ldr r4, auxiliary_object
        mov r0, #0
        strh r0, [r4]
        mvn r5, #0x1F
        strh r5, [r4, #2]
        ldrh r0, [r4, #8]
        orr r0, r0, #0x0C00
        strh r0, [r4, #8]
        push {{r4}}
        push {{r4}}
        mov r8, #0
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
        pop {{r4-r6, lr}}
        bx lr
        .align 2
    auxiliary_object: .word 0x{AUXILIARY_OBJECT:08X}
    """, CONSTRUCT_AUXILIARY)


def build_update_object() -> bytes:
    return assemble_arm(f"""
        push {{r4, lr}}
        mov r4, r0
        push {{r4}}
        push {{r4}}
        mov r8, #1
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_MOTION:X}
        add sp, sp, #12
        push {{r4}}
        push {{r11}}
        bl 0x{GBA_BASE + DISPLAY_UPDATE:X}
        add sp, sp, #8
        pop {{r4, lr}}
        bx lr
    """, UPDATE_OBJECT)


def build_maybe_skip() -> bytes:
    return assemble_arm(f"""
        push {{r4-r6, lr}}
        mov r6, r0
        ldr r4, input_state
        ldrh r0, [r4]
        tst r0, #0x60
        beq no_skip
        bl 0x{GBA_BASE + SKIP_CLEANUP:X}
        ldr r4, fade_state
        mov r0, #0x26
        strh r0, [r4]
        mov r0, #0
        strh r0, [r4, #2]
        ldr r4, display_control
        mov r0, #2
        strb r0, [r4], #1
        mov r0, #0
        strh r0, [r4]
        ldr r4, task_count
        strh r6, [r4]
        ldr r4, task_object_list
        ldr r5, primary_object
        str r5, [r4]
        cmp r6, #2
        ldreq r5, auxiliary_object
        streq r5, [r4, #4]
        ldr r8, retail_terminal
        bl 0x{GBA_BASE + TASK_SET_CALLBACK:X}
        mov r0, #1
        pop {{r4-r6, lr}}
        bx lr
    no_skip:
        mov r0, #0
        pop {{r4-r6, lr}}
        bx lr
        .align 2
    input_state: .word 0x{INPUT_STATE:08X}
    fade_state: .word 0x{FADE_STATE:08X}
    display_control: .word 0x{DISPLAY_CONTROL:08X}
    task_count: .word 0x{TASK_COUNT:08X}
    task_object_list: .word 0x{TASK_OBJECT_LIST:08X}
    primary_object: .word 0x{PRIMARY_OBJECT:08X}
    auxiliary_object: .word 0x{AUXILIARY_OBJECT:08X}
    retail_terminal: .word 0x{GBA_BASE + RETAIL_TERMINAL:08X}
    """, MAYBE_SKIP)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    if sha256(source) != INPUT_SHA256:
        raise SystemExit("refusing unknown pre-linear-opening candidate")
    wsc = args.wsc15.read_bytes()
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    bank = wsc[0x750000:0x760000]
    for label, (start, end, expected) in WSC_RANGES.items():
        if sha256(bank[start:end]) != expected:
            raise SystemExit(f"WSC linear callback source changed: {label}")
    for label, (start, end, expected) in REUSED_GBA_RANGES.items():
        if sha256(source[start:end]) != expected:
            raise SystemExit(f"reused GBA range changed: {label}")
    expected_words = {
        PREDECESSOR_SUCCESSOR_SITE: EXPECTED_SUCCESSOR_WORD,
        PREDECESSOR_SELECTOR_SITE: EXPECTED_SELECTOR_WORD,
        PREDECESSOR_AUX_SITE: EXPECTED_AUX_SITE_WORD,
    }
    for offset, expected in expected_words.items():
        actual = struct.unpack_from("<I", source, offset)[0]
        if actual != expected:
            raise SystemExit(f"linear opening hook word changed at 0x{offset:X}")

    placements = (
        (CALLBACK_7, build_callback_7(), "added linear callback 7"),
        (CALLBACK_8, build_callback_8(), "added linear callback 8"),
        (CALLBACK_9, build_callback_9(), "added linear callback 9"),
        (CALLBACK_10, build_callback_10(), "added linear callback 10"),
        (PREDECESSOR_SUCCESSOR_HOOK, build_predecessor_successor_hook(), "callback-6 successor hook"),
        (PREDECESSOR_AUX_HOOK, build_predecessor_aux_hook(), "record-50 predecessor hook"),
        (CONSTRUCT_PRIMARY, build_construct_primary(), "opening primary-object constructor adapter"),
        (CONSTRUCT_AUXILIARY, build_construct_auxiliary(), "opening slot-3 constructor adapter"),
        (UPDATE_OBJECT, build_update_object(), "opening object update adapter"),
        (MAYBE_SKIP, build_maybe_skip(), "opening one/two-object skip adapter"),
        (CALLBACK_10_EVENT_TABLE, build_callback_10_event_table(), "callback-10 converted event table"),
    )
    ordered = sorted((target, target + len(blob), label) for target, blob, label in placements)
    for previous, current in zip(ordered, ordered[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"linear opening placements overlap: {previous[2]} / {current[2]}")

    patched = bytearray(source)
    manifest_placements = []
    for target, blob, label in placements:
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is not blank expansion space")
        patched[target:target + len(blob)] = blob
        manifest_placements.append({
            "label": label,
            "target": target,
            "bytes": len(blob),
            "sha256": sha256(blob),
        })

    struct.pack_into(
        "<I", patched, PREDECESSOR_SUCCESSOR_SITE,
        arm_branch(PREDECESSOR_SUCCESSOR_SITE, PREDECESSOR_SUCCESSOR_HOOK),
    )
    struct.pack_into("<I", patched, PREDECESSOR_SELECTOR_SITE, 0xE3A0800D)
    struct.pack_into(
        "<I", patched, PREDECESSOR_AUX_SITE,
        arm_branch(PREDECESSOR_AUX_SITE, PREDECESSOR_AUX_HOOK),
    )

    output_hash = sha256(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-opening-linear-integration-build",
        "claim_scope": (
            "static four-callback chain, selector 3-to-13 predecessor change, "
            "and sequential extra-slot construction/update/skip handling; "
            "runtime timing, visual, audio, transition, and skip QA deferred"
        ),
        "input_sha256": INPUT_SHA256,
        "wsc15_sha256": WSC15_SHA256,
        "output_sha256": output_hash,
        "output_bytes": len(patched),
        "hooks": {
            "successor_site": PREDECESSOR_SUCCESSOR_SITE,
            "selector_site": PREDECESSOR_SELECTOR_SITE,
            "auxiliary_site": PREDECESSOR_AUX_SITE,
        },
        "callbacks": [CALLBACK_7, CALLBACK_8, CALLBACK_9, CALLBACK_10],
        "slot_plan": {
            "slot": 3,
            "address": AUXILIARY_OBJECT,
            "record_50_constructed_before_callback": 7,
            "record_49_reconstructed_before_callback": 10,
        },
        "placements": manifest_placements,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[opening-linear] output SHA-256 {output_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
