#!/usr/bin/env python3
"""Install the dedicated Shoot graphics initializer and closed palette consumer.

The palette adapter retains four source counters and three immutable ROM slices
inside the original native 32-byte allocation.  It never expands that allocation
into the adjacent, live fighter state.  No new RAM owner or renderer is added.
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
from convert_wsc_palette_block import convert_color

INPUT_SHA256 = "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E"
BASE = 0x08000000
START, END = 0x5C6800, 0x5C7800
GRAPHICS, STAGE_RESOURCES = 0x5C6800, 0x5C6A00
BOUNDS, BOUNDS_HOOK = 0x5C6B00, 0x5C6C00
PALETTE_INIT, PALETTE_UPDATE = 0x5C6D00, 0x5C6E00
PALETTE_PROJECT, PALETTE_HOOK = 0x5C6F00, 0x5C7100
IRQ_PREAMBLE, SEED = 0x5C7200, 0x5C7300
PALETTE_INIT_HOOK = 0x5C7380
SEED_WORDS = (0x400, 0x200, 0xA00, 0x600, 0xF00, 0xC00,
              0x020, 0x040, 0x060, 0x080, 0x090, 0x0B0, 0x0D0, 0x0F0,
              0x500, 0x700, 0xA55, 0xCAA, 0xFFF)


def code(assembly: str, raw: int, literal_bytes: int) -> tuple[bytes, int]:
    blob = assemble(assembly, raw)
    return blob, len(blob) - literal_bytes


def graphics() -> tuple[bytes, int]:
    return code(f"""
        push {{r0-r12, lr}}
        mov r11, #0
        mov r0, #0
        bl 0x08000CF8
        bl 0x0807FBF8
        ldr r4, control
        ldr r5, backgrounds
        mov r0, #4
    controls:
        str r4, [r5]
        add r8, r4, #1
        str r8, [r5, #4]
        add r5, r5, #0x50
        subs r0, r0, #1
        bne controls
        bl 0x08000CD8
        and r0, r0, #0xFF
        strh r0, [r8]
        bl 0x08015D38
        bl 0x0801369C
        ldr r8, stage
        mov r0, #11
        strh r0, [r8]
        bl 0x{BASE+PALETTE_INIT:08X}
        ldr r8, dimensions
        ldr r0, size
        str r0, [r8]
        ldr r8, camera_clear
        mov r0, #0
        strh r0, [r8]
        ldr r0, white
        ldr r8, backdrop
        strh r0, [r8]
        mov r8, #0x05000000
        strh r0, [r8]
        bl 0x{BASE+STAGE_RESOURCES:08X}
        ldr r4, hud_colors
        ldr r5, hud_palette
        mov r2, #15
        bl 0x080110DC
        ldr r4, hud_pixels
        ldr r5, hud_vram
        mov r2, #0x88
        bl 0x080110F8
        ldr r5, hud_map
        ldr r0, hud_cell
        strh r0, [r5]
        strh r0, [r5, #2]
        strh r0, [r5, #4]
        strh r0, [r5, #6]
        ldr r8, backgrounds
        push {{r8}}
        push {{r11}}
        mov r8, #0x70
        push {{r8}}
        push {{r11}}
        bl 0x08080040
        add sp, sp, #16
        pop {{r0-r12, lr}}
        bx lr
    control: .word 0x030012B8
    backgrounds: .word 0x03002338
    stage: .word 0x03002656
    dimensions: .word 0x03004568
    size: .word 0x01B001C0
    camera_clear: .word 0x0300470A
    white: .word 0x7FFF
    backdrop: .word 0x03002654
    hud_colors: .word 0x0801FD32
    hud_palette: .word 0x050000E2
    hud_pixels: .word 0x0801FD50
    hud_vram: .word 0x06007DE0
    hud_map: .word 0x0600D800
    hud_cell: .word 0x73FF
    """, GRAPHICS, 56)


def stage_resources() -> tuple[bytes, int]:
    # Match the resident clone's entry stack and copy prefix, then continue at
    # its two BG constructors.  The omitted +24..2C store is the generic
    # stage's backdrop color; dedicated 0FC4 has already installed white.
    return code("""
        push {lr}
        ldr r5, palette
        ldr r4, colors
        mov r2, #0x6F
        bl 0x080110DC
        ldr r5, vram
        ldr r4, pixels
        mov r2, #0x1000
        bl 0x080110F8
        b 0x08582A30
    palette: .word 0x05000002
    colors: .word 0x085A8000
    vram: .word 0x06004000
    pixels: .word 0x085A8100
    """, STAGE_RESOURCES, 16)


def bounds() -> tuple[bytes, int]:
    # Source stage11 case 7CCF:15AF invokes the proven common parallax helper
    # with AX=1, BX=2, DI=BG1 and two E0 stack arguments.
    return code("""
        push {r0-r12, lr}
        mov r11, #0
        ldr r4, primary
        add r5, r4, #0x50
        mov r0, #1
        mov r1, #2
        mov r8, #0xE0
        push {r8}
        push {r8}
        bl 0x0807FEB0
        add sp, sp, #8
        ldr r4, primary
        ldr r5, scroll
        mov r2, #4
    copy:
        ldrb r0, [r4, #0x1A]
        strb r0, [r5]
        ldrb r0, [r4, #0x1B]
        strb r0, [r5, #1]
        add r5, r5, #2
        add r4, r4, #0x50
        subs r2, r2, #1
        bne copy
        pop {r0-r12, lr}
        bx lr
    primary: .word 0x03002338
    scroll: .word 0x0300456C
    """, BOUNDS, 8)


def conditional_hook(raw: int, target: int, legacy: int,
                     legacy_registers: str = "r0-r5, lr") -> tuple[bytes, int]:
    return code(f"""
        push {{r0}}
        ldr r0, battle
        ldrb r0, [r0, #0xE]
        cmp r0, #11
        pop {{r0}}
        beq 0x{BASE+target:08X}
        push {{{legacy_registers}}}
        b 0x{legacy:08X}
    battle: .word 0x03002310
    """, raw, 4)


def palette_init() -> tuple[bytes, int]:
    return code(f"""
        push {{r0-r12, lr}}
        ldr r4, state
        mov r0, #0
        mov r2, #8
    clear:
        str r0, [r4], #4
        subs r2, r2, #1
        bne clear
        ldr r4, state
        ldr r0, seed_a
        str r0, [r4, #8]
        add r0, r0, #12
        str r0, [r4, #12]
        add r0, r0, #16
        str r0, [r4, #16]
        pop {{r0-r12, lr}}
        bx lr
    state: .word 0x03003D30
    seed_a: .word 0x{BASE+SEED:08X}
    """, PALETTE_INIT, 8)


def palette_update() -> tuple[bytes, int]:
    return code("""
        push {r0-r12, lr}
        ldr r4, state
        ldr r8, flags
        ldrh r8, [r8]
        tst r8, #8
        ldreq r5, normal
        ldrne r5, alternate
        ldrh r0, [r4]
        add r0, r0, #1
        and r0, r0, #7
        strh r0, [r4]
        cmp r0, #0
        beq slow
        tst r0, #1
        beq done
        ldrh r0, [r4, #4]
        add r1, r0, #1
        and r1, r1, #7
        strh r1, [r4, #4]
        add r2, r5, #0x3C
        add r2, r2, r0, lsl #1
        str r2, [r4, #12]
        ldrh r0, [r4, #6]
        add r1, r0, #1
        cmp r1, #7
        movhs r1, #0
        strh r1, [r4, #6]
        add r2, r5, #0x5A
        add r2, r2, r0, lsl #4
        str r2, [r4, #16]
        b done
    slow:
        ldrh r0, [r4, #2]
        add r1, r0, #1
        cmp r1, #10
        movhs r1, #0
        strh r1, [r4, #2]
        add r2, r5, r0, lsl #2
        str r2, [r4, #8]
    done:
        pop {r0-r12, lr}
        bx lr
    state: .word 0x03003D30
    flags: .word 0x0300450A
    normal: .word 0x08586800
    alternate: .word 0x085868CA
    """, PALETTE_UPDATE, 16)


def palette_project() -> tuple[bytes, int]:
    return code("""
        push {r0-r12, lr}
        ldr r8, flags
        ldrh r0, [r8]
        tst r0, #0x10
        bne done
        ldr r8, disabled
        ldrb r0, [r8]
        cmp r0, #0
        bne done
        ldr r8, dimmed
        ldrb r7, [r8]
        ldr r6, dim_mask
        ldr r5, state
        ldr r4, [r5, #8]
        mov r8, #0x05000000
        add r8, r8, #0x10
        mov r2, #3
    pairs:
        ldrh r0, [r4], #2
        cmp r7, #0
        blne dim
        strh r0, [r8]
        ldrh r0, [r4], #2
        cmp r7, #0
        blne dim
        strh r0, [r8, #2]
        add r8, r8, #0x20
        subs r2, r2, #1
        bne pairs
        ldr r4, [r5, #12]
        mov r8, #0x05000000
        add r8, r8, #0x64
        mov r2, #8
    repeated:
        ldrh r0, [r4], #2
        cmp r7, #0
        blne dim
        strh r0, [r8]
        strh r0, [r8, #0x20]
        strh r0, [r8, #0x40]
        add r8, r8, #2
        subs r2, r2, #1
        bne repeated
        ldr r4, [r5, #16]
        mov r8, #0x05000000
        add r8, r8, #0xC4
        mov r2, #5
    five:
        ldrh r0, [r4], #2
        cmp r7, #0
        blne dim
        strh r0, [r8], #2
        subs r2, r2, #1
        bne five
    done:
        pop {r0-r12, lr}
        bx lr
    dim:
        and r0, r0, r6
        lsr r0, r0, #1
        tst r0, #0x1E
        orrne r0, r0, #1
        tst r0, #0x3C0
        orrne r0, r0, #0x20
        tst r0, #0x7800
        orrne r0, r0, #0x400
        bx lr
    flags: .word 0x03004506
    disabled: .word 0x0300260B
    dimmed: .word 0x03004529
    dim_mask: .word 0x739C
    state: .word 0x03003D30
    """, PALETTE_PROJECT, 20)


def irq_preamble() -> tuple[bytes, int]:
    return code("""
        push {r0-r12, lr}
        ldr r8, interrupt_enable
        ldrh r0, [r8]
        bic r0, r0, #4
        strh r0, [r8]
        ldr r8, backdrop_alias
        ldr r0, white
        strh r0, [r8]
        bl 0x08000CD8
        and r0, r0, #0xFF
        orr r0, r0, #0xF000
        bl 0x08000CF8
        pop {r0-r12, lr}
        bx lr
    interrupt_enable: .word 0x04000200
    backdrop_alias: .word 0x050001E0
    white: .word 0x7FFF
    """, IRQ_PREAMBLE, 12)


def build(original: bytes, sources: dict[str, bytes]) -> tuple[bytes, dict]:
    require_hash(original, INPUT_SHA256, "exact lower-rules predecessor")
    for key, expected in (("gba", GBA_SHA256), ("wsc10", WSC10_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], expected, key)
    if original[START:END] != b"\xFF" * (END - START):
        raise ValueError("graphics expansion window is not unused")
    for site in range(0, len(original)-3, 4):
        word = struct.unpack_from("<I", original, site)[0]
        if BASE+START <= word < BASE+END:
            raise ValueError(f"inbound pointer at {site:X}")
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            if START <= site + 8 + displacement * 4 < END:
                raise ValueError(f"inbound branch at {site:X}")
    rows, machine = [], {}
    for entry, following, label, (blob, n), external in (
        (GRAPHICS, STAGE_RESOURCES, "graphics", graphics(), {0x08000CF8, 0x0807FBF8, 0x08000CD8, 0x08015D38, 0x0801369C, BASE+PALETTE_INIT, BASE+STAGE_RESOURCES, 0x080110DC, 0x080110F8, 0x08080040}),
        (STAGE_RESOURCES, BOUNDS, "stage_resources", stage_resources(), {0x080110DC, 0x080110F8, 0x08582A30}),
        (BOUNDS, BOUNDS_HOOK, "bounds", bounds(), {0x0807FEB0}),
        (BOUNDS_HOOK, PALETTE_INIT, "bounds_hook", conditional_hook(BOUNDS_HOOK, BOUNDS, 0x0807FC38), {BASE+BOUNDS, 0x0807FC38}),
        (PALETTE_INIT, PALETTE_UPDATE, "palette_init", palette_init(), set()),
        (PALETTE_UPDATE, PALETTE_PROJECT, "palette_update", palette_update(), set()),
        (PALETTE_PROJECT, PALETTE_HOOK, "palette_project", palette_project(), set()),
        (PALETTE_HOOK, IRQ_PREAMBLE, "palette_hook", conditional_hook(PALETTE_HOOK, PALETTE_PROJECT, 0x080C4CC8), {BASE+PALETTE_PROJECT, 0x080C4CC8}),
        (IRQ_PREAMBLE, SEED, "irq_preamble", irq_preamble(), {0x08000CD8, 0x08000CF8}),
        (PALETTE_INIT_HOOK, END, "palette_init_hook", conditional_hook(PALETTE_INIT_HOOK, PALETTE_INIT, 0x080C4BC4, "r0-r2, r4-r5, lr"), {BASE+PALETTE_INIT, 0x080C4BC4}),
    ):
        if entry+len(blob) > following:
            raise ValueError(f"code slot overflow: {label}")
        machine[label] = verify_machine_code(blob, entry, n, external)
        rows.append((entry, b"\xFF"*len(blob), blob, label))
    seeds = struct.pack("<19H", *(convert_color(x) for x in SEED_WORDS))
    rows.append((SEED, b"\xFF"*len(seeds), seeds, "initial_color_slices"))
    for site, target, before, label in (
        (0x7FC34, BOUNDS_HOOK, bytes.fromhex("3F402DE9"), "actual_stage_bounds_hook"),
        (0xC4CC4, PALETTE_HOOK, bytes.fromhex("3F402DE9"), "actual_stage_palette_hook"),
        (0x586400, PALETTE_UPDATE, bytes.fromhex("FF412DE9"), "compact_shoot_palette_update_hook"),
        (0xC4BC0, PALETTE_INIT_HOOK, bytes.fromhex("37402DE9"), "actual_stage_palette_init_hook"),
    ):
        rows.append((site, before, assemble(f"b 0x{BASE+target:08X}", site), label))
    result = bytearray(original)
    used = set()
    for start, before, after, label in rows:
        if len(before) != len(after) or original[start:start+len(before)] != before:
            raise ValueError(f"Expected Write failed: {label}")
        addresses = set(range(start, start+len(after)))
        if used & addresses:
            raise ValueError("overlapping Expected Writes")
        used |= addresses
        result[start:start+len(after)] = after
    changed = {i for i,(a,b) in enumerate(zip(original,result,strict=True)) if a != b}
    expected = {start+i for start,before,after,_ in rows for i,(a,b) in enumerate(zip(before,after,strict=True)) if a != b}
    if changed != expected:
        raise ValueError("full-ROM diff differs from Expected Writes")
    manifest = {
        "schema": 1, "kind": "shoot-dedicated-graphics-initializer",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(result),
        "native_entries": {"graphics": BASE+GRAPHICS, "irq_preamble": BASE+IRQ_PREAMBLE,
                           "bounds": BASE+BOUNDS, "palette_init": BASE+PALETTE_INIT},
        "abi": "public dedicated entries preserve r0-r12/lr/sp; flags clobbered; actual stage must be 11",
        "palette_state": {"start": 0x03003D30, "bytes": 32, "counters": [0,2,4,6], "selected_ROM_slices": [8,12,16]},
        "generated_code": machine, "actual_changed_bytes": len(changed),
        "expected_writes": [{"offset": start, "bytes": len(after), "label": label,
                             "before_sha256": sha256(before), "after_sha256": sha256(after)} for start,before,after,label in rows],
        "claim_scope": "dedicated graphics/display effects plus repaired Shoot palette state and projection; full scene initializer and runtime QA remain separate",
    }
    return bytes(result), manifest


def main() -> int:
    p = argparse.ArgumentParser()
    for key in ("input", "gba", "wsc10", "wsc15", "output"):
        p.add_argument(key, type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path)
    a = p.parse_args()
    output, report = build(a.input.read_bytes(), {key: getattr(a,key).read_bytes() for key in ("gba", "wsc10", "wsc15")})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(output)
    if a.manifest:
        a.manifest.parent.mkdir(parents=True, exist_ok=True)
        a.manifest.write_text(json.dumps(report,indent=2)+"\n", encoding="utf-8")
    print(f"[shoot-graphics] static build {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
