# Aligned AI and Iraira actual source evidence — 2026-11-17

Root's original session 49898 completed with exit 0 on frozen 3FE5 and reached the guarded healthy-Shoot result at core 89405. This report covers the independently checked source fields and background owners; the separate campaign QA owns full route, clock, phase, palette and visual acceptance.

`tools/verify_ai_iraira_capture_independent.py` SHA-256 is `3B9F3FED4F71DFE2FB20F32C17FF3160FE7C3F19E9471320C0D8298705EE6322`. The frozen report `build/ai-iraira-actual-independent-20261117/report.json` is `9B6FEC1161B356773563A8AAB36510EF9F6041192767973C145F1B2401685075`, status `AI_IRAIRA_SCOPED_ACTUAL_PASS`.

At core 19961, CPU 14 normalizes to row 9 with stride 18, reading even address 08D8ABA2. R0 and the actual store to 03004D8A now contain the full source value 02E4, replacing the earlier measured 00E4 truncation. All fifteen copied fields equal the original WSC row. At core 20199 the saved behavior bank is 0D80; the actual native action copy selects ordinal 00CC at 08D8A658 and dispatches state 8 through the valid target 080C6630.

The ten existing first-active snapshots cover every normalized parameter row without another replay. Both stored halfwords at 03004D8A/4D8C match the original WSC source:

| CPU | Normalized row | First word | Second word |
| --- | --- | --- | --- |
| 13 | 8 | 0250 | 00DE |
| 1 | 1 | 0250 | 00DE |
| 14 | 9 | 02E4 | 0094 |
| 3 | 3 | 02E4 | 0094 |
| 11 | 7 | 0250 | 0094 |
| 5 | 5 | 0250 | 0094 |
| 2 | 2 | 0250 | 0094 |
| 6 | 6 | 02E4 | 00DE |
| 4 | 4 | 0250 | 00DE |
| 0 | 0 | 02E4 | 0094 |

Iraira snapshot `13-campaign-active-04` has actual stage 10 / CPU 11 / progress 4. Descriptor 03002338 owns source resource 38 through native resource 26 and map 0600F000; descriptor 03002388 owns source resource 37 through native resource 25 and map 0600F800. Their ports, source-map descriptor pointers and 2×2 geometry match the repaired native bindings. The backdrop RAM owner 03002654 is zero; this is not proof of the hardware backdrop color. Separate palette QA found hardware color 0 equal to 033D and two animated groups inconsistent with current counters, so palette closure remains unresolved. Palette counters are `[5,1,2,3,0]` in their compact owner, and the separate display phase is zero.

All 31,680 pixel indices in the 495 dedicated live VRAM tile slots equal the original WSC planar data. The last 17 slots are the existing shared overlay and are explicitly excluded from this source-atlas comparison. Source-resource cell-value membership counts in the two live ring maps are 940 and 1,024; these are diagnostic coverage counts, not proof of exact scrolling-coordinate order. This check establishes source pixel indices and owner routing, not a complete raster-composition comparison.

The retained type8 first-chain count is still zero. This successful route and corrected AI evidence do not establish an actual evolved-air event16 witness. No emulator, main build or Git operation was performed by this reviewer.
