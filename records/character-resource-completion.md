# Character resource completion, 2026-10-16

The added fighters had multiple independent data-format failures. Correct
physics-table pointers did not cause the opening renderer overflow. The
opening selector repair is documented separately in
`opening-presentation-routing-repair.md`. This record covers the subsequent
P0 completion and the canonical fighter resource table/P4 repair.

No supplied save file was read, copied, hashed or run. These are static build
and inverse-consumer results. Runtime validation is owned by the parent task.

## P0 descriptor populations and companion graphics

`tools/build_character_p0_completion.py` takes the opening-routing output
`E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D`.
Its output is
`973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D`,
at `build/character-p0-completion-20261016/current-candidate.gba`.

The former descriptor parser stopped at a segment change. The source far
descriptor format permits that change. Complete source P1 event geometry,
all source commands and their actual descriptor selections bound the missing
population; no terminator or blank-space scan supplies the count.

| Source record | Existing native P0 | Old/full descriptors | New descriptor table |
|---:|---:|---:|---:|
| 14, base ID14 | `08420AC0` | 260 / 324 | `087C1100` |
| 43, evolved ID13 | `084E85E0` | 59 / 77 | `087D9440` |
| 44, evolved ID14 | `084FB380` | 61 / 78 | `087F6200` |
| 36, opening selector12 | `0850D000` | 79 / 88 | `087FAD00` |

The full tables point to existing valid pixel payloads after exact planar
conversion comparison. Only previously missing pixels are appended. Existing
layout arrays stay intact. Source companion records27/28/29/56/57/58/59 receive
complete P0 layouts, their one descriptor, all pixels and their palettes.
Their P0 flag disables descriptor indexing, so P1's varying tile field does
not select additional descriptors for these records.

The actual new intervals are `7C1100..7C9280`, `7D9440..7DE600`,
`7F6200..7FACE0`, `7FAD00..7FCBC0`, `60B400..60B8A8`,
`60B8C0..60BE88`, `60BEA0..60C468`, `60C480..60CA68`,
`60CA80..60CFC8`, `60CFE0..60D5E8`, and `60DB80..60E1E8`.
All end addresses in this record are exclusive. Potential inbound targets
`60DB54` and `60E204` remain untouched; they are not classified as data.

The independent `tools/verify_character_p0_completion.py` passes. Its report
at `build/character-p0-completion-20261016/verification.json` hashes to
`9330DCE05012EC852202F59A5994F9362B193035DB6A1D68E43D78C325E6ECEB`.

## Native resource ABI and four groups

The real native resource record starts at retail raw `0D3FB8`. It contains
P0, P1, primary palette, alternate palette and P4 at byte offsets
`0,4,8,12,16`, followed by twelve zero bytes. The previous expanded table was
changed to this canonical origin, but its new-field writes retained the old
eight-byte bias. Added P0/P1 values therefore occupied the preceding record's
padding, and palette/P4 addresses occupied the intended record's P0/P1 slots.

Native `08353390..083533AC` consumes P0/P1 directly; `083533B8..083533C0`
selects primary/alternate palette; `08353408` consumes P4. The companion
pointer is stored into the actor's `+80` field at `0835349C`. Native
`083593E0`, `083594DC`, `0835950C..0835952C`, and `083595A8` subsequently
consume the companion's P0/P1/palette/P4. These are actual consumers, not
similar-looking record offsets.

Source `7437B1..7438B5` shifts the fighter ID by five, adds `3C0` for
evolution and `1E0` for its companion. The commercial source constructor
`393386..393472` uses the corresponding twelve-row `300` / `180` deltas.
The resulting native groups each have fifteen records:

| Group | Native address | Source records |
|---|---:|---:|
| Main | `084A80F8` | 0..14 |
| Companion | `084A82D8` | 15..29 |
| Evolved main | `0860B000` | 30..44 |
| Evolved companion | `0860B1E0` | 45..59 |

The same evolution delta now works for both main and companion resources.
All46 retained commercial rows are copied exactly from the original native
table. The14 added rows use the completed source assets. Every record's last
twelve bytes are zero.

