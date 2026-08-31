# Port recovery audit

Audit date: 2026-08-31 (Asia/Seoul)

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

These are real GBA-side code/data changes. Their presence and static structure
do not by themselves prove that the corresponding gameplay paths work.

### B. Asset and conversion tooling

- WSC-to-GBA graphics, palette, map, descriptor, object-record, and table
  conversion helpers.
- ROM survey, disassembly, probe, smoke-build, and manifest generation tools.
- Four guarded builders used for the current composite candidate.

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

The corrected candidate was rebuilt in four guarded layers into the ignored
`build/audit-fix-v32/` directory:

| Layer | SHA-256 |
|---|---|
| Corrected base roster | `5FE62385736851014C62E8F68B5D8F1583230DE2A30648CE893E3A45440B4ECA` |
| Stage integration | `FA0A48EC933AB9A2BD8960A61D0BE6F07CD15E2FC0B2037917595BDE154DACED` |
| Progression integration | `6D18B67E80C85429B20468449EB4024D4A29C50FC73A133163D028B02408D623` |
| Full composite v32 | `1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291` |

The full candidate is 8 MiB. Its GBA header has entry word `0xEA00002E`, title
`DIGIMON BTSP`, game code `A8SE`, maker code `B2`, fixed byte `0x96`, and a
valid stored/computed complement byte of `0x6C`.

The guarded layers are deterministic from their current inputs. However, this
is not yet a clean build from only the two original ROMs:
`build/converted-assets` and `build/stage-assets-v9` must already exist, and no
single checked-in command regenerates both directories and all four layers.
Closing that gap is required before release packaging.

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
| Tag/rating/opening additions | NOT IMPLEMENTED | Required producers, persistence/UI, and opening remain |
| Alternate final boss route | UNKNOWN | Static integration exists; no exact-v32 runtime proof |
| BGM | UNKNOWN | Not verified on exact v32 |
| SFX | UNKNOWN | Not verified on exact v32 |
| Save/load | UNKNOWN | Deferred save has not been used |
| Soft reset / restart | UNKNOWN | Not exercised on exact v32 |
| Extended stability | UNKNOWN | No exact-v32 soak or regression run |

## Known implementation gaps

- Train vents/bounce behavior, Iraira suction, and remaining vertical-stage
  engine branches.
- Digimon Shoot rules/object callbacks, private transition state, reward,
  win/loss, menu, and exit behavior.
- Tag/reward/rating persistence and associated UI.
- Extended opening/presentation sequence.
- End-to-end added-fighter evolution paths and alternate-boss outcomes.
- Audio parity, save/load parity, reset behavior, and stability regression.
- A single clean build command and final BPS generation/round-trip validation.

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
complete for exact v32. The next active milestone is **CLEAN CURRENT-CANDIDATE
BUILD FROM DECLARED ORIGINAL INPUTS**. The present four-layer build still
depends on ignored pre-generated asset directories, so no further static
content claim should be treated as reproducible until each dependency is
either regenerated by the main path or explicitly identified as a remaining
non-reproducible gate.

All further runtime checks must remain non-displaying unless the user changes
that requirement. `tools/mgba_headless_gdb_capture.py` provides the current
private-desktop, attributable frame-and-memory capture boundary.
