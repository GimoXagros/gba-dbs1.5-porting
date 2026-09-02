#!/usr/bin/env python3
"""Install the resident Digimon Shoot upper player-state graph.

The graph is deliberately not connected to the menu or initializer in this
layer.  Calls that reach the still-unported 4090:9908 rules controller target a
resident BX-LR boundary stub; a later guarded layer must replace that stub and
connect the initializer atomically.
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
sys.path.insert(0, str(SCRIPT_DIR))

from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks  # type: ignore

from convert_wsc_palette_block import convert_block, convert_color  # type: ignore


INPUT_SHA256 = "C8C3AF5DABBE7CCE9F0D124DDEEF3CD6348FCDB085416DBA5E78C65DD5BFB3B4"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OWNERSHIP_START = 0x5BC800
OWNERSHIP_END = 0x5C1000

STATE_7792 = 0x5BC800
STATE_7803 = 0x5BCA00
STATE_7836 = 0x5BCC00
STATE_7893 = 0x5BCE00
STATE_78F0 = 0x5BD000
STATE_794D = 0x5BD200
STATE_7996 = 0x5BD400
STATE_7A19 = 0x5BD700
STATE_7A41 = 0x5BD900
STATE_7A79 = 0x5BDB00
STATE_7AB1 = 0x5BDD00
STATE_7B1B = 0x5BE000
STATE_7B3A = 0x5BE200
STATE_7BFF = 0x5BE600
STATE_7C64 = 0x5BEA00
STATE_7CE5 = 0x5BEE00
STATE_7D7C = 0x5BF200
STATE_7D8D = 0x5BF204
STATE_7DA9 = 0x5BF400
STATE_7DD8 = 0x5BF600
STATE_7DD9 = 0x5BF800
STATE_7E8D = 0x5BFC00
STATE_7EBB = 0x5C0000
STATE_8069 = 0x5C0600
STATE_809C = 0x5C0800
CONTROLLER_BOUNDARY = 0x5C0A00
P2_VARIANT_3 = 0x5C0B00
INTRO_BG_PALETTE = 0x5C0C00
TARGET_TABLE = 0x5C0D00

PRESENTATION_EVENT = 0x08012874
PRESENTATION_UPDATE = 0x08012A84
TRIG_X = 0x0801233C
TRIG_Y = 0x08012348
RNG = 0x08012600
P2_LOADER = 0x080132EC
SOUND_REQUEST = 0x080D15C0
SHOOT_FLAGS = 0x0300450A
P2_VARIANT_0 = 0x08587100
P2_VARIANT_1 = 0x08587128
P2_VARIANT_2 = 0x08587150

WSC_RANGES = {
    "upper_main": (0x748092, 0x74867D, "46FF062CBF19229B16A48C1FAEA64B09042C2CE79889CC851496B65EE991A098"),
    "upper_second": (0x74868D, 0x7486BE, "25A0BE0C607054F3C7051444B5418EE66B85413B8828AFD29F568F1E95BD2491"),
    "upper_shared": (0x7486D8, 0x7489CB, "71CAF3C450D363D6F0D05A9B65A3C8E5FA5232739F75E2EED668C621CD6820FF"),
    "intro_palette": (0x7491F8, 0x7492D8, "8E6C0695DEE2B90AF2A74DF35FD1FCCB9EF05E4C5E3954D519308E3640BC8390"),
    "target_table": (0x7489CC, 0x748A0C, "C7CF22F2C66285C53CE7B00F78284C82D8E6D29C5238002D5D71522C6A9836ED"),
    "p2_variant_3": (0x3D4B92, 0x3D4BB8, "CDB85BE76FA8020711EE525F1EBC4EDCA0372E484F0E10D1A66E8EEB7AE84CD4"),
}

P2_VARIANT_3_SHA256 = "829EB7173630790AA6266A53A0C4AB43BF98D9ED1B5964E8037E6311F693D793"
INTRO_BG_PALETTE_SHA256 = "7176D11049581343B4A2BB1A3A451592851D9E7F903207041268B1E8EFA1C1D2"


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


def build_7792() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldr r8, shoot_flags
        ldrh r9, [r8]
        tst r9, #1
        beq done
        ldr r1, [r4, #0x18]
        ldrsh r8, [r1, #0x34]
        strh r8, [r4, #0x34]
        mov r0, #0xC1
        push {{r0}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        add r0, r0, r0, lsl #1
        ldr r1, [r4, #0x18]
        ldrsh r8, [r1, #0x36]
        add r0, r0, r8
        strh r0, [r4, #0x36]
        ldrh r8, [r4, #4]
        bic r8, r8, #0x20
        strh r8, [r4, #4]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        mov r8, #0x4A
        mov r9, #1
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7803:08X}
    """, STATE_7792)


