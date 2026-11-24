# Character-select name headers

The isolated assets provide EN, JA, KO and Digicode labels for all 15 physical character IDs. They change only the 96×16 name header of each 96×128 portrait atlas. No ROM, main builder, palette, OAM layout or persistent state was changed by this work. Allocation, integration and independent QA remain separate gates.

## Source and native ownership

- WSC 1.5 SHA `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`. The actual portrait loader is `779EEF..779F47`, SHA `021784FBE892E4F962762D13AFE5BADC2E3CA50EAA03ACA47DB4106BF651FD06`. It reads the 15 palette/tile offsets at `779D68`, bank/segment selectors at `779DA4`, segment table at `779DC2`, copies palette to FE20 and tiles to 9780. Japanese tiles are the base view; the original English view follows by `1800`. The retained source branch selects Japanese.
- Native baseline is frozen `5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC`. `0808329C` enters the existing `084A5C40` adapter. Its 15 palette/tile pointer pairs begin at `084A5BC0`. `4A5C40..4A5C93` SHA `638AE6ECA1E212700B5A5ED467806582627DBF4D69ED5E8E141D5EF27ACD03F6`.
- Actual palette destination is **05000020**, 32 bytes. Actual tile destination is **06005780**, 6144 bytes, ending at **06006F80**. The 24-tile header is **06005780..06005A80**. An early analysis transcription incorrectly said 06005000; actual-loader execution rejected that address before the helper was frozen. No ROM used that draft address.
- Source JA/EN names are embedded BG tile pixels, not strings or independent sprites. Horizontal palette variants do not select another name atlas. Duplicate Agumon and Guilmon identities keep their base names; no invented “Black” or evolved labels are added.
- Native ID11 Impmon has a commercial portrait and palette different from the source atlas. Its entire 5376-byte body is retained. Source name ink/shadow indices 2/3 are mapped to the existing native 14/2. White is exact 7FFF; the shadow adopts the commercial palette. This is source glyph geometry with a native palette adaptation, not whole-source RGB equivalence.

## Approved labels

| ID | English source | Japanese source | Korean | Digicode reading |
|---:|---|---|---|---|
| 0 | GUILMON | ギルモン | 길몬 | ギルモン |
| 1 | TERRIERMON | テリアモン | 테리어몬 | テリアモン |
| 2 | RENAMON | レナモン | 레나몬 | レナモン |
| 3 | VEEMON | ブイモン | 브이몬 | ブイモン |
| 4 | WORMMON | ワームモン | 추추몬 | ワームモン |
| 5 | AGUMON | アグモン | 아구몬 | アグモン |
| 6 | SUKAMON | スカモン | 스카몬 | スカモン |
| 7 | AGUMON | アグモン | 아구몬 | アグモン |
| 8 | LOPMON | ロップモン | 로프몬 | ロツプモン |
| 9 | GABUMON | ガブモン | 파피몬 | ガブモン |
| 10 | AGUMON | アグモン | 아구몬 | アグモン |
| 11 | IMPMON | インプモン | 임프몬 | インプモン |
| 12 | GUILMON | ギルモン | 길몬 | ギルモン |
| 13 | PATAMON | パタモン | 파닥몬 | パタモン |
| 14 | GATOMON | テイルモン | 가트몬 | テイルモン |

The parent approved these source/established Korean labels. Digicode retains Japanese readings; small ッ is explicitly normalized to ツ under the existing project chart convention. No label here contains a Japanese Latin exception. Full chart glyph pixels and voiced marks are retained without scaling or clipping. Korean uses the pinned Galmuri11 Condensed 2.404 BDF and OFL license already used by the project.

## Protected pixels and budget

Every header keeps native row y=0 and columns x=0..12 / 83..95 byte-for-pixel identical. Terriermon's existing English frame is narrower and instead keeps columns x=0..6 / 89..95. Those masks protect 486 pixels per ordinary header and 306 for Terriermon, including checker background cells and exact palette indices. Source lettering is extracted separately from source checker bands, so language changes cannot recolor or widen the native frame. All 96×112 pixels below the header remain the original native atlas.

