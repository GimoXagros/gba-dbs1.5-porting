"""Verify transcribed chart identities and mixed Japanese/Latin reference encoding.

This does not verify glyph pixels or native game rendering.
"""
import argparse
import json
from pathlib import Path

from encode_digicode_reading import CATALOG, encode

ROWS = ('あいうえおはひふへほ', 'かきくけこまみむめも', 'さしすせそや ゆ よ',
        'たちつてとらりるれろ', 'なにぬねのわ を ん', 'がぎぐげごばびぶべぼ',
        'ざじずぜぞぱぴぷぺぽ', 'だぢづでどー')


def verify(catalog):
    expected = {(r + 1, c + 1): kana for r, row in enumerate(ROWS)
                for c, kana in enumerate(row) if kana != ' '}
    actual = {(g['reference_row'], g['reference_column']): g['hiragana']
              for g in catalog['glyphs']}
    if actual != expected or len(catalog['glyphs']) != 72:
        raise ValueError('Japanese chart cells differ')
    ids = []
    for g in catalog['glyphs']:
        expected_id = f"jp-{ord(g['hiragana']):04x}"
        katakana = chr(ord(g['hiragana']) + 96) if g['hiragana'] != 'ー' else 'ー'
        if g['id'] != expected_id or g['katakana'] != katakana:
            raise ValueError('Japanese identity or kana equivalence')
        if encode(g['hiragana'], catalog) != encode(katakana, catalog):
            raise ValueError('Kana encoding equivalence')
        ids.append(g['id'])
    if len(catalog['latin_glyphs']) != 26:
        raise ValueError('Latin alphabet extent')
    for i, g in enumerate(catalog['latin_glyphs']):
        if (g['id'], g['uppercase'], g['lowercase'], g['reference_row'], g['reference_column']) != (
            'latin-' + chr(97 + i), chr(65 + i), chr(97 + i), i // 13 + 1, i % 13 + 1
        ):
            raise ValueError('Latin chart cell')
        if encode(g['uppercase'], catalog) != encode(g['lowercase'], catalog):
            raise ValueError('Latin case equivalence')
        ids.append(g['id'])
    if len(set(ids)) != 98:
        raise ValueError('Reference identity collision')
    if encode('デジモンAa', catalog) != ['jp-3067', 'jp-3058', 'jp-3082', 'jp-3093', 'latin-a', 'latin-a']:
        raise ValueError('Mixed source order')
    if encode('か\u3099', catalog) != encode('が', catalog):
        raise ValueError('Canonical voicing equivalence')
    for unknown in ('ゃ', '小', '。', '１'):
        try:
            encode(unknown, catalog)
        except ValueError:
            continue
        raise ValueError('Unresolved input accepted: ' + unknown)
    return {'status': 'PASS', 'Japanese_cells': 72, 'Latin_cells': 26,
            'mixed_order_and_case_equivalence': True, 'unresolved_inputs_rejected': True,
            'scope': 'reference identity/transcription only; pixels, game encoding, menus and persistence excluded'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = verify(json.loads(CATALOG.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
