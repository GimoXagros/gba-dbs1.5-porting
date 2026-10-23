#!/usr/bin/env python3
"""Build a development-only Korean Options resource and its native route.

This deliberately separate PoC preserves both original atlases and all native
code. It does not implement a language selector or write a language/save byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_language_consumers import ASSETS, decode_asset, render_asset

BASE, RAW = 0x08000000, 0x632000
GBA_SHA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
FONT_SHA = "4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED"
LICENSE_SHA = "76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C"
P1, P2 = 0xA02E8, 0xA05B8
P1_SITES = (0xC3160, 0xC316C, 0xC3178, 0xC3188, 0xC3194,
            0xC31A8, 0xC31B4, 0xC31C8, 0xC31D4, 0xC31E4,
            0xC31F0, 0xC31FC, 0xC320C, 0xC3218, 0xC3228)
# Fifteen native presentation objects; every reachable frame is bounded even
# when an object is currently hidden. Four independent arrow objects coexist.
EVENTS = (0, 2, 4, 6, 7, 1, 8, 3, 8, 8, 5, 5, 8, 11, 9)
TEXT = {(0, 0): "しあいじかん", (2, 0): "むずかしさ",
        (3, 0): "かんたん", (3, 1): "ふつう", (3, 2): "むずかしい",
        (4, 0): "サウンドテスト", (6, 0): "データをけす", (7, 0): "もどる",
        (11, 0): "いいえ", (11, 1): "はい"}
ROW_EVENTS = (0, 2, 4, 6, 7)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from("<I", data, at)[0]


def font_glyphs(data, characters):
    """Read the exact BDF glyphs; bitmap rows are MSB-first and byte padded."""
    glyphs = {}
    for block in data.decode("utf-8").split("STARTCHAR ")[1:]:
        lines = block.splitlines()
        fields = {line.split()[0]: line.split()[1:] for line in lines if line.split()}
        code = int(fields["ENCODING"][0])
        if code < 0 or chr(code) not in characters:
            continue
        ch = chr(code)
        need(ch not in glyphs, f"duplicate font character {ch!r}")
        advance, dy = map(int, fields["DWIDTH"])
        width, height, left, bottom = map(int, fields["BBX"])
        rows = lines[lines.index("BITMAP") + 1:lines.index("ENDCHAR")]
        need(dy == 0 and 0 < advance <= 8 and 0 <= width <= 7 and
             0 <= height <= 11 and left == 0 and bottom >= 0 and
             height + bottom <= 11, f"bounded Galmuri11 Condensed metrics: {ch!r}")
        need(len(rows) == height and all(len(row) == (width + 7)//8*2 for row in rows),
             f"complete bitmap rows for {ch!r}")
        ink = {(x + left, y - height - bottom)
               for y, row in enumerate(rows) for x in range(width)
               if int(row, 16) & (1 << (((width + 7)//8)*8 - x - 1))}
        need(bool(ink) or ch == " ", f"nonempty required glyph {ch!r}")
        glyphs[ch] = (advance, ink)
    need(set(glyphs) == set(characters), f"missing font glyphs: {sorted(set(characters) - set(glyphs))}")
    return glyphs


def text_pixels(text, glyphs):
    need(isinstance(text, str) and text and text == text.strip(), "nonempty, unpadded translation")
    ink, cursor = set(), 0
    for ch in text:
        need(ch in glyphs, f"unmapped translated character {ch!r}")
        advance, points = glyphs[ch]
        ink.update((x + cursor + 1, y) for x, y in points)
        cursor += advance
    need(ink, "translation has visible ink")
    # Native Options uses palette index 1 for ink and 2 for its one-pixel edge.
    pixels = {(x + dx, y + dy): 2 for x, y in ink
              for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    pixels.update({point: 1 for point in ink})
    width = max(x for x, _ in pixels) + 1
    need(min(x for x, _ in pixels) == 0 and min(y for _, y in pixels) >= -12 and
         max(y for _, y in pixels) <= 0, "complete thirteen-pixel font bounds")
    return pixels, width


def pack_tile(pixels, left, top):
    return bytes(pixels.get((left + x, top + y), 0) |
                 pixels.get((left + x + 1, top + y), 0) << 4
                 for y in range(8) for x in range(0, 8, 2))


def resource(gba, font, draft):
    need(draft.get("schema") == 1 and draft.get("status") == "draft-not-product-build-input",
         "explicit development-only translation input")
    entries = draft["entries"]
    translated = {(row["event"], row.get("frame", 0)): row for row in entries}
    need(len(entries) == len(translated) == len(TEXT) and set(translated) == set(TEXT),
         "all ten and only the ten identified source text frames")
    for identity, row in translated.items():
        need(row["ja_transcription"] == row["ja_reading"] == TEXT[identity],
             f"protected Japanese transcription/reading {identity}")
    glyphs = font_glyphs(font, set("".join(row["ko_draft"] for row in entries)))
    original = decode_asset(gba, ASSETS[0])
    layouts = {row["layout"]: [dict(p) for p in row["entries"]] for row in original["layouts"]}
    atlas_start = original["atlas_pixels_raw"]
    tiles = [gba[at:at + 32] for at in range(atlas_start, atlas_start + original["atlas_bytes"], 32)]
    indices = {data: i for i, data in enumerate(tiles)}
    frames = []
    for (event, frame), row in translated.items():
        layout = original["events"][event]["layouts"][frame]
        pixels, width = text_pixels(row["ko_draft"], glyphs)
        need(width <= (72 if event in ROW_EVENTS else 40), f"horizontal text overflow {event}:{frame}")
        left = 8 if event in ROW_EVENTS else ((24 if event == 11 else 40) - width)//2
        parts = ([dict(p) for p in layouts[layout] if p["x"] == 0 and p["tile_flags"] == 27]
                 if event in ROW_EVENTS else [])
        need(len(parts) == (1 if event in ROW_EVENTS else 0), "preserve native square marker")
        for top in (-12, -4):
            for x in range(0, width, 8):
                tile = pack_tile(pixels, x, top)
                if not any(tile):
                    continue
                if tile not in indices:
                    indices[tile] = len(tiles)
                    tiles.append(tile)
                parts.append(dict(tile_flags=indices[tile], x=left + x, y=top))
        need(0 < len(parts) <= 20 and all(-128 <= p[k] <= 127 for p in parts for k in ("x", "y")),
             "native layout part/coordinate bounds")
        layouts[layout] = parts
        frames.append(dict(event=event, frame=frame, layout=layout, ja=row["ja_transcription"],
                           ko=row["ko_draft"], width=width, left=left, parts=len(parts)))
    need(len(tiles) <= 256, "actual native renderer uses an eight-bit source tile index")
    counts = [max(len(layouts[index]) for index in original["events"][event]["layouts"]) for event in EVENTS]
    need(sum(counts) <= 127, "whole Options screen exceeds native OAM queue")
    out = bytearray(16 + 32*8)
    for layout in range(32):
        parts = layouts[layout]
        struct.pack_into("<II", out, 16 + layout*8, len(parts), BASE + RAW + len(out))
        for p in parts:
            out.extend(struct.pack("<Hbb", p["tile_flags"], p["y"], p["x"]))
    descriptor = len(out)
    out.extend(struct.pack("<II", len(tiles)*32, BASE + RAW + descriptor + 8))
    out.extend(b"".join(tiles))
    struct.pack_into("<IIHHHH", out, 0, BASE + RAW + 16, BASE + RAW + descriptor,
                     5, len(tiles) - 1, (len(tiles) - 1)*32, 8)
    return bytes(out), dict(p0_raw=RAW, p1_raw=P1, p2_raw=P2, atlas_tiles=len(tiles),
        atlas_bytes=len(tiles)*32, frames=frames, glyphs=sorted(glyphs),
        active_budget=dict(events=list(EVENTS), maximum_parts_by_object=counts,
                          maximum_oam_parts=sum(counts), maximum_active_tile_bytes=sum(counts)*32,
                          oam_capacity=128, native_tile_queue_bytes=4096,
                          atlas_residency="per-emitted-tile staging; entire ROM atlas is not preloaded"))


def ownership(data, end):
    need(RAW < end <= 0x640000 and data[RAW:end] == b"\xff"*(end - RAW), "exact resource allocation is FF")
    for at in range(len(data) - 3):
        need(not BASE + RAW <= word(data, at) < BASE + end, f"prior encoded pointer into resource: {at:X}")
    for at in range(0, len(data) - 3, 4):
        value = word(data, at)
        if value >> 28 == 15:
            continue
        if value & 0x0E000000 == 0x0A000000:
            delta = value & 0xFFFFFF
            delta -= 0x1000000 if delta & 0x800000 else 0
            need(not RAW <= at + 8 + delta*4 < end, f"prior ARM branch into resource: {at:X}")
        if value & 0x0E1F0000 == 0x041F0000:
            delta = (value & 4095) * (1 if value & 0x800000 else -1)
            need(not RAW <= at + 8 + delta < end, f"prior PC-relative reference into resource: {at:X}")


def build(before, gba, font, license_data, draft):
    need(sha(gba) == GBA_SHA and len(before) == 0x800000, "pinned USA source and expanded predecessor")
    need(sha(font) == FONT_SHA and sha(license_data) == LICENSE_SHA, "exact Galmuri11 Condensed 2.404 and OFL license")
    for start, end in ((0x9F980, 0xA1060), (0xC15C4, 0xC4018), (0x127E4, 0x12DD8),
                       (0x11708, 0x11854), (0x18C, 0x198), (0x39C, 0x3A0)):
        need(before[start:end] == gba[start:end], f"native dependency unchanged {start:X}..{end:X}")
    payload, info = resource(gba, font, draft)
    ownership(before, RAW + len(payload))
    writes = [(RAW, payload, "Korean Options P0 layouts and exact font-derived atlas")]
    for at in P1_SITES:
        for delta, old, new, name in ((0, 0xA0D68, P1, "Japanese event identities"),
                                      (4, 0xA05E0, RAW, "Korean P0"),
                                      (8, 0xA1038, P2, "source palette")):
            need(word(before, at + delta) == BASE + old, f"exact native presentation pointer {at + delta:X}")
            writes.append((at + delta, struct.pack("<I", BASE + new), name))
    need(word(before, 0xC1784) == BASE + 0xA1038, "exact initial Options palette pointer")
    writes.append((0xC1784, struct.pack("<I", BASE + P2), "matching source palette preload"))
    after, covered = bytearray(before), set()
    for at, value, _ in writes:
        cells = set(range(at, at + len(value)))
        need(not covered & cells, "disjoint Expected Writes")
        covered |= cells
        after[at:at + len(value)] = value
    inverse = bytearray(after)
    for at, value, _ in writes:
        inverse[at:at + len(value)] = before[at:at + len(value)]
    need(inverse == before, "whole-image inverse including unchanged original atlases/code/save logic")
    decode_asset(after, ("options-korean", RAW, P1, P2, 12, info["atlas_tiles"]))
    report = dict(schema=1, kind="development-only-korean-options-native-poc",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=GBA_SHA,
        font_sha256=FONT_SHA, font_license_sha256=LICENSE_SHA, resource=info,
        expected_writes=[dict(raw=at, bytes=len(value), purpose=label,
                             before_sha256=sha(before[at:at + len(value)]), after_sha256=sha(value))
                         for at, value, label in writes],
        changed_bytes=sum(a != b for a, b in zip(before, after, strict=True)),
        translation_policy="ten existing unreviewed drafts, explicitly accepted for this development PoC only",
        scope="normal five-row Options and its existing values/confirmation; English branch routes to Korean in this standalone PoC",
        language_selector=False, persistence_changed=False, executable_code_changed=False,
        original_assets_preserved=True, supplied_save_accessed=False, runtime_claim=False,
        four_language_feature_complete=False)
    return bytes(after), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "gba", "font", "license", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--draft", type=Path, default=Path(__file__).resolve().parents[1]/"localization/options-draft.json")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--render-directory", type=Path)
    args = parser.parse_args()
    need(all(p.suffix.lower() != ".sav" for p in (args.input, args.gba, args.font, args.license, args.output, args.draft, args.manifest)), "save paths forbidden")
    need(args.output.resolve() not in {args.input.resolve(), args.gba.resolve()}, "never overwrite input ROM")
    after, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.font.read_bytes(),
                          args.license.read_bytes(), json.loads(args.draft.read_text(encoding="utf-8")))
    if args.render_directory:
        asset = decode_asset(after, ("options-korean", RAW, P1, P2, 12, report["resource"]["atlas_tiles"]))
        report["preview"] = render_asset(after, asset, args.render_directory, True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[Korean Options PoC] " + report["output_sha256"])


if __name__ == "__main__":
    main()
