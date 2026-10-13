# Shoot dedicated graphics/display initializer

Date: 2026-10-13. Static ROM-bound implementation; no emulator or save access.

This layer closes the dedicated `7CCF:0FC4` graphics effects and the display/IRQ
preamble at source `4090:7168`. It also repairs two assumptions in the previous
stage integration: stage11 bounds are not the native stage7 no-op, and Shoot's
palette state cannot extend beyond the native 32-byte palette allocation.

The separate full scene initializer, SRAM audio writes, task lifetime, and
constructors remain the scene workstream's responsibility. These functions do
not open the menu, remove the source `9908` gate, or establish runtime acceptance.

## Artifact and write ownership

- Exact predecessor: v51 plus audio and lower-rules layers,
  `223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E`.
- Output: `build/graphics-integrated-20261013/graphics.gba`.
- Output SHA256: `6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29`.
- New code/data only in the previously all-FF raw range `5C6800..5C7800`
  (end excluded); aligned pointer and ARM branch scans found no preexisting
  inbound references to that entire reservation.
- Four Expected Writes outside that reservation: native `07FC34` and `0C4CC4`
  each replace the exact `push {r0-r5,lr}`; resident `586400` replaces its exact
  `push {r0-r8,lr}`; native `0C4BC0` replaces its exact
  `push {r0-r2,r4-r5,lr}`. Each becomes a single ARM branch.
- Full-ROM diff: 1,148 changed bytes. No v51 generator or historical output was
  modified. The old uncalled graphics subset remains resident.

| Native entry | Effect | Contract |
|---|---|---|
| `085C7200` | `7168` IRQ/display preamble | No arguments; preserves r0-r12, LR and SP; flags clobbered |
| `085C6800` | Complete dedicated `0FC4` graphics effects | Same ABI; actual stage byte `0300231E` must already be 11 |
| `085C6B00` | Dedicated source stage11 BG1 parallax and shadow copy | Same ABI; called by actual-stage bounds hook |
| `085C6D00` | Compact palette-state initialization | Same ABI; called by dedicated graphics before any Shoot update/projection |

The source caller order is: preamble, actual-stage byte=11, dedicated graphics,
then timer/flags/stage-manager work. `085C6800` stores the native graphics stage
global `03002656=11`, distinct from that actual-stage byte.

## Graphics effect correspondence

Source `77DCB4..77DE62` is `7CCF:0FC4`, not the generic battle graphics routine.
The implementation blanks display through native `08000CF8`, uses native
`0807FBF8` for BG map reset, reproduces all four native BG control pointer pairs,
and calls existing staging reset helpers `08015D38` and `0801369C`.

The source stage11 dimension row at `77CD1C` is `(448,432)`. The earlier legacy
dimension selector deliberately mapped 11 to stage7 `(672,576)`; this dedicated
routine writes the source pair directly to `03004568`. It also clears the
mapped source camera field at `0300470A`.

Source `1000:0380` and hardware color0 receive `FFFF`, whose BGR444 hardware
color is white. The native color global `03002654` and `05000000` receive
`7FFF`. The resident Shoot clone's palette copy already skips palette color0.
The new `085C6A00` adapter performs its exact palette/tiles copy prefix and then
continues at `08582A30` with the clone's expected saved-LR stack. It bypasses only
the clone's generic backdrop-global store at `08582A24..2C`, retaining white in
the source's original write order. The two existing BG constructors and their
resident resource descriptors remain unchanged.

The entire generic native `0803EE08` is not called. Its actual-stage HUD lookup
at `0803EF08..44` still selects a row from the eight-stage table at raw `03F078`;
the existing dimension and graphics-dispatch hooks do not make that HUD index
valid for stage11.

### HUD data and layout

