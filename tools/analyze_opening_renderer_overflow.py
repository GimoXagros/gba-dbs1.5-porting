#!/usr/bin/env python3
"""Replay the observed opening overflow's pointer/count chain without execution.

Consumes the original bad ROM and an endpoint-verified root-owned runtime probe.
Does not import a patch builder, write guest memory, or inspect a save file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct

BASE = 0x08000000
BAD_SHA256 = "93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E"
PROBE_SHA256 = "F548E7E9C1F5EAE8FA035908E5AC69171E538127DDA8A3649A85A38D196A0D8C"


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def analyze(rom: bytes, probe_bytes: bytes) -> dict:
    need(sha(rom) == BAD_SHA256, "original failed runtime artifact")
    need(sha(probe_bytes) == PROBE_SHA256, "frozen actual overflow probe")
    probe = json.loads(probe_bytes)
    need(probe["rom_sha256"] == BAD_SHA256 and
         probe["endpoint"]["verified"] and
         probe["loaded_rom_samples"]["verified"] and
         probe["guest_writes"] == [] and not probe["monitor_visible"],
         "runtime provenance")
    event, = [e for e in probe["events"] if e["stop"] == "T05watch:03001828;"]
    regs = [int(value, 16) for value in event["registers"]]
    obj = bytes.fromhex(event["presentation"]["hex"])
    need(regs[5] == 0x03002908 and event["presentation"]["address"] == "03002908",
         "observed primary presentation")

    # Resolve the actual native literal load and constructor's 32-byte row.
    need(u32(rom, 0x851CC) == 0xE3A0800D and
         u32(rom, 0x851DC) == 0xE59F8210 and
         u32(rom, 0x851E4) == 0xEB000C19, "callback selector/load/call")
    literal_raw = 0x851DC + 8 + (u32(rom, 0x851DC) & 0xFFF)
    view = u32(rom, literal_raw)
    need(literal_raw == 0x853F4 and view == 0x080D42B8, "old view address")
    row_raw = view - BASE + 13 * 32
    p0, p1, p2 = struct.unpack_from("<III", rom, row_raw)
    need((p0, p1, p2) == (0x082A02EC, 0x082A0040, 0x082A0988),
         "unintended auxiliary row")
    need((u32(obj, 0x48), u32(obj, 0x44), u32(obj, 0x4C)) == (p0, p1, p2),
         "actual presentation retained the wrong row")

    table = u32(rom, p0 - BASE)
    descriptor = u32(rom, p0 - BASE + 4)
    pixel_base = u32(rom, descriptor - BASE + 4)
    frame = u16(obj, 0x18)
    entry_raw = table - BASE + frame * 8
    count, items = struct.unpack_from("<II", rom, entry_raw)
    need((table, frame, entry_raw, count, items) ==
         (0x082A02FC, 0xE1D1, 0x311184, 0x00F223F3, 0x00F2223F),
         "malformed frame count and pointer")
    steps = (regs[10] - items) // 4
    need(steps == 128 and regs[10] == items + steps * 4 and
         regs[2] == count - steps and regs[0] == 128 and
         regs[11] == pixel_base == 0x082A0508 and regs[12] == 0x03001828 and
         regs[15] == 0x030002A0, "exact native loop progress")

    # The renderer is an original ROM-to-IWRAM DMA copy, not decompressed code.
    need(u32(rom, 0x18C) == 0xE59F4208 and u32(rom, 0x39C) == 0x08012C58 and
         u32(rom, 0x194) == 0xE3A04060 and u32(rom, 0x12C50) == 0x03000204,
         "native boot copy and renderer entry")
    need(sha(rom[0x12C58:0x12DD8]) ==
         "D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685",
         "complete copied native renderer")
    need(u32(rom, 0x12DBC) == 0x03001428 and
         u32(rom, 0x12CF4) == 0xE1CC30B0 and
         u32(rom, 0x12D98) == 0xE28CC008 and
         u32(rom, 0x12DA0) == 0xE28AA004 and
         u32(rom, 0x12DA4) == 0xE2522001, "OAM store and loop consumers")
    need(0x03000200 + (0x12CF4 - 0x12C58) + 4 == regs[15],
         "watch PC is immediately after the attr0 store")
    return {
        "schema": 1,
        "status": "PASS",
        "bad_rom_sha256": BAD_SHA256,
        "probe_sha256": PROBE_SHA256,
        "runtime_endpoint_verified": True,
        "runtime_loaded_rom_identity": "sample verification, not a complete loaded-ROM hash",
        "callback": {"selector": 13, "literal_raw": literal_raw, "view": view,
                     "row_raw": row_raw, "p0": p0, "p1": p1, "p2": p2},
        "malformed_frame": {"table": table, "frame": frame, "entry_raw": entry_raw,
                            "count": count, "items": items, "pixel_base": pixel_base},
        "loop": {"completed_steps": steps, "remaining_count": regs[2],
                 "current_items": regs[10], "oam_count": regs[0],
                 "oam_pointer": regs[12], "watch_pc": regs[15]},
        "native_renderer": {"rom": 0x08012C58, "iwram": 0x03000200,
                            "copy_bytes": 0x180, "call_entry": 0x03000204,
                            "oam_base": 0x03001428},
        "conclusion": "wrong opening resource row causes the observed native OAM overflow",
        "not_claimed": ["complete opening/source parity", "later Shoot runtime success",
                        "a proof that any arbitrary multi-object OAM aggregate is bounded"],
        "provided_save_accessed": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("rom", type=pathlib.Path)
    p.add_argument("probe", type=pathlib.Path)
    p.add_argument("report", type=pathlib.Path)
    a = p.parse_args()
    need(all(x.suffix.lower() != ".sav" for x in (a.rom, a.probe, a.report)), "save paths forbidden")
    report = analyze(a.rom.read_bytes(), a.probe.read_bytes())
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[opening-renderer-overflow] " + report["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
