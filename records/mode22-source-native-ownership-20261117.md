# Mode22 Tamer Tag source/native implementation map — 2026-11-17

This read-only map establishes the separate mode22 source scene and its storage dependencies. It does not install a native scene. Disabling the unfinished title row is an interim guard, not feature completion.

Frozen analyzer `tools/analyze_mode22_source_native_ownership.py` SHA `F96CDAA8BD7D7EE6C4E2C96A53548A78AC9487F2C0F6D58B6CD4754864F0FF69`; report `build/mode22-native-map-20261117/report.json` SHA `23B275984E1F1EDEC907068D5C87116E42B1824B2EAD57BB150098C4848609C5`. Inputs are source WSC1.5 `C415F227...` and isolated r3 native `B1EA99E4...`. No game, supplied save, ROM or main builder was changed.

## Entry and native dispatcher contract

Source callback row74FBD4 is init848F:0000 (`7848F0`), constructor848F:0401 (`784CF1`), common4FA3:0287 (RETF). Source title mode3 choice1 selects22; mode22 choice0 selects20. Tamer Tag is always available in the source Collection subtree. Its availability does not depend on mode23's saved unlock bit.

The mode22 initializer is substantive. It copies graphics/maps/palettes, clears local state, reads saved tag data and chooses one of three display branches. It deliberately leaves CX=1 at784C1B. The native translation must return scheduler R2=1; an all-register-preserving wrapper would lose this source ABI. Current r3's relocated callback row22 is still zero and has no implementation.

The bounded viewer graph has708 decoded instructions rooted0000,0401,04BF,05B9,0647,0677, including called07FA. Data tables are excluded. The separate award/linked-result graph has194 instructions rooted0728,081E,08C0. Direct targets remain within the bounded848F:0000..092C segment; external far imports are reported explicitly. This is a local control-flow map, not an assertion that no arbitrary computed external alias can exist.

## Two scene tasks and shared services

| Source owner | Behavior | Native implementation requirement |
|---|---|---|
| 0401 constructor | Creates source common OAM reset service, render task0677 priorityF100, and controller04BF or05B9 priority1000 | Allocate two owned scene tasks; use the existing native shared OAM flush/reset instead of a duplicate reset task |
| 04BF | A/B accepted-input exit; otherwise draws two OAM characters for each nonzero ordinary tag count | Native repeat-qualified input130A&C0; convert source digits to actual native sprite layouts/atlas uploads |
| 05B9 | Same exit; otherwise draws four-byte saved name through86EF:01F1 | Preserve source text/name semantics; explicit native font/OBJ contract |
| 0677 | Audio service, opposite-direction byte scroll counters, line IRQ setup, palette cycling every19 frames | Owned native raster queue/callback and converted colors; preserve frame ordering |
| 0647 IRQ | At source line8, switch compare to136 and horizontal scroll0; otherwise use bottom-scroll byte | GBA line timing/margins and IRQ lifetime require a typed adapter, not raw port substitution |

Source local0300:0000..0013 copies only the first ten counters. Word0016 holds branch flags1=no tags,2=ordinary,4=special. Bytes0018/0019 are opposing horizontal-scroll counters; word001A holds the render task handle. The native representation can be task-owned and widen handles, but the IRQ must have a proved way to access its owner/values. A global pointer or reused queue field must not be guessed. Root owns the native RAM footprint review.

The source exit calls4FFF:1D8C to retire its common OAM task, requests1,0,0, disables source line IRQ, zeros the two X-scroll ports and retires current/render tasks. The normal callback can finish its current draw after requesting cleanup; free-task lifetime must remain safe through return. Native exit must retire only owned tasks and the owned raster channel, retain common system tasks, and allow the shared next-frame OAM flush to hide unused slots. The existing mode23 VCOUNT ownership proof is a hardware-semantics reference, not permission to broaden its frozen sole-caller census.

Input is positively paired: source751933..751990 starts with edge3858, merges held3854 repeat-counter events and stores385C. Native080119D8..11A60 starts with1306, merges held1302 and stores130A. Both source mode22 controllers test385C&C0. Calling this a fresh-edge read would be inaccurate.

Reusable native services already have typed contracts: allocator08011AC4, release08011BE4, priority08011E54, shared OAM/upload08011708, word DMA08000B84, audio request080D15C0/service080D1500 and normal mode20 constructor08040470. Their availability does not prove a new caller's ABI. Source audio commandFC, priority4, is not in the frozen mode23 sound map and needs separate counterpart/conversion proof. Source font services86EF:0000/0130/01F1 also need explicit mapping.

## Display branches and source assets

Highest-tag helper07FA (`7850EA..78510D`) scans eleven words39FC..3A10 backwards. It returnsFFFF when all are zero,0..9 for ordinary tags and10 for the special tag. The initializer uses all three outcomes; empty storage is a valid source screen, not an error or permission to unlock everything.

The report records59 source asset references totaling27,688 referenced bytes, with source address, size, hash, WSC destination and type. References can overlap; that total is not a new ROM reservation size. Principal assets are:

| Dependency | Source raw span |
|---|---|
| Common scrolling BG98 tiles / palette |420000..420C40 /420C40..420C60|
| Common32×18 map |2DEED8..2DF358|
| Ordinary base tiles/palette/map |2DCDF8/600 bytes,2DD118/20,2DD138/60|
| Count digits11 tiles/palette |2DF358/160,2DF4B8/20|
| Ten tag palettes |2DC9E0/140|
| Special-tag tiles/palette/map |2DC1E0/A80,2DCB20/20,2DCD80/78|
| Special name palette/banner map |2DF4D8/20,2DF4F8/70|
| Special portrait |BA:25FA:0000 tiles700 bytes and+700 palette20|

