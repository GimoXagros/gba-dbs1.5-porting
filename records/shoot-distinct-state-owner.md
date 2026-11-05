# Distinct Shoot state: conditional native persistence contract

Initial read-only review recorded 2026-10-26; implementation follow-up
2026-11-03. The source objects are the two halfwords at
`1000:3CD8/3CDA`, physical `13CD8..13CDB`. They are distinct from the ordinary
regeneration timers represented by `030048AC/AE`.

The [ordered initializer storage layer](shoot-initializer-storage.md) now
adopts block 25 through the native API buffer coordinates defined below.
It advances the disconnected initializer to source `73F0`. No emulator,
physical EEPROM operation or supplied save was accessed.

## Decision

A small, disconnected persistence helper can be specified and implemented
before proving the complete source observer population. It can expose an
ordinary read/modify/write and error-return contract using the existing native
EEPROM service. Its correctness can be checked without claiming that the full
Shoot initializer or a source reader has been translated.

The bounded native ownership question now has a positive answer: the selected
backend has capacity, all its actual callers use blocks `0..24`, and every
additional match in the finite EEPROM-address construction inventory below
has a positively established graphics/audio owner. The expanded entry-alias
census also finds only the existing library bindings. Thus block 25 is a
concrete candidate owner under this explicit ordinary-program boundary,
without assuming that the source stores are dead.

**Block 25 is adopted by the 2026-11-03 source-ordered layer.** The finite
proof is not an assertion about every possible computed address or control-flow
alias. Missing source observer/caller contracts still prevent claiming a
complete reachable initializer. The positive resource/API evidence below
supplies the owner's bounded justification. No standalone placeholder helper
was implemented; the original entry itself performs both ordered updates.

This separates two questions: proving a native storage operation can preserve
and persist four bytes, and proving that the reachable game uses the correct
representation at every relevant source access. Global source deadness is
not a prerequisite for the former and is not claimed for the latter.

## Selected cartridge backend and current candidate compatibility

The earlier [EEPROM storage report](shoot-eeprom-storage.md) already establishes
the selected backend. This review reuses its `contracts()` and `census()`
checks directly, without running its frozen-v53 entry point or changing its
output. Both functions passed on all three exact inputs:

| Input | SHA-256 |
| --- | --- |
| Retail USA GBA, 4 MiB | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |
| Port-only predecessor, `build/stage-priority-routing-20261023-a/current-candidate.gba`, 8 MiB | `389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1` |
| Current v63, `build/repro-v63-20261026-a/current-candidate.gba`, 8 MiB | `4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC` |

Boot `08000280` passes 4 to `0837DADC -> 0837D5EC`, selecting descriptor
`083877D0`: **512 bytes / 64 eight-byte blocks / six protocol address bits**.
The configuration is selected by executable instructions, not inferred from
the `EEPROM_V122` marker or from a save file's length. The unused alternative
descriptor at `083877DC` describes 8192 bytes; its presence does not mean that
the running program selects that geometry.

Reader `0801FCA8` and writer `0801FC5C` initialize block index zero and count
25. They transfer RAM `03001120..030011E7`, advancing by eight bytes each time.
The payload is offsets `00..BF`, checksum `C0..C3`, and transferred tail
`C4..C7`. Checksum helper `0801FD0C` sums exactly the first `C0` bytes.
Therefore bytes `C8..CF` are within selected capacity and outside these
record transfers. This is a bounded transfer exclusion, not a global free-space
declaration.

The complete record/reset region `01F894..01FD30` is unchanged in all three
inputs, SHA-256
`A29BE760B3E28AE415F2C617E2EA53FE820BF625D63C7E17857377BA8E1247E0`.
The native library `37D5EC..37DA06` is also unchanged, SHA-256
`C80BD60510C782EC1B094D909010A44C8157607A8BBFB6723DECE7A64BEA2C64`.
Every additional dependency interval in the earlier analyzer's `RANGES`
also matched retail. No language or later port layer expanded these transfers.

## Complete consumers within the inspected API boundary

The existing census scans every aligned ARM B/BL encoding, halfword-aligned
Thumb BL encoding, and byte-aligned pointer representation for its declared
entries across each complete input. Its exact populations remain unchanged:

