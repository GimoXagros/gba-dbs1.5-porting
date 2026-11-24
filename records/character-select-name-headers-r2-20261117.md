# Character-select headers: spacing revision and isolated installation

This follows the frozen source/name/border contract in `character-select-name-headers-20261117.md`. Its r1 assets and E9FF author result remain unchanged. The current isolated component is **C956A267**, based on the corrected title **9F0DA031**, not the historical failed title 9E3B.

## Digicode clearance

The first preview placed complete voiced glyph bounds at y1..14. Although inside the header, those marks visually touched the preserved white y0 frame. Revision 2 translates every entire Digicode label down exactly one pixel. Voiced labels occupy y2..15, leaving one full background row after the top frame. Unvoiced labels occupy y4..13, leaving three top and two bottom background rows. No glyph pixel is scaled, removed or clipped. The header owns y0..15; portrait pixels begin at y16 and remain unchanged.

All 45 EN/JA/KO headers are byte-identical to r1. All 15 Digicode headers preserve their complete ink sets and native palette indices under translation (0,+1), with zero changes to the protected checker/top-frame mask. The unchanged overlay remains 104 bytes and still copies only 768 bytes to **06005780..06005A80**.

- New asset builder `tools/build_character_select_name_assets_r2.py`: `1CA43B82F49B3C7F6974F0D88B2FE694C25E113FA32A4C67F8EEF6482EE309DC`.
- New assets `build/character-select-name-assets-r2-20261117/manifest.json`: `9F479B7C13FA4BCECDBD24E3170628377369C31CC5FD4563D311B9B49A1C3C11`.
- Preview: `build/character-select-name-assets-r2-20261117/headers-native.png` and `headers-3x.png`; full portraits are in the same directory.
- Delta checker `tools/check_character_select_name_r2.py`: `697B55DEFC8E7DC89631E790F9C4F7C9762621322ADB4B3999D1B290EA878FB8`.
- Delta result `build/character-select-name-author-r2-20261117/report.json`: `37533284A660D8B042B14B196BCC422C4F75484CBD581893A99C4C109889EC40`.

The delta gate retains the frozen E9FF native ARM proof; it does not repeat unrelated old suites.

## Isolated component

`tools/build_character_select_name_scene.py` SHA `6DA9E5855F9A90A38E15977A0EAF20DE8259AAB9997447221DACF5BE9D7F4177` consumes:

- Corrected title input `9F0DA0316B76CA6D2634DF7F89CCE1FFD1F1B0AC2CB37B2EDCDC0753466B228A` and owner manifest `A54778FA9FCA9A689E6B632C477DBF457B50B5BAFD5CEB4A324B1AA463A87324`.
- Source scene r3 owner `3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B`.
- Header assets r2 `9F479B7C...` and unchanged helper module `4156DDC0A8AD9FD2B9D3C5E2B2745DEEF5E17034D98BCC32B9D83B3F94B76824`.

The strict allocator scans the complete merged 16 MiB predecessor for conservative references into D90000..FFFFFF. Only actual FF runs with no inbound target qualify. The builder additionally excludes the **entire DB0404..DB5C04 scene code/root reservation**, including erased slack, and every prior typed scene/title allocation. There are 170 excluded extents, including that reservation. No reference exception or padding waiver is used.

There are 62 new allocations: sixty 768-byte headers, one 240-byte pointer table, and one 104-byte helper. The only existing-code mutation is the 4-byte B at 084A5C6C. The 63 declared writes total 46,428 bytes, of which 34,623 actually change. A complete inverse reconstructs 9F0D exactly. OAM, palette writes and new global RAM each remain zero.

- Component `build/character-select-name-scene-20261117/component.gba`: `C956A267974010391DF931F18F6B7963703F3511D0772F1D2686367015BC7D3A`.
- Manifest in the same directory: `FEB91A11848B4AE3C35DD200F9CAC3B339D984920FF84DFB0BE2D9FDF8179E3E`.
- Complete allocation census in that directory: `465E50CDFAECC91E5E5EE224DBEBD8D7F16CC8A440712971E239C9D45EDCDDD7`.
- Installed author checker `tools/check_character_select_name_scene.py`: `3FE4000EC82B1A5C87EFC864AC55617D1DECF7F07421F1C0EC7B8AB025C797FC`.
- Installed author result `build/character-select-name-scene-author-20261117/report.json`: `8473529C1E3E69E2E80E97DE847AB1983587169712C5D25AFC8AC6DBDAC0D582`.

The installed check reconstructs every declared byte, verifies every pointer against its exact header, and executes actual native loader/getter/helper/DMA-setup/continuation for all 15 identities × four languages × 16 NZCV combinations. Returned R0..R14 and NZCV match the prior native loader; the cache store, palette, all 5376 body bytes and original DMA order remain exact, followed by the one header DMA. DMA hardware transfer is modeled from the actual MMIO setup. No emulator was launched. Independent pixel/allocation/consumer review and actual runtime validation are separate requirements; this author report does not claim them.

```powershell
python tools/build_character_select_name_scene.py --input build/mode23-title-scene-r2-20261117/component.gba --assets build/character-select-name-assets-r2-20261117 --scene-owner build/mode23-scene-v88-r3-20261117/manifest.json --title-owner build/mode23-title-scene-r2-20261117/manifest.json --output-dir build/character-select-name-scene-fresh
python tools/check_character_select_name_scene.py --before build/mode23-title-scene-r2-20261117/component.gba --after build/character-select-name-scene-fresh/component.gba --owner build/character-select-name-scene-fresh/manifest.json --assets build/character-select-name-assets-r2-20261117 --report build/character-select-name-scene-author-fresh/report.json
```
