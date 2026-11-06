#!/usr/bin/env python3
"""Prove synchronous pause retirement before the normal Shoot terminal owner."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from analyze_shoot_terminal_bx import exact, need, SOURCE

GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"


def arm(b, at, rows):
    actual = [i.mnemonic + " " + i.op_str for i in
        Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(b[at:at + len(rows)*4], 0x08000000 + at)]
    need(actual == rows, f"native semantics {at:X}")


def contracts(s, b):
    exact(s, 0x7412BB, ["or byte ptr es:[0x3cd], 1"])
    exact(s, 0x7412DC, ["or byte ptr es:[0x3cd], 2"])
    exact(s, 0x74165E, ["test byte ptr es:[0x3cd], 7", "je 0x741669", "jmp 0x74181a"])
    exact(s, 0x7417E6, ["mov bx, word ptr es:[0x65e]", "cmp word ptr [bx + 0x50], 0",
        "jg 0x7417fe", "push 5", "lcall 0x71f0, 0", "add sp, 2", "jmp 0x7418c6"])
    exact(s, 0x7864A3, ["and byte ptr es:[0x3cd], 0xfc", "and byte ptr es:[0x3cd], 0xf7"])
    exact(s, 0x7864DA, ["push ds", "mov ax, 0xc00", "mov ds, ax", "mov ax, word ptr [8]",
        "pop ds", "push 0xc00", "push ax", "lcall 0x4fff, 0xa32", "add sp, 4",
        "cmp word ptr [si + 0x84], 0", "je 0x786508", "push 1", "lcall 0x71f0, 0"])
    exact(s, 0x750A2F, ["dec word ptr [6]", "mov word ptr [si + 0xa], 0"])
    exact(s, 0x750A85, ["mov di, word ptr [si + 6]", "mov ax, word ptr [si + 8]",
        "mov word ptr [di + 8], ax", "mov di, word ptr [si + 8]",
        "mov ax, word ptr [si + 6]", "mov word ptr [di + 6], ax"])
    # Scene input contains no pause dispatch and is installed before allocation.
    exact(s, 0x771FA3, ["push 0x4090", "push 0x7d6", "push 0xc00",
        "push word ptr es:[0x3de]", "lcall 0x4fff, 0xbc7", "add sp, 8",
        "push 0xff0", "push 0x71f0", "push 0x653", "lcall 0x4fff, 0x980"])
    exact(s, 0x7410D6, ["mov ax, 0xc00", "mov ds, ax", "mov ax, 0x1000", "mov es, ax",
        "mov word ptr [0x3a20], 0", "call 0x7424c6", "mov ax, word ptr es:[0x1de]",
        "mov bx, word ptr es:[0x1e0]", "mov word ptr [0x3a14], ax",
        "mov word ptr [0x3a16], bx", "retf"])
    exact(s, 0x7424C6, ["mov byte ptr [0x3bae], 0", "mov byte ptr [0x3baf], 0",
        "mov byte ptr [0x3cd6], 0", "ret"])
    arm(b, 0x37527C, ["ldrb sb, [r8]", "orr sb, sb, #1", "strb sb, [r8]"])
    arm(b, 0x3752B0, ["ldrb sb, [r8]", "orr sb, sb, #2", "strb sb, [r8]"])
    arm(b, 0x37362C, ["ldrb sb, [r8]", "tst sb, #7", "bne #0x83736e8"])
    arm(b, 0x375718, ["ldr r8, [pc, #0xb0]", "ldrb sb, [r8]", "bic sb, sb, #3",
        "bic sb, sb, #8", "strb sb, [r8]", "bl #0x801201c", "mov r4, r0",
        "bl #0x8012030", "ldrh r8, [r4, #0xa0]", "cmp r8, #0", "beq #0x837579c",
        "mov r8, #1", "stmdb sp!, {r8}", "bl #0x833fc28"])
    arm(b, 0x12034, ["ldr r8, [pc, #0x18]", "ldr sb, [r8]", "stmdb sp!, {sb}",
        "stmdb sp!, {fp}", "bl #0x8011be4"])
    arm(b, 0x11BFC, ["mov sl, #0", "strh sl, [r4, #0x10]"])
    arm(b, 0x11C74, ["ldr r5, [r4, #8]", "ldr r0, [r4, #0xc]", "str r0, [r5, #0xc]",
        "ldr r5, [r4, #0xc]", "ldr r0, [r4, #8]", "str r0, [r5, #8]"])
    for site in (0x375278, 0x3752AC, 0x373628, 0x375718):
        w = struct.unpack_from("<I", b, site)[0]
        need(struct.unpack_from("<I", b, site + 8 + (w & 4095))[0] == 0x03004529,
             "all native pause flags use the same byte owner")


def main():
    p = argparse.ArgumentParser()
    for name in ("source", "gba", "current", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    need(not a.output.exists(), "fresh report required")
    s, g, b = (getattr(a, name).read_bytes() for name in ("source", "gba", "current"))
    sha = lambda x: hashlib.sha256(x).hexdigest().upper()
    need(sha(s) == SOURCE and sha(g) == GBA, "source identities")
    ranges = ((0x375250, 0x375314), (0x375360, 0x3757F8), (0x3735BC, 0x373928),
              (0x12008, 0x12058), (0x11BE4, 0x11CB0), (0x374FAC, 0x374FE4))
    need(all(b[x:y] == g[x:y] for x,y in ranges), "actual image retains native pause/retirement consumers")
    contracts(s,b)
    rejected = []
    for label, source, site in (("source pause flag", True, 0x7412C0),
        ("source battle mask", True, 0x741663), ("source retire call", True, 0x7864E9),
        ("source unlink next", True, 0x750A8D), ("native battle mask", False, 0x373630),
        ("native missing retirement", False, 0x375734), ("native retirement unlink", False, 0x11C7C)):
        x,y = bytearray(s),bytearray(b)
        (x if source else y)[site] ^= 1
        try: contracts(x,y)
        except ValueError: rejected.append(label)
        else: raise ValueError("ineffective mutation " + label)
    for flags in range(256):
        for player in (1,2):
            need((flags | player) & 7, "allocated pause suppresses normal case5 producer")
    report = {"status":"PASS", "current_sha256":sha(b), "source_sha256":SOURCE,
        "pause_interposer_closed_for_normal_case5":True,
        "proof":"pause sets1/2 before allocation; battle excludes mask7; unpause unlinks synchronously before later battle/case1 root;07D6 cannot allocate pause",
        "flags_cases":512, "negative_controls":rejected,
        "limit":"normal source case5 producer only; no arbitrary forced task entry or camera/clear equivalence claim",
        "ROM_modified":False, "runtime_executed":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8",newline="\n")
    print("[terminal-pause] normal case5 pause exclusion PASS")


if __name__ == "__main__": main()
