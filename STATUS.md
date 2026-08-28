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
- Digimon Shoot palette, tiles, maps, descriptors, initializer slot, native
  presentation objects, and the stage-11 dedicated core-loop route.

The current internal stage candidate is `stage-integrated-v27.gba`, identified
only by SHA-256
`AD68EE487A2D1265F50E8B86375D0ED4A84516CABAD7A5972DB3F3E99A5C57DE`.
That file is intentionally excluded from Git. Static branch/disassembly checks
have been performed for the newest hooks, but no emulator-pass claim is made
for this candidate.

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
same stride. The Shoot-only timer callback `4090:989C` and its new resource
family are not yet converted; v27 marks the commercial `0x083731A0` callback
as an explicit temporary boundary. Rules, reward, win/loss, and exit remain
release gates.

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
