#!/usr/bin/env python3
"""Read-only evidence for the native Options/language/persistence boundary.

Reads three pinned ROMs and one candidate. No save, emulator, patch builder,
font, or guest memory is accessed. Optional previews decode the actual static
P0/P1 atlases; they are resource views, not screenshots of running software.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
RECORD = 0x03001120
INPUT_HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
UNCHANGED_RANGES = (
    ("cold_configuration", 0x158CC, 0x15970),
    ("mode_dispatch", 0x15AB4, 0x15D31),
    ("record_read_reset_normalize_transfer", 0x1F894, 0x1FD30),
    ("title_labels", 0x8FC58, 0x90898),
    ("both_options_assets", 0x9F980, 0xA1060),
    ("options_tasks_and_input", 0xC15C4, 0xC3B24),
    ("sprite_event_and_frame_consumers", 0x124CC, 0x12DD8),
)
NATIVE_WORDS = {
    0xC15F4: 0xE3B00001, 0xC1824: 0xE3B00001,
    0xC32B8: 0xE3A02004, 0xC32C4: 0xE3520004,
    0xC32FC: 0xE3580004, 0xC33F4: 0x000001FB,
    0xC3344: 0x03001306, 0xC3348: 0x0300130A,
    0xC334C: 0x03004738, 0xC3350: 0x080C3354,
    0xC38E0: 0xE3510002, 0xC3A90: 0xE3510002,
    0x15930: 0xE1C101B0, 0x15934: 0xE5C1000F,
    0x1F8C8: 0xE3A02008, 0x1F904: 0xE3A02010,
    0x1FC64: 0xE3A02019, 0x1FCAC: 0xE3A02019,
    0x1FD14: 0xE3A0A0C0, 0x1FC6C: 0xE58190C0,
    0x1FCA4: RECORD, 0x1FD04: RECORD,
    0x1FD08: RECORD + 0xC0, 0x1FD2C: RECORD,
    0xC1780: 0x080A05B8, 0xC1784: 0x080A1038,
    0x15C18: 0x080C15C4, 0x15C1C: 0x080C17B0,
}
SOURCE_OPTIONS = (
    (0x3B4299, "33c0e4cd24013d0000752e", 0x775679, "33c033c03d0000752e"),
    (0x3B4438, "33c0e4cd24013d0000750a", 0x775816, "33c033c03d0000750a"),
    (0x3C5BD2, "33c0e4cd24010bc07435", 0x786202, "33c033c00bc07435"),
)
WSC10_MASKED_READS = (
    0x3972AB, 0x39C486, 0x39FDC1, 0x39FDEC, 0x39FE13, 0x3B2594,
    0x3B429B, 0x3B443A, 0x3B5C49, 0x3B5EC0, 0x3B5FA3, 0x3B6032,
    0x3B740E, 0x3B8A49, 0x3BB8DA, 0x3BC24B, 0x3BCA31, 0x3BE8FC,
    0x3C263A, 0x3C2817, 0x3C2851, 0x3C2878, 0x3C2918, 0x3C5BD4,
    0x3C5C64, 0x3C5D0D,
)
RECORD_BASE_LOADS = {
    0x15948: (0x1596C, "unlocks +10/+12 copied to configuration"),
    0x1CCD8: (0x1CE9C, "high-score display, record +14"),
    0x1CF4C: (0x1D158, "high-score task, record +14"),
    0x1F8B0: (0x1FA08, "first eight signature bytes"),
    0x1F8E8: (0x1FA0C, "whole payload reset and sixteen-byte header initialization"),
    0x1FA1C: (0x1FA94, "count +64 and entries +66"),
    0x1FA9C: (0x1FBC8, "normalization at +10 and later"),
    0x1FBE4: (0x1FC50, "optional unlock synchronization at +10"),
    0x1FBF8: (0x1FC54, "record transfer pointer"),
    0x1FC10: (0x1FC58, "whole payload clear after failed read"),
    0x1FC68: (0x1FCA4, "checksum store and 25-block write"),
    0x1FCB0: (0x1FD04, "25-block read"),
    0x1FD0C: (0x1FD2C, "sum all C0 payload bytes"),
    0x8B458: (0x8B490, "record +64"),
    0x8B564: (0x8B5E4, "record +BE"),
    0xC17B4: (0xC1884, "record +64, immediately overridden to zero"),
    0x33ED8C: (0x33EE1C, "record +8E+2+fighterID*4"),
}
ASSETS = (
    ("options-japanese", 0x9F980, 0xA02E8, 0xA05B8, 12, 50),
    ("options-english", 0xA05E0, 0xA0D68, 0xA1038, 12, 34),
    ("title-menu-labels", 0x8FD08, 0x8FC58, 0x90878, 5, 77),
)


def need(test: bool, message: str) -> None:
    if not test:
        raise ValueError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def u16(data: bytes, at: int) -> int:
    return struct.unpack_from("<H", data, at)[0]


def u32(data: bytes, at: int) -> int:
    return struct.unpack_from("<I", data, at)[0]


def hits(data: bytes, pattern: bytes) -> list[int]:
    out, at = [], 0
    while (at := data.find(pattern, at)) >= 0:
        out.append(at)
        at += 1
    return out


def pointer(data: bytes, at: int) -> int:
    raw = u32(data, at) - BASE
    need(0 <= raw < len(data), f"ROM pointer at {at:X}")
    return raw


def literal_target(data: bytes, at: int) -> int:
    word = u32(data, at)
    need(word & 0x0F7F0000 == 0x051F0000, f"ARM immediate PC-relative LDR at {at:X}")
    return at + 8 + ((word & 0xFFF) if word & 0x800000 else -(word & 0xFFF))


def native_guards(data: bytes) -> None:
    for at, expected in NATIVE_WORDS.items():
        need(u32(data, at) == expected, f"native contract at {at:X}")
    need(data[0x1F9D4:0x1F9E4] == b"DIMPS Ver0.72   ", "default record header")
    need(data[0x15CC8 + 3 * 5:0x15CC8 + 4 * 5] == bytes((4, 4, 14, 2, 19)),
         "title mode-three five-way transitions")
    for instruction, (literal, _) in RECORD_BASE_LOADS.items():
        need(literal_target(data, instruction) == literal and u32(data, literal) == RECORD,
             f"record base load {instruction:X}")


def decode_asset(data: bytes, spec: tuple) -> dict:
    name, p0, p1, p2, expected_events, expected_tiles = spec
    table, descriptors = pointer(data, p0), pointer(data, p0 + 4)
    need(u16(data, p0 + 14) == 8, f"{name} is static-atlas P0")
    tile_bytes, pixels = u32(data, descriptors), pointer(data, descriptors + 4)
    need(tile_bytes == expected_tiles * 32, f"{name} tile byte count")
    event_table = pointer(data, p1)
    first_payload = pointer(data, event_table + 4)
    need(first_payload - event_table == expected_events * 16, f"{name} event geometry")
    events, layouts = [], {}
    for event in range(expected_events):
        count = u16(data, event_table + event * 16)
        commands = pointer(data, event_table + event * 16 + 4)
        need(1 <= count <= 10, f"{name} frame population")
        ids = []
        for frame in range(count):
            layout = u16(data, commands + frame * 16 + 2)
            need(layout < 64, f"{name} layout bound")
            ids.append(layout)
            if layout in layouts:
                continue
            parts = u32(data, table + layout * 8)
            source = pointer(data, table + layout * 8 + 4)
            need(0 < parts <= 128, f"{name} part count")
            entries = []
            for j in range(parts):
                tile, y, x = struct.unpack_from("<Hbb", data, source + j * 4)
                need(tile & 0x3FFF < expected_tiles, f"{name} atlas tile index")
                entries.append({"tile_flags": tile, "x": x, "y": y})
            layouts[layout] = {"layout": layout, "parts_raw": source,
                               "parts": parts, "entries": entries}
        events.append({"event": event, "frame_count": count,
                       "commands_raw": commands, "layouts": ids})
    return {"name": name, "p0_raw": p0, "p1_raw": p1, "p2_raw": p2,
            "p0_header_hex": data[p0:p0 + 16].hex().upper(),
            "palette_header_and_colors_hex": data[p2:p2 + 38].hex().upper(),
            "atlas_pixels_raw": pixels, "atlas_bytes": tile_bytes,
            "atlas_tiles": expected_tiles, "atlas_sha256": sha(data[pixels:pixels + tile_bytes]),
            "event_count": expected_events, "layout_count": len(layouts),
            "max_parts_one_frame": max(x["parts"] for x in layouts.values()),
            "events": events, "layouts": [layouts[k] for k in sorted(layouts)],
            "bound_scope": "one resource frame; not a whole-screen OAM aggregate"}


def render_asset(data: bytes, asset: dict, output: Path, all_frames: bool = False) -> dict:
    from PIL import Image, ImageDraw
    scale = 3
    layouts = {x["layout"]: x for x in asset["layouts"]}
    frames = [(event["event"], index, layouts[layout])
              for event in asset["events"]
              for index, layout in enumerate(event["layouts"])
              if all_frames or index == 0]
    # Complete previews must include tall decorative sprites and every value
    # frame; the historical first-frame preview remains byte-reproducible.
    row_height, width, left = 40, 304, 28
    if all_frames:
        left = 48
        row_height = max(40, max((max(p["y"] for p in frame["entries"]) -
                                 min(p["y"] for p in frame["entries"]) + 8) * scale + 8
                                for _, _, frame in frames))
        width = max(width, max((max(p["x"] for p in frame["entries"]) -
                                min(p["x"] for p in frame["entries"]) + 8) * scale + left + 4
                               for _, _, frame in frames))
    image = Image.new("RGB", (width, len(frames) * row_height), (25, 25, 25))
    pen = ImageDraw.Draw(image)
    for row, (event_id, frame_id, layout) in enumerate(frames):
        y0 = row * row_height
        label = f"{event_id}:{frame_id}" if all_frames else str(event_id)
        pen.text((4, y0 + 12), label, fill=(200, 200, 200))
        min_x = min(p["x"] for p in layout["entries"])
        min_y = min(p["y"] for p in layout["entries"])
        for part in layout["entries"]:
            flags = part["tile_flags"]
            tile_raw = asset["atlas_pixels_raw"] + (flags & 0x3FFF) * 32
            for yy in range(8):
                for xx in range(8):
                    sx, sy = (7 - xx if flags & 0x4000 else xx), (7 - yy if flags & 0x8000 else yy)
                    packed = data[tile_raw + sy * 4 + sx // 2]
                    color = (packed >> (4 * (sx & 1))) & 15
                    if color:
                        px = left + (part["x"] - min_x + xx) * scale
                        py = y0 + 4 + (part["y"] - min_y + yy) * scale
                        shade = min(255, 55 + color * 13)
                        pen.rectangle((px, py, px + scale - 1, py + scale - 1), fill=(shade,) * 3)
    output.mkdir(parents=True, exist_ok=True)
    path = output / (asset["name"] + ("-all-frames" if all_frames else "") + ".png")
    image.save(path)
    return {"name": path.name, "sha256": sha(path.read_bytes()),
            "kind": "static-ROM-resource " + ("all-frames" if all_frames else "first-frame") + " preview, grayscale"}


def analyze(gba: bytes, w10: bytes, w15: bytes, candidate: bytes) -> dict:
    for name, data in (("gba", gba), ("wsc10", w10), ("wsc15", w15)):
        need(sha(data) == INPUT_HASHES[name], f"pinned {name} original")
    need(len(candidate) >= len(gba), "candidate ROM length")
    native_guards(gba)
    native_guards(candidate)
    ranges = []
    for name, lo, hi in UNCHANGED_RANGES:
        need(gba[lo:hi] == candidate[lo:hi], f"candidate preserves {name}")
        ranges.append({"name": name, "raw_start": lo, "raw_end_exclusive": hi,
                       "sha256": sha(gba[lo:hi])})
    need(hits(w10, bytes.fromhex("e4cd2401")) == list(WSC10_MASKED_READS), "WSC10 masked language reads")
    need(not hits(w15, bytes.fromhex("e4cd2401")), "WSC15 has no exact masked language-read sequence")
    source = []
    for old, oldhex, new, newhex in SOURCE_OPTIONS:
        need(w10[old:old + len(oldhex)//2] == bytes.fromhex(oldhex), "commercial source language branch")
        need(w15[new:new + len(newhex)//2] == bytes.fromhex(newhex), "WSC15 fixed source language branch")
        source.append({"old_raw": old, "old_hex": oldhex.upper(), "new_raw": new, "new_hex": newhex.upper()})
    # Inventory every byte-aligned ROM word into the native record. This is an
    # encoded-reference denominator, not arbitrary computed-pointer exclusion.
    inventories = {}
    base_load_populations = {}
    for name, data in (("commercial", gba), ("candidate", candidate)):
        refs = []
        for offset in range(0xC8):
            for at in hits(data, struct.pack("<I", RECORD + offset)):
                refs.append({"raw": at, "record_offset": offset, "word_aligned": at % 4 == 0})
        inventories[name] = sorted(refs, key=lambda x: x["raw"])
        loads = []
        for at in range(0, len(data) - 3, 4):
            word = u32(data, at)
            if word & 0x0F7F0000 != 0x051F0000:
                continue
            literal = literal_target(data, at)
            if 0 <= literal <= len(data) - 4 and u32(data, literal) == RECORD:
                loads.append(at)
        need(loads == sorted(RECORD_BASE_LOADS), f"{name} complete encoded base-LDR population")
        base_load_populations[name] = loads
    assets = [decode_asset(gba, spec) for spec in ASSETS]
    selector_words = bytes.fromhex("0100B0E3000050E3")
    constant_choices = [x for x in hits(gba, selector_words) if x % 4 == 0]
    need(constant_choices == [0x895A4, 0x89A88, 0x89B98, 0xBB44C, 0xC15F4, 0xC1824],
         "native exact constant-branch pattern population")
    return {
        "schema": 1, "status": "PASS", "input_sha256": INPUT_HASHES,
        "candidate_sha256": sha(candidate), "unchanged_native_ranges": ranges,
        "guarded_native_words": [{"raw": k, "word_hex": f"{v:08X}"} for k, v in sorted(NATIVE_WORDS.items())],
        "language_source": {"wsc10_masked_in_cd_reads": list(WSC10_MASKED_READS),
            "wsc15_exact_sequence_count": 0, "paired_options_and_error_branches": source,
            "native_exact_constant_branches": constant_choices,
            "scope": "three paired fixed branches and exact-encoding inventories; not every language observer"},
        "options": {"mode": 14, "initializer": 0x080C15C4, "task_constructor": 0x080C17B0,
            "japanese_constructor": 0x080C1894, "english_constructor": 0x080C2564,
            "input_callback": 0x080C3234, "cursor_state": 0x03004738,
            "cursor_offset": 6, "previous_cursor_offset": 8, "rows": 5, "return_row": 4,
            "up": 1, "down": 4, "left": 8, "right": 2, "confirm": 0x40, "cancel": 0x80,
            "exit_callback": 0x080C3354, "retirement_state": 0x0300473C, "retirement_mask": 0x1FB,
            "time_callback": 0x080C37EC, "time_owner": 0x03002320, "time_range": [0, 2],
            "level_callback": 0x080C3998, "level_owner": 0x0300231F, "level_range": [0, 2],
            "time_and_level_cold_default": 1, "existing_language_row": False},
        "assets": assets,
        "record": {"base": RECORD, "payload_bytes": 0xC0, "checksum_offset": 0xC0,
            "checksum_algorithm": "unsigned byte sum across exactly C0 payload bytes",
            "transferred_bytes": 0xC8, "eight_byte_blocks": 25, "signature_compare_bytes": 8,
            "default_header_hex": gba[0x1F9D4:0x1F9E4].hex().upper(),
            "reset": 0x0801F894, "normalize": 0x0801FA98, "wrapper": 0x0801FBD0,
            "writer": 0x0801FC5C, "reader": 0x0801FCA8, "checksum": 0x0801FD0C,
            "write_status": "r0 == 0 success; nonzero native write failure must remain observable",
            "base_load_consumers": [{"instruction": k, "literal": v[0], "observed_use": v[1]}
                                    for k, v in sorted(RECORD_BASE_LOADS.items())],
            "all_byte_aligned_encoded_record_pointers": inventories,
            "all_aligned_arm_literal_loads_of_record_base": base_load_populations,
            "pointer_inventory_limitation": "does not prove absence of arbitrary computed aliases",
            "proposed_language_padding_offset": 0x0F,
            "proposal": "tagged A0..A3; legacy20/invalid tag defaults English; not adopted",
            "preserved_header_if_adopted_hex": gba[0x1F9D4:0x1F9E3].hex().upper()},
        "next_implementation_boundary": [
            "New sixth Language row: construct/display/input, reflow all row coordinates, retire its task",
            "Four-way resource dispatch; preserve the two existing static atlases and exact native constructors",
            "Independent review of the proposed padding owner and reset/load/save error behavior",
            "Build Korean and user-chart Digicode P0/P1 resources after active OAM/VRAM budgets are closed",
            "Map the remaining title, errors, results and gameplay language consumers",
            "Invisible fresh-data switching/persistence tests, never the supplied save"],
        "rom_changed": False, "provided_save_accessed": False, "runtime_launched": False,
        "font_adopted": False, "four_language_feature_complete": False,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    for arg in ("gba", "wsc10", "wsc15", "candidate", "report"):
        p.add_argument(arg, type=Path)
    p.add_argument("--render-directory", type=Path)
    p.add_argument("--all-frames", action="store_true",
                   help="render every event frame with complete sprite bounds")
    a = p.parse_args()
    need(a.gba.suffix.lower() == a.candidate.suffix.lower() == ".gba", "GBA paths only")
    need(a.wsc10.suffix.lower() == a.wsc15.suffix.lower() == ".wsc", "WSC paths only")
    need(a.report.suffix.lower() == ".json", "JSON report only")
    gba, w10, w15, candidate = (x.read_bytes() for x in (a.gba, a.wsc10, a.wsc15, a.candidate))
    report = analyze(gba, w10, w15, candidate)
    if a.render_directory:
        report["resource_previews"] = [render_asset(gba, x, a.render_directory, a.all_frames) for x in report["assets"]]
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[language-consumers] PASS: five native rows; two static option atlases; persistence proposal only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
