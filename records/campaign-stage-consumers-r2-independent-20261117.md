# Campaign revision2: independent AI progress and HUD verification

Revision2 passes independent checks for the missing AI progress-table rows
and decimal round display. It completes the two newly identified consumer
gaps in the earlier ADBF producer component. The producer verifier and report
remain frozen and are reused as an explicit predecessor gate.

Input ADBF is `ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9`.
Final isolated image
`build/campaign-stage-progression-v80-20261117-r2/component.gba` is
`933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775`.
Its manifest is `6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C`.
New independent verifier is `tools/verify_campaign_stage_consumers_r2.py`.
Final report
`build/campaign-stage-consumers-independent-v80-20261117-r2/audit.json` is
`3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84`.

## AI tables are indexed by progress

The retained helper at `080C8248` reads config `+1E`, persisted progress at
`0300232E`. It does not read physical stage `+0E` or RNG row `+1F`. Source
`782C34`, `782C93`, `782CBB`, `782CDF` and `782D08` independently establish
that same progress owner for all five table lookups.

At source CS base `782970`, three pointer families at offsets DD,107,131
each select three twelve-byte difficulty rows. The family at17F selects
three twelve-halfword rows. The native pointers at `080C7048..7074` previously
selected nine-entry rows. All retained byte-row prefixes agree exactly with
the source; all 27 retained native halfwords equal `floor(source*4/5)`.
The extension preserves that proven native conversion for the remaining
halfwords. This is a narrow data-family unit contract, not a claim of global
wall-clock or hardware timing equivalence.

The difficulty-zero first table at source offset185 has thirteen bytes
`7,7,6,6,5,5,4,4,3,3,3,3,3`. The first ten native bytes agree, but the following
native bytes belong to another table. A small adapter at `08D3FFDC` redirects
the retained lookup at `080C6EEC` to the complete thirteen-byte source row,
then branches back to `080C6EF0`. No writable state or speculative clamp is
introduced.

The verifier executes the actual four native consumer segments, including
their typed field writes:

| Consumer | Native outcome checked |
|---|---|
| `080C6F6C..6FA4` | Add byte to AI field+6, mask to low nibble |
| `080C6FA4..6FCC` | Add source byte to native halfword at03004DCA |
| `080C6FCC..6FFC` | Store source byte as halfword at03004DCC, mask007F |
| `080C6FFC..7020` | Signed halfword lookup and add to native field+22 |

There are 864 typed consumer cases: all twelve progress entries, all three
difficulties, three independent physical-stage values and two RNG rows,
across four consumers. Configuration neighbors and unrelated AI fields are
preserved. Thirteen separate first-table lookups verify the retained caller
stack and restored r0/r5.

The existing strict interpreter required two narrowly checked additions:
the exact retained register-offset `LDRSH r0,[r5,r0]` at `080C700C`, word
`E19500F0`, and immediate post-index unsigned halfword transfers. The former
performs an actual signed16 load; the latter executes the actual HUD/fill
stores. Neither uses a mocked AI result, and no old interpreter file changed.

## Decimal progress and final label

Source `77E389` compares progress against10. Other values display progress+1
using decimal quotient/remainder; progress9 therefore displays two digits,
“10”. The old native path compares against7 and only writes one numeric tile.

The adapter at `08D3FFA4` follows the source partitions:

- Progress0..8 enters the retained one-digit numeric path at `080B5FBC`.
- Progress9 writes native digit tiles2215 and2214, then fills seven blank
  words2201 through the actual native fill helper `08001064`.
- Progress10 enters the retained final-text path at `080B6044`.

The source tile base2400 and retained native tile base2200 are not conflated.
The test checks the actual native decimal digits, exactly nine output words,
the unchanged neighboring tiles, final destination pointer, and balanced
stack. All eleven progress states, all sixteen incoming NZCV combinations,
and both halfword alignments are exercised: 352 cases. Numeric cases execute
the existing fill loop rather than substituting a service result. Final-label
cases stop at the exact retained text-path entry and verify its ABI; they do
not claim graphical rendering evidence or rerun a previous language suite.

Ten semantic mutations are rejected: each of four old short-row pointer
families, the old short first table, an unconverted new halfword, using
physical stage instead of progress, final label at7, the wrong second digit,
and eight blanks after the two-digit value. The third short byte family is
tested at progress9 because its accidental progress10 value happens to match;
the negative control does not accept coincidence as coverage.

## Owned storage and preserved predecessor

The exact independent definition is 29 writes, 313 declared bytes and 297
changed bytes. It includes nine 12-byte rows, three 24-byte rows, the 13-byte
first table, twelve row pointers, a 52-byte HUD adapter and hook, and a 12-byte
first-table adapter and hook. All instructions and literal words are checked
against an independently assembled integer opcode definition.

The new interval is raw `D3FEE0..D40000`, within the established audio
reservation. Four frozen prior manifests establish ownership: audio,
evolution tables, ID13 callbacks, and the ADBF campaign producer. All 46
relevant preceding writes are checked against both input and output, and
none overlaps the new interval. The conservative whole-ROM pointer/control/
literal/ADR scanner reports zero incoming references without exemptions.

Reversing only the 29 new spans reconstructs the entire ADBF image. Reversing
the pinned earlier producer spans then reconstructs FBD9 exactly. Thus the
first producer's CPU map, RNG-row formula, default-mode challenge behavior,
getters and special0010 branch remain unchanged. The old producer semantic
suite is not rerun; its completed independent report1162 is pinned, and full
binary composition proves preservation.

This result closes the specific AI/HUD issues noted in
`records/campaign-stage-progression-independent-20261117.md`. Root owns the
new hidden first-entry observation, main integration, complete builds and
publication. Default source mode remains the scope; this report does not
claim alternate-mode implementation, an eleven-round playthrough, graphical
runtime parity or complete-port readiness.
