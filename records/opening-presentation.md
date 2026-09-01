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

| WSC 1.5 index | Body | Graph role | Object-selector arguments |
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

The graph identity and positions of the two new choice callbacks are now
bounded, but their exact runtime selection conditions and presentation meaning
are not yet named. They must be translated together with the added linear
callbacks rather than forced through a diagnostic-only route.

## Reproduction

The evidence is regenerated from the three hash-identified originals with:

```text
python tools/analyze_opening_initializer_population.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-initializer-population.json
python tools/analyze_gba_opening_dispatch.py <USA-GBA> --output evidence/gba-opening-callback-graph.json
python tools/analyze_wsc_opening_dispatch.py <WSC-1.0> <WSC-1.5> --output evidence/wsc-opening-callback-graph.json
```

Current generated-manifest SHA-256 values are:

- initializer population: `EB621403F9385C970A1571C0716FE5C1239414362F3DB93DC670A1566B91B253`
- GBA callback graph: `6E7238805853002CF3BAA1138C186C161377C4661D07AD794D213B6265F4462C`
- WSC callback comparison: `1A3B5EB958F43813A789D1CC46CB1B835C6669FDEB279062128246BFF952101D`

## Runtime evidence boundary

The graph and reachability results above are static evidence. No emulator was
run for this milestone. A prior WSC 1.0 hidden/chromeless BizHawk attempt parsed
its command line but did not start the Lua capture and produced no PNG, RAM
dump, completion log, or runtime evidence. It remains `INCONCLUSIVE` and is not
cited as validation. The exact diagnostic script is retained at
`tools/bizhawk_capture_wswan_intro_reference.lua`.

## Remaining proof gates

1. Determine the runtime selection conditions and semantic identity of the two
   additional WSC 1.5 choice callbacks.
2. Translate the four added linear callbacks, two added choices, and expanded
   selector behavior into the commercial GBA opening state machine.
3. Integrate the translation through the single reproducible candidate build.
4. Only after all declared port content is integrated, run a non-displaying
   cold boot through the full extended sequence and verify skip-to-title.
