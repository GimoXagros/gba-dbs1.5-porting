# ID14 collision dispatch investigation

Date: 2026-10-26. This is a bounded investigation of candidate
`389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1`.
It does not establish the producer of the invalid type or install a repair.
No type clamp, rollback, game-code change, emulator launch, or supplied-save
access is part of this analysis. The parent owns invisible runtime probes.

## Observed failure and exact consumer

`records/fixtures/id14-collision-dispatch-failure-20261023.json` preserves
the original timeout from
`build/runtime-waterfall-third-exit-20261023-a/probe.json`.
Its registers include `r1=000001BA`, `r4=02011710`, `r5=02011828`,
`r8=0836EBA8`, `r9=E28DD00C`, `LR=08353FF0`, and `PC=E28DD00C`.

The candidate bytes identify the failed dispatch precisely:

| Address | Native operation |
|---|---|
| `0836EB54` | Load address `03004D20` |
| `0836EB58` | Read its unsigned collision-type halfword into r1 |
| `0836EB5C` | Subtract 8 |
| `0836EB60` | Multiply by 2 |
| `0836EB9C` | Set r8 to dispatch table `0836EBA8` |
| `0836EBA0` | Load a word at `r8 + r1*2` |
| `0836EBA4` | Branch through that word |

The table contains eighteen pointers for types 8 through 25. The captured
index `1BA` means `(type-8)*2=1BA`, hence type `E5`, absent the separate
evolution override that sets r1 to zero. Its effective word address is
`0836EBA8 + 1BA*2 = 0836EF1C`, whose bytes encode `E28DD00C` (`add sp,sp,#12`).
This explains the invalid branch target; it does not prove which producer
first introduced type E5.

`08353FEC` calls `0836E348`, matching saved LR `08353FF0`. At entry, r4 and
r5 are collision-record handles, not actor handles. `0836E348` pushes
`r1,r2,r3,r4,r5,lr`, so the original handles remain at `SP+0C` and `SP+10`
on the normal no-extra-frame path to `0836EBA0`. At `0836E364/370`, record
r4 `+4` becomes the type at `03004D20`; r5's type goes to `03004D28` at
`0836E394..3A0`. Only afterwards do `0836E3B0/3B4` replace r4/r5 with the
actor pointers stored at the starts of those records.

For ordinary fighter-kind routes, the path through `0836E8D8`, `0836EA74`,
and `0836EB30` does not change `03004D20` before the load at `0836EB58`.
The failed capture lacks the actor/record memory needed to certify that
entire predecessor path in the failing run.

## Actual list producers

`030048C8` is the command-B collision list, counted by byte `03004C4D`.
`030049B8` is the event-B list, counted by byte `03004C4E`. Their spacing
is `F0`, or twelve 20-byte entries. Each entry contains actor pointer at
`+0`, collision type at `+4`, four rectangle halfwords at `+6..C`, and
A metadata pointer at `+10`.

The general producer `08353B74` receives an actor in r4 and forms its
presentation at actor `+AC`. The only aligned ARM BL into that entry in
this candidate is `0835284C`.

- `08353BCC` loads presentation `+24`, the current native P1 command.
- The event route loads presentation `+2C` at `08353BF0`, reads the B10
  record's type at `08353C6C`, and writes the event-list type at `08353C70`.
- The command route loads command `+0C` at `08353CA4`, reads its B10 type
  at `08353D20`, and writes the command-list type at `08353D24`.
- Both routes preserve the current A metadata from presentation `+28`.

There is also a non-P1 producer, `08377630..083776FC`. It selects a B10
record from table `08377700` using actor `+A0`, writes the type at
`083776E4`, and appends to the command list. The one ordinary table entry
points to `08377704`, whose type is 15. Its complete selector-domain proof
is outside the current evidence; it must not silently be excluded from
the producer search.

All-byte encoded-pointer scans find these direct literals:

| Global | Candidate literal locations |
|---|---|
| `030048C8` | `08353D84`, `08354024`, `0837771C` |
| `030049B8` | `08353D60`, `0835401C` |
| `03004C4D` | `08353B68`, `08353D88`, `08353DA0`, `08354018`, `08354028`, `08377720`, `08377730` |
| `03004C4E` | `08353B6C`, `08353D64`, `08353D7C`, `08354014`, `08354020` |

