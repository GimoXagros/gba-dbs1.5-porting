# Bounded Digicode pixel draft — 2026-10-23

The 98 reference identities now have a reproducible development pixel draft in
`tools/digicode_glyphs.py`: 72 Japanese cells and 26 case-shared Latin cells.
This is a bounded Options font component, not whole-game localization or a
formally certified Digicode font. It does not modify any ROM, emulator, save,
existing encoder, or language catalog.

## Provenance and review scope

`localization/digicode-reference.json` remains the identity authority. Japanese
readings are converted directly; Latin glyphs are used only for Latin characters
already present in those readings. English translation and romanization are not
conversion steps. Unknown small kana, kanji, punctuation, spaces, and digits
still fail through the existing strict encoder.

The original user chart files were unavailable to this worker. No extraction or
hash of those attachments is claimed. For shape inspection, the root worker
downloaded 98 SVGs from [cenrji's Digimoji](https://cenrji.neocities.org/digimoji/)
to ignored `local/digimoji-reference-20261021`. Each local SVG is checked against
the recorded SHA-256 before inclusion in the local comparison HTML. The metadata
SHA-256 is `F51D2F020C05CF231FE69A7784E75E150188F3034C5AB062614FC0F48C5CD765`.

The new integer-grid strokes are manually placed pixel transcriptions of these
symbols. They are not a raster export, a copied font program, or vendored SVG
geometry. “Original pixel transcription” describes the new placement of pixels;
it does not claim authorship of the underlying fictional alphabet. No license
was verified for the external SVGs, and no license or unrestricted distribution
claim is assigned to their shapes. External SVGs remain local comparison inputs.
Public redistribution rights have not been established by this work.

The final comparison was visually reviewed by the root worker across all 98
cells, with specific inspection of `え`, `ゆ`, `ら`, and `り`. Their narrow gaps
were corrected: the right stems of `え` are separated; `ゆ` has three separated
stems; `ら` has visible upper and lower counters; each of `り`'s four triangles
retains a one-pixel counter. This was accepted for bounded development Options
integration. It is not independent specialist authentication or final
native-size/hardware readability approval. Some seven-column details remain
one-pixel approximations, including the compressed arms/counters of complex
kana. The comparison remains available for review.

## Pixel and consumer contract

`font_glyphs(catalog)` returns the existing glyph IDs mapped to 16 MSB-first row
bytes. Each stored cell is 8×16 with at most seven ink columns. Total raw
monochrome storage is 1,568 bytes. The concatenated rows in catalog order hash to
`E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195`.

`text_pixels(reading, catalog, glyphs)` returns `(pixels, width)`, where pixels
use the existing native palette roles 1 for ink and 2 for edge. Placement trims
only blank side columns and leaves one clear column between adjacent glyph ink.
The maximum advance is eight pixels. Every input ink pixel and the complete
one-pixel exterior edge are preserved. There is no edge or glyph clipping.

The outlined vertical interval is `-15..0`, so consumers must pack native tiles
at `y=-15` and `y=-7`. The Korean font's `-12/-4` tile origins are inappropriate
for this font. `build_options_korean_poc.pack_tile` is reused for 4bpp packing;
there is no new native tile format. A last partial tile column is retained when
needed. The font does not allocate ROM/VRAM or choose a persistence byte.

| Reading | Width | Native 8×8 parts |
| --- | ---: | ---: |
| `しあいじかん` | 43 | 12 |
| `むずかしさ` | 38 | 10 |
| `かんたん` | 33 | 10 |
| `ふつう` | 24 | 6 |
| `むずかしい` | 34 | 10 |
| `サウンドテスト` | 55 | 14 |
| `データをけす` | 47 | 12 |
| `もどる` | 25 | 8 |
| `いいえ` | 17 | 6 |
| `はい` | 13 | 4 |
| `げんご` | 22 | 6 |
| `デジコード` | 39 | 10 |
| `ほぞんエラー` | 47 | 12 |

These are text-only counts. Original row squares remain separate native parts.
A naive nearest-neighbor 8×8 reduction has no exact bitmap collisions, but
discards stroke detail and the side pixels of the semivoicing ring. Collision
absence does not establish readability; that reduced version is not adopted.

## Native wider-object investigation

The native renderer cannot select 8×16, 16×16, or 32×16 GBA objects merely by
changing P0 entries. The checked renderer bytes `012C58..012DD8` hash to
`D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685`.
The shape/size interpretation agrees with [Tonc's OBJ attribute tables](https://www.coranac.com/tonc/text/regobj.htm);
the game-specific writes and transfer extent come from the native instructions.

- `08012CF4` stores only the computed Y coordinate to OBJ attribute 0; shape
  bits remain zero.
- `08012D18..08012D28` preserve only H/V flip from source flags; size bits remain
  zero. A P0 part therefore emits one 8×8 square.
- `08012D50..08012D94` select the source tile using its low byte and copy exactly
  32 bytes to the dynamic tile queue for each emitted part.
- `08011744..08011798` transfer exactly `OAM_count * 32` bytes to OBJ VRAM.

Wider hardware objects would need renderer, tile placement, and VBlank transfer
changes. They are unnecessary for the bounded layout below and were not added.

## Full native-screen layout feasibility

`tools/analyze_digicode_layout_budget.py` reads the existing decoded native
EN/JA layout inventory, the checked Korean resource manifest, and the checked
three-language selector manifest. It retains all fifteen actual constructor
objects with events `0,2,4,6,7,1,8,3,8,8,5,5,8,11,9`. The bound includes all
time/difficulty values, both ten-frame number objects, all four independent
arrow objects, both erase-confirmation choices, and all five common head
frames, including the twenty-part head frame. It does not assume hidden heads.

All 729,000 independent native frame assignments per entry language are
enumerated. Each is combined with four selectable-name/arrow states and one
save-error state, for 14,580,000 checked assignments across four languages.
The independent frame maximum agrees with the sum of object maxima.

For Digicode the fifteen object maxima are
`13,11,15,13,9,3,2,10,2,2,1,1,2,6,20`, totaling 110. All original five squares,
numeric frames, heads, arrows, and confirmation frames are retained.

The proposed new row omits its own decorative square consistently in all four
languages. It displays the full label, full selected name, and endpoint-sensitive
arrows. On save failure the full localized error temporarily replaces the new
row's label/name/arrows; it does not remove an original native object. Keeping
the Digicode label alongside its error would exceed the chosen limit by one.

| Entry language | Existing fifteen-object maximum | Normal row peak | Error replacing new row | Overall peak |
| --- | ---: | ---: | ---: | ---: |
| English | 80 | 103 | 94 | 103 |
| Japanese | 73 | 91 | 85 | 91 |
| Korean | 107 | 124 | 117 | 124 |
| Digicode | 110 | 127 | 122 | 127 |

Peak usage is 127 OAM parts and 4,064 staging/OBJ-VRAM bytes. This is a verified
composition proposal from decoded inputs. It does not prove that a fourth-mode
ROM, error transition, or save behavior has been installed. Final binary layout,
all-byte write ownership, runtime display, and persistence still require their
own artifact/runtime verification. Whole-game language consumers and the full
text corpus remain outside this component.

## Independent actual-resource check

`tools/verify_digicode_resource.py` independently checked
`build/options-selector-four-20261023-a/options-selector.gba`, SHA-256
`6675FB3676E5507379F6787B885C86475E9B7891386AF8EA27E1A4BA584846CE`.
It imports no font or ROM producer. The expected image is built with Pillow's
MSB-first row-byte decoding, bounding-box cropping, and `MaxFilter(3)` dilation,
then compared with every pixel decoded directly from actual ROM P0/P1 resources.

All ten Digicode text frames and all three Digicode selector label/name/error
frames match the reviewed font. All 22 untranslated native layouts retain both
their exact part arrays and pixels, including the common heads. The original
EN/JA assets and native renderer remain byte-identical. Actual atlas extents
are 132 tiles for Digicode and 153 for the selector, both within the native
eight-bit source-index limit.

The checker also recovers all fifteen actual routed constructor calls and event
immediates from the candidate instructions. Using the actual ROM frame arrays,
it re-enumerates 14,580,000 frame/row combinations and confirms maxima
`103/91/124/127` for EN/JA/KO/Digicode. The save-error case assumes the installed
state machine displays only the full error; execution of that transition remains
the root worker's runtime check. No save or emulator is accessed by this check.

Report: `build/digicode-glyphs-20261023/actual-resource-review.json`, SHA-256
`4442EAE2B77CCD89D4A87B34860070A02AC05758AC18E4FEF46C8CCF6DB6E712`.

```text
tools/verify_digicode_resource.py build/options-selector-four-20261023-a/options-selector.gba build/options-selector-four-20261023-a/manifest.json build/digicode-glyphs-20261023/font-8x16.json build/language-consumers-20261016/analysis.json build/digicode-glyphs-20261023/actual-resource-review.json
```

The same checker also passes the integrated candidate
`build/options-selector-integrated-20261023/options-selector.gba`, SHA-256
`3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C`,
built from predecessor
`F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E`.
Its actual pixels, original resources, constructor routing, and all 14,580,000
frame/row combinations pass with the same `103/91/124/127` maxima. Report:
`build/digicode-glyphs-20261023/integrated-resource-review.json`, SHA-256
`947522802723845EF01DD7090F5F39D3BF6D06BA1209FE6BDB42EE11633DA05F`.

```text
tools/verify_digicode_resource.py build/options-selector-integrated-20261023/options-selector.gba build/options-selector-integrated-20261023/manifest.json build/digicode-glyphs-20261023/font-8x16.json build/language-consumers-20261016/analysis.json build/digicode-glyphs-20261023/integrated-resource-review.json
```

## Checks and local artifacts

`tools/verify_digicode_glyphs.py` passes all 98 distinct/nonempty/bounded cells,
independent square/stroke/voicing fixtures, targeted topology gaps, NFC and case
equivalence, strict unknown/missing/empty rejection, lossless proportional ink
placement, and native 4bpp pack/unpack checks for all ten Options readings plus
selector/error and mixed-script examples. Host MS Gothic is used only for
preview captions; it is not a native font input.

Artifacts are in ignored `build/digicode-glyphs-20261023`:

| Artifact | SHA-256 |
| --- | --- |
| `font-8x16.json` | `ABDFB29C40C3C8F38BB64214B1F3695FED4774C32362A6ACC1F4EE5D90029EEA` |
| `verification.json` | `65F191BF4FE977A9CEB9867DDD7A81079985BFFBD5EBD19E44AD35318FCB683F` |
| `layout-budget.json` | `7786FFDE255662EB42BA2443AA64A273E265E6CBBC16D825A8785E9BA222FE84` |
| `comparison.png` | `341F5E7F0403C787EFE57F9C3B01AC5E8C2A5142916B5CCBF7364DAFFC73CC92` |
| `pixel-atlas.png` | `74594BA119F1E2DA7A2F694B9633AFAFB1B78AAC13E671C14533ED759F078326` |
| `reading-samples.png` | `461090768C3B8158F69C827C6A5F850969265790E900F2001275CD0FE45C3B3F` |

Reproduction (using the bundled Python with Pillow):

```text
tools/digicode_glyphs.py build/digicode-glyphs-20261023/font-8x16.json
tools/verify_digicode_glyphs.py build/digicode-glyphs-20261023 --reference-directory local/digimoji-reference-20261021
tools/analyze_digicode_layout_budget.py build/language-consumers-20261016/analysis.json build/options-korean-poc-20261021/manifest.json build/options-selector-20261023-a/manifest.json build/digicode-glyphs-20261023/layout-budget.json
```

The optional reference directory creates local comparison HTML without embedding
or distributing the external SVGs. The screenshot uses that HTML in a separate
headless browser. No supplied save was read or written.

## Follow-up evidence for the Options title's small kana

The separately investigated Japanese title is `オプション`. Its small `ョ` is
still rejected by the frozen strict encoder and is absent from the 98-cell
catalog. The local comparison metadata already records both `ょョ` and `よヨ`
as aliases of `/jp/yo.svg`; this is explicit creator-reference evidence rather
than a guessed spelling normalization.

The creator's current [mapping and renderer](https://cenrji.neocities.org/digimoji/assets/scripts.js)
were inspected on 2026-10-23. Both forms have type 0 and the same image path;
the smaller kana is explicitly named as such. The renderer uses one image
class and does not change its size for small kana. The corresponding
[stylesheet](https://cenrji.neocities.org/digimoji/assets/styles.css) gives this
class a uniform 32-by-32 box. Verified source hashes:

| Reference | SHA-256 |
| --- | --- |
| Existing local `reference.json` | `F51D2F020C05CF231FE69A7784E75E150188F3034C5AB062614FC0F48C5CD765` |
| Creator `assets/scripts.js` | `10200506E01098F46ECE866AEA110F43ED0C1AB3C7F0622C1DC7EAA8ACBA9588` |
| Creator `assets/styles.css` | `C971421253360FD97ACB2A289026DF79C6B5A9DF3D5CAD213EEE5247E2B4E58D` |

This supports an explicit title-component alias from source `ョ` to existing
`jp-3088` (`ヨ`). Such a component must retain `オプション` as the source reading
and record the alias separately, leaving all other unknown characters rejected.
It does not require new glyph pixels, a font hash change, automatic romanization,
or an English reading. No encoder/catalog change or title ROM installation was
made by this evidence review. Other small-kana mappings are not automatically
adopted. The creator files remain references; no external font or code has been
vendored and no broader font license claim is made.
