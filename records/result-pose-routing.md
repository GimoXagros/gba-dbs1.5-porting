# Result-pose table routing — 2026-10-23

The mode8 result screen still indexed two short native byte-pair tables after
the playable roster expanded to IDs0–14. This is a concrete resource route
defect, discovered while bounding the next language component. It is separate
from result-label translation. No source-only LOSE label behavior is added.

The exact predecessor is A3E
`A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61`,
`build/character-hit-routing-20261023/current-candidate.gba`.
`tools/analyze_result_pose_routing.py` reads that candidate and the three pinned
original ROMs. It does not import a builder or use a manifest as evidence.
No emulator or save file is accessed by this component's worker.

## Source producers and table boundaries

| Family | Native raw start | WSC1.0 raw interval | WSC1.5 raw interval |
| --- | --- | --- | --- |
| Win pose pair | `089774` | `3B5D7C..3B5D96` | `7771C0..7771E0` |
| Lose pose pair | `089790` | `3B5D96..3B5DB0` | `7771E0..777200` |

Source intervals are bounded by the adjacent table reference and actual
constructor entry. WSC1.0 stores26 bytes per table; WSC1.5 stores32. Both have
an explicit final00/00 pair. It is retained as indexed data, without assigning
it an unsupported fighter or sentinel meaning. Native tables are28 bytes
apart. The two bytes between each old26-byte payload and the next aligned
native entry are not assumed to be another playable character's animation.

The source constructor copies configuration bytes`+0A/+0C` into its two local
IDs at `77725C..777270`; WSC1.0 `3B5E0C..3B5E20` is byte-identical. Each ID is
doubled before loading low/high event bytes. Source CS bases are`3B5AD0` and
`776F10`, so the actual displacement readers resolve the tables above:

| Native pair load | WSC1.0 pair load | WSC1.5 pair load | Family |
| --- | --- | --- | --- |
| `0808A014` | `3B6281` | `7776B4` | Win, first fighter |
| `0808A030` | `3B628E` | `7776C1` | Lose, first fighter |
| `0808A12C` | `3B6316` | `777749` | Win, second fighter |
| `0808A148` | `3B6323` | `777756` | Lose, second fighter |
| `0808A174` | `3B6345` | `777778` | Win, second fighter draw route |
| `0808A190` | `3B6352` | `777785` | Lose, second fighter draw route |

Each x86 pair uses two five-byte instructions. Each native pair uses two
PC-relative pointer loads and indexed byte loads, then packs the high byte
at shift8. No sentinel or zero check occurs in these paths. The native
constructor records the low/high events in task payload`+4/+6`.

## Exact playable mapping

All event numbers below are hexadecimal. Rows0–11 have exact WSC1.0,
WSC1.5 and native byte identity. Only the six added-character pairs differ.

| ID | Source win pair | Source lose pair | Current native win / lose |
| ---: | --- | --- | --- |
| 0 | `6F 70` | `71 72` | Same |
| 1 | `79 7A` | `7B 7C` | Same |
| 2 | `5F 60` | `61 62` | Same |
| 3 | `6F 70` | `71 72` | Same |
| 4 | `80 81` | `82 83` | Same |
| 5 | `64 65` | `66 67` | Same |
| 6 | `71 72` | `73 74` | Same |
| 7 | `64 65` | `6E 6F` | Same |
| 8 | `82 83` | `84 85` | Same |
| 9 | `72 73` | `6C 6D` | Same |
| 10 | `64 65` | `66 67` | Same |
| 11 | `6B 6C` | `6D 6E` | Same |
| 12 | `6F 70` | `71 72` | `00 00 / 00 00` |
| 13 | `6E 6F` | `70 71` | `00 00 / 00 00` |
| 14 | `74 75` | `76 77` | `71 72 / 3F 40` |

ID14 reads the next table's first pair for its win route and the native
constructor's first instruction bytes for its lose route. These values may
remain inside its P1 population; that does not make their animation identity
correct. A bounds-only check would miss this defect.

## Actual animation consumer and complete frame population

The result constructor initializes both poses through`0801F3A8`. Its literal
at`0801F4A0` selects the base resource group`084A80F8`, indexed by ID*32.
There is no evolution-group adjustment in this presentation loader. Result
poses therefore use the base presentation resources even when the preceding
battle used an evolved fighter. The source counterpart`785A82..785B21` also
indexes its base resource record by ID*32.

Native callback`0808A94C` loads the first stored event through`0808A9C4`.
Callback`0808AA30` advances the animation, waits for presentation`+0A` bit2000,
sets task`+8` once, and loads the second stored event at`0808AAA0`. The native
driver at`08012A84` visits sequential commands and sets that completion bit
when a non-looping event ends. The second poses must retain their individual
loop/hold semantics; they are not all looping animations.

The proof walks every source-selected frame for all15 IDs: four pose events
plus unchanged events0,1,51,56 per ID, totaling120 events and1,252 frames.
Every native event count and command layout/tile/flags/scalar word matches
WSC1.5. Legacy selected commands additionally retain the exact retail native
bytes and source1.0 geometry. Each selected layout and actual tile descriptor
is bounded; renderer tile selection uses the low8 tile bits and descriptor
indexing follows combined P0/P1 flag2. No missing frame is filled by a template.

