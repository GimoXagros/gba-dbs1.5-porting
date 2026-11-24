# Fourth opening pair and Start timing

The fourth opening ending now uses the same two actor records as the WonderSwan Color original. Both actors' silhouettes, interior colors, and visible palette entries match in cold playback. Pressing Start in the first added linear scene reaches the title in 1.33942 seconds on GBA and 1.33825 seconds on WonderSwan Color.

## Fourth ending

The fourth ending is the fourth idle pass through the opening, with incoming choice value 3. WSC instructions at file offsets `7593D1` and `7593FD` pass a table displacement of `03C0` and selectors 13 and 14 to `558C:4CCC`. Its constructor multiplies the selector by 32 and adds that displacement. The resulting rows in the 1.5 table at `740000` are **43 and 44**. The previous GBA presentation selected the same numbers in a view built from rows 37 and 38. That view started at record 24 of the earlier table. The 1.5 view starts at record 30.

The existing GBA actor constructor at `08088250` uses the same stride. Changing its shared fourth-ending table literal at file offset `5B4254` to `0860B000` selects the existing native conversions of both original records. No new actor assets are required. Their source palette blocks begin at file offsets `3D7580` and `3D75B0`. On both systems the corresponding 15 visible OBJ colors for each actor match the expected RGB conversion in physical palette memory.

Two windowless cold runs left the controls idle until the fourth return to title (WSC frame 29493, GBA frame 23902). At callback age 16, the entire visible raster of each actor matched after position alignment and normalization to the original four-bit channels, including all 1,307 left-actor pixels and 1,326 right-actor pixels. At GBA ages 32 and 48, the left actor also matched the original poses at ages 40 and 60 (1,379 and 1,462 pixels). The right actor appears at the identical screen coordinate on source age 20 and GBA age 16. The check separately records positions; it does not assert an identical movement path on every frame.

## Start skip

The WSC handler writes 48 and zero to the terminal fade's duration and elapsed fields at `0300:0916` and `0300:0918`. Its terminal test reads those same fields at source file offset `75A227`. The native retail GBA skip stores 38 and zero at `0300267C` and `0300267E`. The added linear scenes previously wrote into an unrelated field at `03002338`; the first terminal callback then used a zero duration. The new shared handler points at the two fields read by `08087E74`.

| Cold run, ordinary Start in callback 8 | Start | Title | Frames | Elapsed |
| --- | ---: | ---: | ---: | ---: |
| WSC original | 1972 | 2073 | 101 | 1.338250 s |
| GBA v93 before repair | 1690 | 1732 | 42 | 0.703194 s |
| GBA after repair | 1690 | 1770 | 80 | 1.339417 s |

The measured difference after repair is 1.167 ms. Rates use 3,072,000 clocks per second with 256 × 159 clocks per WSC frame, and 16,777,216 with 280,896 clocks per GBA frame. Both cold skips captured the first and second terminal callbacks' duration and elapsed fields every frame. The observers generated ordinary controller input and used no supplied save or guest-memory writes. The older five-choice opening validation is recorded in `records/opening-five-choice-playback-20261124.md`.

## Reproduction

`tools/build_opening_choice_skip_fix.py` takes `--source`, `--input`, `--input-sha256`, `--owner`, `--owner-sha256`, and a fresh `--output` directory. It checks the underlying instructions, resident table data and original literal values before applying its two word writes. The full-image inverse reconstructs the exact parent ROM.

`tools/run_opening_playback.py --rom ROM --output FRESH --choice-detail` captures the fourth idle ending. Add `--skip --limit 4500` for the separate ordinary skip. On GBA pass `--expected-sha256` with the candidate's full hash. `tools/verify_opening_choice_skip_fix.py --source WSC --prior PARENT --image CANDIDATE --owner CANDIDATE_MANIFEST --report FRESH_JSON` validates each image. Adding all four capture arguments (`--wsc-art`, `--gba-art`, `--wsc-skip`, `--gba-skip`) independently checks both screen contents and both measured timings. The matching reference and candidate capture directories are under `build/opening-choice-corrected-{wsc,gba}-{art,skip}`.

| Standalone evidence | SHA-256 |
| --- | --- |
| v93 parent GBA | `D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99` |
| Parent owner | `55390CB7C04E02AFC82BF38F9574BBAB234AC4E3B9316876F6E90D61DF6C553D` |
| Corrected GBA | `31344FA2884010B5C03AE59975B8671EB4BA4A666421B036CF98B7C53BC97853` |
| Corrected owner | `FB4A3CE86EC18D2A8C27FEF97573122F55A9B7682A243C462C87693ECE1D7FA9` |
| Image and actual playback report | `728CB595CAE20F9E8DD1C3DA565FB452CF93541E9287F12B1EEA29EC09BE47FF` |