Source C3=C2, DS=3FD6 resolves to raw `42FD60`. Its 16 BGR444 colors inverse-map
exactly to native raw `01FD30..01FD50`. Its 544 planar bytes at `42FD80..42FFA0`
inverse-map pixel-for-pixel to the 17 packed native tiles `01FD50..01FF70`.
Native font SHA256 is
`CCB3BBA8A1580F0E63881BDBD6C2D061FF42EF66D6FF89D69DA420B50C24B41B`.

The dedicated source copies 15 colors, skipping color0. The new routine copies
`0801FD32→050000E2` with native halfword count15, and the 544 font bytes
`0801FD50→06007DE0` with native word count136. It writes exactly four `73FF`
halfwords at `0600D800..806`. This is the proven native row7 tile3FF form of the
source's four `2FFF` cells at source `0000:3000..3006`; final font tile3FF is
all index15 pixels. The generic HUD map copy is omitted because it is absent
from the dedicated source helper, not because no consumer was found.

### Camera and stage11 bounds

Source `7CCF:1240` (`77DF30..77DFDF`) and native `08080040..08080140` implement
the same 8-pixel stepping algorithm. Source arguments are BG0, X=112, Y=0.
The existing native routine receives exactly those four native stack slots,
with its unused source-segment slot zero. Its 14 horizontal steps call existing
`08013DD4` and the now-correct actual-stage bounds hook.

Source stage11 bounds table entry at `77DE94+22` is `15AF`, which sets
AX=1, BX=2, DI=BG1, and passes E0/E0 to common `13D5`. This common helper is the
native `0807FEB0` with r4=BG0, r5=BG1, r0=1, r1=2 and two E0 stack arguments.
The adapter subsequently copies all four BG X/Y shadow bytes to `0300456C..73`
in the original X-byte then Y-byte order. Actual stage11 now uses this path
during both initial camera stepping and later common bounds calls. Other
stages reproduce the replaced native push and continue at `0807FC38`.

## Palette lifetime and representation

Native `080C4BC0` allocates/clears exactly 32 bytes at `03003D30..03003D50`.
The preceding Shoot helper wrote as far as `03003D5C`. Parent analysis confirmed
`03003D50` is live fighter/AI state, read by `080C65AC`, so the previous larger
write extent cannot be retained. `03002568` was also investigated but rejected
as a replacement: besides stage users it has generic transition and actor
consumers, including `08083070` and `080C85BC`.

The replacement stays entirely in the existing 32-byte palette owner:

| Offset | Native representation |
|---|---|
| `+0,+2,+4,+6` | Original four source counters |
| `+8` | Pointer to the selected immutable six-color group |
| `+C` | Pointer to the selected immutable eight-color group |
| `+10` | Pointer to the selected immutable five-color group |
| `+14..1F` | Cleared, unused within the original allocation |

Source initialization case `8347:021D` supplies 19 immediate seed colors. They
are converted into the immutable ROM seed at `085C7300`; initialization points
the three groups at that seed. Source update `68F7:226B` is `76B1DB..76B312`.
It copies only contiguous slices from six immutable ROM tables. Every eighth
tick changes the six-color group, odd ticks change the other two groups, and
even nonzero ticks retain every group. The adapter captures the table selection
flag at update time, indexes by the old counter, then advances that counter.
Projection never reselects a group based on a newer flag.

The closed Shoot consumers are source palette initialization table row11,
stage-update table row11, and palette-projection table row11. Other explicit
`0174` consumers in the same source overlays belong to different stage cases.
Native actual-stage dispatch now routes Shoot projection to its dedicated
consumer and routes the existing Shoot update entry to the compact update.
Other stages retain their original representation and native projection path.
The actual-stage hook at native `080C4BC0` also routes stage11 to compact
initialization, covering the generic graphics initializer. Its legacy branch
reproduces the original six-register push exactly (r3 is deliberately absent)
and resumes at `080C4BC4`, retaining the already-installed legacy selector.
An aligned branch/pointer scan finds only the native call at `0803EE6C` and no
function-pointer reference to `080C4BC0`; generic graphics has only the call at
`080D1A2C`. Thus both dedicated and existing generic palette initialization
prepare the compact representation before their subsequent Shoot consumers.

