# Separate experimental stage11 score HUD guard

The frozen D0 entry experiment still draws the score in stage11. Source
78769E..7876AA excludes both7 and11, while native373ED8 excludes only7.
This separate component implements that exact missing exclusion. It does not
change the first-run D0 file, main, difficulty/progression, damage or entry.

The sole hook replaces CMP r9,#7 at373ED8 with B086FF400. New16 bytes at
6FF400..6FF410 are `CMP r9,#11; BXEQ lr; CMP r9,#7; B08373EDC`. The original
stage7 conditional return remains in place. Other stages retain the exact
original CMP7 flags and register state at the join. Stage11 returns before
actor, score, stack, BIOS division and VRAM access. No RAM, task, literal pool
or storage write is added. Twenty bytes are declared; nineteen actually differ.

The first candidate in the authorized6FF400..6FF5F0 search passed. All16 bytes
are erased, outside the complete1394-interval/70-layer ledger, both v73 IRQ
reservations, fatal/IRQ hooks and the full6FF380..6FF400 entry reservation.
The conservative whole-ROM scanner includes all unaligned mirrored pointers,
ARM references and Thumb-looking references, with zero exemptions. The entry
reservation's erased tail was not reused. Exact expected writes and a complete
inverse recover D0 byte-for-byte; adjacent and unrelated changes are rejected.

Author checks passed4096 actual ARM entry cases (every stage byte and NZCV),
576 complete native HUD cases with owner0/1, zero/digit boundaries,999 clamp
and65535, and144 real BL caller cases. Non11 compares registers, flags, reads,
calls and ordered writes against D0. Ordinary stages write exactly three
expected halfwords at0600D804/+2/+4. Stages7/11 read only the stage byte and
perform no writes or calls. Nine controls cover expected-write/inverse damage
and a demonstrably wrong stage predicate.

The existing strict ARM interpreter is reused. The unchanged37DB3C native
thunk and Thumb37D5E8 `SWI6; BX LR` are pinned; BIOS positive division alone is
modeled as quotient/remainder. No BIOS, emulator, hardware or save ran. This
is not evidence about the physical BIOS service or a gameplay capture.

Full source78768C..7876F5 is pinned and includes PUSHF/POPF. Native calling
conventions are evaluated separately: the non11 join preserves CMP7 NZCV;
callers373538/3735A4 immediately return, and37364C overwrites NZCV at373658
before branching. The first two return into their scheduler context; independent
QA owns the remaining scheduler flag-consumer check and final component verdict.
Positive callback literals are3734F0 atD1C1C,37354C at33FDA4/6FFD88, and3735BC
at377BCC/5C8D74. No complete entry, ending or E5 closure is claimed.

| Frozen artifact | SHA256 |
| --- | --- |
| D0 predecessor | `D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C` |
| tools/build_shoot_score_hud_guard.py | `7D5C647547E4FECD6707A0B8AB6411B6A0FC3233442B04465820F27823634B32` |
| build/shoot-score-hud-guard-20261109/component.gba | `C8E810258B41A979A4DCE514119D8CAF139D615D63355F18F1C2E49AD72332F6` |
| build/shoot-score-hud-guard-20261109/component.json | `BD1DF6DC17B0E3474F969CA617031B3BEB56FCF6CB300209A12976F28CBD4DAD` |

CLI accepts `INPUT GBA SOURCE OUTPUT --manifest JSON`, exact frozen inputs and
fresh distinct output paths only. Independent QA and any follow-up runtime are
separate; this component remains experimental and is not integrated into main.
