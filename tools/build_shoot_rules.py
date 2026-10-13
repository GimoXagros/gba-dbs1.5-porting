#!/usr/bin/env python3
"""Install resident native components of the Shoot 9908 rules controller.

SELECT uses the commercial object/RNG ABI and returns an action token in r0.
APPLY consumes that token and three caller-supplied native callback addresses.
There is deliberately no wrapper, external caller, or pointer to an absent
callback. The existing 5C0A00 boundary remains unchanged. A future controller
adapter must call SELECT then APPLY without allowing intervening game updates.
This is static resident implementation, not the complete 43-callback graph.
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
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore
from capstone.arm_const import (ARM_INS_ADD, ARM_INS_AND, ARM_INS_B, ARM_INS_BL, ARM_INS_BX,
                               ARM_INS_CMP, ARM_INS_LDR, ARM_INS_LDRB, ARM_INS_LDRH,
                               ARM_INS_LDRSB, ARM_INS_MOV, ARM_INS_POP, ARM_INS_PUSH,
                               ARM_INS_STR, ARM_INS_STRH, ARM_INS_TST)  # type: ignore
from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks  # type: ignore

INPUT_SHA256 = "C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
SELECT, APPLY, ACTION_TABLE = 0x5C6000, 0x5C6200, 0x5C6400
OWNERSHIP_START, OWNERSHIP_END = 0x5C6000, 0x5C6500
NATIVE_RNG = 0x08012600
DIFFICULTY = 0x0300231F
SHOOT_FLAGS = 0x0300450A
PARENT_9083 = 0x085BA800
SOURCE_ACTIONS = {0x99EF: 0, 0x99F1: 1, 0x9A0E: 2, 0x9A1B: 3}

ORACLES = (
    ("wsc15", 0x74A208, 0x74A345, "25FB35105253832BDC2377094FE7EDFB3B75F459026B4D4473913C7EE773CEF4", "9908 controller, complete table and four tails"),
    ("gba", 0x12600, 0x12634, "D9F67CD6F116DA2F351D422534A7A4ECDB221075D07B3EDF50326CEDC738C9C9", "native RNG state, return and clobbers"),
    ("gba", 0x370104, 0x37027C, "1A5045070C97CB3DD6956359C517C6D59D850CC9A4D7144D985F53C55994E385", "commercial timer field +76"),
    ("wsc10", 0x394AE4, 0x394BB3, "D895190DA850CA7CF33BC59C5D6662C7643D37327DC5CF3F853F8CA402ABE05A", "commercial timer field +62"),
    ("gba", 0x36FD0C, 0x36FD64, "A02F2BC73BEDEDED8A924B4B6C3B5B6CE4E3BE7165A7948F016F176161DE54DA", "native HP and difficulty consumers"),
    ("wsc10", 0x394897, 0x3948E3, "F92B5DEB079724307C7A2DD21B70DBB12137F677F58E356DD6E3517AE90A1A7F", "commercial HP and difficulty consumers"),
    ("gba", 0x372148, 0x3721B8, "560C27100FB098E03A01BA6C9D0B492AF6D107C90BC4BA3E935BAD95267D3965", "native scratch field +A2"),
    ("wsc10", 0x395FFB, 0x396052, "A89E01B66D975DD69F96827062073FBE07127933A484D9E6029871696138001C", "commercial scratch field +8C"),
    ("gba", 0x37273C, 0x372920, "7E087397E772C0293D458FBFEAB13FF3BC04DFD42D90F44AE453738C8CEF4B7C", "native primary/secondary links and coordinates"),
    ("wsc15", 0x751CA5, 0x751CC4, "88EEFFEA0DC972C95542E1E6DFEB49257816DC24A86D06C1D7FDBF0B0A6FF1B5", "source RNG recurrence and consumed low bits"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    if sha256(data) != expected:
        raise ValueError(f"{label}: unexpected SHA-256 {sha256(data)}")


def assemble(source: str, offset: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(source, BASE + offset)
    return bytes(encoded)


def selector() -> tuple[bytes, int]:
    """r4=current native object; return r0=0..3, preserve r1-r12 and SP.

    The only persistent change is the native RNG's two-halfword state advance,
    zero times when object+76 != 0 and exactly once on every other path.
    Source unsigned X/Y comparisons and *signed byte* difficulty are retained.
    """
    blob = assemble(f"""
        push {{r1-r12, lr}}
        ldrh r0, [r4, #0x76]
        cmp r0, #0
        bne auxiliary
        ldr r8, [r4, #0x18]
        ldrh r6, [r8, #0x34]
        ldrh r7, [r8, #0x36]
        cmp r6, #0x500
        blo by_difficulty
        cmp r6, #0x900
        bhi by_difficulty
        bl 0x{NATIVE_RNG:08X}
        and r0, r0, #3
        cmp r0, #0
        beq paired
        cmp r7, #0xC00
        blo parent_guard
        b auxiliary
    by_difficulty:
        ldr r8, difficulty
        ldrsb r6, [r8]
        cmp r6, #3
        movgt r6, #3
        cmp r6, #0
        movlt r6, #0
        bl 0x{NATIVE_RNG:08X}
        and r0, r0, #15
        add r0, r0, r6, lsl #4
        ldr r8, action_table
        ldrb r0, [r8, r0]
        cmp r0, #3
        bne done
    parent_guard:
        ldr r8, shoot_flags
        ldrh r0, [r8]
        tst r0, #0x40
        moveq r0, #3
        movne r0, #2
        b done
    paired:
        mov r0, #1
        b done
    auxiliary:
        mov r0, #2
    done:
        pop {{r1-r12, lr}}
        bx lr
        .align 2
    difficulty: .word 0x{DIFFICULTY:08X}
    action_table: .word 0x{BASE + ACTION_TABLE:08X}
    shoot_flags: .word 0x{SHOOT_FLAGS:08X}
    """, SELECT)
    return blob, len(blob) - 12


def application() -> tuple[bytes, int]:
    """Apply SELECT's action using a same-update native object snapshot.

    r0=action; r1=810D callback; r2=8AB8 callback; r3=8CDD callback;
    r4=current object. All r0-r12 and SP are preserved; CPSR is scratch.
    The three callback live-ins must be valid implemented native addresses.
    No caller meets that contract yet, so this routine remains uncalled.
    """
    blob = assemble(f"""
        push {{r8-r9}}
        cmp r0, #0
        beq done
        ldr r9, [r4, #0x28]
        cmp r0, #1
        beq paired
        cmp r0, #2
        streq r3, [r9]
        beq done
        ldr r8, parent
        str r8, [r9]
        b done
    paired:
        str r1, [r4]
        ldrh r8, [r4, #0x64]
        strh r8, [r4, #0xA2]
        str r2, [r9]
    done:
        pop {{r8-r9}}
        bx lr
        .align 2
    parent: .word 0x{PARENT_9083:08X}
    """, APPLY)
    return blob, len(blob) - 4


def verify_machine_code(blob: bytes, offset: int, code_bytes: int) -> dict:
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    encoder = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN)
    instructions = list(decoder.disasm(blob[:code_bytes], BASE + offset))
    if len(instructions) * 4 != code_bytes or any(i.size != 4 for i in instructions):
        raise ValueError("incomplete final ARM instruction population")
    addresses = {i.address for i in instructions}
    armv4t_ids = {ARM_INS_ADD, ARM_INS_AND, ARM_INS_B, ARM_INS_BL, ARM_INS_BX,
                  ARM_INS_CMP, ARM_INS_LDR, ARM_INS_LDRB, ARM_INS_LDRH,
                  ARM_INS_LDRSB, ARM_INS_MOV, ARM_INS_POP, ARM_INS_PUSH,
                  ARM_INS_STR, ARM_INS_STRH, ARM_INS_TST}
    branches = []
    for item in instructions:
        encoded, _ = encoder.asm(f"{item.mnemonic} {item.op_str}", item.address)
        if bytes(encoded) != item.bytes:
            raise ValueError(f"ARM round trip differs at {item.address:X}")
        word = int.from_bytes(item.bytes, "little")
        # All generated code uses base ARMv4T instructions; no Thumb, extended
        # multiply, saturating, coprocessor or ARMv5+ opcode is emitted.
        if item.id not in armv4t_ids:
            raise ValueError("out-of-profile ARM opcode")
        if word & 0x0E000000 == 0x0A000000:
            disp = word & 0xFFFFFF
            if disp & 0x800000:
                disp -= 0x1000000
            target = item.address + 8 + 4 * disp
            if target not in addresses and target != NATIVE_RNG:
                raise ValueError(f"undeclared branch target {target:X}")
            branches.append({"site": item.address, "target": target})
        if word & 0x0FFF0000 == 0x059F0000:
            literal = item.address + 8 + (word & 0xFFF)
            if not BASE + offset + code_bytes <= literal <= BASE + offset + len(blob) - 4:
                raise ValueError("PC literal leaves declared literal pool")
    return {"code_bytes": code_bytes, "instructions": len(instructions),
            "literal_bytes": len(blob) - code_bytes, "all_instruction_roundtrips_exact": True,
            "profile": "ARM7TDMI ARMv4T, 32-bit ARM, little-endian", "branches": branches}


def aligned_refs(data: bytes) -> list[dict[str, int]]:
    return [{"offset": i, "value": v} for i in range(0, len(data) - 3, 4)
            if BASE + OWNERSHIP_START <= (v := struct.unpack_from("<I", data, i)[0]) < BASE + OWNERSHIP_END]


def inbound_arm_branches(data: bytes) -> list[dict[str, int]]:
    refs = []
    for site in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, site)[0]
        if value >> 28 == 15 or value & 0x0E000000 != 0x0A000000:
            continue
        delta = value & 0xFFFFFF
        if delta & 0x800000:
            delta -= 0x1000000
        target = site + 8 + delta * 4
        if OWNERSHIP_START <= target < OWNERSHIP_END:
            refs.append({"site": site, "target": target})
    return refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    before = args.input.read_bytes()
    require_hash(before, INPUT_SHA256, "exact v50 predecessor")
    sources = {name: getattr(args, name).read_bytes() for name in ("gba", "wsc10", "wsc15")}
    for name, digest in (("gba", GBA_SHA256), ("wsc10", WSC10_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[name], digest, name)
    for name, start, end, digest, label in ORACLES:
        require_hash(sources[name][start:end], digest, label)
    if len(before) != 0x800000 or before[OWNERSHIP_START:OWNERSHIP_END] != b"\xFF" * (OWNERSHIP_END - OWNERSHIP_START):
        raise ValueError("rules ownership interval is not blank expanded ROM")
    if aligned_refs(before):
        raise ValueError("pre-existing aligned pointer reaches rules interval")
    if inbound_arm_branches(before):
        raise ValueError("pre-existing ARM B/BL reaches rules interval")
    source_table = struct.unpack_from("<64H", sources["wsc15"], 0x74A26F)
    if set(source_table) != set(SOURCE_ACTIONS):
        raise ValueError("source controller table contains an unresolved target")
    table = bytes(SOURCE_ACTIONS[value] for value in source_table)
    select, select_code = selector()
    apply, apply_code = application()
    code = [verify_machine_code(select, SELECT, select_code), verify_machine_code(apply, APPLY, apply_code)]
    plan = [(SELECT, select, "9908-decision"), (APPLY, apply, "controller-action-application"),
            (ACTION_TABLE, table, "source-64-entry-action-table")]
    for (start, blob, label), (next_start, _, _) in zip(plan, plan[1:]):
        if start + len(blob) > next_start:
            raise ValueError(f"Expected Writes overlap: {label}")
    if plan[-1][0] + len(plan[-1][1]) > OWNERSHIP_END:
        raise ValueError("rules payload leaves ownership interval")
    # Compute and validate every write against immutable predecessor first.
    writes = []
    allowed: set[int] = set()
    for start, blob, label in plan:
        old = before[start:start + len(blob)]
        if old != b"\xFF" * len(blob):
            raise ValueError(f"Expected Write source mismatch: {label}")
        allowed.update(range(start, start + len(blob)))
        writes.append({"label": label, "target": start, "bytes": len(blob),
                       "before_sha256": sha256(old), "after_sha256": sha256(blob)})
    after = bytearray(before)
    for start, blob, _ in plan:
        after[start:start + len(blob)] = blob
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if not changed or not changed <= allowed or after[0x5C0A00:0x5C0A04] != bytes.fromhex("1EFF2FE1"):
        raise ValueError("unexplained final diff or controller boundary changed")
    report = {"schema": 1, "kind": "shoot-resident-controller-components",
              "input_sha256": INPUT_SHA256, "output_sha256": sha256(after), "output_bytes": len(after),
              "source_guards": ORACLES, "expected_writes": writes, "machine_code": code,
              "changed_bytes": len(changed), "ownership": [OWNERSHIP_START, OWNERSHIP_END],
              "preexisting_aligned_pointers": [], "preexisting_arm_branches": [],
              "entries": {"select": BASE + SELECT, "apply": BASE + APPLY},
              "actions": {"0": "idle", "1": "810D and 8AB8", "2": "8CDD", "3": "9083"},
              "select_live_in": "r4=current native object; its +18 target link is valid when +76 is zero",
              "select_live_out": "r0=action 0..3, r1-r12/SP preserved; CPSR scratch; native RNG advances 0 or 1 times",
              "apply_live_in": "r0=select action; r1/r2/r3=implemented 810D/8AB8/8CDD native callbacks; r4=same object; no intervening game update or object/link mutation",
              "apply_live_out": "r0-r12/SP preserved; CPSR scratch; only selected source-equivalent object stores",
              "external_entry_connected": False, "controller_boundary_preserved": True,
              "unimplemented": ["810D", "8AB8", "8CDD", "remaining lower graph", "controller wrapper", "menu entry"],
              "claim_scope": "resident finite controller components only; no complete controller, gameplay, palette lifetime or runtime claim"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-rules] output SHA-256 {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
