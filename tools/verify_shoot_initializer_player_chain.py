#!/usr/bin/env python3
"""Independently check the disconnected Shoot prefix/player composition.

Only reviewed independent verifiers are reused; no builder, analyzer, manifest,
emulator or save is read. Bounded instruction/stack models assume the retained
native services' contracts, valid existing objects, and exclusive scene ownership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

import verify_shoot_initializer_prefix as prefix
from verify_shoot_player_binding import check_constructor, decode, literal_value, semantic_checks
from verify_shoot_initializer_p1_assets import SPECS, verify_entry
from verify_shoot_far_tile_repair import check_asset

BASE, START, STOP = 0x08000000, 0x629800, 0x629818
BEFORE = "4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC"
AFTER = "2C9C96129EBECF30FCB915E077899CE91FBA979F4AC44C027EE39F4C9A8C4BC7"
SOURCE_PHASE = "9B65CB9B0866AB0B2137B34BBAEAD2B367760B276C9EB3C6666575AA2D428774"
GUARDS = (
    ("prefix", 0x629700, 0x62975C, "F139BF6F77A01C884D70207AE0B13D5E52998411025DCE531BE1B96E6755FC0A"),
    ("player", 0x5C1000, 0x5C11A4, "AEF73AB400F8B6611201CBAF3F24E19693D62BA7D84976A8479FFA33A46D2843"),
    ("auxiliary reuse", 0x5C1300, 0x5C1308, "57DC8F64037C3351974AD77B27E4300F2149CE6B7FDA13F8CA9B9985163EB9FD"),
    ("HP table", 0x5C1400, 0x5C141E, "F19BB19802488BA10E6948937E946AF4385760BF7E88CE4FBDC4A7006346B98E"),
    ("auxiliary body/literals", 0x5BC244, 0x5BC3B4, "BA5A9707BB6C8F1285251AFAA53ED0F98135A1FEA1107FDF858AD9CC3CE0F2A2"),
    ("auxiliary idle", 0x5BC600, 0x5BC604, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
    ("P1", 0x5D0000, 0x5D0A4C, "778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2"),
    ("active P0", 0x5D1000, 0x5D1080, "5A2C5CC07776A7100216F2E9F34E4E858EFB46389F1981D71D19F3336864FE0C"),
    ("active P0 pixels", 0x5F3B20, 0x5F4A00, "C943F1CE481B5BC2B18F2DABD9EAB2D78C891218A6C0B022A3CF390CE1027662"),
    ("auxiliary P0", 0x5D1100, 0x5DB2C0, "C739645446A1802F937551F845327D2F87B861B6ABE8DDA02EA7D91B8A24CB91"),
    ("active P2", 0x5B9300, 0x5B9328, "33172ACF7FAB5731C38D6328D0E7A677EEEF32198103C2114E9EA2BB6249885C"),
    ("auxiliary P2", 0x5DB700, 0x5DB728, "8A03ACD97845436324EEC8F16669BE4153C30440845E2C7385A8B6E45CA4DCCD"),
    ("constructor", 0x127E4, 0x12874, "7318C6DA564B699897D6E9EE7B22EA26540EE84F8492D3CCD247DF8E8A4EB94D"),
    ("complete event consumer", 0x12874, 0x129C8, "1BBCE2EEE607287D2AEFA2B899D43A9C4C6890BFE5CCAF6533D8FAF6EBF2EBD4"),
    ("P2 consumer", 0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def listing(data, start, stop):
    return [f"{i.mnemonic} {i.op_str}" for i in decode(data, start, stop)]


def source_listing(source, start, stop):
    return prefix.listing(source, 0x740900 + start, 0x740900 + stop,
                          prefix.CS_ARCH_X86, prefix.CS_MODE_16, -0x740900)


def dependencies(image):
    for name, start, stop, digest in GUARDS:
        need(sha(image[start:stop]) == digest, f"retained {name} instructions/data")
    for start, stop, digest in prefix.DEPENDENCIES:
        need(sha(image[start:stop]) == digest, f"retained prefix dependency {start:06X}")
    need(image[0x5C7800:0x5C8000] == b"\xff" * 0x800, "complete initializer remains absent")


def source_contract(source):
    rows = source_listing(source, 0x71D1, 0x7394)
    need(len(rows) == 129 and sha(source[0x747AD1:0x747C94]) == SOURCE_PHASE,
         "complete actual 129-instruction source player phase")
    need(rows[:10] == ["mov si, word ptr es:[0x65e]", "mov word ptr [bp - 6], si",
         "mov di, word ptr es:[0x65c]", "mov word ptr [bp - 8], di",
         "or word ptr [si + 4], 0x20", "xor bx, bx", "mov bl, byte ptr [di + 0x11]",
         "shl bx, 1", "mov ax, word ptr cs:[bx + 0x7554]", "mov word ptr [si + 0x50], ax"],
         "source object globals, other-character index and HP table producer")
    need(source_listing(source, 0x71F5, 0x722C) == [
         "cmp byte ptr es:[0x5d], 0", "jne 0x7206", "sar ax, 2",
         "sub word ptr [si + 0x50], ax", "jmp 0x721f",
         "cmp byte ptr es:[0x5d], 2", "jb 0x721f", "sar ax, 2",
         "add word ptr [si + 0x50], ax", "cmp byte ptr es:[0x5d], 3", "jne 0x721f",
         "add word ptr [si + 0x50], ax", "mov ax, word ptr [si + 0x50]", "shr ax, 1",
         "mov word ptr [si + 0x54], ax", "shr ax, 1", "mov word ptr [si + 0x56], ax"],
         "source unsigned difficulty branches and signed/unsigned HP shifts")
    need(source_listing(source, 0x730F, 0x731B) == ["mov ax, word ptr [bp - 6]",
         "mov word ptr [si + 0x1c], ax", "mov ax, word ptr [bp - 8]", "mov word ptr [si + 0x14], ax"] and
         source_listing(source, 0x7383, 0x7394) == ["mov ax, si", "sub ax, 0x96",
         "mov si, word ptr [bp - 6]", "mov word ptr [si + 0x1c], ax",
         "mov ax, word ptr [bp - 8]", "mov word ptr [si + 0x14], ax"],
         "source auxiliary and active back-link roles")
    resources = []
    for start, stop in ((0x7270, 0x729A), (0x7329, 0x7353)):
        pushes = source_listing(source, start, stop)
        need(len(pushes) == 15 and pushes[-2:] == ["push 0xc00", "push si"] and
             all(row.startswith("push ") for row in pushes), "source constructor argument population")
        values = [int(row[5:], 0) for row in pushes[:-1]]
        addresses = []
        for offset in (10, 7, 4):
            bank, segment, displacement = values[offset:offset + 3]
            need(0x80 <= bank <= 0xFF and 0x2000 <= segment < 0x3000 and displacement == 0,
                 "source constructor far pointer bounds")
            addresses.append((bank % 128) * 65536 + segment * 16 - 0x20000)
        resources.append(dict(arguments=values[:4], P1_P0_P2=addresses))
    need([r["P1_P0_P2"] for r in resources] ==
         [[0x3CF410, 0x3D5F80, 0x3D4B20], [0x3BD730, 0x3914E0, 0x3D7640]],
         "actual source constructor resource owners")
    return resources


def player_contract(image, gba, source):
    source_resources = source_contract(source)
    need(len(decode(image, 0x5C1000, 0x5C1180)) == 96, "complete native player instruction population")
    calls = semantic_checks(image)
    for source_row, native_row in zip(source_resources, (calls[2], calls[1]), strict=True):
        need(source_row["arguments"] == native_row["entry_sp_arguments"][:4],
             "source/native slot, tile and geometry arguments")
    need(listing(gba, 0x127E4, 0x12804) == ["push {r0, r3, r4, r5}",
         "ldr r5, [sp, #0x48]", "ldr r0, [sp, #0x40]", "str r0, [r5, #0x44]",
         "ldr r0, [sp, #0x34]", "str r0, [r5, #0x48]", "ldr r0, [sp, #0x28]",
         "str r0, [r5, #0x4c]"], "actual native constructor stack consumers")
    for start, stop in ((0x127E4, 0x12874), (0x12874, 0x129C8), (0x132EC, 0x133A8)):
        need(image[start:stop] == gba[start:stop], "complete native consumer retained")
    need(struct.unpack_from("<3I", gba, 0x37005C) == (0x030048A0, 0x0300489C, 0x03002310) and
         tuple(literal_value(image, at) for at in (0x5C1004, 0x5C100C, 0x5C1034)) ==
         (0x030048A0, 0x0300489C, 0x03002310), "commercial active/other/difficulty owners")
    need(listing(image, 0x5C1020, 0x5C106C) == ["ldrb r0, [r7, #0x11]", "lsl r0, r0, #1",
         "ldr r8, [pc, #0x158]", "ldrh r1, [r8, r0]", "asr r2, r1, #2",
         "ldr r8, [pc, #0x150]", "ldrb r3, [r8, #0xf]", "cmp r3, #0",
         "subeq r1, r1, r2", "beq #0x85c1058", "cmp r3, #2", "addhs r1, r1, r2",
         "cmp r3, #3", "addeq r1, r1, r2", "strh r1, [r4, #0x64]", "lsr r0, r1, #1",
         "strh r0, [r4, #0x68]", "lsr r0, r0, #1", "strh r0, [r4, #0x6a]"],
         "native HP index, conditions, shifts, destinations and widths")
    need(literal_value(image, 0x5C1028) == 0x085C1400 and
         image[0x5C1400:0x5C141E] == source[0x747E54:0x747E72], "all 15 actual HP entries")
    need(literal_value(image, 0x5C10A8) == 0x085BC800 and
         word(image, 0x5BC38C) == 0x03004D3C and word(image, 0x5BC3A4) == 0x085BC600 and
         word(image, 0x5BC600) == 0xE12FFF1E, "actual active/auxiliary callbacks and existing auxiliary handle")
    need(tuple(word(image, at) for at in (0x5C1000, 0x5C1178, 0x5C117C, 0x5C1300, 0x5BC384, 0x5BC388)) ==
         (0xE92D5FFF, 0xE8BD5FFF, 0xE12FFF1E, 0xE92D40FF, 0xE8BD40FF, 0xE12FFF1E) and
         listing(image, 0x5C1304, 0x5C1308) == ["b #0x85bc244"],
         "native saved register frames, returns and allocation-bypassing reuse")
    need([i.operands[0].imm for i in decode(image, 0x5C1000, 0x5C1180) if i.mnemonic == "bl"] ==
         [0x080127E4, 0x08012874, 0x080132EC, 0x085C1300], "native player service order")
    for at, expected in ((0x5C107C, 0xE3C88B2F), (0x5C1070, 0xE1C494BE),
                         (0x5C1074, 0xE1C495B0), (0x5C1084, 0xE1C493B4), (0x5C1088, 0xE1C493B6),
                         (0x5C108C, 0xE1C494B2), (0x5C1090, 0xE1C494B4), (0x5C1094, 0xE1C494B6),
                         (0x5C1098, 0xE1C494B8), (0x5C10A0, 0xE1C495B2), (0x5C10A4, 0xE1C495B4),
                         (0x5C10AC, 0xE5848000), (0x5C1174, 0xE5847018)):
        need(word(image, at) == expected, f"native player field semantics {at:06X}")
    hp_cases = 0
    for hp in struct.unpack_from("<15H", source, 0x747E54):
        need(0 < hp < 0x8000, "source signed-quarter and native positive-halfword domain")
        for difficulty in range(256):
            source_hp = hp
            if difficulty == 0:
                source_hp = (source_hp - (hp >> 2)) & 65535
            elif difficulty >= 2:
                source_hp = (source_hp + (hp >> 2)) & 65535
                if difficulty == 3:
                    source_hp = (source_hp + (hp >> 2)) & 65535
            native_hp = hp - (hp >> 2) if difficulty == 0 else hp + (hp >> 2) * ((difficulty >= 2) + (difficulty == 3))
            need((source_hp, source_hp >> 1, source_hp >> 2) == (native_hp, native_hp >> 1, native_hp >> 2),
                 "guarded source/native final HP projections")
            hp_cases += 1
    return dict(source_resources=source_resources, constructors=calls, HP_projection_cases=hp_cases)


def resource_contract(image, gba, old, source):
    p1 = [verify_entry(source, image[0x5D0000:0x5D0A4C], spec) for spec in SPECS]
    first_events = []
    for _, start, size, counts, _ in SPECS:
        for index, count in enumerate(counts):
            _, payload, a, b = struct.unpack_from("<4I", image, start + 8 + 16 * index)
            for pointer, length in ((payload, count * 16), (a, 8), (b, 10 if b else 0)):
                need(not length or BASE + start <= pointer < pointer + length <= BASE + start + size,
                     "every retained P1 pointer has its complete extent inside its owner")
        frame = word(image, start + 12) - BASE
        need(image[frame + 1] == 255 and struct.unpack_from("<H", image, frame + 6)[0] == 0,
             "first event skips sound request and alternate palette path")
        first_events.append(dict(P1=f"{start:06X}", frame=f"{frame:06X}", sound_byte=255, flags=0))
    need(listing(image, 0x12814, 0x1281C) == ["mvn r8, #0", "strh r8, [r5, #0x30]"] and
         listing(image, 0x128E0, 0x128EC) == ["ldrb r8, [r1, #1]", "cmp r8, #0xff", "beq #0x801291c"] and
         listing(image, 0x12934, 0x1294C) == ["ldrh r8, [r1, #6]", "tst r8, #0x200", "bne #0x8012978",
         "ldrsh r8, [r5, #0x30]", "cmn r8, #1", "beq #0x8012974"],
         "actual first-event branch consumers and constructor sentinel")
    for at, signature in ((0x12C80, "BA A1 D5 E1 0A 42 84 E0 B4 30 D4 E1 48 40 95 E5 04 B0 94 E5"),
                          (0x12C98, "02 00 11 E3 83 B1 8B 10 04 B0 9B E5"),
                          (0x12D50, "00 30 DA E5 83 32 8B E0")):
        expected = bytes.fromhex(signature)
        need(image[at:at + len(expected)] == gba[at:at + len(expected)] == expected,
             "actual native P0 indexed descriptor/tile consumer")
    p0 = [check_asset(image, source, *spec) for spec in
          ((0x3D5F80, 0x5D1000, 28, 0x3CF410, 0x5D0000),
           (0x3914E0, 0x5D1100, 61, 0x3BD730, 0x5D029C))]
    oracle = check_asset(gba, old, 0x2AD910, 0x3505E8, 21, 0x2AE180, 0x350248)
    for src, native in ((0x3D4B20, 0x5B9300), (0x3D7640, 0x5DB700)):
        need(image[native:native + 6] == source[src:src + 6] and image[native + 38:native + 40] == b"\0\0",
             "P2 source header and native padding")
        for index, color in enumerate(struct.unpack_from("<16H", image, native + 6)):
            channels = [(color >> shift) & 31 for shift in (0, 5, 10)]
            need(color < 0x8000 and all(c == 0 or c >= 3 and c % 2 for c in channels), "P2 color lattice")
            original = (channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2
            need(original == struct.unpack_from("<H", source, src + 6 + index * 2)[0], "every P2 color recovers source")
    return dict(P1=p1, P0=p0, commercial_P0_oracle=oracle, P2_inverse_colors=32, first_events=first_events)


def stack_paths(image, ranges, entry, allowed_calls):
    """Explore the exact local CFG, abstracting only named balanced callees."""
    instructions = {i.address - BASE: i for start, stop in ranges for i in decode(image, start, stop)}
    pending, seen, calls, returns, deepest = [(entry, 0)], set(), set(), set(), 0
    while pending:
        at, depth = pending.pop()
        if (at, depth) in seen:
            continue
        seen.add((at, depth))
        need(at in instructions and len(seen) <= 1000, "stack CFG remains inside reviewed instruction owners")
        item = instructions[at]
        text = f"{item.mnemonic} {item.op_str}"
        if item.mnemonic == "push":
            depth += 4 * len(item.operands)
        elif item.mnemonic == "pop":
            depth -= 4 * len(item.operands)
        elif text in ("str r5, [sp, #-4]!", "str r8, [sp, #-4]!", "stmdb sp!, {r8}", "stmdb sp!, {fp}", "stmdb sp!, {r2}"):
            depth += 4
        elif item.mnemonic == "add" and item.op_str.startswith("sp, sp, #"):
            depth -= item.operands[2].imm
        else:
            need("sp" not in [item.reg_name(r) for r in item.regs_access()[1]], "unknown stack-writing instruction")
        need(0 <= depth <= 256, "local stack depth remains bounded")
        deepest = max(deepest, depth)
        if item.mnemonic == "bl":
            destination = item.operands[0].imm
            need(destination in allowed_calls, "stack proof has only reviewed callees")
            calls.add((at, destination, depth))
        elif item.mnemonic == "bx":
            need(item.op_str == "lr" and depth == 0, "return restores the exact entry stack")
            returns.add(at)
            continue
        elif item.mnemonic.startswith("b") and item.mnemonic != "bic":
            pending.append((item.operands[0].imm - BASE, depth))
            if item.mnemonic == "b":
                continue
        pending.append((at + 4, depth))
    need(returns, "local stack proof reaches a return")
    return dict(local_max_bytes=deepest, calls=sorted(calls), return_sites=sorted(returns), states=len(seen))


def stack_contract(image):
    services = {0x080127E4, 0x08012874, 0x080132EC}
    player = stack_paths(image, ((0x5C1000, 0x5C1180),), 0x5C1000, services | {0x085C1300})
    auxiliary = stack_paths(image, ((0x5C1300, 0x5C1308), (0x5BC244, 0x5BC38C)), 0x5C1300, services)
    constructor = stack_paths(image, ((0x127E4, 0x1285C),), 0x127E4, set())
    event = stack_paths(image, ((0x12874, 0x129C8),), 0x12874, {0x080132EC, 0x080D15C0})
    palette = stack_paths(image, ((0x132EC, 0x133A8),), 0x132EC, set())
    for start, stop in ((0x5C1004, 0x5C1178), (0x5BC244, 0x5BC384),
                        (0x127E4, 0x1285C), (0x12874, 0x129C8), (0x132EC, 0x133A8)):
        need(all("fp" not in [i.reg_name(r) for r in i.regs_access()[1]] for i in decode(image, start, stop)),
             "player and retained native consumers preserve zero r11")
    need((player["local_max_bytes"], auxiliary["local_max_bytes"], constructor["local_max_bytes"]) == (116, 96, 16),
         "reviewed local frame and constructor argument depths")
    return dict(player=player, auxiliary=auxiliary, constructor=constructor, event_all_local_branches=event,
                palette=palette, direct_auxiliary_constructor_path_bytes=8 + 56 + 36 + 60 + 16,
                complete_transitive_bound_proved=False)


def wrapper_contract(before, after):
    need(len(before) == len(after) == 0x800000, "unchanged eight-MiB extent")
    need(before[START:STOP] == b"\xff" * 24, "exact new range was unoccupied")
    need(listing(after, START, STOP) == ["push {fp, lr}", "mov fp, #0", "bl #0x8629700",
         "bl #0x85c1000", "pop {fp, lr}", "bx lr"], "all six actual ARM instructions and ordered targets")
    restored = bytearray(after)
    restored[START:STOP] = before[START:STOP]
    need(restored == before, "exact full-ROM inverse; no outside route/data/dependency changed")


def wrapper_abi(image):
    cases = 0
    for flags in range(16):
        for sp in (0x03007EFC, 0x03007F00):
            for fp in (0, 1, 0x80000000, 0xFFFFFFFF):
                for lr in (0x0833FD1C, 0x0833FD1D):
                    regs = [0x12340000 + n * 0x1111 for n in range(15)]
                    regs[11], regs[13], regs[14] = fp, sp, lr
                    initial, saved, order = tuple(regs), {}, []
                    for at in range(START, STOP, 4):
                        encoded = word(image, at)
                        need(encoded >> 28 == 14, "wrapper has no incoming-flag-dependent instruction")
                        if encoded == 0xE92D4800:
                            regs[13] -= 8
                            saved[regs[13]], saved[regs[13] + 4] = regs[11], regs[14]
                        elif encoded == 0xE3A0B000:
                            regs[11] = 0
                        elif encoded >> 24 == 0xEB:
                            need(regs[11] == 0 and regs[13] == sp - 8, "callee r11 and wrapper stack contract")
                            order.append(prefix.target(at, encoded))
                            regs[14] = BASE + at + 4
                            # Both reviewed outer frames restore r0-r12 and SP; LR/flags may change here.
                        elif encoded == 0xE8BD4800:
                            regs[11], regs[14] = saved[regs[13]], saved[regs[13] + 4]
                            regs[13] += 8
                        elif encoded == 0xE12FFF1E:
                            need(tuple(regs) == initial, "all caller registers and return ISA bit restored")
                        else:
                            raise ValueError("instruction outside bounded wrapper ABI model")
                    need(order == [0x08629700, 0x085C1000], "prefix returns before the player phase is called")
                    cases += 1
    return dict(cases=cases, incoming_NZCV=16, saved_registers="r11,LR", added_stack_bytes=8,
                preserved="r0-r12,LR,SP", flags="clobbered", return_ISA_states=2, internal_r11=0)


def scan(data, origin=0):
    """All byte-alignment pointers, ROM mirrors, and ARM/Thumb static references."""
    hits = []
    def inside(value):
        return any(base + START <= value < base + STOP for base in (BASE, 0x0A000000, 0x0C000000))
    for alignment in range(4):
        stop = len(data) - ((len(data) - alignment) % 4)
        for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            if inside(encoded):
                hits.append(("pointer", origin + alignment + 4 * n, encoded))
    for n, (encoded,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at, pc = origin + n * 4, BASE + origin + n * 4 + 8
        if encoded & 0x0E000000 == 0x0A000000 and inside(prefix.target(at, encoded)):
            hits.append(("ARM branch", at, prefix.target(at, encoded)))
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


def classify_own_references(image, hits):
    expected = [("Thumb literal/ADR", START, BASE + START + 4),
                ("Thumb literal/ADR", START + 16, BASE + START + 20)]
    need(hits == expected, "no external or unclassified references into the complete wrapper")
    owners = {i.address - BASE: i for i in decode(image, START, STOP)}
    classified = []
    for kind, site, destination in hits:
        owner = owners.get(site)
        expected_word = {START: 0xE92D4800, START + 16: 0xE8BD4800}[site]
        need(owner is not None and owner.size == 4 and word(image, site) == expected_word and
             f"{owner.mnemonic} {owner.op_str}" == ("push {fp, lr}" if site == START else "pop {fp, lr}") and
             struct.unpack_from("<H", image, site)[0] == 0x4800 and destination == BASE + site + 4,
             "Thumb-looking low halfword belongs to the exact decoded ARM frame instruction")
        classified.append(dict(raw_kind=kind, site=f"{site:06X}", raw_target=f"{destination:08X}",
                               ARM_word=f"{expected_word:08X}", ARM_owner=f"{owner.mnemonic} {owner.op_str}",
                               classification="low halfword of owned ARM instruction; entry contract is ARM"))
    return classified


def negatives(blobs):
    rejected = []
    def reject(label, check):
        try:
            check()
        except (ValueError, SystemExit, struct.error) as error:
            rejected.append(dict(case=label, reason=str(error)))
        else:
            raise ValueError(f"accepted negative control: {label}")
    for at in (*range(START, STOP), START - 1, STOP, 0x629700, 0x5C1000, 0x5C7800, 0x5D1004):
        wrong = bytearray(blobs["after"]); wrong[at] ^= 1
        reject(f"output byte {at:06X}", lambda: wrapper_contract(blobs["before"], wrong))
    for name, at, _, _ in GUARDS:
        wrong = bytearray(blobs["before"]); wrong[at] ^= 1
        reject(f"dependency {name}", lambda: dependencies(wrong))
    for label, at, value in (("nonzero internal r11", START + 4, 0xE3A0B001),
                             ("lost saved r11", START + 16, 0xE8BD4000)):
        wrong = bytearray(blobs["after"]); struct.pack_into("<I", wrong, at, value)
        reject(label, lambda: wrapper_abi(wrong))
    wrong = bytearray(blobs["after"])
    for at, destination in ((START + 8, 0x085C1000), (START + 12, 0x08629700)):
        struct.pack_into("<I", wrong, at, 0xEB000000 | (((destination - (BASE + at + 8)) // 4) & 0xFFFFFF))
    reject("correct targets in reversed component order", lambda: wrapper_abi(wrong))
    for label, at, value in (("active/other owner inversion", 0x5C1180, 0x0300489C),
                             ("wrong HP condition", 0x5C104C, 0x80811002),
                             ("HP signed threshold", 0x5C105C, 0xE1A000C1),
                             ("auxiliary active/other inversion", 0x5BC398, 0x0300489C),
                             ("auxiliary allocation no longer bypassed", 0x5C1304, 0xEAFFEBCC),
                             ("wrong object halfword width", 0x5C1070, 0xE584904E)):
        wrong = bytearray(blobs["before"]); struct.pack_into("<I", wrong, at, value)
        reject(label, lambda: player_contract(wrong, blobs["gba"], blobs["source"]))
    wrong = bytearray(blobs["before"])
    wrong[0x5C10C0:0x5C10C4], wrong[0x5C10E8:0x5C10EC] = wrong[0x5C10E8:0x5C10EC], wrong[0x5C10C0:0x5C10C4]
    reject("constructor P1/P2 producer corruption", lambda: semantic_checks(wrong))
    wrong = bytearray(blobs["before"]); struct.pack_into("<I", wrong, 0x5C1120, 0xE28DD038)
    reject("constructor cleanup leaks four bytes", lambda: stack_contract(wrong))
    wrong = bytearray(blobs["before"]); wrong[0x5C1178] ^= 1
    reject("player outer stack restore drops r0", lambda: stack_contract(wrong))
    for at in (0x5D0068, 0x5F49FF, 0x5DB2BF, 0x5B9306, 0x5DB706):
        wrong = bytearray(blobs["before"]); wrong[at] ^= 1
        reject(f"semantic resource byte {at:06X}", lambda: resource_contract(wrong, blobs["gba"], blobs["old"], blobs["source"]))
    for at in (0x747AD1, 0x747AF0, 0x747B7E, 0x747C12, 0x747C91):
        wrong = bytearray(blobs["source"]); wrong[at] ^= 1
        reject(f"actual source byte {at:06X}", lambda: source_contract(wrong))
    wrong = bytearray(blobs["after"]); struct.pack_into("<I", wrong, START, 0xE1A04800)
    reject("Thumb-looking word without ARM push ownership", lambda: classify_own_references(wrong,
           [("Thumb literal/ADR", START, BASE + START + 4), ("Thumb literal/ADR", START + 16, BASE + START + 20)]))
    scanner_cases = 0
    for mirror in (BASE, 0x0A000000, 0x0C000000):
        for interior in (0, 1, 8, 23):
            for alignment in range(4):
                sample = bytearray(b"\xff" * 64)
                struct.pack_into("<I", sample, alignment, mirror + START + interior)
                need(any(hit[0] == "pointer" for hit in scan(sample)), "scanner catches mirrored/interior/unaligned pointer")
                scanner_cases += 1
    for encoded in (0xEA00003E, 0xEB00003E, 0xE59F80F8, 0xE28F00F8):
        need(scan(struct.pack("<I", encoded) + b"\xff" * 60, START - 0x100), "scanner catches ARM reference")
        scanner_cases += 1
    for encoded in (0x483F, 0xA03F, 0xE07E, 0xD07E):
        need(scan(struct.pack("<H", encoded) + b"\xff" * 62, START - 0x100), "scanner catches Thumb reference")
        scanner_cases += 1
    for tail in (0xF87E, 0xE87E):
        need(scan(struct.pack("<HH", 0xF000, tail) + b"\xff" * 60, START - 0x100), "scanner catches Thumb BL/BLX")
        scanner_cases += 1
    return rejected, scanner_cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "source", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    names = ("before", "after", "gba", "old", "source")
    need(all(getattr(args, n).suffix.lower() == ".gba" for n in names[:3]) and
         all(getattr(args, n).suffix.lower() == ".wsc" for n in names[3:]), "ROM-only inputs before reading")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in
         {getattr(args, n).resolve() for n in names}, "distinct JSON report before reading")
    blobs = {name: getattr(args, name).read_bytes() for name in names}
    need(tuple(sha(blobs[n]) for n in ("before", "gba", "old", "source")) == (BEFORE, *prefix.ORIGINALS),
         "pinned predecessor and all three immutable original ROMs")
    before, after, gba, old, source = (blobs[n] for n in names)
    wrapper_contract(before, after)
    dependencies(before)
    trace = prefix.source_trace(gba, old, source)
    prefix.code_contract(before, trace)
    prefix_abi = prefix.abi_effects(before, trace)
    graphics = prefix.decode_and_check(before)
    graphics_source = prefix.verify_sources(dict(gba=gba, wsc10=old, wsc15=source), before)
    for character in range(256):
        result, _, reads, _ = prefix.run_exact(before, 0x629500, character, 11)
        need(result == 11 and reads == (0x0300231E,), "retained manager selects stage 11 for every character byte")
    player = player_contract(before, gba, source)
    commercial = check_constructor(gba, 0x372810, 0x372868, (0x08350248, 0x083505E8, 0x08352240), 0x99, 0)
    resources = resource_contract(before, gba, old, source)
    stack = stack_contract(before)
    abi = wrapper_abi(after)
    need(not scan(before), "no preexisting static references to any new wrapper byte")
    classified = classify_own_references(after, scan(after))
    negative, scanner_cases = negatives(blobs)
    need(sha(after) == AFTER, "final artifact identity after independent semantic checks")
    report = dict(schema=1, status="PASS", kind="independent-shoot-initializer-player-chain-verification",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=list(prefix.ORIGINALS),
        source_range=["4090:7168", "4090:7394"], source_player_raw_half_open=["747AD1", "747C94"],
        source_player_sha256=SOURCE_PHASE, source_player_instructions=129, native_player_instructions=96,
        writes=[[f"{START:06X}", f"{STOP:06X}"]], declared_bytes=24,
        changed_bytes=sum(a != b for a, b in zip(before, after)), full_inverse=True,
        new_instructions=6, new_RAM_bytes=0, internal_call_order=["08629700", "085C1000"],
        external_callers_added=0, full_initializer_absent=True, wrapper_ABI=abi, prefix_ABI_and_order=prefix_abi,
        player_contract=player, commercial_constructor=commercial, resource_contract=resources, stack_contract=stack,
        graphics_dependency=graphics, graphics_source_dependency=graphics_source, stage_priority_cases=256,
        retained_dependencies=[dict(name=n, start=f"{a:06X}", end=f"{z:06X}", sha256=h) for n,a,z,h in GUARDS],
        allocation=dict(all_pointer_alignments=True, ROM_mirrors=["08", "0A", "0C"], ARM_and_Thumb_scan=True,
                        raw_references_classified_by_ARM_owner=classified, external_references=[]),
        negative_controls=negative, scanner_negative_controls=scanner_cases,
        negative_control_count=len(negative) + scanner_cases,
        preconditions=["ARM entry with a valid native stack and eight additional writable stack bytes beyond the retained callees' requirements.",
                       "Existing valid objects at 030048A0, 0300489C, 03004D3C; other-character ID is 0..14.",
                       "Initialized native globals and exclusive scene/display ownership during both calls."],
        limits=["Disconnected component order only; no full initializer or external scene/controller entry is installed.",
                "Player final fields/resources and retained instruction contracts are checked; intermediate player store timing is not newly proved.",
                "176 bytes is one concrete auxiliary constructor path, not a complete transitive or interrupt stack bound.",
                "No emulator, game service, supplied save, runtime, visual, audio or hardware timing test was performed.",
                "Source SRAM 1000:3CD8/3CDA, terminal DI, camera lifetime and remaining initializer phases stay open."],
        input_ROMs_written=False, supplied_save_accessed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=report["output_sha256"], changed_bytes=report["changed_bytes"],
                         ABI_cases=abi["cases"], negative_control_count=report["negative_control_count"])))


if __name__ == "__main__":
    main()
