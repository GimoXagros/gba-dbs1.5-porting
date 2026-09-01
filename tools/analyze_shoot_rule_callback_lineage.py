#!/usr/bin/env python3
"""Rank WSC 1.0 lineages for the Ver. 1.5 Digimon Shoot rule entries.

The Ver. 1.5 controller at 4090:9908 selects four object callback families.
This report compares normalized x86 instruction/operand shapes against every
directly referenced callback entry in the retail 9070 overlay.  It is a
lineage-ranking aid only and does not assert a GBA implementation address.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from difflib import SequenceMatcher

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


WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC10_OVERLAY_BASE = 0x390900
WSC15_OVERLAY_BASE = 0x740900
OVERLAY_BYTES = 0x10000

TARGETS = {
    "shoot_controller": 0x9908,
    "family_810d": 0x810D,
    "family_8ab8": 0x8AB8,
    "family_8cdd": 0x8CDD,
    "family_9083": 0x9083,
    "chained_94c1": 0x94C1,
    "chained_9798": 0x9798,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def callback_candidates(bank: bytes, segment: int) -> list[int]:
    candidates: set[int] = set()
    segment_bytes = segment.to_bytes(2, "little")
    # Same-segment far calls: 9A <near> <segment>.
    for offset in range(len(bank) - 4):
        if bank[offset] == 0x9A and bank[offset + 3:offset + 5] == segment_bytes:
            target = int.from_bytes(bank[offset + 1:offset + 3], "little")
            if target < len(bank):
                candidates.add(target)
    # Callback assignments emitted by the compiler use an immediate near
    # pointer followed shortly by a 4090 segment store.  Accept both [si] and
    # [bx] forms while retaining only in-bank immediates.
    for offset in range(len(bank) - 18):
        if bank[offset] != 0xC7:
            continue
        window = bank[offset:offset + 18]
        if segment_bytes not in window:
            continue
        modrm = bank[offset + 1]
        immediate_offset = 2
        if modrm & 0xC0 == 0x40:
            immediate_offset = 3
        elif modrm & 0xC0 == 0x80:
            immediate_offset = 4
        if offset + immediate_offset + 2 > len(bank):
            continue
        target = int.from_bytes(
            bank[offset + immediate_offset:offset + immediate_offset + 2], "little"
        )
        if target < len(bank):
            candidates.add(target)
    # Compiler-emitted callback bodies and local state handlers commonly start
    # immediately after RET/RETF even when no direct pointer to that exact body
    # survives in the overlay.  Include those boundaries so a shifted family
    # is not ranked from the middle of its closest retail routine.
    candidates.update(
        offset + 1
        for offset, value in enumerate(bank[:-1])
        if value in (0xC3, 0xCB)
    )
    return sorted(candidates)


def operand_token(engine: Cs, instruction, operand) -> str:
    if operand.type == CS_OP_REG:
        return f"r:{engine.reg_name(operand.reg)}"
    if operand.type == CS_OP_MEM:
        memory = operand.mem
        return (
            f"m:{engine.reg_name(memory.segment)}:{engine.reg_name(memory.base)}:"
            f"{engine.reg_name(memory.index)}:{memory.scale}:{memory.disp}"
        )
    if operand.type == CS_OP_IMM:
        immediate = operand.imm
        if instruction.mnemonic.startswith("j") or instruction.mnemonic in ("call", "lcall"):
            return "i:control"
        if -0xFF <= immediate <= 0xFF:
            return f"i:{immediate}"
        return "i:wide"
    return f"t:{operand.type}"


def normalized_shape(bank: bytes, start: int, *, max_bytes: int = 0x300,
                     max_instructions: int = 140) -> list[str]:
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True
    tokens = []
    window = bank[start:min(len(bank), start + max_bytes)]
    for instruction in engine.disasm(window, start):
        operands = ",".join(
            operand_token(engine, instruction, operand)
            for operand in instruction.operands
        )
        tokens.append(f"{instruction.mnemonic}|{operands}")
        if len(tokens) >= max_instructions:
            break
    return tokens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--graph", type=pathlib.Path)
    args = parser.parse_args()

    old_rom = args.wsc10.read_bytes()
    new_rom = args.wsc15.read_bytes()
    if sha256(old_rom) != WSC10_SHA256:
        raise SystemExit("refusing unknown WSC 1.0 source")
    if sha256(new_rom) != WSC15_SHA256:
        raise SystemExit("refusing unknown WSC Ver. 1.5 source")
    old_bank = old_rom[WSC10_OVERLAY_BASE:WSC10_OVERLAY_BASE + OVERLAY_BYTES]
    new_bank = new_rom[WSC15_OVERLAY_BASE:WSC15_OVERLAY_BASE + OVERLAY_BYTES]
    if len(old_bank) != OVERLAY_BYTES or len(new_bank) != OVERLAY_BYTES:
        raise SystemExit("object overlay bank is truncated")

    candidates = callback_candidates(old_bank, 0x9070)
    candidate_shapes = {
        start: normalized_shape(old_bank, start)
        for start in candidates
    }
    score_windows = (32, 64, 96, 140)
    targets = dict(TARGETS)
    target_offsets = set(targets.values())
    if args.graph:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        if (
            graph.get("kind") != "digimon-shoot-rule-callback-graph"
            or graph.get("source_sha256") != WSC15_SHA256
        ):
            raise SystemExit("refusing unknown Shoot callback graph")
        for start in graph["callback_entries"]:
            if start not in target_offsets:
                targets[f"graph_{start:04x}"] = start
                target_offsets.add(start)
        for edge in graph["same_segment_calls"]:
            start = edge["target"]
            if start not in target_offsets:
                targets[f"helper_{start:04x}"] = start
                target_offsets.add(start)

    results = []
    for label, start in targets.items():
        target_shape = normalized_shape(new_bank, start)
        ranked = []
        for candidate, candidate_shape in candidate_shapes.items():
            scores = [
                SequenceMatcher(
                    None,
                    target_shape[:window],
                    candidate_shape[:window],
                ).ratio()
                for window in score_windows
            ]
            score = sum(scores) / len(scores)
            ranked.append((score, scores, candidate, len(candidate_shape)))
        ranked.sort(reverse=True)
        results.append({
            "label": label,
            "wsc15_offset": start,
            "wsc15_physical": WSC15_OVERLAY_BASE + start,
            "normalized_instructions": len(target_shape),
            "best_wsc10": [
                {
                    "score": round(score, 6),
                    "window_scores": {
                        str(window): round(window_score, 6)
                        for window, window_score in zip(score_windows, scores, strict=True)
                    },
                    "offset": candidate,
                    "physical": WSC10_OVERLAY_BASE + candidate,
                    "normalized_instructions": instruction_count,
                }
                for score, scores, candidate, instruction_count in ranked[:args.top]
            ],
        })

    result = {
        "schema": 1,
        "kind": "digimon-shoot-rule-callback-lineage-ranking",
        "sources": {
            "wsc10_sha256": WSC10_SHA256,
            "wsc15_sha256": WSC15_SHA256,
        },
        "candidate_population": len(candidates),
        "normalization": (
            "x86 mnemonic, register and memory shape; branch/call targets and "
            "wide immediates masked; fixed 0x300-byte windows scored at "
            "32/64/96/140 instructions"
        ),
        "targets": results,
        "claim_scope": (
            "ranked cross-version lineage evidence only; no GBA callback address "
            "or runtime behavior is asserted"
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
