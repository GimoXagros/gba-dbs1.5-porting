# Ver. 1.5 port scope and activation gates

## Evidence boundary

This is the live completion population for the port.  A row is complete only
when its content is present in the integrated GBA candidate and both static and
runtime evidence prove that the retail GBA consumer reaches it.  The supplied
WonderSwan SRAM is registered for the final comparison gate and is not an
implementation input.

## Completion population

| Population | Ver. 1.5 addition | Current state | Required completion evidence |
|---|---|---|---|
| Selectable fighters | Patamon (ID 13), Tailmon/Gatomon (ID 14) | Integrated internal build; clean-state selection, VS load, battle load, and base attacks observed | Integrated regression after all systems are merged |
| New evolution paths | Impmon→Beelzemon Blast Mode (ID 11), Extra Guilmon→Gallantmon Crimson Mode (ID 12), Patamon→Seraphimon (ID 13), Tailmon→Ophanimon (ID 14) | Five-resource bundles integrated; evolution forms have only been exercised as base-form smoke probes | Real Calumon-triggered group-1 load and post-transition attacks for all four IDs |
| Train level | Locomon/train stage | Correct 28×18 maps, four 2×2 resources, exact Ver. 1.5 spawn record, route ID 13→stage 8, native extended movement pattern, native two-record object configuration, both native train movement callbacks, and static display/scroll/palette translation integrated in internal stage build v21 | Collision, vents/bounce producers, and final integrated runtime proof |
| Impmon level | Iraira Room digital stage with persistent suction behavior | Retail digital-stage palette/tiles reused exactly; eight new 28×18 maps, two 2×2 resources, exact Ver. 1.5 spawn record, route ID 11→stage 10, native extended movement pattern, bounded object configuration, and both confirmed stage-9/10 object-flag exceptions integrated in v21 | Native object callbacks, collision, automatic suction producer/consumer path, background motion, and final integrated runtime proof |
| Waterfall level | Pichipichi/PetiPeti Falls vertical waterfall stage | Correct palette/tiles and six 28×18 maps, two 1×3 resources, exact Ver. 1.5 spawn record, route ID 14→stage 9, native extended movement pattern, bounded object configuration, static display/palette path, three-phase rolling-hazard state machine, and both confirmed stage-9/10 object-flag exceptions integrated in v21 | Native mode-1/mode-2 visual/movement callbacks, remaining vertical-stage engine branches, and final integrated runtime proof |
| Final boss | ZeedMillenniummon alternate/second final-boss path | Statically integrated | Reachable Normal-or-harder/no-continue two-phase route, converted battle graphics, sentinel relocation; final runtime regression deferred |
| Minigame | Digimon Shoot | Palette, tiles, eight maps, resource descriptors, initializer slot ID 11, and bounded legacy analog integrated statically; dedicated update/mode route is pending | Menu/reward route, rules, update/display callback, win/loss and exit transitions |
| Progression | Tag/reward/rating and related collection state | Population confirmed; binary mapping pending | New-save and progressed-save unlock/reward persistence, collection display |
| Opening/presentation | Extended opening with added roster/evolution duels | Population confirmed; binary mapping pending | Cold-boot playback through full extended sequence and skip transition |

## Activation gates

1. No final supplied-SRAM run until every population row above has an
   integrated candidate and its clean-state runtime checks pass.
2. A rendered or directly forced asset is diagnostic evidence only.  It does
   not prove the retail consumer reaches or uses the asset.
3. Final output is a patch only.  Applying it to the exact documented USA ROM
   must byte-for-byte recreate the validated candidate; no ROM image may be
   placed in `outputs/`.

## Scope correction record

The first implementation pass treated the four character/evolution bundles as
the full port.  External scope cross-checking and direct WSC bank inspection
showed that this omitted three stages, a boss path, a minigame, progression/tag
state, and opening changes.  The premature supplied-SRAM roster observation is
therefore invalid as final QA and remains documented only as an invalidated
observation in `final-qa.md`.

The earlier stage-bank classification was also corrected.  WSC banks `0x4B`
and `0x4C` are not wholly new: they contain relocated retail stages.  Exact
cross-version/GBA matching now identifies the new payloads as train palette
and tiles at `0x430000/0x4300E0` with maps at `0x435000`, Iraira maps at
`0x4C60E0` while reusing the retail digital-stage graphics at
`0x4C0000/0x4C0160`, and waterfall graphics/maps at
`0x4D0000/0x4D00E0/0x4D40E0`.
