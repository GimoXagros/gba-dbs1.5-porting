# Next bounded language consumer — 2026-10-23

**Historical proposal, superseded.** The active implementation and approval
are `records/result-language.md` and `records/result-language-qa-20261105.md`.
Latest user policy keeps English WINS/DRAW and reuses exact Japanese WIN/DRAW
graphics for Japanese, Korean and Digicode. Korean/Digicode last chance now
uses approved26/27-part native art; their complete bounds are122 parts each.
The older translated/Latin-Digicode headings, draft counts, unallocated/closed
gates and no-built-ROM statements below describe the historical investigation,
not current work or permission. Full-main/runtime validation remains separate.
The original body is retained as evidence.

Read-only follow-up after Options and the five-event title component. The
inspected candidate is title143E
`143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80`.
No ROM, builder, localization file, emulator, or save was changed. Existing
`analyze_language_consumers.py` sites and source parsers guided the inspection;
this is one next-component proposal, not another whole-game inventory.

## Recommendation: existing match-result labels

Localize the existing four-event result-label family used by native mode8:
P0 `080B8210`, P1 `080B9004`, P2 `080B9144`. It contains the outcome heading,
digits, and last-chance message. This is a frequent, visible gameplay boundary
with a concrete Japanese source producer and a small text population. Preserve
the native digits, timing, fighter poses, names, and result behavior.

Mode8's table row at `08015BD0` binds initializer `080893A4`, constructor
`080897AC`, and common `080159B0`. Mode7's native transition row is
`08 14 0F 06 00`, with the ordinary route entering mode8. This establishes a
native match-result route; no result capture was taken in this investigation.
The source constructor and visible labels, not the address's name, establish
the semantic role.

The selection candidate inspected first, P0 `0809BA8C`, is mainly the moving
Digivice decoration. Its event8 says `ONE MOMENT PLEASE...`; replacing that
alone would have less impact than the result family. Selection names and
background text remain separate consumers and are not claimed complete.

## Exact Japanese wording and source routes

WSC 1.0 language branch `3B6030` uses `IN AL,CD; AND AL,1`; its Japanese
constructor arguments bind P0 `2AF360`, P1 `2B3580`, P2 `2B5F90`.
Its English alternative binds `2AF5C0 / 2B3660 / 2B6080`.
WSC 1.5 counterpart `777465` executes `XOR AX,AX` twice, compares zero,
and binds the Japanese resources below through the actual constructor call at
`777496`. The alternative English call is `7774C9`.

| Language/version | P0 raw | P1 raw | P2 raw |
| --- | --- | --- | --- |
| WSC 1.5 Japanese, actual zero branch | `3CB870` | `3D29E0` | `3D7EB0` |
| WSC 1.5 English alternative | `3CBB20` | `3D2AE0` | `3D7FA0` |
| Native GBA English | `0B8210` | `0B9004` | `0B9144` |

The Japanese source atlas descriptor `3D8E80` binds `3A0000`, length `CC0`
(102 native-sized tiles after planar conversion). Its first-frame resources
were decoded and visually inspected in memory; no image or source-ROM copy was
written. Exact visible wording:

| Event | Native English | Actual Japanese-source text | Native P1 layouts / parts |
| --- | --- | --- | --- |
| 0 | WINS | **WIN**, already Latin | layout0,35 parts; source Japanese38 |
| 1 | DRAW | **DRAW**, already Latin | layout1,20 parts |
| 2 | twelve digit/symbol frames | same numeric role | layouts2–13, maximum5 parts |
| 3 | LAST CHANCE! | **ラストチャンス！** | layout14,28 parts |
| source-only4 | absent | **LOSE**, already Latin | source layout15,17 parts |

Proposed scope is native events0–3 only. Source-only LOSE requires a distinct
behavior/consumer decision and must not be added merely because its pixels
exist. English keeps its original WINS. Japanese preserves the source's WIN.
Digicode can use Latin glyphs for WIN/DRAW because the selected Japanese
original actually contains those Latin words; it must use Japanese reading
for ラストチャンス. The smallャ requires an explicit, evidence-backed local
alias policy before encoding. The frozen title-onlyョ alias is not a blanket
permission to normalize other characters. Keep the source exclamation and
numeric symbols intact. Korean wording would be a separate draft/review step.

