#!/usr/bin/env python3
"""Bind the missing Shoot collision grid and preserve terminal fallthrough.

This is a later layer over immutable v53. It neither relaxes coordinate guards
nor installs external scene/controller hooks. No CPU execution or saves.
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
from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

BASE = 0x08000000
INPUT = "455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
NATIVE = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
START, END, GRID, REPAIR = 0x607000, 0x60A100, 0x607000, 0x60A000
GRID_BYTES = 56 * 54 * 4
HOOK = 0x5CD290
SOURCE_GUARDS = (
    (0x33CA20, 0x33F960, "8C05871B9374EA0E8E56ACA1D19B65E522BA8947630F7A6E4D56AE881EB066C6"),
    (0x3B5178, 0x3B51A8, "DB9B26744B3869741DE021CA571E4282736886329F39A79E3A6365C18602F4F4"),
    (0x76FB11, 0x76FF84, "52DF29A10734F9828CC9428D5983EF7FD72DB0C8AAF800F38BA66B2B591F95D3"),
    (0x77383B, 0x77387A, "CAE11D3076E7127D08E38487AD4A0EA94DF42652660BA8C6A61C10FCC674847F"),
    (0x752F8C, 0x75301E, "D81BB04710329235EC05FE021E0B1A6996CDEA9430F91E7CF55D05716198C385"),
)
NATIVE_GUARDS = (
    (0x13BF8, 0x13C64, "8EBC5E30F50EE0FE598CBB54B98B130CF1F0CA04D20E0027EF8EE7762550398B"),
    (0xC86B4, 0xC8E18, "68D63E299A5D2CB8195C1964B87FE0F39EB2E6F01EF66BA40CCC62671A43A4AB"),
    (0x373928, 0x373BA4, "820D0446E40A7A6B89C41067CF361902C53423D381ED60D30D92CE42E976D935"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def asm(source: str, raw: int) -> bytes:
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + raw)[0])


def inbound(data: bytes) -> list[tuple[str, int, int]]:
    candidates = []
    for site in range(len(data) - 3):
        target = struct.unpack_from("<I", data, site)[0] - BASE
        if START <= target < END:
            candidates.append(("unaligned-inclusive pointer", site, target))
    for site in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, site)[0]
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            relative = word & 0xFFFFFF
            if relative & 0x800000:
                relative -= 0x1000000
            target = site + 8 + relative * 4
            if START <= target < END:
                candidates.append(("ARM-like B/BL", site, target))
    return candidates


def source_grid(wsc: bytes) -> tuple[bytes, list[dict]]:
    rows = []
    for index in (39, 40):
        at = 0x3B4DD0 + index * 24
        width, height = struct.unpack_from("<HH", wsc, at)
        bank = wsc[at + 5]
        offset, segment = struct.unpack_from("<HH", wsc, at + 12)
        physical = segment * 16 + offset
        need(0x20000 <= physical < 0x30000, "source collision must use C2 bank window")
        raw = (bank & 0x7F) * 0x10000 + (physical & 0xFFFF)
        length = width * 28 * height * 18 * 4
        need((width, height, bank, raw, length) == (2, 3, 0xB3, 0x33CA20, GRID_BYTES), "source collision descriptor changed")
        rows.append({"resource": index, "raw": raw, "bytes": length, "bank": bank, "segment": segment, "offset": offset})
    return wsc[rows[0]["raw"]:rows[0]["raw"] + GRID_BYTES], rows


def build(before: bytes, gba: bytes, wsc: bytes) -> tuple[bytes, dict]:
    need((sha(before), sha(gba), sha(wsc)) == (INPUT, NATIVE, SOURCE), "exact v53/native/source identities")
    need(before[START:END] == b"\xFF" * (END - START), "new allocation is not wholly blank")
    references = inbound(before)
    need(not references, "candidate incoming encoding reaches the new allocation")
    for a, z, expected in SOURCE_GUARDS:
        need(sha(wsc[a:z]) == expected, f"source guard {a:X}")
    for a, z, expected in NATIVE_GUARDS:
        need(sha(gba[a:z]) == expected and before[a:z] == gba[a:z], f"actual native consumer guard {a:X}")
    need(sha(before[0x5CD270:0x5CD2A4]) == "14AD79A6E31C778D05A1588E4315BAB2C215A766403D572267471001874AD66E", "193B predecessor")
    need(sha(before[0x5CD2B0:0x5CD33C]) == "23A09AC06AEEA36E0D817E8531612A3217C19C788D1100EB8F411221A9436DE4", "197A prerequisite")
    grid, descriptors = source_grid(wsc)
    repair = asm("bl 0x08012008\nbl 0x085CD2B0\nb 0x085CD294", REPAIR)
    need(len(repair) == 12, "unexpected repair size")
    writes = [(GRID, grid, "complete source collision grid"),
              (REPAIR, repair, "193B assignment and same-call 197A"),
              (HOOK, asm(f"b 0x{BASE + REPAIR:08X}", HOOK), "193B successful arm only")]
    for index, map_pointer in ((29, 0x085F1F40), (30, 0x085F1F70)):
        at = 0x580000 + index * 24
        need(struct.unpack_from("<HH", before, at) == (2, 3), "source-corrected BG geometry required")
        need(struct.unpack_from("<I", before, at + 8)[0] == map_pointer, "source-corrected map descriptor required")
        need(before[at + 12:at + 16] == bytes(4), "previous collision pointer changed")
        writes.append((at + 12, struct.pack("<I", BASE + GRID), f"resource {index} collision pointer"))
    output = bytearray(before)
    allowed = set()
    details = []
    for at, blob, label in writes:
        interval = set(range(at, at + len(blob)))
        need(not allowed & interval, "overlapping writers")
        allowed |= interval
        output[at:at + len(blob)] = blob
        details.append({"offset": at, "bytes": len(blob), "label": label,
                        "before_sha256": sha(before[at:at + len(blob)]), "after_sha256": sha(blob)})
    changed = {i for i, (x, y) in enumerate(zip(before, output, strict=True)) if x != y}
    expected = {at + i for at, blob, _ in writes for i, value in enumerate(blob) if value != before[at + i]}
    need(changed == expected, "complete diff does not match Expected Writes")
    return bytes(output), {"schema": 1, "kind": "shoot-collision-and-terminal-order-repair",
                           "input_sha256": INPUT, "output_sha256": sha(output), "source_sha256": SOURCE,
                           "source_descriptors": descriptors, "grid_dimensions": [56, 54], "cell_bytes": 4,
                           "collision_entry": BASE + GRID, "terminal_order_entry": BASE + REPAIR,
                           "incoming_candidates": references, "expected_writes": details,
                           "actual_changed_bytes": len(changed),
                           "preserved_guards": ["197A clear_rows camera domain", "8EF3 captured Y/current X domain"],
                           "claim_scope": "actual collision-resource consumer and source fallthrough; no external route hook or unrestricted spatial-equivalence claim"}


def main() -> int:
    p = argparse.ArgumentParser()
    for name in ("input", "gba", "wsc15", "output"):
        p.add_argument(name, type=pathlib.Path)
    p.add_argument("--manifest", required=True, type=pathlib.Path)
    a = p.parse_args()
    need(all(getattr(a, k).suffix.lower() != ".sav" for k in ("input", "gba", "wsc15", "output")), "save files forbidden")
    output, report = build(a.input.read_bytes(), a.gba.read_bytes(), a.wsc15.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(output)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-spatial-repair] {report['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
