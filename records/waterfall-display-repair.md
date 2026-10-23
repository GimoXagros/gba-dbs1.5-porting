# Waterfall display, background owners and compact palette state

Date: 2026-10-23. This is a bounded display/palette repair and independent
static verification. First-battle entry has visible evidence; movement/attack
stability remains open after a later fault. It is not a completed Waterfall
implementation or a release candidate.

## Source operation and actual native consumers

WSC callback `5EEA:0B4E`, raw `75F9EE..75FA64`, reads hardware port0, ORs
mask5 and retained word `1000:0382` into it, writes port0, then XORs only
the retained word with2. It does not XOR the hardware display register.
Source graphics initialization at `77DBD7..77DBE5` clears phase0382 and
hazard0384 separately from palette owner0174.

The USA native translator at `08011478..08011498` establishes these masks:

| Source display mask | Native hardware mask |
|---|---|
| 1 | BG1, `0200` |
| 2 | BG0, `0100` |
| 4 | OBJ, `1000` |

The old shared helper at `08583F00` always enabled BG0 and XORed hardware
BG1. The repair instead ORs `1200`, ORs `0100` when retained phase bit2 is
set, then toggles that phase. It reads native hardware `04000000`, not a
logical display shadow. The existing Waterfall graphics clone already owns
phase `03002568`; the repair uses that retained initializer and leaves hazard
`0300256A` separate. The valid phase domain is0/2 from that initializer and
the callback's XOR2 transition.

Source initializer `77DB11..77DBE6` assigns resource35 to owner020E and
resource36 to owner01CE. Eight existing clone literals had these native
object owners reversed. They are corrected without changing the resource
data, map buffers or scroll-port pointers:

| Layer | Source resource / owner | Native resource / object | Hardware map |
|---|---|---|---|
| Waterfall | 35 / `1000:020E` | 27 / `03002388` | BG0, `0600F800` |
| Scenery | 36 / `1000:01CE` | 28 / `03002338` | BG1, `0600F000` |

Software background object order and hardware BG numbering are not the
same mapping. The retained callback's control word `1E031F02` selects these
two map buffers. The first resource keeps scroll shadows `030012BA/BB`;
the second keeps `030012B8/B9`. Both retain the already verified collision
pointer `08626000` and dimensions1x3. Every one of the six source maps
inverse-converts exactly, as do all32,768 retained tile pixels and111
background palette entries. No replacement renderer or graphics extraction
is introduced by this layer.

## Palette lifetime and compact representation

Source `783495` selects palette owner `1000:0174`. The native initializer
at `080C4BD8..080C4BF8` clears exactly eight words at
`03003D30..03003D50`; literal `080C6284` identifies the adjacent live
collider owner `03003D50`. Eighteen colors plus counters do not fit in this
native32-byte allocation, so the repair stores only counters+0/+2 and
projects immutable ROM rows. It does not extend the RAM color cache.

All18 immediate source colors at `78352C..7835A1` equal phase0 slices of
the58-color source table at `76AA63`. The retained native conversion is
`08584000..08584074`. Source update `76AAD7..76ABC3` advances counter0
modulo4 and, on wrap, decrements phase1 modulo5. The replacement reproduces
all20 valid counter pairs; the ROM slices for every phase are eight main
colors plus two five-color windows. Neither cycle nor projection writes the
phase/hazard owner or collider.

Source projector `783AE4..783B90` writes exactly these18 native halfwords:
`05000024..32`, `05000036..3E`, and `05000056..5E`. It preserves the gap at34.
The common source flag03D4 bit10, disable byte0370 and dim byte03CD retain
their established native owners `03004506`, `0300260B` and `03004529`.
Channel-halving is checked against source RGB444 arithmetic for all4096
colors, both full and dimmed, including normalization after native BGR555
conversion.

The new callback is private to Waterfall; Iraira still uses the historical
shared callback. New palette entry adapters select logical stage9 but first
preserve actual stage11's dedicated Shoot priority. All256 character selector
bytes and twelve supported progression values are checked on both routes.
Fallbacks remain the existing Train/Shoot adapters, with arguments and stack
restored and no progression write.

## Independent verification and exact writes

Builder: `tools/build_waterfall_display_repair.py`.
Verifier: `tools/verify_waterfall_display_repair.py`.
The verifier does not import or invoke a builder or consume its manifest as
an oracle. It reuses the existing verifier's restricted ARM word checker for
bounded routines. Native service effects are explicit summaries, not native
service execution; the display EOR word is independently decoded and
evaluated between two bounded walks because that checker lacks EOR.

| Artifact | SHA-256 |
|---|---|
| Predecessor | `AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF` |
| Candidate | `C50ADCF54D29B327CCF5BFAE21F51784AC2A7A9544DF6093680BDB6387F93DFF` |
| Independent report | `2FE4896E11B5CD9C63AD30010594C7A613F9C0AE2DA21459DCCBE73D0F29A6D1` |

The candidate/report are under `build/waterfall-display-repair-20261021`.
Two independent verifier invocations produced byte-identical reports;
the second is `verification-repeat.json` in the same directory.
All three original ROM identities are checked; WSC1.0 is identity-checked,
while this repair's direct source contracts use WSC1.5 and USA GBA consumers.

The independent19 write intervals total664 bytes, of which611 change.
They comprise seven routine allocations, eight owner literals and four
entry/callback hooks. Every installed instruction and literal is checked;
the139 ARM instructions decode completely. The entire reservation
`628300..628900` is FF in the predecessor, with no existing unaligned
32-bit pointer, aligned ARM branch target or PC-relative literal reference.
Replacing only those19 intervals restores the complete predecessor,
including unused allocation gaps, the historical shared callback and all
preceding routes.

