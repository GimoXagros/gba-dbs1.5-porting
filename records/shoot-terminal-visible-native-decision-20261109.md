# Actual terminal visibility and native implementation boundary

Read-only assessment of the completed neutral continuation
`build/bizhawk-wsc-terminal-tail-20261109-a`. No native ROM or frozen runtime
file was changed. The tail starts from genuine core100570 and exits naturally
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
consumed words. A possible cause is the first restored-frame entry preceding
DIv3's fresh execution calibration; that entry is not promoted to a consumed-word
pair. Independent QA owns the exact callback-error diagnosis. No count was
silently reconciled.

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

A bounded implementation can be considered for an explicitly recognized live
stationary family, using the existing router to retain its current fallback
outside that family. Its contract must bind the real native player callback,
zero control/physics and equal coordinates, zero BG velocities, terminal
upper/aux owners, and the blank-tile producer/lifetime. It would execute the
exact0D87 recurrence and use a return-only final callback because the remaining
horizontal effect is unobservable. No new latch or invented source-DI mapping
is required by that design. It is a proposal, not an emitted implementation or
a claim that the low-Y arm is fixed. Parent review must choose that bounded
scope or close the specific low-Y entry condition first.

Evidence hashes:

- `terminal-tail.txt`: `B21FE05CE1FCA0387761F9DAF68919B437771D6EC50979BB5083966D8F6334CA`.
- `tile0-writes.txt`: `8F7D7A2CA0A09621D3B024B050B5B4C20BA09974D8CC4DCFE453D00512033CFD`.
- `bg1-refills.txt`: `4C2F1CA8408F2FB8258A300DB7134A2F719E04B472C7B1460D45A28A49F7B7FD`.
