#!/usr/bin/env python3
"""Independently check actual Digicode ROM pixels and all native frame budgets.

No font or ROM producer is imported. Pillow decodes the reviewed row bytes,
crops empty columns, and dilates the image for a separately implemented edge.
This does not emulate save-error transitions or claim whole-game localization.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import struct
import unicodedata

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
FONT_JSON_SHA = "ABDFB29C40C3C8F38BB64214B1F3695FED4774C32362A6ACC1F4EE5D90029EEA"
FONT_ROWS_SHA = "E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195"
RENDERER_SHA = "D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685"
GBA_SHA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def verify(rom, manifest, font_bytes, native_inventory):
    need(len(rom) == 0x800000 and sha(rom) == manifest["output_sha256"], "Exact complete candidate identity")
    need(manifest["original_sha256"] == native_inventory["input_sha256"]["gba"] == GBA_SHA,
         "Known original consumer inventory")
    need(sha(rom[0x12C58:0x12DD8]) == RENDERER_SHA, "Original renderer is intact")
    source = next(row for row in native_inventory["unchanged_native_ranges"] if row["name"] == "both_options_assets")
    need(sha(rom[source["raw_start"]:source["raw_end_exclusive"]]) == source["sha256"], "Original EN/JA assets are intact")
    need(sha(font_bytes) == FONT_JSON_SHA, "Exact reviewed bitmap artifact")
    font = json.loads(font_bytes)
    catalog = json.loads((ROOT / "localization/digicode-reference.json").read_text(encoding="utf-8"))
    glyphs = {key: bytes.fromhex(value) for key, value in font["glyphs"].items()}
    ids = [g["id"] for g in catalog["glyphs"] + catalog["latin_glyphs"]]
    need(len(ids) == len(set(ids)) == len(glyphs) == 98 and set(ids) == set(glyphs), "Exact 98 glyph identities")
    need(sha(b"".join(glyphs[key] for key in ids)) == FONT_ROWS_SHA, "Reviewed canonical glyph row digest")
    lookup = {g[key]: g["id"] for group, keys in (("glyphs", ("hiragana", "katakana")),
                                                 ("latin_glyphs", ("uppercase", "lowercase")))
              for g in catalog[group] for key in keys}

    def expected(reading):
        images = []
        for character in unicodedata.normalize("NFC", reading):
            need(character in lookup, "Unresolved Japanese reading")
            image = Image.frombytes("1", (8, 16), glyphs[lookup[character]]).convert("L")
            left, top, right, bottom = image.getbbox()
            need(top >= 1 and bottom <= 15, "Complete exterior edge fits sixteen rows")
            images.append(image.crop((left, 0, right, 16)))
        need(images, "Nonempty reading")
        width = 1 + sum(image.width + 1 for image in images)
        ink, x = Image.new("L", (width, 16)), 1
        for image in images:
            ink.paste(image, (x, 0))
            x += image.width + 1
        edge = ink.filter(ImageFilter.MaxFilter(3))
        return {(x, y - 15): (1 if ink.getpixel((x, y)) else 2)
                for y in range(16) for x in range(width) if edge.getpixel((x, y))}, width

    def u32(offset):
        need(0 <= offset <= len(rom) - 4, "Readable word")
        return struct.unpack_from("<I", rom, offset)[0]

    def pointer(offset):
        value = u32(offset) - 0x08000000
        need(0 <= value < len(rom), "In-ROM pointer")
        return value

    def decode(p0, count):
        table, descriptor = pointer(p0), pointer(p0 + 4)
        size, base = u32(descriptor), pointer(descriptor + 4)
        need(0 < size <= 8192 and size % 32 == 0 and base <= len(rom) - size, "Bounded complete tile pool")
        need(struct.unpack_from("<4H", rom, p0 + 8) == (5, size // 32 - 1, size - 32, 8), "Native P0 header")
        result = []
        for index in range(count):
            total, start = u32(table + index * 8), pointer(table + index * 8 + 4)
            need(0 < total <= 20 and start <= len(rom) - 4 * total, "Bounded complete part array")
            parts = [struct.unpack_from("<Hbb", rom, start + j * 4) for j in range(total)]
            pixels = {}
            for tile, top, left in parts:
                need(tile & 0x3FFF < size // 32 <= 256, "Source index fits the native low-byte lookup")
                for y in range(8):
                    sy = 7 - y if tile & 0x8000 else y
                    for x in range(8):
                        sx = 7 - x if tile & 0x4000 else x
                        value = rom[base + (tile & 255) * 32 + sy * 4 + sx // 2] >> (4 * (sx % 2)) & 15
                        if value:
                            pixels[left + x, top + y] = value
            result.append((parts, pixels))
        return result, base + size, size // 32

    def events(p1, count):
        table, result = pointer(p1), []
        for index in range(count):
            total, start = u32(table + 16 * index), pointer(table + 16 * index + 4)
            need(0 < total <= 32 and start <= len(rom) - total * 16, "Complete native event frames")
            result.append([struct.unpack_from("<H", rom, start + 16 * j + 2)[0] for j in range(total)])
        return result

    ja, _, _ = decode(0x9F980, 32)
    en, _, _ = decode(0xA05E0, 32)
    ko, _, _ = decode(0x632000, 32)
    dg, _, dg_tiles = decode(0x639000, 32)
    selector, p1, selector_tiles = decode(0x637000, 16)
    jp_events, en_events = events(0xA02E8, 12), events(0xA0D68, 12)
    need(events(p1, 4) == [list(range(i * 4, i * 4 + 4)) for i in range(4)], "Exact selector frame identity")
    draft = json.loads((ROOT / "localization/options-draft.json").read_text(encoding="utf-8"))["entries"]
    replaced = set()
    for row in draft:
        event, frame = row["event"], row.get("frame", 0)
        index = jp_events[event][frame]
        replaced.add(index)
        pixels, width = expected(row["ja_reading"])
        label = event in (0, 2, 4, 6, 7)
        need(width <= (72 if label else 40), "Unclipped text width")
        left = 8 if label else ((24 if event == 11 else 40) - width) // 2
        pixels = {(x + left, y): value for (x, y), value in pixels.items()}
        if label:
            pixels.update({point: value for point, value in ja[index][1].items() if point[0] < 8})
        need(dg[index][1] == pixels, f"Every Digicode text pixel {event}:{frame}")
    need(replaced == {0, 4, 5, 6, 7, 8, 19, 20, 30, 31}, "Exact ten translated frames")
    need(all(dg[i] == ja[i] for i in set(range(32)) - replaced), "All 22 original part lists and pixels retained")
    config = json.loads((ROOT / "localization/options-selector.json").read_text(encoding="utf-8"))
    for event, key in enumerate(("labels", "names", "save_errors")):
        pixels, width = expected(config[key][3])
        left = 8 if event == 0 else (56 - width) // 2
        need(selector[event * 4 + 3][1] == {(x + left, y): value for (x, y), value in pixels.items()},
             "Every Digicode selector label/name/error pixel, without a new square")
    need([len(selector[i][0]) for i in range(12, 16)] == [1, 2, 2, 1], "Endpoint-sensitive native arrow counts")

    constructor_events, object_calls = [], 0
    for address in range(0xC2564, 0xC315C, 4):
        instruction = u32(address)
        if instruction >> 24 != 0xEB:
            continue
        delta = (instruction & 0xFFFFFF) - (0x1000000 if instruction & 0x800000 else 0)
        target = address + 8 + delta * 4
        if target == 0x6334C0:
            object_calls += 1
        if target in (0x12874, 0x129C8):
            event_word = u32(address - (8 if target == 0x12874 else 12))
            need(event_word & 0xFFFFFF00 == 0xE3A08000, "Native event immediate")
            constructor_events.append(event_word & 255)
    need(object_calls == 15 and constructor_events == [0, 2, 4, 6, 7, 1, 8, 3, 8, 8, 5, 5, 8, 11, 9],
         "Recovered all fifteen actual routed constructor objects and native events")
    budgets = []
    for language, layouts, event_lists, label in (("en", en, en_events, 0), ("ja", ja, jp_events, 1),
                                                ("ko", ko, jp_events, 2), ("digicode", dg, jp_events, 3)):
        choices = [[len(layouts[index][0]) for index in event_lists[event]] for event in constructor_events]
        totals = Counter(sum(combination) for combination in product(*choices))
        row_costs = [len(selector[label][0]) + len(selector[4 + i][0]) + len(selector[12 + i][0]) for i in range(4)]
        row_costs.append(len(selector[8 + label][0]))
        need(all(total + cost <= 127 for total in totals for cost in row_costs), "Complete actual-ROM OAM budget")
        budgets.append(dict(language=language, native_objects=object_calls, maximum_parts_by_object=list(map(max, choices)),
                            base_max=max(totals), native_combinations=sum(totals.values()),
                            row_costs_selected_en_ja_ko_dg_error=row_costs, max_oam=max(totals) + max(row_costs)))
    need([row["max_oam"] for row in budgets] == [103, 91, 124, 127], "Exact reviewed four-language bounds")
    return dict(status="PASS", kind="independent-font-worker-actual-ROM-resource-review", rom_sha256=sha(rom),
                font_json_sha256=sha(font_bytes), font_compositor="Pillow row-byte image decoding, bounding-box crop, MaxFilter edge; no font or ROM producer imported",
                digicode_text_frames=10, unchanged_native_layouts=22, digicode_selector_frames=3,
                digicode_atlas_tiles=dg_tiles, selector_atlas_tiles=selector_tiles, budgets=budgets,
                native_frame_and_row_assignments=sum(row["native_combinations"] * 5 for row in budgets),
                original_assets_and_renderer_intact=True, original_common_heads_included=True,
                error_state_assumption="full error only; state-machine execution is root-owned",
                runtime_claim=False, save_accessed=False, whole_game_localization_complete=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("font_json", type=Path)
    parser.add_argument("native_inventory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = verify(args.rom.read_bytes(), json.loads(args.manifest.read_text(encoding="utf-8")),
                    args.font_json.read_bytes(), json.loads(args.native_inventory.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "rom_sha256": report["rom_sha256"],
                      "peak_oam": max(row["max_oam"] for row in report["budgets"]), "report_sha256": sha(args.output.read_bytes())}))


if __name__ == "__main__":
    main()
