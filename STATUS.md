# Port status

## 2026-11-25 v1.0.0 배포 기준

미국판과 최종 포팅판 `AA6BB1EB`을 두 코어에서 실제로 연결했다. 양쪽 배치·승패·재대전·저장 재시작을 확인했다. 무보조 전체 캠페인과 실기·공개 테스트는 배포 후 검수한다. 아래의 이전 버전 기록은 당시 상태다. [정식판 검수·지원 범위](records/v1-release.md).

Snapshot date: 2026-09-02 (Asia/Seoul)

User-requested pause after the v50 palette-transition investigation:
[`RESUME.md`](RESUME.md) records the saved checkpoint, unresolved work and
restart procedure. This handoff changes documentation only; no v51, runtime
validation, supplied-save use or GitHub upload is claimed.

> **Recovery correction:** [`PORT_AUDIT.md`](PORT_AUDIT.md) is the
> authoritative current status. The earlier 55-60% / 57% planning estimate is
> withdrawn because it mixed static integration with unverified runtime
> behavior. A roster-record relocation defect in v31 was isolated and fixed.
> Exact v32 now passes `BOOT -> TITLE -> MAIN MENU -> CHARACTER SELECT` in
> non-displaying mGBA runs and reaches the first retail battle; overall
> runtime-evidenced progress is no more than 8%. The single next runtime
> milestone was completed by observing the retail Right-input consumer. The
> clean current-candidate milestone is now complete: the hash-identified USA
> GBA, WSC 1.0, and WSC 1.5 originals reproduce internal v50 byte-for-byte in
> two independent builds. Its modulo-5 dispatcher, added choice states 3
> and 4, selector resource records 11..14, four added linear callbacks, and
> sequential slot-3 reuse for auxiliary records 50/49 are statically integrated.
> The Shoot child P1/P0/P2 resources and resident
> `9229 -> 94C1 -> 9570 -> 9617` generator/callback family are also integrated,
> including the payload-proved WSC 1.5 `A7` -> WSC 1.0 `A5` -> GBA `0x4A`
> sound request. The Ver. 1.5-only parent-start `CE` payload is now represented
> by a bounded native GBA ID `0x5B` M4A reconstruction that preserves its
> packed pitch, 20-tick lead, and four 10-tick volume-decay steps.
> Its source volume nibbles are now decoded correctly: `0x0F`, `9`, `6`, `3`,
> and `1` are right-only values, so a one-byte v44 correction changes the
> native M4A pan from center to right. The distinct Ver. 1.5-only upper-state
> sound `D2` is also installed as native GBA ID `0x5C`, preserving its nine
> packed pitches, 80-tick schedule, right-only direction, commercial
> `A2=01`→voice-`0x1F` timbre lineage, and a bounded M4A pitch controller.
> The `9083 -> 90F3 -> 912A -> 91AB -> 91EF` parent callback chain now
> reaches that sound and the resident child generator internally. A proved
> commercial lineage now maps Ver. 1.5 auxiliary object `ES:071E` through WSC
> 1.0 `ES:06A2` to native GBA slot `0x03004D3C`, allocation ID `0x343`, and
> pool 5. Internal v45 installs a resident constructor and translated idle
> callback using that slot and the verified rule resources. Internal v46 adds
> the full resident 26-callback/2,320-source-byte upper-state population, its
> fourth P2 record, intro palette table, eight movement targets, native RNG
> calls, and the three native `0x5C` requests. The graph remains deliberately
> unreachable until the `7168` initializer/menu route and controller rules are
> installed. v47 corrects inverted P1/P2 arguments in the child and auxiliary
> constructors and inverted active/other auxiliary links, then installs the
> resident `71D1..7394` player/auxiliary binding phase. It reuses the existing
> auxiliary object without allocating a duplicate and assigns `7792`
> internally, but its own entry remains uncalled. v48 repairs a separate,
> source-proved defect: the legacy P0 parser rejected non-`0x2000` source
> segments and silently omitted tiles from five Shoot resources. All 46 far
> descriptors and 393 tiles are now installed through five P0 pointer repairs,
> preserving code and layouts. The composite is reproducible at SHA-256
> `11940B101AD0FA2DDA0886A5A04D3A750FE2D87411ADCA512F4ADEE78888284E`
> for historical v48. v49 corrects three additional-character physics pointers
> that were one record early and installs resident source `73F0..74A2`
> other-player restoration. Its final hash is
> `93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E`.
> The phase has no caller; full initialization and palette-transition ownership
> remain open. v50 adds resident `7394..73A9` and `74A2..74DA` resource
> segments for OBJ slots 5/6, exact commercial HUD tiles and scroll reset.
> They have no caller and do not complete the tail or its palette transition.
> Current v50 SHA-256 is
> `C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
> Fourteen v49 negative checks and complete added physics records
> are verified against the actual native consumers, not manifest targets alone.
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
> save was used for v50. The parent and child families are internally connected,
> but external controller `9908/9A1B` does not yet assign parent `9083`, so the
> chain remains unreachable from retail play. Audible/timbre parity and playback
> remain unverified until final non-displaying runtime QA. A new deterministic
> initializer-resource report resolves all nine direct P0/P1/P2 references used
> by `4090:7168`: five P0 containers and four P2 blocks are structurally bounded,
> one P2 block reuses the installed Shoot palette source, and another is already
> byte-identical to commercial GBA data at `0x080D3078`. The two P1 containers
> are a distinct self-delimiting format. A separate
> twelve-pair commercial oracle proves all 283 P1 payload conversions and six
> non-null B records, plus all 92 eight-byte A-record command references; both
> initializer sources satisfy those rules. Their 2,636-byte native P1 blob,
> five P0 containers, and two non-reused P2 blocks are now installed as a
> resource-only v42 layer. Its former zero-descriptor P0 verification was
> insufficient; v48 supersedes it with source-loader, retail-oracle and
> complete pixel/animation-pair checks. The separate v45
> auxiliary-object layer binds `ES:071E` to the exact commercial GBA
> allocation/lifetime lineage, but no menu or upper-state caller reaches its
> resident constructor. v43 resolves the separate `D2` asset dependency; v44
> corrects CE stereo direction; v45 installs the independently verified resident
> auxiliary component; v46 installs and internally connects the upper-state
> graph and its three `0x5C` calls. The v47 corrections and phase are now checked
> against actual native constructor consumers, with six negative regression
> checks that reject individually reverted fixes. Normal-play entry is still absent;
> runtime-evidenced progress remains unchanged.

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
  commercial 91-entry song table preserved and extended first to 92 entries.
  Ver. 1.5-only `D2` is appended as ID `0x5C`; its nine-note/80-tick/right-only
  track uses commercial voice `0x1F`, proved by the WSC 1.0 `A2=01`→GBA
  sound-`0x56` oracle. CE's right-only source volume is corrected in v44. The
  resident `9083 -> 90F3 -> 912A -> 91AB -> 91EF` parent chain issues `0x5B`,
  later issues `0x4A`, and calls child generator `9229`; only its external
  `9908/9A1B` controller assignment remains pending.
- Resource-only v42 placement of all converted `7168` initializer P1/P0/P2
  assets in `0x5D0000..0x5DB768`, with exact diff containment and no external
  pointer into the new window yet.
- Resident v45 Shoot auxiliary-object constructor at `0x085BC200`, using the
  commercial ID-`0x343`/pool-5 allocator lineage, native slot `0x03004D3C`,
  player slots `0x0300489C/0x030048A0`, installed rule resources, and a native
  translation of idle callback `88F6`. It remains deliberately uncalled.
- Resident v46 Shoot upper-state graph in `0x085BC800..0x085C0D40`. It covers
  all 26 source callback entries (including v45's `88F6`), 2,320 source code
  bytes, 24 source callback edges, the fourth P2 record, seven-row intro
  palette, eight target rows, native presentation/trigonometry/RNG helpers,
  and the `0x4A`/`0x5B`/`0x5C` request population. The two calls corresponding
  to source helper `9908` stop at an unimplemented `BX LR` boundary; no pointer
  from normal play reaches the graph. v47 now assigns `7792` from its resident
  player-binding phase, which has no external caller.
- v47 consumer-driven corrections for the child/auxiliary P1/P2 argument
  order and auxiliary player identity, plus source `71D1..7394` player binding,
  fifteen-entry HP table, and allocation-free auxiliary reconfiguration.
- v48 repair of the child P0 and four initializer P0 descriptor pointers,
  restoring 46 descriptors and 12,576 bytes / 393 tiles. Source `DS:SI`/C2
  semantics, the full commercial 21-descriptor oracle, all pixel data and
  every P1/layout pair are checked independently; ten damaged variants fail.
- v49 correction of all three shifted added-character physics pointers and a
  resident other-player restoration phase at `0x085C1500`. Native presentation,
  two existing OBJ palette-mirror rows, 32-bit physics pointers, bounds and
  paired positions are consumer-checked. This phase remains uncalled.
- v50 resident tail resource segments at `0x085C1700/1800`: OBJ palettes
  5/6, exact native HUD tile-`3FC` reload, and scroll reset. Ten negative
  cases and actual retail producer/OAM/palette consumers are checked. These
  entries remain uncalled; no complete initializer or runtime claim is made.
- Opening modulo-5 choice dispatcher and the added `[13,14]` and `[12,11]`
  presentation cases/callbacks.
- Four added linear opening callbacks, selector-3→13 predecessor change,
  converted timing/event plan, and sequential slot-3 auxiliary-object reuse.

The current static internal composite is v50, identified only by SHA-256
`C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
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
binary assets from the three original ROMs before assembling nineteen guarded
layers. Two builds in separate empty output directories both produced v50
SHA-256
`C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`;
all 121 files in each output tree matched by relative path and SHA-256. The
build-manifest SHA-256 is
`5CDD5FB7595039958DB3B5D37D22168C3216A9CD69791234219E5E33C7F90EA5`.
The explicit legacy physics option is used only to reproduce the pinned
historical layers; the v49 layer repairs the pointers and the final image must match the
separately generated corrected physics blob byte-for-byte.
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
`912A` parent chain is implemented in v41 and internally reaches generator
`9229`, with source `+0x1C` linked-object access mapped to GBA `+0x28` by the
commercial WSC 1.0/GBA generator pair. Six final-placement ARM7TDMI functions,
695 changed bytes, all internal callback edges, native call targets, timers,
events, fields, and both sound arguments are independently checked; report
SHA-256 is
`3989E33CD893742F9DD116D7050D9F33071763A04D9A174321EEC0A723755D13`.
The corrected upper-state analysis proves that `9908` is not an external
entry. The menu transition calls the Ver. 1.5-only initializer `4090:7168` at
raw `0x773143`; that initializer assigns active callbacks `7792` and `88F6`.
The later stage-11 battle-transition branch assigns `7AB1`/`7D8D`. Walking
both populations reaches 26 callbacks, 2,320 code bytes and 24 callback edges
without an unresolved indirect transfer. Only callbacks `7EBB` and `809C`
call helper `9908`, at `8057` and `80AF`. The deterministic report SHA-256 is
`55B6AD9E1FA162C67AE6B14A125F6D02E257506F80FB16786D54B678B49C75A0`.
It also binds WSC import `4FFF:1CB5` to the platform-native GBA random routine
`0x08012600` by its argument/return use and a guarded commercial call-site
oracle; identical PRNG sequences are not claimed. Therefore a standalone
`9908/9A1B` hook would remain unreachable and is not an acceptable port.
v46 translates that bounded population into resident ARM7TDMI code without
making it externally reachable. The layer writes 4,144 changed bytes across
29 declared placements in `0x5BC800..0x5C0D40`; it also independently converts
the fourth P2 record, all seven 16-color intro palette rows, and the eight
movement-target rows. Final-placement disassembly verifies every native helper
and internal callback edge, including three native `0x5C` requests and exactly
two calls to a resident `BX LR` boundary for the still-unimplemented `9908`
rules helper. No aligned pointer outside the ownership window reaches the new
graph. Independent verification report SHA-256 is
`504A375A5A4F98A6F92975D06044FC46791481915E3A7FF528FA21ECF38353EE`.
This is static resident-code evidence only; the initializer/menu route,
controller rules, runtime, audible behavior, and save QA remain excluded.
`tools/analyze_shoot_initializer_resources.py` now resolves the complete
initializer resource call population and reproduces report SHA-256
`4367C6588F904C282DD857E37CC6F67AC9B8E5DAB8FA8D222239655D7522C1C5`.
It proves deterministic conversion boundaries for five P0 and four P2
resources and correctly pairs P1 word-1 indices with 4/50 P0 layouts rather
than adjacent A data. The expanded audio-lineage report additionally
proves that three upper-state requests for WSC sound `D2` use a 32-byte
Ver. 1.5-only payload with no WSC 1.0 match; its new report SHA-256 is
`0CD28C17EB6DC3F1FE88F0FB755910434EC0B05DD06AD2F164A078BBEE60997E`.
The separate v43 layer reconstructs that payload as native ID `0x5C`; v46 now
contains all three request sites inside the resident upper-state graph. The
`7168` initializer/menu route and `9908/9A1B` rules must still be integrated
before the graph becomes reachable. Runtime reachability and audible playback
are not claimed. Rules, reward, win/loss, and exit remain release gates, and
the runtime-evidenced percentage is unchanged.

