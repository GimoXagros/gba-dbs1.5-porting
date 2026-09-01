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
ROMs produced byte-identical internal v34 SHA-256
`33CDF2FDB1E374A424E21D4C80CB9ED98CB7B1BBE4F0409BE8C8943C679650E1`.
This is static callback-code and resource integration evidence only.

The commercial GBA presentation view at `0x080D42B8` corresponds to WSC
resource records 24..34 for selectors 0..10. Ver. 1.5 records 35..38 supply
selectors 11..14. `tools/build_opening_presentation_assets.py` proves that all
four P1 containers are byte-identical to their commercial selector 5..8 source
lineages, all four P2 palettes convert exactly to resident GBA palettes, and
selectors 11/13 share the exact resident commercial P0. Only selector 12 and
14 P0 containers are nonresident; their guarded converted blob is placed at
`0x0850D000..0x08540920`. The rebuilt 15-record view at `0x085B5400`
preserves selectors 0..10 byte-for-byte and supplies the three native pointers
consumed by `0x08088250` for each new selector.

Two clean builds produced opening P0 SHA-256
`2F085D49410AFAEA4A5AC9EEF7ECC806CFF6E8095FFAA8305EC801A551829151`,
resource-view SHA-256
`8EFF8EC1B0CBBD7334563D8EA55B920E67BA8D88883FD334F7929E29B615DBD3`,
and identical v34 manifests. Runtime behavior remains unverified.

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

`tools/analyze_opening_linear_callback_semantics.py` now fixes the
implementation-facing state machines as well as their raw bounds. Callbacks
7, 8, and 9 have closest commercial WSC 1.0 templates 7, 8, and 9, which map
to GBA functions `0x08085454`, `0x080857E4`, and `0x08085D44`. Callback 10 is
only 0.512998 similar to old callback 9 and is classified as a bespoke
translation because it owns a seven-entry event table and activates a second
object on event `0x25`.

| Added callback | Initial timer | Main position/event | Timed events | Auxiliary behavior |
|---:|---:|---|---|---|
| 7 | `0x6E` | `(0x40,0x68)`, event 0 | `0x5A→0x21`, `0x34→0x22`, `0x2A→0x23` | record 50; object `0x0952`; event-0x23 motion `(-2,+1)` |
| 8 | `0xAA` | `(0x9E,0x68)`, event 0 | `0x43→0x1A` | none |
| 9 | `0xB4` | `(0x40,0x68)`, event 0 | `0x96→0x1D` | shared event-table driver |
| 10 | `0x64` | `(0x96,0x68)`, event 2 | shared event-table driver | record 49; event `0x25` creates object `0x0994` at `(0x54,0x58)` |

The shared table at `0x7976` is exactly
`[(0x0B,6),(0x0C,9),(0x0D,30),(0x0E,24),(0x23,24),(0x24,8),(0x25,500)]`.
Skip populations are one object for callbacks 8/9 and two objects for 7/10.
These are source semantics, not an ARM implementation claim.

`tools/analyze_opening_linear_timing_translation.py` additionally anchors the
implementation constants to exact commercial WSC 1.0/GBA instruction pairs.
The retail conversion uses a 4/5 duration scale, while motion ratios vary by
template family. Applying those bounded rules produces this static plan:

| Added callback | GBA timers | Fade decrement | Basis |
|---:|---|---:|---|
| 7 | setup 8; events `0x21/22/23` at 72/41/33; fade 83; successor 86 | 11 | commercial template 7 |
| 8 | setup 8; event `0x1A` at 53; fade 76; successor 136 | 16 | commercial template 8 |
| 9 | setup 8; event `0x1D` at 120; fade 108; successor 136 | 14 | commercial template 9 |
| 10 | setup 8; fade 132; successor 78; table durations 4/7/24/19/19/6/400 | 7 | absolute timing plus nearest motion family |

Changed successor timers are translated as a signed delta from the matching
commercial WSC/GBA pair rather than by blindly scaling the absolute value.
These constants are implementation inferences, not runtime evidence; perceptual
timing and transition correctness remain part of the deferred non-displaying
QA. Both normal/skip auxiliary-object lifetimes also remain gates.

Records 49 and 50 at WSC 1.5 raw offsets `0x740620` and `0x740640` are not
relocations of their WSC 1.0 counterparts: all five pointer targets are
replaced. The two complex callbacks directly consume pointer fields 0 and 2
through WSC loaders `4FFF:226E` and `4FFF:2389`. The commercial WSC creators at
raw `0x39FC37..0x39FCDA` and
`0x75A58C..0x75A62F` use 0x20-byte resource records; their native GBA consumer
is `0x08088250..0x08088310`, which maps WSC constructor `4FFF:23F4` to
`0x080127E4` and companion loader `4FFF:2389` to `0x080132EC`.

