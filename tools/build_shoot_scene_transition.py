#!/usr/bin/env python3
"""Translate the source EEA scene on the existing native current-task ABI.

The layer has no allocation or external hook.  Full 7168 and the two audio
services must be real, hash-bound code in its exact predecessor.  No RAM
callback table, replacement renderer, or runtime interpreter is introduced.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import (
    GBA_SHA256, WSC10_SHA256, WSC15_SHA256, assemble, require_hash, sha256,
    verify_machine_code,
)
from build_full_asset_poc import convert_tile, parse_wsc_far_descriptor
from build_shoot_initializer import parse_p1, prove_per_item_oracle
from convert_wsc_palette_block import convert_block
from shoot_resource_conversion import parse_shoot_p1, verify_commercial_p1

BASE = 0x08000000
V51_SHA256 = "726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284"
START, END = 0x5C8000, 0x5CA000
PHASES = {
    0xEEA: 0x5C8000, 0xF67: 0x5C8100, 0xFC3: 0x5C8200,
    0x1043: 0x5C8300, 0x10DD: 0x5C8400, 0x11F7: 0x5C8500,
    0x1267: 0x5C8600, 0x12C6: 0x5C8700, 0x1331: 0x5C8800,
    0x139C: 0x5C8900, 0x13F4: 0x5C8A00, 0x1434: 0x5C8B00,
    0x1486: 0x5C8C00, 0x1540: 0x5C8D00,
}
SPAWN, INITIAL, HOMING = 0x5C8E00, 0x5C9000, 0x5C9100
TO_WHITE, CAPTURE_BLACK, DRAW_ICONS, POSITIONS = 0x5C9300, 0x5C9500, 0x5C9600, 0x5C9700
AUDIO_PRELUDE = 0x5C9800
CURRENT_TASK = 0x0300133C
FIRST_PLAYER, SECOND_PLAYER = 0x0300489C, 0x030048A0
FLAGS, SECOND_FLAGS, SHOOT_FLAGS = 0x03004506, 0x03004508, 0x0300450A
BLINK, OBJECT_COUNT, OBJECT_LIST = 0x03004529, 0x0300475E, 0x03004760
OBJECT_HANDLE, SCROLL_EFFECT = 0x03004D54, 0x03004D4C
SOUND = 0x080D15C0
P1, P0, P2 = 0x08350248, 0x083505E8, 0x08352240
POINTS = ((0x600, 0x900), (0xD00, 0x1200), (0x600, 0x1200), (0xE00, 0x900),
          (0x600, 0xB00), (0x1500, 0x1200), (0xE00, 0x1200), (0x1500, 0x900))
SOURCE_GUARDS = (
    ("wsc15", 0x772DEA, 0x7734A9, "39CA2AD6110D79A81414788BAF8997D067F8C220C839DF39090CD66ECB7AC988"),
    ("wsc15", 0x7734C9, 0x773650, "50D9299D5F44A3A21A472602C1B9A97F15C2CBAFA1E9B85A7191806154CA82F2"),
    ("wsc15", 0x751F6B, 0x751FCF, "E669E3E80BDCE078E916F821EDE22F439753584D3F93189FE2164CF112A13B08"),
    ("gba", 0x1565C, 0x15810, "42D0CDC0817926DD399BFD3265A319E3B80F84CE0C65394D1FEFDF8861902717"),
    ("gba", 0x158C8, 0x158CC, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("gba", 0x34059C, 0x3407F4, "B0088F9E6A47A0CEC0B5D6F10473FDB75E9D2EAB573CC8BC51D647583C0D5116"),
    ("gba", 0x370124, 0x37016C, "7D30CA072AB92424F24AA413FB5E2A5A10B9A016E0646F0B696A30389D3DF51C"),
)


def presentation_resources(wsc: bytes, wsc10: bytes, gba: bytes) -> dict:
    """Bind all three source resources to the real retail native consumers."""
    source, native = 0x3CAD70, 0x350248
    if wsc[source:source + 0x2BA] != wsc10[0x2AE180:0x2AE43A]:
        raise ValueError("15C9 source P1 differs from its commercial ancestor")
    p1 = verify_commercial_p1(parse_shoot_p1(wsc, source), gba, native)
    if not p1["payloads_exact"] or not p1["a_records_exact"]:
        raise ValueError("native P1 does not implement the source commands")
    tails = prove_per_item_oracle(gba, wsc10)
    parsed = parse_p1(wsc, source, 0x2BA)
    if [i[0] for i in parsed["commands"]] != [5, 3, 1, 5, 10, 8, 10]:
        raise ValueError("15C9 P1 population changed")
    source, native = 0x3CA7D0, 0x3505E8
    table, descriptors, a, b = struct.unpack_from("<4I", gba, native)
    if (a, b) != struct.unpack_from("<2I", wsc, source + 8):
        raise ValueError("native P0 constants differ")
    table -= BASE
    descriptors -= BASE
    first_count, first_relative = struct.unpack_from("<2H", wsc, source + 16)
    if first_relative != 16 + 15 * 4 or first_count == 0:
        raise ValueError("source P0 layout boundary changed")
    layout_bytes = 0
    for index in range(15):
        count, relative = struct.unpack_from("<2H", wsc, source + 16 + index * 4)
        count2, pointer = struct.unpack_from("<2I", gba, table + index * 8)
        if count != count2 or wsc[source + relative:source + relative + count * 4] != gba[pointer - BASE:pointer - BASE + count * 4]:
            raise ValueError("native P0 layout differs")
        layout_bytes += count * 4
    segment, bank = struct.unpack_from("<2H", wsc, source + 4)
    desc_source = (bank & 127) * 0x10000 + (segment << 4) - 0x20000
    if desc_source != 0x3D4710 or wsc[desc_source + 21 * 8:desc_source + 22 * 8] != b"\xff" * 8:
        raise ValueError("source P0 descriptor boundary changed")
    tile_bytes = 0
    for index in range(21):
        count, raw = parse_wsc_far_descriptor(wsc, desc_source + index * 8)
        native_count, pointer = struct.unpack_from("<2I", gba, descriptors + index * 8)
        converted = b"".join(convert_tile(wsc[p:p + 32]) for p in range(raw, raw + count, 32))
        if native_count != count or converted != gba[pointer - BASE:pointer - BASE + count]:
            raise ValueError("native P0 tile payload differs")
        tile_bytes += count
    if (layout_bytes, tile_bytes) != (648, 6304):
        raise ValueError("15C9 P0 byte population changed")
    if convert_block(wsc[0x3D7A60:0x3D7A86]) != gba[0x352240:0x352268]:
        raise ValueError("native P2 is not the source palette")
    return {"p1": p1, "per_item_tails": tails, "p0_layouts": 15,
            "p0_layout_bytes": layout_bytes, "p0_descriptors": 21,
            "p0_tile_bytes": tile_bytes, "p2_bytes": 40,
            "native_resources": [P1, P0, P2]}


def word_modify(address: int, *, set_bits: int = 0, clear_bits: int = 0) -> str:
    text = f"ldr r1, ={address:#x}\nldrh r2, [r1]\n"
    if clear_bits:
        text += f"bic r2, r2, #{clear_bits:#x}\n"
    if set_bits:
        text += f"orr r2, r2, #{set_bits:#x}\n"
    return text + "strh r2, [r1]\n"


def assign(phase: int) -> str:
    return f"ldr r8, ={BASE + PHASES[phase]:#x}\nbl 0x08012008\n"


def timer(value: int) -> str:
    return f"mov r0, #{value}\nstrh r0, [r4, #0x50]\n"


def countdown() -> str:
    return "ldrh r0, [r4, #0x50]\nsubs r0, r0, #1\nstrh r0, [r4, #0x50]\n"


def pack_code(text: str, offset: int) -> tuple[bytes, int]:
    """Keep Keystone's explicit literal pool outside the decoded code extent."""
    # The two sentinel words delimit a known data-only pool, rather than
    # disassembling arbitrary literal data as if it were ARM instructions.
    source = text + "\n.word 0x13572468\n.word 0x24681357\n.ltorg\n"
    blob = assemble(source, offset)
    marker = struct.pack("<2I", 0x13572468, 0x24681357)
    point = blob.find(marker)
    if point < 0 or point % 4 or blob.find(marker, point + 1) >= 0:
        raise ValueError("generated code/data boundary is ambiguous")
    return blob, point


