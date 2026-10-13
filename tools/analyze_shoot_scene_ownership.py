#!/usr/bin/env python3
"""Bound Shoot scene ownership to the retail task lifecycle, without execution.

The proof is conditional on entering through the normal live battle task. It
does not prove arbitrary RAM-derived calls safe or declare a global absence of
indirect palette writers. No game code, save, or emulator is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

PROFILES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
RANGES = (
    ("wsc15", 0x771F00, 0x772061, "847CEB2B4299B0ED0F375262774BE4DA0444C8811CE331F08C27BB46D4522881", "scene entry and both input task selections"),
    ("wsc15", 0x772DEA, 0x7734A9, "39CA2AD6110D79A81414788BAF8997D067F8C220C839DF39090CD66ECB7AC988", "EEA through task retirement 15A8"),
    ("wsc15", 0x741069, 0x741116, "A1097AEB6EB498778908B94C742B5D7186155D78A6785D469B8D639270161998", "source inactive and scene input callbacks"),
    ("wsc15", 0x740FBA, 0x74101A, "431ED73F48DF7F7E148AD4BBE20B33D292869536AC167C51A116A70F7436F279", "source two task handles and priorities"),
    ("wsc15", 0x7424C6, 0x7424D6, "ED3AE42813AA52BE9B2FA58CA13A2D916945EF37D510987E30A5DF74E666E55C", "scene input sole local callee"),
    ("wsc15", 0x750BB7, 0x750BD5, "F06EBF042A81B9C77C6D2215E776D51D345FB7302C0632024AC4C276CB6C5506", "source task callback replacement ABI"),
    ("gba", 0x33FC28, 0x33FE1C, "1B6C57EF17667CBDDC76016F7BE6BA07FDB4DFD4B1B748F5BCBBFBFD430ECE56", "native scene root, creation choice, capture"),
    ("gba", 0x374EFC, 0x375314, "8E4F55A58189AF2D81722B40AC21F512B91EFF8A505C741C2554C020EA5A748D", "inactive, scene, full input and pause callers"),
    ("gba", 0x37354C, 0x373928, "F5CD59EC5702CC94AB6F7F36C063C7751CAF27C1CAB09DF2C4FA59CCCD2ECD7A", "scene update versus normal battle root producers"),
    ("gba", 0x377900, 0x377BD0, "E61A36D2BD8FCC8FAE3D4DFDDAA1EF96A6985F0DC3698FE75BCE02E63FBB3AA8", "bootstrap mirror write and task retirement"),
    ("gba", 0xD1BBC, 0xD1C68, "DFBCD7ADC95D800702A67B72B646055CFC4F16B06AD126837792378A96305DD5", "native two task handles and priorities"),
    ("gba", 0x11AC4, 0x11CB0, "87DF81E6A2D6A680EBC1B5CA771EAA7EAEC72B527B69395641F426B7DB410025", "native task allocation and unlink ABI"),
    ("gba", 0x11D78, 0x11E8C, "B08543611930783CE49D1B75ECA86F9AB11C48C9DCD97DC834DA6A9FF89DF415", "serial scheduler and callback replacement ABI"),
    ("gba", 0x12008, 0x12058, "9BA17D280349C0E8A6ED2A05F5C1168F4515274BC001640898F0F4EACDDD2F81", "current task callback, state and retirement helpers"),
    ("gba", 0x353B48, 0x353B74, "33493EDC0598F9CD9548F2CB191CBC2F9804218702DD1DA5572CB7BB3A7D7FA3", "scene input sole callee"),
    ("gba", 0x352B10, 0x352B24, "EFCFC38628F46D760CDA308DA2593EF367CBCF45D352AB33BA0CDC44391E19FA", "native pause/freeze mask consumer"),
)
SCENE_BASE = 0x771F00
SOURCE_PHASES = [0xEEA, 0xF67, 0xFC3, 0x1043, 0x10DD, 0x11F7, 0x1267,
                 0x12C6, 0x1331, 0x139C, 0x13F4, 0x1434, 0x1486, 0x1540]
SOURCE_EDGES = [(0xF5A, 0xF67), (0xFA9, 0xFC3), (0x1036, 0x1043),
                (0x10CF, 0x10DD), (0x11EA, 0x11F7), (0x1259, 0x1267),
                (0x12B8, 0x12C6), (0x1323, 0x1331), (0x138E, 0x139C),
                (0x13E6, 0x13F4), (0x1426, 0x1434), (0x1478, 0x1486),
                (0x14F7, 0x1540)]
SOURCE_TIMERS = [(0xF03, 151), (0xF98, 200), (0x1020, 5), (0x1069, 100),
                 (0x10B1, 6), (0x11D9, 32), (0x1248, 32), (0x12A7, 150),
                 (0x1312, 32), (0x13CE, 30), (0x1462, 0), (0x14E6, 20)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def decode(data: bytes, raw: int, end: int, address: int, arm: bool) -> list:
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    result = list(decoder.disasm(data[raw:end], address))
    require(sum(i.size for i in result) == end - raw, f"incomplete bounded decoding at {raw:X}")
    return result


def at(data: bytes, raw: int, end: int, address: int, arm: bool, expected: list[str]) -> None:
    actual = [f"{i.mnemonic} {i.op_str}".strip() for i in decode(data, raw, end, address, arm)]
    require(actual == expected, f"instruction contract changed at {address:X}")


def arm_at(data: bytes, raw: int, expected: list[str]) -> None:
    at(data, raw, raw + len(expected) * 4, raw + 0x08000000, True, expected)


def arm_literal(data: bytes, raw: int) -> int:
    word = struct.unpack_from("<I", data, raw)[0]
    require(word & 0xFFFFF000 == 0xE59F8000, f"expected r8 PC literal at {raw:X}")
    return struct.unpack_from("<I", data, raw + 8 + (word & 0xFFF))[0]


def native_retarget(data: bytes, call: int) -> tuple[int, int]:
    arm_at(data, call - 24, ["ldr sb, [r8]", "stmdb sp!, {sb}", "stmdb sp!, {fp}"])
    arm_at(data, call - 8, ["stmdb sp!, {r8}", "stmdb sp!, {fp}",
                              "bl #0x8011e7c", "add sp, sp, #0x10"])
    return arm_literal(data, call - 28), arm_literal(data, call - 12)


def source_retarget(data: bytes, call: int) -> tuple[int, int]:
    raw = SCENE_BASE + call
    block = data[raw - 14:raw + 8]
    require(block[:4] == bytes.fromhex("68 90 40 68") and
            block[6:12] == bytes.fromhex("68 00 0C 26 FF 36") and
            block[14:] == bytes.fromhex("9A C7 0B FF 4F 83 C4 08"),
            f"source callback replacement ABI changed at {call:X}")
    return struct.unpack_from("<H", block, 12)[0], struct.unpack_from("<H", block, 4)[0]


def source_contract(data: bytes) -> dict:
    entry = decode(data, SCENE_BASE, SCENE_BASE + 0x161, 0, False)
    life = decode(data, SCENE_BASE + 0xEEA, SCENE_BASE + 0x15A9, 0xEEA, False)
    retargets = [(i.address, *source_retarget(data, i.address)) for i in entry + life
                 if i.mnemonic == "lcall" and i.op_str == "0x4fff, 0xbc7"]
    require(retargets == [(0x4B, 0x3DE, 0x769), (0x61, 0x3E0, 0xB8B),
                         (0xB1, 0x3DE, 0x7D6), (0xDB, 0x3DE, 0x7D6),
                         (0x1574, 0x3DE, 0x7FA), (0x158A, 0x3E0, 0xD0B)],
            "source handle callback lifetime changed")
    entry_by_address = {i.address: i for i in entry}
    for point, wanted in {
        0x69: ("cmp", "word ptr [bp + 6], 5"), 0x84: ("cmp", "ax, 0xb"),
        0x88: ("je", "0xa3"), 0x8A: ("cmp", "byte ptr es:[0x5d], 3"),
        0x90: ("je", "0xcd"), 0x92: ("cmp", "byte ptr es:[0x5d], 0"),
        0x98: ("je", "0xa3"), 0x9A: ("test", "word ptr es:[0x68], 0x400"),
        0xA1: ("je", "0xcd"),
    }.items():
        actual = entry_by_address[point]
        require((actual.mnemonic, actual.op_str) == wanted, f"source case-5 selection changed at {point:X}")
    for point, destination in ((0xB9, 0x653), (0xE3, 0xEEA)):
        wanted = bytes.fromhex("68 F0 0F 68 F0 71 68") + struct.pack("<H", destination) + bytes.fromhex("9A 80 09 FF 4F 83 C4 06")
        require(data[SCENE_BASE + point:SCENE_BASE + point + len(wanted)] == wanted,
                "source case-5 existing scene allocation changed")
    instructions = {i.address: i for i in life}
    edges = []
    timers = []
    for n, i in enumerate(life):
        if i.mnemonic == "mov" and i.op_str == "word ptr [bx], ax":
            previous = life[n - 1]
            require(previous.mnemonic == "mov" and previous.op_str.startswith("ax, 0x"),
                    "source callback destination no longer immediate")
            target = int(previous.op_str.split(", ")[1], 0)
            require([(j.mnemonic, j.op_str) for j in life[n + 1:n + 5]] == [
                ("mov", "ax, 0x71f0"), ("mov", "word ptr [bx + 2], ax"),
                ("pop", "ds"), ("pop", "bx")], "source callback segment changed")
            edges.append((previous.address, target))
        if i.mnemonic == "mov" and i.op_str.startswith("word ptr [si + 0x42], "):
            value = i.op_str.split(", ")[1]
            require(value != "ax", "dynamic source phase timer")
            timers.append((i.address, int(value, 0)))
    require(edges == SOURCE_EDGES, "source phase graph changed")
    require(timers == SOURCE_TIMERS, "source timer initialization changed")
    for point, wanted in {
        0x1073: ("lcall", "0x71f0, 0x161"), 0x1082: ("lcall", "0x4fff, 0x2142"),
        0x1225: ("lcall", "0x4fff, 0x1f7b"), 0x123E: ("lcall", "0x4fff, 0x50f2"),
        0x1243: ("lcall", "0x4090, 0x7168"), 0x1295: ("lcall", "0x4fff, 0x1e9d"),
        0x12E4: ("cmp", "word ptr [si + 0x42], 0x82"),
        0x12FB: ("mov", "word ptr [si + 2], 0xd2"),
        0x1300: ("mov", "word ptr [si + 0xe], 2"),
        0x1366: ("lcall", "0x4fff, 0x1ef5"),
        0x15A0: ("lcall", "0x4fff, 0xa32"), 0x15A8: ("retf", ""),
    }.items():
        require((instructions[point].mnemonic, instructions[point].op_str) == wanted,
                f"source phase event changed at {point:X}")
    for point in (0x1210, 0x1280, 0x134A):
        at(data, SCENE_BASE + point, SCENE_BASE + point + 9, point, False, [
            "mov ax, word ptr [si + 0x42]", "and ax, 1", "shl ax, 8"])
    for point in (0x121C, 0x128C, 0x135B):
        require(data[SCENE_BASE + point:SCENE_BASE + point + 3] == b"\x68\x80\x00",
                "source transition half is not 128 colors")
    # The only local callee of 07D6 is a three-byte-counter reset, not a pause check.
    at(data, 0x7410D6, 0x7410FA, 0x7D6, False, [
        "mov ax, 0xc00", "mov ds, ax", "mov ax, 0x1000", "mov es, ax",
        "mov word ptr [0x3a20], 0", "call 0x1bc6", "mov ax, word ptr es:[0x1de]",
        "mov bx, word ptr es:[0x1e0]", "mov word ptr [0x3a14], ax",
        "mov word ptr [0x3a16], bx", "retf"])
    at(data, 0x7424C6, 0x7424D6, 0x1BC6, False, [
        "mov byte ptr [0x3bae], 0", "mov byte ptr [0x3baf], 0",
        "mov byte ptr [0x3cd6], 0", "ret"])
    fallthroughs = [target for site, target in edges if site + 13 == target]
    require(fallthroughs == [0xF67, 0x1043, 0x11F7], "same-invocation phase falls changed")
    return {"decoded_entry_instructions": len(entry), "decoded_lifecycle_instructions": len(life),
            "task_replacements": retargets, "phase_edges": edges, "timer_initializers": timers,
            "same_invocation_fallthrough_targets": fallthroughs,
            "eea_selection": "case==5 and stage!=11 and (difficulty==3 or (difficulty!=0 and (progression0068&0400)==0)); equality tests, not signed clamping",
            "mirror_lifetime": ["1073 full snapshot", "1243 ordered 7168", "1331 restore ends at 1378"],
            "input_suppression_lifetime": ["case-5 scene entry", "1574 and 158A restore", "15A0 self retirement"],
            "hold": {"executions": 150, "sound_attempt_after_decrement_to": 130, "id": 0xD2, "type": 2},
            "transition_executions": {"11F7 white prelude": 32, "1267 to black": 32, "1331 to saved target": 32},
            "event_dependent_phases": ["10DD waits bit03D6.10 and presentation events", "139C waits player+6.0800",
                                       "1434 waits03D8.2", "1486 HP count with 30-tick delay"]}


def native_contract(data: bytes) -> dict:
    replacements = [(p + 0x08000000, *native_retarget(data, p))
                    for p in (0x33FCA0, 0x33FCC4, 0x33FCFC, 0x377B84, 0x377BA8)]
    require(replacements == [(0x0833FCA0, 0x03004510, 0x08374EFC),
                             (0x0833FCC4, 0x03004514, 0x0837354C),
                             (0x0833FCFC, 0x03004510, 0x08374FAC),
                             (0x08377B84, 0x03004510, 0x08374FF4),
                             (0x08377BA8, 0x03004514, 0x083735BC)],
            "native task callback owner changed")
    arm_at(data, 0x11E7C, ["ldr r8, [sp, #0xc]", "ldr sb, [sp, #4]", "str sb, [r8]", "bx lr"])
    arm_at(data, 0x11DC8, ["push {r2, r5, lr}", "ldr r8, [r5]", "mov lr, pc", "bx r8", "pop {r2, r5, lr}"])
    arm_at(data, 0x12030, ["stmdb sp!, {lr}", "ldr r8, [pc, #0x18]", "ldr sb, [r8]",
                            "stmdb sp!, {sb}", "stmdb sp!, {fp}", "bl #0x8011be4",
                            "add sp, sp, #8", "ldm sp!, {lr}", "bx lr"])
    require(arm_literal(data, 0x12034) == 0x0300133C, "current-task handle changed")
    arm_at(data, 0x11BFC, ["mov sl, #0", "strh sl, [r4, #0x10]"])
    arm_at(data, 0x377BAC, ["add sp, sp, #0x10", "bl #0x8012030", "ldm sp!, {lr}", "bx lr"])
    arm_at(data, 0x374FAC, ["stmdb sp!, {lr}", "ldr r8, [pc, #0x2c]", "mov sb, #0",
        "strh sb, [r8]", "bl #0x8353b48", "ldr r8, [pc, #0x20]", "ldrsh r0, [r8, #0x10]",
        "ldrsh r1, [r8, #0x12]", "ldr r8, [pc, #0x18]", "strh r0, [r8]",
        "ldr r8, [pc, #0x14]", "strh r1, [r8]", "ldm sp!, {lr}", "bx lr"])
    require([arm_literal(data, p) for p in (0x374FB0, 0x374FC0, 0x374FCC, 0x374FD4)] ==
            [0x0300482A, 0x03002338, 0x0300451C, 0x0300451E], "scene input stores changed")
    arm_at(data, 0x353B48, ["ldr r8, [pc, #0x18]", "mov sb, #0", "strb sb, [r8]",
        "ldr r8, [pc, #0x10]", "strb sb, [r8]", "ldr r8, [pc, #0xc]", "strb sb, [r8]", "bx lr"])
    require([arm_literal(data, p) for p in (0x353B48, 0x353B54, 0x353B5C)] ==
            [0x03004C4D, 0x03004C4E, 0x03004C4C], "scene input reset stores changed")
    arm_at(data, 0x373628, ["ldr r8, [pc, #0xec]", "ldrb sb, [r8]", "tst sb, #7", "bne #0x83736e8"])
    require(arm_literal(data, 0x373628) == 0x03004529, "case-5 pause/freeze gate changed")
    arm_at(data, 0x3736A8, ["mov r8, #5", "stmdb sp!, {r8}", "bl #0x833fc28",
                            "add sp, sp, #4", "b #0x83738d4"])
    arm_at(data, 0x373650, ["ldr r8, [pc, #0xc8]", "ldrh sb, [r8, #2]", "cmp sb, #2", "bne #0x83736bc"])
    require(arm_literal(data, 0x373650) == 0x03004500, "case-5 battle-mode gate changed")
    require(struct.unpack_from("<I", data, 0x33FDB4)[0] == 0x0834059C,
            "native case-5 existing scene callback changed")
    arm_at(data, 0x33FD04, ["ldr r8, [pc, #0xa8]", "stmdb sp!, {r8}", "stmdb sp!, {fp}",
                            "mov r8, #0xff0", "stmdb sp!, {r8}", "bl #0x8011ac4", "add sp, sp, #0xc"])
    return {"task_replacements": replacements,
            "source_native_pairs": [["4090:0769", "08374EFC"], ["4090:07D6", "08374FAC"],
                                    ["4090:07FA", "08374FF4"], ["4090:0B8B", "0837354C"],
                                    ["4090:0D0B", "083735BC"]],
            "source_native_task_handles": [["1000:03DE", "03004510"], ["1000:03E0", "03004514"]],
            "source_native_task_state_bias": [16, 24],
            "task_priorities": {"input": 0xF00, "scene": 0xFF0, "battle_update": 0x6000},
            "normal_case5_producer": "083736B0, 03004529&7==0, mode03004502==2, second player HP<=0",
            "new_input_callbacks_have_pause_entry": False,
            "bootstrap_retirement": "08377B54 restores both tasks, then 08377BB0 calls 08012030",
            "allocation_deduplicates_priority": False,
            "retirement_abi": "08012030 uses 0300133C; 08011BE4 clears task+10 and unlinks node"}


def scan(data: bytes) -> dict:
    targets = (0x0833FC28, 0x0833FDC0, 0x08375360, 0x08374FAC, 0x08374FF4)
    branches = {target: [] for target in targets}
    literals = {target: [] for target in (0x03004510, 0x03004514, 0x08374FAC, 0x08374FF4)}
    for site in range(0, len(data), 4):
        word = struct.unpack_from("<I", data, site)[0]
        if word in literals:
            literals[word].append(site + 0x08000000)
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            target = site + 0x08000008 + delta * 4
            if target in branches:
                branches[target].append(site + 0x08000000)
    require(branches[0x08375360] == [0x08375298, 0x083752CC], "pause entry branch population changed")
    require(branches[0x0833FC28] == [0x08373688, 0x083736B0, 0x083736DC, 0x083738B0, 0x0837574C, 0x08378510],
            "scene root branch population changed")
    require(branches[0x0833FDC0] == [0x08340110, 0x083403BC, 0x08340728, 0x08340C18, 0x08340EC0],
            "mirror capture branch population changed")
    require(literals[0x03004510] == [0x080D1C18, 0x080D1C60, 0x0833FD98, 0x0833FDAC, 0x08377BC0] and
            literals[0x03004514] == [0x080D1C20, 0x080D1C64, 0x0833FDA0, 0x08377BC8],
            "task handle literal population changed")
    return {"denominator": "all aligned words of the exact retail GBA ROM; B/BL encodings and exact literals",
            "branch_references": {f"{k:08X}": v for k, v in branches.items()},
            "literal_references": {f"{k:08X}": v for k, v in literals.items()},
            "indirect_or_computed_references_excluded": False}


def negative_cases(gba: bytes, source: bytes) -> list[str]:
    cases = [
        ("scene input replaced with full pause-capable input", "gba", 0x33FDB0, struct.pack("<I", 0x08374FF4)),
        ("battle task is not replaced", "gba", 0x33FDA4, struct.pack("<I", 0x083735BC)),
        ("bootstrap does not retire after restoring normal tasks", "gba", 0x377BB0, bytes.fromhex("00 00 A0 E1")),
        ("case-5 bypasses pause gate", "gba", 0x373634, bytes.fromhex("00 00 A0 E1")),
        ("source restores wrong input callback", "wsc15", SCENE_BASE + 0x156A, struct.pack("<H", 0x7D6)),
        ("source fade starts at wrong parity/count", "wsc15", SCENE_BASE + 0x124B, struct.pack("<H", 31)),
        ("source exit leaves scene task alive", "wsc15", SCENE_BASE + 0x15A1, struct.pack("<H", 0xBC7)),
    ]
    passed = []
    for label, name, raw, replacement in cases:
        modified = bytearray(gba if name == "gba" else source)
        require(modified[raw:raw + len(replacement)] != replacement, f"ineffective negative case: {label}")
        modified[raw:raw + len(replacement)] = replacement
        try:
            native_contract(bytes(modified)) if name == "gba" else source_contract(bytes(modified))
        except (ValueError, KeyError):
            passed.append(label)
        else:
            raise ValueError(f"semantic negative escaped: {label}")
    return passed


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in PROFILES:
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    sources = {name: getattr(args, name).read_bytes() for name in PROFILES}
    for name, data in sources.items():
        require(sha(data) == PROFILES[name], f"unknown input revision: {name}")
    evidence = []
    for name, start, end, expected, label in RANGES:
        require(sha(sources[name][start:end]) == expected, f"evidence range changed: {label}")
        evidence.append({"input": name, "start": start, "end": end, "sha256": expected, "role": label})
    gba, source = sources["gba"], sources["wsc15"]
    report = {
        "schema": 1, "kind": "shoot-scene-task-ownership",
        "inputs": {name: {"bytes": len(data), "sha256": PROFILES[name]} for name, data in sources.items()},
        "evidence_ranges": evidence, "source": source_contract(source), "native": native_contract(gba),
        "finite_references": scan(gba), "negative_cases": negative_cases(gba, source),
        "conclusion": "retail task replacement supplies a concrete conditional ownership mechanism; native Shoot scene is not installed",
        "entry_preconditions": [
            "normal retail battle owns live input and battle task handles, with one scene transition at a time",
            "no foreign startup, pause, or cutscene task is concurrently live; normal task callbacks alone are not a RAM-wide uniqueness proof",
            "normal case-5 producer 083736B0 passes its existing pause/freeze and battle-mode gates",
            "selected source case-5 branch is EEA under original stage/difficulty/progression conditions",
            "the existing scene allocation callback is replaced; no second parallel scene task is added",
            "both tasks remain on their scene callbacks until source 1574/158A restoration and 15A0 retirement",
        ],
        "integration_boundary": {"existing_scene_callback_literal": "0833FDB4 -> 0834059C",
            "native_task_creation_call": "0833FD18 -> 08011AC4", "required_new_callback": "complete source EEA scene translation",
            "source_snapshot_call": "1073 before destructive writes", "native_snapshot_helper": "085C1900",
            "required_initializer_boundary": "source1243 -> 7168 ordered phases, then 085C1C00 preparation",
            "not_a_safe_replacement": "direct call to initializer or separate scene allocation while retail scene remains live"},
        "excluded_claims": ["arbitrary caller safety", "global proof against computed/indirect writers",
                            "priority allocation uniqueness", "all lower callbacks implemented", "native scene installed",
                            "source D2 timing scheduled natively", "emulator or save QA", "frame or visual parity"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-scene-ownership] bounded task lifecycle PASS; conditional entry; report {sha(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