The direct-P1 commercial oracle now covers twelve WSC 1.0→USA GBA pairs,
92 commands, and 283 payload items. It proves every Shoot-lineage payload
expansion and six non-null 10-byte B records exactly. Both Ver. 1.5 initializer
P1 payload populations have zero word-5 tail values and fall within the proved
zero-tail rule. All 92 commercial A references across 14 unique mappings prove
eight-byte A-record identity; adjacent bytes are not part of those records.
The deterministic report SHA-256 is
`21B9DF5B7248E069FF4AC750C34305D42B6974FE5141C667B31A231B2E19D82B`.
Both initializer P1 containers are now emitted in a 2,636-byte relocatable blob
with SHA-256
`778C91C2B64072BE07AF9B66B9EE194AE09DE7EEBD73C67FABDFA4B5D443EAC2`.
Independent final-placement verification report SHA-256 is
`A435A75BA9D68D4D937125F3B0523BE54980A21D58EBE86E137A665B1DA3CBAD`.
v42 installs the P1 blob, five P0 containers, and two new P2 blocks in the
pointer-unclaimed `0x5D0000..0x5DB768` window. Exact diff containment covers
44,696 changed bytes, 198 post-write internal pointers, and zero external
pointers into the new window. Independent integration verification report
SHA-256 is
`7114A9C7B8CA51F8C52254EB03C3771F90B0CBB63B2D19D3D9B50ABA34A3576B`.
No runtime evidence or supplied-save state is involved.

