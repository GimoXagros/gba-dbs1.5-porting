# Port status

Snapshot date: 2026-09-01 (Asia/Seoul)

> **Recovery correction:** [`PORT_AUDIT.md`](PORT_AUDIT.md) is the
> authoritative current status. The earlier 55-60% / 57% planning estimate is
> withdrawn because it mixed static integration with unverified runtime
> behavior. A roster-record relocation defect in v31 was isolated and fixed.
> Exact v32 now passes `BOOT -> TITLE -> MAIN MENU -> CHARACTER SELECT` in
> non-displaying mGBA runs and reaches the first retail battle; overall
> runtime-evidenced progress is no more than 8%. The single next runtime
> milestone was completed by observing the retail Right-input consumer. The
> clean current-candidate milestone is now complete: two independent builds
> from the hash-identified USA GBA, WSC 1.0, and WSC 1.5 originals reproduce
> exact v32 byte-for-byte. This closes a build-reproducibility gap only; the
> overall runtime-evidenced progress remains no more than 8%.

This repository tracks an in-progress clean-room port of the complete
WonderSwan Color Ver. 1.5 content set to the USA GBA release. It is not a
release and contains no original or patched ROM image, save, extracted asset,
memory dump, screenshot, or emulator state.

## Integrated in the current internal candidate

- Patamon and Tailmon/Gatomon base fighters, resource bundles, selection,
  versus, and battle-load routes.
- Four added evolution resource bundles: Beelzemon Blast Mode, Gallantmon
  Crimson Mode, Seraphimon, and Ophanimon.
- Static stage content and routing for Locomon/train, waterfall, and Iraira
  Room, including bounded legacy consumers.
- Waterfall three-phase rolling-hazard state machine and confirmed stage 9/10
  object-flag exceptions.
- Static ZeedMillenniummon alternate final-boss integration.
- Digimon Shoot palette, tiles, maps, descriptors, initializer slot, native
  presentation objects, and the stage-11 dedicated core-loop route.

The corrected internal composite candidate is `full-fixed.gba`, identified
only by SHA-256
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
That file is intentionally excluded from Git. Its corrected base, stage, and
progression layer hashes are recorded in [`PORT_AUDIT.md`](PORT_AUDIT.md).
Exact v32 reaches title, responds to Start with a main-menu frame byte-identical
to the USA control, and responds to A by entering the same character-select
display/background/game state while mGBA runs on a private, non-interactive
desktop. Character roster correctness remains unverified.

Selecting retail character ID 0 also reaches the same baseline battle state,
stage byte, and player pointers as the USA control. This is entry proof only;
battle input, collision, attacks, damage, results, and added-content behavior
remain unverified.

A bounded Right press is now verified at the exact retail consumer in both the
USA control and v32: hardware input, translated frame input, registers, and
the current player object's input fields agree. Attacks, collision, damage,
results, and added-content behavior remain unverified.

