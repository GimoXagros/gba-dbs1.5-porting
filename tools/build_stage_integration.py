#!/usr/bin/env python3
"""Integrate the three converted Ver. 1.5 arenas into the expanded GBA build."""

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

from convert_wsc_palette_block import convert_color


INPUT_SHA256 = "38E5F35AA4C9A92EC0738DE01EC6C1654F0A0CC0BD75289054383FBE9A7E7AB4"
GBA_BASE = 0x08000000
RESOURCE_SOURCE = 0x07F8E0
RESOURCE_TARGET = 0x580000
RESOURCE_BYTES = 0x18
ORIGINAL_RESOURCE_COUNT = 21
EXPANDED_RESOURCE_COUNT = 31
DESCRIPTOR_TARGET = 0x580400
CLONE_TARGETS = {
    "train": 0x582000,
    "impmon": 0x582400,
    "waterfall": 0x582800,
    "shoot": 0x582A00,
}
DISPATCH_HOOK = 0x582C00
SELECTOR_HOOK = 0x582C40
STAGE_TABLE = 0x582D00
UPDATE_DISPATCH_HOOK = 0x582E00
UPDATE_STAGE_TABLE = 0x582E40
UPDATE_STUB = 0x582E80
SPAWN_HOOK = 0x582F00
SPAWN_TABLE = 0x583000
AUX_STAGE_TABLE = 0x583100
STAGE_SETUP_MAP_HOOK = 0x583200
STAGE_BOUNDS_MAP_HOOK = 0x583240
TRAIN_UPDATE = 0x583400
TRAIN_SCROLL_HELPER = 0x583500
TRAIN_PALETTE_HELPER = 0x583640
TRAIN_PRIMARY_CALLBACK = 0x583740
TRAIN_PALETTE_TABLE = 0x583840
WATERFALL_UPDATE = 0x583900
WATERFALL_PALETTE_HELPER = 0x583A00
IRAIRA_UPDATE = 0x583B00
IRAIRA_PALETTE_HELPER = 0x583C00
FLICKER_CALLBACK = 0x583E00
FLICKER_CALLBACK_HELPER = 0x583F00
WATERFALL_PALETTE_TABLES = 0x584000
IRAIRA_PALETTE_TABLES = 0x584200
WATERFALL_HAZARD_HELPER = 0x584600
WATERFALL_HAZARD_TABLE = 0x584800
VERTICAL_FLAG_R0_HELPER = 0x584900
VERTICAL_FLAG_R8_HELPER = 0x584940
LEGACY_STAGE_SELECTOR = 0x584A00
STAGE_DIMENSION_MAP_HELPER = 0x584A80
OBJECT_PATTERN_TABLE = 0x584B00
OBJECT_PATTERN_DATA = 0x584B80
OBJECT_CONFIG_TABLE = 0x584C00
OBJECT_CONFIG_DATA = 0x584C80
WATERFALL_OBJECT_CONFIG = 0x584CC0
IRAIRA_OBJECT_CONFIG = 0x584D00
SHOOT_OBJECT_CONFIG = 0x584DC0
OBJECT_CONFIG_TABLE_HOOK = 0x584D40
OBJECT_CALLBACK_SLOTS = 0x584D80
WATERFALL_CALLBACK_SLOTS = 0x584D88
IRAIRA_CALLBACK_SLOTS = 0x584D90
SHOOT_CALLBACK_SLOTS = 0x584D98
TRAIN_OBJECT_CALLBACK_LEFT = 0x584E00
TRAIN_OBJECT_CALLBACK_RIGHT = 0x585000
WATERFALL_OBJECT_CALLBACK_LEFT = 0x585200
WATERFALL_OBJECT_CALLBACK_RIGHT = 0x585500
IRAIRA_OBJECT_CALLBACK_LEFT = 0x585800
IRAIRA_OBJECT_CALLBACK_RIGHT = 0x585C00
SHOOT_OBJECT_CALLBACK_LEFT = 0x585E00
SHOOT_OBJECT_CALLBACK_RIGHT = 0x586000
DISPATCH_SITE = 0x03EEC0
SELECTOR_SITE = 0x0D1C78
DISPATCH_RETURN = 0x03EED0
UPDATE_DISPATCH_SITE = 0x015D9C
UPDATE_DISPATCH_RETURN = 0x015DAC
SPAWN_SITE = 0x353130
SPAWN_RETURN = 0x353190
AUX_STAGE_POINTER_SITE = 0x35B3B4
STAGE_SETUP_MAP_SITE = 0x377B18
STAGE_SETUP_MAP_RETURN = 0x377B1C
STAGE_BOUNDS_MAP_SITE = 0x07FC3C
STAGE_BOUNDS_MAP_RETURN = 0x07FC40
VERTICAL_FLAG_R0_SITE = 0x359568
VERTICAL_FLAG_R8_SITE = 0x3597D0
STAGE_DIMENSION_MAP_SITE = 0x03EE70
STAGE_DIMENSION_MAP_RETURN = 0x03EE74
OBJECT_CONFIG_TABLE_SITE = 0x36D2C0
OBJECT_CONFIG_TABLE_RETURN = 0x36D2C8
# These callers immediately index an eight-entry retail jump or data table.
# Keep the route selector's actual IDs for expanded dispatches, but present a
# safe retail analog at these still-unported consumers.
LEGACY_STAGE_SELECTOR_SITES = (
    0x0C4BC4,
    0x0C4CC8,
    0x0D0BD0,
    0x0D1408,
)
OBJECT_PATTERN_POINTER_SITE = 0x36D40C
ORIGINAL_OBJECT_PATTERN_TABLE = 0x36E078
WSC15_OBJECT_PATTERN_RECORDS = 0x74512D
WSC15_OBJECT_PATTERN_BYTES = 0x74515D
WSC15_OBJECT_OVERLAY_BASE = 0x740900
ORIGINAL_OBJECT_CONFIG_TABLE = 0x36D38C
WSC15_OBJECT_CONFIG_TABLE = 0x744F2D

STAGES = {
    "train": {
        "palette": 0x590000,
        "tiles": 0x590100,
        "maps": 0x594100,
        "indices": (21, 22, 23, 24),
    },
    "impmon": {
        "palette": 0x598000,
        "tiles": 0x598100,
        "maps": 0x59C100,
        "indices": (25, 26),
    },
    "waterfall": {
        "palette": 0x5A0000,
        "tiles": 0x5A0100,
        "maps": 0x5A4100,
        "indices": (27, 28),
    },
    "shoot": {
        "palette": 0x5A8000,
        "tiles": 0x5A8100,
        "maps": 0x5AC100,
        "indices": (29, 30),
    },
}

CLONE_SPECS = {
    "train": {
        # Train preparation extends the WSC stage-6 setup and has the same
        # four-resource population.  The GBA stage-6 initializer therefore
        # supplies the correct background-object/vent ABI.
        "source": 0x040080,
        "end": 0x040334,
        "code_end": 0x0402B4,
        "palette_pointers": (0x0803880A,),
        "tile_pointer": 0x080388E8,
        "index_offsets": (0x50, 0xCC, 0x148, 0x1D0),
    },
    # Iraira Room shares the two-layer ABI of retail stage 3.
    "impmon": {
        "source": 0x03FBB0,
        "end": 0x03FD30,
        "code_end": 0x03FCE0,
        "palette_pointers": (0x0802C32A,),
        "tile_pointer": 0x0802C488,
        "index_offsets": (0x5C, 0xD8),
    },
    "waterfall": {
        # Ver. 1.5 preparation function ID 9 is byte-identical to WSC 1.0
        # stage 5.  The commercial GBA stage-5 initializer also owns the
        # required two-resource setup and hazard-state initialization.
        "source": 0x03FEF0,
        "end": 0x040080,
        "code_end": 0x040030,
        "palette_pointers": (0x0803464A, 0x0803472A),
        "tile_pointer": 0x08034808,
        "index_offsets": (0x5C, 0xD8),
    },
    "shoot": {
        "source": 0x03FBB0,
        "end": 0x03FD30,
        "code_end": 0x03FCE0,
        "palette_pointers": (0x0802C32A,),
        "tile_pointer": 0x0802C488,
        "index_offsets": (0x5C, 0xD8),
    },
}

ASSET_NAMES = tuple(
    f"stage-{stage}-{kind}.bin"
    for stage in STAGES
    for kind in ("palette", "tiles", "maps")
)
RETAIL_IMPMON_SHARED = {"palette": 0x02C32A, "tiles": 0x02C488}

# The commercial GBA port kept the original WSC 1.0 tables byte-for-byte.
# Ver. 1.5 appends three 16-byte spawn records at WSC ROM 0x7432B4 and four
# auxiliary selector records at 0x74535E.  The WSC append order is train,
# waterfall, Iraira Room.  The expanded WSC update table preserves original
# IDs 0..7 and appends these at IDs 8, 9, and 10 in exactly that order.
WSC15_SPAWN_RECORDS = {
    "train": bytes.fromhex("00 04 80 0B 80 18 00 0C 00 0C 00 0C 00 10 00 0C"),
    "waterfall": bytes.fromhex("00 05 00 03 00 07 00 1A 00 04 00 0D E0 07 00 10"),
    "impmon": bytes.fromhex("00 0D 80 0A 00 11 80 0A 00 0C 00 11 00 0E 80 0D"),
}
WSC15_AUX_RECORD = bytes.fromhex(
    "00 00 00 02 02 02 04 04 06 06 06 08 08 0A 0A 0A"
)
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC15_STAGE_OVERLAY_BASE = 0x768F70


