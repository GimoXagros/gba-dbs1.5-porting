#!/usr/bin/env python3
"""Bound the WSC 1.5 Digimon Shoot upper player-state graph.

The dedicated initializer at 4090:7168 assigns 4090:7792 to the active player
and 4090:88F6 to the rules object.  A later common battle-transition branch
special-cases stage 11 and assigns 4090:7AB1/7D8D to the linked players.  This
walker follows direct control flow and compiler-shaped callback assignments
from both populations, but deliberately stops at calls to controller 9908.
The existing rules graph owns 9908 and everything below it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys
from collections import Counter, deque


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import (  # type: ignore
    CS_ARCH_X86,
    CS_MODE_16,
    CS_OP_IMM,
    CS_OP_MEM,
    CS_OP_REG,
    Cs,
)


WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
GBA_BASE = 0x08000000
OBJECT_OVERLAY_BASE = 0x740900
OBJECT_OVERLAY_SEGMENT = 0x4090
TRANSITION_OVERLAY_BASE = 0x75EEA0
TRANSITION_OVERLAY_SEGMENT = 0x5EEA
ROOT_INIT_RAW_START = 0x747A68
ROOT_INIT_RAW_END = 0x747E72
ROOT_INIT_SHA256 = "F0F825AE96C188F14EA8ED89A78C18D9F5D752EAD123FE2C02FD0056AB51B8C3"
MENU_ENTRY_CALL_RAW = 0x773143
STAGE11_ENTRY_RAW_START = 0x760197
STAGE11_ENTRY_RAW_END = 0x760204
ACTIVE_SEEDS = (0x7792, 0x88F6)
TRANSITION_SEEDS = (0x7AB1, 0x7D8D)
SEEDS = ACTIVE_SEEDS + TRANSITION_SEEDS
CONTROLLER_ENTRY = 0x9908
NATIVE_RNG = 0x08012600
NATIVE_RNG_RANGE = (0x12600, 0x12630)
NATIVE_RNG_SHA256 = "D33F9308DE9A71E08248449130A46E5EC22EA574A26C75E6BF228EC0A929BA65"
NATIVE_RNG_ORACLE_RANGE = (0x91180, 0x911A4)
NATIVE_RNG_ORACLE_SHA256 = "5B72097136205113AC7A9C4A026421C87C54C011C6902730D1E63D3CCF4C91CF"
NATIVE_RNG_ORACLE_CALLS = (0x91180, 0x91188, 0x91190, 0x91198)

ROOT_CALLBACK_ASSIGNMENTS = (
    (0x747B63, 0x7792),
    (0x747BD4, 0x88F6),
)

STAGE11_ENTRY_BYTES = bytes.fromhex(
    "26 80 3E 5C 00 0B 74 4D 26 80 3E 5D 00 03 74 2B "
    "26 80 3E 5D 00 00 74 09 26 F7 06 68 00 00 04 74 1A "
    "8B C7 C7 05 9A 64 C7 45 02 90 40 8B 7D 1C C7 05 0E 56 "
    "C7 45 02 90 40 E9 31 00 8B C7 C7 05 9A 64 C7 45 02 "
    "90 40 8B 7D 1C C7 05 36 57 C7 45 02 90 40 E9 17 00 "
    "8B C7 C7 05 B1 7A C7 45 02 90 40 8B 7D 1C C7 05 8D 7D "
    "C7 45 02 90 40 07"
)
STAGE11_CALLBACK_ASSIGNMENTS = (
    (0x7601EE, 0x7AB1),
    (0x7601FA, 0x7D8D),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def decode_one(engine: Cs, bank: bytes, address: int):
    if not 0 <= address < len(bank):
        return None
    return next(engine.disasm(bank[address:min(len(bank), address + 16)], address, 1), None)


def direct_target(instruction) -> int | None:
    if len(instruction.operands) == 1 and instruction.operands[0].type == CS_OP_IMM:
        return instruction.operands[0].imm & 0xFFFF
    return None


def callback_assignment(engine: Cs, bank: bytes, instruction) -> int | None:
    """Recognize a same-overlay far callback store rooted at this instruction."""
    if instruction.mnemonic != "mov" or len(instruction.operands) != 2:
        return None
    destination, source = instruction.operands
    if destination.type == CS_OP_MEM and source.type == CS_OP_IMM:
        if destination.mem.disp != 0:
            return None
        target = source.imm & 0xFFFF
        following = decode_one(engine, bank, instruction.address + instruction.size)
        if following is None or following.mnemonic != "mov" or len(following.operands) != 2:
            return None
        next_destination, next_source = following.operands
        if next_destination.type != CS_OP_MEM or next_source.type != CS_OP_IMM:
            return None
        if next_destination.mem.disp != 2:
            return None
        if (next_source.imm & 0xFFFF) != OBJECT_OVERLAY_SEGMENT:
            return None
        return target

    if destination.type != CS_OP_REG or source.type != CS_OP_IMM:
        return None
    target = source.imm & 0xFFFF
    following = decode_one(engine, bank, instruction.address + instruction.size)
    if following is None or following.mnemonic != "mov" or len(following.operands) != 2:
        return None
    stored_destination, stored_source = following.operands
    if stored_destination.type != CS_OP_MEM or stored_source.type != CS_OP_REG:
        return None
    if stored_destination.mem.disp != 0 or stored_source.reg != destination.reg:
        return None
    segment_store = decode_one(engine, bank, following.address + following.size)
    if segment_store is None or segment_store.mnemonic != "mov":
        return None
    if len(segment_store.operands) != 2:
        return None
    segment_destination, segment_source = segment_store.operands
    if segment_destination.type != CS_OP_MEM or segment_source.type != CS_OP_IMM:
        return None
    if segment_destination.mem.disp != 2:
        return None
    if (segment_source.imm & 0xFFFF) != OBJECT_OVERLAY_SEGMENT:
        return None
    return target


def contiguous_ranges(addresses: set[int]) -> list[tuple[int, int]]:
    if not addresses:
        return []
    ordered = sorted(addresses)
    result = []
    start = previous = ordered[0]
    for address in ordered[1:]:
        if address != previous + 1:
            result.append((start, previous + 1))
            start = address
        previous = address
    result.append((start, previous + 1))
    return result


def arm_branch_target(address: int, word: int) -> int:
    if word & 0x0F000000 != 0x0B000000:
        raise SystemExit(f"expected ARM BL at 0x{address:08X}")
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def require_native_rng(gba: bytes) -> dict[str, object]:
    start, end = NATIVE_RNG_RANGE
    if sha256(gba[start:end]) != NATIVE_RNG_SHA256:
        raise SystemExit("native GBA random routine changed")
    oracle_start, oracle_end = NATIVE_RNG_ORACLE_RANGE
    if sha256(gba[oracle_start:oracle_end]) != NATIVE_RNG_ORACLE_SHA256:
        raise SystemExit("native GBA random call-site oracle changed")
    targets = []
    for offset in NATIVE_RNG_ORACLE_CALLS:
        word = struct.unpack_from("<I", gba, offset)[0]
        targets.append(arm_branch_target(GBA_BASE + offset, word))
    if targets != [NATIVE_RNG] * len(NATIVE_RNG_ORACLE_CALLS):
        raise SystemExit("native GBA random call targets changed")
    if struct.unpack_from("<I", gba, 0x9119C)[0] != 0xE2000007:
        raise SystemExit("native GBA random-mask oracle changed")
    return {
        "wsc15_import": "4FFF:1CB5",
        "gba_entry": NATIVE_RNG,
        "gba_entry_range": [start, end],
        "gba_entry_sha256": NATIVE_RNG_SHA256,
        "commercial_oracle_range": [oracle_start, oracle_end],
        "commercial_oracle_sha256": NATIVE_RNG_ORACLE_SHA256,
        "commercial_oracle_calls": [GBA_BASE + offset for offset in NATIVE_RNG_ORACLE_CALLS],
        "role_proof": (
            "both ABIs call without arguments and consume the returned integer through "
            "small bit masks; the commercial GBA oracle calls 08012600 four times and "
            "masks the fourth result by 7"
        ),
        "claim": "platform-native random-role/ABI binding, not identical PRNG-sequence parity",
    }


def require_callback_assignments(
    rom: bytes, rows: tuple[tuple[int, int], ...], *, coordinate: str
) -> list[dict[str, int]]:
    assignments = []
    for raw, target in rows:
        expected = bytes.fromhex("C7 04") + struct.pack("<H", target) + bytes.fromhex(
            "C7 44 02 90 40"
        )
        if rom[raw:raw + len(expected)] != expected:
            raise SystemExit(f"callback assignment changed at 0x{raw:X}")
        assignments.append({
            "raw_address": raw,
            coordinate: raw - OBJECT_OVERLAY_BASE,
            "target_segment": OBJECT_OVERLAY_SEGMENT,
            "target_offset": target,
        })
    return assignments


def require_root_initializer(rom: bytes) -> list[dict[str, int]]:
    if sha256(rom[ROOT_INIT_RAW_START:ROOT_INIT_RAW_END]) != ROOT_INIT_SHA256:
        raise SystemExit("Shoot root initializer range changed")
    if rom[MENU_ENTRY_CALL_RAW:MENU_ENTRY_CALL_RAW + 5] != bytes.fromhex(
        "9A 68 71 90 40"
    ):
        raise SystemExit("Shoot menu entry no longer calls 4090:7168")
    return require_callback_assignments(
        rom, ROOT_CALLBACK_ASSIGNMENTS, coordinate="object_overlay_offset"
    )


def require_stage11_entry(rom: bytes) -> list[dict[str, int]]:
    actual = rom[STAGE11_ENTRY_RAW_START:STAGE11_ENTRY_RAW_END]
    if actual != STAGE11_ENTRY_BYTES:
        raise SystemExit("stage-11 object-transition entry signature changed")
    assignments = []
    for raw, target in STAGE11_CALLBACK_ASSIGNMENTS:
        expected = bytes.fromhex("C7 05") + struct.pack("<H", target) + bytes.fromhex(
            "C7 45 02 90 40"
        )
        if rom[raw:raw + len(expected)] != expected:
            raise SystemExit(f"stage-11 callback assignment changed at 0x{raw:X}")
        assignments.append({
            "raw_address": raw,
            "transition_overlay_offset": raw - TRANSITION_OVERLAY_BASE,
            "target_segment": OBJECT_OVERLAY_SEGMENT,
            "target_offset": target,
        })
    return assignments


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.wsc15.read_bytes()
    gba = args.gba.read_bytes()
    if sha256(rom) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    if sha256(gba) != GBA_SHA256:
        raise SystemExit("refusing unknown USA GBA source")
    native_rng = require_native_rng(gba)
    root_assignments = require_root_initializer(rom)
    entry_assignments = require_stage11_entry(rom)
    bank = rom[OBJECT_OVERLAY_BASE:OBJECT_OVERLAY_BASE + 0x10000]
    if len(bank) != 0x10000:
        raise SystemExit("object overlay bank is truncated")

    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True
    pending = deque(SEEDS)
    queued = set(SEEDS)
    visited: set[int] = set()
    byte_population: set[int] = set()
    callback_edges: set[tuple[int, int]] = set()
    same_segment_calls: set[tuple[int, int]] = set()
    controller_calls: set[int] = set()
    imports: Counter[tuple[int, int]] = Counter()
    indirect_transfers = []

    while pending:
        address = pending.popleft()
        while 0 <= address < len(bank) and address not in visited:
            instruction = decode_one(engine, bank, address)
            if instruction is None:
                break
            visited.add(address)
            byte_population.update(range(address, address + instruction.size))

            callback = callback_assignment(engine, bank, instruction)
            if callback is not None and callback < len(bank):
                callback_edges.add((instruction.address, callback))
                if callback not in queued:
                    queued.add(callback)
                    pending.append(callback)

            mnemonic = instruction.mnemonic
            fallthrough = instruction.address + instruction.size
            if mnemonic in ("ret", "retf", "iret"):
                break
            if mnemonic == "lcall":
                if (
                    len(instruction.operands) == 2
                    and all(operand.type == CS_OP_IMM for operand in instruction.operands)
                ):
                    segment = instruction.operands[0].imm & 0xFFFF
                    target = instruction.operands[1].imm & 0xFFFF
                    if segment == OBJECT_OVERLAY_SEGMENT:
                        same_segment_calls.add((instruction.address, target))
                        if target != CONTROLLER_ENTRY and target not in queued:
                            queued.add(target)
                            pending.append(target)
                    else:
                        imports[(segment, target)] += 1
                else:
                    indirect_transfers.append({
                        "address": instruction.address,
                        "mnemonic": mnemonic,
                        "op_str": instruction.op_str,
                    })
                address = fallthrough
                continue
            if mnemonic == "call":
                target = direct_target(instruction)
                if target is None:
                    indirect_transfers.append({
                        "address": instruction.address,
                        "mnemonic": mnemonic,
                        "op_str": instruction.op_str,
                    })
                elif target == CONTROLLER_ENTRY:
                    controller_calls.add(instruction.address)
                else:
                    same_segment_calls.add((instruction.address, target))
                    if target not in queued:
                        queued.add(target)
                        pending.append(target)
                address = fallthrough
                continue
            if mnemonic == "jmp":
                target = direct_target(instruction)
                if target is None:
                    indirect_transfers.append({
                        "address": instruction.address,
                        "mnemonic": mnemonic,
                        "op_str": instruction.op_str,
                    })
                    break
                address = target
                continue
            if mnemonic.startswith("j") or mnemonic.startswith("loop"):
                target = direct_target(instruction)
                if target is not None and target not in queued:
                    queued.add(target)
                    pending.append(target)
                address = fallthrough
                continue
            address = fallthrough

    if not controller_calls:
        raise SystemExit("upper state graph no longer reaches controller 9908")
    ranges = contiguous_ranges(byte_population)
    callback_targets = sorted({target for _, target in callback_edges})
    result = {
        "schema": 1,
        "kind": "digimon-shoot-upper-state-callback-graph",
        "source_sha256": WSC15_SHA256,
        "root_initializer": {
            "entry": {
                "segment": OBJECT_OVERLAY_SEGMENT,
                "offset": 0x7168,
                "raw_start": ROOT_INIT_RAW_START,
                "raw_end": ROOT_INIT_RAW_END,
                "bytes": ROOT_INIT_RAW_END - ROOT_INIT_RAW_START,
                "sha256": ROOT_INIT_SHA256,
            },
            "menu_entry_call_raw": MENU_ENTRY_CALL_RAW,
            "callback_assignments": root_assignments,
        },
        "stage11_entry": {
            "transition_overlay": {
                "segment": TRANSITION_OVERLAY_SEGMENT,
                "physical_base": TRANSITION_OVERLAY_BASE,
            },
            "raw_range": [STAGE11_ENTRY_RAW_START, STAGE11_ENTRY_RAW_END],
            "sha256": sha256(STAGE11_ENTRY_BYTES),
            "callback_assignments": entry_assignments,
        },
        "object_overlay": {
            "segment": OBJECT_OVERLAY_SEGMENT,
            "physical_base": OBJECT_OVERLAY_BASE,
        },
        "seeds": {
            "active_initializer": list(ACTIVE_SEEDS),
            "battle_transition": list(TRANSITION_SEEDS),
        },
        "reachable_instruction_starts": len(visited),
        "reachable_code_bytes": len(byte_population),
        "reachable_ranges": [
            {
                "start": start,
                "end": end,
                "bytes": end - start,
                "physical_start": OBJECT_OVERLAY_BASE + start,
                "sha256": sha256(bank[start:end]),
            }
            for start, end in ranges
        ],
        "callback_entries": sorted(set(SEEDS) | set(callback_targets)),
        "callback_edges": [
            {"source": source, "target": target}
            for source, target in sorted(callback_edges)
        ],
        "same_segment_calls": [
            {"source": source, "target": target}
            for source, target in sorted(same_segment_calls)
        ],
        "controller_boundary": {
            "target": CONTROLLER_ENTRY,
            "call_sites": sorted(controller_calls),
        },
        "imports": [
            {"segment": segment, "offset": offset, "calls": count}
            for (segment, offset), count in sorted(imports.items())
        ],
        "native_runtime_mapping": native_rng,
        "indirect_transfers": indirect_transfers,
        "claim_scope": (
            "static stage-11 entry and upper callback reachability through calls to "
            "controller 9908; GBA mapping, controller implementation, and runtime excluded"
        ),
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
