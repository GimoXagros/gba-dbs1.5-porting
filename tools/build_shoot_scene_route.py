#!/usr/bin/env python3
"""Add the source case-5 predicate and progress-bit producer to retail flow.

No scene allocation is added: only the callback argument selected at the
existing case-5 allocation is changed. Real scene and full initializer code
must already exist in the hash-bound predecessor. This layer never invents
an initializer body or removes a lower-rule boundary.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import assemble, require_hash, sha256
from build_shoot_scene_transition import INITIALIZER as INITIALIZER_CONTRACT, pack_code

BASE = 0x08000000
SELECTOR, PROGRESS = 0x5C9900, 0x5C9A00
SCENE, INITIALIZER = 0x085C8000, 0x08629800
# Pin only after the controller, pursuit, terminal-camera and IRQ lifetime proofs close.
INPUT_SHA256: str | None = None
HOOKS = ((0x33FD04, 0xE59F80A8, SELECTOR), (0x0B9E68, 0xE59F10C0, PROGRESS))
HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
SOURCE_GUARDS = (
    ("gba", 0x33FCCC, 0x33FDC0, "BA358E3B4CE1E19E4EEDB0B54F0119F9D0FAEA77DE1DCF26AF2B75B9C15CAFF4"),
    ("gba", 0x0B9E48, 0x0B9E78, "F9990D6B5DA65FB1986758D3EAD3BB4D9B40699204C905B07FA0707B2A907F07"),
    ("wsc15", 0x771F69, 0x772011, "CD05FF48C1922F76960ECEE5B2C2847E693DEC337D2B598C32777F7F367C2B8E"),
    ("wsc15", 0x77F9F8, 0x77FA30, "60A7A0D2605A271EF03A19EF79075FA6EC159AC01756829FF1BFBF3D4415476A"),
    ("wsc10", 0x3C157E, 0x3C15A0, "78A4337C5B048F5B2E2532912365281AE1F3E1CC187B7E187450AF2634AAD94C"),
)


def code() -> dict[int, tuple[bytes, int]]:
    selector = """
        push {r0, r1, r12, lr}
        mrs r12, cpsr
        ldr r8, =0x0834059C
        ldr r0, =0x0300231E
        ldrb r1, [r0]
        cmp r1, #11
        beq done
        ldrb r1, [r0, #1]
        cmp r1, #3
        beq shoot
        cmp r1, #0
        beq done
        ldr r0, =0x0300232A
        ldrh r1, [r0]
        tst r1, #0x400
        bne done
    shoot:
        ldr r8, =0x085C8000
    done:
        msr cpsr_f, r12
        pop {r0, r1, r12, lr}
        b 0x0833FD08
    """
    producer = """
        push {r0, r8, r9, r12, lr}
        mrs r12, cpsr
        ldr r8, =0x0300231E
        ldrb r9, [r8]
        cmp r9, #7
        beq done
        cmp r9, #11
        beq done
        ldr r8, =0x0300232A
        ldrh r9, [r8]
        orr r9, r9, #0x400
        strh r9, [r8]
    done:
        ldr r1, =0x03002310
        msr cpsr_f, r12
        pop {r0, r8, r9, r12, lr}
        b 0x080B9E6C
    """
    return {SELECTOR: pack_code(selector, SELECTOR), PROGRESS: pack_code(producer, PROGRESS)}


def inbound(data: bytes, spans: list[tuple[int, int]]) -> None:
    for site in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, site)[0]
        if any(BASE + a <= (word & ~1) < BASE + z for a, z in spans):
            raise ValueError(f"route destination has an existing literal reference at {site:X}")
        if (word >> 28) != 15 and (word & 0x0E000000) == 0x0A000000:
            immediate = word & 0xFFFFFF
            if immediate & 0x800000:
                immediate -= 0x1000000
            target = site + 8 + immediate * 4
            if any(a <= target < z for a, z in spans):
                raise ValueError(f"route destination has an existing ARM branch at {site:X}")


def dependencies(before: bytes, spec: dict) -> dict:
    if set(spec) != {"input_sha256", "scene", "initializer"}:
        raise ValueError("route dependency manifest fields")
    require_hash(before, spec["input_sha256"], "route exact predecessor")
    if spec["initializer"] != INITIALIZER_CONTRACT:
        raise ValueError("route requires the verified source-ordered v65 initializer")
    bound = {}
    for name, expected_entry, maximum in (("scene", SCENE, 0x100), ("initializer", INITIALIZER, 0x800)):
        row = spec[name]
        if set(row) != {"entry", "bytes", "sha256"} or row["entry"] != expected_entry:
            raise ValueError(f"route {name} entry contract")
        size = row["bytes"]
        if not isinstance(size, int) or size < 40 or size > maximum or size % 4:
            raise ValueError(f"route {name} code extent")
        raw = expected_entry - BASE
        payload = before[raw:raw + size]
        require_hash(payload, row["sha256"], f"real resident {name}")
        if payload[:4] in (b"\xff" * 4, struct.pack("<I", 0xE12FFF1E)):
            raise ValueError(f"route {name} cannot be an absent function or return stub")
        bound[name] = dict(row)
    return bound


def build(before: bytes, originals: dict[str, bytes], spec: dict) -> tuple[bytes, dict]:
    if INPUT_SHA256 is None:
        raise ValueError("external Shoot route remains gated on controller, pursuit, terminal-camera and IRQ lifetime")
    require_hash(before, INPUT_SHA256, "verified complete route predecessor")
    for name, expected in HASHES.items():
        require_hash(originals[name], expected, name)
    for name, a, z, expected in SOURCE_GUARDS:
        require_hash(originals[name][a:z], expected, f"{name} route guard {a:X}")
    bound = dependencies(before, spec)
    placements = code()
    spans = [(a, a + len(blob)) for a, (blob, _) in placements.items()]
    for a, z in spans:
        if before[a:z] != b"\xff" * (z - a):
            raise ValueError(f"route placement is not FF at {a:X}")
    inbound(before, spans)
    # Both source branches and the single retail allocation are kept bytewise.
    for _, a, z, expected in SOURCE_GUARDS:
        if a in (0x33FCCC, 0x0B9E48):
            require_hash(before[a:z], expected, f"unchanged retail hook neighborhood {a:X}")
    out = bytearray(before)
    manifests = []
    for a, (blob, code_size) in placements.items():
        out[a:a + len(blob)] = blob
        manifests.append({"offset": a, "entry": BASE + a, "bytes": len(blob), "code_bytes": code_size,
                          "sha256": sha256(blob)})
    hooks = []
    for at, expected, target in HOOKS:
        if struct.unpack_from("<I", before, at)[0] != expected:
            raise ValueError(f"route hook precondition {at:X}")
        branch = assemble(f"b {BASE + target:#x}", at)
        if len(branch) != 4:
            raise ValueError("route hook is not one ARM branch")
        out[at:at + 4] = branch
        hooks.append({"offset": at, "expected": expected, "replacement": struct.unpack("<I", branch)[0]})
    report = {"schema": 1, "kind": "shoot-case5-source-conditional-route", "input_sha256": sha256(before),
              "output_sha256": sha256(out), "dependencies": bound, "placements": manifests, "hooks": hooks,
              "source_predicate": "stage != 11 && (difficulty == 3 || (difficulty != 0 && (progress & 0x0400) == 0))",
              "new_allocations": 0, "native_allocation_retained": 0x0833FD18,
              "source_progress_word": "1000:0068", "native_progress_word": 0x0300232A,
              "new_progress_rule": "stage not in (7,11): progress |= 0x0400",
              "existing_stage7_0200_preserved": True,
              "no_new_RAM": True, "runtime_executed": False,
              "integration_precondition": "normal initialized retail battle, scene ownership/object lifetime and all full-initializer dependencies separately verified"}
    return bytes(out), report


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "gba", "wsc10", "wsc15", "dependencies", "output"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--manifest", required=True, type=pathlib.Path)
    args = parser.parse_args()
    output, report = build(args.before.read_bytes(), {name: getattr(args, name).read_bytes() for name in HASHES},
                           json.loads(args.dependencies.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-case5-route] native condition/progress hook installed: {sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
