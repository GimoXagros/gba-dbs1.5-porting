# Port recovery audit

Audit date: 2026-08-31; last updated 2026-09-01 (Asia/Seoul)

This document is the authoritative recovery baseline for the current port.
It separates committed implementation from behavior actually observed in a
GBA emulator. A runtime item is marked `PASS` only when the exact candidate
identified below has produced direct evidence for it.

## Repository state

- Branch: `codex/progress-snapshot`
- Recovery-audit base commit: `48b5d3932d92b334454dc9a9bc00ef5f6fcf6ca1`
- Available repository baseline: `ffa4ddb75cc5277d9e483e018447917480083ee3`
- Working tree at the start of the audit: clean
- Commits from baseline through recovery-audit base: 12
- Configured Git remote: none
- Tracked ROM, save, extracted binary, screenshot, or emulator state: none

There is currently no GitHub destination to which this branch can be pushed.
The local Git history is the only repository record until a remote is supplied
or configured.

## Exact port objective

Reproduce the additional content and behavior of *Digimon Tamers: Battle
Spirit Ver. 1.5* in the USA GBA release of *Digimon: Battle Spirit*. The final
deliverable is a reproducible BPS patch, input/output hashes, application
instructions, and verification evidence. Original or patched ROM images must
not be committed or distributed. The supplied WSC save is reserved for final
QA after all declared content is integrated.

## Architecture decision

**Current architecture: static/binary translation on the commercial GBA
engine.**

Python tools convert selected WSC data and assets, while generated ARM code and
tables hook or extend the existing USA GBA program. This repository does not
contain a WonderSwan CPU, PPU, APU, or system emulator, and it does not append
the WSC ROM as an executable compatibility payload. It is therefore neither a
native source port nor an emulator-assisted port.

## Work classification

### A. Actual GBA runtime integration

- GBA ROM expansion, table relocation, ARM hook generation, and guarded
  downstream layering.
- Added fighter/evolution resource routes, added-stage tables and callbacks,
  progression/unlock changes, and alternate final-boss data/code.
- Digimon Shoot stage routing, graphics/palette data, core-loop route, timer
  callback, normal display callback, and scanline-threshold callback.
- Opening modulo-5 dispatcher plus the added state-3/state-4 case setup,
  callbacks, and converted motion/event tables.

These are real GBA-side code/data changes. Their presence and static structure
do not by themselves prove that the corresponding gameplay paths work.

### B. Asset and conversion tooling

- WSC-to-GBA graphics, palette, map, descriptor, object-record, and table
  conversion helpers.
- ROM survey, disassembly, probe, smoke-build, and manifest generation tools.
- Five guarded builders used for the current composite candidate.

### C. Emulation or compatibility layer

None. No WonderSwan execution core or compatibility runtime is present.

### D. Stubs, placeholders, and bounded fallbacks

- `UPDATE_STUB` at expansion address `0x582E80` is written as `bx lr`; the
  current stage update table points at dedicated train, waterfall, Iraira, and
  Shoot entries instead, so this is an unused residue rather than a working
  implementation.
- The Digimon Shoot spawn record is a bounded safety copy of a retail stage-7
  record, not yet a translation of the complete Ver. 1.5 rules/object system.
- Several `legacy_stage_analogs` mappings deliberately keep old GBA consumers
  in range; they are compatibility fallbacks, not proof of equivalent added
  stage behavior.
- The Shoot `0x400` transition branch falls back to a matching retail callback
  because the WSC private state used by `5EEA:0D87/0E0B` is not mapped.
- Probe and smoke ROMs demonstrate isolated routes only and are not release or
  full-candidate evidence.

### E. Irrelevant, superseded, or duplicate artifacts

- The ignored `build/` directory contains dozens of historical ROMs,
  manifests, binary extracts, saves, and screenshots from intermediate v2-v30
  work. They are not the current candidate.
- Earlier provisional waterfall mode-3 work was retracted after direct table
  analysis showed the assumption was incorrect.
- `local/mgba-dev/` contains an unusable zero-byte executable, while
  `local/mgba-dev-complete/` contains the usable development build.
- Numerous one-off probe/smoke scripts overlap in purpose. They are retained
  until their dependencies are audited; this correction does not delete or
  rewrite valid historical work.

## Reproducibility audit

The current static candidate was rebuilt in five guarded layers into two
ignored clean output directories:

