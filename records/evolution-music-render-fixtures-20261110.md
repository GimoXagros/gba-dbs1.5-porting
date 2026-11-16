# Isolated original/native evolution-music render fixtures

These eight ROMs are **audio-driver test fixtures**, not normal gameplay
builds. They let ordinary boot invoke each selected score through the original
drivers. They do not prove ordinary evolution activation or complete restoration.

The root's read-only ordinary-boot observations established source request
`DC/type4` at frame520 and four initialized payload pointers
`8A94,8C60,8FF4,9332` at521. They exactly match original table entries `DC..DF`.
The isolated native r1 component requests song`01/type4` at534, consumed at535.
This positive observation determines the fixture targets; no title is inferred
from a number alone.

For each original group `38,3C,40,F8`, the source fixture copies its four
six-byte table descriptors onto `DC..DF` at `3F0528`. The only other write is
the recomputed checksum at `7FFFFE`. The native fixture copies the corresponding
appended song-table row `6C..6F` onto row`01` at `D33008`: one eight-byte write.
Its player fields remain`0,0`, and the selected header has four tracks.

Every fixture has complete Expected Writes, whole-ROM diff containment and an
exact inverse back to the original source or isolated DD6D73B5 component.
The original source files, component r1, and main build are unchanged. The
generator rejects aliases and existing output directories. It neither starts
an emulator nor accesses saves, RAM or registers.

Files are in `build/evolution-music-render-fixtures-20261110-r1/`:
`wsc-source-{38,3C,40,F8}-boot-fixture.wsc` and
`gba-source-{38,3C,40,F8}-boot-fixture.gba`.

| Item | SHA-256 |
|---|---|
| `tools/build_evolution_music_render_fixtures.py` | `DAB6E9274AF918B3FAA4BC9D34FB5A4E15892336437BD827868F137628EDD8E1` |
| Fixture `manifest.json` | `FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F` |
| Original boot-discovery log | `47B26B2B7A50D9D4329CBB7116330FA5BDC688FCC32DA1CA26A445949EAEEA04` |
| Native boot-discovery log | `7A08C04540340A261BB2253E26ACF45B2054ECE463F40C1429C18BC00F9AA57F` |

The planned4400-frame captures must also log later music requests. Dump length
alone does not establish that a song finishes before a later boot scene replaces
it. Actual captures, independent fixture QA, musical identification, and source
versus native audible comparison remain pending at this record's creation.