| Operation | Entry | Encoded caller or function-pointer binding |
| --- | --- | --- |
| Select geometry | ARM `0837DADC` -> Thumb `0837D5EC` | Boot `08000284`; veneer literal `0837DAE4` |
| Select timer/IRQ | ARM `0837DAE8` -> Thumb `0837D65C` | Boot `08000290`; veneer literal `0837DAF0` |
| Write with verification/retry | ARM `0837DB54` -> Thumb `0837D9C8` | Record loop `0801FC7C`; veneer literal `0837DB5C` |
| Read one block | ARM `0837DB60` -> Thumb `0837D7E4` | Record loop `0801FCC0`; veneer literal `0837DB68`; internal verification call `0837D998` |
| Low-level block write | Thumb `0837D894` | Retry wrapper `0837D9E2` only |
| Compare one block | Thumb `0837D970` | Retry wrapper `0837D9F2` only |

The last three functions do not invent a new block index: verification and
retry forward their caller's index. Thus the known native record readers,
progress saves, reset path, and existing language commit all remain bounded
by the actual record loop when they use these entries. There is no current
encoded caller to the inspected public API that requests block 25.

The error ABI has useful concrete limits:

- `0837D7E4` rejects an index outside the selected block count with `80FF`.
  Otherwise it reads eight bytes and returns zero. There is no checksum or
  independent data-validity result for a new private block.
- `0837D894` consumes exactly four input halfwords. Its out-of-range status is
  `80FF`; its busy-timeout status is `C001`.
- `0837D970` compares all four halfwords; mismatch returns `8000`.
- `0837D9C8` makes at most three write/verify attempts and returns the status
  of the attempt that succeeded or the last failed attempt. Zero means the
  readback matched the supplied eight bytes.

## Direct-MMIO ownership limit

The earlier API census alone is not a complete proof of all physical EEPROM
access. This follow-up additionally scans byte-aligned pointers and encoded
ARM/Thumb branches to all ten inspected initialization/read/write entries,
with both pointer state bits and the `08/0A/0C` ROM mirrors. Retail and v63
have the same four veneer pointers and seven branches in the table above;
there are no additional mirror bindings. This closes that finite alias gap.

A supplemental, read-only finite scan was made to avoid silently promoting
the API result to a stronger claim. It covers ARM immediate MOV values and
ARM PC-relative word loads, Thumb PC-relative word loads, and adjacent Thumb
MOV-immediate/LSL constructions whose resulting value is in `0D000000..0DFFFFFF`.
The full retail input has 15 matching encodings; v63 has 16. Three are the
positively decoded native EEPROM constructions at raw `37D836`, `37D916`,
and `37D930`. All other 12 retail / 13 current matches are classified below
using actual owners and operand flow, not the appearance of their bytes.

### Character tile owners

Each listed P0 is selected by the actual canonical resource row. Its P1
command selects the descriptor index; descriptor `+0` is its byte extent and
`+4` is its ROM payload. The complete payload of every one of the seven
descriptors was independently converted back to WSC bitplanes and matched
the listed source bytes exactly.

| Encoding position(s), raw | P0 / descriptor index / descriptor raw | Native payload, half-open | Actual P1 event:frame / command raw | WSC1.5 pixel source |
| --- | --- | --- | --- | --- |
| `19C724` | `1889B0` / 164 / `18CCA8` | `19C6C8..19C848` | `60:0` / `186CF0` | `04F320` |
| `1A85FC` | `1889B0` / 282 / `18D058` | `1A84A8..1A86A8` | `104:0` / `1879A0` | `07B140` |
| `1AF7E0` | `1889B0` / 349 / `18D270` | `1AF608..1AF808` | `125:9` / `188190` | `2EAE40` |
| `1B1648, 1B164C, 1B1650, 1B1654` | `1889B0` / 364 / `18D2E8` | `1B1428..1B1768` | `128:20` / `188530` | `2ECC60` |
| `32B048` | `31CA58` / 39 / `320040` | `32AD78..32B1D8` | `5:2` / `31BFB4` | `1CAB00` |
| `333B72` | `31CA58` / 72 / `320148` | `333B38..333F78` | `29:3` / `31C5D4` | `233BC0` |
| Current-only `473D90` | `448000` / 315 / `44C940` | `473C80..473F60` | `115:5` / `614FC8` | `2874A0` |

