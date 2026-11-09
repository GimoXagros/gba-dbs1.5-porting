# Experimental native Shoot entry probe

This is a separate development ROM for bounded observation, not a release
candidate or approval of complete source entry. No emulator was launched by
the author, and main/final build inputs were not edited.

The new builder reuses the reviewed case5 selector logic from frozen
`build_shoot_scene_route.py` (`6E431B58...`). The current corrected104-byte
selector, with default `086FC300`, hashes to `9408A3EE...`; `4DA88F37...`
belongs to the older default-callback profile and is not its current hash.
The old draft placement5C9900 fails the stronger ownership check: an unaligned
word at43454F equals mirror pointer0C5C9900, and Thumb-looking encodings also
target its interior. No classification exemption was used. That placement
was rejected before creating any output.

Within the root-approved bounded search6FF300..6FF5F0, the final selector uses
6FF380..6FF3E8. Its entire128-byte reservation6FF380..6FF400 is FF and passes
the full conservative pointer/ARM/Thumb reference scanner without exemptions.
The independent1394-interval/70-layer layout ledger, both added18BB IRQ
reservations, the IRQ hook and fatal4-byte hook are included in disjointness
checks; erased declared tails are not treated as unowned. The relocated
selector differs from the reviewed code only at word+76, its final branch
back to0833FD08. Internal relative branches and literal-pool loads stay local.

One external word at33FD04 changes its original callback load into a branch
to086FF380. The selector returns r8=085C8000 for
`stage!=11 && (difficulty==3 || (difficulty!=0 && !(progress&0400)))`, or
r8=086FC300 otherwise. Every other register, SP/LR and CPSR are preserved.
The existing push sequence and sole0833FD18 allocator call retain priority
0FF0. No second scene, descriptor, constructor or guest diagnostic field is
created. The existing native progression producer0B9E68 is untouched; the
selector reads the actual stage/difficulty/progress fields.

The builder checks48 actual ARM joins over stage, difficulty, progress and
NZCV partitions, plus six expected-write mutations. Only its16-byte stack
frame may be written by the selector. Exactly108 bytes are declared and
changed; reversing them recovers the complete6A predecessor. Earlier complete
selector algebra, caller/palette/storage and scene-owner proofs are reused.
Independent verification is owned by the separate reviewer.

| Frozen artifact | SHA256 |
| --- | --- |
| Predecessor6A | `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7` |
| tools/build_shoot_runtime_entry_probe.py | `027FD5849411535D0C367B2C35E5978DECA381628744D62F0F868EDFDF3518E2` |
| build/shoot-runtime-entry-probe-20261109/experimental.gba | `D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C` |
| build/shoot-runtime-entry-probe-20261109/experimental.json | `DF4EB38EA39F845B936A08CE0923B966BE8ECC729B697AD5FDEED16F3A08E746` |

CLI: `INPUT GBA SOURCE OUTPUT --manifest JSON`. Outputs must be fresh and
distinct. The builder requires the frozen layout ledger and18BB manifest.

## Read-only native observation bindings

FIRST and SECOND are native pointers in0300489C/030048A0. Actor HP is word+64:
normal construction3530E8 stores8; native boss construction36FD44 stores its
difficulty-derived HP; translated Shoot upper5C1058 stores its source-derived
HP. No constant captured actor address is needed.

D-Spirit is word+66, positively bound by zero-initialization3530F0, pickup
increment/cap250 at35477C..354798, HUD read373EF4/clamp999, and byte exports
340434/340440. Source actor+52 is not the native offset. The post-processing
battle boundary373650 precedes real P1-death/root4 and SECOND-death/root5
decisions; root5 is3736B0. The earlier HP<=0/death-event3E root4 has priority.

The scene calls the real ordered initializer at5C853C->629800;5C8540 is its
return. The stage byte is written11 at629714. Saved source health is restored
from current scene state+54 to FIRST+64 at5C8B2C. Active Shoot flag0300450A
bit4 is written at5C8D2C; input and battle callbacks restore at5C8D3C/5C8D4C,
then the scene retires through5C8D50. A safe outer observation after this path
should validate real actors/phase and positive saved/current health, not infer
activation from an earlier initialization dump.

One newly checked visible difference is retained score HUD373ED0: it skips
stage7 only, while source78769E..7876AA skips both7 and11. If reached during
stage11, native373F20 and following stores draw digits at0600D804. This is a
specific UI parity difference; it is not an invalid-pointer or BG1F000 claim.
No HUD change is included in this probe.

The first identified conditional invalid consumer remains generic victim
event48 hexadecimal on the six-event upper resource, with a zero native frame
pointer. Existing8EF3 residual-domain and terminal live-guard refusals remain
observable as documented in the feasibility note. No guard is removed and no
full-entry, E5-cause or completed-gameplay claim follows from emitting this ROM.