These are encoded-reference results, not a proof excluding arithmetic or
indirect aliases. List overflow has not been observed in the failing run.

## Canonical source/native resources

The existing independent
`tools/verify_character_hit_routing.py:p1_graph` was rerun directly on the
exact 389F candidate and the pinned WSC1.5 input. It reads current native
resource groups `084A80F8/084A82D8/0860B000/0860B1E0` and source table
raw `740000`; no earlier build manifest supplies expected pointers.

All sixty resources, 2,498 events, 12,506 commands, and 15,004 individual
event/command collision edges pass. Of these edges, 2,934 are non-null.
Every individual type and null-presence value equals its source edge.
The exact type set is
`{0,1,3,8,9,10,12,13,14,15,16,17,18,19}`. E5 does not occur.
The eight pre-existing A-selector edits are preserved as documented by
the independent verifier; they are not collision-type changes.

This excludes a canonical source-to-native type mismatch at the declared
edges. It does not establish which event/command was selected at failure,
prove that a RAM pointer still addresses a declared edge, or exclude a
later list/scratch overwrite.

Native current-command storage is written by event setters `080128B0`
and `080129F4`, animation-loop reset `08012AFC`, and stride advancement
`08012B10`. An aligned ARM immediate-store scan finds these four writes
for presentation `[r5,#24]` and none for actor `[r4,#D0]`; this scan does
not exclude other addressing modes or base registers. The ordinary tick
compares the next command index against the stored count before advancing
at 16-byte stride. Event selection at `08012874` is not bounds-checked.

## Runtime evidence boundary and next discriminator

The parent's new seed probe
`build/runtime-collision-seed-watch-20261026-a` captured initial Waterfall
pattern 2, then installed the read watch at `0836EF1C`. Its first RAM pair
shows actor `02011710` is ID14 with P1 `086184A0`, and opponent `02011828`
is ID1 with P1 `080FE478`. Both are on valid event 0. The event-list count
is 2, both recorded types are 0, and the command-list count is 0.

That probe did not reproduce the invalid read. It timed out at
`PC=08011200`, native mode 9, with Waterfall phase/mode `00000D00`.
The older read-watch attempt
`build/runtime-collision-type-overread-20261023-a` also ended in mode 9
without a hit. Neither no-hit run invalidates the original failure or
establishes a repair.

Useful next traps, all before the listed instruction executes:

| Trap/filter | Evidence obtained |
|---|---|
| `0836E370`, r0=`E5` or r0>=26 | Copy from the actual overlapping attack record into `03004D20`; r4/r5 still hold collision-record handles, r1 is attack owner |
| `08353D24`, r0=`E5` | General command producer: r4 is B10 pointer, r1 is destination record, r5 is presentation |
| `083776E4`, r0=`E5` | Non-P1 producer: r4 is selected B10 pointer, r1 is destination record |
| `0836EB9C`, r1=`1BA` | Consumer before the bad load; saved original record handles at `SP+0C/+10` |
| Read `0836EF1C`, 4 bytes | Exact observed overread with fewer stops than every collision producer |

The `0836E370` filter runs only after rectangle overlap succeeds. It is the
preferred host-filtered fallback when an exact bad-address watch does not
reproduce the failure; trapping every list write would stop much more often.

For a producer hit, preserve the entire RAM pair and presentation fields
`+0E` (event), `+1A/+1C` (command index/count), `+20/+24` (command base/current),
`+28/+2C` (A/event B), and `+44` (P1 resource). These distinguish invalid
event selection, command progression, source-pointer selection, and a
post-producer overwrite. A valid B type followed by E5 in the same entry
requires watching that entry's `+4`, rather than changing the P1 converter.

The unresolved gate is the first actual E5 producer/overwrite. No corrective
ROM change is justified by the current evidence alone.

## Bounded capacity comparison, 2026-10-26

The native collision-list capacity matches WSC1.5. This is not another
twelve-character table that needs fifteen rows: these rows represent active
collision entries, not selectable character IDs.

| List | WSC1.5 DS=`0C00`, near offsets | Native start/end, exclusive | Entries |
|---|---|---|---:|
| Command B / attack | `3A5E..3B06` | `030048C8..030049B8` | 12 |
| Event B / receiver | `3B06..3BAE` | `030049B8..03004AA8` | 12 |
| Other/world collision | `3BB0..3CD6` | `03004AA8..03004C4C` | 21 |

