# WonderSwan 1.0 to Ver. 1.5 lineage

## Evidence boundary

The comparison uses the exact retail inputs identified in `initial-survey.md`.
The original game's digest and 4 MiB size match the MAME software-list entry
`digitbs1`; Ver. 1.5 matches `digitbs`. The user-supplied SRAM was not opened,
parsed, copied, or used by this comparison.

## Confirmed table lineage

- The original contains the same 60-record, `0x20`-byte five-pointer resource
  table at raw offset `0x390000` that Ver. 1.5 contains at `0x740000`.
- Pointer-bank normalization depends on ROM capacity. The physical bank is
  `bank & (bank_count - 1)`: 4 MiB uses a `0x3F` mask and 8 MiB uses `0x7F`.
- Base character records remain indices `0..14`; evolution records remain
  indices `30..44`. This confirms that Ver. 1.5 extended reserved logical IDs
  instead of renumbering the original roster.
- In the original, base records 12 through 14 and evolution records 41 through
  44 point to placeholder bundles. Ver. 1.5 replaces those slots with the new
  or newly enabled character content. Record 11 already contains Impmon's base
  bundle in the original, while evolution record 41 is replaced in Ver. 1.5.

## Exact-copy map

The aligned exact-byte comparison found 2,134 copied intervals of at least
`0x100` bytes. Their union covers 3,147,353 bytes of the 4 MiB original and
3,275,846 bytes of Ver. 1.5. This is a relocation map only: unmatched bytes can
be relocated pointer-bearing structures or edits and are not automatically
classified as new content.

For unchanged base records `0..11`, fields P1 through P4 generally relocate as
exact byte copies. P0 animation headers differ at their embedded addresses even
when their underlying planar tiles are shared. The comparison therefore gives
stable old/new pairs for the supporting containers without treating pointer
rewrites as content changes.

## P4 behavior-container conversion corpus

The original WSC and retail GBA base-character bundles provide 12 paired P4
containers, totaling 289 corresponding records.

- WSC container: `u16 table-relative`, `u16 count`, `u16[count]` relative item
  offsets, followed by `0x24`-byte items.
- GBA container: absolute `u32` table pointer, `u32 count`, `u32[count]`
  absolute item pointers, followed by `0x34`-byte items.
- Seven WSC relative-pointer halfwords per item expand to seven absolute GBA
  pointers. All 2,023 pointer comparisons in the base-character corpus match
  this structural rule.
- The first three logical dwords mostly carry through, but 46 of 867 samples
  are deliberate platform adjustments. Common scalar changes match the 75 Hz
  WSC to 60 Hz GBA timing relationship: durations commonly scale by `4/5`,
  velocities by `5/4`, and acceleration-like values by `25/16`. Some command
  types contain hand-tuned exceptions and must not be converted by an
  unconditional field-wide formula.

Evolution P4 containers are not a one-to-one record conversion. For example,
original WSC evolution ID 0 has 20 items while the GBA counterpart has eight
and uses different state identifiers. A complete port must map those states by
consumer semantics or use a validated GBA evolution template; base-character
conversion evidence cannot be generalized to this path.

## P1 command-container conversion corpus

For original runtime IDs `0..10`, P1 begins with a command table in both
versions. The GBA table adds one platform-specific leading command and then
retains the WSC command population. Across 254 paired commands:

- WSC payload items are `0x0C` bytes; GBA items are `0x10` bytes and every
  observed added four-byte tail is zero.
- Payload item counts and the first five halfword fields are frequently
  changed or reordered. Only the sixth WSC halfword is invariant at the same
  item index throughout the current corpus.
- WSC command entries point to small animation/geometry tables outside the P1
  container. GBA command entries likewise point to converted tables located
  immediately before the P0 animation header. Those dependencies are not
  included in the current standalone animation blobs.

Therefore a raw `0x0C` to `0x10` expansion is insufficient. The P1 converter
must translate the external animation/geometry tables together with P0 and use
their relocated addresses. Existing animation blobs remain valid format
experiments but are not complete character bundles.

## Current decision

Use the original/GBA pairs as the conversion oracle for P1 and base P4, with
command-specific rules and exact-corpus regression tests. Keep the evolution
P4 path separate. The newly confirmed placeholder lineage fixes all target
record IDs, but does not by itself prove runtime consumption or gameplay
equivalence.
