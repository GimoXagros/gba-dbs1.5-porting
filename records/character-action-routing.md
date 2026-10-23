# Character action routing and the ID14 callback reset

## Observed failure and exact writer

The Waterfall display repair exposed a separate native character-table extent
error. It was reproduced with plain scheduled input as well as the instrumented
Right-input capture; the debugger was not the sole trigger.

`build/waterfall-boot-entry-20261023/probe.json` stops after the ID14 constructor
and then at native startup `08000128`. At the second stop P1 is still
`02011710`, its callback word is zero, and its EWRAM fields have not yet been
cleared. The earlier S04 capture retains the boot-loop arithmetic
`03001DC4 + 4*148F = 03007000` and IRQ return `08000144`, matching native IWRAM
startup clearing. The valid saved hitstop callback and nonzero remaining timer
in the boot-entry capture ruled out assuming a missing saved callback.

The later conditional write watch identifies the first null writer directly:

| Evidence | Observed value |
|---|---|
| Capture | `build/waterfall-zero-callback-writer-20261023/probe.json` |
| Stop | `T05watch:02011710;`, after 34 nonzero writes were skipped |
| Next PC / LR | `0835560C` / `0836AE28` |
| P1 / presentation | `r4=02011710`, `r5=020117BC` |
| Character / follow-up index | P1 `+11=14`, `+AA=0` |
| Follow-up pointer-table owner | P1 `+9C=0836A62C` |
| Selected record address | `r1=063C0000` |
| Callback written | `r0=0`, P1 callback becomes zero |

Native `0836AE08..0836AE24` reads P1 `+9C`, indexes it by the actual character
ID times four, and adds `P1.+AA * 32`. The table has twelve rows. ID14 therefore
reads `0836A664`, which contains action metadata `063C0000`, beyond the table.
`08355604` loads the callback at selected-record `+4`; `08355608` stores the
observed zero into P1. The normal player-state dispatcher at `083525BC..C4`
loads P1's callback and branches through it without a null check.

The zero writer and startup re-entry were captured in separate runs. Together
with the unguarded dispatcher and preserved startup-loop registers, they
explain the reset path; a continuous instruction trace between those two
stops was not recorded.

## Source-backed follow-up repair

| Version | Pointer table | Rows | Pointer values | Selected record |
|---|---|---:|---|---|
| WSC 1.0 | raw `3A659A`, CS base `3A45B0` | 12 | all `2022` | raw `3A65D2` |
| WSC 1.5 | raw `762780`, CS base `75FFD0` | 15 | all `27EE` | raw `7627BE` |
| Retail GBA | `0836A62C` | 12 | all `0836A67C` | `0836A67C` |
| Repaired GBA | `08628900` | 15 | all `0836A67C` | `0836A67C` |

The source records' flag/event fields and all bytes outside the relocated
callback pointer are identical. The old far pointer `A45B:11EF` resolves to
raw `3A579F`; the new `5FFD:138B` resolves to `76135B`. Their first 97 bytes are
identical. The remaining 19 constructor bytes pass the corresponding relocated
continuation and the duration helper, then return. The retained retail native
record selects the matching constructor `0836AE94`, including its phase,
velocity, facing, and duration fields. This is an explicit callback lineage,
not acceptance of an arbitrary different pointer word.

Source `761317..76133A` proves the character-indexed follow-up consumer. Source
`76694D..76695D` copies the record's table offset to fighter `+84`; native
`08355638..40` copies its translated pointer to fighter `+9C`.

The narrow repair changes metadata pointer raw `36A668` from `0836A62C` to
`08628900`, and writes a 60-byte, fifteen-row pointer table at raw
`628900..62893C`. It declares two spans, 64 written bytes, and 63 changed bytes.
Original tables, action records, instructions, and RAM layouts remain intact.

The adjacent initial table `0836A5FC` has a single aligned encoded reference,
literal `0836A4BC`. Its actual reader `0836A478..47C` takes row zero directly.
Source `7628D0..7628E0` does the same. That table does not require extension for
this consumer; extending it would not address the observed indexed overread.

`tools/verify_character_followup_routing.py` imports no builder. It checks the
source/retail lineage, producers and consumers, all fifteen routes, original
table preservation, FF ownership, encoded pointers at every alignment, ARM
branch/literal references, exact writes, and full inverse. All 28 controlled
negative cases fail as intended. Two report runs are byte-identical.

