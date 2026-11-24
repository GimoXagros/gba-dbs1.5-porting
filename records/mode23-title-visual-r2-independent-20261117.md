# Revised Digicode title spacing

The corrected asset blob `0633125FE39EC15C2421BDF9A560554A9ED240CCD75EFB1ADF9C9F3D82FF486C` has aligned blue markers and aligned text on all five Digicode root rows. A native-size inspection of the final preview shows the text clears the dark panel edges. Both final previews match the independently decoded atlas.

The nine revised Digicode rows use 88 to 104 pixel panels. Each keeps seven blank columns between the marker and the first glyph, at least seven columns to the right edge, and at least one dark row above and below the ink. A two-column gap preserves adjacent glyph shapes. All chart ink pixels and the original version digits and hyphen survive exactly. Removing the white perimeter gives full-height voiced marks a clean dark background. The prior Digicode prompt remains intact.

The revised English COLLECTION label uses a 62-pixel, seven-row bold treatment. The checker matches its O, L, E, T, I, and N directly to retail glyphs and verifies the C adapted from O. It separately checks the disclosed matching-style additions in the other new English entries. All original Japanese and Korean frames, the original five English frames, locked question-mark images, and source event and palette records remain exact.

The frozen native renderer was run over all 24 prompt, root, submenu, and locked-row cases using the final r2 atlas. English, Japanese and Korean each use 110 parts for all five simultaneous root rows. Digicode uses 116 of 128 parts and 3712 of 4096 dynamically staged tile bytes. Its largest checked submenu uses 52 parts. These results cover the exact generated rows. The eventual live display and source E6 overlay require separate evidence.

- Pixel checker `tools/verify_mode23_title_visual_revision.py` SHA-256 `CA204A74F21E169B63BFFA2AEB57C32ECE6B82FD40D0AFE3DB50A19E6AF22575`.
- Independent pixel result `build/mode23-title-visual-r2-independent-20261117/final.json` SHA-256 `A1829C48C3275569FD1116E9F2EB98B06912A33A07CF24FE3799EF22E4AEAFF4`.
- Native renderer result `build/mode23-title-assets-r2-native-independent-20261117/report.json` SHA-256 `9B7AD4CBE4E37D669FBE25E4E836FD7A9E6C4281B3C994CFD0A76910F89F3893`.
- Native-size root preview `build/mode23-title-preview-r2-20261117/root-menus.png` SHA-256 `88AD8A067572F0A46BAF64BCD14C3EFB6C93CDF3EB127DF103434987A0EB857E`.
