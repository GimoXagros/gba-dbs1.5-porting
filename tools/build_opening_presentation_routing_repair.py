#!/usr/bin/env python3
"""Bind callback 6's new selector 13 to the existing expanded resource view.

The historical callback changed its selector but retained the eleven-row retail
view.  This final overlay repairs that one literal; it does not alter resources,
the native renderer, callback instructions, or earlier reproducible layers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

BASE = 0x08000000
INPUT_SHA256 = "8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
SITE, OLD_VIEW, NEW_VIEW = 0x0853F4, 0x0D42B8, 0x5B5400
SOURCE_GUARDS = (
    (0x756DB7, 0x757077, "2CBAA61F3F805446659BF3815EA77D94BF911F816A252D131C153A0B0D6FDDC5", "source callback 6"),
    (0x7404A0, 0x7404C0, "E5040857EF14B2FCCD87734A0ED71C75A696BB3D048017996FAD093E49382BFF", "source presentation record 37"),
    (0x3B0000, 0x3B0519, "C761D001B02C6F89F3AAC533F198CB35E51761BDA05122A7ACFCC803B124EE1D", "source selector 13 P1"),
)
NATIVE_GUARDS = (
    (0x088250, 0x088310, "AAF329B99CD8BABB7A4CC6AE663C59C09C2E05B05C8288ED484FD694870EA27E", "native constructor"),
    (0x012C28, 0x012DCC, "CA332A44EEDF35C22C1B20104C457753C5095AB3564657A713880552A0BBF7B8", "native layout renderer"),
    (0x000160, 0x0001A0, "535BAFF9F42CD7CD2A3FE51C8E154CCD28CB73285BE88D58A788FFC793037F66", "native renderer DMA copy"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def u32(data: bytes, raw: int) -> int:
    return struct.unpack_from("<I", data, raw)[0]


def pointer(data: bytes, raw: int) -> int:
    result = u32(data, raw) - BASE
    need(0 <= result < len(data), f"invalid ROM pointer at {raw:06X}")
    return result


def inspect_layouts(data: bytes) -> list[dict]:
    """Read the native count/pointer entries consumed by the copied renderer."""
    result = []
    for selector in range(15):
        row = NEW_VIEW + 32 * selector
        header = pointer(data, row)
        table = pointer(data, header)
        first_items = pointer(data, table + 4)
        need(table == header + 16 and first_items > table and
             (first_items - table) % 8 == 0, "native P0 table geometry")
        frames = (first_items - table) // 8
        need(0 < frames <= 256, "native P0 frame population")
        cursor, counts = first_items, []
        for frame in range(frames):
            count = u32(data, table + frame * 8)
            items = pointer(data, table + frame * 8 + 4)
            need(0 < count <= 36 and items == cursor and
                 items + count * 4 <= len(data), "native P0 count or item extent")
            counts.append(count)
            cursor += count * 4
        descriptor = pointer(data, header + 4)
        need(cursor == descriptor, "native P0 layout/descriptor boundary")
        result.append({"selector": selector, "p0": BASE + header,
                       "layout_frames": frames, "minimum_items": min(counts),
                       "maximum_items": max(counts), "layout_items": sum(counts),
                       "layout_sha256": sha(data[table:cursor])})
    return result


def build(before: bytes, gba: bytes, wsc15: bytes) -> tuple[bytes, dict]:
    need(len(before) == 0x800000 and sha(before) == INPUT_SHA256,
         "fixed physics-routing-repaired predecessor")
    need(sha(gba) == GBA_SHA256 and sha(wsc15) == WSC15_SHA256,
         "original ROM identities")
    for first, last, digest, label in SOURCE_GUARDS:
        need(sha(wsc15[first:last]) == digest, label)
    for first, last, digest, label in NATIVE_GUARDS:
        need(sha(gba[first:last]) == digest, label)
        need(before[first:last] == gba[first:last], "preserved " + label)
    need(wsc15[0x756F05:0x756F11] == bytes.fromhex(
        "68C0036A006A0D9ACC4C8C55"), "source selector 13 constructor")
    need(sha(before[0x85118:0x85454]) ==
         "41ADC248BDA7A6CBE77FFBCBA0B83EED062D436EF28666D07B743A1C632B0AB8",
         "exact integrated callback 6")
    need(u32(before, 0x851CC) == 0xE3A0800D, "callback selector is not 13")
    need(u32(before, 0x851DC) == 0xE59F8210 and
         0x851DC + 8 + 0x210 == SITE, "callback literal consumer")
    need(u32(before, 0x851E4) == 0xEB000C19, "native constructor call")
    need(u32(before, SITE) == BASE + OLD_VIEW, "Expected Write old view")
    need(sha(before[NEW_VIEW:NEW_VIEW + 15 * 32]) ==
         "8EFF8EC1B0CBBD7334563D8EA55B920E67BA8D88883FD334F7929E29B615DBD3",
         "expanded fifteen-selector resource view")
    need(before[NEW_VIEW:NEW_VIEW + 11 * 32] == gba[OLD_VIEW:OLD_VIEW + 11 * 32],
         "retail selectors 0 through 10 are preserved")
    expected = (0x082DA800, 0x082D9A94, 0x082F8D28)
    need(struct.unpack_from("<3I", before, NEW_VIEW + 13 * 32) == expected,
         "expanded selector 13 resource identity")
    need(struct.unpack_from("<3I", gba, OLD_VIEW + 7 * 32) == expected,
         "commercial selector 7 resource reuse")
    layouts = inspect_layouts(before)
    old, new = struct.pack("<I", BASE + OLD_VIEW), struct.pack("<I", BASE + NEW_VIEW)
    after = bytearray(before)
    after[SITE:SITE + 4] = new
    changed = [i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b]
    need(changed == [SITE + i for i in range(4) if old[i] != new[i]],
         "complete ROM diff outside Expected Write")
    return bytes(after), {
        "schema": 1, "kind": "opening-presentation-routing-repair",
        "input_sha256": INPUT_SHA256, "output_sha256": sha(after),
        "output_bytes": len(after), "changed_bytes": len(changed),
        "expected_writes": [{"raw": SITE, "bytes": 4, "before_hex": old.hex(),
                             "after_hex": new.hex(), "before_sha256": sha(old),
                             "after_sha256": sha(new),
                             "label": "callback 6 selector 13 expanded resource view"}],
        "consumer": {"literal_load": BASE + 0x851DC, "selector": 13,
                     "constructor": BASE + 0x88250, "row_bytes": 32,
                     "p0": expected[0], "p1": expected[1], "p2": expected[2]},
        "source_guards": [{"raw": first, "end_exclusive": last, "sha256": digest,
                           "label": label} for first, last, digest, label in SOURCE_GUARDS],
        "expanded_view_layouts": layouts,
        "instructions_changed": False, "new_ROM_or_RAM_allocation": False,
        "runtime_verification": "performed separately; builder does not launch an emulator",
        "provided_save_accessed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path, required=True)
    args = parser.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in
             (args.input, args.gba, args.wsc15, args.output, args.manifest)), "save paths forbidden")
    result, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[opening-presentation-routing-repair] " + report["output_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
