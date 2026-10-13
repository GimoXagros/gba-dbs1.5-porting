#!/usr/bin/env python3
"""Independent static consumer proof for the source conditional case-5 route.

Does not import either generator, execute a CPU/game, or open a save.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16  # type: ignore

BASE = 0x08000000
HASHES = {"gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
          "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
          "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"}
PROFILE = ((0x5C9900, 80, 104, "4DA88F37392E04BF28407CCF0E1A25A96A01FF8A412A2F974B6F89BF927C6A4C"),
           (0x5C9A00, 64, 84, "8CFDEB79A40E7FA23B90C6513C239C09A47D7D9075EAD8EE145D2BBC76848D76"))
HOOKS = ((0x33FD04, 0xE59F80A8, 0x5C9900), (0xB9E68, 0xE59F10C0, 0x5C9A00))


def digest(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def x86(data, start, expected):
    rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(data[start:start + 128], start))[:len(expected)]
    need([f"{i.mnemonic} {i.op_str}".strip() for i in rows] == expected, f"source semantics {start:X}")


def arm(data, start, end):
    return [f"{i.mnemonic} {i.op_str}" for i in Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[start:end], BASE + start)]


def literal(data, site):
    word = struct.unpack_from("<I", data, site)[0]
    need(word & 0x0FFF0000 == 0x059F0000, f"positive ARM literal at {site:X}")
    return struct.unpack_from("<I", data, site + 8 + (word & 0xFFF))[0]


def source_contract(gba, old, new):
    x86(new, 0x771F69, ["cmp word ptr [bp + 6], 5", "je 0x771f72", "jmp 0x771ff7"])
    x86(new, 0x771F84, ["cmp ax, 0xb", "pop ax", "je 0x771fa3",
                        "cmp byte ptr es:[0x5d], 3", "je 0x771fcd",
                        "cmp byte ptr es:[0x5d], 0", "je 0x771fa3",
                        "test word ptr es:[0x68], 0x400", "je 0x771fcd"])
    x86(new, 0x771FE3, ["push 0xff0", "push 0x71f0", "push 0xeea", "lcall 0x4fff, 0x980"])
    x86(new, 0x771FB9, ["push 0xff0", "push 0x71f0", "push 0x653", "lcall 0x4fff, 0x980"])
    x86(old, 0x3C157E, ["cmp byte ptr es:[0x5c], 7", "jne 0x3c158d",
                        "or word ptr es:[0x68], 0x200", "mov bx, 0x4e", "mov ax, 0x1000",
                        "mov es, ax", "xor ax, ax", "mov word ptr es:[bx + 0x21], ax"])
    x86(new, 0x77F9F8, ["cmp byte ptr es:[0x5c], 7", "jne 0x77fa07",
                        "or word ptr es:[0x68], 0x200", "cmp byte ptr es:[0x5c], 7",
                        "je 0x77fa1e", "cmp byte ptr es:[0x5c], 0xb", "je 0x77fa1e",
                        "or word ptr es:[0x68], 0x400"])
    need(arm(gba, 0xB9E48, 0xB9E78) == [
        "ldr r8, [pc, #0xd8]", "ldrb sb, [r8, #0xe]", "cmp sb, #7", "bne #0x80b9e68",
        "ldr r8, [pc, #0xcc]", "ldrh sb, [r8, #0x1a]", "orrs sb, sb, #0x200",
        "strh sb, [r8, #0x1a]", "ldr r1, [pc, #0xc0]", "subs r0, r0, r0",
        "strh r0, [r1, #0x22]", "b #0x80b9f0c"], "commercial progress producer lineage")
    need([literal(gba, p) for p in (0xB9E48, 0xB9E58, 0xB9E68)] == [0x03002310] * 3,
         "commercial producer physical globals")
    need(arm(gba, 0x33FCD8, 0x33FCE0) == ["cmp r8, #5", "bne #0x833fd24"], "native case5 boundary")
    need(arm(gba, 0x33FCFC, 0x33FD24) == ["bl #0x8011e7c", "add sp, sp, #0x10",
        "ldr r8, [pc, #0xa8]", "stmdb sp!, {r8}", "stmdb sp!, {fp}", "mov r8, #0xff0",
        "stmdb sp!, {r8}", "bl #0x8011ac4", "add sp, sp, #0xc", "b #0x833fd6c"],
         "single native case5 allocation")
    need(literal(gba, 0x33FD04) == 0x0834059C, "original case5 callback")
    return {"source_progress": "1000:0068", "native_progress": 0x0300232A,
            "native_stage": 0x0300231E, "native_difficulty": 0x0300231F,
            "single_allocation": 0x0833FD18, "source_callback": "71F0:0EEA", "native_callback": 0x085C8000}


def semantic_contract(data):
    need(arm(data, 0x5C9900, 0x5C9950) == [
        "push {r0, r1, ip, lr}", "mrs ip, apsr", "ldr r8, [pc, #0x48]", "ldr r0, [pc, #0x48]",
        "ldrb r1, [r0]", "cmp r1, #0xb", "beq #0x85c9944", "ldrb r1, [r0, #1]",
        "cmp r1, #3", "beq #0x85c9940", "cmp r1, #0", "beq #0x85c9944",
        "ldr r0, [pc, #0x28]", "ldrh r1, [r0]", "tst r1, #0x400", "bne #0x85c9944",
        "ldr r8, [pc, #0x1c]", "msr apsr_nzcvq, ip", "pop {r0, r1, ip, lr}", "b #0x833fd08"],
        "native case5 complete condition/ABI")
    need([literal(data, p) for p in (0x5C9908, 0x5C990C, 0x5C9930, 0x5C9940)] ==
         [0x0834059C, 0x0300231E, 0x0300232A, 0x085C8000], "case5 actual literal consumers")
    need(arm(data, 0x5C9A00, 0x5C9A40) == [
        "push {r0, r8, sb, ip, lr}", "mrs ip, apsr", "ldr r8, [pc, #0x38]", "ldrb sb, [r8]",
        "cmp sb, #7", "beq #0x85c9a30", "cmp sb, #0xb", "beq #0x85c9a30",
        "ldr r8, [pc, #0x24]", "ldrh sb, [r8]", "orr sb, sb, #0x400", "strh sb, [r8]",
        "ldr r1, [pc, #0x18]", "msr apsr_nzcvq, ip", "pop {r0, r8, sb, ip, lr}", "b #0x80b9e6c"],
        "native progress complete condition/ABI")
    need([literal(data, p) for p in (0x5C9A08, 0x5C9A20, 0x5C9A30)] ==
         [0x0300231E, 0x0300232A, 0x03002310], "progress actual literal consumers")
    # Capstone uses newer APSR aliases for these ARMv4 CPSR flag instructions.
    need(struct.unpack_from("<I", data, 0x5C9904)[0] == 0xE10FC000 and
         struct.unpack_from("<I", data, 0x5C9944)[0] == 0xE128F00C and
         struct.unpack_from("<I", data, 0x5C9A04)[0] == 0xE10FC000 and
         struct.unpack_from("<I", data, 0x5C9A34)[0] == 0xE128F00C, "ARM7 CPSR encoding")


def algebra_contract():
    selected = 0
    for stage in range(256):
        for difficulty in range(256):
            for flag in (0, 0x400):
                source = stage != 11 and (difficulty == 3 or (difficulty != 0 and flag == 0))
                # Direct Boolean reduction of the independently checked ARM
                # branch chain above; this does not execute ARM instructions.
                native = False
                if stage != 11:
                    if difficulty == 3:
                        native = True
                    elif difficulty != 0:
                        native = not bool(flag & 0x400)
                need(source == native, "all-byte selector algebra")
                selected += int(source)
    checks = 0
    for stage in (0, 7, 11, 255):
        for flags in range(65536):
            source = flags
            if stage == 7:
                source |= 0x200
            if stage != 7 and stage != 11:
                source |= 0x400
            inherited = flags | (0x200 if stage == 7 else 0)
            native = inherited if stage in (7, 11) else inherited | 0x400
            need(source == native and (native & ~0x600) == (flags & ~0x600), "word-preserving progress algebra")
            need((native & 0x200) == (inherited & 0x200), "existing0200 producer preserved")
            checks += 1
    return {"selector_cases": 256 * 256 * 2, "selected_cases": selected,
            "all_word_progress_cases": checks, "no_source_clamp": True,
            "all_noncase5_paths_unchanged": True}


def verify(before, after, originals, spec):
    for name, expected in HASHES.items():
        need(digest(originals[name]) == expected, f"original {name}")
    source = source_contract(originals["gba"], originals["wsc10"], originals["wsc15"])
    need(len(before) == len(after) == 0x800000, "ROM extent")
    need(set(spec) == {"input_sha256", "scene", "initializer"} and digest(before) == spec["input_sha256"], "exact route predecessor")
    for name, entry, maximum in (("scene", 0x085C8000, 0x100), ("initializer", 0x085C7800, 0x800)):
        row = spec[name]
        need(set(row) == {"entry", "bytes", "sha256"} and row["entry"] == entry, "dependency entry")
        size = row["bytes"]
        need(isinstance(size, int) and 40 <= size <= maximum and size % 4 == 0, "dependency span")
        payload = before[entry - BASE:entry - BASE + size]
        need(digest(payload) == row["sha256"] and payload[:4] not in (b"\xff" * 4, b"\x1e\xff\x2f\xe1"), "real hash-bound dependency")
    semantic_contract(after)
    allowed = set()
    spans = []
    for offset, code_size, size, expected in PROFILE:
        need(before[offset:offset + size] == b"\xff" * size, "route ownership FF")
        need(digest(after[offset:offset + size]) == expected, "complete route profile")
        need(len(arm(after, offset, offset + code_size)) == code_size // 4, "ARM instruction population")
        allowed.update(range(offset, offset + size))
        spans.append((offset, offset + size))
    for site in range(0, len(before), 4):
        value, = struct.unpack_from("<I", before, site)
        need(not any(BASE + a <= value & ~1 < BASE + z for a, z in spans), "prior literal references route")
        if value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            relative = value & 0xFFFFFF
            relative -= 0x1000000 if relative & 0x800000 else 0
            target = site + 8 + 4 * relative
            need(not any(a <= target < z for a, z in spans), "prior ARM branch references route")
    for site, original, target in HOOKS:
        need(struct.unpack_from("<I", before, site)[0] == original, "original hook word")
        need(arm(after, site, site + 4) == [f"b #{BASE + target:#x}"], "one-word hook target")
        allowed.update(range(site, site + 4))
    for a, z in ((0x33FCCC, 0x33FDC0), (0xB9E48, 0xB9E78)):
        restored = bytearray(after[a:z])
        for site, word, _ in HOOKS:
            if a <= site < z:
                struct.pack_into("<I", restored, site - a, word)
        need(bytes(restored) == originals["gba"][a:z] == before[a:z], "all existing case/progress flow preserved")
    changed = {i for i, (a, b) in enumerate(zip(before, after)) if a != b}
    need(changed <= allowed, "write outside exact route ownership")
    negatives = []
    for at, word, label in ((0x5C9914, 0xE3510007, "stage exclusion changed"),
                            (0x5C9920, 0xE3510002, "difficulty3 changed"),
                            (0x5C9938, 0xE3110C02, "0400 predicate changed"),
                            (0x5C9A28, 0xE3899C02, "0400 producer changed"),
                            (0x5C9A2C, 0xE5889000, "halfword write widened"),
                            (0x5C9944, 0xE1A00000, "CPSR restoration omitted")):
        bad = bytearray(after); struct.pack_into("<I", bad, at, word)
        try:
            semantic_contract(bad)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"ineffective semantic negative {label}")
    return {"result": "PASS", "kind": "independent-shoot-case5-route", "input_sha256": digest(before),
            "output_sha256": digest(after), "source_native_consumer": source, "algebra": algebra_contract(),
            "ARM_instructions": 36, "changed_bytes": len(changed), "semantic_negatives": negatives,
            "runtime_executed": False, "arbitrary_foreign_task_entry_proven": False}


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "dependencies"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    report = verify(args.before.read_bytes(), args.after.read_bytes(),
                    {name: getattr(args, name).read_bytes() for name in HASHES},
                    json.loads(args.dependencies.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-case5-route] independent PASS: {digest(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
