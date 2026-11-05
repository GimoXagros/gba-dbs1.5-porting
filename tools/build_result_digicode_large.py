"""Enlarge only the approved Digicode ink; reconstruct a native one-pixel edge."""
import json
from pathlib import Path

from PIL import Image, ImageDraw
import build_result_pixel_art as production
import digicode_glyphs as dg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/result-pixel-art-20261105-dg-large-v2"
FROZEN = ROOT / "build/result-pixel-art-20261105"


def make_digicode(punctuation, catalog, original_ink=None):
    font = dg.font_glyphs(catalog)
    glyph_ids = ["jp-3089","jp-3059","jp-3068","jp-3061","jp-3084","jp-3093","jp-3059"]
    cursor, old_cursor, ink, metadata, original_recovered = -50, -31, set(), [], set()
    for number, (source_char, rendered_char, glyph_id) in enumerate(zip("ラストチャンス", "ラストチヤンス", glyph_ids)):
        rows = font[glyph_id]
        points = {(x, y) for y, row in enumerate(rows) for x in range(8) if row & (128 >> x)}
        left, top = min(x for x, y in points), min(y for x, y in points)
        width, height = max(x for x, y in points) - left + 1, max(y for x, y in points) - top + 1
        assert width in (6, 7) and height == 10
        local = {(x - left, y - top) for x, y in points}
        original_recovered.update((x + old_cursor, y - 3) for x, y in local)
        target_width = {6: 9, 7: 11}[width]
        enlarged = {(x, y) for y in range(14) for x in range(target_width) if (x * width // target_width, y * height // 14) in local}
        ink.update((x + cursor, y - 7) for x, y in enlarged)
        metadata.append({"position": number, "source": source_char, "render": rendered_char, "glyph_id": glyph_id,
            "source_local_ink": [list(p) for p in sorted(local)], "source_size": [width, height],
            "target_local_ink": [list(p) for p in sorted(enlarged)], "target_size": [target_width, 14],
            "target_origin": [cursor, -7], "source_user_origin": [old_cursor, -3], "row_bytes_hex": rows.hex()})
        cursor += target_width + 3
        old_cursor += width + 1
    if original_ink is not None:
        assert original_recovered == original_ink
    assert cursor - 3 == 37
    assert metadata[1]["target_local_ink"] == metadata[6]["target_local_ink"], "two SU glyphs retain identical geometry"
    edge = {(x + dx, y + dy) for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - ink
    assert production.budget.bounds(dict.fromkeys(ink | edge)) == [-51, -8, 37, 7]
    for glyph in metadata[:-1]:
        clear_x = glyph["target_origin"][0] + glyph["target_size"][0] + 1
        assert all((clear_x, y) not in ink | edge for y in range(-8, 8))
    colors = [6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10]
    pixels = {point: 12 for point in edge}
    for x, y in ink:
        row = y + 7
        pixels[x, y] = colors[row] + int(row in (2, 5, 8, 11) and (x + y) % 2 == 0)
    assert len(punctuation) == 65 and production.budget.pixel_sha(punctuation) == "26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8"
    pixels.update(punctuation)
    assert not any(x in (40, 41) for x, y in pixels)
    revised = production.export("ラストチャンス plus original ! enlarged native ink", pixels, (-56, -8))
    assert revised["bounds"] == [-51, -8, 50, 7] and len(revised["parts"]) <= 28
    authoring = {"method": "per-glyph integer nearest expansion of approved ink; one-pixel outline reconstructed afterwards",
        "resampling": "dest(x,y) reads source(floor(x*source_width/target_width), floor(y*10/14))",
        "source_art_sha256": "7FB3925216D8E80DE8410970C2E4ACEFD314C1E675DD0FCB1973C342BDFE00B0", "source_body_ink_pixels": len(original_recovered),
        "ink_pixels": [list(p) for p in sorted(ink)], "white_edge_pixels": [list(p) for p in sorted(edge)], "glyphs": metadata,
        "body_bounds": [-51, -8, 37, 7], "punctuation_clear_columns": [40, 41], "glyph_ink_gap": 3}
    return revised, authoring


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = (FROZEN / "source-art-data.json").read_bytes()
    assert production.sha(frozen) == "7FB3925216D8E80DE8410970C2E4ACEFD314C1E675DD0FCB1973C342BDFE00B0"
    art = json.loads(frozen)
    palette = art["native_palette_rgb888"]
    catalog_bytes = (ROOT / "localization/digicode-reference.json").read_bytes()
    catalog = json.loads(catalog_bytes)
    font = dg.font_glyphs(catalog)
    small = {(x, y): value for x, y, value in art["digicode"]["pixels"]}
    original_ink = {point for point, value in small.items() if value in (6, 7, 8, 9, 10) and point[0] <= 19}
    assert len(original_ink) == 240
    punctuation = {(x,y):v for x,y,v in art["korean"]["pixels"] if x>=42}
    revised, authoring = make_digicode(punctuation,catalog,original_ink)
    art["digicode"], art["digicode_authoring"] = revised, authoring
    ink, edge = authoring["ink_pixels"], authoring["white_edge_pixels"]
    art["status"] = "enlarged-digicode-native-art-awaiting-independent-QA-not-ROM"
    production.OUT = OUT
    for name, frame in [("japanese-win", art["japanese_common"][0]), ("japanese-draw", art["japanese_common"][1]), ("korean-last-chance", art["korean"]), ("digicode-last-chance", revised)]:
        production.images(name, frame, palette)
    sheet = Image.new("RGBA", (224, 210), (28, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)
    for row, (label, path) in enumerate([
        ("Japanese original LAST CHANCE", FROZEN / "japanese-last-chance-1x.png"),
        ("Korean native-grid: 26 parts", OUT / "korean-last-chance-1x.png"),
        (f"Enlarged Digicode: {len(revised['parts'])} parts", OUT / "digicode-last-chance-1x.png"),
        ("Shared Japanese WIN: 30 parts", OUT / "japanese-win-1x.png"),
        ("Shared Japanese DRAW: 20 parts", OUT / "japanese-draw-1x.png"),
    ]):
        draw.text((6, row * 42 + 2), label, fill=(200, 204, 214, 255))
        preview = Image.open(path).convert("RGBA")
        sheet.alpha_composite(preview, ((224 - preview.width) // 2, row * 42 + 17))
    sheet.save(OUT / "comparison-dark-1x.png")
    sheet.resize((1792, 1680), Image.Resampling.NEAREST).save(OUT / "comparison-dark-8x.png")
    (OUT / "source-art-data.json").write_bytes((json.dumps(art, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    report = {"status": "PASS-production-assertions-independent-QA-pending", "frozen_original_untouched": True,
        "frozen_original_sha256": production.sha((FROZEN / "source-art-data.json").read_bytes()),
        "producer_sha256": production.sha(Path(__file__).read_bytes()), "catalog_sha256": production.sha(catalog_bytes),
        "digicode_parts": len(revised["parts"]), "digicode_tiles": len(revised["tiles_4bpp_hex"]),
        "ink_pixels": len(ink), "edge_pixels": len(edge), "punctuation_pixels": 65,
        "pixel_sha256": revised["palette_pixel_sha256"], "files": {p.name: production.sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "production.json"}}
    (OUT / "production.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(json.dumps({k: report[k] for k in ("status", "digicode_parts", "digicode_tiles", "ink_pixels", "edge_pixels", "pixel_sha256")}))


if __name__ == "__main__":
    main()
