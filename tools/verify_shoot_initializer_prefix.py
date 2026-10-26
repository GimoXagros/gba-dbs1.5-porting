#!/usr/bin/env python3
"""Independently verify the disconnected, source-ordered Shoot prefix.

Reads actual source and final ROM instructions; imports no builder or manifest.
The bounded register/effect proof abstracts the three already verified callees.
It is not CPU emulation, service execution, or evidence of a playable entry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16
from verify_shoot_graphics_initializer import decode_and_check, verify_sources
from verify_stage_priority_routing import run_exact

BASE, START, STOP = 0x08000000, 0x629700, 0x62975C
BEFORE = "389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1"
ORIGINALS = (
    "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
)
REGS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
SOURCE_SEQUENCE = (
    "push bp", "mov bp, sp", "add sp, -8", "push ax", "push cx", "push dx",
    "push bx", "push si", "push di", "push es", "push ds", "in al, 0xb2",
    "and al, 0xef", "out 0xb2, al", "xor ax, ax", "mov es, ax",
    "mov word ptr es:[0xffe0], 0xfff", "in ax, 0", "mov ah, 0xf0", "out 0, ax",
    "mov di, 0x1000", "mov es, di", "mov di, 0x4e",
    "mov byte ptr es:[di + 0xe], 0xb", "lcall 0x7ccf, 0xfc4",
    "mov ax, 0x1000", "mov ds, ax", "mov word ptr [0x3ce], 0x4650",
    "mov word ptr [0x3d4], 0", "mov word ptr [0x3d6], 0",
    "mov word ptr [0x3d8], 0", "or word ptr [0x3d4], 0x10",
    "lcall 0x4090, 0x36c0", "mov ax, 0xc00", "mov dx, 0x1000",
    "mov ds, ax", "mov es, dx",
)
DEPENDENCIES = (
    (0x5C6800, 0x5C7800, "523710887E9E7DE9F34EF6E52BA466699839AD190A800E0B0D1819654D4E3265"),
    (0x5C4300, 0x5C4354, "715D48A742EC4B7046E8822615D2E5A2599A7627FFCEFDC04587D338C72A272D"),
    (0x36D224, 0x36D38C, "489A5436AB9158296B933F1DE55CD7CDE5BD198C979C866FA17933151B4A8C86"),
    (0x629500, 0x629518, "7A42F8C8D7AA3EDFDB669182B498F1EC0A6091BCECA491B2BAD4CF55ECD2F94A"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def target(at, encoded):
    displacement = encoded & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    return BASE + at + 8 + 4 * displacement


def listing(data, start, end, arch=CS_ARCH_ARM, mode=CS_MODE_ARM, base=BASE):
    rows = list(Cs(arch, mode).disasm(data[start:end], base + start))
    need(sum(i.size for i in rows) == end - start, "complete instruction boundaries")
    return [f"{i.mnemonic} {i.op_str}" for i in rows]


def source_trace(gba, old, source):
    need(tuple(listing(source, 0x747A68, 0x747AD1, CS_ARCH_X86, CS_MODE_16, -0x740900)) == SOURCE_SEQUENCE,
         "complete actual source prefix, segment contexts, widths and order")
    # Check the commercial bridge, then derive 18000/75*60 from actual consumers.
    relocated = source[0x740C73:0x740CB3]
    for current, previous in ((0x3CE, 0x354), (0x3D0, 0x356), (0x3D2, 0x358), (0x3D4, 0x35A), (0x3D6, 0x35C)):
        relocated = relocated.replace(struct.pack("<H", current), struct.pack("<H", previous))
    need(relocated == old[0x390A33:0x390A73], "complete commercial timer producer lineage")
    need(old[0x39FEAC:0x39FEB2] == bytes.fromhex("a15403b94b00") and
         source[0x7875AC:0x7875B2] == bytes.fromhex("a1ce03b94b00"), "both source HUD timer units")
    need(listing(gba, 0x373D34, 0x373D4C) == ["ldr r8, [pc, #0x68]", "ldrh r0, [r8]",
         "mov r1, #0x3c", "bl #0x837db3c", "mov r1, #0x3c", "bl #0x837db3c"] and
         word(gba, 0x373DA4) == 0x03004500, "native HUD units and timer owner")
    need(listing(gba, 0x37500C, 0x37501C) == ["ldr r8, [pc, #0x15c]", "ldrh sb, [r8]",
         "subs sb, sb, #1", "strh sb, [r8]"] and word(gba, 0x375170) == 0x03004500,
         "native timer decrement owner and width")
    need(struct.unpack_from("<3I", gba, 0xD1894) == (5400, 7200, 10800) and
         listing(gba, 0xD183C, 0xD1848) == ["ldr r8, [pc, #0x64]", "mov sb, #0x3840", "strh sb, [r8]"] and
         word(gba, 0xD18A8) == 0x03004500, "commercial native timer producer")
    ticks = struct.unpack_from("<H", source, 0x747AA8)[0]
    divisor = struct.unpack_from("<H", source, 0x7875B0)[0]
    native_ticks, remainder = divmod(ticks * 60, divisor)
    need(remainder == 0 and native_ticks == 14400, "consumer-derived timer conversion")
    need(sha(source[0x743FC0:0x7440C7]) ==
         "A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6", "actual source stage manager")
    return [
        ("call", 0x085C7200),
        ("write", 0x0300231E, 1, source[0x747A99]),
        ("call", 0x085C6800),
        ("write", 0x03004500, 2, native_ticks),
        ("write", 0x03004506, 2, struct.unpack_from("<H", source, 0x747AAE)[0]),
        ("write", 0x03004508, 2, struct.unpack_from("<H", source, 0x747AB4)[0]),
        ("write", 0x0300450A, 2, struct.unpack_from("<H", source, 0x747ABA)[0]),
        ("write", 0x03004506, 2, struct.unpack_from("<H", source, 0x747AC0)[0]),
        ("call", 0x0836D224),
    ]


def code_contract(after, trace):
    stage, ticks, flag = trace[1][3], trace[3][3], trace[7][3]
    expected = ["push " + REGS, "mov fp, #0", "bl #0x85c7200", "ldr r8, [pc, #0x3c]",
                f"mov sb, #{stage:#x}", "strb sb, [r8]", "bl #0x85c6800", "ldr r8, [pc, #0x30]",
                f"mov sb, #{ticks:#x}", "strh sb, [r8]", "ldr r8, [pc, #0x28]", "mov sb, #0",
                "strh sb, [r8]", "strh sb, [r8, #2]", "strh sb, [r8, #4]",
                f"mov sb, #{flag:#x}", "strh sb, [r8]", "bl #0x836d224", "pop " + REGS, "bx lr"]
    need(listing(after, START, START + 80) == expected, "all 20 final instruction semantics and source order")
    need(struct.unpack_from("<3I", after, START + 80) == (0x0300231E, 0x03004500, 0x03004506),
         "three exact source-domain owner literals")
    for offset, literal in ((0x0C, 0x50), (0x1C, 0x54), (0x28, 0x58)):
        need(START + offset + 8 + (word(after, START + offset) & 0xFFF) == START + literal,
             "every load uses its own bounded aligned literal")


def core(before, after, gba, old, source):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB image extent")
    need(before[START:STOP] == b"\xff" * (STOP - START), "unoccupied exact new-code range")
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer is still absent")
    for start, stop, expected in DEPENDENCIES:
        need(sha(before[start:stop]) == expected, f"retained dependency {start:06X}")
    trace = source_trace(gba, old, source)
    code_contract(after, trace)
    restored = bytearray(after)
    restored[START:STOP] = before[START:STOP]
    need(restored == before, "full inverse: no external route, data, dependency or adjacent byte changed")
    return trace


def abi_effects(after, expected):
    """Bounded evaluation of the reviewed 20 instructions and callee contracts."""
    cases = 0
    for flag_bits in range(16):
        for initial_sp in (0x03007EFC, 0x03007F00):
            for initial_r11 in (0, 1, 0x80000000, 0xFFFFFFFF):
                regs = [(0xA1000000 + 0x10101 * n) & 0xFFFFFFFF for n in range(15)]
                regs[11], regs[13], regs[14] = initial_r11, initial_sp, 0x0833FD1C
                initial, saved, effects = tuple(regs), {}, []
                for at in range(START, START + 80, 4):
                    encoded = word(after, at)
                    if encoded == 0xE92D5FFF:
                        regs[13] -= 56
                        for slot, register in enumerate((*range(13), 14)):
                            saved[regs[13] + 4 * slot] = regs[register]
                    elif encoded == 0xE8BD5FFF:
                        for slot, register in enumerate((*range(13), 14)):
                            regs[register] = saved[regs[13] + 4 * slot]
                        regs[13] += 56
                    elif encoded == 0xE12FFF1E:
                        need(tuple(regs) == initial, "all r0-r12, LR and SP restored for arbitrary caller r11")
                    elif encoded & 0xFFFF0000 == 0xE3A00000:
                        value, rotate = encoded & 255, ((encoded >> 8) & 15) * 2
                        regs[(encoded >> 12) & 15] = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF if rotate else value
                    elif encoded & 0xFFFF0000 == 0xE59F0000:
                        regs[(encoded >> 12) & 15] = word(after, at + 8 + (encoded & 0xFFF))
                    elif encoded & 0xFF000000 == 0xEB000000:
                        destination = target(at, encoded)
                        need(regs[11] == 0 and regs[13] == initial_sp - 56, "zero-r11 call ABI and balanced saved frame")
                        effects.append(("call", destination))
                        regs[14] = BASE + at + 4
                        if destination == 0x0836D224:
                            # The manager may clobber every work register; the outer frame owns preservation.
                            regs[:13] = [0xB0000000 + flag_bits * 256 + n for n in range(13)]
                        else:
                            need(destination in (0x085C7200, 0x085C6800), "only two register-preserving graphics services")
                    elif encoded == 0xE5C89000:
                        effects.append(("write", regs[8], 1, regs[9] & 255))
                    elif encoded in (0xE1C890B0, 0xE1C890B2, 0xE1C890B4):
                        effects.append(("write", regs[8] + (encoded & 15), 2, regs[9] & 65535))
                    else:
                        raise ValueError(f"instruction outside bounded proof {at:06X}/{encoded:08X}")
                need(effects == expected, "actual final instruction effects equal actual source order")
                cases += 1
    return dict(cases=cases, incoming_NZCV_states=16, stack_bytes=56, balanced=True,
                registers_preserved="r0-r12,LR,SP", flags="clobbered; no incoming flag dependence",
                callee_contracts=["preamble and graphics preserve r0-r12/SP", "manager may clobber r0-r12; SP balanced"],
                ordered_effects=expected)


def scan(data, origin=0):
    """Conservative all-alignment mirrored pointers and ARM/Thumb references."""
    hits = []
    def inside(value):
        return any(base + START <= value < base + STOP for base in (BASE, 0x0A000000, 0x0C000000))
    for shift in range(4):
        end = len(data) - ((len(data) - shift) % 4)
        for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[shift:end])):
            if inside(encoded):
                hits.append(("pointer", origin + shift + 4 * n, encoded))
    for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at, pc = origin + n * 4, BASE + origin + n * 4 + 8
        if encoded & 0x0E000000 == 0x0A000000 and inside(target(at, encoded)):
            hits.append(("ARM branch", at, target(at, encoded)))
        if encoded & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            dst = pc + (encoded & 0xFFF) * (1 if encoded & 0x800000 else -1)
            if inside(dst): hits.append(("ARM literal", at, dst))
        if encoded & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            immediate, rotate = encoded & 255, ((encoded >> 8) & 15) * 2
            if rotate: immediate = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF
            dst = pc + (immediate if encoded & 0x01E00000 == 0x00800000 else -immediate)
            if inside(dst): hits.append(("ARM ADR", at, dst))
    for n, (encoded,) in enumerate(struct.iter_unpack("<H", data[:len(data) // 2 * 2])):
        at, pc = origin + n * 2, BASE + origin + n * 2 + 4
        if encoded & 0xF800 in (0x4800, 0xA000):
            dst = (pc & ~3) + (encoded & 255) * 4
            if inside(dst): hits.append(("Thumb literal/ADR", at, dst))
        if encoded & 0xF800 == 0xE000:
            immediate = encoded & 0x7FF
            dst = pc + 2 * (immediate - (0x800 if immediate & 0x400 else 0))
            if inside(dst): hits.append(("Thumb B", at, dst))
        if encoded & 0xF000 == 0xD000 and encoded & 0x0F00 < 0x0E00:
            immediate = encoded & 255
            dst = pc + 2 * (immediate - (256 if immediate & 128 else 0))
            if inside(dst): hits.append(("Thumb conditional B", at, dst))
        if encoded & 0xF800 == 0xF000 and n * 2 + 4 <= len(data):
            tail = struct.unpack_from("<H", data, n * 2 + 2)[0]
            if tail & 0xF800 in (0xF800, 0xE800):
                immediate = encoded & 0x7FF
                dst = pc + ((immediate - (0x800 if immediate & 0x400 else 0)) << 12) + ((tail & 0x7FF) << 1)
                if tail & 0xF800 == 0xE800: dst &= ~3
                if inside(dst): hits.append(("Thumb BL/BLX", at, dst))
    return hits


def negatives(blobs):
    rejected = []
    sites = {"after": [*range(START, STOP), START - 1, STOP, 0x5C4300, 0x5C7800, 0x36D28C, 0x629500],
             "before": [START, 0x5C7800, *(a for a, _, _ in DEPENDENCIES)],
             "source": [0x747A99, 0x747A9B, 0x747AA8, 0x747AAE, 0x747AB4, 0x747ABA, 0x747AC0, 0x747AC3, 0x747AC8, 0x7875B0],
             "gba": [0x373D3D, 0x373DA4, 0x375170, 0xD1840, 0xD18A8], "old": [0x390A33, 0x39FEB0]}
    for name, positions in sites.items():
        for at in positions:
            changed = bytearray(blobs[name]); changed[at] ^= 1
            wrong = dict(blobs, **{name: changed})
            try:
                core(*(wrong[n] for n in ("before", "after", "gba", "old", "source")))
            except ValueError as error:
                rejected.append(dict(image=name, offset=f"{at:06X}", reason=str(error)))
            else:
                raise ValueError(f"accepted mutation {name}:{at:06X}")
    # Preserve final flag values while changing the observable write order.
    wrong = bytearray(blobs["after"])
    wrong[START + 0x30:START + 0x34], wrong[START + 0x38:START + 0x3C] = wrong[START + 0x38:START + 0x3C], wrong[START + 0x30:START + 0x34]
    try:
        core(blobs["before"], wrong, blobs["gba"], blobs["old"], blobs["source"])
    except ValueError as error:
        rejected.append(dict(image="after", kind="same-final-state-reordered-clears", reason=str(error)))
    else:
        raise ValueError("accepted equal-final-state source-order corruption")
    scanner_cases = 0
    for mirror in (BASE, 0x0A000000, 0x0C000000):
        for interior in (0, 1, 80, 91):
            for alignment in range(4):
                sample = bytearray(b"\xff" * 64)
                struct.pack_into("<I", sample, alignment, mirror + START + interior)
                need(any(hit[0] == "pointer" for hit in scan(sample)), "mirrored/interior/unaligned scanner control")
                scanner_cases += 1
    for encoded in (0xEA00003E, 0xEB00003E, 0xE59F80F8, 0xE28F00F8):
        need(scan(struct.pack("<I", encoded) + b"\xff" * 60, START - 0x100), "ARM scanner control")
        scanner_cases += 1
    for encoded in (0x483F, 0xA03F, 0xE07E, 0xD07E):
        need(scan(struct.pack("<H", encoded) + b"\xff" * 62, START - 0x100), "Thumb scanner control")
        scanner_cases += 1
    need(scan(struct.pack("<HH", 0xF000, 0xF87E) + b"\xff" * 60, START - 0x100), "Thumb BL scanner control")
    return rejected, scanner_cases + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    names = ("before", "after", "gba", "old", "source")
    need(all(getattr(args, n).suffix.lower() == ".gba" for n in names[:3]) and
         all(getattr(args, n).suffix.lower() == ".wsc" for n in names[3:]), "ROM-only extensions before reading")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in
         {getattr(args, n).resolve() for n in names}, "distinct JSON output before reading")
    blobs = {name: getattr(args, name).read_bytes() for name in names}
    need(tuple(sha(blobs[n]) for n in ("before", "gba", "old", "source")) == (BEFORE, *ORIGINALS),
         "exact port predecessor and three immutable originals")
    trace = core(*(blobs[n] for n in names))
    abi = abi_effects(blobs["after"], trace)
    graphics = decode_and_check(blobs["before"])
    graphics_source = verify_sources(dict(gba=blobs["gba"], wsc10=blobs["old"], wsc15=blobs["source"]), blobs["before"])
    for character in range(256):
        result, _, reads, _ = run_exact(blobs["before"], 0x629500, character, 11)
        need(result == 11 and reads == (0x0300231E,), "manager actual-stage11 priority for every character byte")
    need(not scan(blobs["before"]), "no preexisting references into any new byte")
    expected_refs = [("ARM literal", START + offset, BASE + START + literal)
                     for offset, literal in ((0x0C, 0x50), (0x1C, 0x54), (0x28, 0x58))]
    need(scan(blobs["after"]) == expected_refs, "only the prefix's three local literal references; no external caller")
    negative, scanner_cases = negatives(blobs)
    report = dict(schema=1, status="PASS", kind="independent-shoot-initializer-prefix-verification",
                  input_sha256=sha(blobs["before"]), output_sha256=sha(blobs["after"]),
                  original_sha256=list(ORIGINALS), source_range=["4090:7168", "4090:71D1"],
                  source_raw_half_open=["747A68", "747AD1"],
                  source_prefix_sha256=sha(blobs["source"][0x747A68:0x747AD1]),
                  writes=[[f"{START:06X}", f"{STOP:06X}"]], declared_bytes=92,
                  changed_bytes=sum(a != b for a, b in zip(blobs["before"], blobs["after"])),
                  full_inverse=True, external_callers_added=0, full_initializer_absent=True,
                  instructions=20, source_instructions=len(SOURCE_SEQUENCE), literal_words=3,
                  ABI_and_order=abi, graphics_dependency=graphics, graphics_source_dependency=graphics_source,
                  stage_priority_cases=256, allocation=dict(all_alignments=True, mirrors=["08", "0A", "0C"],
                  arm_thumb_references=True, own_literal_references=expected_refs, external_references=[]),
                  negative_controls=negative, scanner_negative_controls=scanner_cases,
                  negative_control_count=len(negative) + scanner_cases,
                  limits=["Disconnected prefix only; full scene/player lifetime and external entry remain absent.",
                          "No result-language layer is required; existing options/title content is inherited unchanged.",
                          "SRAM 1000:3CD8/3CDA, terminal DI, camera lifetime and full controller gates remain unresolved.",
                          "Bounded instruction effects under existing callee contracts; no emulator, save, hardware timing or gameplay claim."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
                         report_sha256=sha(args.output.read_bytes()), negative_controls=report["negative_control_count"],
                         changed_bytes=report["changed_bytes"])))


if __name__ == "__main__":
    main()