`tools/analyze_shoot_d2_sound.py` decodes the unique 32-byte `D2` payload
through guarded WSC 1.0/1.5 `A0`/`A1`/`A2`/`A3` interpreter signatures. It
proves setup `A1=09`, `A2=01`, `C1=00`, `A3=20`, right-only volume `0x0F`,
packed pitches `20,18,17,16,15,14,13,12,11`, and a 40+8×5=80-tick schedule.
Commercial WSC 1.0 sound `B5` uses the same `A2=01` wave and maps to USA GBA
sound `0x56`, whose native track selects voice `0x1F`; this is the bounded
timbre oracle. Analysis report SHA-256 is
`ECB4780B4EC38D44B6F5FC0B11D7E45A7BF0D30214474D5A45778F91CC231E0B`.

v43 appends `D2` as native sound ID `0x5C` without changing IDs `00..5B`.
Only the eight-byte table entry and 67-byte song are changed. Independent
verification checks exact diff containment, every pitch and duration, 80 total
ticks, right pan, voice `0x1F`, M4A pitch MOD, and the two new pointer sites;
report SHA-256 is
`A636C763D0AF93DA8E47D9BC67DDBD8F1895D1A4BF95C1AE0029CF2A3C79B473`.
The three upper-state requests are now connected inside resident v46, but the
upper graph itself has no external caller. Conditional WSC channel-3 sweep and
audible parity remain final non-displaying QA boundaries.

