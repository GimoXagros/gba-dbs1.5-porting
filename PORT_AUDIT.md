# Port recovery audit

Audit date: 2026-08-31 (Asia/Seoul)

This document is the authoritative recovery baseline for the current port.
It separates committed implementation from behavior actually observed in a
GBA emulator. A runtime item is marked `PASS` only when the exact candidate
identified below has produced direct evidence for it.

## Repository state

- Branch: `codex/progress-snapshot`
- Audited commit: `9d306e71eb9926b4a57b489dd59318ad445996d4`
- Available repository baseline: `ffa4ddb75cc5277d9e483e018447917480083ee3`
- Working tree at the start of the audit: clean
- Commits from baseline through audited commit: 12
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

The current candidate was rebuilt in four guarded layers into the ignored
`build/audit-v31-20260831/` directory:

| Layer | SHA-256 |
|---|---|
| Base roster | `38E5F35AA4C9A92EC0738DE01EC6C1654F0A0CC0BD75289054383FBE9A7E7AB4` |
| Stage v30 | `BA9EDDDFAE4499B2D72DCD8DDE3001128F2A4012D054796321750AE9DC9800FE` |
| Progression v5 | `DF7EF1537FBCA48C2FA08450A0535230EB46F6E058020CAE01C5859DE0ED0CA5` |
| Full composite v31 | `16F4C7A827F3F9D241A3E5C2AE3D2EB2803447F7693BDD1F88400EA2D97BE4AC` |

The full candidate is 8 MiB. Its GBA header has entry word `0xEA00002E`, title
`DIGIMON BTSP`, game code `A8SE`, maker code `B2`, fixed byte `0x96`, and a
valid stored/computed complement byte of `0x6C`.

The layer hashes reproduce the previously recorded v31 hashes byte-for-byte.
However, this is not yet a clean build from only the two original ROMs:
`build/converted-assets` and `build/stage-assets-v9` must already exist, and no
single checked-in command regenerates both directories and all four layers.
Closing that gap is required before release packaging.

## Runtime status for exact v31 candidate

Emulator: mGBA 0.10.5 release build. Candidate SHA-256:
`16F4C7A827F3F9D241A3E5C2AE3D2EB2803447F7693BDD1F88400EA2D97BE4AC`.

The emulator opened the candidate at approximately 59.9 fps and rendered its
first GBA frame (white inner field with blue border). Verification was then
stopped before the title screen was observed. The interruption is recorded as
`UNKNOWN`, not as a ROM failure.

At the user's request, subsequent verification was run without displaying an
emulator window on the monitor. A development mGBA build was started hidden,
offscreen, and on a separate non-interactive Windows desktop. Its startup Lua
file loaded, but no ROM controller or frame callback was attached; launching
the ROM first and the script second also produced no attributable callback.
Those attempts establish a harness limitation only. They do not change the
candidate's title status from `UNKNOWN` and are not counted as runtime proof.

| Runtime area | Status | Evidence or limitation |
|---|---|---|
| ROM build and header | PASS | Four layers rebuilt; header validated |
| GBA boot / first rendered frame | PASS | Exact v31 opened and rendered in mGBA |
| Initialization beyond first frame | PARTIAL | Execution began; completion not observed |
| Title/logo | UNKNOWN | Verification stopped before observation |
| Main menu | UNKNOWN | Not reached on exact v31 |
| Input response | UNKNOWN | Not exercised on exact v31 |
| First gameplay entry | UNKNOWN | Not reached on exact v31 |
| Background/map display | UNKNOWN | Not reached on exact v31 |
| Sprites, animation, palettes, scrolling | UNKNOWN | Not exercised on exact v31 |
| Collision, events, battle logic | UNKNOWN | Not exercised on exact v31 |
| Added fighters/evolutions | UNKNOWN | Static routes exist; no exact-v31 runtime proof |
| Added stage mechanics | UNKNOWN | Static code exists; no exact-v31 runtime proof |
| Digimon Shoot complete rules and transitions | NOT IMPLEMENTED | Rules, transition state, rewards, win/loss, and exit remain |
| Tag/rating/opening additions | NOT IMPLEMENTED | Required producers, persistence/UI, and opening remain |
| Alternate final boss route | UNKNOWN | Static integration exists; no exact-v31 runtime proof |
| BGM | UNKNOWN | Not verified on exact v31 |
| SFX | UNKNOWN | Not verified on exact v31 |
| Save/load | UNKNOWN | Deferred save has not been used |
| Soft reset / restart | UNKNOWN | Not exercised on exact v31 |
| Extended stability | UNKNOWN | No exact-v31 soak or regression run |

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
observed from the exact v31 candidate:

| Area | Runtime-evidenced progress |
|---|---:|
| Graphics/display | about 2% (first frame only) |
| Game logic | 0% |
| Input | 0% |
| Audio | 0% |
| Save/load | 0% |
| Overall playable/release progress | no more than 5% |

This does not mean the committed static code is absent. It means that code has
not yet earned runtime credit under the recovery audit rules.

## Single next milestone

**BOOT -> TITLE on the exact v31 hash.**

No new gameplay feature, broad refactor, or unrelated cleanup should begin
until the title/logo screen is observed reproducibly. A failure must first be
separated from emulator or automation-harness failure before any ROM code is
changed. Once this milestone passes, the next milestone may be chosen from the
new evidence; it is not pre-declared as completed work.

All further runtime checks must remain non-displaying unless the user changes
that requirement. A suitable headless or isolated renderer with an
attributable frame-dump interface is therefore the immediate verification
dependency for this milestone.
