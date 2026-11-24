"""Verify prepared title labels from their actual atlas bytes and source images."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from struct import pack, unpack_from

from PIL import Image

from digicode_glyphs import font_glyphs


ROOT = Path(__file__).resolve().parents[1]
ROM_BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
FONT = '4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED'
LICENSE = '76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C'
BLOB = '2A6FC8168C1FA166EE9D8FD575975ABC7381060E76F4867B52480EDE41A41431'
MANIFEST = '9F7A51A3EF43884A4A2DF821B6342756E4504B2A8DDECB7448220DC30EFE6B05'
AUTHOR = 'EC743A039FAF81386CEAA758572058B510DC7F837DC9DCF93B259D9FAC6A44AB'
GLYPH_ROWS = 'E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195'
LANGUAGES = ('english', 'japanese', 'korean', 'digicode')
JA = ('スタートボタンをおしてね！', 'ひとりでバトル', 'ともだちとバトル', 'オプション',
      'D-ARK', 'コレクション', 'Ver.1.5とバトル', 'バトスピとバトル', 'テイマータグ', 'デジモンシュート', '?')
DG = ('スタートボタンをおしてね', 'ひとりでバトル', 'ともだちとバトル', 'おぷしよん',
      'DARK', 'これくしよん', 'Verとばとる', 'ばとすぴとばとる', 'ていまーたぐ', 'でじもんしゆーと')
EN = ('COLLECTION', 'BATTLE VER.1.5', 'VS BATTLE SPIRIT', 'TAMER TAG', 'DIGIMON SHOOT')
KO = ('컬렉션', 'Ver.1.5와 대전', '배틀 스피릿과 대전', '테이머 태그', '디지몬 슈트')
QUEUES = ((0,), (1, 2, 3, 4, 5), (6, 7), (8, 9), (10, 9), (8, 10))
SHEETS = {'contact-sheet.png': 'F68761B3F9AAD44AA1BDC24417A8D633B3FFDC9EC0DD949903A1B2D4E9E75828',
          'root-menus.png': '7ED1FFCCFD5E9DF7072CE1FF04E1F21E57B3F08CB62DBE2140AC1A1DBF8E060A'}


def sha(data):
    return sha256(data).hexdigest().upper()


def need(ok, detail):
    if not ok:
        raise ValueError(detail)


def exact(path, digest):
    data = path.read_bytes()
    need(sha(data) == digest, f'Unexpected SHA-256: {path}')
    return data


def native_atlas(container, header, base, events, end):
    table, atlas = (value - base for value in unpack_from('<II', container, header))
    size, tile_at = unpack_from('<II', container, atlas)
    tile_at -= base
    need(0 < size <= 8192 and size % 32 == 0 and header < table < atlas
         and atlas + 8 <= tile_at <= end - size, 'Bounded native title atlas')
    frames = []
    for event in range(events):
        count, parts = unpack_from('<II', container, table + event * 8)
        parts -= base
        need(0 < count <= 128 and table + events * 8 <= parts and parts + count * 4 <= atlas,
             f'Bounded layout records for event {event}')
        composed = {}
        for i in range(count):
            flags, dy, dx = unpack_from('<Hbb', container, parts + 4 * i)
            tile = tile_at + (flags & 0x3FFF) * 32
            need(tile < tile_at + size, f'8-bit native tile index for event {event}')
            for y in range(8):
                for x in range(8):
                    tx = 7 - x if flags & 0x4000 else x
                    ty = 7 - y if flags & 0x8000 else y
                    raw = container[tile + ty * 4 + tx // 2]
                    color = raw >> (tx % 2 * 4) & 15
                    if color:
                        composed[(dx + x, dy + y)] = color
        frames.append((count, composed))
    return size // 32, frames


def source_frames(source):
    need(source[0x780148:0x780151] == bytes.fromhex('33C033C03D00007551'), 'Actual fixed Japanese title branch')
    table, tile_descriptor = unpack_from('<II', source, 0x3C3FE0)
    first_count, first_layout = unpack_from('<HH', source, 0x3C3FE0 + table)
    need((table, first_count, first_layout, tile_descriptor) == (16, 17, 60, 0x00BD28E9),
         'Exact source P0 and eleven events')
    descriptor = (tile_descriptor >> 16 & 127) * 0x10000 + (tile_descriptor & 0xFFFF) * 16 - 0x20000
    need(descriptor == 0x3D8E90, 'Source title far descriptor address')
    length, offset, segment, bank = unpack_from('<4H', source, descriptor)
    pixels = (bank & 127) * 0x10000 + segment * 16 + offset - 0x20000
    need((length, pixels) == (0x11C0, 0x396300) and source[descriptor + 8:descriptor + 16] == b'\xff' * 8,
         'Typed original planar tile extent')
    out = []
    for i in range(11):
        count, off = unpack_from('<HH', source, 0x3C3FE0 + table + i * 4)
        frame = {}
        for j in range(count):
            flags, dy, dx = unpack_from('<Hbb', source, 0x3C3FE0 + off + j * 4)
            tile = 0x396300 + (flags & 0x3FFF) * 32
            need(0x396300 <= tile < 0x3974C0, 'Source planar tile in range')
            for y in range(8):
                for x in range(8):
                    ty = 7 - y if flags & 0x8000 else y
                    bit = 1 << (x if flags & 0x4000 else 7 - x)
                    color = sum(1 << plane for plane in range(4) if source[tile + 4 * ty + plane] & bit)
                    if color:
                        frame[dx + x, dy + y] = color
        out.append(frame)
    return out


def extent(pixels):
    xs, ys = zip(*pixels)
    return [min(xs), min(ys), max(xs), max(ys)]


def glyph_space(text, font):
    wanted = set(text)
    result = {}
    for block in font.decode().split('STARTCHAR ')[1:]:
        rows = block.splitlines()
        encoded = int(next(line.split()[1] for line in rows if line.startswith('ENCODING ')))
        if not 0 <= encoded <= 0x10FFFF or chr(encoded) not in wanted:
            continue
        advance = int(next(line.split()[1] for line in rows if line.startswith('DWIDTH ')))
        width, height, left, down = map(int, next(line.split()[1:] for line in rows if line.startswith('BBX ')))
        pixels = rows[rows.index('BITMAP') + 1:rows.index('ENDCHAR')]
        need(len(pixels) == height and width <= 7 and 0 < advance <= 8, 'Complete pinned Galmuri glyph')
        result[chr(encoded)] = (advance, {(left + x, y - height - down)
            for y, row in enumerate(pixels) for x in range(width) if int(row, 16) & (0x80 >> x)})
    need(result.keys() == wanted, 'All required Galmuri glyphs present')
    return result


def bdf_ink(text, glyphs):
    result = set()
    pen = 1
    for char in text:
        advance, points = glyphs[char]
        result.update((pen + x, y) for x, y in points)
        pen += advance
    return result


def chart_ink(ids, glyphs):
    result = set()
    pen = 1
    for glyph_id in ids:
        rows = glyphs[glyph_id]
        dots = {(x, y - 15) for y in range(16) for x in range(8) if rows[y] & (0x80 >> x)}
        left, _, right, _ = extent(dots)
        result.update((pen + x - left, y) for x, y in dots)
        pen += right - left + 2
    return result


def outlined(ink, shift):
    result = {(x + dx, y + dy + shift): 15 for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    result.update({(x, y + shift): 13 for x, y in ink})
    return result


def append_pixels(left, right):
    left_width = extent(left)[2] + 1
    right_start = extent(right)[0]
    return left | {(x + left_width + 2 - right_start, y): color for (x, y), color in right.items()}


def check_button(image, letters, marker, name):
    left, top, right, bottom = extent(image)
    width = extent(letters)[2] + 1
    start = left + 16 + (right - left - 16 - width) // 2
    need(top == -8 and bottom == 7 and start >= left + 16 and start + width - 1 < right,
         f'No border or marker overwritten by text: {name}')
    expect = {(x, y): 13 if x in (left, right) or y in (top, bottom) else 15
              for x in range(left, right + 1) for y in range(top, bottom + 1)}
    expect.update({(x + left + 44, y): color for (x, y), color in marker.items()})
    expect.update({(x + start, y): color for (x, y), color in letters.items()})
    need(expect == image, f'Exact message, marker and border pixels for {name}')
    return [width, len(letters), start - (left + 15), right - (start + width - 1)]


def palette_events(source, native, blob, objects, base):
    p1 = objects['p1']['offset']
    p2 = objects['p2']['offset']
    start = 0x3D3A80
    need(unpack_from('<II', blob, p1) == (base + p1 + 8, 0), 'Title native P1 table pointer')
    for event in range(11):
        count, old_payload, old_a, old_b = unpack_from('<4H', source, start + 4 + 8 * event)
        n, payload, a, b = unpack_from('<4I', blob, p1 + 8 + event * 16)
        need((count, n, b, old_b) == (1, 1, 0, 0) and p1 <= payload - base <= p2 - 16
             and p1 <= a - base <= p2 - 8, f'Typed event payload and timing {event}')
        need(source[start + old_payload:start + old_payload + 12] == pack('<6H', 0xFF01, event, event, 0, 0, 0)
             and blob[payload - base:payload - base + 16] == pack('<6HI', 0xFF01, event, event, 0, 0, 0, 0)
             and blob[a - base:a - base + 8] == source[start + old_a:start + old_a + 8], f'Exact source P1 event {event}')
    raw = source[0x3D7EE0:0x3D7EE0 + 38]
    colors = []
    for old in unpack_from('<16H', raw, 6):
        need(old < 0x1000, 'Source BGR444 palette range')
        r, g, b = ((old >> shift) & 15 for shift in (8, 4, 0))
        colors.append((r * 2 + bool(r)) | ((g * 2 + bool(g)) << 5) | ((b * 2 + bool(b)) << 10))
    palette = blob[p2:p2 + 40]
    need(palette == raw[:6] + pack('<16H', *colors) + b'\0\0' == native[0x90878:0x908A0],
         'Exact source colors and preserved native title palette')
    return palette


def check_previews(previews, palette, frames):
    background = (40, 40, 48)
    rgb = [background] + [tuple(((w >> bit) & 31) * 255 // 31 for bit in (0, 5, 10))
                          for w in unpack_from('<15H', palette, 8)]
    for name, digest in SHEETS.items():
        exact(previews / name, digest)
        root = name == 'root-menus.png'
        with Image.open(previews / name) as opened:
            image = opened.convert('RGB')
        need(image.size == ((896, 164) if root else (896, 440)), 'Native-scale preview surface')
        for column, language in enumerate(LANGUAGES):
            for event in (range(1, 6) if root else range(11)):
                center = (52, 70, 88, 108, 126)[event - 1] if root else 25 + event * 40
                origin = 112 + 224 * column
                expected = frames[language][event][1]
                for y in range(-8, 8):
                    for x in range(-52, 52):
                        need(image.getpixel((origin + x, center + y)) == rgb[expected.get((x, y), 0)],
                             f'Preview/atlas mismatch: {language}, event {event}, ({x}, {y})')


def audit(source, native, font, blob, meta, author, previews):
    source_images = source_frames(source)
    base = meta['base_address']
    cursor = 0
    objects = {}
    for item in meta['objects']:
        need(item['offset'] == cursor and item['size'] % 4 == 0, 'Complete aligned object inventory')
        end = cursor + item['size']
        need(sha(blob[cursor:end]) == item['sha256'], 'Exact object extent and bytes')
        objects[item['label']] = item
        cursor = end
    need(cursor == len(blob) == 23868 and len(objects) == 6, 'Full asset blob')
    frames = {}
    report = {}
    for language in LANGUAGES:
        obj = objects[f'{language}_p0']
        offset = obj['offset']
        summary = meta['languages'][language]
        need(base + offset == summary['address'], 'Atlas start backed by physical bytes')
        tile_count, frames[language] = native_atlas(blob, offset, base, 11, offset + obj['size'])
        sizes = [n for n, _ in frames[language]]
        cases = [sum(sizes[e] for e in case) for case in QUEUES]
        need(tile_count == summary['tiles'] and [extent(f) for _, f in frames[language]] == summary['bounds']
             and sizes == summary['parts'] and cases[1] == 110 == summary['root_parts']
             and cases[2:4] == summary['subtrees'] and max(cases) <= 128, 'Native sprite/tile budget')
        need(all(extent(f)[2] - extent(f)[0] + 1 <= 102 and extent(f)[3] - extent(f)[1] + 1 <= 16
                 for _, f in frames[language]), 'Native glyph width and height')
        for event_list, parts in zip(QUEUES, cases, strict=True):
            need(dict(language=language, events=list(event_list), actual_parts=parts,
                      actual_staged_tile_bytes=parts * 32) in author['cases'], 'Bounded native renderer agreement')
        report[language] = dict(atlas_tiles=tile_count, simultaneous_parts=cases, root_tile_bytes=110 * 32,
                                physical_oam_limit=128, open_slots_at_root=18)
    need([frame for _, frame in frames['japanese']] == source_images, 'All 11 Japanese frames exact original planar pixels')
    need(tuple(meta['source_text']) == JA, 'Reviewed Japanese source labels')
    for lang, at, count in (('english', 0x8FD08, 5), ('japanese', 0x63A800, 5),
                            ('korean', 0x63D000, 5), ('digicode', 0x63E000, 1)):
        _, old = native_atlas(native, at, ROM_BASE, 5, len(native))
        need([f for _, f in old[:count]] == [f for _, f in frames[lang][:count]], 'Existing native title frames ' + lang)
    marker = {(x, y): c for (x, y), c in source_images[1].items() if -43 <= x <= -30 and -7 <= y <= 6}
    need(len(marker) == 196, 'Complete source fourteen-pixel marker cell')
    glyphs = glyph_space(''.join(EN + KO), font)
    text_metrics = {}
    for language, labels in (('english', EN), ('korean', KO)):
        text_metrics[language] = [check_button(frames[language][event][1], outlined(bdf_ink(label, glyphs), 5), marker,
                                              f'{language} {label}') for event, label in enumerate(labels, 5)]
    catalog = json.loads((ROOT / 'localization/digicode-reference.json').read_bytes())
    glyphs = font_glyphs(catalog)
    need(sha(b''.join(glyphs[g['id']] for g in catalog['glyphs'] + catalog['latin_glyphs'])) == GLYPH_ROWS,
         'Existing complete Digicode chart pixels')
    ids = {g[key]: g['id'] for kind, keys in (('glyphs', ('hiragana', 'katakana')),
          ('latin_glyphs', ('uppercase', 'lowercase'))) for g in catalog[kind] for key in keys}
    digicode_labels = [[ids[char] for char in reading] for reading in DG]
    hyphen = {(x, y): c for (x, y), c in source_images[4].items() if -7 <= x <= -2 and y == -1}
    version = {(x, y): c for (x, y), c in source_images[6].items() if -8 <= x <= 4 and -4 <= y <= 2 and c in (13, 14)}
    bang = {(x, y): c for (x, y), c in source_images[0].items() if 48 <= x <= 50}
    need(len(hyphen) == 6 and len(version) == 34 and len(bang) == 22, 'Exact original punctuation pixels')
    prompt = append_pixels(outlined(chart_ink(digicode_labels[0], glyphs), 7), bang)
    center = (extent(prompt)[2] + 1) // 2
    need({(x - center, y): c for (x, y), c in prompt.items()} == frames['digicode'][0][1], 'Digicode prompt and literal bang')
    metrics = []
    for event, glyph_ids in enumerate(digicode_labels[1:], 1):
        need(meta['digicode_glyph_ids'][str(event)] == glyph_ids, 'Japanese reading mapped to chart IDs')
        if event in (4, 6):
            split, literal, shift = (1, hyphen, 5) if event == 4 else (3, version, 7)
            first = outlined(chart_ink(glyph_ids[:split], glyphs), shift)
            second = outlined(chart_ink(glyph_ids[split:], glyphs), shift)
            letters = append_pixels(append_pixels(first, literal), second)
        else:
            letters = outlined(chart_ink(glyph_ids, glyphs), 7)
        metrics.append(check_button(frames['digicode'][event][1], letters, marker, f'Digicode {DG[event]}'))
    text_metrics['digicode'] = metrics
    need(all(rows[10][1] == source_images[10] for rows in frames.values()), 'Exact original locked question-mark pixels')
    palette = palette_events(source, native, blob, objects, base)
    check_previews(previews, palette, frames)
    return dict(languages=report, text_metrics_width_pixels_left_gap_right_gap=text_metrics,
                digicode_chart_ids=digicode_labels, preserved_prior_events=dict(english=5, japanese=5, korean=5, digicode=1),
                exact_source_japanese_events=11, source_p1_events=11, source_palette_native_exact=True,
                exact_previews=SHEETS, actual_game_rendering_observed=False, E6_overlay_exercised=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('source', 'native', 'font', 'license', 'assets', 'previews', 'author', 'report'):
        p.add_argument('--' + arg, type=Path, required=True)
    args = p.parse_args()
    need(not args.report.exists(), 'Fresh output report')
    exact(args.license, LICENSE)
    source, native, font = exact(args.source, SOURCE), exact(args.native, NATIVE), exact(args.font, FONT)
    blob = exact(args.assets / 'assets.bin', BLOB)
    meta = json.loads(exact(args.assets / 'manifest.json', MANIFEST))
    author = json.loads(exact(args.author, AUTHOR))
    need(author['assets_sha256'] == BLOB and author['manifest_sha256'] == MANIFEST
         and len(author['cases']) == 24, 'Exact author renderer suite identity')
    results = audit(source, native, font, blob, meta, author, args.previews)
    report = dict(status='MODE23_TITLE_FOUR_LANGUAGE_PIXEL_ASSETS_PASS', assets_sha256=BLOB,
                  manifest_sha256=MANIFEST, author_sha256=AUTHOR, checker_sha256=sha(Path(__file__).read_bytes()),
                  **results)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
