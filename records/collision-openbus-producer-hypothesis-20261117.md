# Historical E5: a discriminating malformed-command mechanism

The historical E5 producer is still unobserved. New offline analysis supplies
a concrete mechanism that can produce both the observed collision type E5 and
metadata register 04000020 from the malformed FFFFFFFF command/A pointers
already observed on the old evolution path. This is a conditional explanation,
not a claim that the historical failure traversed that path.

## Exact conditional chain

The input ROM is the original 8 MiB 389F56FF...ABD7F1 image and the original
22A2F2D8...D16C9937 timeout report. This analysis does not rerun the canonical
P1 census, any old route, or an emulator.

1. The ordinary per-frame collision producer reads current command from
   presentation +24 at 08353BCC. Its command-B lookup at 08353CA4 is
   `ldr r4,[r4,#0xC]`. A current command of FFFFFFFF therefore reads a word
   from wrapped address 0000000B, inside protected BIOS memory.
2. The pinned mGBA protected BIOS word path returns the BIOS prefetch latch
   and rotates by `(address & 3)*8`. With latch E3A02004, this yields the
   actual B pointer A02004E3. This is an unmapped address with low bits 3.
   E3A02004 is not an invented signature: the pinned
   [GBASwi16 implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/bios.c#L612)
   explicitly assigns that value to the latch. The actual last BIOS/SWI
   history in the failing run was not captured. A separate memory.c path
   updates the latch when execution leaves BIOS.
3. At 08353D20, `ldrh r0,[r4]` reads the collision type. In the ordinary
   non-DMA ARM open-bus path, the pinned emulator uses `cpu->prefetch[1]`.
   The [ARM instruction runner](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/arm/arm.c#L195)
   fetches current instruction +8 into that slot before executing the load.
   The exact word at 08353D28 is E59F8070. Address bit 1 selects E59F;
   odd-address rotation gives `ROR32(0000E59F,8)=9F0000E5`.
4. The next instruction, 08353D24 `strh r0,[r1,#4]`, truncates the loaded
   register to the exact collision-list type **00E5**. Consequently the
   consumer computes `(E5-8)*2=1BA` and reads its target at 0836EF1C,
   reproducing the historical dispatch arithmetic.
5. The same malformed A pointer FFFFFFFF makes 0836E37C read its second
   halfword at wrapped address 00000001. Protected BIOS low halfword 2004
   rotates to **04000020**, exactly the historical r3. The intervening
   receiver loads at E394 and E3A8 overwrite r0 and r2 respectively, so the
   historical zeros in those registers do not contradict an earlier
   malformed attack metadata read. Their actual source values remain unknown.

The pinned [memory implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/memory.c)
distinguishes the protected BIOS latch from unmapped-memory open bus. The
word lookup in step 2 and the halfword lookup in step 3 intentionally use
different paths. During DMA or the documented immediately-following DMA
case, GBALoadBad uses the DMA bus instead; the exact E5 result then is not
guaranteed. Binary-to-pinned-source identity remains unproved.

An event B pointer FFFFFFFF would produce a different stored type, 00E8:
the event type load at 08353C6C sees prefetched 08353C74=E8BD0010, whose
upper half rotates to BD0000E8. Thus the next observation must distinguish
the command producer from the event producer, and retain the full loaded
register as well as its stored low halfword.

## Why the existing captures cannot decide this

The old ID14 entry and air captures record FFFFFFFF command and metadata
pointers at the initializer, but neither records the collision producer's
subsequent B load. Their retained RAM pairs are title/battle/result samples,
not the malformed producer instant; their later live-ID14 snapshots have
valid current command/A/B pointers. The prior odd-metadata observer reports
no odd collision metadata on those bounded routes. This does not establish
whether the producer was skipped, produced an invalid non-overlapping row,
or was superseded before the next actor pass.

The producer itself is gated by actor flags: 08352830..48 requires bit4000
and excludes low kind9. Within the general producer, the event append tests
actor +8 bit1 and a nonzero event-B pointer; the command append tests presentation
flags bit1000 and a nonzero command-B lookup. A malformed initializer does
not by itself prove that either append happened or that rectangles overlapped.

## New bounded read-only observer

`tools/bizhawk_observe_collision_openbus.lua` has eight exact-opcode-checked
hooks: actor gate 08352830, command lookup before/after 08353CA4/CA8,
event/command type stores 08353C70/D24, overlap 0836E370, and paired metadata
reads 0836E37C/E380. It logs only malformed current-command/A/B cases or
invalid stored types, capped at 32 rows per event label. The full loaded
32-bit type is retained separately from the actual stored low halfword.

The first invalid type, first E5 type, and first malformed command-type
observation each preserve a RAM pair. At the first malformed command-type
observation, a dedicated `collision-openbus-produced.txt` marker closes
inside the callback after the RAM writes. The module does not change guest
memory, registers, inputs, or program flow. It exposes `outcome()` for the
parent wrapper to stop after the current frame, allowing downstream overlap
and metadata hooks to run; `finish()` closes its summary before the parent's
normal completion marker. Existing alignment diagnostics can still stop
at an actual E5 consumer. A host/core stall must be classified separately,
using the already-flushed producer evidence, rather than called a completed run.

The frozen module SHA-256 is
2E92FCF81D391E558AC72E1D0D65A23661382DAFFB48B61AEFD13D1A77C43C88.
The focused checker `tools/check_collision_openbus_provenance.py` verifies
the original ROM/probe hashes and exact relevant instructions, binds the
three pinned emulator source files, checks the conditional arithmetic and
negative controls, and executes eleven actual Lua54 mock cases. They cover
valid silence, malformed gate, paired and stale B reads, E5/truncation,
separate event/command captures, row bounds, paired/stale metadata, and
opcode refusal. The source-bound report is
`build/e5-openbus-v79-20261117/author-check-source-bound.json`.

This verifies the observer and conditional mechanism only. It does not
prove actual B=A02004E3, actual type E5 production, actual overlap, or the
historical first cause. No clamp, fabricated pointer, game patch, or emulator
execution is part of this author work.

## First actual E5 producer observed in the parent-owned run

After this conditional analysis, the parent completed the new hidden run
`build/bizhawk-id14-openbus-20261117-a` on exact old8C72. Its completed
`collision-openbus.txt` now contains the previously missing actual chain at
core8322: actor02011710, presentation020117BC, eventB054, current command/A/B
FFFFFFFF, actual B lookup A02004E3, and loaded command type9F0000E5 before
the store to command record030048C8. This is an actual producer observation,
not arithmetic alone. The parent and independent capture reviewer own the
complete launch/pin/post-store-RAM audit.

The same scalar rows directly reject a gating explanation for this run:
actor+4=F780 contains bit4000 and low kind0, and presentation+0C=0 leaves
the command-disable bit1000 clear. There was one command producer and no
overlap or metadata callback before the next-frame stop. The historical
389F crash's actual rectangle overlap and metadata chain therefore remain
unreconstructed; the new producer observation must not be described as a
reproduction of that historical crash.

### Exact source/native gate ownership

Native PC-relative literal evaluation gives these two distinct owners:
08353BAC/BB0 saves presentation+0C to03004C62, and 08353C88..C94 tests its
bit1000 for command eligibility. 08353BB8/BBC saves actor+8 to03004C5E,
and 08353BDC..BE8 tests its bit1 for event eligibility. WSC1.5 has the
same distinction: 7424F9/4FF saves presentation+0C at BP-0C and742580 tests
bit1000; 742502/505 saves actor+8 at BP-0A and742522 tests bit1.

The event setter clears presentation+0C bit1000 only when the loaded command
flags at080128C4 have bit4 set. The malformed04000020 value has that bit
clear, so a previously set command-disable bit can survive and suppress
the malformed producer on another path. That predicate explains a possible
route difference, but it was explicitly clear in the new actual producer
capture. Actor+8 is absent from the scalar gate row and must be read from
the captured RAM before classifying the separate event-list omission.

## Bounded positive fixed-entry comparison prepared

The new module `bizhawk_observe_evolution_entry_provenance.lua` and wrapper
`bizhawk_probe_id14_entry_provenance.lua` reuse the same ordinary contact
input but stop at the first frame after actual ID14 event initialization.
They positively record the selected event, actual event row and command/A/B
pointers, all three relevant flag words, and the actual command-B lookup
even when it is zero. Boundary RAM is captured once. They do not modify the
frozen malformed-producer observer or rerun the full music sequence.

The expected row is grounded in a single source/native comparison:

| Field | WSC1.5 | Fixed native C91 |
|---|---|---|
| Actual ID14 base P1 | raw368FF0 | 086184A0 |
| Entry event | 115 from source7679DE | 115 from extended entry table |
| Event row | raw36938C | 08618BD8 |
| Command count | 2 | 2 |
| First command | P1+1F24 | 0861B0A8 |
| A pointer | P1+2298 | 0861B258 |
| Event B / initial command B | 0 / 0 | 0 / 0 |

The native initial command is02FF1D002A0001000000000000000000. Its first
duration is the established FF03-to-FF02 platform scaling; the command
fields and null B agree with source. Thus a fixed actual lookup of zero
would be a positive source-backed result, rather than an unexplained
absence of type E5. No full P1 census was rerun.

The module SHA is C942791335CDA9F7DE23411F5EC9069DC1F32D1F431C3B607775F0F4EDB8C93C
and wrapper SHA is0A5742C9B04130EC3418F5C67A8FC7D471343726FE18693066903F316EF99F78.
`check_evolution_entry_provenance.py` passes six actual Lua mock cases,
including valid null and non-null B, wrong identity, uninitialized/stale
selection, one-time boundary snapshots, and opcode refusal. Full nested
composition and actual fixed runtime are independently owned and are not
claimed by these author checks.
