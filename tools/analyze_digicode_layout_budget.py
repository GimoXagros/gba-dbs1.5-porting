#!/usr/bin/env python3
"""Exhaust all native frame choices for a proposed four-language Options row.

This is a read-only layout calculation from existing decoded/verified inputs,
not proof that a fourth-mode ROM or its error-state transition is installed.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from math import prod
from pathlib import Path

from build_options_korean_poc import pack_tile
from digicode_glyphs import CATALOG, font_glyphs, text_pixels
from verify_digicode_glyphs import need, verify as verify_font


EVENTS = (0, 2, 4, 6, 7, 1, 8, 3, 8, 8, 5, 5, 8, 11, 9)
TEXT_FRAMES = {(0, 0), (2, 0), (3, 0), (3, 1), (3, 2), (4, 0), (6, 0), (7, 0), (11, 0), (11, 1)}
GBA_SHA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"


def native_counts(asset):
    need(all(row["parts"] == len(row["entries"]) for row in asset["layouts"]), "Complete native layout inventory")
    return {row["layout"]: row["parts"] for row in asset["layouts"]}


def analyze(native, korean, selector):
    need(native["input_sha256"]["gba"] == GBA_SHA and selector["original_sha256"] == GBA_SHA,
         "Known retail consumer inventory")
    assets = {row["name"]: row for row in native["assets"]}
    ja, en = assets["options-japanese"], assets["options-english"]
    counts = {"en": native_counts(en), "ja": native_counts(ja),
              "ko": native_counts(ja), "dg": native_counts(ja)}
    ko = korean["resource"]
    need(ko["active_budget"]["events"] == list(EVENTS), "All fifteen original native presentations retained")
    need({(row["event"], row["frame"]) for row in ko["frames"]} == TEXT_FRAMES, "Exact Korean frame set")
    for row in ko["frames"]:
        layout = ja["events"][row["event"]]["layouts"][row["frame"]]
        need(layout == row["layout"], "Korean layout identity")
        counts["ko"][layout] = row["parts"]

    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    glyphs = font_glyphs(catalog)
    font_report = verify_font(catalog, glyphs)

    def parts(reading):
        pixels, width = text_pixels(reading, catalog, glyphs)
        return width, sum(any(pack_tile(pixels, x, y)) for y in (-15, -7) for x in range(0, width, 8))

    draft = json.loads((CATALOG.parent / "options-draft.json").read_text(encoding="utf-8"))["entries"]
    need({(row["event"], row.get("frame", 0)) for row in draft} == TEXT_FRAMES, "Exact Digicode frame set")
    dg_frames = []
    native_layouts = {row["layout"]: row for row in ja["layouts"]}
    for row in draft:
        event, frame = row["event"], row.get("frame", 0)
        layout = ja["events"][event]["layouts"][frame]
        label = event in (0, 2, 4, 6, 7)
        marker = [part for part in native_layouts[layout]["entries"] if part["x"] == 0 and part["tile_flags"] == 27]
        if label:
            need(len(marker) == 1, "Every original row square is retained")
        width, tiles = parts(row["ja_reading"])
        need(width <= (72 if label else 40), "Complete native text width")
        counts["dg"][layout] = tiles + int(label)
        dg_frames.append(dict(event=event, frame=frame, reading=row["ja_reading"], width=width,
                              parts=tiles + int(label), original_square_retained=label))

    existing_frames = {(row["event"], row["frame"]): row for row in selector["selector_resource"]["frames"]}
    need(set(existing_frames) == set(product(range(3), repeat=2)), "Exact EN/JA/KO predecessor selector frames")
    labels = [existing_frames[0, i]["parts"] - 1 for i in range(3)] + [parts("げんご")[1]]
    names = [existing_frames[1, i]["parts"] for i in range(3)] + [parts("デジコード")[1]]
    errors = [existing_frames[2, i]["parts"] for i in range(3)] + [parts("ほぞんエラー")[1]]
    arrows = (1, 2, 2, 1)
    result = []
    for index, language in enumerate(("en", "ja", "ko", "dg")):
        asset = en if language == "en" else ja
        choices = [[counts[language][layout] for layout in asset["events"][event]["layouts"]] for event in EVENTS]
        totals = Counter(sum(combination) for combination in product(*choices))
        need(sum(totals.values()) == prod(map(len, choices)), "Every frame combination is covered")
        need(max(totals) == sum(map(max, choices)), "Exhaustion agrees with conservative per-object maximum")
        states = [{"state": "selected-" + selected, "row_parts": labels[index] + names[i] + arrows[i]}
                  for i, selected in enumerate(("en", "ja", "ko", "dg"))]
        states.append({"state": "save-error-replaces-new-row", "row_parts": errors[index]})
        for state in states:
            state["maximum_oam"] = max(totals) + state["row_parts"]
            state["maximum_tile_bytes"] = state["maximum_oam"] * 32
            need(all(total + state["row_parts"] <= 127 for total in totals), "Whole-screen capacity: " + language + " " + state["state"])
        result.append(dict(language=language, native_objects=15, original_max_parts_by_object=list(map(max, choices)),
                           original_max_parts=max(totals), frame_combinations=sum(totals.values()),
                           checked_combination_states=sum(totals.values()) * len(states), states=states,
                           peak_oam=max(state["maximum_oam"] for state in states),
                           rejected_error_plus_label_peak=max(totals) + errors[index] + labels[index]))
    need([row["original_max_parts"] for row in result] == [80, 73, 107, 110], "Expected four native-screen bounds")
    need(max(row["peak_oam"] for row in result) == 127, "Exact proposed whole-screen peak")
    return {"status": "PASS", "scope": "proposed composition only; no ROM/rendered/failure-state implementation claim",
            "proposal": {"new_row_square": "omitted consistently in all four languages; original five squares retained",
                         "normal_row": "label plus full selected name and endpoint-sensitive arrows",
                         "error_row": "full localized save-error text replaces label/name/arrows until next input",
                         "clipping": False, "original_native_objects_removed": 0},
            "digicode_font_pixels_sha256": font_report["pixels_sha256"], "digicode_frames": dg_frames,
            "languages": result, "peak_oam": 127, "peak_tile_bytes": 4064,
            "checked_combination_states": sum(row["checked_combination_states"] for row in result)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("native_analysis", type=Path)
    parser.add_argument("korean_manifest", type=Path)
    parser.add_argument("selector_manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    paths = (args.native_analysis, args.korean_manifest, args.selector_manifest)
    report = analyze(*(json.loads(path.read_text(encoding="utf-8")) for path in paths))
    report["input_sha256"] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "peak_oam", "peak_tile_bytes", "checked_combination_states")}))


if __name__ == "__main__":
    main()