def arm_branch(source: int, target: int, *, link: bool = False, condition: int = 0xE) -> int:
    delta = target - (source + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("ARM branch target is not encodable")
    return ((condition << 28) | 0x0A000000 | (int(link) << 24)
            | ((delta >> 2) & 0x00FFFFFF))


def decode_arm_branch(source: int, word: int) -> int:
    immediate = word & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    return source + 8 + immediate * 4


def assemble_arm(source: str, address: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(
        source, GBA_BASE + address
    )
    return bytes(encoded)


def relocate_arm_blob(source: bytes, start: int, end: int, target: int) -> bytearray:
    """Copy a self-contained ARM routine/data window and relocate branches."""
    blob = bytearray(source[start:end])
    for relative in range(0, end - start, 4):
        word = struct.unpack_from("<I", blob, relative)[0]
        if (word >> 25) & 7 != 5:
            continue
        old_address = GBA_BASE + start + relative
        old_target = decode_arm_branch(old_address, word)
        new_target = (
            GBA_BASE + target + old_target - (GBA_BASE + start)
            if GBA_BASE + start <= old_target < GBA_BASE + end
            else old_target
        )
        struct.pack_into(
            "<I", blob, relative,
            arm_branch(
                GBA_BASE + target + relative, new_target,
                link=bool(word & 0x01000000), condition=word >> 28,
            ),
        )
    return blob


def build_train_primary_callback(source: bytes, palette_table: bytes) -> bytes:
    """Translate WSC 5EEA:0AD8 from the retail stage-3 GBA callback.

    The two x86 callbacks are structurally identical except that the train
    clamps its 21-entry gradient at index 20, whereas retail stage 3 rejects
    indices 32 and above.  The commercial conversion maps the WSC 12-bit
    table to inline GBA BGR555 halfwords, which we reproduce here.
    """
    blob = relocate_arm_blob(source, 0x0C92C4, 0x0C9388, TRAIN_PRIMARY_CALLBACK)
    if struct.unpack_from("<I", blob, 0x40)[0] != 0xE3510020:
        raise SystemExit("retail stage-3 callback comparison invariant failed")
    if struct.unpack_from("<I", blob, 0x44)[0] != 0x5A000008:
        raise SystemExit("retail stage-3 callback branch invariant failed")
    struct.pack_into("<I", blob, 0x40, 0xE3510015)  # cmp r1, #21
    struct.pack_into("<I", blob, 0x44, 0x53A01014)  # movpl r1, #20
    if len(palette_table) != 42:
        raise AssertionError("train callback gradient must contain 21 colors")
    blob[0x74:0x74 + len(palette_table)] = palette_table
    return bytes(blob)


def build_train_update() -> bytes:
    return assemble_arm(f"""
        push {{lr}}
        ldr r1, train_source
        ldrh r0, [r1, #0x12]
        ldr r8, stage_output
        strh r0, [r8]
        tst r3, #0x10
        bne train_always
        ldr r8, train_primary
        str r8, [r5], #4
        and r8, r0, #7
        add r8, r8, #8
        strh r8, [r4], #2
        add r2, r2, #1
    train_always:
        ldr r8, standard_callback
        str r8, [r5], #4
        add r2, r2, #1
        bl 0x{GBA_BASE + TRAIN_SCROLL_HELPER:X}
        bl 0x{GBA_BASE + TRAIN_PALETTE_HELPER:X}
        pop {{lr}}
        bx lr
        .align 2
    train_source: .word 0x03002378
    stage_output: .word 0x03002568
    train_primary: .word 0x{GBA_BASE + TRAIN_PRIMARY_CALLBACK:08X}
    standard_callback: .word 0x080C94FC
    """, TRAIN_UPDATE)


def build_train_scroll_helper() -> bytes:
    return assemble_arm("""
        push {r0-r5, r8-r11, lr}
        ldr r8, train_motion_gate
        ldrh r2, [r8]
        ldr r5, train_camera
        ldr r4, train_scroll_state
        mov r0, #0x80
        mov r1, #8
        cmp r2, #0
        beq scroll_store
        ldrh r3, [r5, #0x1c]
        cmp r3, #0
        beq scroll_store
        ldrh r8, [r5, #0x42]
        tst r8, #8
        bne scroll_add
        cmp r0, r3
        beq scroll_clear
        blo scroll_under
        sub r0, r0, r3
        b scroll_store
    scroll_under:
        mov r1, #2
        sub r0, r3, r0
        b scroll_store
    scroll_add:
        add r0, r0, r3
    scroll_store:
        strh r0, [r4, #0x1c]
        mov r0, #0
        strh r0, [r4, #0x1e]
        orr r1, r1, #0x80
        push {r4}
        push {r11}
        push {r1}
        bl 0x08013DD4
        add sp, sp, #0xc
        ldr r1, train_scroll_registers
        ldrb r0, [r4, #0x1a]
        strb r0, [r1]
        ldrb r0, [r4, #0x1b]
        strb r0, [r1, #1]
    scroll_clear:
        mov r0, #0
        strh r0, [r4, #0x1c]
        pop {r0-r5, r8-r11, lr}
        bx lr
        .align 2
    train_motion_gate: .word 0x03002608
    train_camera: .word 0x03002338
    train_scroll_state: .word 0x03002378
    train_scroll_registers: .word 0x0300456E
    """, TRAIN_SCROLL_HELPER)


def build_train_palette_helper() -> bytes:
    return assemble_arm(f"""
        push {{r0-r4, lr}}
        ldr r4, stage_output
        ldrh r0, [r4, #4]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r4, #4]
        cmp r0, #0
        bne palette_done
        ldrh r0, [r4, #6]
        add r0, r0, #1
        cmp r0, #3
        movhs r0, #0
        strh r0, [r4, #6]
        ldr r1, palette_table
        add r1, r1, r0, lsl #4
        add r2, r4, #8
        mov r3, #6
    palette_copy:
        ldrh r0, [r1], #2
        strh r0, [r2], #2
        subs r3, r3, #1
        bne palette_copy
    palette_done:
        pop {{r0-r4, lr}}
        bx lr
        .align 2
    stage_output: .word 0x03002568
    palette_table: .word 0x{GBA_BASE + TRAIN_PALETTE_TABLE:08X}
    """, TRAIN_PALETTE_HELPER)


def build_flicker_callback(source: bytes) -> bytes:
    """Translate the identical WSC 5EEA:0B4E/0BC4 display callback.

    Its scroll-register core is the retail WSC 5EEA:0A48 lineage (GBA
    0x080C94FC).  Ver. 1.5 changes the display mask to keep BG0/OBJ enabled
    while toggling BG1 each invocation; a small helper performs that tail.
    """
    blob = relocate_arm_blob(source, 0x0C94FC, 0x0C9570, FLICKER_CALLBACK)
    original = struct.unpack_from("<I", blob, 0x60)[0]
    if decode_arm_branch(GBA_BASE + FLICKER_CALLBACK + 0x60, original) != 0x080C9000:
        raise SystemExit("retail stage display-callback tail invariant failed")
    struct.pack_into(
        "<I", blob, 0x60,
        arm_branch(
            GBA_BASE + FLICKER_CALLBACK + 0x60,
            GBA_BASE + FLICKER_CALLBACK_HELPER,
            link=True,
        ),
    )
    return bytes(blob)


def build_flicker_callback_helper() -> bytes:
    return assemble_arm("""
        push {r0-r2, lr}
        bl 0x080C9000
        ldr r0, display_control
        ldrh r1, [r0]
        orr r1, r1, #0x1000
        orr r1, r1, #0x100
        eor r1, r1, #0x200
        strh r1, [r0]
        pop {r0-r2, lr}
        bx lr
        .align 2
    display_control: .word 0x04000000
    """, FLICKER_CALLBACK_HELPER)


def build_simple_stage_update(
    address: int,
    palette_helper: int,
    *,
    call_common: bool,
    mechanics_helper: int | None = None,
) -> bytes:
    common = """
        ldr r0, battle_camera
        push {r0}
        push {r11}
        mov r0, #0
        push {r0}
        bl 0x080137AC
        add sp, sp, #0xc
    """ if call_common else ""
    mechanics = (
        f"bl 0x{GBA_BASE + mechanics_helper:X}"
        if mechanics_helper is not None else ""
    )
    return assemble_arm(f"""
        push {{lr}}
        {common}
        ldr r0, display_callback
        str r0, [r5], #4
        mov r8, #7
        strh r8, [r4]
        add r2, r2, #1
        {mechanics}
        bl 0x{GBA_BASE + palette_helper:X}
        pop {{lr}}
        bx lr
        .align 2
    battle_camera: .word 0x03002338
    display_callback: .word 0x{GBA_BASE + FLICKER_CALLBACK:08X}
    """, address)


def build_waterfall_hazard_helper() -> bytes:
    """Translate WSC Ver. 1.5 overlay 0x1C5F..0x1D85.

    The WSC routine uses the same six-byte entity records and spawn service as
    retail stage 5.  The commercial GBA port converts those to eight-byte
    records at 0x03001C68 and service 0x08013764. WSC ES:0384 maps to GBA
    0x0300256A, the second halfword cleared by the stage-5 initializer at
    0x0803FEF0. Ver. 1.5 adds a three-phase state there: spawn a mode-specific pair, wait for the
    first entity to disappear, spawn the paired successors, then clear both
    records and emit the remaining IDs 9..11 once the shared activity gate is
    idle.
    """
    return assemble_arm(f"""
        push {{r0-r8, lr}}
        ldr r4, hazard_state
        ldrh r0, [r4]
        and r2, r0, #3
        cmp r2, #1
        blo hazard_done
        cmp r2, #3
        bhi hazard_done
        sub r1, r2, #1
        ldr r6, hazard_pairs
        add r6, r6, r1, lsl #2
        ldrh r5, [r6]
        ldrh r7, [r6, #2]

        tst r0, #0x300
        bne hazard_phase_one
        mov r1, #0
        push {{r5}}
        push {{r1}}
        bl 0x08013764
        add sp, sp, #8
        push {{r7}}
        push {{r1}}
        bl 0x08013764
        add sp, sp, #8
        ldrh r0, [r4]
        orr r0, r0, #0x100
        strh r0, [r4]
        b hazard_done

    hazard_phase_one:
        tst r0, #0x100
        beq hazard_phase_two
        ldr r6, entity_table
        sub r1, r5, #1
        add r1, r6, r1, lsl #3
        ldrh r1, [r1]
        cmp r1, #0
        bne hazard_done
        add r5, r5, #1
        add r7, r7, #1
        mov r1, #1
        push {{r5}}
        push {{r1}}
        bl 0x08013764
        add sp, sp, #8
        push {{r7}}
        push {{r1}}
        bl 0x08013764
        add sp, sp, #8
        ldrh r0, [r4]
        bic r0, r0, #0x100
        orr r0, r0, #0x200
        strh r0, [r4]
        b hazard_done

    hazard_phase_two:
        tst r0, #0x200
        beq hazard_done
        ldr r1, activity_gate
        ldrh r1, [r1]
        tst r1, #1
        bne hazard_done
        mov r0, #0
        strh r0, [r4]
        ldr r6, entity_table
        sub r1, r5, #1
        add r1, r6, r1, lsl #3
        strh r0, [r1]
        strh r0, [r1, #2]
        sub r1, r7, #1
        add r1, r6, r1, lsl #3
        strh r0, [r1]
        strh r0, [r1, #2]
        mov r7, #3
    hazard_remaining_loop:
        cmp r7, r2
        beq hazard_remaining_next
        add r5, r7, #8
        push {{r5}}
        push {{r0}}
        bl 0x08013764
        add sp, sp, #8
    hazard_remaining_next:
        subs r7, r7, #1
        bne hazard_remaining_loop
    hazard_done:
        pop {{r0-r8, lr}}
        bx lr
        .align 2
    hazard_state: .word 0x0300256A
    entity_table: .word 0x03001C68
    activity_gate: .word 0x03004CEC
    hazard_pairs: .word 0x{GBA_BASE + WATERFALL_HAZARD_TABLE:08X}
    """, WATERFALL_HAZARD_HELPER)


def build_vertical_flag_helper(address: int, value_register: int) -> bytes:
    """Apply the Ver. 1.5 stage-9/10 exception to object flag 0x2000.

    WSC raw 0x781BEF and 0x786C5C add the same stage test to two distinct
    retail object-construction paths. Their GBA counterparts are the single
    unconditional OR instructions at 0x08359568 and 0x083597D0. The helper
    leaves all caller state intact except the value register that would have
    received the retail flag.
    """
    if value_register == 0:
        save, scratch, target = "r2", "r2", "r0"
    elif value_register == 8:
        save, scratch, target = "r0", "r0", "r8"
    else:
        raise ValueError("vertical flag helper supports only r0 or r8")
    return assemble_arm(f"""
        push {{{save}}}
        ldr {scratch}, battle_state
        ldrb {scratch}, [{scratch}, #0xe]
        cmp {scratch}, #9
        blo vertical_add_flag
        cmp {scratch}, #10
        bls vertical_done
    vertical_add_flag:
        orr {target}, {target}, #0x2000
    vertical_done:
        pop {{{save}}}
        bx lr
        .align 2
    battle_state: .word 0x03002310
    """, address)


def build_waterfall_palette_helper() -> bytes:
    return assemble_arm(f"""
        push {{r0-r7, lr}}
        ldr r4, palette_state
        ldrh r0, [r4]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r4]
        cmp r0, #0
        bne waterfall_palette_done
        ldrh r0, [r4, #2]
        subs r0, r0, #1
        movmi r0, #4
        strh r0, [r4, #2]
        ldr r1, tables
        add r1, r1, r0, lsl #4
        add r2, r4, #4
        mov r3, #8
    waterfall_main_copy:
        ldrh r5, [r1], #2
        strh r5, [r2], #2
        subs r3, r3, #1
        bne waterfall_main_copy
        ldr r1, tables
        add r5, r1, #0x50
        add r6, r1, #0x62
        add r5, r5, r0, lsl #1
        add r6, r6, r0, lsl #1
        mov r3, #5
    waterfall_pair_copy:
        ldrh r7, [r5], #2
        strh r7, [r2]
        ldrh r7, [r6], #2
        strh r7, [r2, #0xa]
        add r2, r2, #2
        subs r3, r3, #1
        bne waterfall_pair_copy
    waterfall_palette_done:
        pop {{r0-r7, lr}}
        bx lr
        .align 2
    palette_state: .word 0x03002568
    tables: .word 0x{GBA_BASE + WATERFALL_PALETTE_TABLES:08X}
    """, WATERFALL_PALETTE_HELPER)


def build_iraira_palette_helper() -> bytes:
    return assemble_arm(f"""
        push {{r0-r7, lr}}
        ldr r4, palette_state
        ldrh r0, [r4]
        add r0, r0, #1
        and r0, r0, #7
        strh r0, [r4]
        cmp r0, #0
        bne iraira_skip_first
        ldrh r0, [r4, #4]
        add r0, r0, #1
        and r0, r0, #3
        strh r0, [r4, #4]
        ldr r1, tables
        add r1, r1, r0, lsl #5
        add r2, r4, #0xa
        mov r3, #11
    iraira_first_copy:
        ldrh r5, [r1], #2
        strh r5, [r2], #2
        subs r3, r3, #1
        bne iraira_first_copy
        ldr r1, tables
        add r1, r1, #0x80
        add r1, r1, r0, lsl #4
        mov r3, #6
    iraira_second_copy:
        ldrh r5, [r1], #2
        strh r5, [r2], #2
        subs r3, r3, #1
        bne iraira_second_copy
    iraira_skip_first:
        ldrh r0, [r4]
        tst r0, #0xb
        bne iraira_skip_third
        ldrh r0, [r4, #6]
        add r0, r0, #1
        cmp r0, #7
        movhs r0, #0
        strh r0, [r4, #6]
        ldr r1, tables
        add r5, r1, #0xc0
        add r6, r1, #0x190
        add r5, r5, r0, lsl #4
        add r6, r6, r0, lsl #4
        add r2, r4, #0x2c
        mov r3, #7
    iraira_third_copy:
        ldrh r7, [r5], #2
        strh r7, [r2]
        ldrh r7, [r6], #2
        strh r7, [r2, #0x1c]
        add r2, r2, #2
        subs r3, r3, #1
        bne iraira_third_copy
    iraira_skip_third:
        ldrh r0, [r4, #2]
        add r0, r0, #1
        cmp r0, #5
        blo iraira_store_delay
        mov r0, #0
        strh r0, [r4, #2]
        ldrh r0, [r4, #8]
        add r0, r0, #1
        cmp r0, #6
        movhs r0, #0
        strh r0, [r4, #8]
        ldr r1, tables
        add r1, r1, #0x130
        add r1, r1, r0, lsl #4
        add r2, r4, #0x3a
        mov r3, #7
    iraira_fourth_copy:
        ldrh r5, [r1], #2
        strh r5, [r2], #2
        subs r3, r3, #1
        bne iraira_fourth_copy
        b iraira_done
    iraira_store_delay:
        strh r0, [r4, #2]
    iraira_done:
        pop {{r0-r7, lr}}
        bx lr
        .align 2
    palette_state: .word 0x03002568
    tables: .word 0x{GBA_BASE + IRAIRA_PALETTE_TABLES:08X}
    """, IRAIRA_PALETTE_HELPER)


def relocate_stage_clone(source: bytes, target: int, *, spec: dict[str, object],
                         palette: int, tiles: int, indices: tuple[int, ...]) -> bytes:
    clone_source = int(spec["source"])
    clone_end = int(spec["end"])
    clone_code_end = int(spec["code_end"])
    clone = bytearray(source[clone_source:clone_end])
    for offset in range(0, clone_code_end - clone_source, 4):
        old_address = GBA_BASE + clone_source + offset
        new_address = GBA_BASE + target + offset
        word = struct.unpack_from("<I", clone, offset)[0]
        if (word >> 25) & 7 == 5:
            old_target = decode_arm_branch(old_address, word)
            new_target = (
                GBA_BASE + target + (old_target - (GBA_BASE + clone_source))
                if GBA_BASE + clone_source <= old_target < GBA_BASE + clone_end
                else old_target
            )
            struct.pack_into(
                "<I", clone, offset,
                arm_branch(
                    new_address, new_target,
                    link=bool(word & 0x01000000), condition=word >> 28,
                ),
            )

    # Relocate absolute pointers into the copied window, then replace the
    # initializer's external asset/resource pointers.
    for offset in range(0, len(clone), 4):
        value = struct.unpack_from("<I", clone, offset)[0]
        if GBA_BASE + clone_source <= value < GBA_BASE + clone_end:
            struct.pack_into("<I", clone, offset, GBA_BASE + target + value - (GBA_BASE + clone_source))
    replacements = {pointer: GBA_BASE + palette for pointer in spec["palette_pointers"]}
    replacements[int(spec["tile_pointer"])] = GBA_BASE + tiles
    replacements[0x0807F8E0] = GBA_BASE + RESOURCE_TARGET
    for offset in range(0, len(clone), 4):
        value = struct.unpack_from("<I", clone, offset)[0]
        if value in replacements:
            struct.pack_into("<I", clone, offset, replacements[value])
    for relative, index in zip(spec["index_offsets"], indices, strict=True):
        struct.pack_into("<I", clone, relative, 0xE3A08000 | index)
    return bytes(clone)


def build_dispatch_hook() -> bytes:
    words = [
        0xE59F8010,  # ldr r8, [pc, #0x10]
        0xE7989101,  # ldr r9, [r8, r1, lsl #2]
        0xE1A0E00F,  # mov lr, pc
        0xE12FFF19,  # bx r9
        arm_branch(GBA_BASE + DISPATCH_HOOK + 0x10, GBA_BASE + DISPATCH_RETURN),
        0xE1A00000,  # nop / literal alignment
        GBA_BASE + STAGE_TABLE,
    ]
    return struct.pack(f"<{len(words)}I", *words)


def build_selector_hook() -> bytes:
    words = [
        0xE59F802C,  # ldr r8, [pc, #0x2c] -> battle state
        0xE5D8000A,  # ldrb r0, [r8, #0xa] -> player character ID
        0xE350000B,  # cmp r0, #11 (Impmon)
        0x03A0000A,  # moveq r0, #10 (Iraira Room)
        0x012FFF1E,  # bxeq lr
        0xE350000D,  # cmp r0, #13 (Patamon)
        0x03A00008,  # moveq r0, #8
        0x012FFF1E,  # bxeq lr
        0xE350000E,  # cmp r0, #14 (Tailmon)
        0x03A00009,  # moveq r0, #9 (waterfall)
        0x012FFF1E,  # bxeq lr
        0xE5D8000E,  # ldrb r0, [r8, #0xe] (retail stage)
        0xE12FFF1E,  # bx lr
        0x03002310,
    ]
    return struct.pack(f"<{len(words)}I", *words)


def build_legacy_stage_selector() -> bytes:
    """Return a bounded retail analog for confirmed eight-entry consumers.

    This duplicates the temporary character route policy used by the actual
    selector, then maps train/waterfall/Iraira/Shoot to retail stages
    0/6/3/7. It is intentionally called only from consumers proven to index
    an eight-entry retail table. The actual initializer/update dispatches
    continue to receive IDs 8..11.
    """
    return assemble_arm("""
        ldr r8, legacy_battle_state
        ldrb r0, [r8, #0xA]
        cmp r0, #11
        moveq r0, #3
        bxeq lr
        cmp r0, #13
        moveq r0, #0
        bxeq lr
        cmp r0, #14
        moveq r0, #6
        bxeq lr
        ldrb r0, [r8, #0xE]
        cmp r0, #8
        moveq r0, #0
        bxeq lr
        cmp r0, #9
        moveq r0, #6
        bxeq lr
        cmp r0, #10
        moveq r0, #3
        bxeq lr
        cmp r0, #11
        moveq r0, #7
        bx lr
        .align 2
    legacy_battle_state: .word 0x03002310
    """, LEGACY_STAGE_SELECTOR)


def build_stage_dimension_map_helper() -> bytes:
    """Form the retail dimension-table byte offset without changing r1."""
    return assemble_arm(f"""
        mov r5, r1
        cmp r5, #8
        moveq r5, #0
        cmp r5, #9
        moveq r5, #6
        cmp r5, #10
        moveq r5, #3
        cmp r5, #11
        moveq r5, #7
        lsl r5, r5, #2
        b 0x{GBA_BASE + STAGE_DIMENSION_MAP_RETURN:08X}
    """, STAGE_DIMENSION_MAP_HELPER)


def build_object_config_table_hook() -> bytes:
    """Index the relocated twelve-entry object-configuration table.

    The caller has already masked the stage ID into r1.  The two replaced
    retail instructions formed the address of the inline eight-entry table;
    this helper performs the same calculation against the expanded table.
    """
    return assemble_arm(f"""
        ldr sb, object_config_table
        add r1, sb, r1, lsl #3
        b 0x{GBA_BASE + OBJECT_CONFIG_TABLE_RETURN:08X}
        .align 2
    object_config_table: .word 0x{GBA_BASE + OBJECT_CONFIG_TABLE:08X}
    """, OBJECT_CONFIG_TABLE_HOOK)


def build_train_object_callback_left() -> bytes:
    """Translate WSC object callback 4090:3CD5 (train, left entrant)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r0, #0
        mvn r8, #0x6F
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x40
        strh r8, [r4, #0x94]
        adr r8, approach
        str r8, [r4]
        bl approach
        pop {lr}
        bx lr

    approach:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmp r8, #0xF00
        bgt approach_update
        mov r8, #0x100
        strh r8, [r4, #0x42]
        adr r8, depart
        str r8, [r4]
        b left_return
    approach_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
    left_return:
        pop {lr}
        bx lr

    depart:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmp r8, #0x1D00
        blt depart_update
        bl 0x0836D750
        pop {lr}
        bx lr
    depart_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        pop {lr}
        bx lr
    """, TRAIN_OBJECT_CALLBACK_LEFT)


def build_train_object_callback_right() -> bytes:
    """Translate WSC object callback 4090:3D7B (train, right entrant)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r0, #0
        mov r8, #0xE0
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x40
        strh r8, [r4, #0x94]
        adr r8, update
        str r8, [r4]
        bl update
        pop {lr}
        bx lr

    update:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmp r8, #0x1D00
        blt choose_velocity
        bl 0x0836D750
        pop {lr}
        bx lr
    choose_velocity:
        ldrsh r8, [r4, #0x36]
        cmp r8, #0xC80
        movle r8, #0x80
        movgt r8, #0xE0
        strh r8, [r4, #0x42]
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        asr r0, r0, #1
        ldrsh r8, [r4, #0x44]
        add r8, r8, r0
        strh r8, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        pop {lr}
        bx lr
    """, TRAIN_OBJECT_CALLBACK_RIGHT)


