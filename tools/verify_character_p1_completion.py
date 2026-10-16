#!/usr/bin/env python3
"""Independently decode all added P1 events and native P0 consumer reads.

No converter or generated manifest is imported.  Relative source graphs are
compared with native pointers, with explicit frame quantization and separately
proved audio routing.  Source-specific retail edits are not learned as rules.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
BEFORE = "10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354"
AFTER = "3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
REGIONS = ((0x611800, 0x61E7DC), (0x621000, 0x621B90))
# Resource record, native P1, allocation end, associated native P0.
SPECS = (
    (12, 0x611800, 0x6156B4, 0x448000), (13, 0x6156B4, 0x6184A0, 0x400000),
    (14, 0x6184A0, 0x61B4BC, 0x420AC0), (41, 0x61B4BC, 0x61C288, 0x4B0000),
    (42, 0x61C288, 0x61CF0C, 0x4CEAE0), (43, 0x61CF0C, 0x61DB48, 0x4E85E0),
    (44, 0x61DB48, 0x61E71C, 0x4FB380), (27, 0x61E71C, 0x61E7DC, 0x60B400),
    (28, 0x621000, 0x621158, 0x60B8C0), (29, 0x621158, 0x6212C8, 0x60BEA0),
    (56, 0x6212C8, 0x62154C, 0x60C480), (57, 0x62154C, 0x6216AC, 0x60CA80),
    (58, 0x6216AC, 0x621824, 0x60CFE0), (59, 0x621824, 0x621B90, 0x60DB80),
)
SOUNDS = {5: 0, 155: 62, 156: 63, 157: 64, 158: 65, 159: 66,
          160: 67, 161: 68, 162: 69, 181: 84, 188: 95, 198: 96,
          200: 97, 203: 98, 204: 99, 255: 255}
ANCHORS = ((5, 5, 0x23F618), (155, 153, 0x2514FC), (156, 154, 0x297C20),
           (157, 155, 0x2515BC), (158, 156, 0x297BA8), (159, 157, 0x23F438),
           (160, 158, 0x263DA4), (161, 159, 0x23F0CC), (162, 160, 0x263F30),
           (181, 179, 0x23F5E8))


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, length):
    need(0 <= at <= len(data) and 0 <= length <= len(data) - at, "bounded ROM extent")
    return data[at:at + length]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def ptr(data, at, length=1):
    result = u(data, at) - BASE
    cut(data, result, length)
    return result


def far(data, at):
    offset, segment, bank = struct.unpack("<3H", cut(data, at, 6))
    physical = segment * 16 + offset
    need(0x20000 <= physical < 0x30000 and 0x80 <= bank <= 0xFF, "far source C2 mapping")
    banks = len(data) // 65536
    need(banks > 0 and banks & (banks - 1) == 0, "power-of-two source bank population")
    return (bank & (banks - 1)) * 65536 + physical - 0x20000


def source_events(data, at):
    need(u(data, at) == 4, "direct P1 source header")
    first = h(data, at + 6)
    need(first > 4 and (first - 4) % 8 == 0, "source P1 table boundary")
    count = (first - 4) // 8
    need(count <= 256, "source event population")
    result, aa, bb, end = [], {}, {}, at + first
    for index in range(count):
        n, relative, a, b = struct.unpack("<4H", cut(data, at + 4 + index * 8, 8))
        need(0 < n <= 255 and relative >= first and a > 0, "source P1 event inputs")
        commands = [struct.unpack("<6H", cut(data, at + relative + j * 12, 12)) for j in range(n)]
        aa[a] = cut(data, at + a, 8)
        end = max(end, at + relative + n * 12, at + a + 8)
        for b_relative in [b] + [words[5] for words in commands]:
            if b_relative:
                bb[b_relative] = cut(data, at + b_relative, 10)
                end = max(end, at + b_relative + 10)
        result.append((relative, a, b, commands))
    return result, aa, bb, end


def sound_lineage(old, gba, wsc, after):
    # Pair actual command slots through all 48 canonical retail resources.
    paired = {}
    for record in range(48):
        source = far(old, 0x390000 + record * 32 + 6)
        native = ptr(gba, 0xD3FB8 + record * 32 + 4)
        events, _aa, _bb, _end = source_events(old, source)
        table = ptr(gba, native, len(events) * 16)
        for event, (relative, _a, _b, commands) in enumerate(events):
            row = table + event * 16
            need(u(gba, row) == len(commands), "commercial paired event population")
            payload = ptr(gba, row + 4, len(commands) * 16)
            for command in range(len(commands)):
                paired[source + relative + command * 12] = payload + command * 16
    result = []
    for new_id, old_id, old_at in ANCHORS:
        native_at = paired[old_at]
        need(old[old_at + 1] == old_id and gba[native_at + 1] == SOUNDS[new_id],
             "actual same-event commercial audio ID")
        starts = [(data, bank + h(data, bank + sid * 6 + 4),
                   bank + h(data, bank + (sid + 1) * 6 + 4))
                  for data, bank, sid in ((old, 0x2D0000, old_id), (wsc, 0x3F0000, new_id))]
        need(all(0 < stop - start < 0x10000 for _, start, stop in starts), "bounded source sound")
        left, right = [cut(data, start, stop - start) for data, start, stop in starts]
        need(left == right, "exact old/new sound payload identity")
        result.append({"source_id": new_id, "old_id": old_id, "native_id": SOUNDS[new_id],
                       "old_item": old_at, "native_item": native_at, "payload_sha256": sha(left)})
    for sid in range(95, 100):
        song = ptr(after, 0x683200 + sid * 8, 8)
        need(0 < after[song] <= 3, "new character audio has actual track population")
        for track in range(after[song]):
            ptr(after, song + 8 + track * 4)
    return result


def all_resources(after, wsc):
    rows, total_events, total_commands, tails, A, B = [], 0, 0, 0, 0, 0
    for record, native, limit, p0 in SPECS:
        source = far(wsc, 0x740000 + record * 32 + 6)
        source_p0 = far(wsc, 0x740000 + record * 32)
        events, aa, bb, source_end = source_events(wsc, source)
        table = ptr(after, native, len(events) * 16)
        need(table == native + 8 and u(after, native + 4) == 0, "native P1 header")
        cursor = table + len(events) * 16
        a_pointers, b_pointers, commands_native = {}, {}, []
        layouts = (h(wsc, source_p0 + 18) - 16) // 4
        need(layouts > 0 and ptr(after, p0) == p0 + 16, "P0 table binding")
        need(cut(after, p0 + 8, 8) == cut(wsc, source_p0 + 8, 8), "P0 source flag binding")
        indexed = bool(h(wsc, source_p0 + 14) & 2)
        descriptors = ptr(after, p0 + 4)
        for event, (_relative, a, b, commands) in enumerate(events):
            row = table + event * 16
            need(u(after, row) == len(commands), "full native event count")
            at = ptr(after, row + 4, len(commands) * 16)
            need(at == cursor, "native command sequence and boundary")
            cursor += len(commands) * 16
            ap = ptr(after, row + 8, 8)
            need(a not in a_pointers or a_pointers[a] == ap, "source A alias preserved")
            a_pointers[a] = ap
            bp = u(after, row + 12)
            need(bool(bp) == bool(b), "event collision null preserved")
            if b:
                bp -= BASE
                cut(after, bp, 10)
                need(b not in b_pointers or b_pointers[b] == bp, "source B alias preserved")
                b_pointers[b] = bp
            for command, source_words in enumerate(commands):
                where = at + command * 16
                native_words = struct.unpack("<6H", cut(after, where, 12))
                duration, sound = source_words[0] & 255, source_words[0] >> 8
                need(sound in SOUNDS and duration > 0, "source audio and frame-time domain")
                need(native_words[0] & 255 == (duration * 4 + 2) // 5,
                     "explicit nearest 75-to-60 animation duration")
                need(native_words[0] >> 8 == SOUNDS[sound], "source audio dispatch preserved")
                need(native_words[1:5] == source_words[1:5] and native_words[5] == 0,
                     "layout, descriptor, flags and scalar words preserved; pointer word widened")
                tail = u(after, where + 12)
                need(bool(tail) == bool(source_words[5]), "command collision null preserved")
                if source_words[5]:
                    tail -= BASE
                    cut(after, tail, 10)
                    relative = source_words[5]
                    need(relative not in b_pointers or b_pointers[relative] == tail,
                         "command/event collision aliases preserved")
                    b_pointers[relative] = tail
                    tails += 1
                layout, tile = native_words[1:3]
                need(layout < layouts, "actual native P1 layout domain")
                n, original = struct.unpack("<HH", cut(wsc, source_p0 + 16 + layout * 4, 4))
                native_layout = p0 + 16 + layout * 8
                need(u(after, native_layout) == n, "actual renderer sprite part count")
                parts = ptr(after, native_layout + 4, n * 4)
                need(cut(after, parts, n * 4) == cut(wsc, source_p0 + original, n * 4),
                     "actual renderer layout identity")
                tile = tile if indexed else 0
                descriptor = descriptors + tile * 8
                length = u(after, descriptor)
                need(length > 0 and length % 32 == 0, "native descriptor copy extent")
                ptr(after, descriptor + 4, length)
                need(max(after[parts + j * 4] for j in range(n)) * 32 + 32 <= length,
                     "every native sprite tile read lies inside payload")
                commands_native.append(where)
        need(set(a_pointers) == set(aa) and set(b_pointers) == set(bb), "complete metadata graph")
        for relative in sorted(aa):
            need(a_pointers[relative] == cursor, "native A metadata packing")
            value = cut(after, cursor, 8)
            original = aa[relative]
            need(value[0] == (original[0] * 4 + 2) // 5 and
                 value[1] == (original[1] * 4 + 2) // 5 and value[2:] == original[2:],
                 "typed A durations scaled and remaining metadata preserved")
            cursor += 8
        for relative in sorted(bb):
            need(b_pointers[relative] == cursor and cut(after, cursor, 10) == bb[relative],
                 "all B collision record bytes preserved")
            cursor += 10
        need((cursor + 3) & ~3 == limit and cut(after, cursor, limit - cursor) == bytes(limit - cursor),
             "exact native P1 payload end and alignment")
        total_events += len(events)
        total_commands += len(commands_native)
        A += len(aa)
        B += len(bb)
        rows.append({"record": record, "source_p1": source, "source_end": source_end,
                     "native_p1": native, "end": limit, "p0": p0, "events": len(events),
                     "commands": len(commands_native), "A8": len(aa), "B10": len(bb)})
    need((total_events, total_commands) == (544, 2742), "all fourteen source populations")
    return rows, {"events": total_events, "commands": total_commands, "A8": A, "B10": B,
                  "nonnull_command_collision_pointers": tails}


def consumer_contract(after, gba, wsc):
    for at, raw in {
        0x75FFFF: "268B07268B5702268B4F048946FA8956FC894EFE",
        0x760323: "8A46FB", 0x760D62: "8A46FA",
        0x760EFC: "8B460E894476", 0x760F2C: "FF4C76",
        0x76033C: "9AC80EFD5F", 0x760D7B: "9AC80EFD5F",
    }.items():
        expected = bytes.fromhex(raw)
        need(cut(wsc, at, len(expected)) == expected, f"source typed consumer {at:X}")
    for at, expected in {
        0x12890: 0xE5912008, 0x12894: 0xE5852028,
        0x353BC0: 0xE5950028, 0x353C20: 0xE5810010,
        0x36E374: 0xE5941010, 0x36E378: 0xE1D100B0,
        0x36E388: 0xE1C800B2, 0x36E758: 0xE5D80003,
        0x36F60C: 0xE5D80002, 0x36A714: 0xE1C408BC,
        0x36A748: 0xE1D488FC, 0x36A74C: 0xE2588001,
        0x36A750: 0xE1C488BC,
    }.items():
        need(u(gba, at) == expected and u(after, at) == expected, f"native typed consumer {at:X}")
    for start, stop in ((0x12874, 0x12BB8), (0x12C8C, 0x12DA4),
                        (0x353B74, 0x353D40), (0x36E348, 0x36E394), (0x36A69C, 0x36A7D4)):
        need(cut(after, start, stop - start) == cut(gba, start, stop - start), "unchanged actual consumers")


def diff_check(before, after):
    need(len(before) == len(after) == 0x800000, "ROM length")
    cursor = 0
    for start, stop in REGIONS:
        need(before[cursor:start] == after[cursor:start], "outside P1 allocations unchanged")
        need(before[start:stop] == b"\xff" * (stop - start), "Expected Write empty P1 allocation")
        cursor = stop
    need(before[cursor:] == after[cursor:], "remaining ROM unchanged")


def inbound(data):
    found = []
    for pos in range(len(data) - 3):
        value = struct.unpack_from("<I", data, pos)[0]
        if any(BASE + start <= value < BASE + stop for start, stop in REGIONS):
            found.append((pos, value, "unaligned-inclusive pointer"))
        if pos % 4 == 0 and value >> 28 != 15 and value & 0x0E000000 == 0x0A000000:
            d = value & 0xFFFFFF
            d -= 0x1000000 if d & 0x800000 else 0
            target = pos + 8 + d * 4
            if any(start <= target < stop for start, stop in REGIONS):
                found.append((pos, target, "ARM-like branch"))
    return found


def rejects(call, label):
    try:
        call()
    except (ValueError, IndexError, KeyError, struct.error):
        return label
    raise ValueError(f"negative fixture accepted: {label}")


def main():
    p = argparse.ArgumentParser()
    for name in ("before", "after", "gba", "wsc10", "wsc15", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    need(all(getattr(a, name).suffix.lower() != ".sav" for name in vars(a)), "save paths forbidden")
    before, after, gba, old, source = [getattr(a, name).read_bytes() for name in
                                      ("before", "after", "gba", "wsc10", "wsc15")]
    need(tuple(map(sha, (before, after, gba, old, source))) == (BEFORE, AFTER, GBA, OLD, WSC), "input identities")
    diff_check(before, after)
    consumer_contract(after, gba, source)
    need(not inbound(before), "owned P1 allocations have no earlier inbound candidate")
    lineage = sound_lineage(old, gba, source, after)
    rows, totals = all_resources(after, source)
    table = ptr(after, SPECS[0][1])
    command = ptr(after, table + 4)
    aa = ptr(after, table + 8)
    collision_command = None
    for record, start, _stop, _p0 in SPECS:
        source_p1 = far(source, 0x740000 + record * 32 + 6)
        events, _, _, _ = source_events(source, source_p1)
        for event, (_, _, _, commands) in enumerate(events):
            native_commands = ptr(after, ptr(after, start) + event * 16 + 4)
            for index, words in enumerate(commands):
                if words[5]:
                    collision_command = native_commands + index * 16
                    break
            if collision_command is not None:
                break
        if collision_command is not None:
            break
    need(collision_command is not None, "nonnull collision negative fixture exists")
    negative = []
    fixtures = (("event count changed", table, struct.pack("<I", u(after, table) + 1)),
                ("payload shifted", table + 4, struct.pack("<I", BASE + command + 16)),
                ("source duration lost", command, bytes([after[command] ^ 1])),
                ("sound silently dropped", command + 1, b"\x01"),
                ("layout index corrupted", command + 2, b"\xff\xff"),
                ("descriptor index corrupted", command + 4, b"\xff\xff"),
                ("flags copied from template", command + 6, struct.pack("<H", h(after, command + 6) ^ 1)),
                ("A duration not preserved", aa, bytes([after[aa] ^ 1])),
                ("A scalar changed", aa + 4, bytes([after[aa + 4] ^ 1])),
                ("collision pointer omitted", collision_command + 12, bytes(4)))
    for label, at, data in fixtures:
        mutant = bytearray(after)
        mutant[at:at + len(data)] = data
        negative.append(rejects(lambda: all_resources(mutant, source), label))
    mutant = bytearray(after)
    mutant[0x61E800] ^= 1
    negative.append(rejects(lambda: diff_check(before, mutant), "unowned skipped gap"))
    mutant = bytearray(after)
    mutant[0x36A74C] ^= 1
    negative.append(rejects(lambda: consumer_contract(mutant, gba, source), "duration consumer mutation"))
    inverse = bytearray(after)
    for start, stop in REGIONS:
        inverse[start:stop] = before[start:stop]
    need(bytes(inverse) == before, "complete inverse restoration")
    result = {"schema": 1, "kind": "independent-complete-character-P1-verification", "status": "PASS",
              "before_sha256": BEFORE, "after_sha256": AFTER, "source_sha256": WSC,
              "source_records": rows, "totals": totals, "retail_audio_lineage": lineage,
              "frame_policy": "nearest integer of source ticks*60/75, independently typed animation/A durations",
              "source_remaining_A_and_all_B_bytes_preserved": True,
              "source_all_event_command_scalar_words_preserved": True,
              "actual_P0_layout_and_tile_domains_checked": True,
              "expected_write_regions": REGIONS, "predecessor_inbound_candidates": [],
              "negative_cases": negative, "inverse_restores_predecessor": True,
              "scope_limitations": ["data remains unhooked until canonical four-group routing layer",
                                    "frame quantization is explicit policy, not equality to per-resource retail tuning",
                                    "new score synthesis is verified by separate audio layer", "runtime gameplay not executed"]}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[verify-character-p1-completion] PASS {sha(a.output.read_bytes())}")


if __name__ == "__main__":
    main()
