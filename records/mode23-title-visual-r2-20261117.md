# Mode23 title visual revision 2

The user reported crowded Digicode lettering and a mismatched thin English COLLECTION label. Revision 1 remains immutable. This revision is an isolated asset dependency, with no ROM or main changes by the asset builder.

## Digicode clearance

The previous full white button border left no spare row beside fourteen-row voiced glyphs. An eighteen-row solid bordered button would need three native eight-pixel tile rows and exceed the simultaneous five-row sprite budget. Revision 2 uses a sixteen-row black backplate with a separate existing blue selection marker and no enclosing white text border. All catalog ink pixels and accent marks remain, with two blank columns between glyphs and one completely dark row above/below their maximum ink extent. Every panel begins at local X=-52; every text string starts at X=-30. Thus markers and text starts align across the five root choices. Variable right edges retain at least six blank columns after the text.

The widest root panel is 104 pixels, centered around the existing X=112 menu anchor. Root rows collectively use 116 native parts / 3712 staged bytes, below 128. No overlay is added. Japanese readings, the explicit small-kana normalizations and the Latin D-ARK / Ver exceptions are unchanged. The absence of a full border is an intentional visual adaptation, not a source geometry claim.

## English typography

The first five English layouts are unchanged. Added labels now use exact retail seven-row, two-pixel-stem glyph pixels for 1/2/P/B/A/T/L/E/O/I/N/S/D/R/K. Their source rectangles are recorded in the asset manifest. C is derived from the existing O by removing its middle right stem. Missing G/H/M/V/5/period are explicit matching-style pixel extensions, not claimed to come from an identical commercial font. COLLECTION uses the original O/L/E/T/I/N and derived C, with the same seven-row height and bold stroke width as 1P BATTLE and OPTIONS. All other added English menu labels use the same atlas.

## Frozen prepared output

- Builder `tools/build_mode23_title_assets_r2.py`: 423FB5D13C4402F3F057B38FF5681F2B89A915D53E3FC489FB8CAFCE18EE515B.
- Visual helper `tools/mode23_title_visual_layout.py`: 8F47E1A2291E3B21DEB0AD9567F2165249F9FD10ECAB4E02B49F35CC0948209C.
- `build/mode23-title-assets-r2-20261117/assets.bin`: 0633125FE39EC15C2421BDF9A560554A9ED240CCD75EFB1ADF9C9F3D82FF486C.
- Manifest: 1D9CC9E4F22AEF744F6CDAD318D2F90E4A98FD0452386D4F3CB61FDABDBC7756.
- Native-size preview `build/mode23-title-preview-r2-20261117/root-menus.png`: 88AD8A067572F0A46BAF64BCD14C3EFB6C93CDF3EB127DF103434987A0EB857E.

The parent inspected the first open-panel proposal and requested fixed left alignment, now incorporated. These deterministic pixel previews are not emulator screenshots. Independent final spacing/pixel/native-consumer QA is pending. The source E6 text task and mode22 remain separate unfinished content; this asset revision does not claim full title or port completion.
