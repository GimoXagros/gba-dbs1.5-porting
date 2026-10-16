# Player spawn literal repair, 2026-10-16

The invisible fighters were traced to the first world-coordinate stores, before
movement or collision processing. The relocated native spawn constructor retained
a PC-relative load from its original address. It consequently used blank ROM as
the address of stage state and selected instruction bytes as coordinates.

## Direct cause and runtime evidence

The retail instruction at `08353130`, `LDR r8,[pc,#1C8]`, reads the literal at
`08353300`, whose value is the existing stage-state address `03002310`. Its copy
at `08582F00` used the same displacement and therefore read `085830D0`, whose
value is `FFFFFFFF`. The next instruction reads the actual-stage byte at
`r8+0E`; the later variant read uses `r8+14`.

The parent-controlled, invisible development-emulator watch is saved as
`build/player-world-writes-20261016/probe.json`, SHA-256
`513BDCFB277176F364EAF4D61851C31B1DD0B0DD1C13D67F6C4C8A58ABF947C8`.
It used candidate
`C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017`.
The first watch event after constructor entry stopped immediately after the
world-X store at `08582F48`: PC was `08582F4C`, selector `r1=218`, table base
`r8=08583000`, and the stored halfword was `9003`. This is outside the complete
`D0`-byte spawn table. ROM bytes at `08583218` are `03 90 A0 03`, the ARM word
`03A09003` (`MOVEQ r9,#3`) in another stage adapter. Its halfwords are
`9003,03A0`, exactly the initial erroneous X/Y pair.
Later movement stores retain the already-invalid X. The watch recorded no
debugger guest-memory writes. No supplied save was accessed.

The late battle capture initially suggested an OAM problem. Its full signed
coordinates instead explain the missing fighters. At
`build/runtime-resource-routing-battle-20261016`, camera X/Y were `152,144`.
Native `083528DC..08352944` computes presentation coordinates by signed
`world >> 4` minus the camera. Player 0 world `9003,1539` becomes `-1944,195`;
player 1 world `06C3,3667` becomes `-44,726`. These equal their actual
presentation halfwords. Fighter fields `+3E/+40` are byte caches and must not
be treated as full signed positions. Both presentations were culled.

The normal retail capture used the same scheduled inputs and showed visible
fighters. Both captures had actual stage `1`, BG0 dimensions `2x2`, and collision
pointer `08046F48`. Its entire `1F80`-byte grid is unchanged (SHA-256
`DFA47F83353CBDAA62475E26045AAF2671E81D2B2819A179023E3768BA5669B0`).
The native collision consumer `080C86B4..080C8E18` and movement pass
`08373928..08373BA4` are unchanged. Native OAM publication
`08011708..080117CC` copies the shadow using count `030012CA`, disables remaining
objects, and resets that count. Neither a zero count after publication nor stale
shadow attributes alone establishes a transfer failure.

## Exact repair and source contract

`tools/build_player_spawn_literal_repair.py` appends a final overlay without
changing the frozen stage-integration layer:

| Raw offset | Expected word | Replacement | Meaning |
| --- | --- | --- | --- |
| `582F00` | `E59F81C8` | `E59F8060` | Load the stage-state literal at `582F68` |
| `582F68` | `FFFFFFFF` | `03002310` | Existing native stage-state address |

Only six bytes differ. The new four-byte literal had an exact blank-byte guard
and no encoded unaligned pointer, aligned ARM B/BL, or aligned immediate ARM
PC-relative load reference in the predecessor. No new RAM or callback is added.
All 24 copied constructor instructions retain their retail correspondence;
the previous intentional changes remain the `stage>=7` extra-row bias and the
expanded table base. The other relocated PC-relative load at `582F3C` already
resolves correctly to `582F64` and table `08583000`. The final branch still
continues at `08353190`, with the same stack and current/previous-coordinate
stores.

Source `743654..7436A4` selects stage from `ES=1000:005C`, shifts it by four,
adds `10` for stage at least seven, and selects the low two variant bits except
that stages other than six retain only one variant bit. A nonzero player-slot
argument adds four. It loads X/Y from source table `743224` and stores both
current and previous coordinates. The `C0` bytes for stages 0 through 10 are
identical to native table `583000..5830C0`; the first `90` bytes also equal the
retail table `35326C..3532FC`. The repair changes no coordinate values.

All 88 combinations of stages 0 through 10, four variant-bit inputs, and two
player-slot equivalence classes are source-backed. The eight stage-11
combinations are checked only for bounded access to the existing retained
retail-stage-7 placeholder. Ordinary fighter spawn remains forbidden for the
dedicated Shoot entry, and no source-equivalence claim is made for that row.

## Reproduction

```powershell
py -3 tools/build_player_spawn_literal_repair.py `
  build/selection-palette-routing-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/player-spawn-literal-repair-20261016/current-candidate.gba `
  --manifest build/player-spawn-literal-repair-20261016/manifest.json
```

Output ROM SHA-256:
`1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995`.
Manifest SHA-256:
`D3A5A0841AE7FD685C96EE5E02E05ECFF968831FD3F974194A2EDD98DF885E6D`.

The independently implemented verifier does not import the builder. It checks
24 source instructions, including the `XOR BX,BX` before the stage-byte load;
25 native instructions; both relocated PC-relative loads; all 88 source-backed
cases; and paired current/previous stores. Nine corrupted-result fixtures and
the inbound-reference detector fixtures are rejected. The full-ROM inverse
recovers the exact predecessor.

```powershell
py -3 tools/verify_player_spawn_literal_repair.py `
  build/selection-palette-routing-20261016/current-candidate.gba `
  build/player-spawn-literal-repair-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/player-spawn-literal-repair-20261016/verification.json
```

Final independent report SHA-256:
`5AA3B9172D5E9462B310E6A60478A9B6C89307D0416A933F1CB1BF4E466DBD0E`.

## Bounded post-repair runtime check

The parent ran the repaired ROM invisibly with the same scheduled first-battle
inputs. `build/runtime-spawn-repair-battle-20261016/capture.json` has SHA-256
`4FABB6AA2BB851D3982E7502617E82E66B6E5D1DC2B6BEEAAC91B8CD4F967AD8`.
Its 70-second screenshot shows both fighters in the Christmas arena. Reading
the saved hardware OAM dump independently gives 34 enabled objects, versus zero
in the failing capture. The renderer integrity check passed; its report
`invariants.json` has SHA-256
`E2EF62D0C400AEC8B63CE471AD68BB56E2D8EE8E7274441EBFE793AD0DC7CF57`.
The emulator was stopped normally (`S02`) without an asynchronous failure.

This confirms the bounded invisible-fighter regression for the recorded first
battle. Static selector equivalence and this checkpoint do not establish that
every playable stage, added fighter, or later battle transition is complete.