def phase(phase_id: int, body: str) -> tuple[bytes, int]:
    return pack_code("push {r0-r12, lr}\nmov r11, #0\nbl 0x0801201C\nmov r4, r0\n" +
                     body + "\ndone:\npop {r0-r12, lr}\nbx lr\n", PHASES[phase_id])


def phases(initializer: int) -> dict[int, tuple[bytes, int]]:
    result = {}
    result[0xEEA] = phase(0xEEA, timer(151) + word_modify(FLAGS, set_bits=0x10) + f"""
        ldr r1, ={SHOOT_FLAGS:#x}
        mov r2, #0
        strh r2, [r1]
        ldr r6, ={OBJECT_LIST:#x}
        ldr r1, ={OBJECT_COUNT:#x}
        ldrb r7, [r1]
        cmp r7, #0
        beq released
    release_loop:
        ldr r8, [r6], #4
        push {{r8}}
        push {{r11}}
        bl 0x083524C4
        add sp, sp, #8
        subs r7, r7, #1
        bne release_loop
    released:
        ldr r1, ={FIRST_PLAYER:#x}
        ldr r5, [r1]
        ldrh r0, [r5, #0x64]
        strh r0, [r4, #0x54]
        mov r0, #1
        strh r0, [r5, #0x64]
    """ + word_modify(FLAGS, clear_bits=0x400) + assign(0xF67) + f"bl {BASE + PHASES[0xF67]:#x}\n")
    result[0xF67] = phase(0xF67, countdown() + "bne blink\n" +
        word_modify(SECOND_FLAGS, clear_bits=1, set_bits=2) + timer(200) + assign(0xFC3) + f"""
        b done
    blink:
        ldr r1, ={BLINK:#x}
        ldrb r0, [r1]
        eor r0, r0, #7
        strb r0, [r1]
        mov r0, #1
        strh r0, [r4, #0x64]
    """)
    result[0xFC3] = phase(0xFC3, f"""
        ldr r1, ={FIRST_PLAYER:#x}
        ldr r5, [r1]
        mov r0, #0
        strh r0, [r5, #0x2C]
        strh r0, [r5, #0x2E]
        ldrsh r0, [r5, #0x34]
        cmp r0, #0xE40
        movge r0, #8
        strhge r0, [r5, #0x2C]
        bge done
        cmp r0, #0xDC0
        movle r0, #2
        strhle r0, [r5, #0x2C]
        ble done
        ldr r1, ={FLAGS:#x}
        ldrh r2, [r1]
        tst r2, #0x40
        beq done
        orr r2, r2, #8
        strh r2, [r1]
        mov r0, #5
        strh r0, [r5, #0x52]
        mov r0, #0
        strh r0, [r5, #0x2C]
    """ + assign(0x1043) + f"bl {BASE + PHASES[0x1043]:#x}\n")
    result[0x1043] = phase(0x1043, countdown() + "bne done\n" +
        word_modify(FLAGS, clear_bits=8) + timer(100) + f"""
        mov r0, #0
        strh r0, [r4, #0x2C]
        bl {BASE + CAPTURE_BLACK:#x}
    """ + word_modify(FLAGS, set_bits=2) + f"""
        ldr r1, ={SCROLL_EFFECT:#x}
        mov r0, #0
        strh r0, [r1]
        ldr r1, ={SECOND_PLAYER:#x}
        ldr r6, [r1]
        ldrh r0, [r6, #4]
        orr r0, r0, #0x20
        strh r0, [r6, #4]
    """ + timer(6) + f"mov r4, r6\nmov r0, #7\nbl {BASE + SPAWN:#x}\n" + assign(0x10DD))
    result[0x10DD] = phase(0x10DD, f"""
        ldr r1, ={SECOND_FLAGS:#x}
        ldrh r2, [r1]
        tst r2, #0x10
        beq done
        bic r2, r2, #0x10
        strh r2, [r1]
        ldrsh r0, [r4, #0x50]
        cmp r0, #0
        blt finish
        sub r2, r0, #1
        strh r2, [r4, #0x50]
        ldr r1, ={SECOND_PLAYER:#x}
        ldr r4, [r1]
        bl {BASE + SPAWN:#x}
        b done
    finish:
    """ + word_modify(FLAGS, set_bits=0x20) + f"""
        mov r8, #0
        mov r9, #2
        mov r10, #0
        bl {SOUND:#x}
        bl {BASE + AUDIO_PRELUDE:#x}
    """ + timer(32) + assign(0x11F7) + f"bl {BASE + PHASES[0x11F7]:#x}\n")
    result[0x11F7] = phase(0x11F7, f"ldrh r0, [r4, #0x50]\nbl {BASE + TO_WHITE:#x}\n" +
        countdown() + "bne done\n" + word_modify(FLAGS, clear_bits=0x20) +
        f"bl 0x0801565C\nbl {initializer:#x}\n" + timer(32) + assign(0x1267))
    result[0x1267] = phase(0x1267, "ldrh r0, [r4, #0x50]\nbl 0x085C1D00\n" +
        countdown() + "bne done\n" + timer(150) + assign(0x12C6))
    result[0x12C6] = phase(0x12C6, countdown() + f"""
        beq restore
        cmp r0, #130
        bne done
        mov r8, #0x5C
        mov r9, #2
        mov r10, #0
        bl {SOUND:#x}
        b done
    restore:
    """ + timer(32) + assign(0x1331))
    result[0x1331] = phase(0x1331, "ldrh r0, [r4, #0x50]\nbl 0x085C1F00\n" +
        countdown() + f"""
        bne done
        ldr r1, ={FIRST_PLAYER:#x}
        ldr r5, [r1]
        ldrh r0, [r5, #6]
        bic r0, r0, #0x40
        strh r0, [r5, #6]
    """ + assign(0x139C))
    result[0x139C] = phase(0x139C, f"""
        ldr r1, ={BLINK:#x}
        ldrb r0, [r1]
        eor r0, r0, #7
        strb r0, [r1]
        ldr r2, ={FIRST_PLAYER:#x}
        ldr r5, [r2]
        ldrh r2, [r5, #6]
        tst r2, #0x800
        beq done
        bic r0, r0, #7
        strb r0, [r1]
    """ + timer(30) + word_modify(FLAGS, clear_bits=0x10) + assign(0x13F4))
    result[0x13F4] = phase(0x13F4, countdown() + "bne done\n" +
        word_modify(SHOOT_FLAGS, set_bits=1) + assign(0x1434))
    result[0x1434] = phase(0x1434, f"""
        ldr r1, ={SHOOT_FLAGS:#x}
        ldrh r0, [r1]
        tst r0, #2
        beq done
        ldrh r0, [r4, #0x54]
        ldr r1, ={FIRST_PLAYER:#x}
        ldr r5, [r1]
        strh r0, [r5, #0x64]
        mov r0, #0
        strh r0, [r4, #0x50]
        strh r0, [r4, #0x52]
    """ + assign(0x1486))
    result[0x1486] = phase(0x1486, f"""
        ldr r1, ={FIRST_PLAYER:#x}
        ldr r5, [r1]
        ldrh r0, [r5, #0x64]
        cmp r0, #0
        beq complete
        ldrh r0, [r4, #0x52]
        cmp r0, #0
        bne draw
        mov r8, #0x5A
        mov r9, #1
        mov r10, #0
        bl {SOUND:#x}
        ldrh r0, [r4, #0x50]
        add r0, r0, #1
        strh r0, [r4, #0x50]
        ldrh r0, [r4, #0x50]
        mov r1, #30
        strh r1, [r4, #0x52]
        ldrh r1, [r5, #0x64]
        cmp r1, r0
        bhi draw
    complete:
    """ + timer(20) + assign(0x1540) + word_modify(FLAGS, set_bits=0x400) + f"""
        b done
    draw:
        ldrh r0, [r4, #0x52]
        sub r0, r0, #1
        strh r0, [r4, #0x52]
        ldrh r0, [r4, #0x50]
        cmp r0, #0
        blne {BASE + DRAW_ICONS:#x}
    """)
    result[0x1540] = phase(0x1540, countdown() + "bne done\n" +
        word_modify(SHOOT_FLAGS, set_bits=4) + """
        ldr r1, =0x03004510
        ldr r1, [r1]
        ldr r2, =0x08374FF4
        str r2, [r1]
        ldr r1, =0x03004514
        ldr r1, [r1]
        ldr r2, =0x083735BC
        str r2, [r1]
        bl 0x08012030
    """)
    return result


