#!/usr/bin/env python3
"""Independently verify the static four-callback opening integration.

The check compares the exact v34 base with the candidate, limits every changed
byte to the declared hooks/expansion ranges, and disassembles the ARM callbacks
to verify their native call graph.  It intentionally makes no runtime claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import (  # type: ignore
    CS_ARCH_ARM,
    CS_MODE_ARM,
    CS_MODE_LITTLE_ENDIAN,
    CS_OP_IMM,
    Cs,
)


GBA_BASE = 0x08000000
BASE_SHA256 = "33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1"
CANDIDATE_SHA256 = "9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"

TASK_SET_CALLBACK = 0x08012008
TASK_STATE = 0x0801201C
TASK_FRAME = 0x08013DD4
DISPLAY_EVENT = 0x08012874
DISPLAY_MOTION = 0x08012A84
DISPLAY_UPDATE = 0x08012C28
PALETTE_SETUP = 0x080881F0
RETAIL_SUCCESSOR = 0x08085454

CALLBACKS = {
    7: {
        "offset": 0x5B6000,
        "size": 508,
        "sha256": "6B72BBF0E893561878FE59F42BC6EF6B9AE9B0E63FECB7EE787E07CE3BBEE933",
        "successor": 0x085B6800,
        "selector": 14,
        "call_counts": {
            TASK_FRAME: 1,
            DISPLAY_EVENT: 4,
            DISPLAY_MOTION: 1,
            DISPLAY_UPDATE: 1,
            0x085B8300: 1,
            TASK_SET_CALLBACK: 1,
            0x085B8100: 1,
            PALETTE_SETUP: 1,
            0x085B8400: 1,
        },
    },
    8: {
        "offset": 0x5B6800,
        "size": 308,
        "sha256": "61D6DD24273A8E3805FD34ABEA619085B79D5356AA13B5F258FE87D7455418DE",
        "successor": 0x085B7000,
        "selector": 8,
        "call_counts": {
            TASK_FRAME: 1,
            DISPLAY_EVENT: 1,
            0x085B8300: 1,
            TASK_SET_CALLBACK: 1,
            0x085B8100: 1,
            PALETTE_SETUP: 1,
            0x085B8400: 1,
        },
    },
    9: {
        "offset": 0x5B7000,
        "size": 400,
        "sha256": "D49E74A8E511C26235881F1939CDD51FEAFEC0F54A9159D79BC25C6D5408F572",
        "successor": 0x085B7800,
        "selector": 9,
        "call_counts": {
            TASK_FRAME: 1,
            DISPLAY_EVENT: 2,
            0x085B8300: 1,
            TASK_STATE: 1,
            TASK_SET_CALLBACK: 1,
            0x085B8100: 1,
            0x085B8200: 1,
            PALETTE_SETUP: 1,
            0x085B8400: 1,
        },
    },
    10: {
        "offset": 0x5B7800,
        "size": 484,
        "sha256": "32AC7C128DE19F9F8E99BF7D7040E8D12BF6D038CB03F6C7014963E90987795D",
        "successor": RETAIL_SUCCESSOR,
        "selector": 3,
        "call_counts": {
            TASK_FRAME: 1,
            TASK_STATE: 2,
            DISPLAY_EVENT: 1,
            0x085B8300: 2,
            TASK_SET_CALLBACK: 1,
            0x085B8100: 1,
            PALETTE_SETUP: 1,
            0x085B8400: 1,
        },
    },
}

PLACEMENTS = {
    "callback_7": (0x5B6000, 508, CALLBACKS[7]["sha256"]),
    "callback_8": (0x5B6800, 308, CALLBACKS[8]["sha256"]),
    "callback_9": (0x5B7000, 400, CALLBACKS[9]["sha256"]),
    "callback_10": (0x5B7800, 484, CALLBACKS[10]["sha256"]),
    "successor_hook": (0x5B8000, 16, "6679E064B4726CD1DADFE1DA150E76755FBCBD70A6226087C2386E56B3C4A299"),
    "auxiliary_hook": (0x5B8040, 20, "197FB1080B7C8EAA8C6965B3D4BFE69DCCBB895E2819F353058A8EF7DF2E3762"),
    "primary_constructor": (0x5B8100, 112, "8AEDFAAB6A90BC51791219CF5B4DEA0E96F8686024670F4B16557B8CA44C5A2C"),
    "auxiliary_constructor": (0x5B8200, 104, "0EE5309DD43341B943A1E703355653F8C25CB2CC03AF67AC5A4AD17ED2A1AE65"),
    "object_update": (0x5B8300, 56, "CC7AD97119970AEAA0A62E234C04F41AC7C0B80FD750F2E0CB3E3BCAB3CC0BDF"),
    "skip_adapter": (0x5B8400, 164, "971103B5BA9AD7CB75AA4ABD9979CBC52EC74655F9A088B03BD8BFE238022F3B"),
    "event_table": (0x5B8500, 28, "50FA93DF7778AEC44B0DAF6F47B0C1EB4F4FD5718A5364904F9D31CBB5C21C52"),
}

HOOK_WORDS = {
    0x08516C: 0xEA14CBA3,
    0x0851CC: 0xE3A0800D,
    0x0851E8: 0xEA14CB94,
}

WSC_RANGES = {
    "callback_7": (0x7077, 0x7407, "C3AC134789C3DE1983E8964696851CDEC636F3F95722DD8CF24F0ADD4346554F"),
    "callback_8": (0x7407, 0x7698, "4B1F3D651E981A3006E42C642CEFABCDFC5AE455F7B9BAB488FAA5493E8D3991"),
    "callback_9": (0x7698, 0x7992, "1A20D0D18BC4AB2E9C1ECDBF57D1BC4D2C959C79A7DF1445B7AC4E101A3DCAD7"),
    "callback_10": (0x7992, 0x7D28, "FB46FFCD4F9BD7D50ADDBFE824AD1A70E5295054902C22C0720421B8D3EE542E"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def disassemble(blob: bytes, address: int):
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    engine.detail = True
    return tuple(engine.disasm(blob, address))


def branch_calls(instructions) -> dict[int, int]:
    calls: dict[int, int] = {}
    for insn in instructions:
        if insn.mnemonic == "bl" and insn.operands and insn.operands[0].type == CS_OP_IMM:
            target = insn.operands[0].imm
            calls[target] = calls.get(target, 0) + 1
    return calls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=pathlib.Path)
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    base = args.base.read_bytes()
    candidate = args.candidate.read_bytes()
    wsc = args.wsc15.read_bytes()
    if sha256(base) != BASE_SHA256:
        raise SystemExit("refusing unknown v34 base")
    if sha256(candidate) != CANDIDATE_SHA256:
        raise SystemExit("refusing unknown linear-opening candidate")
    if sha256(wsc) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    if len(base) != len(candidate):
        raise SystemExit("candidate size changed")

    allowed = bytearray(len(base))
    for offset, size, _ in PLACEMENTS.values():
        allowed[offset:offset + size] = bytes([1]) * size
    for offset in HOOK_WORDS:
        allowed[offset:offset + 4] = bytes([1]) * 4
    outside_changes = [
        offset for offset, (old, new) in enumerate(zip(base, candidate))
        if old != new and not allowed[offset]
    ]
    if outside_changes:
        raise SystemExit(f"change escaped declared integration ranges at 0x{outside_changes[0]:X}")

    placement_results = {}
    for label, (offset, size, expected) in PLACEMENTS.items():
        digest = sha256(candidate[offset:offset + size])
        if digest != expected:
            raise SystemExit(f"placement changed: {label}")
        placement_results[label] = {"offset": offset, "bytes": size, "sha256": digest}

    for offset, expected in HOOK_WORDS.items():
        actual = struct.unpack_from("<I", candidate, offset)[0]
        if actual != expected:
            raise SystemExit(f"hook word changed at 0x{offset:X}")

    callback_results = {}
    for number, spec in CALLBACKS.items():
        offset = spec["offset"]
        size = spec["size"]
        blob = candidate[offset:offset + size]
        instructions = disassemble(blob, GBA_BASE + offset)
        calls = branch_calls(instructions)
        for target, expected_count in spec["call_counts"].items():
            if calls.get(target, 0) != expected_count:
                raise SystemExit(
                    f"callback {number} call count changed for 0x{target:08X}: "
                    f"{calls.get(target, 0)} != {expected_count}"
                )
        if set(calls) != set(spec["call_counts"]):
            raise SystemExit(f"callback {number} has an undeclared call target")
        if struct.pack("<I", spec["successor"]) not in blob:
            raise SystemExit(f"callback {number} successor literal changed")
        selector_pattern = struct.pack("<I", 0xE3A00000 | spec["selector"])
        if selector_pattern not in blob:
            raise SystemExit(f"callback {number} selector construction changed")
        callback_results[str(number)] = {
            "offset": offset,
            "bytes": size,
            "successor": spec["successor"],
            "selector": spec["selector"],
            "call_counts": {f"0x{target:08X}": count for target, count in sorted(calls.items())},
        }

    callback_8 = candidate[0x5B6800:0x5B6800 + 308]
    callback_9 = candidate[0x5B7000:0x5B7000 + 400]
    event_1e = struct.pack("<I", 0xE3A0801E)
    if event_1e in callback_8 or callback_9.count(event_1e) != 1:
        raise SystemExit("event 0x1E is not isolated to callback 9")

    event_table = [
        list(struct.unpack_from("<HH", candidate, 0x5B8500 + index * 4))
        for index in range(7)
    ]
    expected_table = [[0x0B, 4], [0x0C, 7], [0x0D, 24], [0x0E, 19],
                      [0x23, 19], [0x24, 6], [0x25, 400]]
    if event_table != expected_table:
        raise SystemExit("callback-10 event table changed")

    bank = wsc[0x750000:0x760000]
    for label, (start, end, expected) in WSC_RANGES.items():
        if sha256(bank[start:end]) != expected:
            raise SystemExit(f"WSC source callback changed: {label}")

    changed_bytes = sum(old != new for old, new in zip(base, candidate))
    result = {
        "schema": 1,
        "kind": "opening-linear-integration-static-verification",
        "claim_scope": (
            "exact-source byte confinement and ARM callback graph verification only; "
            "runtime timing, visual, audio, transition, and skip behavior remain unverified"
        ),
        "sources": {
            "base_sha256": BASE_SHA256,
            "candidate_sha256": CANDIDATE_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "changed_bytes": changed_bytes,
        "hook_words": {f"0x{offset:06X}": f"0x{word:08X}" for offset, word in HOOK_WORDS.items()},
        "callbacks": callback_results,
        "callback_10_event_table": event_table,
        "placements": placement_results,
        "conclusion": "static integration graph and changed-byte boundary verified",
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
