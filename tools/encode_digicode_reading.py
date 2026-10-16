"""Resolve Japanese readings to reference glyph IDs, not native ROM bytes.

Unknown kana, punctuation and kanji require explicit corpus decisions.
Latin letters already in the Japanese text use the separate Latin chart.
This catalog tool cannot establish a rendered font or a working language menu.
"""
import argparse
import json
import unicodedata
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'localization/digicode-reference.json'


def encode(reading, catalog):
    mapping = {}
    for glyph in catalog['glyphs']:
        for key in ('hiragana', 'katakana'):
            mapping[glyph[key]] = glyph['id']
    for glyph in catalog['latin_glyphs']:
        for key in ('uppercase', 'lowercase'):
            mapping[glyph[key]] = glyph['id']
    normalized = unicodedata.normalize('NFC', reading)
    unknown = sorted(set(normalized) - mapping.keys())
    if unknown:
        raise ValueError('Unresolved Japanese reading characters: ' + repr(''.join(unknown)))
    return [mapping[character] for character in normalized]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reading', help='explicit Japanese reading, never an English transcription')
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    print(json.dumps({'reading': args.reading, 'glyph_ids': encode(args.reading, catalog),
                      'status': 'reference-only; no ROM encoding assigned'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
