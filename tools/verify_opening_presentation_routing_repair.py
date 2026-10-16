#!/usr/bin/env python3
"""Independent consumer and inverse checks for the opening selector-view repair.

No builder is imported.  This validates the one literal repair and reconstructs
the native P1 -> layout -> sprite/tile reads that the selected resources drive.
It does not certify the remaining callback timing/position/flag translation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
BEFORE = "8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2"
AFTER = "E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
SITE, OLD, NEW = 0x853F4, 0xD42B8, 0x5B5400
OLD_LITERALS = (0x850E0, 0x850E4, 0x850E8, SITE, 0x85794, 0x86288,
                0x862B8, 0x87018, 0x87020, 0x8718C, 0x87194, 0x87388,
                0x87394, 0xCC230, 0xCC708, 0x3534B8)
OPENING_LOADS = {
    0x850E0: (0x84F00, 0), 0x850E4: (0x84F1C, 1),
    0x850E8: (0x84F38, 2), SITE: (0x851DC, 13),
    0x85794: (0x8556C, 4), 0x86288: (0x85EA8, 5),
    0x862B8: (0x85FD0, 6), 0x87018: (0x86EAC, 5),
    0x87020: (0x86F04, 7), 0x8718C: (0x87058, 1),
    0x87194: (0x870B0, 8), 0x87388: (0x871CC, 0),
    0x87394: (0x87224, 9),
}
NATIVE_CONTRACT = {
    0x88254: 0xE59D000C, 0x88258: 0xE59D5004, 0x8825C: 0xE0855280,
    0x88294: 0xE5958004, 0x882A4: 0xE5958000, 0x882B4: 0xE5958008,
    0x127F0: 0xE5850044, 0x127F8: 0xE5850048,
    0x1287C: 0xE5954044, 0x12888: 0xE5941000, 0x1288C: 0xE0811203,
    0x128A4: 0xE5911004, 0x128B0: 0xE5851024,
    0x1291C: 0xE1D100B2, 0x12920: 0xE1C501B8,
    0x12C8C: 0xE5954048, 0x12CA4: 0xE594A000,
    0x12CA8: 0xE1D521B8, 0x12CAC: 0xE08AA182,
    0x12CB0: 0xE59A2000, 0x12CB4: 0xE59AA004,
    0x12DA4: 0xE2522001, 0x12DA8: 0xCAFFFFC9,
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, raw):
    need(0 <= raw <= len(data) - 4, f"word outside ROM: {raw:X}")
    return struct.unpack_from("<I", data, raw)[0]


def ptr(data, raw):
    result = word(data, raw) - BASE
    need(0 <= result < len(data), f"non-ROM pointer read from {raw:X}")
    return result


def occurrences(data, value):
    needle = struct.pack("<I", value)
    result, cursor = [], 0
    while True:
        cursor = data.find(needle, cursor)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def literal_target(data, raw):
    code = word(data, raw)
    need(code & 0x0F7F0000 == 0x051F0000, "expected ARM PC-relative word load")
    return raw + 8 + ((code & 4095) if code & (1 << 23) else -(code & 4095))


def branch_target(data, raw):
    code = word(data, raw)
    need(code & 0x0F000000 == 0x0B000000, "expected ARM BL")
    delta = code & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return BASE + raw + 8 + 4 * delta


def routing_contract(data):
    need(word(data, 0x851CC) == 0xE3A0800D, "selector 13 assignment")
    need(literal_target(data, 0x851DC) == SITE, "literal consumer address")
    need(word(data, SITE) == BASE + NEW, "selector 13 uses expanded view")
    need(branch_target(data, 0x851E4) == BASE + 0x88250, "constructor target")
    for raw, expected in NATIVE_CONTRACT.items():
        need(word(data, raw) == expected, f"native consumer instruction {raw:X}")
    need(tuple(word(data, NEW + 13 * 32 + i * 4) for i in range(3)) ==
         (0x082DA800, 0x082D9A94, 0x082F8D28), "selector 13 P0/P1/P2 identity")


def view_audit(data):
    need(occurrences(data, BASE + OLD) == [x for x in OLD_LITERALS if x != SITE],
         "complete unaligned old-view literal population")
    need(occurrences(data, BASE + NEW) == [SITE, 0x5B4254, 0x5B4464, 0x5B8168],
         "complete unaligned expanded-view literal population")
    rows = []
    for pool, (load, selector) in OPENING_LOADS.items():
        need(literal_target(data, load) == pool, "opening resource literal load")
        need(branch_target(data, load + 8) == BASE + 0x88250, "opening constructor BL")
        pushes = [p for p in range(load - 24, load, 4)
                  if word(data, p) == 0xE92D0100]
        need(len(pushes) >= 2, "opening selector/slot stack arguments")
        assignment = word(data, pushes[-2] - 4)
        need(assignment == 0xE3A08000 | selector, "opening immediate selector")
        need(selector < (15 if pool == SITE else 11), "opening selector inside selected view")
        rows.append({"literal": pool, "load": load, "selector": selector,
                     "view": word(data, pool), "consumer": BASE + 0x88250})
    # These three consumers take dynamic fighter IDs.  Their expanded-roster
    # repair is a separate work item; they are deliberately not certified here.
    for pool, load in ((0xCC230, 0xCBE74), (0xCC708, 0xCC34C), (0x3534B8, 0x353370)):
        need(literal_target(data, load) == pool, "remaining dynamic view consumer")
    return rows


def resource_commands(data, selector, check_tiles=False):
    row = NEW + selector * 32
    p0, p1 = ptr(data, row), ptr(data, row + 4)
    layout = ptr(data, p0)
    items = ptr(data, layout + 4)
    need(items > layout and (items - layout) % 8 == 0, "layout-table geometry")
    layouts = (items - layout) // 8
    event = ptr(data, p1)
    commands = ptr(data, event + 4)
    need(commands > event and (commands - event) % 16 == 0, "P1 event-table geometry")
    events = (commands - event) // 16
    need(layouts <= 256 and events <= 256, "bounded resource populations")
    rows, total = [], 0
    for index in range(events):
        count = word(data, event + 16 * index)
        command = ptr(data, event + 16 * index + 4)
        need(0 < count <= 256 and command + count * 16 <= len(data), "event command extent")
        max_parts = 0
        for frame in range(count):
            command_row = command + frame * 16
            layout_id, tile_id = struct.unpack_from("<HH", data, command_row + 2)
            need(layout_id < layouts, "P1 command layout index inside native P0")
            parts = word(data, layout + layout_id * 8)
            parts_at = ptr(data, layout + layout_id * 8 + 4)
            need(0 < parts <= 36 and parts_at + parts * 4 <= len(data), "native sprite part extent")
            max_parts = max(max_parts, parts)
            if check_tiles:
                descriptor = ptr(data, p0 + 4) + tile_id * 8
                length, tile = word(data, descriptor), ptr(data, descriptor + 4)
                need(length > 0 and length % 32 == 0 and tile + length <= len(data), "tile payload extent")
                need(max(data[parts_at + p * 4] for p in range(parts)) * 32 + 32 <= length,
                     "sprite tile index inside descriptor payload")
            total += 1
        rows.append({"event": index, "commands": count, "maximum_sprite_parts": max_parts})
    return {"selector": selector, "p0": BASE + p0, "p1": BASE + p1,
            "layouts": layouts, "events": events, "commands": total,
            "all_command_layout_indices_valid": True,
            "all_command_tiles_checked": check_tiles, "event_rows": rows}


def verify_diff(before, after):
    need(len(before) == len(after) == 0x800000, "ROM length")
    need(word(before, SITE) == BASE + OLD, "Expected Write old value")
    need(word(after, SITE) == BASE + NEW, "Expected Write replacement")
    need(before[:SITE] == after[:SITE] and before[SITE + 4:] == after[SITE + 4:],
         "unexpected byte outside literal")


def rejected(call, label):
    try:
        call()
    except (ValueError, struct.error):
        return label
    raise ValueError(f"negative did not reject: {label}")


def main():
    parser = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav"
             for name in ("before", "after", "gba", "wsc15", "output")), "save paths forbidden")
    before, after, gba, wsc = [getattr(args, name).read_bytes()
                              for name in ("before", "after", "gba", "wsc15")]
    need(tuple(map(sha, (before, after, gba, wsc))) == (BEFORE, AFTER, GBA, WSC), "input identities")
    verify_diff(before, after)
    routing_contract(after)
    need(wsc[0x756F05:0x756F11] == bytes.fromhex("68C0036A006A0D9ACC4C8C55"),
         "source table 03C0, slot 0, selector 13, constructor")
    need(after[NEW:NEW + 11 * 32] == gba[OLD:OLD + 11 * 32], "commercial rows preserved")
    need(after[NEW + 13 * 32:NEW + 13 * 32 + 12] ==
         gba[OLD + 7 * 32:OLD + 7 * 32 + 12], "commercial selector 7 reuse")
    audit = view_audit(after)
    resources = [resource_commands(after, selector, selector == 13) for selector in range(15)]
    negative = [rejected(lambda: routing_contract(before), "historical wrong view"),
                rejected(lambda: verify_diff(after, before), "inverse wrong-direction patch")]
    for label, raw, replacement, check in (
        ("unrelated byte", 0x5C1500, word(after, 0x5C1500) ^ 1, lambda x: verify_diff(before, x)),
        ("selector out of range", 0x851CC, 0xE3A0800F, routing_contract),
        ("constructor stride changed", 0x8825C, 0xE0855200, routing_contract),
        ("P0 replaced by auxiliary", NEW + 13 * 32, 0x082A02EC, routing_contract),
        ("P1 replaced by auxiliary", NEW + 13 * 32 + 4, 0x082A0040, routing_contract),
        ("first command layout out of bounds", 0x2D9D2C, word(after, 0x2D9D2C) | 0xFFFF0000,
         lambda x: resource_commands(x, 13, True)),
        ("renderer sprite count oversized", 0x2DA810, 129,
         lambda x: resource_commands(x, 13, True)),
    ):
        mutant = bytearray(after)
        struct.pack_into("<I", mutant, raw, replacement)
        negative.append(rejected(lambda: check(mutant), label))
    inverse = bytearray(after)
    inverse[SITE:SITE + 4] = before[SITE:SITE + 4]
    need(bytes(inverse) == before, "complete inverse recovers exact predecessor")
    old_p1 = ptr(before, OLD + 13 * 32 + 4)
    old_events = ptr(before, old_p1)
    old_count = (ptr(before, old_events + 4) - old_events) // 16
    need(old_count == 6 and word(before, old_events + 0x21 * 16 + 4) == 0x00700000,
         "bad event 21 reads source-external non-ROM command pointer")
    report = {
        "status": "PASS", "kind": "independent-opening-presentation-routing-verification",
        "before_sha256": sha(before), "after_sha256": sha(after),
        "expected_write": {"raw": SITE, "old": BASE + OLD, "new": BASE + NEW},
        "changed_bytes": sum(a != b for a, b in zip(before, after, strict=True)),
        "inverse_exact": True, "native_consumer_instruction_contracts": len(NATIVE_CONTRACT),
        "opening_old_view_use_audit": audit,
        "remaining_dynamic_old_view_consumers": [0x080CBE74, 0x080CC34C, 0x08353370],
        "expanded_view_command_layout_coverage": resources,
        "wrong_view_chain": {"p0": 0x082A02EC, "p1": 0x082A0040,
                             "tile_base": 0x082A0508, "events": old_count,
                             "event_21_command_pointer": 0x00700000},
        "negatives": negative,
        "scope_limits": [
            "Callback 6 source event0/flip-clear/position differences remain separate from this literal repair.",
            "All15rows have valid command-to-layout indices; only repairedselector13 has complete tile-payload checks here.",
            "Selector12 unused later events38..45 have truncated descriptors in the historical asset and require separate repair.",
            "Three dynamic gameplay view consumers and added-roster table field routing require separate repair.",
            "No emulator or save file is opened by this verifier.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[opening-routing-verify] PASS report={sha(args.output.read_bytes())}")


if __name__ == "__main__":
    main()
