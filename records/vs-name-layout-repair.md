# Missing VS name layouts and native renderer overflow, 2026-10-21

The expanded roster repair successfully exposes ID14. The subsequent VS
transition failed because its existing expanded event selected a layout that
the retained name resource did not contain. This is a separate downstream
resource defect, not evidence that the roster adapter corrupted its base
registers.

## Actual first overflow

The root-owned read-only probe is
`build/roster-first-overflow-20261021/probe.json`, SHA-256
`9F19C51728E7182FC95F76527FE5E89F119693CEC45085FC97A7D37BE3245F52`.
Its watched presentation at `03002CC8` has P1 `080B77EC`, P0 `080B799C`,
palette `080B81D4`, and layout `0C`. The retained P0 table at `080B79AC`
contains eleven entries, ending at `080B7A04`, where its first part array begins.
The installed ID14 event at `08485340` selects layout12. Its supposed table
entry at `080B7A0C` is therefore part data: count `0EF80206`, items `16F80207`.

The first OAM overflow watch at `03001828` captures 97 emitted items:
remaining count `0EF801A5 = 0EF80206 - 97`, and items pointer
`16F8038B = 16F80207 + 97*4`. The pixel base remains the native name atlas,
`080B7D34`; the captured stack includes `080B6AF8` / `080B73E4`.
This connects the malformed resource lookup to the native renderer's runaway
part loop. A later undefined-instruction stop after IWRAM and EWRAM overwrite
is not treated as a valid caller chain.

## Source-backed resource repair

WSC1.0 P0 raw `2AB3A0` has eleven layouts. WSC1.5 P0 raw `3C3BF0`
has thirteen. Their first ten layouts and the corresponding native layouts
match byte for byte. Source1.0 row10 equals Source1.5 row12; the native boss
has a retail-specific first-twelve-part variation that is preserved exactly.

The missing Source1.5 rows10/11 are the two new names, each sixteen parts:

| Native appended layout | Source parts | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| 11 | `3C3ECC` | 64 | `A5697AD4902561A25035D4336735A8B7FA9835A22DBBAAADF6AF0A93D4448F01` |
| 12 | `3C3F0C` | 64 | `CBA893CA6F641F03406A82E8663E6249BA019002541E7A9D748E0AD0BD13E6AA` |

Source event families `3D0F70` and `3D10C0` both map ID13 to source layout10,
ID14 to11, and boss15 to12. The existing native expansion instead reserves
native10 for the retained boss and maps IDs13/14 to native11/12. Appending
the two source part arrays preserves that established native mapping.

The source alphabets at WSC1.0 `2A6280` and WSC1.5 `3BEBC0` are identical,
1184 bytes / 37 tiles. Inverting native pixels `0B7D34..0B81D4` reproduces
those source bytes exactly, so the new names need no new font or pixels.

`tools/build_vs_name_layout_repair.py` allocates exactly `628140..628228`:
a thirteen-entry table retains all eleven original native count/pointer rows,
then adds the two source part arrays. Its sole existing-data write is P0's
first pointer at raw `0B799C`: `080B79AC -> 08628140`. The layer changes
235 bytes. All nine encoded P0 callers retain the same resource header;
the old layout-table pointer occurs only in that header. The exact allocation
is FF with no prior encoded pointer, ARM branch, or immediate PC-relative
access into it. Complete inverse restoration preserves every earlier layer,
the native atlas, events, palettes, renderer, and RAM owners.

## Verification and runtime boundary

| Artifact | SHA-256 |
| --- | --- |
| Predecessor | `7DBFA0B464AB9A0E2DA55049855A0BC08AABAAACDA1AF3E21CC780F2864854E9` |
| `build/vs-name-layout-repair-20261021/current-candidate.gba` | `99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1` |
| `build/vs-name-layout-repair-20261021/manifest.json` | `0F460EC3C03CE2B0F7F3EA8F492B211899595883D3B6CA4F19855EE85C7A8E13` |
| `build/vs-name-layout-repair-20261021/verification.json` | `D5080E7D2813E274BCB19E4B688A357734ABFF1F7B722EEC3739D7ED63AA09F8` |

The separate agent-owned `tools/verify_vs_name_layout_repair.py` reproduces
the 97-step failure chain, checks all sixteen installed VS events against the
expanded layouts, inversely checks the font, binds the native consumers,
rejects fourteen mutations, and checks the complete write inverse.

The root-owned natural ID14 run of the repaired ROM reaches Waterfall battle
with timer `1:55`, 25 OAM entries, an intact copied renderer, and no fault.
Capture `build/runtime-vs-name-repair-id14-20261021/capture.json` has SHA-256
`90A5CB2B319BC0FEEF2372C8E064719CEA78A9D4BFAC0030E9439591BA8103D9`.
The black side regions/background require separate graphics investigation;
this is bounded transition/renderer confirmation, not full visual parity.

No save was opened and no emulator was launched by the builder/review agent.
