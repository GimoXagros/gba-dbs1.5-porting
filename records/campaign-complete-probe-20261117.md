# Assisted eleven-encounter campaign observation — 2026-11-17

`tools/bizhawk_probe_campaign_complete.lua` prepares one fresh bounded
observation of candidate933C. It reuses the existing ordinary input controller
and the corrected typed score/boss observer. No emulator was started by this
author. This is an assisted development observation, not a claim of an ordinary
no-cheat campaign completion or a completed Shoot battle.

## Preserved controller and authorized actions

The wrapper loads these immutable files in isolated Lua environments:

| File | SHA-256 |
| --- | --- |
| `bizhawk_probe_gba_shoot_entry.lua` | D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D |
| `bizhawk_gba_shoot_entry_observer.lua` | 7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59 |
| `bizhawk_probe_gba_collision.lua` | 7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9 |

Observer7513 is the corrected version documented in
`shoot-native-entry-guard-repair-20261109.md` and independently checked by
`shoot-native-entry-guard-delta-qa-20261109.md`. Its stage7 kind3/resource
profile and stage11 kind6/resource profile remain distinct. Its actual save API
must return boolean true before a healthy marker is allowed. The olderE620
module and its known failed-save false-success issue are not reused.

The unchanged driver selects difficulty2 through Options, default fighter/form0,
and applies the existing approach/jump/no-Up controller. Continue stops the
observation. The frame cap remains120000; this wrapper neither increases it nor
replaces the controller. No prior savestate is loaded.

The original observer remains the only writer. It may restore the active,
typed ordinary P1 score WORD at+66 to999, and write the typed stage7 boss
SECOND+64 WORD to1 once. Its existing mode, gamekind, active task, reciprocal
actor/resource, signed positive P1 health, difficulty, neighboring-word, and
consumed-before-write checks are unchanged. Stage11 HP writes remain disabled.
It never writes P1 HP, stage, timer, mode, campaign progress, RNG row, or registers.

The old proof of actual FIRST damage remains mandatory: pre/post0836E5E4/E8
must join the real attacker/victim and resulting signed fatal HP value, followed
by healthy root5 and the eligible case5 path. Scene saved health, initializer
call/return, matching restored health, retired scene owner, native input/battle
tasks, and actual healthy stage11 activation remain the original final gate.
The new wrapper does not substitute a host-written zero HP for that real hit.

## Exact adaptations and added evidence

Only two observer text substitutions are made in memory: the host ROM identity
pin changes from historicalD0 to933C, and its ROM read bound expands from8 to
16MiB. The collision frame loop receives a16MiB loaded-ROM dump and a truthful
assisted-run log label. Reversing those four substitutions recovers the exact
three frozen source files. The controller file is byte unchanged.

Required userdata remains `output`, `frames`, optional `start_frame`, and:

```text
probe_sha256=933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775
score_authorization=user-approved-development-score999
boss_authorization=user-approved-development-boss-once-per-stage
```

The host must hash the copied ROM, all four Lua dependencies, and the complete
16MiB `loaded-rom.bin`; the userdata hash is not a Lua-computed verification.
Fresh isolated output/data paths and the existing hidden-host boundary remain
the root's responsibility.

At the actual producer return0808B70C, the wrapper checks R4=03002310,
progress0..10, RNG row0..7, unchanged row across the campaign, and the actual
source-selected physical stage/CPU/form. The first progress must be0. A new
progress may advance only by1; duplicates of the current progress are allowed.
It checks the loaded source-derived tables at08D3FB10/18/40 before registering
the hooks. Each first producer observation queues one memory/image checkpoint.

Each encounter also requires an outer boundary with the retained observer's
actual input/battle task owners and typed reciprocal pair. The new
read-only check joins SECOND's actual identity/kind to the selected source CPU.
The existing observer's live predicate already requires08374FF4/083735BC,
so this does not reuse the insufficient early READY-only actor predicate.
These are active-owner checkpoints. They do not require a decreasing clock and
do not repeat the separate120-frame control-tail experiment or prove every
battle's entire trajectory.

At080B6054, after the numeric/final row has been written, progress9 must show
the actual two-digit10 tail:2215,2214 and seven2201 blanks. Progress10 must
match all16 words of the retained final-label ROM row at080B5FEA. R5 must be
0600E820. Both observations require the corresponding producer checkpoint first.
Their snapshots are queued to the original observer's outer-frame exporter.

The existing activation-tail hook is wrapped only to retain an activation fact.
Before its next outer flush can accept healthy activation, all eleven ordered
producer checkpoints, all eleven active-owner checkpoints, and both HUD checks
must exist. Missing proof calls the original named failure path before its
healthy outcome is assigned. No write or activation guard is removed.

New scalar facts go to `campaign-complete-trace.txt`; full memory, screenshots,
and genuine savestates remain deferred to the original outer-frame exporter.
The original `shoot-entry-writes.txt` ledger and `shoot-entry-done.txt` remain.
The additional `campaign-complete-done.txt` reports
`campaign-eleven-stages-and-healthy-shoot-activation` only after the original
healthy result and all added evidence. Named failures and `bounded-no-activation`
remain failures/absence, not completion. Both marker files and the genuine
healthy checkpoint must be independently audited after a real run.

## Focused author check and limits

Wrapper SHA-256:
`F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF`.
Checker `tools/check_campaign_complete_wrapper.py` SHA-256:
`F44AA4A365C626FA34CC91C315F8444C652103A06D4417C7A264FEE764CF7CF0`.
Report `build/campaign-complete-wrapper-20261117/author-r2-labels.json` SHA-256:
`A8371C50992534325B836FF2677CDA82248B4E9E8EF9CEC7671631033BD52D4E`.
The earlier author.json remains preserved. This revision changes only the
two emitted checkpoint labels from running to active; all predicates are exact.

Eleven Lua54 scenarios pass: complete ordered evidence; skipped progress;
changed RNG row; wrong committed CPU; wrong HUD; missing HUD; missing live
checkpoint; wrong live CPU; preserved original failure; bounded absence; and
wrong ROM identity. The real new wrapper closures execute with a modeled
retained observer API. The check compiles all effective source, verifies exact
text inverses and hook opcodes, and rejects new memory/register/control/state
write APIs in the wrapper. It does not rerun the old authorized-write/controller
suites or claim a complete live core test. Independent review precedes root's
launch. Actual campaign, fatal boss hit, healthy Shoot activation, terminal
Shoot play, and no-cheat completion remain unobserved by this author check.
