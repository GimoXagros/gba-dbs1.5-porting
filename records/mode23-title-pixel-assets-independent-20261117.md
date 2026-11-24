# Independent title pixel checks in four languages

The prepared title asset blob `2A6FC8168C1FA166EE9D8FD575975ABC7381060E76F4867B52480EDE41A41431` passed independent decoding in all 44 language/event combinations. The source and four decoded atlases reproduce the two native-size preview images exactly in their menu regions. A visual review at 1× found each bordered row and blue selection marker distinct, including on the longest English and Korean rows. The Digicode cells use fine single-pixel strokes that should be assessed again on the actual title background.

- Japanese retains every visible palette index of the eleven original WSC planar frames. The first five English, Japanese, and Korean images and the existing Digicode prompt match their prior GBA images exactly. The locked question-mark frame matches the original in all four languages.
- Ten added English and Korean labels reconstruct exactly from the pinned Galmuri11 Condensed BDF. All expanded Digicode labels reconstruct exactly from the catalog bitmap rows and Japanese readings, with chart Latin letters for D-ARK and Ver. The original hyphen, version digits and period, and prompt exclamation mark remain exact source pixel groups. The kana normalizations expand small ョ and ュ to their explicit chart equivalents.
- Longest added outlined labels are 75 pixels for English, 71 for Korean, and 74 for Digicode. The wider rows span 96 pixels and the five simultaneous root rows span 88 pixels each. All added labels keep at least one clear column between the complete outlined text and the marker or frame. Every generated marker matches the original 14×14 source cell.
- Eleven native P1 event records and timing regions match the source after their pointer-width conversion. One converted P2 block retains all original GBA title colors.

| Language | Atlas tiles | Start prompt parts | All five root rows | Largest two-row submenu |
| --- | ---: | ---: | ---: | ---: |
| English | 143 | 8 | 110 | 46 |
| Japanese | 153 | 25 | 110 | 44 |
| Korean | 145 | 24 | 110 | 46 |
| Digicode | 157 | 26 | 110 | 46 |

The root's 110 parts use 3520 bytes of the 4096-byte tile staging queue and occupy 110 of 128 OAM slots. The root, prompt, two submenus and two locked-row combinations agree with the pinned 24-case native renderer fixture. The actual title controller and physical OAM upload still require runtime verification. The source E6 counter overlay remains outside this assessment and would consume some of the spare budget if added.

Checker `tools/verify_mode23_title_pixel_assets.py` SHA-256 `97ED53A0A676B9D9E8A92183FDF14CADA7FFE68EAB829352136AB99979D34D11`. Report `build/mode23-title-pixels-independent-20261117/report.json` SHA-256 `25A1FF684B9BE94EBD971C76ED27AB04E540B988E89AE0AAD740504AC4D56C29`. The unchanged native-scale previews are `build/mode23-title-preview-20261117/contact-sheet.png` and `build/mode23-title-preview-20261117/root-menus.png`.