The command-interpreter correction also proves that CE `A1 72` is hardware
sweep control, not a note length. CE still ends after its source-proved
60-tick command schedule because M4A `FINE` terminates the longer note gate.
Its header and all `A0` values have zero left nibbles, so v44 changes only the
CE M4A pan argument from 64 to 127. The one-byte independent verifier also
proves D2 preservation; report SHA-256 is
`A087DCD31E27A17615AEB897BD037F090F69C699D1EB2C6384674D4B2F0A0ABA`.
No emulator, supplied save, or audible claim is involved.

`tools/analyze_shoot_aux_object_lifetime.py` exhaustively proves the missing
object lineage instead of assigning new RAM speculatively. Ver. 1.5
`ES:071E` and WSC 1.0 `ES:06A2` are both allocation ID `0x343`, pool 5;
the commercial GBA counterpart uses native slot `0x03004D3C`, allocator
`0x08352374`, callback `0x083703EC`, and the same screen-effect consumers.
The field mapping and 75→60 Hz timer conversions also agree exactly. Two
analysis runs reproduce report SHA-256
`8F7E38A3C835503B5F1598CD9CD2468A7E229A1B483307F8A918D5ED10097F50`.

v45 adds a 436-byte resident ARM constructor at `0x085BC200` and a four-byte
native `BX LR` translation of source idle callback `88F6` at `0x085BC600`.
It allocates through the commercial ABI, populates native object fields, binds
the existing player slots and installed rules resources, and writes back the
active-player link. Exact diff containment covers 434 changed bytes. The
independent verifier checks final-placement calls, literals, fields, resource
preservation, commercial signatures, and that the constructor has no caller;
report SHA-256 is
`BC3B8E04C681C6DB7EF3A3A9A1BDF02B320E7478590877E0C5513C3327610228`.
No emulator, supplied save, or runtime claim is involved.

