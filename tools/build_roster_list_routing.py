#!/usr/bin/env python3
"""Keep expanded roster lookups out of the retail selection-state fields.

The established clean-roster/unlock policy is unchanged. Four immutable ROM
views supply the three real indexed consumers; the original twelve RAM slots
and the live selection presentation handle remain owned by their native users.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

INPUT = "7D9849EA7E46ECEB9C41D21194277E694F34A2E190E4DAE38083D451E8D27470"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, TABLE = 0x08000000, 0x628000
BRIDGES = ((0x81D04, 0x628080, 4, 0xE59F41E0),
           (0x81FF4, 0x6280C0, 4, 0xE59F4094),
           (0x83238, 0x628100, 8, 0xE59F8050))
INTERVALS = ((TABLE, TABLE + 128),) + tuple((at, at + 44) for _, at, _, _ in BRIDGES)
SUPPRESS = ((0x5B002C, 0xE0C400B2, 0xE1A04004),
            (0x5B0040, 0x10C410B2, 0x11A04004),
            (0x5B0050, 0x10C410B2, 0x11A04004))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def branch(at, destination):
    delta = destination - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM B range")
    return 0xEA000000 | ((delta // 4) & 0xFFFFFF)


def ownership(data):
    def owned(at):
        return any(a <= at < b for a, b in INTERVALS)
    for a, b in INTERVALS:
        need(data[a:b] == bytes([255]) * (b - a), "exact new span is FF")
    for at in range(len(data) - 3):
        need(not owned(word(data, at) - BASE), "prior encoded pointer into new span")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            delta -= 0x1000000 if delta & 0x800000 else 0
            need(not owned(at + 8 + delta * 4), "prior ARM branch into new span")
        if value & 0x0E1F0000 == 0x041F0000:
            delta = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not owned(at + 8 + delta), "prior immediate PC-relative reference into new span")


def build(before, gba, source):
    need((sha(before), sha(gba), sha(source)) == (INPUT, GBA, SOURCE), "exact predecessor and source identities")
    need(len(before) == 0x800000, "expanded ROM size")
    need(sha(source[0x7787DB:0x778848]) ==
         "312C684C77B26610C6EE4F443B6F365AF12F6D3E354646317E9776B60DF8F35C",
         "source clean roster and conditional unlock producer")
    # The overlapping field is positively a native presentation handle. It is
    # not spare array capacity and must remain a full 32-bit pointer.
    need(before[0x8240C:0x82414] == gba[0x8240C:0x82414] == bytes.fromhex("1c509fe5180085e5") and
         word(before, 0x82430) == 0x03004710, "actual selection handle producer at list+18")
    need(before[0x81DBC:0x81DC4] == gba[0x81DBC:0x81DC4] == bytes.fromhex("30519fe5180095e5") and
         word(before, 0x81EF4) == 0x03004710, "actual selection handle reader at list+18")
    need(before[0x81710:0x8171C] == gba[0x81710:0x8171C] == bytes.fromhex("0230a0e1013053e2b830c4e1"),
         "native maximum cursor remains count minus one")
    need(word(before, 0x81880) == 0x03002310 and
         word(before, 0x5B0034) == 0xE5D50019, "actual shared unlock byte owner")
    need(before[0x5B0000:0x5B0028] == bytes.fromhex(
        "82c044e00c40a0e10000a0e30b20a0e3b200c4e0010080e2012052e2fbffffca0d00a0e3b200c4e0"),
         "first twelve original RAM list slots unchanged")
    need(word(before, 0x5B0030) == 0xE3A0200D and
         word(before, 0x5B0044) == word(before, 0x5B0054) == 0x12822001,
         "established thirteen plus optional unlock count")
    for site, _, _, expected in BRIDGES:
        need(word(before, site) == expected and before[site:site + 12] == gba[site:site + 12],
             "actual retail indexed-list consumer")
    ownership(before)
    tables, rows = bytearray(), []
    for index in range(4):
        row = list(range(11)) + [13, 14]
        if index & 1:
            row.append(11)
        if index & 2:
            row.append(12)
        rows.append(row)
        tables.extend(struct.pack("<16H", *(row + [0xFFFF] * (16 - len(row)))))
    writes = [(TABLE, bytes(tables), "four source-backed immutable roster views")]
    for site, at, register, expected in BRIDGES:
        words = (0xE92D0001, 0xE59F0018, 0xE5D00019, 0xE2000030, 0xE1A00080,
                 0xE59F000C | register << 12,
                 0xE0800000 | register << 16 | register << 12,
                 0xE8BD0001, branch(at + 32, site + 4), 0x03002310, BASE + TABLE)
        writes.append((at, struct.pack("<11I", *words), f"consumer {site:06X} base adapter"))
        writes.append((site, struct.pack("<I", branch(site, at)), f"consumer {site:06X} hook"))
    for at, expected, replacement in SUPPRESS:
        need(word(before, at) == expected, "Expected Write overflow store")
        writes.append((at, struct.pack("<I", replacement), "remove write outside twelve native roster slots"))
    after = bytearray(before)
    occupied = set()
    for at, data, label in writes:
        cells = set(range(at, at + len(data)))
        need(not occupied & cells, "disjoint expected writes")
        occupied |= cells
        after[at:at + len(data)] = data
    inverse = bytearray(after)
    for at, data, _ in writes:
        inverse[at:at + len(data)] = before[at:at + len(data)]
    need(inverse == before, "whole-ROM inverse outside exact new spans/hooks")
    return bytes(after), dict(schema=1, kind="roster-list-routing", input_sha256=INPUT,
        output_sha256=sha(after), changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        expected_writes=[dict(raw=at, bytes=len(data), label=label,
                             before_sha256=sha(before[at:at + len(data)]), after_sha256=sha(data))
                         for at, data, label in writes], intervals=INTERVALS, rows=rows,
        indexed_consumers=[dict(site=site, bridge=at, output_register=f"r{register}", continuation=BASE + site + 4)
                           for site, at, register, _ in BRIDGES],
        ABI="only original list-base output register changes; r0, all other registers, NZCV, LR and SP preserved",
        RAM_writes="original first12 list slots only; no new state owner; native presentation handle and cached-ID fields untouched",
        source_policy="existing clean roster0..10,13,14 plus unlocked11/12; sourcealternate-mode branch not changed by this repair",
        live_overlap=dict(list=0x03004710, index12=0x03004728, handle_store=0x08082410,
                          handle_read=0x08081DC0, capture_handle=0x02010360),
        supplied_save_accessed=False, runtime_claim=False)


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    need(all(getattr(args, name).suffix.lower() != ".sav" for name in
             ("input", "gba", "wsc15", "output", "manifest")), "save paths forbidden")
    after, report = build(*(getattr(args, name).read_bytes() for name in ("input", "gba", "wsc15")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[roster-list-routing] " + report["output_sha256"])


if __name__ == "__main__":
    main()
