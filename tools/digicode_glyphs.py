#!/usr/bin/env python3
"""Original bounded pixel transcription of the supplied Digicode alphabet.

This is a development font draft, not an adopted third-party SVG/font. The
integer paths below are hand placed on a seven-column grid. The user chart
defines identity; local web references were used only to inspect topology.
See records/digicode-glyphs.md for provenance and the remaining review limits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from encode_digicode_reading import CATALOG, encode


# Body coordinates are 0..6 by 0..9; rows 0..4 of the cell are reserved for
# voicing and separation. Semicolons start separate strokes, not pen joins.
# shortcut: some seven-column counters are one pixel, widen cells if native-size review finds ambiguous symbols.
BODIES = {
    "あ": "1,1 5,1 5,8 1,8 1,1",
    "い": "2,0 4,0 4,3 2,3 2,0;3,3 3,6;2,6 4,6 4,9 2,9 2,6",
    "う": "0,3 5,3 5,0 3,0 3,9 0,9 0,6",
    "え": "0,2 0,0 2,0 2,9 0,9 0,5 2,5 4,9 4,2;3,5 6,5 6,1",
    "お": "3,0 3,9 0,9 0,3 5,3 5,9 4,9 4,6 6,6",
    "か": "2,0 2,9;4,5 4,3 6,3 6,9 0,2 0,7 5,1",
    "き": "2,7 0,6 2,4 2,0 4,3 6,1 4,6 4,9 6,7",
    "く": "2,6 2,0 4,2 0,6 2,9;5,5 5,9;4,6 6,8;4,8 6,6",
    "け": "0,3 0,0 3,0 0,8 3,8;3,6 3,4 5,4 5,9",
    "こ": "1,0 5,0;2,1 4,1;3,2 3,3;1,4 5,4;1,6 5,6;3,7 3,7;2,8 4,8;1,9 5,9",
    "さ": "4,2 0,2 0,0 6,0 6,4 0,4 0,9 6,9 6,7 2,7",
    "し": "0,0 0,9 4,9 4,2 2,2 2,5 6,5",
    "す": "3,9 3,6 0,6 0,0 5,0 5,4 2,4 2,2 3,2 3,3",
    "せ": "1,0 1,6 3,6 3,2 5,2 5,9;0,4 6,4",
    "そ": "1,9 5,9 5,3 1,3 1,6 3,6 3,0",
    "た": "0,6 0,1 3,1 3,9 6,9 6,1;0,8 0,8",
    "ち": "0,2 5,2 5,5 0,5 0,9 5,9;1,0 1,4;3,0 3,4",
    "つ": "0,0 6,0 6,6 2,6 2,3 4,3 4,9 0,9 0,6",
    "て": "0,0 1,4 3,0 5,4 6,0;1,9 3,5 5,9",
    "と": "0,1 6,1 6,6 1,6 1,3 4,3 4,8 1,8;3,0 3,9",
    "な": "0,6 0,1 2,1 2,9 5,9 5,1 3,1 3,5 6,5;0,8 0,8",
    "に": "1,0 1,4;0,1 2,3;0,3 2,1;5,0 5,4;4,1 6,3;4,3 6,1;1,6 3,7 5,6;3,7 3,9",
    "ぬ": "0,0 0,6 3,6 3,3 1,3 1,9 4,9 4,7 6,7 6,4 4,4 4,0",
    "ね": "0,2 3,2 2,0 2,9 0,9 0,6 5,6 5,4 4,4 4,9 6,9 6,7",
    "の": "0,4 3,4 3,8 0,8 0,4;2,1 5,1 5,5 2,5 2,1",
    "は": "0,0 0,9;4,0 4,5 6,5 6,2 2,2 2,9 6,9",
    "ひ": "0,4 2,4 2,0 0,0 0,9 6,9 6,0 4,0 4,4 6,4",
    "ふ": "0,6 0,3 2,3 2,0 4,0;2,9 2,6 4,6 4,3 6,3",
    "へ": "2,0 0,0 0,4 2,4 2,9 0,9 3,2;5,4 5,9;4,5 6,8;4,8 6,5",
    "ほ": "0,0 0,9;3,0 3,5 6,5 6,9 2,9 2,2 4,2 4,6",
    "ま": "3,0 3,6 5,6 5,2 1,2 1,9 5,9",
    "み": "0,2 4,2;2,0 2,7 0,7 0,4 3,4 6,9 6,3 2,9",
    "む": "3,6 3,0 5,4 1,4 1,9 5,9 5,5",
    "め": "2,4 4,4 4,7 2,7 2,4;0,6 0,9 6,9 6,6;1,0 2,2;3,0 3,2;5,0 4,2",
    "も": "0,5 6,5;1,0 1,9 5,9 5,0 3,0 3,3 6,3",
    "や": "1,4 1,0 4,0 1,9 6,9 6,4 4,4 4,6",
    "ゆ": "0,7 5,0 5,7 1,7 1,0 3,0 3,9 1,9",
    "よ": "0,6 0,9 2,9 2,0;5,0 5,3;4,1 6,3;4,3 6,1;5,6 5,9;4,6 6,8;4,8 6,6",
    "ら": "0,2 4,2;2,0 2,6 0,6 0,3 6,6 6,3 4,3 4,9 0,9 0,7 2,7 2,8",
    "り": "2,9 0,9 0,0 2,0 2,1 0,4 2,4 2,5 0,8;6,9 4,9 4,0 6,0 6,1 4,4 6,4 6,5 4,8",
    "る": "0,9 3,5 3,0 1,0 1,5 4,9 6,6 6,3 4,3 4,6 6,9",
    "れ": "0,2 3,2 2,0 2,9 0,9 0,5 5,9 5,0 4,2 6,2 6,1",
    "ろ": "0,9 2,5 2,0 0,0 0,5 3,9 5,5 5,0 3,0 3,5 6,9 6,5",
    "わ": "0,2 5,2 2,0 2,9 0,9 0,5 5,9 5,6",
    "を": "0,0 0,9 3,9 3,2 1,2 1,7 3,7 5,4 6,4;5,1 5,7",
    "ん": "0,0 6,0 6,9 0,9 0,0;3,2 3,7;1,3 5,7;1,7 5,3",
    "ー": "0,5 6,5;4,3 6,5 4,7",
    "A": "3,9 0,9 0,0 6,9",
    "B": "0,0 6,0 6,9;1,0 6,7",
    "C": "0,9 0,0 6,0 6,7 2,7 2,0",
    "D": "0,0 6,9 6,0 0,9 0,0",
    "E": "0,2 1,2 1,0 5,0 5,2 6,2 6,6 0,6 0,2;1,9 2,9 2,6;5,9 4,9 4,6",
    "F": "0,9 0,0 6,0 6,2;2,7 5,7 5,4 0,4",
    "G": "6,0 4,3 2,3 0,0 0,9 2,6 4,6 6,9",
    "H": "0,0 0,9 3,6 6,6 6,3 3,3 0,0",
    "I": "0,0 2,2 2,7 0,9;6,9 4,7 4,2 6,0;1,5 5,5",
    "J": "3,0 3,9;0,0 1,3 5,3 6,0;2,9 4,9",
    "K": "2,0 6,0 6,7 2,7;5,2 0,2 0,9 5,9",
    "L": "6,2 6,0 0,0 0,5 6,5 6,9 0,9;3,4 3,9",
    "M": "0,6 0,9 3,9 3,0 6,0 6,4;2,5 4,5",
    "N": "0,9 0,0 6,0 6,6 0,6;6,9 3,9 3,0",
    "O": "0,0 0,2 2,2 2,7 0,7 0,9;6,0 6,2 4,2 4,7 6,7 6,9;2,4 4,4",
    "P": "1,2 3,0 5,2;0,9 1,7 3,9 5,7 6,9;3,0 3,9",
    "Q": "2,0 4,0;3,0 3,9;2,9 4,9;2,2 0,2 3,6 6,2 4,2",
    "R": "0,9 0,0 3,4 6,0 6,9;3,4 3,7;2,7 4,7",
    "S": "0,9 0,0 6,0;6,9 4,9 4,4 0,4",
    "T": "0,9 0,0 6,0 6,9;0,6 2,6 2,3 4,3 4,6 6,6;3,0 3,3",
    "U": "3,0 6,2 6,7 3,9 0,7 0,2 3,0;0,5 6,5;3,9 3,3 6,3",
    "V": "0,0 0,9;6,0 6,9;6,0 0,3;6,3 0,6",
    "W": "0,0 0,9 3,9;3,0 6,0 6,9;0,5 6,5",
    "X": "6,9 0,5 6,1;6,0 6,2",
    "Y": "0,0 6,0 6,5 0,5 0,0;1,7 1,9 5,9 5,7;3,9 3,5",
    "Z": "0,0 3,0 3,9 0,9 0,0;6,0 6,9;0,5 6,5",
}
VOICED = dict(zip("がぎぐげござじずぜぞだぢづでどばびぶべぼ", "かきくけこさしすせそたちつてとはひふへほ"))
SEMIVOICED = dict(zip("ぱぴぷぺぽ", "はひふへほ"))


def stroke_pixels(strokes):
    """Integer Bresenham strokes; the font geometry never reads a web asset."""
    points = set()
    for stroke in strokes.split(";"):
        vertices = [tuple(map(int, pair.split(","))) for pair in stroke.split()]
        if not vertices or any(not (0 <= x <= 6 and 0 <= y <= 9) for x, y in vertices):
            raise ValueError("Unbounded or empty pixel stroke")
        points.update(vertices)
        for (x, y), (end_x, end_y) in zip(vertices, vertices[1:]):
            dx, dy = abs(end_x - x), -abs(end_y - y)
            step_x, step_y = (1 if x < end_x else -1), (1 if y < end_y else -1)
            error = dx + dy
            while (x, y) != (end_x, end_y):
                twice = 2 * error
                if twice >= dy:
                    error += dy
                    x += step_x
                if twice <= dx:
                    error += dx
                    y += step_y
                points.add((x, y))
    return points


def font_glyphs(catalog):
    """Return the existing catalog IDs as exact 8x16 cell row bytes, MSB first."""
    glyphs = {}
    for glyph in catalog["glyphs"] + catalog["latin_glyphs"]:
        character = glyph.get("hiragana", glyph.get("uppercase"))
        base = VOICED.get(character, SEMIVOICED.get(character, character))
        if base not in BODIES:
            raise ValueError("No pixel transcription for " + repr(character))
        points = {(x, y + 5) for x, y in stroke_pixels(BODIES[base])}
        if character in VOICED:
            points.update(((1, 1), (2, 2), (5, 1), (4, 2)))
        elif character in SEMIVOICED:
            points.update(((3, 1), (2, 2), (4, 2), (3, 3)))
        rows = bytes(sum(128 >> x for x, py in points if py == y) for y in range(16))
        if glyph["id"] in glyphs:
            raise ValueError("Duplicate catalog glyph ID")
        glyphs[glyph["id"]] = rows
    return glyphs


def text_pixels(reading, catalog, glyphs, *, outline=True):
    """Return native palette pixels and width; baseline is the bottom at y=0.

    Trim blank side columns only, leaving one empty column between glyph ink.
    The maximum advance is eight pixels. Ink and the complete one-pixel edge
    are retained; native tiling can add a partial column to the whole string.
    """
    if not isinstance(reading, str) or not reading:
        raise ValueError("An explicit nonempty Japanese reading is required")
    ids = encode(reading, catalog)
    ink, cursor = set(), int(outline)
    for glyph_id in ids:
        if glyph_id not in glyphs:
            raise ValueError("Missing pixel glyph: " + glyph_id)
        rows = glyphs[glyph_id]
        if len(rows) != 16 or not any(rows):
            raise ValueError("Incomplete or empty pixel glyph: " + glyph_id)
        points = {(x, y - 15) for y, row in enumerate(rows) for x in range(8) if row & (128 >> x)}
        left, right = min(x for x, _ in points), max(x for x, _ in points)
        ink.update((cursor + x - left, y) for x, y in points)
        cursor += right - left + 2
    pixels = ({(x + dx, y + dy): 2 for x, y in ink
               for dx in (-1, 0, 1) for dy in (-1, 0, 1)} if outline else {})
    pixels.update({point: 1 for point in ink})
    if min(x for x, _ in pixels) < 0 or min(y for _, y in pixels) < -15 or max(y for _, y in pixels) > 0:
        raise ValueError("Pixel glyph escaped the documented cell/edge bounds")
    return pixels, max(x for x, _ in pixels) + 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="development bitmap JSON; never a ROM input by default")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    glyphs = font_glyphs(catalog)
    result = {"schema": 1, "status": "development-pixel-transcription-needs-chart-review",
              "source_language": "ja", "cell": [8, 16], "maximum_advance": 8,
              "spacing": "trim blank side columns; one clear column between glyph ink; full exterior outline",
              "row_encoding": "16 row bytes per glyph, MSB is x=0, index 1 ink; no outline stored",
              "catalog_sha256": hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
              "provenance": "Hand-placed integer pixel paths; see records/digicode-glyphs.md. No third-party font license claimed.",
              "glyphs": {key: rows.hex() for key, rows in glyphs.items()}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"glyphs": len(glyphs), "cell": result["cell"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
