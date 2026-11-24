"""Measure the actual spacing and preserved source pixels in revised title assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import unpack_from

from PIL import Image

import verify_mode23_title_pixel_assets as prior
from digicode_glyphs import font_glyphs


RETAIL_GLYPHS = {
    '1': (1, -20, -18), '2': (2, -22, -17), 'P': (1, -14, -9), 'B': (1, -3, 2),
    'A': (1, 4, 9), 'T': (1, 11, 16), 'L': (1, 25, 29), 'E': (1, 31, 35),
    'O': (3, -20, -15), 'I': (3, 2, 3), 'N': (3, 14, 19), 'S': (3, 24, 27),
    'D': (4, -15, -10), 'R': (4, 9, 14), 'K': (4, 17, 22),
}
EXTENSIONS = {
    'G': ('+####+', '##    ', '##    ', '## ###', '##  ##', '##  ##', '+####+'),
    'H': ('##  ##', '##  ##', '##  ##', '######', '##  ##', '##  ##', '##  ##'),
    'M': ('##  ##', '######', '######', '##++##', '##  ##', '##  ##', '##  ##'),
    'V': ('##  ##', '##  ##', '##  ##', '##  ##', '+####+', ' #### ', '  ##  '),
    '5': ('######', '##    ', '##    ', '#####+', '    ##', '##  ##', '+####+'),
    '.': ('  ', '  ', '  ', '  ', '  ', '##', '##'),
}


def decode(blob, manifest):
    base = manifest['base_address']
    out, objects, cursor = {}, {}, 0
    for obj in manifest['objects']:
        lo, hi = obj['offset'], obj['offset'] + obj['size']
        prior.need(lo == cursor and lo % 4 == hi % 4 == 0 and hi > lo
                   and prior.sha(blob[lo:hi]) == obj['sha256'], 'Complete aligned asset span')
        objects[obj['label']] = obj
        cursor = hi
        if obj['label'].endswith('_p0'):
            language = obj['label'][:-3]
            atlas, frames = prior.native_atlas(blob, lo, base, 11, hi)
            row = manifest['languages'][language]
            prior.need(row['address'] == lo + base and row['tiles'] == atlas
                       and row['parts'] == [count for count, _ in frames]
                       and row['bounds'] == [prior.extent(pixels) for _, pixels in frames], 'All physical P0 identities')
            out[language] = frames
    prior.need(cursor == len(blob) == manifest['bytes'] and len(objects) == 6
               and set(out) == set(prior.LANGUAGES), 'Full four-language asset blob')
    return out, objects


def english_shapes(english, manifest, marker):
    prior.need(manifest['retail_english_glyph_rectangles'] == {k: list(v) for k, v in RETAIL_GLYPHS.items()}
               and manifest['constructed_english_glyphs'] == ['C'] + list(EXTENSIONS), 'Actual retail and constructed provenance')
    glyphs = {}
    for char, (event, loose_left, loose_right) in RETAIL_GLYPHS.items():
        frame = english[event][1]
        width = loose_right - loose_left + 1
        glyph = {(x - loose_left, y): color for (x, y), color in frame.items()
                 if loose_left <= x <= loose_right and -3 <= y <= 3 and color in (13, 14)}
        prior.need(prior.extent(glyph) == [0, -3, width - 1, 3], 'Complete native seven-row retail letter ' + char)
        glyphs[char] = (width, glyph)
    glyphs['C'] = (6, {p: v for p, v in glyphs['O'][1].items() if p[0] < 4 or abs(p[1]) == 3})
    for label, shape in EXTENSIONS.items():
        glyphs[label] = (len(shape[0]), {(x, y - 3): {'#': 13, '+': 14}[pixel]
            for y, line in enumerate(shape) for x, pixel in enumerate(line) if pixel in '#+'})
    metrics = {}
    for event, name in enumerate(prior.EN, 5):
        text, pen = {}, 0
        for char in name:
            if char == ' ':
                pen += 4
            else:
                width, mask = glyphs[char]
                text.update({(x + pen, y): color for (x, y), color in mask.items()})
                pen += width + 1
        prior.need(prior.extent(text)[1::2] == [-3, 3], 'Actual retail bold seven-pixel baseline')
        metrics[name] = prior.check_button(english[event][1], text, marker, name)
    return metrics


def spaced_text(indexes, glyphs):
    placed = {}
    column = 0
    for index in indexes:
        source = glyphs[index]
        points = {(x, y - 8) for y, row in enumerate(source) for x in range(8) if row & (128 >> x)}
        left, top, right, bottom = prior.extent(points)
        prior.need(-7 <= top <= bottom <= 6, f'Two blank panel rows for full chart glyph {index}')
        placed.update({(x - left + column, y): 13 for x, y in points})
        column += right - left + 3
    return placed


def digicode_shapes(digicode, source_images, manifest, marker):
    catalog = json.loads((prior.ROOT / 'localization/digicode-reference.json').read_bytes())
    charts = font_glyphs(catalog)
    prior.need(prior.sha(b''.join(charts[g['id']] for g in catalog['glyphs'] + catalog['latin_glyphs'])) == prior.GLYPH_ROWS,
               'Earlier Digicode chart bytes are preserved')
    symbols = {g[key]: g['id'] for kind, keys in (('glyphs', ('hiragana', 'katakana')),
               ('latin_glyphs', ('uppercase', 'lowercase'))) for g in catalog[kind] for key in keys}
    metric = {}
    hyphen = {(x, y): color for (x, y), color in source_images[4].items() if -7 <= x <= -2 and y == -1}
    version = {(x, y): color for (x, y), color in source_images[6].items() if -8 <= x <= 4 and -4 <= y <= 2
               and color in (13, 14)}
    for event, reading in enumerate(prior.DG[1:], 1):
        indices = [symbols[char] for char in reading]
        prior.need(indices == manifest['digicode_glyph_ids'][str(event)], 'Japanese readings and exact chart glyph IDs')
        if event == 4:
            letters = prior.append_pixels(prior.append_pixels(spaced_text(indices[:1], charts), hyphen),
                                          spaced_text(indices[1:], charts))
        elif event == 6:
            letters = prior.append_pixels(prior.append_pixels(spaced_text(indices[:3], charts), version),
                                          spaced_text(indices[3:], charts))
        else:
            letters = spaced_text(indices, charts)
        panel = digicode[event][1]
        left, top, right, bottom = prior.extent(panel)
        marker_area = {(x + left + 44, y): color for (x, y), color in marker.items()}
        marker_right = max(x for x, _ in marker_area)
        observed = {(x, y): color for (x, y), color in panel.items() if color != 15 and (x, y) not in marker_area}
        x0, y0, x1, y1 = prior.extent(observed)
        origin = x0 - prior.extent(letters)[0]
        prior.need(observed == {(x + origin, y): color for (x, y), color in letters.items()},
                   f'Every real chart ink and punctuation pixel present exactly once, with two clear inter-glyph columns for {reading}')
        prior.need((left, top, bottom, x0) == (-52, -8, 7, -30)
                   and y0 > top and y1 < bottom and x0 - marker_right - 1 >= 7 and right - x1 >= 6,
                   'Common actual marker/text anchor with dark vertical padding and horizontal clearance')
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                prior.need(panel[(x, y)] == observed.get((x, y), marker_area.get((x, y), 15)),
                           'Uniform dark panel, exact original marker and absent white perimeter')
        metric[event] = dict(pixels=len(observed), text_width=x1 - x0 + 1, panel_width=right - left + 1,
                             clear_columns_after_marker=x0 - marker_right - 1, clear_columns_to_right=right - x1,
                             blank_rows_above_ink=y0 - top, blank_rows_below_ink=bottom - y1)
    return metric


def preview_check(directory, manifest, frames, palette):
    info = json.loads((directory / 'report.json').read_bytes())
    prior.need(info['assets_sha256'] == manifest['sha256'] and info['scale'] == 1, 'Exact native scale preview binding')
    rgb = [(40, 40, 48)] + [tuple(((word >> s) & 31) * 255 // 31 for s in (0, 5, 10))
                           for word in unpack_from('<15H', palette, 8)]
    for file, root in (('contact-sheet.png', False), ('root-menus.png', True)):
        prior.exact(directory / file, info['files'][file])
        with Image.open(directory / file) as png:
            image = png.convert('RGB')
        prior.need(image.size == ((896, 164) if root else (896, 440)), 'Native scale preview geometry')
        for col, lang in enumerate(prior.LANGUAGES):
            for event in (range(1, 6) if root else range(11)):
                center_y = (52, 70, 88, 108, 126)[event - 1] if root else 25 + 40 * event
                pixels = frames[lang][event][1]
                prior.need(-106 <= prior.extent(pixels)[0] <= prior.extent(pixels)[2] < 106, 'Crop bounds')
                for y in range(-8, 8):
                    for x in range(-106, 106):
                        prior.need(image.getpixel((224 * col + 112 + x, center_y + y)) == rgb[pixels.get((x, y), 0)],
                                   f'Exact actual preview pixels for {lang} {event}')
    return info['files']


def verify(args):
    previous_dir = prior.ROOT / 'build/mode23-title-assets-20261117'
    prev_blob = prior.exact(previous_dir / 'assets.bin', prior.BLOB)
    prev_meta = json.loads(prior.exact(previous_dir / 'manifest.json', prior.MANIFEST))
    previous, _ = decode(prev_blob, prev_meta)
    raw = prior.exact(args.assets / 'manifest.json', args.manifest_sha256)
    revision = json.loads(raw)
    blob = prior.exact(args.assets / 'assets.bin', args.blob_sha256)
    prior.need(revision['sha256'] == args.blob_sha256 and revision['schema'] == 2, 'Frozen corrected title assets')
    frames, objects = decode(blob, revision)
    source = prior.exact(args.source, prior.SOURCE)
    native = prior.exact(args.native, prior.NATIVE)
    original = prior.source_frames(source)
    prior.need(frames['korean'] == previous['korean'] and frames['japanese'] == previous['japanese']
               and [pixels for _, pixels in frames['japanese']] == original
               and frames['english'][:5] == previous['english'][:5] and frames['digicode'][0] == previous['digicode'][0]
               and all(frames[l][10][1] == original[10] for l in frames), 'Keep published assets outside the revised labels')
    marker = {(x, y): c for (x, y), c in original[1].items() if -43 <= x <= -30 and -7 <= y <= 6}
    metrics = dict(english=english_shapes(frames['english'], revision, marker),
                   digicode=digicode_shapes(frames['digicode'], original, revision, marker))
    palette = prior.palette_events(source, native, blob, objects, revision['base_address'])
    previews = preview_check(args.previews, revision, frames, palette)
    fixture = json.loads(prior.exact(args.author, args.author_sha256))
    prior.need(fixture['assets_sha256'] == args.blob_sha256 and fixture['manifest_sha256'] == args.manifest_sha256
               and len(fixture['cases']) == 24, 'Bind exact renderer fixture for revised assets')
    summary = {}
    for lang, row in frames.items():
        cases = [sum(row[event][0] for event in group) for group in prior.QUEUES]
        prior.need(all(n <= 128 for n in cases), 'All simultaneous groups fit physical OAM')
        for parts, group in zip(cases, prior.QUEUES, strict=True):
            prior.need(dict(language=lang, events=list(group), actual_parts=parts, actual_staged_tile_bytes=parts * 32)
                       in fixture['cases'], 'Simultaneous native sprite consumer output')
        summary[lang] = dict(prompt=cases[0], root_parts=cases[1], root_staged_tile_bytes=cases[1] * 32,
                             high_submenu_parts=max(cases[2:]), free_root_parts=128 - cases[1])
    prior.need({lang: row['root_parts'] for lang, row in summary.items()} ==
               dict(english=110, japanese=110, korean=110, digicode=116), 'All five rows at corrected aggregate sprite budget')
    return dict(assets_sha256=args.blob_sha256, manifest_sha256=args.manifest_sha256, renderer_fixture_sha256=args.author_sha256,
                native_consumer_and_physical_limits=summary, measured_spacing=metrics, previews=previews,
                physical_game_frame_observed=False, E6_overlay_exercised=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'native', 'assets', 'previews', 'author', 'report'):
        p.add_argument('--' + key, type=Path, required=True)
    for key in ('blob-sha256', 'manifest-sha256', 'author-sha256'):
        p.add_argument('--' + key, required=True)
    args = p.parse_args()
    prior.need(not args.report.exists(), 'Fresh report')
    result = dict(status='MODE23_TITLE_VISUAL_REVISION_PASS', checker_sha256=prior.sha(Path(__file__).read_bytes()),
                  **verify(args))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], prior.sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