`tools/analyze_opening_aux_resource_reuse.py` now closes the pixel/palette
conversion part of that boundary without claiming the callback implementation.
For record 49, WSC P0 at `0x3D3E20` (33 tiles / `0x420` bytes) converts exactly
to the native GBA P0 container at `0x082D94D8`, including its tile descriptor
at `0x082D95CC`; WSC P2 at `0x3D7880` converts exactly to the 40-byte GBA
palette block at `0x082D99F4`. For record 50, WSC P0 at `0x3D5620` (12 tiles /
`0x180` bytes) converts exactly to `0x082F91CC`, with descriptor
`0x082F9260`, and WSC P2 at `0x3D6960` converts exactly to palette block
`0x082F93E8`. All four converted containers are byte-identical to data in the
unmodified USA GBA ROM, and their native pointer references are asserted.

The same proof now closes the full native record path rather than only the
pixel/palette subset. WSC 1.5 record 49 P1 is byte-identical for its complete
`0x90`-byte bounded container to WSC 1.0 record 39 P1; record 50 P1 is
byte-identical for `0xB4` bytes to WSC 1.0 record 41 P1. The corresponding
complete GBA record views are:

| WSC 1.5 record | Native GBA record view | First three consumer fields |
|---:|---:|---|
| 49 | `0x080D4498` | `0x082D94D8`, `0x082D9428`, `0x082D99F4` |
| 50 | `0x080D44D8` | `0x082F91CC`, `0x082F90A0`, `0x082F93E8` |

The hash-guarded GBA consumer selects `record + selector*0x20` and creates the
target at `0x03002908 + slot*0x50`. Passing either complete view with selector
0 therefore replaces both WSC low-level loader calls through the native GBA
ABI; no direct translation of `4FFF:226E` is required.

Therefore no duplicate auxiliary payload is needed. The remaining boundary is
now bounded by `tools/analyze_opening_aux_object_lifetime.py`. WSC 1.5 creates
objects `0x0952` and `0x0994` during opening setup, but their complete
bank-local reference populations confine active use to callbacks 7 and 10,
respectively. Those callback ranges do not overlap.

The commercial GBA consumer uses opening slots 0, 1, and 2 at
`0x03002908 + slot*0x50`. Slot 3 is `0x030029F8`; it has no aligned literal
reference anywhere in the retail ROM and its 0x50-byte extent ends exactly at
the independently referenced task-count field `0x03002A48`. The retained
commercial auxiliary objects at `0x03002778` and `0x030027C8` therefore do not
need to be overwritten. Internal v35 implements the bounded translation plan:
it constructs record 50 in slot 3 during the callback-6→7 transition,
uses/includes it only in callback 7, then reconstructs record 49 in the same
slot during the callback-9→10 transition and uses/includes it only in callback
10. Callbacks 8 and 9 retain one-object skip populations; callbacks 7 and 10
use two.

## Added linear-chain GBA integration

`tools/build_opening_linear_integration.py` consumes exact v34 and installs
the four ARM callbacks plus native adapters at these guarded expansion ranges:

| Role | GBA address | Bytes |
|---|---:|---:|
| Added callback 7 | `0x085B6000` | 508 |
| Added callback 8 | `0x085B6800` | 308 |
| Added callback 9 | `0x085B7000` | 400 |
| Added callback 10 | `0x085B7800` | 484 |
| Predecessor successor hook | `0x085B8000` | 16 |
| Predecessor record-50 hook | `0x085B8040` | 20 |
| Primary/auxiliary constructors | `0x085B8100`, `0x085B8200` | 112, 104 |
| Object update / skip adapters | `0x085B8300`, `0x085B8400` | 56, 164 |
| Converted callback-10 event table | `0x085B8500` | 28 |

The predecessor selector word at ROM offset `0x0851CC` changes from 3 to 13.
The successor assignment at `0x08516C` branches through the new chain, and
the stack-cleanup edge at `0x0851E8` constructs record 50 in slot 3. Callback
9 initializes the source-derived countdown state and reconstructs record 49
before callback 10. Callback 10 consumes the converted table
`[(0x0B,4),(0x0C,7),(0x0D,24),(0x0E,19),(0x23,19),(0x24,6),(0x25,400)]`,
activates the auxiliary object on event `0x25`, and returns to the commercial
successor with selector 3.

