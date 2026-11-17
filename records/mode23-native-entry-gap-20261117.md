# Separate mode23: bounded native entry gap

Read-only review of current75BD, retail USA996D, WSC1.0 `58220B9C…`,
and WSC1.5 `C415F227…`. No ROM, main build, save, emulator or Git changes.
The existing44-root/4052-instruction traversal in
[normal-entry source analysis](shoot-normal-entry-save-copy-20261109.md)
was reused, not repeated. Further mapping was deferred for the higher-priority
observed Waterfall visibility failure.

## Positive source entry chain

Source title confirmation `780CBE` reads tree pointer table CS:09A7,
raw780957. Root row4 opens tree2; tree2 row1 selects character selection.
The separate flag pointer table CS:096B, raw78091B, selects raw78092A for
tree2; its two bytes are `00 08`. After the title exit animation,
`780B1D..780B20` loads that selected byte and ORs it into
config `1000:004E+1A`. This is the actual producer of bit0008.
The availability predicate at780E76 uses copied save record
`0C00:392C+CA` bit0001 and substitutes event10 when unavailable.
The prior authorized-copy eligibility finding is reused; no save was read here.

Character-selection outgoing code `778BEA..778C4C` selects transition1
normally,3 for config+1A bit0002,4 for the separate selection-state flag,
and5 for config+1A bit0008. Source transition rows use six bytes:

| Source mode | Raw row | Bytes |
|---|---|---|
| 3 title | 74FA42 | `04 16 0E 02 13 00` |
| 4 character select | 74FA48 | `0F 06 14 12 05 17` |
| 20 | 74FAA8 | `03 00 00 00 00 00` |
| 23 | 74FABA | `14 00 00 00 00 00` |

Thus mode4 transition5 is source mode23 (decimal), while source mode23
transition0 is source mode20. The row is not evidence that arbitrary native
mode numbers have the same behavior.

Source mode23 registers `4090:A040/A041`, raw74A940/74A941. Init returns;
main creates source tasks C999/A56B/BC1C and initializes its private state
at0200:0012, selected identity at0200:001B from config+0A. Source cleanup
4090:A0FD, raw74A9FD, retires its three task handles at0200:0000/0002/0004;
74AA7E/83/88 then write config+4=1, +6=0, +8=0. The existing complete
traversal proves this is its separate local game, not the campaign stage11
terminal scene.

## Current native coverage and exact gaps

Current75BD retains these retail bytes exactly:

- Mode callback table `015B70..015C6C`:21 rows, modes0..20;
  SHA-256 `3082893D6E21A5E67660E3B5960AD62B821E84E924085EA6A1EF893F344F9C75`.
- Per-mode dispatch table `015C6C..015CC0`:
  `0FC15B7A1203175B6CEB3E12816CC611D9E3109460A764A956C681D7E686E655`.
- Five-byte transition rows `015CC8..015D31`:
  `DE5A1120D5E4FACCFFD9EDBB42C95DFA17A53643A022211FF8A1E210445F4CA9`.
- Character-select outgoing selector `081C64..081CD8`:
  `60E4772685059C90C6838F725B67602C9BA3D1BE9D42D2B335D3533DF937BC2A`.
- Title input/confirmation `090FA0..091268`:
  `9E341693E92F1C8DD79045BEA0F2552B03E6486098775D324C40343FAAF58C32`.

Native mode4's five transition bytes are `0F 06 14 12 05`. Its first five
destinations match the source row, but the sixth source destination is absent.
Native081C64 starts with transition1;081C7C tests only config+1A bit0002,
then selects3 or branches directly to081CB4. The source's second bit0008
test and transition5 assignment are absent. The ordinary title's native
flag table090F96 is only `00 05 00 02`; its consumer091134..091140 has no
tree2 selection. The added title background and five localized labels do
not implement the source menu tree or the missing flag producer.

The existing native selected identity/palette stores are08082010/08082018
to config+0A/+0B. Existing shared task/config/selection machinery therefore
supplies useful services, but the normal title cannot request this new route.

There is no registered native mode23 callback row. Interpreting the bytes
after the21-row native table as rows21..23 would interpret the following
dispatch table as initializer/constructor pointers. Similarly, merely
requesting transition5 under native mode4 would read the next mode's row.
The mode dispatch uses five-byte stride at015AEC and the following owners:
callback table readers0159E0/0159FC/015A20/015AD4, per-mode dispatch015AF8,
and transition row base015AF0. All required owners must be handled together.

## Completion target is not established by numeric equality

Native mode20 has init08040448, constructor08040470, two task priorities
1000/F100 and transition0→mode3. Source mode20's initializer7824E0 has
an exact53-byte prefix match at old WSC1.0 raw3C22F0; its constructor782535
also creates1000/F100 tasks. These are positive correspondence leads,
not a complete old-source/native behavioral proof. The source initializer
clears/copies palette staging and the native calls its palette service.
The exact service/task lineage, completion and ownership comparison was
not finished before this review was redirected. It would be incorrect to
label native mode20 a source-compatible mode23 completion target solely
because both transition rows return to3.

## Smallest justified next boundary

The missing flag0008 outgoing selector is a small, source-exact control
slice, but it cannot be exposed alone: it would enter unregistered code or
overread a five-column table. A complete normal entry needs the source tree
and eligibility presentation, its selected flag producer, character-select
transition5, all three mode-table consumers, a real mode23 scene with owned
tasks/resources/private state, and a proved completion target. No existing
native mode23 implementation has been established by this bounded review.

Before wiring a user-visible menu item, establish native equivalents or
new ownership for the three initial mode23 tasks and its private state, and
finish source20→old-source→native completion correspondence. Reuse the
already mapped44-root source graph; do not launch a fresh blind traversal.
No placeholder scene, forced mode, or button that leads nowhere is proposed.
