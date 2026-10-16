# Independent character resource verification, 2026-10-16

This record covers the three resource gates after the physics routing and
opening presentation repairs. It certifies their stated static contracts,
not complete-game or visual runtime behavior. Original ROMs were read; no save
file or emulator was used by this verifier work.

## Reproducible gates

Each verifier accepts positional paths in the order shown. The independent
P0 and P1 verifiers import no generators or generated manifests. The final
routing verifier reuses only the independent P1 verifier's complete consumer
walk; its table, palette, P4, ownership and instruction checks are separate.

| Gate | CLI | Candidate SHA-256 | Verification report SHA-256 |
|---|---|---|---|
| P0 completion | `py -3 tools/verify_character_p0_completion.py before after gba wsc15 output` | `973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D` | `9330DCE05012EC852202F59A5994F9362B193035DB6A1D68E43D78C325E6ECEB` |
| Complete P1 | `py -3 tools/verify_character_p1_completion.py before after gba wsc10 wsc15 output` | `3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA` | `FAC5E6F50B55BF4789E4FB06EB6454DF1AFB8DCE5172E08A7F35275AD08E87E7` |
| Canonical resource routing | `py -3 tools/verify_character_resource_routing.py before after gba wsc10 wsc15 output` | `3D554185AE5686FA9FDD0D735D6EDCB9C7C3A2015EE2A60B7B85C914D0191065` | `476488DE9B0413D53BACA1125B41241FC6322ACB54D2AA139E20E187CCFE6C2A` |

Reports are respectively `build/character-p0-completion-20261016/verification.json`,
`build/character-p1-completion-20261016/verification.json`, and
`build/character-resource-routing-20261016/verification.json`. Their respective
predecessors are the opening routing candidate `E2B700D2...62AE4D`, the audio
candidate `10372B56...2B3354`, and the complete P1 candidate above. All input
identities are pinned in the verifier code; filenames alone are not accepted.

P0 checks derive descriptor populations from every source P1 event, distinguish
the source flag selecting one descriptor versus an indexed table, compare all
layout records, invert every native tile's pixels back to source bitplanes,
and check companion palettes. Four existing descriptor pointers and eleven
new allocation intervals are the only writes. Existing prefix descriptors
must retain their exact pointers and pixels. Fifteen negative fixtures cover
truncation, pointers, pixels, layouts, palettes, source window crossing,
renderer mutation and incoming references.

P1 checks decode all 544 events and 2,742 commands of the fourteen resources,
including every A8 metadata record, B10 collision record, nonnull command tail
and shared/null pointer relationship. Layout, tile, flags and remaining scalar
words retain source values. Every command is then interpreted against its
actual native P0 layout and descriptor. Ten existing sound mappings are paired
through actual command positions in all 48 canonical commercial resources;
the five new scores are bound to the preceding audio layer. Twelve mutation
fixtures reject dropped sounds/collision pointers, changed durations/scalars,
out-of-range layouts/descriptors and unowned writes.

The final gate checks all sixty 32-byte records: 46 complete commercial rows
and fourteen new rows. It checks the five consumed fields at offsets
`0,4,8,12,16`, restores the twelve zero padding bytes, and enumerates all sixty
ID/form/alternate-palette cases. All source P4 records and seven internal link
fields are checked independently. Thirteen negative fixtures include the old
staggered ABI, wrong companion form, old evolution view, opening redirection,
truncated Patamon palette and the discarded arbitrary retail scalar tuning.

All gates enforce exact write ownership and inverse restoration. New intervals
must be FF in the exact predecessor and have no all-byte-offset pointer or
aligned ARM B/BL-like incoming candidate. These scans establish this bounded
placement contract; they do not claim an exhaustive CPU reachability proof.

## Actual field types recovered during verification

The source P1 header's first command count is not its event count. Events begin
at relative 4 and are eight bytes each; the first payload boundary establishes
their population. The historical parser read that first count as the table
count and supplied unrelated commercial trailing events. The new layer uses
every source event and does not substitute template events.

P1 A bytes 0 and 1 are frame durations, not layout dimensions. Source
`75FFFF..760013` reads A+0/+2/+4 into local words; `760323` and `760D62` read
the two duration bytes and pass them to `5FFD:0EC8`. That helper at raw
`760E98` stores its duration into source fighter+76 at `760EFC..760F02`.
Callback `760F2C` decrements the field and restores the previous callback and
motion values at zero. Native presentation+28 flows through global
`03004C54` and collision-entry+10 into `0836E374..0836E390`; the duration
bytes become `03004D22/23`. Native `0836A69C` stores the supplied duration into
fighter+8C, and `0836A744` decrements it once per callback. This supports a
consistent frame-time conversion. It does not support the old value-dependent
heuristic that transformed 8 or values over 10 while skipping other values.

P4 word 3 is likewise a timer: source `781064..78106B` writes fighter+7E,
and states at `781907` and `781926` decrement it. Native `083584A0..083584A8`
writes fighter+94, with the matching decrement states at `083590E4` and
`08359114`. Patamon main item 11 uses state selector 4, so its source duration
36 is live. Copying the value 36 from a different commercial tuning example
was not justified; the explicit 75-to-60 nearest policy yields 29.

P4 words 7/8 are motion velocities and words 9/10 are accelerations. Source
`781831..7818D5` loads them into AX/BX/CX/DX and transfers them through
`781094..7810D4` to fighter+32/+34/+36/+38. Native
`08358FD0..08359098` and `083584F8..08358578` perform the same operations with
fighter+42/+44/+46/+48. Word 4 must stay unchanged: it is also an input bitmask
at source `780FBE` / native `083583C0`, and class-4 HP at source `781018` /
native `08358434`. State word 1 contains two independent bytes: low-byte
dispatch 0..4 and the companion action high byte. Both are preserved, with
their actual dispatch/action populations checked.

The resulting integer policy is explicit: duration 4/5 nearest away from zero;
velocity 5/4 toward zero; acceleration word 9 uses 25/16 nearest even and word
10 uses nearest away. This is temporal/spatial quantization, not a claim that
all retail per-resource tuning is interchangeable. The two former learned
velocity values 219 become 218 under the declared truncation policy.

## Reachable palette defect found at the final gate

Patamon source palettes `3D5470` and `3D54B8` each contain two entries: four
header bytes followed by two 34-byte bank/color records. The old converter
emitted only forty bytes for each. The missing second entry is reachable:
source record 13, P1 event 111, command 0 has flag 0200 and A+6 equal to 1.
Source `7525D4..7525F5` and native `0801297C..080129B0` pass that A+6 selector
to their palette helper. Native `080132F4..08013304` reads from
`palette+4+34*selector`, skips color 0 and copies fifteen visible colors.

The final layer therefore installs both complete 72-byte palettes at
`0860E700` and `0860E748` and points Patamon's canonical +8/+C fields to them.
The independent verifier checks all sixteen encoded colors of every entry,
the exact selector-1 command, and the actual native bank/color read extent.
The initial P0 and P1 repair layers remain reproducible and unchanged.

## Remaining scope

These gates do not establish visible sprites, VBlank/OAM transfer, complete
battle behavior, all stages, save behavior or full-game completion. Those are
separate runtime and integration requirements. In particular, the parent is
investigating a capture where shadow OAM is populated while hardware OAM is
disabled; a static resource PASS does not resolve that observation.
