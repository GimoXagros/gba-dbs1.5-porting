# Actual terminal visibility and native implementation boundary

Initial read-only assessment of the completed neutral continuation
`build/bizhawk-wsc-terminal-tail-20261109-a`, followed below by the separately
authorized isolated native component. Frozen runtime files remain unchanged.
The tail starts from genuine core100570 and exits naturally
at core101035, mode8, stage11, flags0D86. It uses no HP module or battle policy.

The frozen observer is `tools/bizhawk_continue_wsc_terminal.lua`, SHA256
`C8E0675BDDFF5484173398CC686340B151E94456E5F24E6EB2A4F0E9B355F3AC`.
Its strict loader composition and exact BG1 call-site pin passed the author
check; independent actual-Lua and runtime QA are separate records.

## Concrete visible samples

There are106 potentially visible final-IRQ reads, old k114 down through9,
while Shoot0800 is clear. All106 have full RAM/SRAM snapshots; the128-snapshot
cap begins later. For every visible line L from k+29 through143, every one of
the32 cells in row `((state8 - 21 + L) & 255) >> 3` of RAM0800..0FFF is0000.
The corresponding common-bank tile0 at RAM4000..401F is all zero in every
one of the128 full snapshots. Thus these actual samples satisfy the pixel
prerequisites of the existing finite row-coverage proof.

The fixed32 CPU-write callbacks logged zero events. The exact BG1 refill call
at77E196 logged zero calls. These are bounded observations: the CPU hook does
not observe general DMA, and snapshots do not exclude an unobserved DMA
write-and-restore. The source-owner analysis separately identifies the actual
FIRST-only presentation queue and safe descriptor destinations above4000..401F;
see `shoot-actual-terminal-di-owner-20261109.md` and the source investigator's
following-consumer assessment. No blanket absence of DMA is claimed.

The custom observer records217 pre-read entries; frozen DIv3 records216 paired
consumed words. Independent capture QA confirmed that the first restored-frame
entry preceded DIv3's fresh calibration and was offscreen. All106 potentially
visible pairs were captured; the89 omitted full snapshots had BG1 disabled.

## Horizontal-value lifetime

Source0C3A at75FB20..35 writes all four scroll ports from persistent0300:3C..3F.
In particular75FB30 overwrites OUT10 from0300:3E before the layer-disable test
or0400 routing. Native085E7400 has the corresponding unconditional four calls,
including08000F2C from0300456E. The immediate next display therefore replaces
the stray0DEC horizontal value without reading it back. Source0D87 uses
IN03/OUT11/OUT03 and0E0B uses IN11; neither consumes OUT10. The bounded source
terminal/display/camera bodies inspected by the source investigator contain
no IN10. This supports an observationally inert final callback only together
with the cleared-row and blank-tile lifetime prerequisites.

It does not justify a constant-zero source operand. Actual interrupted DI varies,
and source assets can positively populate the earlier0521E alias with nonzero
values. The native callback dispatcher supplies no source-DI argument.

## Exact remaining caller condition

Source773776 compares the player's Y with0C00. The low-Y arm77377D..796 installs
197A without replacing the player callback or resetting motion. Neither197A
nor1B55 supplies a later ground/current-previous/velocity guard. The high-Y
arm instead installs668E:1E51 and enters193B's grounded wait. Therefore the
actual stationary tail does not establish absence of refills for every legal
low-Y moving-player entry.

The initial proposal considered an explicitly recognized live
stationary family, using the existing router to retain its current fallback
outside that family. Its contract must bind the real native player callback,
zero control/physics and equal coordinates, zero BG velocities, terminal
upper/aux owners, and the blank-tile producer/lifetime. It would execute the
exact0D87 recurrence and use a return-only final callback because the remaining
horizontal effect is unobservable. No new latch or invented source-DI mapping
is required by that design. Parent subsequently authorized the bounded scope;
the isolated implementation below supersedes the proposed router hook. The
general low-Y arm remains open.

## Isolated late-queue component

Corrected candidate `build/shoot-guarded-transition-20261109/component-c.gba` has SHA256
`18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1`.
The first B3F7349A candidate is rejected: it compared the display priority
with unsigned0000F000. Constructor11AE4..AF0 sign-extends the16-bit argument;
the real header storesFFFFF000. Root independently confirmed this value and
current==last==4518 in a retained native capture. The corrected instruction
at6FF65C is CMN R0,#1000, with an explicit unsigned-priority negative case.
The intermediate3C097281 candidate is also superseded: stage11/0400 can
remain set after source mode8 exit. The final tiny wrapper additionally
requires actual native mode WORD03002310=7.
Its predecessor is exact v72 `025C1C5E...1732DA`. It changes four spans:
D0BE8 (4 bytes),6FF600 (288),6FF9C0 (1092),6FFE10 (192):1576 declared bytes.
Full inversion restores every predecessor byte.