def spawn() -> tuple[bytes, int]:
    """Source15C9: r4=parent, r0=source table index0..7, preserve all."""
    return pack_code(f"""
        push {{r0-r12, lr}}
        mov r11, #0
        mov r6, r4
        ldr r7, [r6, #0x18]
        ldr r8, ={OBJECT_HANDLE:#x}
        push {{r8}}
        push {{r11}}
        push {{r11}}
        push {{r11}}
        mov r8, #0x100
        orr r8, r8, #0xB
        push {{r8}}
        mov r8, #1
        push {{r8}}
        mov r8, #2
        push {{r8}}
        bl 0x08352374
        add sp, sp, #28
        ldr r12, [sp]
        ldr r8, ={OBJECT_HANDLE:#x}
        ldr r4, [r8]
        mov r0, #1
        strb r0, [r4, #0x10]
        str r6, [r4, #0x14]
        str r7, [r4, #0x18]
        ldr r1, ={BASE + POSITIONS:#x}
        add r1, r1, r12, lsl #2
        ldrh r0, [r1]
        strh r0, [r4, #0x34]
        ldrh r0, [r1, #2]
        strh r0, [r4, #0x36]
        mov r0, #8
        strh r0, [r4, #0x52]
        mov r0, #16
        strh r0, [r4, #0x54]
        add r5, r4, #0xAC
        push {{r5}}
        push {{r11}}
        ldr r8, ={P1:#x}
        push {{r8}}
        push {{r11}}
        push {{r11}}
        ldr r8, ={P0:#x}
        push {{r8}}
        push {{r11}}
        push {{r11}}
        ldr r8, ={P2:#x}
        push {{r8}}
        push {{r11}}
        push {{r11}}
        mov r8, #0x4000
        push {{r8}}
        mov r8, #0x1800
        push {{r8}}
        mov r8, #0x99
        push {{r8}}
        push {{r11}}
        bl 0x080127E4
        add sp, sp, #60
        ldrh r0, [r5, #8]
        orr r0, r0, #0x2000
        strh r0, [r5, #8]
        str r4, [r6, #0x20]
        mov r0, #0
        strh r0, [r4, #0x42]
        strh r0, [r4, #0x44]
        mov r0, #1
        strh r0, [r4, #0x64]
        push {{r5}}
        push {{r11}}
        mov r8, #5
        push {{r8}}
        bl 0x08012874
        add sp, sp, #12
        ldr r8, ={BASE + INITIAL:#x}
        str r8, [r4]
        pop {{r0-r12, lr}}
        bx lr
    """, SPAWN)


