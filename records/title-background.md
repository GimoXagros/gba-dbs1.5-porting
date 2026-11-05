# Source1.5 title background component — 2026-11-05

This isolated component ports the selected Japanese WSC1.5 title logo and
background. It leaves the existing five-label four-language component and
all original shared native art intact. Source menu expansion remains separate.
No emulator, supplied save, main pipeline or Git operation belongs to this
component. Independent static and isolated captured-runtime verification passed;
current full-main build and result-runtime work remain root-owned.

`tools/build_title_background.py` accepts only scene candidate
`428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281`
and original WSC1.5
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
Output`build/title-background-20261105-a/title.gba`:
`494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6`.

## Positive source consumers

The source initializer sets C3 toCA and DS to380C at raw780039..780042.
That physical30000-window selection resolves base4A80C0, not4B80C0.
Exact source instructions at780043/780070/78008A select the Japanese
palette, tiles and map after fixed-zero language branches:

| Asset | Source raw / size | Source destination |
| --- | --- | --- |
| BG map |4A80C0 /3F0 bytes |0800,18 rows of28 halfwords with8-byte padding |
| Planar tiles |4A84B0 /3300 bytes,408tiles |7200..A500 |
| Six palette rows |4AB6B0 /C0 bytes |FE20 and0300:02D8 staging |

WSC4bpp tile address7200 is combined tile190: `(7200-4000)/32`.
The payload crosses the bank boundary at8000, so map bit13 must become
combined tile bit9. The existing stage map converter already implements
this exact mapping, together with H/V flips and palette fields. All504
cells reference400 distinct combined tiles400..799(decimal), wholly
inside the408 loaded tiles190..327(hex), and palette rows1..6.
All408x64 planar pixels are checked against the converted4bpp nibbles.

The complete32,256-pixel map reconstruction uses no color-zero pixels.
Consequently the GBA transparency interpretation of color0 cannot alter
any visible title BG pixel, despite nonblack source palette-zero entries.
Source secondary palette4AB790 converts exactly to existing native8B748
and is retained. The new256-byte primary palette contains192 converted
source bytes followed by the unchanged native rows7/8; existing physical
palette and fade-staging copies keep their original256-byte extent.

## Native owner, allocation and smallest complete hookup

Native title transfers live in080908A0. The original map8B768, tiles8BB58
and palette8FB58 also have actual users around0407xx and0883xx. They are
shared assets, so replacing them in place would alter other screens.
Their bytes remain unchanged, including title sprite resources and labels.

A contiguous14KB FF allocation failed the conservative all-alignment
mirrored-pointer and ARM/Thumb reference census. Two smaller clean tile
reservations avoid weakening that ownership rule:

| Native raw interval | Contents |
| --- | --- |
|712680..714680 |first2000 bytes of converted tiles |
|717F40..719240 |remaining1300 bytes of converted tiles |
|6FBDA8..6FC198 |converted28x18 BG map |
|6FC198..6FC298 |six source palette rows plus two retained native rows |
|6FC298..6FC2C8 |48-byte DMA helper |

Every reservation is FF in the exact input and passes the complete existing
`no_inbound` scanner, including08/0A/0C mirrors, every pointer alignment,
ARM branch/literal/ADR and Thumb references. No matches are waived.

There are only three existing-ROM writes:

-090924 changes its original destination load to an ARM B into the helper.
-090B7C points both physical/fade-staging copies to086FC198.
-090B90 points the unchanged map-row loop to086FBDA8.

The eight-instruction helper loads destination06003200, copies80032-bit
words from08712680 through native08000B84, then copies4C0words from
08717F40 to the now-advanced06005200. It sets LR to08090938 and tail-enters
the same DMA routine, returning to the original map-transfer continuation.
Its literals and exact disassembly/roundtrip are asserted. Flags and all
registers outside the existing DMA scratch/clobber set are preserved; it
adds no stack, task, persistent state or guest RAM owner. The final source,
destination and count scratch values follow the new source payload.

The new VRAM extent06003200..06006500 is within the former native title
tile extent06003200..06006820. Map writes remain0600F000,18rows,56bytes
each with64-byte stride. Later shared transfers at06007080 and0600F840,
secondary palette staging and existing sprite resources are unchanged.
The original skipped tile instructions090928..090934 remain byte-exact.

## Verification and previews

The builder checks exact source/native producer bytes, complete DMA
instructions, source planar/palette/map geometry, all loaded pixel nibbles,
map tile/palette ownership, FF/no-inbound allocation, disjoint expected
writes and whole-ROM inverse. Eight expected-write spans declare14380
bytes;13831 bytes actually change. The current output remains8MB.

`title-source-background-1x.png` and`-2x.png` under the component output
directory reconstruct the actual converted BG without sprites. The viewed
preview reads Digimon Tamers / Battle Spirit Ver.1.5 and retains the source
Japanese copyright and source background artwork. It is a static data
reconstruction, not an emulator screenshot or a complete menu frame.

Reproduction:

```powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/build_title_background.py build/shoot-scene-resident-20261105-a/scene.gba 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' build/title-background-20261105-a/title.gba --manifest build/title-background-20261105-a/manifest.json
```

## Completed independent verification

The builder-independent static report is
`build/title-background-qa-20261105/independent-final.json`, SHA-256
`1D2AF8B349E42701DD85BA59B1111E1ED3C88E5AF7C7AB3B3F0DEC289800C665`.
It verifies all408 tiles,504 map cells,32,256 displayed pixels, palette rows,
helper ABI, literal owners, allocation/inverse,22 artifact mutations and nine
ownership-reference controls. No builder/converter is used as its oracle.

Root's hidden ordinary-input title/selection run on exact494D also passed
independent live-buffer review:
`build/title-background-qa-20261105/capture-a.json`, SHA-256
`F9FD70BF2FC79E20E159ECEA48121A737AA16DBFE7AC62748B677FAA7BBF7873`.
The actual title screenshot was viewed; all408 live VRAM tiles and504 map
cells match. Source palette staging and the completed native3/5 menu dim
match the captured physical palette. The earlier capture names are retained:
`prompt-*` is the settled title menu, `menu-*` is character selection.
See `records/title-background-qa.md` for the precise captured scope.

Root has completed the two current268-file full builds and independent
audit. That is distinct from the already passed isolated component/capture;
the new ordinary-input result-language campaign remains in progress.


The completed full-build comparison is
`build/repro-v67-20261105-comparison.json`, SHA-256
`249B3B2E997E8C2B289D53B0C7BD46A17B029AE5F020BB215BEAF96386BF5AD3`.
Independent recomputation is
`build/repro-v67-final-audit-20261105/audit.json`, SHA-256
`2006A629A9F8334ADDF771ED8C104A06CFE758A12DFFCDF789C49805973BD155`.
It verifies both complete268-file inventories, exact component reports and
the whole final-to-v65 inverse chain. This does not replace result runtime.

The subsequent final A4CB main ROM also reached title, battle and natural WIN through ordinary input in all four languages; see records/title-result-integration-v67.md.

Skipped: hardware timing and the missing menu state tree. Risk: this background does not complete the extra1.5 menus.