def build_waterfall_object_callback_left() -> bytes:
    """Translate WSC callback 4090:3DFB (waterfall mode 1)."""
    return assemble_arm("""
    entry:
        push {lr}
        ldr r8, waterfall_mode
        mov r0, #1
        strh r0, [r8]
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        bic r8, r8, #0x6000
        strh r8, [r5, #8]
        mov r0, #0
        mvn r8, #0x6F
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x40
        strh r8, [r4, #0x94]
        strh r0, [r4, #0x96]
        mov r8, #0x100
        strh r8, [r4, #0x98]
        adr r8, wait_phase
        str r8, [r4]
        bl wait_phase
        pop {lr}
        bx lr

    wait_phase:
        push {lr}
        ldrh r8, [r4, #0x98]
        cmp r8, #0
        bne wait_update
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r8, #0x70
        strh r8, [r4, #0x42]
        adr r8, exit_phase
        str r8, [r4]
        b waterfall_left_return
    wait_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne waterfall_left_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
    waterfall_left_return:
        pop {lr}
        bx lr

    exit_phase:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmp r8, #0xF00
        blt exit_update
        bl 0x0836D750
        pop {lr}
        bx lr
    exit_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne waterfall_left_exit_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
    waterfall_left_exit_return:
        pop {lr}
        bx lr
        .align 2
    waterfall_mode: .word 0x0300256A
    """, WATERFALL_OBJECT_CALLBACK_LEFT)


