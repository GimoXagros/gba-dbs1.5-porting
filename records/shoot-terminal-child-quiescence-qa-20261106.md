# Terminal child quiescence: positive entry proof, conditional closure only

The fatal callback pair has a closed no-new-child graph, but the actual
terminal-entry predicate does **not** check that pair. The separate HP writer
`4090:3030` still prevents an unconditional terminal no-new-child conclusion.
No native terminal builder, main build, ROM, emulator or save was changed.

`tools/analyze_shoot_terminal_child_quiescence.py` now pins the actual dispatch
and both HP-writing mechanisms, rather than treating terminal ownership as
proof of fatal callback ownership. Its sole ROM input is original WSC1.5
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.

## Actual terminal entry

| Actual source location | Positively checked behavior |
|---|---|
| `7417B5..7417FE` | Kind2 only. First actor `065C` can take case4 when HP is0 and state `A4` is `003E`; otherwise second actor `065E` with signed HP `+50 <= 0` calls root `71F0:0000` with argument5 at `7417F3`. |
| `771F69..771F8A` | Root case5 reads stage byte `1000:005C`; stage11 selects `771FA3`. |
| `771FA3..771FCA` | Installs input `4090:07D6` and allocates priority `0FF0` task `71F0:0653`. Battle replacement `4090:0B8B` was installed at `771F53`. |
| `772553..77256F` | Task `71F0:0653` checks stage11 and directly calls terminal `71F0:1750` at `772569`. |

Neither the second-actor HP predicate nor the stage11 dispatch tests an actor
callback. These are actual decoded callers and allocation arguments, not
address-pattern matches or assumed gameplay states.

## What the HP writers establish

Common damage at `760177..76019F` obtains damage, applies the existing half
damage flag, subtracts actor `DI+50`, and branches on signed nonpositive HP.
Stage11 then branches directly to `7601EC`. That block assigns upper
`4090:7AB1` to `DI`, follows `DI+1C`, and assigns lower `4090:7D8D`.
Thus this positively identified fatal writer supplies the required pair.

The independent service `4090:3030` at `743930..743ADB` also writes actor HP.
Its exact checked block `743962..74399C` requires positive HP, bounds the
deduction by current HP, and subtracts at `743987` when kind is2. Therefore
its local arithmetic permits HP to reach zero. Its full decoded service has
exactly three direct SI-parent stores: `743987:+50`, `74398A:+C`, and
`743997:+C`. It does not install either parent callback word.

This is not a hypothetical unused service: actual source attack constructors
at `7617AF`, `7618D5`, and `761986` begin with `LCALL 4090:3030`. The first
checked constructor subsequently assigns ordinary reaction callback
`5FFD:1817` at `7617DD`, rather than the fatal pair. The existing attack
dispatch implementation owns their full record/handler correspondence.

This does **not** prove a natural terminal trace with that writer. Which
actors it can drain, whether one is the actual terminal-trigger actor, and
whether another callback change intervenes must still be closed. Until then,
HP depletion alone cannot establish fatal callback ownership. No complete
inventory of all reachable HP writers is claimed.

## Narrow callback closure and checks

The source graph from `7AB1/7D8D` covers237 instructions and exactly these
callbacks: `7AB1,7B1B,7B3A,7BFF,7C64,7CE5,7D7C,7D8D,7DA9,7DD8`.
Its imports are only `4FFF:2389/24CB/2862`. Existing child seeds `9798/97BB`
cover93 instructions and callbacks `9798,97BB,984D,9879`, with typed retained
presentation/math services and `4090:181E` release. The analyzer now rejects
any untyped common-service import, including task allocator `4FFF:0980`,
and rejects a register-derived actor callback assignment.

Thirteen in-memory source mutations are rejected: wrong input owner, wrong
fatal upper/lower callbacks, active controller/spawn re-entry, wrong trigger
actor, reversed signed HP gate, wrong dispatch/fatal stage, a hidden callback
store in3030, a false fatal continuation in its caller, task allocation in the
fatal graph, and an unresolved callback assignment. These bypass the source
hash guard and exercise the actual decoded contracts and walker.

Report: `build/shoot-terminal-child-quiescence-20261106-a/proof.json`.
Its status is `CONDITIONAL_NO_NEW_CHILD_PASS`, with
`callback_identity_checked_by_entry=false` and
`every_terminal_entry_writer_installs_pair_proven=false`.

| Artifact | SHA-256 |
|---|---|
| Analyzer | `A9FCE5598660DA2618CD075D6BF2E7350EBBB62C3ACE5A79FA61DF0665DDF9FD` |
| JSON report | `D34141BEEA543F838E19F4F62C76E11ABF34FDA5F26C7B2F161AE831EB45B994` |

The prior `93E7` lifetime proof remains a separate dependency and was not
repeated. Input replacement does not prove stale actor keys are cleared;
the battle callback retains the movement pass; `1750` frees the orb list,
not every actor. No blanket child expiry, stationary-actor invariant,
terminal refill exclusion, native projection, or whole-port completion is
established here. The static-companion subset's separate ordering proof is
owned by the terminal worker and is not blocked or authorized by this record.