def build_7803() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r5, #0xA]
        tst r8, #0x2000
        beq done
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        mov r8, #60
        strh r8, [r4, #0x94]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7836:08X}
    """, STATE_7803)


def build_timed_palette_state(offset: int, next_state: int, palette: int) -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        strh r8, [r4, #0x94]
        cmp r8, #0
        bne done
        ldr r8, palette
        push {{r8}}
        mov r9, #0
        push {{r9}}
        push {{r9}}
        push {{r9}}
        mov r9, #1
        push {{r9}}
        bl 0x{P2_LOADER:08X}
        add sp, sp, #20
        mov r8, #0x5B
        mov r9, #1
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        mov r8, #60
        strh r8, [r4, #0x94]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    palette: .word 0x{palette:08X}
    next_state: .word 0x{GBA_BASE + next_state:08X}
    """, offset)


def build_794d() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        strh r8, [r4, #0x94]
        cmp r8, #0
        bne done
        mov r8, #0xC2
        strh r8, [r4, #0x94]
        mov r8, #0
        strh r8, [r4, #0x46]
        mov r8, #0x5C
        mov r9, #2
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7996:08X}
    """, STATE_794D)


def build_7996() -> bytes:
    return assemble_arm(f"""
        push {{r6-r7, lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldr r7, [r4, #0x18]
        ldrh r6, [r4, #0x94]
        push {{r6}}
        bl 0x{TRIG_Y:08X}
        add sp, sp, #4
        add r0, r0, r0, lsl #1
        ldrsh r8, [r7, #0x36]
        add r0, r0, r8
        strh r0, [r4, #0x36]
        push {{r6}}
        bl 0x{TRIG_X:08X}
        add sp, sp, #4
        add r0, r0, r0, lsl #1
        ldrsh r8, [r7, #0x34]
        add r0, r0, r8
        strh r0, [r4, #0x34]
        add r6, r6, #1
        ldrh r8, [r4, #0x46]
        add r8, r8, #1
        cmp r8, #4
        addeq r6, r6, #1
        moveq r8, #0
        and r6, r6, #0xFF
        strh r6, [r4, #0x94]
        strh r8, [r4, #0x46]
        cmp r6, #0xC1
        bne done
        mov r8, #60
        strh r8, [r4, #0x94]
        mov r8, #0x5C
        mov r9, #2
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{r6-r7, lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7A19:08X}
    """, STATE_7996)


def build_7a19() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        strh r8, [r4, #0x94]
        cmp r8, #0
        bne done
        mov r8, #0
        strh r8, [r4, #0x42]
        mov r8, #0x80
        rsb r8, r8, #0
        strh r8, [r4, #0x44]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7A41:08X}
    """, STATE_7A19)


def build_7a41() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0x36]
        cmp r8, #0xE00
        bhs done
        ldr r8, shoot_flags
        ldrh r9, [r8]
        bic r9, r9, #1
        orr r9, r9, #2
        strh r9, [r8]
        mov r9, #0
        strh r9, [r4, #0x44]
        ldr r9, next_state
        str r9, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7A79:08X}
    """, STATE_7A41)


def build_7a79() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldr r8, shoot_flags
        ldrh r9, [r8]
        tst r9, #4
        beq done
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]
        bl 0x{RNG:08X}
        and r0, r0, #0x3F
        add r0, r0, #0x4B
        strh r0, [r4, #0x94]
        mov r8, #0
        strh r8, [r4, #0x46]
        strh r8, [r4, #0xA0]
        strh r8, [r4, #0xA2]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7DD9:08X}
    """, STATE_7A79)


def build_7ab1() -> bytes:
    return assemble_arm(f"""
        push {{r6-r7, lr}}
        mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        strh r8, [r4, #0x46]
        strh r8, [r4, #0x48]
        strh r8, [r4, #0x94]
        strh r8, [r4, #0x96]
        mov r8, #0x10
        strh r8, [r4, #0xA0]
        strh r8, [r4, #0xA2]
        mov r8, #121
        strh r8, [r4, #0xA4]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r6, palette_table
        add r6, r6, #2
        ldr r7, palette_ram
        add r7, r7, #2
        mov r8, #7
    palette_rows:
        mov r9, #15
    palette_words:
        ldrh r10, [r6], #2
        strh r10, [r7], #2
        subs r9, r9, #1
        bne palette_words
        add r6, r6, #2
        add r7, r7, #2
        subs r8, r8, #1
        bne palette_rows
        ldr r8, next_state
        str r8, [r4]
        pop {{r6-r7, lr}}
        bx lr
        .align 2
    palette_table: .word 0x{GBA_BASE + INTRO_BG_PALETTE:08X}
    palette_ram: .word 0x05000000
    next_state: .word 0x{GBA_BASE + STATE_7B1B:08X}
    """, STATE_7AB1)


def build_7b1b() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0xA4]
        sub r8, r8, #1
        strh r8, [r4, #0xA4]
        cmp r8, #0
        bne done
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7B3A:08X}
    """, STATE_7B1B)


def oscillation_body() -> str:
    return """
        ldrh r8, [r4, #0x94]
        tst r8, #3
        bne oscillate_y
        ldrsh r9, [r4, #0xA0]
        rsb r10, r9, #0
        strh r10, [r4, #0xA0]
        ldrsh r10, [r4, #0x34]
        add r10, r10, r9
        strh r10, [r4, #0x34]
    oscillate_y:
        add r8, r8, #1
        and r8, r8, #3
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x96]
        tst r8, #3
        bne oscillate_done
        ldrsh r9, [r4, #0xA2]
        rsb r10, r9, #0
        strh r10, [r4, #0xA2]
        ldrsh r10, [r4, #0x36]
        add r10, r10, r9
        strh r10, [r4, #0x36]
    oscillate_done:
        add r8, r8, #1
        and r8, r8, #3
        strh r8, [r4, #0x96]
    """


def build_7b3a() -> bytes:
    body = oscillation_body()
    return assemble_arm(f"""
        push {{r11, lr}}
        {body}
        mov r11, #0
        ldrsh r8, [r4, #0x34]
        cmp r8, #0xDE0
        blt x_left
        cmp r8, #0xE20
        movge r9, #0x80
        rsbge r9, r9, #0
        strhge r9, [r4, #0x42]
        bge y_bounds
        b x_inside
    x_left:
        mov r9, #0x80
        strh r9, [r4, #0x42]
    x_inside:
        cmp r8, #0xDC0
        blt y_bounds
        cmp r8, #0xE40
        addle r11, r11, #1
    y_bounds:
        ldrsh r8, [r4, #0x36]
        mov r10, #0x16
        lsl r10, r10, #8
        add r10, r10, #0xE0
        cmp r8, r10
        blt y_up
        add r10, r10, #0x40
        cmp r8, r10
        movge r9, #0x80
        rsbge r9, r9, #0
        strhge r9, [r4, #0x44]
        bge incomplete
        b y_inside
    y_up:
        mov r9, #0x80
        strh r9, [r4, #0x44]
    y_inside:
        cmp r8, #0x16C0
        blt incomplete
        cmp r8, #0x1740
        addle r11, r11, #1
    incomplete:
        strh r11, [r4, #0xA4]
        cmp r11, #2
        bne done
        mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        strh r8, [r4, #0x46]
        strh r8, [r4, #0x48]
        ldr r8, shoot_flags
        ldrh r9, [r8]
        orr r9, r9, #0x100
        strh r9, [r8]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{r11, lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7BFF:08X}
    """, STATE_7B3A)


def build_7bff() -> bytes:
    body = oscillation_body()
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        {body}
        ldr r8, shoot_flags
        ldrh r9, [r8]
        tst r9, #0x100
        bne done
        mov r8, #60
        strh r8, [r4, #0x98]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7C64:08X}
    """, STATE_7BFF)


def build_7c64() -> bytes:
    body = oscillation_body()
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        {body}
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
        cmp r8, #0
        bne done
        mov r8, #150
        strh r8, [r4, #0x98]
        mov r8, #0
        strh r8, [r4, #0x46]
        mov r8, #0x5C
        mov r9, #2
        mov r10, #0
        bl 0x{SOUND_REQUEST:08X}
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7CE5:08X}
    """, STATE_7C64)


def build_7ce5() -> bytes:
    body = oscillation_body()
    return assemble_arm(f"""
        push {{lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        {body}
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        ldrh r9, [r4, #0x46]
        add r9, r9, #1
        cmp r9, #4
        subeq r8, r8, #1
        moveq r9, #0
        strh r8, [r4, #0x98]
        strh r9, [r4, #0x46]
        cmp r8, #0
        ble complete
        ldrh r9, [r4, #4]
        eor r9, r9, #0x20
        strh r9, [r4, #4]
        mov r0, r8, lsr #3
        and r0, r0, #3
        adr r9, palettes
        ldr r8, [r9, r0, lsl #2]
        push {{r8}}
        mov r9, #0
        push {{r9}}
        push {{r9}}
        push {{r9}}
        mov r9, #1
        push {{r9}}
        bl 0x{P2_LOADER:08X}
        add sp, sp, #20
        b done
    complete:
        mov r8, #0
        strh r8, [r4, #0x46]
        ldr r8, shoot_flags
        ldrh r9, [r8]
        orr r9, r9, #0x100
        strh r9, [r8]
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    palettes:
        .word 0x{P2_VARIANT_0:08X}
        .word 0x{P2_VARIANT_1:08X}
        .word 0x{P2_VARIANT_2:08X}
        .word 0x{GBA_BASE + P2_VARIANT_3:08X}
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    next_state: .word 0x{GBA_BASE + STATE_7D7C:08X}
    """, STATE_7CE5)


def build_7d8d() -> bytes:
    return assemble_arm(f"""
        mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        strh r8, [r4, #0x46]
        strh r8, [r4, #0x48]
        mov r8, #60
        strh r8, [r4, #0x94]
        ldr r8, next_state
        str r8, [r4]
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7DA9:08X}
    """, STATE_7D8D)


def build_7da9() -> bytes:
    return assemble_arm(f"""
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        strh r8, [r4, #0x94]
        cmp r8, #0
        bxne lr
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]
        ldr r8, next_state
        str r8, [r4]
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7DD8:08X}
    """, STATE_7DA9)


def build_7dd9() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r4, #4]
        tst r8, #0x20
        beq resume_move
        bic r8, r8, #0x20
        strh r8, [r4, #4]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        bl 0x{RNG:08X}
        and r0, r0, #7
        ldr r8, targets
        add r8, r8, r0, lsl #3
        ldrsh r9, [r8]
        strh r9, [r4, #0x34]
        strh r9, [r4, #0xA4]
        ldrsh r9, [r8, #2]
        strh r9, [r4, #0x36]
        strh r9, [r4, #0xA6]
        ldrsh r9, [r8, #4]
        strh r9, [r4, #0xA8]
        ldrsh r9, [r8, #6]
        strh r9, [r4, #0xAA]
        mov r9, #0
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        strh r9, [r4, #0x96]
        ldrsh r9, [r4, #0xA4]
        ldrsh r10, [r4, #0xA8]
        sub r9, r9, r10
        asr r9, r9, #1
        add r9, r9, r10
        strh r9, [r4, #0x9A]
        ldrsh r9, [r4, #0xA6]
        ldrsh r10, [r4, #0xAA]
        sub r9, r9, r10
        asr r9, r9, #1
        add r9, r9, r10
        strh r9, [r4, #0x9C]
        ldr r8, wait_state
        str r8, [r4]
        bl 0x{GBA_BASE + STATE_7E8D:08X}
        b done
    resume_move:
        ldrb r8, [r5, #0xE]
        cmp r8, #1
        beq set_move
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
    set_move:
        ldr r8, move_state
        str r8, [r4]
        bl 0x{GBA_BASE + STATE_7EBB:08X}
    done:
        pop {{lr}}
        bx lr
        .align 2
    targets: .word 0x{GBA_BASE + TARGET_TABLE:08X}
    wait_state: .word 0x{GBA_BASE + STATE_7E8D:08X}
    move_state: .word 0x{GBA_BASE + STATE_7EBB:08X}
    """, STATE_7DD9)


def build_7e8d() -> bytes:
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
        b done
    complete:
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7EBB:08X}
    """, STATE_7E8D)


def build_7ebb() -> bytes:
    return assemble_arm(f"""
        push {{r11, lr}}
        mov r11, #0
        ldrsh r8, [r4, #0xA8]
        ldrsh r9, [r4, #0xA4]
        cmp r8, r9
        beq x_reached
        blt x_negative
        ldrsh r10, [r4, #0x34]
        cmp r8, r10
        ble x_reached
        ldrsh r9, [r4, #0x9A]
        cmp r10, r9
        bgt x_positive_decel
        ldrsh r9, [r4, #0x42]
        add r9, r9, #2
        cmp r9, #0x300
        movgt r9, #0x300
        cmp r9, #0x80
        movlt r9, #0x80
        strh r9, [r4, #0x42]
        b y_axis
    x_positive_decel:
        ldrsh r9, [r4, #0x42]
        sub r9, r9, #2
        cmp r9, #0x300
        movgt r9, #0x300
        cmp r9, #0x80
        movlt r9, #0x80
        strh r9, [r4, #0x42]
        b y_axis
    x_negative:
        ldrsh r10, [r4, #0x34]
        cmp r8, r10
        bge x_reached
        ldrsh r9, [r4, #0x9A]
        cmp r10, r9
        blt x_negative_decel
        ldrsh r9, [r4, #0x42]
        sub r9, r9, #2
        mov r10, #0x80
        rsb r10, r10, #0
        cmp r9, r10
        movgt r9, r10
        mov r10, #0x300
        rsb r10, r10, #0
        cmp r9, r10
        movlt r9, r10
        strh r9, [r4, #0x42]
        b y_axis
    x_negative_decel:
        ldrsh r9, [r4, #0x42]
        add r9, r9, #2
        mov r10, #0x80
        rsb r10, r10, #0
        cmp r9, r10
        movgt r9, r10
        mov r10, #0x300
        rsb r10, r10, #0
        cmp r9, r10
        movlt r9, r10
        strh r9, [r4, #0x42]
        b y_axis
    x_reached:
        orr r11, r11, #1
    y_axis:
        ldrsh r8, [r4, #0xAA]
        ldrsh r9, [r4, #0xA6]
        cmp r8, r9
        beq y_reached
        blt y_negative
        ldrsh r10, [r4, #0x36]
        cmp r8, r10
        ble y_reached
        ldrsh r9, [r4, #0x9C]
        cmp r10, r9
        bgt y_positive_decel
        ldrsh r9, [r4, #0x44]
        add r9, r9, #2
        cmp r9, #0x300
        movgt r9, #0x300
        cmp r9, #0x80
        movlt r9, #0x80
        strh r9, [r4, #0x44]
        b movement_done
    y_positive_decel:
        ldrsh r9, [r4, #0x44]
        sub r9, r9, #2
        cmp r9, #0x300
        movgt r9, #0x300
        cmp r9, #0x80
        movlt r9, #0x80
        strh r9, [r4, #0x44]
        b movement_done
    y_negative:
        ldrsh r10, [r4, #0x36]
        cmp r8, r10
        bge y_reached
        ldrsh r9, [r4, #0x9C]
        cmp r10, r9
        blt y_negative_decel
        ldrsh r9, [r4, #0x44]
        sub r9, r9, #2
        mov r10, #0x80
        rsb r10, r10, #0
        cmp r9, r10
        movgt r9, r10
        mov r10, #0x300
        rsb r10, r10, #0
        cmp r9, r10
        movlt r9, r10
        strh r9, [r4, #0x44]
        b movement_done
    y_negative_decel:
        ldrsh r9, [r4, #0x44]
        add r9, r9, #2
        mov r10, #0x80
        rsb r10, r10, #0
        cmp r9, r10
        movgt r9, r10
        mov r10, #0x300
        rsb r10, r10, #0
        cmp r9, r10
        movlt r9, r10
        strh r9, [r4, #0x44]
        b movement_done
    y_reached:
        orr r11, r11, #2
    movement_done:
        strh r11, [r4, #0x96]
        cmp r11, #3
        bne update
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #3
        push {{r8}}
        bl 0x{PRESENTATION_EVENT:08X}
        add sp, sp, #12
        mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        ldr r8, next_state
        str r8, [r4]
        b done
    update:
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x{PRESENTATION_UPDATE:08X}
        add sp, sp, #12
        ldrh r8, [r4, #0xA0]
        tst r8, #1
        bne done
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        ldrh r9, [r4, #0x46]
        add r9, r9, #1
        cmp r9, #4
        subeq r8, r8, #1
        moveq r9, #0
        strh r8, [r4, #0x94]
        strh r9, [r4, #0x46]
        cmp r8, #0
        bgt done
        mov r8, #0
        strh r8, [r4, #0x46]
        bl 0x{GBA_BASE + CONTROLLER_BOUNDARY:08X}
        bl 0x{RNG:08X}
        and r0, r0, #0x3F
        add r0, r0, #0x4B
        strh r0, [r4, #0x94]
    done:
        pop {{r11, lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_8069:08X}
    """, STATE_7EBB)


def build_8069() -> bytes:
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
        b done
    complete:
        bl 0x{RNG:08X}
        and r0, r0, #0xFF
        add r0, r0, #0x4B
        strh r0, [r4, #0x98]
        mov r8, #0
        strh r8, [r4, #0x48]
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_809C:08X}
    """, STATE_8069)


def build_809c() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        ldrh r9, [r4, #0x48]
        add r9, r9, #1
        cmp r9, #4
        subeq r8, r8, #1
        moveq r9, #0
        strh r8, [r4, #0x98]
        strh r9, [r4, #0x48]
        cmp r8, #0
        ble complete
        ldrh r8, [r4, #0xA0]
        tst r8, #1
        bne done
        ldrh r8, [r4, #0x94]
        sub r8, r8, #1
        ldrh r9, [r4, #0x46]
        add r9, r9, #1
        cmp r9, #4
        subeq r8, r8, #1
        moveq r9, #0
        strh r8, [r4, #0x94]
        strh r9, [r4, #0x46]
        cmp r8, #0
        bgt done
        mov r8, #0
        strh r8, [r4, #0x46]
        bl 0x{GBA_BASE + CONTROLLER_BOUNDARY:08X}
        bl 0x{RNG:08X}
        and r0, r0, #0x3F
        add r0, r0, #0x4B
        strh r0, [r4, #0x94]
        b done
    complete:
        mov r8, #0
        strh r8, [r4, #0x48]
        ldr r8, next_state
        str r8, [r4]
    done:
        pop {{lr}}
        bx lr
        .align 2
    next_state: .word 0x{GBA_BASE + STATE_7DD9:08X}
    """, STATE_809C)


def converted_p2_variant_3(wsc15: bytes) -> bytes:
    start, end, expected = WSC_RANGES["p2_variant_3"]
    source = wsc15[start:end]
    require_hash(source, expected, "WSC P2 variant 3")
    converted = bytearray(convert_block(source))
    converted[-2:] = source[:2]
    result = bytes(converted)
    require_hash(result, P2_VARIANT_3_SHA256, "native P2 variant 3")
    return result


def converted_intro_palette(wsc15: bytes) -> bytes:
    start, end, expected = WSC_RANGES["intro_palette"]
    source = wsc15[start:end]
    require_hash(source, expected, "WSC upper-state palette table")
    words = struct.unpack("<112H", source)
    converted = struct.pack(
        "<112H",
        *(0 if index % 16 == 0 else convert_color(value)
          for index, value in enumerate(words)),
    )
    require_hash(converted, INTRO_BG_PALETTE_SHA256, "native upper-state palette table")
    return converted


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
    require_hash(source, INPUT_SHA256, "v45 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    for label, (start, end, expected) in WSC_RANGES.items():
        require_hash(wsc15[start:end], expected, label)
    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (
        OWNERSHIP_END - OWNERSHIP_START
    ):
        raise SystemExit("Shoot upper-state ownership window is not blank")
    refs_before = aligned_pointer_refs(source, OWNERSHIP_START, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointers reach upper-state window: {refs_before}")

    placements = [
        (STATE_7792, build_7792(), "upper_7792"),
        (STATE_7803, build_7803(), "upper_7803"),
        (STATE_7836, build_timed_palette_state(STATE_7836, STATE_7893, P2_VARIANT_2), "upper_7836"),
        (STATE_7893, build_timed_palette_state(STATE_7893, STATE_78F0, P2_VARIANT_1), "upper_7893"),
        (STATE_78F0, build_timed_palette_state(STATE_78F0, STATE_794D, P2_VARIANT_0), "upper_78F0"),
        (STATE_794D, build_794d(), "upper_794D"),
        (STATE_7996, build_7996(), "upper_7996"),
        (STATE_7A19, build_7a19(), "upper_7A19"),
        (STATE_7A41, build_7a41(), "upper_7A41"),
        (STATE_7A79, build_7a79(), "upper_7A79"),
        (STATE_7AB1, build_7ab1(), "upper_7AB1"),
        (STATE_7B1B, build_7b1b(), "upper_7B1B"),
        (STATE_7B3A, build_7b3a(), "upper_7B3A"),
        (STATE_7BFF, build_7bff(), "upper_7BFF"),
        (STATE_7C64, build_7c64(), "upper_7C64"),
        (STATE_7CE5, build_7ce5(), "upper_7CE5"),
        (STATE_7D7C, assemble_arm("bx lr", STATE_7D7C), "upper_7D7C_idle"),
        (STATE_7D8D, build_7d8d(), "upper_7D8D"),
        (STATE_7DA9, build_7da9(), "upper_7DA9"),
        (STATE_7DD8, assemble_arm("bx lr", STATE_7DD8), "upper_7DD8_idle"),
        (STATE_7DD9, build_7dd9(), "upper_7DD9"),
        (STATE_7E8D, build_7e8d(), "upper_7E8D"),
        (STATE_7EBB, build_7ebb(), "upper_7EBB"),
        (STATE_8069, build_8069(), "upper_8069"),
        (STATE_809C, build_809c(), "upper_809C"),
        (CONTROLLER_BOUNDARY, assemble_arm("bx lr", CONTROLLER_BOUNDARY), "controller_9908_boundary"),
        (P2_VARIANT_3, converted_p2_variant_3(wsc15), "upper_p2_variant_3"),
        (INTRO_BG_PALETTE, converted_intro_palette(wsc15), "upper_intro_bg_palette"),
        (TARGET_TABLE, wsc15[WSC_RANGES["target_table"][0]:WSC_RANGES["target_table"][1]], "upper_target_table"),
    ]
    placements.sort()
    for (start, blob, label), (next_start, _next_blob, next_label) in zip(
        placements, placements[1:]
    ):
        if start + len(blob) > next_start:
            raise SystemExit(f"upper-state placements overlap: {label} / {next_label}")
    if placements[0][0] < OWNERSHIP_START or placements[-1][0] + len(placements[-1][1]) > OWNERSHIP_END:
        raise SystemExit("upper-state placement exceeds ownership window")

    output = bytearray(source)
    expected_writes = []
    allowed = set()
    for offset, blob, label in placements:
        before = bytes(output[offset:offset + len(blob)])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is no longer blank")
        output[offset:offset + len(blob)] = blob
        allowed.update(
            offset + index for index, (old, new) in enumerate(zip(before, blob))
            if old != new
        )
        expected_writes.append({
            "label": label,
            "offset": offset,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })
    changed = {
        index for index, (old, new) in enumerate(zip(source, output)) if old != new
    }
    if changed != allowed:
        raise SystemExit("actual writes exceed declared upper-state placements")

    result_bytes = bytes(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result_bytes)
    manifest = {
        "schema": 1,
        "kind": "internal-shoot-upper-state-integration-build",
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(result_bytes),
        "output_bytes": len(result_bytes),
        "ownership": {
            "start": OWNERSHIP_START,
            "end": OWNERSHIP_END,
            "preexisting_aligned_pointer_refs": refs_before,
        },
        "expected_writes": expected_writes,
        "actual_changed_bytes": len(changed),
        "timing_policy": (
            "75-to-60 Hz constants use 4/5 scaling; orbit and source counters with "
            "visible cadence use a 1,1,1,2 virtual-source-tick phase"
        ),
        "controller_boundary": {
            "source": "4090:9908",
            "native_stub": GBA_BASE + CONTROLLER_BOUNDARY,
            "implementation": "BX LR",
            "basis": "resident graph is not externally reachable in this layer",
        },
        "claim_scope": (
            "resident upper-state graph only; menu/7168 entry, controller 9908 rules, "
            "runtime, audible behavior, emulator, and supplied-save QA excluded"
        ),
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-upper-state-integration] output SHA-256 {manifest['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
