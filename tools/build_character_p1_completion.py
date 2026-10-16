#!/usr/bin/env python3
"""Emit all source events for the fourteen added character P1 resources.

This is a data-only layer. Later canonical resource-table wiring is separate.
No template events, metadata pointers, or command tails replace source data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
INPUT_SHA256 = "10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
SOURCE_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
# Record, source, guarded source extent, events, commands, output raw, source hash.
SPECS = (
    (12, 0x342E60, 0x2DE0, 131, 824, 0x611800, "C2F33110B2ABC971AB31E7130D56D5DDB003F18E80758CA6EC13BF063E46EB47"),
    (13, 0x370000, 0x212A, 115, 585, 0x6156B4, "81DFE668EB4E53537312147AAA78EA14F64A78362EA07680F038480EEEF4FFB1"),
    (14, 0x368FF0, 0x22E0, 120, 611, 0x6184A0, "9136E0950AAC65F24197700355806D66A66C50735E5136272CE3574235DA747B"),
    (41, 0x3ADEF0, 0xA0A, 39, 164, 0x61B4BC, "3FD94EFBD82DB33241B4C25352C8780FA746F6F4B850CFED7CC9C83C770E05CD"),
    (42, 0x2EF6C0, 0x914, 37, 145, 0x61C288, "A6B9730E3B2479CA275081623B1C7D1164B8CCC7861B357E7D20C812BF08E830"),
    (43, 0x3B37B0, 0x8E0, 42, 130, 0x61CF0C, "91BFC08783CEA88255DFCED40CC3A8057168E0FDFCF9FC8451982384FB116A50"),
    (44, 0x3B6340, 0x882, 35, 141, 0x61DB48, "2CFD7165DCD0329259438D445AF6E62B06A06D8CA531B4955BA4F509B5D88E9C"),
    (27, 0x3D4C60, 0x94, 2, 6, 0x61E71C, "2EC109D8ACD17E59D95B44CF4183DDBD1B42D7796F2238003C7F3DA84B5C0C5B"),
    (28, 0x3D22A0, 0x10A, 3, 12, 0x621000, "A3CF3B05674EE9EACC162F00FBA4F51C6DF923F35A2C2CFC9EBD4B2B09F7D9B2"),
    (29, 0x3CFEE0, 0x110, 4, 15, 0x621158, "76508B218AB81161587205A45BF6F49EA80256CA477F573CC230119AB6CBF8E4"),
    (56, 0x3CF5F0, 0x1DE, 5, 30, 0x6212C8, "80DAFEDBE2E6E867EBF0A50677BDA753FC14264E950CC11ABA31DB98199F57CD"),
    (57, 0x3D2190, 0x108, 3, 15, 0x62154C, "40E6FC637269510D7EDFA5245D99682394E2CD929425D37FF14371924FC4CC35"),
    (58, 0x3D1BF0, 0x11C, 4, 16, 0x6216AC, "B5CB000B8D25ABB1BDEDF4F2A0BB0FCF239EAC503B03E1D8D043524EE90A4CA3"),
    (59, 0x3CC590, 0x288, 4, 48, 0x621824, "9CCD97B239D427A34B12B87094C5AB224DCD3AD77B09205500C353E91DCE81B5"),
)
REGIONS = ((0x611800, 0x61E7DC), (0x621000, 0x621B90))
SOUNDS = {0xFF: 0xFF, 0x05: 0x00, 0x9B: 0x3E, 0x9C: 0x3F,
          0x9D: 0x40, 0x9E: 0x41, 0x9F: 0x42, 0xA0: 0x43,
          0xA1: 0x44, 0xA2: 0x45, 0xB5: 0x54, 0xBC: 0x5F,
          0xC6: 0x60, 0xC8: 0x61, 0xCB: 0x62, 0xCC: 0x63}
# New source sound, old source sound, native sound, old/new native paired P1 item.
SOUND_ANCHORS = (
    (0x05, 0x05, 0x00, 0x23F618, 0x0D6E40),
    (0x9B, 0x99, 0x3E, 0x2514FC, 0x100340),
    (0x9C, 0x9A, 0x3F, 0x297C20, 0x28AA6C),
    (0x9D, 0x9B, 0x40, 0x2515BC, 0x100440),
    (0x9E, 0x9C, 0x41, 0x297BA8, 0x28A9CC),
    (0x9F, 0x9D, 0x42, 0x23F438, 0x0D6BC0),
    (0xA0, 0x9E, 0x43, 0x263DA4, 0x226664),
    (0xA1, 0x9F, 0x44, 0x23F0CC, 0x0D6730),
    (0xA2, 0xA0, 0x45, 0x263F30, 0x226874),
    (0xB5, 0xB3, 0x54, 0x23F5E8, 0x0D6E00),
)
SOURCE_CODE = (
    (0x7524CB, 0x75260B, "1826E9A4434E337A7E3FBE513B266D2469D7FD4D2BEA8934A3B982C50B86A66F", "source event reader"),
    (0x752852, 0x752A06, "E82866DD794B203F903BF03D6B9707160DB5431D44F1B8F661CE4A20899CA9B5", "source animation tick"),
    (0x75FFF8, 0x760016, "2702D15F58DF752B01B8AF0C8F385FABF2062216A9B4EDF776FF8A8931C467F9", "source A metadata reader"),
    (0x760323, 0x760341, "DC5CEAA7948BB4E9CEB97CAF24DA1CE5AB6AF6589D9C275360F25753F377321C", "source A byte1 duration"),
    (0x760D62, 0x760D80, "7667F06CE9144939D955E17A236C8279A4EB172A0D93248B501B38257EAFF4A9", "source A byte0 duration"),
    (0x760E98, 0x760F79, "2E7A2C56FA205641D57A13379BACEF429E8BD51268C809BEC627767055286BF1", "source duration callback"),
)
NATIVE_CODE = (
    (0x12874, 0x129C8, "1BBCE2EEE607287D2AEFA2B899D43A9C4C6890BFE5CCAF6533D8FAF6EBF2EBD4", "native event reader"),
    (0x12A84, 0x12BB8, "F9003EC255AF1C92BA2262AB6DE6B98FBC6C59DC368B31E3D6C316B7B834437E", "native animation tick"),
    (0x36E348, 0x36E394, "82CF37E7AC589DFC7B238FE59B23CE1BBFE1A0A01DD67875BA5F911715EB074B", "native A metadata reader"),
    (0x36A69C, 0x36A7D4, "803FE3D37F8962FE2CB84172DEAB606E24507245629AD9BACA06849976EDC757", "native duration callback"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def u16(data, pos):
    return struct.unpack_from("<H", data, pos)[0]


def u32(data, pos):
    return struct.unpack_from("<I", data, pos)[0]


def sound_payload(data, bank, sound):
    start = u16(data, bank + sound * 6 + 4)
    end = u16(data, bank + (sound + 1) * 6 + 4)
    need(0x400 <= start < end < 0x10000, "bounded sound payload")
    return data[bank + start:bank + end]


def ticks(value):
    return (value * 4 + 2) // 5


def parse(data):
    """One source P1 container; every pointer is relative to its start."""
    table, reserved = struct.unpack_from("<HH", data)
    need(table == 4 and reserved == 0, "source header")
    first_payload = u16(data, table + 2)
    need(first_payload > table and (first_payload - table) % 8 == 0, "source table boundary")
    events = (first_payload - table) // 8
    need(0 < events <= 256, "source event population")
    entries, commands, a_records, b_offsets = [], [], {}, set()
    ends = [first_payload]
    for index in range(events):
        count, payload, a, b = struct.unpack_from("<4H", data, table + index * 8)
        need(0 < count <= 255 and first_payload <= payload <= len(data) - count * 12,
             "source command extent")
        need(0 < a <= len(data) - 8 and (b == 0 or b <= len(data) - 10), "source metadata extent")
        items = [struct.unpack_from("<6H", data, payload + j * 12) for j in range(count)]
        need(all(item[0] >> 8 in SOUNDS and 1 <= (item[0] & 255) <= 30 for item in items),
             "source sound and animation duration population")
        entries.append((count, payload, a, b))
        commands.append(items)
        a_records[a] = data[a:a + 8]
        b_offsets.add(b)
        b_offsets.update(item[5] for item in items)
        ends.extend((payload + count * 12, a + 8))
    b_offsets.discard(0)
    need(all(0 < b <= len(data) - 10 for b in b_offsets), "source command B extent")
    ends.extend(b + 10 for b in b_offsets)
    need(max(ends) == len(data), "source complete bounded footprint")
    return entries, commands, a_records, {b: data[b:b + 10] for b in sorted(b_offsets)}


def convert(data, target):
    entries, commands, aa, bb = parse(data)
    cursor = 8 + len(entries) * 16
    payload_at = []
    for payload in commands:
        payload_at.append(cursor)
        cursor += len(payload) * 16
    a_at, b_at = {}, {}
    for relative in sorted(aa):
        a_at[relative] = cursor
        cursor += 8
    for relative in sorted(bb):
        b_at[relative] = cursor
        cursor += 10
    out = bytearray((cursor + 3) & ~3)
    address = lambda offset: BASE + target + offset
    struct.pack_into("<II", out, 0, address(8), 0)
    for event, ((count, _, a, b), payload) in enumerate(zip(entries, commands, strict=True)):
        struct.pack_into("<4I", out, 8 + 16 * event, count, address(payload_at[event]),
                         address(a_at[a]), address(b_at[b]) if b else 0)
        for index, source_words in enumerate(payload):
            low = source_words[0] & 255
            high = source_words[0] >> 8
            word0 = ticks(low) | SOUNDS[high] << 8
            tail = address(b_at[source_words[5]]) if source_words[5] else 0
            struct.pack_into("<6HI", out, payload_at[event] + index * 16,
                             word0, *source_words[1:5], 0, tail)
    for relative, record in aa.items():
        value = bytes((ticks(record[0]), ticks(record[1]))) + record[2:]
        out[a_at[relative]:a_at[relative] + 8] = value
    for relative, record in bb.items():
        out[b_at[relative]:b_at[relative] + 10] = record
    return bytes(out), {"events": len(entries), "commands": sum(e[0] for e in entries),
                        "unique_A8": len(aa), "unique_B10": len(bb),
                        "nonnull_command_B": sum(bool(i[5]) for p in commands for i in p),
                        "sound_source_ids": sorted({i[0] >> 8 for p in commands for i in p})}


def make_assets(gba, old, source):
    need(tuple(map(sha, (gba, old, source))) == (GBA_SHA256, OLD_SHA256, SOURCE_SHA256),
         "original ROM identities")
    for data, ranges in ((source, SOURCE_CODE), (gba, NATIVE_CODE)):
        for lo, hi, digest, label in ranges:
            need(sha(data[lo:hi]) == digest, label)
    anchors = []
    for new_id, old_id, native_id, old_at, native_at in SOUND_ANCHORS:
        payload = sound_payload(source, 0x3F0000, new_id)
        need(payload == sound_payload(old, 0x2D0000, old_id), "exact source sound payload lineage")
        need(old[old_at + 1] == old_id and gba[native_at + 1] == native_id,
             "commercial P1 sound anchor")
        need(SOUNDS[new_id] == native_id, "sound mapping")
        anchors.append({"source_id": new_id, "old_id": old_id, "native_id": native_id,
                        "old_item": old_at, "native_item": native_at, "payload_sha256": sha(payload)})
    outputs = []
    for record, src, length, events, commands, dst, digest in SPECS:
        offset, segment, bank = struct.unpack_from("<3H", source, 0x740000 + record * 32 + 6)
        resolved = ((bank & 127) << 16) | (((segment << 4) + offset) & 0xFFFF)
        need(resolved == src, "source resource pointer")
        data = source[src:src + length]
        need(sha(data) == digest, "complete source P1 identity")
        blob, details = convert(data, dst)
        need((details["events"], details["commands"]) == (events, commands), "source population")
        need(any(lo <= dst < dst + len(blob) <= hi for lo, hi in REGIONS), "owned output range")
        outputs.append((dst, blob, {"record": record, "source": src, "source_bytes": length,
                                   "source_sha256": digest, "target": dst, "bytes": len(blob),
                                   "sha256": sha(blob), **details}))
    for lo, hi in REGIONS:
        covered = [(dst, dst + len(blob)) for dst, blob, _ in outputs if lo <= dst < hi]
        need(covered[0][0] == lo and covered[-1][1] == hi and
             all(a[1] == b[0] for a, b in zip(covered, covered[1:])), "asset packing geometry")
    return outputs, anchors


def check_inbound(before):
    hits = []
    for pos in range(len(before) - 3):
        word = u32(before, pos)
        if any(BASE + lo <= word < BASE + hi for lo, hi in REGIONS):
            hits.append((pos, word, "unaligned pointer"))
        if pos % 4 == 0 and word & 0x0E000000 == 0x0A000000 and word >> 28 != 15:
            delta = word & 0xFFFFFF
            if delta & 0x800000:
                delta -= 0x1000000
            target = pos + 8 + delta * 4
            if any(lo <= target < hi for lo, hi in REGIONS):
                hits.append((pos, target, "ARM branch-like word"))
    need(not hits, f"existing potential inbound reference: {hits[:4]}")


def build(before, gba, old, source):
    need(len(before) == 0x800000 and sha(before) == INPUT_SHA256, "fixed character-audio predecessor")
    outputs, anchors = make_assets(gba, old, source)
    for lo, hi, digest, label in NATIVE_CODE:
        need(sha(before[lo:hi]) == digest, "preserved " + label)
    check_inbound(before)
    after = bytearray(before)
    writes = []
    for target, blob, details in outputs:
        previous = before[target:target + len(blob)]
        need(previous == b"\xFF" * len(blob), "Expected Write blank expansion")
        after[target:target + len(blob)] = blob
        writes.append({"raw": target, "bytes": len(blob), "before_sha256": sha(previous),
                       "after_sha256": sha(blob), "record": details["record"]})
    for index, (left, right) in enumerate(zip(before, after, strict=True)):
        need(left == right or any(lo <= index < hi for lo, hi in REGIONS), "complete ROM diff ownership")
    report = {"schema": 1, "kind": "complete-character-p1-assets", "input_sha256": INPUT_SHA256,
              "output_sha256": sha(after), "expected_writes": writes,
              "assets": [details for _, _, details in outputs],
              "total_payload_bytes": sum(len(blob) for _, blob, _ in outputs),
              "source_sound_lineage": anchors, "sound_map": SOUNDS,
              "frame_time_policy": "75-to60 Hz nearest integer (4*n+2)//5 for command duration and A bytes0/1",
              "source_metadata_policy": "A bytes2..7 and all B10 bytes preserved; relative pointers relocated",
              "source_command_policy": "all events and all commands; words1..4 preserved; word5 becomes tail pointer",
              "source_05_audio_bridge": "commercial P1 native highbyte00 skips request; no invented stop helper",
              "new_audio_ids": {"BC": 95, "C6": 96, "C8": 97, "CB": 98, "CC": 99},
              "inbound_scan": {"all_byte_offset_pointers": 0, "aligned_ARM_B_BL_like": 0},
              "source_consumer_guards": SOURCE_CODE, "native_consumer_guards": NATIVE_CODE,
              "template_events_used": 0, "external_entry_or_table_writes": 0,
              "new_RAM_allocation": False, "runtime_or_save_access": False}
    return bytes(after), report


def main():
    p = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc10", "wsc15", "output"):
        p.add_argument(name, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    a = p.parse_args()
    need(all(getattr(a, n).suffix.lower() != ".sav" for n in
             ("input", "gba", "wsc10", "wsc15", "output", "manifest")), "save paths forbidden")
    after, report = build(*(getattr(a, n).read_bytes() for n in ("input", "gba", "wsc10", "wsc15")))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[character-p1-completion] " + report["output_sha256"])


if __name__ == "__main__":
    main()