Tables at source848F:0347 (ten destination/source tile pairs),036F (ten map rectangle descriptors),03BF/03D5/03EB (rank tiles/palettes/maps) govern the ordinary population. The report enumerates the ten reachable ordinary rank references. Common/empty and special edge strips are5AB8,5AF8,5B38 relative toAD:2936. Empty text is the literal source `YOU HAVE NO TAGS` at784C26.

Source tiles must be planar-converted, map attributes translated and direct WSC OAM draws given a native OBJ staging/presentation contract. Merely copying WSC destination addresses into GBA VRAM is not an implementation. No native allocation, output pixels or runtime graphics are claimed here.

## Counter producers, readers and reset

| Source owner | Exact responsibility |
|---|---|
| 785018..785091 (0728) | Mode11 award: difficulty config+0F selects one of four11-word threshold rows; config+26 is compared unsigned to the first inclusive threshold; resulting rank0..10 is awarded through08C0; config+23 gets result/8000; selector8 save follows |
| 77B106 | Sole encoded far call to0728, in the mode11 score scene; native hook placement remains to be paired |
| 7851B0..78521C (08C0) | Eleven16-bit counters; refuses an already nonzero final counter, increments selected rank, carries a tenth count upward while clearing carried lower rank; final special counter blocks subsequent awards |
| 78510E..7851AF (081E) | Linked-game result path: compares the paired player outcomes, handles tie/win/loss, validates selected rank, adds a won tag or decrements highest ordinary tag, then selector8 save |
| 741EAD | Sole encoded far call to081E; gated by link/config logic, not an ordinary single-player viewer action |
| 774BB5..774BC5 | Copies four text bytes into39F8..39FB, then selector8 save |
| 785E98..785EA7 | New-record path clears the whole E8-byte record, including tags/name |
| 7860CF..786146 | Normal selector transfer/save carries the full source record |
| 77857F..7785AD /77863C..77866D | Tag-dependent permanent unlocks: high ranks8..10 produce bit20; ranks4..10 produce bit10, avoiding already permanent bits |

The complete encoded far-call census for07FA has seven callers:741E40,77420A,78021B,780317,784991,784A4E,785178. Thus implementing only the Collection renderer would leave consumers in linking, UI and title/profile paths unhandled.

Threshold rows are:

- Difficulty0:249,299,349,449,549,599,649,699,799,998,FFFF.
- Difficulty1:199,249,299,399,499,549,599,649,749,998,FFFF.
- Difficulties2/3:149,199,249,299,399,449,499,549,649,998,FFFF.

The report checks all262,144 difficulty/value combinations remain in rank0..10 and records44 source-derived carry examples. These are source-derived models, not execution of a V30 emulator. Values remain16-bit; normal0..9 domain does not justify packing/clamping stored words.

## Shared persistent tail proposal

Source record fields8E..C9 are15 four-byte fighter statistic pairs. Native08033ED64 still computes8E+ID*4; ID12 beginsBE and its second word reaches the native C0 checksum. IDs13/14 continue intoC2..C9. Root is independently investigating native buffer relocation and consumers; this map does not choose RAM.

The remainder is CA..CB progress flags, CC..CF four-byte name, D0..E5 eleven tag counters and E6..E7 the title count read780326 and clamped to999. A shared source-tail view C0..E7 is40 bytes. A version/integrity envelope rounded to56 bytes would fit candidate EEPROM blocks27..33. This is an allocation proposal, not an installed layout.

The current r3 whole-image encoded ARM/Thumb API and veneer census matches the existing reviewed callers. Native capacity is64 eight-byte blocks; ordinary prefix/checksum transfers use0..24, Shoot uses25, and the planned persistent eligibility bridge reserves26. No proposal may overwrite25/26 or extend the old contiguous writer through them. The census covers actual encoded references, not arbitrary calculated targets or future components; final merged-image inventory must recheck it.

The shared-tail design must specify canonical RAM, version/checksum, load failure, legacy/fresh migration, factory reset, update ordering and partial-write behavior. In particular CA bit0 is logically the eligibility bit now represented by block26: define a migration/coherence policy instead of allowing two independent flags. A valid legacy prefix can retain its known fields while absent extended fields start at documented defaults; corrupted checksum/trailer bytes are not recoverable tag statistics. Native storage/root ownership work and source producer integration are prerequisites to calling mode22 complete.

## Implementation ownership handoff

1. Root: shared native record/tail RAM and persistence, preserving Shoot25 and eligibility26; paired mode11 award/reset/save hooks.
2. Scene implementation: mode22 init/constructor/two callbacks, source assets/font/FC audio, typed IRQ lifetime, return20, then remove only its temporary missing-implementation menu guard.
3. Independent QA: linked native constructor/scheduler ABI, three display branches,11-counter boundaries/carry, preserved unrelated EEPROM blocks, source-earned award-to-view evidence, normal A/B exit and physical OAM/palette/IRQ retirement. Multiplayer mutation requires its own actual supported-link contract; it must not be fabricated from an unrelated single-player event.

Reproduce with a fresh report:

```powershell
python tools/analyze_mode22_source_native_ownership.py --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --native build/mode23-scene-v88-r3-20261117/component.gba --report build/mode22-native-map-20261117/report.json
```