def initial() -> tuple[bytes, int]:
    return pack_code(f"""
        push {{r0-r12, lr}}
        ldr r1, [r4, #0x14]
        ldrsh r0, [r1, #0x34]
        ldrsh r2, [r4, #0x34]
        cmp r0, r2
        mvnge r0, #27
        strhge r0, [r4, #0xA0]
        ldr r8, ={BASE + HOMING:#x}
        str r8, [r4]
        bl {BASE + HOMING:#x}
        pop {{r0-r12, lr}}
        bx lr
    """, INITIAL)


def homing() -> tuple[bytes, int]:
    return pack_code(f"""
        push {{r0-r12, lr}}
        mov r11, #0
        ldr r1, [r4, #0x14]
        ldrsh r0, [r1, #0x34]
        ldrsh r2, [r4, #0x34]
        sub r0, r0, r2
        lsl r0, r0, #16
        asr r0, r0, #16
        ldrsh r3, [r1, #0x36]
        ldrsh r2, [r4, #0x36]
        sub r3, r3, r2
        lsl r3, r3, #16
        asr r3, r3, #16
        push {{r3}}
        push {{r0}}
        bl 0x08012560
        add sp, sp, #8
        ldrh r2, [r4, #0xA0]
        add r3, r0, r2
        push {{r3}}
        bl 0x0801233C
        add sp, sp, #4
        lsl r0, r0, #2
        strh r0, [r4, #0x42]
        push {{r3}}
        bl 0x08012348
        add sp, sp, #4
        lsl r0, r0, #2
        strh r0, [r4, #0x44]
        ldrsh r0, [r1, #0x34]
        sub r0, r0, #0x100
        lsl r0, r0, #16
        asr r0, r0, #16
        ldrsh r2, [r4, #0x34]
        cmp r0, r2
        bgt done
        add r0, r0, #0x200
        lsl r0, r0, #16
        asr r0, r0, #16
        cmp r0, r2
        blt done
        ldrsh r0, [r1, #0x36]
        sub r0, r0, #0x100
        lsl r0, r0, #16
        asr r0, r0, #16
        ldrsh r2, [r4, #0x36]
        cmp r0, r2
        bgt done
        add r0, r0, #0x200
        lsl r0, r0, #16
        asr r0, r0, #16
        cmp r0, r2
        blt done
    """ + word_modify(SECOND_FLAGS, set_bits=0x10) + """
        push {r4}
        push {r11}
        bl 0x083524C4
        add sp, sp, #8
    done:
        pop {r0-r12, lr}
        bx lr
    """, HOMING)