These extents follow the actual adjacent list/count owners. No symbol table
or allocation declaration is present in the ROM. The first two source
spans are `A8=12*14`; the third is `126=21*14`. The native counterparts are
`F0=12*20` and `1A4=21*20`.

The source element is fourteen bytes: actor near pointer `+0`, type `+2`,
rectangle X/Y/width/height `+4/+6/+8/+A`, and A near pointer `+C`. The
native element is twenty bytes: actor pointer `+0`, type `+4`, rectangle
`+6/+8/+A/+C`, two alignment bytes at `+E`, and A pointer `+10`. The world
producer does not populate the A field. Both traversal loops consume their
platform's respective stride; a native loop has not retained source stride14.

Count initialization and iteration are explicit:

- WSC1.5 reset `7424C6..7424D5` clears bytes `3BAE`, `3BAF`, and `3CD6`.
  For example, input callbacks call it at `741079` and `7410E6`.
- Native reset `08353B48..08353B64` clears `03004C4D`, `03004C4E`, and
  `03004C4C`. Its four aligned native BL callers are `08374E7C`,
  `08374F0C`, `08374FBC`, and `0837504C`. It clears counts, not list bytes.
- Native `08353F00` returns when either attack/receiver count is zero.
  Otherwise it traverses the full byte counts, advances by20 at
  `08353FF0/08354000`, and decrements the loop counts at
  `08353FF4/08354004`. Source `7426B0..74273A` performs the same nested
  count traversal with stride14 at `74272F/742735`. Neither caps the
  count at12, and neither resets it at its terminal return.
- The world consumer checks count zero at `083541B0..083541BC`, reloads
  the count at `08354390/394`, advances by20 at `083547D4`, and terminates
  its decrementing loop at `083547DC/E0`. Its native reset is the shared
  count reset above.

There is **no append-time capacity check** in the examined native or source
producers. The source event/command append ranges `742530..74257C` and
`742598..7425E3` multiply an unsigned byte count by14, write one record,
and increment the byte. Native `08353BF4..08353C84` and
`08353CA8..08353D34` do the same with20. World append
`742655..74269A` / `08353E58..08353ED8` and the separate producer
`745549..74558A` / `0837767C..083776F4` likewise have no count limit.
The branch conditions before appending test actor/presentation flags or
null B pointers, not available list slots.

A general actor pass appends at most one event record and one command
record. Additional P1 events or commands do not themselves add multiple
records in that pass: the producer consumes only the current event B and
current command B. Multiple simultaneous actors still contribute separate
entries. Therefore the source/native list geometry and per-pass asset
contract agree, but the static resource population does not prove a maximum
of twelve simultaneous participating actors for every added-content path.
That aggregate concurrency limit remains unproved.

The following available RAM snapshots were inspected without an emulator
or supplied-save access:

| Snapshot | Attack / event / world counts |
|---|---|
| seed-watch `event-1-iwram.bin` | `0 / 2 / 0` |
| seed-watch timeout `iwram.bin` | `0 / 0 / 0` |
| dispatch-filter `-a` timeout `iwram.bin` | `0 / 0 / 0` |
| dispatch-filter `-b` timeout `iwram.bin` | `0 / 0 / 0` |

These are the `build/runtime-collision-*-20261026-*` probes named above.
They are isolated observations, not maximum-per-frame telemetry. No list
capacity violation is present in those snapshots. The `-b` timeout is
`PC=00000074`, mode9, with eight valid dispatches skipped; the captured
BIOS address alone is not classified as a game fault.

The number `E5` alone is insufficient to identify a coordinate. Native
type and coordinate fields have distinct offsets, and all three native
list bases differ by whole multiples of20. Simply crossing an adjacent
list boundary preserves the type column; it does not shift a coordinate
halfword into `+4`. A different overwrite or malformed record would need
its own observed writer. Thus the supplied evidence neither demonstrates
aggregate overflow nor supports attributing E5 to coordinate229.

## Separate type15 producer and index domain

The ordinary record used by `08377630` has a direct source/retail lineage:

| Version | Producer raw/native | Pointer table | Sole pointer target |
|---|---|---|---|
| WSC1.0, CS base `390700` | `3947CD` | raw `394854`, word `4156` | raw `394856` |
| WSC1.5, CS base `740900` | `745513` | raw `74559A`, word `4C9C` | raw `74559C` |
| Retail/current GBA | `08377630` | `08377700`, word `08377704` | `08377704` |

