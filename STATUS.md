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
> clean current-candidate milestone is now complete: the hash-identified USA
> GBA, WSC 1.0, and WSC 1.5 originals reproduce internal v40 byte-for-byte in
> two independent builds. Its modulo-5 dispatcher, added choice states 3
> and 4, selector resource records 11..14, four added linear callbacks, and
> sequential slot-3 reuse for auxiliary records 50/49 are statically integrated.
> The Shoot child P1/P0/P2 resources and resident
> `9229 -> 94C1 -> 9570 -> 9617` generator/callback family are also integrated,
> including the payload-proved WSC 1.5 `A7` -> WSC 1.0 `A5` -> GBA `0x4A`
> sound request. The Ver. 1.5-only parent-start `CE` payload is now represented
> by a bounded native GBA ID `0x5B` M4A reconstruction that preserves its
> packed pitch, 20-tick lead, and four 10-tick volume-decay steps,
> and reproducible at SHA-256
> `9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B`.
> This closes part of the opening implementation gap only; exact v32 remains
> the last runtime-evidenced candidate and the
> overall runtime-evidenced progress remains no more than 8%. Static cold-boot
> callback recovery now proves that GBA/WSC 1.0 use a 15-linear + 3-choice
> opening graph and WSC 1.5 expands it to 19 + 5. The six additions are bounded
> and the modulo-5 state cycle with selector pairs `[13,14]` and `[12,11]` is
> mapped. Both added choices and all four added linear callbacks are now
> integrated statically. Static dependency recovery additionally
> proves that the complex first/fourth additions require replacement resource
> records 50/49. Their directly consumed P0 animation/tile containers and P2
> palettes convert byte-for-byte to assets already resident in the commercial
> USA GBA ROM, so no duplicate graphics payload is required; their construction,
> update, event, and skip-list wiring now uses bounded native GBA adapters. The
> selector view is rebuilt: P1/P2 and selector
> 11/13 P0 resources reuse byte-identical commercial GBA assets, while only
> selector 12/14 P0 containers are newly converted. No emulator or supplied
> save was used for v40. The installed child family is internally connected to
> its resources, but no external parent/controller reaches generator `9229`.
> The parent `9083`/`912A` code has not yet been translated or connected, so it
> does not request the new `0x5B` sound yet. Audible/timbre parity and playback
> remain unverified until final non-displaying runtime QA.

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
- Source-bound Digimon Shoot child P1/P0/P2 resources installed under an
  Expected Writes contract, with the resident
  `9229 -> 94C1 -> 9570 -> 9617` generator/callback family connected internally.
  Its source `A7` payload is byte-identical to WSC 1.0 sound `A5` and maps
  through the exact native GBA queue writer as ID `0x4A`. The unique `CE`
  command is statically reconstructed as native GBA sound ID `0x5B`, with the
  commercial 91-entry song table preserved and extended to 92 entries;
  external parent/controller entry and its `0x5B` request remain pending.
- Opening modulo-5 choice dispatcher and the added `[13,14]` and `[12,11]`
  presentation cases/callbacks.
- Four added linear opening callbacks, selector-3→13 predecessor change,
  converted timing/event plan, and sequential slot-3 auxiliary-object reuse.

