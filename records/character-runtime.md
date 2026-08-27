# GBA character selection and asset-loader runtime

## Evidence boundary

These observations come from the exact USA GBA retail baseline identified in
`initial-survey.md`. The supplied WonderSwan save was not loaded, parsed, or
tested. Runtime captures used a clean-ROM mGBA savestate made at the default
character-selection screen.

## Confirmed selector state

| Address | Width | Meaning | Evidence |
|---|---:|---|---|
| `0x03004710` | `u16[]` | Ordered list of selectable character IDs | IDs `0..6` are populated in the default state; injecting `7..11` exposes the five built-in unlockable entries. |
| `0x0300473C` | `u16` | Current selection cursor; low byte is list index and high byte is palette variant | Down input produced `0,1,2,1`; right input changed `0x0000` to `0x0100` without changing character identity. |
| `0x0300473E` | `u16` | Display/transition mirror of the current cursor | It follows the low-byte cursor after the selection transition completes. |
| `0x03004740` | `u16` | Maximum selection-list cursor | Default value is `6`, yielding seven entries. |

The primary cursor is written by the ARM instruction at `0x08081D90`; the
display mirror is written at `0x0808322C`. The selection renderer multiplies a
character ID by 32 at `0x080831C4` before indexing the asset-record table.

## Confirmed GBA roster IDs

| ID | Character shown by the retail ROM |
|---:|---|
| `0` | Guilmon |
| `1` | Terriermon |
| `2` | Renamon |
| `3` | Veemon |
| `4` | Wormmon |
| `5` | Agumon |
| `6` | Sukamon |
| `7` | Agumon (Black) |
| `8` | Lopmon |
| `9` | Gabumon |
| `10` | Agumon (extra entry) |
| `11` | Impmon |

IDs `7..11` were exposed by changing only the live selection-list mapping and
cursor maximum. Their portraits, names, and sprites are therefore existing GBA
content, not imported assets.

## Confirmed indexed asset records

- Record size: `0x20` bytes / eight little-endian `u32` fields.
- Group 0 starts at ROM offset `0x0D3FC0`.
- Group 1 starts at ROM offset `0x0D42C0` (`0x300` bytes after group 0).
- The central loader starts at `0x08353304`, shifts the character ID left by 5,
  and applies the `0x300` group delta when its group flag is nonzero.
- At `0x08353324` the retail loader special-cases character ID `0x0C` and
  returns before normal record loading.
- Selecting Guilmon produced loader ID `0`; the CPU Terriermon produced loader
  ID `1`. Both used group 0 in the observed battle-load call.

This proves that the 1.5 characters cannot be added merely by increasing the
selection maximum. The port needs new selectable IDs, both indexed asset
groups (normal and alternate/evolution path), the selection-list population
logic, name/portrait resources, and a deliberate resolution of the retail
ID-`0x0C` sentinel behavior.

## WSC-only animation-asset boundary

Five WSC asset headers with the confirmed animation format have no exact GBA
layout-record counterpart:

| WSC header | Layout entries | Record bytes | Tile descriptors | Tile bytes |
|---:|---:|---:|---:|---:|
| `0x23E500` | 48 | 6,360 | 61 | 64,576 |
| `0x350000` | 76 | 10,596 | 59 | 65,504 |
| `0x35A860` | 79 | 10,180 | 109 | 113,952 |
| `0x3624A0` | 66 | 9,072 | 86 | 94,912 |
| `0x3914E0` | 50 | 4,872 | 61 | 35,616 |

Raw tile inspection alone was ambiguous. Frame assembly later proved that four
of these headers are ID-indexed evolution animation assets and `0x3914E0` is a
small effect animation outside that table. Exact on-screen evolution names
still require palette and in-game transformation confirmation.

## Confirmed WSC 1.5 selector state

These observations used a fresh, emulator-generated blank SRAM path. The
user-supplied WSC save was not loaded, parsed, copied, or tested.

| Address | Width | Meaning | Evidence |
|---|---:|---|---|
| `0x30EA` | `u16[]` | Ordered selectable-character ID list | Initialization code writes the list and the captured blank-SRAM runtime contains `0..10,13,14`. |
| `0x3116` | `u16` | Current selection-list cursor | Thirteen captures produced the exact sequence `0..12`. |
| `0x3118` | `u16` | Display/transition mirror | It follows the cursor after the selection transition. |
| `0x311A` | `u16` | Maximum cursor | Stable value is `12`, giving thirteen default entries. |

The selector routine is in the fixed-ROM window at raw ROM offsets
`0x778750..0x778847` (runtime system-bus addresses `0x787A0..0x78847`). Its
confirmed initialization behavior is:

1. Write IDs `0..10` to RAM `0x30EA`.
2. When SRAM offset `0x73`, bit 0 is clear, append IDs `13` and `14`.
3. Read SRAM offset `0x67`; bit 4 appends ID `11` and bit 5 appends ID `12`.
4. Store `(entry count - 1)` at RAM `0x311A`.

The blank-SRAM visible order and stable in-game portraits establish:

| Cursor | Runtime ID | Character |
|---:|---:|---|
| `0..10` | `0..10` | Same established base roster order as the GBA version |
| `11` | `13` | Patamon |
| `12` | `14` | Tailmon / Gatomon |

The next downward move wraps to cursor 0, proving the default list ends at 12.
IDs `11` and `12` are unlock-controlled and are not present in the blank-SRAM
selection cycle. This corrects the earlier provisional idea that Patamon and
Tailmon might occupy IDs 11 and 12: the 1.5 code deliberately preserves those
IDs and assigns the new default characters IDs 13 and 14.