`tools/build_current_candidate.py` is now the checked-in main build entry
point. It regenerates the P4 comparison corpus and all currently consumed
binary assets from the three original ROMs before assembling the four guarded
layers. Two builds in separate empty output directories both produced
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`.
The VS generator no longer consumes Patamon/Tailmon emulator RAM dumps:
palette and tile ranges are read directly from WSC 1.5, while the verified
sparse 28x18 runtime composition is an explicit checked-in build rule. The
newly generated VS blob is byte-identical to the prior RAM-derived blob.

v31 is retained as superseded history. Its relocated roster records omitted
the canonical first eight bytes, causing the opening sequence to return to the
initial frame. v32 corrects only that record origin and advances the guarded
downstream hashes; no unrelated gameplay implementation was changed.

## Historical implementation estimate (withdrawn)

The table below is retained only as a record of the former static-work
estimate. It must not be read as playable or release progress. Runtime status
and corrected progress are recorded in [`PORT_AUDIT.md`](PORT_AUDIT.md).

| Area | Former static-work estimate | Main remaining work |
|---|---:|---|
| Fighters and evolution resources/routes | 80% | Real evolution transitions and final regression |
| Added stage content and mechanics | 65% | Train vents/bounce, suction, remaining vertical branches |
| Alternate final boss | 70% | End-to-end runtime route, loss/continue/victory regression |
| Digimon Shoot | 45% | Rules/objects, transition state, reward, win/loss, exit |
| Progression, tag/rating, opening | 25% | Remaining producers, persistence/UI, and cold-boot opening dispatch/implementation |
| Build tooling and static integration | 85% | Full final-candidate audit and release packaging |
| Final emulator/save QA and BPS release | 0% | Deferred until all content is connected |

v26 retains the corrected WSC `ES:0384` waterfall-state mapping to GBA
`0x0300256A`, but retracts v20's provisional mode-3 initializer. Direct table
analysis proves that waterfall stage 9 is configured with callbacks
`4090:3DFB` and `4090:3EE0`, which produce modes 1 and 2; `4090:3FCA` is a
separate behavior and cannot be treated as the stage initializer.

The Ver. 1.5 movement-pattern and graphics/object-configuration tables are now
native through ID 11. The latter is relocated to twelve entries after its
commercial WSC→GBA record-conversion rule is checked against all eight retail
stages. Stages 8–11 use their exact Ver. 1.5 record pairs and eight translated
callbacks: train `3CD5/3D7B`, waterfall `3DFB/3EE0`, Iraira Room
`40AF/42B5`, and Shoot `432F/43E6`. Waterfall callbacks now produce the
correct modes 1 and 2 at GBA `0x0300256A`. Four unrelated legacy consumers
plus the setup-time dimension lookup remain bounded independently; those
analogs no longer apply to this native object-configuration family.

Digimon Shoot update slot 11 is no longer a return stub. Static comparison
with the commercial stage-7 conversion establishes the camera state
(`0x03002338`), threshold outputs (`0x03004D44/46`), palette-animation state
(`0x03003D30`), and stage flags (`0x0300450A`) without inventing a parallel
ABI. v25 installs the exact stage-11 threshold scan and converts all 202
BGR444 colors used by its two three-rate palette-table groups to GBA BGR555.
The commercial battle loop at GBA `0x083700F0..0x0837024C` is also the exact
translation of WSC `4090:583E`. v27 replaces its first literal load with a
bounded dispatcher: stages 0–10 reproduce the displaced counter update and
rejoin at `0x08370104`, while actual stage ID 11 enters the translated WSC
`4090:7572` core loop and returns through the original epilogue. The WSC
`4090:7642` signed scroll state machine and its 48-color BGR444 table are
converted to GBA BGR555 and write the same sixteen palette entries at the
same stride. v28 replaces the final temporary call to commercial
`0x083731A0` with the translated Shoot-only timer callback `4090:989C`. Its
three WSC runtime-palette records are converted by a rule verified against all
three records selected by the commercial `4090:6FDE`→GBA `0x083731A0`
lineage, including the distinct GBA record trailer. v30 replaces the normal
display callback with a translation of WSC `5EEA:0C3A` and connects the
translated scanline threshold callback `5EEA:0D42`. The Shoot flag `0x400`
transition branch still falls back to the matching retail GBA callback until
the private state used by WSC `5EEA:0D87/0E0B` is mapped without guessing.
Rules, reward, win/loss, and exit remain release gates.

v26 also completes the four confirmed stage-9/10 renderer-flag consumers.
The commercial player constructor at GBA `0x08353428` is the exact counterpart
of the WSC raw `0x74382E` branch. The shared stage/character auxiliary
constructor at GBA `0x0835B298..0x0835B3A8` matches WSC `4090:53D7`, including
the stage×character lookup, object loader, four cleared motion fields, `4/7`
state pair, and `0x1100` clamp; its flag site is `0x0835B354`. Both now call
the same bounded stage-9/10 exception helper already used by the two later
object-construction consumers.

## Remaining release gates

1. Finish the train, waterfall, and Iraira Room runtime mechanics and remaining
   vertical-stage engine branches.
2. Port Digimon Shoot rules/object callbacks, the remaining transition state,
   menu/reward route, win/loss behavior, and exit transitions.
3. Port tag/reward/rating persistence and the extended opening/presentation
   sequence.
4. Combine every declared Ver. 1.5 population in one reproducible candidate and
   pass the full static-integrity audit.
5. Only then run final emulator QA, including the separately supplied WSC save,
   and record evidence against the exact candidate hash.
6. Generate and verify a BPS patch whose application to the documented USA ROM
   reproduces the validated candidate byte-for-byte. Publish the patch,
   application instructions, and hashes—never a ROM image.

The opening/presentation initializer population is now bounded more precisely:
the declared originals contain 18 relevant calls in the commercial GBA and WSC
1.0 ROMs and 24 in WSC 1.5. The six-call delta is confirmed, but its cold-boot
dispatcher attribution is not; it is not counted as integrated opening logic.

Detailed scope and evidence requirements live in
[`records/port-scope.md`](records/port-scope.md); the deferred save gate is in
[`records/final-qa.md`](records/final-qa.md).
