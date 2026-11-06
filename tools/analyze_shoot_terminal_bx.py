#!/usr/bin/env python3
"""Source-only terminal BX provenance; no game execution or image mutation."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def need(ok, label):
    if not ok:
        raise ValueError(label)


def decode(s, a, z):
    rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(s[a:z], a))
    need(sum(i.size for i in rows) == z - a, f"complete source range {a:X}")
    return rows


def exact(s, a, expected):
    rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(s[a:a + 192], a))[:len(expected)]
    need([f"{i.mnemonic} {i.op_str}".rstrip() for i in rows] == expected,
         f"source semantics {a:X}")


def contracts(s):
    # Dispatcher saves the iterator, not the callback's BX live-out.
    exact(s, 0x750B57, ["push es", "push di", "push cx", "lcall es:[di]",
        "pop cx", "pop di", "pop es", "mov si, word ptr es:[0x10]",
        "mov ax, word ptr es:[si + 4]", "cmp word ptr es:[di + 4], ax",
        "mov di, word ptr es:[di + 8]", "jae 0x750b76", "jmp 0x750b43"])
    scheduler = decode(s, 0x750B1F, 0x750B94)
    need(not any("bx" in i.op_str or i.mnemonic in ("pushaw", "popaw") for i in scheduler),
         "dispatcher never saves, restores, or assigns BX")
    exact(s, 0x750EBD, ["push ax", "push ds", "in al, 0xb2", "or al, 0x40",
        "out 0xb2, al", "mov ax, 0xc00", "mov ds, ax",
        "cmp byte ptr [0x3754], 0", "je 0x750eca", "mov byte ptr [0x3754], 0",
        "pop ds", "pop ax", "retf"])
    # The insertion search uses unsigned ascending priorities, including equals.
    exact(s, 0x750C73, ["mov bx, word ptr [bp + 6]", "mov di, word ptr [0xc]",
        "cmp word ptr [di + 4], bx", "jbe 0x750c89"])
    exact(s, 0x750C89, ["mov di, word ptr [0x10]", "cmp word ptr [di + 4], bx",
        "ja 0x750c9c", "mov dx, 0xffff"])
    exact(s, 0x750C9C, ["mov di, word ptr [0xc]", "mov si, word ptr [di + 8]",
        "cmp bx, word ptr [si + 4]", "jb 0x750cad", "mov di, si", "jmp 0x750ca0"])
    exact(s, 0x740CB3, ["push 0", "lcall 0x4fff, 0x1d68", "add sp, 2",
        "lcall 0x4090, 0x166e", "lcall 0x4090, 0x6ba"])
    exact(s, 0x740FC1, ["push 0xf00", "push 0x4090", "push 0x71a",
        "lcall 0x4fff, 0x980", "add sp, 6", "mov word ptr [0x3de], ax",
        "push 0x6000", "push 0x4090", "push 0xa16", "lcall 0x4fff, 0x980"])
    exact(s, 0x771FA3, ["push 0x4090", "push 0x7d6", "push 0xc00",
        "push word ptr es:[0x3de]", "lcall 0x4fff, 0xbc7", "add sp, 8",
        "push 0xff0", "push 0x71f0", "push 0x653", "lcall 0x4fff, 0x980"])
    exact(s, 0x771F53, ["push 0x4090", "push 0xb8b", "push 0xc00",
        "push word ptr es:[0x3e0]", "lcall 0x4fff, 0xbc7", "add sp, 8"])
    exact(s, 0x7861E7, ["push 0xff0", "push 0x8619", "push 0x193", "lcall 0x4fff, 0x980"])
    # Callback replacement changes only task+0/+2, preserving priority+4.
    exact(s, 0x750BC3, ["mov ax, word ptr [bp + 0xa]", "mov word ptr [si], ax",
        "mov ax, word ptr [bp + 0xc]", "mov word ptr [si + 2], ax",
        "pop ds", "pop si", "pop ax", "mov sp, bp", "pop bp", "retf"])
    exact(s, 0x741FAA, ["push word ptr cs:[bx + 0x16ce]", "push 0x4090",
        "push 0x1bc4", "lcall 0x4fff, 0x980", "add sp, 6", "mov word ptr [si], ax",
        "add si, 2", "add bx, 2", "loop 0x741faa"])
    exact(s, 0x741FA5, ["mov cx, 0x1a", "xor bx, bx"])
    exact(s, 0x7410D6, ["mov ax, 0xc00", "mov ds, ax", "mov ax, 0x1000",
        "mov es, ax", "mov word ptr [0x3a20], 0", "call 0x7424c6",
        "mov ax, word ptr es:[0x1de]", "mov bx, word ptr es:[0x1e0]",
        "mov word ptr [0x3a14], ax", "mov word ptr [0x3a16], bx", "retf"])
    terminal = decode(s, 0x77383B, 0x7738CA)
    bxops = [(i.address, i.mnemonic, i.op_str) for i in terminal if "bx" in i.op_str]
    need(bxops == [(0x773861, "push", "bx"), (0x77386B, "mov", "bx, ax"),
        (0x773870, "mov", "word ptr [bx], ax"), (0x773875, "mov", "word ptr [bx + 2], ax"),
        (0x773879, "pop", "bx")], "193B assignment restores incoming BX;197A does not replace it")
    need(not any(i.mnemonic in ("call", "lcall") for i in terminal),
         "no hidden callee before terminal BX consumer")
    exact(s, 0x7738CA, ["mov di, bx", "shl di, 6", "add di, 0x800",
        "mov cx, 0x40", "rep stosw word ptr es:[di], ax"])
    # Both transition line handlers explicitly balance BX around their writes.
    for a, z in ((0x75FC27, 0x75FC8C), (0x75FC8C, 0x75FCA3)):
        rows = decode(s, a, z)
        need([(i.mnemonic, i.op_str) for i in rows if i.mnemonic in ("push", "pop") and i.op_str == "bx"]
             == [("push", "bx"), ("pop", "bx")], "line IRQ preserves BX")
        need(not any(i.mnemonic in ("call", "lcall") for i in rows), "line IRQ has no callees")


def analyze(s):
    need(hashlib.sha256(s).hexdigest().upper() == SOURCE, "original identity")
    contracts(s)
    pool = struct.unpack_from("<26H", s, 0x741FCE)
    need(all(p > 0xFF0 for p in pool), "all actual pool priorities follow scene")
    queue = sorted([(0, "sound"), (0xF00, "input"), (0xFF0, "scene"), (0x6000, "battle")]
                   + [(p, f"pool{i}") for i, p in enumerate(pool)])
    names = [n for _, n in queue]
    need(names[names.index("input") + 1] == "scene", "positive normal creators have adjacent input/scene")
    starts = {(0x800 + (bx << 6)) & 0xFFFF for bx in range(65536)}
    need(starts == set(range(0, 65536, 64)), "provenance alone does not bound camera")
    rejected = []
    for label, at in (("dispatcher restores BX instead of CX", 0x750B5D),
                      ("input priority", 0x740FC2), ("scene priority", 0x771FBA),
                      ("input camera owner", 0x7410F0), ("lost scene BX restore", 0x773879),
                      ("clear takes AX", 0x7738CB), ("reversed priority ordering", 0x750CA6),
                      ("lost final IRQ BX restore", 0x75FCA0)):
        bad = bytearray(s); bad[at] ^= 1
        try:
            contracts(bad)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("ineffective mutation " + label)
    return {"status": "SOURCE_PROVENANCE_PASS", "source_sha256": SOURCE,
        "dispatcher_restores_BX": False, "dispatcher_bookkeeping_writes_BX": False,
        "ordering": {"input": 0xF00, "scene": 0xFF0, "battle": 0x6000,
                     "actor_pool_priorities": list(pool), "normal_creator_queue": queue,
                     "battle_runs_after_scene": True},
        "input_live_out": "BX=word1000:01E0 (BG0 pixel camera Y);same value stored0C00:3A16",
        "scene_live_in": "193B restores its temporary callback-assignment BX;197A uses incoming BX unchanged",
        "transition_line_IRQs_preserve_BX": True,
        "conclusion": "With the normal exclusive scene queue,7738CA consumes the preceding07D6 camera snapshot, not a task pointer or tile-row index",
        "scope": "Positive normal creators and relevant dispatch/callback bodies; not an exhaustive arbitrary task-state or all-interrupt proof",
        "still_open": ["pause8619:0193 also uses0FF0; its retirement/exclusion and other enabled IRQ ownership remain required",
                       "actual camera value/range at197A and its reached physical destination owner",
                       "source-owner native projection or overwritten-before-consumption proof"],
        "unrestricted_arithmetic_starts": len(starts), "negative_controls": rejected,
        "ROM_written": False, "runtime_executed": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("wsc15", type=pathlib.Path)
    p.add_argument("output", type=pathlib.Path)
    a = p.parse_args()
    need(not a.output.exists(), "fresh output required")
    report = analyze(a.wsc15.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
    print("[terminal-BX] source provenance PASS; actual destination remains open")


if __name__ == "__main__":
    main()
