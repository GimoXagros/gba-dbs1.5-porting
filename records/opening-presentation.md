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
This is static integration evidence only.

## Reproduction

The evidence is regenerated from the three hash-identified originals with:

```text
python tools/analyze_opening_initializer_population.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-initializer-population.json
python tools/analyze_gba_opening_dispatch.py <USA-GBA> --output evidence/gba-opening-callback-graph.json
python tools/analyze_wsc_opening_dispatch.py <WSC-1.0> <WSC-1.5> --output evidence/wsc-opening-callback-graph.json
```

Current generated-manifest SHA-256 values are:

- initializer population: `EB621403F9385C970A1571C0716FE5C1239414362F3DB93DC670A1566B91B253`
- GBA callback graph: `77E64A38FEDE93B1712758D0C67F674D3C9A4F723F77689403D060A4A80E981A`
- WSC callback comparison: `4EE9A0F13CCAC897600ACA3E52E80EDC125D17808720B4398599B2B2AA9EE098`

## Runtime evidence boundary

The graph, reachability, and v33 integration results above are static evidence.
No emulator was run for this milestone. A prior WSC 1.0 hidden/chromeless BizHawk attempt parsed
its command line but did not start the Lua capture and produced no PNG, RAM
dump, completion log, or runtime evidence. It remains `INCONCLUSIVE` and is not
cited as validation. The exact diagnostic script is retained at
`tools/bizhawk_capture_wswan_intro_reference.lua`.

## Remaining proof gates

1. Translate the four added linear callbacks and aligned selector-3→13 change
   into the commercial GBA opening state machine.
2. Preserve the complete 19-linear + 5-choice graph through the single
   reproducible candidate build.
3. Only after all declared port content is integrated, run a non-displaying
   cold boot through the full extended sequence and verify skip-to-title.
