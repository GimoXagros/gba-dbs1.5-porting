# Native Options language component — 2026-10-23

This development component adds a sixth Options row and actual English,
Japanese, Korean, and Digicode resource routes. It does not complete four-language
support outside Options. Original English and Japanese resources remain
byte-identical. Korean wording remains the draft in `localization/options-draft.json`.
Digicode uses its Japanese readings, with Latin glyphs only for Latin characters
already present in those readings. See `records/digicode-glyphs.md` for the
development font's provenance and review limits.

The builder is `tools/build_options_selector.py`, independent artifact/snapshot
checker `tools/verify_options_selector.py`, and placed ARM source
`tools/options_selector_arm.py`. `localization/options-selector.json` owns the
four labels, endonyms, and complete localized save errors. This implementation
worker launched no emulator and accessed no save file. Runtime observations
below are from the root worker's separate runs.

## Immutable inputs and artifacts

Only two predecessors are accepted by both builder and checker:

| Input | SHA-256 |
| --- | --- |
| Historical v59 | `AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF` |
| Waterfall and character follow-up routing repairs | `F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E` |

The original GBA hash is
`996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`.
Exact Galmuri11-Condensed BDF and license hashes are
`4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED` and
`76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C`.
Canonical 98 Digicode row-byte hash is
`E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195`.

Two AAD4 builds, `build/options-selector-four-20261023-a` and `-b`, match byte
for byte across ROM, manifest, independent verification JSON, and static preview:

| File | SHA-256 |
| --- | --- |
| `options-selector.gba` | `6675FB3676E5507379F6787B885C86475E9B7891386AF8EA27E1A4BA584846CE` |
| `manifest.json` | `AB0701820DE43D6C6A5090944430FB449CE3C45D875271B793064B96FE9FAF4F` |
| `verification.json` | `16BF786B7CC35D7A06F819CDB424067A944E0B17905A510A4D93396D15A52CD8` |
| `previews/selector-all-frames.png` | `86CA6FE3C3F8572D69BC7F4EC5D28804FD1934A75676056B9A528353C308D1BA` |

F1BC integrated artifact:
`build/options-selector-integrated-20261023/options-selector.gba`, SHA-256
`3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C`.
Its adjacent manifest is
`B77C0BAD1EB756B146BAF62A815D67685227684A78E6799943C6A9CD26385A2F`;
independent PASS report
`85F723E9B043A161788B1821F6D2BF895D3906254EFF6CBF255CB8D1B9094175`.
Main-pipeline integration and exact-integrated-ROM runtime remain root-owned.

## Selection and native record ownership

The approved byte is `03001120+0F`; see
`records/language-padding-owner-review.md`. Exact tags `A0..A3` decode to
English/Japanese/Korean/Digicode. Legacy `20` and other values read as English
without a write. Native reset restores `20`. The first 15 header bytes and all
existing payload fields keep their original locations.

Left/Right stage a choice at row 4, with bounded endpoints. Entry language stays
fixed until re-entry. A on row 4 writes the chosen tag through `0801FC5C` and
exits only on success. Row 5 is Return. Ordinary B or Return discards staging
without an EEPROM write; A on Return retains the native exit behavior.

The direct native writer recalculates the unsigned checksum over `C0` bytes and
writes 25 eight-byte blocks sequentially. Its status is checked before caller
registers are restored. Failed commit restores the exact old RAM tag/checksum,
retains row 4 and a pending-error flag, and shows the full localized save error.
Navigation is filtered in both the returned input register and shared Options
button halfword. A retries the staged new record. B writes the restored old
record and permits exit only when all blocks succeed. Failed repair preserves
the exact old RAM checksum and keeps the menu pending.

RAM rollback alone cannot repair partial physical writes. The independent model
covers 25 first failures, 625 failed repairs, 23 torn-header counterexamples, and
successful retries/repairs. This is not device fault injection. Power-loss
atomicity and recovery from permanently failed storage are not claimed. Native
record read/write, normalization, and low-level retry functions are unchanged.

## Actual task ownership and lifetime

Allocator `08011AC4` owns a pool at `02010000`. The reset count at raw `11AC0`
describes `52 * 118` bytes. Each slot is `118` bytes: `18` bytes of scheduler
header followed by a `100`-byte payload. Payload accessor `0801201C` adds `18`;
retirement `08012030` releases the current slot through native unlink/free
routine `08011BE4`. These routines are checked against original GBA bytes.

One new priority-`1500` task uses `F8` of its `100` payload bytes. Pending
language, entry language, and pending I/O error occupy halfwords `+0,+2,+4`.
Three native `50`-byte presentations start at `+8,+58,+A8`; the last ends at
`+F8`. Creation clears exactly `3E` words because native allocation does not
zero reused payloads. The final eight bytes remain outside this component's use.

Stable captures contain the original ten tasks plus this one, within 52 slots.
Native priority lookup clobbers `r8`; its wrapper preserves the cursor register.
The selector sets retirement bit `200` and calls native `08012030`; the complete
Options retirement mask changes from `1FB` to `3FB`. Original presentation tasks
and exit callback ownership remain native.

## Resources, display bounds, and budgets

| New raw half-open allocation | Role |
| --- | --- |
| `632000..633348` | Korean P0 and 124-tile atlas |
| `633400..634200` | Reserved ARM routine slots and literals |
| `637000..6386E8` | Selector P0/P1 and 153-tile atlas |
| `639000..63A468` | Digicode P0 and 132-tile atlas |