The report contains two initializer cases,20 cycle cases,240 full-projector
cases,8,192 shade cases,6,144 actual-getter routing cases,12 display instruction
walks and131,072 display truth-table cases. Forty negative mutations are
rejected independently of a fixed output-ROM hash, including BG owners,
display mask/phase, palette extent/destinations/gates, Shoot precedence,
source operations, source maps/tiles/colors, unowned gaps and unrelated ROM
bytes. The full-ROM inverse and source-map inverse are distinct checks.

Reproduce with six positional paths:

```powershell
py -3 tools/verify_waterfall_display_repair.py `
  build/selection-palette-index-repair-20261021/current-candidate.gba `
  build/waterfall-display-repair-20261021/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/waterfall-display-repair-20261021/verification.json
```

## Runtime boundary

The parent-owned77-second natural ID14 entry capture at
`build/runtime-waterfall-repair-id14-20261021` shows scenery, greenery and
Waterfall with timer1:55. Its capture manifest SHA-256 is
`9567FD140F2E841082822FAC846B25217678B8653BAC1F548F02ACDE55989123`.
The separate invariant report passes with23 enabled OAM objects, intact
native copied renderer and a bounded S02 stop. This supports first-entry
display repair only.

A later parent-owned movement/attack capture, with Right-input consumer
breakpoints, at
`build/runtime-waterfall-movement-20261023` ends in S04 with PC00000004.
Its capture SHA-256 is
`A2E568C21539236C1608B9DF367EDB4F67DC97B9DF0EF52333F6A7C8190ED675`.
The saved capture has zeros across the copied renderer `03000200..03000380`
and queue `03001D60..03001D70` while battle mode7 remains at03002310.
The fault's first writer and causal path are unresolved. A subsequent bounded
write-watch probe did not reproduce the fault.

The parent then repeated the99-second input schedule without Right-consumer
breakpoints at `build/runtime-waterfall-movement-plain-20261023`. That bounded
run passes the invariant check with38 enabled OAM objects, intact renderer,
and visible timer1:33; capture SHA-256 is
`81F2C18C0ADBB953961D3FCF93D6532AD672C385799CAC80637A1C13D46259A2`.
This narrows the observed failure to the instrumented run so far, without
establishing its cause. The fault is not dismissed as a debugger artifact.
The static verifier therefore deliberately does not claim runtime success.

The original USA control with the same instrumented movement schedule passes
at `build/runtime-usa-instrumented-movement-20261023` (27 enabled objects;
manifest `187029F4F952D6B1D1FB607D2B6E47FD45DCC08ADB44B3F735C4E8BA56F89DB2`).
More decisively, a plain-input execution probe at
`build/waterfall-boot-entry-20261023/probe.json` first reaches the ID14
constructor `083530CC`, then unexpectedly reaches boot clear `08000128`.
This reproduces reset entry without the Right-consumer instrumentation.
The preserved player pointer is `02011710`, its presentation is `020117BC`,
and its callback word is zero. The saved hitstop callback remains valid;
the subsequent write watch identifies the writer below. This is an open
gameplay defect, not an accepted debugger artifact or a repaired failure.

`build/waterfall-zero-callback-writer-20261023/probe.json` hashes to
`2C89274DD056F0EEFD190F16C4D2D7B55EC7E016EEDAA585F8DDFAF70902A35E`.
After 34 nonzero callback writes, a read-only watch catches `08355608`
storing zero into `02011710` (reported next PC `0835560C`, LR `0836AE28`).
The player has character14, table `+9C=0836A62C`, and row `+AA=0`.
Consumer `0836AE10` reads table index14 at `0836A664`, obtaining
`063C0000`; `08355604` then reads a zero callback from `063C0004`.
The 12-row native damage/follow-up table has not been expanded for ID14.
Source-backed table/payload conversion is the required next repair; a null
guard or substitution with another fighter would not establish parity.

That follow-up repair is now implemented separately in
`tools/build_character_followup_routing.py`: source1.5 has fifteen identical
follow-up routes, each corresponding to retained native record `0836A67C`.
The fixed ID14 execution probe reaches `0836AE24` with `r1=0836A67C` and
metadata owner `+9C=08628900`. The combined four-language development ROM
`3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C`
then completes the99-second instrumented movement/attack capture at
`build/runtime-integrated-id14-movement-20261023`: S02, no asynchronous faults,
intact copied renderer,42 enabled objects, coherent scenery and timer1:33.
Capture manifest: `7A08E9BDB2721220E264D2195D865FDCEA46137706E6033B6DA3193219F76192`.
This bounds the repaired failure; it does not make the standalone C50 artifact
or every remaining gameplay path complete.

Complete movement, attacks, hazards,
campaign parity and Iraira display/palette behavior remain outside closure.

## Later third-pattern correction

The later DBB long-run failure is a distinct stage-entity configuration
overread, not the player follow-up failure above. The source Waterfall
cycle selects indices `[1,0,2,1]`, while the previous configuration converter
copied only two records. Source third record `7450C1` points through slot
`4823` to callback `4090:3FCA`, which writes hazard mode3. The earlier
exclusion of that callback as unrelated in `records/object-config-conversion.md`
and `records/stage-runtime.md` is superseded by this actual consumer proof.
The bounded correction and its evidence are in
`records/waterfall-third-pattern.md`. Display phase `03002568` and compact
palette owner `03003D30` remain distinct from hazard `0300256A`; the display
and palette claims in this record do not establish complete stage stability.

This verification agent launched no emulator and opened or hashed no save.
The pipeline and all other agents' source changes were left untouched.