Source projection `8347:082E` is `783C9E..783EAF`, selected by the row11 entry at
`78370E+22`. It writes six paired colors at palette offsets10/12,30/32,50/52,
repeats an eight-color group at64..72,84..92,A4..B2, and writes five colors at
C4..CC. It suppresses projection for source03D4 bit10 or source0370 nonzero,
mapped to `03004506` and `0300260B`; source03CD maps to native `03004529` and
selects half-brightness. The native stage7 projection interpreted some of
Shoot's buffered colors as palette offsets, so retaining that fallback was
also unsafe.

Commercial palette conversion uses 0→0 and nonzero channel n→2n+1. Therefore
source four-bit channel halving is not ordinary five-bit channel halving.
The new projector masks with739C, shifts once, and restores each surviving
channel's low bit. All 4,096 source colors prove this equals source channel
halving followed by the commercial conversion.

## Display/IRQ preamble

Source `747A76..747A8D` disables B2 bit4, writes source `FFE0=0FFF`, then changes
the display control high byte to F0 while retaining its low byte.

The commercial semantic bridge is source WSC10 `3BC801..3BC898` and native
`080D0B24..080D0BC0`: identical bit2/bit4 branching, task replacement, palette
restore and task deletion surround the interrupt-disable operation. The source
B2&EF operation corresponds to native `04000200` IE&~4. Native callback
`080D0B9C` and source `3BC86F` both set the corresponding global bit8000 and
delete the current task, providing a second lineage anchor.

Native `08000CF8→08011454` computes the backdrop address from the display high
byte: `05000000+((control&FF00)>>7)`. Thus source F0 selects native BG alias
`050001E0`, as independently established in the palette ownership work. The
preamble writes that alias7FFF, preserves the display low byte via `08000CD8`,
sets highF0 and uses the native display writer. This is the existing backdrop
alias path, not OBJ7's transparent color0.

## Verification

`verify_shoot_graphics_initializer.py` imports no builder or converter and does
not run a CPU emulator. It verifies exact original hashes, pinned source/native
oracle ranges, all 249 final instruction boundaries and reviewed ARM7TDMI
instruction classes, local literal ownership, ten complete reviewed code/data
hashes, four branch-hook targets, and the full-ROM Expected Write diff.

Independent asset checks reverse all 1,088 HUD pixels, 16 HUD palette colors,
19 initial colors, and 202 animation-table colors. Semantic checks cover all
8,960 counter/flag input combinations and all 4,096 dim colors. A repeated build
is byte-identical. Six deliberate input/output mutations are rejected by the
fixed-chain verification gates. Reports reside beside the artifact in
`graphics.json`, `verification.json`, and `negative-controls.json`.

No save files, emulator state, runtime screenshots, frame timing, live IRQ
scheduling or menu playthrough were used or verified.

## Separate coordinate-domain follow-up

The graphics dimensions are not a proof of the lower `8EF3` callback's entire
coordinate domain. A separate normal-battle producer converts pixel dimensions
to fixed-point world limits: WSC10 `390BDF..390BFC` loads `0300:0038/003A`,
shifts by4, and writes `0C00:39F0/39F2`; WSC15 `740E2B..740E48` writes the
relocated `0C00:3A18/3A1A`; native `080D1A70..94` writes `03004520/22`.

The dedicated `7168` source has no direct write to those two world-limit
globals, so this graphics layer does not invent one. Native `0836A570` consumes
the X limit for fighter collision correction, while `08341460` compares fighter
Y against the Y limit for flags/death processing; the latter is not itself a
clamp. Scene entry must establish which normal initializer ran beforehand and
with which dimensions before removing the lower rules' explicit coordinate
domain guard. This is outside the closed dedicated graphics effect contract.
