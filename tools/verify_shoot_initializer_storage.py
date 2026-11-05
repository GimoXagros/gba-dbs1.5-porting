#!/usr/bin/env python3
"""Independently verify the disconnected ordered Shoot storage adapter.

No builder, analyzer, manifest, emulator, service or save is executed/read.
The block model assumes initialized, functional, exclusively owned native
EEPROM/timer services; injected errors test safe bounded adapter control flow,
not equivalence on a failed device or raw save-file byte ordering.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import struct

import verify_shoot_initializer_front as front
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

need, sha, word, listing = front.need, front.sha, front.word, front.listing
BASE, START, WRITE, STOP = 0x08000000, 0x629800, 0x629818, 0x629880
BEFORE = "CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7"
AFTER = "66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF"
FRONT_VERIFIER = "39652942A0E480C7B08016F7E2B8CC93046A1163F29572490096AA3A9A3244CD"
READ, WRITE_BLOCK = 0x0837DB60, 0x0837DB54
GUARDS = (
    ("boot geometry and timer", 0x280, 0x294, "9E1C7CDF3B3AD4E90F37EB7A70F10EEF709BEB0523F857F2DCF075B18C0CA9EB"),
    ("boot IRQ slot", 0x3BC, 0x3C0, "E071247BB64DDEEBC28DF8822F4FE38B382462DC752E0F8493D4AD27A9125099"),
    ("record loops and checksum", 0x1FBD0, 0x1FD30, "01F43CF82067A774BDAB0046737BCC74F11A511B171D2280B36BA6BBE65F22F6"),
    ("complete EEPROM library", 0x37D5EC, 0x37DA06, "C80BD60510C782EC1B094D909010A44C8157607A8BBFB6723DECE7A64BEA2C64"),
    ("initialization veneers", 0x37DADC, 0x37DAF4, "B51A70816C9DE9663A98D27254D2FB134D68FB1C23A87B7CA0D12CCF1CA3ED33"),
    ("storage veneers", 0x37DB54, 0x37DB6C, "B014D1AFC2E22F57B83E733F4011BCC2B8E6D26FB83F48B550F9C6F605B31CC3"),
    ("selected descriptors", 0x3877C4, 0x3877F0, "8D1725133323FBF85BDB2948856A80A08621AD290777008C183DB80083939FB5"),
)
OWNER_GUARDS = (
    (0x629500, 0x629518, "7A42F8C8D7AA3EDFDB669182B498F1EC0A6091BCECA491B2BAD4CF55ECD2F94A"),
    (0x629600, 0x629680, "51739551E0633D3A3FC58ECC6F5B2E9DDCB164E12E57FCACFEE63FEA3AB1ECF0"),
)


def thumb(data, start, stop):
    rows = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(data[start:stop], BASE + start))
    need(sum(i.size for i in rows) == stop - start, "complete Thumb instruction interval")
    return [f"{i.mnemonic} {i.op_str}" for i in rows]


def sequence(data, start, expected, thumb_mode=False):
    rows = thumb(data, start, start + 2 * len(expected)) if thumb_mode else listing(data, start, start + 4 * len(expected))
    need(rows == expected, f"actual instruction semantics at {start:06X}")


def source_contract(source):
    need(sha(source[0x747CD6:0x747CF0]) == "E9A7773BC80C92BBF1BD6DD942C0E3A5A0E0FF69244448A8F60CE8964CB96686", "actual source segment and ordered stores")
    need(front.chain.source_listing(source, 0x73D6, 0x73F0) == ["mov ax, 0x1000", "mov es, ax",
         "mov word ptr es:[0x660], 0", "mov word ptr es:[0x3cd8], 0", "mov word ptr es:[0x3cda], 0"], "two distinct SRAM halfword clears after retained 0660")
    need(source[0x7FFFF0:] == bytes.fromhex("EAFC06FF4F0001003000080204003E44"), "actual 32-KiB SRAM cartridge footer")
    cases = 0
    for bank, alias, byte in itertools.product(range(256), (0x13CD8, 0x1BCD8), range(4)):
        need((((alias + byte) & 0xFFFF) | (bank << 16)) & 0x7FFF == 0x3CD8 + byte,
             "every source C1 bank and upper-half alias preserves the four SRAM bytes")
        cases += 1
    need(0x0C00 * 16 + 0x3CD8 == 0xFCD8 and 0xFCD8 >> 16 == 0, "ordinary regeneration fields are a different bus domain")
    return dict(raw_half_open=["747CE2", "747CF0"], source_end_exclusive="4090:73F0",
                ordered_source_words=["1000:3CD8", "1000:3CDA"], SRAM_bytes=32768,
                bank_alias_cases=cases, native_API_block=25, native_API_buffer_halfwords=[0, 2],
                raw_save_or_wire_byte_order_claimed=False,
                primary_revision="4b01295838ea89e3f1355bbe4cb5cf98aa6108cd",
                primary_urls=["https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/libretro.c",
                              "https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/mednafen/wswan/wswan-memory.c"])


def native_contract(image, retail):
    for name, a, z, expected in GUARDS:
        need(sha(image[a:z]) == expected and image[a:z] == retail[a:z], "retained native " + name)
    sequence(image, 0x280, ["mov r0, #4", "bl #0x837dadc", "mov r0, #2", "ldr r1, [pc, #0x128]", "bl #0x837dae8"])
    need(word(image, 0x3BC) == 0x030000F0 and word(image, 0x37D604) == 0x083877D0,
         "selected geometry and native timer-2 IRQ backend")
    need(struct.unpack_from("<IHHB", image, 0x3877D0) == (512, 64, 0x0300, 6), "512 bytes / 64 eight-byte blocks")
    sequence(image, 0x1FC64, ["mov r2, #0x19", "ldr r1, [pc, #0x34]", "str sb, [r1, #0xc0]", "mov r3, #0"])
    sequence(image, 0x1FC8C, ["add r1, r1, #8", "add r3, r3, #1", "subs r2, r2, #1", "bgt #0x801fc74"])
    sequence(image, 0x1FCAC, ["mov r2, #0x19", "ldr r1, [pc, #0x4c]", "mov r3, #0"])
    sequence(image, 0x1FCD0, ["add r1, r1, #8", "add r3, r3, #1", "subs r2, r2, #1", "bgt #0x801fcb8"])
    for a, target in ((0x37DB54, 0x0837D9C9), (0x37DB60, 0x0837D7E5)):
        sequence(image, a, ["ldr ip, [pc]", "bx ip"])
        need(word(image, a + 8) == target, "actual interworking veneer target")
    # Code spans exclude literal pools; every instruction, call and high-register write is inspected.
    specs = (
        ("read", ((0x37D7E4, 0x37D7FC), (0x37D804, 0x37D88E)), 152, {"r4", "r5", "r6"}, [0x0837D764, 0x0837D764]),
        ("write", ((0x37D894, 0x37D8AC), (0x37D8B4, 0x37D8F4), (0x37D8F8, 0x37D960)), 176, {"r4", "r5"}, [0x0837D764, 0x0837D698, 0x0837D720]),
        ("compare", ((0x37D970, 0x37D98A), (0x37D994, 0x37D9C6)), 20, {"r4", "r5"}, [0x0837D7E4]),
        ("retry", ((0x37D9C8, 0x37DA06),), 16, {"r4", "r5", "r6"}, [0x0837D894, 0x0837D970]),
        ("DMA", ((0x37D764, 0x37D7C2),), 16, {"r4", "r5", "r6"}, []),
        ("timer start", ((0x37D698, 0x37D702),), 28, {"r4", "r5", "r6", "r7", "r8", "sb"}, []),
        ("timer stop", ((0x37D720, 0x37D74E),), 0, set(), []),
    )
    decoded = []
    for name, spans, frame, saved, calls in specs:
        decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB); decoder.detail = True
        rows = [i for a, z in spans for i in decoder.disasm(image[a:z], BASE + a)]
        need(sum(i.size for i in rows) == sum(z - a for a, z in spans), "complete callee instructions")
        need([int(i.op_str[1:], 16) for i in rows if i.mnemonic == "bl"] == calls, "complete retained synchronous call graph")
        writes = {i.reg_name(r) for i in rows for r in i.regs_access()[1]}
        need((writes & {"r4", "r5", "r6", "r7", "r8", "sb", "sl", "fp"}) <= saved,
             "no unsaved callee register mutation")
        decoded.append(dict(name=name, instructions=len(rows), local_stack_bytes=frame))
    for a, expected in (
        (0x37D7E4, ["push {r4, r5, r6, lr}", "sub sp, #0x88"]),
        (0x37D886, ["add sp, #0x88", "pop {r4, r5, r6}", "pop {r1}", "bx r1"]),
        (0x37D894, ["push {r4, r5, lr}", "sub sp, #0xa4"]),
        (0x37D958, ["add sp, #0xa4", "pop {r4, r5}", "pop {r1}", "bx r1"]),
        (0x37D970, ["push {r4, r5, lr}", "sub sp, #8"]),
        (0x37D9BE, ["add sp, #8", "pop {r4, r5}", "pop {r1}", "bx r1"]),
        (0x37D9C8, ["push {r4, r5, r6, lr}"]),
        (0x37DA00, ["pop {r4, r5, r6}", "pop {r1}", "bx r1"]),
        (0x37D764, ["push {r4, r5, r6, lr}"]),
        (0x37D7BC, ["pop {r4, r5, r6}", "pop {r0}", "bx r0"]),
        (0x37D698, ["push {r4, r5, r6, r7, lr}", "mov r7, sb", "mov r6, r8", "push {r6, r7}"]),
        (0x37D6F6, ["pop {r3, r4}", "mov r8, r3", "mov sb, r4", "pop {r4, r5, r6, r7}", "pop {r0}", "bx r0"]),
        (0x37D9DA, ["cmp r6, #2", "bhi #0x837d9fe"]),
        (0x37D8CA, ["ldrh r2, [r5]", "adds r5, #2", "movs r0, #0"]),
        (0x37D8E6, ["cmp r1, #3", "bls #0x837d8ca"]),
        (0x37D87C, ["lsls r0, r0, #0x18", "lsrs r4, r0, #0x18", "cmp r4, #3", "bls #0x837d85c"]),
        (0x37D9AC, ["ldrh r1, [r4]", "ldrh r0, [r2]", "adds r2, #2", "adds r4, #2", "cmp r1, r0", "beq #0x837d9a2"]),
    ):
        sequence(image, a, expected, True)
    need(word(image, 0x37D7F8) == 0xE0444801, "read out-of-range path precedes every destination write")
    need(struct.unpack_from("<8I", image, 0x37D7C4) == (0x04000208, 0x04000204, 0xF8FF, 0x03006CD0,
         0x040000D4, 0x040000D8, 0x040000DC, 0x040000DE), "actual IME/WAITCNT/DMA3 side-effect addresses")
    return dict(callees=decoded, preserved_by_services="r4-r11,SP", caller_saved="r0-r3,r12,LR,flags",
                stack_alignment_bytes=4, entry_stack_bytes=36, inspected_synchronous_stack_bytes=256,
                hardware_and_library_state=["DMA3 SAD/DAD/CNT", "WAITCNT protocol wait bits", "IME saved/restored",
                    "timer2 and its IE/IF bits", "native EEPROM timer state 030053A0..030053AD"],
                native_record_blocks=[0, 25], private_block=25, write_attempt_limit=3,
                read_error="80FF for invalid index; valid block25 reads eight bytes and returns zero",
                write_errors=["80FF invalid index", "C001 timeout", "8000 verification mismatch"],
                time_bound_claimed=False, source_observer_translation_closed=False)


def artifact_contract(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB image")
    need(before[WRITE:WRITE + 8] == struct.pack("<2I", 0xE8BD4800, 0xE12FFF1E) and
         before[WRITE + 8:STOP] == b"\xff" * 96, "exact old return and erased extension")
    need(before[START:WRITE] == after[START:WRITE], "all four preceding calls retained")
    expected = ["push {fp, lr}", "mov fp, #0", "bl #0x8629700", "bl #0x85c1000", "bl #0x85c1700", "bl #0x85c4400",
        "push {r0, r1, r2, r3, ip}", "sub sp, sp, #8", "mov r0, #0x19", "mov r1, sp", "bl #0x837db60",
        "cmp r0, #0", "bne #0x8629848", "mov r0, #0", "strh r0, [sp]", "mov r0, #0x19", "mov r1, sp", "bl #0x837db54",
        "mov r0, #0x19", "mov r1, sp", "bl #0x837db60", "cmp r0, #0", "bne #0x8629870", "mov r0, #0",
        "strh r0, [sp, #2]", "mov r0, #0x19", "mov r1, sp", "bl #0x837db54", "add sp, sp, #8",
        "pop {r0, r1, r2, r3, ip}", "pop {fp, lr}", "bx lr"]
    need(listing(after, START, STOP) == expected, "complete final artifact instructions and source store order")
    inverse = bytearray(after); inverse[WRITE:STOP] = before[WRITE:STOP]
    need(inverse == before, "104-byte full inverse preserves every other byte, route and dependency")
    need(after[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer still absent")


def run_adapter(image, flags, sp, fp, lr, failures, seed):
    regs = [0x12340000 + n * 0x1111 for n in range(15)]
    regs[11], regs[13], regs[14] = fp, sp, lr
    initial, memory, pc, minimum = tuple(regs), {}, START, sp
    block = bytearray((seed + 29 * n) & 255 for n in range(8))
    original, read_count, writes, events, snapshot = bytes(block), 0, [], [], None
    z = bool(flags & 4)
    for _ in range(40):
        encoded = word(image, pc); next_pc = pc + 4; condition = encoded >> 28
        need(condition in (1, 14), "bounded unconditional/BNE adapter model")
        if condition == 1 and z:
            pc = next_pc; continue
        if encoded & 0xFFFF0000 in (0xE92D0000, 0xE8BD0000):
            selected = [r for r in range(15) if encoded & (1 << r)]
            push = encoded & 0xFFFF0000 == 0xE92D0000
            if push: regs[13] -= 4 * len(selected)
            for offset, reg in enumerate(selected):
                address = regs[13] + 4 * offset
                if push:
                    for n, value in enumerate(struct.pack("<I", regs[reg])): memory[address + n] = value
                else: regs[reg] = int.from_bytes(bytes(memory[address + n] for n in range(4)), "little")
            if not push: regs[13] += 4 * len(selected)
        elif encoded in (0xE24DD008, 0xE28DD008): regs[13] += -8 if encoded == 0xE24DD008 else 8
        elif encoded in (0xE3A00019, 0xE3A00000): regs[0] = encoded & 255
        elif encoded == 0xE3A0B000: regs[11] = 0
        elif encoded == 0xE1A0100D: regs[1] = regs[13]
        elif encoded == 0xE1A00000: pass
        elif encoded == 0xE3500000: z = regs[0] == 0
        elif encoded in (0xE1CD00B0, 0xE1CD00B2):
            address = regs[13] + (encoded & 15)
            memory[address], memory[address + 1] = regs[0] & 255, (regs[0] >> 8) & 255
        elif encoded & 0x0F000000 == 0x0A000000:
            next_pc = front.chain.prefix.target(pc, encoded) - BASE
        elif encoded & 0x0F000000 == 0x0B000000:
            target = front.chain.prefix.target(pc, encoded); regs[14] = BASE + pc + 4
            need(regs[11] == 0, "r11 stays zero through retained/new services")
            if target in (0x08629700, 0x085C1000, 0x085C1700, 0x085C4400):
                need(regs[13] == sp - 8, "retained front frame")
                events.append(target)
            else:
                need(target in (READ, WRITE_BLOCK) and regs[0] == 25 and regs[1] == regs[13] == sp - 36,
                     "exact block25 and writable aligned eight-byte stack buffer")
                if target == READ:
                    phase = read_count; read_count += 1; snapshot = bytes(block)
                    failed = failures[phase * 2]
                    if not failed:
                        for n, value in enumerate(block): memory[regs[13] + n] = value
                    status = 0x80FF if failed else 0
                    events.append("read" + str(phase))
                else:
                    phase = read_count - 1
                    need(not failures[phase * 2], "never write a buffer after a failed read")
                    proposed = bytes(memory[regs[13] + n] for n in range(8))
                    expected = bytearray(snapshot); expected[phase * 2:phase * 2 + 2] = b"\0\0"
                    need(proposed == expected, "each write changes only its source halfword and preserves the other six read bytes")
                    writes.append(phase); status = 0xC001 if failures[phase * 2 + 1] else 0
                    if status == 0:
                        block[:] = proposed
                    else:
                        # A synthetic partial failure makes the next fresh read observably necessary.
                        block[0], block[7] = proposed[0], block[7] ^ 0x80
                    events.append("write" + str(phase))
                for r in (0, 1, 2, 3, 12): regs[r] = 0xBAD00000 + r
                regs[0], z = status, not z
        elif encoded == 0xE12FFF1E:
            need(tuple(regs) == initial, "all caller registers, SP and ARM/Thumb return bit restored")
            need(events[:4] == [0x08629700, 0x085C1000, 0x085C1700, 0x085C4400], "retained source phases precede storage")
            need(events[4:] == [x for n in range(2) for x in (["read" + str(n)] + ([] if failures[n * 2] else ["write" + str(n)]))],
                 "ordered independent reads and writes, including read-error skips")
            if not any(failures): need(block == b"\0" * 4 + original[4:], "normal backend commits both words and preserves API buffer bytes4..7")
            need(minimum == sp - 36, "exact 36-byte adapter high-water mark")
            return
        else: raise ValueError(f"instruction outside independent adapter model: {encoded:08X}")
        minimum = min(minimum, regs[13]); pc = next_pc
    raise ValueError("adapter did not return within bounded instruction count")


def abi_contract(image):
    cases = 0
    for flags, sp, fp, lr, failures in itertools.product(range(16), (0x03007EFC, 0x03007F00),
            (0, 1, 0x80000000, 0xFFFFFFFF), (0x0833FD1C, 0x0833FD1D), itertools.product((False, True), repeat=4)):
        run_adapter(image, flags, sp, fp, lr, failures, (cases * 17) & 255); cases += 1
    return dict(cases=cases, incoming_NZCV_states=16, stack_modulo8=[0, 4], preserved="r0-r12,LR,SP",
                flags="clobbered", outer_and_storage_stack_bytes=36, service_boundary="retained native ABI and functional block storage",
                error_cases="both read and write failures in every combination; no unread buffer writes; restoration and finite adapter continuation",
                failed_device_equivalence_claimed=False)


def scan(data, origin=0):
    hits = []
    def inside(value):
        return any(base + START <= value < base + STOP for base in (BASE, 0x0A000000, 0x0C000000))
    for alignment in range(4):
        stop = len(data) - ((len(data) - alignment) % 4)
        for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            if inside(encoded): hits.append(("pointer", origin + alignment + 4 * n, encoded))
    for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at, pc = origin + n * 4, BASE + origin + n * 4 + 8
        if encoded & 0x0E000000 == 0x0A000000 and inside(front.chain.prefix.target(at, encoded)):
            hits.append(("ARM branch", at, front.chain.prefix.target(at, encoded)))
        if encoded & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            destination = pc + (encoded & 0xFFF) * (1 if encoded & 0x800000 else -1)
            if inside(destination): hits.append(("ARM literal", at, destination))
        if encoded & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            immediate, rotate = encoded & 255, ((encoded >> 8) & 15) * 2
            if rotate: immediate = ((immediate >> rotate) | (immediate << (32 - rotate))) & 0xFFFFFFFF
            destination = pc + (immediate if encoded & 0x01E00000 == 0x00800000 else -immediate)
            if inside(destination): hits.append(("ARM ADR", at, destination))
    for n, (encoded,) in enumerate(struct.iter_unpack("<H", data[:len(data) // 2 * 2])):
        at, pc = origin + n * 2, BASE + origin + n * 2 + 4
        if encoded & 0xF800 in (0x4800, 0xA000):
            destination = (pc & ~3) + (encoded & 255) * 4
            if inside(destination): hits.append(("Thumb literal/ADR", at, destination))
        if encoded & 0xF800 == 0xE000:
            immediate = encoded & 0x7FF; destination = pc + 2 * (immediate - (0x800 if immediate & 0x400 else 0))
            if inside(destination): hits.append(("Thumb B", at, destination))
        if encoded & 0xF000 == 0xD000 and encoded & 0x0F00 < 0x0E00:
            immediate = encoded & 255; destination = pc + 2 * (immediate - (256 if immediate & 128 else 0))
            if inside(destination): hits.append(("Thumb conditional B", at, destination))
        if encoded & 0xF800 == 0xF000 and n * 2 + 4 <= len(data):
            tail = struct.unpack_from("<H", data, n * 2 + 2)[0]
            if tail & 0xF800 in (0xF800, 0xE800):
                immediate = encoded & 0x7FF
                destination = pc + ((immediate - (0x800 if immediate & 0x400 else 0)) << 12) + ((tail & 0x7FF) << 1)
                if tail & 0xF800 == 0xE800: destination &= ~3
                if inside(destination): hits.append(("Thumb BL/BLX", at, destination))
    return hits


def ownership(image, final, hits):
    pop_at = STOP - 8 if final else WRITE
    expected = ([("ARM branch", 0x629830, 0x08629848), ("ARM branch", 0x629858, 0x08629870)] if final else []) + [
        ("Thumb literal/ADR", 0x629510, 0x08629874), ("Thumb literal/ADR", 0x629620, 0x08629870),
        ("Thumb literal/ADR", START, BASE + START + 4)] + ([
        ("Thumb conditional B", 0x62981C, 0x08629830)] if final else []) + [
        ("Thumb literal/ADR", pop_at, BASE + pop_at + 4)]
    need(hits == expected, "only internal branches and positively owned Thumb-looking ARM halfwords")
    for a, z, expected_hash in OWNER_GUARDS:
        need(sha(image[a:z]) == expected_hash, "complete external ARM owner retained")
    need(listing(image, 0x629510, 0x629514) == ["b #0x80d1c78"] and
         listing(image, 0x629620, 0x629624) == ["bl #0x8012874"], "two external false ADRs belong to actual ARM branches")
    for a in (0x36D28C, 0x36D2F8):
        need(listing(image, a, a + 4) == ["bl #0x8629500"], "stage helper has ARM callers")
    need(word(image, 0x62967C) == 0x08629600, "retained waterfall ARM callback pointer")
    need(word(image, START) == 0xE92D4800 and word(image, pop_at) == 0xE8BD4800, "the two local low4800 halfwords have exact ARM push/pop owners")
    if final:
        need(word(image, 0x62981C) == 0xE24DD008 and listing(image, 0x62981C, 0x629820) == ["sub sp, sp, #8"],
             "lowD008 is owned by the ARM stack allocation, not a Thumb incoming branch")
    return dict(classified_references=hits, actual_external_references=[], finite_static_scan=True,
                all_pointer_alignments=True, ROM_mirrors=["08", "0A", "0C"], computed_entry_exclusion_claimed=False)


def negatives(before, after, retail, source, before_hits):
    rejected = []
    def reject(label, check):
        try: check()
        except (ValueError, KeyError, struct.error) as error: rejected.append(dict(case=label, reason=str(error)))
        else: raise ValueError("accepted negative control: " + label)
    for a in (*range(WRITE, STOP), START, WRITE - 1, STOP, 0x5C7800):
        wrong = bytearray(after); wrong[a] ^= 1
        reject(f"output byte {a:06X}", lambda: artifact_contract(before, wrong))
    for label, a, encoded in (("wrong block", 0x629820, 0xE3A00018), ("two clears target same halfword", 0x629860, 0xE1CD00B0),
            ("write unread buffer", 0x629830, 0xE1A00000), ("skip second read", 0x629850, 0xE1A00000),
            ("branch skips restoration", 0x629858, 0x1A000006), ("leaked temporary block", 0x629870, 0xE28DD004),
            ("wide clear overwrites neighbor", 0x629838, 0xE58D0000)):
        wrong = bytearray(after); struct.pack_into("<I", wrong, a, encoded)
        failures = {"write unread buffer": (True, False, False, False), "branch skips restoration": (False, False, True, False)}.get(label, (False,) * 4)
        reject(label, lambda: run_adapter(wrong, 0, 0x03007F00, 1, 0x0833FD1D, failures, 37))
    for name, a, z, _ in GUARDS:
        wrong = bytearray(before); wrong[a] ^= 1
        reject("native " + name, lambda: native_contract(wrong, retail))
    for a in (0x747CD7, 0x747CE5, 0x747CEC, 0x7FFFFB):
        wrong = bytearray(source); wrong[a] ^= 1
        reject(f"source domain/store/header {a:06X}", lambda: source_contract(wrong))
    for a, z, _ in OWNER_GUARDS:
        wrong = bytearray(before); wrong[a] ^= 1
        reject(f"false-ADR owner {a:06X}", lambda: ownership(wrong, False, before_hits))
    controls = 0
    for mirror, interior, alignment in itertools.product((BASE, 0x0A000000, 0x0C000000), (0, 1, 24, 127), range(4)):
        sample = bytearray(b"\xff" * 64); struct.pack_into("<I", sample, alignment, mirror + START + interior)
        need(any(hit[0] == "pointer" for hit in scan(sample)), "pointer scanner positive rejection control"); controls += 1
    for encoded in (0xEA00003E, 0xEB00003E, 0xE59F80F8, 0xE28F00F8):
        need(scan(struct.pack("<I", encoded) + b"\xff" * 60, START - 0x100), "ARM scanner control"); controls += 1
    for encoded in (0x483F, 0xA03F, 0xE07E, 0xD07E):
        need(scan(struct.pack("<H", encoded) + b"\xff" * 62, START - 0x100), "Thumb scanner control"); controls += 1
    for tail in (0xF87E, 0xE87E):
        need(scan(struct.pack("<HH", 0xF000, tail) + b"\xff" * 60, START - 0x100), "Thumb BL/BLX scanner control"); controls += 1
    return rejected, controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "source", "output"): parser.add_argument(name, type=Path)
    args = parser.parse_args(); names = ("before", "after", "gba", "old", "source")
    need(all(getattr(args, n).suffix.lower() == ".gba" for n in names[:3]) and
         all(getattr(args, n).suffix.lower() == ".wsc" for n in names[3:]), "ROM-only inputs before reading")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in {getattr(args, n).resolve() for n in names}, "distinct JSON output")
    before, after, retail, old, source = (getattr(args, n).read_bytes() for n in names)
    need(tuple(map(sha, (before, retail, old, source))) == (BEFORE, *front.chain.prefix.ORIGINALS), "exact front predecessor and immutable originals")
    need(sha(Path(front.__file__).read_bytes()) == FRONT_VERIFIER, "frozen independent inherited front verifier")
    artifact_contract(before, after)
    src, native, abi = source_contract(source), native_contract(before, retail), abi_contract(after)
    before_hits, after_hits = scan(before), scan(after)
    ownership_before, ownership_after = ownership(before, False, before_hits), ownership(after, True, after_hits)
    rejected, controls = negatives(before, after, retail, source, before_hits)
    need(sha(after) == AFTER, "final storage artifact identity after independent checks")
    report = dict(schema=1, status="PASS", kind="independent-shoot-initializer-storage-verification",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=list(front.chain.prefix.ORIGINALS),
        inherited_front_verifier_sha256=FRONT_VERIFIER, inherited_front_proof_reexecuted=False,
        source=src, native_services=native, ABI=abi, native_entry="08629800", final_entry_bytes=128,
        write_half_open=["629818", "629880"], declared_bytes=104, appended_bytes=96,
        changed_bytes=sum(a != b for a, b in zip(before, after)), full_inverse=True, first_24_bytes_retained=True,
        ownership_before=ownership_before, ownership_after=ownership_after,
        negative_controls=rejected, scanner_negative_controls=controls, negative_control_count=len(rejected) + controls,
        full_initializer_absent=True, external_callers_added=0, new_persistent_RAM_bytes=0,
        native_API_block25_adopted=True, source_observer_translation_closed=False,
        preconditions=["Retained front object, renderer, stack and exclusive scene/display ownership contracts.",
            "Initialized functional native 512-byte EEPROM backend, available timer2/IRQ/DMA3 ownership and aligned stack.",
            "At least256 bytes for the inspected synchronous storage chain; IRQ/live-caller stack requires separate proof."],
        limits=["Disconnected entry only; no complete initializer or external scene/controller caller.",
            "Two RMW operations preserve six API-buffer bytes each; no raw save-byte order, atomicity or power-failure equivalence claim.",
            "Read error skips its write; native writer makes at most three attempts and adapter continues after final write error.",
            "No failed-device equivalence or wall-clock bound; DMA/timer progress requires the functional-backend precondition.",
            "Unknown source observers, later initializer phases, terminal DI and camera lifetime remain unresolved.",
            "Static artifact/models only; no emulator, native service, EEPROM operation, save, gameplay or hardware test."],
        input_ROMs_written=False, supplied_save_accessed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=sha(after), ABI_cases=abi["cases"], negative_control_count=report["negative_control_count"])))


if __name__ == "__main__":
    main()
