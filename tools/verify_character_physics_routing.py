#!/usr/bin/env python3
"""Independently verify source pointer routing and the v54 payload repair.

No generator imports, instruction execution, emulator, or save access.
The source constructor and native consumers establish routing and extent;
the retail corpus establishes the per-field numerical conversion.
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

BEFORE = "CAB43EA68A6620D150CA853FC51D4690AAF0889A6D7351D90F99128FE5DD2C69"
AFTER = "8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
FIRST, LIMIT = 0x4850B4, 0x48521C
SOURCE_OFFSETS = (0x001E, 0x0096, 0x010E, 0x0186, 0x01FE, 0x0276, 0x02EE,
                  0x0366, 0x03DE, 0x0456, 0x04CE, 0x0546, 0x0776, 0x0686, 0x06FE)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def sequence(data: bytes, a: int, z: int, expected: list[str], *, arm: bool = False) -> None:
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    instructions = list(decoder.disasm(data[a:z], a + (BASE if arm else 0)))
    need(sum(i.size for i in instructions) == z - a, f"complete instruction boundary {a:X}")
    observed = [f"{i.mnemonic} {i.op_str}".strip() for i in instructions]
    need(observed == expected, f"instruction contract {a:X}: {observed}")


def source_addresses(wsc: bytes) -> list[int]:
    sequence(wsc, 0x7435EC, 0x743612, [
        "mov ax, 0x2846", "mov es, ax", "mov al, 0xbb", "out 0xc2, al",
        "mov bx, word ptr [bp + 0xc]", "add bx, bx", "add bx, 0",
        "mov bx, word ptr es:[bx]", "mov word ptr [si + 0x4e], bx",
        "mov ax, word ptr es:[bx + 0x24]", "mov word ptr [si + 0x42], ax",
        "mov ax, word ptr es:[bx + 0x26]", "mov word ptr [si + 0x44], ax",
    ])
    sequence(wsc, 0x7674B4, 0x7674BD, [
        "add word ptr [si + 0x4e], 0x50", "mov word ptr [si + 0x56], 0x600",
    ])
    sequence(wsc, 0x7674DB, 0x7674F5, [
        "mov al, 0xbb", "out 0xc2, al", "mov ax, 0x2846", "mov es, ax",
        "mov bx, word ptr [si + 0x4e]", "mov ax, word ptr es:[bx + 0x24]",
        "mov dx, word ptr es:[bx + 0x26]", "mov word ptr [si + 0x42], ax",
        "mov word ptr [si + 0x44], dx",
    ])
    sequence(wsc, 0x76768F, 0x7676AD, [
        "sub word ptr [si + 0x4e], 0x50", "mov al, 0xbb", "out 0xc2, al",
        "mov ax, 0x2846", "mov es, ax", "mov bx, word ptr [si + 0x4e]",
        "mov ax, word ptr es:[bx + 0x24]", "mov dx, word ptr es:[bx + 0x26]",
        "mov word ptr [si + 0x42], ax", "mov word ptr [si + 0x44], dx",
    ])
    offsets = struct.unpack_from("<15H", wsc, 0x3B8460)
    need(offsets == SOURCE_OFFSETS, "actual source pointer table values")
    addresses = []
    for offset in offsets:
        linear = 0x28460 + offset
        need(0x20000 <= linear and linear + 0x78 <= 0x30000, "record in one source C2 window")
        addresses.append(0x3B0000 + linear % 0x10000)
    return addresses


def native_consumers(data: bytes, gba: bytes) -> None:
    for a, z, expected in (
        (0x3530BC, 0x3530E4, [
            "push {r0, r1, r3, r4, r5, lr}", "ldr r4, [sp, #0x2c]", "ldr r1, [sp, #0x20]",
            "ldr r8, [pc, #0x22c]", "ldr r1, [r8, r1, lsl #2]", "str r1, [r4, #0x60]",
            "ldrsh r0, [r1, #0x24]", "strh r0, [r4, #0x52]",
            "ldrsh r0, [r1, #0x26]", "strh r0, [r4, #0x54]",
        ]),
        (0x35A3C4, 0x35A3D0, [
            "ldr r8, [r4, #0x60]", "add r8, r8, #0x50", "str r8, [r4, #0x60]",
        ]),
        (0x35A410, 0x35A424, [
            "ldr r1, [r4, #0x60]", "ldrsh r0, [r1, #0x24]", "ldrsh r3, [r1, #0x26]",
            "strh r0, [r4, #0x52]", "strh r3, [r4, #0x54]",
        ]),
        (0x35A6E8, 0x35A708, [
            "ldr r8, [r4, #0x60]", "sub r8, r8, #0x50", "str r8, [r4, #0x60]",
            "ldr r1, [r4, #0x60]", "ldrsh r0, [r1, #0x24]", "ldrsh r3, [r1, #0x26]",
            "strh r0, [r4, #0x52]", "strh r3, [r4, #0x54]",
        ]),
    ):
        sequence(gba, a, z, expected, arm=True)
        need(data[a:z] == gba[a:z], f"actual native consumer retained {a:X}")
    need(struct.unpack_from("<I", gba, 0x3532FC)[0] == 0x083534D8, "retail table literal")
    need(struct.unpack_from("<I", data, 0x3532FC)[0] == 0x08485000, "actual expanded table literal")


def converted_values(source: bytes) -> tuple[int, ...]:
    need(len(source) == 120, "complete three-row source group")
    values = []
    for n, original in enumerate(struct.unpack("<60h", source)):
        field = n % 20
        if field in (0, 1, 2, 5, 6, 10):
            numerator, denominator = 5, 4
        elif field in (3, 4, 7, 9, 11, 12, 13, 14):
            numerator, denominator = 25, 16
        elif field == 8:
            numerator, denominator = 4, 5
        else:
            numerator, denominator = 1, 1
        value = abs(original) * numerator // denominator
        if original < 0:
            value = -value
        if field == 2 and original == -804:
            value = -1011
        values.append(value)
    return tuple(values)


def record(data: bytes, at: int) -> bytes:
    return data[at:at + 120]


def retail_oracle(gba: bytes, wsc: bytes, addresses: list[int]) -> list[dict]:
    pointers = struct.unpack_from("<12I", gba, 0x3534D8)
    need(pointers == tuple(0x08353508 + 120 * n for n in range(12)), "retail table resolved from literal")
    exceptions = []
    for character, pointer in enumerate(pointers):
        expected = converted_values(record(wsc, addresses[character]))
        actual = struct.unpack("<60h", record(gba, pointer - BASE))
        for field, (a, e) in enumerate(zip(actual, expected, strict=True)):
            if a != e:
                exceptions.append({"character": character, "halfword": field, "native": a, "converted_source": e})
    need(len(exceptions) == 13 and all(x["character"] == 11 for x in exceptions),
         "retail IDs 0-10 exact; ID11 retains its known commercial differences")
    return exceptions


def current_physics(data: bytes, gba: bytes, wsc: bytes, addresses: list[int]) -> list[dict]:
    native_consumers(data, gba)
    expected_pointers = tuple(0x08353508 + 120 * n for n in range(12)) + tuple(
        BASE + FIRST + 120 * n for n in range(3))
    pointers = struct.unpack_from("<15I", data, 0x485000)
    need(pointers == expected_pointers, "fifteen corrected destination pointers")
    need(data[0x48503C:FIRST] == bytes(120), "preserved reserved gap")
    records = []
    for character, pointer in enumerate(pointers):
        source = record(wsc, addresses[character])
        payload = record(data, pointer - BASE)
        if character < 12:
            need(payload == record(gba, pointer - BASE), f"retail group {character} unchanged")
        else:
            need(struct.unpack("<60h", payload) == converted_values(source),
                 f"source-table-routed group {character}")
        for form_offset in (0, 0x50):
            if character == 11 and form_offset == 0x50:
                # This is one of the 13 explicitly retained commercial
                # differences, already checked by full retail byte equality.
                continue
            need(struct.unpack_from("<hh", payload, form_offset + 0x24)
                 == struct.unpack_from("<hh", source, form_offset + 0x24),
                 f"base/evolved consumer bounds {character}")
        records.append({"character": character, "source": addresses[character],
                        "destination": pointer, "sha256": sha(payload),
                        "base_bounds": struct.unpack_from("<hh", payload, 0x24),
                        "evolved_bounds": struct.unpack_from("<hh", payload, 0x74),
                        "evolved_bounds_preserve_retail_exception": character == 11})
    return records


def exact_diff(before: bytes, after: bytes) -> int:
    need(len(before) == len(after) == 0x800000, "same ROM extent")
    need(before[:FIRST] == after[:FIRST] and before[LIMIT:] == after[LIMIT:],
         "changes limited to the existing three physics payloads")
    changed = sum(a != b for a, b in zip(before[FIRST:LIMIT], after[FIRST:LIMIT], strict=True))
    need(changed > 0, "repair has an observable byte change")
    return changed


def rejected(fn, label: str) -> str:
    try:
        fn()
    except ValueError:
        return label
    raise ValueError(f"negative case accepted: {label}")


def verify(before: bytes, after: bytes, gba: bytes, wsc: bytes) -> dict:
    need((sha(before), sha(gba), sha(wsc)) == (BEFORE, GBA, WSC), "immutable predecessor/source identities")
    addresses = source_addresses(wsc)
    exceptions = retail_oracle(gba, wsc, addresses)
    records = current_physics(after, gba, wsc, addresses)
    changed = exact_diff(before, after)
    deltas = []
    for character in (12, 13, 14):
        at = FIRST + (character - 12) * 120
        old = record(before, at)
        old_source_at = 0x3B847E + character * 120
        need(struct.unpack("<60h", old) == converted_values(record(wsc, old_source_at)),
             "historical arithmetic-routing defect reproduced")
        original_values = struct.unpack("<60h", old)
        corrected_values = struct.unpack("<60h", record(after, at))
        deltas.append({
            "character": character, "historical_source": old_source_at, "actual_source": addresses[character],
            "changed_halfwords": [{"halfword": n, "row": n // 20, "field_byte_offset": n % 20 * 2,
                                   "before": a, "after": b}
                                  for n, (a, b) in enumerate(zip(original_values, corrected_values, strict=True)) if a != b],
        })
    negatives = [rejected(lambda: current_physics(before, gba, wsc, addresses), "unrepaired v54 source routing")]
    # Every added scalar is tested independently, without checking the output
    # hash. This also catches a corrupt field whose base bounds look correct.
    halfwords_rejected = 0
    for n in range(180):
        mutated = bytearray(after)
        mutated[FIRST + n * 2] ^= 1
        rejected(lambda: current_physics(mutated, gba, wsc, addresses), f"added halfword {n}")
        halfwords_rejected += 1
    for character in (12, 13, 14):
        at = FIRST + (character - 12) * 120
        mutated = bytearray(after)
        mutated[at:at + 120] = before[at:at + 120]
        negatives.append(rejected(lambda: current_physics(mutated, gba, wsc, addresses),
                                  f"arithmetic-source payload for ID {character}"))
        mutated = bytearray(after)
        struct.pack_into("<I", mutated, 0x485000 + character * 4, BASE + at - 120)
        negatives.append(rejected(lambda: current_physics(mutated, gba, wsc, addresses),
                                  f"old one-record-early pointer for ID {character}"))
        mutated = bytearray(after)
        mutated[at:at + 40], mutated[at + 80:at + 120] = after[at + 80:at + 120], after[at:at + 40]
        negatives.append(rejected(lambda: current_physics(mutated, gba, wsc, addresses),
                                  f"base/evolved row swap for ID {character}"))
    for at, replacement, label in (
        (0x35A3C8, 0xE2888028, "native evolution adds wrong row offset"),
        (0x35A6EC, 0xE2488028, "native de-evolution subtracts wrong row offset"),
        (0x3530D0, 0xE1C416B0, "native constructor stores a narrow pointer"),
    ):
        mutated = bytearray(after)
        struct.pack_into("<I", mutated, at, replacement)
        negatives.append(rejected(lambda: current_physics(mutated, gba, wsc, addresses), label))
    mutated = bytearray(wsc)
    struct.pack_into("<H", mutated, 0x3B8478, 0x001E + 12 * 120)
    negatives.append(rejected(lambda: source_addresses(mutated), "source ID12 replaced by arithmetic offset"))
    mutated = bytearray(wsc)
    mutated[0x7435F2] = 0xBA
    negatives.append(rejected(lambda: source_addresses(mutated), "wrong C2 source bank"))
    mutated = bytearray(after)
    mutated[0x48503C] = 1
    negatives.append(rejected(lambda: exact_diff(before, mutated), "write outside existing payload ownership"))
    need(sha(after) == AFTER, "candidate identity after semantic validation")
    return {
        "schema": 1, "kind": "character-physics-source-routing-verification",
        "input_sha256": BEFORE, "output_sha256": AFTER,
        "source_identities": {"gba": GBA, "wsc15": WSC},
        "source_constructor": [0x7435EC, 0x743612],
        "source_pointer_table": 0x3B8460, "source_pointer_offsets": SOURCE_OFFSETS,
        "source_record_addresses": addresses,
        "native_constructor": [0x083530BC, 0x083530E4],
        "native_pointer_field": 0x60, "native_pointer_bytes": 4,
        "form_extent": {"base_row_bytes": 0x28, "evolved_offset": 0x50,
                        "last_evolved_read": 0x76, "preserved_group_bytes": 0x78,
                        "middle_row_reachability_claimed": False},
        "retail_exact_halfwords": 660, "preserved_id11_exceptions": exceptions,
        "records": records, "historical_source_routing_deltas": deltas,
        "actual_changed_bytes": changed, "pointer_words_changed": 0, "code_bytes_changed": 0,
        "individual_added_halfword_mutations_rejected": halfwords_rejected,
        "negative_cases_rejected": negatives,
        "claim_scope": "static source-routing defect and complete native payload repair; this does not establish the cause of observed runtime corruption or whole-port completion",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav"
             for name in ("before", "after", "gba", "wsc15", "output")), "save files forbidden")
    report = verify(*(getattr(args, name).read_bytes() for name in ("before", "after", "gba", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, indent=2) + "\n"
    args.output.write_text(rendered, encoding="utf-8")
    print(f"[character-physics-routing-verification] PASS {sha(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
