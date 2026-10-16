# Opening callback 6 source parity — 2026-10-16

This separate layer completes the four remaining setup differences in the
already repaired callback-6 resource route. It follows the canonical character
resource ABI layer; it does not modify any earlier generator or output.

The old WSC callback at raw `39D97C..39D9AC` constructs selector 3, writes
X=`96`, Y=`68`, ORs flags with `4800`, selects event 2, and loads VS palette
selector 3. Commercial GBA `080851CC..08085230` preserves those values.
WSC1.5 `756F05..756F3D` instead constructs selector 13, writes X=`9E`,
Y=`68`, performs a separate `AND BFFF` flag write followed by `OR 0800`,
selects event 0, and loads VS palette selector 13. The matching old source
and GBA coordinate establish that X=`9E` is a source change; no blanket
eight-pixel screen adjustment is inferred.

The earlier routing repair already changed the constructor's resource-view
literal. This layer changes native instructions only at `080851EC`,
`080851FC`, `08085210`, and `08085220`. The replacement at `080851FC`
branches to six ARM7TDMI instructions at `08621C00..08621C18`. They load
presentation flags through r4, clear `4000`, store, set `0800`, store again,
then branch to the existing continuation `08085208`. Only r8 is clobbered;
SP, LR, CPSR flags and all other registers are preserved. Y and the event
loader's existing stack contract remain unchanged. The existing auxiliary
constructor bridge returns before the position writes and is byte-pinned.

The complete 32-byte reservation `621C00..621C20` is FF in the exact
predecessor. A complete-ROM scan found no little-endian pointers at any
byte alignment and no aligned ARM B/BL-like inbound target. The replaced
flag block `851FC..85208` also has no encoded external entry in that scan.
Only 24 bytes are allocated. There are five Expected Writes and 31 actual
changed bytes; the inverse restores the exact predecessor. No RAM owner
or additional rendering routine is introduced.

## Actual palette and tile consumer

Source helper `558C:4C5C`, raw `75A51C..75A58C`, and the older helper
`39FBC7..39FC37` establish the same resource-loading operation. Selector 13
selects source descriptor `3CEDE0`; its C2-window segment/bank fields
resolve to tiles `36F6A0`, palette `3D8950`, and 74 tiles. C2 maps the
linear `20000..2FFFF` window; that window base is subtracted before adding
the selected ROM bank.

Native helper `080881F0` loads the existing expanded VS descriptor table
from literal `08088244` (`084A7C60`), multiplies the selector by 28, reads
tiles from row `+0`, palette from `+4`, and tile count from halfword `+16`
(hex). It copies 74 * 32 bytes to `06004000`, 16 colors to `05000000`, and
those colors to its original shadow `02018020`. Selector 13 currently
resolves to native tiles `084A5D20` and palette `084A5D00`.

Both validation directions check all 4,736 pixels and all 16 colors against
the original source. The expected source tile SHA is
`D60170207CFDAC952DB385F009CD50C1A517C322B9750A2F9D8D66B8EBA74C09`;
the source palette SHA is
`C2C9B2C6338DC969DC9279DDF1D726C07847956185104D45A974C6AA12A97A02`.

## Artifacts and independent verification

Builder: `tools/build_opening_callback6_parity.py`.
Separate verifier: `tools/verify_opening_callback6_parity.py`.

| Artifact | SHA-256 |
| --- | --- |
| Input `build/character-resource-routing-20261016/current-candidate.gba` | `3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065` |
| Output `build/opening-callback6-parity-20261016/current-candidate.gba` | `A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949` |
| Manifest `build/opening-callback6-parity-20261016/manifest.json` | `94C4AAC81487C460CFB480E6D88F72FE9BB327B99836446D8D34F3648FF1097A` |
| Verification `build/opening-callback6-parity-20261016/verification.json` | `1F7673D861FFA2342ABDA367CA4EF661E63CFABFD4D8EDCD6586DAF7BF65EB00` |

Independent verification is PASS. It imports neither the generator nor its
manifest, checks 31 native instruction contracts, compares the source and
commercial setup, exhaustively checks both ordered flag writes for all
65,536 input halfwords, reverses the complete diff, and rejects ten semantic
mutations. Runtime observation remains root-owned and separate. This layer
does not claim completion of unrelated opening callbacks, language support,
or every playable route. No provided save was accessed and no emulator was
launched by this workstream.
