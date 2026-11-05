# Source 1.5 title background: independent QA

The isolated title background passes static and captured-runtime checks. Its ROM SHA256 is `494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6`, with exact v66 predecessor `428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281`. This component changes the background; the five-label selector remains intact and the additional source menu controller/events remain separate work.

`tools/verify_title_background.py` imports no builder or conversion oracle. The final report is `build/title-background-qa-20261105/independent-final.json`, SHA256 `1D2AF8B349E42701DD85BA59B1111E1ED3C88E5AF7C7AB3B3F0DEC289800C665`. The earlier `independent-a.json` was superseded by the stronger literal-owner check.

All 408 loaded tiles (26,112 pixels), 504 map cells and 32,256 displayed pixels invert to the original source. The checker calculates WSC physical tile addresses separately for both banks, including map bit13 across 7200..A500, and compares the native index, flips and palette attributes. The used population is exactly 400 distinct tiles, indices400..799. None of the displayed pixels uses transparent index0. Six converted source palette rows and the two retained native rows are exact; source secondary palette identity is independently checked.

Positive source instructions establish C3=CA, DS=380C and selected Japanese palette/map/tile copies. Native mode3 dispatch reaches080908A0. The actual native palette consumer reads the new pointer for both physical palette05000020..05000120 and staging0201E400..0201E500. The unchanged128-halfword fade consumer reads that staging. The48-byte helper transfers tiles to06003200..06005200 and06005200..06006500, preserving flags and stack, and returns to08090938 with the original continuation LR. The18 map rows each transfer56bytes at64-byte stride into0600F000. Shared transfers, old shared artwork, the secondary palette and existing language hook are unchanged.

All five new allocation spans are FF in the exact predecessor and have no pre-existing mirrored pointers or conservative ARM/Thumb branch, literal or ADR references. The two modified literal addresses have the expected actual PC-load consumers. Two additional raw matches are positively explained: AAFF9FFA at080A8BA0 is inside the retained native tile DMA row4 payload080A8940..080AA140, established by080832B8..080832C8 and its table; the apparent Thumb branch at0809103A is the upper halfword of native ARM LDR08091038 inside the mode3 frame callback. No appearance-based data classification is used. The complete ROM inverses to v66 outside eight declared spans. Twenty-two artifact mutation controls and nine injected ownership-reference controls pass.

The parent ran the isolated component through ordinary input in a hidden emulator. Independent read-only capture verification is `build/title-background-qa-20261105/capture-a.json`, SHA256 `F9FD70BF2FC79E20E159ECEA48121A737AA16DBFE7AC62748B677FAA7BBF7873`, produced by `tools/verify_title_background_capture.py`. All captured files are checked against the original launch manifest, and the loaded8MB ROM equals the component.

Capture filenames are misleading but preserved: `prompt-*` is the settled title menu at mode3/frame3202, and `menu-*` is character selection at mode4/frame3652 after A input. The actual title screenshot was inspected. Its live VRAM contains all408 exact tiles and all504 exact map cells; source palette staging is exact. The physical palette intentionally differs from the full-bright source: native fade counter reaches2 with target2/denominator5, and the exit-before-paint branch leaves the last painted ratio3/5. All128 physical palette words match that completed menu dim exactly. DISPCNT3A40/BG1CNT1E03 select enabled4bpp BG1, charbase0 and screenbaseF000. Captured scroll register reads are open-bus values and are not treated as evidence.

Commands accept explicit paths:

```text
verify_title_background.py BEFORE AFTER GBA WSC15 OUTPUT_JSON
verify_title_background_capture.py ROM CAPTURE_DIR OUTPUT_JSON --title-label prompt --selection-label menu
```

No emulator was launched by the independent checker, no guest memory was changed and no supplied save was read. These results cover this background and one ordinary-input title/selection path; they do not certify the whole game, extra title modes or hardware behavior.