All three B10 targets contain the exact same ten bytes:
`0F 00 00 00 00 00 00 01 C0 07`. The type is15, with rectangle fields
`0,0,0100,07C0`. The source pointer table ends where that record begins,
after one two-byte pointer; native ends after one four-byte pointer.
The next source functions begin immediately after the B10 record at
`394860` and `7455A6`. There is no additional WSC1.5 table row here.

The index is an ordinal, not a byte displacement. Source `3947F8..394803`
and `74553E..745549` read actor `+8A`, multiply by2, and load a near
pointer. Native `08377670..08377678` reads actor `+A0`, multiplies by4,
and loads the translated pointer. Those widths match their tables.

The dedicated actor is obtained through native global `03004DF8`,
corresponding to source `1000:06A0` in1.0 and `1000:071C` in1.5.
Native constructor `083775B0` is called at `080D19F0`, creates the actor
with flags `0029` and callback `08377630`, and writes its A metadata
pointer at actor `+D4`. Its initial `4000` participation bit is off.
The collision callback returns immediately while that bit is off.

The identified activation path explicitly selects row0 before enabling it:

- WSC1.0 `3AEF17..3AEF22`: zero AX, store actor `+8A`, set flags `4000`.
- WSC1.5 `769DC5..769DD0`: the identical sequence.
- Native `080168D0..080168E4`: zero r0, store actor `+A0`, then set
  actor flags `4000` at `080168E0`.

All direct encoded references to native global `03004DF8` resolve to the
constructor and four native reader sites: `08016544`, `080166CC`,
`08016718`, and `080168BC`. These respectively process hit/disable state,
update Y, disable participation, and activate at index0. The first three
do not write `+A0`. The corresponding source readers are visible at
`769B6F`, `769C81`, `769CC5`, and `769DB3`.

The initial seed snapshot identifies this actor as `02010130`, callback
`08377630`, flags `0029`, index0. It is distinct from ID14 at `02011710`.
The three timeout snapshots also retain index0 for that global's actor;
their later callback lifetime is not treated as a live-combat observation.

Byte comparison confirms the relevant current native ranges are unchanged
from retail: `0801653C..08016A4C`, `083775B0..08377734`, and the shared
list code `08353B48..08354030`. Assertions check source pointer resolution
and exact three-way B10 equality. These findings exclude a missing
WSC1.5 row or a source/native pointer-width mismatch in this ordinary
producer path. They do not prove the absence of unrelated indirect alias
writes or establish the selector value in the original failing run.

## GDB observer-artifact audit, 2026-11-03

This read-only audit tests two specific alternative explanations for the
original failure: breakpoint instruction replacement and register-packet
misinterpretation. It does not establish the first E5 producer or repair
the game. No emulator was launched and no supplied save was accessed.

The original `runtime-waterfall-third-exit-20261023-a/probe.json` still
matches the fixture's SHA-256
`22A2F2D822688D1E2E7239C987F303AA2F6AA8FEE6AD0A5EBADA4437D16C9937`.
Its configured ROM independently hashes to the recorded `389F56FF...ABD7F1`
candidate. The report and the historical `bdc4389` version of
`tools/probe_physics_consumers.py` identify this sequence:

1. Arm `Z0,836d348,4`; observe one `S05k` breakpoint at `0836D348`.
2. Read registers/memory, remove that breakpoint, and issue one `s`.
   The recorded step response is `S05`.
3. Arm `Z0,8585310,4`, continue, and reach a bounded `S02` timeout.
   The second breakpoint was not observed.

Disassembly of that exact candidate shows the stepped instruction is
`0836D348: strh r3,[r8]`. The captured operands are `r3=2` and
`r8=03004CF8`; that store neither targets collision scratch `03004D20`
nor changes r1/r9. The unhit `08585310` instruction pushes LR. Neither
instruction is the `E28DD00C` word observed as the invalid target.