The current static internal composite is v40, identified only by SHA-256
`9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B`.
That file is intentionally excluded from Git. Exact v32, SHA-256
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`,
remains the last runtime-evidenced candidate. It reaches title, responds to
Start with a main-menu frame byte-identical
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
binary assets from the three original ROMs before assembling nine guarded
layers. Two builds in separate empty output directories both produced v40
SHA-256
`9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B`;
all 73 files in each output tree matched by relative path and SHA-256.
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
| Progression, tag/rating, opening | 25% | Remaining producers, persistence/UI, and GBA translation of the confirmed five-state opening graph |
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
The rules code beginning at `4090:9908` is now bounded separately as 6,096
reachable bytes, 43 callback entries, and three fully resolved indirect
tables. Commercial WSC 1.0/GBA comparison binds its `94C1`/`9570`/`9617`
chain to GBA `0x08372110`/`0x083721FC`/`0x08372320` and proves five native
runtime-call mappings. The `9229` child generator is additionally bound to
commercial GBA `0x0837273C`; its P1/P0/P2 sources are resolved and converted
by rules checked against the complete commercial ancestor resources. v36
installs those three generated resources at `0x5B9000`, `0x5B9200`, and
`0x5B9300`. An independent verifier confines the diff to those ranges and
proves that the only pointers into the new window are the containers' own
internal pointers. v37 adds an independently verified ARM7TDMI translation of
generator `9229` and the `94C1 -> 9570 -> 9617` child callback chain. Its
internal literals reach the three v36 resources and its completion callback
clears Shoot flag `0x40`. v38 added a provisional request translation based on
equal numeric WSC IDs. v39 supersedes it after comparing the actual six-byte
sound-table entries and command payloads: WSC 1.5 `A7` is byte-identical to
WSC 1.0 `A5`, not WSC 1.0 `A7`, so generator `9229` now calls native writer
`0x080D15C0` with GBA ID `0x4A`. Parent state `9083` also requests WSC 1.5
sound `CE`; its 30-byte command payload has no exact match in the 185
independently bounded WSC 1.0 payloads and therefore requires a new GBA-native
sound asset. v40 relocates the commercial 91-entry GBA song table without
changing IDs `00..5A`, appends ID `0x5B`, and installs a one-track M4A
reconstruction of `CE`. An independent verifier confines the layer to 790
changed bytes, proves all five table references, checks the exact WSC pitch and
60-tick schedule against the GBA track, and reports SHA-256
`98EB32D4CA01A8AF1F824D1FAB6E88E2F735CB620DE012D819182498D72EC748`.
This is a bounded semantic reconstruction; audible/timbre parity is not yet
claimed. No external callback points to the generator yet; the `9083`/
`912A` parent connection remains unimplemented, so runtime reachability and
audible playback are not claimed. Rules, reward, win/loss, and exit remain
release gates, and the runtime-evidenced percentage is unchanged.

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

The opening/presentation route is now bounded statically from each registered
cold-boot root. The commercial GBA and WSC 1.0 graphs have 15 linear callbacks
plus three choices; WSC 1.5 has 19 plus five. Instruction-shape alignment and
object-selector extraction identify four added linear callbacks and two added
choices. The new conditions are a modulo-5 cycle whose states 3 and 4 select
`[13,14]` and `[12,11]`. Internal v35, retained as v40's opening-linear
intermediate, translates those two cases/callbacks and the dispatcher
extension into GBA ARM code while preserving retail states
0..2. Its dedicated 15-record presentation view preserves commercial
selectors 0..10 and supplies selectors 11..14. Static conversion proves that
their P1/P2 resources and selector 11/13 P0 resources reuse byte-identical
commercial assets; only selector 12/14 P0 containers are newly emitted.
Static conversion also proves that replacement records 49/50 map to complete
native GBA record views at `0x080D4498` and `0x080D44D8`: their P0/P1/P2
inputs are already resident, and the exact commercial consumer at
`0x08088250` supports the required 0x20-byte record and 0x50-byte object-slot
strides. This removes the need to translate the otherwise unmapped WSC primary
loader. Their source state machines are also fixed now: callbacks 7/8/9 map to
commercial GBA template lineages, while callback 10 is a bespoke event-table
and auxiliary-object translation. Exact commercial WSC 1.0/GBA instruction
pairs now also bound a static per-constant timing/motion plan for all four
additions. That plan remains an implementation inference until the deferred
non-displaying runtime QA. The four ARM callbacks, auxiliary-object
construction/updates/skip lists, and aligned selector-3→13 change are now
integrated in the guarded main build. Static lifetime analysis bounds sequential
reuse of unused GBA opening slot 3 for records 50 and 49 without overwriting
retained commercial auxiliary objects. An independent verifier confines all
2,199 changed bytes to the three hooks and declared expansion ranges,
disassembles the four callback call graphs, and checks the exact converted
seven-entry event table. No v40 runtime evidence exists, so the static integration
does not increase playable/release progress.

Detailed scope and evidence requirements live in
[`records/port-scope.md`](records/port-scope.md); the deferred save gate is in
[`records/final-qa.md`](records/final-qa.md).
