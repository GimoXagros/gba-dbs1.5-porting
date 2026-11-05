"""Author a 1x Hangul mask and export isolated native result art; no ROM writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from PIL import Image, ImageDraw
import analyze_result_language_budget as budget

OUT = ROOT / "build/result-pixel-art-20261105"
ORIGINALS = Path("C:/Users/김기호/Downloads/JUS")
REVIEW = ROOT / "build/result-art-review-20261026"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def korean_mask():
    """Hand-authored integer strokes; no large image or font is sampled."""
    glyphs = {}

    def glyph(label, start, draw):
        pixels = set()

        def rect(x0, y0, x1, y1):
            pixels.update((x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1))

        def box(x0, y0, x1, y1, thickness=2):
            rect(x0, y0, x1, y0 + thickness - 1)
            rect(x0, y1 - thickness + 1, x1, y1)
            rect(x0, y0, x0 + thickness - 1, y1)
            rect(x1 - thickness + 1, y0, x1, y1)

        draw(rect, box)
        assert pixels and all(0 <= x <= 13 and 0 <= y <= 13 for x, y in pixels)
        glyphs[label] = {(x + start, y - 7) for x, y in pixels}

    def ma(r, b):
        b(0, 0, 7, 13)
        r(10, 0, 11, 13)
        r(10, 5, 13, 6)

    def ji(r, b):
        r(0, 0, 8, 1)
        for y in range(2, 11):
            d = (y - 2) // 2
            r(4 - d, y, 5 - d, y)
            r(4 + d, y, min(9, 5 + d), y)
        r(12, 0, 13, 13)

    def mak(r, b):
        b(0, 0, 7, 8)
        r(10, 0, 11, 8)
        r(10, 3, 13, 4)
        r(0, 11, 12, 12)
        r(11, 11, 12, 13)

    def gi(r, b):
        r(0, 0, 8, 1)
        r(7, 0, 8, 13)
        r(12, 0, 13, 13)

    def hoe(r, b):
        r(3, 0, 5, 0)
        r(0, 2, 8, 2)
        b(0, 4, 8, 9, 1)
        r(4, 11, 5, 12)
        r(0, 12, 8, 13)
        r(12, 0, 13, 13)

    for label, start, draw in [("마", -50, ma), ("지", -33, ji), ("막", -16, mak), ("기", 5, gi), ("회", 23, hoe)]:
        glyph(label, start, draw)
    ink = set().union(*glyphs.values())
    edge = {(x + dx, y + dy) for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - ink
    assert all(-51 <= x <= 38 and -8 <= y <= 7 for x, y in ink | edge)
    assert all(not (-1 <= x <= 3) for x, y in ink | edge), "five clear columns between words"
    # Transparent cores remain inside both mieum and hieut after the white edge.
    for x, y in [(-47, 0), (-13, -3), (27, -1), (28, -1)]:
        assert (x, y) not in ink | edge, (x, y)
    assert all((36, y) in ink for y in range(-7, 7)), "complete final right-hand i"
    assert all((-16 + x, 4) in ink for x in range(13)), "mak final giyeok top"
    colors = [6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10]
    pixels = {point: 12 for point in edge}
    for x, y in ink:
        row = y + 7
        color = colors[row]
        if row in (2, 5, 8, 11) and (x + y) % 2 == 0:
            color += 1
        pixels[x, y] = color
    metadata = {label: {"ink": [list(p) for p in sorted(points)], "bounds": budget.bounds(dict.fromkeys(points))} for label, points in glyphs.items()}
    return pixels, ink, edge, metadata


def export(label, pixels, grid):
    parts, tiles = budget.pack_exact(pixels, grid)
    assert budget.compose(parts, tiles) == pixels
    return {"label": label, "bounds": budget.bounds(pixels), "palette_pixel_sha256": budget.pixel_sha(pixels),
            "parts": parts, "tiles_4bpp_hex": [tile.hex() for tile in tiles],
            "pixels": [[x, y, value] for (x, y), value in sorted(pixels.items())]}


def art_data(native, source, catalog):
    """Fresh-build production path: originals and tracked masks/catalog only."""
    from build_result_digicode_large import make_digicode
    assert sha(source) == "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
    assert sha(native) == "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
    frames, punctuation, _ = budget.source_labels(source,native)
    colors = struct.unpack_from("<16H",native,0xB9144+6)
    palette = [[((color >> shift) & 31)*255//31 for shift in (0,5,10)] for color in colors]
    korean,ink,edge,glyphs = korean_mask()
    korean.update(punctuation)
    digicode,authoring = make_digicode(punctuation,catalog)
    result = {"schema":1,"status":"fresh-generated-approved-native-pixels-not-ROM",
        "native_palette_rgb888":palette,
        "japanese_common":[export("WIN",frames[0],(0,5)),export("DRAW",frames[1],(-40,-8))],
        "korean":export("마지막 기회!",korean,(-56,-8)),"digicode":digicode,
        "digicode_authoring":authoring,"glyph_ids":[g["glyph_id"] for g in authoring["glyphs"]],
        "source_reading":"ラストチャンス","render_reading":"ラストチヤンス",
        "complete_native_punctuation_pixels":65,
        "korean_authoring":{"method":"hand-authored 1x integer Hangul strokes","ink_pixels":[list(p) for p in sorted(ink)],
                            "white_edge_pixels":[list(p) for p in sorted(edge)],"glyphs":glyphs}}
    budget.approved_labels(result,frames,punctuation)
    return result


def images(name, frame, palette, canvas=None):
    bounds = canvas or frame["bounds"]
    image = Image.new("P", (bounds[2] - bounds[0] + 1, bounds[3] - bounds[1] + 1), 0)
    image.putpalette(sum(palette, []) + [0] * (768 - len(palette) * 3))
    image.info["transparency"] = 0
    for x, y, value in frame["pixels"]:
        image.putpixel((x - bounds[0], y - bounds[1]), value)
    image.save(OUT / f"{name}-indices.png", transparency=0)
    rgba_source = image.convert("RGBA")
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) == 0:
                rgba_source.putpixel((x, y), (0, 0, 0, 0))
    for scale in (1, 8):
        preview = rgba_source if scale == 1 else rgba_source.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        preview.save(OUT / f"{name}-{scale}x.png")
        assert {preview.getpixel((x, y))[3] for y in range(preview.height) for x in range(preview.width)} <= {0, 255}
    return image


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (ORIGINALS / "Digimon Tamers - Battle Spirit Ver 1.5.wsc").read_bytes()
    native = (ORIGINALS / "Digimon - Battle Spirit (USA).gba").read_bytes()
    assert sha(source) == "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
    assert sha(native) == "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
    prior_bytes = (REVIEW / "source-art-data.json").read_bytes()
    art = json.loads(prior_bytes)
    source_frames, punctuation, source_report = budget.source_labels(source, native)
    assert len(punctuation) == 65 and budget.pixel_sha(punctuation) == "26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8"
    for index, frame in enumerate(art["japanese_common"]):
        assert {(x, y): value for x, y, value in frame["pixels"]} == source_frames[index]
    dg_image_bytes = (REVIEW / "source-digicode-last-chance-16x.png").read_bytes()
    assert sha(dg_image_bytes) == "7ED62F223587B4AEFE82ACA425F5D2B336548D3299DFA31D5E818225E7714D50"
    dg_image = Image.open(REVIEW / "source-digicode-last-chance-16x.png").convert("RGBA")
    assert dg_image.size == (1024, 256)
    palette = art["native_palette_rgb888"]
    dg_pixels = {(x, y): value for x, y, value in art["digicode"]["pixels"]}
    for y in range(256):
        for x in range(1024):
            value = dg_pixels.get((x // 16 - 32, y // 16 - 8), 0)
            actual = dg_image.getpixel((x, y))
            assert actual == tuple(palette[value]) + (255,) if value else actual[3] == 0
    pixels, ink, edge, glyphs = korean_mask()
    assert not pixels.keys() & punctuation.keys()
    pixels.update(punctuation)
    assert not any(x in (40, 41) for x, y in pixels)
    assert set(pixels.values()) <= {6, 7, 8, 9, 10, 12}
    korean = export("마지막 기회!", pixels, (-56, -8))
    assert len(korean["parts"]) <= 28 and korean["bounds"] == [-51, -8, 50, 7]
    art.update(status="native-grid-art-awaiting-independent-QA-not-ROM", korean=korean,
               no_korean_native_asset=False, korean_authoring={"method": "hand-authored 1x integer Hangul strokes", "logical_canvas": [-51, -8, 50, 7],
               "ink_pixels": [list(p) for p in sorted(ink)], "white_edge_pixels": [list(p) for p in sorted(edge)], "glyphs": glyphs,
               "word_gap_columns": [-1, 0, 1, 2, 3], "punctuation_clear_columns": [40, 41], "grid": [-56, -8]})
    for name, frame in [("japanese-win", art["japanese_common"][0]), ("japanese-draw", art["japanese_common"][1]), ("digicode-last-chance", art["digicode"]), ("korean-last-chance", korean)]:
        assert budget.compose(frame["parts"], [bytes.fromhex(t) for t in frame["tiles_4bpp_hex"]]) == {(x, y): value for x, y, value in frame["pixels"]}
        images(name, frame, palette)
    japanese_last = export("Japanese original last chance", source_frames[14], (-56, -8))
    images("japanese-last-chance", japanese_last, palette)
    sheet = Image.new("RGBA", (224, 210), (28, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)
    for row, (name, label) in enumerate([
        ("japanese-last-chance", "Japanese original LAST CHANCE"),
        ("korean-last-chance", "Korean native-grid: 26 parts"),
        ("digicode-last-chance", "Approved user Digicode: 16 parts"),
        ("japanese-win", "Shared Japanese WIN: 30 parts"),
        ("japanese-draw", "Shared Japanese DRAW: 20 parts"),
    ]):
        draw.text((6, row * 42 + 2), label, fill=(200, 204, 214, 255))
        preview = Image.open(OUT / f"{name}-1x.png").convert("RGBA")
        sheet.alpha_composite(preview, ((224 - preview.width) // 2, row * 42 + 17))
    sheet.save(OUT / "comparison-dark-1x.png")
    sheet.resize((sheet.width * 8, sheet.height * 8), Image.Resampling.NEAREST).save(OUT / "comparison-dark-8x.png")
    mask = Image.new("1", (102, 16))
    for x, y in ink:
        mask.putpixel((x + 51, y + 8), 1)
    mask.save(OUT / "korean-ink-mask-1x.png")
    (OUT / "source-art-data.json").write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ascii_mask = "\n".join("".join("#" if (x, y) in ink else "." for x in range(-51, 51)) for y in range(-8, 8))
    (OUT / "korean-ink-mask.txt").write_text(ascii_mask + "\n", encoding="utf-8")
    report = {"status": "PASS-production-assertions-independent-QA-pending", "source_sha256": sha(source), "retail_sha256": sha(native),
              "prior_art_sha256": sha(prior_bytes), "producer_sha256": sha(Path(__file__).read_bytes()),
              "korean_parts": len(korean["parts"]), "korean_tiles": len(korean["tiles_4bpp_hex"]), "korean_pixels": len(pixels),
              "ink_pixels": len(ink), "edge_pixels": len(edge), "punctuation_pixels": len(punctuation),
              "korean_pixel_sha256": korean["palette_pixel_sha256"], "shared_japanese_parts": [len(f["parts"]) for f in art["japanese_common"]],
              "digicode_parts": len(art["digicode"]["parts"]), "source_report": source_report,
              "files": {p.name: sha(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "production.json"}}
    (OUT / "production.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("status", "korean_parts", "korean_tiles", "ink_pixels", "edge_pixels", "korean_pixel_sha256")}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--generate-data":
        assert len(sys.argv)==6,"--generate-data GBA WSC15 CATALOG OUTPUT"
        native_path,source_path,catalog_path,output_path=map(Path,sys.argv[2:])
        assert all(p.suffix.lower()!=".sav" for p in (native_path,source_path,catalog_path,output_path)),"save paths forbidden"
        assert output_path.suffix.lower()==".json" and output_path.resolve() not in {p.resolve() for p in (native_path,source_path,catalog_path)}
        generated=art_data(native_path.read_bytes(),source_path.read_bytes(),json.loads(catalog_path.read_bytes()))
        output_path.parent.mkdir(parents=True,exist_ok=True)
        output_path.write_bytes((json.dumps(generated,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        print("[approved-native-art] "+sha(output_path.read_bytes()))
    else:
        main()