At raw ROM offsets `0x778B6A..0x778D17`, the input routine loads the cursor
from selection-object field `+4`, the maximum from field `+8`, wraps it, and
writes the new cursor back to field `+4`. Runtime instruction polling observed
the write followed by `PS:PC=7875:05CB` (raw next instruction `0x778D1B`).

## Confirmed WSC ID-indexed evolution table

The WSC 1.5 ROM table at raw offset `0x7403C0` has 16 records of `0x20` bytes.
Each record contains five six-byte banked pointers plus two padding bytes. Its
first pointer selects the character's evolution animation header. Correctly
normalizing a WSC pointer requires the ROM-window term:

`segment = 0x2000 + ((physical_offset & 0xFFFF) >> 4)`

This correction exposes the following first-pointer mapping:

| Runtime ID | WSC evolution header | GBA counterpart |
|---:|---:|---:|
| `0` | `0x340000` | `0x26EC38` |
| `1` | `0x36B2D0` | `0x28AE34` |
| `2` | `0x24D900` | `0x2A1960` |
| `3` | `0x3366B0` | `0x2BB970` |
| `4` | `0x3366B0` | `0x2BB970` |
| `5` | `0x34B410` | `0x2DA800` |
| `6` | `0x364930` | `0x25937C` |
| `7` | `0x34B410` | `0x2DA800` |
| `8` | `0x323C00` | `0x2FA524` |
| `9` | `0x333360` | `0x31CA58` |
| `10` | `0x333360` | `0x31CA58` |
| `11` | `0x35A860` | Missing from GBA |
| `12` | `0x3624A0` | Missing from GBA; GBA loader special-cases this ID |
| `13` | `0x350000` | Missing from GBA; Patamon evolution path |
| `14` | `0x23E500` | Missing from GBA; Tailmon/Gatomon evolution path |

The existing GBA evolution-header pointer sequence starts at ROM offset
`0x0D42B8` and has a `0x20` stride. Therefore `0x0D42D8` is runtime ID 1
(Terriermon), not Guilmon and not a generic opening pointer. The old full-asset
PoC redirects that ID-1 pointer to the WSC ID-11 asset and is intentionally a
mismatched wiring probe, not a playable port.

The remaining four WSC pointers per ID map to the GBA record's supporting
metadata/palette resources. A complete port must convert and relocate those
resources together with each missing animation header; replacing only the
first pointer cannot produce a correct evolution.

## Confirmed base/evolution record slots

The evolution table is part of a continuous 60-record WSC resource table at
`0x740000`. Structural reuse and the established runtime IDs identify these
subranges:

| Purpose | WSC records | WSC offset | GBA record base |
|---|---:|---:|---:|
| Base fighter resources, IDs `0..14` | `0..14` | `0x740000` | `0x0D3FC0` |
| Other entities/effects | `15..29` | `0x7401E0` | GBA omits or rearranges part of this range |
| Evolution resources, IDs `0..14` | `30..44` | `0x7403C0` | logical GBA base `0x0D42A0` |

The WSC base records for the two new default characters contain these five
banked-pointer targets:

| Runtime ID | Character | WSC record | Pointer targets |
|---:|---|---:|---|
| `13` | Patamon | `0x7401A0` | `0x352AB0`, `0x370000`, `0x3D5470`, `0x3D54B8`, `0x3C1680` |
| `14` | Tailmon/Gatomon | `0x7401C0` | `0x32A5E0`, `0x368FF0`, `0x3D67D0`, `0x3D67F6`, `0x2BFAF0` |

Their exact reserved/placeholder destinations in the GBA record tables are:

| Runtime ID | Base record | Evolution record | Evolution-header field |
|---:|---:|---:|---:|
| `11` | `0x0D4120` | `0x0D4400` | `0x0D4418` |
| `12` | `0x0D4140` | `0x0D4420` | `0x0D4438` |
| `13` | `0x0D4160` | `0x0D4440` | `0x0D4458` |
| `14` | `0x0D4180` | `0x0D4460` | `0x0D4478` |

IDs 13 and 14 therefore have deterministic insertion records in both base and
evolution paths. Their current GBA contents are reused placeholders and must be
replaced as complete five-resource bundles, not patched field-by-field without
conversion evidence.

## Confirmed original-to-1.5 lineage

The retail 4 MiB WonderSwan original supplied later contains the corresponding
60-record table at raw offset `0x390000`. Direct record comparison confirms:

- base records `0..11` are the original roster bundles, including Impmon at 11;
- base records `12..14` are placeholders in the original;
- evolution records `30..40` cover original runtime IDs `0..10`;
- evolution records `41..44` are placeholders in the original and are replaced
  by Ver. 1.5 content for runtime IDs `11..14`.

This independently confirms the runtime-ID interpretation above and removes
the need to infer new-character slots from Ver. 1.5 alone. Supporting evidence
and conversion limits are recorded in `version-lineage.md`.

## Completed boss-sentinel relocation

The expanded build assigns Extra Guilmon to ID `12`, so every confirmed
Millenniummon sentinel comparison was moved to ID `15` and the final-opponent
table byte at `0x08B616` was changed to `15`. The dedicated boss setup does not
pass through the generic character loader; its immediate assignment at
`0x36FD84` was therefore separately changed from `12` to `15` by the boss
integration builder. This closes the last alias between playable ID `12` and
the non-playable final-boss sentinel.
