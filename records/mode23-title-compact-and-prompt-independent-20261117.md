# Compact Digicode buttons and warm Start prompts

The final atlas `4BB3592128E231C49457551BE6C9DDB39734F8515FCFBBA6D8EA7CA817173CB4` matches the requested original-sized Digicode menu and warm localized prompts. The characters, border, and marker were inspected at native scale. The separate 4× preview confirms the same pixels at a readable inspection size.

All nine Digicode label frames use the original 88×16 white frame and original blue marker. The widest label is 63 pixels. There are at least four clear interior columns at the sides of the longest label and a full dark row separating the ink from each horizontal border. The 33 chart identities used by the displayed labels remain distinct pixel masks. Compact Digicode is drawn expressly for the menu, using the chart's shapes and independent voicing rows. Portrait lettering and the original chart are unchanged.

The English and Japanese prompts and all forty non-prompt frames match the approved compact revision pixel for pixel. The Korean Start prompt preserves its original 95×13 footprint, lettering, outline, and punctuation. Its white foreground becomes the native yellow-to-orange gradient. The compact Digicode Start prompt occupies 89×12 pixels, preserves the Japanese reading `スタートボタンをおしてね` and its voicing, and uses the exact 22 source exclamation pixels. The native palette indices are 7–11 for warm ink and 15 for black outline. Both recolored prompts use these existing palette entries exclusively.

The exact final atlas passes the 24 native renderer cases. All four five-row menus use 110 of 128 OAM slots and 3520 of 4096 staging bytes. Both deterministic preview images match the atlas across the displayed regions. These checks cover the prepared pixels and native renderer instructions. Actual game framebuffer evidence remains a separate run.

- Independent checker `tools/verify_mode23_title_compact_prompt.py` SHA-256 `C69E5AC566369EC79457B845E8A3BADFA5D3FE49E59478403BDAD7C8E260CD3D`.
- Independent pixel report `build/mode23-title-compact-prompt-independent-20261117/report.json` SHA-256 `178DEF852F565C069E79EE849D081DAA17FAD091DE9D9CEB9FBE5DF44174703D`.
- Native renderer report `build/mode23-title-assets-r4-native-independent-20261117/report.json` SHA-256 `247685EA2137645937126BD4698A2A75090B43210102E0259718262C587ACAB0`.
