#!/usr/bin/env python3
"""ROM-only evidence for the Shoot defeat/result/exit scene and native ABIs.

The result display is a proved existing retail resource.  Calling it a reward
does not imply an invented score, unlock or currency write: the source ends by
retiring this task and returning three existing mode words to (1, 0, 0).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

HASHES = (
    "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
)
BASE, SCENE = 0x08000000, 0x771F00
PHASES = (0x1750, 0x17DF, 0x182F, 0x18EE, 0x193B, 0x197A, 0x19F2,
          0x1A42, 0x1A95, 0x1B15, 0x1B55, 0x1B97, 0x1C17, 0x1C5C,
          0x1D41, 0x1DA0, 0x1DC3)
EDGES = ((0x17D2, 0x17DF), (0x1815, 0x182F), (0x1889, 0x197A),
         (0x18E0, 0x193B), (0x192D, 0x193B), (0x196D, 0x197A),
         (0x19E4, 0x19F2), (0x1A34, 0x1A42), (0x1A87, 0x1A95),
         (0x1B07, 0x1B15), (0x1B47, 0x1B55), (0x1B89, 0x1B97),
         (0x1C09, 0x1C17), (0x1C4E, 0x1C5C), (0x1D0D, 0x1D41),
         (0x1D92, 0x1DA0), (0x1DB6, 0x1DC3))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def decode(data: bytes, raw: int, size: int, address: int, arm: bool) -> list:
    engine = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    instructions = list(engine.disasm(data[raw:raw + size], address))
    need(sum(i.size for i in instructions) == size, f"bounded decode at {raw:X}")
    return instructions


def exact_arm(data: bytes, raw: int, expected: list[str]) -> None:
    actual = [f"{i.mnemonic} {i.op_str}".strip()
              for i in decode(data, raw, len(expected) * 4, BASE + raw, True)]
    need(actual == expected, f"native instruction contract at {raw:X}: {actual}")


def convert_color(value: int) -> int:
    need(value < 0x1000, "source RGB444 color")
    expand = lambda c: c * 2 + bool(c)
    return expand(value >> 8) | expand(value >> 4 & 15) << 5 | expand(value & 15) << 10


def convert_tile(data: bytes) -> bytes:
    need(len(data) == 32, "source tile size")
    output = bytearray()
    for y in range(8):
        planes = data[y * 4:y * 4 + 4]
        pixels = [sum(((planes[p] >> (7 - x)) & 1) << p for p in range(4)) for x in range(8)]
        output.extend(pixels[x] | pixels[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(output)


def resource_proof(gba: bytes, old: bytes, source: bytes) -> dict:
    p1, native = 0x3D8750, 0x374824
    need(source[p1:p1 + 32] == old[0x2B6150:0x2B6170], "result P1 commercial ancestor")
    need(struct.unpack_from("<6H", source, p1) == (4, 0, 1, 12, 24, 0), "one result P1 command")
    table, reserved = struct.unpack_from("<2I", gba, native)
    count, payload, a_record, b_record = struct.unpack_from("<4I", gba, table - BASE)
    need((table, reserved, count, payload, a_record, b_record) ==
         (BASE + native + 8, 0, 1, BASE + native + 24, BASE + native + 40, 0),
         "native result P1 pointer population")
    need(gba[payload - BASE:payload - BASE + 16] == source[p1 + 12:p1 + 24] + bytes(4),
         "result command payload exact; FF64 is retained by the commercial port")
    need(gba[a_record - BASE:a_record - BASE + 8] == source[p1 + 24:p1 + 32], "result A record")
    p0, native0 = 0x2DFF20, 0x374854
    table0, desc0, x, y = struct.unpack_from("<4I", gba, native0)
    need((x, y) == struct.unpack_from("<2I", source, p0 + 8), "result P0 constants")
    count0, rel0 = struct.unpack_from("<2H", source, p0 + 16)
    native_count, native_layout = struct.unpack_from("<2I", gba, table0 - BASE)
    need((count0, rel0, native_count) == (44, 20, 44), "one result P0 layout")
    need(source[p0 + rel0:p0 + rel0 + 176] == gba[native_layout - BASE:native_layout - BASE + 176],
         "all result layout records")
    segment, bank = struct.unpack_from("<2H", source, p0 + 4)
    desc = (bank & 127) * 0x10000 + (segment << 4) - 0x20000
    size, offset, segment, bank = struct.unpack_from("<4H", source, desc)
    pixels = (bank & 127) * 0x10000 + (segment << 4) + offset - 0x20000
    native_size, native_pixels = struct.unpack_from("<2I", gba, desc0 - BASE)
    need((desc, size, pixels, native_size) == (0x0EFFE0, 1312, 0x3BE1F0, 1312), "result tile descriptor")
    need(source[desc + 8:desc + 16] == b"\xff" * 8, "one source result descriptor")
    converted = b"".join(convert_tile(source[p:p + 32]) for p in range(pixels, pixels + size, 32))
    need(converted == gba[native_pixels - BASE:native_pixels - BASE + size], "all 41 result tiles")
    p2 = source[0x3D7400:0x3D7426]
    converted2 = p2[:6] + b"".join(struct.pack("<H", convert_color(c)) for c in struct.unpack_from("<16H", p2, 6)) + bytes(2)
    need(converted2 == gba[0x374E44:0x374E6C], "result native P2 inverse")
    return {"p1": BASE + native, "p0": BASE + native0, "p2": 0x08374E44,
            "p1_commands": 1, "p1_items": 1, "p0_layout_bytes": 176,
            "p0_tiles": 41, "p0_tile_bytes": 1312, "p2_colors": 16,
            "p1_duration_word": "FF64 retained exactly, as in the commercial ancestor"}


def proof(gba: bytes, old: bytes, source: bytes) -> dict:
    life = decode(source, SCENE + 0x1750, 0x1E23 - 0x1750, 0x1750, False)
    found = []
    for n, i in enumerate(life):
        if i.mnemonic == "mov" and i.op_str == "word ptr [bx], ax":
            previous = life[n - 1]
            need(previous.mnemonic == "mov" and previous.op_str.startswith("ax, 0x"), "source callback literal")
            found.append((previous.address, int(previous.op_str.split(", ")[1], 0)))
    need(tuple(found) == EDGES, "complete terminal source callback edge population")
    need(source[SCENE + 0x669:SCENE + 0x66F] == bytes.fromhex("9A5017F071CB"), "stage11 terminal dispatch")
    for raw, target in ((0x7601EE, 0x7AB1), (0x7601FA, 0x7D8D)):
        need(source[raw:raw + 9] == bytes.fromhex("C705") + struct.pack("<H", target) + bytes.fromhex("C745029040"),
             "source fatal callback selection")
    need(source[0x760177:0x76018B] == old[0x3A4757:0x3A476B], "commercial damage arithmetic ancestor")
    exact_arm(gba, 0x36E5C8, ["ldr r8, [pc, #0xb8]", "ldrb r0, [r8, #4]", "ldrh r8, [r4, #8]",
        "tst r8, #0x4000", "lsrne r0, r0, #1", "ldrsh r8, [r5, #0x64]", "subs r8, r8, r0",
        "strh r8, [r5, #0x64]", "bgt #0x836e634"])
    exact_arm(gba, 0x36E604, ["mov sb, #0", "strh sb, [r5, #0x76]", "mov r5, r0", "mov sb, #0",
        "strh sb, [r5, #0x76]", "ldr r1, [r5, #0x20]", "mov sb, #1", "strh sb, [r1, #0x94]",
        "ldr r8, [pc, #0x68]", "mov sb, #0", "strh sb, [r8]", "b #0x836e438"])
    need(struct.unpack_from("<I", gba, 0x36E694)[0] == 0x03004D40, "damage scroll reset owner")
    need(struct.unpack_from("<I", gba, 0x36E698)[0] == 0x0834F836, "legacy nonfatal palette pointer")
    need(source[0x768731:0x768754] == old[0x3ADBF7:0x3ADC1A], "commercial player jump ancestor")
    exact_arm(gba, 0x357670, ["stmdb sp!, {lr}", "mov sb, #3", "strb sb, [r4, #0x6e]", "mov sb, #0",
        "strh sb, [r4, #0xa6]", "strh sb, [r4, #0x42]", "strh sb, [r4, #0x44]", "strh sb, [r4, #0x46]",
        "strh sb, [r4, #0x48]", "ldrh r8, [r4, #6]", "orr r8, r8, #1", "strh r8, [r4, #6]"])
    need(source[0x742DCA:0x742DE2] == old[0x392AE2:0x392AFA], "commercial jump argument producer")
    exact_arm(gba, 0x354C24, ["ldr sb, [pc, #0x64]", "strh sb, [r4, #0xa0]", "mov sb, #0x14",
        "strh sb, [r4, #0xa2]", "mov sb, #0xf", "strh sb, [r4, #0xa4]", "mov sb, #1", "strh sb, [r4, #0xa8]"])
    need(struct.unpack_from("<I", gba, 0x354C90)[0] == 0xFFFFFB54, "native jump velocity")
    need(struct.unpack_from("<I", gba, 0x354C94)[0] == 0x08357670, "native jump entry")
    need(source[0x74348F:0x7434AC] == old[0x393064:0x393081], "jump age counter commercial producer")
    need(source[0x76877C:0x768799] == old[0x3ADC42:0x3ADC5F], "jump age threshold commercial consumer")
    exact_arm(gba, 0x352E1C, ["ldrh r8, [r4, #0x2e]", "tst r8, #0x40", "mov sb, #0",
        "strbne sb, [r4, #0x70]", "ldrb r8, [r4, #0x70]", "add r8, r8, #1",
        "strb r8, [r4, #0x70]", "cmp r8, #0x7f", "blo #0x8352e48", "mov sb, #0x7f",
        "strb sb, [r4, #0x70]"])
    exact_arm(gba, 0x3576FC, ["ldrb r8, [r4, #0x70]", "cmp r8, #0x18", "blo #0x8357724"])
    # The retail display pair determines the WS port mapping; hardware BG
    # numbering alone does not. WS 12/13 uses native F5C/F74, WS 10/11 F2C/F44.
    need(old[0x390796:0x3907A1] == bytes.fromhex("268B3EA2068B85BE00E710"), "source scroll port10/11 producer")
    exact_arm(gba, 0xC97FC, ["ldr r8, [pc, #0xf8]", "ldr r5, [r8]", "ldrb r0, [r5, #0xe0]",
        "bl #0x8000f2c", "ldrb r0, [r5, #0xe1]", "bl #0x8000f44"])
    exact_arm(gba, 0xF44, ["ldr r8, [pc, #0x60]", "strb r0, [r8]", "mov sb, #0x4000000",
        "sub sl, r0, #8", "strh sl, [sb, #0x16]", "bx lr"])
    need(struct.unpack_from("<I", gba, 0xFAC)[0] == 0x030012B9, "port11 logical native shadow")
    need(source[0x3F37AE:0x3F37DE] == old[0x2D35C2:0x2D35F2] and
         sha(source[0x3F37AE:0x3F37DE]) == "7FB3E9E59A9482B71C69B377855D1684A611B55092C1E33AE8EB3EE6E3C7BA03",
         "result sound34 commercial payload lineage")
    exact_arm(gba, 0x340B60, ["mov r8, #0xb", "mov sb, #4", "mov sl, #1", "bl #0x80d15c0"])
    # The normal commercial result scene is the native consumer oracle for
    # constructor/event/update/draw/fade/retirement; Shoot reuses those services.
    native_calls = []
    for a, b in ((0x340A8C, 0x340B78), (0x340B98, 0x340BF4), (0x340BF8, 0x340CB0)):
        native_calls.extend((i.address, i.op_str) for i in decode(gba, a, b - a, BASE + a, True) if i.mnemonic == "bl")
    expected_calls = ((0x08340AEC, "#0x80127e4"), (0x08340B04, "#0x8012874"),
                      (0x08340B50, "#0x80132ec"), (0x08340BC8, "#0x8012a84"),
                      (0x08340BD8, "#0x8012c28"), (0x08340C18, "#0x833fdc0"),
                      (0x08340C34, "#0x833ff00"), (0x08340C78, "#0x80d1b0c"),
                      (0x08340C7C, "#0x8012030"))
    need(all(pair in native_calls for pair in expected_calls), "result service consumer population")
    need([struct.unpack_from("<I", gba, p)[0] for p in (0x340B84, 0x340B88, 0x340B8C)] ==
         [0x08374824, 0x08374854, 0x08374E44], "native result resource arguments")
    exact_arm(gba, 0x340C90, ["mov r8, #1", "strh r8, [sb, #4]", "mov r8, #0", "strh r8, [sb, #6]",
        "mov r8, #0", "strh r8, [sb, #8]"])
    need(struct.unpack_from("<I", gba, 0x340CBC)[0] == 0x03002310, "native mode owner")
    return {"source_phases": PHASES, "source_edges": EDGES, "source_phase_instructions": len(life),
            "unused_source_phase": "18EE has no edge from the decoded terminal graph; retained for audit",
            "native_result_resources": resource_proof(gba, old, source),
            "native_services": expected_calls,
            "jump_age": "same incrementing/saturating byte5C->70; commercial threshold30->24 supports source20->native16",
            "scroll_port11": {"commercial_source": "390796..3907A0", "native_calls": "080C97FC..080C9810",
                "native_shadow": 0x030012B9, "hardware_write": "F44 subtracts8 only at BG1VOFS; shadow remains logical"},
            "result_sound": {"source_id": 0x34, "native_id": 0x0B, "type": 4, "shoot_delay": 0,
                "commercial_request_delay": 1, "proof": "exact48-byte payload plus same result-request/presentation consumer"},
            "same_update_edges": [[0x1750, 0x17DF], [0x1DA0, 0x1DC3]],
            "upper_same_update_repairs": [[0x7AB1, 0x7B1B], [0x7BFF, 0x7C64], [0x7C64, 0x7CE5], [0x7D8D, 0x7DA9]],
            "terminal_handshake": {"upper_sets": [0x100], "scene_clears": [0x100],
                "scene_sets": [0x80, 0x20, 0x1000, 0x200, 0x2000], "stage_transition_must_supply": [0x100]},
            "mode_exit": {"native_entry": 0x08340C54, "global": 0x03002310, "writes": [[4, 1], [6, 0], [8, 0]],
                "task_retirement": 0x08012030, "source": "71F0:1DC3..1E22"},
            "reward_scope": "existing source result presentation and parent-mode handoff; no source score/unlock/currency write is invented",
            "remaining_integration_contracts": ["terminal scene runs under existing exclusive FF0 task ownership",
                "stage transition 0E0B/0D87/0DEC ABI is independently required",
                "197A camera-Y live-in and mapped tilemap destination require owner/range proof",
                "root case5 stage11 selects this terminal entry only after all prerequisites"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    paths = (args.gba, args.wsc10, args.wsc15)
    need(all(p.suffix.lower() != ".sav" for p in paths), "save files are forbidden")
    data = tuple(p.read_bytes() for p in paths)
    need(tuple(map(sha, data)) == HASHES, "terminal source identities")
    report = {"schema": 1, "kind": "shoot-terminal-commercial-proof", "rom_sha256": HASHES, **proof(*data)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[shoot-terminal-proof] source graph and native consumer proof PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
