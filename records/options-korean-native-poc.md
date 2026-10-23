# Native Korean Options PoC — 2026-10-21

The standalone development ROM displays Korean through the real Options
constructor, renderer and OBJ VRAM. The main port default is unchanged. This
component does not implement four-language selection or persistence.

`tools/build_options_korean_poc.py` uses the retained Japanese P0 layouts,
P1 event commands and P2 palette, replacing only the ten Korean text frames in
`localization/options-draft.json`. Those drafts remain unreviewed and are
explicitly accepted for this development PoC only. All 22 other layouts,
including every number, arrow and head frame, retain exact source consumption.
Both original atlases and every executable instruction remain unchanged.

| Artifact | Identity |
| --- | --- |
| Original USA ROM | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |
| Predecessor | `build/repro-v58-20261021-a/current-candidate.gba` |
| Output | `build/options-korean-poc-20261021/options-korean-poc.gba` |
| Output SHA-256 | `90E6A4E58E5F01356115699D6F447FB8A8FC9AEF4013A4CEC686EFBA4EE0CA24` |
| New P0 | raw `632000..633348` exclusive |
| Retained P1 / P2 | raw `0A02E8` / `0A05B8` |

There are 47 disjoint Expected Writes: one new resource, fifteen P1/P0/P2
literal triples, and the initial palette pointer at `0C1784`. Whole-image
inverse verification explains the entire final diff. The first proposed
allocation at `630000` was rejected for existing encoded inbound references.
The adopted exact span passes FF ownership, all-byte pointer, aligned ARM
branch and immediate PC-relative inbound checks. These finite checks do not
exclude arbitrary computed aliases.

## Exact font and consumer budgets

The explicit input is Galmuri11 Condensed 2.404, supplied locally as
`Galmuri11-Condensed.bdf`, SHA-256
`4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED`.
Its accompanying SIL Open Font License 1.1 file hashes to
`76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C`.
Both are explicit build arguments and both identities are required. There is
no host font discovery, hinting, rasterizer substitution or missing-glyph
fallback. Any font derivative redistribution must include the licensed source
basis and license; no source ROM or extracted atlas is committed.

The 30 required non-space syllables use exact BDF pixels, at most 7×11, with
advance 8. The native ink/edge palette roles 1/2 supply a deterministic
one-pixel outline. Ink plus edge fits 13 pixels vertically inside the existing
20-pixel row spacing. Square markers remain unchanged. Missing/empty glyphs,
truncated rows, width overflow, source tile overflow and OAM overflow fail.

Native ROM `012C58..012DD8` is copied to `03000200..03000380`, entry `03000204`.
It selects tiles using the **low byte** and copies each emitted 8×8 tile into
`02000000 + OAM_index*32`. VBlank code `011744..011798` transfers exactly
`OAM_count*32` bytes to `06010000`. P0 flag 8 selects one source descriptor;
it does not preload the entire atlas into VRAM.

| Budget | Result | Limit |
| --- | ---: | ---: |
| ROM atlas | 124 tiles / 3,968 bytes | 256 tiles through the low-byte lookup |
| All 15 presentations at maximum frames | 107 OAM parts | 128, with final slot reserved by build |
| Corresponding active tile staging / OBJ VRAM | 3,424 bytes | 4,096 bytes |

The independent verifier recovers native constructor events
`0,2,4,6,7,1,8,3,8,8,5,5,8,11,9`. Four independent arrows coexist. The bound
includes the maximum twenty-part head frame even though ordinary clean data
hides the heads. It applies to these existing tasks, not future added rows.

## Independent verification and actual rendering

`test_options_korean_poc.py` passes three controlled tests: BDF MSB/padding and
baseline, missing/empty/truncated glyph rejection, and native 4bpp nibble order.
`verify_options_korean_poc.py` does not import the builder. It independently
compares every translated pixel with the exact BDF, checks all 22 preserved
layouts, recovers fifteen object/event calls and 45 real LDR references,
recomputes the complete screen bound and checks every final write. Both artifact
verification and the optional exact runtime observation pass.

The root-owned invisible natural-input capture is
`build/runtime-options-korean-20261021`, manifest SHA-256
`7ED27983C07E58349CC5C02D1670B116830C08536294E5CC081C6B093D866D6C`.
Inputs were Start 50 s, Down 56/57 s, A 60 s, capture 69 s. No supplied save was
opened and no guest memory was written to manufacture the route.

The screenshot was visually inspected: all five row labels, `보통` and
`아니요` are readable on the actual background and highlight palette. Mode is
14, cursor 0, Time 1 (120), Level 1. All fifteen live presentations bind
`P0=08632000`, `P1=080A02E8`, `P2=080A05B8`, with valid layout IDs. Hardware has
85 enabled OAM objects and tile indices 0..84; all 2,720 active OBJ VRAM bytes
exactly match native EWRAM staging. The copied renderer remains intact and the
run stops normally without recorded asynchronous faults.
`verification-runtime.json` hashes to
`FEB0E1521A0242D12048F833512D13A9CDCA7D8A62CB465AC509A5270D1902E3`.

This closes the observed producer → resource → renderer → hardware path.
Language selection, commit/failure behavior, fresh-session persistence,
four-language text coverage and genuine Digicode pixels remain separate work.

## Reproduction

`build_options_korean_poc.py <before.gba> <original.gba> <font.bdf> <LICENSE.txt>
<output.gba> --manifest <manifest.json>` builds the standalone PoC.
`--render-directory <directory>` optionally produces an all-frame preview.

`verify_options_korean_poc.py <before.gba> <after.gba> <original.gba> <font.bdf>
<manifest.json> <verification.json>` checks it independently. Add
`--capture-directory <root-owned-capture>` to verify the bounded runtime snapshot.
The normal current-candidate build deliberately does not run this PoC route.