| Layer | SHA-256 |
|---|---|
| Corrected base roster | `5FE62385736851014C62E8F68B5D8F1583230DE2A30648CE893E3A45440B4ECA` |
| Stage integration | `FA0A48EC933AB9A2BD8960A61D0BE6F07CD15E2FC0B2037917595BDE154DACED` |
| Progression integration | `6D18B67E80C85429B20468449EB4024D4A29C50FC73A133163D028B02408D623` |
| Zeed boss / runtime-evidenced composite v32 | `1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291` |
| Opening-choice/resources / current static composite v34 | `33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1` |

The full candidate is 8 MiB. Its GBA header has entry word `0xEA00002E`, title
`DIGIMON BTSP`, game code `A8SE`, maker code `B2`, fixed byte `0x96`, and a
valid stored/computed complement byte of `0x6C`.

The clean-build gap is now closed for the current candidate.
`tools/build_current_candidate.py` takes the hash-identified USA GBA, retail
WSC 1.0, and WSC Ver. 1.5 originals and regenerates the P4 and opening-P1
conversion corpora, all fourteen consumed character/evolution/VS/boss blobs,
the opening P0 blob, all twelve consumed stage blobs, and all five ROM layers.
Every source, intermediate, asset, and layer is checked against its expected
SHA-256.

The former VS presentation generator required two ignored 64 KiB emulator RAM
dumps. Direct attribution proved that the Patamon/Tailmon palettes and planar
tiles are exact WSC ROM ranges. Their verified sparse 28x18 runtime placement
is now encoded as a reviewable generator rule. A clean ROM-only regeneration
produces VS blob SHA-256
`2D212622DB36E3D86281768F8C3438D394451FA275D519AA32B97FEE697D2856`,
byte-identical to the prior RAM-derived blob.

Two new runs in separate empty output directories each regenerated exact v34
SHA `33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1`.
The preceding four layers still reproduce exact v32 SHA
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
This proves current-candidate reproducibility only; it does not close any
missing-content or final-QA gate. No emulator or supplied save was used for
the v34 build checks.

## Boot regression and correction

The exact v31 composite was rechecked with mGBA on a private Windows desktop,
with no emulator window visible on the user's monitor. At 45 seconds it had
returned to the initial white/blue frame instead of reaching the title. The
base, stage, progression, and full v31 layers shared this failure, while the
unaltered USA ROM reached the title under the same harness.

Binary ablation isolated the failure to the relocated roster literal at ROM
offset `0x83CF8`. The builder treated `0x0D3FC0` as the start of each 0x20-byte
record, but the engine consumer at `0x08088250` reads fields at offsets 0, 4,
and 8 from the canonical record base `0x0D3FB8`. The relocated table therefore
lost its first eight bytes and supplied `0xFFFFFFFF` fields during the opening
sequence. The minimal correction relocates from `0x0D3FB8` to `0x4A80F8`,
preserving all existing pointer values while copying complete records. Builder
assertions now require unchanged retail records to remain byte-identical.

## Runtime status for exact v32 candidate

The exact full v32 SHA-256 is
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
It was run for 45 seconds with development mGBA SHA-256
`0D9A2779ADD78D41A093C3AF8CEC7D72CC07A5451C8A1E1B167B48CD54950288`
on a private, non-interactive Windows desktop. The captured 240x160 title
frame SHA-256 is
`644C6C5269FB847FF90BB9ADDFECC11462830A96CFCC47D9D33A2620455F387B`,
byte-identical to the historical known-good title capture. The evidence and
memory hashes are recorded under ignored directory
`evidence/full-fixed-gdb-title-20260831-r2/`; its manifest records
`monitor_visible: false`.

The next controlled run pressed the default mGBA Start key at 45.0 seconds,
held it for 0.25 seconds, and captured at 52.0 seconds. Exact v32 produced
menu-frame SHA-256
`CFDA553C0C6B14BB65E8A34543E3A657B92338751B207644A9D42D2786C24BF2`,
byte-identical to the unmodified USA ROM under the same timings. Palette,
VRAM, and OAM hashes also match the USA control. Manifests are under ignored
directories `evidence/usa-gdb-menu-20260831/` and
`evidence/full-fixed-gdb-menu-20260831/`, both with `monitor_visible: false`.

A second scheduled input pressed the default mGBA A key at 53.0 seconds and
captured at 60.0 seconds. Exact v32 and the USA control both entered display
state `DISPCNT=0x6B40`; palette, VRAM, and EWRAM were byte-identical. Their
frames differed by 635 of 38,400 pixels and OAM differed from offset `0x210`,
consistent with a different sprite-animation phase at a wall-clock capture;
the shared selection background and game state are direct evidence for the
transition, not for roster correctness. Manifests are under ignored
directories `evidence/usa-gdb-character-select-20260831/` and
`evidence/full-fixed-gdb-character-select-20260831/`.

