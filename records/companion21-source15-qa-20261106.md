# Record21 companion provenance: no repair justified

**The prior “missing source1.5 companion P0 content” diagnosis is withdrawn.**
The byte/layout mismatch is real, but is already a difference between the
commercial WSC1.0 and USA GBA versions. The reviewed WSC1.5 asset adds no change
over WSC1.0. A source-eight-layout P0 replacement alone would break the actual
retained nine-layout native animation ABI. No builder, allocation or ROM change
is justified by this finding.

Independent inputs are original WSC1.0 `58220B9C...`, WSC1.5 `C415F227...`,
retail GBA `996DE333...` and current v70 `8EC8C507...`; full identities and
results are in `build/companion21-provenance-qa-20261106/audit.json`.

| Owner | Record | P0 | Descriptor | Tile payload |
|---|---:|---:|---:|---:|
| WSC1.0 | 18 | `2B3D90` | `1AFFE0` | `2AACB0`, 896 bytes |
| WSC1.5 | 21 | `09FF40` | `1FFFE0` | `3C5E80`, 896 bytes |
| Retail/current GBA | native companion6 | `1FBFB0` | `1FC098` | `1FC0A0`, 896 bytes |

All eight source layouts, all 28 source tiles, both 38-byte palette resources,
and the complete 320-byte P1 resource are byte-identical between WSC1.0 and
WSC1.5. The P1 locations are respectively `2B2460` and `23FEB0`. Current native
P1/P0/payload span `[1FBDF0,1FC420)` is byte-identical to retail. Its live group
row still points to P0 `081FBFB0` and P1 `081FBDF0`; the shared P0/P1 renderer
span `[127E4,12DC8)` is also retained retail code.

Native has **nine** layouts: first-part pointer `1FC008` minus table `1FBFC0`,
divided by eight-byte native entries. Comparing only the first eight layouts
misses that ABI fact. All five events and 19 commands were followed:

| Event | WSC1.0/1.5 layout sequence | Retained native layout sequence |
|---|---|---|
| 0 | `0,1` | `0,1` |
| 1 | `2,3,0,2,0` | `2,3,4,2,3` |
| 2, 3, 4 each | `4,5,6,7` | `5,6,7,8` |

The independent pixel comparison decodes source bitplanes and native nibbles,
uses the actual low-byte tile selector (`08012D50`), signed part coordinates,
H/V flips, transparent index0 and earlier-part priority. It compares the union
of coordinates, counting absent pixels as transparent. No source frame matches
any of the nine native frames exactly. Actual paired-command differing pixel
counts are `149,140,119,113,147,119,101`, then `130,129,145,137` for each of
events2–4. All 28 native tiles differ, totaling597 packed bytes. Thus this is
not merely equivalent tiling; it is retained original native artwork/animation,
with no reviewed 1.5 source delta. The exact artistic intent is not inferred.

Host-only analysis script SHA-256:
`DCEBA0B2833D8BE33AED781FB50129697E2B01A80719DBC3C2C167F542DE1510`.
Frozen JSON SHA-256:
`794D329A0B08E98217E222E0CB16ACA7E8A9E98E3492F3D1F6DFD619EA94F588`.
Small assertions check both pixel storage formats, flips, signed coordinates
and composition behavior. No repair verifier was created for a nonexistent
repair. Proposed reservation `6FF000..6FF480` was not used.

This corrects the record21 interpretation in
`shoot-companion-clear-lineage-20261106.md`; that historical record was not
edited by this QA worker. It does not certify runtime rendering, whole-port
content completeness or terminal clear lifetime. No emulator, supplied save,
guest writes, main builder edits or production ROM edits were used.