## Other short input tables

The separate input-action tables also retain the twelve-character retail
extent. Their source lineage is explicit:

- Native table `i`: raw `35515C + i*30h`, twelve `u32` pointers.
- WSC 1.0 table `i`: raw `3ADE08 + i*18h`, twelve `u16` offsets relative to
  CS base `3ABDF0`.
- WSC 1.5 table `i`: raw `768B4E + i*1Eh`, fifteen `u16` offsets relative to
  CS base `7668E0`.

All 168 original source action headers equal their retail GBA counterparts.
The 42 accesses for IDs12–14 exceed the original table extents; 41 read headers
that differ from source, and the remaining accidental match is still outside
the table. Table13's ID14 pointer is zero. Four existing ID11 evolution rows
also change in WSC 1.5: tables8/10/12/13 change action indices `2→1`, `6→4`,
`4→2`, and `4→7` respectively.

| Table | Native pointer table | Source 1.5 table | ID12 / ID13 / ID14 field +2, hex | Native literal(s), raw |
|---:|---|---|---|---|
| 0 | `0835515C` | `768B4E` | `12 / 13 / 18` | `355AB0` |
| 1 | `0835518C` | `768B6C` | `02 / 02 / 08` | `356B30`, `356B34` |
| 2 | `083551BC` | `768B8A` | `00 / 00 / 00` | `355990` |
| 3 | `083551EC` | `768BA8` | `16 / 09 / 0E` | `355980` |
| 4 | `0835521C` | `768BC6` | `0E / 00 / 00` | `355988` |
| 5 | `0835524C` | `768BE4` | `04 / 06 / 0D` | `355A58` |
| 6 | `0835527C` | `768C02` | `1E / 11 / 11` | `355A50` |
| 7 | `083552AC` | `768C20` | `02 / 02 / 02` | `355FEC` |
| 8 | `083552DC` | `768C3E` | `01 / 01 / 01` | `356B38` |
| 9 | `0835530C` | `768C5C` | `00 / 00 / 00` | `355994` |
| 10 | `0835533C` | `768C7A` | `05 / 07 / 06` | `355984` |
| 11 | `0835536C` | `768C98` | `00 / 00 / 00` | `35598C` |
| 12 | `0835539C` | `768CB6` | `04 / 04 / 02` | `355A5C` |
| 13 | `083553CC` | `768CD4` | `08 / 0A / 03` | `355A54` |

For flag1 records, `083555D0..5600` consumes only the four-byte flags/action
header and calls the actual P4 reader at `08358264`. Thus existing native
records with identical headers are valid reusable action descriptors. All 210
source rows resolve to 28 existing retail header classes. Tables0–7 use base
resources; tables8–13 use evolution resources. The analyzer checks the 39
added flag1 routes and six ID11 evolution routes against both the source P4
count and the actual converted native resource count and pointer list.

The shared flag0/event2 action uses existing record `083553FC`, callback
`0835655C`. Its source record has identical metadata outside its relocated far
callback. The independent verifier proves the old constructor
`3AD102..3AD152`, new `767C0A..767C5A`, and native `0835655C..083565D0` lineage.
The old/new 80-byte constructors differ only in four explicit relocations:
physics bank/table and continuation offset/segment. The consumed metadata at
record `+8..31` is zero. The old/new sound requests83/85 and84/86 have identical
payloads, corresponding to retained native requests29/2A. Full shared callback
and service parity is outside this bounded proof.

There are fifteen literal references and fourteen effective table loads. The
load at `08356B00` (literal `356B30`) is overwritten by `08356B04`; it is
redirected conservatively along with the live references. The analyzer reports
each actual literal reader and each corresponding source CS-relative reader.

## Input-table layer

`tools/build_character_action_routing.py` appends the layer after the integrated
language/follow-up predecessor. Fourteen 60-byte pointer tables occupy raw
`629000..629348`; fifteen existing literals point to their respective views.
The layer declares sixteen spans, 900 written bytes, and 885 changed bytes.
All original table and descriptor bytes remain intact. It preserves 164
unchanged in-bounds pointer identities; only the four source-changed ID11 rows
and the 42 added-ID rows select newly routed pointers. For those entries the
lowest retail address with the proved flags/action header is used.

