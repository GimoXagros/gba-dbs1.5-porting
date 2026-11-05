#!/usr/bin/env python3
"""Extend the disconnected Shoot front through the two source SRAM stores.

The existing native EEPROM API represents the two words in block 25 buffer
halfwords +0/+2. Each ordered read/modify/write preserves its other six bytes.
Functional, initialized, serialized storage is a precondition; failed-device
equivalence is not claimed and no new retry state or external entry is added.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, no_inbound
from analyze_shoot_eeprom_storage import RANGES, contracts, census

PARENT = "CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7"
ENTRY, START, EXTENSION, END = 0x629800, 0x629818, 0x629820, 0x629880
HEAD = (0xE92D4800, 0xE3A0B000, 0xEBFFFFBC, 0xEBFE5DFB, 0xEBFE5FBA, 0xEBFE6AF9)
WORDS = (
    0xE92D100F, 0xE24DD008,                         # save scratch registers; eight-byte block
    0xE3A00019, 0xE1A0100D, 0xEBF550CC,             # read block 25
    0xE3500000, 0x1A000004,                         # never write an unread buffer
    0xE3A00000, 0xE1CD00B0,                         # source 73E2: first halfword only
    0xE3A00019, 0xE1A0100D, 0xEBF550C2,             # native bounded write/verify
    0xE3A00019, 0xE1A0100D, 0xEBF550C2,             # reread actual block for the second store
    0xE3500000, 0x1A000004,
    0xE3A00000, 0xE1CD00B2,                         # source 73E9: second halfword only
    0xE3A00019, 0xE1A0100D, 0xEBF550B8,
    0xE28DD008, 0xE8BD100F, 0xE8BD4800, 0xE12FFF1E,
)
OWNER_GUARDS = (
    (0x629500, 0x629518, "7A42F8C8D7AA3EDFDB669182B498F1EC0A6091BCECA491B2BAD4CF55ECD2F94A"),
    (0x629600, 0x629680, "51739551E0633D3A3FC58ECC6F5B2E9DDCB164E12E57FCACFEE63FEA3AB1ECF0"),
)
RETAIL_CALLERS = ((0x8B368, 0x8B3A0), (0x8B4BC, 0x8B4DC),
                  (0xC07B8, 0xC07D8), (0xC0EC0, 0xC0EE0), (0x33EDF4, 0x33EE14))
PRIMARY_REVISION = "4b01295838ea89e3f1355bbe4cb5cf98aa6108cd"
PRIMARY_URLS = ["https://github.com/libretro/beetle-wswan-libretro/blob/" + PRIMARY_REVISION + "/" + path
                for path in ("libretro.c", "mednafen/wswan/wswan-memory.c")]


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def target(at, encoded):
    delta = encoded & 0xFFFFFF
    return BASE + at + 8 + (delta - (0x1000000 if delta & 0x800000 else 0)) * 4


def payload():
    return struct.pack("<26I", *WORDS)


def owners(image):
    for start, end, expected in OWNER_GUARDS:
        need(sha(image[start:end]) == expected, "positive ARM owner " + hex(start))
    need(all(target(at, word(image, at)) == 0x08629500 and word(image, at) >> 24 == 0xEB
             for at in (0x36D28C, 0x36D2F8)), "both ARM manager calls select the priority helper")
    need(word(image, 0x62967C) == 0x08629600, "waterfall callback selects the owned ARM entry")
    need(word(image, 0x629510) == 0xEAEAA1D8 and target(0x629510, word(image, 0x629510)) == 0x080D1C78,
         "first apparent Thumb ADR is an ARM tail branch outside the extension")
    need(word(image, 0x629620) == 0xEBE7A493 and target(0x629620, word(image, 0x629620)) == 0x08012874,
         "second apparent Thumb ADR is an ARM constructor call outside the extension")


def ownership(image):
    owners(image)
    expected = ("pre-existing ownership of proposed writes: "
                "[('Thumb literal/ADR', 6460688, 140679284), ('Thumb literal/ADR', 6460960, 140679280)]")
    try:
        no_inbound(image, ((EXTENSION, END),))
    except ValueError as error:
        need(str(error) == expected, "unclassified extension ownership: " + str(error))
    else:
        raise ValueError("expected positively owned ARM/Thumb interpretation candidates missing")
    return dict(all_alignment_mirrored_pointers=True, arm_thumb_static_references=True,
                external_references=[], classified_ARM_words=["629510:EAEAA1D8", "629620:EBE7A493"],
                boundary="Finite encoded-reference proof; arbitrary computed aliases are not excluded.")


def dependencies(before, gba, source):
    need(struct.unpack_from("<6I", before, ENTRY) == HEAD, "retained first 24 bytes and source phase order")
    need(before[START:EXTENSION] == bytes.fromhex("0048bde81eff2fe1"), "exact original return")
    need(before[EXTENSION:END] == b"\xff" * (END - EXTENSION), "unused 96-byte extension")
    need(before[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer remains absent")
    need(source[-16:] == bytes.fromhex("eafc06ff4f0001003000080204003e44"), "source cartridge header selects 32-KiB SRAM")
    need(source[0x747CD6:0x747CF0] == bytes.fromhex("b800108ec026c7066006000026c706d83c000026c706da3c0000"),
         "ES1000 and the ordered distinct halfword stores")
    need(source[0x773143:0x77314D] == bytes.fromhex("9a68719040c744422000"),
         "source caller continues after initialization without a storage-status branch")
    for start, end in RANGES + RETAIL_CALLERS:
        need(before[start:end] == gba[start:end], "retained native storage/ordinary caller " + hex(start))
    owners(before)
    return contracts(before)


def bank_identity(source):
    need(source[-5] == 2, "fixed source SRAM geometry")
    count = 0
    for bank in range(256):
        for linear in (*range(0x13CD8, 0x13CDC), *range(0x1BCD8, 0x1BCDC)):
            need(((linear & 0xFFFF) | (bank << 16)) & 0x7FFF == linear & 0x7FFF,
                 "all C1 values and both aperture aliases use the same SRAM bytes")
            count += 1
    return dict(source_header_code="02", SRAM_bytes=32768, cases=count,
                backing_bytes_half_open=["3CD8", "3CDC"], C1_affects_identity=False,
                primary_revision=PRIMARY_REVISION, primary_urls=PRIMARY_URLS,
                scope="Standard retail SRAM mapping; no source-observer, reset-initial-value or hardware-run claim.")


def validate(before, after):
    need(len(before) == len(after) == 0x800000, "fixed eight-MiB image")
    need(after[ENTRY:START] == before[ENTRY:START], "first 24 bytes preserved")
    need(after[START:END] == payload(), "exact reviewed 26 ARM words")
    inverse = bytearray(after)
    inverse[START:END] = before[START:END]
    need(inverse == before, "full inverse; every other code, caller, resource and save service retained")


def abi_and_rmw():
    """Finite instruction algebra with abstract API outcomes, not game execution."""
    cases = 0
    for seed, read_status, write_status in itertools.product(range(4),
            itertools.product((0, 0x80FF), repeat=2), itertools.product((0, 0x8000, 0xC001), repeat=2)):
        incoming = [0x11220000 + n * 0x101 + seed for n in range(15)]
        incoming[13], incoming[14] = 0x03007F00 - seed * 4, 0x0833FD1C | (seed & 1)
        regs, stack = incoming.copy(), {}
        def put(at, value, size):
            for n in range(size):
                stack[at + n] = (value >> (8 * n)) & 255
        def get(at, size):
            return sum(stack[at + n] << (8 * n) for n in range(size))
        regs[13] -= 8
        put(regs[13], incoming[11], 4)
        put(regs[13] + 4, incoming[14], 4)
        regs[11], regs[14] = 0, BASE + START
        original = bytes((seed * 71 + n * 29 + 7) & 255 for n in range(8))
        block, events, snapshots = bytearray(original), [], []
        phase, at, equal, minimum_sp = -1, START, False, regs[13]
        while at < END:
            encoded = WORDS[(at - START) // 4]
            following = at + 4
            if encoded in (0xE92D100F, 0xE8BD100F, 0xE8BD4800):
                selected = [n for n in range(15) if encoded & (1 << n)]
                if encoded == 0xE92D100F:
                    regs[13] -= len(selected) * 4
                    for n, reg in enumerate(selected): put(regs[13] + n * 4, regs[reg], 4)
                else:
                    for n, reg in enumerate(selected): regs[reg] = get(regs[13] + n * 4, 4)
                    regs[13] += len(selected) * 4
            elif encoded == 0xE24DD008: regs[13] -= 8
            elif encoded == 0xE28DD008: regs[13] += 8
            elif encoded in (0xE3A00019, 0xE3A00000): regs[0] = encoded & 255
            elif encoded == 0xE1A0100D: regs[1] = regs[13]
            elif encoded == 0xE3500000: equal = regs[0] == 0
            elif encoded == 0x1A000004:
                if not equal: following = target(at, encoded) - BASE
            elif encoded in (0xE1CD00B0, 0xE1CD00B2):
                need(regs[0] == 0, "source halfword clear value")
                put(regs[13] + (encoded & 15), regs[0], 2)
            elif encoded >> 24 == 0xEB:
                need(regs[0] == 25 and regs[1] == regs[13] and regs[13] % 4 == 0,
                     "actual service block and word-aligned buffer arguments")
                destination = target(at, encoded)
                if destination == 0x0837DB60:
                    phase += 1
                    need(phase < 2, "exactly two ordered reads")
                    status = read_status[phase]
                    snapshots.append(bytes(block))
                    if status == 0:
                        for n, value in enumerate(block): stack[regs[1] + n] = value
                    events.append(("read", phase))
                else:
                    need(destination == 0x0837DB54 and read_status[phase] == 0,
                         "writer follows a successful corresponding read")
                    actual = bytes(stack[regs[1] + n] for n in range(8))
                    expected = bytearray(snapshots[phase])
                    expected[phase * 2:phase * 2 + 2] = b"\0\0"
                    need(actual == expected, "selected halfword zero; other six actual-read bytes preserved")
                    status = write_status[phase]
                    # Failed devices may apply a prefix; the second read must use actual contents.
                    extent = 8 if status == 0 else seed
                    block[:extent] = actual[:extent]
                    events.append(("write", phase))
                for reg in (0, 1, 2, 3, 12): regs[reg] = 0xDEAD0000 + at + reg
                regs[0], regs[14] = status, BASE + following
            elif encoded == 0xE12FFF1E:
                need(regs == incoming, "all caller registers, SP and return ISA bit restored")
            else:
                raise ValueError("instruction outside reviewed finite ABI model")
            minimum_sp = min(minimum_sp, regs[13])
            at = following
        expected_events = [(operation, n) for n in range(2)
                           for operation in (("read", "write") if read_status[n] == 0 else ("read",))]
        need(events == expected_events and incoming[13] - minimum_sp == 36, "source order, failure skips and 36-byte frame")
        need(bytes(block[4:]) == original[4:], "unassigned API buffer halfwords retained")
        if not any(read_status + write_status):
            need(bytes(block) == bytes(4) + original[4:], "both source stores succeed on functional storage")
        cases += 1
    return dict(cases=cases, entry_stack_bytes=36, source_halfword_order=[0, 2],
                caller_registers_preserved="r0-r12,LR,SP", flags="clobbered", failed_device_equivalence=False)


def negatives(before, after, gba, source):
    rejected = []
    def reject(label, operation):
        try: operation()
        except ValueError: rejected.append(label)
        else: raise ValueError("accepted mutation: " + label)
    for at in (*range(START, END), ENTRY, END, 0x5C7800, 0x352B54, 0x633640):
        wrong = bytearray(after); wrong[at] ^= 1
        reject("output byte " + hex(at), lambda: validate(before, wrong))
    for at in (ENTRY, START, EXTENSION, END - 1, 0x5C7800, 0x629510, 0x629620,
               0x36D28C, 0x36D2F8, *(a for a, _ in RANGES), *(a for a, _ in RETAIL_CALLERS)):
        wrong = bytearray(before); wrong[at] ^= 1
        reject("native dependency " + hex(at), lambda: dependencies(wrong, gba, source))
    for at in (0x7FFFFB, 0x747CD7, 0x747CE4, 0x747CE9, 0x773143):
        wrong = bytearray(source); wrong[at] ^= 1
        reject("source contract " + hex(at), lambda: dependencies(before, gba, wrong))
    wrong = bytearray(before)
    struct.pack_into("<I", wrong, END + 1, 0x0A629840)
    reject("new unaligned mirrored pointer into extension", lambda: ownership(wrong))
    return rejected


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW), "exact predecessor and three originals")
    native = dependencies(before, gba, source)
    api = census(before)
    bank = bank_identity(source)
    owner = ownership(before)
    algebra = abi_and_rmw()
    after = bytearray(before)
    after[START:END] = payload()
    validate(before, after)
    rejected = negatives(before, after, gba, source)
    return bytes(after), dict(schema=1, status="PASS", kind="disconnected-shoot-initializer-storage",
        input_sha256=PARENT, output_sha256=sha(after), output_bytes=len(after), native_entry="08629800",
        source_range=["4090:7168", "4090:73F0"], new_source_range=["747CE2", "747CF0"],
        declared_bytes=104, new_reservation_bytes=96, entry_bytes=128,
        changed_bytes=sum(a != b for a, b in zip(before, after)), payload_sha256=sha(payload()),
        writes=[dict(start=f"{START:06X}", end=f"{END:06X}", before_hex=before[START:END].hex(), after_hex=payload().hex())],
        first_24_bytes_preserved=True, full_inverse=True, external_entry_added=False, full_initializer_absent=True,
        new_RAM_bytes=0, native_storage=native, predecessor_API_census=api, source_bank_identity=bank, ownership=owner,
        storage_owner=dict(block=25, source_3CD8_API_buffer_halfword=0, source_3CDA_API_buffer_halfword=2,
            retained_API_buffer_bytes=[4, 8], byte_coordinate_system="Native API buffer coordinates; no raw save-file or wire byte-order claim."),
        abi=algebra, synchronous_storage_stack_bytes=dict(entry=36, read_with_DMA=204,
            write_with_timer_start=256, verification_read_with_DMA=240, IRQ_and_full_scene_bound_proved=False),
        dependencies=[dict(start=f"{a:06X}", end=f"{z:06X}", sha256=sha(before[a:z])) for a, z in RANGES + RETAIL_CALLERS],
        negative_cases=len(rejected), rejected_mutations=rejected,
        preconditions=["Native EEPROM startup selected the retained 512-byte geometry; storage is functional.",
            "Serialized main-task ownership of native DMA3, timer2 and EEPROM service; no concurrent operation.",
            "Retained scene/object/renderer preconditions and word-aligned stack with the inspected synchronous call-chain space."],
        limits=["Each nonzero read skips that corresponding write. Writes retain the native at-most-three attempts; final statuses are not exposed by the retained scene ABI.",
            "Failed-device data integrity, source failure equivalence, interrupt-time intermediate observation and cycle timing are not claimed.",
            "Known retail save callers discard final status; existing Options-language callers separately handle errors and are unchanged.",
            "Future actual source observers must use this same persistent owner; no global observer closure or dead-store conclusion.",
            "Full initializer tail, external scene route, terminal IRQ/camera lifetime and runtime verification remain open.",
            "No emulator, physical EEPROM operation, supplied save access or main-pipeline change."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    need(args.before.suffix.lower() == args.gba.suffix.lower() == ".gba" and
         args.old.suffix.lower() == args.source.suffix.lower() == ".wsc", "ROM-only inputs before reading")
    inputs = {getattr(args, n).resolve() for n in ("before", "gba", "old", "source")}
    need(args.output.suffix.lower() == ".gba" and args.manifest.suffix.lower() == ".json" and
         args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve() != args.manifest.resolve(), "distinct ROM/report output paths")
    need(not args.output.exists() and not args.manifest.exists(), "fresh output artifacts; never overwrite a checkpoint")
    after, report = build(*(getattr(args, n).read_bytes() for n in ("before", "gba", "old", "source")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"],
        changed_bytes=report["changed_bytes"], negative_cases=report["negative_cases"], ABI_RMW_cases=report["abi"]["cases"])))


if __name__ == "__main__":
    main()
