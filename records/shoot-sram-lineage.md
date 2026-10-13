# Shoot SRAM lineage counterexample

Recorded 2026-10-13, supplementing the frozen
[SRAM boundary report](shoot-sram-boundary.md). Its analyzer and JSON were
left unchanged. This investigation read the three immutable ROM inputs;
it did not execute a CPU or game, open an emulator, or access a save file.

## What the older commercial version establishes

The original WSC fighter initializer `9070:27C2`, raw `392EC2`, inherits DS.
Its normal entry at `3909FE` sets DS=`1000`. Before calling the initializer
at `390AB0`, the three preparation helpers `96B2:1D88`, `9070:15AA`, and
`9070:066E` save and restore DS. The initializer itself has no intervening
DS switch and writes:

| Old source location | Value |
| --- | --- |
| `DS:05E4`, `DS:05E8` | `0` |
| `DS:3CB0`, `DS:3CB2` | `0` |
| `DS:3CB4`, `DS:3CB6` | `4` |

The live old regeneration reader at `393185..3931A9` instead uses the
object-task DS=`0C00` convention. It selects `3CB0 + 2 * player_index`.
When the object's `+56` value differs from `60`, a nonzero
timer is decremented; a zero timer becomes `3` and the object's value is
incremented. The dispatcher at `391EDB` establishes DS=`0C00` before the
object callback and subsequent call at `391F20`; this assumes a callback
which obeys that task ABI. No new claim about arbitrary callbacks is made.

The matching commercial GBA reader at `08353040..08353080` uses the same
timer branch and delay, the same player index, and object field `+6A`.
Its actual timer base is `030048AC`, so the two native timers occupy
`030048AC/030048AE`. The native common initializer also clears those
addresses at `08352B54..08352B60`. This is a positive functional identity
for the regeneration timers, not a separate representation of every old
source address which happens to contain the corresponding offsets.

## The new source keeps two different storage identities

WSC 1.5 common initialization explicitly sets ES=`0C00` at `7432ED`, then
clears `ES:3CD8/3CDA` and sets `ES:3CDC/3CDE` to `4`. Its ordinary reader
at `7435B0..7435D4` still performs the timer operation above, now at
`DS:3CD8 + 2 * player_index` under the object-task DS=`0C00` convention.

Shoot initialization at `747CD6` explicitly selects ES=`1000` before its
two zero stores. The ordinary timer words are physical `FCD8/FCDA`; the
Shoot stores are physical `13CD8/13CDA`. Their difference cannot be
discarded on the basis of the old initializer's inherited DS or the
matching timer algorithm. The evidence does not determine whether either
original segment choice was intentional.

## Finite counterexample to merging the two locations

Consider the ordinary reader's timer=`1`, object value=`0`, with its
regeneration branch selected. The source Shoot SRAM stores leave that
ordinary timer intact. The next ordinary-reader step yields timer=`0`,
value=`0`. If the port instead clears native `030048AC`, the native reader
yields timer=`3`, value=`1`.

The analyzer checks all 65,536 timer values with object value zero.
65,535 distinguish the original separate storage from this proposed
merged mapping. This is an algebraic counterexample to **unconditional
aliasing**, not a proof that the complete Shoot route reaches this exact
example state. Such a route-specific precondition would need separate
evidence; it cannot be assumed to justify the alias.

No positive independent native storage location has been proved. The
source writes therefore remain required, and neither their elimination
nor mapping to the live regeneration timers is authorized by this report.
A dedicated representation would require a positive ownership and
persistence contract. The global and first-milestone no-observer questions
remain unresolved.

## Reproduction

```powershell
py -3 tools/analyze_shoot_sram_lineage.py `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  --output build/shoot-sram-lineage-20261013/analysis.json
```

Report SHA-256:
`2AA0538B380BB2E7857904A87DD50210A2BA1B48ACD0C2727FC625A6C286CD5D`.
Five semantic mutations are rejected: the Shoot segment, common segment,
old high-field offset, native regeneration pointer, and native delay.
The result is `DISTINCT_STATE_IDENTITY_CONFIRMED_MAPPING_UNRESOLVED`.
No ROM code, route, main-build input, or frozen report was changed.
