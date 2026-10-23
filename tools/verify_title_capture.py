#!/usr/bin/env python3
"""Check one exact, naturally reached title snapshot without opening saves."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_native_capture_invariants import inspect


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def verify(directory, rom, gba, manifest):
    invariants = inspect(directory, gba)
    capture = json.loads((directory / "capture.json").read_text(encoding="utf-8"))
    need(capture["rom"]["sha256"] == sha(rom) == manifest["output_sha256"],
         "capture, actual ROM and title manifest identities match")
    need(manifest["kind"] == "development-five-event-title-language", "bounded title component")
    iwram, ewram, vram, oam = ((directory / name).read_bytes()
                             for name in ("iwram.bin", "ewram.bin", "vram.bin", "oam.bin"))
    u16 = lambda data, at: struct.unpack_from("<H", data, at)[0]
    s16 = lambda data, at: struct.unpack_from("<h", data, at)[0]
    u32 = lambda data, at: struct.unpack_from("<I", data, at)[0]
    need(u16(iwram, 0x2310) == 3, "stable native title mode")
    tag = iwram[0x112F]
    language = tag - 0xA0 if 0xA0 <= tag <= 0xA3 else 0
    info = manifest["resources"][language]
    need(info["language"] == ("en", "ja", "ko", "digicode")[language], "fixed language ordering")
    tasks = {}
    for slot in range(52):
        at = 0x10000 + slot * 0x118
        if u16(ewram, at + 0x10) & 2:
            priority = u32(ewram, at + 4)
            need(priority not in tasks, "unique live task priorities")
            tasks[priority] = u32(ewram, at)
    need(set(tasks) == {0, 0x1000, 0xFFFFF000} and u16(iwram, 0x1338) == 3,
         "exact native title task population")
    need(tasks[0] == 0x08015AB4 and tasks[0xFFFFF000] == 0x080914E4,
         "native mode controller and palette-only fade")
    callback = tasks[0x1000]
    need(callback in (0x08090C7C, 0x08090FA0), "stable prompt or settled menu, not a transition")
    objects = []
    for index in range(5):
        at = 0x2A78 + index * 0x50
        pointers = tuple(u32(iwram, at + offset) for offset in (0x44, 0x48, 0x4C))
        need(pointers == (0x0808FC58, 0x08000000 + info["p0_raw"], 0x08090878),
             "all five native presentations use the selected P0 and retained P1/P2")
        event, frame = u16(iwram, at + 0xE), u16(iwram, at + 0x18)
        need(event == frame == index, "exact native title event and layout")
        need(u16(iwram, at + 8) == 0x408 and u16(iwram, at + 0x1A) == 0,
             "retained presentation flags and sole P1 command index")
        row = 0x8FC60 + index * 16
        need(tuple(u32(iwram, at + offset) for offset in (0x20, 0x24, 0x28, 0x2C)) ==
             (u32(rom, row + 4), u32(rom, row + 4), u32(rom, row + 8), u32(rom, row + 12)),
             "actual command and auxiliary pointers match the native P1 event row")
        need(u16(iwram, at + 2) == (104, 36, 72, 108, 200)[index], "native title Y coordinates")
        objects.append(dict(address=0x03000000 + at, event=event, frame=frame,
                            x=s16(iwram, at), y=s16(iwram, at + 2)))
    active = invariants["enabled_objects_at_capture"]
    need(invariants["affine_objects_at_capture"] == 0 and
         active <= info["maximum_oam"] <= 127 and u16(iwram, 0x12D6) == active,
         "actual staging and hardware OAM fit the complete title population bound")
    if callback == 0x08090FA0:
        need(all(obj["x"] == 112 for obj in objects[1:]) and active == sum(info["parts"][1:]),
             "settled menu emits every part of all four objects, including offscreen D-ARK")
    else:
        need(objects[0]["x"] == 112 and active in (0, info["parts"][0]),
             "prompt emits its entire layout or its native blink hides it")
    need([u16(oam, at * 8 + 4) & 1023 for at in range(active)] == list(range(active)),
         "native tile-per-OAM sequence")
    need(vram[0x10000:0x10000 + active * 32] == ewram[:active * 32],
         "all active title tiles reached physical OBJ VRAM")
    return dict(status="PASS", rom_sha256=sha(rom),
                capture_manifest_sha256=sha((directory / "capture.json").read_bytes()),
                language=info["language"], record_tag=tag, native_presentations=objects,
                phase="menu" if callback == 0x08090FA0 else "prompt", sprites_visible=active > 0,
                enabled_oam=active, maximum_oam=info["maximum_oam"],
                native_staging_matches_hardware=True,
                scope="one exact native title snapshot; visual review, full transitions and complete localization are separate")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("directory", "rom", "gba", "manifest", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    need(all(path.suffix.lower() != ".sav" for path in vars(args).values()), "save paths forbidden")
    result = verify(args.directory, args.rom.read_bytes(), args.gba.read_bytes(),
                    json.loads(args.manifest.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
