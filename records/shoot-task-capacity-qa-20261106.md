# Scoped upload restoration: comparative task-capacity evidence

**Result: one extra task slot remains unproved.** The reviewed native additions do not establish a persistent extra battle task, but that is not a global free-slot bound. No reachable full-pool counterexample is identified either. This read-only review covers original sourceC415, retail996D and actual v70 native8EC8; `terminal_path` owns any restoration proposal. No emulator, sampled task counts, save contents, main changes or new implementation were used.

Both schedulers have52 normal task slots with0x100-byte payloads. Source reset750960..750968 clears0x1BA0 words, i.e.0x3740 bytes =52×0x110, starting at near0014; the header is0x10 bytes. Native reset08011AA0..08011AAC uses the literal at11AC0, 0xE38 words×4 =0x38E0 bytes =52×0x118, starting02010000; the header is0x18 bytes. The count literals are copy lengths, not live-count upper bounds at a particular allocation.

The positively paired battle populations are:

| Owner | Source | Native | Proven allocation count |
|---|---|---|---:|
| Preallocated normal actor pool | 741FA5..741FC5, allocator741FB5 | 083522BC..083522F0, allocator083522DC | 26 per creator invocation |
| Input and battle-update service pair | 740FC1..740FE6, priorities0F00/6000 | 080D1BCC..080D1C04, same priorities | 2 |
| Actor-pool teardown | paired ordinary battle ownership | 080D1B24 →08352340, same26-pointer array | Releases that population |
| Service-pair teardown | 740FF1..741018 | 080D1C24..080D1C58 | Frees both saved handles |

The object API08352374 uses those preallocated slots; it is not a new scheduler allocation per actor spawn. Actual new native calls at085B9468,085BC23C,085C8E40,085CC220 and085CC360 target that object API. Their number is not an added-task count. The fixed26 population count also must not be mistaken for a proof that all remaining scheduler owners fit in the other26 slots.

A bounded allocation-delta check compares all aligned ARM BL encodings, including conditional BLs, that target08011AC4: retail has91 sites and current92, with **one added site,08633A1C**, and no removed site. There are no encoded allocator pointer literals at any byte alignment for08011AC4 or its0A/0C ROM mirrors in either input. These checks do not exclude arbitrary computed/indirect calls or prove dynamic call multiplicity.

The added site is positively the Options language task: constructor08633A00 uses callback08633E00 and priority1500. Its callback checks the native Options exit flags, sets retirement bit200 at08633ED8 and calls08012030 at08633EE0. Native08012030→08011BE4 unlinks and clears allocation status. The ordinary Options exit at080C3380..080C3390 waits for the complete3FB mask at literal080C33F4, including that200 bit. Thus this known native-only addition has a positive normal-exit retirement owner; it is not a justified permanent battle occupancy increment. Existing title localization selects resources for the original two constructor tasks rather than creating another task; result localization likewise retains its seven original constructor allocations and original callback population. This is consistent with the actual allocator-site delta, not an inference from a quiet runtime sample.

What remains missing is the bound on **all other simultaneously live scheduler owners** at a scoped FIRST+AC upload. Taking the paired26+2 populations as the known28 slots, let R include every remaining mode, HUD, scene, effect, pause, transition or unreleased prior owner. One extra upload fits only if R≤23 at that allocation point. No complete positive source/native battle-owner proof of that inequality is available here. There are positively additional native owners, for example case5's separate0FF0 task created at0833FD18; R cannot be assumed zero. A direct-call-site count is not a maximum live-task count.

The source lifecycle review identifies P1/P2 pending uploads omitted by the retail native presentation path. Omission alone does not establish a pointwise scheduler-population inequality: the relevant source/native phase alignment, remaining owner lifetimes and available slot must still be coupled. “At most one new pending task” bounds the proposed increment, not the baseline. The constructors' scan for a free slot does not supply an independent capacity proof. Accordingly this comparison neither approves allocating the extra F001 task nor proposes a speculative clamp, silent fallback or altered pool. The scoped capacity obligation remains **UNKNOWN**.