A third A press at 61.0 seconds and capture at 75.0 seconds entered the first
retail battle in both ROMs. `DISPCNT=0x3F40`, the full palette, battle state
`0x03002310..0x0300231F`, stage byte 1, and player pointers
`0x0300489C/A0` match. Exact v32 differs as intended in the selection list
(`0x03004710`) and maximum cursor (12 instead of 6); dynamic battle VRAM and
the frame are not byte-identical because the independently timed battles had
already advanced to different animation/camera phases. This proves baseline
battle entry only. Manifests are under ignored directories
`evidence/usa-gdb-first-battle-20260831/` and
`evidence/full-fixed-gdb-first-battle-20260831/`.

The first directional-input experiment compared player coordinates at two
wall-clock times. The USA control moved right, but v32 had already entered a
different combat/animation phase and its object was repositioned; that result
is `INCONCLUSIVE`, not evidence of either success or failure. Static analysis
then identified the common retail input consumer: `0x083750FC` loads the frame
input at `0x03001302`, and `0x08375138/3C` stores the translated halfwords to
the current player object's `+0x2C/+0x2E`. A corrected run delivered Right
while stopped and broke at `0x08375140`, immediately after those stores.

Both the USA control and exact v32 produced GBA `KEYINPUT=0x03EF` (Right
active-low), frame input `0x0002`, registers `r0=r1=0x0002`, and player-1
fields `+0x2C/+0x2E=0x0002`. This directly proves the same bounded Right-input
consumer path. Evidence is under ignored directories
`evidence/usa-gdb-first-battle-right-consumer-20260831-r2/` and
`evidence/full-fixed-gdb-first-battle-right-consumer-20260831-r2/`; both
manifests record `monitor_visible: false`.

| Runtime area | Status | Evidence or limitation |
|---|---|---|
| ROM build and header | PASS | Four corrected layers rebuilt; header validated |
| GBA boot / first rendered frame | PASS | Exact v32 rendered through the opening sequence |
| Initialization beyond first frame | PASS | Exact v32 reached the stable title frame at 45 s |
| Title/logo | PASS | Exact title PNG matches known-good capture byte-for-byte |
| Main menu | PASS | Post-Start frame is byte-identical to the USA control |
| Input response | PASS | Start/A transitions and battle Right consumer observed |
| Character select entry | PASS | A input reached matching display/background/game state |
| First gameplay entry | PASS | ID-0 selection reached matching retail battle state |
| Background/map display | PASS | First retail arena rendered; stage ID matches control |
| Sprites, animation, palettes, scrolling | PARTIAL | Rendered in baseline battle; behavior not exercised |
| Collision, events, battle logic | UNKNOWN | Not exercised on exact v32 |
| Added fighters/evolutions | UNKNOWN | Static routes exist; no exact-v32 runtime proof |
| Added stage mechanics | UNKNOWN | Static code exists; no exact-v32 runtime proof |
| Digimon Shoot complete rules and transitions | NOT IMPLEMENTED | Rules, transition state, rewards, win/loss, and exit remain |
| Tag/rating/opening additions | PARTIAL STATIC ONLY | Opening choice states 3/4, modulo-5 dispatch, and selector resources 11..14 are integrated in untested v34; four linear additions plus tag/rating producers and persistence/UI remain |
| Alternate final boss route | UNKNOWN | Static integration exists; no exact-v32 runtime proof |
| BGM | UNKNOWN | Not verified on exact v32 |
| SFX | UNKNOWN | Not verified on exact v32 |
| Save/load | UNKNOWN | Deferred save has not been used |
| Soft reset / restart | UNKNOWN | Not exercised on exact v32 |
| Extended stability | UNKNOWN | No exact-v32 soak or regression run |

### Opening/presentation evidence correction (2026-09-01)

The 18-to-24 initializer increase is now connected to the registered cold-boot
roots rather than inferred from call counts. Static callback recovery proves
that the commercial GBA and WSC 1.0 openings each contain a 15-callback linear
path and three choice callbacks. WSC 1.5 contains 19 linear callbacks and five
choices. Every population member is graph-reachable from its version's
registered root.

Monotonic instruction-shape alignment identifies four WSC 1.5-only linear
callbacks at `7077`, `7407`, `7698`, and `7992`, plus choice callbacks at
`9C17` and `9E40`. Object-selector extraction also confirms the expanded
roster/evolution inputs. The split state is a high-nibble cycle: GBA/WSC 1.0
advance modulo 3, while WSC 1.5 advances modulo 5. New state 3 selects callback
`9E40` with pair `[13,14]`; state 4 selects `9C17` with `[12,11]`.

