# Train map and native graphics consumer repair

Date: 2026-10-16. This layer follows the separately verified collision and
logical-stage spawn repairs. It changes the Train graphics consumers without
writing the campaign progression byte. It does not complete campaign routing
or the remaining source-only Train hazard state machine.

## Observed defect and first incorrect input

The parent-owned natural-input capture
`build/runtime-spawn-repair-id13-20261016` selected character13, while native
`0300231E` still held progression1. The existing temporary selector at
`08582C40`, reached through `080D1C78`, maps character13 to logical arena8.
The capture showed a largely blue background and offscreen fighter objects.
This graphics repair does not claim that every observed actor symptom has the
same cause; collision and spawn were repaired in their preceding layers.

The old Train graphics extraction started at WSC raw `435000`. Source
resource33 starts at `4340E0`, exactly `F20` bytes earlier. That old extraction
therefore started inside map data. Source resource34 then begins at `4350A0`.
The source initializer instantiates two backgrounds, with dimensions2×2 and
48×2. The previous native initializer cloned four2×2 backgrounds. Its update
and scroll consumers also used `03002378`, which is inside BG0, instead of
the real next native background at `03002388`.

## Source addresses and native consumers

Source stage8 selects bankC3 and initializer `7CCF:0CEF`; its body is raw
`77D9DF..77DB11`. It sets DS3000, copies111 colors from raw430002 and512 tiles
from4300E0, then loads source resources33 and34 from the24-byte table at
`3B4DD0`. Their four-byte map descriptors are relative to `3B4970` and use
segment3000. The bank/segment/offset calculation gives36 unique maps, each
504 halfwords, at `4340E0 + n*3F0` for n0..35.

Resource33 uses the first four maps. Resource34 has96 descriptors: its first
16 maps repeat three times across the first48-wide row, and its remaining16
maps repeat three times across the second row. The replacement preserves this
descriptor order; it does not collapse the48-wide logical geometry to the
number of unique payloads.

The existing native BG loader at `08013BF8` consumes24-byte resource rows and
places dimensions at BG+C/E, the descriptor pointer at BG+24 and the collision
pointer at BG+28. The replacement updates only native resource21/22 headers.
It preserves resource21's independently verified collision pointer08622000
and resource22's null collision pointer. Existing resources23/24 remain
unchanged and are no longer instantiated by the Train initializer.

Source owners1000:01CE/020E correspond to native03002338/03002388, whose
structure stride is50 bytes. The native initializer calls the existing
`08013BE0`, `08013BF8` and `08013C64` in source order, using map basesF800/F000
and scroll shadows030012BA/BB and030012B8/B9 respectively. Initial fill uses
cleared map selectors; streaming consumers use the existing eight-byte
native map descriptors. No replacement renderer is introduced.

All512 retained native tiles at590100..594100 are checked against a complete
source planar-to-packed conversion. All111 retained colors at590000..5900DE
are checked against the commercial RGB444 conversion. The repair adds map
data; it does not replace already-correct tile or palette payloads.

## Scroll and initial camera coordinates

Source `77DAA5..77DAB5` calls4FFF:3274 on BG1 with X5240,Y0. It then calls
the same helper using the selected stage/variant/side origin pair.
The exact native helper is `08014574..080146B0`: it performs eight-pixel
steps through `08013DD4` and projects the scroll bytes through `08013DB4`.
Its stack arguments at entry are Y,X,unused segment slot,BG pointer. Both
source calls are represented using those existing consumers.

The Train origin row is raw77CE44..77CE64. The generic native initializer
also indexes a camera-origin table at0803F078, but that retail table has only
seven ordinary rows; stage7 uses a separate constant path. Added logical
stages were reading beyond the table into following literal data. The new
table contains all12 source rows at77CD44..77CEC4. Its first seven rows are
byte-identical to the retail table, and the existing stage7 special case is
preserved. Two address adapters replace the ADR instructions at0803EF38
and0803EF78; the existing arithmetic and consumers remain in place.

The side field is not guessed from adjacency: source7432ED onward stores
the constructor argument into source03CC, while native08352B30 onward stores
it through literal08352CC4=03004528. The generic camera consumer uses the
same address through literal0803F1A4. The variant mask remains3 and the side
domain remains the established constructor's0/1 input.

## Per-frame route and palette ownership

The existing update caller08015D94 reads progression+E into r1, even though
graphics initialization already uses logical-stage getter080D1C78. The new
update adapter uses that same getter and feeds the existing08582E40 dispatch
table. It preserves r0,r3,r8,lr around the getter. The current getter changes
only r0/r8 and retains its temporary policy: character11→arena10,
character13→arena8, character14→arena9, otherwise progression. Actual
progression11 retains dedicated Shoot precedence. The adapter never stores
to the progression byte.

