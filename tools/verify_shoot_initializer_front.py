#!/usr/bin/env python3
"""Independently verify the disconnected Shoot front through source 73E2.

The pinned predecessor retains the independently verified prefix/player chain.
Only the two added source phases and their retained native consumers are checked
here. No builder/analyzer, manifest, emulator, native service, or save is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

import verify_shoot_initializer_player_chain as chain
from verify_shoot_tail_resources import sequence

BASE, START, STOP, WRITE = chain.BASE, 0x629800, 0x629820, 0x629810
BEFORE = chain.AFTER
AFTER = "CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7"
CHAIN_VERIFIER = "0D36464802D94FFFAD85FBBF6F40CF7AE38B8B820A0FAC0930B1B9256263B0B0"
SOURCE = "D3BB949DFAC1F1281974822C5A60CEB156FF8BA65226FBFC5E0386CAD32BE2E9"
GUARDS = (
    ("palette phase", 0x5C1700, 0x5C173C, "4D820BC4540F166FE98F6BB2F0E7B7FA6153010A63A373BD9B221C57154612E4"),
    ("single halfword clear", 0x5C4400, 0x5C441C, "9765E2CC0B5B3E473FC00D18FC4FF564D2E0E729237FB2C5AFA0CC1BC67A0E46"),
    ("6D constructor", 0x5C4500, 0x5C458C, "D9A8CAD358CBF0667D1A5363C75F777267EDB5E8A726783A291E3D29C5A79BFA"),
    ("137 constructor", 0x5C4600, 0x5C468C, "E3DB55773E5CDF3B942176B97A29B0F01918473E22067ABB1FFD7BE97B6E9829"),
    ("6D P1", 0x5C4800, 0x5C494C, "447CB640585411B6027544D57882206D283337CB90DAA0C9099A4E455D0C4AE4"),
    ("137 P1", 0x5C4C00, 0x5C4D94, "C3A099E04431467D752A25D9AF10ED9C2C4F046D2CB4468DF6EAC968758AA7AD"),
    ("slot-5 P2", 0x5DB740, 0x5DB768, "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1"),
    ("complete renderer copy and dispatcher", 0x12C28, 0x12DD8, "78B1C64C99CB980EBC60E8950B941B11B118AAE2CD9A7A6A1E15B926C88FA0DB"),
    ("renderer DMA startup", 0x13C, 0x1A0, "E49944B876A5261FE15118E832A315D2E38A3784044F4550B1FA8283D8AEFA6B"),
)
need, sha, word, listing = chain.need, chain.sha, chain.word, chain.listing


def source_contract(source):
    actual = chain.source_listing(source, 0x7394, 0x73E2)
    expected = ["push 5", "push 0", "push 0xbd", "push 0x27a9", "push 0",
        "lcall 0x4fff, 0x2389", "add sp, 0xa", "push 0x6d", "push 0x4000",
        "push 0xbd", "push 0x244e", "push 0", "lcall 0x4fff, 0x226e", "add sp, 0xa",
        "push 0x137", "push 0x4000", "push 0xbd", "push 0x20ca", "push 0",
        "lcall 0x4fff, 0x226e", "add sp, 0xa", "mov ax, 0x1000", "mov es, ax",
        "mov word ptr es:[0x660], 0"]
    need(actual == expected and sha(source[0x747C94:0x747CE2]) == SOURCE,
         "all 24 actual source instructions stop immediately before 73E2")
    need(chain.source_listing(source, 0x73E2, 0x73F0) ==
         ["mov word ptr es:[0x3cd8], 0", "mov word ptr es:[0x3cda], 0"],
         "hard boundary excludes the two source SRAM-domain clears")
    return dict(instructions=len(actual), raw_half_open=["747C94", "747CE2"],
                source_end_exclusive="4090:73E2", excluded_next_stores=["1000:3CD8", "1000:3CDA"])


def dependencies(image):
    chain.dependencies(image)
    need(listing(image, START, START + 24) == ["push {fp, lr}", "mov fp, #0", "bl #0x8629700",
         "bl #0x85c1000", "pop {fp, lr}", "bx lr"], "retained independently checked chain")
    for name, start, stop, expected in GUARDS:
        need(sha(image[start:stop]) == expected, f"retained dependency {name}")


def palette_contract(image, source):
    regs = chain.prefix.REGS
    sequence(image, 0x5C1700, ["push " + regs, "ldr r8, [pc, #0x2c]", "str r8, [sp, #-4]!",
        "mov r8, #0", *["str r8, [sp, #-4]!"] * 3, "mov r8, #5", "str r8, [sp, #-4]!",
        "mov fp, #0", "bl #0x80132ec", "add sp, sp, #0x14", "pop " + regs, "bx lr"])
    need(word(image, 0x5C1738) == 0x085DB740, "source slot-5 P2 pointer")
    sequence(image, 0x132EC, ["push {r2, r4, r5, lr}", "ldr r4, [sp, #0x20]", "add r4, r4, #4",
        "ldr r8, [sp, #0x14]", "lsl r2, r8, #5", "add r2, r2, r8, lsl #1", "add r4, r4, r2",
        "ldrh r8, [r4], #4", "sub r8, r8, #8", "ldr r5, [sp, #0x10]", "add r5, r5, r8",
        "add r5, r5, #0x10", "lsl r5, r5, #5", "add r5, r5, #0x5000000", "add r5, r5, #2"] +
        [item for _ in range(15) for item in ("ldrh r8, [r4], #2", "strh r8, [r5], #2")] +
        ["pop {r2, r4, r5, lr}", "bx lr"])
    src, native = 0x3D7A90, 0x5DB740
    header = struct.unpack_from("<3H", source, src)
    need(header == (1, 1, 8) and image[native:native + 6] == source[src:src + 6] and
         image[native + 38:native + 40] == b"\0\0", "actual source P2 header and native padding")
    for n, color in enumerate(struct.unpack_from("<16H", image, native + 6)):
        channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
        need(color < 0x8000 and all(c == 0 or c >= 3 and c % 2 for c in channels), "P2 source lattice")
        inverse = (channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2
        need(inverse == struct.unpack_from("<H", source, src + 6 + n * 2)[0], "all slot-5 P2 colors recover source")
    destination = 0x05000000 + (header[2] - 8 + 5 + 16) * 32 + 2
    need(destination == 0x050002A2, "actual loader's slot-5 destination")
    stack = chain.stack_paths(image, ((0x5C1700, 0x5C1738),), 0x5C1700, {0x080132EC})
    need(stack["local_max_bytes"] == 76, "palette frame plus five-word arguments")
    return dict(entry_sp_arguments=[5, 0, 0, 0, 0x085DB740], destination=f"{destination:08X}",
                halfwords_written=15, color_zero_untouched=True, source_colors_inversed=16,
                wrapper_plus_direct_palette_stack_bytes=8 + 76 + 16, stack=stack)


def clear_contract(image, gba, source):
    sequence(image, 0x5C4400, ["push " + chain.prefix.REGS, "ldr r8, [pc, #0xc]", "mov sb, #0",
                              "strh sb, [r8]", "pop " + chain.prefix.REGS, "bx lr"])
    need(word(image, 0x5C4418) == 0x030048A4, "one exact native halfword; no HP/SRAM alias substitution")
    # This second source reader establishes ES=1000 without calls or another ES assignment.
    second = chain.prefix.listing(source, 0x766ECD, 0x766EEE, chain.prefix.CS_ARCH_X86, chain.prefix.CS_MODE_16, 0)
    need(second == ["mov ax, 0x1000", "mov es, ax", "xor ax, ax", "mov al, byte ptr [si + 0x10]",
         "shl ax, 2", "mov bx, 0x660", "add bx, ax", "test word ptr [si + 0x20], 2",
         "jne 0x766ee9", "add bx, 2", "test word ptr es:[bx], 0xffff"],
         "unambiguous source ES1000 indexed 0660 reader")
    sequence(gba, 0x355EE8, ["ldrb r0, [r4, #0x10]", "lsl r0, r0, #2", "ldr r1, [pc, #0xec]",
        "add r1, r1, r0", "ldrh r8, [r4, #0x2e]", "tst r8, #2", "addeq r1, r1, #2",
        "ldrsh r8, [r1]", "movs r8, r8"])
    sequence(gba, 0x352DC4, ["ldrb r0, [r4, #0x10]", "lsls r0, r0, #2", "ldr r1, [pc, #0x2d0]",
        "add r1, r1, r0", "ldrsh r8, [r1]", "lsls r8, r8, #1", "strh r8, [r1]",
        "ldrsh r8, [r1, #2]", "lsls r8, r8, #1", "strh r8, [r1, #2]"])
    sequence(gba, 0x352B40, ["mov sb, #0", "ldr r8, [pc, #0x17c]", "strh sb, [r8]"])
    for at in (0x352B44, 0x352DCC, 0x355EF0):
        encoded = word(gba, at)
        need(encoded & 0x0FFF0000 == 0x059F0000, "native indexed-owner literal producer")
        literal = at + 8 + (encoded & 4095)
        need(word(gba, literal) == word(image, literal) == 0x030048A4, "producer and both indexed owners agree")
    for start, stop in ((0x352B40, 0x352B4C), (0x352DC4, 0x352DEC), (0x355EE8, 0x355F0C)):
        need(image[start:stop] == gba[start:stop], "retained actual native owner consumers")
    need(source[0x7432F8:0x743304] == bytes.fromhex("c70660060000c70664060000") and
         sha(source[0x7433E8:0x743478]) == "07F7DF54D7FE572F0349FCB0A2B875BB1920B47AFA04ACD6541BE194579D6C7A",
         "source producer and first indexed counterpart remain unchanged")
    return dict(native_halfword="030048A4", zero_value=0, bytes_written=2,
                direct_source_domain_proof="766ECD..766EEE: explicit ES1000 and no segment-changing call",
                first_source_counterpart_limit="743470 corroborates indexed shape; its earlier alternate path changes ES, so no all-path ES1000 claim",
                excluded_aliases=["030048AC", "030048AE", "1000:3CD8", "1000:3CDA"])


def preload_contract(image, gba, source):
    need(image[0x12C28:0x12DD8] == gba[0x12C28:0x12DD8] and image[0x13C:0x1A0] == gba[0x13C:0x1A0],
         "complete retail renderer copy and startup retained")
    sequence(image, 0x1281C, ["ldr r4, [sp, #0x40]", "ldr r3, [r4, #4]", "ldr r4, [sp, #0x34]",
        "ldrh r8, [r4, #0xe]", "orr r3, r3, r8", "strh r3, [r5, #8]"])
    sequence(image, 0x12C34, ["ldrh r1, [r5, #8]", "and r1, r1, #1", "add r8, pc, #0xc",
        "ldr sb, [r8, r1, lsl #2]", "bx sb"])
    need(word(image, 0x12C50) == 0x03000204 and word(image, 0x39C) == 0x08012C58,
         "dynamic draw dispatch and actual startup source literal")
    sequence(image, 0x160, ["mov r8, #0x8400", "mov r6, #0x4000000", "mov r7, #0x3000000"])
    sequence(image, 0x184, ["add r7, r7, #0x200", "str r7, [r6, #0xd8]", "ldr r4, [pc, #0x208]",
        "str r4, [r6, #0xd4]", "mov r4, #0x60", "strh r4, [r6, #0xdc]", "strh r8, [r6, #0xde]"])
    sequence(image, 0x12C74, ["mov lr, #0x2000000", "add lr, lr, r0, lsl #5"])
    sequence(image, 0x12C8C, ["ldr r4, [r5, #0x48]", "ldr fp, [r4, #4]", "ldrh r1, [r5, #8]",
        "tst r1, #2", "addne fp, fp, r3, lsl #3", "ldr fp, [fp, #4]"])
    sequence(image, 0x12D2C, ["ldrh r3, [r5, #0x10]", "add r3, r0, r3, lsl #12"])
    sequence(image, 0x12D50, ["ldrb r3, [sl]", "add r3, fp, r3, lsl #5"] +
        [item for _ in range(8) for item in ("ldr r8, [r3], #4", "str r8, [lr], #4")])
    sequence(image, 0x12DB4, ["pop {r0, r1, r2, r3, r4, r5, lr}", "bx lr"])
    need(struct.unpack_from("<3I", image, 0x12DBC) == (0x03001428, 0x030012CA, 0x030012CA),
         "copied renderer's actual OAM/index owner literals")
    code = chain.decode(image, 0x12C58, 0x12DBC)
    need(not any(i.mnemonic.startswith("ldr") and "[r5, #0x14]" in i.op_str for i in code),
         "bounded dynamic renderer does not use constructor tile identity as staging address")
    results = []
    for src, p0, source_p1, p1, end, counts, constructor, tile, p2, caller in (
        (0x3D44E0, 0x5DB300, 0x3D23B0, 0x5C4800, 0x5C494C, (15,), 0x5C4500, 0x6D, 0x5C5000, 0x5CC3F8),
        (0x3D0CA0, 0x5DB400, 0x0DFEC0, 0x5C4C00, 0x5C4D94, (6, 8, 6), 0x5C4600, 0x137, 0x5DB740, 0x5CC278)):
        arguments = chain.check_constructor(image, constructor + 4, constructor + 0x6C,
                                             (BASE + p1, BASE + p0, BASE + p2), tile, 5)
        need(chain.prefix.target(caller, word(image, caller)) == BASE + constructor and
             word(image, caller) >> 24 == 0xEB, "actual retained lower constructor caller")
        need(word(image, p1 + 4) == 0 and struct.unpack_from("<H", image, p0 + 14)[0] == 8,
             "constructor flags select dynamic draw with static descriptor zero")
        asset = chain.check_asset(image, source, src, p0, 1, None, None)
        need(word(image, p1) == BASE + p1 + 8 and struct.unpack_from("<H", source, source_p1)[0] == 4,
             "source/native P1 table owners")
        items = 0
        for n, count in enumerate(counts):
            native_count, payload = struct.unpack_from("<2I", image, p1 + 8 + n * 16)
            source_count, relative = struct.unpack_from("<2H", source, source_p1 + 4 + n * 8)
            need(native_count == source_count == count and BASE + p1 <= payload < payload + count * 16 <= BASE + end,
                 "bounded actual P1 command population")
            for index in range(count):
                layout = struct.unpack_from("<H", image, payload - BASE + index * 16 + 2)[0]
                need(layout == struct.unpack_from("<H", source, source_p1 + relative + index * 12 + 2)[0] and
                     layout < asset["layouts"], "every source/native animation layout selects a bounded P0 layout")
                items += 1
        results.append(dict(source_P0=f"{src:06X}", tile_identity=tile, constructor=arguments,
                            P0=asset, animation_items=items, fixed_VRAM_upload_added=False))
    return dict(resources=results, renderer_ROM_copy=["012C58", "012DD8"], renderer_IWRAM_entry="03000204",
                staging="02000000 + dynamic_tile_index * 32", OAM_uses_same_index=True,
                source_preload_identity_retained_in_constructor=True)


def artifact_contract(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB image")
    need(before[START + 24:STOP] == b"\xff" * 8, "eight appended bytes were unoccupied")
    need(before[START:WRITE] == after[START:WRITE], "first sixteen chain bytes retained verbatim")
    need(listing(after, START, STOP) == ["push {fp, lr}", "mov fp, #0", "bl #0x8629700", "bl #0x85c1000",
         "bl #0x85c1700", "bl #0x85c4400", "pop {fp, lr}", "bx lr"], "complete source-ordered four-call front")
    inverse = bytearray(after); inverse[WRITE:STOP] = before[WRITE:STOP]
    need(inverse == before, "16-byte full-ROM inverse; all external routes and hard-gate dependencies retained")


def abi_contract(image):
    cases = 0
    for flags in range(16):
        for sp in (0x03007EFC, 0x03007F00):
            for fp in (0, 1, 0x80000000, 0xFFFFFFFF):
                for lr in (0x0833FD1C, 0x0833FD1D):
                    regs = [0x12340000 + n * 0x1111 for n in range(15)]
                    regs[11], regs[13], regs[14] = fp, sp, lr
                    initial, saved, calls = tuple(regs), {}, []
                    for at in range(START, STOP, 4):
                        encoded = word(image, at)
                        need(encoded >> 28 == 14, "no incoming-flag dependence")
                        if encoded == 0xE92D4800:
                            regs[13] -= 8
                            saved[regs[13]], saved[regs[13] + 4] = regs[11], regs[14]
                        elif encoded == 0xE3A0B000:
                            regs[11] = 0
                        elif encoded >> 24 == 0xEB:
                            need(regs[11] == 0 and regs[13] == sp - 8, "zero r11 and retained outer frame at every service")
                            calls.append(chain.prefix.target(at, encoded))
                            regs[14] = BASE + at + 4
                        elif encoded == 0xE8BD4800:
                            regs[11], regs[14] = saved[regs[13]], saved[regs[13] + 4]
                            regs[13] += 8
                        elif encoded == 0xE12FFF1E:
                            need(tuple(regs) == initial, "all caller registers, stack and return ISA state restored")
                        else:
                            raise ValueError("instruction outside bounded front ABI model")
                    need(calls == [0x08629700, 0x085C1000, 0x085C1700, 0x085C4400], "all four component calls in source order")
                    cases += 1
    return dict(cases=cases, saved_here="r11,LR", preserved="r0-r12,LR,SP", stack_bytes=8,
                internal_r11=0, flags="clobbered", callee_contract="each guarded component restores r0-r12 and SP")


def scan(data, origin=0):
    """The reviewed chain scanner, extended to this front's complete 32 bytes."""
    hits = []
    def inside(value):
        return any(base + START <= value < base + STOP for base in (BASE, 0x0A000000, 0x0C000000))
    for alignment in range(4):
        stop = len(data) - ((len(data) - alignment) % 4)
        for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            if inside(encoded): hits.append(("pointer", origin + alignment + 4 * n, encoded))
    for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at, pc = origin + n * 4, BASE + origin + n * 4 + 8
        if encoded & 0x0E000000 == 0x0A000000 and inside(chain.prefix.target(at, encoded)):
            hits.append(("ARM branch", at, chain.prefix.target(at, encoded)))
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
            immediate = encoded & 0x7FF
            destination = pc + 2 * (immediate - (0x800 if immediate & 0x400 else 0))
            if inside(destination): hits.append(("Thumb B", at, destination))
        if encoded & 0xF000 == 0xD000 and encoded & 0x0F00 < 0x0E00:
            immediate = encoded & 255
            destination = pc + 2 * (immediate - (256 if immediate & 128 else 0))
            if inside(destination): hits.append(("Thumb conditional B", at, destination))
        if encoded & 0xF800 == 0xF000 and n * 2 + 4 <= len(data):
            tail = struct.unpack_from("<H", data, n * 2 + 2)[0]
            if tail & 0xF800 in (0xF800, 0xE800):
                immediate = encoded & 0x7FF
                destination = pc + ((immediate - (0x800 if immediate & 0x400 else 0)) << 12) + ((tail & 0x7FF) << 1)
                if tail & 0xF800 == 0xE800: destination &= ~3
                if inside(destination): hits.append(("Thumb BL/BLX", at, destination))
    return hits