def to_white() -> tuple[bytes, int]:
    channels = []
    for shift in (0, 5, 10):
        channels.append(f"""
            {'mov r5, r3' if shift == 0 else f'lsr r5, r3, #{shift}'}
            and r5, r5, #31
            cmp r5, #31
            beq channel_{shift}
            cmp r5, #0
            moveq r5, #3
            addne r5, r5, #2
            cmp r5, #31
            movhi r5, #31
        channel_{shift}:
            orr r4, r4, r5, lsl #{shift}
        """)
    return pack_code("""
        push {r0-r12, lr}
        and r7, r0, #1
        mov r1, #0x05000000
        add r1, r1, r7, lsl #9
        mov r2, #128
    colors:
        ldrh r3, [r1]
        mov r4, #0
    """ + "\n".join(channels) + """
        strh r4, [r1], #2
        subs r2, r2, #1
        bne colors
        cmp r7, #0
        beq canonical_zero
        sub r1, r1, #0x100
        sub r2, r1, #0x100
        mov r3, #8
    aliases:
        ldrh r4, [r1], #0x20
        strh r4, [r2], #0x20
        subs r3, r3, #1
        bne aliases
    canonical_zero:
        mov r1, #0x05000000
        ldr r4, =0x7FFF
        strh r4, [r1]
        pop {r0-r12, lr}
        bx lr
    """, TO_WHITE)