Internal v34 now translates those two added case setup blocks, both callbacks,
their motion/event tables, and the five-state dispatcher into GBA ARM code.
States 0..2 branch to the unchanged commercial GBA cases. The builder hashes
the exact WSC source ranges and reused GBA ranges, refuses nonblank expansion
targets, and is part of the clean main build. A dedicated 15-record resource
view preserves commercial selectors 0..10 and adds Ver. 1.5 selectors 11..14.
All four P1/P2 resources and selector 11/13 P0 resources reuse byte-identical
commercial assets. Only selector 12/14 P0 containers are newly converted and
inserted.

The four added linear callbacks at `7077`, `7407`, `7698`, and `7992` are now
bounded to the chain edge from GBA `0x08085118` to `0x08085454`; the exact
assignment and selector instructions are ROM offsets `0x08516C` and
`0x0851CC`. The first and fourth additions also require WSC 1.5 replacement
resource records 50 and 49. A guarded conversion proves that both P0
animation/tile containers and both P2 palettes already exist byte-for-byte in
the unmodified USA GBA ROM. Their P1 sources are also identical to WSC 1.0
records 41 and 39, whose complete native GBA views are `0x080D44D8` and
`0x080D4498`. The commercial consumer at `0x08088250` selects a 0x20-byte
record and creates an object at `0x03002908 + slot*0x50`; its constructor and
companion calls are `0x080127E4` and `0x080132EC`. Therefore the native
translation can use the existing complete records and does not require a
direct counterpart for WSC primary loader `4FFF:226E`. The four callbacks,
auxiliary-object activation/cleanup, and aligned selector-3→13 change remain
unimplemented. Their source state machines are nevertheless bounded: the
first three map to commercial GBA callback-template lineages 7/8/9; the fourth
owns a seven-entry event table and requires a bespoke translation. Exact
commercial WSC 1.0/GBA instruction pairs additionally derive a guarded timing
and motion plan for all four additions. Those derived constants remain an
implementation inference until non-displaying runtime timing and transition
QA. No v34 runtime evidence was collected. See
`records/opening-presentation.md` for addresses and manifest hashes.

A hidden/chromeless WSC 1.0 capture attempt parsed its command line but did not
start the Lua script. It generated no frame, RAM, or completion evidence and is
classified as inconclusive. No monitor-visible window was used, and no further
runtime attempt was made in this milestone.

## Known implementation gaps

- Train vents/bounce behavior, Iraira suction, and remaining vertical-stage
  engine branches.
- Digimon Shoot rules/object callbacks, private transition state, reward,
  win/loss, menu, and exit behavior.
- Tag/reward/rating persistence and associated UI.
- Four added linear opening callbacks, native second-slot lifetime/cleanup for
  the already resident auxiliary records, aligned selector-3→13 behavior, and
  complete extended opening/presentation sequence.
- End-to-end added-fighter evolution paths and alternate-boss outcomes.
- Audio parity, save/load parity, reset behavior, and stability regression.
- Final BPS generation/round-trip validation after all content and QA gates.

## Corrected progress statement

The previous 55-60% / 57% figure mixed static implementation with assumed
runtime readiness and is withdrawn. Based strictly on behavior directly
observed from the exact corrected v32 candidate:

| Area | Runtime-evidenced progress |
|---|---:|
| Graphics/display | about 12% (through first retail arena entry only) |
| Game logic | about 1% (baseline battle transition only) |
| Input | about 5% (Start/A transitions and one battle direction only) |
| Audio | 0% |
| Save/load | 0% |
| Overall playable/release progress | no more than 8% |

This does not mean the committed static code is absent. It means that code has
not yet earned runtime credit under the recovery audit rules.

## Single next milestone

The baseline path through one `FIRST RETAIL BATTLE` Right-input consumer is
complete for exact v32. The clean v34 build, static opening callback graphs,
two added choice callbacks, modulo-5 dispatcher, and selector resources 11..14
are also complete. The next
active milestone remains **EXTENDED OPENING/PRESENTATION IMPLEMENTATION**:
wire the resident auxiliary resources, translate the four added linear
callbacks and aligned selector-3→13 behavior,
then preserve the full graph through the same main build path. Broader runtime
verification remains deferred and non-displaying.

All further runtime checks must remain non-displaying unless the user changes
that requirement. `tools/mgba_headless_gdb_capture.py` provides the current
private-desktop, attributable frame-and-memory capture boundary.