Only three dynamic evolution-view literals change: raw `3534B8`, `0CC230`
and `0CC708`. The latter two belong to native selector branches that test
resource flag4000 and shift the low-byte fighter ID by five. The twelve
remaining opening-view literals keep `080D42B8`; opening selector13 retains
the separately repaired `085B5400` view. A global replacement would conflate
different selector domains.

## P4 timing, flags and links

Native `083584A0..083584A8` loads source P4 word3 into actor `+94`.
Source `781064..78106B` writes its counterpart `+7E`. Source timed states
`781907` and `781926` decrement that field and transition when negative;
native `083590E4` and `083590F8` do the same. Base ID13 item11 selects a live
timed state. The legacy per-value oracle left its duration36 unchanged by
borrowing an unrelated commercial tuning value. The explicit75-to60 Hz
conversion gives29.

Source `781831..7818D5` selects motion words7..10, then
`781094..7810D4` assigns or adds them to actor `+32/+34/+36/+38`. Native
`08358FD0..08359098` and `083584F8..08358578` perform the same operations on
`+42/+44/+46/+48`. Flags, indices and the input mask are preserved. In
particular word4 is an input mask at native `083583A8..083583C0`, and a
class-dependent actor value at `08358434`; it is not a generic velocity.

The explicit policies are duration4/5 with nearest-away rounding, velocity
5/4 with truncation toward zero, and acceleration25/16 with the documented
nearest-even X / nearest-away Y rounding. Integer quantization remains a
fidelity limit. Reemitting the seven existing main P4 containers changes only
three halfwords: the duration36 to29 and two velocity175 conversions from
219 to218. All flags and links remain source-derived. A packed state word
uses only its low byte as the five-entry state selector; the high byte stays
intact.

Companion records27 and29 reuse native P4 at `080FE400` and `0815E9FC`.
Their complete80-byte and156-byte source bodies exactly equal commercial
source records12 and14; the native counterparts also equal the explicit
conversion. Five remaining companion P4 containers occupy actual intervals
`60E240..60E2F0`, `60E2F0..60E410`, `60E410..60E4F8`,
`60E4F8..60E5E0`, and `60E5E0..60E6C8`. Every nonzero source link maps to a
declared item and every P4 event index lies inside its complete P1 population.

## Second palette block

Base ID13 source primary/alternate palettes at `3D5470` / `3D54B8` contain
two blocks each. The former converter emitted only the first40 bytes. This
is reached by source event111 command0: its flags contain0200 and its A
metadata at+6 selects block1. Native `0801297C..080129B0` forwards that
selector to `080132EC`, whose reader computes `palette +4 +34*selector`,
reads the bank, skips transparent color0 and copies the other15 colors.
Source `7525D4..7525F5` uses the same A metadata field.

Both full72-byte palettes now reside at `0860E700` and `0860E748`.
The header and bank words are preserved; all32 colors per palette use the
existing explicit RGB444-to-native conversion. Both resource pointers change
to these complete payloads. The independent verifier checks selector1 and
all palette blocks, not only the first native color copy.

## Artifact and verification boundary

`tools/build_character_resource_routing.py` takes the complete P1 output
`3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA`.
The candidate at `build/character-resource-routing-20261016/current-candidate.gba`
hashes to `3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065`.
Its manifest records each Expected Write, every added resource and all P4
source/native words. The builder's native walk checks all2742 complete P1
commands against their actual P0 layouts and selected pixel buffers, plus
all dynamic palette selectors.

The independent `tools/verify_character_resource_routing.py` passes. Its
report at `build/character-resource-routing-20261016/verification.json` hashes
to `476488DE9B0413D53BACA1125B41241FC6322ACB54D2AA139E20E187CCFE6C2A`.
It independently checks all60 records, all14 source P4 graphs, both complete
ID13 palettes and the live selector1, the three scalar repairs and three
dynamic evolution literal changes.

New allocations require exact FF contents and no unaligned-inclusive pointer
or aligned ARM B/BL-like inbound candidate. The complete final byte diff must
equal the declared writes. No RAM or callbacks are allocated. Runtime results
remain a separate completion gate; this record does not claim gameplay QA
from static data checks.
