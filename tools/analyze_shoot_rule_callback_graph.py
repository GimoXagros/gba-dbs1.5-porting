#!/usr/bin/env python3
"""Recover the statically reachable WSC 1.5 Digimon Shoot rule graph.

The walk follows direct 16-bit branches/calls, the three bounded indirect
dispatch tables, and callback-pointer assignments from the 4090:9908
controller and its four selected families.  Imported calls are recorded but
not followed.  Every supplied indirect target is verified against source ROM
bytes below.
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
OVERLAY_BASE = 0x740900
OVERLAY_SEGMENT = 0x4090
SEEDS = (0x9908, 0x810D, 0x8AB8, 0x8CDD, 0x9083)
CONTROLLER_TABLE = 0x996F
CONTROLLER_TABLE_ENTRIES = 64
CONTROLLER_TARGETS = (0x99EF, 0x99F1, 0x9A0E, 0x9A1B)
OBJECT_KIND_TABLE = 0x1742
OBJECT_KIND_TARGETS = (0x174E, 0x1757, 0x175D, 0x1766, 0x176C, 0x1772)
SHOOT_OBJECT_KINDS = (0, 2)
SHOOT_STATE_TABLE = 0x8FDB
SHOOT_STATE_TARGETS = (0x8F29,) + (0x8F65,) * 9


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
        if next_destination.mem.disp != 2 or (next_source.imm & 0xFFFF) != OVERLAY_SEGMENT:
            return None
        return target

    # Some callbacks load the offset into a register before storing the far
    # pointer.  Accept only the exact three-instruction shape ending in the
    # same verified segment word.
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
    if segment_store is None or segment_store.mnemonic != "mov" or len(segment_store.operands) != 2:
        return None
    segment_destination, segment_source = segment_store.operands
    if segment_destination.type != CS_OP_MEM or segment_source.type != CS_OP_IMM:
        return None
    if segment_destination.mem.disp != 2 or (segment_source.imm & 0xFFFF) != OVERLAY_SEGMENT:
        return None
    return target


def verified_indirect_dispatches(bank: bytes) -> dict[int, dict[str, object]]:
    controller = struct.unpack_from(f"<{CONTROLLER_TABLE_ENTRIES}H", bank, CONTROLLER_TABLE)
    if set(controller) != set(CONTROLLER_TARGETS):
        raise SystemExit("Shoot controller dispatch population changed")

    object_kinds = struct.unpack_from("<6H", bank, OBJECT_KIND_TABLE)
    if object_kinds != OBJECT_KIND_TARGETS:
        raise SystemExit("shared object-kind dispatch changed")

    shoot_states = struct.unpack_from("<10H", bank, SHOOT_STATE_TABLE)
    if shoot_states != SHOOT_STATE_TARGETS:
        raise SystemExit("Shoot state dispatch changed")

    return {
        0x996A: {
            "kind": "shoot-controller-random-dispatch",
            "table": CONTROLLER_TABLE,
            "entries": CONTROLLER_TABLE_ENTRIES,
            "targets": sorted(set(controller)),
        },
        0x173D: {
            "kind": "shared-object-kind-dispatch",
            "table": OBJECT_KIND_TABLE,
            "entries": len(object_kinds),
            "active_indices": list(SHOOT_OBJECT_KINDS),
            "targets": [object_kinds[index] for index in SHOOT_OBJECT_KINDS],
            "all_table_targets": list(object_kinds),
        },
        0x8F24: {
            "kind": "shoot-state-dispatch",
            "table": SHOOT_STATE_TABLE,
            "entries": len(shoot_states),
            "targets": sorted(set(shoot_states)),
        },
    }


def contiguous_ranges(addresses: set[int]) -> list[tuple[int, int]]:
    if not addresses:
        return []
    ordered = sorted(addresses)
    ranges = []
    start = previous = ordered[0]
    for address in ordered[1:]:
        if address != previous + 1:
            ranges.append((start, previous + 1))
            start = address
        previous = address
    ranges.append((start, previous + 1))
    return ranges


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    rom = args.wsc15.read_bytes()
    if sha256(rom) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    bank = rom[OVERLAY_BASE:OVERLAY_BASE + 0x10000]
    if len(bank) != 0x10000:
        raise SystemExit("object overlay bank is truncated")

    table = struct.unpack_from(f"<{CONTROLLER_TABLE_ENTRIES}H", bank, CONTROLLER_TABLE)
    resolved_dispatches = verified_indirect_dispatches(bank)

    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True
    pending = deque((*SEEDS, *CONTROLLER_TARGETS))
    queued = set(pending)
    visited: set[int] = set()
    byte_population: set[int] = set()
    callback_edges: set[tuple[int, int]] = set()
    same_segment_calls: set[tuple[int, int]] = set()
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
                    if segment == OVERLAY_SEGMENT:
                        same_segment_calls.add((instruction.address, target))
                        if target not in queued:
                            queued.add(target)
                            pending.append(target)
                    else:
                        imports[(segment, target)] += 1
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
                    record = {
                        "address": instruction.address,
                        "mnemonic": mnemonic,
                        "op_str": instruction.op_str,
                    }
                    resolved = resolved_dispatches.get(instruction.address)
                    if resolved is not None:
                        record["resolution"] = resolved
                        for dispatch_target in resolved["targets"]:
                            if dispatch_target not in queued:
                                queued.add(dispatch_target)
                                pending.append(dispatch_target)
                    indirect_transfers.append(record)
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

    ranges = contiguous_ranges(byte_population)
    callback_targets = sorted({target for _, target in callback_edges})
    result = {
        "schema": 1,
        "kind": "digimon-shoot-rule-callback-graph",
        "source_sha256": WSC15_SHA256,
        "overlay": {"segment": OVERLAY_SEGMENT, "physical_base": OVERLAY_BASE},
        "seeds": list(SEEDS),
        "controller_dispatch": {
            "table": CONTROLLER_TABLE,
            "entries": CONTROLLER_TABLE_ENTRIES,
            "target_counts": {
                f"0x{target:04X}": table.count(target)
                for target in sorted(set(table))
            },
        },
        "reachable_instruction_starts": len(visited),
        "reachable_code_bytes": len(byte_population),
        "reachable_ranges": [
            {
                "start": start,
                "end": end,
                "bytes": end - start,
                "physical_start": OVERLAY_BASE + start,
                "sha256": sha256(bank[start:end]),
            }
            for start, end in ranges
        ],
        "callback_entries": sorted(set(SEEDS) | set(CONTROLLER_TARGETS) | set(callback_targets)),
        "callback_edges": [
            {"source": source, "target": target}
            for source, target in sorted(callback_edges)
        ],
        "same_segment_calls": [
            {"source": source, "target": target}
            for source, target in sorted(same_segment_calls)
        ],
        "imports": [
            {"segment": segment, "offset": offset, "calls": count}
            for (segment, offset), count in sorted(imports.items())
        ],
        "indirect_transfers": indirect_transfers,
        "claim_scope": (
            "static control-flow and callback-assignment reachability with three "
            "source-verified bounded dispatch tables; GBA mapping and runtime remain unverified"
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
