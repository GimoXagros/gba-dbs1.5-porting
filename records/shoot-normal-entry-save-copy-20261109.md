# Original normal entry and authorized save-copy preparation

Read-only source investigation, 2026-11-09. Source WSC SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No emulator launch, guest mutation, original-save access, save write, or ROM
change by this investigator. Root owns the separately authorized original-only
development observation and all launch/provenance handling.

## Ordinary campaign entry

The existing `analyze_shoot_lifetime_consumers.py:actual_shoot_caller` proof is
reused. At `740C97..CB0`, game mode `03D0` becomes SRAM `0050` plus two when
stage `005C` is seven. Single-player mode zero therefore reaches the required
mode two at stage seven, not after the first ordinary stage victory.

At `7417B5..17FE`, FIRST HP zero with state `003E` takes root case four first;
otherwise SECOND signed HP <= zero takes root case five at `7417F3`.
Timer expiration at `74180F` takes root case zero. The root-five Shoot gate is
stage != 11 and (difficulty == 3 or (difficulty != 0 and progress bit0400 clear)).
Difficulty three guarantees this predicate only after the actual stage-seven
HP victory. It does not convert a first-stage timer win into Shoot entry.
The resulting scene allocation at `771FE3` installs `71F0:0EEA`, priority0FF0.
No reliable shortest campaign battle policy is established here; no new timing
variant or autoplay implementation follows from these source facts.

## Extra menu and its separate mode23 graph

Title menu consumer `780CBE` uses tree pointer table09A7 and eight-byte row
records. Root row four opens tree two. Tree-two row zero requests mode22;
row one requests character selection with config bit0008. Character-selection
outgoing handler `778C09` tests that bit and requests transition five, whose
mode-four table entry is mode23.

The second tree-two item is disabled by `780E76` only when
`0C00:39F6` bit zero is clear. Startup `85DE:007B` calls `85DE:02EF` to copy
SRAM0076..015D to `0C00:392C..3A13`; its eight-byte signature comparison
passes for the authorized copy. Thus this unlock is backed by SRAM0140.
Selected reads from **only** `build/wsc-user-save-copy-20261109/supplied-copy.sav`
show0140=0001,0073=02,0086=3800,0088=0030. The extra item is unlocked.
This establishes eligibility, not an observed menu selection.

Mode23 init `4090:A040` returns; main `4090:A041` allocates local callbacks
C999, A56B and BC1C, initializes its state at0200:0012 and selected character
at0200:001B. Additional allocator `74AC6A` installs B71C. All13 reachable
literal `4FFF:0BC7` installations resolve to BC1C, B740, B71C, B7D9, BC36,
BC5A, B99A or AC67. Following these and inline task callback replacements
gives44 local callback roots and4052 decoded instructions in A040..C9FF.
The only computed jump, BD2F, uses bytes9A46 = [1,1,1,1,1,1,0,1], selecting
BD3A or BE18 from tableBD34. No other unresolved jump or direct target outside
that local interval remains in this bounded traversal.

This is positive separate behavior, rather than an inference from a different
initializer: the graph uses local presentation/tasks and its own completion
cleanup A0FD, which deletes the three owned tasks and requests transition zero
(mode23 -> mode20). The only71F0 imports are0161 and01AB, the exact palette
snapshot/fade helpers at772061/7720AB. Import859A:034A loads static tiles,
palette and a map at785CEA;85DE:02EF copies configuration/save data. There is
no local target7168/Shoot scene call, stage11 installation,375E/3760 IRQ-slot
reference, or OUT03 scheduling in the traversed graph. Local outputs concern
display/window/scroll and mapper registers. Generic task, sprite, palette,
sound and configuration helpers are retained as their typed services; this is
not a claim about arbitrary corrupted task pointers or all RAM states.
The unlocked mode23 route does not supply the targeted Shoot terminal IRQ
observation under these normal-entry contracts.

## Exact first-frame SRAM normalization

Reset `7FFFF0` jumps to `4FFF:06FC` (`7506EC`), which calls `4FFF:07E2`
(`7507D2`), then `4FA3:01D4` (`74FC04`). That initializer establishes DS1000,
AX0000 and BX004E. `74FC1F` writes word[004E]=0001; `74FC4A` writes
byte[004E+25]=00. These explain the root observer's two first-frame differences:
004E changes04->01 and0073 changes02->00. The appropriate check compares all
32768 bytes against the authorized copy with **only these expected values**
substituted. It must not ignore those positions or broaden exclusions merely
because the initializer also touches fields already equal in this copy.

## Observation contracts

Reuse the frozen observer's calibrated BizHawk2.11.1 callback adaptation and
preinstruction-fetch PC check. Capture actual source entry747A68, scene772DEA,
terminal773650, clear7738CA, normal scroll75FC27 and finalIRQ75FC90/98/9C,
with registers, actual callback slot and relevant maps/state. These are
observations; no register or RAM assignment is justified.

The old collector's `diA` expression `(0x3000+IY+10)%0x10000` is incorrect
outside internal RAM. For source `ES:[DI+A]`, effective offset is
`(DI+0xA)&0xFFFF`, linear address is `(ES<<4)+offset` with the core's20-bit bus
mapping. At75FC98, ES0300 with DI>=D000 can read SRAM above physical10000.
Observe the actual System Bus access, and the AW value at75FC9C after the
load, rather than aliasing the address into internal RAM. Preserve exact
word-access behavior at boundaries. The original frozen harnesses remain
unchanged; a new authorized-copy harness must state the new provenance.
