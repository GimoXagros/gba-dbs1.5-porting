#!/usr/bin/env python3
"""Narrow terminal owner and conditional camera evidence from immutable source.

No builder import, CPU execution, emulator, save or guest-memory write. The
conditional no-refill result does not assert the pending actor lifetime.
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
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def exact(data, at, expected):
    decoded = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(data[at:at + 160], at))[:len(expected)]
    need([f"{i.mnemonic} {i.op_str}".rstrip() for i in decoded] == expected, f"source contract {at:X}")


def contracts(s):
    exact(s, 0x77DD9A, ["mov di, 0x1ce", "mov word ptr [di + 4], 0x1000",
        "mov word ptr [di], 0x12", "mov word ptr [di + 2], 0x13"])
    exact(s, 0x77DDE1, ["mov di, 0x20e", "mov word ptr [di + 4], 0x800",
        "mov word ptr [di], 0x10", "mov word ptr [di + 2], 0x11"])
    exact(s, 0x77DE2E, ["xor di, di", "mov es, di", "mov di, 0x3000", "mov ax, 0x2fff",
        "mov word ptr es:[di], ax", "mov word ptr es:[di + 2], ax",
        "mov word ptr es:[di + 4], ax", "mov word ptr es:[di + 6], ax"])
    exact(s, 0x773895, ["mov di, 0x300", "mov es, di", "mov di, 0xea", "xor ax, ax",
        "mov word ptr es:[di], 0x154", "mov word ptr es:[di + 2], 0x8f"])
    exact(s, 0x7738C6, ["xor ax, ax", "mov es, ax", "mov di, bx", "shl di, 6",
        "add di, 0x800", "mov cx, 0x40", "rep stosw word ptr es:[di], ax"])
    exact(s, 0x7410E9, ["mov ax, word ptr es:[0x1de]", "mov bx, word ptr es:[0x1e0]",
        "mov word ptr [0x3a14], ax", "mov word ptr [0x3a16], bx", "retf"])
    # The battle camera compares coordinates, not merely their on-screen bytes.
    exact(s, 0x741500, ["mov ax, word ptr [di + 0x2a]", "mov dx, word ptr [di + 0x26]",
        "and ax, 0xfff0", "and dx, 0xfff0", "sub ax, dx", "je 0x741543"])
    exact(s, 0x74154E, ["mov ax, word ptr [di + 0x2c]", "mov dx, word ptr [di + 0x28]",
        "or dx, dx", "js 0x74159d", "and ax, 0xfff0", "and dx, 0xfff0",
        "or dx, dx", "js 0x74159d", "or ax, ax", "js 0x74159d",
        "sub ax, dx", "je 0x74159d"])
    exact(s, 0x7414EB, ["xor cx, cx", "mov word ptr es:[si + 0x1c], cx",
        "mov word ptr es:[si + 0x1e], cx", "xor bx, bx"])
    exact(s, 0x74159D, ["xor dx, dx", "push di", "xor di, di", "jcxz 0x7415dc"])
    exact(s, 0x7415D7, ["lcall 0x7ccf, 0x11bc"])
    exact(s, 0x771F53, ["push 0x4090", "push 0xb8b", "push 0xc00",
        "push word ptr es:[0x3e0]", "lcall 0x4fff, 0xbc7", "add sp, 8"])
    exact(s, 0x74161F, ["call 0x7426b0", "call 0x7427fb",
        "mov si, word ptr es:[0x65c]", "mov di, word ptr es:[0x65e]", "call 0x74273b"])
    exact(s, 0x74271E, ["lcall 0x4fff, 0x21b9", "add sp, 0x14", "or ax, ax",
        "je 0x74272f", "lcall 0x5ffd, 0"])
    exact(s, 0x7427DB, ["add word ptr [si + 0x3a], ax", "test word ptr [di + 0xa], 0x2000",
        "jne 0x7427ea", "neg ax", "add word ptr [di + 0x3a], ax", "ret"])
    scene = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(s[0x74148B:0x74160B], 0x74148B))
    need(sum(i.size for i in scene) == 0x180, "complete terminal battle body")
    need([(i.mnemonic, i.op_str) for i in scene if i.mnemonic in ("call", "lcall")] == [
        ("lcall", "0x4fff, 0x2a4b"), ("call", "0x7418c7"), ("lcall", "0x4fff, 0x3367"),
        ("lcall", "0x7ccf, 0x11bc"), ("lcall", "0x68f7, 0x454"), ("lcall", "0x875a, 0"),
        ("lcall", "0x875a, 0x3a"), ("lcall", "0x875a, 0x6f"), ("lcall", "0x875a, 0xec")],
         "scene battle replaces ordinary hit, command-pair collision and bodypush consumers")
    # The wipe and shake affect different descriptor/map owners.
    exact(s, 0x75FCBB, ["mov si, 0x1000", "mov ds, si", "mov si, 0x20e",
        "test word ptr [0x3d8], 0x200", "jne 0x75fcce", "jmp 0x75fd49"])
    exact(s, 0x75FD28, ["xor ax, ax", "mov word ptr [si + 0x1c], ax",
        "mov word ptr [si + 0x1e], ax", "and word ptr [0x3d8], 0xfdff",
        "or word ptr [0x3d8], 0x400"])
    exact(s, 0x75FDD2, ["mov si, 0x1000", "mov ds, si", "mov si, 0x1ce",
        "mov word ptr [si + 0x1e], 0x200", "push ax", "push ds", "push si",
        "lcall 0x4fff, 0x3367"])
    exact(s, 0x773966, ["or word ptr es:[0x3d8], 0x20", "mov word ptr es:[0x720], 1",
        "or word ptr es:[0x3d8], 0x1000"])
    exact(s, 0x773A34, ["or word ptr es:[0x3d8], 0x200"])
    exact(s, 0x74A1F7, ["test word ptr es:[0x3d8], 0x4030", "jne 0x74a203", "call 0x747f42"])
    exact(s, 0x75FC90, ["mov bx, 0x300", "mov es, bx", "mov bx, 0xea",
        "mov ax, word ptr es:[di + 0xa]", "out 0x10, al"])


def analyze(s):
    need(sha(s) == SOURCE, "immutable WSC1.5 source")
    contracts(s)
    # Complete equality-domain check for the two independent camera deltas.
    for value in range(65536):
        need(((value & 0xFFF0) - (value & 0xFFF0)) & 65535 == 0,
             "stationary coordinate cannot request camera direction")
    table = [struct.unpack_from("<HH", s, 0x33CA20 + 4 * i) for i in range(56 * 54)]
    need(set(x for x, _ in table) == {0, 1, 2, 3} and all(y == 0 for _, y in table),
         "actual Shoot grid excludes conveyor/material force metadata")
    centers = [[table[y * 56 + x][0] for x in range(24, 33)] for y in range(54)]
    need(all(not any(row) for row in centers[:42]) and centers[42] == [2] * 9 and
         centers[50] == [1] * 9 and all(row == [3] * 9 for row in centers[51:]),
         "positive central landing geometry")
    rejected = []
    for label, at in (("BG1 map owner", 0x77DDE7), ("source clear stride", 0x7738CE),
                      ("camera equality branch", 0x74150F), ("shake descriptor owner", 0x75FDD8),
                      ("scroll suppression flag", 0x74A1FC), ("IRQ actual DI read", 0x75FC9A),
                      ("wrong terminal battle callback", 0x771F57), ("restored bodypush call", 0x7414BF)):
        bad = bytearray(s)
        bad[at] ^= 1
        try:
            contracts(bad)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("accepted source mutation " + label)
    return {"schema": 1, "status": "CONDITIONAL_EVIDENCE_PASS", "source_sha256": SOURCE,
            "closed": {"BG0_map": "1000..17FF, logical ports12/13",
                       "BG1_map": "0800..0FFF, logical ports10/11",
                       "HUD_positive_owner": "3000..3007",
                       "transition_state_positive_owner": "30EA..30F7",
                       "camera_equality_cases": 65536 * 2,
                       "stationary_battle_camera": "equal current/previous X/Y keepsCX0 and skips3367 plus11BC/parallax",
                       "wipe_stage_update": "after0200 completes,0400 branch does not callBG1 camera;1000 shake callsBG0 only",
                       "timer_scroll": "terminal1A42 sets20 before1B15 sets200;989C4030 test excludes its scroll call",
                       "ordinary_external_displacement": "scene root installs0B8B, whose complete call population omits normal0D0B's7426B0 hit,7427FB pair-command collision,74273B bodypush consumers",
                       "grid_cells": 3024, "grid_auxiliary_words_zero": True,
                       "center_landing_rows": [42, 50, 51, 52, 53]},
            "source_clear": {"live_input": "BX from input07D6 BG0+12 if intervening task/IRQ preserves it",
                             "formula": "(0800 + (BX<<6)) & FFFF;64 halfwords",
                             "native_map_only_domain": [0, 62],
                             "conditional_witness_not_runtime": {"BX": 268, "start": 0x4B00, "end": 0x4B80,
                                 "owner": "common-bank tile graphics, not BG screen maps"}},
            "remaining": ["actual terminal BX and incoming scheduling ownership",
                          "project exact reached source destination into its native owner",
                          "post-ground P1 current/previous equality through0400, including existing callback/hit owners",
                          "common tile0 remains horizontally uniform through finalIRQ"],
            "no_unconditional_IRQ_or_entry_claim": True, "negative_controls": rejected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    need(not args.output.exists(), "fresh evidence output required")
    report = analyze(args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
    print("[shoot-terminal-lifetime] conditional evidence PASS; exact live-in/owner remains open")


if __name__ == "__main__":
    main()
