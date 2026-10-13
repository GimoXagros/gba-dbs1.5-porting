#!/usr/bin/env python3
"""Independently read Shoot initializer resources and their native consumers.

No builder/converter is imported.  This checks the file representation and
straight-line constructor argument setup; it never executes a game or opens
a save.  Lifetime and segment findings are reported with their limitations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vendor"))
from capstone import CS_ARCH_ARM, CS_MODE_ARM, Cs  # type: ignore
from capstone.arm_const import ARM_OP_IMM, ARM_OP_MEM  # type: ignore

BASE = 0x08000000
HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
RESOURCE_ROWS = (
    ("93E7", 0x3D23B0, 0x3D24B8, 0x5C4800, 0x5C494C, (15,), 0x5C4500, 0x085DB300, 0x085C5000, 0x6D),
    ("888B", 0x0DFEC0, 0x0DFFE6, 0x5C4C00, 0x5C4D94, (6, 8, 6), 0x5C4600, 0x085DB400, 0x085DB740, 0x137),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def demand(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_commands(source: bytes, begin: int, end: int) -> list[dict]:
    """Read the compact command stream through its leading payload boundary."""
    table = begin + struct.unpack_from("<H", source, begin)[0]
    demand(table == begin + 4 and source[begin + 2:begin + 4] == bytes(2), "WSC P1 header")
    stop = begin + struct.unpack_from("<H", source, table + 2)[0]
    demand(table < stop <= end and (stop - table) % 8 == 0, "WSC P1 table boundary")
    result = []
    while table < stop:
        count, payload, a_ref, b_ref = struct.unpack_from("<4H", source, table)
        demand(count > 0 and stop <= begin + payload <= end - count * 12, "WSC payload range")
        demand(stop <= begin + a_ref <= end - 8, "WSC A range")
        demand(not b_ref or stop <= begin + b_ref <= end - 10, "WSC B range")
        words = [struct.unpack_from("<6H", source, begin + payload + j * 12) for j in range(count)]
        for item in words:
            demand(not item[5] or stop <= begin + item[5] <= end - 10, "WSC per-item range")
        result.append({"count": count, "words": words, "a": begin + a_ref,
                       "b": begin + b_ref if b_ref else None, "begin": begin})
        table += 8
    return result


def native_commands(rom: bytes, begin: int, end: int) -> list[dict]:
    table_pointer, flags = struct.unpack_from("<2I", rom, begin)
    demand(table_pointer == BASE + begin + 8 and flags == 0, "native P1 header")
    table = table_pointer - BASE
    stop = struct.unpack_from("<I", rom, table + 4)[0] - BASE
    demand(table < stop <= end and (stop - table) % 16 == 0, "native P1 command extent")
    result = []
    while table < stop:
        count, payload, a_ref, b_ref = struct.unpack_from("<4I", rom, table)
        payload, a_ref = payload - BASE, a_ref - BASE
        b_ref = b_ref - BASE if b_ref else None
        demand(count > 0 and stop <= payload <= end - count * 16, "native payload range")
        demand(stop <= a_ref <= end - 8, "native A pointer escapes owned P1")
        demand(b_ref is None or stop <= b_ref <= end - 10, "native B pointer escapes owned P1")
        items = [struct.unpack_from("<6HI", rom, payload + j * 16) for j in range(count)]
        for item in items:
            demand(not item[6] or stop <= item[6] - BASE <= end - 10, "native tail pointer escapes owned P1")
        result.append({"count": count, "items": items, "a": a_ref, "b": b_ref,
                       "payload": payload, "row": table})
        table += 16
    return result


def compare_p1(source: bytes, rom: bytes, row: tuple) -> dict:
    label, source_start, source_end, start, end, counts, *_ = row
    src = source_commands(source, source_start, source_end)
    dst = native_commands(rom, start, end)
    demand(tuple(x["count"] for x in src) == counts == tuple(x["count"] for x in dst), "P1 command populations")
    nonzero_tails = 0
    record_pairs = set()
    tail_sites = []
    for s, d in zip(src, dst, strict=True):
        demand(source[s["a"]:s["a"] + 8] == rom[d["a"]:d["a"] + 8], "P1 A identity")
        demand((s["b"] is None) == (d["b"] is None), "P1 B nullness")
        if s["b"] is not None:
            demand(source[s["b"]:s["b"] + 10] == rom[d["b"]:d["b"] + 10], "P1 B identity")
        for j, (before, after) in enumerate(zip(s["words"], d["items"], strict=True)):
            # Commercial WSC75Hz/native60Hz marker conversion, separately read
            # from generator logic.  Other source words 1..4 retain identity.
            duration = before[0]
            if duration >= 0xFF00:
                duration = 0xFF00 + (4 * (duration % 256) + 2) // 5
            demand(after[0] == duration and after[1:5] == before[1:5] and after[5] == 0, "P1 payload identity/conversion")
            demand(bool(before[5]) == bool(after[6]), "P1 tail nullness")
            if before[5]:
                sa, na = source_start + before[5], after[6] - BASE
                demand(source[sa:sa + 10] == rom[na:na + 10], "P1 per-item record identity")
                record_pairs.add((sa, na))
                nonzero_tails += 1
                tail_sites.append(d["payload"] + j * 16 + 12)
    return {"label": label, "source": source_start, "target": start, "bytes": end - start,
            "sha256": digest(rom[start:end]), "commands": len(src), "payload_items": sum(counts),
            "nonzero_tail_references": nonzero_tails, "unique_tail_records": len(record_pairs),
            "source_native_record_pairs": sorted(record_pairs), "tail_sites": tail_sites}


def decode(rom: bytes, start: int, length: int):
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    engine.detail = True
    instructions = list(engine.disasm(rom[start:start + length], BASE + start))
    demand(sum(i.size for i in instructions) == length, "ARM code not completely decoded")
    return instructions


def constructor_arguments(rom: bytes, row: tuple) -> dict:
    label, _, _, p1, _, _, start, p0, p2, tile = row
    # This is a static reconstruction of the one straight-line stack setup;
    # native calls and RAM stores are never executed.
    instructions = decode(rom, start, 124)
    demand(int.from_bytes(instructions[0].bytes, "little") == 0xE92D5FFF, "constructor must preserve r0-r12/LR")
    pushed = []
    register8 = None
    calls = []
    for ins in instructions[1:]:
        word = int.from_bytes(ins.bytes, "little")
        if word == 0xE52D5004:
            pushed.append("presentation")
        elif word == 0xE52D8004:
            demand(register8 is not None, "unknown constructor argument")
            pushed.append(register8)
        elif ins.mnemonic == "mov" and ins.reg_name(ins.operands[0].reg) == "r8":
            demand(ins.operands[1].type == ARM_OP_IMM, "nonconstant constructor argument")
            register8 = ins.operands[1].imm
        elif ins.mnemonic == "ldr" and ins.reg_name(ins.operands[0].reg) == "r8":
            memory = ins.operands[1]
            demand(memory.type == ARM_OP_MEM and ins.reg_name(memory.mem.base) == "pc", "constructor nonliteral read")
            address = ins.address + 8 + memory.mem.disp - BASE
            demand(start + 124 <= address <= start + 136, "constructor literal bound")
            register8 = struct.unpack_from("<I", rom, address)[0]
        elif ins.mnemonic == "bl":
            calls.append(ins.operands[0].imm)
    demand(calls == [0x080127E4], "constructor call target")
    expected = ["presentation", 0, BASE + p1, 0, 0, p0, 0, 0, p2, 0, 0, 0x4000, 0x1800, tile, 5]
    demand(pushed == expected, f"{label} constructor resource/stack order")
    demand([int.from_bytes(i.bytes, "little") for i in instructions[-3:]] == [0xE28DD03C, 0xE8BD5FFF, 0xE12FFF1E], "constructor stack/register return")
    p0_raw = p0 - BASE
    layout, descriptor, shift, _, _, flags = struct.unpack_from("<2I4H", rom, p0_raw)
    demand(shift == 5 and flags == 8, "P0 native dynamic draw flags")
    demand(0x085F0000 <= descriptor < 0x08600000 and BASE <= layout < BASE + len(rom), "P0 resident descriptor/layout pointers")
    return {"label": label, "entry": BASE + start, "entry_sp_arguments": list(reversed(expected)),
            "p1_field": "+44", "p0_field": "+48", "p2_field": "+4C", "tile_field": "+14",
            "palette_field": "+10", "native_p0_flags": flags, "dynamic_renderer_entry": 0x03000204,
            "fixed_vram_preload_emitted": False}


def commercial_tail_oracle(gba: bytes, old: bytes) -> dict:
    # Retail tails may reside outside the main P1 byte range; read their actual
    # pointer values and compare bounded ROM bytes, without a relocation formula.
    src = source_commands(old, 0x2AE180, 0x2AE480)
    unique, references = set(), 0
    for k, command in enumerate(src):
        count, pointer = struct.unpack_from("<2I", gba, 0x350250 + k * 16)
        demand(count == command["count"], "retail command population")
        for j, words in enumerate(command["words"]):
            if words[5]:
                tail = struct.unpack_from("<I", gba, pointer - BASE + j * 16 + 12)[0] - BASE
                before = 0x2AE180 + words[5]
                demand(0 <= tail <= len(gba) - 10, "retail tail range")
                demand(old[before:before + 10] == gba[tail:tail + 10], "retail tail identity")
                unique.add((before, tail))
                references += 1
    demand(len(unique) == 11, "retail unique tail population")
    return {"references": references, "unique_records": 11, "pairs": sorted(unique)}


def timer_proof(gba: bytes, old: bytes, source: bytes, candidate: bytes) -> dict:
    # The source producer lineage differs only in five absolute globals.
    old_producer = old[0x390A33:0x390A73]
    new_producer = bytearray(source[0x740C73:0x740CB3])
    for current, previous in ((0x03CE, 0x0354), (0x03D0, 0x0356), (0x03D2, 0x0358), (0x03D4, 0x035A), (0x03D6, 0x035C)):
        new_producer = new_producer.replace(struct.pack("<H", current), struct.pack("<H", previous))
    demand(bytes(new_producer) == old_producer, "three-way timer producer lineage")
    demand(struct.unpack_from("<3I", gba, 0xD1894) == (5400, 7200, 10800), "native timer choice constants")
    demand(source[0x747AA4:0x747AAA] == bytes.fromhex("c706ce035046"), "Shoot source timer store")
    demand(old[0x39FEAC:0x39FEB2] == bytes.fromhex("a15403b94b00"), "commercial source timer HUD first divide")
    demand(source[0x7875AC:0x7875B2] == bytes.fromhex("a1ce03b94b00"), "Shoot-lineage source timer HUD first divide")
    emitted = decode(candidate, 0x5C4300, 72)
    listing = [f"{i.mnemonic} {i.op_str}" for i in emitted]
    demand("mov sb, #0x3840" in listing, "initializer native 14400 frame timer")
    demand(struct.unpack_from("<3I", candidate, 0x5C4348) == (0x0300231E, 0x03004500, 0x03004506), "initializer stage/timer/flag literal consumers")
    return {"wsc_frames": 18000, "native_frames": 14400, "source_hud_first_divisor": 75,
            "native_hud_first_divisor": 60, "native_global": 0x03004500,
            "native_choice_constants": [5400, 7200, 10800], "producer_lineage_exact_after_global_relocation": True}


def globals_and_segments(gba: bytes, source: bytes, candidate: bytes) -> dict:
    demand(source[0x7432F8:0x743304] == bytes.fromhex("c70660060000c70664060000"), "source 0660/0664 producer")
    demand(source[0x7432ED:0x7432F2] == bytes.fromhex("b8000c8ec0"), "fighter producer ES0C00 segment")
    demand(source[0x747CD6:0x747CF0] == bytes.fromhex("b800108ec026c7066006000026c706d83c000026c706da3c0000"), "Shoot ES1000 segment and three clears")
    # Two independent consumers use character*4 on the same base.  One shifts
    # both halfwords; the other selects +0/+2 from a source object flag.
    demand(source[0x743465:0x743470] == bytes.fromhex("8a4410c1e002bb600603d8"), "source first indexed 0660 consumer")
    demand(source[0x766ED4:0x766EDF] == bytes.fromhex("8a4410c1e002bb600603d8"), "source second indexed 0660 consumer")
    native_sites = (0x352B44, 0x352DCC, 0x355EF0)
    native_pointers = []
    for site in native_sites:
        word = struct.unpack_from("<I", gba, site)[0]
        demand(word & 0x0FFF0000 == 0x059F0000, "native 0660 consumer literal load")
        native_pointers.append(struct.unpack_from("<I", gba, site + 8 + (word & 0xFFF))[0])
    demand(native_pointers == [0x030048A4] * 3, "0660 producer and two consumers disagree")
    demand(struct.unpack_from("<I", candidate, 0x5C4418)[0] == 0x030048A4, "resident 0660 clear literal")
    hits = {}
    for name, pattern in (("3CD8_operands", b"\xD8\x3C"), ("3CDA_operands", b"\xDA\x3C"), ("C1_out_byte_patterns", b"\xE6\xC1")):
        found, cursor = [], 0x700000
        while True:
            cursor = source.find(pattern, cursor, 0x800000)
            if cursor < 0:
                break
            found.append(cursor)
            cursor += len(pattern)
        hits[name] = found
    demand(source[0x7638F6:0x7638FB] == bytes.fromhex("e4c18946fe"), "source C1 save")
    demand(source[0x76391F:0x763923] == bytes.fromhex("b0ffe6c1"), "source C1 FF selection")
    demand(source[0x763975:0x76397A] == bytes.fromhex("8b46fee6c1"), "source C1 restoration")
    return {"0660_native_global": 0x030048A4, "native_consumer_sites": native_sites,
            "source_clear_segments": {"Shoot": 0x1000, "fighter_hp": 0x0C00},
            "source_linear_addresses_3CD8": {"Shoot": 0x13CD8, "fighter_hp": 0xFCD8},
            "operand_search_raw_range": [0x700000, 0x800000], "raw_pattern_hits": hits,
            "C1_save_select_restore": [0x7638F6, 0x76391F, 0x763975],
            "conclusion": "0660 mapping is consumer-proven; no equivalent for banked ES1000:3CD8/DA is established by this bounded scan; no omit or native HP-clear substitution is justified"}


def analyze(sources: dict[str, bytes], candidate: bytes) -> dict:
    for key, expected in HASHES.items():
        demand(digest(sources[key]) == expected, f"immutable {key} source hash")
    resources = [compare_p1(sources["wsc15"], candidate, row) for row in RESOURCE_ROWS]
    constructors = [constructor_arguments(candidate, row) for row in RESOURCE_ROWS]
    timer = timer_proof(sources["gba"], sources["wsc10"], sources["wsc15"], candidate)
    globals_report = globals_and_segments(sources["gba"], sources["wsc15"], candidate)
    rejection_checks = []
    for label, mutate, verify in (
        ("per-item tail redirected to retail container", lambda rom: struct.pack_into("<I", rom, resources[0]["tail_sites"][0], 0x083503F6),
         lambda rom: compare_p1(sources["wsc15"], rom, RESOURCE_ROWS[0])),
        ("P1 command count corrupted", lambda rom: struct.pack_into("<I", rom, 0x5C4808, 14),
         lambda rom: compare_p1(sources["wsc15"], rom, RESOURCE_ROWS[0])),
        ("constructor P0 swapped", lambda rom: struct.pack_into("<I", rom, 0x5C4580, 0x085DB400),
         lambda rom: constructor_arguments(rom, RESOURCE_ROWS[0])),
    ):
        changed = bytearray(candidate)
        mutate(changed)
        try:
            verify(changed)
        except ValueError:
            rejection_checks.append(label)
        else:
            raise ValueError(f"negative control accepted: {label}")
    return {"schema": 1, "kind": "independent-shoot-initializer-resource-and-lifetime-analysis",
            "candidate_sha256": digest(candidate), "p1_resources": resources, "constructor_consumers": constructors,
            "commercial_tail_oracle": commercial_tail_oracle(sources["gba"], sources["wsc10"]),
            "timer_proof": timer, "global_and_segment_proof": globals_report, "negative_controls_rejected": rejection_checks,
            "lifetime": {"source_36C0_allocates_fighters": False,
                         "active_slot": 0x030048A0, "other_slot": 0x0300489C, "auxiliary_slot": 0x03004D3C,
                         "entry_lifetime_proven": False,
                         "source_global_clears": ["1000:0660", "1000:3CD8", "1000:3CDA"],
                         "fighter_hp_globals_differ": ["0C00:3CD8", "0C00:3CDA"],
                         "only_0660_native_clear_installed": 0x030048A4},
            "claim_scope": "static consumer/resource identity, timer units and ABI only; lifetime across a new scene entry and whole initializer remain unproven"}


def main() -> int:
    parser = argparse.ArgumentParser()
    for key in ("gba", "wsc10", "wsc15", "candidate"):
        parser.add_argument(key, type=pathlib.Path)
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()
    result = analyze({key: getattr(args, key).read_bytes() for key in HASHES}, args.candidate.read_bytes())
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-initializer-independent] PASS {result['candidate_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
