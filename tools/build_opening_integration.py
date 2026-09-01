#!/usr/bin/env python3
"""Integrate the two additional Ver. 1.5 opening-choice presentations.

This layer extends the commercial three-state high-nibble cycle to five states,
preserves the three retail case entries, and translates WSC 1.5 states 3 and 4
into the existing GBA opening ABI. Runtime verification remains deferred.
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


INPUT_SHA256 = "1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

CHOICE_HOOK_SITE = 0x086E48
EXPECTED_CHOICE_HOOK_WORD = 0xE59F11BC
CHOICE_DISPATCH = 0x5B4000
CHOICE_CASE_STATE3 = 0x5B4100
CHOICE_CASE_STATE4 = 0x5B4300
CHOICE_CALLBACK_STATE3 = 0x5B4600
CHOICE_CALLBACK_STATE4 = 0x5B4C00
STATE3_TABLE_LEFT = 0x5B5200
STATE3_TABLE_RIGHT = 0x5B5280
STATE4_TABLE_LEFT = 0x5B5300
STATE4_TABLE_RIGHT = 0x5B5320

RETAIL_CASE_STATE0 = 0x086E90
RETAIL_CASE_STATE1 = 0x08703C
RETAIL_CASE_STATE2 = 0x0871B4
RETAIL_CASE_COMMON_TAIL = 0x08730C
RETAIL_CHOICE_CONVERGENCE = 0x087788
RETAIL_CHOICE_TRANSITION = 0x087940

TASK_SET_CALLBACK = 0x012008
TASK_STATE = 0x01201C
CHARACTER_CONSUMER = 0x088250
DISPLAY_EVENT = 0x012874
DISPLAY_MOTION = 0x012A84
DISPLAY_UPDATE = 0x012C28
PALETTE_CLEAR = 0x000104C
CASE_FINALIZE = 0x0000D18

BATTLE_STATE = 0x03002310
PRESENTATION_TIMER = 0x03002674
PRESENTATION_PARAMS = 0x0300267C
PRESENTATION_FLAGS = 0x03002A50
PRESENTATION_RESOURCE = 0x080D42B8
DISPLAY_OBJECT_LEFT = 0x03002908
DISPLAY_OBJECT_RIGHT = 0x03002958
DISPLAY_CONTROL = 0x030012CB
PALETTE_LEFT = 0x05000200
PALETTE_RIGHT = 0x05000240

WSC_RANGES = {
    "state4_case": (0x92C0, 0x93B5, "8FA5DEE99A83AFBF8F3651EFF2EB5511E67185E400C796DF06A245A3BB71F539"),
    "state3_case": (0x93B5, 0x94A2, "6D9BE72A47BFEF18E5D8B4060B14C48F6F4B08B7A55802DBE701CDFD39872576"),
    "state4_callback": (0x9C17, 0x9E24, "4ACA001A4BEFAA06503347BAA93417C4F1BA980760243E4CEAA522C9629891F6"),
    "state4_tables": (0x9E24, 0x9E40, "E40953CC70149EEC2B430F3C5836DB1A9981DFA86DAE969B38DE7D3B75608692"),
    "state3_callback": (0x9E40, 0xA0EC, "528F3590F530A597320EF9E27D60165B48E522AF6172D6FF0ACEC71CEDD46D45"),
    "state3_tables": (0xA0EC, 0xA180, "2461F08A169A1D305CA002526DFDCE875CC9DFAEA07B8E0023D767F7955B88A6"),
}
REUSED_GBA_RANGES = {
    "retail_choice_cases": (0x086E90, 0x08730C, "C94630CE393812278D414E7196D9315DC704691606B18AF7C5FE6E9488EAA2AD"),
    "retail_case_common_tail": (0x08730C, 0x0873CC, "1DAD63CC643CB43CF443FE7B0261E5DF70F8FC8842E14AFF6063C7FF0F483DD9"),
    "retail_choice_convergence": (0x087788, 0x087798, "88E13154DD96603871FD41F5BE1963DBBEF5C4B16E81AB1C7D66765DE8A16063"),
    "retail_choice_transition": (0x087940, 0x087A48, "3F8D028978B0F2D04FF8B32300C6968E5C0A9590137B02F824415BAF08762A36"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def assemble_arm(source: str, address: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(
        source, GBA_BASE + address
    )
    return bytes(encoded)


def arm_branch(source: int, target: int) -> int:
    source += GBA_BASE if source < GBA_BASE else 0
    target += GBA_BASE if target < GBA_BASE else 0
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    return 0xEA000000 | ((delta >> 2) & 0x00FFFFFF)


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def packed16(value: int) -> int:
    return value & 0xFFFF


def scale_duration(value: int) -> int:
    return value * 4 // 5


def scale_motion(value: int) -> int:
    if value == 0xFFFF:
        return value
    signed = signed16(value)
    magnitude = abs(signed) * 5 // 4
    return packed16(-magnitude if signed < 0 else magnitude)


def read_pair_table(bank: bytes, start: int) -> list[tuple[int, int]]:
    rows = []
    cursor = start
    while True:
        event, duration = struct.unpack_from("<HH", bank, cursor)
        rows.append((event, duration))
        cursor += 4
        if event == 0xFFFF:
            return rows


def convert_pair_table(rows: list[tuple[int, int]]) -> bytes:
    converted = []
    for event, duration in rows:
        converted.extend((event, 0 if event == 0xFFFF else scale_duration(duration)))
    return struct.pack(f"<{len(converted)}H", *converted)


def read_motion_table(bank: bytes, start: int) -> list[tuple[int, ...]]:
    rows = []
    cursor = start
    while True:
        row = struct.unpack_from("<8H", bank, cursor)
        rows.append(row)
        cursor += 16
        if row[0] == 0xFFFF:
            return rows


def convert_motion_table(rows: list[tuple[int, ...]]) -> bytes:
    converted = []
    for row in rows:
        event, duration, velocity_x, velocity_y, accel_x, accel_y, pad0, pad1 = row
        if event == 0xFFFF:
            converted.append((0xFFFF, 0, 0, 0, 0, 0, 0, 0))
            continue
        converted.append((
            event,
            scale_duration(duration),
            scale_motion(velocity_x),
            scale_motion(velocity_y),
            scale_motion(accel_x),
            scale_motion(accel_y),
            pad0,
            pad1,
        ))
    return b"".join(struct.pack("<8H", *row) for row in converted)


def build_dispatch() -> bytes:
    return assemble_arm(f"""
        ldr r1, battle_state
        ldrb r3, [r1, #0x20]
        lsr r3, r3, #4
        add r2, r3, #1
        cmp r2, #5
        movge r2, #0
        lsl r2, r2, #4
        ldrb r0, [r1, #0x20]
        and r0, r0, #0x0F
        orr r0, r0, r2
        strb r0, [r1, #0x20]
        mov r9, #0
        cmp r3, #3
        beq 0x{GBA_BASE + CHOICE_CASE_STATE3:X}
        cmp r3, #4
        beq 0x{GBA_BASE + CHOICE_CASE_STATE4:X}
        cmp r3, #1
        beq 0x{GBA_BASE + RETAIL_CASE_STATE1:X}
        cmp r3, #2
        beq 0x{GBA_BASE + RETAIL_CASE_STATE2:X}
        b 0x{GBA_BASE + RETAIL_CASE_STATE0:X}
        .align 2
    battle_state: .word 0x{BATTLE_STATE:08X}
    """, CHOICE_DISPATCH)


def build_choice_case(
    *,
    address: int,
    callback: int,
    selectors: tuple[int, int],
    positions: tuple[tuple[int, int], tuple[int, int]],
    events: tuple[int, int],
    clear_masks: tuple[int, ...],
    state_halfwords: tuple[int, ...],
) -> bytes:
    clear_source = ""
    for index, mask in enumerate(clear_masks):
        palette = PALETTE_LEFT if index == 0 else PALETTE_RIGHT
        clear_source += f"""
        ldr r8, presentation_flags
        ldrh r9, [r8]
        tst r9, #0x{mask:X}
        bne clear_done_{index}
        ldr r5, palette_{index}
        mov r0, #0
        mov r2, #8
        bl 0x{GBA_BASE + PALETTE_CLEAR:X}
    clear_done_{index}:
        """
    state_source = ""
    for index, value in enumerate(state_halfwords):
        if value <= 0xFF:
            state_source += f"mov r9, #0x{value:X}\n"
        else:
            state_source += f"ldr r9, state_value_{index}\n"
        state_source += f"strh r9, [r1, #0x{index * 2:X}]\n"
    literal_values = "\n".join(
        f"state_value_{index}: .word 0x{value:08X}"
        for index, value in enumerate(state_halfwords)
        if value > 0xFF
    )
    x0, y0 = positions[0]
    x1, y1 = positions[1]
    return assemble_arm(f"""
        ldr r8, selected_callback
        bl 0x{GBA_BASE + TASK_SET_CALLBACK:X}

        ldr r4, object_left
        mov r8, #0x{selectors[0]:X}
        push {{r8}}
        mov r8, #0
        push {{r8}}
        ldr r8, presentation_resource
        push {{r8}}
        bl 0x{GBA_BASE + CHARACTER_CONSUMER:X}
        add sp, sp, #12
        ldr r9, left_x
        strh r9, [r4]
        mov r9, #0x{y0:X}
        strh r9, [r4, #2]
        ldrh r8, [r4, #8]
        orr r8, r8, #0x4C00
        strh r8, [r4, #8]
        push {{r4}}
        push {{r4}}
        mov r8, #0x{events[0]:X}
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12

        ldr r4, object_right
        mov r8, #0x{selectors[1]:X}
        push {{r8}}
        mov r8, #1
        push {{r8}}
        ldr r8, presentation_resource
        push {{r8}}
        bl 0x{GBA_BASE + CHARACTER_CONSUMER:X}
        add sp, sp, #12
        ldr r9, right_x
        strh r9, [r4]
        mov r9, #0x{y1:X}
        strh r9, [r4, #2]
        ldrh r8, [r4, #8]
        orr r8, r8, #0x0C00
        strh r8, [r4, #8]
        push {{r4}}
        push {{r4}}
        mov r8, #0x{events[1]:X}
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12

        {clear_source}
        bl 0x{GBA_BASE + TASK_STATE:X}
        mov r1, r0
        {state_source}
        bl 0x{GBA_BASE + CASE_FINALIZE:X}
        b 0x{GBA_BASE + RETAIL_CASE_COMMON_TAIL:X}
        .align 2
    selected_callback: .word 0x{GBA_BASE + callback:08X}
    object_left: .word 0x{DISPLAY_OBJECT_LEFT:08X}
    object_right: .word 0x{DISPLAY_OBJECT_RIGHT:08X}
    presentation_resource: .word 0x{PRESENTATION_RESOURCE:08X}
    presentation_flags: .word 0x{PRESENTATION_FLAGS:08X}
    palette_0: .word 0x{PALETTE_LEFT:08X}
    palette_1: .word 0x{PALETTE_RIGHT:08X}
    left_x: .word 0x{x0 & 0xFFFFFFFF:08X}
    right_x: .word 0x{x1 & 0xFFFFFFFF:08X}
    {literal_values}
    """, address)


TIMER_PREFIX = f"""
        push {{r0-r5, lr}}
        bl 0x{GBA_BASE + TASK_STATE:X}
        mov r1, r0
        ldr r8, presentation_timer
        ldrsh r9, [r8]
        sub r9, r9, #1
        strh r9, [r8]
        cmp r9, #12
        bne timer_ready
        ldr r8, presentation_flags
        ldrh r0, [r8]
        orr r0, r0, #0x8000
        strh r0, [r8]
        mov r0, #0
        ldr r8, presentation_params
        mov r9, #12
        strh r9, [r8]
        strh r0, [r8, #2]
        ldr r8, display_control
        mov r9, #2
        strb r9, [r8], #1
        mov r9, #0
        strh r9, [r8]
    timer_ready:
        cmp r9, #0
        bgt process_objects
        b 0x{GBA_BASE + RETAIL_CHOICE_CONVERGENCE:X}
    process_objects:
"""


CALLBACK_LITERALS = f"""
        .align 2
    presentation_timer: .word 0x{PRESENTATION_TIMER:08X}
    presentation_flags: .word 0x{PRESENTATION_FLAGS:08X}
    presentation_params: .word 0x{PRESENTATION_PARAMS:08X}
    display_control: .word 0x{DISPLAY_CONTROL:08X}
    object_left: .word 0x{DISPLAY_OBJECT_LEFT:08X}
    object_right: .word 0x{DISPLAY_OBJECT_RIGHT:08X}
"""


def pair_object_source(prefix: str, state_offset: int, object_label: str, table_label: str) -> str:
    return f"""
        ldr r4, {object_label}
        ldrh r0, [r1, #0x{state_offset + 6:X}]
        cmp r0, #0
        beq {prefix}_finish
        push {{r4}}
        push {{r4}}
        mov r8, #1
        push {{r8}}
        bl 0x{GBA_BASE + DISPLAY_MOTION:X}
        add sp, sp, #12
        ldrh r0, [r1, #0x{state_offset + 6:X}]
        sub r0, r0, #1
        strh r0, [r1, #0x{state_offset + 6:X}]
        cmp r0, #0
        bne {prefix}_move
        ldr r2, {table_label}
        ldrh r3, [r1, #0x{state_offset + 8:X}]
        add r0, r3, #1
        strh r0, [r1, #0x{state_offset + 8:X}]
        add r2, r2, r3, lsl #2
        ldrh r0, [r2]
        mvn r3, #0
        cmp r0, r3
        beq {prefix}_move
        push {{r1-r3}}
        push {{r4}}
        push {{r11}}
        push {{r0}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
        pop {{r1-r3}}
        ldrh r0, [r2, #2]
        strh r0, [r1, #0x{state_offset + 6:X}]
    {prefix}_move:
        ldrh r0, [r4, #0xE]
        cmp r0, #0
        beq {prefix}_finish
        ldrsh r0, [r1, #0x{state_offset + 4:X}]
        ldrsh r2, [r1, #0x{state_offset + 2:X}]
        add r2, r2, r0
        strh r2, [r1, #0x{state_offset + 2:X}]
        asr r2, r2, #4
        ldrsh r0, [r1, #0x{state_offset:X}]
        add r0, r0, r2
        strh r0, [r1, #0x{state_offset:X}]
        asr r0, r0, #4
        strh r0, [r4]
    {prefix}_finish:
        push {{r4}}
        push {{r11}}
        bl 0x{GBA_BASE + DISPLAY_UPDATE:X}
        add sp, sp, #8
    """


def build_state4_callback() -> bytes:
    source = (
        TIMER_PREFIX
        + pair_object_source("left", 0x00, "object_left", "table_left")
        + pair_object_source("right", 0x0A, "object_right", "table_right")
        + f"b 0x{GBA_BASE + RETAIL_CHOICE_TRANSITION:X}\n"
        + CALLBACK_LITERALS
        + f"table_left: .word 0x{GBA_BASE + STATE4_TABLE_LEFT:08X}\n"
        + f"table_right: .word 0x{GBA_BASE + STATE4_TABLE_RIGHT:08X}\n"
    )
    return assemble_arm(source, CHOICE_CALLBACK_STATE4)


def motion_object_source(prefix: str, state_offset: int, object_label: str, table_label: str) -> str:
    return f"""
        ldr r4, {object_label}
        ldrh r0, [r1, #0x{state_offset + 0xC:X}]
        cmp r0, #0
        beq {prefix}_helpers
        sub r0, r0, #1
        strh r0, [r1, #0x{state_offset + 0xC:X}]
        cmp r0, #0
        bne {prefix}_move
        ldr r2, {table_label}
        ldrh r3, [r1, #0x{state_offset + 0xE:X}]
        add r0, r3, #1
        strh r0, [r1, #0x{state_offset + 0xE:X}]
        add r2, r2, r3, lsl #4
        ldrh r0, [r2]
        mvn r3, #0
        cmp r0, r3
        beq {prefix}_helpers
        cmp r0, #0x8000
        beq {prefix}_event_done
        push {{r1-r3}}
        push {{r4}}
        push {{r11}}
        push {{r0}}
        bl 0x{GBA_BASE + DISPLAY_EVENT:X}
        add sp, sp, #12
        pop {{r1-r3}}
    {prefix}_event_done:
        ldrh r0, [r2, #2]
        strh r0, [r1, #0x{state_offset + 0xC:X}]
        ldrh r0, [r2, #4]
        cmp r0, r3
        strhne r0, [r1, #0x{state_offset + 2:X}]
        ldrh r0, [r2, #6]
        cmp r0, r3
        strhne r0, [r1, #0x{state_offset + 8:X}]
        ldrh r0, [r2, #8]
        cmp r0, r3
        strhne r0, [r1, #0x{state_offset + 4:X}]
        ldrh r0, [r2, #10]
        cmp r0, r3
        strhne r0, [r1, #0x{state_offset + 0xA:X}]
    {prefix}_move:
        ldrsh r0, [r1, #0x{state_offset + 4:X}]
        ldrsh r2, [r1, #0x{state_offset + 2:X}]
        add r2, r2, r0
        strh r2, [r1, #0x{state_offset + 2:X}]
        asr r2, r2, #4
        ldrsh r0, [r1, #0x{state_offset:X}]
        add r0, r0, r2
        strh r0, [r1, #0x{state_offset:X}]
        asr r0, r0, #4
        strh r0, [r4]
        ldrsh r0, [r1, #0x{state_offset + 0xA:X}]
        ldrsh r2, [r1, #0x{state_offset + 8:X}]
        add r2, r2, r0
        strh r2, [r1, #0x{state_offset + 8:X}]
        asr r2, r2, #4
        ldrsh r0, [r1, #0x{state_offset + 6:X}]
        add r0, r0, r2
        strh r0, [r1, #0x{state_offset + 6:X}]
        asr r0, r0, #4
        strh r0, [r4, #2]
    {prefix}_helpers:
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
    """


def build_state3_callback() -> bytes:
    source = (
        TIMER_PREFIX
        + motion_object_source("left", 0x00, "object_left", "table_left")
        + motion_object_source("right", 0x10, "object_right", "table_right")
        + f"b 0x{GBA_BASE + RETAIL_CHOICE_TRANSITION:X}\n"
        + CALLBACK_LITERALS
        + f"table_left: .word 0x{GBA_BASE + STATE3_TABLE_LEFT:08X}\n"
        + f"table_right: .word 0x{GBA_BASE + STATE3_TABLE_RIGHT:08X}\n"
    )
    return assemble_arm(source, CHOICE_CALLBACK_STATE3)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    if sha256(source) != INPUT_SHA256:
        raise SystemExit("refusing unknown pre-opening candidate")
    wsc = args.wsc15.read_bytes()
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    bank = wsc[0x75 * 0x10000:0x76 * 0x10000]
    for label, (start, end, expected) in WSC_RANGES.items():
        actual = sha256(bank[start:end])
        if actual != expected:
            raise SystemExit(f"WSC opening source range changed: {label}")
    for label, (start, end, expected) in REUSED_GBA_RANGES.items():
        if sha256(source[start:end]) != expected:
            raise SystemExit(f"reused commercial GBA opening range changed: {label}")
    if struct.unpack_from("<I", source, CHOICE_HOOK_SITE)[0] != EXPECTED_CHOICE_HOOK_WORD:
        raise SystemExit("commercial opening choice hook site changed")

    state4_left = convert_pair_table(read_pair_table(bank, 0x9E24))
    state4_right = convert_pair_table(read_pair_table(bank, 0x9E32))
    state3_left = convert_motion_table(read_motion_table(bank, 0xA0EC))
    state3_right = convert_motion_table(read_motion_table(bank, 0xA12E))
    if [struct.unpack_from("<2H", state4_left, offset) for offset in range(0, len(state4_left), 4)] != [
        (0, 40), (27, 16), (28, 8), (0xFFFF, 0),
    ]:
        raise SystemExit("state-4 left event-table conversion changed")
    if [struct.unpack_from("<2H", state4_right, offset) for offset in range(0, len(state4_right), 4)] != [
        (0, 40), (2, 16), (27, 8), (0xFFFF, 0),
    ]:
        raise SystemExit("state-4 right event-table conversion changed")

    state3_case = build_choice_case(
        address=CHOICE_CASE_STATE3,
        callback=CHOICE_CALLBACK_STATE3,
        selectors=(13, 14),
        positions=((0x20, 0x60), (0xD0, 0x58)),
        events=(7, 4),
        clear_masks=(),
        state_halfwords=(
            0x01FE, 0x0280, 0x0014, 0x0600,
            0x0140, 0x0014, 0x0010, 0x0000,
            0x0D00, 0x0000, 0x0000, 0x0580,
            0x0000, 0x0000, 0x0008, 0x0000,
        ),
    )
    state4_case = build_choice_case(
        address=CHOICE_CASE_STATE4,
        callback=CHOICE_CALLBACK_STATE4,
        selectors=(12, 11),
        positions=((-0x40, 0x58), (0x120, 0x58)),
        events=(2, 2),
        clear_masks=(0x20, 0x10),
        state_halfwords=(
            0xFBFE, 0x0280, 0x0012, 0x0018, 0x0000,
            0x1200, 0xFD80, 0xFFEE, 0x0018, 0x0000,
        ),
    )
    placements = (
        (CHOICE_DISPATCH, build_dispatch(), "five-state opening choice dispatcher"),
        (CHOICE_CASE_STATE3, state3_case, "Patamon/Tailmon opening case"),
        (CHOICE_CASE_STATE4, state4_case, "Crimson/Blast opening case"),
        (CHOICE_CALLBACK_STATE3, build_state3_callback(), "Patamon/Tailmon opening callback"),
        (CHOICE_CALLBACK_STATE4, build_state4_callback(), "Crimson/Blast opening callback"),
        (STATE3_TABLE_LEFT, state3_left, "state-3 left motion table"),
        (STATE3_TABLE_RIGHT, state3_right, "state-3 right motion table"),
        (STATE4_TABLE_LEFT, state4_left, "state-4 left event table"),
        (STATE4_TABLE_RIGHT, state4_right, "state-4 right event table"),
    )

    patched = bytearray(source)
    manifest_placements = []
    ordered = sorted((target, target + len(blob), label) for target, blob, label in placements)
    for previous, current in zip(ordered, ordered[1:]):
        if previous[1] > current[0]:
            raise SystemExit(f"opening placements overlap: {previous[2]} / {current[2]}")
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
        "<I", patched, CHOICE_HOOK_SITE,
        arm_branch(CHOICE_HOOK_SITE, CHOICE_DISPATCH),
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-opening-choice-integration-build",
        "claim_scope": (
            "static modulo-5 dispatcher plus WSC 1.5 choice states 3 and 4; "
            "four added linear callbacks and runtime QA remain pending"
        ),
        "input_sha256": INPUT_SHA256,
        "wsc15_sha256": WSC15_SHA256,
        "output_sha256": sha256(patched),
        "output_bytes": len(patched),
        "hook_site": CHOICE_HOOK_SITE,
        "placements": manifest_placements,
        "choice_cycle": {
            "state_storage": "0x03002330 high nibble",
            "modulus": 5,
            "preserved_retail_states": [0, 1, 2],
            "state_3": {"selectors": [13, 14], "callback": CHOICE_CALLBACK_STATE3},
            "state_4": {"selectors": [12, 11], "callback": CHOICE_CALLBACK_STATE4},
        },
        "conversion_rules": {
            "frame_durations": "floor(WSC * 4 / 5)",
            "signed_motion_terms": "truncate_toward_zero(WSC * 5 / 4)",
            "coordinates_and_event_ids": "unchanged",
        },
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
