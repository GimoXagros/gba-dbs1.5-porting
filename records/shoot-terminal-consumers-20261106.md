# Terminal common-tile consumer bounds — 2026-11-06

The fixed P1 graphics consumer occupies source common tiles 1..52 in base form and 1..72 across base and evolved forms, including every animation and alternate graphics bank. Therefore the source terminal clear is disjoint from P1 graphics when BX is at least 261 and at most 288. This is a consumer bound; the actual terminal camera range has not been proved.

The source constructor at `7437A1` chooses tile base 1 for side zero, passes it at `7437D6`, and presentation constructor `752440` stores it at +10. Evolution selects resource records by adding `03C0` at `7437C4`: 30 records, not 15. The checked populations are records 0..14 and 30..44. The draw consumer `752AF0..752B11` adds P0+0A on the alternate graphics phase. Base resources use alternate offset 26 (24 for record14); evolved resources use 36. Omitting this alternate bank would understate the actual consumer interval.

The 93E7 child constructor binds fixed tile base 6D and P1 data at `3D23B0`. Its one event contains 15 rows with durations totaling 62 source updates. The first countdown starts at duration; subsequent transitions add the next duration to the negative remainder. This means completion after 63 updates, followed by retirement on callback 64, rather than adding an extra update for every row. Actual resident converted P1 durations total55, with completion56 and following-callback bound57. Both fit inside the respective 75 source /60 native unpaused updates during the terminal blink. The checker pins actual native initializer/update semantics and the resident P1 bytes.

This lifetime bound applies to pre-existing 93E7 children that follow callback9798 and are not replaced or newly spawned. Parent investigation identified fatal callback replacement `7601EC..7601FE` (active7AB1, linked auxiliary7D8D) and normal case5 producer `7417E6..7417FB`. Exhaustive producer exclusion is not asserted by this checker. Source1750 frees only the P1 orb list66E/670; it does not free all26 actor entries.

A naming correction to the earlier BX record: normal initializer `740CB3` calls `4FFF:1D68`, whose body `751D58..751D7B` creates the priority-zero OAM-reset callback `4FFF:1DA5`. It is not the sound task. Callback `751D95..751DA3` waits for scanline146 or later and resets sprite count port6. The previously checked queue priority and BX preservation are unaffected. The frozen old analyzer's representative queue label `sound` is descriptive metadata, not an additional sound producer proof. The actual OAM count reset precedes input/scene; subsequent actor draw consumers write active OAM entries at1800..19FF. This is a positive overwrite lead, not yet a complete proof for every byte in1800..2FFF.

Other source findings relevant to the remaining camera proof:

- Initializer `747D8E..747D9D` puts P1 at worldX=0E00, worldY=FF80. BG0 reset `77DD7C`, followed by the position helper at `77DE4A..77DE58`, starts vertical camera at zero.
- Projection `7423A3..7423E1` subtracts the input camera snapshot from world coordinates shifted right4 and stores the low byte at actor+31. Grounded mode2 additionally subtracts the signed shake byte0300:0112.
- Normal battle and terminal battle track vertical motion against screen threshold44. Camera alone is bounded0..288 by the separate step checker; a tracked-player relation still needs all relevant writers and movement contracts.
- Generic camera shake `76B40C..76B42B` independently modifies BG0 camera from state037E using nonwrapping flags1/4. The current work does not assume that this writer or the projection shake is inactive.
- The unsignedY<=0C00 terminal branch bypasses forced-jump/ground wait. Its camera domain needs a separate argument; no blanket settling claim is used.

`tools/analyze_shoot_terminal_consumers.py` passed all30 character resource populations, exact child countdown semantics, actual resident resource comparison and nine direct semantic negative controls. It modifies no ROM, emulator, save or guest memory.

Frozen checker SHA-256: `AC32C571E1955E18879FDFDE65E9A938AC1546D03F588D967A701C6E650C4CF4`.
Evidence `build/shoot-terminal-consumers-20261106/proof-final.json` SHA-256: `FDDCAE2ADAF59FC4BB158B3DF6BC4C2E0E26686362596B8E8A06A9CB36A31290`.

No terminal mapping is extended or omitted on the strength of these conditional bounds. Actual camera reachability and non-common clear consumers remain open.