The recorded emulator path names mGBA commit
`fa977ccbc815efc93aefad9acddc9af0577d7827`. Its
[GDB breakpoint handler](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/debugger/gdb-stub.c#L574-L592)
maps both `Z0` and `Z1` to `BREAKPOINT_HARDWARE`. The corresponding
[ARM breakpoint implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/arm/debugger/debugger.c#L206-L246)
compares the execution address; insertion/removal manage breakpoint
records. This path does not replace ROM instructions, so a patched-opcode
alias or an incorrectly restored original opcode is not supported by this
implementation. Software-breakpoint replacement is a separate path.

The same source's
[register response](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/debugger/gdb-stub.c#L358-L382)
emits r0..r14, adjusted PC, and CPSR as seventeen little-endian words.
Thus the harness's `<17I` decoding matches the actual 68-byte fixture.
PC is adjusted by four in ARM mode, but this does not change r1 or r9.
The independently decoded tuple is `r1=1BA`, `r8=0836EBA8`,
`r9=PC=E28DD00C`, `LR=08353FF0`, `CPSR=40000010`. Assertions verify that
`r8+r1*2=0836EF1C` and that the exact candidate word there equals r9.
This coherence survives the documented PC convention; it is not explained
by treating instruction bytes as a misnumbered register.

The GDB
[single-step handler](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/debugger/gdb-stub.c#L242-L263)
calls the core step function. The
[GBA implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/gba/core.c#L816-L818)
uses the ordinary ARM instruction runner. The
[ARM runner](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/arm/arm.c#L213-L225)
processes scheduled events around one instruction. No direct register
replacement is present in this step path.

Limits remain explicit. The executable's reported hash is preserved, but
this audit has not independently proved its binary-to-source identity.
The original report has no failure-time RAM pair, full GDB packet log, or
post-step register snapshot. Its controller timers run in host wall time
while debugger stops consume wall time, so an otherwise similar
frame-indexed BizHawk run is not an identical replay. A different input
trajectory, emulator-core defect, or broader observer effect remains
possible. A no-hit run cannot negate the original coherent register state.
The specific patch-alias and register-decoding hypotheses lack supporting
evidence; the actual collision producer/overwrite remains unresolved.

## Discriminating producer observation, prepared 2026-11-05

The exact v65 ordinary trajectory already completed twice without E5:
84 overlap callbacks, 79 dispatches, and sampled command/event/world
maxima `3/4/4`. Repeating that input is not the next causal test.
`tools/bizhawk_probe_gba_collision_producer.lua` wraps the existing
consumer observer and supplies a different ordinary combat trajectory.
It changes no game bytes and performs no guest-memory writes.

The wrapper adds these distinct observations:

- Pre-store hooks at `08353C70`, `08353D24`, and `083776E4` record the
  actual B pointer, loaded source type, destination, computed list index,
  current count, and actor pointer read from the already-written record.
  Actor `+A0` and presentation event/index/count/base/current/A/B/P1
  fields accompany each origin. The native instructions at these three
  hooks are all `strh r0,[r1,#4]` on v65.
- Twenty-four direct type-field write watches retain raw callback address,
  value, flags, old type, and exposed PC. A separate write watch observes
  scratch `03004D20`. Write callback values can be unsupported/zero in
  BizHawk, so they are evidence, not independently classified as new types.
- The overlap hook relates the actual type to that slot's latest producer
  in the same frame. The `0836EB58` hook reads the actual scratch halfword
  before the dispatch load. Invalid producer/overlap/scratch types, a
  changed same-frame list type, or out-of-capacity/inconsistent append
  geometry preserve the first anomaly.

Telemetry is bounded to a 128-event ring and the latest origin per
destination. Ordinary execution performs no per-event disk writes.
`producer-trace.txt` receives the ring at the first anomaly or normal exit,
with totals on exit. The first anomaly additionally writes complete
`producer-failure-iwram.bin` and `producer-failure-ewram.bin` before the
observed instruction executes. The original observer still independently
captures invalid overlap/dispatch and writes its usual outputs.

The proposed parent-owned invisible experiment uses the pinned v65 ROM,
the existing isolated launcher/configuration, and these changed arguments:

```text
--lua=W:/tools/bizhawk_probe_gba_collision_producer.lua
--userdata=output:W:/build/<new-run>;frames:18000;start_frame:2970;combat_profile:approach-jump
```

The menu sequence remains unchanged. From relative frame5550, in battle
mode7 only, the actual input becomes A for7/97 frames, B for7/29,
Up for9/181, Right until6150 and then for300/720, and Left for
relative phases360..659 of each720-frame period. The wrapper mutates the
same input table before the existing observer logs it, so its input trace
records the actual submitted state. All eleven buttons are explicitly
released before exit. `combat_profile:baseline` provides the old trajectory
with the new telemetry if a later controlled comparison becomes useful.

The first run is bounded to18,000 advances and a480-second host deadline
because producer/write callbacks add work. Its runner must retain exact
ROM/executable/isolation/completion checks, pin both Lua scripts, and omit
the old trajectory's exact84/79/30,000 assertions. A timeout remains an
incomplete observation. No runtime is claimed by preparation of this tool.

The new mock self-check executes the actual wrapper through the bundled
Lua5.4 library. Valid source/unsupported zero write-values, invalid source
E5, index12 overflow, post-producer type change, and invalid actual scratch
are checked separately; it also verifies the24+1 write hooks, the128-entry
ring, single capture, RAM snapshots, and final controller release.
`tools/verify_bizhawk_probe_gba_collision_producer.py` passes. This validates
observer logic against mocks, not actual core write-hook delivery.

Limits: the direct slot watches do not claim to catch every possible
overlapping/interior alias write. The ring can discard an older writer;
exposed callback PC must be interpreted using the core's PC convention.
The first anomalous source pointer must still be resolved against its
declared event/command resource before selecting a repair. There is no
E5 causal fix or new game-code change in this observer preparation.

### Parent-owned producer experiment outcome

`build/bizhawk-producer-v65-20261105-a` completed18000 advances with
`combat_profile:approach-jump` on exact v65. Its launch manifest records
invisible private-desktop execution, no guest-memory writes, no physical
background input, exact complete loaded-ROM equality, and unchanged script.
The wrapper and baseline Lua hashes are respectively
`82EFDCC01099271CE75E6CF3D2FAFB05A4A6F04AE61907AA6AE50B091DE864E2`
and `7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9`.

The terminal result is bounded-no-hit at core18001:44960 producer visits,
44984 direct list-type writes,51 scratch writes,50 overlaps,42 scratch
consumer reads, and `captured=false`. Consumer trace independently reports
50 valid overlap callbacks and42 valid dispatches. Sampled command/event/
world maxima are`3/3/5`. The first94 of the planned128 final journal records include live ID14
actor`02011710`, P1`086184A0`, valid source B pointers and event/command
fields, rather than inferring the actor from the dispatcher registers.

Actual core callbacks delivered pre-store exposed PC`hook+4` and
write-callback PC`hook+8`. The retained v65 tail has zero write values and flags`2000` for
zero-type records; this alone does not prove unsupported callback values.
The complete later v66 journal also observes value8 at actual type8 writes.
Classification still uses actual scratch reads and producer register/source
reads rather than assuming every callback backend supplies reliable values. All list writes/producer totals are bounded
observations; unmatched write totals can include initialization and are
not themselves classified as corruption.

`producer-trace.txt` SHA-256 is
`BEC310ACCC7F1933F5A2252DEC1CFF163650D165159D601619BD31193E9F5B05`;
the consumer trace is
`9929C743C6C4977837E61AA5BA3B69EB81F6DBFE74119EA98A8EF87F3B018D38`.
No anomaly RAM pair was expected because no anomaly was observed. This
different ordinary trajectory does not solve or invalidate the original
E5 failure. A replay of the original host-timed GDB stop/step/input
interaction remains a possible next discriminator; no such rerun or
repair is claimed here.

### Completion ordering repair and v66 regression

Root found that the baseline observer closed `done.txt` before the wrapper
finished writing its final ring. The first v65 run retained94/128 final ring
records; this cannot be treated as a complete128-record journal. The existing
RAM/screen artifacts and earlier summary counts were already complete.

The wrapper now writes `producer-done.txt` only after closing every final ring
line. Its host-Lua check verifies this marker before the mocked exit. Root's
runner waits for both completion markers. A new exact-v66 hidden18,000-frame
run in `build/bizhawk-producer-v66-20261105-b` retains all128 records, the same
44,960 producer visits and all six memory/screen artifacts as v65/v66-a.
All ordinary input/event lines agree in order, and register dictionaries agree
after sorting their enumeration order. No E5 occurred and no gameplay repair
was inferred. Full evidence and current tool hashes are recorded in
[v66 integration](shoot-scene-integration-v66.md).
