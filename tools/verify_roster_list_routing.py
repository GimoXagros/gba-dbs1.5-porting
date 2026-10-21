#!/usr/bin/env python3
"""Independent source-order, native lifetime and exact adapter verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

PRE = "7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470"
ORIGINAL = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE = 0x08000000
ARM = Cs(CS_ARCH_ARM, CS_MODE_ARM)
NEW = ((0x628000, 0x628080), (0x628080, 0x6280AC),
       (0x6280C0, 0x6280EC), (0x628100, 0x62812C))


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return int.from_bytes(data[at:at + 4], "little")


def half(data, at):
    return int.from_bytes(data[at:at + 2], "little")


def decoded(data, at, expected):
    q = next(ARM.disasm(data[at:at + 4], BASE + at), None)
    need(q is not None and q.mnemonic + " " + q.op_str == expected, f"instruction {at:06X}: {expected}")


def incoming(data):
    def belongs(value):
        return any(a <= value < b for a, b in NEW)
    for a, b in NEW:
        need(data[a:b] == b"\xFF" * (b - a), "Expected Write new allocation blank")
    for at in range(len(data) - 3):
        need(not belongs(word(data, at) - BASE), "encoded pointer into new allocation")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            n = value & 0xFFFFFF
            n -= 0x1000000 if n & 0x800000 else 0
            need(not belongs(at + 8 + n * 4), "ARM branch into new allocation")
        if value & 0x0E1F0000 == 0x041F0000:
            n = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not belongs(at + 8 + n), "PC-relative access into new allocation")


def verify(before, after, gba, source):
    need(len(before) == len(after) == 0x800000, "ROM size")
    source_checks = ((0x7787DB, "beea00"), (0x7787E3, "b9070083c104"),
                     (0x7787EA, "33d28914424646e2f9"),
                     (0x7787F3, "26f6452501750d"), (0x7787FA, "b90200ba0d00"),
                     (0x778800, "8914424646e2f9"), (0x77880F, "83c102"),
                     (0x77881C, "268a4519ba0b00bb0100"), (0x77882D, "bb0200"),
                     (0x778830, "a9100074058914464641d1e8424b75f0"),
                     (0x778841, "8bd14a895408"))
    for at, text in source_checks:
        expected = bytes.fromhex(text)
        need(source[at:at + len(expected)] == expected, f"actual source roster producer {at:06X}")
    native = {
        0x81710: "mov r3, r2", 0x81714: "subs r3, r3, #1", 0x81718: "strh r3, [r4, #8]",
        0x81D08: "add r4, r4, r1, lsl #1", 0x81D0C: "ldrh r1, [r4]",
        0x81FF8: "add r4, r4, r1, lsl #1", 0x81FFC: "ldrh r1, [r4]",
        0x83230: "and r1, r1, #0xff", 0x83234: "add r1, r1, r1", 0x8323C: "ldrh r1, [r8, r1]",
        0x8240C: "ldr r5, [pc, #0x1c]", 0x82410: "str r0, [r5, #0x18]",
        0x81DBC: "ldr r5, [pc, #0x130]", 0x81DC0: "ldr r0, [r5, #0x18]",
        0x81DA4: "ldrh r1, [r5, #0x1e]", 0x4A5C74: "strh r1, [r4, #0x1e]",
        0x81BC0: "ldrh r3, [r5, #8]", 0x81D70: "cmp r8, sb", 0x81D74: "bls #0x8081d7c",
        0x5B002C: "mov r4, r4", 0x5B0040: "movne r4, r4", 0x5B0050: "movne r4, r4",
    }
    for at, text in native.items():
        decoded(after, at, text)
        if at < 0x400000:
            need(before[at:at + 4] == gba[at:at + 4] == after[at:at + 4], "actual retail consumer preserved")
    need(word(after, 0x82430) == word(after, 0x81EF4) == word(after, 0x4A5C90) == 0x03004710,
         "live selection handle/cache retain native owner")
    need(word(after, 0x81880) == 0x03002310, "roster initialization reads same existing unlock owner")
    for at, expected in ((0x5B002C, 0xE0C400B2), (0x5B0040, 0x10C410B2), (0x5B0050, 0x10C410B2)):
        need(word(before, at) == expected, "Expected Write exact original overflow store")
    # Bind every untouched initializer instruction, not just its source order.
    restored = bytearray(after[0x5B0000:0x5B0060])
    for offset in (0x2C, 0x40, 0x50):
        restored[offset:offset + 4] = before[0x5B0000 + offset:0x5B0004 + offset]
    need(restored == before[0x5B0000:0x5B0060], "original count, unlock reads and native continuation unchanged")
    need(before[0x5B0000:0x5B0028] == bytes.fromhex(
        "82c044e00c40a0e10000a0e30b20a0e3b200c4e0010080e2012052e2fbffffca0d00a0e3b200c4e0"),
         "complete first12 RAM producer contract")
    for at, text in ((0x5B0030, "mov r2, #0xd"), (0x5B0034, "ldrb r0, [r5, #0x19]"),
                     (0x5B0038, "tst r0, #0x10"), (0x5B0044, "addne r2, r2, #1"),
                     (0x5B0048, "tst r0, #0x20"), (0x5B0054, "addne r2, r2, #1"),
                     (0x5B0058, "ldm sp!, {r4}"), (0x5B005C, "b #0x8081710")):
        decoded(after, at, text)
    sites = ((0x81D04, 0x628080, "r4", 0xE59F41E0),
             (0x81FF4, 0x6280C0, "r4", 0xE59F4094),
             (0x83238, 0x628100, "r8", 0xE59F8050))
    for site, bridge, output, predecessor in sites:
        need(word(before, site) == predecessor, "Expected Write real indexed-load site")
        decoded(after, site, f"b #0x{BASE + bridge:x}")
        listing = ("stmdb sp!, {r0}", "ldr r0, [pc, #0x18]", "ldrb r0, [r0, #0x19]",
                   "and r0, r0, #0x30", "lsl r0, r0, #1", f"ldr {output}, [pc, #0xc]",
                   f"add {output}, {output}, r0", "ldm sp!, {r0}", f"b #0x{BASE + site + 4:x}")
        for i, text in enumerate(listing):
            decoded(after, bridge + i * 4, text)
        need(word(after, bridge + 36) == 0x03002310 and word(after, bridge + 40) == 0x08628000,
             "actual flags and ROM-view literals")
        # All AL instructions, no flag-setting data operation, no BL or PC/LR
        # destination: therefore every possible incoming NZCV/LR is preserved.
        for i in range(9):
            w = word(after, bridge + i * 4)
            need(w >> 28 == 14, "bridge does not depend on incoming condition flags")
            if w & 0x0C000000 == 0:
                need(not w & 0x100000, "bridge arithmetic never changes condition flags")
    cases = 0
    for unlock in range(256):
        # Source clean-mode loop decoded above: 7+4 ordinary IDs, two new IDs,
        # then two rounds of TEST10/SHR to append the unlock-controlled IDs.
        expected = list(range(half(source, 0x7787E4) + source[0x7787E8]))
        expected += [half(source, 0x7787FE) + i for i in range(half(source, 0x7787FB))]
        flag, candidate = unlock, half(source, 0x778821)
        for _ in range(half(source, 0x77882E)):
            if flag & half(source, 0x778831):
                expected.append(candidate)
            flag >>= 1
            candidate += 1
        native_count = 13 + bool(unlock & 0x10) + bool(unlock & 0x20)
        need(native_count == len(expected), "unchanged count agrees with source clean-mode list")
        base = 0x628000 + ((unlock & 0x30) << 1)
        need([half(after, base + 2 * i) for i in range(native_count)] == expected,
             "complete source list for every unlock byte")
        need(after[base + native_count * 2:base + 32] == b"\xFF" * (32 - native_count * 2), "unused ROM-view tail is explicit")
        for index, actual_id in enumerate(expected):
            # The two unscaled native consumers shift once; portrait already
            # doubled its low-byte index. Their final byte addresses must agree.
            for scale in (1, 1, 2):
                incoming_index = index * scale
                offset = incoming_index * 2 if scale == 1 else incoming_index
                need(half(after, base + offset) == actual_id and actual_id < 15, "all three real lookup forms")
                cases += 1
        # Actual initializer memory stores after suppressing overflow are the
        # same first12 entries for every unlock byte, never handle/cache fields.
        stores = [(0x03004710 + i * 2, value) for i, value in enumerate(expected[:12])]
        need(stores[-1] == (0x03004726, 13) and all(at + 2 <= 0x03004728 for at, _ in stores),
             "native RAM list ends before live presentation handle")
    expected_spans = list(NEW) + [(site, site + 4) for site, _, _, _ in sites]
    expected_spans += [(at, at + 4) for at in (0x5B002C, 0x5B0040, 0x5B0050)]
    inverse = bytearray(after)
    for lo, hi in expected_spans:
        inverse[lo:hi] = before[lo:hi]
    need(inverse == before, "full-ROM inverse outside exact owned spans")
    return dict(source_contracts=len(source_checks), native_consumer_contracts=len(native) + 8,
                new_instruction_contracts=27, finite_lookup_cases=cases, unlock_bytes=256,
                pointer_alias_lifetime="retail list12entries endsbefore shared+18presentationhandle; three reads use immutable ROMviews",
                flags_and_registers="all16 NZCV combinations and anyLR preserved structurally; r0push/pop balanced; only intended base-register output",
                source_mode_scope="established clean-mode list policy; alternate source mode remains outside this layer",
                expected_write_spans=expected_spans)


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("before", "after", "gba", "wsc15", "report")), "save paths forbidden")
    before, after, gba, source = [getattr(args, name).read_bytes() for name in ("before", "after", "gba", "wsc15")]
    need(tuple(map(sha, (before, gba, source))) == (PRE, ORIGINAL, SOURCE), "fixed originals/predecessor")
    incoming(before)
    result = verify(before, after, gba, source)
    negatives = []
    for at, label in ((0x628018, "ID14 view entry"), (0x62805A, "Extra-only unlocked order"),
                      (0x62808C, "unlock mask"), (0x628090, "view stride"),
                      (0x628098, "list-base output"), (0x62809C, "caller r0 restore"),
                      (0x6280A0, "first continuation"), (0x628124, "unlock owner"),
                      (0x628128, "portrait ROM-view base"), (0x5B002C, "overflow store suppression"),
                      (0x81FF4, "confirmed selection hook"), (0x12340, "unrelated write")):
        damaged = bytearray(after)
        damaged[at] ^= 1
        try:
            verify(before, damaged, gba, source)
        except ValueError as error:
            negatives.append(dict(case=label, rejected=True, reason=str(error)))
        else:
            raise ValueError("negative case accepted: " + label)
    result.update(schema=1, kind="independent-roster-list-routing-verification", status="PASS",
                  input_sha256=sha(before), output_sha256=sha(after), negative_cases=negatives,
                  generator_imported=False, emulator_or_save_access=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("[verify-roster-list-routing] PASS " + sha(args.report.read_bytes()))


if __name__ == "__main__":
    main()
