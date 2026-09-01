# Opening/presentation callback graph

## Confirmed cold-boot provenance

The commercial GBA opening entry at `0x080838A4` registers callback
`0x08083978` through task consumer `0x08011AC4`. The callback setter at
`0x08012008` connects an 18-callback presentation population rooted at that
entry. The graph contains 15 callbacks on the linear path, a three-way split
at `0x08086D60`, convergence at `0x08087D94`, and termination at
`0x08087E3C`. All 18 population callbacks are statically reachable from the
registered root.

WSC 1.0 registers its root at bank `0x39`, setup function `C78A`, call `C7A0`,
and runtime pointer `9C3F:0453`, which maps to callback body `C843`. Its graph
also has 15 linear callbacks followed by three choice callbacks, converging at
`F82B` and terminating at `F8A8`. WSC 1.5 registers its root at bank `0x75`,
setup function `5CF7`, call `5D0D`, and runtime pointer `558C:04F0`, which maps
to callback body `5DB0`. Every initializer population member in both WSC
versions is statically reachable from its registered root.

The previous statement that the six additional WSC 1.5 calls formed three
arithmetic pairs was incorrect. The confirmed topology is:

| Version | Linear callbacks | Choice callbacks | Total |
|---|---:|---:|---:|
| Commercial GBA | 15 | 3 | 18 |
| WSC 1.0 | 15 | 3 | 18 |
| WSC 1.5 | 19 | 5 | 24 |

Thus the GBA conversion retained the WSC 1.0 topology, while WSC 1.5 added
four callbacks to the linear path and two callbacks to the choice set.

## WSC 1.5 additions and selector evidence

A maximum-score monotonic alignment of x86 instruction-mnemonic shapes maps
all 18 WSC 1.0 callbacks into the WSC 1.5 graph while leaving these six WSC
1.5 callbacks unmatched:

| WSC 1.5 index | Body | Graph role | Selectors inside callback body |
|---:|---:|---|---|
| 7 | `7077` | linear | `14` |
| 8 | `7407` | linear | `8` |
| 9 | `7698` | linear | `9` |
| 10 | `7992` | linear | `3` |
| 22 | `9C17` | choice | none |
| 23 | `9E40` | choice | none |

The aligned callback at index 6 changes its object selector from `3` in WSC
1.0 to `13` in WSC 1.5. The final linear/split callback expands its selector
sequence from `[5, 7, 1, 8, 0, 9]` to
`[5, 7, 1, 8, 0, 9, 12, 11, 13, 14]`. These facts establish the expanded
roster/evolution presentation inputs without guessing from call counts.

## Confirmed five-state choice cycle

The split callback reads the high nibble of the presentation-state byte, uses
that old value to choose a case, and then stores `(old + 1) modulo N` back to
the high nibble. WSC 1.0 uses `N=3` at `1000:006E`; the GBA conversion preserves
the same three-state policy at `0x03002330`. WSC 1.5 changes only the cycle size
and dispatch population to `N=5`.

| State | Commercial GBA callback | WSC 1.5 callback | Selector pair |
|---:|---:|---:|---:|
| 0 | `0x080873CC` | `958C` | `[5, 7]` |
| 1 | `0x080876DC` | `97CC` | `[1, 8]` |
| 2 | `0x08087A48` | `99FE` | `[0, 9]` |
| 3 | absent | `9E40` | `[13, 14]` |
| 4 | absent | `9C17` | `[12, 11]` |

This identifies the two added selections: state 3 presents the new base-fighter
pair, and state 4 presents the two new evolution IDs. The GBA implementation
must therefore extend the existing state byte in place, preserve states 0..2,
and translate both new case setup blocks and both selected callbacks. A forced
single-case diagnostic route would not reproduce the retail policy.

## Static GBA integration

`tools/build_opening_integration.py` now performs that bounded choice-path
translation. It replaces the commercial split hook at ROM offset `0x086E48`
with a dispatcher at `0x085B4000`, keeps retail states 0..2 on their original
case entries, and adds:

| State | Case setup | Callback | Converted tables |
|---:|---:|---:|---:|
| 3 (`[13,14]`) | `0x085B4100` | `0x085B4600` | `0x085B5200`, `0x085B5280` |
| 4 (`[12,11]`) | `0x085B4300` | `0x085B4C00` | `0x085B5300`, `0x085B5320` |

