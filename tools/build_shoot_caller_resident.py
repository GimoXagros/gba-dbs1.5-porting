#!/usr/bin/env python3
"""Emit real synchronous Shoot callers without opening external entry gates.

The two functions have no incoming references in the exact predecessor. The
controller boundary, case-5 allocation, damage hooks and display router stay
unchanged. This is executable resident code, not a claim of gameplay closure.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from analyze_waterfall_third_pattern import no_inbound, need, sha
from build_shoot_controller_adapter import adapter, CONTRACTS

BASE = 0x08000000
INPUT = "A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ADAPTER, EXIT = 0x5C6500, 0x6FC300
EXIT_SOURCE = bytes.fromhex("1E57BF00108EDFBF4E0033C08A450E5F1F3D0B0075069A5017F071CB")
PINS = (*CONTRACTS,
        (0x5CD000, 160, "488AD379AB04A0CDD47883AEE8C5D87252E4235C98CBC6A23F423558CF5FBFE8"),
        (0x34059C, 600, "B0088F9E6A47A0CEC0B5D6F10473FDB75E9D2EAB573CC8BC51D647583C0D5116"))


def exit_router():
    source = """
        push {r0, r12, lr}
        mrs r12, cpsr
        ldr r0, stage
        ldrb r0, [r0]
        cmp r0, #11
        beq terminal
        msr cpsr_f, r12
        pop {r0, r12, lr}
        b 0x0834059C
    terminal:
        msr cpsr_f, r12
        pop {r0, r12, lr}
        b 0x085CD000
    stage: .word 0x0300231E
    """
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + EXIT)[0])


def shapes(controller, router):
    def decode(data, raw, count):
        return [i.mnemonic + " " + i.op_str for i in
                Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[:count], BASE + raw)]
    saved = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
    need(len(controller) == 44 and decode(controller, ADAPTER, 32) == [
        "push " + saved, "bl #0x85c6000", "ldr r1, [pc, #0x10]",
        "ldr r2, [pc, #0x10]", "ldr r3, [pc, #0x10]", "bl #0x85c6200",
        "pop " + saved, "bx lr"], "controller ABI and same-invocation call order")
    need(struct.unpack_from("<3I", controller, 32) ==
         (0x085CB000, 0x085CB970, 0x085CBD80), "all three real lower callbacks")
    need(len(router) == 52 and decode(router, EXIT, 48) == [
        "push {r0, ip, lr}", "mrs ip, apsr", "ldr r0, [pc, #0x20]",
        "ldrb r0, [r0]", "cmp r0, #0xb", "beq #0x86fc324",
        "msr apsr_nzcvq, ip", "pop {r0, ip, lr}", "b #0x834059c",
        "msr apsr_nzcvq, ip", "pop {r0, ip, lr}", "b #0x85cd000"],
         "exit stage-byte predicate, balanced frame, flags and tail continuations")
    need(struct.unpack_from("<I", router, 48)[0] == 0x0300231E, "actual stage owner")
    # Decoders can ignore reserved status-register bits; pin those encodings.
    need(struct.unpack_from("<I", router, 4)[0] == 0xE10FC000 and
         all(struct.unpack_from("<I", router, i)[0] == 0xE128F00C for i in (24, 36)),
         "ARM7 status-register encoding")


def proof(before, gba, wsc, controller, router):
    need(sha(before) == INPUT and sha(gba) == GBA and sha(wsc) == SOURCE,
         "exact v67 and original identities")
    need(wsc[0x772553:0x77256F] == EXIT_SOURCE, "source0653 stage11 branch to1750")
    ins = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(EXIT_SOURCE, 0x772553))
    need([(i.address, i.mnemonic, i.op_str) for i in ins[-4:]] == [
        (0x772564, "cmp", "ax, 0xb"), (0x772567, "jne", "0x77256f"),
        (0x772569, "lcall", "0x71f0, 0x1750"), (0x77256E, "retf", "")],
         "source branch/call/return boundaries")
    for at, size, digest in PINS:
        need(sha(before[at:at + size]) == digest, f"resident dependency {at:X}")
    need(before[0x34059C:0x3407F4] == gba[0x34059C:0x3407F4], "retained ordinary case5 callback")
    need(before[0x33FCCC:0x33FDC0] == gba[0x33FCCC:0x33FDC0], "actual native case5 allocation owner")
    need(before[0x5C0A00:0x5C0A04] == bytes.fromhex("1EFF2FE1"), "controller boundary remains closed")
    shapes(controller, router)
    # Exhaust the actual byte-valued stage producer, including noncanonical IDs.
    destinations = [0x085CD000 if stage == 11 else 0x0834059C for stage in range(256)]
    need(destinations.count(0x085CD000) == 1, "exact256-stage decision population")
    rejected = []
    for label, which, at, word in (
        ("wrong controller family", 0, 36, 0x085CBD80),
        ("missing SELECT", 0, 4, 0xE1A00000),
        ("lost r4 restore", 0, 24, 0xE8BD5FEF),
        ("halfword stage read", 1, 12, 0xE1D000B0),
        ("wrong stage", 1, 16, 0xE3500007),
        ("reversed stage branch", 1, 20, 0x1A000003),
        ("flags not restored", 1, 36, 0xE1A00000),
        ("wrong terminal destination", 1, 44, 0xEA000000),
        ("wrong stage owner", 1, 48, 0x0300231F)):
        parts = [bytearray(controller), bytearray(router)]
        struct.pack_into("<I", parts[which], at, word)
        try:
            shapes(*parts)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("accepted semantic mutation " + label)
    return {"source_exit_entry": "71F0:0653", "source_terminal_call": "772569 ->71F0:1750",
            "native_stage_owner": "0300231E", "stage_cases": 256,
            "adapter": "same current r4: SELECT, three literal loads, APPLY; r0-r12/LR/SP restored",
            "exit": "stage11 tail1750; all other stage bytes tail original0653; r0-r12/LR/SP and NZCV restored",
            "negative_controls": rejected}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "gba", "wsc15", "output"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists() and not args.manifest.exists(), "fresh output paths required")
    before, gba, wsc = (p.read_bytes() for p in (args.before, args.gba, args.wsc15))
    controller, router = adapter(), exit_router()
    checks = proof(before, gba, wsc, controller, router)
    placements = ((ADAPTER, controller), (EXIT, router))
    spans = [(at, at + len(blob)) for at, blob in placements]
    for at, blob in placements:
        need(before[at:at + len(blob)] == b"\xff" * len(blob), "actual emitted span must be FF")
    ownership = no_inbound(before, spans)
    result = bytearray(before)
    for at, blob in placements:
        result[at:at + len(blob)] = blob
    inverse = bytearray(result)
    for at, blob in placements:
        inverse[at:at + len(blob)] = before[at:at + len(blob)]
    need(inverse == before, "whole-ROM inverse")
    changed = sum(a != b for a, b in zip(before, result, strict=True))
    report = {"schema": 1, "kind": "shoot-caller-resident", "status": "PASS",
              "input_sha256": sha(before), "output_sha256": sha(result),
              "source_sha256": SOURCE, "gba_sha256": GBA,
              "placements": [{"offset": at, "bytes": len(blob), "sha256": sha(blob)} for at, blob in placements],
              "declared_bytes": sum(len(b) for _, b in placements), "changed_bytes": changed,
              "proof": checks, "ownership": ownership, "whole_ROM_inverse": True,
              "external_hooks_changed": False, "controller_boundary_changed": False,
              "future_route_default_callback": BASE + EXIT,
              "remaining": ["terminal197A live BX camera/destination lifetime",
                            "transition0DEC IRQ visibility and map/tile preservation",
                            "P1 captured Y and lower position/displacement lifetime"],
              "runtime_executed": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
    print("[shoot-caller-resident] PASS " + sha(result))


if __name__ == "__main__":
    main()