def build_waterfall_object_callback_right() -> bytes:
    """Translate WSC callback 4090:3EE0 (waterfall mode 2)."""
    return assemble_arm("""
    entry:
        push {lr}
        ldr r8, waterfall_mode
        mov r0, #2
        strh r0, [r8]
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        bic r8, r8, #0x2000
        strh r8, [r5, #8]
        mov r0, #0
        mov r8, #0x70
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0xC0
        strh r8, [r4, #0x94]
        strh r0, [r4, #0x96]
        mov r8, #0x100
        strh r8, [r4, #0x98]
        adr r8, wait_phase
        str r8, [r4]
        bl wait_phase
        pop {lr}
        bx lr

    wait_phase:
        push {lr}
        ldrh r8, [r4, #0x98]
        cmp r8, #0
        bne wait_update
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mvn r8, #0x6F
        strh r8, [r4, #0x42]
        adr r8, exit_phase
        str r8, [r4]
        b waterfall_right_return
    wait_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne waterfall_right_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
    waterfall_right_return:
        pop {lr}
        bx lr

    exit_phase:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmn r8, #0x200
        bgt exit_update
        bl 0x0836D750
        pop {lr}
        bx lr
    exit_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne waterfall_right_exit_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
    waterfall_right_exit_return:
        pop {lr}
        bx lr
        .align 2
    waterfall_mode: .word 0x0300256A
    """, WATERFALL_OBJECT_CALLBACK_RIGHT)


def build_iraira_object_callback_left() -> bytes:
    """Translate WSC callback 4090:40AF (Iraira oscillating entrant)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        bic r8, r8, #0x2000
        strh r8, [r5, #8]
        mov r0, #0
        mov r8, #0x120
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0xC0
        strh r8, [r4, #0x94]
        mov r8, #0x140
        strh r8, [r4, #0x98]
        adr r8, wait_phase
        str r8, [r4]
        bl wait_phase
        pop {lr}
        bx lr

    wait_phase:
        push {lr}
        ldrh r8, [r4, #0x98]
        cmp r8, #0
        bne wait_update
        mvn r8, #0x1F
        strh r8, [r4, #0x46]
        mov r8, #0x80
        strh r8, [r4, #0x44]
        adr r8, decelerate_to_zero
        str r8, [r4]
        b iraira_left_return
    wait_update:
        bl object_update
        bl animate_frame
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        asr r0, r0, #2
        ldrsh r8, [r4, #0x44]
        add r8, r8, r0
        strh r8, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
    iraira_left_return:
        pop {lr}
        bx lr

    decelerate_to_zero:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmp r8, #0
        bgt decelerate_update
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mvn r8, #0x7F
        strh r8, [r4, #0x46]
        adr r8, accelerate_left
        str r8, [r4]
        b iraira_decelerate_return
    decelerate_update:
        bl object_update
    iraira_decelerate_return:
        pop {lr}
        bx lr

    accelerate_left:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmn r8, #0x100
        bgt accelerate_left_update
        mov r8, #0x80
        strh r8, [r4, #0x46]
        adr r8, return_to_zero
        str r8, [r4]
        b iraira_accelerate_left_return
    accelerate_left_update:
        bl object_update
    iraira_accelerate_left_return:
        pop {lr}
        bx lr

    return_to_zero:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmp r8, #0
        blt return_to_zero_update
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r8, #0x80
        strh r8, [r4, #0x46]
        adr r8, accelerate_right
        str r8, [r4]
        b iraira_return_zero_done
    return_to_zero_update:
        bl object_update
    iraira_return_zero_done:
        pop {lr}
        bx lr

    accelerate_right:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmp r8, #0x100
        blt accelerate_right_update
        mvn r8, #0x7F
        strh r8, [r4, #0x46]
        adr r8, decelerate_right
        str r8, [r4]
        b iraira_accelerate_right_return
    accelerate_right_update:
        bl object_update
    iraira_accelerate_right_return:
        pop {lr}
        bx lr

    decelerate_right:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmp r8, #0
        bgt decelerate_right_update
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mvn r8, #0x1F
        strh r8, [r4, #0x46]
        adr r8, final_acceleration
        str r8, [r4]
        b iraira_decelerate_right_return
    decelerate_right_update:
        bl object_update
    iraira_decelerate_right_return:
        pop {lr}
        bx lr

    final_acceleration:
        push {lr}
        bl apply_acceleration
        ldrsh r8, [r4, #0x42]
        cmn r8, #0x100
        bgt final_acceleration_update
        mov r0, #0
        mvn r8, #0xFF
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x80
        strh r8, [r4, #0x94]
        adr r8, exit_phase
        str r8, [r4]
        b iraira_final_accel_return
    final_acceleration_update:
        bl object_update
    iraira_final_accel_return:
        pop {lr}
        bx lr

    exit_phase:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmn r8, #0x100
        bgt exit_update
        bl 0x0836D750
        pop {lr}
        bx lr
    exit_update:
        bl object_update
        bl animate_frame
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        asr r0, r0, #2
        ldrsh r8, [r4, #0x44]
        add r8, r8, r0
        strh r8, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
        pop {lr}
        bx lr

    apply_acceleration:
        ldrsh r0, [r4, #0x46]
        asr r0, r0, #4
        ldrsh r8, [r4, #0x42]
        add r8, r8, r0
        strh r8, [r4, #0x42]
        bx lr

    object_update:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        pop {lr}
        bx lr

    animate_frame:
        push {lr}
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        pop {lr}
        bx lr
    """, IRAIRA_OBJECT_CALLBACK_LEFT)


def build_iraira_object_callback_right() -> bytes:
    """Translate WSC callback 4090:42B5 (Iraira right entrant)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        bic r8, r8, #0x6000
        strh r8, [r5, #8]
        mov r0, #0
        mvn r8, #0xCF
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x80
        strh r8, [r4, #0x94]
        adr r8, update
        str r8, [r4]
        bl update
        pop {lr}
        bx lr

    update:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmn r8, #0x200
        bgt continue_update
        bl 0x0836D750
        pop {lr}
        bx lr
    continue_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        tst r0, #0x8000
        asrne r0, r0, #2
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        ldrh r8, [r4, #0x98]
        sub r8, r8, #1
        strh r8, [r4, #0x98]
        pop {lr}
        bx lr
    """, IRAIRA_OBJECT_CALLBACK_RIGHT)