def capture_black() -> tuple[bytes, int]:
    return pack_code("""
        push {r0-r12, lr}
        ldr r1, =0x0203F000
        mov r0, #0
        strh r0, [r1]
        bl 0x085C1900
        mov r1, #0x05000000
        mov r2, #128
    bg:
        strh r0, [r1], #2
        subs r2, r2, #1
        bne bg
        mov r2, #8
    high_zero:
        strh r0, [r1], #0x20
        subs r2, r2, #1
        bne high_zero
        mov r2, #128
    obj:
        strh r0, [r1], #2
        subs r2, r2, #1
        bne obj
        mov r1, #0x05000000
        ldr r0, =0x7FFF
        strh r0, [r1]
        pop {r0-r12, lr}
        bx lr
    """, CAPTURE_BLACK)


def draw_icons() -> tuple[bytes, int]:
    """Source150E uses exactly the native HUD producer's tile/palette/coords."""
    return pack_code("""
        push {r0-r12, lr}
        mov r2, r0
        ldr r8, =0x030012CA
        ldrb r0, [r8]
        ldr r12, =0x03001428
        add r12, r12, r0, lsl #3
        mov r7, #11
        mov r6, #20
        ldr r9, =0x67FC
    next_icon:
        strh r9, [r12, #4]
        strh r7, [r12, #2]
        add r7, r7, #10
        strh r6, [r12], #8
        add r0, r0, #1
        subs r2, r2, #1
        bne next_icon
        strb r0, [r8]
        pop {r0-r12, lr}
        bx lr
    """, DRAW_ICONS)


