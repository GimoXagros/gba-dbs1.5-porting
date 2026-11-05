# Native result pixel production — 2026-11-05

Status: independently approved Korean native-grid art and enlarged Digicode
v2. The art-production task performed no ROM installation, emulator launch or
save access. The user explicitly authorized code-native pixel production.
A different agent completed visual and decoder QA. The approved indexed pixels
are now consumed by the isolated result-language component; current main full
builds and normal runtime remain root-owned.

The new `마지막 기회!` is authored directly at1x from explicit integer Hangul
strokes. No large image, resized draft, thresholded mask or font supplies its
shape. The former generated images remain style references only.

The logical canvas is102x16, bounds`[-51,-8,50,7]`. Five glyphs contain
440 ink pixels, and their complete eight-neighbor one-pixel white edge has
554 pixels. The visibly wider word gap retains five entirely clear columns
`-1..3`; columns40–41 remain clear before the original punctuation.
The twoㅁ counters,ㅎ counter,막 finalㄱ and회 right-handㅣ have explicit
integer-mask assertions. Visual review at1x and8x reads the full phrase.
Color is native yellow/orange/red indices6–10 with an integer-grid checker
transition; every body edge is white12. Empty pixels are fully transparent.

The65 original exclamation palette pixels are copied unchanged at
`[42,-8,50,6]`, hash
`26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8`.
The Korean frame packs on`(-56,-8)` into26 actual8x8 parts and26 local
4bpp tiles, below the28-part ceiling. A complete pack/decode roundtrip equals
all1059 palette-index pixels. Korean pixel SHA-256:
`124F00001D3C12A36C3336049D28BAFEE6EC3321C975ADAE0D072C15D9946917`.

Japanese WIN/DRAW are reused exactly from the prior approved source-art
export and compared again to the pinned WSC1.5 source decoder:1508/1064
pixels and30/20parts. Digicode reuses the exact approved64x16 user mask,
631pixels/16parts, checked against every uniform16x source-image block and
the original image hash. No new Digicode glyph shapes or alphabet policy
were introduced. Its `ラストチャンス` reading and explicitャ→ヤ adapter
remain the previously reviewed mapping.

Artifacts under `build/result-pixel-art-20261105`:

- `source-art-data.json`: existing palette/parts/tile/pixel schema with the
  new `korean` frame and `korean_authoring` ink/edge/glyph metadata.
- `korean-last-chance-1x.png` and`-8x.png`: RGBA review images.
- `korean-last-chance-indices.png`: exact indexed102x16 native palette PNG.
- `korean-ink-mask-1x.png` and`.txt`: authored binary glyph mask.
- Japanese WIN/DRAW and Digicode equivalents at1x/8x plus indexed PNGs.
- `production.json`: source/input/producer/output hashes and assertions.

Reproduction:

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/build_result_pixel_art.py
```

The generator asserts pinned original hashes, exact Japanese/Digicode reuse,
punctuation, native palette membership, binary alpha, white edge geometry,
counter/gap/stroke anchors,26-part packing and all four frame roundtrips.
Independent visual and decoder QA passed in
`build/result-pixel-qa-20261105/independent-art-qa-final.json`, SHA-256
`B125AEB3F90433425D6C9E2A8349916770A882903DE05240562A5A192EF2E69C`.
It confirms exact source Japanese/Digicode reuse, complete Korean white edge,
open counters, readable1x/8x Hangul, native palette/alpha and4bpp inverse.
The source-art export has local tile indices and supplies no ROM pointers;
`records/result-language.md` owns the subsequent resource/allocation proof.

The subsequent isolated result component and its independent verifier have
now checked all12 digit frames and the complete correlated scene budget.
Skipped here: current full-main result runtime and hardware testing. Risk:
static pixel approval does not establish in-game timing or last-chance use.

## User-requested larger Digicode revision

The original revision remains frozen. A separate
`build/result-pixel-art-20261105-dg-large` directory contains the requested
larger Digicode, its palette-index JSON/PNG,1x/8x RGBA previews and updated
dark-background comparison. Its producer is
`tools/build_result_digicode_large.py`.

The seven original Japanese-reading glyph masks recover all240 user-image
body ink pixels exactly. Each7-pixel glyph expands to12 pixels wide and
each6-pixel glyph to10; all10-pixel heights expand to14. Integer nearest
sampling acts on ink only, with two ink-gap columns between glyphs. The
complete white outline is rebuilt afterwards at exactly one native pixel,
rather than stretching the old white edge. The twoス masks remain identical.
Per-glyph source/target masks, row bytes, origins and formula are recorded
in `digicode_authoring` for independent reconstruction.

The new outlined body measures90x16, bounds`[-51,-8,38,7]`; the complete
frame remains102x16 with the same65 source punctuation pixels at42–50
and clear40–41 columns. It contains551 body-ink and633 fresh white-edge
pixels. All1249 frame pixels roundtrip through27 parts/26 unique4bpp
tiles, within the28-part limit. Pixel SHA-256:
`1382C22C3F8A2A9497A2652A1530D93F8097A4CE3991B377585749A2F75250C0`.
Korean and Japanese WIN/DRAW remain unchanged. The enlarged revision is
handed to the separate QA agent; no ROM resource or allocation is installed.

### Independent spacing correction

The first enlarged revision above is preserved as a visual HOLD: its two
empty ink columns are consumed by the two neighboring one-pixel outlines,
joining their white edges. Independent QA and the root reviewer both
identified this crowding despite the data checks passing.

The separate `build/result-pixel-art-20261105-dg-large-v2` revision uses
7→11 and6→9 horizontal expansion with three ink-gap columns. A full
transparent column now separates each pair of outlined glyphs; the producer
asserts all six clear columns. All glyphs remain14 pixels high. The body
is89x16, bounds`[-51,-8,37,7]`, comparable to the Korean body, while the
full punctuation-bearing frame remains102x16. Its496 ink/587 white-edge/
65 source punctuation pixels pack into27parts/26tiles. Pixel SHA-256:
`4F9B02D9BC03779DCB14B62B0D0EB0F5755BC0DD48B3006669E5631F4BAAC924`.
The twoス geometries remain identical and source recovery still checks
every original240 user-ink pixel. Updated1x/8x dark comparisons accompany
this revision. V1 is retained, including its producer source, and must not
be mistaken for the revised candidate. V2 independently passed
`build/result-pixel-qa-20261105/digicode-large-v2-data.json`, SHA-256
`9796301A0618FD9457E1966287D9B306423FCC2A99516E5006F565BED754E70E`.
All seven source counter topologies/order, six transparent separators,
exact punctuation, alpha/palette and native packing passed;1x/8x previews
were separately viewed. The approved enlarged revision is v2, not v1.

## Fresh-build production closure

The active main path uses `build_result_pixel_art.py --generate-data GBA
WSC15 CATALOG OUTPUT`, which reads originals and tracked masks/catalog only.
It reproduces every approved pixel hash without prior build JSON or PNGs.
The shared pure `make_digicode` function implements the same v2 expansion.
The generated JSON8BFC3960… differs from review JSON875700A7… in metadata;
all approved Japanese/Korean/Digicode palette pixels and part counts agree.
The historical default preview commands still use their retained review inputs
and are not dependencies of the fresh main build.
