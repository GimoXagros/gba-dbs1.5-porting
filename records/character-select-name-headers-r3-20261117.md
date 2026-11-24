# Korean character-name spacing revision

The user requested 1–3 pixels of separation because the Korean syllables were difficult to distinguish. Revision 3 places **two actual background columns between each syllable's complete ink and outline bounds**. It preserves every pinned BDF glyph, its full one-pixel outline, native palette indices, vertical position, frame and checker pixels. The earlier r1/r2 tools, assets, C956 component and reports remain frozen.

The old outline edges touched or overlapped; therefore two genuinely empty columns require three additional advance pixels per boundary. Two-syllable names grow from17 to20 pixels, three-syllable names from25 to31, and Terriermon's four-syllable name from33 to42. All fit the original header interior with ample side clearance. No letter is scaled or redrawn.

EN, JA and Digicode are byte-identical to revision2: 45 unchanged headers. The approved Digicode portrait spacing and voiced marks are untouched. All 15 changed headers retain the protected native y0 frame and checker columns, use only existing native colors, and continue to occupy exactly768 bytes. There are no added sprites, palette writes or persistent state.

- Builder `tools/build_character_select_name_assets_r3.py`: `FE760D37B4F3091660BDB269432860CB85F94BB2C658F30DDCC5CD394E8AED31`.
- Assets `build/character-select-name-assets-r3-20261117/manifest.json`: `7F844AD8AA1672BE95EBBCD241AEF542DF2E9EA97D99A24D6CC96C2B81343204`.
- Before/after previews in that directory: `korean-before-after-native.png` and `korean-before-after-3x.png`. Full four-language sheets and all60 full portrait previews are also included.
- New checker `tools/check_character_select_name_r3.py`: `04810E72F7A5EFEE27687B3A8F315E456EC40AF574B324142981A2315BCDC377`.
- Author result `build/character-select-name-author-r3-20261117/report.json`: `845A3181FAD9F373253FBE57664699CE5D7236B145E4EAD492A1ECDD6489F94A`.

The affected-pixel check independently decodes the pinned BDF rows, reconstructs each complete glyph outline, and compares3998 visible glyph/outline pixels across the15 Korean headers. Every boundary has exactly two background columns over all15 interior rows. No clipped glyph or altered protected pixel is accepted. The checker also verifies the other45 headers are exact r2 bytes.

The isolated header component now uses final title r4 `280202556B6DC6AD624718A9F693C0466F2C6287F1A7681C46AFDB06D853D58B`, with the accepted compact Digicode menu and warm KO/DG start prompt. Its title owner manifest is `91618BDC7A28BB36A829AABDD19271CDCB66747B305917E5174968AC38D9F412`. Historical C956, the r1/r2 headers and the primary builder remain unchanged.

New `tools/build_character_select_name_scene_r3.py` SHA `B2881B40BD4D07E3D9F7779E8AC3625A7272C45373ECA4D88A5E26A12984B731` reuses frozen strict builder6DA9 with only the new input/title/asset pins. The full scene reservation, all prior scene/title allocations and every conservative inbound target are still excluded. It emits63 writes /46,428 declared bytes /34,674 changed bytes, with a whole-image inverse to28020255. No new OAM or persistent RAM is introduced.

- Final isolated ROM `build/character-select-name-scene-r3-20261117/component.gba`: `9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5`.
- Manifest in that directory: `8D4FC0A9973981D40FCA86CC639CF35D49AF580C13CC10B9810CAAB4D7636B43`.
- Whole merged-image allocation census: `090A1B6F23D091B4A58F70A18DC25DBB1C65D96FB6526D882A302CE575567C5B`.
- Installed checker `tools/check_character_select_name_scene_r3.py`: `518C2F1493FDC7694FE469FA0CB4307989E0F38437A65EF0A21DC5B48362475D`. It is exactly frozen3FE4000E with the two input hashes rebound.
- Installed author result `build/character-select-name-scene-author-r3-20261117/report.json`: `CC0D7969E214130E8EC0B603E0755CB26B210130C64DC4FBD16A8A1121B179EF`.

All960 actual native loader/getter/helper/DMA-setup/tail cases pass on the final composition. The pointer table contains all60 exact r3 headers; native body/palette/cache and returned registers/flags remain unchanged. DMA transfers are modeled from real MMIO setup. Independent review and live capture remain separate requirements; no game emulator was launched by this work.

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_character_select_name_assets_r3.py --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --native build/shoot-child-contact-20261117/component.gba --font 'C:/Users/김기호/Downloads/JUS/jus-kr-project/local/vendor/galmuri/dist/Galmuri11-Condensed.bdf' --license 'C:/Users/김기호/Downloads/JUS/jus-kr-project/local/vendor/galmuri/dist/LICENSE.txt' --output-dir build/character-select-name-assets-r3-fresh
python tools/check_character_select_name_r3.py --before build/character-select-name-assets-r2-20261117 --after build/character-select-name-assets-r3-fresh --font 'C:/Users/김기호/Downloads/JUS/jus-kr-project/local/vendor/galmuri/dist/Galmuri11-Condensed.bdf' --report build/character-select-name-author-r3-fresh/report.json
python tools/build_character_select_name_scene_r3.py --input build/mode23-title-scene-r4-20261117/component.gba --assets build/character-select-name-assets-r3-fresh --scene-owner build/mode23-scene-v88-r3-20261117/manifest.json --title-owner build/mode23-title-scene-r4-20261117/manifest.json --output-dir build/character-select-name-scene-r3-fresh
python tools/check_character_select_name_scene_r3.py --before build/mode23-title-scene-r4-20261117/component.gba --after build/character-select-name-scene-r3-fresh/component.gba --owner build/character-select-name-scene-r3-fresh/manifest.json --assets build/character-select-name-assets-r3-fresh --report build/character-select-name-scene-author-r3-fresh/report.json
```
