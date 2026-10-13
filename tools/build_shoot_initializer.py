#!/usr/bin/env python3
"""Install bounded Shoot initializer and downstream presentation components.

This layer deliberately has no outer initializer or caller.  ES=1000:3CD8/DA,
and the display/IRQ scene contract remain unresolved.  Native
presentation resources replace source P0 preloads through the existing native
draw consumer; this does not create fixed-VRAM copies or a new renderer.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct

from build_shoot_player_binding import (
    GBA_SHA256, WSC10_SHA256, WSC15_SHA256, assemble, require_hash, sha256,
    verify_machine_code,
)
from convert_wsc_palette_block import convert_block

INPUT_SHA256 = "2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE"
BASE = 0x08000000
GRAPHICS, STAGE_MANAGER, CLEAR_0660 = 0x5C4000, 0x5C4300, 0x5C4400
RESOURCE_93E7, RESOURCE_888B = 0x5C4500, 0x5C4600
P1_93E7, P1_888B, P2_93E7 = 0x5C4800, 0x5C4C00, 0x5C5000
OWNERSHIP_START, OWNERSHIP_END = 0x5C4000, 0x5C6000

ORACLES = (
    ("wsc15", 0x747A68, 0x747E72, "F0F825AE96C188F14EA8ED89A78C18D9F5D752EAD123FE2C02FD0056AB51B8C3", "source initializer"),
    ("wsc15", 0x743FC0, 0x7440C7, "A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6", "source stage manager"),
    ("wsc15", 0x77DCB4, 0x77DE62, "F43D8674B2C9CC396250727CD2987FBBC0E5015348839F1771234F0D80A3D2E4", "source graphics helper"),
    ("gba", 0x3EE08, 0x3F034, "7672CC503F4A09672C555703D060CFAF6F63FE1CEA8E9B19D37FE96E1FADA6A3", "native graphics control flow"),
    ("gba", 0x36D224, 0x36D388, "FC18BF11FAA9D02079C935C55E54D4E943DB3C6ECCE8DE8822AFB230E8E635A3", "native stage manager"),
    ("gba", 0x127E4, 0x1285C, "EF628791EF3580DEAD14EEC7400E44A43A696EF8012D62304FD0C7B6A45FD0C2", "native presentation constructor"),
    ("gba", 0x12C28, 0x12DB8, "666847891A381AE5916738395631C3067445A9D51410D8742C8E4ADFD23854AF", "native dynamic draw consumer"),
    ("gba", 0x7FBF8, 0x7FC30, "D40A0A4ECA87948D305AE011F1ED37C469AC34E995937E2FC227459A297F2510", "native BG map clear"),
    ("gba", 0x15D38, 0x15D78, "39A8B7A3E5E1E63A8AE3AA44F11721C2028BA2ED774B4E905572F8970CE70C5C", "native object staging reset"),
    ("gba", 0x1369C, 0x136F0, "A1436B6A7F40C6019E0A27B4A3A636C8819D05E5B0391914FA85FF2DA9236026", "native BG staging reset"),
    ("wsc15", 0x740C73, 0x740CB3, "EE2E4E79E4C547419CFA1C2B2795B9EE91BF403F1AE26D67986F83F460057F00", "source native-lineage global timer producer"),
    ("wsc10", 0x390A33, 0x390A73, "0334FF449070DBFEBF0EBA3345F79F0819B6939E5B4164496DAE70EB5810BED9", "commercial source global timer producer"),
    ("gba", 0xD17F8, 0xD18A0, "72A2447F55763B6E59941E06367CD144770746BA2D13DA2258378D94C89F5FD9", "native timer constants and 03004500 destination"),
    ("gba", 0x37500C, 0x37501C, "663FDF6FFEA987EDCE05F57FDA219DE50060117AC914211743440440401A03D0", "native timer decrement"),
    ("gba", 0x373D34, 0x373D4C, "BE55AEF0CD7A8CDCD3BC3C814CCBA58C51AA1EFF1565CB04FD400C037A53DB6E", "native timer HUD division"),
    ("wsc15", 0x7432E4, 0x74333C, "9FF8BCECB7293927D6AA8ADB00E4A29A12A9479CC04B3E3CA691FE9A512F3E32", "source 0660 producer with distinct ES0C00 globals"),
    ("gba", 0x352B30, 0x352B78, "7CC58F0AF079D6E2FCE39FC28C8E73B57C814E8128F7B9CD80D05A43772D651E", "native 0660 producer lineage"),
    ("gba", 0x352DC4, 0x352DEC, "D2A8EB8F055D1064E1C9138CF0ACB4A842587B12AED628CDB453360974CBAA65", "native 030048A4 indexed shift consumer"),
    ("gba", 0x355EE8, 0x355F0C, "0AD127BA53BC4A60F400DF2739B01D684F0ABB2137C9DB1F5CFEB2B1FEDF7831", "native 030048A4 indexed flag consumer"),
)
PREREQUISITES = (
    (0xD1C78, 4, "B64EC4BAE12E3973B5886FF21A0F40EA0F2749C97ADC8A3C9EAC47AA1E60D320", "v50 stage selector branch"),
    (0x582C40, 0x38, "EDC7EA0D1CBBB0D76547636A2D3F5E22E4A454181B5F40EB92196CEA76A62EEB", "v50 stage selector"),
    (0x584C00, 0x60, "17DDA5211D60EF553341981E26447E93E02C6A145307DD255371BD277B151F75", "twelve-stage object configuration"),
    (0x584D40, 0x10, "C6277C1ED496B87BF065ECC872163E4ECDD65B2F48AA54B328CE4FF32637D441", "expanded stage configuration hook"),
    (0x582A00, 0x180, "59E534C9B012E911AE97C0295AF1E909793DCF3CFD5509857672D01EA722C1E6", "resident Shoot graphics clone"),
    (0x5DB300, 16, "9E7B9E52D871E2740A1621015196531A7A1812D6DD712143E355EC77CC3F8A83", "93E7 P0"),
    (0x5DB400, 16, "F343F725C771B3D8F8DF92CC1A5BBC0F2A0693767D966AA112470F34258D41F2", "888B P0"),
    (0x5DB740, 40, "B5652748382A44ADDEB2BB191FFA880D46D6721CEA54CACF15D7B0C51729A4A1", "888B P2"),
)
P1_SPECS = (
    ("93E7", 0x3D23B0, 0x108, (15,), P1_93E7),
    ("888B", 0x0DFEC0, 0x126, (6, 8, 6), P1_888B),
)


def parse_p1(source: bytes, raw: int, size: int) -> dict:
    """Read direct source commands, including the one-command population."""
    data = source[raw:raw + size]
    if len(data) != size or struct.unpack_from("<2H", data) != (4, 0):
        raise ValueError("unsupported source P1 header")
    first_payload = struct.unpack_from("<H", data, 6)[0]
    if first_payload < 12 or (first_payload - 4) % 8:
        raise ValueError("source P1 command table is not self-delimiting")
    commands = [struct.unpack_from("<4H", data, 4 + k * 8)
                for k in range((first_payload - 4) // 8)]
    a_refs, b_refs = set(), set()
    payloads = []
    for count, relative, a_ref, b_ref in commands:
        if not count or relative < first_payload or relative + count * 12 > size:
            raise ValueError("source P1 payload escapes container")
        if not a_ref or a_ref + 8 > size:
            raise ValueError("source P1 A record escapes container")
        a_refs.add(a_ref)
        if b_ref:
            b_refs.add(b_ref)
        items = [struct.unpack_from("<6H", data, relative + j * 12) for j in range(count)]
        b_refs.update(item[5] for item in items if item[5])
        payloads.append(items)
    if any(relative + 10 > size for relative in b_refs):
        raise ValueError("source P1 ten-byte record escapes container")
    return {"data": data, "commands": commands, "payloads": payloads,
            "a_refs": sorted(a_refs), "b_refs": sorted(b_refs)}


def convert_p1(parsed: dict, target: int) -> bytes:
    """Relocate every P1 reference, including per-item ten-byte records.

    The old converter's 0835032C+word5 formula names its one retail container.
    Reusing that constant for these resources would silently bind wrong data.
    """
    cursor = 8 + len(parsed["commands"]) * 16
    payload_locations = []
    for payload in parsed["payloads"]:
        payload_locations.append(cursor)
        cursor += len(payload) * 16
    a_locations = {}
    for relative in parsed["a_refs"]:
        a_locations[relative] = cursor
        cursor += 8
    b_locations = {}
    for relative in parsed["b_refs"]:
        b_locations[relative] = cursor
        cursor += 10
    result = bytearray((cursor + 3) & ~3)
    pointer = BASE + target
    struct.pack_into("<2I", result, 0, pointer + 8, 0)
    for index, ((count, _, a_ref, b_ref), payload) in enumerate(zip(parsed["commands"], parsed["payloads"], strict=True)):
        struct.pack_into("<4I", result, 8 + index * 16, count,
                         pointer + payload_locations[index], pointer + a_locations[a_ref],
                         pointer + b_locations[b_ref] if b_ref else 0)
        for j, item in enumerate(payload):
            words = list(item)
            if words[0] & 0xFF00 == 0xFF00:
                words[0] = 0xFF00 | (((words[0] & 0xFF) * 4 + 2) // 5)
            tail = pointer + b_locations[words[5]] if words[5] else 0
            words[5] = 0
            struct.pack_into("<6HI", result, payload_locations[index] + j * 16, *words, tail)
    for relative, local in a_locations.items():
        result[local:local + 8] = parsed["data"][relative:relative + 8]
    for relative, local in b_locations.items():
        result[local:local + 10] = parsed["data"][relative:relative + 10]
    return bytes(result)


def prove_per_item_oracle(gba: bytes, wsc10: bytes) -> dict:
    """Read actual commercial native tail pointers and compare their targets."""
    source, native = 0x2AE180, 0x350248
    parsed = parse_p1(wsc10, source, 0x300)
    unique = set()
    checks = 0
    for k, items in enumerate(parsed["payloads"]):
        count, payload, _, _ = struct.unpack_from("<4I", gba, native + 8 + k * 16)
        if count != len(items):
            raise ValueError("commercial P1 payload population changed")
        for j, item in enumerate(items):
            if not item[5]:
                continue
            native_tail = struct.unpack_from("<I", gba, payload - BASE + j * 16 + 12)[0] - BASE
            source_tail = source + item[5]
            if gba[native_tail:native_tail + 10] != wsc10[source_tail:source_tail + 10]:
                raise ValueError("commercial per-item ten-byte record is not identical")
            unique.add((source_tail, native_tail))
            checks += 1
    if len(unique) != 11:
        raise ValueError("commercial per-item record population changed")
    return {"references": checks, "unique_records": len(unique),
            "source_native_pairs": sorted(unique), "record_bytes": 10}


def graphics_subset() -> tuple[bytes, int]:
    """Only the proved native common resets and resident stage resource clone.

    Callers must already own the scene, disable conflicting display/IRQ work,
    and arrange actual stage/dimension/HUD globals.  This is not all of 0FC4.
    """
    blob = assemble("""
        push {r0-r12, lr}
        mov r11, #0
        bl 0x0807FBF8
        ldr r8, shadow
        add r9, r8, #1
        ldr r5, bg0
        str r8, [r5]
        str r9, [r5, #4]
        ldr r5, bg1
        str r8, [r5]
        str r9, [r5, #4]
        ldr r5, bg2
        str r8, [r5]
        str r9, [r5, #4]
        ldr r5, bg3
        str r8, [r5]
        str r9, [r5, #4]
        bl 0x08000CD8
        and r0, r0, #0xFF
        strh r0, [r8]
        bl 0x08015D38
        bl 0x0801369C
        bl 0x08582A00
        pop {r0-r12, lr}
        bx lr
    shadow: .word 0x030012B8
    bg0: .word 0x03002338
    bg1: .word 0x03002388
    bg2: .word 0x030023D8
    bg3: .word 0x03002428
    """, GRAPHICS)
    return blob, len(blob) - 20


def stage_manager_subset() -> tuple[bytes, int]:
    """Source stage11 plus 71A4..71C7 using commercial timer conversion."""
    blob = assemble("""
        push {r0-r12, lr}
        mov r11, #0
        ldr r8, stage
        mov r9, #11
        strb r9, [r8]
        ldr r8, timer
        mov r9, #0x3840
        strh r9, [r8]
        ldr r8, flags
        mov r9, #0
        strh r9, [r8]
        strh r9, [r8, #2]
        strh r9, [r8, #4]
        mov r9, #0x10
        strh r9, [r8]
        bl 0x0836D224
        pop {r0-r12, lr}
        bx lr
    stage: .word 0x0300231E
    timer: .word 0x03004500
    flags: .word 0x03004506
    """, STAGE_MANAGER)
    return blob, len(blob) - 12


def clear_0660() -> tuple[bytes, int]:
    blob = assemble("""
        push {r0-r12, lr}
        ldr r8, slot
        mov r9, #0
        strh r9, [r8]
        pop {r0-r12, lr}
        bx lr
    slot: .word 0x030048A4
    """, CLEAR_0660)
    return blob, len(blob) - 4


def resource_adapter(entry: int, p1: int, p0: int, p2: int, tile: int) -> tuple[bytes, int]:
    """r5 is an existing valid native presentation; all registers preserved.

    Exactly the source's 15 constructor arguments are passed.  This does not
    allocate an object, select its first event, or install a callback.
    """
    blob = assemble(f"""
        push {{r0-r12, lr}}
        push {{r5}}
        mov r8, #0
        push {{r8}}
        ldr r8, p1
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, p0
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        ldr r8, p2
        push {{r8}}
        mov r8, #0
        push {{r8}}
        push {{r8}}
        mov r8, #0x4000
        push {{r8}}
        mov r8, #0x1800
        push {{r8}}
        ldr r8, tile
        push {{r8}}
        mov r8, #5
        push {{r8}}
        bl 0x080127E4
        add sp, sp, #60
        pop {{r0-r12, lr}}
        bx lr
    p1: .word 0x{BASE + p1:08X}
    p0: .word 0x{p0:08X}
    p2: .word 0x{p2:08X}
    tile: .word 0x{tile:X}
    """, entry)
    return blob, len(blob) - 16


def build(original: bytes, sources: dict[str, bytes]) -> tuple[bytes, dict]:
    require_hash(original, INPUT_SHA256, "exact palette predecessor")
    for key, expected in (("gba", GBA_SHA256), ("wsc10", WSC10_SHA256), ("wsc15", WSC15_SHA256)):
        require_hash(sources[key], expected, key)
    for key, start, end, expected, label in ORACLES:
        require_hash(sources[key][start:end], expected, label)
    for start, size, expected, label in PREREQUISITES:
        require_hash(original[start:start + size], expected, label)
    # The v50 stage manager must retain its expanded table routing.  Its native
    # code outside those already documented branch sites must be unchanged.
    for start, end in ((0x36D224, 0x36D2C0), (0x36D2C4, 0x36D388),
                       (0x127E4, 0x1285C), (0x12C28, 0x12DB8), (0x7FBF8, 0x7FC30),
                       (0x15D38, 0x15D78), (0x1369C, 0x136F0), (0xD1C7C, 0xD1C88)):
        if original[start:end] != sources["gba"][start:end]:
            raise ValueError(f"native dependency changed at {start:X}")
    if struct.unpack_from("<I", original, 0x36D2C0)[0] != 0xEA085E9E:
        raise ValueError("expanded stage manager branch changed")
    if len(original) != 0x800000 or original[OWNERSHIP_START:OWNERSHIP_END] != b"\xFF" * (OWNERSHIP_END - OWNERSHIP_START):
        raise ValueError("initializer ownership window is not unused expansion")
    oracle = prove_per_item_oracle(sources["gba"], sources["wsc10"])
    rows, machine_code = [], {}
    for entry, (blob, code_bytes), following, label, externals in (
        (GRAPHICS, graphics_subset(), STAGE_MANAGER, "graphics_subset", {0x0807FBF8, 0x08000CD8, 0x08015D38, 0x0801369C, 0x08582A00}),
        (STAGE_MANAGER, stage_manager_subset(), CLEAR_0660, "stage_manager_subset", {0x0836D224}),
        (CLEAR_0660, clear_0660(), RESOURCE_93E7, "clear_0660_only", set()),
        (RESOURCE_93E7, resource_adapter(RESOURCE_93E7, P1_93E7, 0x085DB300, BASE + P2_93E7, 0x6D), RESOURCE_888B, "93E7_constructor_resources", {0x080127E4}),
        (RESOURCE_888B, resource_adapter(RESOURCE_888B, P1_888B, 0x085DB400, 0x085DB740, 0x137), P1_93E7, "888B_constructor_resources", {0x080127E4}),
    ):
        if entry + len(blob) > following:
            raise ValueError(f"initializer placement overflow: {label}")
        machine_code[label] = verify_machine_code(blob, entry, code_bytes, externals)
        rows.append((entry, blob, label))
    resources = []
    for label, raw, size, counts, target in P1_SPECS:
        parsed = parse_p1(sources["wsc15"], raw, size)
        if tuple(command[0] for command in parsed["commands"]) != counts:
            raise ValueError("source P1 command population changed")
        blob = convert_p1(parsed, target)
        if len(blob) > 0x400:
            raise ValueError("P1 resource exceeds reserved slot")
        rows.append((target, blob, f"{label}_relocated_P1"))
        resources.append({"label": label, "source": raw, "source_bytes": size,
                          "source_sha256": sha256(parsed["data"]), "target": target,
                          "bytes": len(blob), "sha256": sha256(blob), "counts": counts,
                          "a_relatives": parsed["a_refs"], "ten_byte_relatives": parsed["b_refs"]})
    rows.append((P2_93E7, convert_block(sources["wsc15"][0x3D7AC0:0x3D7AE6]), "93E7_P2"))
    plan = []
    allowed = set()
    for start, after, label in rows:
        before = b"\xFF" * len(after)
        if not OWNERSHIP_START <= start < start + len(after) <= OWNERSHIP_END or original[start:start + len(after)] != before:
            raise ValueError(f"Expected Write failed: {label}")
        touched = set(range(start, start + len(after)))
        if touched & allowed:
            raise ValueError("overlapping Expected Writes")
        allowed |= touched
        plan.append((start, before, after, label))
    untouched_gap_candidates = []
    for site in range(0, len(original) - 3, 4):
        word = struct.unpack_from("<I", original, site)[0]
        if word - BASE in allowed:
            raise ValueError(f"preexisting pointer into installed initializer bytes at {site:X}")
        if word & 0x0E000000 == 0x0A000000:
            displacement = word & 0xFFFFFF
            if displacement & 0x800000:
                displacement -= 0x1000000
            target = site + 8 + displacement * 4
            if target in allowed:
                raise ValueError(f"preexisting ARM branch into installed initializer bytes at {site:X}")
            if OWNERSHIP_START <= target < OWNERSHIP_END:
                untouched_gap_candidates.append({"site": site, "target": target})
    result = bytearray(original)
    for start, _, after, _ in plan:
        result[start:start + len(after)] = after
    changed = {i for i, (a, b) in enumerate(zip(original, result, strict=True)) if a != b}
    expected = {start + i for start, before, after, _ in plan for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    if changed != expected or not changed <= allowed:
        raise ValueError("final diff differs from Expected Writes")
    manifest = {
        "schema": 1, "kind": "shoot-initializer-resident-components",
        "input_sha256": INPUT_SHA256, "output_sha256": sha256(result), "output_bytes": len(result),
        "native_entries": {"graphics_subset": BASE + GRAPHICS, "stage_manager_subset": BASE + STAGE_MANAGER,
                           "clear_0660_only": BASE + CLEAR_0660, "resource_93E7": BASE + RESOURCE_93E7,
                           "resource_888B": BASE + RESOURCE_888B},
        "abi": {"preserved": "r0-r12, lr, sp", "flags": "clobbered", "resource_adapters_input": "r5=existing valid native presentation",
                "graphics_subset_requires": "exclusive scene ownership, safe display/IRQ state, stage11/dimension/HUD globals supplied by caller",
                "stage_manager_requires": "native selector must resolve stage11; battle+0A must not trigger existing 0B/0D/0E overrides",
                "all_entries_have_no_callers": True},
        "commercial_per_item_oracle": oracle, "p1_resources": resources,
        "generated_code": machine_code, "actual_changed_bytes": len(changed),
        "branch_like_targets_left_as_untouched_FF": untouched_gap_candidates,
        "expected_writes": [{"offset": start, "bytes": len(after), "label": label,
                             "before_sha256": sha256(before), "after_sha256": sha256(after)} for start, before, after, label in plan],
        "timer_translation": {"source_global": "1000:03CE", "source_frames": 18000,
                              "native_global": 0x03004500, "native_frames": 14400,
                              "proof": "commercial 6750/9000/13500 -> 5400/7200/10800 and 18000 -> 14400 producer lineage"},
        "unresolved": ["7168 display/IRQ preamble", "remaining 7CCF:0FC4 HUD/display operations",
                       "ES1000:3CD8/3CDA distinct from ES0C00 fighter globals", "entry lifetime across scene transition", "full 93E7/888B callbacks"],
        "claim_scope": "resident proved subsets and constructor resources only; no complete initializer, palette orchestration, menu/controller hook, emulator or save QA",
    }
    return bytes(result), manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()
    sources = {key: getattr(args, key).read_bytes() for key in ("gba", "wsc10", "wsc15")}
    output, manifest = build(args.input.read_bytes(), sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-initializer] static build {manifest['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
