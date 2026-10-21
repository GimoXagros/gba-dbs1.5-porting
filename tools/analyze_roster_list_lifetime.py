#!/usr/bin/env python3
"""Read-only source roster order and actual native list-owner inventory.

No generator imports, emulator, or save access. This records the pre-repair
state and distinguishes list reads from other users of the shared address.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

INPUT = "7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, OWNER = 0x08000000, 0x03004710
POOLS = (0x1CE98, 0x1D5B4, 0x8187C, 0x81ED0, 0x81EEC, 0x81EF0,
         0x81EF4, 0x82090, 0x82430, 0x83290, 0x832EC, 0x89730,
         0x8A4A8, 0x8A4F8, 0x8A680, 0x8ADAC, 0x8B308, 0x4A5C90,
         0x5CD32C, 0x5E71A8, 0x5E753C)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def arm(data, at, expected):
    actual = [f"{i.mnemonic} {i.op_str}" for i in
              Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[at:at + 4 * len(expected)], BASE + at)]
    need(actual == expected, f"native instruction contract {at:X}: {actual}")


def analyze(candidate, gba, source):
    need((sha(candidate), sha(gba), sha(source)) == (INPUT, GBA, SOURCE), "fixed ROM identities")
    source_slice = source[0x7787DB:0x778847]
    need(sha(source_slice) == "9BABC5510A2FADE32E501D968E337747C7BCD67168D79453132DC1556187D263",
         "complete source list producer")
    listing = [dict(raw=0x7787DB + i.address, mnemonic=i.mnemonic, operands=i.op_str)
               for i in Cs(CS_ARCH_X86, CS_MODE_16).disasm(source_slice, 0)]
    need(source[0x7787E3:0x7787EC] == bytes.fromhex("b9070083c1045133d2"), "source eleven initial IDs")
    need(source[0x7787F3:0x7787FA] == bytes.fromhex("26f6452501750d"), "source alternate-mode gate")
    need(source[0x7787FA:0x778807] == bytes.fromhex("b90200ba0d008914424646e2f9"), "source IDs13 and14")
    need(source[0x77881C:0x778826] == bytes.fromhex("268a4519ba0b00bb0100"), "source unlock byte and ID11")
    need(source[0x778830:0x778840] == bytes.fromhex("a9100074058914464641d1e8424b75f0"), "source unlock loop")
    source_cases = []
    for alternate in (0, 1):
        for unlock in (0, 0x10, 0x20, 0x30):
            ids = list(range(11)) + ([] if alternate else [13, 14])
            if unlock & 0x10:
                ids.append(11)
            if not alternate and unlock & 0x20:
                ids.append(12)
            source_cases.append(dict(alternate_bit=alternate, unlock_bits=unlock,
                                     ids=ids, maximum=len(ids) - 1))
    actual_pools = tuple(at for at in range(len(candidate) - 3) if word(candidate, at) == OWNER)
    need(actual_pools == POOLS, "whole-ROM unaligned owner pointer population")
    interiors = [at for at in range(len(candidate) - 3) if OWNER < word(candidate, at) < OWNER + 0x20]
    need(not interiors, "no separate encoded list-interior pointers")
    loads = []
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    for at in range(0, len(candidate) - 3, 4):
        value = word(candidate, at)
        if value >> 28 == 15 or value & 0x0F7F0000 != 0x051F0000:
            continue
        pool = at + 8 + (1 if value & 0x800000 else -1) * (value & 0xFFF)
        if pool in POOLS:
            insn = next(engine.disasm(candidate[at:at + 4], BASE + at))
            loads.append(dict(raw=at, pool=pool, instruction=f"{insn.mnemonic} {insn.op_str}"))
    indexed = (
        (0x81D04, ["ldr r4, [pc, #0x1e0]", "add r4, r4, r1, lsl #1", "ldrh r1, [r4]"], "palette variant"),
        (0x81FF4, ["ldr r4, [pc, #0x94]", "add r4, r4, r1, lsl #1", "ldrh r1, [r4]"], "confirmed character"),
        (0x83230, ["and r1, r1, #0xff", "add r1, r1, r1", "ldr r8, [pc, #0x50]", "ldrh r1, [r8, r1]"], "portrait"),
    )
    for raw, expected, _ in indexed:
        arm(candidate, raw, expected)
        need(candidate[raw:raw + len(expected) * 4] == gba[raw:raw + len(expected) * 4], "retail list consumer unchanged")
    # Native state+18 stores the same presentation pointer prepared from the
    # current task+18. Later input reads it; it is not unused list capacity.
    arm(candidate, 0x82328, ["ldr r8, [pc, #0xf4]", "ldr r0, [r8]", "add r0, r0, #0x18", "mov r4, r0"])
    need(word(candidate, 0x82424) == 0x0300133C, "actual task-slot owner")
    arm(candidate, 0x8240C, ["ldr r5, [pc, #0x1c]", "str r0, [r5, #0x18]"])
    arm(candidate, 0x81DBC, ["ldr r5, [pc, #0x130]", "ldr r0, [r5, #0x18]"])
    arm(candidate, 0x4A5C6C, ["ldr r4, [pc, #0x1c]", "add r1, r1, #1", "strh r1, [r4, #0x1e]"])
    # Other register-indexed halfword loads in the selection animation block
    # are positively based on nearby ROM tables, not the list owner.
    exclusions = ((0x825B4, "add r8, pc, #0x1e", 0x825DA),
                  (0x82654, "sub r8, pc, #0x84", 0x825D8),
                  (0x82698, "sub r8, pc, #0xcc", 0x825D4),
                  (0x826B4, "sub r8, pc, #0xe6", 0x825D6))
    for at, instruction, target in exclusions:
        arm(candidate, at, [instruction])
        need(target < 0x800000, "ROM table exclusion")
    return dict(input_sha256=INPUT, source_producer=dict(raw=0x7787DB, end=0x778847,
                sha256=sha(source_slice), listing=listing), source_cases=source_cases,
                literal_sites=POOLS, encoded_literal_loads=loads, interior_pointer_sites=[],
                indexed_list_consumers=[dict(raw=p, role=role) for p, _, role in indexed],
                fixed_selection_state_consumers={"cached_ID_plus1": [0x81B68, 0x81DA0, 0x832D0, 0x4A5C6C],
                                                 "presentation_pointer": [0x81DBC, 0x8240C]},
                excluded_ROM_indexed_loads=[dict(raw=p, base_raw=t) for p, _, t in exclusions],
                overlap=dict(first_bad_index=12, native_pointer_address=OWNER + 0x18,
                             index12_halfword=OWNER + 24, index13_halfword=OWNER + 26),
                scope="Complete encoded owner/interior pointer inventory plus positive selection code contracts; other-mode owners are not roster consumers",
                current_policy_limit="Four proposed normal-mode unlock views reproduce source alternate_bit=0; source alternate_bit=1 remains outside existing temporary roster policy",
                provided_save_accessed=False, emulator_launched=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(p.suffix.lower() != ".sav" for p in vars(args).values()), "save paths forbidden")
    report = analyze(args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS " + sha(args.output.read_bytes()))


if __name__ == "__main__":
    main()
