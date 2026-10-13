#!/usr/bin/env python3
"""Independent consumer/static-semantic verification of Shoot rules components.

No generator import and no instruction execution are used. Capstone decodes
the complete final code; a bounded shape recognizer checks each branch, access
width, native consumer and side effect. The Python decision comparison is a
finite source/target specification check, not a CPU or game emulator.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pathlib
import struct
import sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore

BEFORE_SHA256 = "C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1"
AFTER_SHA256 = "FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
SELECT, SELECT_END, APPLY, APPLY_END, TABLE = 0x5C6000, 0x5C60A8, 0x5C6200, 0x5C6248, 0x5C6400


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, digest: str, label: str) -> None:
    if sha256(data) != digest:
        raise ValueError(f"{label}: SHA-256 mismatch")


def decode(data: bytes, start: int, end: int) -> list:
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    engine.detail = True
    insns = list(engine.disasm(data[start:end], BASE + start))
    if len(insns) * 4 != end - start or any(i.size != 4 for i in insns):
        raise ValueError("incomplete final ARM decode")
    return insns


def word(data: bytes, site: int) -> int:
    return struct.unpack_from("<I", data, site)[0]


def text_at(data: bytes, site: int) -> str:
    i = decode(data, site, site + 4)[0]
    return f"{i.mnemonic} {i.op_str}"


def check_text(data: bytes, site: int, expected: str) -> None:
    actual = text_at(data, site)
    if actual != expected:
        raise ValueError(f"consumer/semantic mismatch at {BASE + site:08X}: {actual} != {expected}")


def literal(data: bytes, site: int) -> int:
    i = decode(data, site, site + 4)[0]
    if i.mnemonic != "ldr" or i.reg_name(i.operands[1].mem.base) != "pc":
        raise ValueError("expected PC-relative native literal")
    target = site + 8 + i.operands[1].mem.disp
    if target & 3:
        raise ValueError("unaligned native literal")
    return word(data, target)


def controller_code(data: bytes, source_table: tuple[int, ...]) -> None:
    # Complete control shape, including both paths through the only RNG call
    # target, early no-RNG path, unsigned coordinate comparisons, signed-byte
    # difficulty clamp, all four return values and exact preserved register set.
    selector = [
        "push {r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}",
        "ldrh r0, [r4, #0x76]", "cmp r0, #0", "bne #0x85c609c",
        "ldr r8, [r4, #0x18]", "ldrh r6, [r8, #0x34]", "ldrh r7, [r8, #0x36]",
        "cmp r6, #0x500", "blo #0x85c6048", "cmp r6, #0x900", "bhi #0x85c6048",
        "bl #0x8012600", "and r0, r0, #3", "cmp r0, #0", "beq #0x85c6094",
        "cmp r7, #0xc00", "blo #0x85c607c", "b #0x85c609c",
        "ldr r8, [pc, #0x58]", "ldrsb r6, [r8]", "cmp r6, #3", "movgt r6, #3",
        "cmp r6, #0", "movlt r6, #0", "bl #0x8012600", "and r0, r0, #0xf",
        "add r0, r0, r6, lsl #4", "ldr r8, [pc, #0x38]", "ldrb r0, [r8, r0]",
        "cmp r0, #3", "bne #0x85c60a0", "ldr r8, [pc, #0x2c]", "ldrh r0, [r8]",
        "tst r0, #0x40", "moveq r0, #3", "movne r0, #2", "b #0x85c60a0",
        "mov r0, #1", "b #0x85c60a0", "mov r0, #2",
        "pop {r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}", "bx lr",
    ]
    apply = [
        "push {r8, sb}", "cmp r0, #0", "beq #0x85c6240", "ldr sb, [r4, #0x28]",
        "cmp r0, #1", "beq #0x85c6230", "cmp r0, #2", "streq r3, [sb]",
        "beq #0x85c6240", "ldr r8, [pc, #0x1c]", "str r8, [sb]", "b #0x85c6240",
        "str r1, [r4]", "ldrh r8, [r4, #0x64]", "strh r8, [r4, #0xa2]",
        "str r2, [sb]", "pop {r8, sb}", "bx lr",
    ]
    for base, end, expected in ((SELECT, SELECT_END, selector), (APPLY, APPLY_END, apply)):
        actual = [f"{i.mnemonic} {i.op_str}" for i in decode(data, base, end)]
        if actual != expected:
            differences = [f"{base + 4 * n:X}: {a} != {b}" for n, (a, b) in enumerate(zip(actual, expected)) if a != b]
            raise ValueError("native controller semantics differ: " + "; ".join(differences))
    if tuple(literal(data, p) for p in (0x5C6048, 0x5C606C, 0x5C607C, 0x5C6224)) != (
        0x0300231F, 0x085C6400, 0x0300450A, 0x085BA800
    ):
        raise ValueError("controller literal reaches wrong consumer")
    decoded = {0: 0x99EF, 1: 0x99F1, 2: 0x9A0E, 3: 0x9A1B}
    try:
        inverse = tuple(decoded[value] for value in data[TABLE:TABLE + 64])
    except KeyError as error:
        raise ValueError("unresolved native action token") from error
    if inverse != source_table:
        raise ValueError("native table inverse does not reproduce all 64 source targets")


def consumer_proof(gba: bytes, old: bytes, new: bytes) -> dict:
    # Physical source coordinates are retained: the retail overlay has the
    # documented +200 display-address trap, so no global logical base is used.
    source_signatures = (
        (old, 0x394B4F, "837D6200"), (old, 0x394B6A, "C745620000"),
        (old, 0x394B72, "FF4D62"), (old, 0x3948AD, "894450"),
        (old, 0x3948B0, "26803E5D0000"), (old, 0x39604E, "89948C00"),
        (old, 0x39639C, "8B741C8B44268B5428"),
        (old, 0x3963AB, "8B5C128B5414"),
        (new, 0x74A2F1, "C7040D81C7440290408B445089848C008B5C1CC707B88A"),
        (new, 0x74A30E, "8B5C1CC707DD8CC747029040C3"),
        (new, 0x74A321, "26F706D803400007750D8B5C1CC7078390"),
        (new, 0x751CA5, "531EB8000C8ED8A186388B1E883803C3891E8638051137A3883886C41F5BCB"),
    )
    for data, start, expected_hex in source_signatures:
        expected = bytes.fromhex(expected_hex)
        if data[start:start + len(expected)] != expected:
            raise ValueError(f"source consumer signature changed: {start:X}")
    for site, expected in (
        (0x3701A4, "ldrsh r8, [r5, #0x76]"), (0x3701D4, "strh sb, [r5, #0x76]"),
        (0x3701DC, "ldrsh r8, [r5, #0x76]"), (0x3701E4, "strh r8, [r5, #0x76]"),
        (0x36FD30, "ldrb sb, [r8, #0xf]"), (0x36FD44, "strh sl, [r4, #0x64]"),
        (0x3721AC, "strh r3, [r4, #0xa0]"), (0x3721B0, "sub r3, r3, #0x80"),
        (0x3721B4, "strh r3, [r4, #0xa2]"),
        (0x372740, "ldr r4, [r4, #0x28]"), (0x372744, "ldrsh r0, [r4, #0x34]"),
        (0x372748, "ldrsh r3, [r4, #0x36]"), (0x372760, "ldr r3, [r4, #0x18]"),
    ):
        check_text(gba, site, expected)
    if literal(gba, 0x36FD2C) + 0xF != 0x0300231F:
        raise ValueError("native difficulty consumer points elsewhere")
    rng = [f"{i.mnemonic} {i.op_str}" for i in decode(gba, 0x12600, 0x12630)]
    if rng != [
        "ldr r8, [pc, #0x28]", "ldrh r0, [r8]", "ldrh sb, [r8, #2]", "add r0, r0, sb",
        "strh sb, [r8]", "add r0, r0, #0x3700", "add r0, r0, #0x11", "strh r0, [r8, #2]",
        "and r8, r0, #0xff", "lsr r0, r0, #8", "add r0, r0, r8, lsl #8", "bx lr",
    ] or literal(gba, 0x12600) != 0x03001420:
        raise ValueError("native RNG contract changed")
    return {"source_to_native_fields": {"62": "76", "14": "18", "26": "34", "28": "36",
                                        "1C": "28", "50": "64", "8C": "A2"},
            "difficulty": "source signed byte ES:005D -> native 0300231F",
            "rng_state": "03001420..03001424", "rng_clobbers": ["r0", "r8", "r9"],
            "rng_equivalence_scope": "stored halfwords and consumed return low four bits; not unrestricted 32-bit return identity",
            "parent": "existing resident 085BA800; passed callback pointers remain an unmet caller prerequisite"}


def finite_decisions(source_table: tuple[int, ...], native_table: bytes) -> dict:
    def source(forced, x, y, difficulty, random_low, flags):
        if forced:
            return 2, 0
        if 0x500 <= x <= 0x900:
            target = 0x99F1 if random_low & 3 == 0 else 0x9A0E if y >= 0xC00 else 0x9A1B
        else:
            signed = difficulty if difficulty < 128 else difficulty - 256
            row = min(3, max(0, signed))
            target = source_table[row * 16 + random_low]
        if target == 0x99EF:
            return 0, 1
        if target == 0x99F1:
            return 1, 1
        if target == 0x9A0E or flags & 0x40:
            return 2, 1
        return 3, 1

    def native(forced, x, y, difficulty, random_low, flags):
        if forced != 0:
            return 2, 0
        if x < 0x500 or x > 0x900:
            row = difficulty - 256 if difficulty & 128 else difficulty
            if row > 3:
                row = 3
            if row < 0:
                row = 0
            action = native_table[(row << 4) + random_low]
        elif random_low % 4 == 0:
            action = 1
        elif y < 0xC00:
            action = 3
        else:
            action = 2
        if action == 3 and flags & 0x40:
            action = 2
        return action, 1

    count = 0
    for args in itertools.product((0, 0xFFFF), (0, 0x4FF, 0x500, 0x501, 0x8FF, 0x900, 0x901, 0xFFFF),
                                  (0xBFF, 0xC00), range(256), range(16), (0, 0x40)):
        if source(*args) != native(*args):
            raise ValueError(f"static decision specification mismatch for {args}")
        count += 1
    # Object effects are determined by action, not by coordinates after SELECT.
    # A linked object may alias the current object; source ordering still agrees.
    effects = {
        "0": [],
        "1": ["current.callback=810D", "current.A2=current.u16(64)", "linked.callback=8AB8"],
        "2": ["linked.callback=8CDD"], "3": ["linked.callback=085BA800"],
    }
    return {"partition_cases": count, "difficulty_byte_population": 256, "rng_low4_population": 16,
            "coordinate_partitions": "unsigned X boundaries 500/900 and Y boundary C00; all other values are equivalent within each decoded branch partition",
            "action_effects": effects, "source_order_retained": True,
            "same_update_precondition": "SELECT/APPLY must use the same object, link, HP, flags and callback inputs without intervening game updates"}


def rejection_checks(after: bytes, source_table: tuple[int, ...]) -> list[dict]:
    cases = (
        ("wrong countdown field", 0x5C6004, 0xE1D407B4),
        ("signed upper X comparison accepts FFFF", 0x5C6028, (word(after, 0x5C6028) & 0x0FFFFFFF) | 0xC0000000),
        ("exclude upper X endpoint", 0x5C6028, (word(after, 0x5C6028) & 0x0FFFFFFF) | 0x20000000),
        ("wrong RNG entry", 0x5C602C, word(after, 0x5C602C) + 1),
        ("unsigned difficulty load", 0x5C604C, 0xE5D86000),
        ("wrong parent guard bit", 0x5C6084, 0xE3100020),
        ("wrong primary link", 0x5C620C, 0xE5949024),
        ("swapped paired callback", 0x5C6230, 0xE5842000),
        ("half-HP threshold substituted for HP", 0x5C6234, 0xE1D486B8),
        ("scratch word clobbers next field", 0x5C6238, 0xE58480A2),
        ("wrong parent callback", 0x5C6248, 0x085BAC00),
    )
    rejected = []
    for label, offset, value in cases:
        mutated = bytearray(after)
        struct.pack_into("<I", mutated, offset, value)
        try:
            controller_code(mutated, source_table)
        except ValueError as error:
            rejected.append({"case": label, "site": offset, "detected": str(error)})
        else:
            raise ValueError(f"semantic verifier accepts {label}")
    mutated = bytearray(after)
    mutated[TABLE] = (mutated[TABLE] + 1) % 4
    try:
        controller_code(mutated, source_table)
    except ValueError as error:
        rejected.append({"case": "wrong source dispatch entry", "site": TABLE, "detected": str(error)})
    else:
        raise ValueError("semantic verifier accepts wrong dispatch entry")
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15"):
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    before, after, gba, old, new = (getattr(args, n).read_bytes() for n in ("before", "after", "gba", "wsc10", "wsc15"))
    for data, digest, label in ((before, BEFORE_SHA256, "v50"), (after, AFTER_SHA256, "rules candidate"),
                                (gba, GBA_SHA256, "GBA"), (old, WSC10_SHA256, "WSC10"), (new, WSC15_SHA256, "WSC15")):
        require_hash(data, digest, label)
    if len(before) != len(after) or len(after) != 0x800000:
        raise ValueError("candidate extent changed")
    source_table = struct.unpack_from("<64H", new, 0x74A26F)
    controller_code(after, source_table)
    consumers = consumer_proof(gba, old, new)
    decisions = finite_decisions(source_table, after[TABLE:TABLE + 64])
    rejected = rejection_checks(after, source_table)
    ranges = ((SELECT, 0x5C60B4), (APPLY, 0x5C624C), (TABLE, TABLE + 64))
    allowed = {i for start, end in ranges for i in range(start, end)}
    changed = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if not changed or not changed <= allowed or before[0x5C6000:0x5C6500] != b"\xFF" * 0x500:
        raise ValueError("Expected Write containment/ownership failed")
    if before[0x5C0A00:0x5C0A04] != bytes.fromhex("1EFF2FE1") or after[0x5C0A00:0x5C0A04] != before[0x5C0A00:0x5C0A04]:
        raise ValueError("unimplemented controller boundary was changed")
    pointers = []
    for off in range(0, len(after), 4):
        old_value, value = word(before, off), word(after, off)
        if 0x085C6000 <= old_value < 0x085C6500:
            raise ValueError("pre-existing pointer reaches rules ownership")
        if 0x085C6000 <= value < 0x085C6500:
            pointers.append({"site": off, "target": value})
            if off not in allowed:
                raise ValueError("unexpected external pointer reaches rules components")
        for candidate, prior in ((old_value, True), (value, False)):
            if candidate >> 28 == 15 or candidate & 0x0E000000 != 0x0A000000:
                continue
            delta = candidate & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            target = off + 8 + delta * 4
            if 0x5C6000 <= target < 0x5C6500 and (prior or off not in allowed):
                raise ValueError("pre-existing or external ARM B/BL reaches rules components")
    if pointers != [{"site": 0x5C60AC, "target": 0x085C6400}]:
        raise ValueError("rules pointer population changed")
    report = {"schema": 1, "kind": "shoot-controller-static-consumer-verification",
              "before_sha256": BEFORE_SHA256, "after_sha256": AFTER_SHA256,
              "changed_bytes": len(changed), "expected_write_ranges": ranges,
              "native_consumers": consumers, "finite_decision_specification": decisions,
              "negative_cases": rejected, "aligned_pointer_population": pointers,
              "preexisting_arm_branches": [], "external_arm_branches": [],
              "decoded_arm_instructions": 60, "literal_bytes": 16,
              "rng_paths": {"object_76_nonzero": 0, "all_other_paths": 1},
              "source_table_counts": {f"{v:04X}": source_table.count(v) for v in sorted(set(source_table))},
              "unimplemented_callback_addresses_present": False,
              "external_entry_connected": False, "controller_boundary_preserved": True,
              "runtime_verification_performed": False,
              "claim_scope": "exact static controller decision/application components; no complete lower graph or callable controller adapter"}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
