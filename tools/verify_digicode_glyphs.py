#!/usr/bin/env python3
"""Check the bounded pixel draft and produce local review artifacts, not a ROM."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_options_korean_poc import pack_tile
from digicode_glyphs import BODIES, CATALOG, font_glyphs, stroke_pixels, text_pixels
from encode_digicode_reading import encode


def need(condition, message):
    if not condition:
        raise ValueError(message)


def expect_rejection(callback):
    try:
        callback()
    except ValueError:
        return
    raise ValueError("Unsupported or malformed input was accepted")


def duplicates(values):
    groups = defaultdict(list)
    for key, value in values.items():
        groups[value].append(key)
    return [ids for ids in groups.values() if len(ids) > 1]


def pixel_image(rows):
    image = Image.new("RGB", (8, 16), "white")
    for y, row in enumerate(rows):
        for x in range(8):
            if row & (128 >> x):
                image.putpixel((x, y), (0, 0, 0))
    return image


def verify(catalog, glyphs):
    expected = [g["id"] for g in catalog["glyphs"] + catalog["latin_glyphs"]]
    need(len(expected) == len(set(expected)) == 98 and set(glyphs) == set(expected), "Exact 98 catalog identities")
    need(len(BODIES) == 73, "47 Japanese base symbols and 26 Latin symbols")
    need(all(len(rows) == 16 and any(rows) and all(not row & 1 for row in rows)
             for rows in glyphs.values()), "Complete, nonempty, seven-column cell pixels")
    need(not duplicates(glyphs), "Two identities collapse to identical 8x16 bitmaps")
    # Independent fixtures check stroke stepping, the square, and voicing shape.
    need(stroke_pixels("0,0 3,3") == {(0, 0), (1, 1), (2, 2), (3, 3)}, "Diagonal stepping")
    need(stroke_pixels("3,3 0,0") == stroke_pixels("0,0 3,3"), "Reversed stroke")
    need(stroke_pixels("0,0 0,2;2,2 4,2") == {(0, 0), (0, 1), (0, 2), (2, 2), (3, 2), (4, 2)}, "Separate strokes")
    need(list(glyphs["jp-3042"]) == [0, 0, 0, 0, 0, 0, 124, 68, 68, 68, 68, 68, 68, 124, 0, 0], "Square fixture")
    for voiced, base in (("が", "か"), ("じ", "し"), ("で", "て"), ("ぼ", "ほ")):
        variant, plain = (glyphs[encode(ch, catalog)[0]] for ch in (voiced, base))
        need(variant[:5] == bytes((0, 68, 40, 0, 0)) and variant[5:] == plain[5:], "Exact voicing and preserved body")
    need(glyphs["jp-3071"][:5] == bytes((0, 16, 40, 16, 0)), "Semivoicing ring")
    for character, gaps in (("え", ((5, 2), (5, 3), (1, 7))),
                            ("ゆ", ((2, 1), (4, 5))),
                            ("ら", ((1, 5), (1, 8))),
                            ("り", ((1, 1), (1, 5), (5, 1), (5, 5)))):
        points = stroke_pixels(BODIES[character])
        need(all(gap not in points for gap in gaps), "Preserved topology gaps: " + character)
    for reading in ("", "ゃ", "小", "。", "1", "１", " ", "あ い", "ヴ"):
        expect_rejection(lambda: text_pixels(reading, catalog, glyphs))
    missing = dict(glyphs)
    del missing["jp-3042"]
    expect_rejection(lambda: text_pixels("あ", catalog, missing))
    missing["jp-3042"] = bytes(15)
    expect_rejection(lambda: text_pixels("あ", catalog, missing))
    missing["jp-3042"] = bytes(16)
    expect_rejection(lambda: text_pixels("あ", catalog, missing))
    need(text_pixels("か\u3099Aa", catalog, glyphs) == text_pixels("ガaA", catalog, glyphs), "Kana/case/NFC equivalence")
    need(encode("デジモンAa", catalog) == ["jp-3067", "jp-3058", "jp-3082", "jp-3093", "latin-a", "latin-a"], "Japanese and Latin source order")

    samples = json.loads((CATALOG.parent / "options-draft.json").read_text(encoding="utf-8"))["entries"]
    readings = [row["ja_reading"] for row in samples] + ["げんご", "デジコード", "ほぞんエラー", "あぐもん", "やがみたいち", "デジモンAa"]
    budgets = []
    for reading in readings:
        pixels, width = text_pixels(reading, catalog, glyphs)
        source_ink = sum(sum(row.bit_count() for row in glyphs[key]) for key in encode(reading, catalog))
        need(sum(value == 1 for value in pixels.values()) == source_ink, "Proportional spacing must not merge or drop ink")
        recovered, tiles = {}, []
        for top in (-15, -7):
            for left in range(0, width, 8):
                tile = pack_tile(pixels, left, top)
                if not any(tile):
                    continue
                tiles.append(tile)
                for y in range(8):
                    for x in range(8):
                        value = (tile[y * 4 + x // 2] >> ((x % 2) * 4)) & 15
                        if value:
                            recovered[(left + x, top + y)] = value
        need(recovered == pixels, "Native tile round trip or clipping: " + reading)
        budgets.append({"reading": reading, "glyphs": len(encode(reading, catalog)), "width": width,
                        "height": max(y for _, y in pixels) - min(y for _, y in pixels) + 1,
                        "parts": len(tiles), "tile_bytes": len(tiles) * 32})
    compact = {key: pixel_image(rows).resize((8, 8), Image.Resampling.NEAREST).tobytes()
               for key, rows in glyphs.items()}
    return {"status": "PASS", "scope": "catalog coverage, pixel bounds, noncollision, strict input, native 4bpp round trip; not authenticity or runtime proof",
            "glyphs": len(glyphs), "bitmap_bytes": sum(map(len, glyphs.values())), "maximum_advance": 8,
            "spacing": "blank columns trimmed; one clear column between glyph ink; full exterior edge",
            "outlined_native_tile_tops": [-15, -7], "duplicates_8x16": duplicates(glyphs),
            "naive_8x8_duplicates": duplicates(compact), "samples": budgets,
            "pixels_sha256": hashlib.sha256(b"".join(glyphs[key] for key in expected)).hexdigest()}


def review_artifacts(directory, catalog, glyphs, report, reference_directory):
    directory.mkdir(parents=True, exist_ok=True)
    label_font = ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 16)
    atlas = Image.new("RGB", (1200, 1200), (239, 241, 245))
    draw = ImageDraw.Draw(atlas)
    draw.text((12, 10), "Digicode pixel transcription / 8x16 enlarged 5x / 98 cells", font=label_font, fill="black")
    cells = []
    for index, entry in enumerate(catalog["glyphs"] + catalog["latin_glyphs"]):
        key = entry["id"]
        char = entry.get("hiragana", entry.get("uppercase"))
        x, y = index % 10 * 120, index // 10 * 114 + 44
        draw.rectangle((x + 4, y, x + 115, y + 108), fill="white")
        draw.text((x + 8, y + 4), char + " " + key, font=label_font, fill="black")
        atlas.paste(pixel_image(glyphs[key]).resize((40, 80), Image.Resampling.NEAREST), (x + 40, y + 26))
        cells.append((char, key))
    atlas.save(directory / "pixel-atlas.png")
    sample_image = Image.new("RGB", (780, 100 + 60 * len(report["samples"])), (48, 56, 76))
    pen = ImageDraw.Draw(sample_image)
    pen.text((12, 10), "Original Japanese readings / native ink=black, edge=white / 3x", font=label_font, fill="white")
    for index, sample in enumerate(report["samples"]):
        reading = sample["reading"]
        pixels, width = text_pixels(reading, catalog, glyphs)
        row = Image.new("RGB", (width, 16), (48, 56, 76))
        for (x, y), value in pixels.items():
            row.putpixel((x, y + 15), (0, 0, 0) if value == 1 else (255, 255, 255))
        y = 48 + index * 60
        pen.text((12, y + 8), f'{reading} ({sample["parts"]} parts)', font=label_font, fill="white")
        sample_image.paste(row.resize((width * 3, 48), Image.Resampling.NEAREST), (300, y))
    sample_image.save(directory / "reading-samples.png")
    if reference_directory is None:
        return
    metadata = json.loads((reference_directory / "reference.json").read_text(encoding="utf-8"))
    expected_hashes = {row["path"]: row["sha256"].lower() for row in metadata["files"]}
    mappings = {char: path for chars, path in metadata["mapping"] for char in chars}
    markup = ['<!doctype html><meta charset="utf-8"><title>Local Digicode draft review</title>',
              '<style>body{font:14px Arial;background:#eee}.grid{display:grid;grid-template-columns:repeat(7,182px);gap:8px}.cell{background:white;padding:4px;text-align:center}img{width:60px;height:76px;object-fit:contain}svg{width:40px;height:80px;image-rendering:pixelated;margin-left:20px}</style>',
              '<h1>Local reference / hand-placed 8x16 draft</h1><p>Reference SVGs are local comparison inputs only. Pixel distinctness is not proof of authentic glyph transcription.</p><div class="grid">']
    for char, key in cells:
        relative = mappings[char]
        path = reference_directory / relative.lstrip("/")
        need(path.resolve().is_relative_to(reference_directory.resolve()), "Reference path escaped its directory")
        need(hashlib.sha256(path.read_bytes()).hexdigest() == expected_hashes[relative], "Changed reference SVG")
        rectangles = ''.join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y, row in enumerate(glyphs[key])
                             for x in range(8) if row & (128 >> x))
        markup.append(f'<div class="cell"><div>{html.escape(char)} / {key}</div><img src="{path.as_uri()}"><svg viewBox="0 0 8 16">{rectangles}</svg></div>')
    markup.append('</div>')
    (directory / "comparison.html").write_text(''.join(markup), encoding="utf-8")
    report["local_reference"] = {"source": metadata["source"], "checked_files": len(cells),
                                 "metadata_sha256": hashlib.sha256((reference_directory / "reference.json").read_bytes()).hexdigest(),
                                 "adopted_as_font": False, "license_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--reference-directory", type=Path)
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    glyphs = font_glyphs(catalog)
    report = verify(catalog, glyphs)
    review_artifacts(args.directory, catalog, glyphs, report,
                     args.reference_directory.resolve() if args.reference_directory else None)
    (args.directory / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
