"""Check compact Digicode menu geometry and localized Start prompt color."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from struct import unpack_from

from digicode_glyphs import BODIES, SEMIVOICED, VOICED
from mode23_compact_menu_digicode import glyph, line
import verify_mode23_title_pixel_assets as prior
from verify_mode23_title_visual_revision import decode, preview_check


COMPACT = '3F45DF599E25CC768FE92526EB7BF40B466808A592EEA781A6B02F1231A49A32'
COMPACT_MANIFEST = 'CB9F5D591B890496783569AB69EFB29DE415555A0047D7952730FD07EDEA23B3'
OLD_REVISION = '0633125FE39EC15C2421BDF9A560554A9ED240CCD75EFB1ADF9C9F3D82FF486C'
OLD_MANIFEST = '1D9CC9E4F22AEF744F6CDAD318D2F90E4A98FD0452386D4F3CB61FDABDBC7756'
WARM = frozenset(range(7, 12))


def get_assets(directory, sha_blob, sha_manifest):
    meta = json.loads(prior.exact(directory / 'manifest.json', sha_manifest))
    data = prior.exact(directory / 'assets.bin', sha_blob)
    prior.need(meta['sha256'] == sha_blob, 'Bound asset manifest')
    frames, objects = decode(data, meta)
    return data, meta, frames, objects


def glyphs_in(text):
    pixels = {}
    stream = 0
    for char in text:
        shape = glyph(char)
        left, top, right, bottom = prior.extent(shape)
        prior.need(right - left + 1 <= 6 and 0 <= top <= bottom <= 11, 'Compact Digicode body and dedicated voicing rows')
        pixels.update({(x + stream - left, y - 6): 13 for x, y in shape})
        stream += right - left + 2
    return pixels


def compact_buttons(images, source_frames):
    marker = {(x, y): c for (x, y), c in source_frames[1].items() if -43 <= x <= -30 and -7 <= y <= 6}
    hyphen = {(x, y + 2): v for (x, y), v in source_frames[4].items() if -7 <= x <= -2 and y == -1}
    version = {(x, y + 3): v for (x, y), v in source_frames[6].items() if -8 <= x <= 4 and -4 <= y <= 2 and v in (13, 14)}
    descriptors = {}
    for event, label in enumerate(prior.DG[1:], 1):
        if event in (4, 6):
            cut, suffix = (1, hyphen) if event == 4 else (3, version)
            letters = prior.append_pixels(prior.append_pixels(glyphs_in(label[:cut]), suffix), glyphs_in(label[cut:]))
        else:
            letters = glyphs_in(label)
        parts, ink = images[event]
        prior.need(prior.extent(ink) == [-44, -8, 43, 7] and parts == 22 and len(ink) == 88 * 16,
                   'Original fixed 88×16 sprite frame')
        expected_border = {(x, y) for x, y in ink if x in (-44, 43) or y in (-8, 7)}
        prior.need(all(ink[point] == 13 for point in expected_border), 'Complete white perimeter')
        seen = {p: value for p, value in ink.items() if value != 15 and p not in marker and p not in expected_border}
        left, top, right, bottom = prior.extent(seen)
        start = left - prior.extent(letters)[0]
        prior.need(seen == {(x + start, y): v for (x, y), v in letters.items()}, 'Exact compact glyphs and source punctuation placement')
        prior.need(left - (-30) - 1 >= 1 and right <= 41 and -6 <= top <= bottom <= 5
                   and all(ink[p] == v for p, v in marker.items()), 'No glyph, marker, or border contact')
        descriptors[event] = dict(width=right - left + 1, height=bottom - top + 1, left_gap=left - (-30) - 1,
                                  right_gap=43 - right - 1, above=top - (-8) - 1, below=7 - bottom - 1)
    # Preserve separate identities in the actual nine displayed readings.
    catalog = json.loads((prior.ROOT / 'localization/digicode-reference.json').read_bytes())
    identities = {g[field]: g['id'] for kind, fields in (('glyphs', ('hiragana', 'katakana')),
                  ('latin_glyphs', ('uppercase', 'lowercase'))) for g in catalog[kind] for field in fields}
    patterns = {}
    for char in set(''.join(prior.DG[1:])):
        shape = glyph(char)
        left = min(x for x, _ in shape)
        signature = frozenset((x - left, y) for x, y in shape)
        key = identities[char]
        prior.need(patterns.setdefault(key, signature) == signature, 'Case and kana aliases share chart shape')
    prior.need(len(set(patterns.values())) == len(patterns), 'Every used compact chart identity remains a distinct native bitmap')
    return dict(frames=descriptors, used_distinct_compact_glyphs=len(patterns))


def compact_digicode_prompt(source):
    reading = 'スタートボタンをおしてね'
    ink = set()
    at = 1
    for char in reading:
        hira = chr(ord(char) - 96) if 'ァ' <= char <= 'ヶ' else char
        base = VOICED.get(hira, SEMIVOICED.get(hira, hira))
        body = set()
        for command in BODIES[base].split(';'):
            path = [tuple(map(int, xy.split(','))) for xy in command.split()]
            points = [((x * 5 + 3) // 6, (y * 6 + 4) // 9) for x, y in path]
            body.update(points)
            for a, b in zip(points, points[1:]):
                body.update(line(a, b))
        dots = {(x, y - 2) for x, y in body}
        if hira in VOICED:
            dots |= {(1, -5), (2, -4), (4, -5), (5, -4)}
        if hira in SEMIVOICED:
            dots |= {(3, -5), (2, -4), (4, -4), (3, -3)}
        left, top, right, bottom = prior.extent(dots)
        prior.need(right - left < 6 and -5 <= top <= bottom <= 4, 'Original chart paths redrawn with complete voicing at prompt scale')
        ink |= {(x - left + at, y) for x, y in dots}
        at += right - left + 2
    outline = {(x + dx, y + dy): 15 for x, y in ink
               for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (x + dx, y + dy) not in ink}
    gradient = {(x, y): max(7, 11 - (y + 5) // 2) for x, y in ink}
    extent = prior.extent(outline | gradient)[2] + 1
    bang = {(x - 48 + extent + 2, y + 2): pixel for (x, y), pixel in source.items() if 48 <= x <= 50}
    prior.need(len(bang) == 22, 'Exact source Japanese exclamation mark retained after alignment')
    out = outline | gradient | bang
    center = (prior.extent(out)[2] + 1) // 2
    return {(x - center, y): c for (x, y), c in out.items()}, reading


def prompt_treatment(base, revised, palette, source):
    colors = unpack_from('<16H', palette, 6)
    for index in WARM:
        r, g, b = ((colors[index] >> shift) & 31 for shift in (0, 5, 10))
        prior.need(r == 31 and r > g > b, 'Exact shared yellow/orange source palette')
    prior.need(colors[15] == 0, 'Exact existing dark shadow color')
    samples = {}
    for language in ('english', 'japanese', 'korean', 'digicode'):
        before, after = (rows[language][0][1] for rows in (base, revised))
        prior.need(set(after.values()) <= WARM | {15} and set(WARM & set(after.values())) >= {7, 8, 9, 10},
                   'Only original warm gradient and dark shadow, without white glyph ink')
        if language in ('english', 'japanese'):
            prior.need(after == before, 'Preserved original Start prompt')
        elif language == 'korean':
            prior.need(set(before) == set(after) and {point for point, c in before.items() if c == 15} ==
                       {point for point, c in after.items() if c == 15}, 'Recolor preserves glyph footprint and supplied dark shadow')
            _, top, _, bottom = prior.extent({p for p, color in before.items() if color == 13})
            expected = {p: 11 - min(4, 5 * (p[1] - top) // (bottom - top + 1)) if color == 13 else color
                        for p, color in before.items()}
            prior.need(after == expected, 'Korean original glyphs and punctuation with exact warm row gradient')
        else:
            reconstructed, _ = compact_digicode_prompt(source)
            prior.need(after == reconstructed, 'Digicode prompt retains exact Japanese chart names, voicing, gradient, dark edge, and source punctuation')
        samples[language] = dict(native_bounds=prior.extent(after), palette_index_counts=Counter(after.values()))
    return samples


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'native', 'assets', 'previews', 'renderer', 'report'):
        p.add_argument('--' + key, type=Path, required=True)
    for key in ('assets-sha256', 'manifest-sha256', 'renderer-sha256'):
        p.add_argument('--' + key, required=True)
    args = p.parse_args()
    prior.need(not args.report.exists(), 'Fresh report')
    work = prior.ROOT / 'build'
    _, _, compact, _ = get_assets(work / 'mode23-title-assets-r3-20261117', COMPACT, COMPACT_MANIFEST)
    _, _, old, _ = get_assets(work / 'mode23-title-assets-r2-20261117', OLD_REVISION, OLD_MANIFEST)
    assets, manifest, frames, objects = get_assets(args.assets, args.assets_sha256, args.manifest_sha256)
    source = prior.exact(args.source, prior.SOURCE)
    native = prior.exact(args.native, prior.NATIVE)
    runs = {name: [count for count, _ in frame] for name, frame in frames.items()}
    prior.need(all(frames[lang][1:] == compact[lang][1:] for lang in prior.LANGUAGES)
               and all(compact[lang] == old[lang] for lang in ('english', 'japanese', 'korean')), 'Only localized prompt pixels change since compact revision')
    source_frames = prior.source_frames(source)
    compact_qc = compact_buttons(frames['digicode'], source_frames)
    palette = prior.palette_events(source, native, assets, objects, manifest['base_address'])
    prompts = prompt_treatment(compact, frames, palette, source_frames[0])
    screenshots = preview_check(args.previews, manifest, frames, palette)
    fixture = json.loads(prior.exact(args.renderer, args.renderer_sha256))
    prior.need(fixture['assets_sha256'] == args.assets_sha256 and fixture['manifest_sha256'] == args.manifest_sha256
               and len(fixture['cases']) == 24, 'Exact 24-case native renderer checks')
    root = {}
    for language, counts in runs.items():
        for group in prior.QUEUES:
            count = sum(counts[part] for part in group)
            prior.need(count <= 128 and dict(language=language, events=list(group), actual_parts=count,
                                            actual_staged_tile_bytes=count * 32) in fixture['cases'], 'Actual typed simultaneous renderer count')
        root[language] = sum(counts[1:6])
    prior.need(set(root.values()) == {110}, 'All four five-row menus match original OAM population')
    result = dict(status='MODE23_COMPACT_TITLE_AND_WARM_PROMPT_PASS', checker_sha256=prior.sha(Path(__file__).read_bytes()),
                  assets_sha256=args.assets_sha256, manifest_sha256=args.manifest_sha256,
                  renderer_fixture_sha256=args.renderer_sha256, five_root_row_parts=root,
                  compact_redraw=compact_qc, warm_prompt_color=prompts, valid_previews=screenshots,
                  physical_game_frame_observed=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], prior.sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
