#!/usr/bin/env python3
"""Distinguish the Shoot SRAM stores from the retail regeneration timers.

Reads immutable ROM files only.  The algebraic counterexample is not a CPU
simulation or a claim that the complete scene reaches the example state.
This report supplements, and does not modify, the frozen boundary report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

HASHES = {
    "old": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "new": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
    "native": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
}
RANGES = {
    "old": ((0x3909FE, 0x390AB5), (0x390D6E, 0x390DA5),
            (0x391CAA, 0x391D0A), (0x392EC2, 0x392EF5),
            (0x391ED5, 0x391F25), (0x393185, 0x3931AF),
            (0x3988A8, 0x3988CC)),
    "new": ((0x7432E4, 0x743320), (0x7435B0, 0x7435DA),
            (0x747CD6, 0x747CF0)),
    "native": ((0x352B30, 0x352B78), (0x352CC0, 0x352CE0),
               (0x353040, 0x35308C), (0x3530B8, 0x3530BC)),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def anchor(blob: bytes, raw: int, expected: list[str], arm: bool = False) -> None:
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86,
                 CS_MODE_ARM if arm else CS_MODE_16)
    rows = list(decoder.disasm(blob[raw:raw + 256], raw + (0x08000000 if arm else 0)))[:len(expected)]
    actual = [f"{i.mnemonic} {i.op_str}".strip() for i in rows]
    need(actual == expected, f"instruction contract changed at {raw:06X}: {actual}")


def semantic_contract(blobs: dict[str, bytes]) -> dict:
    old, new, native = (blobs[x] for x in ("old", "new", "native"))
    # Normal single-player entry establishes SRAM DS.  All three imported
    # preparation helpers save and restore it before this initializer call.
    anchor(old, 0x3909FE, ["mov ax, 0x1000", "mov ds, ax"])
    anchor(old, 0x390A73, ["push 0", "lcall 0x96b2, 0x1d88", "add sp, 2",
                           "lcall 0x9070, 0x15aa", "lcall 0x9070, 0x66e"])
    for begin, end in ((0x3988AC, 0x3988C6), (0x391CAF, 0x391D03),
                       (0x390D6F, 0x390DA2)):
        anchor(old, begin, ["push ds"])
        anchor(old, end, ["pop ds"])
    anchor(old, 0x390AB0, ["lcall 0x9070, 0x27c2", "add sp, 0xa"])
    anchor(old, 0x392EC2, ["push bp", "mov bp, sp", "push ax", "push bx", "push si",
                           "push di", "push es", "push ds", "mov ax, word ptr [bp + 0xe]",
                           "mov byte ptr [0x352], al", "mov word ptr [0x5e4], 0",
                           "mov word ptr [0x5e8], 0", "mov word ptr [0x3cb0], 0",
                           "mov word ptr [0x3cb2], 0", "mov word ptr [0x3cb4], 4",
                           "mov word ptr [0x3cb6], 4"])
    old_calls = [i for i in range(len(old) - 4) if old[i:i + 5] == bytes.fromhex("9AC2277090")]
    need(old_calls == [0x390AB0, 0x390AF9, 0x390B17, 0x390B35], "old initialization call inventory")

    anchor(new, 0x7432ED, ["mov ax, 0xc00", "mov es, ax", "mov ax, word ptr [bp + 0xe]",
                           "mov byte ptr [0x3cc], al", "mov word ptr [0x660], 0",
                           "mov word ptr [0x664], 0", "mov word ptr es:[0x3cd8], 0",
                           "mov word ptr es:[0x3cda], 0", "mov word ptr es:[0x3cdc], 4",
                           "mov word ptr es:[0x3cde], 4"])
    anchor(new, 0x747CD6, ["mov ax, 0x1000", "mov es, ax",
                           "mov word ptr es:[0x660], 0", "mov word ptr es:[0x3cd8], 0",
                           "mov word ptr es:[0x3cda], 0"])
    anchor(old, 0x391EDB, ["mov ax, 0xc00", "mov dx, 0x1000", "mov ds, ax", "mov es, dx"])
    anchor(old, 0x391F20, ["lcall 0x9070, 0x28b5"])
    anchor(old, 0x393185, ["cmp word ptr [si + 0x56], 0x60", "je 0x3931a9", "xor bx, bx",
                           "mov bl, byte ptr [si + 0x10]", "shl bx, 1", "cmp word ptr [bx + 0x3cb0], 0",
                           "je 0x3931a0", "dec word ptr [bx + 0x3cb0]", "jmp 0x3931a9",
                           "inc word ptr [si + 0x56]", "mov word ptr [bx + 0x3cb0], 3"])
    anchor(new, 0x7435B0, ["cmp word ptr [si + 0x56], 0x60", "je 0x7435d4", "xor bx, bx",
                           "mov bl, byte ptr [si + 0x10]", "shl bx, 1", "cmp word ptr [bx + 0x3cd8], 0",
                           "je 0x7435cb", "dec word ptr [bx + 0x3cd8]", "jmp 0x7435d4",
                           "inc word ptr [si + 0x56]", "mov word ptr [bx + 0x3cd8], 3"])
    anchor(native, 0x353040, ["ldrsh r8, [r4, #0x6a]", "cmp r8, #0x60", "beq #0x8353084",
                              "ldrb r1, [r4, #0x10]", "lsl r1, r1, #1", "ldr r8, [pc, #0x5c]",
                              "ldrsh sb, [r1, r8]", "cmp sb, #0", "beq #0x8353070",
                              "sub sb, sb, #1", "strh sb, [r1, r8]", "b #0x8353084",
                              "mov sb, #3", "strh sb, [r1, r8]", "ldrsh sb, [r4, #0x6a]",
                              "add sb, sb, #1", "strh sb, [r4, #0x6a]"], True)
    need(struct.unpack_from("<I", native, 0x3530B8)[0] == 0x030048AC, "native regeneration timer pointer")
    need(struct.unpack_from("<6I", native, 0x352CC4) == (0x03004528, 0x030048A4, 0x030048A8,
                                                          0x030048AC, 0x030048AE, 0x030048B0),
         "retail initializer pointer lineage")
    need(struct.unpack_from("<I", native, 0x352CDC)[0] == 0x030048B2, "second drain timer pointer")
    return {"old_initialization_direct_calls": old_calls,
            "old_normal_entry_DS": 0x1000, "old_initializer_words": [0x3CB0, 0x3CB2, 0x3CB4, 0x3CB6],
            "new_common_initializer_ES": 0x0C00, "new_shoot_initializer_ES": 0x1000,
            "native_regeneration_timers": [0x030048AC, 0x030048AE],
            "regeneration_state_fields": {"source": 0x56, "native": 0x6A},
            "ordinary_timer_linear": [0xFCD8, 0xFCDA], "Shoot_store_linear": [0x13CD8, 0x13CDA],
            "ordinary_timer_to_Shoot_store_alias": False,
            "old_consumer_precondition": "task dispatcher DS=0C00; object callback must return with the native task ABI intact"}


def algebra() -> dict:
    # Exact finite branch formulas, independently written from the inspected
    # instructions.  No CPU state or source instruction stream is executed.
    def unchanged_timer_step(timer: int, charge: int) -> tuple[int, int]:
        if charge == 0x60:
            return timer, charge
        if timer:
            return (timer - 1) & 0xFFFF, charge
        return 3, (charge + 1) & 0xFFFF

    differences = sum(unchanged_timer_step(timer, 0) != unchanged_timer_step(0, 0)
                      for timer in range(65536))
    need(differences == 65535, "counterexample population")
    return {"initial_regeneration_timer": 1, "initial_charge": 0,
            "source_SRAM_store_then_ordinary_consumer": list(unchanged_timer_step(1, 0)),
            "incorrect_native_timer_clear_then_consumer": list(unchanged_timer_step(0, 0)),
            "charge_zero_timer_domain": 65536, "differing_timer_values": differences,
            "scope": "disproves unconditional state aliasing; does not prove the complete Shoot entry reaches this particular state"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wsc10", type=Path)
    parser.add_argument("wsc15", type=Path)
    parser.add_argument("gba", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    blobs = {name: path.read_bytes() for name, path in (("old", args.wsc10), ("new", args.wsc15), ("native", args.gba))}
    for name, blob in blobs.items():
        need(digest(blob) == HASHES[name], f"immutable {name} input mismatch")
    facts = semantic_contract(blobs)
    rejected = []
    for name, raw, replacement, label in (
        ("new", 0x747CD7, bytes.fromhex("000C"), "Shoot segment changed to ordinary IRAM"),
        ("new", 0x7432EE, bytes.fromhex("0010"), "common segment changed to SRAM"),
        ("old", 0x392EDF, bytes.fromhex("D83C"), "old high-field offset conflated with new one"),
        ("native", 0x3530B8, struct.pack("<I", 0x030048A4), "regen timer replaced with other fighter cache"),
        ("native", 0x353070, struct.pack("<I", 0xE3A09004), "native regen delay changed"),
    ):
        altered = dict(blobs)
        data = bytearray(altered[name]); data[raw:raw + len(replacement)] = replacement
        altered[name] = bytes(data)
        try:
            semantic_contract(altered)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError(f"semantic mutation accepted: {label}")
    report = {"schema": 1, "result": "DISTINCT_STATE_IDENTITY_CONFIRMED_MAPPING_UNRESOLVED",
              "immutable_inputs": HASHES, "facts": facts, "alias_counterexample": algebra(),
              "range_sha256": {name: [{"start": a, "end": z, "sha256": digest(blobs[name][a:z])}
                                       for a, z in rows] for name, rows in RANGES.items()},
              "semantic_mutations_rejected": rejected, "native_storage_mapping_proven": False,
              "source_store_elimination_authorized": False, "new_ROM_code_installed": False,
              "no_emulator_CPU_execution_or_save_access": True,
              "limitations": ["No claim that the original DS choice was accidental or intentional.",
                              "No global or first-milestone no-observer claim.",
                              "Existing native regen timers cannot represent both distinct source regions.",
                              "A dedicated representation would need its own positive ownership and persistence contract."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "output": str(args.output), "sha256": digest(args.output.read_bytes()),
                      "semantic_mutations_rejected": len(rejected)}, sort_keys=True))


if __name__ == "__main__":
    main()
