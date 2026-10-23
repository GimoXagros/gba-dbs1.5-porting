#!/usr/bin/env python3
"""Independently verify the source-backed character follow-up table repair.

Reads the five explicitly supplied ROMs only. No builder imports, emulator,
save access, or native service execution. The report has no clock/path fields.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BEFORE = "C50ADCF54D29B327CCF5BFAE21F51784AC2A7A9544DF6093680BDB6387F93DFF"
AFTER = "F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, SITE, TABLE, LIMIT = 0x08000000, 0x36A668, 0x628900, 0x628940
RECORD, CALLBACK = 0x0836A67C, 0x0836AE94


def need(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def sequence(data: bytes, start: int, end: int, expected: list[str], arm=False) -> None:
    cs = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    rows = list(cs.disasm(data[start:end], start + (BASE if arm else 0)))
    need(sum(row.size for row in rows) == end - start, f"instruction extent {start:X}")
    actual = [f"{row.mnemonic} {row.op_str}".strip() for row in rows]
    need(actual == expected, f"instruction contract {start:X}")


def refs(data: bytes, pointer: int) -> list[int]:
    encoded, result, pos = struct.pack("<I", pointer), [], 0
    while True:
        pos = data.find(encoded, pos)
        if pos < 0:
            return result
        if pos % 4 == 0:
            result.append(pos)
        pos += 1


def source_proof(old: bytes, new: bytes, gba: bytes) -> dict:
    need(struct.unpack_from("<12H", old, 0x3A659A) == (0x2022,) * 12, "old 12-row follow-up table")
    need(struct.unpack_from("<15H", new, 0x762780) == (0x27EE,) * 15, "source 15-row follow-up table")
    need(0x3A45B0 + 0x2022 == 0x3A65D2, "old CS offset resolves")
    need(0x75FFD0 + 0x27EE == 0x7627BE, "new CS offset resolves")
    a, b = old[0x3A65D2:0x3A65F2], new[0x7627BE:0x7627DE]
    need(a[:4] == b[:4] == bytes.fromhex("00003700"), "follow-up event 37")
    need(a[8:] == b[8:], "all source non-callback metadata identical")
    need(struct.unpack_from("<HH", a, 4) == (0x11EF, 0xA45B), "old callback far pointer")
    need(struct.unpack_from("<HH", b, 4) == (0x138B, 0x5FFD), "new callback far pointer")
    need(0x3A45B0 + 0x11EF == 0x3A579F, "old callback resolves")
    need(0x75FFD0 + 0x138B == 0x76135B, "new callback resolves")
    old_callback, new_callback = old[0x3A579F:0x3A5800], new[0x76135B:0x7613BC]
    need(old_callback == new_callback, "relocated callback 97-byte body identity")
    need(sha(new_callback) == "0F65E5C92F15761470305E58DA3BCD1F380EFFAFDBBAD16805371667CC7FC9E6", "callback lineage body pin")
    sequence(new, 0x76135B, 0x7613BC, [
        "mov byte ptr [si + 0x5a], 9", "cmp word ptr [si + 0x80], 0", "je 0x761372",
        "or word ptr [si + 8], 1", "mov ax, word ptr [si + 0x80]", "mov byte ptr [si + 0x5b], al",
        "mov ax, word ptr [si + 0x8c]", "mov bx, word ptr [si + 0x8e]",
        "and word ptr [di + 8], 0xbfff", "test word ptr [si + 0xc], 0x4000", "jne 0x76138f",
        "neg ax", "neg bx", "or word ptr [di + 8], 0x4000", "test word ptr [si + 0x8a], 2",
        "je 0x7613a0", "xor word ptr [di + 8], 0x4000", "neg ax", "neg bx",
        "mov word ptr [si + 0x32], ax", "mov word ptr [si + 0x36], bx",
        "mov ax, word ptr [si + 0x90]", "mov bx, word ptr [si + 0x92]",
        "mov word ptr [si + 0x34], ax", "mov word ptr [si + 0x38], bx",
        "or word ptr [si + 6], 1", "push word ptr [si + 0x7e]",
    ])
    sequence(old, 0x3A5800, 0x3A5813, [
        "push 0xa45b", "push 0x1263", "push 0xc00", "push si",
        "lcall 0xa45b, 0xd2c", "add sp, 0xa", "retf",
    ])
    sequence(new, 0x7613BC, 0x7613CF, [
        "push 0x5ffd", "push 0x13ff", "push 0xc00", "push si",
        "lcall 0x5ffd, 0xec8", "add sp, 0xa", "retf",
    ])
    need(struct.unpack_from("<12I", gba, 0x36A62C) == (RECORD,) * 12, "native retail row oracle")
    need(gba[0x36A67C:0x36A69C] == bytes.fromhex("0000370094ae360800003c0610000000183c04004001f4ff40fc320090000000"), "native follow-up record oracle")
    need(u32(gba, 0x36A680) == CALLBACK, "native callback lineage")
    need(sha(gba[0x36AE94:0x36AF38]) == "D5CACEDE073F11F9E3A7D1E3F4AAA4A92909E26B44CB6F92E4C0D8FB1D455D9E", "native callback constructor pin")
    sequence(gba, 0x36AF38, 0x36AF64, [
        "stmdb sp!, {r4}", "stmdb sp!, {fp}", "add r8, pc, #0x1c", "stmdb sp!, {r8}",
        "stmdb sp!, {fp}", "ldrh r8, [r4, #0x94]", "stmdb sp!, {r8}",
        "bl #0x836a69c", "add sp, sp, #0x14", "ldm sp!, {lr}", "bx lr",
    ], arm=True)
    sequence(new, 0x761317, 0x76133A, [
        "mov bx, word ptr [si + 0x84]", "xor ax, ax", "mov al, byte ptr [si + 0x11]",
        "shl ax, 1", "add bx, ax", "mov bx, word ptr cs:[bx]", "mov ax, word ptr [si + 0x94]",
        "shl ax, 5", "add bx, ax", "push cs", "lcall 0x668e, 0", "add sp, 2", "retf",
    ])
    sequence(new, 0x76694D, 0x76695D, [
        "mov ax, word ptr es:[bx + 0xc]", "mov dx, word ptr es:[bx + 0xe]",
        "mov word ptr [si + 0x82], ax", "mov word ptr [si + 0x84], dx",
    ])
    need(struct.unpack_from("<HH", new, 0x76279E + 0xE) == (0x27B0, 0x5FFD), "source metadata follow-up pointer")
    need(0x75FFD0 + 0x27B0 == 0x762780, "source follow-up table producer resolves")
    sequence(new, 0x7628D0, 0x7628E0, [
        "mov bx, 0x2792", "mov bx, word ptr cs:[bx]", "push cs", "lcall 0x668e, 0", "add sp, 2", "retf",
    ])
    return {"source_rows": 15, "old_rows": 12, "source_record": "7627BE", "old_record": "3A65D2",
            "native_record": "0836A67C", "source_callback": "76135B", "old_callback": "3A579F",
            "native_callback": "0836AE94", "callback_identical_bytes": 97,
            "callback_relocated_tail_bytes": 19,
            "initial_table_consumer": "7628D0..7628E0 reads row zero only"}


def check(before: bytes, after: bytes, gba: bytes, old: bytes, new: bytes) -> dict:
    need(len(before) == len(after) == 0x800000, "candidate size")
    evidence = source_proof(old, new, gba)
    for start, end in [(0x36A474, 0x36A48C), (0x36AE08, 0x36AE2C), (0x355604, 0x355644),
                       (0x36AE94, 0x36AF38), (0x36A67C, 0x36A69C)]:
        need(before[start:end] == after[start:end] == gba[start:end], f"native consumer/record retained {start:X}")
    sequence(after, 0x36AE08, 0x36AE2C, [
        "ldr r1, [r4, #0x9c]", "ldrb r0, [r4, #0x11]", "ldr r1, [r1, r0, lsl #2]",
        "ldrsh r0, [r4, #0xaa]", "lsl r0, r0, #5", "add r1, r1, r0",
        "stmdb sp!, {fp}", "bl #0x83555d0", "add sp, sp, #4",
    ], arm=True)
    sequence(after, 0x355604, 0x355610, ["ldr r0, [r1, #4]", "str r0, [r4]", "stmdb sp!, {r5}"], arm=True)
    sequence(after, 0x355634, 0x355644, [
        "ldrsb r0, [r1, #0xb]", "ldr r3, [r1, #0xc]", "strh r0, [r4, #0x98]", "str r3, [r4, #0x9c]",
    ], arm=True)
    sequence(after, 0x36A478, 0x36A480, ["ldr r1, [pc, #0x3c]", "ldr r1, [r1]"], arm=True)
    need(u32(before, SITE) == 0x0836A62C, "predecessor metadata pointer")
    need(before[TABLE:LIMIT] == b"\xff" * (LIMIT - TABLE), "reservation all FF")
    need(refs(before, 0x0836A62C) == [SITE], "unique old metadata reference")
    need(refs(before, 0x0836A5FC) == [0x36A4BC], "initial table sole pointer reference")
    need(u32(before, 0x36A4BC) == 0x0836A5FC, "initial row-zero literal")
    need(before[0x36A5FC:0x36A65C] == after[0x36A5FC:0x36A65C] == gba[0x36A5FC:0x36A65C], "both original tables retained")
    expected = bytearray(before)
    expected[SITE:SITE + 4] = struct.pack("<I", BASE + TABLE)
    expected[TABLE:TABLE + 60] = struct.pack("<15I", *([RECORD] * 15))
    need(after == expected, "exact two spans and no other writes")
    need(refs(after, BASE + TABLE) == [SITE], "unique new table reference")
    inverse = bytearray(after)
    inverse[SITE:SITE + 4] = before[SITE:SITE + 4]
    inverse[TABLE:TABLE + 60] = before[TABLE:TABLE + 60]
    need(inverse == before, "full inverse")
    inbound = []
    # Check every byte alignment for encoded ROM pointers, as well as aligned
    # ARM branch and literal-access encodings. This is a conservative scan of
    # bytes, not a claim to have reconstructed every indirect control flow.
    for off in range(len(before) - 3):
        if before[off + 3] == 8 and BASE + TABLE <= u32(before, off) < BASE + LIMIT:
            inbound.append((off, "encoded pointer"))
    for off in range(0, len(before) - 3, 4):
        word = u32(before, off)
        if word & 0x0E000000 == 0x0A000000 and word >> 28 != 15:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 1 << 24
            target = BASE + off + 8 + imm * 4
            if BASE + TABLE <= target < BASE + LIMIT:
                inbound.append((off, "ARM branch"))
        if word >> 28 != 15 and word & 0x0E1F0000 == 0x041F0000:
            delta = (word & 4095) * (1 if word & 0x800000 else -1)
            if TABLE <= off + 8 + delta < LIMIT:
                inbound.append((off, "ARM PC-relative access"))
    need(not inbound, "no encoded predecessor pointers, ARM branches or literal accesses into reservation")
    routed = []
    for ident in range(15):
        pointer = u32(after, u32(after, SITE) - BASE + ident * 4)
        need(pointer == RECORD and u32(after, pointer - BASE + 4) == CALLBACK, f"native route ID {ident}")
        routed.append(pointer)
    need(u32(before, 0x36A62C + 14 * 4) == 0x063C0000, "observed ID14 overread reproduced")
    evidence.update({"status": "PASS", "write_spans": [{"offset": f"{SITE:06X}", "size": 4},
                    {"offset": f"{TABLE:06X}", "size": 60}], "written_bytes": 64,
                    "changed_bytes": sum(x != y for x, y in zip(before, after)),
                    "verified_routes": len(routed), "full_inverse": True, "reservation_bytes": LIMIT - TABLE,
                    "old_ID14_result": "063C0000", "new_ID14_result": "0836A67C",
                    "runtime": "Not executed by this verifier; callback services are not simulated."})
    return evidence


def negative_tests(before, after, gba, old, new) -> list[str]:
    failures = []
    def reject(label, *, candidate=None, source=None, previous=None):
        try:
            check(previous if previous is not None else before,
                  candidate if candidate is not None else after, gba, old,
                  source if source is not None else new)
        except ValueError:
            failures.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    for ident in range(15):
        changed = bytearray(after)
        struct.pack_into("<I", changed, TABLE + 4 * ident, 0x0836A65C)
        reject(f"wrong record in row {ident}", candidate=bytes(changed))
    for off, label in [(SITE, "wrong producer pointer"), (TABLE + 60, "padding overwrite"),
                       (0x36A67C, "native record altered"), (0x36AE10, "ID consumer altered"),
                       (0x355608, "callback writer altered"), (0x100, "unrelated ROM write")]:
        changed = bytearray(after); changed[off] ^= 1
        reject(label, candidate=bytes(changed))
    for off, label in [(0x762780 + 28, "wrong source ID14 row"), (0x7627BE + 4, "wrong source callback"),
                       (0x76135B, "source callback body changed"), (0x76131D, "source ID consumer changed"),
                       (0x76279E + 14, "source metadata pointer changed")]:
        changed = bytearray(new); changed[off] ^= 1
        reject(label, source=bytes(changed))
    changed = bytearray(before); changed[TABLE] = 0
    reject("occupied predecessor reservation", previous=bytes(changed))
    reject("truncated candidate", candidate=after[:-1])
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("before", "after", "gba", "old", "new", "output"):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    paths = [args.before, args.after, args.gba, args.old, args.new]
    need(all(p.suffix.lower() in (".gba", ".wsc") for p in paths), "explicit ROM inputs only")
    data = [p.read_bytes() for p in paths]
    for payload, expected in zip(data, (BEFORE, AFTER, GBA, OLD, NEW)):
        need(sha(payload) == expected, "input SHA-256")
    report = check(*data)
    report["negative_tests"] = negative_tests(*data)
    report["negative_count"] = len(report["negative_tests"])
    report["input_sha256"] = dict(zip(("before", "after", "gba", "old", "new"), map(sha, data)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    args.output.write_bytes(encoded)
    print(f"PASS: 15 source-backed routes, {report['negative_count']} negative cases; report {sha(encoded)}")


if __name__ == "__main__":
    main()