v46 adds the resident upper-state population after v45. It preserves the
historical auxiliary constructor and all earlier resource/sound layers, hashes
the three exact WSC code ranges plus idle byte totaling 2,320 reachable bytes, and installs
25 new ARM callbacks plus the already translated `88F6` member from v45.
Its two `9908` call sites terminate at a deliberately unreachable boundary
stub so that a later layer must replace the controller and connect `7168`
atomically. Two clean builds produced 107 identical files and exact candidate
SHA-256 `034785435B598C93B7FF79924EB8F4B3D9698B6AE1489B2B8186BB548692EEAC`.
No monitor-visible window, emulator, or supplied save was used.

v47 supersedes the earlier assertion that v45's constructor argument/link
semantics were verified. Native consumer inspection found P1/P2 reversed in
two constructors and active/other links reversed in the auxiliary component.
Six guarded dependent word writes correct those defects. The resident phase
at `0x085C1000` implements source `71D1..7394`, uses source HP values, connects
`7792` internally, and reaches the existing auxiliary body through a matched
stack-frame entry at `0x085C1300` without calling the allocator. Its valid-object
precondition must be established by the still-missing outer initializer.
The verifier reproduces all three old defects and rejects all six individually
reverted fixes without relying on whole-file hash rejection. It confines 459
changed bytes to nine writes; the builder checks all 98 new ARM instructions
with separate literal regions. Report SHA-256 is
`8427FBAD3FDD00EB15CCDF69D55BD39E0341E21629B86CD2B143AFFCC07F9930`.
Runtime progress remains unchanged; `PORT_AUDIT.md` is authoritative.

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
`[13,14]` and `[12,11]`. Internal v35, retained as v46's opening-linear
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
seven-entry event table. No v46 runtime evidence exists, so the static integration
does not increase playable/release progress.

Detailed scope and evidence requirements live in
[`records/port-scope.md`](records/port-scope.md); the deferred save gate is in
[`records/final-qa.md`](records/final-qa.md).
