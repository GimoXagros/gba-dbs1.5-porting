#!/usr/bin/env python3
"""Correct Shoot constructor ABI and install the 7168 player-binding phase.

This is a dependent layer over exact v46, not a replacement converter or object
system.  The new phase implements WSC 4090:71D1..7394 and reuses the resident
auxiliary initializer *after* its allocator.  Its three object globals must
already be valid, as they are at this point in the source initializer.  The
outer 7168 preparation, remaining tail, menu and controller are not installed.
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
from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks  # type: ignore

INPUT_SHA256 = "034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000
PHASE = 0x5C1000
REUSE_AUX = 0x5C1300
HP_TABLE = 0x5C1400
OWNERSHIP_END = 0x5C1440
AUX_BODY = 0x085BC244
ACTIVE_SLOT = 0x030048A0  # WSC ES:065E
OTHER_SLOT = 0x0300489C   # WSC ES:065C
BATTLE_STATE = 0x03002310
ACTIVE_P1 = 0x085D0000
ACTIVE_P0 = 0x085D1000
ACTIVE_P2 = 0x085B9300
UPPER_ENTRY = 0x085BC800

# Intentional dependent writes: change the resource-producing LDRs, not the
# shared literals (the auxiliary P2 literal also feeds the direct P2 loader).
CORRECTIONS = (
    (0x5B94BC, 0xE59F80D8, 0xE59F80D0, "child constructor first resource is P1"),
    (0x5B94E4, 0xE59F80A8, 0xE59F80B0, "child constructor third resource is P2"),
    (0x5BC2D0, 0xE59F80D8, 0xE59F80D0, "aux constructor first resource is P1"),
    (0x5BC2F8, 0xE59F80A8, 0xE59F80B0, "aux constructor third resource is P2"),
    (0x5BC398, OTHER_SLOT, ACTIVE_SLOT, "aux primary link is source ES:065E"),
    (0x5BC39C, ACTIVE_SLOT, OTHER_SLOT, "aux secondary link is source ES:065C"),
)

ORACLES = (
    ("gba", 0x127E4, 0x1285C, "EF628791EF3580DEAD14EEC7400E44A43A696EF8012D62304FD0C7B6A45FD0C2", "native presentation constructor consumer"),
    ("gba", 0x36FD0C, 0x36FD64, "A02F2BC73BEDEDED8A924B4B6C3B5B6CE4E3BE7165A7948F016F176161DE54DA", "native player HP and field mapping"),
    ("gba", 0x37005C, 0x370068, "1766A4CE1E85AE346EF64F858610305D73B3F940CB76821229F8CB0078B77338", "native player and difficulty globals"),
    ("wsc10", 0x394897, 0x3948E3, "F92B5DEB079724307C7A2DD21B70DBB12137F677F58E356DD6E3517AE90A1A7F", "commercial source player setup"),
    ("wsc15", 0x747A68, 0x747E72, "F0F825AE96C188F14EA8ED89A78C18D9F5D752EAD123FE2C02FD0056AB51B8C3", "complete source initializer and tables"),
    ("wsc15", 0x743FC0, 0x7440C7, "A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6", "36C0 stage-manager setup, not a fighter allocator"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    if sha256(data) != expected:
        raise SystemExit(f"{label}: unexpected SHA-256 {sha256(data)}")


def assemble(source: str, offset: int) -> bytes:
    encoded, _ = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN).asm(source, GBA_BASE + offset)
    return bytes(encoded)


def player_phase() -> tuple[bytes, int]:
    # The native constructor reverses the WSC push sequence. Its entry SP
    # +48/+36/+24 carry P1/P0/P2, consumed at presentation +44/+48/+4C.
    source = f"""
        push {{r0-r12, lr}}
        ldr r8, active_slot
        ldr r4, [r8]
        ldr r8, other_slot
        ldr r7, [r8]
        ldrh r8, [r4, #4]
        orr r8, r8, #0x20
        strh r8, [r4, #4]

        ldrb r0, [r7, #0x11]
        lsl r0, r0, #1
        ldr r8, hp_table
        ldrh r1, [r8, r0]
        asr r2, r1, #2
        ldr r8, battle_state
        ldrb r3, [r8, #0xF]
        cmp r3, #0
        subeq r1, r1, r2
        beq hp_ready
        cmp r3, #2
        addhs r1, r1, r2
        cmp r3, #3
        addeq r1, r1, r2
    hp_ready:
        strh r1, [r4, #0x64]
        lsr r0, r1, #1
        strh r0, [r4, #0x68]
        lsr r0, r0, #1
        strh r0, [r4, #0x6A]
        mov r9, #0
        strh r9, [r4, #0x4E]
        strh r9, [r4, #0x50]
        ldrh r8, [r4, #4]
        bic r8, r8, #0xBC00
        strh r8, [r4, #4]
        strh r9, [r4, #0x34]
        strh r9, [r4, #0x36]
        strh r9, [r4, #0x42]
        strh r9, [r4, #0x44]
        strh r9, [r4, #0x46]
        strh r9, [r4, #0x48]
        mov r9, #0x10
        strh r9, [r4, #0x52]
        strh r9, [r4, #0x54]
        ldr r8, upper_entry
        str r8, [r4]

        add r5, r4, #0xAC
        push {{r5}}
        mov r8, #0
        push {{r8}}
        ldr r8, active_p1
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, active_p0
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, active_p2
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        mov r8, #0x4000
        push {{r8}}
        mov r8, #0x1800
        push {{r8}}
        ldr r8, active_tile_id
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x080127E4
        add sp, sp, #60
        ldrh r8, [r5, #8]
        orr r8, r8, #0x2000
        strh r8, [r5, #8]
        push {{r5}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        bl 0x08012874
        add sp, sp, #12
        ldr r8, active_p2
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        push {{r8}}
        mov r8, #1
        push {{r8}}
        bl 0x080132EC
        add sp, sp, #20

        bl 0x{GBA_BASE + REUSE_AUX:08X}
        str r7, [r4, #0x18]
        pop {{r0-r12, lr}}
        bx lr
        .align 2
    active_slot: .word 0x{ACTIVE_SLOT:08X}
    other_slot: .word 0x{OTHER_SLOT:08X}
    hp_table: .word 0x{GBA_BASE + HP_TABLE:08X}
    battle_state: .word 0x{BATTLE_STATE:08X}
    upper_entry: .word 0x{UPPER_ENTRY:08X}
    active_p1: .word 0x{ACTIVE_P1:08X}
    active_p0: .word 0x{ACTIVE_P0:08X}
    active_p2: .word 0x{ACTIVE_P2:08X}
    active_tile_id: .word 0x000001F1
    """
    blob = assemble(source, PHASE)
    return blob, len(blob) - 9 * 4


def verify_machine_code(blob: bytes, offset: int, code_bytes: int, externals: set[int]) -> dict[str, object]:
    """Check every generated ARM instruction, excluding declared literal data.

    Capstone/Keystone supply the ARM ISA, not a project-specific partial CPU.
    This verifies this code population; it does not claim ISA-wide validation.
    """
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    encoder = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN)
    instructions = list(decoder.disasm(blob[:code_bytes], GBA_BASE + offset))
    if sum(item.size for item in instructions) != code_bytes or any(item.size != 4 for item in instructions):
        raise SystemExit("generated ARM code is not fully decoded")
    branches, literals = [], []
    code_addresses = {item.address for item in instructions}
    for item in instructions:
        text = f"{item.mnemonic} {item.op_str}"
        encoded, _ = encoder.asm(text, item.address)
        if bytes(encoded) != item.bytes:
            raise SystemExit(f"ARM round-trip differs at {item.address:08X}: {text}")
        word = int.from_bytes(item.bytes, "little")
        if (word & 0x0E000000) == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            target = item.address + 8 + delta * 4
            if target not in code_addresses and target not in externals:
                raise SystemExit(f"undeclared branch target {target:08X}")
            branches.append({"site": item.address, "target": target})
        if (word & 0x0FFF0000) == 0x059F0000:
            target = item.address + 8 + (word & 0xFFF)
            if not GBA_BASE + offset + code_bytes <= target <= GBA_BASE + offset + len(blob) - 4:
                raise SystemExit(f"LDR literal escapes data region at {item.address:08X}")
            literals.append({"site": item.address, "target": target})
    return {"code_bytes": code_bytes, "instructions": len(instructions), "literal_bytes": len(blob) - code_bytes,
            "all_instruction_roundtrips_exact": True, "branches": branches, "literal_loads": literals}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    original = args.input.read_bytes()
    sources = {"gba": args.gba.read_bytes(), "wsc10": args.wsc10.read_bytes(), "wsc15": args.wsc15.read_bytes()}
    require_hash(original, INPUT_SHA256, "exact v46")
    for name, digest in (("gba", GBA_SHA256), ("wsc10", WSC10_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[name], digest, name)
    for name, start, end, digest, label in ORACLES:
        require_hash(sources[name][start:end], digest, label)
    for start, size, digest, label in (
        (0x5B9400, 420, "A3A8103CF0E20334F0B3B5189C5BA082F4596D306A07D2ADE492C1CA665FEA60", "original child constructor"),
        (0x5BC200, 436, "49D24F0D03A38A935E6FC9FA1AA0D43AFEB4EEAA9BFE7CC50FAD5A076422DC9E", "original aux constructor"),
        (0x5D0000, 668, "9672981DDE22024A89658FB9B68FFBB8C76EA5E4927D17D9CF549A90620996DA", "active P1"),
        (0x5D1000, 128, "04F248F48F22DC66BEB965ADBCB72DDA271534A5BE9A8EB0B5F04CB373BD97BB", "active P0"),
        (0x5B9300, 40, "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C", "active P2"),
    ):
        require_hash(original[start:start + size], digest, label)
    if len(original) != 0x800000 or original[PHASE:OWNERSHIP_END] != b"\xff" * (OWNERSHIP_END - PHASE):
        raise SystemExit("new phase ownership is not the declared unused expansion window")
    # Exclude known pre-existing code/data pointers as well as direct ARM B/BL.
    for site in range(0, len(original) - 3, 4):
        word = struct.unpack_from("<I", original, site)[0]
        if GBA_BASE + PHASE <= word < GBA_BASE + OWNERSHIP_END:
            raise SystemExit(f"pre-existing pointer into new window at {site:X}")
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            target = site + 8 + displacement * 4
            if PHASE <= target < OWNERSHIP_END:
                raise SystemExit(f"pre-existing ARM branch into new window at {site:X}")

    phase, code_bytes = player_phase()
    reuse = assemble(f"push {{r0-r7, lr}}; b 0x{AUX_BODY:08X}", REUSE_AUX)
    hp_table = sources["wsc15"][0x747E54:0x747E72]
    if PHASE + len(phase) > REUSE_AUX or len(reuse) != 8:
        raise SystemExit("new player phase exceeds placement bounds")
    code_report = {
        "player_phase": verify_machine_code(phase, PHASE, code_bytes, {0x080127E4, 0x08012874, 0x080132EC, GBA_BASE + REUSE_AUX}),
        "reuse_aux": verify_machine_code(reuse, REUSE_AUX, 8, {AUX_BODY}),
    }

    # Plan and validate *all* writes against immutable v46 before mutating.
    plan = [(site, struct.pack("<I", old), struct.pack("<I", new), label) for site, old, new, label in CORRECTIONS]
    plan.extend((site, b"\xff" * len(blob), blob, label) for site, blob, label in (
        (PHASE, phase, "source 71D1..7394 player and auxiliary binding"),
        (REUSE_AUX, reuse, "reuse existing auxiliary object without allocation"),
        (HP_TABLE, hp_table, "source fifteen-character HP table"),
    ))
    allowed: set[int] = set()
    for site, before, after, label in plan:
        if len(before) != len(after) or original[site:site + len(before)] != before:
            raise SystemExit(f"Expected Write precondition failed: {label}")
        owned = set(range(site, site + len(after)))
        if owned & allowed:
            raise SystemExit(f"overlapping Expected Writes: {label}")
        allowed |= owned
    output = bytearray(original)
    for site, _before, after, _label in plan:
        output[site:site + len(after)] = after
    changed = {site for site, (a, b) in enumerate(zip(original, output, strict=True)) if a != b}
    expected_changed = {site + i for site, before, after, _label in plan for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if changed != expected_changed or not changed <= allowed:
        raise SystemExit("final diff does not equal planned writes")
    result = {
        "schema": 1, "kind": "shoot-player-binding-dependent-integration",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(output), "output_bytes": len(output),
        "source_phase": {"entry": "4090:71D1", "end_exclusive": "4090:7394", "hp_table": "4090:7554..7572"},
        "native_entries": {"player_phase": GBA_BASE + PHASE, "reuse_aux": GBA_BASE + REUSE_AUX, "existing_aux_body": AUX_BODY},
        "abi": {"active_player_slot": ACTIVE_SLOT, "other_player_slot": OTHER_SLOT, "aux_slot": 0x03004D3C,
                "requires_preexisting_objects": True, "other_character_index_range": [0, 14],
                "constructor_entry_sp_offsets": {"p1": 48, "p0": 36, "p2": 24}},
        "expected_writes": [{"offset": site, "bytes": len(after), "label": label,
                             "before_sha256": sha256(before), "after_sha256": sha256(after)} for site, before, after, label in plan],
        "actual_changed_bytes": len(changed), "generated_code": code_report,
        "claim_scope": "static constructor-ABI and player-link corrections plus resident source player/auxiliary binding; no outer initializer, menu/controller entry, gameplay, emulator or supplied-save QA",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-player-binding] static build {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
