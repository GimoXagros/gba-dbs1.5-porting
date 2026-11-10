# Terminal BG guard: phase-order investigation and scalar observer

The completed46B3 trial `build/bizhawk-gba-shoot-terminal-owner-20261109-a`
passes the corrected owner predicate, then records `BG-velocity` at69932
and `hardware-BG-mapping` at69933. Both have prepared/copied queue1/08587200.
The first has BG1CNT1E03 and transition state+C=01B0; the second has
BG1CNT1F03 and state+C=01B1. The existing log does not contain the four
velocity values, so the following first-frame velocity attribution is a
source/native causal prediction awaiting added instruction-time telemetry.

## Source/native causal chain

Source75FDB8 increments state+C;75FDBC tests its low two bits. Every fourth
update,75FDDA stores0200 to source1000:01CE+1E, then calls the ordinary
descriptor consumer. Native085E714C/7150 and085E716C implement this with
descriptor03002338, hence velocity03002356. This source-defined shake is
consistent with actual69932's01B0. It is separate from FIRST actor motion.

The guard runs at086FF9C0 after17758 copies the queue, before080D0C18/1C
clear03002354/2356. Thus final outer RAM with zero velocity cannot describe
the earlier guard instant. Descriptor03002388's two velocities are distinct;
no proposed change removes any of the four velocity checks.

After refusal the original copied callback08587200 routes through085E7A00.
With0400 set, it enters retail080C97B8, whose080C97BC/C0 passes map selector12
to08000FEC. That helper's table at1030 is1E1E1F1F1C1D1B1B; selector low
index2 gives BG1 high byte1F. Instructions08001004/08/0C/10 preserve BG1's
low byte and replace its entire high byte. In contrast the intended Shoot
display085E7418/1C passes selector21, index1, giving high byte1E.

This agrees with source75FAE6/FAE8 setting selector21 before the transition
IRQ installation. The current guard tests the previous hardware mapping
before the selected next display configures its own mapping. A first
velocity refusal can therefore lead to a mapping refusal on following
frames. The new telemetry is designed to bind this exact ordering in the
actual CPU execution rather than combining final RAM with an earlier hook.

## Frozen scalar telemetry wrapper

`tools/bizhawk_probe_gba_shoot_terminal_bg_epoch.lua` SHA256
`8BC67A68FCF9681D5CF7F34E12F501611A14C9DB2F2D50C2760B10A9775F0439`
reads the unchanged964B base observer directly. It applies precisely the
existing owner wrapper's ROM binding and auxiliary+28 predicate, then
inserts one block inside the unique `install()` function. It adds no guest
write, input, save/load or full capture operation. The existing approved
healthy checkpoint and one-shot boss HP intervention remain unchanged.

Eleven scalar hooks cover shake before/after(085E716C/7170), guard entry/
return(086FF9C0/698), fallback(080C97B8), velocity clear before/between/after
(080D0C18/1C/20), and map call/store before/store after(08000FEC/1010/1014).
Map hooks require R0=12 or21. All hooks require the observed scene,
mode7/stage11/0400. Each label records at most once per core in the first
relevant core and its successor: at most22 added scalar records.

Each record includes all four descriptor velocities, map shadow12CE,
BG0CNT, existing state/IRQ/queue/MMIO fields, registers, and the planned
BG1CNT computed from the real ROM selector table. It labels that value as
planned rather than observed. Full captures remain at outer boundaries.

Author Lua54 checks parsed the actual composed observer, verified that
removing the one insertion restores the complete effective owner observer,
and exercised gates, deduplication, two-core bound, velocity fields and both
map selectors. `build/shoot-terminal-bg-epoch-20261110/author-report.json`
SHA256 is `61C38CB843242F9B68E94A3B520B639F62E27D4395CEF7C3DBCF52A54D32D59C`.
Independent wrapper/host QA and actual replay are separate root-owned gates.

## Bounded remedy under review, not implemented

The smallest candidate keeps all velocity, actor, queue, hardware mode,
blank tile and sampled-row predicates. It validates the selected display's
prospective mapping: `projected=(current_BG1CNT & FF) | 1E00`, followed by
the unchanged requirement `(projected & DFCC)==1E00`. Algebraically that
is `(current_BG1CNT & CC)==0`; only literal words6FFDE8/6FFDEC would change
DFCC→CC and1E00→0. High map/size bits would be guaranteed by the actual
unconditional FEC#21 producer, not treated as arbitrary acceptable hardware.

This requires explicit ownership/lifetime review from queued selection
through tiny callback, FEC and IRQ consumption, including low-byte fields,
mode, blank tile and sampled F000 rows. Existing555554FD queue/IRQ chains
and stationary-family proofs remain relevant, but do not justify claiming
that no ordinary scheduler iteration can occur in that interval. If those
conditions cannot be established, the two-literal proposal is insufficient.
No ROM, guard, main build or frozen predecessor has been changed here.
