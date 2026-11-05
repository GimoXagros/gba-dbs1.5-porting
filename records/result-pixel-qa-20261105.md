# Independent native result-pixel QA — 2026-11-05

**PASS as isolated art data:** the fresh 102×16 Korean `마지막 기회!` mask is
readable at native size, palette-exact and tile-ready. Japanese WIN/DRAW and
the existing supplied Digicode image remain exact. This review approves these
specific art bytes; it does not approve a ROM allocation or installation.

The QA agent is separate from the pixel producer. No producer code, font helper
or encoder is imported by `tools/verify_result_pixel_art.py`; no producer image,
ROM, catalog or localization builder was edited. The checker reuses the earlier
independently authored source decoder, then adds new mask, image and structure
checks. No emulator or supplied save was opened.

## Frozen reviewed artifacts

- Art directory: `build/result-pixel-art-20261105`.
- `source-art-data.json` SHA-256:
  `7FB3925216D8E80DE8410970C2E4ACEFD314C1E675DD0FCB1973C342BDFE00B0`.
- Korean coordinate/palette pixel SHA-256:
  `124F00001D3C12A36C3336049D28BAFEE6EC3321C975ADAE0D072C15D9946917`.
- Final report: `build/result-pixel-qa-20261105/independent-art-qa-final.json`,
  SHA-256 `B125AEB3F90433425D6C9E2A8349916770A882903DE05240562A5A192EF2E69C`.
- The earlier `independent-art-qa.json` is retained as superseded evidence.
  The final report additionally checks the normalized previews, all eight
  1×/8× image grids, authored ink and specific Hangul counters/components.

The producer confirmed the pixel data frozen before final QA. Preview-only
normalization replaced hidden transparent RGB with black; it did not alter
the Korean mask, visible colors or tile data. Current Korean previews are
RGBA with empty pixels exactly `(0,0,0,0)`, and all alpha values are 0 or 255.
There is no opaque lime background or antialiasing in the reviewed files.

## Independent results

| Asset | Reviewed result |
|---|---|
| Korean last chance | 102×16 canvas, bounds `[-51,-8,50,7]`, 1,059 visible pixels, 26 parts / 26 tiles; limit 28 |
| Korean body | 440 ink pixels and 554 exact one-pixel white outline pixels |
| Original exclamation | All 65 palette-index pixels exact at `[42,-8,50,6]`; columns 40–41 empty |
| Word spacing | Five fully transparent columns `-1..3` between 막 and 기 |
| Counters | 마: 16 transparent pixels; 막: 6; 회: 10, all remain open after outlining |
| Japanese WIN | Exact 1,508 source pixels, 30 native parts; no added S |
| Japanese DRAW | Exact 1,064 source pixels, 20 native parts; original blue palette |
| Digicode last chance | Exact supplied 631-pixel image, 16 parts; unchanged seven-glyph reading and punctuation |
| Original digits/symbols | All 12 source/native frames independently agree, 46 parts total; no new resource layout claimed |

The checker follows the actual WSC P0 atlas descriptor and planar tiles,
handles both flips and earlier-part overlap priority, independently converts
the source palette to native words, and re-decodes every exported 4bpp tile.
Exported pixel lists, decoded tiles, native palette and all eight previews
agree at every visible pixel. The 8× previews contain exact uniform integer
blocks. No resampling or color quantization is accepted as mask authorship.

Hand-constructed decoder checks cover nibble order, planar bit order, both
flips and overlap priority. Four deliberately altered Korean payloads are
rejected: recolored punctuation, missing outline pixel, occupied punctuation
gap, and non-native ink index. The authored 102×16 binary ink PNG and all five
glyph ink populations exactly match the colored body mask.

## Visual review

The actual Korean 1× and 8× images and binary mask were viewed. All five
syllables read `마지막 기회!`; the wider word gap is visible. The ㅁ counters
in 마 and 막 remain open. 막 retains its bottom ㄱ; 회 retains its top ㅎ,
lower ㅗ stem/bar and distinct full-height right ㅣ. The checker also verifies
those final ㄱ / ㅗ / ㅣ pixels and the transparent counter populations.

The warm yellow/orange/red progression and grid-aligned checker texture are
coherent with the native reference style. The body has a complete white edge
without detached fringes. The exact original exclamation is visually distinct
and separated from the word. Japanese WIN/DRAW and Digicode enlarged images
were also viewed against the previously reviewed source art. This is a visual
judgment on the frozen mask, not a promise of identical font or checker pattern
geometry to the Japanese lettering.

Reproduce with the project Python and:

```text
tools/verify_result_pixel_art.py
  build/result-pixel-art-20261105/source-art-data.json
  <original-USA.gba> <original-WSC15.wsc>
  build/result-art-review-20261026/source-digicode-last-chance-16x.png
  build/result-pixel-art-20261105/korean-last-chance-1x.png
  build/result-pixel-art-20261105/korean-last-chance-8x.png
  <fresh-output-report.json>
```

Skipped: ROM integration/allocation, runtime placement, full-scene OAM/timing,
emulator, save and hardware checks. Risk: the old Korean/Digicode resource
allocations and catalogs remain stale; passing art must not be inserted into
those old blobs without the separate resource/integration proof. Original
Digicode-chart authentication remains limited to the frozen local references
and exact supplied image already documented in the prior QA.
