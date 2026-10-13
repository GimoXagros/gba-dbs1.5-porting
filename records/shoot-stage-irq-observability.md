# Shoot final IRQ: bounded lifetime and visibility evidence

Date: 2026-10-13. The0DEC route remains unresolved. This investigation changes
no ROM, generator pin, live callback, scene route or menu route.

Evidence tool: `tools/analyze_shoot_stage_irq_observability.py`, SHA256
`F5F8D96944C33749A8A1267D0C158D97D6B52A2F1803169E160FB984EA5F5A52`.
Report: `build/shoot-stage-irq-observability-20261013/evidence.json`, SHA256
`6CED897C10CB79CCAA4D94DD02849AD355828345E6AD1637141E4DF818FAF3C5`.
It reads only the hash-identified WSC15 original. Ten source ranges and the
critical decoded instructions are independently checked. It imports no ROM
builder, uses no machine execution and accesses no save.

## Interrupted DI is not a global invariant

The actual main loop at7506F6 calls the task scheduler at75075E, the transfer
flush at750763, then returns to the loop. The scheduler750B1F loads DI from
the task-list head at `0C00:000C`, saves/restores it around every indirect task
call, advances it through task+8 at750B6D, and calls the frame wait at750B7F.
The wait routine750EBD saves only AX/DS and spins on `0C00:3754`; it does not
change DI.

The task allocator starts at offset0014 and adds0110 when selecting another
slot (`75097D..750989`). Thus every valid task-list offset is4 modulo16,
whereas00EA is10 modulo16. All4096 distinct16-bit results of this allocation
arithmetic retain that property. This arithmetic check does not assert that
all4096 values are valid task slots.

Consequently, if0DEC interrupts the scheduler's actual frame wait, its read
is source `0300:(task_offset+A)`, rather than the transition state's EA+A.
The segment distinction matters: the offset came from a task in0C00, but the
IRQ reads it relative to0300. The main-loop transfer flush also writes DI:
7520DE loads a transfer destination and REP MOVSW advances it; no DI restore
appears before return.

These are reachable main-program contexts and concrete DI writers. No
instruction-cycle bound or live scanline observation establishes whether0DEC
interrupts them in a particular execution. The evidence therefore disproves a
global DI=EA assumption but is not a timed runtime counterexample and does
not justify silently repairing the source instruction.

## Conditional proof that the horizontal write could be hidden

The eight actual bytes at source75FCA3 are
`00 02 04 07 0A 0D 11 15`, or decimal `[0,2,4,7,10,13,17,21]`.
The evidence tool reads and checks these bytes directly. An earlier handoff
transcription of the last four values was corrected during this check; no
frozen ROM routine used that unimplemented IRQ table.

Let k be the old positive state2 value used by0C3A, and b the captured IN11
byte. The display writes state4=k, state6=0 and schedules k-1. At each matched
0D87 step i, the comparison is `k+i+offset[i]`; it writes vertical scroll
`b-offset[i]`, then advances state4 and state6. The eighth match therefore
occurs at k+28. It installs0DEC and schedules k+29, retaining vertical scroll
`(b-21)&255`.

For source visible lines0..143, a final IRQ can affect the visible region
only when k<=114. For any later visible line L, the sampled map row is
`((b+L-21)&255)>>3`. At the first such line, L=k+29, this becomes the row of
`b+k+8`.

The main0400 helper previously cleared32 cells across each row selected by
`((b+m)&255)>>3`, for descending multiples of8 starting at136. Exhaustive
checking of all b=0..255, k=1..143 and visible L>=k+29 proves that every sampled
row belongs to the set cleared at an earlier count m>k. All1,678,080 relevant
line/base/count cases pass. The proof deliberately excludes a clear at the
current count k, so it does not depend on current-frame update/IRQ ordering.
It also needs none of the earlier fixed0A40..0DC0 clear.

This is a conditional map-row coverage proof. Turning it into proof that the
horizontal OUT10 write is unobservable still requires both:

1. Zero map cells select a horizontally uniform common-bank tile0, whose
   initialization is reachable and whose contents remain preserved.
2. No later camera/map refill repopulates any of those cleared rows before
   the visible final IRQ samples them.

Neither condition is closed. Source74FEA0 contains a candidate clear of
4000..401F, but no reachable caller/lifetime has been validated. Apparent far
pointer hits inside other instructions are not treated as callers. Stage
bank1 tile0 is a different resource and is not horizontally uniform; its
presence cannot establish the common-bank tile0 condition.

After display completion sets Shoot0800, source display disables the
affected layer. The terminal workstream found no clearing of0800 in its
remaining phases, but the finite proof here is confined to positive k and
does not use that separate lifetime assertion to bypass either open condition.

## Camera refill remains an explicit gate

The terminal entry replaces input with4090:07D6 and battle with4090:0B8B before
calling1750. Although the input task only resets lists and captures camera
coordinates, the battle callback at74148B..74160A retains its camera block.
Its bypass test at7414B3 checks source03CD low7; common03D4 bit10 is not a
general camera freeze.

When the fighter's position changes, the battle block can call camera3367
at7415B7 and common bounds11BC at7415D7. The stage11 bounds consumer at
77E0C5 copies BG0's vertical velocity into BG1, then calls3367 again at77E196.
Thus the source has a concrete potential BG1 refill path during the same
terminal ownership. The source0E0B helper's zeroing of BG1 velocities at the
end of0200 alone does not establish that no later writer restores them.

The remaining proof would need a complete stationary-actor invariant or a
map-refill footprint showing that every sampled cleared row is preserved,
together with the common-bank zero-tile lifetime. Neither is assumed here.
The completed normal-display router continues to retain the existing0400
fallback, and no0D87/0DEC approximation or fabricated callback is installed.