def build_shoot_object_callback_left() -> bytes:
    """Translate WSC callback 4090:432F (Shoot left presentation object)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        orr r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r8, #0x200
        rsb r8, r8, #0
        strh r8, [r4, #0x34]
        mov r8, #0x1800
        strh r8, [r4, #0x36]
        mov r0, #0
        mov r8, #0xD0
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        mov r8, #0x80
        strh r8, [r4, #0x94]
        adr r8, intro_phase
        str r8, [r4]
        bl intro_phase
        pop {lr}
        bx lr

    intro_phase:
        push {lr}
        ldrh r8, [r4, #0x94]
        cmp r8, #0x7F
        bne intro_update
        adr r8, travel_phase
        str r8, [r4]
        mov r8, #0
        strh r8, [r4, #0x96]
        pop {lr}
        bx lr
    intro_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        pop {lr}
        bx lr

    travel_phase:
        push {lr}
        ldrh r8, [r4, #0x34]
        cmp r8, #0x1D00
        blo travel_update
        bl 0x0836D750
        pop {lr}
        bx lr
    travel_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #1
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne shoot_left_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
    shoot_left_return:
        pop {lr}
        bx lr
    """, SHOOT_OBJECT_CALLBACK_LEFT)


def build_shoot_object_callback_right() -> bytes:
    """Translate WSC callback 4090:43E6 (Shoot right presentation object)."""
    return assemble_arm("""
    entry:
        push {lr}
        push {r5}
        push {fp}
        mov r8, #0
        push {r8}
        bl 0x08012874
        add sp, sp, #12
        ldrh r8, [r5, #8]
        bic r8, r8, #0x4000
        strh r8, [r5, #8]
        mov r8, #0x1D00
        strh r8, [r4, #0x34]
        mov r8, #0xC00
        strh r8, [r4, #0x36]
        mov r0, #0
        mvn r8, #0xCF
        strh r8, [r4, #0x42]
        strh r0, [r4, #0x44]
        strh r0, [r4, #0x46]
        strh r0, [r4, #0x48]
        strh r0, [r4, #0x94]
        strh r0, [r4, #0x96]
        adr r8, update
        str r8, [r4]
        bl update
        pop {lr}
        bx lr

    update:
        push {lr}
        ldrsh r8, [r4, #0x34]
        cmn r8, #0x200
        bgt continue_update
        bl 0x0836D750
        pop {lr}
        bx lr
    continue_update:
        push {r5}
        push {fp}
        mov r8, #1
        push {r8}
        bl 0x08012A84
        add sp, sp, #12
        ldrh r8, [r4, #0x94]
        push {r8}
        bl 0x08012348
        add sp, sp, #4
        asr r0, r0, #1
        strh r0, [r4, #0x44]
        ldrh r8, [r4, #0x96]
        add r8, r8, #1
        and r8, r8, #3
        strh r8, [r4, #0x96]
        cmp r8, #0
        bne shoot_right_return
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
    shoot_right_return:
        pop {lr}
        bx lr
    """, SHOOT_OBJECT_CALLBACK_RIGHT)


def build_update_dispatch_hook() -> bytes:
    words = [
        0xE59F8010,  # ldr r8, [pc, #0x10]
        0xE7989101,  # ldr r9, [r8, r1, lsl #2]
        0xE1A0E00F,  # mov lr, pc
        0xE12FFF19,  # bx r9
        arm_branch(
            GBA_BASE + UPDATE_DISPATCH_HOOK + 0x10,
            GBA_BASE + UPDATE_DISPATCH_RETURN,
        ),
        0xE1A00000,  # nop / literal alignment
        GBA_BASE + UPDATE_STAGE_TABLE,
    ]
    return struct.pack(f"<{len(words)}I", *words)


def build_spawn_hook(source: bytes) -> bytes:
    """Relocate the retail spawn calculation and extend its stage>=7 bias.

    Stage 6 owns an extra 16-byte variation record.  Retail therefore adds
    0x10 only for stage 7.  The appended stages live after stage 7 and need
    the same bias, so the copied ADDEQ becomes ADDHS.
    """
    words = list(struct.unpack("<24I", source[SPAWN_SITE:SPAWN_RETURN]))
    if words[5] != 0x02811010:
        raise SystemExit("spawn-stage bias instruction check failed")
    if words[15] != 0xE28F80F8:
        raise SystemExit("spawn-table base instruction check failed")
    words[5] = 0x22811010  # addhs r1, r1, #0x10
    words[15] = 0xE59F8020  # ldr r8, [pc, #0x20] -> expanded table literal
    words.append(arm_branch(GBA_BASE + SPAWN_HOOK + 0x60, GBA_BASE + SPAWN_RETURN))
    words.append(GBA_BASE + SPAWN_TABLE)
    return struct.pack(f"<{len(words)}I", *words)


def build_stage_id_map_hook(register: int, return_offset: int) -> bytes:
    """Map new stage IDs to safe retail analogs without altering battle state.

    The mapped value is consumed only by legacy per-stage tables: train uses
    stage 0, the vertical waterfall uses stage 6, and Iraira Room uses digital
    stage 3.  Dedicated stage initializers still see IDs 8..10.
    """
    if register == 9:  # sb, loaded from [r8,#0xe]
        words = [
            0xE5D8900E,
            0xE3590008, 0x03A09000,
            0xE3590009, 0x03A09006,
            0xE359000A, 0x03A09003,
            0xE359000B, 0x03A09007,
        ]
        target = STAGE_SETUP_MAP_HOOK
    elif register == 5:  # r5, loaded from [r5,#0xe]
        words = [
            0xE5D5500E,
            0xE3550008, 0x03A05000,
            0xE3550009, 0x03A05006,
            0xE355000A, 0x03A05003,
            0xE355000B, 0x03A05007,
        ]
        target = STAGE_BOUNDS_MAP_HOOK
    else:
        raise ValueError("unsupported stage-map register")
    words.append(arm_branch(GBA_BASE + target + len(words) * 4, GBA_BASE + return_offset))
    return struct.pack(f"<{len(words)}I", *words)


def descriptor_blob(map_target: int, indices: tuple[int, ...]) -> bytes:
    return b"".join(
        struct.pack("<2I", 257, GBA_BASE + map_target + index * 0x3F0)
        for index in indices
    )


