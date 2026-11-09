# Actual terminal IRQ operand owner — 2026-11-09

This read-only finding uses the successful original-reference run in
`build/bizhawk-wsc-healthy-shoot-terminal-20261109-a`. It changes no ROM,
controller, emulator, save or native callback. Source identity and the existing
0D87 recurrence/native scroll ABI are reused; their suites were not rerun.

The direct FIRST attack kills SECOND at core99458, native source root5 follows
in that frame, and source1750 is observed at99459. The first actual0DEC pair
occurs at100569. It reads ES0300,DI2214, hence physical0521E/F, and the next
instruction fetch observes AX0000. The backing-byte peek matches consumed AX.

## Recovered interrupted caller

The captured SP is1FC2. Source0DEC pushes AX,BX,ES,FLAGS, eight bytes. The
far-return words at1FCA/1FCC are0F41/4FFF, exactly the instruction after the
IRQ dispatcher's indirect call. That dispatcher pushes AX,DS,FLAGS, six bytes.
The hardware return words at1FD4/1FD6/1FD8 are therefore IP0173,CS8719,
FLAGSF246. The interrupted instruction is source787303, `pop si`.

This is the epilogue of8719:0148. Its immediately previous instruction787302
has restored DI. The retained caller return at1FE4/1FE6 is4090:1135; source
741A30 calls8719:0148 and returns there. Source C00:[8] is2214, and task HEADER
2214 contains callback4090:1130, priorityF000 and flags2. Thus the observed
DI belongs to this scheduler task header. This particular interrupt did not
occur in the frame wait, although earlier calibration also observed DI2214.

The read is not task flags at0C00:221E and is not transition state0300:00F4.
Physical0521E is common-bank logical tile90, byte1E. Source side1 companion
preload743870..743886 uses base6D; companion record28 descriptor0 contains
36tiles and writes003C to that exact word. Evolved companion46 containsC0C0
there. These are positive counterexamples to a general constant-zero resolver,
not claims that either supplied the captured tile's last write.

## Visible interval and native boundary

At the paired read, transition words at0300:00EA are
`0000,0074,007D,0008,00B8,0030,01DA`. The trusted recurrence gives old k117
from state4 minus8 and final comparison line146 from k+29. This first read is
after source visible line143. It does not settle later frames when k<=114.

The native IRQ callback dispatcher supplies no source-DI argument. It loads
030012E0, establishes LR and branches. Source OUT10 maps to native08000F2C,
but neither its entry r0 nor an ARM task pointer has been proved equivalent
to this source graphics-byte alias. The captured zero alone cannot justify
an unconditional native zero write. Visibility equivalence is the smaller
remaining avenue, using the existing cleared-row proof.

The actual final100570 snapshot supplies a finite entry for that avenue:
FIRST1784 is668E:115D, grounded flags1800, zero controls/physics/displacement,
and equal current/previous X0DC7,Y1500. Its queued-upload field+C0 is zero.
Input07D6, battle0B8B and scene1B55 remain installed. BG0 and BG1 velocities
are zero. SECOND is4090:7D7C and AUX4090:7DD8; both source entries are single
RETF. Shoot flags1486 lack20, so the older conditional timer4030 exclusion
must not simply be assumed from that flag in this capture.

The subsequent neutral tail should retain full IRQ snapshots, watch CPU writes
to all32 physical bytes4000..401F, and count the exact BG1 camera call at
77E196. Its arguments are stack offset020E,segment1000,modeBX; post77E19B
precedes argument removal. Pre/post map0800..0FFF and descriptor020E..024D
snapshots reveal completed-call changed cells. They do not exclude an
interior write-and-restore if such calls occur. No calls positively exclude
this specific refill path. Snapshot equality alone does not replace a write
ledger for the blank tile.

The emulator's hardware DMA path bypasses that CPU-write hook. Source7520DE
is a CPU REP MOVSW flush, but this does not exclude DMA: the already reviewed
presentation uploader2E6E invokes CC6/D1E, and CC6 enables general DMA at750CF8
after writing ports40/42/44/46. The existing synchronous completion proof is
reused, not rerun.

There is a smaller positive destination bound for the three captured current
presentation owners. Source752EBB..752ED2 computes
`(fixed_base << shift) + (bank ? alternate_bytes : 0) + graphics_base`.
Their shift is5 and graphics base4000. Reading the current event's actual
descriptor indices and descriptor lengths gives:

