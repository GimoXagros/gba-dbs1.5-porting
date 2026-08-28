# GBA stage runtime and Ver. 1.5 stage assets

## Evidence boundary

The GBA observations use the exact USA retail ROM.  WSC asset classifications
use the clean Ver. 1.5 ROM and direct planar-tile rendering; the supplied SRAM
is not involved.

## Retail GBA dispatch

The battle setup routine at `0x0803EE08` obtains a stage index and dispatches
through the eight-entry ARM function table at ROM offset `0x03F038`.  The
dispatch instruction at `0x0803EEC4` loads `table[index]` and branches to it.

| Stage index | Initializer | Primary palette(s) | Primary tile payload |
|---:|---:|---:|---:|
| 0 | `0x0803F1C4` | `0x01FFAA`, `0x02008A` | `0x020168` |
| 1 | `0x0803F51C` | `0x02416A` | `0x024248` |
| 2 | `0x0803F734` | `0x02824A` | `0x028328` |
| 3 | `0x0803FBB0` | `0x02C32A` | `0x02C488` |
| 4 | `0x0803FD30` | `0x03048A`, `0x03056A` | `0x030648` |
| 5 | `0x0803FEF0` | `0x03464A`, `0x03472A` | `0x034808` |
| 6 | `0x08040080` | `0x03880A` | `0x0388E8` |
| 7 | `0x08040334` | `0x03C8EA` | `0x03C988` (plus stage-specific data at `0x03E608`) |

The first initializer establishes the shared ABI.  It copies a palette to
palette RAM, copies a `0x1000`-unit primary graphic payload to `0x06004000`,
and then creates four background objects using the common support resource at
`0x0807F8E0`.  Later initializers reuse that ABI and add stage-specific state
or effects.  The GBA ROM therefore has a real fixed eight-stage population;
adding graphics without expanding or replacing the dispatch path cannot make
the three Ver. 1.5 stages reachable.

## Corrected Ver. 1.5 resource boundaries

Direct WSC planar rendering separates all three added arenas:

| WSC range | Classification | Converted GBA geometry |
|---:|---|---|
| palette `0x430000`, tiles `0x4300E0`, maps `0x435000` | Locomon/train arena | Sixteen direct 28×18 maps grouped as four 2×2 resources |
| palette `0x4C0000`, tiles `0x4C0160`, maps `0x4C60E0` | Iraira Room | Retail stage-3 palette/tiles reused exactly; eight added maps grouped as two 2×2 resources |
| palette `0x4D0000`, tiles `0x4D00E0`, maps `0x4D40E0` | Pichipichi/PetiPeti Falls | Six meaningful maps grouped as two independent 1×3 resources |
| palette `0x490000`, tiles `0x4900E0`, maps `0x495000` | Digimon Shoot | Eight direct 28×18 maps grouped as two 2×2 resources; dedicated mode logic is not yet ported |

The commercial GBA converter retained WSC 28×18 maps (`0x3F0` bytes each),
not cropped 32×32 maps.  WSC tile-bank 0 is preserved as GBA indices
`0x000..0x1FF`; tile-bank 1 is rebased to `0x200..0x3FF`.

Exact static correspondence for all eight retail GBA stages is recorded in
`evidence/stage-tile-version-map/all-stages.json`.  That correspondence
invalidated the earlier assumption that banks `0x4B` and `0x4C` were wholly
new; both contain relocated retail content.

## Internal stage build v21 boundary

`build/stage-integrated-v21.gba` (internal only; SHA-256
`5E37F8C69F17B5067CAA6E004168F797F0E0E4A6B829C9F250D10B05A1B73F6F`)
contains the corrected arena resources, twelve-entry initializer and update
dispatches, temporary character routes for the three battle stages, and exact
Ver. 1.5 spawn records. The new IDs are also bounded at each currently
confirmed legacy stage-index consumer:

