#!/usr/bin/env python3
"""Read all 48 commercial P1 pairs without the historical truncated parser.

The oracle distinguishes structural correspondences from release-specific
edits; it never treats a native character template as missing source events.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
NEW_RECORDS = (12, 13, 14, 41, 42, 43, 44, 27, 28, 29, 56, 57, 58, 59)
NEW_COUNTS = (131, 115, 120, 39, 37, 42, 35, 2, 3, 4, 5, 3, 4, 4)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def pointer(data, where):
    offset, segment, bank = struct.unpack_from("<HHH", data, where)
    return ((bank & ((len(data) >> 16) - 1)) << 16) | (((segment << 4) + offset) & 0xFFFF)


def source(data, raw):
    table, reserved = struct.unpack_from("<HH", data, raw)
    need(table == 4 and reserved == 0, "source P1 header")
    first_payload = struct.unpack_from("<H", data, raw + table + 2)[0]
    need(first_payload > table and (first_payload - table) % 8 == 0, "source table geometry")
    count = (first_payload - table) // 8
    need(1 <= count <= 256, "source event population")
    rows = [struct.unpack_from("<HHHH", data, raw + table + 8 * i) for i in range(count)]
    items = []
    ends = [first_payload]
    for length, relative, a, b in rows:
        need(0 < length < 256 and relative >= first_payload, "source command extent")
        need(raw + relative + length * 12 <= len(data), "source command range")
        commands = [struct.unpack_from("<6H", data, raw + relative + j * 12) for j in range(length)]
        ends.extend((relative + length * 12, a + 8))
        ends.extend(value + 10 for value in [b] + [c[5] for c in commands] if value)
        items.append(commands)
    end = max(ends)
    need(end < 0x10000 and raw + end <= len(data), "complete source resource extent")
    return rows, items, end


def main():
    p = argparse.ArgumentParser()
    for name in ("gba", "wsc10", "wsc15", "output"):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    need(all(getattr(a, n).suffix.lower() != ".sav" for n in ("gba", "wsc10", "wsc15", "output")),
         "save paths forbidden")
    gba, old, new = (getattr(a, n).read_bytes() for n in ("gba", "wsc10", "wsc15"))
    need(tuple(map(sha, (gba, old, new))) == (GBA_SHA256, WSC10_SHA256, WSC15_SHA256), "original identities")
    totals = Counter()
    sound_map = defaultdict(Counter)
    pairs, edits, anchors = [], [], {}
    for record in range(48):
        src = pointer(old, 0x390000 + record * 32 + 6)
        dst = struct.unpack_from("<I", gba, 0xD3FB8 + record * 32 + 4)[0] - BASE
        rows, commands, end = source(old, src)
        table, reserved = struct.unpack_from("<II", gba, dst)
        need(table == BASE + dst + 8 and reserved == 0, "native P1 header")
        first = struct.unpack_from("<I", gba, dst + 12)[0]
        need(first - table == len(rows) * 16, "commercial event population")
        before = totals.copy()
        for event, ((count, rel, ar, br), payload) in enumerate(zip(rows, commands, strict=True)):
            gc, gp, ga, gb = struct.unpack_from("<IIII", gba, dst + 8 + event * 16)
            need(gc == count, "commercial per-event command count")
            need(BASE <= gp <= BASE + len(gba) - count * 16 and BASE <= ga <= BASE + len(gba) - 8,
                 "commercial payload/A pointers")
            totals["events"] += 1
            av, gav = old[src + ar:src + ar + 8], gba[ga - BASE:ga - BASE + 8]
            if av != gav:
                totals["A_metadata_edits"] += 1
                edits.append({"record": record, "event": event, "kind": "A8",
                              "source_hex": av.hex(), "native_hex": gav.hex()})
            need(bool(br) == bool(gb), "commercial B null correspondence")
            if br and old[src + br:src + br + 10] != gba[gb - BASE:gb - BASE + 10]:
                totals["B_metadata_edits"] += 1
                edits.append({"record": record, "event": event, "kind": "B10",
                              "source_hex": old[src + br:src + br + 10].hex(),
                              "native_hex": gba[gb - BASE:gb - BASE + 10].hex()})
            for index, item in enumerate(payload):
                native = struct.unpack_from("<8H", gba, gp - BASE + index * 16)
                totals["commands"] += 1
                for field in (1, 2, 3, 4):
                    if item[field] != native[field]:
                        totals[f"command_word{field}_edits"] += 1
                        edits.append({"record": record, "event": event, "item": index,
                                      "kind": f"word{field}", "source": item[field], "native": native[field]})
                tail = native[6] | native[7] << 16
                need(native[5] == 0, "native old relative-pointer word cleared")
                if item[5]:
                    need(BASE <= tail <= BASE + len(gba) - 10, "native command B pointer")
                    need(old[src + item[5]:src + item[5] + 10] == gba[tail - BASE:tail - BASE + 10],
                         "all commercial command B records exact")
                    totals["non_null_command_B_records_exact"] += 1
                else:
                    need(tail == 0, "native null command B remains null")
                hi, g_hi = item[0] >> 8, native[0] >> 8
                if hi not in (0, 255):
                    sound_map[hi][g_hi] += 1
                    anchors.setdefault((hi, g_hi), {"record": record, "event": event, "item": index,
                                                   "source_raw": src + rel + index * 12,
                                                   "native_raw": gp - BASE + index * 16})
        pairs.append({"record": record, "source": src, "native": dst,
                      "source_bytes": end, "source_sha256": sha(old[src:src + end]),
                      "events": len(rows), "commands": sum(row[0] for row in rows),
                      "structural_event_and_command_counts_exact": True})
    expected = {"events": 1997, "commands": 9928, "non_null_command_B_records_exact": 703,
                "A_metadata_edits": 133, "B_metadata_edits": 1,
                "command_word1_edits": 16, "command_word2_edits": 2, "command_word3_edits": 14}
    need(dict(totals) == expected, "complete commercial population changed")
    targets = []
    for record, expected_count in zip(NEW_RECORDS, NEW_COUNTS, strict=True):
        src = pointer(new, 0x740000 + record * 32 + 6)
        rows, commands, end = source(new, src)
        need(len(rows) == expected_count, "new source event population")
        b = set(row[3] for row in rows) | {item[5] for payload in commands for item in payload}
        b.discard(0)
        targets.append({"record": record, "source": src, "source_bytes": end,
                        "source_sha256": sha(new[src:src + end]), "events": len(rows),
                        "commands": sum(row[0] for row in rows),
                        "unique_A8": len({row[2] for row in rows}), "unique_B10": len(b),
                        "sound_bytes": sorted({item[0] >> 8 for payload in commands for item in payload})})
    report = {"status": "PASS", "kind": "independent-complete-character-p1-commercial-oracle",
              "inputs": [GBA_SHA256, WSC10_SHA256, WSC15_SHA256], "totals": dict(totals),
              "pairs": pairs, "release_specific_edits": edits,
              "sound_pair_population": [{"source_id": sid, "native_ids": dict(counts),
                                          "anchors": [{"native_id": native, **anchors[sid, native]}
                                                      for native in counts]}
                                         for sid, counts in sorted(sound_map.items())],
              "target_populations": targets,
              "proved": ["event table geometry and all counts", "12-byte to16-byte command stride",
                         "word5 relative B10 becomes32-bit native pointer at+12; old word5 iszero",
                         "all703 nonnull command B10 records byte-identical; nullstaysnull"],
              "not_generalized": ["commercial release-specific scalar/metadata edits",
                                   "sound IDs based solely on numeric offset", "template replacement"],
              "runtime_or_save_access": False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[character-p1-oracle] PASS " + sha(a.output.read_bytes()))


if __name__ == "__main__":
    main()