def resource_entry(template: bytes, width: int, height: int, descriptor: int) -> bytes:
    entry = bytearray(template)
    struct.pack_into("<HH", entry, 0, width, height)
    struct.pack_into("<I", entry, 8, GBA_BASE + descriptor)
    struct.pack_into("<III", entry, 12, 0, 0, 0)
    return bytes(entry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("asset_dir", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--wsc15", type=pathlib.Path, required=True)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    if hashlib.sha256(source).hexdigest().upper() != INPUT_SHA256:
        raise SystemExit("refusing unknown integrated character build")
    if struct.unpack_from("<I", source, DISPATCH_SITE)[0] != 0xE28F8E17:
        raise SystemExit("stage-dispatch hook-site check failed")
    if struct.unpack_from("<I", source, SELECTOR_SITE)[0] != 0xE59F8004:
        raise SystemExit("stage-selector hook-site check failed")
    if struct.unpack_from("<I", source, UPDATE_DISPATCH_SITE)[0] != 0xE28F8018:
        raise SystemExit("stage-update dispatch hook-site check failed")
    if struct.unpack_from("<I", source, SPAWN_SITE)[0] != 0xE59F81C8:
        raise SystemExit("fighter spawn hook-site check failed")
    if struct.unpack_from("<I", source, AUX_STAGE_POINTER_SITE)[0] != 0x0835B19C:
        raise SystemExit("auxiliary stage-table pointer check failed")
    if struct.unpack_from("<I", source, STAGE_SETUP_MAP_SITE)[0] != 0xE5D8900E:
        raise SystemExit("stage setup map hook-site check failed")
    if struct.unpack_from("<I", source, STAGE_BOUNDS_MAP_SITE)[0] != 0xE5D5500E:
        raise SystemExit("stage bounds map hook-site check failed")
    if struct.unpack_from("<I", source, VERTICAL_FLAG_R0_SITE)[0] != 0xE3800A02:
        raise SystemExit("vertical-stage r0 flag hook-site check failed")
    if struct.unpack_from("<I", source, VERTICAL_FLAG_R8_SITE)[0] != 0xE3888A02:
        raise SystemExit("vertical-stage r8 flag hook-site check failed")
    if struct.unpack_from("<I", source, STAGE_DIMENSION_MAP_SITE)[0] != 0xE1A05101:
        raise SystemExit("stage dimension map hook-site check failed")
    if struct.unpack_from("<I", source, OBJECT_CONFIG_TABLE_SITE)[0] != 0xE28F90C4:
        raise SystemExit("object configuration table hook-site check failed")
    expected_selector_call = lambda site: arm_branch(
        GBA_BASE + site, GBA_BASE + SELECTOR_SITE, link=True
    )
    for site in LEGACY_STAGE_SELECTOR_SITES:
        if struct.unpack_from("<I", source, site)[0] != expected_selector_call(site):
            raise SystemExit(f"legacy stage selector call check failed at 0x{site:06X}")
    if struct.unpack_from("<I", source, OBJECT_PATTERN_POINTER_SITE)[0] != (
        GBA_BASE + ORIGINAL_OBJECT_PATTERN_TABLE
    ):
        raise SystemExit("object pattern table pointer check failed")

    wsc15 = args.wsc15.read_bytes()
    if hashlib.sha256(wsc15).hexdigest().upper() != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")

    # The commercial converter expands each WSC (count, divisor, near-pointer)
    # record from 4 to 8 bytes and retains the referenced 0x20-byte pattern
    # verbatim. Prove that rule on all nine records retained in the USA ROM
    # before applying it to the three Ver. 1.5-only records.
    object_pattern_records = bytearray()
    object_pattern_data = bytearray()
    for index in range(12):
        record_offset = WSC15_OBJECT_PATTERN_RECORDS + index * 4
        count, divisor, logical_pointer = struct.unpack_from("<BBH", wsc15, record_offset)
        pattern_offset = WSC15_OBJECT_OVERLAY_BASE + logical_pointer
        pattern = wsc15[pattern_offset:pattern_offset + 0x20]
        if len(pattern) != 0x20:
            raise SystemExit(f"WSC object pattern {index} falls outside ROM")
        if index < 9:
            gba_record_offset = ORIGINAL_OBJECT_PATTERN_TABLE + index * 8
            gba_count, gba_divisor, gba_pointer = struct.unpack_from(
                "<HHI", source, gba_record_offset
            )
            if (gba_count, gba_divisor) != (count, divisor):
                raise SystemExit(f"object pattern record {index} conversion check failed")
            gba_pattern_offset = gba_pointer - GBA_BASE
            if source[gba_pattern_offset:gba_pattern_offset + 0x20] != pattern:
                raise SystemExit(f"object pattern {index} payload check failed")
            target_pointer = gba_pointer
        else:
            target_pointer = GBA_BASE + OBJECT_PATTERN_DATA + len(object_pattern_data)
            object_pattern_data.extend(pattern)
        object_pattern_records.extend(struct.pack("<HHI", count, divisor, target_pointer))

    # The WSC table stores (resource bank, near pointer) pairs.  The commercial
    # GBA conversion keeps the bank as a 32-bit value and expands the near
    # pointer to an ARM address.  Each pointed-to WSC pair contains two 16-byte
    # object records; the converter copies the first 14 bytes of each record,
    # inserts two padding bytes, and replaces its final callback-table near
    # pointer with a 32-bit address.  Prove this on all eight retail stages
    # before applying the same rule to the Ver. 1.5 train pair.
    retail_object_config_table = source[
        ORIGINAL_OBJECT_CONFIG_TABLE:ORIGINAL_OBJECT_CONFIG_TABLE + 8 * 8
    ]
    for stage_id in range(8):
        wsc_bank, wsc_config_pointer = struct.unpack_from(
            "<HH", wsc15, WSC15_OBJECT_CONFIG_TABLE + stage_id * 4
        )
        gba_bank, gba_config_pointer = struct.unpack_from(
            "<II", retail_object_config_table, stage_id * 8
        )
        if gba_bank != wsc_bank:
            raise SystemExit(f"object config bank {stage_id} conversion check failed")
        wsc_config_offset = WSC15_OBJECT_OVERLAY_BASE + wsc_config_pointer
        gba_config_offset = gba_config_pointer - GBA_BASE
        for record_id in range(2):
            wsc_record = wsc15[
                wsc_config_offset + record_id * 0x10:
                wsc_config_offset + (record_id + 1) * 0x10
            ]
            gba_record = source[
                gba_config_offset + record_id * 0x14:
                gba_config_offset + (record_id + 1) * 0x14
            ]
            if gba_record[:14] != wsc_record[:14] or gba_record[14:16] != b"\0\0":
                raise SystemExit(
                    f"object config record {stage_id}:{record_id} conversion check failed"
                )
            callback_slot = struct.unpack_from("<I", gba_record, 16)[0] - GBA_BASE
            if not (0 <= callback_slot <= len(source) - 4):
                raise SystemExit(
                    f"object config callback {stage_id}:{record_id} falls outside GBA ROM"
                )

    def convert_new_object_config(
        stage_id: int,
        expected: tuple[int, int],
        expected_callbacks: list[int],
        callback_slots: int,
    ) -> tuple[int, bytes]:
        bank, config_pointer = struct.unpack_from(
            "<HH", wsc15, WSC15_OBJECT_CONFIG_TABLE + stage_id * 4
        )
        if (bank, config_pointer) != expected:
            raise SystemExit(f"unexpected WSC stage-{stage_id} object configuration")
        config_source = WSC15_OBJECT_OVERLAY_BASE + config_pointer
        callback_pointers = []
        converted = bytearray()
        for record_id in range(2):
            record = wsc15[
                config_source + record_id * 0x10:
                config_source + (record_id + 1) * 0x10
            ]
            callback_pointers.append(struct.unpack_from("<H", record, 14)[0])
            converted.extend(record[:14])
            converted.extend(b"\0\0")
            converted.extend(struct.pack(
                "<I", GBA_BASE + callback_slots + record_id * 4
            ))
        if callback_pointers != expected_callbacks:
            raise SystemExit(f"unexpected WSC stage-{stage_id} object callbacks")
        return bank, bytes(converted)

    train_bank, train_object_config_data = convert_new_object_config(
        8, (2, 0x4781), [0x481B, 0x481D], OBJECT_CALLBACK_SLOTS
    )
    waterfall_bank, waterfall_object_config_data = convert_new_object_config(
        9, (3, 0x47A1), [0x481F, 0x4821], WATERFALL_CALLBACK_SLOTS
    )
    iraira_bank, iraira_object_config_data = convert_new_object_config(
        10, (2, 0x47D1), [0x4825, 0x4827], IRAIRA_CALLBACK_SLOTS
    )
    shoot_bank, shoot_object_config_data = convert_new_object_config(
        11, (2, 0x47F1), [0x4829, 0x482B], SHOOT_CALLBACK_SLOTS
    )

    # All four appended stages now receive their native Ver. 1.5 pairs. Shoot
    # still requires its dedicated minigame loop even though its presentation
    # objects no longer use a retail analog.
    object_config_table = (
        retail_object_config_table
        + struct.pack("<II", train_bank, GBA_BASE + OBJECT_CONFIG_DATA)
        + struct.pack("<II", waterfall_bank, GBA_BASE + WATERFALL_OBJECT_CONFIG)
        + struct.pack("<II", iraira_bank, GBA_BASE + IRAIRA_OBJECT_CONFIG)
        + struct.pack("<II", shoot_bank, GBA_BASE + SHOOT_OBJECT_CONFIG)
    )
    if (
        len(object_config_table) != 12 * 8
        or len(train_object_config_data) != 2 * 0x14
        or len(waterfall_object_config_data) != 2 * 0x14
        or len(iraira_object_config_data) != 2 * 0x14
        or len(shoot_object_config_data) != 2 * 0x14
    ):
        raise AssertionError("expanded object configuration size invariant failed")
    train_callback_slots = struct.pack(
        "<II",
        GBA_BASE + TRAIN_OBJECT_CALLBACK_LEFT,
        GBA_BASE + TRAIN_OBJECT_CALLBACK_RIGHT,
    )
    waterfall_callback_slots = struct.pack(
        "<II",
        GBA_BASE + WATERFALL_OBJECT_CALLBACK_LEFT,
        GBA_BASE + WATERFALL_OBJECT_CALLBACK_RIGHT,
    )
    iraira_callback_slots = struct.pack(
        "<II",
        GBA_BASE + IRAIRA_OBJECT_CALLBACK_LEFT,
        GBA_BASE + IRAIRA_OBJECT_CALLBACK_RIGHT,
    )
    shoot_callback_slots = struct.pack(
        "<II",
        GBA_BASE + SHOOT_OBJECT_CALLBACK_LEFT,
        GBA_BASE + SHOOT_OBJECT_CALLBACK_RIGHT,
    )

    train_gradient_wsc = struct.unpack_from(
        "<21H", wsc15, 0x75F94C
    )
    train_gradient = struct.pack(
        "<21H", *(convert_color(value) for value in train_gradient_wsc)
    )
    train_palette_wsc = struct.unpack_from(
        "<24H", wsc15, WSC15_STAGE_OVERLAY_BASE + 0x19B2
    )
    train_palette = struct.pack(
        "<24H", *(convert_color(value) for value in train_palette_wsc)
    )
    waterfall_palette_wsc = struct.unpack_from(
        "<58H", wsc15, WSC15_STAGE_OVERLAY_BASE + 0x1AF3
    )
    waterfall_palette = struct.pack(
        "<58H", *(convert_color(value) for value in waterfall_palette_wsc)
    )
    iraira_palette_wsc = struct.unpack_from(
        "<256H", wsc15, WSC15_STAGE_OVERLAY_BASE + 0x1DA3
    )
    iraira_palette = struct.pack(
        "<256H", *(convert_color(value) for value in iraira_palette_wsc)
    )

    asset_manifest = json.loads((args.asset_dir / "stage-assets.json").read_text(encoding="utf-8"))
    patched = bytearray(source)
    placements: list[dict[str, object]] = []
    for stage, spec in STAGES.items():
        outputs = asset_manifest["stages"][stage]["outputs"]
        for kind in ("palette", "tiles", "maps"):
            item = outputs[kind]
            blob = (args.asset_dir / item["file"]).read_bytes()
            if hashlib.sha256(blob).hexdigest().upper() != item["sha256"]:
                raise SystemExit(f"{item['file']} does not match stage manifest")
            target = int(item["target"])
            if target != spec[kind]:
                raise SystemExit(f"unexpected target for {item['file']}")
            if stage == "impmon" and kind in RETAIL_IMPMON_SHARED:
                retail = RETAIL_IMPMON_SHARED[kind]
                if blob != source[retail:retail + len(blob)]:
                    raise SystemExit(f"{item['file']} does not exactly reuse retail stage 3")
            if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
                raise SystemExit(f"stage target for {item['file']} is not blank")
            patched[target:target + len(blob)] = blob
            placements.append({"name": item["file"], "target": target, "bytes": len(blob)})

    # Preserve all retail resources and append eight stage-specific resources.
    resource_table = bytearray(source[
        RESOURCE_SOURCE:RESOURCE_SOURCE + ORIGINAL_RESOURCE_COUNT * RESOURCE_BYTES
    ])
    descriptor_parts: list[bytes] = []
    descriptor_cursor = DESCRIPTOR_TARGET
    simple_template = source[RESOURCE_SOURCE + RESOURCE_BYTES:RESOURCE_SOURCE + 2 * RESOURCE_BYTES]
    definitions = [
        (2, 2, STAGES["train"]["maps"], tuple(range(start, start + 4)))
        for start in (0, 4, 8, 12)
    ] + [
        (2, 2, STAGES["impmon"]["maps"], tuple(range(start, start + 4)))
        for start in (0, 4)
    ] + [
        (1, 3, STAGES["waterfall"]["maps"], tuple(range(start, start + 3)))
        for start in (0, 3)
    ] + [
        (2, 2, STAGES["shoot"]["maps"], tuple(range(start, start + 4)))
        for start in (0, 4)
    ]
    for width, height, map_target, map_indices in definitions:
        descriptors = descriptor_blob(map_target, map_indices)
        resource_table.extend(resource_entry(simple_template, width, height, descriptor_cursor))
        descriptor_parts.append(descriptors)
        descriptor_cursor += len(descriptors)
    if len(resource_table) != EXPANDED_RESOURCE_COUNT * RESOURCE_BYTES:
        raise AssertionError("expanded stage-resource table size invariant failed")
    descriptor_data = b"".join(descriptor_parts)
    for target, blob, label in (
        (RESOURCE_TARGET, resource_table, "expanded stage-resource table"),
        (DESCRIPTOR_TARGET, descriptor_data, "new stage descriptors"),
    ):
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is not blank")
        patched[target:target + len(blob)] = blob

    old_resource_pointer = GBA_BASE + RESOURCE_SOURCE
    new_resource_pointer = GBA_BASE + RESOURCE_TARGET
    resource_pointer_sites = tuple(
        offset for offset in range(0, len(source) - 3, 4)
        if struct.unpack_from("<I", source, offset)[0] == old_resource_pointer
    )
    if len(resource_pointer_sites) != 32:
        raise SystemExit(f"unexpected stage-resource pointer population: {len(resource_pointer_sites)}")
    for site in resource_pointer_sites:
        struct.pack_into("<I", patched, site, new_resource_pointer)

    clone_placements = []
    for stage, target in CLONE_TARGETS.items():
        spec = STAGES[stage]
        clone = relocate_stage_clone(
            source, target, spec=CLONE_SPECS[stage], palette=spec["palette"],
            tiles=spec["tiles"], indices=spec["indices"]
        )
        if patched[target:target + len(clone)] != bytes([0xFF]) * len(clone):
            raise SystemExit(f"{stage} initializer clone target is not blank")
        patched[target:target + len(clone)] = clone
        clone_placements.append({"stage": stage, "target": target, "bytes": len(clone)})

    retail_stage_table = source[0x03F038:0x03F058]
    stage_table = retail_stage_table + struct.pack(
        "<4I", *(GBA_BASE + CLONE_TARGETS[name]
                 for name in ("train", "waterfall", "impmon", "shoot"))
    )
    retail_update_table = source[0x015DBC:0x015DDC]
    retail_update_functions = struct.unpack("<8I", retail_update_table)
    update_stage_table = retail_update_table + struct.pack(
        "<4I",
        GBA_BASE + TRAIN_UPDATE,
        GBA_BASE + WATERFALL_UPDATE,
        GBA_BASE + IRAIRA_UPDATE,
        GBA_BASE + UPDATE_STUB,
    )
    update_stub = struct.pack("<I", 0xE12FFF1E)  # bx lr

    retail_spawn_table = source[0x35326C:0x3532FC]
    if len(retail_spawn_table) != 0x90:
        raise AssertionError("retail spawn table size invariant failed")
    spawn_table = retail_spawn_table + b"".join(
        WSC15_SPAWN_RECORDS[name] for name in ("train", "waterfall", "impmon")
    ) + retail_spawn_table[-0x10:]
    if len(spawn_table) != 0xD0:
        raise AssertionError("expanded spawn table size invariant failed")

    retail_aux_stage_table = source[0x35B19C:0x35B21C]
    if len(retail_aux_stage_table) != 0x80:
        raise AssertionError("retail auxiliary stage table size invariant failed")
    aux_stage_table = retail_aux_stage_table + WSC15_AUX_RECORD * 4
    if len(aux_stage_table) != 0xC0:
        raise AssertionError("expanded auxiliary stage table size invariant failed")

    for target, blob, label in (
        (DISPATCH_HOOK, build_dispatch_hook(), "stage dispatch hook"),
        (SELECTOR_HOOK, build_selector_hook(), "character stage-routing hook"),
        (STAGE_TABLE, stage_table, "expanded stage function table"),
        (UPDATE_DISPATCH_HOOK, build_update_dispatch_hook(), "stage-update dispatch hook"),
        (UPDATE_STAGE_TABLE, update_stage_table, "expanded stage-update table"),
        (UPDATE_STUB, update_stub, "new-stage update safety stub"),
        (SPAWN_HOOK, build_spawn_hook(source), "expanded fighter-spawn hook"),
        (SPAWN_TABLE, spawn_table, "expanded fighter-spawn table"),
        (AUX_STAGE_TABLE, aux_stage_table, "expanded auxiliary stage table"),
        (
            STAGE_SETUP_MAP_HOOK,
            build_stage_id_map_hook(9, STAGE_SETUP_MAP_RETURN),
            "legacy stage-setup map hook",
        ),
        (
            STAGE_BOUNDS_MAP_HOOK,
            build_stage_id_map_hook(5, STAGE_BOUNDS_MAP_RETURN),
            "legacy stage-bounds map hook",
        ),
        (TRAIN_UPDATE, build_train_update(), "train stage update"),
        (TRAIN_SCROLL_HELPER, build_train_scroll_helper(), "train scroll helper"),
        (TRAIN_PALETTE_HELPER, build_train_palette_helper(), "train palette helper"),
        (
            TRAIN_PRIMARY_CALLBACK,
            build_train_primary_callback(source, train_gradient),
            "train primary display callback",
        ),
        (TRAIN_PALETTE_TABLE, train_palette, "train palette-cycle table"),
        (
            WATERFALL_UPDATE,
            build_simple_stage_update(
                WATERFALL_UPDATE,
                WATERFALL_PALETTE_HELPER,
                call_common=True,
                mechanics_helper=WATERFALL_HAZARD_HELPER,
            ),
            "waterfall stage update",
        ),
        (
            WATERFALL_PALETTE_HELPER,
            build_waterfall_palette_helper(),
            "waterfall palette helper",
        ),
        (
            IRAIRA_UPDATE,
            build_simple_stage_update(
                IRAIRA_UPDATE, IRAIRA_PALETTE_HELPER, call_common=False
            ),
            "Iraira Room stage update",
        ),
        (
            IRAIRA_PALETTE_HELPER,
            build_iraira_palette_helper(),
            "Iraira Room palette helper",
        ),
        (
            FLICKER_CALLBACK,
            build_flicker_callback(source),
            "waterfall/Iraira display callback",
        ),
        (
            FLICKER_CALLBACK_HELPER,
            build_flicker_callback_helper(),
            "waterfall/Iraira display callback tail",
        ),
        (
            WATERFALL_PALETTE_TABLES,
            waterfall_palette,
            "waterfall palette-cycle tables",
        ),
        (
            IRAIRA_PALETTE_TABLES,
            iraira_palette,
            "Iraira Room palette-cycle tables",
        ),
        (
            WATERFALL_HAZARD_HELPER,
            build_waterfall_hazard_helper(),
            "waterfall rolling-hazard state machine",
        ),
        (
            WATERFALL_HAZARD_TABLE,
            struct.pack("<6H", 5, 7, 1, 7, 1, 3),
            "waterfall rolling-hazard mode table",
        ),
        (
            VERTICAL_FLAG_R0_HELPER,
            build_vertical_flag_helper(VERTICAL_FLAG_R0_HELPER, 0),
            "waterfall/Iraira object-flag r0 helper",
        ),
        (
            VERTICAL_FLAG_R8_HELPER,
            build_vertical_flag_helper(VERTICAL_FLAG_R8_HELPER, 8),
            "waterfall/Iraira object-flag r8 helper",
        ),
        (
            LEGACY_STAGE_SELECTOR,
            build_legacy_stage_selector(),
            "bounded selector for eight-entry retail consumers",
        ),
        (
            STAGE_DIMENSION_MAP_HELPER,
            build_stage_dimension_map_helper(),
            "legacy stage-dimension index map helper",
        ),
        (
            OBJECT_PATTERN_TABLE,
            bytes(object_pattern_records),
            "expanded Ver. 1.5 object-pattern table",
        ),
        (
            OBJECT_PATTERN_DATA,
            bytes(object_pattern_data),
            "Ver. 1.5 object-pattern payloads",
        ),
        (
            OBJECT_CONFIG_TABLE,
            object_config_table,
            "expanded stage object-configuration table",
        ),
        (
            OBJECT_CONFIG_DATA,
            bytes(train_object_config_data),
            "native Ver. 1.5 train object configuration",
        ),
        (
            WATERFALL_OBJECT_CONFIG,
            bytes(waterfall_object_config_data),
            "native Ver. 1.5 waterfall object configuration",
        ),
        (
            IRAIRA_OBJECT_CONFIG,
            bytes(iraira_object_config_data),
            "native Ver. 1.5 Iraira object configuration",
        ),
        (
            SHOOT_OBJECT_CONFIG,
            bytes(shoot_object_config_data),
            "native Ver. 1.5 Shoot object configuration",
        ),
        (
            OBJECT_CONFIG_TABLE_HOOK,
            build_object_config_table_hook(),
            "expanded object-configuration table hook",
        ),
        (
            OBJECT_CALLBACK_SLOTS,
            train_callback_slots,
            "native train object callback slots",
        ),
        (
            WATERFALL_CALLBACK_SLOTS,
            waterfall_callback_slots,
            "native waterfall object callback slots",
        ),
        (
            IRAIRA_CALLBACK_SLOTS,
            iraira_callback_slots,
            "native Iraira object callback slots",
        ),
        (
            SHOOT_CALLBACK_SLOTS,
            shoot_callback_slots,
            "native Shoot object callback slots",
        ),
        (
            TRAIN_OBJECT_CALLBACK_LEFT,
            build_train_object_callback_left(),
            "native train left object callback",
        ),
        (
            TRAIN_OBJECT_CALLBACK_RIGHT,
            build_train_object_callback_right(),
            "native train right object callback",
        ),
        (
            WATERFALL_OBJECT_CALLBACK_LEFT,
            build_waterfall_object_callback_left(),
            "native waterfall mode-1 object callback",
        ),
        (
            WATERFALL_OBJECT_CALLBACK_RIGHT,
            build_waterfall_object_callback_right(),
            "native waterfall mode-2 object callback",
        ),
        (
            IRAIRA_OBJECT_CALLBACK_LEFT,
            build_iraira_object_callback_left(),
            "native Iraira oscillating object callback",
        ),
        (
            IRAIRA_OBJECT_CALLBACK_RIGHT,
            build_iraira_object_callback_right(),
            "native Iraira right object callback",
        ),
        (
            SHOOT_OBJECT_CALLBACK_LEFT,
            build_shoot_object_callback_left(),
            "native Shoot left presentation callback",
        ),
        (
            SHOOT_OBJECT_CALLBACK_RIGHT,
            build_shoot_object_callback_right(),
            "native Shoot right presentation callback",
        ),
    ):
        if patched[target:target + len(blob)] != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} target is not blank")
        patched[target:target + len(blob)] = blob
    struct.pack_into("<I", patched, DISPATCH_SITE, arm_branch(GBA_BASE + DISPATCH_SITE, GBA_BASE + DISPATCH_HOOK))
    struct.pack_into("<I", patched, SELECTOR_SITE, arm_branch(GBA_BASE + SELECTOR_SITE, GBA_BASE + SELECTOR_HOOK))
    struct.pack_into(
        "<I", patched, UPDATE_DISPATCH_SITE,
        arm_branch(GBA_BASE + UPDATE_DISPATCH_SITE, GBA_BASE + UPDATE_DISPATCH_HOOK),
    )
    struct.pack_into(
        "<I", patched, SPAWN_SITE,
        arm_branch(GBA_BASE + SPAWN_SITE, GBA_BASE + SPAWN_HOOK),
    )
    struct.pack_into("<I", patched, AUX_STAGE_POINTER_SITE, GBA_BASE + AUX_STAGE_TABLE)
    struct.pack_into(
        "<I", patched, STAGE_SETUP_MAP_SITE,
        arm_branch(GBA_BASE + STAGE_SETUP_MAP_SITE, GBA_BASE + STAGE_SETUP_MAP_HOOK),
    )
    struct.pack_into(
        "<I", patched, STAGE_BOUNDS_MAP_SITE,
        arm_branch(GBA_BASE + STAGE_BOUNDS_MAP_SITE, GBA_BASE + STAGE_BOUNDS_MAP_HOOK),
    )
    struct.pack_into(
        "<I", patched, VERTICAL_FLAG_R0_SITE,
        arm_branch(
            GBA_BASE + VERTICAL_FLAG_R0_SITE,
            GBA_BASE + VERTICAL_FLAG_R0_HELPER,
            link=True,
        ),
    )
    struct.pack_into(
        "<I", patched, VERTICAL_FLAG_R8_SITE,
        arm_branch(
            GBA_BASE + VERTICAL_FLAG_R8_SITE,
            GBA_BASE + VERTICAL_FLAG_R8_HELPER,
            link=True,
        ),
    )
    struct.pack_into(
        "<I", patched, STAGE_DIMENSION_MAP_SITE,
        arm_branch(
            GBA_BASE + STAGE_DIMENSION_MAP_SITE,
            GBA_BASE + STAGE_DIMENSION_MAP_HELPER,
        ),
    )
    struct.pack_into(
        "<I", patched, OBJECT_CONFIG_TABLE_SITE,
        arm_branch(
            GBA_BASE + OBJECT_CONFIG_TABLE_SITE,
            GBA_BASE + OBJECT_CONFIG_TABLE_HOOK,
        ),
    )
    for site in LEGACY_STAGE_SELECTOR_SITES:
        struct.pack_into(
            "<I", patched, site,
            arm_branch(
                GBA_BASE + site,
                GBA_BASE + LEGACY_STAGE_SELECTOR,
                link=True,
            ),
        )
    struct.pack_into(
        "<I", patched, OBJECT_PATTERN_POINTER_SITE,
        GBA_BASE + OBJECT_PATTERN_TABLE,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(patched)
    result = {
        "schema": 1,
        "kind": "internal-stage-integration-build",
        "claim_scope": (
            "static stage assets, corrected resource geometry, initializer/update dispatch, "
            "character routes, confirmed legacy stage-table bounds, native Ver. 1.5 "
            "object configurations/callbacks for stages 8..11, and translated display/"
            "palette paths; remaining Iraira suction integration, Digimon Shoot dedicated "
            "runtime logic, and integrated runtime QA deferred"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": hashlib.sha256(patched).hexdigest().upper(),
        "output_bytes": len(patched),
        "placements": placements,
        "resource_table_target": RESOURCE_TARGET,
        "resource_count": EXPANDED_RESOURCE_COUNT,
        "resource_pointer_sites": list(resource_pointer_sites),
        "descriptor_target": DESCRIPTOR_TARGET,
        "descriptor_bytes": len(descriptor_data),
        "initializer_clones": clone_placements,
        "dispatch_hook": DISPATCH_HOOK,
        "selector_hook": SELECTOR_HOOK,
        "stage_table": STAGE_TABLE,
        "update_dispatch_hook": UPDATE_DISPATCH_HOOK,
        "update_stage_table": UPDATE_STAGE_TABLE,
        "update_stub": UPDATE_STUB,
        "train_mechanics": {
            "update": TRAIN_UPDATE,
            "scroll_helper": TRAIN_SCROLL_HELPER,
            "palette_helper": TRAIN_PALETTE_HELPER,
            "primary_callback": TRAIN_PRIMARY_CALLBACK,
            "standard_callback": "retail 0x080C94FC; byte-exact WSC callback lineage",
            "gradient_source": "WSC 1.5 physical 0x75F94C (5EEA:0AAC)",
            "palette_source": "WSC 1.5 stage overlay relative 0x19B2",
            "claim": "static ARM translation; runtime QA deferred",
        },
        "waterfall_mechanics": {
            "update": WATERFALL_UPDATE,
            "palette_helper": WATERFALL_PALETTE_HELPER,
            "display_callback": FLICKER_CALLBACK,
            "rolling_hazard_helper": WATERFALL_HAZARD_HELPER,
            "rolling_hazard_table": WATERFALL_HAZARD_TABLE,
            "rolling_hazard_source": "WSC 1.5 stage overlay relative 0x1C53..0x1D85",
            "palette_source": "WSC 1.5 stage overlay relative 0x1AF3..0x1B67",
            "claim": (
                "static display/palette/rolling-hazard state-machine translation plus "
                "native mode-1/mode-2 object configuration and callbacks; runtime QA deferred"
            ),
        },
        "iraira_mechanics": {
            "update": IRAIRA_UPDATE,
            "palette_helper": IRAIRA_PALETTE_HELPER,
            "display_callback": FLICKER_CALLBACK,
            "palette_source": "WSC 1.5 stage overlay relative 0x1DA3..0x1FA3",
            "claim": (
                "static display/palette translation plus native object configuration "
                "and callbacks; remaining stage-level suction integration pending"
            ),
        },
        "spawn_hook": SPAWN_HOOK,
        "spawn_table": SPAWN_TABLE,
        "spawn_table_bytes": len(spawn_table),
        "shoot_spawn_record": (
            "bounded safety copy of retail stage-7 record; Digimon Shoot uses "
            "its dedicated mode and must not enter fighter-spawn setup"
        ),
        "spawn_record_sources": {
            "train": "WSC 1.5 ROM 0x7432B4",
            "waterfall": "WSC 1.5 ROM 0x7432C4",
            "impmon": "WSC 1.5 ROM 0x7432D4",
        },
        "aux_stage_table": AUX_STAGE_TABLE,
        "aux_stage_table_bytes": len(aux_stage_table),
        "stage_setup_map_hook": STAGE_SETUP_MAP_HOOK,
        "stage_bounds_map_hook": STAGE_BOUNDS_MAP_HOOK,
        "legacy_stage_selector": {
            "helper": LEGACY_STAGE_SELECTOR,
            "patched_call_sites": list(LEGACY_STAGE_SELECTOR_SITES),
            "dimension_index_site": STAGE_DIMENSION_MAP_SITE,
            "dimension_index_helper": STAGE_DIMENSION_MAP_HELPER,
            "claim": (
                "static bounds hardening for confirmed eight-entry retail consumers; "
                "native Ver. 1.5 object configurations are handled by a separate "
                "twelve-entry table"
            ),
        },
        "object_pattern_extension": {
            "table": OBJECT_PATTERN_TABLE,
            "records": 12,
            "new_payloads": OBJECT_PATTERN_DATA,
            "new_payload_bytes": len(object_pattern_data),
            "source_records": WSC15_OBJECT_PATTERN_RECORDS,
            "source_payloads": WSC15_OBJECT_PATTERN_BYTES,
            "pointer_site": OBJECT_PATTERN_POINTER_SITE,
            "claim": (
                "first nine records and payloads verified against the commercial GBA "
                "conversion; Ver. 1.5 records 9..11 converted by the same rule"
            ),
        },
        "object_config_extension": {
            "table": OBJECT_CONFIG_TABLE,
            "records": 12,
            "table_hook_site": OBJECT_CONFIG_TABLE_SITE,
            "table_hook": OBJECT_CONFIG_TABLE_HOOK,
            "train_config": OBJECT_CONFIG_DATA,
            "train_config_source": "WSC 1.5 physical 0x745081..0x7450A1",
            "train_callback_slots": OBJECT_CALLBACK_SLOTS,
            "train_callbacks": [
                TRAIN_OBJECT_CALLBACK_LEFT,
                TRAIN_OBJECT_CALLBACK_RIGHT,
            ],
            "train_callback_sources": ["4090:3CD5", "4090:3D7B"],
            "waterfall_config": WATERFALL_OBJECT_CONFIG,
            "waterfall_config_source": "WSC 1.5 physical 0x7450A1..0x7450C1",
            "waterfall_callback_slots": WATERFALL_CALLBACK_SLOTS,
            "waterfall_callbacks": [
                WATERFALL_OBJECT_CALLBACK_LEFT,
                WATERFALL_OBJECT_CALLBACK_RIGHT,
            ],
            "waterfall_callback_sources": ["4090:3DFB", "4090:3EE0"],
            "iraira_config": IRAIRA_OBJECT_CONFIG,
            "iraira_config_source": "WSC 1.5 physical 0x7450D1..0x7450F1",
            "iraira_callback_slots": IRAIRA_CALLBACK_SLOTS,
            "iraira_callbacks": [
                IRAIRA_OBJECT_CALLBACK_LEFT,
                IRAIRA_OBJECT_CALLBACK_RIGHT,
            ],
            "iraira_callback_sources": ["4090:40AF", "4090:42B5"],
            "shoot_config": SHOOT_OBJECT_CONFIG,
            "shoot_config_source": "WSC 1.5 physical 0x7450F1..0x745111",
            "shoot_callback_slots": SHOOT_CALLBACK_SLOTS,
            "shoot_callbacks": [
                SHOOT_OBJECT_CALLBACK_LEFT,
                SHOOT_OBJECT_CALLBACK_RIGHT,
            ],
            "shoot_callback_sources": ["4090:432F", "4090:43E6"],
            "temporary_analogs": {},
            "claim": (
                "retail conversion rule verified for stages 0..7; all Ver. 1.5 stage "
                "configurations and their eight movement/presentation callbacks translated "
                "statically; runtime QA deferred"
            ),
        },
        "vertical_stage_object_flag_hooks": {
            "source_evidence": [
                "WSC 1.5 raw 0x781BEF stage-ID branch",
                "WSC 1.5 raw 0x786C5C stage-ID branch",
            ],
            "gba_sites": [VERTICAL_FLAG_R0_SITE, VERTICAL_FLAG_R8_SITE],
            "helpers": [VERTICAL_FLAG_R0_HELPER, VERTICAL_FLAG_R8_HELPER],
            "effect": (
                "preserve retail object construction except suppress the default "
                "0x2000 flag for actual stage IDs 9 and 10"
            ),
            "claim": "static engine-branch translation; runtime behavior deferred",
        },
        "legacy_stage_analogs": {
            "train": 0,
            "waterfall": 6,
            "impmon": 3,
            "shoot": 7,
        },
        "routes": {"Patamon ID 13": 8, "Tailmon ID 14": 9, "Impmon ID 11": 10},
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
