# Bounded original Shoot DI observer

New `tools/bizhawk_observe_wsc_shoot_di_v3.lua` installs observation hooks only.
It does not choose input, advance frames, launch a core, write guest state, or
read a save file. The caller owns the authorized save-copy launch and its
provenance. Frozen collector2AD5BB33 and lifetime observer0CC9B17C are unchanged.
No actual Shoot entry or terminal observation is claimed by this preparation.

The caller supplies userdata `output` (fresh W:/build/... directory),
`callback_order="bizhawk2111-rew"`, and `source_sha256` equal to the exact
C415F227 original hash. `dofile` returns `status()` and `finish()`; the caller
must call `finish()` when observation ends. Status separately reports observed
terminal entry and completed final-IRQ operand pairs, so a run with zero hits
cannot silently count as successful Shoot observation.

## Source and core binding

Original bytes75FC8C..A2 pin the final callback prologue, `MOV AX,ES:[DI+A]`
at75FC98 and `OUT10,AL` at75FC9C. The prologue sets ES0300 but leaves DI intact.
At the pre-instruction execute callbacks, V30 fetch has already incremented PC.
Each site checks the callback bus address and physical PS:PC equals site+1.
The paired post additionally requires the same PS, PC=prePC+4 modulo65536,
and unchanged ES/DI. The latter PS/PC check was added after independent review
identified that physical-site checks alone permit different segment aliases.

Official BizHawk2.11.1 source resolves the important distinctions:

- [Managed register/callback binding](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Emulation.Cores/Consoles/WonderSwan/WonderSwan.cs)
  exposes native enum register names, declares System Bus as a callback scope
  rather than a memory domain, and supplies zero callback values. These zeros
  are not operand data.
- [Native V30 implementation](https://github.com/TASEmulators/BizHawk/blob/2.11.1/wonderswan/v30mz.cpp)
  binds DS1 to ES and IY to DI. Prefix26 selects DS1; addressing mode45 uses
  IY plus signed byte displacement0A, truncated into16-bit EO before the
  segment base is added. Opcode8B then reads the word into AW.
- [Word/fetch macros](https://github.com/TASEmulators/BizHawk/blob/2.11.1/wonderswan/v30mz-private.h)
  increment the physical address for the high byte, without another16-bit
  offset wrap. [Read20 mapping](https://github.com/TASEmulators/BizHawk/blob/2.11.1/wonderswan/memory.cpp)
  masks the bank to four bits and selects RAM or SRAM backing. With ES0300,
  every possible operand byte lies in03000..13000; for32KiB SRAM the C1 bank
  contribution is masked away, leaving backing offset physical&7FFF.

The observer therefore records physical20-bit addresses plus explicit backing
domain/address/byte peeks. It does not pretend to read a nonexistent System
Bus domain. After the MOV, it records actual AW and AL and requires AW to equal
the two-byte pre-read value. A mismatch is logged before failing closed.

Important boundaries: DICFF5 reads physical0FFFF/10000 across RAM/SRAM;
DID000 reads1000A/1000B; DIFFF5 reads12FFF/13000, while DIFFF6 wraps the
effective offset and reads03000/03001. Seven embedded address selfchecks also
cover generic20-bit wrapping, independently of the live ES0300 restriction.

## Bounds and verification

Exactly four fixed execute callbacks observe frame-wait calibration750EBD,
first terminal773650, pre75FC98 and post75FC9C. Only stage11 operand pairs are
recorded. Logging stops after512 complete pairs; no dynamic address callbacks
or full-bus logs are installed. RAM/SRAM snapshots are limited to the first
terminal entry and first16 distinct ES:DI pairs, at most34 files. `finish()`
rejects a pending unmatched pre-hook and makes all callbacks inert.

Author validator `tools/verify_wsc_shoot_di_v3.py` runs the actual Lua in the
local lua54 library with explicit read-only mocks, never an emulator. It pins
the original instructions and seven downloaded official core files. The report
`build/wsc-shoot-di-v3-20261109/author-qa.json` passes512 paired reads, seven
boundary selfchecks,14 invalid scenarios and eight deliberate code mutations.
The scenarios include absent/incorrect calibration, orphan/repeated hooks,
wrong operand registers/value, bad source/domain, existing output and pending
finish. Mutations reject64KiB aliasing, high-byte offset rewrap, SI-for-DI,
RAM-for-SRAM, skipped AW verification, excess pairs/snapshots and lost PC checks.
This validates observer behavior under mocks, not gameplay reachability.

Author-tested observer SHA256:
`BD01DF5A399D5D33B9859BBC484F0068B6E6406EFCD7DAAD07AB7AF38DD0E15B`.
Independent execution QA is owned separately; integration/runtime remain with
root. No frozen ROM/main/input policy or save was changed by this task.