The first four descriptors belong to base ID4, current row `4A8178`; that
whole row equals retail row `0D3FB8+4*32`. The next two belong to evolved ID9
(also reused by ID10), current row `60B120`; it equals retail row
`0D3FB8+33*32`. The final descriptor belongs to the added base ID12, current
row `4A8278`, source record 12. Source P0 headers are respectively
`30C560`, `333360`, and `29B8A0`.

The actual renderer is unchanged in v63. `08012C8C..08012CA0` loads P0 from
presentation `+48`, reads its descriptor table, adds the selected index times
eight when flag 2 is set, and loads the payload pointer. `08012D50..08012D94`
adds the selected tile byte times 32 and copies eight words into the staging
buffer rooted at `02000000` (`08012C74/78`). Those pixel words are copied as
data; they are not loaded into a bus-address register or called as code by
this consumer. Full unchanged renderer range `12C58..12DC8` has SHA-256
`7FA5B38C660FB9474B82461F2739D5C0AC93411B7681B59E762672ACE3DDE6F6`.

### Background map owner at `065C28`

The candidate encoding is inside the 504-halfword map `065954..065D44`.
Descriptor `040954` is `00000101,08065954`; it is the fourth entry of the
four-map descriptor view `04093C..04095C`. Retail dimension row 12 at
`07FA00`, and its unchanged v63 copy at `580120`, both select that view with
dimensions `2,2`. The actual initializer `0803FD94..0803FDA8` passes row 12
and the dimension table to `08013BF8`. Its table literal `03FEC0` is
`0807F8E0` in retail and the reviewed relocated table `08580000` in v63.

`08013BF8..08013C1C` selects the 24-byte row and stores its descriptor view
at background object `+24`. The actual map-fill call `0803FDCC..0803FDE8`
passes width 28 and height 18, with VRAM destination `0600F800` set at
`0803FDB0..0803FDB8`. `08013C98..08013CC4` reads the selected map pointer and
copies map halfwords through `080110DC`, rather than executing map entries.
The source inversion of **all 504 map cells** matches the unique WSC1.5
payload at raw `4B4D90`. The native map is unchanged in v63, SHA-256
`2A236C8D2C4F860803AB212C5B9D3C5FCE45ED4AF809255376CBAC829B53D607`.
This establishes the map's data ownership; it is not a runtime claim about
which camera position has displayed its fourth map.

### PCM owners at `38021C` and `380FDC`

Voicegroup `0837E8E0` has 12-byte voice records. Voice `23` at `37EA84`
points to wave header `37FEFC`; voice `25` at `37EA9C` points to `380CBC`.
The wave headers' `+C` lengths are respectively `B03` and `864`, giving
sample spans `37FF0C..380A0F` and `380CCC..381530`. Both candidate encodings
are at sample offset `310`, inside those declared signed-byte PCM payloads.

These are actual selected voices. Native song `3D`, header `387274`, track
`387264`, executes `BD 23` at `387268`; song `5A`, header `3877B8`, track
`3877A8`, executes `BD 25` at `3877AC`. Their complete table rows at
`37FE08` and `37FEF0` are preserved in v63's song table `683200`.

Song start `0837C930/32` installs the song's voicegroup at player `+30`.
The actual BD handler at `0837BAE0` is bound by dispatch word `37DC00`
(entry `BD-B1` in table `37DBD0`). It multiplies the voice index by 12 and
copies the three voice words into track `+24/+28/+2C`. The note path at
`0837C028/2A` transfers voice `+4` to channel `+24`. Mixer
`0837B67A..0837B6BA` obtains that wave header, uses header `+10` as the first
sample and header `+C` as its count. Actual mixing uses signed-byte loads,
including `0837B8C8/CC`, and arithmetic into its output buffers. It does not
interpret the sample bytes as instructions or addresses.

The wave data, voice records, BD handler, song-start body and inspected mixer
are byte-identical between retail and v63. The two complete wave spans,
including headers, have SHA-256 respectively
`26F557680FCEC5034D7E6EEA8182FBD3D6ED6F9284BB736AE903D3C66CFD8128`
and `6BCCC4F0809E22B8E9422CE824944B3BE312F9B254E0D6D1EF822B525CE978DB`.