| Owner / P0 / event | Fixed base | Alternate bytes | Descriptor indices / largest length | Both starts / exclusive maximum end |
|---|---:|---:|---|---|
| FIRST1784 /3399D0 /0 |1|0340|0..9 /384|4020,4360 /44E0|
| Upper1894 /3D5F80 /1 |1F1|0080|7..14 /128|7E20,7EA0 /7F20|
| Aux19A4 /3914E0 /0 |99|0480|0..11 /576|5320,57A0 /59E0|

None wraps16-bit destination arithmetic or overlaps4000..401F. Thus these
specific event/resource upload owners cannot alter the blank tile, even via
DMA. This does not assert exclusion of every other DMA producer or preservation
of these identities through an unobserved transition. The tail ledger remains
explicitly CPU-only; its zero count must not be described as all physical writes.

## Actual neutral tail and bounded visibility result

The separate genuine-state neutral tail is
`build/bizhawk-wsc-terminal-tail-20261109-a`, core100570..101035. It reaches
mode8/stage11 with flags0D86. The author/independent QA own the217 custom
pre-reads versus216 calibrated paired reads; this source finding does not
replace that audit. All216 paired consumed words are0000, with DI varying
among2214,1EE4,02D4,1784,00C8. No constant-DI rule is inferred.

All106 potentially visible reads have full snapshots, before the128-snapshot
cap. For each later visible line L, from expected comparison k+29 through143,
the trusted source row formula is `((state8 + L - 21) & 255) >> 3`.
All32 cells in every selected row are0000:26,272 cell checks pass directly
against the snapshots. Tile0 is identical and all-zero in all128 snapshots.
The ledger records zero CPU writes to4000..401F; the BG1 monitor records zero
calls at77E196. The89 omitted counter snapshots occur after the visible phase.

Every captured render queue has count1 and sole presentation181A, FIRST+96.
The only active2E21 upload task is header1FF4, targeting presentation181A in
segment0C00, descriptor0..9 and bank0/1. It appears in19 snapshots. Thus the
observed queued DMA provider is positively covered by FIRST's destination
bound above, rather than being assumed absent. Display queue0300:44 and CPU
flush count0C00:388C are zero throughout those128 snapshots. The later result
constructor773B7B..773BE9 uses base137 and graphics4000; its known1312-byte
descriptor covers66E0..6C00, also disjoint from tile0.

The first IRQ cycle has k116 down to9; the later cycle restarts at117 with
Shoot800 already set. That later sequence must not be counted as another
visible interval merely from k. The source display's flags800 test suppresses
the layer. This is actual-path evidence, not coverage of every possible k or
every legitimate terminal entry.

The next source0C3A always overwrites horizontal OUT10 from persistent shadow
0300:3E at75FB2E/75FB30, before the flags800/0400 tests. It similarly writes
OUT11 at75FB35. Complete decoded terminal1750..1E23 has only IN11; the bounded
display/IRQ/update range75FADA..75FE03 reads only portsB2,00,03,11. The checked
camera/bounds/idle/uploader bodies contain no IN10 or dynamic-port IN either.
This closes these immediate readback owners, not arbitrary unreviewed imports.

The implementation decision remains scoped: the observed defaultID0 neutral
tail supports visibility equivalence, but the caller does not universally
enforce stationarity. At773776 the centered182F callback checks unsigned Y
against0C00. The Y<=0C00 path77377D..773796 installs197A directly, without a
ground, zero-velocity, callback or current/previous-position guard. Neither
197A nor1B55 adds that guard. The retained0B8B camera path can still reach
7415B7, bounds7415D7 and BG1 camera77E196 when the relevant player moves.
Excluding that moving low-Y entry for the installed family, or preserving its
refill-aware consumer, is the precise remaining broader caller condition.

## Frozen evidence

- `di-observer-v3.txt`: `185A6C749BBB749364F73DF0AFE4544076C6482FF5046656CDE50DA59086249A`.
- `di-v3-distinct-01-0300-2214-RAM.bin`: `74A26F13E48C33B76568C889469262824ABC1AB5610E05B1A4082B4162A49517`.
- `di-v3-distinct-01-0300-2214-SRAM.bin`: `F6654E9A2E1F2649C9E14A452C3BD2A775B78C2D950E46B825522C7D379388F4`.
