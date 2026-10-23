#!/usr/bin/env python3
"""Read-only proof of both result-pose byte-pair table routes.

Reads the four named ROMs only. No save, emulator, builder or manifest is
consulted. The source tables, actual instructions and complete selected P1
frames supply the contract; this program does not create a patch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BASE = 0x08000000
CURRENT = "A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
TABLES = (("win", 0x89774, 0x3B5D7C, 0x7771C0),
          ("lose", 0x89790, 0x3B5D96, 0x7771E0))
LITERALS = ((0x8A418, 0x8A41C, 0x8A43C, 0x8A440, 0x8A44C, 0x8A450),
            (0x8A420, 0x8A424, 0x8A444, 0x8A448, 0x8A454, 0x8A458))
READERS = ((0x8A014, 0x3B6281, 0x7776B4, 0),
           (0x8A030, 0x3B628E, 0x7776C1, 1),
           (0x8A12C, 0x3B6316, 0x777749, 0),
           (0x8A148, 0x3B6323, 0x777756, 1),
           (0x8A174, 0x3B6345, 0x777778, 0),
           (0x8A190, 0x3B6352, 0x777785, 1))
FIRST, LIMIT = 0x629480, 0x6294C0
GUARDS = {
    "current": ((0x897AC, 0x89870, "4AF05F9E3774C81DF5DAEEC3EB81E1518258A0FBDDBA58A9365B8F6CDE3A9FE9"),
                (0x89FC0, 0x8A228, "9893B564778DCCAA40407D3721BD1EA22B3EA84DBCC10DC92FD1EB1A5DDF6C41"),
                (0x1F3A8, 0x1F4A0, "0732867DA2D3D2BE7CB8D1D317B1498C93A8C74E5005317478015865397352BC"),
                (0x8A7C0, 0x8AC34, "66249C9DC26CB9CB6835A09F29D34528635D6BBFC975A8C5B868C862937116E8"),
                (0x12874, 0x12C28, "6A63C22471C3CF2DB8860BC2BEBCBC17BA9754525E31D86E3E3DC496937CAB5F")),
    "old": ((0x3B5E0C, 0x3B5E20, "BC95787F23C3E082F26E28A73E8F3B98337A4A15996106871E8E51CED5E30E60"),
            (0x3B6275, 0x3B62AA, "08ABFD02D79EBD754F359CAF530D4D10DA397A54F05E2616D3CCF65C67502BC0"),
            (0x3B6303, 0x3B636F, "1709394739D2FB5FA429BCF2B5346ADEA5ACA6364B74CB1B8DC3E878151B4E34"),
            (0x3B5D7C, 0x3B5D96, "830259187E9CADBE69BFD117641431D811A076FD3A9921EB3DFFE1425C7E52B8"),
            (0x3B5D96, 0x3B5DB0, "3A66959D8A0A048989904D52FE544BF87EF3607A06EC2BCB44A9A80A1FDBA553")),
    "new": ((0x77725C, 0x777270, "BC95787F23C3E082F26E28A73E8F3B98337A4A15996106871E8E51CED5E30E60"),
            (0x7776A8, 0x7776DD, "0CFECC02BDCB4227DE956DD3A7F0D1CB65FD66C1EEF446B0ABE86F3CDEF9FF48"),
            (0x777736, 0x7777A2, "7DD576220E4C695A75538FC262074000F0A80C2377A7062C5FAC6345E5A98DD3"),
            (0x785A82, 0x785B21, "430BF4B0FB86CCEC17A901FE6D18142840BE626EC73F98A4EDF6CC88325ACC0A"),
            (0x7771C0, 0x7771E0, "14448EABC6A4FFBA9C35F59463C846C39EA58EC64C2644D4306E79D6EFC56DDE"),
            (0x7771E0, 0x777200, "DF5A6BB90401C34B5E96F1B99648191AD796666B4E2D6FF06647565C74E79658")),
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded ROM read")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def ptr(data, at, size=1):
    result = u(data, at) - BASE
    cut(data, result, size)
    return result


def far(data, at):
    off, seg, bank = struct.unpack("<3H", cut(data, at, 6))
    linear = seg * 16 + off
    need(0x20000 <= linear < 0x30000 and 0x80 <= bank <= 0xFF, "source C2 far pointer")
    return (bank & (len(data) // 0x10000 - 1)) * 0x10000 + linear - 0x20000


def refs(data, value):
    pattern, result, at = struct.pack("<I", value), [], 0
    while (at := data.find(pattern, at)) >= 0:
        result.append(at)
        at += 1
    return result


def seq(data, at, size, expected, arm=False):
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    actual = list(decoder.disasm(cut(data, at, size), at + (BASE if arm else 0)))
    need(sum(i.size for i in actual) == size, f"instruction extent {at:X}")
    need([f"{i.mnemonic} {i.op_str}".strip() for i in actual] == expected,
         f"actual instruction contract {at:X}")


def literal(data, at):
    word = u(data, at)
    need(word & 0x0F7FF000 == 0x051F8000, "PC-relative r8 literal load")
    return at + 8 + (word & 4095) * (1 if word & 0x800000 else -1)


def source_events(data, p1):
    need(u(data, p1) == 4, "source P1 header")
    first = h(data, p1 + 6)
    need(first > 4 and (first - 4) % 8 == 0, "source P1 complete event-table boundary")
    count = (first - 4) // 8
    need(1 <= count <= 256, "source P1 event count")
    rows = []
    for event in range(count):
        n, rel, a, b = struct.unpack("<4H", cut(data, p1 + 4 + event * 8, 8))
        need(0 < n <= 255 and rel >= first and a > 0, "source P1 row extent")
        cut(data, p1 + a, 8)
        if b:
            cut(data, p1 + b, 10)
        rows.append((rel, [struct.unpack("<6H", cut(data, p1 + rel + i * 12, 12)) for i in range(n)]))
    return rows


def selected_population(current, gba, old, new, ident, selected):
    p0 = ptr(current, 0x4A80F8 + ident * 32)
    p1 = ptr(current, 0x4A80F8 + ident * 32 + 4)
    p0table, event_table = ptr(current, p0), ptr(current, p1)
    src = far(new, 0x740000 + ident * 32 + 6)
    rows = source_events(new, src)
    need(ptr(current, event_table + 4) - event_table == len(rows) * 16,
         "actual native complete P1 table agrees with source")
    if ident < 12:
        need(ptr(gba, 0xD3FB8 + ident * 32 + 4) == p1, "retail base P1 identity retained")
        old_rows = source_events(old, far(old, 0x390000 + ident * 32 + 6))
        need(len(old_rows) == len(rows), "all legacy result P1 event populations unchanged")
    result = []
    for event in sorted(selected):
        need(0 <= event < len(rows), f"ID{ident} result event{event} within complete P1")
        relative, source_commands = rows[event]
        count = u(current, event_table + event * 16)
        need(count == len(source_commands), "selected event full frame count")
        commands = ptr(current, event_table + event * 16 + 4, count * 16)
        if ident < 12:
            need(cut(current, commands, count * 16) == cut(gba, commands, count * 16),
                 "retail selected command bytes retained")
            need([c[1:5] for c in old_rows[event][1]] == [c[1:5] for c in source_commands],
                 "old/new source selected command layout/tile/flag/scalar lineage")
        frames = []
        for index, words in enumerate(source_commands):
            command = commands + index * 16
            need(tuple(h(current, command + k * 2) for k in (1, 2, 3, 4)) == words[1:5],
                 "every selected native frame has exact source layout/tile/flags/scalar")
            layout, descriptor = words[1:3]
            parts = u(current, p0table + layout * 8)
            need(0 < parts <= 127, "bounded native layout part population")
            part_data = ptr(current, p0table + layout * 8 + 4, parts * 4)
            descriptor_table = ptr(current, p0 + 4)
            flags = h(current, p0 + 14) | h(current, p1 + 4)
            at = descriptor_table + (descriptor * 8 if flags & 2 else 0)
            atlas_bytes = u(current, at)
            ptr(current, at + 4, atlas_bytes)
            need(atlas_bytes > 0 and atlas_bytes % 32 == 0, "selected full native tile descriptor")
            for part in range(parts):
                need((h(current, part_data + part * 4) & 255) * 32 < atlas_bytes,
                     f"actual renderer low-byte tile index within selected atlas: ID{ident} event{event} frame{index} layout{layout} descriptor{descriptor} P0flag{h(current,p0+14):X} tile{h(current,part_data+part*4):X} bytes{atlas_bytes:X}")
            frames.append({"frame": index, "layout": layout, "descriptor": descriptor,
                           "parts": parts, "duration": current[command],
                           "flags": f"{h(current, command + 6):04X}"})
        result.append({"event": event, "frame_count": count, "frames": frames,
                       "source_commands": f"{src + relative:06X}",
                       "native_commands": f"{BASE + commands:08X}"})
    return {"id": ident, "source_P1": f"{src:06X}", "native_P0": f"{BASE + p0:08X}",
            "native_P1": f"{BASE + p1:08X}", "event_population": len(rows), "events": result,
            "max_parts_one_frame": max(f["parts"] for e in result for f in e["frames"])}


def ownership(data):
    need(cut(data, FIRST, LIMIT - FIRST) == b"\xff" * 64, "proposed64-byte reservation is FF")
    for at in range(len(data) - 3):
        if data[at + 3] in (8, 10, 12):
            mirror = data[at + 3] << 24
            need(not mirror + FIRST <= u(data, at) < mirror + LIMIT,
                 "no encoded aligned/unaligned/interior inbound reservation pointer")
    for at in range(0, len(data) - 3, 4):
        word = u(data, at)
        if word >> 28 == 15:
            continue
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF
            delta -= 1 << 24 if delta & 0x800000 else 0
            need(not FIRST <= at + 8 + 4 * delta < LIMIT, "no ARM branch into proposed reservation")
        if word & 0x0E1F0000 == 0x041F0000:
            target = at + 8 + (word & 4095) * (1 if word & 0x800000 else -1)
            need(not FIRST <= target < LIMIT, "no ARM PC-relative access into proposed reservation")
        if word & 0x0E0F0000 == 0x020F0000 and (word >> 21) & 15 in (2, 4):
            rotate, value = ((word >> 8) & 15) * 2, word & 255
            if rotate:
                value = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF
            target = at + 8 + (value if (word >> 21) & 15 == 4 else -value)
            need(not FIRST <= target < LIMIT, "no ARM ADR into proposed reservation")
    for at in range(0, len(data) - 1, 2):
        word = h(data, at)
        if word & 0xF800 in (0x4800, 0xA000):
            target = ((at + 4) & ~3) + (word & 255) * 4
            need(not FIRST <= target < LIMIT, "no Thumb literal/ADR into proposed reservation")
        if word & 0xF800 == 0xE000:
            delta = word & 0x7FF
            delta -= 0x800 if delta & 0x400 else 0
            need(not FIRST <= at + 4 + delta * 2 < LIMIT, "no Thumb branch into proposed reservation")
        if word & 0xF000 == 0xD000 and word & 0xF00 < 0xE00:
            delta = word & 255
            delta -= 256 if delta & 128 else 0
            need(not FIRST <= at + 4 + delta * 2 < LIMIT, "no Thumb conditional branch into proposed reservation")
        if word & 0xF800 == 0xF000 and at + 3 < len(data):
            low = h(data, at + 2)
            if low & 0xF800 == 0xF800:
                high = word & 0x7FF
                high -= 0x800 if high & 0x400 else 0
                target = at + 4 + (high << 12) + ((low & 0x7FF) << 1)
                need(not FIRST <= target < LIMIT, "no Thumb BL into proposed reservation")
    return {"raw": f"{FIRST:06X}..{LIMIT:06X}", "bytes": 64, "previous_hit_layer_end": "629480",
            "FF": True, "all_alignment_interior_pointer_scan": True,
            "ARM_branch_literal_ADR_scan": True, "Thumb_branch_literal_ADR_scan": True}


def analyze(current, gba, old, new, check_allocation=True):
    data = {"current": current, "old": old, "new": new}
    for kind, spans in GUARDS.items():
        for a, b, expected in spans:
            need(sha(cut(data[kind], a, b - a)) == expected, f"complete {kind} code contract {a:X}")
            if kind == "current":
                need(current[a:b] == gba[a:b], "native mode8 constructor/callback/renderer code unchanged")
    seq(new, 0x77725C, 20, ["xor ax, ax", "mov al, byte ptr [di + 0xa]",
        "mov word ptr [bp - 6], ax", "mov al, byte ptr [di + 0xc]",
        "mov word ptr [bp - 8], ax", "mov ax, word ptr es:[si]", "mov word ptr [bp - 0xa], ax"])
    seq(current, 0x1F3B0, 8, ["ldr r8, [pc, #0xe8]", "add r1, r8, r1, lsl #5"], arm=True)
    need(u(current, literal(current, 0x1F3B0)) == BASE + 0x4A80F8, "actual base-only resource group")
    seq(current, 0x8A9B4, 20, ["ldrh r1, [r4, #4]", "stmdb sp!, {r5}",
        "stmdb sp!, {fp}", "stmdb sp!, {r1}", "bl #0x8012874"], arm=True)
    seq(current, 0x8AA90, 20, ["ldrh r2, [r5, #6]", "stmdb sp!, {r1}",
        "stmdb sp!, {fp}", "stmdb sp!, {r2}", "bl #0x8012874"], arm=True)
    seq(current, 0x8AA78, 12, ["ldrh r8, [r1, #0xa]", "tst r8, #0x2000", "beq #0x808aaa8"], arm=True)
    readers = []
    for native_at, old_at, new_at, which in READERS:
        old_offset = TABLES[which][2] - 0x3B5AD0
        new_offset = TABLES[which][3] - 0x776F10
        for rom, at, offset in ((old, old_at, old_offset), (new, new_at, new_offset)):
            seq(rom, at, 10, [f"mov cl, byte ptr cs:[bx + 0x{offset:x}]",
                             f"mov ch, byte ptr cs:[bx + 0x{offset + 1:x}]"])
        lo, hi = literal(current, native_at), literal(current, native_at + 8)
        need(u(current, lo) == BASE + TABLES[which][1] and u(current, hi) == BASE + TABLES[which][1] + 1,
             "native low/high byte literal pair")
        seq(current, native_at + 4, 4, ["ldrb r2, [r1, r8]"], arm=True)
        seq(current, native_at + 12, 12, ["ldrb sb, [r1, r8]", "lsls sb, sb, #8", "orrs r2, r2, sb"], arm=True)
        readers.append({"native": f"{BASE + native_at:08X}", "source10": f"{old_at:06X}",
                        "source15": f"{new_at:06X}", "family": TABLES[which][0],
                        "literals": [f"{BASE + lo:08X}", f"{BASE + hi:08X}"]})
    tables = []
    defects = []
    for number, (name, native, previous, source) in enumerate(TABLES):
        need(old[previous:previous + 24] == new[source:source + 24] == current[native:native + 24] == gba[native:native + 24],
             "all twelve legacy result-pose pairs have exact source lineage")
        need(old[previous + 24:previous + 26] == new[source + 30:source + 32] == b"\0\0", "explicit trailing source zero pair")
        expected_aliases = {native: list(LITERALS[number][::2]), native + 1: list(LITERALS[number][1::2])}
        for offset in range(28):
            need(refs(current, BASE + native + offset) == expected_aliases.get(native + offset, []),
                 "all-alignment base/interior source table aliases closed")
        rows = []
        for ident in range(15):
            current_pair = list(cut(current, native + ident * 2, 2))
            source_pair = list(cut(new, source + ident * 2, 2))
            item = {"id": ident, "current_events": current_pair, "source_events": source_pair,
                    "native_read": f"{BASE + native + ident * 2:08X}",
                    "source_read": f"{source + ident * 2:06X}", "matches": current_pair == source_pair}
            rows.append(item)
            if not item["matches"]:
                defects.append({"family": name, **item})
        tables.append({"family": name, "native": f"{BASE + native:08X}",
                       "old_source": f"{previous:06X}", "source": f"{source:06X}",
                       "old_storage_bytes": 26, "source_storage_bytes": 32,
                       "source_bytes": cut(new, source, 32).hex().upper(), "rows": rows,
                       "source_trailing_pair": [0, 0]})
    # The boundaries are adjacent actual table references and the constructor
    # entry, not a guessed run of zero bytes or a presumed terminator.
    seq(old, 0x3B5DB0, 6, ["push bp", "mov bp, sp", "add sp, -0xa"])
    seq(new, 0x777200, 6, ["push bp", "mov bp, sp", "add sp, -0xa"])
    need(len(defects) == 6 and {x["id"] for x in defects} == {12, 13, 14}, "six added result-pose route defects")
    populations = []
    for ident in range(15):
        selected = {0, 1, 0x51, 0x56}
        selected.update(new[0x7771C0 + ident * 2:0x7771C2 + ident * 2])
        selected.update(new[0x7771E0 + ident * 2:0x7771E2 + ident * 2])
        populations.append(selected_population(current, gba, old, new, ident, selected))
    return {"schema": 1, "kind": "read-only-result-pose-routing", "status": "PROVED_ROUTING_DEFECT",
            "hashes": {"current": sha(current), "gba": sha(gba), "wsc10": sha(old), "wsc15": sha(new)},
            "tables": tables, "readers": readers, "defects": defects, "populations": populations,
            "selected_events": sum(len(p["events"]) for p in populations),
            "selected_frames": sum(e["frame_count"] for p in populations for e in p["events"]),
            "native_event_consumer": {"first": "0808A9C4", "second": "0808AAA0",
                                      "second_trigger": "presentation +0A flag2000; one transition",
                                      "loader": "0801F3A8", "group": "084A80F8", "evolution_switch": False},
            "proposal": {"new_table_bytes": 64, "literal_words": 12, "total_written_bytes": 112,
                         "allocation": ownership(current) if check_allocation else None, "original_tables_retained": True,
                         "code_P1_P0_palette_changes": False},
            "limits": ["No ROM mutation or emulator/save access.",
                       "Source final zero pair is retained as explicit storage; its independent behavior is not inferred.",
                       "Initial slide events1/51, idle0, wait56 and draw override0/1 are retained.",
                       "Single-resource part maxima are not the complete mode8 OAM bound.",
                       "Source result-label LOSE behavior is outside this routing component."]}


def negative_checks(inputs):
    current, gba, old, new = inputs
    cases = []
    def reject(label, index, at, replacement, allocation=False):
        mutated = [bytearray(d) if i == index else d for i, d in enumerate(inputs)]
        mutated[index][at:at + len(replacement)] = replacement
        try:
            ownership(mutated[0]) if allocation else analyze(*mutated, check_allocation=False)
        except (ValueError, struct.error):
            cases.append(label)
        else:
            raise ValueError(f"negative case incorrectly accepted: {label}")
    for table_index, sites in enumerate(LITERALS):
        for site in sites:
            reject(f"wrong-pair-literal-{site:X}", 0, site, struct.pack("<I", BASE + TABLES[1 - table_index][1]))
    reject("source-added-ID14-first-event-changed", 3, 0x7771DC, b"\x73")
    reject("source-final-zero-pair-changed", 3, 0x7771FE, b"\x01")
    reject("native-pair-index-stride-changed", 0, 0x8A000, struct.pack("<I", 0xE2911001))
    reject("second-pose-completion-gate-changed", 0, 0x8AA7C, struct.pack("<I", 0xE3181000))
    reject("unlisted-interior-table-reference", 0, LIMIT + 4, struct.pack("<I", BASE + 0x89776))
    for ident in (12, 13, 14):
        p1 = ptr(current, 0x4A80F8 + ident * 32 + 4)
        table = ptr(current, p1)
        event = new[0x7771C0 + ident * 2]
        command = ptr(current, table + event * 16 + 4)
        reject(f"ID{ident}-missing-native-event-frame", 0, table + event * 16, b"\0\0\0\0")
        reject(f"ID{ident}-wrong-native-frame-layout", 0, command + 2, b"\xff\xff")
        reject(f"ID{ident}-wrong-native-completion-flag", 0, command + 6, b"\x01\0")
    reject("occupied-proposed-allocation", 0, FIRST, b"\0", allocation=True)
    reject("unaligned-interior-inbound-pointer", 0, 0x628F81, struct.pack("<I", BASE + FIRST + 7), allocation=True)
    reject("ROM-mirror-interior-inbound-pointer", 0, 0x628F81, struct.pack("<I", 0x0C000000 + FIRST + 9), allocation=True)
    branch_at = FIRST - 0x100
    reject("ARM-branch-into-proposal", 0, branch_at,
           struct.pack("<I", 0xEA000000 | ((FIRST - branch_at - 8) // 4)), allocation=True)
    reject("Thumb-literal-into-proposal", 0, branch_at,
           struct.pack("<H", 0x4800 | ((FIRST - ((branch_at + 4) & ~3)) // 4)), allocation=True)
    reject("Thumb-BL-into-proposal", 0, branch_at,
           struct.pack("<HH", 0xF000, 0xF800 | ((FIRST - branch_at - 4) // 2)), allocation=True)
    return {"count": len(cases), "all_rejected": True, "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("current", "gba", "wsc10", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    paths = [getattr(args, k) for k in ("current", "gba", "wsc10", "wsc15", "output")]
    need(all(p.suffix.lower() != ".sav" for p in paths), "save paths are forbidden")
    need(args.output.suffix.lower() == ".json", "report extension")
    need(args.output.resolve() not in {p.resolve() for p in paths[:4]}, "report cannot overwrite an input")
    inputs = [p.read_bytes() for p in paths[:4]]
    need(tuple(map(sha, inputs)) == (CURRENT, GBA, OLD, NEW), "pinned four ROM identities")
    report = analyze(*inputs)
    if args.self_test:
        report["negative_checks"] = negative_checks(inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[result-pose-routing] {report['status']} six defects; {report['selected_events']} events/{report['selected_frames']} frames; {sha(args.output.read_bytes())}")


if __name__ == "__main__":
    main()
