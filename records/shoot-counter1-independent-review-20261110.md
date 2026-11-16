# Counter1 observer: independent fresh-cycle review

**PASS** for wrapper `053FD747...` and host `D7D1627B...`. This is a read-only
preflight gate; no emulator was launched by this review.

The original C625 observer had a reproducible evidence gap: actual Lua54
accepted first comparison in core69937 followed by all eight matches, stores
and final callback in core69938. Ordinary one-frame advancement assertions
still passed. The frozen original and its author report were preserved.

The new v2 wrapper composes that exact original with seven additions: six
target-event hooks require the target's core to equal the current core, and
the pending store also requires its comparison core to match. Independent
actual Lua composition verifies the entire effective body `EA950EF5...`.
The cross-frame example is now rejected; all six existing affected routes
still pass. Every CPU callback uses scalar reads and buffered log entries;
bulk memory, files and States remain outside callbacks. Input is entirely
neutral, with a200-frame bound and100-record cap.

The host differs from frozen7A52 only by the new wrapper path/hash and a
pre/post pin on the original wrapper that it reads. Its read-only prefix
validated the genuine69935 checkpoint, exact decompressed Core
`32A904634D2E9F941853496BE03431EBE276234A1C7E28A9DAD3129387C05583`,
all five embedded RAM regions, source inventory and the280D ROM. The prefix
was stopped before output-directory creation or process construction.

Actual ARM execution of C4C for256 independently differing DISPSTAT/VCOUNT
values confirms the helper reads DISPCNT-adjacent **DISPSTAT at04000004**.
The IRQ then takes its high byte, subtracts8 and masks to8bits. Actual VCOUNT
at04000006 is a separate observation. The probe requires a fresh75C→74D8
selection/initialization, first programmed compare≤1 at actual VCOUNT≤9,
then eight matches/stores and the final callback in the same target core.

| Item | SHA-256 |
|---|---|
| Independent verifier | `493F92BB92E933ABD1D3B09FABFB2C46FE0F14326408E5B24A8B0659A45914B4` |
| `build/shoot-counter1-independent-review-20261110/report.json` | `401AD2150307FABC1FD3866098241448B103246E863F877B50EEB2D9BEB7D5BC` |
| v2 wrapper | `053FD747027B9B5ED68769643EBA138BB5313249DFBAC4384427375F6F4F64A6` |
| v2 host | `D7D1627BF2B0CCAD089C3128F764D7953D466BAD499B124DA0F1A965D632735D` |

The host records raw whole-Core equality and every byte difference after
restoration; its required assertions cover CPU bank, native extensions,
managed suffix and all five RAM dumps. This review does not preclaim whole
Core equality, actual first-counter timing, or terminal completion. Those
require the subsequent root-owned capture and its audit.