The source Japanese palette converts byte-for-byte to native P2, and the source
Japanese/English palette blocks are equal. Source events0/1/3 expand exactly
to native P1 commands. Event2 has the same twelve layouts but native command
flags at `+6` differ for digit frames1–10 (native1, source0); retain the native
P1 rather than overwriting those control fields. A localized P0 can preserve
all existing event/command meanings while replacing only layouts0/1/14.

## Actual constructors and shared resource aliases

Native constants at `080895A4`, `0808991C`, `08089A88`, and `08089B98`
force English decisions. Both sides of the result-label branches nevertheless
bind the same native English resources. Flipping a condition alone cannot
recover Japanese text.

The seven encoded references to P0 `080B8210` are all aligned literal words;
their actual consumers are:

| P0 load | Literal | Native init call | Role |
| --- | --- | --- | --- |
| `08089948` | `0808A388` | `08089988` | Heading, dormant Japanese branch |
| `080899AC` | `0808A394` | `080899EC` | Heading, current English branch |
| `08089BBC` | `0808A3C8` | `08089BFC` | Last-chance object, dormant Japanese branch |
| `08089C20` | `0808A3D4` | `08089C60` | Last-chance object, current English branch |
| `08089D5C` | `0808A3E8` | `08089D9C` | Three first-player digit presentations |
| `08089EF4` | `0808A400` | `08089F34` | Three second-player digit presentations |
| `080BB0B4` | `080BBA64` | `080BB0F4` | Separate mode12 presentation; preserve in this component |

P1 has the corresponding seven literals, and P2 also has palette-preload
references. This is why a shared-resource data replacement would have a wider
effect than the proposed mode8 constructor routes.

## Active population and OAM gate

The heading at priority1500 task payload `+0C` chooses event0 or1 according to
the result flag40. Its optional second presentation at payload `+5C` is either
the winning character's separate name family or event3 last-chance text.
Two priority1600/1700 digit tasks each own three presentations at payload
`+0C,+5C,+AC`, selecting event2 frames. Their explicit draw calls include
`0808AC6C/0808AC8C/0808ACAC`; later callbacks retain the three-object population.
Thus this shared label resource has seven simultaneous objects normally and
eight in the last-chance branch, with six original digit frames retained.
The text/name task draws at `0808B0AC/0808B170/0808B19C` according to flags.

Two additional priority2000/3000 tasks own full fighter poses initialized
through `0801F3A8`; they draw through the `0808A7C0` callback family. The mode
controller, result controller, and fade/service task also remain native.
Consequently, `heading + second label + six digits` is **not** the whole-screen
OAM total. The complete frame choices and overlap of both fighter poses must
be bounded before a builder is authorized. The source Japanese WIN alone adds
three parts relative to native WINS. No safe total, clipping exemption, or
runtime clamp is claimed by this read-only proposal.

## Concrete four-mode hookup proposal

Reuse the frozen shared language getter at `08633400` without editing it.
It reads `0300112F`, returns0–3 in `r0`, maps all other tags to0, and clobbers
condition flags. Its actual machine bytes must be pinned as a dependency.
The title helper at `0863FB00` is not a generic getter: it returns a title P0
and has a fixed branch-back continuation, so it is unsuitable for a new caller.

The smallest coherent route is a dedicated wrapper for the six mode8 native
`BL 080127E4` init calls listed above. Replacing an existing BL with a BL to
that wrapper preserves the original return-address contract. The wrapper
saves `r0/r1/r2/LR` and flags before calling the shared getter, selects one of
four P0 values, changes only the consumed P0 argument, restores all registers
and flags, and tail-branches to native `080127E4`. With those four saved words,
the P0 argument is at wrapper `SP+0x34` (entry `SP+0x24`): native `080127F4`
reads that argument at its own `SP+0x34` after its sixteen-byte push. P1/P2,
all other arguments, original digits, and the separate mode12 alias stay intact.

