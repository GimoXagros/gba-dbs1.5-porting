# Mode23 standalone background assets — independent verification

The four standalone asset files pass independent original-source verification. `tools/verify_mode23_background_assets.py` is SHA-256 `5CD9B8B560A7380A0558BC9BE7D7871AA534246DCDBF037AD05BCD6837E33542`. The report `build/mode23-bg-independent-20261117/report.json` is `F8C50ACBC289402F43A2FC92C92386E651914B7B0690ED8A3EBDD561A3FE4AC1`. It binds author manifest `2FCDB897F0CE4E6A2D1BE57E69EA18359AB7950A50C8A77C0DE2698E8BE67DDC` and original WSC1.5 `C415F227…`.

The bounded source helper at785CEA selects bankC1 and DS3F73. Its exact copy operands resolve the 54 tiles at41F830 and the 15 copied colors at41FEF2. The checker independently compares all 3,456 planar source pixel indices with the packed tile output. It imports no author conversion functions.

A small straight-line argument decoder derives the eight rectangle calls from785D22–785DCE. The copier7530B9 supplies 32-cell horizontal wrapping through its AND3F/ANDFFC0 address calculation. Applying the eight 16×8 rectangles from pattern41F730 covers every cell of the 32×32 map exactly once, including the rectangles starting at x24. All 1,024 converted words match. Their bank1 indices become native relative indices512–565; no native character base or VRAM ownership is selected by this result.

The caller at74AEAE starts at source paletteFE00 and processes16 colors. Instructions74AEB7/74AEB9 shift right once and mask0777, which equals `(source & 0x0EEE) >> 1` for all65,536 possible input words. Each of the 15 exported bright colors and its dimmed counterpart matches independent RGB444 conversion. Dimming occurs in source channels before native conversion. Neither30-byte output invents color0: the source inherits that value, and the future native caller must also apply its dimming semantics.

| File | Bytes | SHA-256 prefix |
| --- | ---: | --- |
| tiles.bin | 1,728 | C6E61F2F |
| map.bin | 2,048 | E8CBC32B |
| palette.bin | 30 | 99C6CE91 |
| palette-dim.bin | 30 | FDEDB07E |

This verifies an extracted dependency only. It does not install ROM data, allocate native private state or VRAM, expose a menu entry, implement mode23, or establish visual/runtime behavior. The earlier large callback graph was not repeated, and frozen main6479 and palette gatesC095/852F were not modified.

```powershell
python tools/verify_mode23_background_assets.py --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --assets build/mode23-bg-assets-20261117 --report build/mode23-bg-independent-20261117/report.json
```

Use a fresh report path when reproducing the check.
