# Port status

Snapshot date: 2026-08-31 (Asia/Seoul)

> **Recovery correction:** [`PORT_AUDIT.md`](PORT_AUDIT.md) is the
> authoritative current status. The earlier 55-60% / 57% planning estimate is
> withdrawn because it mixed static integration with unverified runtime
> behavior. The exact v31 candidate currently has direct evidence only for GBA
> boot/first-frame rendering; overall runtime-evidenced progress is no more
> than 5%. The single next milestone is `BOOT -> TITLE`.

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

The current internal composite candidate is `full-integrated-v31.gba`, identified
only by SHA-256
`16F4C7A827F3F9D241A3E5C2AE3D2EB2803447F7693BDD1F88400EA2D97BE4AC`.
That file is intentionally excluded from Git. Static branch/disassembly checks
and independent rebuild hash checks have been performed for the newest hooks,
but no emulator-pass claim is made for this candidate.

v31 is the current composite after the recent Shoot display work. Its checked
build chain is v30 stage integration
`BA9EDDDFAE4499B2D72DCD8DDE3001128F2A4012D054796321750AE9DC9800FE`
→ progression/unlock integration
`DF7EF1537FBCA48C2FA08450A0535230EB46F6E058020CAE01C5859DE0ED0CA5`
→ Zeed final-boss integration. Repeating all three builds produces the same
hashes byte-for-byte.

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
| Progression, tag/rating, opening | 25% | Remaining producers, persistence/UI, opening implementation |
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

Detailed scope and evidence requirements live in
[`records/port-scope.md`](records/port-scope.md); the deferred save gate is in
[`records/final-qa.md`](records/final-qa.md).
