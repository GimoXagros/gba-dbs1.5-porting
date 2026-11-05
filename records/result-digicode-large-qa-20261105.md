# Larger Digicode result sprite: independent QA, 2026-11-05

The second revision passes isolated artwork QA. The first expansion remains preserved but is not the approved visual revision: its two empty ink columns were filled by adjacent white outlines, joining the seven symbols into a nearly continuous bar.

Approved input: `build/result-pixel-art-20261105-dg-large-v2/source-art-data.json`. Independent checker: `tools/verify_result_digicode_large.py --separated`. Report: `build/result-pixel-qa-20261105/digicode-large-v2-data.json`, SHA256 `9796301A0618FD9457E1966287D9B306423FCC2A99516E5006F565BED754E70E`.

The checker independently recovers the seven frozen source glyphs for ラストチャンス (small ャ uses the approved ヤ glyph), then checks their ordered expansion from widths 7/6 to 11/9 and height 10 to 14. All original interior counter components survive: 6, 0, 2, 2, 2, 4, 0. Both ス masks remain identical. Three columns between ink masks provide one fully transparent column between each pair of fresh one-pixel outlines. The native 1× and 8× previews were separately viewed: each symbol is distinguishable, size is balanced with Korean, and the original exclamation mark remains clear.

The final canvas is 102×16; its outlined body is 89×16. It contains 496 warm ink pixels, 587 white outline pixels and the exact 65 source punctuation pixels. Palette-index pixel SHA256 is `4F9B02D9BC03779DCB14B62B0D0EB0F5755BC0DD48B3006669E5631F4BAAC924`. Native palette, binary alpha, all 4bpp tiles, flipped part composition and 1×/8× previews round-trip exactly. There are 27 parts and 26 tiles, within the 28-part limit. Japanese WIN/DRAW and Korean data are unchanged. Missing ink, changed punctuation and occupied gap negative controls all fail as required.

This is newly expanded artwork based on the frozen local glyph source. It does not claim identity to the smaller supplied image, authentication of an external character chart, ROM allocation, aggregate runtime OAM capacity or in-game verification. Those integration checks remain separate.
