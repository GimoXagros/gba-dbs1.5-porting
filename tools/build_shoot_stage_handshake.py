#!/usr/bin/env python3
"""Port the closed Shoot stage-transition effects on existing engine owners.

The main update is connected. The display entry is resident and requires a
proved native 0D87 callback in r0; the interrupted-DI dependency of source
0DEC is deliberately not replaced by guessed state or a no-op callback.
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
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

BASE = 0x08000000
INPUT_SHA256 = "00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7"
HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
START, END = 0x5E7000, 0x5E9000
UPDATE, DISPLAY, NORMAL_IRQ = START, 0x5E7400, 0x5E7800
SOURCE_GUARDS = (
    ("wsc15", 0x75FADA, 0x75FE03, "E4B0AC7FCC0253B9BE437C951368C3F222FDD867583CE723637C91EC1AC9FA93"),
    ("wsc15", 0x77387A, 0x7738C6, "E816020DE72D5E59C1111D761C865133D097C8B9C36DA41E5EE08842477EAA04"),
    ("wsc15", 0x750F25, 0x750F3C, "6828C5BE76B251EAE57A0700D4DF9A1B79BE1510BB7FAC477B75E06F867ABBBF"),
    ("wsc15", 0x753357, 0x7537B0, "7DB1BBE22739EF8EDEDAA91F0AFFD8FA1B600C44D59BD74922D8D41B27A9459B"),
    ("wsc10", 0x3B5B21, 0x3B5B79, "61E02649780D78BDB36373804D772E547D38CE8914AF31DEBC2F16A97226F6E9"),
    ("wsc10", 0x3B6B34, 0x3B6B5F, "C7A7F22468472F2C7EB61955CE9F78728950DEE23F0F87951CBDB46101A8ED27"),
    ("gba", 0x893F0, 0x89450, "22012BA7FC417397A7225FCC2968CA7C35813993E128299B1F6B161983032937"),
    ("gba", 0x8972C, 0x89740, "34EA12787458781EE8583761445700E1D981BD82C0829A39E12411A1E1A22EC8"),
    ("gba", 0x8AD00, 0x8AD2C, "3D0B5A48B61EFF723D7596A9452A34450AA11D6C99628853358A6C80390EC87C"),
    ("gba", 0x8ADAC, 0x8ADBC, "055FACE594A6165FCD333170E07061EF5FAF88DF5AD9126C6252191381CE6137"),
    ("gba", 0x13DD4, 0x14554, "13CD0DD6F48C2FBFEC59AB1F57F897E01F68F143ED33F235DB415BD6A5BADEBA"),
    ("gba", 0xEF0, 0x103C, "21F6D2EBD7FBC2D2445AC26A8EBF816BC61957DF3A7BDCE4530B3917F3737C3D"),
    ("gba", 0x1064, 0x10F8, "7A24DAC6BB3F78C0A6053F7392822655A6AB4C0197ACE183376DED526B370BAB"),
    ("wsc10", 0x3BF8E1, 0x3BF923, "E8DE9C31909E2AA74C1720C4AF6CFE2524D57784C3F0F647F5982837A669A00A"),
    ("wsc10", 0x3BFB6A, 0x3BFB9F, "F76E677DB04D1F63CCF6697B00CA3D0FFB507B0F9DFDDAE542AC821DFBB84A54"),
    ("gba", 0xC90F0, 0xC9164, "C129DCDEB1F40C76AFE27CC964C5568B03B775C4FB4E174802E885E0CD24FC4E"),
    ("gba", 0xC92C8, 0xC9328, "77C754F8CBBB2BFAB7840074E1EF467D27DA00624104884884C238D25821E196"),
    ("wsc10", 0x39072C, 0x3907D5, "12D365B246D5459A8B9F60F10CFAB557F2831FDE7EFC452EB99FA6DC144CE9C2"),
    ("gba", 0xC97B8, 0xC9814, "9A77CD62FCCEA58C61D50BF51B23C836647BD1B70CE6CA5B1B81FC7A72999089"),
    ("gba", 0xC98EC, 0xC9900, "DE2BCD70F36F8EFCAA8C26FE6BEADBC2A115A5339DDC528A6C565410FEC1B335"),
    ("wsc10", 0x3BC801, 0x3BC898, "5A35E1EE297FFB43480DA8B49182B1779CA29D1C7F8B0DCA3272773ADE69FB45"),
    ("gba", 0xD0B24, 0xD0BC0, "BEB7F435B56D93A439220C563B84C8F268D5EBCC3BC9C49E3600F05EDBBB8463"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def assemble(text: str, raw: int, literals: int) -> tuple[bytes, int]:
    out, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, BASE + raw)
    blob = bytes(out)
    return blob, len(blob) - literals


def update() -> tuple[bytes, int]:
    return assemble("""
        push {r0-r12, lr}
        mov r11, #0
        ldr r4, state
        ldr r6, flags
        ldrh r8, [r6]
        tst r8, #0x200
        beq wipe
        ldr r5, bg_one
        mov r8, #0x200
        strh r8, [r5, #0x1C]
        ldrh r8, [r4]
        tst r8, #1
        movne r8, #0x80
        moveq r8, #0
        strh r8, [r5, #0x1E]
        movne r0, #9
        moveq r0, #2
        push {r5}
        push {r11}
        push {r0}
        bl 0x08013DD4
        add sp, sp, #12
        ldr r4, state
        ldr r5, bg_one
        ldr r6, flags
        ldr r7, shadow_one
        ldrb r0, [r5, #0x1A]
        strb r0, [r7]
        ldrb r0, [r5, #0x1B]
        strb r0, [r7, #1]
        ldrh r0, [r4]
        sub r0, r0, #1
        strh r0, [r4]
        lsl r0, r0, #16
        cmp r0, #0
        bne shake
        ldr r8, scroll_y_shadow
        ldrb r0, [r8]
        strh r0, [r4, #8]
        mov r0, #0
        strh r0, [r5, #0x1C]
        strh r0, [r5, #0x1E]
        ldrh r8, [r6]
        bic r8, r8, #0x200
        strh r8, [r6]
        orr r8, r8, #0x400
        strh r8, [r6]
        ldr r5, initial_map
        mov r2, #0x1C0
        bl 0x08001064
        b shake
    wipe:
        tst r8, #0x400
        beq shake
        ldrh r0, [r4, #2]
        tst r0, #7
        bne shake
        ldrb r8, [r4, #10]
        sub r8, r8, #8
        strb r8, [r4, #10]
        ldrb r8, [r4, #8]
        add r0, r0, r8
        and r0, r0, #0xFF
        lsr r0, r0, #3
        ldr r5, map
        add r5, r5, r0, lsl #6
        mov r0, #0
        mov r2, #32
        bl 0x08001064
    shake:
        ldr r4, state
        ldr r6, flags
        ldrh r8, [r6]
        tst r8, #0x1000
        beq done
        tst r8, #0x2000
        beq advance
        ldrh r0, [r4, #12]
        tst r0, #8
        bne advance
        bic r8, r8, #0x3000
        strh r8, [r6]
        b done
    advance:
        ldrh r0, [r4, #12]
        add r0, r0, #1
        strh r0, [r4, #12]
        tst r0, #3
        bne done
        tst r0, #4
        movne r0, #1
        moveq r0, #4
        ldr r5, bg_zero
        mov r8, #0x200
        strh r8, [r5, #0x1E]
        mov r11, #0
        push {r5}
        push {r11}
        push {r0}
        bl 0x08013DD4
        add sp, sp, #12
        ldr r5, bg_zero
        ldr r7, shadow_zero
        ldrb r0, [r5, #0x1A]
        strb r0, [r7]
        ldrb r0, [r5, #0x1B]
        strb r0, [r7, #1]
    done:
        pop {r0-r12, lr}
        bx lr
    state: .word 0x03004710
    flags: .word 0x0300450A
    bg_one: .word 0x03002388
    shadow_one: .word 0x0300456E
    scroll_y_shadow: .word 0x030012B9
    initial_map: .word 0x0600F240
    map: .word 0x0600F000
    bg_zero: .word 0x03002338
    shadow_zero: .word 0x0300456C
    """, UPDATE, 36)


def display() -> tuple[bytes, int]:
    # The external IRQ callback is a required live-in. It is never fabricated
    # here, and no automatic caller is installed for this resident function.
    return assemble("""
        push {r0-r12, lr}
        mov r6, r0
        ldr r8, irq_enable
        ldrh r9, [r8]
        bic r9, r9, #4
        strh r9, [r8]
        mov r0, #0x21
        bl 0x08000FEC
        ldr r5, shadows
        ldrb r0, [r5]
        bl 0x08000F5C
        ldrb r0, [r5, #1]
        bl 0x08000F74
        ldrb r0, [r5, #2]
        bl 0x08000F2C
        ldrb r0, [r5, #3]
        bl 0x08000F44
        bl 0x08000CE8
        orr r0, r0, #7
        ldr r4, flags
        ldrh r8, [r4]
        tst r8, #0x800
        bicne r0, r0, #1
        bl 0x08000CFC
        ldrh r8, [r4]
        tst r8, #0x400
        bne transition
        ldr r8, callback_slot
        ldr r9, normal_irq
        str r9, [r8]
        ldr r8, thresholds_current
        ldrh r1, [r8]
        ldrh r3, [r8, #2]
        strh r3, [r8, #6]
        strh r1, [r8, #4]
        add r9, r1, #1
        strh r9, [r8, #4]
        lsl r1, r1, #1
        ldr r8, thresholds
        ldrh r0, [r8, r1]
        sub r0, r0, r3
        b schedule
    transition:
        ldr r8, callback_slot
        str r6, [r8]
        ldr r5, state
        mov r0, #0
        strh r0, [r5, #6]
        ldrh r0, [r5, #2]
        strh r0, [r5, #4]
        sub r1, r0, #1
        and r1, r1, #0xFF
        bic r0, r0, #0xFF
        orr r0, r0, r1
        strh r0, [r5, #2]
        cmp r1, #0
        bne schedule_low
        ldr r8, common_flags
        ldrh r9, [r8]
        bic r9, r9, #0x400
        strh r9, [r8]
        ldrh r9, [r4]
        orr r9, r9, #0x900
        strh r9, [r4]
    schedule_low:
        mov r0, r1
    schedule:
        add r0, r0, #8
        bl 0x08000C10
        bl 0x080C9000
        ldr r8, irq_enable
        ldrh r9, [r8]
        orr r9, r9, #4
        strh r9, [r8]
        pop {r0-r12, lr}
        bx lr
    shadows: .word 0x0300456C
    flags: .word 0x0300450A
    callback_slot: .word 0x030012E0
    normal_irq: .word 0x085E7800
    thresholds_current: .word 0x03004D44
    thresholds: .word 0x08586A00
    state: .word 0x03004710
    common_flags: .word 0x03004506
    irq_enable: .word 0x04000200
    """, DISPLAY, 36)


def normal_irq() -> tuple[bytes, int]:
    return assemble("""
        push {r0-r12, lr}
        ldr r4, saved
        ldrh r1, [r4]
        add r8, r1, #1
        strh r8, [r4]
        mov r2, r1
        cmp r2, #16
        rsbhs r2, r2, #31
        lsl r2, r2, #4
        and r2, r2, #0xFF
        bl 0x08000CD8
        and r0, r0, #0xFF
        orr r0, r0, r2, lsl #8
        bl 0x08000CF8
        ldrh r3, [r4, #2]
        lsl r1, r1, #1
        ldr r8, thresholds
        ldrh r0, [r8, r1]
        sub r0, r0, r3
        add r0, r0, #8
        bl 0x08000C10
        pop {r0-r12, lr}
        bx lr
    saved: .word 0x03004D48
    thresholds: .word 0x08586A00
    """, NORMAL_IRQ, 8)


def branch(site: int, target: int, link: bool = False) -> bytes:
    delta = target - site - 8
    require(delta % 4 == 0 and -(1 << 25) <= delta < 1 << 25, "invalid ARM branch")
    return struct.pack("<I", (0xEB000000 if link else 0xEA000000) | ((delta >> 2) & 0xFFFFFF))


def inbound(data: bytes) -> dict:
    pointers, branches = [], []
    for site in range(0, len(data), 4):
        word = struct.unpack_from("<I", data, site)[0]
        if BASE + START <= word < BASE + END:
            pointers.append([site, word])
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            target = site + 8 + 4 * delta
            if START <= target < END:
                branches.append([site, target])
    return {"pointers": pointers, "branch_like_words": branches}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    for name in HASHES:
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()
    before = args.input.read_bytes()
    require(digest(before) == INPUT_SHA256, "unknown fixed corrected-asset predecessor")
    sources = {name: getattr(args, name).read_bytes() for name in HASHES}
    for name, value in HASHES.items():
        require(digest(sources[name]) == value, f"unknown original {name}")
    for name, a, b, value in SOURCE_GUARDS:
        require(digest(sources[name][a:b]) == value, f"source guard {name}:{a:X}")
    require(len(before) == 0x800000, "unexpected ROM size")
    require(before[START:END] == b"\xFF" * (END - START), "ownership is not FF")
    refs = inbound(before)
    require(not refs["pointers"] and not refs["branch_like_words"], "pre-existing inbound to ownership")
    require(before[0x586244:0x586248] == branch(0x586244, 0x173BC, True), "old source update call differs")
    plan = []
    code_report = []
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for label, raw, next_raw, function in (("main_0E0B", UPDATE, DISPLAY, update), ("display_0C3A_resident", DISPLAY, NORMAL_IRQ, display), ("normal_IRQ_0D42", NORMAL_IRQ, END, normal_irq)):
        blob, code_bytes = function()
        require(raw + len(blob) <= next_raw, "code interval overlap")
        instructions = list(decoder.disasm(blob[:code_bytes], BASE + raw))
        require(len(instructions) * 4 == code_bytes and all(i.size == 4 for i in instructions), "incomplete ARM decode")
        plan.append((raw, blob, label))
        code_report.append({"label": label, "raw": raw, "bytes": len(blob), "code_bytes": code_bytes,
                            "sha256": digest(blob), "instructions": len(instructions)})
    plan.append((0x586244, branch(0x586244, UPDATE, True), "stage_update_call"))
    allowed, writes = set(), []
    for raw, blob, label in plan:
        interval = set(range(raw, raw + len(blob)))
        require(not allowed & interval, "overlapping Expected Writes")
        allowed |= interval
        writes.append({"label": label, "raw": raw, "bytes": len(blob),
                       "before_sha256": digest(before[raw:raw + len(blob)]), "after_sha256": digest(blob)})
    after = bytearray(before)
    for raw, blob, _ in plan:
        after[raw:raw + len(blob)] = blob
    diff = {i for i, (x, y) in enumerate(zip(before, after, strict=True)) if x != y}
    require(diff and diff <= allowed, "unexplained final diff")
    report = {"schema": 1, "input_sha256": INPUT_SHA256, "output_sha256": digest(after),
              "expected_writes": writes, "code": code_report, "inbound": refs, "changed_bytes": len(diff),
              "source_guards": SOURCE_GUARDS, "entries": {"main_0E0B": BASE + UPDATE, "display_0C3A": BASE + DISPLAY, "normal_IRQ_0D42": BASE + NORMAL_IRQ},
              "state_owner": {"source": "0300:00EA", "native": 0x03004710, "bytes_used": 14},
              "live_out": "r0-r12, LR, SP preserved; CPSR clobbered",
              "display_live_in": "r0 must be a proved native 0D87 IRQ callback; no caller installed",
              "main_connected": True, "display_connected": False,
              "remaining_gate": ["source0DEC uses interrupted DI, not its locally assigned BX=EA"],
              "claim": "closed main update and resident display effects only; no complete terminal display, gameplay, emulator or save verification"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-stage-handshake] " + report["output_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
