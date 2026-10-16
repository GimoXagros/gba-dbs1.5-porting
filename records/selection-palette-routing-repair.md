# Selection palette routing repair, 2026-10-16

The existing portrait hook contained two incorrect PC-relative offsets.
At native `084A5C44`, ARM's PC is instruction+8; immediate38 therefore reads
the word at `084A5C84`, which contains palette RAM address `05000020`, rather
than the portrait-pair table at `084A5C80`. The next instruction at
`084A5C48` similarly reads `084A5BC4` as its DMA destination instead of
`05000020`.

Consequently the palette stage treated palette RAM as a table of ROM pointers
and requested a transfer into ROM. The tile stage used the correct literals.
This is a concrete address calculation defect; it does not by itself establish
the cause of every visual artifact observed on the selection screen.

`tools/build_selection_palette_routing_repair.py` changes precisely:

| Raw instruction | Before | After | Correct literal/value |
|---:|---:|---:|---|
| `4A5C44` | `E59F8038` | `E59F8034` | `4A5C80` → `084A5BC0` |
| `4A5C48` | `E59F5038` | `E59F5034` | `4A5C84` → `05000020` |

Only two actual bytes change. No allocation, RAM state or callback is added.
The tile-source table, tile destination, selection-state write, and call/stack
behavior remain byte-identical.

Native `08000B84..08000BA4` writes DMA3 source/destination/count and control
8400. The two counts8 and600 therefore copy32 palette bytes and6144 tile
bytes. This nine-instruction routine does not write r1, so the same character
ID reaches both indexed loads. The final store writes ID+1 to `0300472E`, as
the commercial loader does. All fifteen palette/tile source pairs are bounded
inside the ROM; the first twelve pairs equal the retail table exactly.

The input is the verified callback6 layer,
`A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949`.
The result at `build/selection-palette-routing-20261016/current-candidate.gba`
is `C5152150749B1E16C7B39BCF7E67C69810FE31C970CCA78988828921DA9AC017`.

The separate `tools/verify_selection_palette_routing_repair.py` passes with
26 native instruction contracts, all15 finite DMA traces, eight negative
cases and a complete ROM inverse check. Its report at
`build/selection-palette-routing-20261016/verification.json` hashes to
`BB7C2B169796F71EAF2FFD39E1A8AB6CE7300E979EF8D108B967B4B49423E2AD`.
An independent agent also checked the actual PC arithmetic, DMA consumer,
preserved r1 and final state store; it found no additional semantic issue.

## Natural roster input

The roster hook at `085B0000` writes IDs0..10,13,14 and optionally appends
the two unlock-controlled IDs11/12. Its returned count13..15 is decremented
and stored by `08081710..08081718`. The native input consumer tests internal
bit4 at `08081BDC` and increments the low cursor byte at `08081D50`; bit1
decrements it at `08081D28`. Internal bitsA instead reach `08081CD8`, which
XORs0100 and changes the palette variant without advancing the character.

The parent-owned hidden runtime probe used eleven Down pulses and naturally
reached ID13. `build/physics-consumers-added13-20261016/probe.json` identifies
ROM `3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065`,
reports no guest-memory writes, and captures two `083530CC` hits with r1=13
and r1=1 and table base `08485000`. This confirms selection and physics entry;
it does not claim final battle graphics correctness.

## Authorized presentation scope

The parent task records user approval to use the English Digicode table only
for Latin characters within the Japanese presentation. This palette-address
layer does not alter language selection, fonts or character tables. That
approved presentation change has its own implementation and validation.

No supplied save file was accessed. This agent did not launch an emulator;
all runtime control and final visual confirmation remain with the parent task.