def ownership(image, pop_at, hits):
    expected = [("Thumb literal/ADR", START, BASE + START + 4), ("Thumb literal/ADR", pop_at, BASE + pop_at + 4)]
    need(hits == expected, "only two Thumb-looking halfwords; no external/interior/static entry reference")
    owners = []
    for at, encoded, text in ((START, 0xE92D4800, "push {fp, lr}"), (pop_at, 0xE8BD4800, "pop {fp, lr}")):
        need(word(image, at) == encoded and listing(image, at, at + 4) == [text],
             "each low 4800 halfword is owned by its exact ARM push/pop instruction")
        owners.append(dict(site=f"{at:06X}", ARM_word=f"{encoded:08X}", ARM_owner=text,
                           raw_Thumb_target=f"{BASE + at + 4:08X}"))
    return owners


def negatives(blobs):
    rejected = []
    def reject(label, check):
        try:
            check()
        except (ValueError, SystemExit, struct.error) as error:
            rejected.append(dict(case=label, reason=str(error)))
        else:
            raise ValueError(f"accepted negative control: {label}")
    for at in (*range(WRITE, STOP), START, WRITE - 1, STOP, 0x5C7800, 0x5C4418):
        wrong = bytearray(blobs["after"]); wrong[at] ^= 1
        reject(f"output byte {at:06X}", lambda: artifact_contract(blobs["before"], wrong))
    for label, at, value, checker in (
        ("wrong palette slot", 0x5C171C, 0xE3A08004, lambda d: palette_contract(d, blobs["source"])),
        ("palette copies color zero", 0x13324, 0xE1A05005, lambda d: palette_contract(d, blobs["source"])),
        ("palette stack cleanup leak", 0x5C172C, 0xE28DD010, lambda d: palette_contract(d, blobs["source"])),
        ("clear widened to word", 0x5C440C, 0xE5889000, lambda d: clear_contract(d, blobs["gba"], blobs["source"])),
        ("clear guessed as HP global", 0x5C4418, 0x030048AC, lambda d: clear_contract(d, blobs["gba"], blobs["source"])),
        ("renderer chosen from tile ID", 0x12C74, 0xE595E014, lambda d: preload_contract(d, blobs["gba"], blobs["source"])),
        ("wrong dynamic descriptor", 0x5DB304, 0x085DB400, lambda d: preload_contract(d, blobs["gba"], blobs["source"])),
        ("constructor resource inversion", 0x5C4580, 0x085C4800, lambda d: preload_contract(d, blobs["gba"], blobs["source"]))):
        wrong = bytearray(blobs["before"]); struct.pack_into("<I", wrong, at, value)
        reject(label, lambda: checker(wrong))
    wrong = bytearray(blobs["after"])
    for at, destination in ((WRITE, 0x085C4400), (WRITE + 4, 0x085C1700)):
        struct.pack_into("<I", wrong, at, 0xEB000000 | (((destination - (BASE + at + 8)) // 4) & 0xFFFFFF))
    reject("correct new targets in reversed order", lambda: abi_contract(wrong))
    for at in (0x747C94, 0x747CB1, 0x747CDE, 0x747CE5):
        wrong = bytearray(blobs["source"]); wrong[at] ^= 1
        reject(f"source instruction/boundary {at:06X}", lambda: source_contract(wrong))
    wrong = bytearray(blobs["source"]); wrong[0x766ECE] ^= 1
    reject("source reader has a different ES domain", lambda: clear_contract(blobs["before"], blobs["gba"], wrong))
    wrong = bytearray(blobs["after"]); struct.pack_into("<I", wrong, START + 24, 0xE1A04800)
    reject("4800 halfword without ARM pop ownership", lambda: ownership(wrong, START + 24,
        [("Thumb literal/ADR", START, BASE + START + 4), ("Thumb literal/ADR", START + 24, BASE + START + 28)]))
    controls = 0
    for mirror in (BASE, 0x0A000000, 0x0C000000):
        for interior in (0, 1, 24, 31):
            for alignment in range(4):
                sample = bytearray(b"\xff" * 64); struct.pack_into("<I", sample, alignment, mirror + START + interior)
                need(any(hit[0] == "pointer" for hit in scan(sample)), "scanner covers old/new interiors and all pointer alignments")
                controls += 1
    for encoded in (0xEA00003E, 0xEB00003E, 0xE59F80F8, 0xE28F00F8):
        need(scan(struct.pack("<I", encoded) + b"\xff" * 60, START - 0x100), "ARM scan control")
        controls += 1
    for encoded in (0x483F, 0xA03F, 0xE07E, 0xD07E):
        need(scan(struct.pack("<H", encoded) + b"\xff" * 62, START - 0x100), "Thumb scan control")
        controls += 1
    for tail in (0xF87E, 0xE87E):
        need(scan(struct.pack("<HH", 0xF000, tail) + b"\xff" * 60, START - 0x100), "Thumb BL/BLX scan control")
        controls += 1
    return rejected, controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    names = ("before", "after", "gba", "old", "source")
    need(all(getattr(args, n).suffix.lower() == ".gba" for n in names[:3]) and
         all(getattr(args, n).suffix.lower() == ".wsc" for n in names[3:]), "ROM-only inputs before reading")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in
         {getattr(args, n).resolve() for n in names}, "distinct JSON output before reading")
    blobs = {name: getattr(args, name).read_bytes() for name in names}
    need(tuple(sha(blobs[n]) for n in ("before", "gba", "old", "source")) == (BEFORE, *chain.prefix.ORIGINALS),
         "exact independently verified chain and all three immutable originals")
    need(sha(Path(chain.__file__).read_bytes()) == CHAIN_VERIFIER, "frozen independent chain verifier dependency")
    before, after, gba, old, source = (blobs[n] for n in names)
    artifact_contract(before, after)
    dependencies(before)
    source_proof = source_contract(source)
    palette = palette_contract(before, source)
    clear = clear_contract(before, gba, source)
    preloads = preload_contract(before, gba, source)
    abi = abi_contract(after)
    before_refs = ownership(before, START + 16, scan(before))
    after_refs = ownership(after, START + 24, scan(after))
    negative, scanner_cases = negatives(blobs)
    need(sha(after) == AFTER, "final front identity after independent semantic checks")
    report = dict(schema=1, status="PASS", kind="independent-shoot-initializer-front-verification",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=list(chain.prefix.ORIGINALS),
        inherited_chain_verifier_sha256=CHAIN_VERIFIER, inherited_chain_proof_reexecuted=False,
        source_added=source_proof, source_added_sha256=SOURCE, native_entry="08629800", instructions=8,
        write_half_open=[f"{WRITE:06X}", f"{STOP:06X}"], declared_bytes=16, appended_bytes=8,
        changed_bytes=sum(a != b for a,b in zip(before,after)), full_inverse=True, first_16_bytes_retained=True,
        call_order=["08629700", "085C1000", "085C1700", "085C4400"], ABI=abi,
        palette_phase=palette, single_halfword_clear=clear, source_preload_mapping=preloads,
        dependencies=[dict(name=n, start=f"{a:06X}", end=f"{z:06X}", sha256=h) for n,a,z,h in GUARDS],
        allocation=dict(before_ARM_owners=before_refs, after_ARM_owners=after_refs, external_references=[],
                        all_pointer_alignments=True, ROM_mirrors=["08", "0A", "0C"], ARM_Thumb_references=True),
        negative_controls=negative, scanner_negative_controls=scanner_cases,
        negative_control_count=len(negative) + scanner_cases, full_initializer_absent=True,
        external_callers_added=0, new_RAM_bytes=0, input_ROMs_written=False, supplied_save_accessed=False,
        preconditions=["ARM entry, existing valid native stack and three objects at 030048A0/0300489C/03004D3C.",
                       "Other-character ID 0..14 and initialized native globals; exclusive scene/display ownership."],
        limits=["Disconnected front only; no menu/controller entry or complete initializer.",
                "Source 73E2 and its 1000:3CD8/3CDA stores remain a hard gate; no substitute or omission claim.",
                "Retained player intermediate store timing and complete transitive/interrupt stack bound remain unproved.",
                "Dynamic-renderer mapping is static consumer proof; no game, emulator, save, visual, audio or hardware timing test."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"], changed_bytes=report["changed_bytes"],
                         ABI_cases=abi["cases"], negative_control_count=report["negative_control_count"])))


if __name__ == "__main__":
    main()