def audio_prelude() -> tuple[bytes, int]:
    """Eight original channel/side requests on the retail GBA backend.

    The existing 080158C8 is a retail BX LR backend. Its no-op behavior is
    proved by source/native caller lineage, not substituted by this layer.
    """
    return pack_code("""
        push {r0-r12, lr}
        mov r11, #0
        mov r6, #0
        mov r7, #32
    channel:
        push {r6}
        mov r8, #1
        push {r8}
        push {r11}
        push {r7}
        push {r11}
        bl 0x080158C8
        add sp, sp, #20
        push {r6}
        push {r11}
        push {r11}
        push {r7}
        push {r11}
        bl 0x080158C8
        add sp, sp, #20
        add r6, r6, #1
        cmp r6, #4
        bne channel
        pop {r0-r12, lr}
        bx lr
    """, AUDIO_PRELUDE)


def make_rows(dependencies: dict) -> list[tuple[int, bytes, int, str]]:
    generated = phases(dependencies["initializer"]["entry"])
    rows = [(PHASES[source], blob, code, f"source_{source:04X}") for source, (blob, code) in generated.items()]
    for start, function, label in ((SPAWN, spawn, "source_15C9"), (INITIAL, initial, "source_16BA"),
                                  (HOMING, homing, "source_16D4"), (TO_WHITE, to_white, "source_1F7B"),
                                  (CAPTURE_BLACK, capture_black, "source_1073_capture_black"),
                                  (DRAW_ICONS, draw_icons, "source_150E_icons"),
                                  (AUDIO_PRELUDE, audio_prelude, "source_1151_audio")):
        blob, code = function()
        rows.append((start, blob, code, label))
    rows.append((POSITIONS, b"".join(struct.pack("<2H", *point) for point in POINTS), 0, "source_15A9_positions"))
    rows.sort()
    for i, (start, blob, code, label) in enumerate(rows):
        bound = rows[i + 1][0] if i + 1 < len(rows) else END
        if start + len(blob) > bound:
            raise ValueError(f"scene placement overflow: {label}")
    return rows


def validate_dependencies(before: bytes, dependencies: dict) -> None:
    if set(dependencies) != {"input_sha256", "initializer"}:
        raise ValueError("scene requires the real full initializer dependency")
    require_hash(before, dependencies["input_sha256"], "exact scene predecessor")
    for name in ("initializer",):
        item = dependencies[name]
        address, count = item["entry"], item["bytes"]
        raw = address - BASE
        if address & 3 or count < 8 or raw < 0 or raw + count > len(before) or START <= raw < END:
            raise ValueError(f"invalid real native dependency {name}")
        require_hash(before[raw:raw + count], item["sha256"], name)
        if before[raw:raw + 4] in (bytes.fromhex("1EFF2FE1"), b"\xff" * 4):
            raise ValueError(f"placeholder is not a native dependency: {name}")