### Actual EEPROM paths remaining in this finite population

| Address construction | Actual use and arguments under selected six-bit geometry |
| --- | --- |
| `0837D836/38`, `r4=0D000000` | `0837D846`: DMA stack read-command -> EEPROM, 9 halfwords; `0837D850`: EEPROM -> stack, 68 halfwords, then unpack 64 data bits after the four dummy bits |
| `0837D916/18`, `r1=0D000000` | `0837D924`: DMA stack write-command -> EEPROM, 73 halfwords, containing the checked block index and four input halfwords |
| `0837D930/32`, `r1=0D000000` | `0837D938/46`: read one halfword and inspect ready bit 0 while waiting for completion/timeout; it does not select another block |

An additional complete branch/pointer scan finds exactly three callers of
the DMA helper `0837D764`: `0837D846`, `0837D850`, and `0837D924`. Timer start
`0837D698` has only caller `0837D92A`; stop `0837D720` only `0837D952`.
There are no exact pointer representations for those three helpers, including
both state bits and the three ROM mirrors. Retail and v63 agree.

The block index is checked before command construction and comes from the
unchanged `0..24` record loops through the complete named API caller set.
Consequently this finite access population has no block-25 read or write.
All 13 non-library address-pattern candidates are accounted for by positive
data consumers, with no independent EEPROM protocol identified.

The remaining gap is **unrecognized computed aliases**, such as a bus address
assembled by a longer arithmetic sequence or loaded through a mutable RAM
pointer, or control entering an unexamined routine interior. Neither these
finite scans nor positive data ownership prove arbitrary such behavior absent.
The conclusion is bounded ordinary-native ownership, not protection against
corrupted program state or a claim of a whole-program formal proof.

## Conditional four-byte owner and lifecycle

The narrow proposed identity is:

| Source identity | Proposed native identity |
| --- | --- |
| `1000:3CD8` | Native API block 25, buffer halfword at `+0` |
| `1000:3CDA` | Native API block 25, buffer halfword at `+2` |
| No new source identity | API buffer bytes `+4..+7` retained byte-for-byte |

The earlier `C8..CF` range labels are API record coordinates, not a claim
about raw serialized save-file byte order. Native reads assemble wire bits
into buffer halfwords `+6,+4,+2,+0`; the write protocol correspondingly
serializes the buffer in reverse word order. The API-coordinate binding is
unambiguous and requires no save inspection.

Preserving the other four bytes avoids assigning them invented padding
semantics. It does **not** establish that the first four bytes have no other
owner. No current contents, initial zero value, validity tag, or migration
from an existing save are assumed.

A separately verifiable helper can have this explicit contract:

1. Preconditions: native EEPROM initialization completed; the call runs in
   the normal serialized main-task context; the native DMA/timer/IRQ service
   is available and no EEPROM operation is already active.
2. Read the proposed block into eight bytes of temporary stack storage through
   `0837DB60`. Return a nonzero read status without calling the writer.
3. Change only the selected source halfword, or the pair for an explicitly
   defined pair-clear operation. Retain every byte outside that update.
4. Pass the same full block to `0837DB54`. Return its status in `r0`; preserve
   the remaining registers and SP according to the surrounding scene ABI.
   Do not hide a failed write by restoring an incoming `r0` over the result.
5. A corresponding reader uses the same block and offsets. It returns the
   read status separately from the value and must not invent zero on failure.

The two actual source stores occur at raw `747CE2` then `747CE9`. An interface
that supports each ordered halfword update avoids requiring an early decision
to merge them. Whether the eventual initializer may use one pair-clear is a
gameplay-observer/order question, not a demand for cycle-exact cartridge timing
or additional power-loss guarantees. No such extra guarantees are claimed.

The persistent owner is the dedicated cartridge representation, **not a task
or fighter object**. The source lifetime is not bounded by the temporary scene
task. Native retirement `08012030 -> 08011BE4` clears the allocated status at
task `+10`; allocation `08011AC4` reuses free slots with stride `118`.
The [scene/pool proof](shoot-scene-object-pools.md) establishes survival of
players in pools 3/4 and the auxiliary in pool 5 through one cleanup, but it
does not give any of them cartridge persistence. The scene's callback can own
commit control and continuation; task data cannot replace the persistent state.