`tools/analyze_opening_linear_integration.py` independently compares exact
v34 and v35. It confines all 2,199 changed bytes to the declared hooks and
placements, disassembles all callback call targets, checks successors and
selectors, ensures event `0x1E` occurs only in callback 9, and verifies the
converted event table. Three full builds from the three original ROMs produced
identical v35 SHA-256
`9E3D495A3E07F2A9A6ECCF3C07E446036AD027B2A32666DD5A5984879BA6AA5F`.
This establishes reproducible static integration, not runtime behavior.

## Reproduction

The evidence is regenerated from the three hash-identified originals with:

```text
python tools/analyze_opening_initializer_population.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-initializer-population.json
python tools/analyze_gba_opening_dispatch.py <USA-GBA> --output evidence/gba-opening-callback-graph.json
python tools/analyze_wsc_opening_dispatch.py <WSC-1.0> <WSC-1.5> --output evidence/wsc-opening-callback-graph.json
python tools/analyze_opening_linear_additions.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-linear-additions.json
python tools/analyze_opening_linear_callback_semantics.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-linear-semantics.json
python tools/analyze_opening_linear_timing_translation.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-linear-timing.json
python tools/analyze_opening_aux_resource_reuse.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-aux-resource-reuse.json
python tools/analyze_opening_aux_object_lifetime.py <USA-GBA> <WSC-1.0> <WSC-1.5> --output evidence/opening-aux-object-lifetime.json
python tools/analyze_p1_conversion.py <USA-GBA> <WSC-1.0> --wsc-table 0x390300 --gba-table 0x0D42A0 --records 11 --output evidence/opening-p1-conversion-corpus.json
python tools/build_opening_presentation_assets.py <USA-GBA> <WSC-1.0> <WSC-1.5> evidence/opening-p1-conversion-corpus.json <opening-assets-directory>
python tools/analyze_opening_linear_integration.py <v34-candidate> <v35-candidate> <WSC-1.5> --output evidence/opening-linear-integration.json
```

Current generated-manifest SHA-256 values are:

- initializer population: `EB621403F9385C970A1571C0716FE5C1239414362F3DB93DC670A1566B91B253`
- GBA callback graph: `77E64A38FEDE93B1712758D0C67F674D3C9A4F723F77689403D060A4A80E981A`
- WSC callback comparison: `4EE9A0F13CCAC897600ACA3E52E80EDC125D17808720B4398599B2B2AA9EE098`
- linear-addition dependency ledger: `A846CB79139FB0B74B480EEB7EDA86D458E2AB860F93FD5066492E529DDEBE6C`
- linear-callback semantic ledger: `1CBBA71D6DD9EE7A7D3D902A16B26A1DC232D05C660886B740DD209E6DB8DBFC`
- linear-callback timing plan: `97EAF415097BFF9AEF3C29DC2904F1C24556EBA10B1BC08A644335C0BBD6780F`
- auxiliary resource/native object-path proof: `52D7F0602C94C8D434F314C0CF318CD80F187F68BB1F88FE10A5C05AA6DF70FA`
- auxiliary object lifetime/slot plan: `499C7A8AAC5B7B864A8CA2EB4956224C889331ADB74D4E70AB80250BF9DC9E8D`
- opening P1 conversion corpus: `B9F671AB5FE6E66DA7351AFFFAFD7C6E4D07370E84D231E501A6D8C51B52B887`
- opening presentation asset manifest: `32F3ED03234C65C88ED33A99562A9C5F0E62246D31A0FBA74BA7E5DFEF167278`
- opening linear build manifest: `03EDEE1360CB95379F2AAA9AC25F25378579B5252D408A30DDA12650F57B72D3`
- opening linear static verification: `15BA39813EE3B54BFA3181251432310E558420D2491A8FF4AAE8825D5DC6FB80`

## Runtime evidence boundary

The graph, reachability, and v35 integration results above are static evidence.
No emulator was run for this milestone. A prior WSC 1.0 hidden/chromeless BizHawk attempt parsed
its command line but did not start the Lua capture and produced no PNG, RAM
dump, completion log, or runtime evidence. It remains `INCONCLUSIVE` and is not
cited as validation. The exact diagnostic script is retained at
`tools/bizhawk_capture_wswan_intro_reference.lua`.

## Remaining proof gates

1. Preserve the complete 19-linear + 5-choice graph while the remaining
   non-opening Ver. 1.5 content is integrated.
2. Only after all declared port content is integrated, run a non-displaying
   cold boot through the full extended sequence and verify skip-to-title.
