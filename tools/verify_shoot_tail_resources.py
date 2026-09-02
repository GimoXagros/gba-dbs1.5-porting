#!/usr/bin/env python3
"""Check v50 against actual source/native consumers without builder imports."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from verify_shoot_far_tile_repair import inverse_pixels, far_source

BEFORE = "93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E"
AFTER = "C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
REGISTERS = "{r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def word(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def sequence(data: bytes, start: int, expected: list[str]) -> None:
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[start:start + len(expected) * 4], BASE + start))
    actual = [f"{i.mnemonic} {i.op_str}" for i in instructions]
    if actual != expected:
        raise ValueError(f"instruction/consumer mismatch at {start:X}")


def check_phases(data: bytes) -> None:
    push = "str r8, [sp, #-4]!"
    sequence(data, 0x5C1700, [
        f"push {REGISTERS}", "ldr r8, [pc, #0x2c]", push, "mov r8, #0",
        push, push, push, "mov r8, #5", push, "mov fp, #0",
        "bl #0x80132ec", "add sp, sp, #0x14", f"pop {REGISTERS}", "bx lr",
    ])
    sequence(data, 0x5C1800, [
        f"push {REGISTERS}", "ldr r0, [pc, #0x50]", "ldr r1, [pc, #0x50]",
        "mov r2, #0x20", "ldr r3, [r0], #4", "str r3, [r1], #4",
        "subs r2, r2, #1", "bne #0x85c1810", "ldr r8, [pc, #0x3c]",
        push, "mov r8, #0", push, push, push, push, "mov fp, #0",
        "bl #0x80132ec", "add sp, sp, #0x14", "ldr r0, [pc, #0x18]",
        "mov r1, #0", "strh r1, [r0]", f"pop {REGISTERS}", "bx lr",
    ])
    for site, value in ((0x5C1738, 0x085DB740), (0x5C185C, 0x080D2FD0),
                        (0x5C1860, 0x06017F80), (0x5C1864, 0x080D3078),
                        (0x5C1868, 0x03004D40)):
        if word(data, site) != value:
            raise ValueError(f"resource/destination literal differs at {site:X}")


def check_consumers(data: bytes, wsc: bytes) -> dict:
    # Prove the five-word native stack ABI, 34-byte P2 index stride, OBJ
    # address calculation and exactly fifteen color writes (zero untouched).
    sequence(data, 0x132EC, [
        "push {r2, r4, r5, lr}", "ldr r4, [sp, #0x20]", "add r4, r4, #4",
        "ldr r8, [sp, #0x14]", "lsl r2, r8, #5", "add r2, r2, r8, lsl #1",
        "add r4, r4, r2", "ldrh r8, [r4], #4", "sub r8, r8, #8",
        "ldr r5, [sp, #0x10]", "add r5, r5, r8", "add r5, r5, #0x10",
        "lsl r5, r5, #5", "add r5, r5, #0x5000000", "add r5, r5, #2",
    ] + [item for _ in range(15) for item in ("ldrh r8, [r4], #2", "strh r8, [r5], #2")]
      + ["pop {r2, r4, r5, lr}", "bx lr"])
    sequence(data, 0xD161C, ["ldr r8, [pc, #0x14c]", "ldr sb, [pc, #0x14c]"]
             + [item for _ in range(32) for item in ("ldr sl, [r8], #4", "str sl, [sb], #4")])
    if (word(data, 0xD1770), word(data, 0xD1774), word(data, 0x370268)) != (0x080D2FD0, 0x06017F80, 0x67FC):
        raise ValueError("retail producer/OAM literals differ")
    sequence(data, 0x370148, ["ldr sb, [pc, #0x118]", "strh sb, [ip, #4]"])
    # Native tile 3FC is exactly the commercial producer's 17F80 destination.
    if 0x06010000 + (word(data, 0x370268) & 0x3FF) * 32 != word(data, 0xD1774):
        raise ValueError("HUD OAM tile index misses the copied payload")
    desc = far_source(wsc, 0x3D7D32, 8)
    length = struct.unpack_from("<H", wsc, desc)[0]
    src = far_source(wsc, desc + 2, length)
    if length != 128 or inverse_pixels(data[0xD2FD0:0xD3050]) != wsc[src:src + length]:
        raise ValueError("commercial HUD pixels do not recover the entire source P0 payload")
    palettes = []
    legal = {0, *range(3, 32, 2)}
    for source, native, offset, dest in ((0x3D7A90, 0x5DB740, 5, 0x050002A2),
                                        (0x3D6B16, 0xD3078, 0, 0x050002C2)):
        header = struct.unpack_from("<3H", wsc, source)
        if header[:2] != (1, 1) or data[native:native + 6] != wsc[source:source + 6]:
            raise ValueError("P2 header/count/format/base mismatch")
        # Inverse conversion is independent of the builder's forward formula.
        for index, color in enumerate(struct.unpack_from("<16H", data, native + 6)):
            channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
            if color & 0x8000 or not set(channels) <= legal:
                raise ValueError("P2 color not in the source channel image")
            original = (channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2
            if original != struct.unpack_from("<H", wsc, source + 6 + index * 2)[0]:
                raise ValueError("P2 colors fail inverse source comparison")
        actual_dest = 0x05000000 + (header[2] - 8 + offset + 16) * 32 + 2
        if actual_dest != dest:
            raise ValueError("P2 slot does not address the declared OBJ palette")
        palettes.append({"source": source, "native": BASE + native,
                         "entry_sp": [offset, 0, 0, 0, BASE + native],
                         "destination": dest, "halfwords": 15, "zero_preserved": True})
    return {"hud_source_payload": src, "hud_bytes": length, "native_hud_source": 0x080D2FD0,
            "native_hud_destination": 0x06017F80, "native_hud_oam": 0x67FC,
            "palettes": palettes}


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    before, after, gba, wsc = (p.read_bytes() for p in (args.before, args.after, args.gba, args.wsc15))
    for data, expected in ((before, BEFORE), (gba, GBA), (wsc, WSC15)):
        if digest(data) != expected:
            raise ValueError("input identity mismatch")
    check_phases(after)
    consumers = check_consumers(after, wsc)
    if after[0xD2FD0:0xD30A0] != gba[0xD2FD0:0xD30A0]:
        raise ValueError("commercial reused data was altered")
    negatives = []
    for label, site, value, checker in (
        ("wrong early slot", 0x5C171C, 0xE3A08004, check_phases),
        ("wrong tile destination", 0x5C1860, 0x06014F80, check_phases),
        ("truncated tile copy", 0x5C180C, 0xE3A02010, check_phases),
        ("wrong tile loop stride", 0x5C1814, 0xE4813002, check_phases),
        ("wrong late P2 source", 0x5C1864, 0x085DB740, check_phases),
        ("wrong scroll clear", 0x5C1868, 0x03004D42, check_phases),
        ("wrong call stack cleanup", 0x5C1844, 0xE28DD010, check_phases),
        ("wrong late palette base", 0xD307C, 0x01A0000D, lambda d: check_consumers(d, wsc)),
        ("wrong retail HUD selection", 0x370268, 0x000067FB, lambda d: check_consumers(d, wsc)),
        ("retail loader copies color zero", 0x13324, 0xE1A05005, lambda d: check_consumers(d, wsc)),
    ):
        changed = bytearray(after)
        struct.pack_into("<I", changed, site, value)
        try:
            checker(changed)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"semantic negative accepted: {label}")
    if digest(after) != AFTER or len(after) != len(before) or len(after) != 0x800000:
        raise ValueError("final identity/size mismatch")
    windows = [(0x5C1700, 0x5C173C), (0x5C1800, 0x5C186C)]
    allowed = {i for a, b in windows for i in range(a, b)}
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if not changed or not changed <= allowed or any(before[a:b] != b"\xff" * (b-a) for a, b in windows):
        raise ValueError("diff escapes the two resident resource writes")
    refs = []
    for site in range(0, len(after), 4):
        value = word(after, site)
        target = value - BASE
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            d = value & 0xFFFFFF
            if d & 0x800000:
                d -= 0x1000000
            target = site + 8 + d * 4
        if 0x5C1700 <= target < 0x5C1900 and not 0x5C1700 <= site < 0x5C1900:
            refs.append(site)
    if refs:
        raise ValueError("incomplete initializer unexpectedly acquired an external caller")
    report = {"schema": 1, "kind": "shoot-tail-resource-consumer-verification",
              "input_sha256": BEFORE, "output_sha256": AFTER,
              "source_segments": [[0x7394, 0x73A9], [0x74A2, 0x74DA]],
              "native_instructions": 37, "literal_bytes": 20, "consumers": consumers,
              "negative_regressions_rejected": negatives, "actual_changed_bytes": len(changed),
              "external_callers": refs,
              "claim_scope": "whole native instruction populations, source pixel/palette inverses, real retail tile producer/OAM/P2 consumers and diff only; no runtime, palette-transition ownership, complete initializer or controller/menu proof"}
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