The builder checks complete `FF` spans, byte-aligned encoded pointers, and
aligned ARM branch/PC-relative references before adoption. Earlier spans with
inbound references were rejected. This finite proof cannot exclude arbitrary
computed aliases. The 62 disjoint Expected Writes explain every changed byte;
independent verification inverts them to the exact input and reconstructs all
installed native resources.

The two Options constants dispatch palette and constructor. Japanese keeps its
original constructor. English constructor's 15 actual native presentation calls
retain original tuples for English and route Korean/Digicode to their new P0
plus original Japanese P1/P2. Both original asset sets remain unchanged. Korean
and Digicode replace the same ten text layouts. The other 22 layouts, including
numbers and decorations, retain original parts/pixels.

The native renderer emits one 8x8 OBJ and copies one 32-byte tile per part;
source atlases are not preloaded into active OBJ VRAM. Bounds include all 15
concurrent native presentations, all their frame choices, and the selector.

| Entry language | Original 15 maximum | New row maximum | Whole screen | Staged bytes |
| --- | ---: | ---: | ---: | ---: |
| English | 80 | 23 | 103 | 3296 |
| Japanese | 73 | 18 | 91 | 2912 |
| Korean | 107 | 17 | 124 | 3968 |
| Digicode | 110 | 17 | 127 | 4064 |

Only the new row's decorative square is consistently omitted; all original
markers/presentations remain. Digicode trims blank side columns while retaining
every ink pixel and its full edge. On failure the complete error replaces the
new label/value/arrows; all 15 original objects still draw. Error cost is below
the normal bound. No runtime clamp, text truncation, or renderer patch is used.

The glyph worker independently decoded actual resources and checked 14,580,000
native frame/row combinations. Its standalone report
`build/digicode-glyphs-20261023/actual-resource-review.json` hashes to
`4442EAE2B77CCD89D4A87B34860070A02AC05758AC18E4FEF46C8CCF6DB6E712`.
The integrated candidate also passes, in `integrated-resource-review.json`,
SHA-256 `947522802723845EF01DD7090F5F39D3BF6D06BA1209FE6BDB42EE11633DA05F`.

Six logical baselines are `36,54,72,90,108,126`; the native logical window is
`(24,200,16,128)`. The rejected BC1778 candidate placed Return at 136 and the
root screenshot showed clipping. Final code reflows both reachable constructors
and native relayout consumers, preserving the window. Constructor input is
forced to zero at `080C17BC`, making the modified normal coordinate path reachable.

## Verification and exact runtime evidence

The independent checker imports no builder. It decodes installed tiles, checks
Korean pixels, separately recomposes Digicode from the pinned 98 row-byte set,
checks selector frames/budgets, decodes/reassembles 268 placed ARM instructions,
checks branch/literal boundaries, and validates allocator/record/renderer
dependencies. Four controlled tests cover BDF bearings/rejection, native layout
boundaries, placed ARM branches, and partial-write/repair semantics.

`verify_capture` reads an exact-ROM stable Options snapshot: all 11 tasks,
15 original resource tuples, three new tuples, bounded entry/pending/error
state, complete Return bounds, OAM count/tile sequence, and equality of active
EWRAM staging with physical OBJ VRAM. It reports RAM tag/checksum. It opens no
save and launches no emulator. One snapshot does not exhaust interaction states.

Historical D245 three-language root runs passed Japanese commit and fresh process
re-entry. Restart capture manifest
`2B3E2FEC85066B1F96D0ECC634697960910FDA4C710F53E3CFEB2591542DE82F` in
`build/runtime-options-selector-jp-restart-20261023` records tag `A1`, valid
checksum, entry/pending 1, 11 tasks, 69 OAM, and Return bounds `[32,118,63,125]`.
This is historical mechanism evidence, not an exact-ROM four-language claim.

Root-owned 6675 observations:

| Capture under `build/` | Manifest SHA-256 | Observation |
| --- | --- | --- |
| `runtime-options-four-digicode-stage-20261023` | `487D4917B4746FBCD9A8943FF81BB588658B9E41F9F2C2EA99F799BA284458DF` | Row 4, pending 3, entry 0, legacy tag 20, 81 OAM, Return visible |
| `runtime-options-four-digicode-commit-20261023` | `0641E7B9EA9F61396B9F7F0FC9D6C786593F3FBE2D0D39F2E1F0B6C7B07B004D` | Root reports tag A3 and valid checksum after successful commit |
| `runtime-options-four-digicode-restart-20261023` | `35513E2AB0CA78FBB30EEB3D68024ED3F789DDEB81F4E11DDFDE2F80BBA246F3` | Fresh process: entry/pending 3, tag A3, valid checksum, error 0, 102 OAM; full Digicode Options and Return visible |

Staging and restart have `language-runtime-verification.json` PASS reports.
These observations do not transfer automatically to integrated ROM 3B40BC0C.

## Reproduction and remaining checks

Run from the repository with the project Python runtime. Builder arguments:
`before gba font license output --manifest manifest --render-directory previews`.
Independent checker arguments: `before after gba font manifest verification`.
Optional `--capture-directory` requires an exact matching root-owned snapshot.

Integrated input is `build/character-followup-routing-20261023/current-candidate.gba`;
standalone input is `build/repro-v59-20261021-a/current-candidate.gba`. Use the
pinned original GBA and licensed BDF above. Controlled tests run with
`python -m unittest discover -s tools -p test_options_selector.py -v`.
Digicode's separate actual-resource checker command is in its record.

Not verified here: physical failure injection, permanent failure, power
interruption, exhaustive live interactions, all four fresh-process transitions
on the integrated ROM, final font readability/authentication, and non-Options
title/error/result/gameplay localization. Main-pipeline and further runtime
evidence remain root-owned. This is a bounded development component.