The heavy predicate runs after the real17758 queue copy at D0BE8 in the
FFFFF000 display-preparation task08352268, which runs after the native111B0
VBlank barrier. It requires the current header133C
to equal both owned4518 and scheduler-last1344, active in the52-slot pool,
with the actual callback/priority. Only copied count1 with sole callback8587200
is eligible. Success replaces that one queued word4578; failure preserves
the original copy's register outputs and memory effects. C9000 then pops1→0
and schedules the tiny wrapper at VCOUNT1. No existing router byte changes.

The tiny wrapper086FF6B4 rechecks live mode7/stage11/0400, supplies the actual new
IRQ address086FFE10 to retained display085E7400, and restores incoming
registers. A stale mode/stage/phase tails8587200. The display's later C9000 sees
the already-empty queue; the wrapper does not invent an IRQ argument from
the interrupted caller's R6. The exact retained display still decrements
state2 and selects its source-compatible first compare.

The live predicate binds terminal input/battle callbacks374FAC/37354C,
neutral base0 FIRST35620C with zero controls, physics and displacement,
equal current/previous coordinates, no drop-through, linked no-op upper/aux
5BF200/5BF600 with exact presentation resources/events, FIRST-only render
queue482A/4830, and both BG descriptors' zero velocities. Shoot-specific
descriptor2388 maps source020E to hardware F000/ports10–11; descriptor2338
maps01CE to F800/ports12–13. These bindings differ from the waterfall scene.

Hardware mode0/BG1CNT maskDFCC=1E00 excludes mosaic and binds charbase0,
4bpp,screenbase30,32×32. Current tile06000000..1F must be zero. With BG1
enabled, old state2 k must be1..143; all32 cells of every sampled row for
native y=k+37..159 must currently be zero. This includes the native bottom
eight lines and rejects historical refill effects directly. The guard uses
old state2 because retained display copies it to state4 before decrementing
state2's low byte; state8 is unchanged.

The source recurrence/table is exact. Actual C10 accepts the already converted
hardware compare; it does not add8. Final086FFEBC is only BX LR. Its omission
of the unrelated DI-derived horizontal write is justified only for this
blank-row family until the next unconditional prepared-tuple OUT10 overwrite.
The scheduler may start another iteration before line1: current==last does
not assert global quiescence. The retained stationary terminal family is
inductive under neutral input/no-op upper+aux; the0400 update can clear more
rows, but does not change state2/state8. Known native OBJ/fixed BG destinations
exclude blank tile0. This is a bounded family contract, not an arbitrary-task,
moving-player, or universal DMA claim.

Both reservations6FF600..800 and6FF9C0..6FFED0 are entirely erased and have
zero strict whole-ROM inbound references, with no exemptions. Independent
layout ledger89EAB41C covers1394 declared predecessor extents, including FF
tails, and intersects neither reservation. There is no new RAM or task.

Author checks execute153 guard cases,480 IRQ cases,12 joins using actual
17758, and4 live-wrapper cases; six output-corruption controls fail closed.
The unchanged192-byte IRQ unit39B5D48F independently passed720 actual-helper
cases,16 return-only cases and9 mutations (report914B52CC). Independent full
component/queue/display QA and root integration remain separate gates.

Independent full-component QA subsequently passed exact18BB: verifier
`1B83BC650DAFF3FCA643DC92789A610962910D11829C34BE690DFCEFF4600054`, report
`555554FDADF48C80F74DE2A9700B7ECD6FC798F859C151B6A4AC440A9C6925FB`.
It executes real17758, copied IWRAM C9000, actual interrupt dispatch, the tiny
wrapper and retained display through all eight matches and the final callback.
It also covers380 guard,109 pool,14 postcopy,144 stale-wrapper,720 IRQ and16
return-only cases, with21 meaningful negatives. Root integration and runtime
checks remain separate; this approval retains the stationary-family limit.

The tiny wrapper's failed checks can change IRQ-local carry before the old
display path. Register/memory effects remain exact. Root review binds the
actual11420→11374..398 interrupt epilogue: it has no flags-dependent consumer
of that carry and restores interrupted flags from SPSR. This qualified ABI
does not claim equality of dead intermediate CPSR bits; the new0D87 handler
itself preserves incoming flags exactly.

Evidence hashes:

- `terminal-tail.txt`: `B21FE05CE1FCA0387761F9DAF68919B437771D6EC50979BB5083966D8F6334CA`.
- `tile0-writes.txt`: `8F7D7A2CA0A09621D3B024B050B5B4C20BA09974D8CC4DCFE453D00512033CFD`.
- `bg1-refills.txt`: `4C2F1CA8408F2FB8258A300DB7134A2F719E04B472C7B1460D45A28A49F7B7FD`.
