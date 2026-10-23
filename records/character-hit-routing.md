# Source-backed hit and dependent follow-up routing

## Result and scope

The requested native hit tables `0836BF08`, `0836BF38`, and `0836BF68` each
contain twelve character rows; their WSC1.5 counterparts contain fifteen.
The third table's action records also produce a pointer to the twelve-row
follow-up table `0836BF98`. Extending only the first three tables leaves that
actual downstream character lookup short. The repair therefore installs four
fifteen-row views, redirects seven existing literals and four embedded pointer
words, and retains all native code and original tables.

The source proof enumerates all 2,498 P1 events of sixty canonical character
resources, including event and command collision pointers. This reveals a
source-prescribed subrecord index8: it crosses from the first action population
into the third population. The original contiguous record layout is preserved.
No arbitrary index clamp or fallback is introduced.

The repair is built on title candidate `143ECA1C…`, whose relevant combat
contracts were checked directly again. This task does not certify the title
component. Independent hit verification and runtime are separately tracked.

## Exact source and retail tables

| View | Native original, 12 rows | WSC1.0, 12 rows | WSC1.5, 15 rows | Native record base | New native view |
|---|---|---|---|---|---|
| Hit A | `0836BF08..0836BF38` | raw `3A6E3C..3A6E54` | raw `76304A..763068` | `0836C32C` | `08629390` |
| Hit B | `0836BF38..0836BF68` | raw `3A6E54..3A6E6C` | raw `763068..763086` | `0836C3AC` | `086293CC` |
| Hit C | `0836BF68..0836BF98` | raw `3A6E6C..3A6E84` | raw `763086..7630A4` | `0836C42C` | `08629408` |
| Follow-up | `0836BF98..0836BFC8` | raw `3A6E84..3A6E9C` | raw `7630A4..7630C2` | `0836C4AC` | `08629444` |

Every row within each table selects the corresponding common record base.
The old source CS base is raw `3A45B0`; the new base is `75FFD0`. The four
source record bases are respectively old `3A71CE/3A724E/3A72CE/3A734E` and new
`763458/7634D8/763558/7635D8`. Each nominal population has four 32-byte records;
all four populations are contiguous. Distinct following table values independently
fix the 12-row and 15-row boundaries. These are not the separate thirteen-row
recovery table repaired previously.

In the predecessor, added IDs12–14 read the next table's first three entries.
Hit A consequently selects `0836C3AC`, Hit B selects `0836C42C`, Hit C selects
`0836C4AC`, and the follow-up selects `0836C52C`. Those are different actions
from the source-selected records. The repair retains the pointer identities
of all 48 original in-bounds rows and supplies the twelve added routes.

## All actual literal and metadata consumers

| View | Raw pointer sites | Actual native readers | Index/variant |
|---|---|---|---|
| Hit A | `36B238` | `0836B04C..0836B068` | Character `+11`; fixed variant3 |
| Hit A | `36F7C0` | `0836ECEC` → `0836F3B8` | Target character `+11`; A byte4 variant |
| Hit A | `36FCE0` | `0836FC44..0836FC64` | Character `+11`; delayed variant from `+A0` |
| Hit B | `36F7C8` | `0836ED38` → `0836F3B8` | Target character `+11`; A byte4 variant |
| Hit B | `378838` | `083787EC..08378814` | Character `+11`; fixed variant3 |
| Hit C | `354C84` | `08354B00..08354B24` | Character `+11`; initial variant0 |
| Hit C | `36F7D4` | `0836ED90` → `0836F3B8` | Target character `+11`; A byte4 variant |
| Follow-up | `36C438/36C458/36C478/36C498` | Descriptor `+0C` → fighter `+9C`; `0836AE08..0836AE2C` | Character `+11`; variant from `+AA` |

The source generic selectors are old `3A4B99/3A4BC0/3A4BEC` and new
`760679/7606A0/7606CC`. They join old `3A5079` / new `760C05`, which index by
target `+11`, add variant times32, and invoke the source action reader.
Native `0836F3DC` is the corresponding action-reader call.

The other source readers are explicitly checked as instruction sequences:

- Hit A variant3: old `3A58BD`, new `761479` and `761A9D`.
- Hit A delayed variant: old `3A67D8`, new `7629C4`.
- Hit B variant3: old `3B10A2`, new `76C562`.
- Hit C initial variant0: old `3929FA`, new `742CE2`.
- Follow-up through the stored table: old `3A575B`, new `761317`.

