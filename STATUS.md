# Port status

Snapshot date: 2026-08-27 (Asia/Seoul)

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

The current internal stage candidate is `stage-integrated-v18.gba`, identified
only by SHA-256
`25AE78266064DC4703B58F41388C4D6A2D50CF4EF4704185D5977DA6B5DF7B3D`.
That file is intentionally excluded from Git. Static branch/disassembly checks
have been performed for the newest hooks, but no emulator-pass claim is made
for this candidate.

v18 corrects the WSC `ES:0384` waterfall state mapping to GBA
`0x0300256A`. It also bounds six confirmed calls that would otherwise index
retail eight-entry tables with stage IDs 8–10, plus the setup-time dimension
lookup. Native Ver. 1.5 object-mode records still replace that temporary
analog mapping in a later integration step.

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
