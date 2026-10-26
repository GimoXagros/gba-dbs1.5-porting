# Result art specialist review — 2026-10-26

Status: isolated pixel-specialist draft and source inspection. This is not
independent QA, a ROM installation, or a runtime claim. The native 1.5 port
remains the priority. Work is limited to this record and
`build/result-art-review-20261026`; existing builders, catalogs, ROMs, emulator
and saves were not modified or opened by this specialist.

## User decision

- Korean and Digicode victory/draw must reuse the exact **Japanese-source
  WIN and DRAW graphics**. English retains its own WINS graphic. No translated
  승리/무승부 and no Digicode WIN/DRAW replacement should be installed.
- Korean 마지막 기회! and Digicode ラストチャンス use the native gold/orange/red
  checker/dither style and complete white outline. The original exclamation
  and all twelve native digit/symbol frames remain exact.
- Every image-based Korean localization needs a pixel specialist and a
  separate independent QA agent. This worker is the specialist only. The
  generated Korean draft is not approved for native use.

## Deliverables

All paths below are relative to `build/result-art-review-20261026`.

| Artifact | Purpose |
| --- | --- |
| `source-digicode-last-chance-16x.png` | Byte-identical copy of the user's clean indexed Digicode image |
| `source-korean-last-chance.png` | Byte-identical 2172×724 user source, retained for comparison |
| `korean-imagegen-v1-draft.png` | First built-in imagegen edit, style-only and rejected as native pixels |
| `korean-imagegen-v2-draft.png` | Targeted second edit, style-only and still rejected as native pixels |
| `korean-imagegen-prompt.txt` | Exact first prompt |
| `korean-imagegen-v2-prompt.txt` | Exact second prompt |
| `source-evidence.json` | Image hashes, alpha/color counts, exact source geometry and palette |
| `source-art-data.json` | Source-backed native palette pixels and local 4bpp tiles for Japanese WIN/DRAW and the user Digicode phrase |
| `inspect-source.py` | Reproducible read-only image/source inspection and asserted data export |

The image edits were performed only with the built-in imagegen tool. Python
was used to read and inspect images and to serialize existing source pixels
as code-native palette/tile data; it did not edit or save any image. The data
export is an isolated art resource, not a complete P0 blob: tile indices are
local to each frame, and no runtime pointers or allocation are supplied.

## Digicode identity and pixel inspection

The Japanese reading is `ラストチャンス`. The single component-local small-kana
alias produces `ラストチヤンス`; neither the shared strict encoder nor the
catalog was broadened. `localization/digicode-reference.json` is the identity
authority. Its original attachment hash is still null, so this inspection
does not claim a fresh extraction/authentication of the original user chart.
The reviewed hand-placed pixel transcription and provenance limitations in
`records/digicode-glyphs.md` still apply.

| Position | Source | Render | Glyph ID | Chart row/column |
| --- | --- | --- | --- | --- |
| 1 | ラ | ラ | `jp-3089` | 4 / 6 |
| 2 | ス | ス | `jp-3059` | 3 / 3 |
| 3 | ト | ト | `jp-3068` | 4 / 5 |
| 4 | チ | チ | `jp-3061` | 4 / 2 |
| 5 | ャ | ヤ | `jp-3084` | 3 / 6 |
| 6 | ン | ン | `jp-3093` | 5 / 10 |
| 7 | ス | ス | `jp-3059` | 3 / 3 |

The existing local reference metadata maps both `ゃャ` and `やヤ` to
`/jp/ya.svg`, supporting only this explicitly recorded adapter. No Latin
translation or romanization enters the phrase.

The user's Digicode PNG is exactly 1024×256, or **64×16 at a uniform 16×
integer scale**. Every 16×16 block is constant. It has seven RGBA colors
(six native visible colors plus transparency), binary alpha, and no
antialiasing. SHA-256:
`7ED62F223587B4AEFE82ACA425F5D2B336548D3299DFA31D5E818225E7714D50`.

At logical size its entire 631-pixel visible mask matches the current
catalog phrase plus original punctuation: zero missing or extra pixels.
All 240 glyph ink pixels retain their identities, every outline pixel is
white, and all 65 punctuation pixels retain the original palette indices.
The isolated data export has bounds `[-32,-8,31,7]`, 16 native 8×8 parts,
16 unique tiles and a checked full pixel pack/decode equality. It is the
exact existing user artwork; it was not redrawn by image generation.

## Native geometry and palette

| Japanese source label | Bounds, inclusive | Visible size | Pixels | Reusable native parts |
| --- | --- | --- | ---: | ---: |
| WIN | `[-39,-11,39,12]` | 79×24 | 1508 | 30, exact-pixel repack on `(0,5)` grid |
| DRAW | `[-40,-8,39,7]` | 80×16 | 1064 | 20 |
| ラストチャンス！ | `[-51,-8,50,6]` | 102×15 | 993 | Existing source 28 |

Source WIN pixel SHA-256:
`8ECA7847B508136FCB6CF9A6B3613778E95CD6932995D6810117D4A6CB622499`.
Source DRAW pixel SHA-256:
`D47B0B69E6AA2E5FBE3AA8228EA6F3F272DBF90400BFB55C9FE79A68EE366F22`.

Warm native palette indices are 6 `#FFCD00`, 7 `#FF8B00`, 8 `#FF6A00`,
9 `#FF4A00`, 10 `#FF0000`; index 12 is white `#FFFFFF`. These RGB888 values
use the current preview's 5-bit-to-8-bit conversion. DRAW keeps its original
blue palette. Original punctuation occupies `[42,-8,50,6]`, contains 65
pixels, and hashes to
`26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8`.

Each native part is 8×8, 4bpp, with an eight-bit source tile index. The
current English last-chance bound is 28 parts; source-preserving Japanese
WIN/DRAW use 30/20 versus English 35/20. Any later installation must retain
the pointwise no-increase rule and complete digits, not simply fit a
rectangle. Reusing Japanese graphics increases KO/Digicode resources versus
the earlier compact text, so existing fixed allocations and exact-size
assertions must be reviewed again; this export does not certify those bytes.

## Korean result and remaining QA

The original Korean PNG has 46,490 distinct RGBA colors and 333,406
partially transparent pixels. Its wording reads 마지막 기회!, but edge
fringes, ragged halos and soft internal pixels prevent direct tile use.
Resizing it alone would not establish a correct native grid.

Both imagegen edits retained the intended wording and warm checker colors
visually, but neither met the native-pixel requirement. V1 contains 43,522
RGBA colors and 453,373 partial-alpha pixels. V2 contains 43,533 RGBA colors
and 342,978 partial-alpha pixels; both remain 2172×724. V2 is the preferred
style draft only. Neither is an approved font mask or a trustworthy source
of exact Hangul pixels. No generated bitmap is installed or included in the
native art-data export.

Independent QA must inspect exact Hangul structure and all seven Digicode
identities against source references, the complete white edge/counters,
native-size readability, palette and integer grid, and original exclamation.
A final Korean sprite still needs deterministic source-grid authoring after
art approval. The old builder/catalog/verification/budget/manifest consumers
must then be changed together by their owner; this record does not alter or
supersede their frozen artifact claims.

Skipped: ROM integration, runtime/emulator/save access and independent QA.
Risk: generated Korean drafts still have antialiasing and are not native-ready.