The independent glyph worker also traced all30 first poses to completion in
5–140 calls at delta1, before the222-call result-task countdown. Added IDs'
win/lose first-pose durations are136/71,31/19,16/37 calls respectively.
Their phase2 behavior is preserved. These are single-presentation frame
facts, **not** a complete mode8 aggregate OAM bound.

## Allocation and minimal write contract

The new source-exact views occupy raw`629480..6294C0`, immediately after the
frozen hit layer ending at`629480`:

| New view | Raw interval | Bytes |
| --- | --- | ---: |
| Win | `629480..6294A0` | 32 |
| Lose | `6294A0..6294C0` | 32 |

All64 predecessor bytes areFF. Ownership checks reject encoded references
at every byte alignment, including interior targets and the08/0A/0C ROM
mirrors, plus ARM branches/literals/ADR and Thumb branches/literals/ADR/BL.
The independent glyph worker separately confirmed this reservation and the
twelve exact old-table aliases. No allocation was moved heuristically.

The only redirects are twelve four-byte literal words:

- Win base: `08A418,08A43C,08A44C` →`08629480`.
- Win base+1: `08A41C,08A440,08A450` →`08629481`.
- Lose base: `08A420,08A444,08A454` →`086294A0`.
- Lose base+1: `08A424,08A448,08A458` →`086294A1`.

Total declared writes are112 bytes:64 table bytes and48 literal bytes. Both
original tables, all native code, P0/P1/palettes, prior allocations, task/RAM
ownership, event timing, and result-label behavior remain byte-identical.
The source final00/00 pair is copied exactly; no new ID or event is enabled.

## Reproduction and evidence

Analyzer positional arguments are`CURRENT GBA WSC10 WSC15 OUTPUT`, with
`--self-test` to run negative checks. Builder positional arguments are
`BEFORE GBA WSC10 WSC15 OUTPUT`, plus`--manifest MANIFEST`. Both pin the
original identities and exact A3E predecessor. The builder re-runs the source,
native-route, selected-frame and allocation proof before writing a new output.
It checks the full inverse of all13 declared spans and unchanged ROM size.

The frozen output is
`build/result-pose-routing-20261023-a/current-candidate.gba`, SHA-256
`DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C`.
Its manifest hashes to
`7B8BAB6F889804E0DF537A52D40DEBB64AD2401F2D1EC41AA989F7758A893D6A`.
The independently repeated `-b` ROM and manifest are byte-identical;
`build/result-pose-routing-20261023-comparison.json` hashes to
`B3A5B657AD578199E2F1E54D99723A31997385878A9C84E1641AF07348CBA395`.
There are112 declared bytes and100 actually changed bytes. All32 negative
checks reject malformed literals, indexed P1 frames, completion flags,
source rows, unexpected aliases, occupied storage, and inbound code/data
references.

The independent `tools/verify_result_pose_routing.py` has SHA-256
`AEF66D291436A850CCF001149AB6984032592EEFFEFAC3F3ADD5E61545DB9AD0`.
Its exact CLI is `BEFORE AFTER GBA WSC10 WSC15 OUTPUT`. The two independently
produced `verification.json` reports in the `-a` and `-b` directories are
byte-identical, SHA-256
`C399601AA969E290F9C61A345CDE035374235BFE0D40B1A6E68E01E7293FFB08`.
This verifies all112 declared/100 changed bytes and the complete inverse,
90 actual pair-consumer routes,120 events/1,252 frames,701 complete
source-equal atlases, and304 rejected negative cases. Phase2 holds for ID4 win
81h, ID7 lose6Fh and ID13 win6Fh are explicitly preserved.

The parent-owned natural ID14 match reached the corrected mode8 consumer.
`build/runtime-result-pose-id14-consumer-20261023/probe.json` hashes to
`B9FDDD0CD4D2C9658F78C414834231EF04BEF112CFBFBE31C8D5B1AC85B57BA4`.
At PC `0808A048`, r1=`1C` is ID14*2, r2=`7776` is the correct loss pair,
and r8=`086294A1` is the relocated loss view+1. At PC `0808A9C4`, r1 and
stack[0] both equal76h; task/presentation addresses are `020106A8/020106B4`,
side0. Both S05k stops were intended breakpoints, without guest writes,
asynchronous breaks or timeout. This establishes an actual corrected indexed
read and first-event selection, not merely a table-bounds assertion.

A subsequent202-second normal capture did **not** validate the result screen:
it remained in mode7 with an invalid nonzero battle callback and no screenshot.
The parent traced that separate failure to a missing third Waterfall pattern;
it is outside these112 bytes. Do not describe this table repair as a normal
result-screen runtime pass or as broad battle-stability certification.

The parent-owned230-second A3E ID14 round capture
`build/runtime-hit-id14-round-20261023`, capture manifest
`FC43DA3303E6665596E38B81F9FB8CE8ED4AE4CDCA59E20092962D9D528EDF65`,
reached mode9 Continue with32 OAM. It did not provide a stable mode8 pose
observation and cannot validate or refute this result-routing defect.

Full mode8 aggregate OAM analysis and four-language result labels remain a
separate gate. This bounded table repair does not certify whole-game behavior
or translation completion.
