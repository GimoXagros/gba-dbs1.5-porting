#!/usr/bin/env python3
"""Resident lower Shoot callbacks, translated into the existing retail ARM ABI.

This layer never replaces the 9908 boundary or installs an external caller.
It uses existing object fields, presentation/resource consumers, and scheduler.
No game or CPU is executed by this builder.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from capstone.arm_const import (ARM_INS_ADD, ARM_INS_AND, ARM_INS_ASR, ARM_INS_B, ARM_INS_BIC,
                               ARM_INS_BL, ARM_INS_BX, ARM_INS_CMP, ARM_INS_EOR, ARM_INS_LDR,
                               ARM_INS_LDRH, ARM_INS_LDRSH, ARM_INS_LSL, ARM_INS_LSR, ARM_INS_MOV,
                               ARM_INS_MVN, ARM_INS_ORR, ARM_INS_POP, ARM_INS_PUSH, ARM_INS_RSB,
                               ARM_INS_STR, ARM_INS_STRB, ARM_INS_STRH, ARM_INS_SUB, ARM_INS_TST)
from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

BASE = 0x08000000
INPUT_SHA256 = "0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
START, END = 0x5CB000, 0x5D0000
GAP_TARGETS = (0x5CB7A0, 0x5CC6F8, 0x5CDBA0, 0x5CE1A0, 0x5CE1E0,
               0x5CE210, 0x5CED34, 0x5CED50, 0x5CFB84, 0x5CFE70)
GAPS = tuple((x & ~31, (x & ~31) + 32) for x in GAP_TARGETS)
EVENT, UPDATE, FRAME = 0x08012874, 0x08012A84, 0x080129C8
RNG, ANGLE, TRIG_X, TRIG_Y = 0x08012600, 0x08012560, 0x0801233C, 0x08012348
ALLOCATE, PRIORITY, RELEASE = 0x08352374, 0x08011E54, 0x083524C4
SOUND = 0x080D15C0
FLAGS, SCROLL, HANDLE = 0x0300450A, 0x03004D40, 0x03004D54
RESOURCE_888B, RESOURCE_93E7 = 0x085C4600, 0x085C4500
IDLE, UPPER_7DD9, INTRO_PALETTE = 0x085BBC00, 0x085BF800, 0x085C0C00
# Native IDs and exact predecessor supplied by the independently verified
# lower-audio layer; no equal-numbered retail substitution is permitted.
CF_ID, D1_ID = 0x5D, 0x5E
AUDIO_DEPENDENCIES = (
    (0x5BA6E8, 16, "842B1544B651EFC0AF5FBB30B5F56EADEE6A4C111A1067E04E17AB0574678F59"),
    (0x5CA000, 169, "211F1717B4F80EF9D34976833E36142ED2257AE396D6F7E3BF44B5DEEFD2E92C"),
    (0x5CA100, 144, "C26570718A39C73572FB9C7994928370607E431F51546E300DE51EAC593D238B"),
    (0x5CA300, 36, "D20A562550E6E6209BC0DB2C31482A5EE23F2A5E3055E51CEB9C552D0D909C65"),
)
ARM7_IDS = {ARM_INS_ADD, ARM_INS_AND, ARM_INS_ASR, ARM_INS_B, ARM_INS_BIC,
            ARM_INS_BL, ARM_INS_BX, ARM_INS_CMP, ARM_INS_EOR, ARM_INS_LDR,
            ARM_INS_LDRH, ARM_INS_LDRSH, ARM_INS_LSL, ARM_INS_LSR, ARM_INS_MOV,
            ARM_INS_MVN, ARM_INS_ORR, ARM_INS_POP, ARM_INS_PUSH, ARM_INS_RSB,
            ARM_INS_STR, ARM_INS_STRB, ARM_INS_STRH, ARM_INS_SUB, ARM_INS_TST}
REGS = "{r0-r12, lr}"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def s16(reg: str) -> str:
    return f"lsl {reg}, {reg}, #16\nasr {reg}, {reg}, #16\n"


def u16(reg: str) -> str:
    return f"lsl {reg}, {reg}, #16\nlsr {reg}, {reg}, #16\n"


def event(number: int) -> str:
    return f"push {{r5}}\nmov r8, #0\npush {{r8}}\nmov r8, #{number}\npush {{r8}}\nbl 0x{EVENT:X}\nadd sp, sp, #12\n"


def update() -> str:
    return f"push {{r5}}\nmov r8, #0\npush {{r8}}\nmov r8, #1\npush {{r8}}\nbl 0x{UPDATE:X}\nadd sp, sp, #12\n"


def clear_motion(obj: str = "r4") -> str:
    return "mov r8, #0\n" + "".join(f"strh r8, [{obj}, #{x}]\n" for x in (0x42, 0x44, 0x46, 0x48))


def sound(number: int, kind: int) -> str:
    return f"mov r8, #{number}\nmov r9, #{kind}\nmov r10, #0\nbl 0x{SOUND:X}\n"


def decrement(field: int) -> str:
    # Source DEC is 16-bit; the flags must be tested after the wrap.
    return f"ldrh r8, [r4, #{field}]\nsub r8, r8, #1\nstrh r8, [r4, #{field}]\n" + u16("r8") + "cmp r8, #0\n"


class Function:
    def __init__(self, addresses: dict[str, int]):
        self.addresses = addresses
        self.literals: list[tuple[str, int]] = []

    def load(self, reg: str, value: int) -> str:
        label = "literal_" + str(len(self.literals))
        self.literals.append((label, value))
        return f"ldr {reg}, {label}\n"

    def callback(self, name: str | int, obj: str = "r4") -> str:
        addr = self.addresses[name] if isinstance(name, str) else name
        return self.load("r8", addr) + f"str r8, [{obj}]\n"

    def call(self, name: str) -> str:
        return f"bl 0x{self.addresses[name]:X}\n"

    def wait(self) -> str:
        return "ldrh r8, [r5, #10]\ntst r8, #0x2000\nbne ready\n" + update() + "b done\nready:\n"

    def finish(self, body: str, address: int, result: bool = False) -> tuple[bytes, int]:
        saved = "{r1-r12, lr}" if result else REGS
        code = f"push {saved}\nmov r11, #0\n" + body + f"done:\npop {saved}\nbx lr\n"
        literals = "".join(f"{label}: .word 0x{value:08X}\n" for label, value in self.literals)
        encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(code + literals, address)
        return bytes(encoded), len(encoded) - len(self.literals) * 4


def lower_810d(f: Function) -> str:
    return """mov r8, #0
        strh r8, [r4, #0x98]
        ldrh r8, [r4, #4]
        tst r8, #0x20
        bne start
        ldrh r8, [r5, #14]
        cmp r8, #1
        beq retire
        ldrh r8, [r5, #10]
        tst r8, #0x2000
        bne check_event
        """ + update() + """b done
    check_event:
        ldrh r8, [r5, #14]
        cmp r8, #0
        beq retire
    start:
        """ + f.call("813F") + "b done\nretire:\n" + f.call("81AB")


def lower_813f(f: Function) -> str:
    b = "ldrh r8, [r4, #4]\nbic r8, r8, #0x20\nstrh r8, [r4, #4]\n" + event(0)
    b += f"bl 0x{RNG:X}\nand r0, r0, #7\n" + f.load("r1", f.addresses["motion_table"])
    b += "add r1, r1, r0, lsl #4\n"
    for i, field in enumerate((0x34, 0x36, 0xA4, 0xA6, 0xA8, 0xAA)):
        b += f"ldrh r8, [r1, #{i * 2}]\nstrh r8, [r4, #{field}]\n"
    return b + clear_motion() + f.callback("81EA")


def lower_81ab(f: Function) -> str:
    return event(3) + clear_motion() + f.callback("81D1")


def lower_81d1(f: Function) -> str:
    return f.wait() + f.call("813F")


def lower_81ea(f: Function) -> str:
    b = f.wait()
    for n, a, z, vel in (("x", 0xA4, 0xA8, 0x42), ("y", 0xA6, 0xAA, 0x44)):
        b += f"""ldrh r8, [r4, #{a}]
        ldrh r9, [r4, #{z}]
        sub r8, r8, r9
        cmp r8, #0
        beq {n}_done
        tst r8, #0x8000
        mov r9, #0x80
        rsbne r9, r9, #0
        strh r9, [r4, #{vel}]
    {n}_done:
        """
    for a, z in ((0x56, 0x9A), (0x58, 0x9C)):
        b += f"ldrsh r8, [r4, #{a}]\ncmp r8, #0\nrsblt r8, r8, #0\nstrh r8, [r4, #{z}]\n"
    return b + event(5) + f.callback("8266")


def heading(f: Function) -> str:
    # Source AL add/sub wraps at eight bits and JS uses SF, not a signed divide.
    return f"""ldrsh r8, [r4, #0x56]
        push {{r8}}
        ldrsh r8, [r4, #0x58]
        push {{r8}}
        bl 0x{ANGLE:X}
        add sp, sp, #8
        add r0, r0, #0x10
        and r0, r0, #0xFF
        mov r1, #0
    frame_loop:
        sub r0, r0, #0x20
        and r0, r0, #0xFF
        tst r0, #0x80
        bne selected
        add r1, r1, #1
        b frame_loop
    selected:
        push {{r5}}
        mov r8, #0
        push {{r8}}
        mov r8, #5
        push {{r8}}
        push {{r1}}
        bl 0x{FRAME:X}
        add sp, sp, #16
        """


def lower_8266(f: Function) -> str:
    b = "ldrh r8, [r4, #0x64]\nadd r8, r8, #3\n" + s16("r8")
    b += "ldrsh r9, [r4, #0xA2]\ncmp r8, r9\nbgt active\n" + clear_motion()
    b += "ldr r1, [r4, #0x28]\nmov r8, #60\nstrh r8, [r1, #0x96]\n" + clear_motion("r1")
    b += f.callback("8CB4", "r1") + event(3) + f.callback("876A") + "b done\nactive:\n"
    b += f.load("r8", FLAGS) + "ldrh r8, [r8]\ntst r8, #8\nbeq bounce\n"
    for field in (0x42, 0x44):
        b += f"""ldrsh r8, [r4, #{field}]
        cmp r8, #0
        movgt r8, #0x1A0
        movlt r8, #0x1A0
        rsblt r8, r8, #0
        strh r8, [r4, #{field}]
        """
    b += "mov r8, #0\nstrh r8, [r4, #0x46]\nstrh r8, [r4, #0x48]\n" + f.callback("8526")
    return b + "b done\nbounce:\n" + f.call("heading") + f.call("bounce")


def bounce(f: Function) -> str:
    # Choose source endpoint 8E/90 or 92/94, preserving X-before-Y and the
    # asymmetric strict negative crossing comparison (JG, not JGE).
    b = """add r1, r4, #0xA4
        add r2, r4, #0xA8
        ldrh r8, [r4, #0x98]
        tst r8, #1
        addne r1, r4, #0xA8
        addne r2, r4, #0xA4
        """
    for axis, offset, pos, velocity, following in (("x", 0, 0x34, 0x42, "axis_y"), ("y", 2, 0x36, 0x44, "distance")):
        b += f"""axis_{axis}:
        ldrsh r8, [r1, #{offset}]
        ldrsh r9, [r2, #{offset}]
        sub r10, r8, r9
        cmp r10, #0
        beq {following}
        tst r10, #0x8000
        bne {axis}_negative
        ldrsh r9, [r4, #{velocity}]
        cmp r9, #0x1A0
        movgt r9, #0x1A0
        cmp r9, #0x80
        movlt r9, #0x80
        strh r9, [r4, #{velocity}]
        ldrsh r9, [r4, #{pos}]
        cmp r8, r9
        ble reached
        b {following}
    {axis}_negative:
        ldrsh r9, [r4, #{velocity}]
        mov r10, #0x80
        rsb r10, r10, #0
        cmp r9, r10
        movgt r9, r10
        sub r10, r10, #0x120
        cmp r9, r10
        movlt r9, r10
        strh r9, [r4, #{velocity}]
        ldrsh r9, [r4, #{pos}]
        cmp r8, r9
        bgt reached
        b {following}
        """
    b += "reached:\nldrh r8, [r1]\nstrh r8, [r4, #0x34]\nldrh r8, [r1, #2]\nstrh r8, [r4, #0x36]\n"
    for field in (0x42, 0x44, 0x46, 0x48):
        b += f"ldrh r8, [r4, #{field}]\nrsb r8, r8, #0\nstrh r8, [r4, #{field}]\n"
    b += """ldrh r8, [r4, #0x98]
        eor r8, r8, #1
        strh r8, [r4, #0x98]
    distance:
        ldrsh r8, [r4, #0x56]
        cmp r8, #0
        rsblt r8, r8, #0
        ldrh r9, [r4, #0x9A]
        cmp r8, r9
        blo speed_up
        bhi slow_down
        ldrsh r8, [r4, #0x58]
        cmp r8, #0
        rsblt r8, r8, #0
        ldrh r9, [r4, #0x9C]
        cmp r8, r9
        bhs slow_down
    speed_up:
        mov r1, #0x10
        b set_acceleration
    slow_down:
        mov r1, #0x10
        rsb r1, r1, #0
    set_acceleration:
        """
    for field, accel in ((0x42, 0x46), (0x44, 0x48)):
        b += f"""ldrsh r8, [r4, #{field}]
        cmp r8, #0
        movgt r9, r1
        rsblt r9, r1, #0
        strhne r9, [r4, #{accel}]
        """
    return b


def lower_8526(f: Function) -> str:
    b = "ldrh r8, [r4, #0x76]\ncmp r8, #0\nbeq moving\n" + clear_motion() + sound(0x4C, 2)
    b += "mov r0, #0\n" + f.call("881A") + "mov r0, #1\n" + f.call("881A")
    b += "mvn r0, #0\n" + f.call("881A") + "mov r8, #14\nstrh r8, [r4, #0x9E]\n"
    return b + f.callback("86D9") + "b done\nmoving:\n" + f.call("heading") + f.call("pursuit")


def pursuit(f: Function) -> str:
    # Keep the original X-first correction. A vertical-only motion instead
    # clamps Y without overwriting X. Then choose X or Y delta magnitude.
    b = """ldrsh r0, [r4, #0xA4]
        ldrsh r1, [r4, #0xA8]
        sub r2, r0, r1
        cmp r2, #0
        beq vertical
        tst r2, #0x8000
        bne x_ascending
        ldrsh r2, [r4, #0x34]
        cmp r2, r1
        blt snap_end
        cmp r2, r0
        bgt snap_start
        b direction
    x_ascending:
        ldrsh r2, [r4, #0x34]
        cmp r2, r0
        blt snap_start
        cmp r2, r1
        bgt snap_end
        b direction
    snap_start:
        ldrh r8, [r4, #0xA4]
        strh r8, [r4, #0x34]
        ldrh r8, [r4, #0xA6]
        strh r8, [r4, #0x36]
        b direction
    snap_end:
        ldrh r8, [r4, #0xA8]
        strh r8, [r4, #0x34]
        ldrh r8, [r4, #0xAA]
        strh r8, [r4, #0x36]
        b direction
    vertical:
        ldrsh r0, [r4, #0xA6]
        ldrsh r1, [r4, #0xAA]
        sub r2, r0, r1
        tst r2, #0x8000
        bne y_ascending
        ldrsh r2, [r4, #0x36]
        cmp r2, r1
        movlt r2, r1
        cmp r2, r0
        movgt r2, r0
        strh r2, [r4, #0x36]
        b direction
    y_ascending:
        ldrsh r2, [r4, #0x36]
        cmp r2, r0
        movlt r2, r0
        cmp r2, r1
        movgt r2, r1
        strh r2, [r4, #0x36]
    direction:
        ldrsh r0, [r4, #0x42]
        ldrsh r1, [r4, #0x44]
        cmp r0, #0
        beq use_y
        cmp r1, #0
        beq use_x
        ldrsh r2, [r4, #0x56]
        cmp r2, #0
        rsblt r2, r2, #0
        ldrsh r3, [r4, #0x58]
        cmp r3, #0
        rsblt r3, r3, #0
        cmp r2, r3
        blo use_y
    use_x:
        ldrsh r2, [r4, #0x56]
        cmp r2, #0
        blt x_delta_negative
        cmp r0, #0
        bge done
        b reverse
    x_delta_negative:
        cmp r0, #0
        ble done
        b reverse
    use_y:
        ldrsh r2, [r4, #0x58]
        cmp r2, #0
        blt y_delta_negative
        cmp r1, #0
        bge done
        b reverse
    y_delta_negative:
        cmp r1, #0
        ble done
    reverse:
        rsb r0, r0, #0
        rsb r1, r1, #0
        strh r0, [r4, #0x42]
        strh r1, [r4, #0x44]
        """
    return b


def lower_86d9(f: Function) -> str:
    return decrement(0x9E) + "bne done\nmov r8, #84\nstrh r8, [r4, #0x9E]\n" + event(4) + f.callback("86FC")


def palette_copy(f: Function, palette: int) -> str:
    return f.load("r0", palette) + f.load("r1", 0x05000000) + """mov r2, #7
    row_loop:
        add r0, r0, #2
        add r1, r1, #2
        mov r3, #15
    color_loop:
        ldrh r8, [r0], #2
        strh r8, [r1], #2
        subs r3, r3, #1
        bne color_loop
        subs r2, r2, #1
        bne row_loop
        """


def lower_86fc(f: Function) -> str:
    b = decrement(0x9E) + "beq restore\n" + update() + "b done\nrestore:\n"
    b += f.load("r8", FLAGS) + "ldrh r9, [r8]\nbic r9, r9, #0x4000\nbic r9, r9, #0x28\nstrh r9, [r8]\n"
    b += f.load("r8", SCROLL) + "mov r9, #0x3F\nstrh r9, [r8]\n" + palette_copy(f, INTRO_PALETTE)
    return b + "mov r8, #0\nstrh r8, [r4, #0x76]\n" + event(3) + f.callback("876A")


def lower_876a(f: Function) -> str:
    # Retain the RNG-derived source value handed to the existing upper graph;
    # this is not an independently owned elapsed-duration countdown here.
    return f.wait() + f"bl 0x{RNG:X}\nand r0, r0, #0xFF\nadd r0, r0, #75\nstrh r0, [r4, #0x98]\nldrh r8, [r4, #4]\norr r8, r8, #0x20\nstrh r8, [r4, #4]\n" + f.callback(UPPER_7DD9)


def linked_entry(f: Function, number: int, callback: str) -> str:
    b = clear_motion() + """ldr r1, [r4, #0x18]
        ldrh r8, [r1, #0x34]
        strh r8, [r4, #0x34]
        ldrh r8, [r1, #0x36]
        sub r8, r8, #0x300
        strh r8, [r4, #0x36]
        """ + event(number)
    b += """ldrh r8, [r4, #4]
        bic r8, r8, #0x20
        strh r8, [r4, #4]
        ldr r1, [r4, #0x28]
        ldrh r8, [r1, #0xA0]
        orr r8, r8, #1
        strh r8, [r1, #0xA0]
        """
    return b + sound(0x5B, 1) + f.callback(callback)


def lower_8ab8(f: Function) -> str:
    return linked_entry(f, 12, "8B28")


def lower_8b28(f: Function) -> str:
    return f.wait() + event(9) + f.callback("8B53") + f.call("8B53")


def lower_8b53(f: Function) -> str:
    return f.wait() + "mov r8, #0\nstrh r8, [r4, #0x94]\nmov r8, #300\nstrh r8, [r4, #0x96]\n" + event(10) + f.callback("8B8A")


def lower_8b8a(f: Function) -> str:
    b = decrement(0x96) + "beq expire\n" + f.call("tracking") + "b done\nexpire:\n" + event(11)
    b += f.load("r8", FLAGS) + "ldrh r9, [r8]\norr r9, r9, #0x4000\norr r9, r9, #0x28\nstrh r9, [r8]\n"
    b += f.load("r8", SCROLL) + "mov r9, #1\nstrh r9, [r8]\n" + palette_copy(f, f.addresses["active_palette"])
    return b + clear_motion() + sound(CF_ID, 2) + f.callback("8C86")


def tracking(f: Function) -> str:
    b = update() + f"""ldr r1, [r4, #0x18]
        ldrh r8, [r4, #0x94]
        push {{r8}}
        bl 0x{TRIG_Y:X}
        add sp, sp, #4
        ldrh r8, [r4, #0x94]
        add r8, r8, #1
        and r8, r8, #0xFF
        strh r8, [r4, #0x94]
        """ + s16("r0") + "asr r0, r0, #2\n"
    b += "ldrsh r2, [r1, #0x36]\nsub r2, r2, #0x280\n" + s16("r2")
    b += """ldrsh r3, [r4, #0x36]
        cmp r2, r3
        bgt lower_check
        sub r0, r0, #0x180
        b y_done
    lower_check:
        sub r2, r2, #0x100
        """ + s16("r2") + """cmp r2, r3
        addge r0, r0, #0x180
    y_done:
        strh r0, [r4, #0x44]
        ldrh r0, [r1, #0x34]
        add r0, r0, #0x10
        """ + u16("r0") + """ldrh r2, [r4, #0x34]
        cmp r0, r2
        blo negative
        sub r0, r0, #0x20
        """ + u16("r0") + """cmp r0, r2
        movhi r0, #0x180
        movls r0, #0
        b x_done
    negative:
        mov r0, #0x180
        rsb r0, r0, #0
    x_done:
        strh r0, [r4, #0x42]
        """
    return b


def lower_8c86(f: Function) -> str:
    return f.wait() + "ldr r1, [r4, #0x28]\nmvn r8, #0\nstrh r8, [r1, #0x76]\nmov r8, #60\nstrh r8, [r4, #0x96]\n" + f.callback("8CB4")


def lower_8cb4(f: Function) -> str:
    return decrement(0x96) + """ldrh r9, [r4, #4]
        beq hide
        eor r9, r9, #0x20
        strh r9, [r4, #4]
        b done
    hide:
        orr r9, r9, #0x20
        strh r9, [r4, #4]
        mov r8, #0xFC00
        strh r8, [r4, #0x34]
        ldr r1, [r4, #0x28]
        ldrh r8, [r1, #0xA0]
        bic r8, r8, #1
        strh r8, [r1, #0xA0]
        """ + f.callback(IDLE)


def lower_8cdd(f: Function) -> str:
    return linked_entry(f, 4, "8D4D")


def lower_8d4d(f: Function) -> str:
    return f.wait() + "mov r8, #0\nstrh r8, [r4, #0x94]\nmov r8, #180\nstrh r8, [r4, #0x96]\n" + event(5) + f.callback("8D84")


def lower_8d84(f: Function) -> str:
    return decrement(0x96) + "beq expire\n" + f.call("tracking") + "b done\nexpire:\n" + event(7) + """mov r8, #0xFE00
        strh r8, [r4, #0x44]
        mov r8, #0x10
        strh r8, [r4, #0x48]
        mov r8, #16
        strh r8, [r4, #0x96]
        ldr r1, [r4, #0x18]
        ldrh r8, [r1, #0x36]
        strh r8, [r4, #0xA2]
        """ + f.callback("8E27")


def lower_8e27(f: Function) -> str:
    return decrement(0x96) + "bne follow\n" + event(8) + """mov r8, #0
        strh r8, [r4, #0x42]
        strh r8, [r4, #0x44]
        strh r8, [r4, #0x48]
        """ + f.callback("8E7F") + """b done
    follow:
        ldr r1, [r4, #0x18]
        ldrh r8, [r1, #0x34]
        ldrh r9, [r4, #0x34]
        cmp r8, r9
        movhi r8, #0x180
        movlo r8, #0x180
        rsblo r8, r8, #0
        moveq r8, #0
        strh r8, [r4, #0x42]
        """ + update()


def lower_8e7f(f: Function) -> str:
    b = f.wait() + f.callback(IDLE) + "ldrh r8, [r4, #4]\norr r8, r8, #0x20\nstrh r8, [r4, #4]\n" + f.call("8EF3")
    # Source equivalence is not established outside the finite table domain.
    # Reject that boundary without a coordinate clamp or an out-of-table read.
    b += "cmp r0, #0\nbeq done\nmov r8, #1\nstrh r8, [r4, #0x96]\nmov r8, #0\nstrh r8, [r4, #0x98]\nmov r8, #0xFC00\nstrh r8, [r4, #0x34]\n"
    return b + f.callback("8EC1")


def lower_8ec1(f: Function) -> str:
    return decrement(0x96) + "bne done\n" + f.call("933B") + """ldrh r8, [r4, #0x98]
        add r8, r8, #1
        strh r8, [r4, #0x98]
        """ + u16("r8") + """ldrh r9, [r4, #0xA4]
        cmp r8, r9
        beq finish
        mov r8, #16
        strh r8, [r4, #0x96]
        b done
    finish:
        ldr r1, [r4, #0x28]
        ldrh r8, [r1, #0xA0]
        bic r8, r8, #1
        strh r8, [r1, #0xA0]
        """ + f.callback(IDLE)


def lower_8ef3(f: Function) -> str:
    b = """mov r0, #0
        ldrsh r1, [r4, #0xA2]
        cmp r1, #0x1B00
        bgt done
        ldrsh r2, [r4, #0x34]
        cmp r2, #0x1E00
        bge done
        """ + f.load("r3", f.addresses["spatial_y"]) + "mov r6, #5\n"
    b += """find_y:
        ldrsh r8, [r3]
        cmp r1, r8
        ble y_found
        add r3, r3, #8
        subs r6, r6, #1
        bne find_y
        b done
    y_found:
        ldrh r6, [r3, #2]
        ldr r3, [r3, #4]
    find_x:
        ldrsh r8, [r3]
        cmp r2, r8
        blt x_found
        add r3, r3, #4
        subs r6, r6, #1
        bne find_x
        b done
    x_found:
        ldrh r1, [r3, #2]
        cmp r1, #9
        bhi done
        cmp r1, #0
        beq zero_case
        sub r1, r1, #1
        """ + f.load("r3", f.addresses["spatial_vectors"]) + "add r3, r3, r1, lsl #3\n"
    for offset, field in ((0, 0xA8), (2, 0xAA), (4, 0xA4)):
        b += f"ldrh r8, [r3, #{offset}]\nstrh r8, [r4, #{field}]\n"
    b += f"bl 0x{RNG:X}\nand r0, r0, #3\nstrh r0, [r4, #0xA6]\nmov r0, #1\nb done\nzero_case:\n"
    b += f"""mov r8, #0x1900
        strh r8, [r4, #0xAA]
        mov r8, #3
        strh r8, [r4, #0xA4]
        bl 0x{RNG:X}
        and r0, r0, #3
        strh r0, [r4, #0xA6]
        ldrh r8, [r4, #0x34]
        cmp r8, #0x580
        movls r8, #0x580
        cmp r8, #0x1680
        movhs r8, #0x1680
        strh r8, [r4, #0xA8]
        mov r0, #1
        """
    return b


def allocate_child(f: Function) -> str:
    # The existing retail allocator explicitly uses FP as the shared zero.
    # Preserve the target BEFORE allocation, as source BP-4/BP-8 does.
    b = "ldr r8, [r6, #0x18]\npush {r8}\nmov r11, #0\n" + f.load("r8", HANDLE) + "push {r8}\nmov r8, #0\npush {r8}\npush {r8}\npush {r8}\n"
    b += "mov r8, #0x4100\norr r8, r8, #4\npush {r8}\nmov r8, #1\npush {r8}\nmov r8, #0\npush {r8}\n"
    b += f"bl 0x{ALLOCATE:X}\nadd sp, sp, #28\n" + f.load("r8", HANDLE) + "ldr r4, [r8]\n"
    b += f"""sub r8, r4, #0x18
        push {{r8}}
        mov r8, #0
        push {{r8}}
        mov r8, #0x4000
        push {{r8}}
        bl 0x{PRIORITY:X}
        add sp, sp, #12
        mov r8, #1
        strb r8, [r4, #0x10]
        """
    return b


def lower_881a(f: Function) -> str:
    b = "mov r6, r4\nmov r7, r0\n" + allocate_child(f)
    b += "str r6, [r4, #0x14]\npop {r8}\nstr r8, [r4, #0x18]\nldrh r8, [r6, #0x34]\nstrh r8, [r4, #0x34]\nldrh r8, [r6, #0x36]\nstrh r8, [r4, #0x36]\n"
    b += f"add r5, r4, #0xAC\nbl 0x{RESOURCE_888B:X}\n" + clear_motion() + "strh r7, [r4, #0xA0]\n" + event(0)
    b += "ldrh r8, [r5, #8]\norr r8, r8, #0x2000\nstrh r8, [r5, #8]\n"
    return b + f.callback("97BB")


def lower_933b(f: Function) -> str:
    # Source 8EF3 and 8EC1 provide count=2/3, variation=0..3, ordinal<count.
    # Validate their complete finite domain before allocating an object.
    b = """ldrh r8, [r4, #0xA4]
        cmp r8, #2
        beq count_valid
        cmp r8, #3
        bne done
    count_valid:
        ldrh r9, [r4, #0xA6]
        cmp r9, #4
        bhs done
        ldrh r10, [r4, #0x98]
        cmp r10, r8
        bhs done
        mov r6, r4
        ldr r8, [r6, #0x28]
        push {r8}
        """ + allocate_child(f)
    b += "pop {r1}\npop {r8}\nstr r8, [r4, #0x14]\nstr r1, [r4, #0x18]\nldrh r0, [r6, #0xA6]\nlsl r0, r0, #3\nldrh r1, [r6, #0x98]\nadd r0, r0, r1, lsl #1\n"
    b += f.load("r1", f.addresses["spawn_patterns"]) + "ldrh r8, [r6, #0xA4]\ncmp r8, #2\naddne r1, r1, #32\nldrh r0, [r1, r0]\nlsl r0, r0, #1\n"
    b += f.load("r1", f.addresses["spawn_offsets"]) + "cmp r8, #2\naddne r1, r1, #4\nldrsh r0, [r1, r0]\nldrh r1, [r6, #0xA8]\nadd r0, r0, r1\nstrh r0, [r4, #0x34]\n"
    b += "ldrh r8, [r6, #0xAA]\nstrh r8, [r4, #0x36]\nadd r5, r4, #0xAC\n"
    b += f"bl 0x{RESOURCE_93E7:X}\n" + clear_motion() + event(0)
    b += "ldrh r8, [r5, #8]\norr r8, r8, #0x2000\nstrh r8, [r5, #8]\n"
    return b + sound(D1_ID, 1) + f.callback("9798")


def lower_9798(f: Function) -> str:
    return f.wait() + f"push {{r4}}\nmov r8, #0\npush {{r8}}\nbl 0x{RELEASE:X}\nadd sp, sp, #8\n"


def lower_97bb(f: Function) -> str:
    b = f.wait() + f"""ldr r1, [r4, #0x14]
        ldrsh r8, [r1, #0x56]
        push {{r8}}
        ldrsh r8, [r1, #0x58]
        push {{r8}}
        bl 0x{ANGLE:X}
        add sp, sp, #8
        ldrsh r8, [r4, #0xA0]
        cmp r8, #0
        addgt r0, r0, #0x10
        sublt r0, r0, #0x10
        and r6, r0, #0xFF
        push {{r6}}
        bl 0x{TRIG_X:X}
        add sp, sp, #4
        lsl r0, r0, #1
        strh r0, [r4, #0x42]
        push {{r6}}
        bl 0x{TRIG_Y:X}
        add sp, sp, #4
        lsl r0, r0, #1
        strh r0, [r4, #0x44]
        """ + event(1)
    return b + "mov r8, #84\nstrh r8, [r4, #0xA2]\n" + f.callback("984D")


def lower_984d(f: Function) -> str:
    return decrement(0xA2) + "beq expire\n" + update() + "b done\nexpire:\n" + event(2) + f.callback("9879") + f.call("9879")


FUNCTIONS = {
    "810D": lower_810d, "813F": lower_813f, "81AB": lower_81ab, "81D1": lower_81d1,
    "81EA": lower_81ea, "8266": lower_8266, "heading": heading, "bounce": bounce,
    "8526": lower_8526, "pursuit": pursuit, "86D9": lower_86d9, "86FC": lower_86fc,
    "876A": lower_876a, "8AB8": lower_8ab8, "8B28": lower_8b28, "8B53": lower_8b53,
    "8B8A": lower_8b8a, "tracking": tracking, "8C86": lower_8c86, "8CB4": lower_8cb4,
    "8CDD": lower_8cdd, "8D4D": lower_8d4d, "8D84": lower_8d84, "8E27": lower_8e27,
    "8E7F": lower_8e7f, "8EC1": lower_8ec1, "8EF3": lower_8ef3, "881A": lower_881a,
    "933B": lower_933b, "9798": lower_9798, "97BB": lower_97bb, "984D": lower_984d,
    "9879": lower_9798,
}
DATA_LENGTHS = {"motion_table": 124, "active_palette": 224, "spatial_vectors": 72,
                "spatial_y": 40, "spatial_x": 108, "spawn_offsets": 10, "spawn_patterns": 64}


def next_slot(cursor: int, size: int) -> int:
    cursor = (cursor + 15) & ~15
    while any(cursor < hi and lo < cursor + size for lo, hi in GAPS):
        cursor = max(hi for lo, hi in GAPS if cursor < hi and lo < cursor + size)
        cursor = (cursor + 15) & ~15
    demand(cursor + size <= END, "lower callbacks exceed guarded reservation")
    return cursor


def layout() -> tuple[dict[str, int], dict[str, tuple[bytes, int]]]:
    names = tuple(FUNCTIONS) + tuple(DATA_LENGTHS)
    addresses = {name: BASE + START for name in names}
    lengths = {}
    for name, builder in FUNCTIONS.items():
        f = Function(addresses)
        body = builder(f)
        blob, code = f.finish(body, addresses[name], result=name == "8EF3")
        lengths[name] = (len(blob), code)
    cursor = START
    for name in names:
        size = lengths[name][0] if name in lengths else DATA_LENGTHS[name]
        cursor = next_slot(cursor, size)
        addresses[name] = BASE + cursor
        cursor += size
    blocks = {}
    for name, builder in FUNCTIONS.items():
        f = Function(addresses)
        body = builder(f)
        blob, code = f.finish(body, addresses[name], result=name == "8EF3")
        demand((len(blob), code) == lengths[name], f"unstable code layout: {name}")
        blocks[name] = (blob, code)
    return addresses, blocks


def source_data(wsc: bytes, addresses: dict[str, int]) -> dict[str, bytes]:
    bank = wsc[0x740900:0x750900]
    output = {"motion_table": bank[0x879E:0x881A], "spatial_vectors": bank[0x8F93:0x8FDB],
              "spatial_x": bank[0x9017:0x9083], "spawn_offsets": bank[0x9477:0x9481],
              "spawn_patterns": bank[0x9481:0x94C1]}
    lattice = (0, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)
    colors = struct.unpack_from("<112H", bank, 0x89D8)
    demand(all(x < 0x1000 for x in colors), "invalid source RGB444 palette")
    output["active_palette"] = struct.pack("<112H", *(lattice[(x >> 8) & 15] | (lattice[(x >> 4) & 15] << 5) | (lattice[x & 15] << 10) for x in colors))
    rows = bytearray()
    for i in range(5):
        y, count, pointer, reserved = struct.unpack_from("<4H", bank, 0x8FEF + i * 8)
        demand(reserved == 0 and 0x9017 <= pointer < 0x9083, "source spatial row contract")
        rows += struct.pack("<HHI", y, count, addresses["spatial_x"] + pointer - 0x9017)
    output["spatial_y"] = bytes(rows)
    for name, data in output.items():
        demand(len(data) == DATA_LENGTHS[name], f"source data size: {name}")
    return output


def refs(data: bytes) -> list[dict[str, int | str]]:
    found = []
    for site in range(len(data) - 3):
        value = struct.unpack_from("<I", data, site)[0]
        if BASE + START <= value < BASE + END:
            found.append({"kind": "pointer_candidate", "site": site, "target": value - BASE})
    for site in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, site)[0]
        if value >> 28 == 15 or value & 0x0E000000 != 0x0A000000:
            continue
        displacement = value & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 0x1000000
        target = site + 8 + displacement * 4
        if START <= target < END:
            found.append({"kind": "branch_candidate", "site": site, "target": target})
    return found


def placements(wsc: bytes) -> tuple[dict[str, int], list[tuple[str, int, bytes, int]]]:
    addresses, blocks = layout()
    blocks.update({name: (blob, 0) for name, blob in source_data(wsc, addresses).items()})
    return addresses, [(name, addresses[name] - BASE, blob, code) for name, (blob, code) in blocks.items()]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=pathlib.Path)
    p.add_argument("gba", type=pathlib.Path)
    p.add_argument("wsc15", type=pathlib.Path)
    p.add_argument("output", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path)
    p.add_argument("--layout-only", action="store_true")
    args = p.parse_args()
    before, gba, wsc = args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes()
    for name, data, sha in (("v51 plus lower audio", before, INPUT_SHA256), ("retail GBA", gba, GBA_SHA256), ("WSC 1.5", wsc, WSC15_SHA256)):
        demand(digest(data) == sha, f"{name} identity")
    addresses, writes = placements(wsc)
    if args.layout_only:
        print(json.dumps({name: {"address": hex(start + BASE), "bytes": len(blob), "code": code} for name, start, blob, code in writes}, indent=2))
        return 0
    demand(bool(AUDIO_DEPENDENCIES), "CF/D1 native command proof and song integration remain unresolved")
    for site, size, expected in AUDIO_DEPENDENCIES:
        demand(digest(before[site:site + size]) == expected, "CF/D1 song/table dependency identity")
    incoming = refs(before)
    result = bytearray(before)
    masks = bytearray(len(before))
    details = []
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for name, start, blob, code in writes:
        end = start + len(blob)
        demand(before[start:end] == b"\xff" * len(blob), f"Expected Write is not blank: {name}")
        demand(not any(start <= r["target"] < end for r in incoming), f"pre-existing reference reaches {name}")
        demand(not any(masks[start:end]), f"overlapping placement {name}")
        if code:
            decoded = list(engine.disasm(blob[:code], start + BASE))
            demand(sum(i.size for i in decoded) == code and all(i.size == 4 for i in decoded), f"incomplete ARM code: {name}")
            demand(all(i.id in ARM7_IDS for i in decoded), f"unsupported ARM7TDMI instruction: {name}")
            reencoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm("\n".join(i.mnemonic + " " + i.op_str for i in decoded), start + BASE)
            demand(bytes(reencoded) == blob[:code], f"ARM round trip: {name}")
        result[start:end] = blob
        masks[start:end] = b"\x01" * len(blob)
        details.append({"name": name, "start": start, "bytes": len(blob), "code_bytes": code,
                        "before_sha256": digest(before[start:end]), "after_sha256": digest(blob)})
    changed = [i for i, (a, b) in enumerate(zip(before, result, strict=True)) if a != b]
    demand(changed and all(masks[i] for i in changed), "unexplained lower-rule diff")
    demand(before[0x5C0A00:0x5C0A04] == bytes(result[0x5C0A00:0x5C0A04]) == bytes.fromhex("1EFF2FE1"), "9908 boundary changed")
    manifest = {"schema": 1, "kind": "resident-shoot-lower-rules", "input_sha256": digest(before),
                "output_sha256": digest(result), "addresses": addresses, "expected_writes": details,
                "actual_changed_bytes": len(changed), "inbound_candidates_preserved": incoming,
                "source_overlay_base": 0x740900, "source_sha256": WSC15_SHA256,
                "audio_dependencies": AUDIO_DEPENDENCIES, "native_sounds": {"CE": 0x5B, "A9": 0x4C, "CF": CF_ID, "D1": D1_ID},
                "spatial_precondition": "signed object X < 1E00; signed captured target Y <= 1B00; failed domain returns idle without coordinate clamp",
                "countdowns": {"375": 300, "225": 180, "75": 60, "105": 84, "20": 16, "18": 14},
                "orbit_cadence": "source +1 per native callback, no invented phase state; runtime cadence QA pending",
                "claim_scope": "resident lower graph only; external entry/9908 boundary, runtime and audible QA excluded"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-lower-rules] {manifest['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
