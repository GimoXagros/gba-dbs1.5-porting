#!/usr/bin/env python3
"""Resident Shoot terminal scene, native damage adapters and order repairs.

The external retail damage/scene hooks are described but remain untouched in
this layer. The route owner may install them only after every prerequisite is
verified. No emulator, new RAM owner or replacement engine is involved.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs
from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks
from analyze_shoot_terminal import HASHES, PHASES, proof, sha, need

BASE, START, END = 0x08000000, 0x5CD000, 0x5D0000
INPUT_SHA256 = "F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF"
DRAFT_SHA256 = "6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29"
FLAGS, COMMON, FIRST, COUNT, LIST = 0x0300450A, 0x03004506, 0x0300489C, 0x0300475E, 0x03004760
STATE, CAMERA_Y, CURRENT = 0x03004710, 0x0300451E, 0x0300133C
GAPS = tuple((x & ~31, (x & ~31) + 32) for x in
             (0x5CDBA0, 0x5CE1A0, 0x5CE1E0, 0x5CE210, 0x5CED34, 0x5CED50, 0x5CFB84, 0x5CFE70))
REGS = "{r0-r12, lr}"
UPPER = (
    ("7AB1", 0x5BDD00, 164, "8A37DE317A192E4495D9806DA8C4CA65BB815430727A9BEBF8D5C5084F1B1C87", 0x5BDD8C, 0x085BE000, "{r6-r7, lr}"),
    ("7BFF", 0x5BE600, 176, "6DCC641FCF4653F71952E48FF5DB110ACDFB89010ECFD47ED76FEA1C39912969", 0x5BE69C, 0x085BEA00, "{lr}"),
    ("7C64", 0x5BEA00, 200, "F052AF98AA98C129CC5A6D0C0B6C97C601382AB50E41965640C677B8D46A0283", 0x5BEAB8, 0x085BEE00, "{lr}"),
    ("7D8D", 0x5BF204, 44, "3A76973A12C401FA38F1128D7D2FB54B8EB719EB2BC7B8F3242B4828B003FEEE", 0x5BF224, 0x085BF400, None),
)


class Function:
    def __init__(self, addresses: dict[str, int]):
        self.addresses = addresses
        self.literals: list[tuple[str, int]] = []

    def load(self, register: str, value: int) -> str:
        label = f"literal_{len(self.literals)}"
        self.literals.append((label, value & 0xFFFFFFFF))
        return f"ldr {register}, {label}\n"

    def call(self, name: str) -> str:
        return f"bl 0x{self.addresses[name]:08X}\n"

    def assign(self, phase: int) -> str:
        return self.load("r8", self.addresses[f"{phase:04X}"]) + "bl 0x08012008\n"

    def finish(self, source: str, offset: int, *, wrapper: bool = True) -> tuple[bytes, int]:
        if wrapper:
            source = f"push {REGS}\nmov r11, #0\n" + source + f"done:\npop {REGS}\nbx lr\n"
        text = source + ".align 2\n" + "".join(f"{label}: .word 0x{value:08X}\n" for label, value in self.literals)
        # Literal labels are resolved only by the complete assembly.
        complete, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, BASE + offset)
        code_size = len(complete) - 4 * len(self.literals)
        return bytes(complete), code_size


def state() -> str:
    return "bl 0x0801201C\nmov r4, r0\n"


def timer(value: int) -> str:
    return f"mov r8, #{value}\nstrh r8, [r4, #0x50]\n"


def decrement() -> str:
    return "ldrh r8, [r4, #0x50]\nsub r8, r8, #1\nstrh r8, [r4, #0x50]\nlsl r8, r8, #16\nlsr r8, r8, #16\ncmp r8, #0\n"


def modify(f: Function, address: int, set_bits: int = 0, clear_bits: int = 0) -> str:
    text = f.load("r0", address) + "ldrh r1, [r0]\n"
    if clear_bits:
        text += f"bic r1, r1, #0x{clear_bits:X}\n"
    if set_bits:
        text += f"orr r1, r1, #0x{set_bits:X}\n"
    return text + "strh r1, [r0]\n"


def object_event(obj: str, number: int) -> str:
    return f"push {{{obj}}}\npush {{r11}}\nmov r8, #{number}\npush {{r8}}\nbl 0x08012874\nadd sp, sp, #12\n"


def sound(number: int, kind: int) -> str:
    return f"mov r8, #{number}\nmov r9, #{kind}\nmov r10, #0\nbl 0x080D15C0\n"


def palette_triples(f: Function, white: bool) -> str:
    text = ""
    for address in (0x05000064, 0x05000084, 0x050000A4):
        text += f.load("r0", address) + f"mov r1, #8\nmov r2, #{int(white)}\n" + f.call("fade_span")
    return text


def make(name: str, offset: int, addresses: dict[str, int]) -> tuple[bytes, int]:
    f = Function(addresses)
    body = ""
    if name == "1750":
        body = state() + timer(121) + f.load("r6", COUNT) + "ldrb r6, [r6]\n" + f.load("r7", LIST)
        body += "cmp r6, #0\nbeq released\nrelease_loop:\nldr r8, [r7], #4\npush {r8}\npush {r11}\nbl 0x083524C4\nadd sp, sp, #8\nsubs r6, r6, #1\nbne release_loop\nreleased:\n"
        body += f.load("r4", FIRST) + "ldr r4, [r4]\nmov r8, #1\nstrh r8, [r4, #0x64]\n"
        body += modify(f, COMMON, clear_bits=0x400) + sound(0x5C, 2) + f.assign(0x17DF) + f.call("17DF")
    elif name == "17DF":
        body = state() + decrement() + "bne blink\n" + modify(f, FLAGS, set_bits=0x80) + f.assign(0x182F) + "b done\nblink:\n"
        body += f.load("r0", 0x03004529) + "ldrb r1, [r0]\neor r1, r1, #7\nstrb r1, [r0]\nmov r8, #1\nstrh r8, [r4, #0x64]\n"
    elif name == "182F":
        body = state() + "mov r6, r4\n" + f.load("r4", FIRST) + "ldr r4, [r4]\nmov r8, #0\nstrh r8, [r4, #0x2C]\nstrh r8, [r4, #0x2E]\n"
        body += "ldrsh r8, [r4, #0x34]\ncmp r8, #0xE40\nmovge r8, #8\nstrhge r8, [r4, #0x2C]\nbge done\ncmp r8, #0xDC0\nmovle r8, #2\nstrhle r8, [r4, #0x2C]\nble done\nldrh r8, [r4, #0x36]\ncmp r8, #0xC00\nbhi jump\n"
        body += f.assign(0x197A) + "b done\njump:\n" + f.load("r8", 0xFFFFFB54)
        body += "strh r8, [r4, #0xA0]\nmov r8, #0x14\nstrh r8, [r4, #0xA2]\nmov r8, #0xF\nstrh r8, [r4, #0xA4]\nmov r8, #1\nstrh r8, [r4, #0xA8]\nmov r8, #16\nstrb r8, [r4, #0x70]\nadd r5, r4, #0xAC\n"
        # An event can call the native sound requester, which overwrites r6/r7.
        # Preserve the current-task state until its following timer write.
        body += "push {r6}\n" + object_event("r5", 11) + "pop {r6}\n" + f.load("r8", 0x08357670) + "str r8, [r4]\nmov r8, #1\nstrh r8, [r6, #0x50]\n" + f.assign(0x193B)
    elif name == "18EE":
        body = state() + f.load("r5", FIRST) + "ldr r5, [r5]\nmov r8, #0x40\nstrh r8, [r5, #0x2C]\n" + decrement() + "bne done\nmov r8, #0\nstrh r8, [r5, #0x2C]\nstrh r8, [r5, #0x2E]\n" + f.assign(0x193B)
    elif name == "193B":
        body = f.load("r4", FIRST) + "ldr r4, [r4]\nldrh r8, [r4, #6]\ntst r8, #4\nbeq done\n" + f.assign(0x197A)
    elif name == "197A":
        body = f.load("r0", FLAGS) + "ldrh r1, [r0]\ntst r1, #0x100\nbeq done\nbic r1, r1, #0x100\nstrh r1, [r0]\n"
        body += f.load("r4", STATE) + "mov r8, #0x154\nstrh r8, [r4]\nmov r8, #0x8F\nstrh r8, [r4, #2]\nstrh r8, [r4, #4]\nmov r8, #0\nstrh r8, [r4, #6]\n"
        # Source IN 11 is the BG0 vertical scroll shadow, as in the retail
        # translated display helper; the map clear's BX comes from scene input.
        body += f.load("r0", 0x030012B9) + "ldrb r8, [r0]\nstrh r8, [r4, #8]\nmov r8, #0x48\nstrh r8, [r4, #0xA]\nmov r8, #0\nstrh r8, [r4, #0xC]\n"
        body += f.load("r0", CAMERA_Y) + "ldrh r1, [r0]\n" + f.call("clear_rows") + f.assign(0x19F2)
    elif name == "19F2":
        body = state() + f.load("r0", FLAGS) + "ldrh r1, [r0]\ntst r1, #0x100\nbeq done\nbic r1, r1, #0x100\nstrh r1, [r0]\n"
        body += modify(f, COMMON, set_bits=0x10) + timer(60) + f.assign(0x1A42)
    elif name == "1A42":
        body = state() + decrement() + "bne done\n" + timer(32) + modify(f, FLAGS, set_bits=0x20)
        body += f.load("r0", 0x03004D40) + "mov r1, #1\nstrh r1, [r0]\n" + modify(f, FLAGS, set_bits=0x1000) + f.assign(0x1A95)
    elif name == "1A95":
        body = state() + "ldrh r8, [r4, #0x50]\ntst r8, #1\nbeq tick\n" + palette_triples(f, False) + "tick:\n" + decrement() + "bne done\n" + timer(60) + f.assign(0x1B15)
    elif name == "1B15":
        body = state() + decrement() + "bne done\n" + modify(f, FLAGS, set_bits=0x200) + f.assign(0x1B55)
    elif name == "1B55":
        body = state() + f.load("r0", FLAGS) + "ldrh r1, [r0]\ntst r1, #0x100\nbeq done\n" + timer(64) + f.assign(0x1B97)
    elif name == "1B97":
        body = state() + "ldrh r8, [r4, #0x50]\ntst r8, #3\nbne tick\n" + palette_triples(f, True) + "tick:\n" + decrement() + "bne done\n" + timer(60) + f.assign(0x1C17)
    elif name == "1C17":
        body = state() + decrement() + "bne done\n" + timer(60) + modify(f, FLAGS, set_bits=0x2000) + f.assign(0x1C5C)
    elif name == "1C5C":
        body = state() + decrement() + "bne done\n" + f.call("result_resources") + f.assign(0x1D41) + sound(0x0B, 4)
    elif name == "1D41":
        body = state() + "ldrh r8, [r4, #0xA]\ntst r8, #0x2000\nbne finished\n" + object_event("r4", 1).replace("0x08012874", "0x08012A84")
        body += "push {r4}\npush {r11}\nbl 0x08012C28\nadd sp, sp, #8\nb done\nfinished:\n" + timer(93)
        body += "mov r8, #32\nbl 0x0833FDC0\nmov r11, #0\n" + f.assign(0x1DA0)
    elif name == "1DA0":
        body = "bl 0x0833FF00\nmov r11, #0\ncmp r0, #0\nbeq done\n" + f.assign(0x1DC3) + f.call("1DC3")
    elif name == "1DC3":
        body = "bl 0x08340C54\n"
    elif name == "result_resources":
        body = "push {r4}\npush {r11}\n" + f.load("r8", 0x08374824) + "push {r8}\npush {r11}\npush {r11}\n"
        body += f.load("r8", 0x08374854) + "push {r8}\npush {r11}\npush {r11}\n" + f.load("r8", 0x08374E44) + "push {r8}\npush {r11}\npush {r11}\n"
        for value in (0x4000, 0x1800, 0x137, 0):
            body += (f.load("r8", value) if value == 0x137 else f"mov r8, #{value}\n") + "push {r8}\n"
        body += "bl 0x080127E4\nadd sp, sp, #60\n" + object_event("r4", 0)
        body += "ldrh r8, [r4, #8]\norr r8, r8, #0x2000\nstrh r8, [r4, #8]\nmov r8, #0x70\nstrh r8, [r4]\nmov r8, #0x48\nstrh r8, [r4, #2]\nmov r8, #0x96\nstrh r8, [r4, #0x50]\n"
        body += f.load("r8", 0x08374E44) + "push {r8}\npush {r11}\npush {r11}\npush {r11}\npush {r11}\nbl 0x080132EC\nadd sp, sp, #20\n"
    elif name == "fade_span":
        body = "cmp r1, #0\nbeq done\ncolor_loop:\nldrh r3, [r0]\nmov r4, #0\n"
        for shift in (0, 5, 10):
            body += ("mov r5, r3\n" if shift == 0 else f"lsr r5, r3, #{shift}\n") + "and r5, r5, #31\ncmp r2, #0\nbne white_%d\n" % shift
            body += f"cmp r5, #3\nmovls r5, #0\nsubhi r5, r5, #2\nb channel_{shift}\nwhite_{shift}:\ncmp r5, #0\nmoveq r5, #3\naddne r5, r5, #2\ncmp r5, #31\nmovhi r5, #31\nchannel_{shift}:\norr r4, r4, r5, lsl #{shift}\n"
        body += "strh r4, [r0], #2\nsubs r1, r1, #1\nbne color_loop\n"
    elif name == "clear_rows":
        # The proved source mapping is two adjacent 32x32 tile maps. No
        # arbitrary source physical address is projected into GBA OBJ VRAM.
        body = "cmp r1, #62\nbhi done\n" + f.load("r0", 0x0600F000) + "add r0, r0, r1, lsl #6\nmov r2, #64\nmov r3, #0\nclear_loop:\nstrh r3, [r0], #2\nsubs r2, r2, #1\nbne clear_loop\n"
    elif name == "fatal_adapter":
        body = f.load("r8", 0x03002310) + "ldrb r8, [r8, #0xE]\ncmp r8, #11\nbne legacy\nmov r0, r5\n" + f.load("r8", 0x085BDD00)
        body += "str r8, [r5]\nldr r5, [r5, #0x28]\n" + f.load("r8", 0x085BF204) + "str r8, [r5]\nb 0x0836E604\nlegacy:\nmov r0, r5\nb 0x0836E5F0\n"
        return f.finish(body, offset, wrapper=False)
    elif name == "hit_adapter":
        body = f.load("r8", 0x03002310) + "ldrb r8, [r8, #0xE]\ncmp r8, #11\nbne legacy\n"
        body += f.load("r8", 0x085C0B00) + "push {r8}\nmov r8, #0\npush {r8}\npush {r8}\npush {r8}\nmov r8, #1\npush {r8}\nbl 0x080132EC\nadd sp, sp, #20\nmov r8, #8\nstrh r8, [r5, #0x74]\n"
        body += f.load("r8", FLAGS) + "ldrh r8, [r8]\ntst r8, #0x4000\nbne hit_done\ntst r8, #0x30\nbne hit_done\nmov r0, #0x05000000\nmov r1, #16\nmov r2, #31\nred_bg:\nstrh r2, [r0], #0x20\nsubs r1, r1, #1\nbne red_bg\nmov r1, #8\nred_obj:\nstrh r2, [r0], #0x20\nsubs r1, r1, #1\nbne red_obj\nhit_done:\nb 0x0836E438\nlegacy:\n"
        body += f.load("r8", 0x0834F836) + "b 0x0836E638\n"
        return f.finish(body, offset, wrapper=False)
    elif name.startswith("repair_"):
        row = next(r for r in UPPER if name == "repair_" + r[0])
        body = "str r8, [r4]\n"
        if row[6] is None:
            body += "push {lr}\n"
        body += f"bl 0x{row[5]:08X}\npop {row[6] or '{lr}'}\nbx lr\n"
        return f.finish(body, offset, wrapper=False)
    else:
        raise ValueError(name)
    return f.finish(body, offset)


def assemble(source: str, offset: int) -> bytes:
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + offset)[0])


def plan() -> list[dict]:
    names = [f"{p:04X}" for p in PHASES] + ["result_resources", "fade_span", "clear_rows", "fatal_adapter", "hit_adapter"] + ["repair_" + r[0] for r in UPPER]
    addresses = {name: BASE + START for name in names}
    for _ in range(3):
        cursor = START
        rows = []
        for name in names:
            cursor = (cursor + 15) & ~15
            while True:
                blob, code_size = make(name, cursor, addresses)
                collision = next(((a, b) for a, b in GAPS if cursor < b and a < cursor + len(blob)), None)
                if collision is None:
                    break
                cursor = collision[1]
            addresses[name] = BASE + cursor
            rows.append({"name": name, "offset": cursor, "blob": blob, "code_size": code_size})
            cursor += len(blob)
        need(cursor <= END, "terminal resident allocation bound")
    return rows


def inbound(before: bytes, intervals: list[tuple[int, int]]) -> list[tuple[str, int, int]]:
    candidates = []
    for site in range(len(before) - 3):
        value = struct.unpack_from("<I", before, site)[0] - BASE
        if START <= value < END:
            candidates.append(("pointer", site, value))
    for site in range(0, len(before) - 3, 4):
        word = struct.unpack_from("<I", before, site)[0]
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            delta = (word & 0xFFFFFF) - (0x1000000 if word & 0x800000 else 0)
            target = site + 8 + delta * 4
            if START <= target < END:
                candidates.append(("branch", site, target))
    need(not any(a <= target < b for _, _, target in candidates for a, b in intervals), "incoming encoding reaches actual terminal write")
    return candidates


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=pathlib.Path)
    p.add_argument("gba", type=pathlib.Path)
    p.add_argument("wsc10", type=pathlib.Path)
    p.add_argument("wsc15", type=pathlib.Path)
    p.add_argument("output", nargs="?", type=pathlib.Path)
    p.add_argument("--manifest", type=pathlib.Path, required=True)
    p.add_argument("--draft-proof", action="store_true")
    args = p.parse_args()
    if not args.draft_proof:
        need(INPUT_SHA256 is not None, "exact stage-handshake predecessor not yet pinned")
        need(args.output is not None, "terminal output path required")
    paths = (args.input, args.gba, args.wsc10, args.wsc15)
    need(all(path.suffix.lower() != ".sav" for path in paths), "save files are forbidden")
    before, gba, old, source = (path.read_bytes() for path in paths)
    need(sha(before) == (DRAFT_SHA256 if args.draft_proof else INPUT_SHA256), "terminal exact predecessor")
    need(tuple(map(sha, (gba, old, source))) == HASHES, "terminal source identities")
    evidence = proof(gba, old, source)
    rows = plan()
    intervals = [(row["offset"], row["offset"] + len(row["blob"])) for row in rows]
    candidates = inbound(before, intervals)
    writes = []
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for row in rows:
        raw, blob, code = row["offset"], row["blob"], row["code_size"]
        need(before[raw:raw + len(blob)] == b"\xff" * len(blob), "terminal resident Expected Write")
        instructions = list(engine.disasm(blob[:code], BASE + raw))
        need(len(instructions) * 4 == code, "complete terminal ARM decoding")
        rebuilt = assemble("\n".join(i.mnemonic + " " + i.op_str for i in instructions), raw)
        need(rebuilt == blob[:code], "terminal ARM instruction round trip")
        writes.append((raw, before[raw:raw + len(blob)], blob, row["name"]))
    entries = {row["name"]: BASE + row["offset"] for row in rows}
    for name, raw, size, digest, site, _, _ in UPPER:
        need(sha(before[raw:raw + size]) == digest, "exact upper callback before same-update repair")
        need(before[site:site + 4] == bytes.fromhex("008084E5"), "upper final callback store")
        writes.append((site, before[site:site + 4], assemble(f"b 0x{entries['repair_' + name]:08X}", site), "same_update_" + name))
    need(before[0x36E5EC:0x36E5F0] == gba[0x36E5EC:0x36E5F0] and before[0x36E634:0x36E638] == gba[0x36E634:0x36E638], "external damage hooks remain original")
    future_hooks = [{"site": site, "before_hex": before[site:site + 4].hex().upper(),
                     "target": entries[name], "after_hex": assemble(f"b 0x{entries[name]:08X}", site).hex().upper()}
                    for site, name in ((0x36E5EC, "fatal_adapter"), (0x36E634, "hit_adapter"))]
    after = bytearray(before)
    covered = set()
    for site, previous, replacement, name in writes:
        population = set(range(site, site + len(previous)))
        need(not population & covered and before[site:site + len(previous)] == previous, "disjoint terminal Expected Writes")
        covered |= population
        after[site:site + len(replacement)] = replacement
    changes = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    expected = {site + i for site, a, b, _ in writes for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y}
    need(changes == expected, "complete terminal diff containment")
    report = {"schema": 1, "kind": "shoot-terminal-resident-draft" if args.draft_proof else "shoot-terminal-resident",
        "input_sha256": sha(before), "planned_output_sha256": sha(after), "rom_emitted": not args.draft_proof,
        "entries": entries, "source_evidence": evidence, "incoming_gap_candidates": candidates,
        "expected_writes": [{"name": name, "offset": site, "bytes": len(b), "before_sha256": sha(a), "sha256": sha(b)} for site, a, b, name in writes],
        "code": [{"name": row["name"], "offset": row["offset"], "bytes": row["code_size"], "literal_bytes": len(row["blob"]) - row["code_size"]} for row in rows],
        "future_damage_hooks": future_hooks, "changed_bytes": len(changes),
        "external_hooks_installed": False, "new_ram": 0,
        "open_contracts": ["stage handshake source0DEC interrupted-DI semantics remain a route gate",
            "197A row clear only maps camera-Y0..62; upstream exact range and live-in ownership remain a route gate",
            "full initializer/controller/scene and all required gates precede external hooks"],
        "scope": "real resident terminal callbacks, existing result resources/native consumers, fatal/nonfatal damage adapters, four same-update fixes; no runtime claim"}
    if not args.draft_proof:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-terminal] " + ("draft machine code verified; external hooks closed" if args.draft_proof else sha(after)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