The source Train scroll consumer76A9BC..76AA33 passes mode2 or8. The old
translated helper added80, enabling wrapping absent from this source call.
That extra bit is removed while its velocity arithmetic and existing native
camera helper remain unchanged. Both wrong BG1 literals are corrected to
03002388. This layer does not reinterpret elapsed time or create virtual
palette phases; one source cycle step occurs per native update callback.

The scanline callback's state is deliberately buffered. Source update76A8DA
writes1000:0330, while callback75F984 reads0300:00A6. Source768FD7..768FEB
copies81 halfwords from1000:02CE to0300:0044, mapping these addresses exactly.
Native08017768..08017798 copies400 bytes from03002478 to03004578, mapping
the update's03002568 to the callback's03004668. The normal frame path calls
this bridge at080D0BE8 before080C9000 installs the queued callback. Therefore
the existing producer literal583454 remains03002568; redirecting it directly
to the shadow would bypass the established buffering contract.

Source palette owner1000:0174 has the established native allocation
03003D30..03003D50. Native080C4BC0 clears eight words there, and native
080C4CC4 projects from the same owner. Train uses counters+0/+2 and six
colors+4..+E, entirely within those32 bytes. The previous Train helper used
03002568 with counters+4/+6 and colors+8, which did not match these consumers.

Source7834FF..783529 supplies Train's initial six colors. Source76A952..76A9BB
updates the two counters and selects one of three source palette rows at
76A922. The already-converted native row payload is at08583840. Source
783A9A..783AE4 writes those six colors to FEC4..FECE, represented by native
050000C4..CE. The new init/cycle/project routines use this single established
owner. The init and projection adapters preserve the preceding Shoot route.

Source projection gates at783726..78378C use common03D4 bit10, source0370
and source03CD. Existing native consumers establish those as03004506,
0300260B and03004529 respectively; native literals080D1C74 and080C4D3C
confirm the latter two. The half-brightness operation is verified for all
4096 source colors: source channel floor-halving followed by commercial
conversion equals the emitted mask739C/shift/remainder operation.

## Allocation and reproducibility

Builder: `tools/build_train_graphics_repair.py`.

Input SHA-256:
`83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD`.

Candidate:
`build/train-graphics-repair-20261016/current-candidate.gba`.

Candidate SHA-256:
`96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530`.

The60 Expected Write intervals total38,556 bytes. New data/code are placed
only inside these four separately checked intervals:

- 6E0EE0..6E51F0
- 6F56A0..6F843C
- 6F8440..6FAFE4
- 6EE900..6EF900

Each interval is exactlyFF in the pinned predecessor and has no unaligned
32-bit pointer, aligned ARM-like branch target or aligned PC-relative literal
reference. Previously considered larger regions contained existing candidate
targets; those targets remain untouched and are not reclassified as data.
Unwritten gaps are preserved. The manifest declares every actual write and
all211 new ARM instructions plus literal pools, and the complete inverse
recovers the predecessor. Independent verification and runtime results are
recorded separately; a successful build alone is not a visible-result claim.

Independent verifier `tools/verify_train_graphics_repair.py` passed with
reportSHA-256
`C4DCF5669AB21BB92978EE0ECE6B5EC027BC0CDF42CDE72D1FBDB9AEDFF084EC`
at `build/train-graphics-repair-20261016/verification.json`. It checks all100
descriptors/36 maps,32,768 tile pixels,111 colors, eight initializer calls,
12 palette-cycle cases,8,192 executed projector paths,9,216 route cases,
20 negative mutations, complete inverse and inbound candidates. Both camera
address adapters have exact instruction/literal contracts and individual
negative cases. A subsequent
in-memory generation with the additional queue-copy preservation guards
reproduced the exact96638 candidate without overwriting the runtime artifact.

## Explicit remaining component

Source77DAA0 calls68F7:2507, raw76B477..76B49B. That helper initializes the
Train hazard state at source0376/0378/037A/037C from two random fields; its
associated76B3xx consumer additionally uses037E. A native lifetime/owner for
these private fields has not been established in this layer. The repair
does not map them by adjacency, create a new RAM allocation, or claim that
the seed and hazard state machine are implemented. This bounded omission is
separate from the now-source-addressed background/map/palette consumers and
from the temporary campaign route policy. No save data was accessed and no
emulator was launched by this builder or its authoring agent.

## Bounded runtime observation

The parent ran the unchanged96638 candidate through natural character13
selection at77 seconds (Start50,A55,11 Down presses during56..61,A65).
`build/runtime-train-repair-id13-20261016/current-candidate-0.png` shows a
coherent Train arena and both fighters on the train with timer1:55. The
capture recorded28 enabled OAM objects, world coordinates0400/0B80, the
actual BG1 owner03002388 with48×2 geometry, and a blank native tile0. Capture
manifest SHA-256 is
`5E373FCF33C085A9CD3C8D39A482DAF316631E7D20DD35841052747C6FCD1775`.
This confirms the repaired entry case; it is not a claim of complete battle,
hazard, palette-animation or campaign regression coverage.
