# Independent result-art QA — 2026-10-26

**Decision: Japanese WIN/DRAW and the supplied Digicode asset pass as isolated
art data. All three Korean images fail native-asset readiness. No asset is
approved for immediate ROM installation.** The native 1.5 port remains the
priority; this review does not require graphics integration now.

This reviewer is separate from the result-art producer. Scope is this record
and `build/result-art-qa-20261026` only. No builder, catalog, allocation, ROM,
emulator, save, or main implementation file was changed.

## Asset decisions

| Asset | Verdict | Independently observed reason |
| --- | --- | --- |
| Japanese-source WIN for KO/Digicode | **PASS — art data only** | Exact 1,508 source pixels, complete 79×24 bounds `[-39,-11,39,12]`; reads **WIN**, without S. Exported 30 parts/28 tiles decode exactly to the WSC source. |
| Japanese-source DRAW for KO/Digicode | **PASS — art data only** | Exact 1,064 source pixels, complete 80×16 bounds `[-40,-8,39,7]`; original blue palette and white edge retained. Exported 20 parts/20 tiles decode exactly to the WSC source. |
| User `digicode-last-chance-16x.png` | **PASS — art data against frozen local references** | Exact 64×16 logical grid, 631 visible pixels, seven verified glyph placements and full original 65-pixel exclamation. Exported 16 parts/16 tiles reproduce every user-image palette index. Original user-chart authentication remains unavailable. |
| User Korean source PNG | **FAIL — native asset** | Correct readable wording, but 46,490 RGBA colors, 333,406 partial-alpha pixels, 313,992 visible pixels outside the permitted native RGB set, and nonuniform 2× blocks. |
| Korean imagegen v1 | **FAIL — native asset; rejected** | Wording readable, but 43,522 RGBA colors and 453,373 partial-alpha pixels. Ragged outline fringes, stray fragments and non-native checker cells remain. |
| Korean imagegen v2 | **FAIL — native asset; rejected** | Wording readable, but 43,533 RGBA colors, 342,978 partial-alpha pixels and 315,294 visible pixels outside the native RGB set. Cleaner style does not constitute an authored native pixel mask. |

Korean source, v1 and v2 were all viewed directly. The supplied Digicode image,
existing reference comparison and independently decoded source render were
also viewed. The source image and both generated images visibly read
**마지막 기회!**: five Hangul syllables, a word space after 막, and an
exclamation. That high-resolution wording pass is not a native-size Hangul
readability pass. The white fringes around the Korean counters/outer strokes,
soft checker cells, and inconsistent edge fragments are visible defects,
in addition to the numerical failures.

## Independent method and evidence

`build/result-art-qa-20261026/verify-art.py` imports only the Python standard
library and Pillow. It imports no producer, analyzer, encoder or project font
helper. Pillow reads images; no image was edited or saved by Python. The
HTML evidence renders independently decoded existing source pixel data.

The checker reads the actual pinned WSC1.5 and retail GBA files, follows the
WSC P0 atlas descriptor, decodes its bitplanes, applies native H/V flips and
earlier-part priority, and compares every source pixel with both the exported
pixel list and a fresh decode of the exported 4bpp tile bytes. Hand-constructed
assertions exercise nibble order, bitplane order, both flips and overlap
priority. Palette words are independently converted from WSC to GBA and
compared with the actual native palette before checking image RGB values.

| Input | SHA-256 |
| --- | --- |
| WSC1.5 source | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| Retail GBA | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |
| Supplied Digicode image | `7ED62F223587B4AEFE82ACA425F5D2B336548D3299DFA31D5E818225E7714D50` |
| Supplied Korean source image | `7BAAFDA04933BD702F9B13BC42649EEC419F6C030E203891E5FC5ACD84A7E997` |
| Korean v2 | `B4053FC4BD5D28016C97A95AEDF5CCA6AFB5FF435FBE6AEB3C468268ECBEF350` |

The producer's retained source PNGs are byte-identical to the two actual
Desktop files. The QA JSON records the tested export's own hash and complete
counts. Evidence files:

- `build/result-art-qa-20261026/independent-art-qa.json`
- `build/result-art-qa-20261026/independent-source-review.html`
- `build/result-art-qa-20261026/verify-art.py`