A scan of every byte alignment for pointers into any byte of the four native
tables finds exactly the eleven sites above, with no additional interior
aliases. Every actual PC-relative reader of the seven literals is also
enumerated. All four embedded follow-up words are produced by real action
records and consumed by the common action helper, rather than being incidental
constants or unused table entries.

## Typed records and callback lineage

All sixteen records preserve their old/new source flags, events, and complete
consumed metadata. Callback far pointers relocate from `A45B` to `5FFD`.
For Hit C only, source metadata word `+0E` also relocates from the old follow-up
table offset `28D4` to `30D4`. Its native counterpart is the 32-bit pointer at
descriptor `+0C`, copied to fighter `+9C` by `08355638/08355640`.

The analyzer records all twelve source metadata words and their twelve native
fields for every record, including counters, status bytes, pointer/scalar field,
motion, and final selector. The 512-byte retail record oracle is pinned and
the current bytes are checked against it. Existing retail temporal/spatial
conversions are reused; no universal conversion rule is inferred from them.

Hit A, Hit B, and the follow-up use source callback old `3A579F`, new `76135B`,
and native `0836AE94`. Their source constructor has 97 identical bytes followed
by a 19-byte tail with explicit continuation and hitstop-service relocations.
Hit C uses old `3A5612`, new `7611CE`, and native `0836AC20`; its constructor has
75 identical bytes plus the corresponding 19-byte relocated tail. The native
constructors remain the retail implementations. This is bounded constructor
lineage, not a claim that every downstream callback or service was compared.

## Actual subrecord populations and index8

P1 A metadata reaches collision-entry `+10` through the native presentation
reader. `0836E374..0836E394` copies A halfwords `+0/+2/+4` into `03004D20+2/+4/+6`.
The generic action path reads byte `03004D26`, so the selector is A byte4.
Old source `3A45DF..3A45F3` and new `75FFFF..760013` copy the same words to locals;
their generic readers consume byte `BP-2`.

All sixty canonical P1 resources are traversed through their actual current
tables and compared with all source events. The 2,498 current event selectors
are 2,365 zeros, 125 ones, five twos, and three eights. Event and command B
records establish the collision-type/variant combinations; the native and new
source sets agree. Eight pre-existing retail/source variant edits are listed
explicitly in the report, rather than treated as new conversion rules.

The requested generic branches select Hit A for collision types9/11, Hit B for
type10, and Hit C for type12. In canonical P1 resources, type9 has variants
`0/1/2/8`; type11 has no producer; types10/12 have `0/1`. The native forced
paths at `0836EE98` and `0836EF6C` select Hit B variants0 and3. The fixed readers
also supply variant3; delayed Hit A reads the selector saved in fighter `+A0`.

Evolution ID14's source record44 events26/27 preserve A byte4=8 and contain
type9 collision records. Native `0836C32C + 8*32 = 0836C42C` corresponds exactly
to source `763458 + 8*32 = 763558`: both select the first Hit C record. Base
ID13 event108 also has variant8, but its type8 collision branch is outside the
three requested generic views. The report records it without treating it as
a Hit A producer.

Hit C's descriptor initially supplies `+AA=0`. Its generic category2 path can
overwrite that field from the same A byte4 before `0836AE08` later consumes
the stored follow-up table. Thus the required follow-up dependency applies
both to direct Hit C selection and to the Hit A variant8 cross-block route.
Cloning only Hit C's four records would miss the original records still
reached by variant8. Updating the four original follow-up pointer words keeps
the whole contiguous route coherent.

Canonical P1 enumeration is a bounded producer analysis. Noncanonical collision
producers, other adjacent hit tables, and three additional WSC1.5 record groups
after this family remain outside this task. These limits are not a runtime
completion claim.

## Exact repair and verification state

`tools/build_character_hit_routing.py` reserves raw `629390..629480`, the next
sixteen-byte aligned range after recovery ends at `62938C`. The four-byte gap
and all 240 table bytes are `FF` on the exact title predecessor. The builder
scans all alignments and interior addresses for encoded pointers, plus ARM
branches, literal accesses, ARM ADR, and Thumb ADR references into the range.
No inbound candidate is found under those bounded scans.

The layer declares twelve spans: eleven four-byte pointer redirects and one
240-byte table payload. There are 284 declared bytes and 273 changed bytes.
Restoring those spans reproduces the entire predecessor. All original table
bytes remain intact; the sixteen action records differ only at the four
declared follow-up pointer words. Native instructions, RAM ownership, previous
action/recovery tables, and alignment padding remain unchanged. No new action
descriptors are allocated.

