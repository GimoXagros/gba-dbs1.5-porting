#!/usr/bin/env python3
"""Independently check resident palette code, consumers and finite color algebra.

This does not execute ARM instructions or a game. Instruction contracts bind
the mathematical checks to final placements. Scene ownership and scheduling
are preconditions, not consequences of a passing resident-code check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs

BASE = 0x08000000
BEFORE = "FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
REGS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"
WINDOWS = ((0x5C1900, 100, 96), (0x5C1C00, 220, 208),
           (0x5C1D00, 208, 208), (0x5C1F00, 276, 272), (0x5C2300, 32, 0))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def word(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def sequence(data: bytes, start: int, expected: list[str]) -> None:
    code = data[start:start + len(expected) * 4]
    actual = [f"{i.mnemonic} {i.op_str}" for i in
              Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(code, BASE + start)]
    if actual != expected:
        raise ValueError(f"instruction contract differs at {start:X}")


def copy_loop(register: str, target: int) -> list[str]:
    return ["ldrh r3, [r0], #2", f"strh r3, [{register}], #2",
            "subs r2, r2, #1", f"bne #0x{BASE + target:x}"]


def check_code(data: bytes) -> None:
    entry, leave = f"push {REGS}", f"pop {REGS}"
    sequence(data, 0x5C1900, [entry, "mov r0, #0x5000000",
        "ldr r1, [pc, #0x50]", "mov r2, #0x80"] + copy_loop("r1", 0x5C1910) + [
        "add r0, r0, #0x100", "add r1, r1, #0x100", "mov r2, #0x80"] +
        copy_loop("r1", 0x5C192C) + ["sub r0, r0, #0x200", "sub r1, r1, #0x100",
        "mov r2, #8", "ldrh r3, [r0], #0x20",
        "strh r3, [r1], #0x20", "subs r2, r2, #1",
        "bne #0x85c1948", leave, "bx lr"])
    sequence(data, 0x5C1C00, [entry, "mov r0, #0x5000000",
        "ldr r1, [pc, #0xc0]", "mov r2, #0x80"] + copy_loop("r1", 0x5C1C10) + [
        "add r0, r0, #0x120", "add r1, r1, #0x120", "mov r2, #0x30"] +
        copy_loop("r1", 0x5C1C2C) + ["add r0, r0, #0x20", "add r1, r1, #0x20",
        "mov r2, #0x10"] + copy_loop("r1", 0x5C1C48) + [
        "ldr r0, [pc, #0x74]", "ldr r1, [pc, #0x6c]", "mov r2, #8",
        "ldrh r3, [r0], #2", "strh r3, [r1], #0x20", "subs r2, r2, #1",
        "bne #0x85c1c64", "add r1, r1, #0x100", "mov r2, #8",
        "ldrh r3, [r0], #2", "strh r3, [r1], #0x20", "subs r2, r2, #1",
        "bne #0x85c1c7c", "mov r0, #0x5000000", "ldr r3, [pc, #0x40]",
        "mov r2, #0x80", "strh r3, [r0], #2", "subs r2, r2, #1",
        "bne #0x85c1c98", "add r4, r0, #0x100", "mov r2, #8",
        "strh r3, [r0], #0x20", "subs r2, r2, #1", "bne #0x85c1cac",
        "mov r2, #0x80", "strh r3, [r4], #2", "subs r2, r2, #1",
        "bne #0x85c1cbc", leave, "bx lr"])
    black = [entry, "cmp r0, #1", "blo #0x85c1dc8", "cmp r0, #0x20",
        "bhi #0x85c1dc8", "and r7, r0, #1", "mov r1, #0x5000000",
        "add r1, r1, r7, lsl #9", "mov r2, #0x80", "ldrh r3, [r1]", "mov r4, #0"]
    for shift in (0, 5, 10):
        black += [("mov r5, r3" if not shift else f"lsr r5, r3, #{hex(shift) if shift == 10 else shift}"),
            "and r5, r5, #0x1f", "cmp r5, #3", "movls r5, #0", "subhi r5, r5, #2",
            "orr r4, r4, r5" + (f", lsl #{shift}" if shift else "")]
    black += ["strh r4, [r1], #2", "subs r2, r2, #1", "bne #0x85c1d24",
        "cmp r7, #0", "beq #0x85c1da8", "sub r1, r1, #0x100", "sub r2, r1, #0x100",
        "mov r3, #8", "ldrh r4, [r1], #0x20", "strh r4, [r2], #0x20",
        "subs r3, r3, #1", "bne #0x85c1d94", "b #0x85c1dc8", "cmp r0, #4",
        "subhi r4, r0, #3", "movls r4, #0", "orr r4, r4, r4, lsl #5",
        "and r5, r4, #0x1f", "orr r4, r4, r5, lsl #10", "mov r1, #0x5000000",
        "strh r4, [r1]", leave, "bx lr"]
    sequence(data, 0x5C1D00, black)
    target = [entry, "cmp r0, #1", "blo #0x85c2008", "cmp r0, #0x20",
        "bhi #0x85c2008", "and r7, r0, #1", "mov r1, #0x5000000",
        "ldr sb, [pc, #0xec]", "add r1, r1, r7, lsl #9", "add sb, sb, r7, lsl #9",
        "mov r2, #0x80", "ldrh r3, [r1]", "ldrh r6, [sb], #2", "mov r4, #0"]
    for index, shift in enumerate((0, 5, 10)):
        distance = hex(shift) if shift == 10 else str(shift)
        target += [("mov r5, r3" if not shift else f"lsr r5, r3, #{distance}"),
            "and r5, r5, #0x1f", ("mov r8, r6" if not shift else f"lsr r8, r6, #{distance}"),
            "and r8, r8, #0x1f", "cmp r5, r8", f"beq #0x{0x085C1F64 + index * 0x30:x}",
            "cmp r5, #0", "moveq r5, #3", "addne r5, r5, #2", "cmp r5, r8",
            "movhi r5, r8", "orr r4, r4, r5" + (f", lsl #{shift}" if shift else "")]
    target += ["strh r4, [r1], #2", "subs r2, r2, #1", "bne #0x85c1f2c",
        "cmp r7, #0", "beq #0x85c1ffc", "sub r1, r1, #0x100", "sub r2, r1, #0x100",
        "mov r3, #8", "ldrh r4, [r1], #0x20", "strh r4, [r2], #0x20",
        "subs r3, r3, #1", "bne #0x85c1fe8", "b #0x85c2008",
        "mov r1, #0x5000000", "mov r4, #0", "strh r4, [r1]", leave, "bx lr"]
    sequence(data, 0x5C1F00, target)
    for site, value in ((0x5C1960, 0x0203E000), (0x5C1CD0, 0x0203E000),
                        (0x5C1CD4, 0x085C2300), (0x5C1CD8, 0x7FFF), (0x5C2010, 0x0203E000)):
        if word(data, site) != value:
            raise ValueError(f"palette literal differs at {site:X}")


def check_consumers(data: bytes, source: bytes) -> None:
    sequence(data, 0x1145C, ["and sl, r0, #0xff00", "mov r8, #0x5000000",
        "add sl, r8, sl, lsr #7", "ldrh sb, [sl]", "strh sb, [r8]"])
    # The five-word P2 ABI includes the high eight rows' OBJ split.
    sequence(data, 0x13308, ["ldrh r8, [r4], #4", "sub r8, r8, #8",
        "ldr r5, [sp, #0x10]", "add r5, r5, r8", "add r5, r5, #0x10",
        "lsl r5, r5, #5", "add r5, r5, #0x5000000", "add r5, r5, #2"])
    if digest(source[0x747DDA:0x747E34]) != "0415462B683CD87C9576DE4685A59D4F5BA6D3C201090C4D5B0A7A9F2FA40843":
        raise ValueError("source selective capture contract changed")
    if digest(source[0x751E8D:0x751F6B]) != "205C09848C45077D6D597B44B7224ABF74C9F7EB8E84179DAD8C5B3A2DA98D11":
        raise ValueError("source color arithmetic changed")
    for index, value in enumerate(struct.unpack_from("<16H", data, 0x5C2300)):
        channels = [(value >> shift) & 31 for shift in (0, 5, 10)]
        if value & 0x8000 or any(c not in (0, *range(3, 32, 2)) for c in channels):
            raise ValueError("gray color is outside the source color image")
        original = ((channels[0] // 2) << 8) | ((channels[1] // 2) << 4) | channels[2] // 2
        if original != struct.unpack_from("<H", source, 0x747E34 + index * 2)[0]:
            raise ValueError("native gray table fails independent inverse")


def check_algebra() -> dict:
    # Closed-form source values, not a CPU interpreter or an emulator.
    expand = lambda n: 0 if n == 0 else n * 2 + 1
    dec = lambda n: 0 if n <= 3 else n - 2
    inc = lambda n, target: n if n == target else min(target, 3 if n == 0 else n + 2)
    for target in range(32):
        color = 0
        for step in range(1, 17):
            color = inc(color, target)
            if color != min(target, step * 2 + 1):
                raise ValueError("native retained-color endpoint/cadence differs")
        if color != target:
            raise ValueError("native target lost a low bit")
    for source in range(16):
        color = expand(source)
        for step in range(1, 17):
            color = dec(color)
            if color != expand(max(0, source - step)):
                raise ValueError("source RGB444 decrement cadence differs")
        color = 0
        for step in range(1, 17):
            color = inc(color, expand(source))
            if color != expand(min(source, step)):
                raise ValueError("source RGB444 increment cadence differs")
    # Both halves receive exactly sixteen steps; aliases share their OBJ row.
    halves = [sum((remaining & 1) == parity for remaining in range(32, 0, -1)) for parity in (0, 1)]
    if halves != [16, 16]:
        raise ValueError("source half schedule differs")
    for remaining in range(32, 0, -2):
        canonical = remaining - 3 if remaining > 4 else 0
        if canonical != expand(max(0, 15 - (34 - remaining) // 2)):
            raise ValueError("canonical BG0 does not recover source white countdown")
    projection = set(range(0, 0x100, 2)) | set(range(0x200, 0x300, 2)) | set(range(0x100, 0x200, 0x20))
    capture = set(range(0, 0x100, 2)) | set(range(0x220, 0x280, 2)) | set(range(0x2A0, 0x2C0, 2))
    gray_zeros = set(range(0, 0x100, 0x20)) | set(range(0x200, 0x300, 0x20))
    retained = set(range(0x200, 0x300, 2)) - capture - gray_zeros
    if len(capture) * 2 != 384 or len(projection) * 2 != 528 or len(retained) != 60:
        raise ValueError("selected capture/retained row population differs")
    extra_bg = set(range(0x100, 0x200, 2)) - set(range(0x100, 0x200, 0x20))
    if extra_bg & (projection | capture | gray_zeros):
        raise ValueError("native-only high BG payload would be overwritten")
    return {"source_channel_cases": 16, "source_steps_each_direction": 16,
            "native_retained_channel_cases": 32, "native_restore_steps": 16,
            "source_halves": halves, "selective_bytes": 384, "projection_bytes": 528,
            "preserved_obj_nonzero_colors": 60, "preserved_high_bg_nonzero_colors": 120,
            "scope": "arithmetic and static instruction contracts only; source hold/audio and scene lifetime excluded"}


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15"):
        p.add_argument(name, type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path)
    args = p.parse_args()
    before, after, gba, source = (f.read_bytes() for f in (args.before, args.after, args.gba, args.wsc15))
    if digest(before) != BEFORE or digest(gba) != GBA or digest(source) != WSC or len(before) != 0x800000 or len(after) != len(before):
        raise ValueError("source identity or image size differs")
    check_code(after)
    check_consumers(after, source)
    arithmetic = check_algebra()
    allowed = {i for start, size, _ in WINDOWS for i in range(start, start + size)}
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if not changed or not changed <= allowed:
        raise ValueError("palette diff escapes Expected Writes")
    if any(before[start:start + size] != b"\xff" * size for start, size, _ in WINDOWS):
        raise ValueError("palette placement is not blank in its predecessor")
    inbound, gap_candidates = [], []
    for site in range(0, len(after), 4):
        value = word(after, site)
        target = value - BASE
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            displacement = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
            target = site + 8 + displacement * 4
        if target in allowed and site not in allowed:
            inbound.append(site)
        elif 0x5C1900 <= target < 0x5C2340 and site not in allowed:
            gap_candidates.append({"site": site, "target": target})
    if inbound:
        raise ValueError("palette helpers acquired a premature external caller")
    negatives = []
    for label, site, replacement, checker in (
        ("snapshot truncates OBJ", 0x5C1928, 0xE3A02040, check_code),
        ("full backup destroys retained rows", 0x5C1C28, 0xE3A02080, check_code),
        ("wrong selective row five", 0x5C1C3C, 0xE2800040, check_code),
        ("gray destroys native high BG payload", 0x5C1C68, 0xE0C130B2, check_code),
        ("incorrect white", 0x5C1CD8, 0x03FF, check_code),
        ("source half mistaken for native half", 0x5C1D1C, 0xE0811407, check_code),
        ("decrement leaves low-bit residue", 0x5C1D34, 0xE3550002, check_code),
        ("wrong green mask", 0x5C1F74, 0xE205801F, check_code),
        ("target clamp removed", 0x5C1F60, 0xE1A05005, check_code),
        ("backdrop alias repair removed", 0x5C2004, 0xE1A04004, check_code),
        ("use retail red table", 0x5C2304, 0x00000007, lambda d: check_consumers(d, source)),
    ):
        mutated = bytearray(after)
        struct.pack_into("<I", mutated, site, replacement)
        try:
            checker(mutated)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"semantic negative accepted: {label}")
    report = {"schema": 1, "kind": "shoot-palette-independent-static-verification",
              "input_sha256": digest(before), "output_sha256": digest(after),
              "actual_changed_bytes": len(changed), "instruction_count": sum(size // 4 for _, _, size in WINDOWS),
              "arithmetic": arithmetic, "negative_regressions_rejected": negatives,
              "external_callers": inbound,
              "unclassified_references_to_preserved_gaps": gap_candidates,
              "claim_scope": "resident code, source inverse, consumer mapping and finite arithmetic only; no complete initialization, scene-exclusive lifetime, hold/audio scheduling or runtime evidence"}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
