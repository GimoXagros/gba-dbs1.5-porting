# Companion record21: unchanged source lineage, no justified repair

The apparent record21 graphics gap does not establish missing Ver.1.5 content.
WSC1.0 and WSC1.5 have the same eight layouts, the same896-byte planar tile
payload, the same complete320-byte P1 container, and both same38-byte palettes.
The retained USA GBA resource has different art and a coordinated nine-layout
P0/P1 population. Replacing only its P0 pointer with the eight-layout source
resource would leave a reachable native P1 layout8 outside that resource.
No asset builder, pointer change, candidate ROM, or main-build change was made.

## Exact inputs and resource provenance

| Input | SHA-256 |
|---|---|
| Frozen v70 | `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717` |
| USA GBA | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |
| WSC1.0 | `58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735` |
| WSC1.5 | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |

The frozen input is `build/repro-v70-20261106-a/current-candidate.gba`.
All following addresses are ROM offsets unless a full bus address is shown.

| Resource | WSC1.0 record18 | WSC1.5 record21 | USA GBA retained resource |
|---|---|---|---|
| Resource-table row | `390240` | `7402A0` | retail `0D41F8`; current `4A8398` |
| P0 | `2B3D90` | `09FF40` | `1FBFB0` |
| Layout count | 8 | 8 | 9 |
| Descriptor table | `1AFFE0` | `1FFFE0` | `1FC098` |
| Tile payload | `2AACB0` | `3C5E80` | `1FC0A0` |
| Tile bytes | 896 | 896 | 896 |
| P1 | `2B2460` | `23FEB0` | `1FBDF0` |
| Palette | `2B5A50` | `3D77C0` | retained native record palette |

Source pointers were resolved using each ROM's actual bank population, not a
fixed128-bank mask. The old descriptor table is therefore1AFFE0, not5AFFE0.
Existing `build_character_p0_completion.source_layout/converted_tiles` and
`build_full_asset_poc.parse_wsc_far_descriptor/convert_tile` were reused for
the source layout and planar-to-packed comparison. The GBA layout population
was obtained from its first layout pointer1FC008 minus table1FBFC0, divided
by8. Comparing only the first eight native entries had missed its ninth entry.

## What the comparison proves

All eight source layout records match between1.0 and1.5. The raw896-byte
tile payloads also match, before any conversion; their SHA-256 is
`1E6EA160B729792CB1F686945C27D57D2751C382E86FB61DE1C9FF3F00E7CEDD`.
The corresponding native packed tile payload hash is
`814666DA1FFAF92523FC811F4E312F051E5EA7C5AD05F04A150ADCC969FED61C`.
Forward conversion and independent pixel decoding distinguish the
representations. The597 differing packed bytes across28tiles are real art
differences, not evidence of a broken tile converter or a1.5-only delta.

All5events/19commands and metadata of the complete320-byte source P1 body
match byte-for-byte between versions. Their layout-index sequences are:

| Event | WSC1.0 and1.5 | Retained USA GBA |
|---|---|---|
| 0 | `0,1` | `0,1` |
| 1 | `2,3,0,2,0` | `2,3,4,2,3` |
| 2,3,4 | `4,5,6,7` each | `5,6,7,8` each |

Source P0 metadata bytes+8..+16 are `05001B0060030800` in both sources
and the native header. Both source palette resources match byte-for-byte.
Independent composition uses signed layout coordinates, the actual low-byte
tile index,4000/8000 flips, transparent pixel0, and sprite ordering. The art
differences survive composition; they are not simply different tile packing.
See the independent evidence in
[companion21-source15-qa-20261106.md](companion21-source15-qa-20261106.md).
Its host-only analysis and frozen result are
`build/companion21-provenance-qa-20261106/audit.py` (SHA-256
`DCEBA0B2833D8BE33AED781FB50129697E2B01A80719DBC3C2C167F542DE1510`)
and `audit.json` (SHA-256
`794D329A0B08E98217E222E0CB16ACA7E8A9E98E3492F3D1F6DFD619EA94F588`).
All19 actual paired commands have different composited pixels; the independent
report records each count and small decoder/composition assertions.

This establishes unchanged source content and an existing coordinated retail
native difference. It does not establish why the commercial art was changed,
nor does it prove every source/native difference elsewhere is intentional.
There is no evidence here of a1.5-only missing resource or wrong record
identity. The stated project scope adds1.5 content/behavior to the USA base;
the copied task in `ASTRA_HANDOFF.md` also requires a small diagnostic check
when evidence changes a proposed design. It does not justify replacing this
shared base artwork from a raw mismatch alone.

## Proposed placement also rejected

The whole proposed reservation`6FF000..6FF480` is FF in frozen v70, but the
strict conservative reference scan fails. The frozen
`verify_shoot_caller_resident.inbound` scanner finds one Thumb BL/BLX-like
candidate at`3559C8` targeting bus`086FF1B0`. Its source SHA-256 is
`7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D`.
The private scanner invocation only substitutes this reservation's SPANS;
there are no data/interior exemptions and no imported-module mutation.
This is a conservative encoded-reference hit, not proof of a live call.
It still rejects the proposed reservation under the required strict rule.
No alternate placement was sought after the repair premise failed.

The terminal worker's`6FE100..6FF000` reservation was untouched. v70 remains
the exact input above. No main rebuild is required for this diagnosis.
No provided save was opened or hashed, and no emulator or guest write ran.
Terminal lifetime/clear correctness and whole-port completion are separate
work and are not claimed by this record.
