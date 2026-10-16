# Complete added-character P1 resources, 2026-10-16

Fourteen source P1 resources are now emitted with every original event and
command: three base fighters, four evolutions, and seven companion resources.
The new data layer contains 544 events, 2,742 commands, 53 eight-byte A metadata
records, 305 ten-byte B records, and 259 non-null command-tail B pointers. It
does not connect resource tables; the following canonical table ABI layer owns
that separate write and the independent complete P0/P1 pairing check.

## The previous parsing defect

A source P1 starts with two halfwords: relative event-table pointer `4` and
reserved zero. At `+4` the first event begins. Each event is four halfwords:
command count, payload relative address, A relative address, B relative
address. Its first payload follows the complete event table, so the event
population is `(first_payload_relative - table_relative) / 8`.

The historical `build_new_base_p1_assets.parse_source` treated the halfword at
`+4`, which is event 0's command count, as the number of table rows. It then
constructed a synthetic leading event and copied later native template events.
For base ID 13 this retained seven logical events from a source with 115.
The evolution builder inherited that parser and selected template rows using
an additional old table-origin error. These frozen layers remain reproducible;
the new final layer supersedes their P1 bindings without editing them.

## Independent commercial format oracle

`tools/analyze_character_p1_oracle.py` parses the source directly at `+4` and
uses the actual retail canonical table `080D3FB8`, P1 field `+4`, for all 48
commercial source/native pairs. It imports no builder or historical parser.
All 1,997 event populations/counts and 9,928 command counts agree. Every one of
703 non-null source command word-5 values resolves to a ten-byte B record
that is byte-identical to the native record referenced by command `+12`.
Native word 5 becomes zero, and a null source value remains a null tail.

The oracle explicitly records release-specific edits instead of promoting
them into format rules: 133 event A records, one event B record, 16 layout
indices, two tile indices, and 14 command flag words differ between the two
commercial releases. The new conversion preserves the WSC1.5 layout, tile,
flag, and other scalar values. It does not borrow these commercial edits.

Oracle artifact: `build/character-p1-repair-20261016/oracle.json`, SHA-256
`06B86534DFC020EA9BDE820C6CA5568E6C22676DC5187324938A3EF46648682F`.

## Actual native consumers and time units

Native `08012874` takes the event index, selects a 16-byte native row, and
stores its A and B pointers into presentation `+28` and `+2C`. Source
`7524CB..75260B` implements the corresponding eight-byte row and relative
address contract. Native `08012A84..08012BB8` advances commands at 16-byte
stride; source `752852..752A06` advances at 12-byte stride. Command byte 0 is
the animation duration and byte 1 selects a sound request.

A is one typed eight-byte record per event, not an array indexed by the
layout number. A `+6` is consumed as a palette-bank adjustment by native
`0801297C..080129B8`, paired with source `7525D4..7525D8`.

The independent rules analysis traced A bytes 0/1 to actual frame timers:

- Native presentation `+28` becomes global `03004C54` at
  `08353BC0..08353BC8`, then collision-entry `+10`. Callback `0836E348`
  copies A halfwords `+0/+2/+4` into `03004D20+2/+4/+6`.
- Native A byte 0 is read through `03004D22` at `0836F60C`, `0836F688`,
  and `0836F6CC`; byte 1 is read through `03004D23` at `0836E758`.
  Helper `0836A69C` stores the requested duration at fighter `+8C`;
  callback `0836A744` decrements it once per frame and restores the saved
  callback and velocities at zero.
- Source `75FFF8..760016` reads the same three A halfwords. A byte 1 at
  `760323` and byte 0 at `760D62` are passed to `5FFD:0EC8` (raw `760E98`).
  It stores the duration at fighter `+76` and assigns `5FFD:0F5C`
  (raw `760F2C`), whose once-per-frame decrement restores the saved state.

The data conversion uses the existing 75-to-60 Hz policy consistently:
`(4*n + 2) // 5` for command duration and A bytes 0/1. A bytes 2..7 and every
B byte remain source-identical. This replaces the old arbitrary rule that
scaled A values only when equal to 8 or greater than 10. It is an explicit
integer time quantization, not a claim that every retail timing choice was
mechanically identical. Source animation advancement also clamps its newly
loaded duration to at least 2 while the native advancement does not; this
platform difference is recorded rather than hidden by template replacement.

## Sounds and complete pointers

