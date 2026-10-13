#!/usr/bin/env python3
"""Independent static audit of the lower Shoot graph and finite source domains.

Does not import a builder, assemble code, or execute CPU/game instructions.
Complete reviewed block identities bind the finite mathematical models to the
decoded machine code; call, stack, operand and data contracts are checked too.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import itertools
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from capstone.arm_const import ARM_INS_B, ARM_OP_IMM, ARM_OP_MEM, ARM_OP_REG

BASE = 0x08000000
BEFORE_SHA256 = "0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BLOCKS = {
    "810D": (0x5CB000, 116, 116, "35B2E41696F64D7DA243DD51CE94A8DDBA883FC7C41436F9540A576A83472C50"),
    "813F": (0x5CB080, 156, 148, "4AE9A2AD0B0B4CBA687DFA6F59F6F92F09710BB66FB9DA7B9C6D8510127B116E"),
    "81AB": (0x5CB120, 76, 72, "CA275E5934DF1D64ACFDFCCF2D0ABDCEAFC05D2EF395BD73C36789983B17E3FB"),
    "81D1": (0x5CB170, 64, 64, "414591EF244C9DD2B8137B06ECDC5F3FEF45E101C065D22E32813D99DB303A35"),
    "81EA": (0x5CB1B0, 204, 200, "CB842AD22A8B74491B583321D7CD2584303FDF7449DDC31CF6A676A28F642186"),
    "8266": (0x5CB280, 256, 240, "A3EE9202EC73A700591993BEE64454629EA243555FF1870EAFB8253B791DA863"),
    "heading": (0x5CB380, 108, 108, "6814B1ADC8D890B5BEFA39165EB065A5D42AABC35705328247C27D1C2D81E569"),
    "bounce": (0x5CB3F0, 464, 464, "B293E57657FD98F66683B4D059BCC43FDFBAAD8B08DE6D1F2C1E6076EE74703E"),
    "8526": (0x5CB5C0, 120, 116, "D6F1E4B1CA98582835320CEA52510370AC26FB88A9592416A684EE9B08C44775"),
    "pursuit": (0x5CB640, 344, 344, "7189B68E00F835F1533E6A2B4DA0D8F1A1A457EA1D00770385383D5C23D7C925"),
    "86D9": (0x5CB7C0, 92, 88, "D507FC9545BAE208774DDEE2C9A0034DC687FFA3554A885F681A6CF29B929C1F"),
    "86FC": (0x5CB820, 220, 200, "1324B4E835E69B78472F93D3C217342DC1E22935C5306A748A064FF3D9F13041"),
    "876A": (0x5CB900, 100, 96, "FD5BF727016B6656BF0C1DD5BD9256C58E023FFABC90722E85F510999120E7E8"),
    "8AB8": (0x5CB970, 144, 140, "2040B1DD0053DEC2F8030CD289C649CF81E770E5E2CFA61AF69F8458C49954F7"),
    "8B28": (0x5CBA00, 104, 100, "45FCEE981511B68B04208128AAEAE39DCC42E62A411CF017B8BF3505BBE78427"),
    "8B53": (0x5CBA70, 116, 112, "ABDF4F2B918B7B6B0A0261AC5D49332B5E505BBD9B7AC43CB8EEA9BCA1CA3DE5"),
    "8B8A": (0x5CBAF0, 224, 204, "7F0986CA83F1983E4FC331CC26BF5A27A765E00B53E3E57151021FB4708CE8F0"),
    "tracking": (0x5CBBD0, 220, 220, "0F699B8FAAE59547DC3252ECF97CE2993C6B953710A21B828D8E8443AF37AAB8"),
    "8C86": (0x5CBCB0, 92, 88, "48DA303B6338EF6BAF523D72D3970FD08F5F435E52808E1FC68C87D0A5C8D948"),
    "8CB4": (0x5CBD10, 104, 100, "24913A471398E0ECFDB6A3F9AC2E6AAA01F363C54826AB6C65E088178F1B49FA"),
    "8CDD": (0x5CBD80, 144, 140, "95D214417328E5564D58836C257DF0B5D7E04D331AA2AC0C97F0A90957C85AD5"),
    "8D4D": (0x5CBE10, 116, 112, "EB4A2A4077C3C2E6F86B4B8B5D7C4DA0AD009103C8CE678C3C2FEB51CED58E2E"),
    "8D84": (0x5CBE90, 128, 124, "3A1D5B3EE42C4E736FB390C936724FDAA4FA36F09860717ACDBA7700714AF81F"),
    "8E27": (0x5CBF10, 168, 164, "A320B1ED5B6561F395932207184A7345CF75B441FC09971DF595F1B62AB7BE6C"),
    "8E7F": (0x5CBFC0, 132, 124, "2EB6A2614B7A921768A76DE4789B6E24AFF6130D55DBEE2CD46B0D4A1C63E09B"),
    "8EC1": (0x5CC050, 120, 116, "5A51CC1992D5D650E72CD06C2698037FDFB35D5A4C840E1AFD35D0797C815078"),
    "8EF3": (0x5CC0D0, 256, 248, "B39AA67A3E25A17E4BA8CE84CA08E19DE2749623139F6A7D26400281BF0B800D"),
    "881A": (0x5CC1D0, 264, 252, "6DFFE72786491F5BA3FEE103589B7F9A168AE09D8ECD85EF687EDDA6BC49773D"),
    "933B": (0x5CC2E0, 396, 376, "C20D15A49931DED52CCFF41958F61E28C58DDF9C3EEDB6E9C9F5B7FC2D7E8114"),
    "9798": (0x5CC470, 80, 80, "3AF83D342AE26CD4EDC6F8916FF7166B90FED2D7D4B663F2FE4858D5A522B337"),
    "97BB": (0x5CC4C0, 196, 192, "FDF2A604A7146A39B50A86EBFEB332E8A96CE5DBD5EF39F87390BBF54DC268DD"),
    "984D": (0x5CC590, 120, 116, "0AA10A4B4B5A79B4491CF92406FAA77CFA97298B7B318D08EF670B4BFDD2AB72"),
    "9879": (0x5CC610, 80, 80, "82B986AD3047D168D95A8887E7A4A13E9834093EE8A2E95A55DC613B5FB6B4EB"),
}
# Independent final geometry; never loaded from a builder manifest.
DATA = {"motion_table": (0x5CC660, 124), "spatial_vectors": (0x5CC7E0, 72),
        "spatial_x": (0x5CC860, 108), "spawn_offsets": (0x5CC8D0, 10),
        "spawn_patterns": (0x5CC8E0, 64), "active_palette": (0x5CC700, 224),
        "spatial_y": (0x5CC830, 40)}
CF_ID, D1_ID = 0x5D, 0x5E
CALLS = {
    "810D": (0x08012A84, "813F", "81AB"), "813F": (0x08012874, 0x08012600),
    "81AB": (0x08012874,), "81D1": (0x08012A84, "813F"), "81EA": (0x08012A84, 0x08012874),
    "8266": (0x08012874, "heading", "bounce"), "heading": (0x08012560, 0x080129C8),
    "bounce": (), "8526": (0x080D15C0, "881A", "881A", "881A", "heading", "pursuit"),
    "pursuit": (), "86D9": (0x08012874,), "86FC": (0x08012A84, 0x08012874),
    "876A": (0x08012A84, 0x08012600), "8AB8": (0x08012874, 0x080D15C0),
    "8B28": (0x08012A84, 0x08012874, "8B53"), "8B53": (0x08012A84, 0x08012874),
    "8B8A": ("tracking", 0x08012874, 0x080D15C0), "tracking": (0x08012A84, 0x08012348),
    "8C86": (0x08012A84,), "8CB4": (), "8CDD": (0x08012874, 0x080D15C0),
    "8D4D": (0x08012A84, 0x08012874), "8D84": ("tracking", 0x08012874),
    "8E27": (0x08012874, 0x08012A84), "8E7F": (0x08012A84, "8EF3"), "8EC1": ("933B",),
    "8EF3": (0x08012600, 0x08012600), "881A": (0x08352374, 0x08011E54, 0x085C4600, 0x08012874),
    "933B": (0x08352374, 0x08011E54, 0x085C4500, 0x08012874, 0x080D15C0),
    "9798": (0x08012A84, 0x083524C4),
    "97BB": (0x08012A84, 0x08012560, 0x0801233C, 0x08012348, 0x08012874),
    "984D": (0x08012A84, 0x08012874, "9879"), "9879": (0x08012A84, 0x083524C4),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def u16(x: int) -> int:
    return x & 65535


def s16(x: int) -> int:
    return (x + 32768) % 65536 - 32768


def decode(data: bytes, site: int, length: int):
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    engine.detail = True
    ins = list(engine.disasm(data[site:site + length], BASE + site))
    demand(len(ins) * 4 == length and all(i.size == 4 for i in ins), "complete ARM decode")
    return ins


def texts(data: bytes, site: int, length: int) -> list[str]:
    return [i.mnemonic + " " + i.op_str for i in decode(data, site, length)]


def literal(data: bytes, site: int) -> int:
    i = decode(data, site, 4)[0]
    demand(i.mnemonic == "ldr" and i.reg_name(i.operands[1].mem.base) == "pc", "native literal operand")
    return struct.unpack_from("<I", data, site + 8 + i.operands[1].mem.disp)[0]


def source_consumers(gba: bytes, old: bytes, new: bytes) -> dict:
    # Actual task-priority producer, list insertion and linked-list consumers.
    demand(texts(gba, 0x11E54, 40) == ["push {r0, r4, lr}", "ldr r4, [sp, #0x14]",
           "ldr r0, [sp, #0xc]", "str r0, [r4, #4]", "stmdb sp!, {r4}", "stmdb sp!, {r4}",
           "bl #0x8011e8c", "add sp, sp, #8", "pop {r0, r4, lr}", "bx lr"], "task-priority native consumer")
    source_priority = new[0x750B94:0x750BB7]
    retail_priority = bytearray(old[0x3976C6:0x3976E9])
    demand(source_priority[:20] == retail_priority[:20] and source_priority[25:] == retail_priority[25:], "commercial task-priority shared body")
    demand(source_priority[20:25] == bytes.fromhex("9AE50BFF4F") and retail_priority[20:25] == bytes.fromhex("9AE70BB296"), "source relink calls")
    demand(texts(gba, 0x11EAC, 4) == ["strh r0, [r4, #0x10]"], "native active task list state")
    demand(texts(gba, 0x129CC, 16) == ["ldr r5, [sp, #0x28]", "ldr r4, [r5, #0x44]",
           "ldr r3, [sp, #0x20]", "strh r3, [r5, #0xe]"], "frame-event presentation/event ABI")
    demand(texts(gba, 0x129F8, 8) == ["ldr r0, [sp, #0x1c]", "strh r0, [r5, #0x1a]"], "frame-event frame ABI")
    demand(new[0x7526BB:0x7526ED] == old[0x39900B:0x39903D], "commercial source frame helper lineage")
    demand(texts(gba, 0x1233C, 36) == ["ldr sb, [sp]", "add sb, sb, #0x40", "b #0x801234c",
           "ldr sb, [sp]", "and sb, sb, #0xff", "add sb, sb, sb", "add r8, pc, #4",
           "ldrsh r0, [r8, sb]", "bx lr"], "trig signed result and r1/r6/r7 survival")
    demand(texts(gba, 0x352420, 4) == ["add r5, r5, #0x18"] and
           texts(gba, 0x35248C, 8) == ["ldr r0, [sp, #0x2c]", "str r5, [r0]"], "allocator object header and handle ABI")
    demand(texts(gba, 0x3524C8, 4) == ["ldr r4, [sp, #0x18]"] and
           texts(gba, 0x3524FC, 4) == ["sub r0, r0, #0x18"], "object release ABI")
    # A9 is old A7 by exact payload, not by numeric ID similarity.
    demand(sha(new[0x3F85B0:0x3F85C0]) == "68CA1B6E09B82F7BAB3F0BA06D37FFF0FB539E0D85A75BAEBCBA12DEE89736FF", "A9 payload identity")
    demand(texts(gba, 0x3719B4, 16) == ["mov r8, #0x4c", "mov sb, #2", "mov sl, #0", "bl #0x80d15c0"], "A9 native request mapping")
    return {"priority": "source4FFF:0BA4 / retail96B2:0BA6 -> native08011E54 -> list08011E8C",
            "frame_event": "source4FFF:26CB -> native080129C8, stack frame/event/ignored/presentation",
            "allocator": "08352374, pool0,id4104,task header18, handle03004D54",
            "release": "083524C4, stack ignored/object; existing retail lifecycle",
            "trig": "r0 signed halfword; only r8/r9 clobbered; low8 argument",
            "A9": "WSC15 A9 payload equals old A7, native4C/type2"}


def static_stack(ins) -> int:
    by_pc = {i.address: i for i in ins}
    pending = deque(((ins[0].address, 0),))
    seen = {}
    peak = 0
    while pending:
        pc, depth = pending.popleft()
        if pc in seen:
            demand(seen[pc] == depth, "static stack joins disagree")
            continue
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
            delta = i.operands[2].imm
            depth += -delta if i.mnemonic == "add" else delta
        peak = max(peak, depth)
        demand(depth >= 0, "stack underflow")
        if i.mnemonic == "bx":
            demand(i.op_str == "lr" and depth == 0, "unbalanced static return")
            continue
        if i.id == ARM_INS_B:
            target = i.operands[0].imm
            demand(target in by_pc, "branch leaves its complete code contract")
            pending.append((target, depth))
            if i.mnemonic == "b":
                continue
        demand(pc + 4 in by_pc, "fallthrough leaves code")
        pending.append((pc + 4, depth))
    demand(len(seen) == len(ins), "unreachable instruction in declared code contract")
    return peak


def code_contract(rom: bytes) -> dict:
    demand(len(BLOCKS) == 33 and CF_ID is not None and D1_ID is not None, "final lower contracts not pinned")
    all_addresses = {name: BASE + row[0] for name, row in BLOCKS.items()}
    peaks, instruction_count = {}, 0
    for name, (site, length, code, expected_sha) in BLOCKS.items():
        blob = rom[site:site + length]
        demand(sha(blob) == expected_sha, f"complete reviewed block {name}")
        ins = decode(rom, site, code)
        instruction_count += len(ins)
        peaks[name] = static_stack(ins)
        normalized = [i.mnemonic + " " + i.op_str for i in ins]
        regs = "{r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}" if name == "8EF3" else "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
        demand(normalized[0] == "push " + regs and normalized[1] == "mov fp, #0" and
               normalized[-2:] == ["pop " + regs, "bx lr"], f"preserved registers and native zero ABI {name}")
        calls = tuple(i.operands[0].imm for i in ins if i.mnemonic == "bl")
        expected_calls = tuple(all_addresses[x] if isinstance(x, str) else x for x in CALLS[name])
        demand(calls == expected_calls, f"native call order {name}")
        for i in ins:
            if i.mnemonic == "ldr" and len(i.operands) > 1 and i.operands[1].type == ARM_OP_MEM and i.reg_name(i.operands[1].mem.base) == "pc":
                p = i.address - BASE + 8 + i.operands[1].mem.disp
                demand(site + code <= p < site + length and p % 4 == 0, f"literal pool ownership {name}")
    return {"instructions": instruction_count, "complete_code_blocks": len(BLOCKS),
            "max_static_local_stack_bytes": max(peaks.values()), "per_callback_stack_peak": peaks,
            "native_call_order_checked": True, "CPU_or_game_execution": False}


def inverse_data(rom: bytes, source: bytes) -> dict:
    bank = source[0x740900:0x750900]
    for name, a, z in (("motion_table", 0x879E, 0x881A), ("spatial_vectors", 0x8F93, 0x8FDB),
                       ("spatial_x", 0x9017, 0x9083), ("spawn_offsets", 0x9477, 0x9481), ("spawn_patterns", 0x9481, 0x94C1)):
        p, length = DATA[name]
        demand(length == z - a and rom[p:p + length] == bank[a:z], f"raw source inverse {name}")
    lattice = (0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
    p, length = DATA["active_palette"]
    native = struct.unpack_from("<112H", rom, p)
    recovered = []
    for color in native:
        channels = (color & 31, (color >> 5) & 31, (color >> 10) & 31)
        demand(color < 0x8000 and all(x in lattice for x in channels), "RGB555 image lattice")
        recovered.append((lattice.index(channels[0]) << 8) | (lattice.index(channels[1]) << 4) | lattice.index(channels[2]))
    demand(tuple(recovered) == struct.unpack_from("<112H", bank, 0x89D8), "all seven palette rows inverse")
    p, length = DATA["spatial_y"]
    for i in range(5):
        y, count, pointer = struct.unpack_from("<HHI", rom, p + i * 8)
        original = struct.unpack_from("<4H", bank, 0x8FEF + i * 8)
        demand((y, count, pointer - BASE - DATA["spatial_x"][0] + 0x9017, 0) == original, "spatial pointer inverse")
    return {"source_bytes_inverted": 124 + 72 + 108 + 10 + 64 + 224 + 40,
            "palette_colors": 112, "spatial_row_pointers": 5, "source_alignment_retained": True}


def finite_arithmetic(source: bytes) -> dict:
    bank = source[0x740900:0x750900]
    for value in range(65536):
        x86_value = (value - 1) & 0xFFFF
        arm_value = ((value - 1) << 16 & 0xFFFFFFFF) >> 16
        demand((x86_value, x86_value == 0) == (arm_value, arm_value == 0), "16-bit decrement/ZF")
        hp_add = (value + 3) & 65535
        demand(s16(hp_add) == s16(value + 3), "HP add wrapping signed compare")
        # Negating a signed extreme must still write its original halfword.
        demand(u16(abs(s16(value))) == (value if value < 32768 else (-value & 65535)), "absolute halfword including8000")
    for angle in range(256):
        accumulator, expected = (angle + 16) & 255, 0
        while True:
            accumulator = (accumulator - 32) & 255
            if accumulator & 128:
                break
            expected += 1
        first_subtraction = (angle - 16) & 255
        native = 0 if first_subtraction >= 128 else first_subtraction // 32 + 1
        demand(expected == native, "source AL/SF frame choice")
    # Every possible signed X is covered in each Y comparison partition.
    y_samples = (-32768, 0, 0x107F, 0x1080, 0x1081, 0x1380, 0x1381,
                 0x1500, 0x1501, 0x1600, 0x1601, 0x1B00)
    rows = [struct.unpack_from("<4H", bank, 0x8FEF + 8 * i) for i in range(5)]
    count = 0
    for y in y_samples:
        row = next(row for row in rows if y <= s16(row[0]))
        entries = [struct.unpack_from("<2H", bank, row[2] + j * 4) for j in range(row[1])]
        for bits in range(65536):
            x = s16(bits)
            if x >= 0x1E00:
                continue
            idx = next(index for threshold, index in entries if x < s16(threshold))
            # Independent interval partition using the complete source list.
            partition = sum(x >= s16(t) for t, _ in entries)
            demand(idx == entries[partition][1] and 0 <= idx <= 9, "finite spatial X partition")
            count += 1
    # All source spawn ordinals and random variants, including unused padding.
    spawn_cases = 0
    for size in (2, 3):
        table, offsets = (0x9481, 0x9477) if size == 2 else (0x94A1, 0x947B)
        for variant, ordinal in itertools.product(range(4), range(size)):
            index = struct.unpack_from("<H", bank, table + variant * 8 + ordinal * 2)[0]
            demand(index < size, "spawn offset index bound")
            relative = struct.unpack_from("<h", bank, offsets + index * 2)[0]
            demand(relative in ((-128, 128) if size == 2 else (0, 256, -256)), "source child offset")
            spawn_cases += 1
    # Native BG zero slots and all other rows must remain untouched.
    palette_writes = {row * 32 + color * 2 for row in range(7) for color in range(1, 16)}
    demand(len(palette_writes) == 105 and not any(row * 32 in palette_writes for row in range(16)), "row-zero preservation")
    return {"all_u16_decrement_and_HP_inputs": 65536, "all_u8_angle_inputs": 256,
            "spatial_partition_cases": count, "spatial_y_representatives": len(y_samples),
            "spawn_cases": spawn_cases, "palette_halfword_writes": 105,
            "timers": {"375": 300, "225": 180, "75": 60, "105": 84, "20": 16, "18": 14}}


def finite_motion(source: bytes) -> dict:
    table = [struct.unpack_from("<6h", source, 0x74909E + 16 * i) for i in range(8)]

    def source_bounce(start, end, pos, vel, accel, phase):
        x, y = pos
        vx, vy = vel
        ax, ay = accel
        chosen, other = (end, start) if phase else (start, end)
        crossed = False
        # Follow the source's duplicated X and Y blocks literally.
        d = u16(chosen[0] - other[0])
        if d:
            if d & 0x8000:
                vx = max(-416, min(-128, vx))
                crossed = chosen[0] > x
            else:
                vx = max(128, min(416, vx))
                crossed = chosen[0] <= x
        if not crossed:
            d = u16(chosen[1] - other[1])
            if d:
                if d & 0x8000:
                    vy = max(-416, min(-128, vy))
                    crossed = chosen[1] > y
                else:
                    vy = max(128, min(416, vy))
                    crossed = chosen[1] <= y
        if crossed:
            return chosen, tuple(s16(-v) for v in (vx, vy)), tuple(s16(-v) for v in (ax, ay)), phase ^ 1
        return pos, (vx, vy), accel, phase

    def native_bounce(start, end, pos, vel, accel, phase):
        points = (start, end)
        destination, origin = points[phase], points[phase ^ 1]
        out = list(vel)
        for axis in (0, 1):
            difference = destination[axis] - origin[axis]
            if difference == 0:
                continue
            if difference & 32768:
                if out[axis] > -128:
                    out[axis] = -128
                if out[axis] < -416:
                    out[axis] = -416
                hit = destination[axis] > pos[axis]
            else:
                if out[axis] > 416:
                    out[axis] = 416
                if out[axis] < 128:
                    out[axis] = 128
                hit = destination[axis] <= pos[axis]
            if hit:
                return destination, tuple(s16(-v) for v in out), tuple(s16(-v) for v in accel), 1 - phase
        return pos, tuple(out), accel, phase

    def source_pursuit(start, end, pos, vel, delta):
        x, y = pos
        if start[0] != end[0]:
            if u16(start[0] - end[0]) & 32768:
                if x < start[0]:
                    x, y = start
                elif x > end[0]:
                    x, y = end
            else:
                if x < end[0]:
                    x, y = end
                elif x > start[0]:
                    x, y = start
                    # This source arm falls into the vertical block.
                    y = min(max(y, min(start[1], end[1])), max(start[1], end[1]))
        else:
            y = min(max(y, min(start[1], end[1])), max(start[1], end[1]))
        vx, vy = vel
        if vx and (not vy or abs(delta[0]) >= abs(delta[1])):
            flip = (delta[0] >= 0 and vx < 0) or (delta[0] < 0 and vx > 0)
        else:
            flip = (delta[1] >= 0 and vy < 0) or (delta[1] < 0 and vy > 0)
        if flip:
            vx, vy = s16(-vx), s16(-vy)
        return (x, y), (vx, vy)

    def native_pursuit(start, end, pos, vel, delta):
        x, y = pos
        if start[0] == end[0]:
            low, high = sorted((start[1], end[1]))
            y = low if y < low else high if y > high else y
        else:
            low_point, high_point = (start, end) if (start[0] - end[0]) & 32768 else (end, start)
            if x < low_point[0]:
                x, y = low_point
            elif x > high_point[0]:
                x, y = high_point
        axis = 1 if vel[0] == 0 else 0 if vel[1] == 0 else int(abs(delta[0]) < abs(delta[1]))
        reverse = (delta[axis] < 0 and vel[axis] > 0) or (delta[axis] >= 0 and vel[axis] < 0)
        return (x, y), tuple(s16(-v) for v in vel) if reverse else vel

    bounce_cases = pursuit_cases = 0
    for _, _, x0, y0, x1, y1 in table:
        start, end = (x0, y0), (x1, y1)
        xs = sorted({-32768, 32767, x0 - 1, x0, x0 + 1, x1 - 1, x1, x1 + 1})
        ys = sorted({-32768, 32767, y0 - 1, y0, y0 + 1, y1 - 1, y1, y1 + 1})
        for phase, x, y, vx, vy in itertools.product((0, 1), xs, ys, (-417, -128, 0, 128, 417), (-417, -128, 0, 128, 417)):
            args = (start, end, (x, y), (vx, vy), (-16, 16), phase)
            demand(source_bounce(*args) == native_bounce(*args), "source/native endpoint order and strict crossing")
            bounce_cases += 1
        for x, y, vel, delta in itertools.product(xs, ys, ((0, 0), (128, 0), (-128, 0), (128, 128), (-128, 128), (0, -128)),
                                                 ((0, 0), (1, 1), (-1, 1), (0, 2), (2, 1), (-2, -1), (-32768, 0), (-32768, -32768))):
            args = (start, end, (x, y), vel, delta)
            demand(source_pursuit(*args) == native_pursuit(*args), "source/native pursuit clamp and reversal")
            pursuit_cases += 1
    return {"motion_source_rows": 8, "bounce_branch_partitions": bounce_cases,
            "pursuit_branch_partitions": pursuit_cases, "negative_crossing_is_strict": True,
            "both_positions_snap_before_motion_negation": True}


def ownership(before: bytes, after: bytes) -> dict:
    demand(len(before) == len(after) == 0x800000, "ROM dimensions")
    intervals = [(row[0], row[0] + row[1], name) for name, row in BLOCKS.items()]
    intervals += [(p, p + length, name) for name, (p, length) in DATA.items()]
    permitted = bytearray(len(before))
    for start, end, name in intervals:
        demand(not any(permitted[start:end]), "overlap " + name)
        demand(before[start:end] == b"\xff" * (end - start), "Expected Write predecessor " + name)
        permitted[start:end] = b"\x01" * (end - start)
    changed = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    demand(changed and all(permitted[i] for i in changed), "final diff containment, including all enclosing gaps")
    candidates = []
    for site in range(len(before) - 3):
        value = struct.unpack_from("<I", before, site)[0]
        if 0x085CB000 <= value < 0x085D0000:
            candidates.append(("pointer", site, value - BASE))
    for site in range(0, len(before) - 3, 4):
        v = struct.unpack_from("<I", before, site)[0]
        if v & 0x0E000000 != 0x0A000000 or v >> 28 == 15:
            continue
        displacement = (v & 0xFFFFFF) - (0x1000000 if v & 0x800000 else 0)
        target = site + 8 + 4 * displacement
        if 0x5CB000 <= target < 0x5D0000:
            candidates.append(("branch", site, target))
    demand(not any(any(start <= target < end for start, end, _ in intervals) for _, _, target in candidates), "inbound candidate enters actual write")
    demand(after[0x5C0A00:0x5C0A04] == before[0x5C0A00:0x5C0A04] == bytes.fromhex("1EFF2FE1"), "9908 boundary retained")
    return {"changed_bytes": len(changed), "geometric_intervals": len(intervals),
            "unclassified_preserved_candidates": candidates, "9908_boundary": "BX LR unchanged"}


def rejection_checks(before: bytes, after: bytes, source: bytes) -> list[str]:
    results = []
    # Perturb a concrete semantic instruction from each risk-bearing family.
    for name, needle in (("81EA", "tst r8, #0x8000"), ("8266", "strh r8, [r1, #0x96]"),
                         ("heading", "tst r0, #0x80"), ("bounce", "bgt"),
                         ("8B28", "bl"), ("tracking", "strh r0, [r4, #0x44]"),
                         ("8E27", "strh r8, [r4, #0x48]"), ("8EF3", "bge"),
                         ("881A", "bl #0x8011e54"), ("933B", "str r8, [r4, #0x14]"),
                         ("984D", "bl")):
        site, length, code, _ = BLOCKS[name]
        i = next(i for i in decode(after, site, code) if (i.mnemonic + " " + i.op_str).startswith(needle))
        broken = bytearray(after)
        p = i.address - BASE
        struct.pack_into("<I", broken, p, 0xE1A00000)  # remove the indicated operation
        try:
            code_contract(broken)
        except ValueError:
            results.append(name + ": " + needle)
        else:
            raise ValueError("accepted omitted operation " + name)
    for name in DATA:
        broken = bytearray(after)
        broken[DATA[name][0]] ^= 1
        try:
            inverse_data(broken, source)
        except ValueError:
            results.append("source inverse " + name)
        else:
            raise ValueError("accepted corrupt table " + name)
    broken = bytearray(after)
    broken[0x5CB7A0] = 0
    try:
        ownership(before, broken)
    except ValueError:
        results.append("preserved incoming-target gap")
    else:
        raise ValueError("accepted named gap write")
    return results


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        p.add_argument(name, type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path)
    args = p.parse_args()
    before, after, gba, old, source = (getattr(args, n).read_bytes() for n in ("before", "after", "gba", "wsc10", "wsc15"))
    for data, expected, name in ((before, BEFORE_SHA256, "predecessor"), (gba, GBA_SHA256, "retail GBA"),
                                 (old, OLD_SHA256, "retail WSC"), (source, NEW_SHA256, "WSC1.5")):
        demand(sha(data) == expected, "identity " + name)
    result = {"schema": 1, "kind": "independent-shoot-lower-rules", "output_sha256": sha(after),
              "consumers": source_consumers(gba, old, source), "code": code_contract(after),
              "inverse": inverse_data(after, source), "finite_specifications": finite_arithmetic(source),
              "finite_motion": finite_motion(source),
              "ownership": ownership(before, after), "negative_cases": rejection_checks(before, after, source),
              "scope": "static resident graph; spatial valid-domain proof, external caller, runtime/audible QA excluded"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-shoot-lower-rules] PASS " + sha(json.dumps(result, sort_keys=True).encode()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