def build(before: bytes, sources: dict[str, bytes], dependencies: dict) -> tuple[bytes, dict]:
    for key, expected in (("gba", GBA_SHA256), ("wsc10", WSC10_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], expected, key)
    for key, start, end, expected in SOURCE_GUARDS:
        require_hash(sources[key][start:end], expected, f"{key} scene source/consumer {start:X}")
    validate_dependencies(before, dependencies)
    if len(before) != 0x800000 or before[START:END] != b"\xff" * (END - START):
        raise ValueError("scene expansion is not wholly free in this predecessor")
    for site in range(0, len(before) - 3, 4):
        word = struct.unpack_from("<I", before, site)[0]
        if BASE + START <= word < BASE + END:
            raise ValueError(f"existing pointer reaches scene reservation at {site:X}")
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            if START <= site + 8 + delta * 4 < END:
                raise ValueError(f"existing ARM branch reaches scene reservation at {site:X}")
    resources = presentation_resources(sources["wsc15"], sources["wsc10"], sources["gba"])
    if sources["wsc15"][0x7734A9:0x7734C9] != b"".join(struct.pack("<2H", *p) for p in POINTS):
        raise ValueError("source spawn positions changed")
    for start, end in ((0x350248, 0x352268), (0x127E4, 0x1285C), (0x12874, 0x12DB8),
                       (0x1233C, 0x126F8), (0x352374, 0x352AC8), (0x12008, 0x12058),
                       (0xD15C0, 0xD15F0), (0x370124, 0x37016C),
                       (0x1565C, 0x15810), (0x158C8, 0x158CC)):
        if before[start:end] != sources["gba"][start:end]:
            raise ValueError(f"retail scene dependency changed at {start:X}")
    rows = make_rows(dependencies)
    entries = {BASE + row[0] for row in rows if row[2]}
    external = ({0x0801201C, 0x08012008, 0x08012030, 0x083524C4, 0x08352374,
                0x080127E4, 0x08012874, 0x08012560, 0x0801233C, 0x08012348,
                SOUND, 0x085C1900, 0x085C1D00, 0x085C1F00, 0x0801565C, 0x080158C8} |
                entries | {dependencies["initializer"]["entry"]})
    output = bytearray(before)
    plan, machines, allowed = [], {}, set()
    for start, blob, code, label in rows:
        if code:
            machines[label] = verify_machine_code(blob, start, code, external)
        output[start:start + len(blob)] = blob
        allowed.update(range(start, start + len(blob)))
        plan.append({"offset": start, "bytes": len(blob), "code_bytes": code, "label": label,
                     "before_sha256": sha256(b"\xff" * len(blob)), "after_sha256": sha256(blob)})
    changed = {i for i, (a, b) in enumerate(zip(before, output, strict=True)) if a != b}
    if not changed or not changed <= allowed:
        raise ValueError("scene Expected Write diff is not exact")
    report = {"schema": 1, "kind": "shoot-scene-native-resident-translation",
              "input_sha256": sha256(before), "output_sha256": sha256(output),
              "output_bytes": len(output), "expected_writes": plan,
              "generated_code": machines, "dependencies": dependencies,
              "resources": resources, "actual_changed_bytes": len(changed),
              "external_hook_installed": False, "new_scene_allocations": 0,
              "new_ram_globals": [], "native_scene_data_bytes": 0x100,
              "scene_locals": {"timer": 0x50, "delay": 0x52, "saved_hp": 0x54},
              "abi": "scheduler current task; all r0-r12/LR/SP preserved; flags clobbered",
              "source_counters_retained": [151, 200, 5, 100, 6, 32, 150, 30, 20],
              "claim_scope": "resident source scene and presentation graph only; no external root hook, runtime or save QA"}
    return bytes(output), report


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "dependencies", "output"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    sources = {key: getattr(args, key).read_bytes() for key in ("gba", "wsc10", "wsc15")}
    output, report = build(args.input.read_bytes(), sources, json.loads(args.dependencies.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-scene] static resident build {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