This is an unallocated proposal. Required implementation gates are exact source
pixel review, explicit small-kana/punctuation policy, four complete P0 resources,
all reachable fighter/label aggregate bounds, new allocation ownership,
placed-machine-code/ABI checks, independent artifact verification, and actual
normal-win/draw/last-chance runtime observations. No whole result-system port
or additional event behavior is implied.

The full mode8 prebuild audit subsequently exposed a result-pose routing
defect for IDs12–14, so label implementation remains closed while the pose
component is verified. See `records/result-pose-routing.md` for the actual
source/native tables, all15 character routes,120 events/1,252 frames, and
minimal112-byte data repair. The aggregate language budget is tracked
separately and must use the repaired poses rather than the wrong old routes.

## Completed read-only aggregate gate

`tools/analyze_result_language_budget.py` pins the corrected DBB candidate
`DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C`.
Its report is `build/result-language-budget-20261023/analysis.json`, SHA-256
`F603259217F75078E64018F13DC65A0BE34DB18A02E20C01C9473F60EE72BE45`.
The CLI is `CURRENT GBA WSC15 FONT LICENSE OUTPUT --self-test`; the exact
commercial ROM/font identities are pinned. The default catalog and reference
are `localization/digicode-reference.json` and
`local/digimoji-reference-20261021/reference.json`, also hashed in the report.
This is a read-only, in-memory packing proposal; no result-language ROM has
been built by this gate.

The constructor's seven allocations are derived from the actual calls and
callback literals: controller1000, fade/serviceF000, text1500, digits1600/1700,
and fighters2000/3000. With the existing priority0 mode controller, this is
eight tasks and ten presentation objects: heading, name-or-last-chance,
six digits, and two fighters. All19 direct native draw sites are pinned.
The callbacks allocate no additional tasks or presentations. Every piece is
counted even when offscreen, transparent or overlapping; the native renderer's
entry-only127 guard is not a clipping remedy or part of the proof.

The base-only fighter loader is unchanged: preceding evolution states do not
choose another result P0/P1 group. The analyzer reads all120 selected events
and1,252 native frames, all15 winner names, both corrected pose pairs, and
all12 digit/symbol frames. The source-only LOSE event remains excluded.

Before result poses start, both text objects are hidden by flags2/4. The
initial left/right pose families have maxima20/26, and six rolling digits
have a conservative30-piece total, giving76. Both fighters finish their16-step
slides before the digits finalize, including the accelerated draw path.
Both digit tasks have identical16/59/118 phase counters and run before both
fighters. Each finalizes all three decimal digits before setting flag1. Both
fighters therefore observe that flag on the same scheduler traversal, select
the held event56, and start the same48-countdown. Flag2, which permits the
text task to appear, is set only when those counters reach zero and the first
result poses are selected. Rolling digits never coexist with the heading.

The initializer reads byte scores, so the analysis includes the entire0–255
domain without assuming a smaller reachable gameplay score. Each frozen
three-digit number costs at most14 pieces; unequal scores244 and44 achieve
the conservative28 total. The two poses then advance exactly once at delta1
per traversal. First-pose completion replaces the event once; phase2 retains
its actual looping or holding behavior. All225 winner/loser ID pairs,
including same-character combinations, close in389,162 joint states. The
longest trajectory is18,852 states. The analysis includes indefinite periodic
tails beyond the normal222-countdown instead of cutting them off. Every first
pose completes in5–140 calls, independently agreeing with the pose verifier.

The largest correlated `winner-name + winner-pose + loser-pose` total is64:
ID1 name22, its phase2 frame8 with23 pieces, and ID6's first loss frame5 with19
pieces, on the42nd simulated call. Adding original English WINS35 and frozen
digits28 gives127. Independent maxima would give128 because they combine
pose frames that do not occur on the same traversal. The reported127 is a
safe upper bound, not a claim that every witness score/battle combination is
known to occur in ordinary play.

Ordinary draw sets4000 and uses only pose events0/1, at most20 pieces each.
Even conservatively counting DRAW and last-chance text together gives116
with original assets; the native intervals actually choose one or the other.
Repeated/linked draw sets1000 and suppresses last-chance. Bounding both poses
with the largest26-piece selected frame gives100. The early4000/8000
constructor-return branch creates no result presentations.