The standalone output contains 60 headers of 768 bytes (46,080 bytes total), a language-major/ID-minor manifest, native-size/3× nearest-neighbor sheets and 60 full portrait previews. Korean lettering includes the existing one-pixel edge. Digicode uses white ink without an added outline so all chart marks fit the 15 interior rows. Both are centered by complete pixel bounds. These assets use the original 16-color palette and add **zero OAM parts**.

## Overlay contract

`character_select_name_overlay.py` emits a 104-byte relocatable helper. The sole hook replaces `084A5C6C: E59F401C` with B to the helper, after the complete native portrait DMA. A separately allocated 60-pointer table permits scattering the header resources.

The helper saves R0..R12 and LR plus CPSR flags (60 bytes below live SP), calls the existing read-only getter `08633400`, forms `language*15+ID`, and invokes the actual `08000B84` DMA routine for 192 words to 06005780. It restores registers/NZCV, executes the displaced R4=03004710 load, and returns to 084A5C70. The native cached ID+1 store, saved-LR pop and return execute unchanged. Getter tags A0/A1/A2/A3 mean EN/JA/KO/DG; every other byte means EN. The valid physical ID domain is the same native 0..14 portrait-table domain; this helper does not clamp an invalid caller.

No new cache, language mutation or input write is introduced. Temporary freed stack bytes and the final DMA3 source/count registers differ intentionally. The native callback's returned registers, flags, SP, LR and cached selection are unchanged. Allocation must separately prove blank owned ROM spans and preserve the pointer table/getter/native caller dependencies.

## Frozen artifacts and author verification

- Builder `tools/build_character_select_name_assets.py`: `EDFF86405B6BFE5AABFDEFECAEF507CBDC016767C5888243CE6D3A979387C959`.
- Overlay `tools/character_select_name_overlay.py`: `4156DDC0A8AD9FD2B9D3C5E2B2745DEEF5E17034D98BCC32B9D83B3F94B76824`.
- Assets `build/character-select-name-assets-20261117/manifest.json`: `E97C5354601F0A3826C6A111AC83D95F0A5FEA65D7C1CA2EA1542E8C1C6B5F7E`.
- Author checker `tools/check_character_select_name_overlay.py`: `35359B1186B7EBEF8AD8D06C72EBB596A666430C9DDD3DDFF8BC0C04967D6FBB`.
- Author result `build/character-select-name-author-20261117/report.json`: `E9FF408C2FD40E87B4760226929D07ABB1C94AA80E27FC4D35C9A6594DEAAF9E`.

The author check executes retained loader/getter/DMA-setup/tail ARM for 960 identity×language×NZCV cases, all 3840 identity×tag cases, and a second code/table/data relocation. DMA3 transfers are modeled from the actual native MMIO writes. It verifies all 60 protected headers and 9159 original English/Japanese glyph pixels using a direct planar decode. This is an author fixture, not independent QA, hardware timing, installed placement or a live four-language capture claim.

Reproduce assets in a fresh directory with the bundled Python runtime (Pillow needed only for previews):

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/build_character_select_name_assets.py --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --native build/shoot-child-contact-20261117/component.gba --font 'C:/Users/김기호/Downloads/JUS/jus-kr-project/local/vendor/galmuri/dist/Galmuri11-Condensed.bdf' --license 'C:/Users/김기호/Downloads/JUS/jus-kr-project/local/vendor/galmuri/dist/LICENSE.txt' --output-dir build/character-select-name-assets-fresh
python tools/check_character_select_name_overlay.py --native build/shoot-child-contact-20261117/component.gba --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --assets build/character-select-name-assets-fresh --report build/character-select-name-author-fresh/report.json
```
