# One-time boss HP1 independent preflight

The proposal was initially unapproved and was not wired or run during review.
The user subsequently explicitly approved the original-reference one-time boss
HP1 change followed by an actual hit. This review covers the frozen module
`CBD4EC42A0106C9F10ADEFF27338E9F5FEE80F724D819822E4180639EB90F952`;
runtime activation remains with the separate approved driver and root launcher.

No blocker was found. Without the exact approval token, load/tick/finish remain
inert before hook installation or memory access. With approval, the module
requires exact original/core binding, active stage7 single-player kind2,
unpaused player0, both active intro-retired callbacks07FA/0D0B, timer<18000,
an owned distinct FIRST/SECOND pair, FIRST alive and SECOND kind3/id0F/index1.
It reduces only SECOND+50 to1 when the prior signed HP is greater than1.
HP0/1 and negative values are untouched. It consumes its one-shot flag before
writing; subsequent ticks, restored HP and repeated hooks cannot hold1 or rearm.

The independent fixture in
`build/boss-hp1-independent-20261109/check.py` executes the actual Lua with a
separately constructed owner layout through the existing Lua54 host. Four
denied-token fixtures have no emulator/memory/event API capabilities at all.
Twenty approved fixtures cover the positive write, no-heal values, timing,
mode/stage/pause, P1 death, wrong type/index/id/link, inactive ownership and
pre-intro callbacks. Every case compares all65536 RAM bytes. Three deliberate
mutations reject default approval, rearming and healingHP1. Report
`build/boss-hp1-independent-20261109/report.json` passes for exactCBD4EC42.
Only mocked memory is changed; no supplied save, emulator or actual guest state
is accessed by this preflight.

Source ownership is independently cross-checked against the retained pins:
74337C..392 passes SECOND with index1/opponentFIRST;743630..633 stores the
index and74364E..651 stores its opponent link. The FIRST call is symmetric.
Mode2 supplies kind3,745640 installs identity0F, and allocator750980/7509A3
establishes the active-slot bit. The author source proof also pins intro
completion, timer decrement and the normal HP branch. These are normal source
ownership contracts, not a theorem about arbitrary corrupted RAM.

The change intentionally does not write zero or advance the stage. Actual
gameplay must still execute its own damage subtraction and victory route.
The new driver must record those separately, including attacker identity
without assuming every source attack object is the FIRST actor itself.
