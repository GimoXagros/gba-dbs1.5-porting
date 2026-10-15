# Native EEPROM backing-store option

Recorded 2026-10-15 against checkpoint `09c92e0` and the unchanged v53 ROM
`455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48`.
Only ROM files were read. No save file, emulator, or CPU was accessed, and
no ROM layer or physical EEPROM operation was produced by this analyzer.

The result supplies a concrete storage option for the required source
`ES1000:3CD8/3CDA` stores. It does **not** close the separate question of
which source readers must use that representation. It leaves both earlier
SRAM reports and every frozen build layer unchanged.

## Actual allocation and API

Retail boot at `08000280` passes `4` to `0837DADC`, whose Thumb target is
`0837D5EC`. The selected descriptor at `083877D0` specifies 512 bytes,
64 eight-byte blocks, and six protocol address bits. This is a positive
capacity selection by the running program, not a guess based on the
`EEPROM_V122` string.

The ordinary record writer `0801FC5C` and reader `0801FCA8` each initialize
their block index to zero and loop exactly 25 times. The transfer pointer
starts at RAM `03001120` and advances by eight bytes. The payload checksum
helper `0801FD0C` sums exactly `C0` bytes; the writer places its four-byte
sum at record offset `C0`. Four trailing bytes at `C4..C7` are transferred
but are outside that checksum's input. Their previous semantic identity is
not assigned by this report.

| Range | Proven current role |
| --- | --- |
| EEPROM bytes `000..0BF` | Native record payload |
| EEPROM bytes `0C0..0C3` | Payload checksum |
| EEPROM bytes `0C4..0C7` | Transferred record tail |
| EEPROM bytes `0C8..1FF` | Outside these record transfers; within selected physical capacity |

The existing write entry is ARM `0837DB54`, an interworking veneer to
Thumb `0837D9C8`. It takes `r0=block index`, `r1=at least eight readable
bytes`, and returns a 16-bit status in `r0`, with zero indicating success.
Its low-level writer consumes exactly four halfwords from the input. The
wrapper attempts a write followed by an eight-byte readback comparison,
with at most three attempts. It returns a nonzero status for failure;
there is no justification for silently discarding that result. Caller-saved
registers must be preserved by an adapter as required by its scene ABI.

The matching read entry is ARM `0837DB60`, targeting Thumb `0837D7E4`, with
the block in `r0` and an eight-byte writable destination in `r1`.

Boot selects timer 2 for the EEPROM helper and supplies IRQ slot
`030000F0`. The helper uses that established native timer/IRQ backend while
waiting for the device. A new call therefore has synchronous wait and
error behavior; it is not an ordinary constant-time RAM halfword store.

## Bounded caller closure

The analyzer scans the complete commercial ROM and the complete v53
candidate for aligned ARM B/BL encodings, Thumb BL encodings, and
byte-aligned function-pointer representations of these actual APIs. In
both files the write veneer has only caller `0801FC7C`; the read veneer has
only caller `0801FCC0`. The lower-level Thumb read, write, and verification
calls remain inside the inspected library. Neither later port layers nor
the native record path address block 25 through these APIs.

This denominator does not prove the absence of arbitrary computed jumps or
an independent, manually implemented EEPROM protocol. Its concrete scope
is the selected native backend and every encoded reference to the inspected
entry points. The exact dependency bytes are unchanged in v53 and pinned
in the report.

## Feasible representation and adoption gate

Reserve one eight-byte block, index `25` (`19` hex), at EEPROM `C8..CF`.
Its first four bytes can represent source physical `13CD8..13CDB`; the
other four bytes would be explicitly owned padding. A constant eight-byte
ROM input allows the two zero stores to be committed by the existing
writer without allocating persistent RAM or modifying the ordinary
record's 200 bytes. This is a physical allocation with a bounded existing
backend, not a new generalized memory or save framework.

The representation remains a **proposal**, because adopting it also
requires:

- A defined scene response to the writer's nonzero status and synchronous
  wait, using the established EEPROM timer ownership.
- Translation of any actual source observer to the same representation.
  Writing backing bytes alone does not translate such a reader.
- An explicit contract for the four native padding bytes and the
  difference between source halfword writes and native block persistence.
  No power-failure atomicity or cross-platform timing equality is claimed.

Reusing `C4..C7` inside the existing record is less isolated: immediately
persisting those bytes would share an eight-byte block with the checksum,
or require saving unrelated progress. That option is not recommended here.
Mapping the source words to native regeneration timers `030048AC/AE`
remains disproved by the [lineage counterexample](shoot-sram-lineage.md).

## Exact source observation target

For an isolated source-ROM runtime check, monitor SRAM backing offsets
`3CD8..3CDB`, including bus aliases `13CD8..13CDB` and `1BCD8..1BCDB`
under the cartridge's 32 KiB mask. Keep IRAM `FCD8..FCDB` separate: those
are the ordinary regeneration timers. Expected Shoot writes occur at
`CS:IP=4090:73E2` and `4090:73E9`, raw `747CE2/747CE9`.

Capture access kind, CS:IP, DS/ES, BX/SI/DI, C1, and the current task
callback from initializer `7168` through scene `155F`, active gameplay,
terminal `1750`, and the following normal stage/menu/save path. Any source
read is direct evidence for a missing observer. An absence of reads is
limited to the exercised route. The supplied user save remains unopened;
an isolated fresh synthetic save can support this observation.

## Reproduction

```powershell
py -3 tools/analyze_shoot_eeprom_storage.py `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  build/repro-v53-20261013-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  --output build/shoot-eeprom-storage-20261015/analysis.json
```

Report SHA-256:
`472D5844A37CFEB1C6D557DFD0F860BFE66D2353E0135DD1D9AB6F9359B78660`.
Seven semantic mutations are rejected: boot protocol selection, physical
capacity, native record extent, checksum extent, write veneer target,
retry count, and writer input extent. The report explicitly leaves
`policy_adopted`, `source_observer_translation_closed`, and
`full_initializer_gate_closed` false.
