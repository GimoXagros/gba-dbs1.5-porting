# Port status

Snapshot date: 2026-08-28 (Asia/Seoul)

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
- Digimon Shoot palette, tiles, maps, descriptors, initializer slot, and
  confirmed dedicated-mode control-flow map.

The current internal stage candidate is `stage-integrated-v25.gba`, identified
only by SHA-256
`99A50594464046A78B3F720F1C8692FEDBAE5D2FDDC6BA857CBC0BB2C482C8EB`.
That file is intentionally excluded from Git. Static branch/disassembly checks
have been performed for the newest hooks, but no emulator-pass claim is made
for this candidate.

v25 retains the corrected WSC `ES:0384` waterfall-state mapping to GBA
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
The retail callback from the same lineage remains temporary: the Shoot-only
interrupt callback, transition helper, dedicated loop, rules, and exit are
still release gates.

## Remaining release gates

1. Finish the train, waterfall, and Iraira Room runtime mechanics and remaining
   vertical-stage engine branches.
2. Port Digimon Shoot rules, update/display callbacks, menu/reward route,
   win/loss behavior, and exit transitions.
3. Port tag/reward/rating persistence and the extended opening/presentation
   sequence.
4. Combine every declared Ver. 1.5 population in one reproducible candidate and
   pass the full static-integrity audit.
5. Only then run final emulator QA, including the separately supplied WSC save,
   and record evidence against the exact candidate hash.
6. Generate and verify a BPS patch whose application to the documented USA ROM
   reproduces the validated candidate byte-for-byte. Publish the patch,
   application instructions, and hashes—never a ROM image.

Detailed scope and evidence requirements live in
[`records/port-scope.md`](records/port-scope.md); the deferred save gate is in
[`records/final-qa.md`](records/final-qa.md).