For shared sounds, each new source payload is first matched byte-for-byte to
the old WSC payload, and a concrete commercial P1 command anchors the native
ID. New source IDs map as follows:

| WSC1.5 | Native | Evidence |
| --- | --- | --- |
| `9B/9C/9D/9E/9F/A0/A1/A2` | `3E/3F/40/41/42/43/44/45` | Exact old sound payload lineage and paired commercial P1 commands |
| `B5` | `54` | Exact old `B3` payload and paired command |
| `05` | `00` | Proven commercial P1 bridge; native byte 00 skips the request |
| `BC/C6/C8/CB/CC` | `5F/60/61/62/63` | New guarded native audio layer, preceding this layer |
| `FF` | `FF` | No-request sentinel |

The shared sound oracle reports per-resource suppressed/retuned exceptions;
it does not infer every ID from a numeric subtraction. In particular `05`
uses the commercial native no-request behavior, not an invented stop helper.
The five new sounds retain the explicitly bounded fidelity of the preceding
audio layer; this P1 conversion makes no additional timbre or sweep claim.

Every event B pointer and every nonzero command word-5 relative pointer joins
the same complete set of source ten-byte records. They are emitted once per
source-relative identity and relocated directly. Command word 5 is cleared,
and its absolute pointer is written at native command `+12`. No command uses
an unrelated template A/B pointer or an address based on an arbitrary bias.

## Exact source and output populations

| Source record | Source raw | New native P1 raw | Events | Commands |
| --- | --- | --- | ---: | ---: |
| Base 12 | `342E60` | `611800` | 131 | 824 |
| Base 13 | `370000` | `6156B4` | 115 | 585 |
| Base 14 | `368FF0` | `6184A0` | 120 | 611 |
| Evolution 11 / record 41 | `3ADEF0` | `61B4BC` | 39 | 164 |
| Evolution 12 / record 42 | `2EF6C0` | `61C288` | 37 | 145 |
| Evolution 13 / record 43 | `3B37B0` | `61CF0C` | 42 | 130 |
| Evolution 14 / record 44 | `3B6340` | `61DB48` | 35 | 141 |
| Companion 27 | `3D4C60` | `61E71C` | 2 | 6 |
| Companion 28 | `3D22A0` | `621000` | 3 | 12 |
| Companion 29 | `3CFEE0` | `621158` | 4 | 15 |
| Companion 56 | `3CF5F0` | `6212C8` | 5 | 30 |
| Companion 57 | `3D2190` | `62154C` | 3 | 15 |
| Companion 58 | `3D1BF0` | `6216AC` | 4 | 16 |
| Companion 59 | `3CC590` | `621824` | 4 | 48 |

All 56,172 payload bytes occupy exactly `611800..61E7DC` and
`621000..621B90`. The input is FF throughout both ranges. The builder scans
the complete predecessor for pointers at every byte offset and ARM B/BL-like
words at every aligned address; neither group has a possible inbound hit.
Previously considered targets at `611680`, `611788`, `611798`, `61E8DC`,
`61F904`, and `620762` remain untouched. The fourteen Expected Writes and the
complete-ROM diff are checked separately.

Builder: `tools/build_character_p1_completion.py`.

| Artifact | SHA-256 |
| --- | --- |
| Input `build/character-audio-20261016/current-candidate.gba` | `10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354` |
| Output `build/character-p1-completion-20261016/current-candidate.gba` | `3F9437068817749C3EB75BF382D5F870EB8539EE49E3D70AAED10D6C93E52CAA` |
| Manifest `build/character-p1-completion-20261016/manifest.json` | `C7B44D990AC2CF9AB8137D806F39FC2D4CC06804EEB8DCF79A6DC5830A7C7667` |
| Independent verification `build/character-p1-completion-20261016/verification.json` | `FAC5E6F50B55BF4789E4FB06EB6454DF1AFB8DCE5172E08A7F35275AD08E87E7` |

No native code, external entry, resource table, or RAM owner changes in this
layer. The separate `tools/verify_character_p1_completion.py` imports no
generator or manifest. It independently checks all 544 events, 2,742 commands,
fourteen P0 bindings, typed A records, shared B aliases, and complete-ROM
Expected Write boundaries. Its result is PASS. The following canonical-table
ABI layer receives a separate consumer check. Runtime success for these new
character populations remains a separate observation; no provided save was
read by this work.
