#!/usr/bin/env python3
"""Independent ROM-only terminal scene audit; no builder imports or CPU execution.

The reviewed complete block identities bind separate source/consumer inverses,
decoded ABI/CFG checks, finite arithmetic checks and semantic negative cases.
External route and damage hooks must remain byte-for-byte original.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from capstone.arm_const import ARM_INS_B, ARM_OP_MEM

BASE = 0x08000000
INPUT = "F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF"
OUTPUT = "39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D"
INPUTS = ("996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
          "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
          "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
BLOCKS = {
    "1750": (0x5CD000, 160, 140, "488AD379AB04A0CDD47883AEE8C5D87252E4235C98CBC6A23F423558CF5FBFE8"),
    "17DF": (0x5CD0A0, 116, 104, "8692376B5D71C56047E0FFCE64B9D9783339AC5AF5B150E2F8B4A27CC15CC71B"),
    "182F": (0x5CD120, 228, 208, "73E5CC7F00FC7453B7D8FF25FF0C8C5B0511C51785EE44B15113517C6F5905BD"),
    "18EE": (0x5CD210, 96, 88, "13992A4261391D095472862FC095E9278DEB83BCDFF82171C82E16CCC1963FD3"),
    "193B": (0x5CD270, 52, 44, "14AD79A6E31C778D05A1588E4315BAB2C215A766403D572267471001874AD66E"),
    "197A": (0x5CD2B0, 140, 120, "23A09AC06AEEA36E0D817E8531612A3217C19C788D1100EB8F411221A9436DE4"),
    "19F2": (0x5CD340, 92, 80, "5BDDD4EB60F4C342539843C046F79BBDB38B7EE015556DB21EE9AA15A5B2BB7F"),
    "1A42": (0x5CD3A0, 128, 112, "93AB94D5484D2E656D2DA8F0F57F4EC025F46345AC523647E00943BF954B4052"),
    "1A95": (0x5CD420, 144, 128, "4BA43847DBAD5E14C92FAFBBFEDE459B40A4E66F486698115394CEF0CB88614C"),
    "1B15": (0x5CD4B0, 84, 76, "41260408D5C17576818C7E654ABEC9CF16C43E0C84C5B87EE24E2D1A89A03775"),
    "1B55": (0x5CD510, 64, 56, "631263206EC499AE13EEFE8A50E1224F5CD272FF5A2D155F1EF846B017BC1A93"),
    "1B97": (0x5CD550, 144, 128, "8F51413C3F28BA772BFC6CD11321D5B6253479ABCD657CB9857290C7D1E06DA4"),
    "1C17": (0x5CD5E0, 92, 84, "182A6D8632DE705CA2EA1B1EDEF19B1A369CC9549EBC24A980E3529471D48D1B"),
    "1C5C": (0x5CD640, 84, 80, "9CBF4ECADC583D4EDB78970A7D4ADCDF779AD49D9F79BEF9460EAE694AF15130"),
    "1D41": (0x5CD6A0, 112, 108, "AAF9202B6D685BFEFFAC027153A94B90756B74FF5384DE138C6338F2765B0AB4"),
    "1DA0": (0x5CD710, 48, 44, "79B7C671CEEE17CA004FE1BE3C3C5AFD0E6B28FC801376265567C57DB288479E"),
    "1DC3": (0x5CD740, 20, 20, "9FA6E3674085049F53D50F9DD875B97104EFBB42DBF07BF9B422EAD8495B06AD"),
    "result_resources": (0x5CD760, 224, 204, "D593F21D8A295B86B2DFBD718A446F387AE4CAE3C0E54F45083AB9CE2FD7AEA5"),
    "fade_span": (0x5CD840, 212, 212, "C68E6FB45143F576E1A065034ECBEB0F332BB8976DABFCB668E67C9E31A81C0E"),
    "clear_rows": (0x5CD920, 56, 52, "CCAF92A0C550DAD440C41001A32F662F90B85C172D96D9E0484F92E7744B0579"),
    "fatal_adapter": (0x5CD960, 64, 52, "49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246"),
    "hit_adapter": (0x5CD9A0, 156, 140, "FAF0C722D88D307D08C32F20B2F5E06A9713ADC116B54CC2E22805C51CAF7404"),
    "repair_7AB1": (0x5CDA40, 16, 16, "57DE65F81D2BB80E8E99CD22D2C5245A72D2E2E224560F83737FFFFD342A80AC"),
    "repair_7BFF": (0x5CDA50, 16, 16, "E64E0DA25C116CA377AB75915D4660C349096988534B9BB5A313B5A6119C6B14"),
    "repair_7C64": (0x5CDA60, 16, 16, "1662F70E3F55DCF19357D60F0D390394EF0575E32B24797A926BB5D65619ECD2"),
    "repair_7D8D": (0x5CDA70, 20, 20, "BA53B2FCD96DE56648A47EEB11C5B1235310FDCA52BD21BA9ED6984106A0A889"),
}
REPAIRS = ((0x5BDD8C, "repair_7AB1"), (0x5BE69C, "repair_7BFF"),
           (0x5BEAB8, "repair_7C64"), (0x5BF224, "repair_7D8D"))
S, C, FIRST = 0x08012008, 0x0801201C, 0x0300489C
FLAGS, COMMON = 0x0300450A, 0x03004506
CALLS = {
    "1750": (C, 0x083524C4, 0x080D15C0, S, "17DF"), "17DF": (C, S),
    "182F": (C, S, 0x08012874, S), "18EE": (C, S), "193B": (S,),
    "197A": ("clear_rows", S), "19F2": (C, S), "1A42": (C, S),
    "1A95": (C, "fade_span", "fade_span", "fade_span", S), "1B15": (C, S),
    "1B55": (C, S), "1B97": (C, "fade_span", "fade_span", "fade_span", S),
    "1C17": (C, S), "1C5C": (C, "result_resources", S, 0x080D15C0),
    "1D41": (C, 0x08012A84, 0x08012C28, 0x0833FDC0, S),
    "1DA0": (0x0833FF00, S, "1DC3"), "1DC3": (0x08340C54,),
    "result_resources": (0x080127E4, 0x08012874, 0x080132EC),
    "fade_span": (), "clear_rows": (), "fatal_adapter": (), "hit_adapter": (0x080132EC,),
    "repair_7AB1": (0x085BE000,), "repair_7BFF": (0x085BEA00,),
    "repair_7C64": (0x085BEE00,), "repair_7D8D": (0x085BF400,),
}
LITERALS = {
    "1750": (0x0300475E, 0x03004760, FIRST, COMMON, "17DF"),
    "17DF": (FLAGS, "182F", 0x03004529),
    "182F": (FIRST, "197A", 0xFFFFFB54, 0x08357670, "193B"),
    "18EE": (FIRST, "193B"), "193B": (FIRST, "197A"),
    "197A": (FLAGS, 0x03004710, 0x030012B9, 0x0300451E, "19F2"),
    "19F2": (FLAGS, COMMON, "1A42"), "1A42": (FLAGS, 0x03004D40, FLAGS, "1A95"),
    "1A95": (0x05000064, 0x05000084, 0x050000A4, "1B15"),
    "1B15": (FLAGS, "1B55"), "1B55": (FLAGS, "1B97"),
    "1B97": (0x05000064, 0x05000084, 0x050000A4, "1C17"),
    "1C17": (FLAGS, "1C5C"), "1C5C": ("1D41",), "1D41": ("1DA0",), "1DA0": ("1DC3",),
    "1DC3": (), "result_resources": (0x08374824, 0x08374854, 0x08374E44, 0x137, 0x08374E44),
    "fade_span": (), "clear_rows": (0x0600F000,),
    "fatal_adapter": (0x03002310, 0x085BDD00, 0x085BF204),
    "hit_adapter": (0x03002310, 0x085C0B00, FLAGS, 0x0834F836),
    "repair_7AB1": (), "repair_7BFF": (), "repair_7C64": (), "repair_7D8D": (),
}


def check(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def addr(value: str | int) -> int:
    return BASE + BLOCKS[value][0] if isinstance(value, str) else value


def decode(data: bytes, raw: int, count: int):
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    engine.detail = True
    result = list(engine.disasm(data[raw:raw + count], BASE + raw))
    check(len(result) * 4 == count and all(i.size == 4 for i in result), "complete ARM decoding")
    return result


def text(data: bytes, raw: int, count: int) -> list[str]:
    return [i.mnemonic + " " + i.op_str for i in decode(data, raw, count)]


def literal(data: bytes, raw: int) -> int:
    i = decode(data, raw, 4)[0]
    check(i.mnemonic == "ldr" and i.reg_name(i.operands[1].mem.base) == "pc", "literal load operand")
    return struct.unpack_from("<I", data, raw + 8 + i.operands[1].mem.disp)[0]


def cfg_stack(instructions, initial: int = 0) -> int:
    by_pc = {i.address: i for i in instructions}
    todo = deque(((instructions[0].address, initial),))
    seen, peak = {}, initial
    while todo:
        pc, depth = todo.popleft()
        if pc in seen:
            check(seen[pc] == depth, "stack depth at CFG join")
            continue
        check(pc in by_pc, "branch stays in declared instruction region")
        seen[pc] = depth
        i = by_pc[pc]
        if i.mnemonic == "push":
            depth += 4 * len(i.operands)
        elif i.mnemonic == "pop":
            depth -= 4 * len(i.operands)
        elif i.mnemonic == "str" and i.op_str.endswith("[sp, #-4]!"):
            depth += 4
        elif i.mnemonic == "ldr" and i.op_str.endswith("[sp], #4"):
            depth -= 4
        elif i.mnemonic in ("add", "sub") and i.op_str.startswith("sp, sp, #"):
            depth += i.operands[2].imm * (-1 if i.mnemonic == "add" else 1)
        check(depth >= 0, "no stack underflow")
        peak = max(peak, depth)
        if i.mnemonic == "bx":
            check(i.op_str == "lr" and depth == 0, "balanced return")
        elif i.id == ARM_INS_B:
            target = i.operands[0].imm
            if target in by_pc:
                todo.append((target, depth))
            else:
                check(depth == 0 and i.mnemonic == "b", "balanced external tail branch")
            if i.mnemonic != "b":
                todo.append((pc + 4, depth))
        else:
            todo.append((pc + 4, depth))
    check(len(seen) == len(instructions), "complete reachable instruction CFG")
    return peak


def machine_contracts(after: bytes, *, strict_hash: bool = True) -> dict:
    instruction_count, peaks = 0, {}
    for name, (raw, size, code, identity) in BLOCKS.items():
        if strict_hash:
            check(digest(after[raw:raw + size]) == identity, "reviewed complete block: " + name)
        ins = decode(after, raw, code)
        instruction_count += len(ins)
        check(all(i.mnemonic not in ("blx", "movw", "movt", "udf", "bkpt", "svc") for i in ins), "ARM7 instruction subset")
        calls = tuple(i.operands[0].imm for i in ins if i.mnemonic == "bl")
        check(calls == tuple(map(addr, CALLS[name])), "ordered native call contract: " + name)
        values = struct.unpack_from("<" + "I" * ((size - code) // 4), after, raw + code)
        check(values == tuple(map(addr, LITERALS[name])), "complete literal contract: " + name)
        refs = []
        for i in ins:
            if len(i.operands) > 1 and i.operands[1].type == ARM_OP_MEM and i.reg_name(i.operands[1].mem.base) == "pc":
                target = i.address - BASE + 8 + i.operands[1].mem.disp
                check(i.mnemonic == "ldr" and target in range(raw + code, raw + size, 4), "literal pool containment")
                refs.append(target)
        check(sorted(refs) == list(range(raw + code, raw + size, 4)), "complete literal usage")
        initial = {"repair_7AB1": 12, "repair_7BFF": 4, "repair_7C64": 4}.get(name, 0)
        peaks[name] = cfg_stack(ins, initial)
    # This explicit operand contract is what ties the finite equations below
    # to the actual machine instructions, independently of the block digests.
    required = {
        "1750": ("mov r8, #0x79", "strh r8, [r4, #0x50]", "ldrb r6, [r6]", "ldr r8, [r7], #4", "strh r8, [r4, #0x64]", "bic r1, r1, #0x400"),
        "17DF": ("lsl r8, r8, #0x10", "lsr r8, r8, #0x10", "orr r1, r1, #0x80", "eor r1, r1, #7", "strh r8, [r4, #0x64]"),
        "182F": ("ldrsh r8, [r4, #0x34]", "cmp r8, #0xe40", "movge r8, #8", "cmp r8, #0xdc0", "movle r8, #2", "ldrh r8, [r4, #0x36]", "cmp r8, #0xc00", "strh r8, [r4, #0xa0]", "strh r8, [r4, #0xa2]", "strh r8, [r4, #0xa4]", "strh r8, [r4, #0xa8]", "strb r8, [r4, #0x70]", "str r6, [sp, #-4]!", "pop {r6}", "strh r8, [r6, #0x50]"),
        "197A": ("tst r1, #0x100", "bic r1, r1, #0x100", "mov r8, #0x154", "mov r8, #0x8f", "ldrb r8, [r0]", "strh r8, [r4, #8]", "mov r8, #0x48", "strh r8, [r4, #0xc]"),
        "1A42": ("mov r8, #0x20", "orr r1, r1, #0x20", "mov r1, #1", "orr r1, r1, #0x1000"),
        "1A95": ("tst r8, #1", "mov r1, #8", "mov r2, #0"),
        "1B55": ("tst r1, #0x100", "mov r8, #0x40"),
        "1B97": ("tst r8, #3", "mov r1, #8", "mov r2, #1"),
        "1C17": ("orr r1, r1, #0x2000",),
        "1C5C": ("mov r8, #0xb", "mov sb, #4", "mov sl, #0"),
        "1D41": ("tst r8, #0x2000", "mov r8, #0x5d", "mov r8, #0x20", "mov fp, #0"),
        "result_resources": ("add sp, sp, #0x3c", "add sp, sp, #0xc", "add sp, sp, #0x14", "orr r8, r8, #0x2000", "mov r8, #0x70", "mov r8, #0x48", "mov r8, #0x96", "strh r8, [r4, #0x50]"),
        "fade_span": ("and r5, r5, #0x1f", "cmp r5, #3", "movls r5, #0", "subhi r5, r5, #2", "moveq r5, #3", "addne r5, r5, #2", "movhi r5, #0x1f", "strh r4, [r0], #2"),
        "clear_rows": ("cmp r1, #0x3e", "bhi #0x85cd94c", "add r0, r0, r1, lsl #6", "mov r2, #0x40", "strh r3, [r0], #2"),
        "fatal_adapter": ("ldrb r8, [r8, #0xe]", "cmp r8, #0xb", "ldr r5, [r5, #0x28]", "b #0x836e604", "b #0x836e5f0"),
        "hit_adapter": ("ldrb r8, [r8, #0xe]", "cmp r8, #0xb", "mov r8, #1", "mov r8, #8", "strh r8, [r5, #0x74]", "tst r8, #0x4000", "tst r8, #0x30", "mov r1, #0x10", "mov r1, #8", "mov r2, #0x1f", "strh r2, [r0], #0x20", "b #0x836e438", "b #0x836e638"),
    }
    for name, expected in required.items():
        raw, _, code, _ = BLOCKS[name]
        actual = text(after, raw, code)
        check(all(item in actual for item in expected), "source operand contract: " + name)
    multiplicities = {
        "fade_span": {"cmp r5, #3": 3, "movls r5, #0": 3, "subhi r5, r5, #2": 3,
                      "moveq r5, #3": 3, "addne r5, r5, #2": 3, "movhi r5, #0x1f": 3},
        "hit_adapter": {"strh r2, [r0], #0x20": 2},
        "1A95": {"mov r1, #8": 3, "mov r2, #0": 3},
        "1B97": {"mov r1, #8": 3, "mov r2, #1": 3},
    }
    for name, counts in multiplicities.items():
        raw, _, code, _ = BLOCKS[name]
        actual = text(after, raw, code)
        check(all(actual.count(item) == count for item, count in counts.items()), "complete repeated operand population: " + name)
    jump = text(after, BLOCKS["182F"][0], BLOCKS["182F"][2])
    check(jump.index("str r6, [sp, #-4]!") < jump.index("bl #0x8012874") < jump.index("pop {r6}") < jump.index("strh r8, [r6, #0x50]"), "r6 survives event sound clobber")
    return {"complete_blocks": len(BLOCKS), "arm_instructions": instruction_count, "max_stack_bytes": max(peaks.values()), "stack_depths": peaks}


def resource_inverse(gba: bytes, old: bytes, new: bytes) -> dict:
    # Read native pointers first, then reconstruct the complete source records.
    table, reserved = struct.unpack_from("<2I", gba, 0x374824)
    count, command, a, b = struct.unpack_from("<4I", gba, table - BASE)
    check((reserved, count, b) == (0, 1, 0), "P1 native header")
    payload = gba[command - BASE:command - BASE + 16]
    check(payload[12:] == bytes(4), "P1 native record padding")
    reconstructed = struct.pack("<6H", 4, 0, 1, 12, 24, 0) + payload[:12] + gba[a - BASE:a - BASE + 8]
    check(reconstructed == new[0x3D8750:0x3D8770] == old[0x2B6150:0x2B6170], "complete P1 inverse and commercial FF64 duration")
    table0, desc, x, y = struct.unpack_from("<4I", gba, 0x374854)
    n, layout = struct.unpack_from("<2I", gba, table0 - BASE)
    check(n == 44 and (x, y) == struct.unpack_from("<2I", new, 0x2DFF28), "P0 header constants")
    check(gba[layout - BASE:layout - BASE + n * 4] == new[0x2DFF34:0x2DFFE4], "complete P0 layout inverse")
    size, pixels = struct.unpack_from("<2I", gba, desc - BASE)
    check(size == 1312, "P0 single tile descriptor size")
    decoded = bytearray()
    for tile in range(41):
        data = gba[pixels - BASE + tile * 32:pixels - BASE + (tile + 1) * 32]
        for row in range(8):
            values = [data[row * 4 + x // 2] >> ((x % 2) * 4) & 15 for x in range(8)]
            decoded.extend(sum(((values[x] >> plane) & 1) << (7 - x) for x in range(8)) for plane in range(4))
    check(decoded == new[0x3BE1F0:0x3BE710], "all41 native tiles inverse")
    check(gba[0x374E44:0x374E4A] == new[0x3D7400:0x3D7406] and gba[0x374E6A:0x374E6C] == bytes(2), "P2 header and padding")
    colors = struct.unpack_from("<16H", gba, 0x374E4A)
    inverse = []
    for color in colors:
        channels = tuple((color >> shift) & 31 for shift in (0, 5, 10))
        check(color < 0x8000 and all(c == 0 or c >= 3 and c & 1 for c in channels), "source-derived native P2 channel domain")
        inverse.append((channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2)
    check(tuple(inverse) == struct.unpack_from("<16H", new, 0x3D7406), "all16 P2 colors inverse")
    return {"p1_items": 1, "p0_layout_items": 44, "p0_tiles": 41, "p2_colors": 16}


def consumers(gba: bytes, old: bytes, new: bytes) -> dict:
    check(new[0x74348F:0x7434AC] == old[0x393064:0x393081], "source jump-age increment lineage")
    check(new[0x76877C:0x768799] == old[0x3ADC42:0x3ADC5F], "source jump-age threshold lineage")
    check(text(gba, 0x3576FC, 12) == ["ldrb r8, [r4, #0x70]", "cmp r8, #0x18", "blo #0x8357724"], "native30->24 jump-age consumer")
    check(text(gba, 0xD15C0, 16) == ["ldr r6, [pc, #0x24]", "ldrh r7, [r6, #6]", "cmp r7, #0", "bxne lr"], "event sound r6/r7 clobbers")
    check(text(gba, 0x1290C, 12) == ["mov sb, #1", "mov sl, #0", "bl #0x80d15c0"], "event can reach sound requester")
    check(text(gba, 0x127E4, 32) == ["push {r0, r3, r4, r5}", "ldr r5, [sp, #0x48]", "ldr r0, [sp, #0x40]", "str r0, [r5, #0x44]", "ldr r0, [sp, #0x34]", "str r0, [r5, #0x48]", "ldr r0, [sp, #0x28]", "str r0, [r5, #0x4c]"], "constructor 15-argument P1/P0/P2 consumer")
    check(text(gba, 0x132EC, 20) == ["push {r2, r4, r5, lr}", "ldr r4, [sp, #0x20]", "add r4, r4, #4", "ldr r8, [sp, #0x14]", "lsl r2, r8, #5"], "P2 pointer/index consumer")
    check(text(gba, 0x3524C4, 8) == ["push {r0, r2, r4, r5, lr}", "ldr r4, [sp, #0x18]"], "release native object consumer")
    check(new[0x3F37AE:0x3F37DE] == old[0x2D35C2:0x2D35F2], "sound34 exact commercial payload")
    check(text(gba, 0x340B60, 16) == ["mov r8, #0xb", "mov sb, #4", "mov sl, #1", "bl #0x80d15c0"], "sound34 native ID/type")
    check(old[0x390796:0x3907A1] == bytes.fromhex("268B3EA2068B85BE00E710"), "source OUT10/11 pair")
    check(text(gba, 0xC9804, 16) == ["ldrb r0, [r5, #0xe0]", "bl #0x8000f2c", "ldrb r0, [r5, #0xe1]", "bl #0x8000f44"], "commercial OUT10/11 native pair")
    check(literal(gba, 0xF44) == 0x030012B9, "port11 shadow")
    check(literal(gba, 0x36E634) == 0x0834F836, "legacy nonfatal displaced literal")
    check(text(gba, 0x340C90, 24) == ["mov r8, #1", "strh r8, [sb, #4]", "mov r8, #0", "strh r8, [sb, #6]", "mov r8, #0", "strh r8, [sb, #8]"], "native parent-mode handoff")
    check(literal(gba, 0x340C8C) == 0x03002310, "native existing parent-mode owner")
    return {"new_ram": 0, "port11_shadow": "030012B9", "result_sound": "34->0B,type4; Shoot delay0 retained", "jump_age": "byte5C->70; threshold30->24; initial20->16", "mode_exit": "08340C54 retires current task and writes existing mode words(1,0,0)"}


def finite_domains() -> dict:
    expand = lambda n: 0 if n == 0 else n * 2 + 1
    down = lambda n: 0 if n <= 3 else n - 2
    up = lambda n: 3 if n == 0 else min(n + 2, 31)
    for source in range(16):
        check(down(expand(source)) == expand(max(source - 1, 0)), "source channel decrement equation")
        check(up(expand(source)) == expand(min(source + 1, 15)), "source channel increment equation")
    for n in range(32):
        a = b = n
        for _ in range(16):
            a, b = down(a), up(b)
        check(a == 0 and b == 31, "all native channels reach exact terminal endpoints")
    for source in range(4096):
        packed = sum(expand((source >> shift) & 15) << native for shift, native in ((8, 0), (4, 5), (0, 10)))
        inverse = ((packed & 31) // 2 << 8) | (((packed >> 5) & 31) // 2 << 4) | ((packed >> 10) & 31) // 2
        check(inverse == source, "all RGB444 source colors invert")
    fade_addresses = {0x05000000 + row * 32 + color * 2 for row in (3, 4, 5) for color in range(2, 10)}
    check(len(fade_addresses) == 24 and all(a % 32 not in (0, 2) for a in fade_addresses), "only BG3..5 colors2..9 mutate")
    check(sum(timer & 1 != 0 for timer in range(32, 0, -1)) == 16 and sum(timer & 3 == 0 for timer in range(64, 0, -1)) == 16, "original16 fade steps and order")
    for flags in range(65536):
        permitted = not bool(flags & 0x4030)
        machine = not bool(flags & 0x4000) and not bool(flags & 0x30)
        check(machine == permitted, "all hit-flash flags")
    for stage in range(256):
        check((stage == 11) == (stage - 11 == 0), "all stage-byte gates")
    row_writes = 0
    for y in range(65536):
        if y <= 62:
            start = 0x0600F000 + (y << 6)
            check(0x0600F000 <= start and start + 128 <= 0x06010000, "bounded clear within both native tilemaps")
            check(((y << 6) + 0x800) <= 0xFFFF, "bounded source address does not wrap")
            row_writes += 64
    for xbits in range(65536):
        x = (xbits + 32768) % 65536 - 32768
        direction = 8 if x >= 0xE40 else 2 if x <= 0xDC0 else 0
        check((direction == 0) == (0xDC0 < x < 0xE40), "signed terminal centering interval")
    return {"source_colors": 4096, "native_channels": 32, "flash_flags": 65536, "stage_values": 256,
            "camera_values": 65536, "bounded_clear_halfwords": row_writes, "signed_x_values": 65536,
            "fade_colors": 24, "fade_step_counts": [16, 16], "elapsed_only_scaling": "151->121,75->60,117->93,byte-age20->16; fade32/64 unchanged"}


def changes(before: bytes, after: bytes) -> int:
    check(len(before) == len(after), "ROM size unchanged")
    intervals = [(a, a + n) for a, n, _, _ in BLOCKS.values()] + [(a, a + 4) for a, _ in REPAIRS]
    mask = bytearray(len(before))
    for start, end in intervals:
        check(not any(mask[start:end]), "disjoint actual write intervals")
        mask[start:end] = b"\1" * (end - start)
    for name, (start, length, _, _) in BLOCKS.items():
        check(before[start:start + length] == b"\xff" * length, "resident FF predecessor: " + name)
    for site, name in REPAIRS:
        check(before[site:site + 4] == bytes.fromhex("008084E5"), "upper exact displaced callback store")
        check(text(after, site, 4) == [f"b #0x{addr(name):x}"], "upper same-update bridge branch")
    check(after[0x36E5EC:0x36E5F0] == before[0x36E5EC:0x36E5F0] and after[0x36E634:0x36E638] == before[0x36E634:0x36E638], "external damage hooks closed")
    count = 0
    for i, (a, b) in enumerate(zip(before, after, strict=True)):
        if a != b:
            check(bool(mask[i]), "no undeclared byte changes including preserved gaps")
            count += 1
    return count


def inbound(before: bytes) -> list:
    intervals = [(a, a + n) for a, n, _, _ in BLOCKS.values()]
    found = []
    for site in range(len(before) - 3):
        pointer = int.from_bytes(before[site:site + 4], "little") - BASE
        if 0x5CD000 <= pointer < 0x5D0000:
            found.append(["pointer", site, pointer])
    for site in range(0, len(before) - 3, 4):
        word = int.from_bytes(before[site:site + 4], "little")
        if word >> 28 != 15 and (word >> 25) & 7 == 5:
            displacement = word & 0xFFFFFF
            if displacement >= 0x800000:
                displacement -= 0x1000000
            target = site + 8 + displacement * 4
            if 0x5CD000 <= target < 0x5D0000:
                found.append(["ARM-like", site, target])
    check(not any(a <= target < b for _, _, target in found for a, b in intervals), "no incoming candidate reaches actual resident writes")
    return found


def negatives(before: bytes, after: bytes, gba: bytes, old: bytes, new: bytes) -> list[str]:
    passed = []
    def rejects(label, action):
        try:
            action()
        except (ValueError, IndexError, struct.error):
            passed.append(label)
        else:
            raise ValueError("negative case escaped: " + label)
    def altered(site: int, replacement: bytes, data: bytes = after) -> bytes:
        trial = bytearray(data)
        trial[site:site + len(replacement)] = replacement
        return bytes(trial)
    def opcode(name: str, wanted: str, replacement: int, label: str):
        raw, _, code, _ = BLOCKS[name]
        site = next(i.address - BASE for i in decode(after, raw, code) if i.mnemonic + " " + i.op_str == wanted)
        trial = altered(site, struct.pack("<I", replacement))
        rejects(label, lambda: machine_contracts(trial, strict_hash=False))
    opcode("1750", "bl #0x83524c4", 0xEB000000, "wrong release consumer")
    opcode("182F", "pop {r6}", 0xE8BD0080, "event destroys live r6")
    opcode("182F", "strh r8, [r6, #0x50]", 0xE1C685B2, "wrong post-event task field")
    opcode("repair_7AB1", "pop {r6, r7, lr}", 0xE8BD4000, "inherited repair frame not restored")
    opcode("fatal_adapter", "cmp r8, #0xb", 0xE358000A, "wrong stage gate")
    opcode("hit_adapter", "strh r2, [r0], #0x20", 0xE0C021B0, "flash uses wrong row stride")
    opcode("fade_span", "cmp r5, #3", 0xE3550002, "fade3 endpoint regresses")
    opcode("1A95", "tst r8, #1", 0xE3180002, "fade callback cadence changed")
    opcode("clear_rows", "cmp r1, #0x3e", 0xE351003F, "tilemap clear crosses OBJ boundary")
    for name, index, value, label in (("197A", 2, 0x030012BB, "swapped logical scroll layer"),
                                    ("hit_adapter", 3, 0x0834E832, "incorrect displaced legacy literal"),
                                    ("result_resources", 0, 0x08374828, "interior P1 pointer")):
        raw, _, code, _ = BLOCKS[name]
        trial = altered(raw + code + index * 4, struct.pack("<I", value))
        rejects(label, lambda trial=trial: machine_contracts(trial, strict_hash=False))
    rejects("foreign ROM write", lambda: changes(before, altered(0x5CDBA0, b"\x00")))
    rejects("missing same-update repair", lambda: changes(before, altered(0x5BDD8C, before[0x5BDD8C:0x5BDD90])))
    rejects("premature external damage hook", lambda: changes(before, altered(0x36E5EC, b"\0\0\0\xEA")))
    for site, label in ((0x37483C, "P1 duration changed"), (0x37486C, "P0 layout changed"),
                        (0x374924, "one native tile pixel changed"), (0x374E4A, "P2 color changed")):
        trial = altered(site, bytes((gba[site] ^ 1,)), gba)
        rejects(label, lambda trial=trial: resource_inverse(trial, old, new))
    return passed


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        p.add_argument(name, type=pathlib.Path)
    p.add_argument("--output", required=True, type=pathlib.Path)
    a = p.parse_args()
    paths = (a.before, a.after, a.gba, a.wsc10, a.wsc15)
    check(all(path.suffix.lower() != ".sav" for path in paths), "save files forbidden")
    before, after, gba, old, new = (path.read_bytes() for path in paths)
    check(digest(before) == INPUT and tuple(map(digest, (gba, old, new))) == INPUTS, "exact predecessor and source identities")
    report = {"schema": 1, "kind": "shoot-terminal-independent-static-verification", "input_sha256": digest(before),
              "output_sha256": digest(after), "machine": machine_contracts(after), "resources": resource_inverse(after, old, new),
              "native_consumers": consumers(after, old, new), "finite_domains": finite_domains(),
              "changed_bytes": changes(before, after), "incoming_gap_candidates": inbound(before),
              "negative_cases": negatives(before, after, gba, old, new),
              "external_hooks_installed": False, "runtime_performed": False,
              "open_gates": ["source0DEC interrupted-DI dependency", "197A camera-BX live-in/range ownership",
                             "complete initializer/controller/scene route before external hook installation"]}
    check(digest(after) == OUTPUT, "final reviewed terminal identity")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-terminal-verify] PASS: {report['machine']['arm_instructions']} instructions, {len(report['negative_cases'])} negative cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
