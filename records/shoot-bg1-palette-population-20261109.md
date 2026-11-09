# BG1 is not made uniformly black by the terminal palette fade

The proposed all-black shortcut is false for the actual Shoot BG1 assets. Its stage-bank cells use palettes0,1 and6, whereas1A95 fades palettes3,4 and5 colors2..9. There are16,130 stage-bank pixels with nonzero color index and nonblack loaded RGB444 color outside that fade set across BG1's six maps. This is an asset counterexample, not an observation of the actual terminal viewport or a claim about every other palette writer.

The check reused `render_wsc_stage_maps.tile_pixels` and the already verified source-loader/native-consumer mapping in `verify_shoot_stage_assets.py`. Source C3=C9 and DS383F select palette4983F0,512 planar tiles4984D0 and twelve504-cell maps49C4D0+i*3F0. Source resource27 maps0..5 belongs to BG0; resource28 maps6..11 belongs to BG1 descriptor020E. Both retain2-by-3 geometry. Current retained native map cells and packed pixels were compared with these exact source values:6,048 map entries and32,768 tile pixels match, including palette, bank and flip bits.

| BG1 map | Stage-bank cells | Common-bank tile0 cells | Nonzero/nonblack pixels outside the fade |
| --- | ---: | ---: | ---: |
|6|0|504|0|
|7|0|504|0|
|8|59|445|2,414|
|9|91|413|3,158|
|10|130|374|4,952|
|11|149|355|5,606|

Concrete counterexamples in zero-based cell/pixel coordinates:

- Map8 cell299, word2000: **stage-bank tile0**, palette0,color14, RGB44497D, tile pixel(7,5). Stage-bank tile0 is not the common blank tile.
- Map9 cell174, word20D4: tile212,palette0,color3, RGB444620, tile pixel(0,0).
- Map10 cell17, word20A2: tile162,palette0,color4, RGB444831, tile pixel(3,5).
- Map11 cell0, word2109: tile265,palette0,color3, RGB444620, tile pixel(0,0).

BG1's complete stage-bank color-index populations are:

| Palette | Used indices |
| --- | --- |
|0|0,1,2,3,4,5,6,7,10,11,12,13,14,15|
|1|0,1,2,10,11,12,13,14|
|6|1,2,3,4,5,6,7,8,9,10,11,12,13,14,15|

Thus indices0/1 and10..15 are actually present. The nonblack count excludes index0 and loaded black colors; merely counting an index was not used to infer visible color. Common-bank cells reference only tile0 and were kept separate: no common-tile-zero lifetime premise was introduced. The negative result already holds in the independently supplied stage bank.

All four horizontal/vertical flip combinations were applied as coordinate permutations to each of512 decoded tiles, giving2,048 equal-population checks. Actual BG1 map10 has32 horizontal-flipped cells; the other five BG1 maps have no flip bits. No vertical flips occur in the maps, but the permutation check also covers vertical and both flips. No recoloring, scaling, screenshots or visual transformation was used to establish the population.

Report: `build/shoot-bg1-palette-population-20261109/report.json`, SHA256 `4E47BAFC046D90E6EC3065D45F62D4124148587D94418231B5D134ECB1E82C93`. It contains per-map/per-palette/per-index pixel counts for all12 maps and exact source counterexamples. Source SHA256C415F227… and retained native025C1C5E… are recorded in full in the report.

Conclusion: the stated1A95 fade alone cannot make BG1 refill/horizontal-scroll differences visually irrelevant. Actual sample restrictions, other palette writers, map-clear/refill lifetime and common tile0 remain separate. No ROM, main/runtime, save, guest memory or Git state was changed; no broad RAM/stationarity proof was attempted.
