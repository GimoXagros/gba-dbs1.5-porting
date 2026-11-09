# Actual original Shoot input boundary

Read-only source/current-run finding,2026-11-09. Immutable WSC1.5 source SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No controller, emulator, guest-write, frozen module, ROM or save change.

Run `build/bizhawk-wsc-score999-boss1-20261109-a` positively reached the
original Shoot initializer at92374 after the separately recorded direct P1
boss hit/root5. This note does not repeat the capture audit or certify final
inventory. Its source is the current trace and existing verified Shoot input,
initializer and player-transition contracts.

## Physical keys were ignored during the observed opening

Trace92400/92700/93000/93300 reports P1 held/edge zero despite physical X4,
A and later X2/B key requests. P1 remains X0E00 and reaches groundY1500.
The timer remains18000 through93300. At93600 the timer is17970 and P1HP0.
The last preceding A request was93510..93518; the next is93690..93698.
The trace therefore does not show an accepted opening jump before that HP
loss. It also does not prove that early physical X4 made P1 walk or fall:
the corresponding source actor controls were still cleared.

The source scene positively explains the boundary. Callback71F0:1540 at
raw773440 waits its countdown, sets03D8 bit4 at77345F, then installs active
input4090:07FA and active post4090:0D0B at773466..48A. Active input decrements
the battle timer at741115. Before this boundary the scene's input task clears
controls; a stage11 byte alone does not establish that player keys are being
consumed. The sparse timer samples bracket activation between93300 and93600;
17970 at93600 is compatible with activation near93570, but it is not an
independently captured exact transition frame.

## HP1 is source-carried state, not an extra player-HP cheat

Shoot entry772E37..42 reads FIRST HP into the scene's+46 saved word and writes
a temporary FIRST HP1. After03D8 bit2,773357..35F restores that saved word to
FIRST HP. This run survived the boss with1 HP and has1 through the stage11
opening; the source carries/restores the survivor's HP rather than providing
a free refill. The authorized one-shot module targets SECOND only. Neither
this finding nor the run authorizes a P1 HP change.

The later P1HP0 is an observed failure state. Current sparse telemetry has no
paired P1-loss writer/attacker snapshot, so this note does not identify its
exact damaging object or attribute it to a particular physical key. The early
cleared-input samples rule out treating every sent key as an accepted action.

## Small bounded controller change worth testing

P1 retains ordinary fighter controls during active07FA; existing source proofs
already bind kind2 to skipping opponent AI while retaining P1 held/edge input.
Normal jump helper668E:01D6/raw766AB6 tests fresh edge0040 before installing
callback16E8. B remains ordinary helper0224; no alternate Shoot-specific fire
mapping is established by these consumers. A held continuously through the
intro is not equivalent to a fresh jump edge after activation.

The smallest source-backed input correction to evaluate is confined to
stage11: release keys during its locked intro; detect03D8 bit4 together with
the owned07FA input callback and a jump-accepting P1 callback; then issue a
fresh A press instead of waiting for the existing modulo90 pulse. This fixes
a positively identified input-availability mismatch. It does not prove that
the opening jump avoids a particular attack, defeats the opponent, or reaches
the terminal. No new bot or experiment was implemented here.

A useful next read-only capture is the exact active transition RAM, followed
by the first actual P1 HP-loss instruction/attacker and accepted jump callback
with source held/edge. Existing entry at92374 is an initializer snapshot,
not that active transition. The final IRQ/row-clear observer remains separate;
absence of those events after failure is not a successful terminal observation.