The builder verifies the full inverse and scans the FF reservation for encoded
pointers at every alignment and ARM branches, literal accesses, and PC-relative
address formation. It adds no RAM, instructions, or action descriptors.
`tools/analyze_character_action_routing.py` produces the source/native mappings
without importing a builder. A separate agent's
`tools/verify_character_action_routing.py` passes independently without importing
the builder: 210 routes, 197 actual P4 indices, fifteen literal aliases,
reservation/interior references at every alignment, exact writes and inverse,
and 337 controlled negative cases. A repeated builder run produces identical
ROM and manifest bytes. The verifier invocation is:

```text
py -3 tools/verify_character_action_routing.py BEFORE AFTER GBA OLD NEW OUTPUT
```

Here BEFORE is the integrated predecessor, AFTER is the input-table candidate,
GBA/OLD/NEW are the three pinned original ROMs, and OUTPUT is
`build/character-action-routing-20261023/verification.json`.

## Bounded runtime evidence

The parent ran the emulator; the analyzer/verifier agent did not launch one or
access any `.sav` file.

- Before repair, the conditional zero-write capture above selects `063C0000`
  and writes zero at `08355608`.
- `build/runtime-followup-id14-consumer-20261023/probe.json` uses the fixed
  follow-up candidate. At `0836AE24`, ID14 has `+9C=08628900`, `+AA=0`, and
  `r1=0836A67C`, directly observing the repaired consumer on the failing path.
- `build/runtime-integrated-id14-movement-20261023` uses integrated candidate
  `3B40BC0C…`, including follow-up and language changes but preceding the input
  layer. The 99-second movement/attack capture passes the parent's invariants:
  42 enabled OAM objects, retained renderer, final S02 and no asynchronous
  fault. The parent reports coherent Waterfall scenery and both fighters at
  timer1:33. This is bounded evidence; it does not establish complete gameplay.
- `build/runtime-action-id14-movement-20261023/capture.json` uses the F2D
  input-table candidate. The parent's 99-second movement/attack capture passes
  its invariants with 42 enabled OAM objects, renderer bytes retained (`D18F`),
  final S02 and no asynchronous fault. The inspected screenshot shows both
  fighters and coherent Waterfall scenery at timer1:33. This bounded run does
  not establish whole-combat completion.

## Artifact identities

| Artifact | SHA-256 |
|---|---|
| Waterfall predecessor | `C50ADCF54D29B327CCF5BFAE21F51784AC2A7A9544DF6093680BDB6387F93DFF` |
| Follow-up candidate | `F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E` |
| Follow-up independent report, both runs | `A96E3DB159C9F33B867D0B96C4290423640DC24C695803F9485058E8C25FC3A9` |
| Source action analysis report | `539401234BC2AD56AADB48A47FCBA90A7107A1055D45733533F86122814A9487` |
| Integrated input-layer predecessor | `3B40BC0C9B253499A1AEC063E855C932191953718491F99DF44405C9CB91911C` |
| Input-table candidate | `F2D484BBF873B6CAE38CB5DCA32E57A16B514D4C0517BBD083BDDC45FBF010A0` |
| Input-table manifest | `CF8209EB95BE2ABA3280D9B693E9139B1DC5E7F76801AC51DDD113F1E5EEF578` |
| Input-table independent report | `D9B1BBC12B8DF71CB3E9522F780063EC699AD12E8D246FBD10A0F2C08A5EFDF8` |
| Pre-repair boot-entry probe | `49AD00252DA40B67C5DF22259B3CB9EBDB79EBB07581D5D277B405AB25734045` |
| Pre-repair zero-writer probe | `2C89274DD056F0EEFD190F16C4D2D7B55EC7E016EEDAA585F8DDFAF70902A35E` |
| Fixed follow-up consumer probe | `6A789AFC0DAB6FF0D7893E720F5D550BC149B21CF39F4CDFC2EB3F66B520D0D7` |
| Integrated 99-second movement capture | `7A08E9BDB2721220E264D2195D865FDCEA46137706E6033B6DA3193219F76192` |
| Input-table 99-second movement capture | `0F50B649525E956251CC4346CFE56FE670EBB72602C32A4465450458B505160B` |

The follow-up report is in
`build/character-followup-routing-20261023/verification.json`; the source analysis
is `action-analysis.json` beside it. The input-layer artifacts are in
`build/character-action-routing-20261023/`. Neither layer claims that all other
character-indexed damage/transition tables have been audited or completed.