The mode controller and fade/service callbacks add no OAM. The traced services
write scroll state, palettes, blend registers, LCD scanline state or BG tilemap
text. In particular, the later SCORE writer `0801E8C4` is a BG writer and does
not add another sprite text object. At battle exit, `080D1B0C` deletes all26
renderer tasks from the same `030047A8` array created by `0835227C`, the two
engine-service handles, and `03004518`; the battle controller also retires
before mode dispatch. Native priority0 transition and frame-queue reset
separate the old and new populations. Result exit waits for all six completion
bits3F00, which are set by the retiring text, digit, fighter and fade tasks,
before requesting the next mode. Fade and exit retain or remove the same
presentations; they do not enlarge the population.

### Complete-pixel packing and wording

The direct source Japanese WIN would require130 pieces in the conservative
correlated aggregate and cannot be installed unchanged. An exact grid repack
at origin(0,5) turns its38 source parts into30. All1,508 nonzero palette/index
pixels remain at their original coordinates, including every edge pixel;
the complete pack/decode roundtrip is equal. Its bounds stay
`[-39,-11,39,12]`, and its pixel digest is
`8ECA7847B508136FCB6CF9A6B3613778E95CD6932995D6810117D4A6CB622499`.
DRAW and last-chance can retain their complete20/28-part source layouts.

Korean geometry drafts are `승리`, `무승부`, and `마지막 기회!`.
Digicode uses the actual Japanese-source Latin WIN/DRAW and the Japanese
reading `ラストチャンス`. The bounded local adapter changes only this
reading's smallャ toヤ (`jp-3084`): the local creator reference explicitly
maps both `ゃャ` and `やヤ` to `/jp/ya.svg`, agreeing with the user-provided
`でじもんあどべんちゃー` example. The frozen strict encoder still rejects
smallャ; no general normalization or fallback is introduced. All98 reviewed
glyph row bytes retain digest
`E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195`.

The exact native exclamation is isolated after source blank column41:
bounds `[42,-8,50,6]`,65 pixels, digest
`26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8`.
Its original colors and complete outline are attached to both new last-chance
phrases. It is not replaced by a font approximation or Japanese long-vowel
symbol. Every Korean/Digicode authored mask also passes complete native
8×8 tile packing/decode equality. The current color mapping is a geometry
draft; final resource/palette preview review remains an implementation gate.

| Language | Heading / draw / last-chance parts | Normal-win bound | Draw bound | Complete maximum |
| --- | --- | ---: | ---: | ---: |
| English, original | 35 /20 /28 | 127 | 116 | **127** |
| Japanese, exact-pixel WIN repack | 30 /20 /28 | 122 | 116 | **122** |
| Korean draft plus native ! | 6 /8 /14 | 98 | 90 | **98** |
| Digicode draft plus native ! | 8 /10 /16 | 100 | 94 | **100** |

The Japanese/Korean/Digicode independent-frame overestimates are123/99/101,
also safe; only unchanged English needs the timing correlation. Maximum tile
staging is4064 bytes. All19 negative checks reject wrong pose routing,
malformed frames/durations, missing task cleanup, broken synchronization,
early transition, lost pixels, unsupported glyph fallback and the unrepacked
Japanese overflow.

This closes the read-only capacity proposal. A future language layer still
requires its own allocation/ABI contract, actual four-resource artifact,
independent pixel/route verification, and normal-win/draw/last-chance runtime
observations. The parent's DBB ID14 consumer breakpoint passed; its separate
normal screenshot attempt encountered a battle callback failure, so it is
not a result-screen runtime pass. The subsequent Waterfall/stage predecessor
must prove these budget dependencies unchanged before building language assets.

## Title capture checker review

Read-only review of root's `tools/verify_title_capture.py` found that object
`+18` is the selected P0 layout index and must equal its event, rather than
merely being below5. A settled menu also requires the exact four-object count,
including Y200, rather than only an upper bound that could hide a missing item.
The exact command pointers, flags0408, signed coordinates, and three task roles
were supplied to root. Root tightened the checker and subsequent exact143E
Digicode/Korean settled menus passed111/88 OAM. No checker file was edited here.