The earlier proposed requirement to stop on a nonzero status was a stronger
commit-confirmed contract, not an established source requirement. Source
`73E2/73E9` uses ordinary MOV stores, and caller `773143` continues without a
storage-status branch. The selected implementation uses the existing bounded
native retry service under a functional-storage precondition, preserving the
original register ABI without a new error/retry scene state. Failed-device
data equivalence is an explicit limitation. Should a future interface promise
commit-confirmed progression, its retry must target the storage step rather
than replay earlier object construction; that stronger interface is not added.

Later scene retirement must not erase this representation. Likewise, the
inspected ordinary native reset only transfers blocks `0..24`; it does not
initialize or clear the proposed block. A future source observer before the
first Shoot clear, or after a scene exit/restart, needs an explicit mapping
and initial-value contract. The existing
[SRAM boundary](shoot-sram-boundary.md) and
[segment-lineage](shoot-sram-lineage.md) reports do not close that observer set.

## Native service effects and remaining adoption gates

The operation is synchronous. Its DMA helper `0837D764` uses DMA3 registers
`040000D4/D8/DC`, temporarily clears/restores IME, and sets the EEPROM wait-state
bits of WAITCNT from the selected descriptor. The decoded routine does not
restore the old WAITCNT value. Busy polling uses timer 2, selected at boot with
IRQ slot `030000F0`. The timer helpers use shared native state
`030053A0..030053AD` and configuration pointer `03006CD0`; they are not reentrant
private storage. The stop helper disables its timer interrupt bit and restores
saved IME. These are existing backend effects, not proposed extra writes.

Therefore the implementable unit is a conditional storage operation, with its
status and service preconditions exposed. It need not wait for a global
dead-store proof. Making it a reachable game component still requires:

- The physical binding is now adopted under the finite access/entry-alias
  boundary above, retaining its explicit computed-alias limit. The allocation
  follows the positive owner evidence, not merely the record's byte extent.
- Actual source readers/writers translated to this identity, including their
  initialization, ordered access, and post-scene lifetime where relevant.
- A complete source-ordered scene continuation with native service ownership.
  The selected bounded backend policy does not require an invented scene error
  state; any later stronger success guarantee would need its own contract.

## 2026-11-03 source bank and failure-policy discrimination

Exact source footer `EAFC06FF4F0001003000080204003E44` has SRAM code `02` at
raw `7FFFFB`. The primary header decoder and memory implementation at Beetle
WonderSwan revision `4b01295838ea89e3f1355bbe4cb5cf98aa6108cd` give 32 KiB
and backing address `((linear & FFFF) | (C1 << 16)) & 7FFF`.
All 256 C1 values therefore preserve the two store identities and their upper
aperture aliases. The new builder checks all 2,048 byte/alias/bank cases.
See the pinned [header decoder](https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/libretro.c)
and [memory implementation](https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/mednafen/wswan/wswan-memory.c).
This closes the C1 identity question for the standard retail cartridge model,
not observer closure or initial state. The source SRAM cannot be collapsed
into the distinct IRAM regeneration timers.

Native `0801FC5C` returns its failed write status, and `0801FBD0` propagates
it. Higher ordinary retail callers at `0808B390`, `080C07C8`, `080C0ED0` and
`0833EE04` instead pop the incoming r0 without checking the result. The two
record writes at `0808B378/0808B390` likewise have no intervening status test.
This establishes an existing bounded backend policy, without pretending that
the low-level wrapper itself discards errors. The current Options-language
callers `08633640/0863383C` do inspect r0 and retain their own error state;
that separate behavior is preserved unchanged.

The implemented layer performs separate RMW operations for source `73E2`
and `73E9`, rereading before the second update. Its first 24 entry bytes,
ordinary regeneration timers, all previous phase components, and every byte
outside `[629818,629880)` remain unchanged. The candidate is
`66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF`;
the linked implementation record contains exact writes, stack, assumptions,
reproduction and the remaining independent-verification status.

No current ROM behavior, source observer closure, hardware timing, fresh-save
persistence, or failed-device gameplay was tested by this review. The existing
runtime work and full Shoot initializer gate remain open.
