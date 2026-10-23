# Source-backed recovery-table repair

## Scope and result

The recovery table at native `0836BFF8` is too short for IDs13 and14. This is a
separate table from the repaired landing follow-up at `0836A62C` and the fourteen
input-action tables. Its exact source lineage supports a small data-only repair:
a new fifteen-row view of existing record `0836C56C`, plus a redirect of literal
raw `36B23C`. No new callbacks, action records, or RAM are needed.

The repair now installs that view at raw `629350..62938C` on the frozen input
candidate. It changes only the sixty-byte table and the existing four-byte
literal. The input-layer candidate and its frozen builder/verifier artifacts
were not modified. Independent repair verification and runtime evidence are
tracked separately below.

## Extents and actual consumer

| Version | Table range | Rows | Every row selects |
|---|---|---:|---|
| WSC 1.0 | raw `3A6EB4..3A6ECE` | 13 | `A45B:2E5E`, raw `3A740E` |
| WSC 1.5 | raw `76313A..763158` | 15 | `5FFD:3848`, raw `763818` |
| Retail/input-layer GBA | `0836BFF8..0836C02C` | 13 | `0836C56C` |
| Repaired recovery view | `08629350..0862938C` | 15 | `0836C56C` |

The original table includes the old boss ID12. It has thirteen rows, unlike
the twelve-row input tables. In all three versions the next record starts
immediately after the table with flags/event bytes `00 00 15 00`; that boundary
independently distinguishes table entries from adjacent action data.

Native `0836B0BC..0836B0D4` loads the actual character byte from fighter `+11`,
loads table literal `0836B23C`, reads `table[ID]`, and calls the common action
reader at `083555D0`. The table pointer has one aligned encoded reference in
the current ROM, at that literal. The surrounding branch is gated by the
recovery counters, the input `40h` bit, and a positive fighter `+64` value.

The source consumers use the same character byte and two-byte table stride:

- WSC 1.0: `3A58FE..3A5913`, CS-relative table offset `2904`.
- WSC 1.5: `7614BA..7614CF` and `761ADE..761AF3`, table offset `316A`.

The second source consumer belongs to another source callback. This proof
records its use of the same table; it does not claim that every surrounding
callback has been ported.

In the predecessor, IDs0–12 resolve to the valid record. ID13 reads `00150000`, the
next record's flags/event word. ID14 reads `0836C58C`, its callback pointer,
and treats the callback's machine instructions as an action record. Neither
is the source-prescribed record. These are static consequences of the actual
indexing instructions, not inferred failures from an emulator capture.

## Record and callback lineage

The old and new 32-byte source records are identical outside the relocated
four-byte callback. Both have flags0 and event `43h`. The complete consumed
metadata is unchanged. Their callbacks resolve as follows:

| WSC 1.0 callback | WSC 1.5 callback | Retained native callback |
|---|---|---|
| `A45B:1974` → raw `3A5F24` | `5FFD:2134` → raw `762104` | `0836BA90` |

The source constructor's first 77 bytes are identical, including phase11,
status/counter handling, facing, velocity fields, and the initial counter.
The next 61 bytes have explicit matching instructions with relocated physics
bank/table, palette-loop target, and continuation offset/segment. The source
physics window changes from bank `EA`/segment `2264` to `BB`/`2846`; the existing
character-physics routing layer already provides the translated native owner
used by this callback.

Native record `0836C56C..0836C58C` and constructor
`0836BA90..0836BB60` are byte-identical to the retail oracle. The record contains
native timers9/6 for source timers12/8, and native motion160/−480/25 for source
128/−384/16. Reusing the retail record preserves these established conversions;
the repair performs no new scalar conversion. The constructor reads
the corresponding fighter fields, selects phase11, adjusts facing and motion,
and refreshes the palette before continuing through existing code.

The full callback/service graph was not compared instruction by instruction.
The bounded proof establishes the table, consumed record, constructor lineage,
and unchanged native implementation needed for this pointer-view repair.

## Generic damage dispatcher is separate

`0836F3DC` also calls the common action reader, but it does not directly consume
the `0836BFF8` recovery table. The targeted analysis verifies these preceding
selectors and their branches into `0836F3B8`:

| Selector | Literal | Selected table |
|---|---|---|
| `0836ECEC` | `0836F7C0` | `0836BF08` |
| `0836ED38` | `0836F7C8` | `0836BF38` |
| `0836ED90` | `0836F7D4` | `0836BF68` |

The common path indexes by the target fighter's ID, adds a selected action
subrecord index times32, changes the fighter/presentation registers, and calls
`083555D0`. Those adjacent tables require their own source mappings; this proof
does not redirect them or infer a common affine mapping across the whole
damage family.

## Minimal repair and evidence

`tools/build_character_damage_routing.py` reserves raw `629350..62938C`, the next
sixteen-byte aligned range after the input layer ends at `629348`. The sixty
bytes and the preceding eight-byte gap are all `FF` in the pinned predecessor.
The builder checks encoded pointers at every alignment and ARM branch, literal,
and PC-relative address formation against the allocation. A full alignment scan
for pointers into any byte of the original thirteen-row table finds only the
actual consumer's literal at `36B23C`.