The builder calls the source analyzer on the actual title predecessor before
writing. It does not use a generated manifest or assume that the earlier A18
proof automatically covers a later ROM. Repeated builds produce identical ROM
and manifest bytes. The frozen A18 source-analysis report is also reproduced
byte for byte, with sixteen controlled negative cases rejected.

```text
py -3 tools/analyze_character_hit_routing.py CURRENT GBA OLD NEW OUTPUT
py -3 tools/build_character_hit_routing.py BEFORE GBA OLD NEW OUTPUT --manifest MANIFEST
```

Analysis CURRENT is the A18 recovery candidate. Builder BEFORE is
`build/title-language-a18-20261023-a/title-language.gba`. The original GBA,
WSC1.0, and WSC1.5 inputs are explicitly supplied and SHA-256 pinned. Builder
OUTPUT and MANIFEST are `current-candidate.gba` and `manifest.json` within
`build/character-hit-routing-20261023/`.

A separate agent's `tools/verify_character_hit_routing.py` independently passes
the exact title143E-to-hitA3E layer without importing the builder or analyzer.
It verifies all sixteen records, 240 nominal character/subrecord routes, and
fifteen complete variant8 graphs, including the four original embedded pointer
updates. It independently traverses 2,498 events and 12,506 commands across all
sixty canonical P1 resources, comparing 15,004 individual collision-type/null
edges with the source. No collision-type or null-presence differences occur;
the eight existing A-selector edits remain separately recorded. The three high
selector cases have actual collision-type sets `[0,8]`, `[3,9]`, and `[3,9]`,
so base ID13's type8 case remains correctly outside the three requested views.

Exact 284-byte write ownership and full inverse, all literal/metadata aliases,
interior references, and ARM/Thumb reservation checks pass. All 409 controlled
negative cases are rejected. Two verifier runs produce the same frozen report.

```text
py -3 tools/verify_character_hit_routing.py BEFORE AFTER GBA OLD NEW OUTPUT
```

BEFORE is the title143E predecessor and AFTER is the hitA3E candidate named
above. OUTPUT is `build/character-hit-routing-20261023/verification.json`.
The existing limits on noncanonical producers and full callback/service parity
remain in force. No emulator was launched and no `.sav` file was accessed by
the analyzer, builder, or independent-verifier agents.

## Bounded first-round runtime evidence

The parent ran the A3E candidate for 230 seconds with natural inputs and
inspected the resulting screenshot. The capture passes the parent's invariants
with 32 enabled OAM objects, intact renderer bytes (`D18F`), final S02, and no
asynchronous fault. The native mode is9, showing `CONTINUE? YES NO` with a
coherent Tailmon pose. This establishes the bounded transition from ID14's
first battle to the native continue outcome.

Capture: `build/runtime-hit-id14-round-20261023/capture.json`, SHA-256
`FC43DA3303E6665596E38B81F9FB8CE8ED4AE4CDCA59E20092962D9D528EDF65`.
It does not establish execution coverage of every hit variant, the complete
callback/service graph, or a full campaign.

## Artifact identities

| Artifact | SHA-256 |
|---|---|
| Source-analysis input A18 | `A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71` |
| Source analysis, both runs | `44F105C9E84A3B69CD626EB28EC023E62114F7EDD6CD9B1611DB24BF3B65DD0F` |
| Title predecessor | `143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80` |
| Hit candidate, both builds | `A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61` |
| Hit manifest, both builds | `13EC6428F91D275F8ABB1F851BBCC6EDBAA4AF37A79282B44D0F0464D85C147B` |
| Hit analyzer | `474DDA9C7A9C5442870ECBE32CDD95251B883E28158AF6B68DE5AD22CF800040` |
| Hit builder | `B7879300CFEDFBAB77899BAECD3128D50E06AF1483A682EE555A1BEE9E1D6909` |
| Hit independent report, both runs | `775EA0F411E73DA7940BFAA74DD9127CC88D896DD7D5C15C3802576BA3857DCE` |
| Hit independent verifier | `56CE2038FBDA2B8A3501595F2122BEF48E76705920FF1BCDD30F2542A8371B99` |
| Hit 230-second first-round capture | `FC43DA3303E6665596E38B81F9FB8CE8ED4AE4CDCA59E20092962D9D528EDF65` |
| Retail sixteen-record oracle | `05BC2738F672102357E8D054D112EF23F41B73A2B5B982209EABB6A8477F064C` |