The builder requires the exact v32 input and exact WSC 1.5 source, verifies
hashes for every translated WSC source range and reused commercial GBA range,
requires all expansion targets to be blank, and records every placement hash.
Frame durations use the retail-derived rule `floor(WSC * 4 / 5)` and signed
motion terms use truncation toward zero of `WSC * 5 / 4`; coordinates and
event IDs are unchanged. Two independent clean builds from the three original
ROMs produced byte-identical internal v33 SHA-256
`05324D1AD61D8AF7F399E14BD35260710F62628333C48859ECDDE199ADFC762D`.
This is static callback-code integration evidence only. The commercial GBA
presentation resource view at `0x080D42B8` is still unchanged in v33; its
Ver. 1.5 records for selectors 11..14 must be rebuilt and repointed before the
new cases can be treated as complete presentation integrations.

## Added linear-chain dependency boundary

`tools/analyze_opening_linear_additions.py` fixes the exact insertion boundary.
Commercial GBA callback `0x08085118` currently assigns successor
`0x08085454`; the assignment instruction is at ROM offset `0x08516C`. Its
character selector is assigned as 3 at `0x0851CC`, while the aligned WSC 1.5
callback changes it to 13. The four new callbacks then run in this order before
the commercial successor:

| WSC 1.5 callback | Bytes | Selector | Additional resource dependency |
|---:|---:|---:|---|
| `7077..7407` | 912 | 14 | replacement resource record 50 |
| `7407..7698` | 657 | 8 | none beyond the presentation record |
| `7698..7992` | 762 | 9 | none beyond the presentation record |
| `7992..7D28` | 918 | 3 | replacement resource record 49 |

Records 49 and 50 at WSC 1.5 raw offsets `0x740620` and `0x740640` are not
relocations of their WSC 1.0 counterparts: all five pointer targets are
replaced. The two complex callbacks directly consume pointer fields 0 and 2
through WSC loaders `4FFF:226E` and `4FFF:2389`. The commercial WSC creators at
raw `0x39FC37..0x39FCDA` and
`0x75A58C..0x75A62F` use 0x20-byte resource records; their native GBA consumer
is `0x08088250..0x08088310`, which maps WSC constructor `4FFF:23F4` to
`0x080127E4` and companion loader `4FFF:2389` to `0x080132EC`. A direct native
counterpart for the callbacks' primary loader `4FFF:226E` is not yet proven.
Therefore the remaining work includes converting the two directly consumed
resource fields, resolving that primary-loader boundary, and attaching a safe
second GBA presentation object; a callback-only chain splice would be
incomplete.

## Reproduction

The evidence is regenerated from the three hash-identified originals with:

```text
python tools/analyze_opening_initializer_population.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-initializer-population.json
python tools/analyze_gba_opening_dispatch.py <USA-GBA> --output evidence/gba-opening-callback-graph.json
python tools/analyze_wsc_opening_dispatch.py <WSC-1.0> <WSC-1.5> --output evidence/wsc-opening-callback-graph.json
python tools/analyze_opening_linear_additions.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-linear-additions.json
```

Current generated-manifest SHA-256 values are:

- initializer population: `EB621403F9385C970A1571C0716FE5C1239414362F3DB93DC670A1566B91B253`
- GBA callback graph: `77E64A38FEDE93B1712758D0C67F674D3C9A4F723F77689403D060A4A80E981A`
- WSC callback comparison: `4EE9A0F13CCAC897600ACA3E52E80EDC125D17808720B4398599B2B2AA9EE098`
- linear-addition dependency ledger: `A846CB79139FB0B74B480EEB7EDA86D458E2AB860F93FD5066492E529DDEBE6C`

## Runtime evidence boundary

The graph, reachability, and v33 integration results above are static evidence.
No emulator was run for this milestone. A prior WSC 1.0 hidden/chromeless BizHawk attempt parsed
its command line but did not start the Lua capture and produced no PNG, RAM
dump, completion log, or runtime evidence. It remains `INCONCLUSIVE` and is not
cited as validation. The exact diagnostic script is retained at
`tools/bizhawk_capture_wswan_intro_reference.lua`.

## Remaining proof gates

1. Convert WSC 1.5 presentation records 11..14 and replacement auxiliary
   records 49/50 into the native GBA resource/object ABI.
2. Translate the four added linear callbacks and aligned selector-3→13 change
   into the commercial GBA opening state machine.
3. Preserve the complete 19-linear + 5-choice graph through the single
   reproducible candidate build.
4. Only after all declared port content is integrated, run a non-displaying
   cold boot through the full extended sequence and verify skip-to-title.
