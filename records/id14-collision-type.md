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