The new range contains fifteen `u32(0836C56C)` entries. Literal `36B23C` changes
from `0836BFF8` to `08629350`. These two spans declare 64 written bytes, of which
63 differ. Restoring them yields the complete predecessor byte for byte. The
original thirteen rows, action record, native code, previous input tables, and
alignment gap remain intact. The layer allocates no RAM, instructions, or new
action descriptors. IDs0–12 retain exactly the same record pointers; IDs13–14
now select the source-prescribed record.

A repeated build produces identical ROM and manifest bytes. The builder uses
only the four explicit pinned ROM inputs and the bounded source analysis; it
does not read a prior manifest to choose data. Invocation:

```text
py -3 tools/build_character_damage_routing.py BEFORE GBA OLD NEW OUTPUT --manifest MANIFEST
```

BEFORE is `build/character-action-routing-20261023/current-candidate.gba`.
OUTPUT and MANIFEST are `current-candidate.gba` and `manifest.json` in
`build/character-damage-routing-20261023/`. GBA/OLD/NEW are the pinned original
USA GBA, WSC1.0, and WSC1.5 ROMs.

`tools/analyze_character_damage_routing.py` reads only the four explicitly
supplied ROM paths. It checks source table boundaries, all rows, both record
versions, constructor instructions and relocations, native consumers and
record bytes, the unique literal, and the separate generic selectors. Eight
controlled mutations of the native/source contracts are rejected.

The source analysis report remains frozen at its pre-implementation state; its
proposal deliberately has no allocated address. The repair manifest supplies
the subsequent concrete allocation and exact write contract. A separate
agent's `tools/verify_character_damage_routing.py` passes without importing this
builder or the source analyzer. It checks all fifteen routes, full consumed
source/native metadata, source constructor lineage, the complete native
constructor through `36BB64` and palette literals `36BB64/68`, exact writes and
inverse, all-alignment/interior aliases, and allocation ownership including
Thumb ADR references. All 88 controlled negative cases are rejected. Invocation:

```text
py -3 tools/verify_character_damage_routing.py BEFORE AFTER GBA OLD NEW OUTPUT
```

OUTPUT is `build/character-damage-routing-20261023/verification.json`. No recovery
runtime claim is made by this static verification.

## Bounded runtime evidence

The parent captured the preceding F2D input-table candidate for 99 seconds with
movement and attack. `build/runtime-action-id14-movement-20261023/capture.json`
has SHA-256 `0F50B649525E956251CC4346CFE56FE670EBB72602C32A4465450458B505160B`.
The parent reports all invariants passing, 42 enabled OAM objects, renderer
bytes retained (`D18F`), final S02 and no asynchronous fault. The inspected image
shows both fighters and coherent Waterfall scenery at timer1:33. This is bounded
predecessor evidence; it does not demonstrate the recovery path or whole combat.

The recovery candidate has not been run by this agent. No runtime capture of
the previous ID13/14 recovery overread is claimed.

The parent subsequently ran A18 for a bounded 99-second movement/attack
regression. `build/runtime-recovery-id14-battle-20261023/capture.json` has
SHA-256 `78B765FFB0E8AFC11E5F42D754C1AF856FDDAAEC0DD11F58B9EADD66737BC883`.
The parent reports passing invariants, 32 enabled OAM objects, intact renderer,
final S02 and no asynchronous fault, with both fighters and coherent Waterfall
scenery at timer1:33 in the inspected screenshot.

A separate 118-second natural-input probe reached the ID14 constructor but
did not reach recovery consumer `0836B0D0`; it ended by bounded timeout in S02
without a fault. `build/runtime-recovery-id14-consumer-20261023/probe.json` has
SHA-256 `B79C2320E6CC962844E085AACFFCA13417B9897A0E182D537D9A6E7C46D705B7`.
Therefore the regression passes, while actual recovery-consumer runtime coverage
remains open. Neither capture establishes whole-combat completion.

## Artifact identities

| Artifact | SHA-256 |
|---|---|
| Analyzed input-layer candidate | `F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0` |
| Recovery analysis report | `839D31B7A04695739C9BA4D9C77A5C69BCA266A042CEED15312AAC77061F7DC2` |
| Recovery candidate | `A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71` |
| Recovery manifest, both builds | `E9B1C03B30E8ACA3C33BF0D48C09867BFA1DF94C10CEF7FD12D759257165F2A7` |
| Recovery independent report | `9D2E87557FC06DEB0816EA2917F1AC0897FBC47110BA14079C7CE3DF2202E9C0` |
| Recovery builder | `0AC20EAD9F17593DDB602BF1AF5330100C13CC620F68E016A5ACDEE89AAA89E7` |
| Identical 77-byte source constructor prefix | `334404E3B6E770988D57432A1BE0C339D406420B2FE403A9F0D873D8F809C68F` |
| Native constructor `36BA90..36BB60` | `4EBFD162FC8EC78CFA9358684C324A097E22BC91EA85E8F6DF299A75AF8A59D0` |

Report: `build/character-damage-routing-analysis-20261023/analysis.json`.
No emulator was launched and no `.sav` file was accessed by this analysis or
repair builder.