- the fighter spawn table is expanded to IDs 8–10;
- the 16-byte auxiliary selector table is expanded with the Ver. 1.5 record;
- legacy setup/bounds tables see safe analogs (train→0, waterfall→6,
  Iraira→3, Shoot→7) without changing the actual battle-state stage ID.

The Ver. 1.5 update-function overlay proves the appended ID order is
train=8, waterfall=9, Iraira Room=10, followed by Digimon Shoot=11.  Its first
eight function pointers preserve the original WSC population, and the spawn
table appends the same three records in that order.  This supersedes the
earlier provisional 9/10 assignment.

The train display/scroll/palette path, the shared waterfall/Iraira display
callback, both palette paths, and the waterfall three-phase rolling-hazard
state machine are translated statically from the confirmed WSC routines. Its
state word is GBA `0x0300256A`: WSC `ES:0384` is the second halfword cleared
from base `0x03002568` by the commercial stage-5 initializer at
`0x0803FEF0`. The hazard state machine reuses the retail GBA entity table and
spawn service rather than a parallel object system. Its mode-producing
visual/movement callbacks are pending. The two commercial GBA object-construction sites
corresponding to WSC raw `0x781BEF` and `0x786C5C` now preserve the Ver. 1.5
exception that suppresses default object flag `0x2000` for stages 9 and 10.
This is a confirmed engine prerequisite, not by itself proof of vertical
motion or suction. Train vent/bounce producers, Iraira suction, Digimon Shoot
mode logic, and any additional stage-specific engine branches remain pending.

An aligned ARM branch audit found all twelve direct calls to the retail stage
getter at `0x080D1C78`. Six callers immediately index an eight-entry retail
table (`0x080C4BC4`, `0x080C4CC8`, `0x080D0BD0`, `0x080D1408`,
`0x0836D28C`, and `0x0836D2F8`). v21 routes four still-unported consumers
through a bounded analog selector and separately bounds the setup-time
dimension lookup at `0x0803EE70`.

The consumer at `0x0836D2F8` uses a native twelve-entry movement-pattern table. The
commercial GBA conversion proves that each WSC four-byte record `(count, 4,
near pointer)` becomes an eight-byte `<halfword, halfword, ARM pointer>` record
while its referenced `0x20`-byte pattern is retained byte-for-byte. The build
verifies this rule against all nine records present in both commercial ROMs,
then converts Ver. 1.5 records 9–11 and their three patterns.

The consumer at `0x0836D28C` now indexes a relocated twelve-entry object
configuration table. Direct comparison proves a second conversion rule: each
WSC entry `(resource bank, near pointer)` becomes `<32-bit bank, ARM pointer>`,
and each 16-byte WSC object record becomes 20 GBA bytes by retaining its first
14 bytes, adding two zero pad bytes, and expanding the callback-table pointer
to 32 bits. The build verifies this across stages 0–7. Stage 8 uses the native
records at WSC physical `0x745081..0x7450A0` and static ARM translations of
callbacks `4090:3CD5` and `4090:3D7B`. They reproduce the two directions,
signed position thresholds, velocity changes, animation cadence, and destroy
conditions using the ABI established by the commercial callbacks at
`0x0836D8B4`, `0x0836D9C8`, and `0x0836DADC`. Entries 9–11 remain labeled
temporary analogs rather than being claimed as native.

The v20 claim that waterfall stage 9 directly seeds mode 3 from
`4090:3FCA` was incorrect and is removed. The WSC stage configuration pair at
physical `0x7450A1` instead references callback tables `0x481F` and `0x4821`,
whose functions `4090:3DFB` and `4090:3EE0` produce modes 1 and 2. Those actual
callbacks, not the unrelated mode-3 behavior, are the remaining native port
targets.

No emulator claim is attached to v21. Per the requested validation policy,
runtime QA is deliberately deferred until the remaining port systems are
integrated into one final candidate.