Reproduction from the repository root:

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 'build\result-art-qa-20261026\verify-art.py'
```

The run completed successfully. The browser-rendered source review was
visually inspected inline. A requested screenshot file was not saved because
the browser tool restricts save destinations to its configured workspace
roots; the HTML remains reproducible.

## Digicode identity, color and punctuation

| Position | Source kana → rendered kana | Catalog identity | Chart row / column |
| --- | --- | --- | --- |
| 1 | ラ | `jp-3089` | 4 / 6 |
| 2 | ス | `jp-3059` | 3 / 3 |
| 3 | ト | `jp-3068` | 4 / 5 |
| 4 | チ | `jp-3061` | 4 / 2 |
| 5 | ャ → ヤ | `jp-3084` | 3 / 6 |
| 6 | ン | `jp-3093` | 5 / 10 |
| 7 | ス | `jp-3059` | 3 / 3 |

The seven glyph placements were reconstructed from the frozen MSB-first font
row data and compared against the actual user image, not the export's glyph-ID
claims. The six distinct local SVG references were read, hash-checked against
their reference manifest and visually compared. ラ retains its upper/lower
counter structure; ス retains its spiral and tail; ト its central vertical
and crossing loops; チ its two upper stems and lower return; ヤ its diagonal
and lower enclosure; ン its box and crossed interior. Both ス occurrences
match the same glyph geometry. These remain narrow pixel transcriptions.

The frozen reference metadata explicitly maps both `ゃャ` and `やヤ` to
`/jp/ya.svg`. This supports only the already-recorded phrase-local alias;
it does not broaden the strict encoder. The original user chart has no
available file/hash, so this PASS certifies consistency with the frozen local
reference and supplied image, not a newly authenticated original chart.

All 16×16 display blocks are uniform. Alpha is binary, all visible RGB values
are native, and there are exactly seven RGBA colors including transparency.
The body has 240 ink pixels and 326 complete one-pixel white outline/counter
pixels. The native punctuation contributes 65 more pixels. There are zero
missing/extra mask pixels, zero incorrect outline pixels, and zero punctuation
pixel/color differences after a horizontal translation only.

The warm body uses native indices 6/7/8/9/10, respectively `#FFCD00`,
`#FF8B00`, `#FF6A00`, `#FF4A00`, `#FF0000`; white is index 12 `#FFFFFF`.
The user image visibly preserves the warm checker/dither progression. The
exclamation's original logical bounds are `[42,-8,50,6]`; its independent
palette-pixel hash is
`26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8`.
The generated Korean exclamation is not approved as a replacement for it.

## Native budget boundary

Actual retail text frame counts are WIN/DRAW/LAST CHANCE = **35/20/28**.
Reviewed Japanese WIN/DRAW plus supplied Digicode are **30/20/16**. Each
corresponding text frame is no larger than its retail counterpart, and every
export uses legal 8×8, 4bpp parts with bounded coordinates and eight-bit tile
indices. All twelve independently decoded native digit/symbol pixel maps
equal the WSC source; those frames contain 46 parts in total.

A conservative Digicode resource calculation retains all 91 original native
tiles and every original digit array, then appends only distinct reviewed
WIN/DRAW/Digicode tile bytes. It needs **135 tiles and 4,912 bytes**, within
the 256-tile index domain but **576 bytes beyond the previous 4,336-byte
Digicode allocation**. This calculation is a feasible resource-size example,
not a lower-bound proof or a final resource layout. The export itself supplies
no pointers or allocation. It must not be copied directly into an old blob.

The old KO/Digicode 6/8 and 8/10 heading counts, fixed allocations, expected
hashes and artifact-size assertions are stale for the user's new shared
WIN/DRAW policy. A later integration owner must update the catalog, shared
builder, independent verifier, budget/manifest consumers and allocations
together. Component part-count nonincrease does not certify a newly built
whole scene, full allocation ownership, runtime placement or timing.

## Earliest concrete Korean fix

Author a fresh **1× integer glyph mask** for `마지막 기회`, using the draft
only as visual direction. Do not accept a resize, color quantization or alpha
threshold of the large generated image as glyph authoring.

Use an initial **102×16 logical target**, bounds **`[-51,-8,50,7]`**, and pack
on the **`(-56,-8)`** 8×8 grid. This spans at most 14 columns by two rows:
**28 parts maximum**, including punctuation. It keeps the Japanese source's
horizontal extent and gives one row of outline allowance. It is a proposed
authoring boundary, not a completed or approved mask.

1. Keep the five syllables distinct: 마 = ㅁ+ㅏ, 지 = ㅈ+ㅣ,
   막 = ㅁ+ㅏ+ㄱ, 기 = ㄱ+ㅣ, 회 = ㅎ+ㅗ+ㅣ. Preserve the ㅁ/ㅎ counters,
   the 막 final ㄱ and the 회 right-hand ㅣ at native size. Leave a visibly
   wider word gap between 막 and 기 than the inter-syllable gaps.
2. Author body ink inside `y=-7..6`; a complete one-pixel white edge can then
   remain inside `y=-8..7`. Use only native warm palette indices 6–10 and
   white 12 with fully transparent empty pixels. Place checker cells on the
   same 1× grid, with yellow at the top and red at the bottom. Remove every
   detached fringe and check counter gaps explicitly after the white edge.
3. Keep the outlined body at or left of `x=39`. Leave `x=40..41` clear, then
   copy the original **65 palette-index pixels** of `!` unchanged at
   `[42,-8,50,6]`. Do not re-author, recolor or rescale the punctuation.
4. Review the authored result at 1× and an integer enlargement. Require all
   five syllables/counters to remain readable, a palette-exact 4bpp roundtrip,
   binary alpha, complete white edge and no more than 28 actual emitted
   parts. Recheck the full assembled resource, all twelve digits and scene
   budget before any installation.

Skipped: emulator/save access, ROM installation, live scene/OAM timing and
original-chart authentication. Risk: Korean remains rejected native art;
passing source art still requires revised allocation and integration checks.
