# Actual native terminal attempt: independent capture audit — 2026-11-09

PASS for integrity of the completed observation in
`build/bizhawk-gba-shoot-terminal-20261109-a`. Its actual outcome remains
**failure:bounded-no-completion**,3000 advances from68927 to71927. A real
lethal FIRST hit, fatal callback installation, healthy root5 and native
terminal scene entry are established. Later actor updates, IRQ selection,
cleanup and actual mode8 are not observed. No terminal completion claim is
made.

All61 files match the immutable launch inventory. Exact1477 ROM,964B
observer,914E host,EED734 pin document, three script pins, original/copy
checkpoint provenance and isolated configuration pass. The process ended
without host stop or deadline; background physical input, automatic state
loading and SaveRAM autosave were disabled. This reviewer only parsed
completed files, without emulator launch, state load or guest write.

## One approved write and the actual fatal chain

The88 prefatal input records match the successful actual aim trial's first
88 Right/B commands. Right occurs only68927/68928, with native0002 first
edge then held without repeated edge. B is a single fresh native0080 edge
at69000; its next-frame actor record at69001 has both held/edge0080.
Immediately before authorization, the69000 actor record still has SECOND
HP37 and FIRST held/edge0. The same-core authorized checkpoint has HP1.
The frozen observer releases every button after the accepted lethal hit;
its later sampled actor records retain held/edge0. It does not emit3000
individual input records, and this audit does not invent them.

The closed ledger records exactly the approved16-bit SECOND+64 write at
core69000, address0201188C,37→1, attempted flag consumed before the API,
FIRST HP4/score0 and neighboring words2120/4 preserved. These values also
match all relevant full snapshots. One-shot/API-width/count behavior was
independently executed in the preceding frozen Lua QA. There is no
separate full-RAM binary dump immediately before the write at69000, so an
independent same-epoch whole-memory inverse is not claimed; evidence here
is the pinned sole write site, closed ledger, scalar transition and full
post-write snapshot.

At core69014, before-HP-store hook0836E5E4 exposes R15=0836E5E8,
FIRST R4=02011710, SECOND R5=02011828, HP1, damage R0=1 and computed R8=0.
The subsequent post-store hook exposes0836E5EC and memory HP0. Fatal branch
0836E5EC and resident085CD960 are recorded. At0836E604, the actual adapter
return has R0=SECOND and R5=aux02011940, upper callback085BDD00 and aux
085BF204. These are native callback installations, not observer writes.

Healthy root5 at083736B0 follows in core69014 while FIRST remains HP4;
stage11 case5 passes R8=086FC300. The outer69015 snapshot contains these
same-advance milestones and a newly allocated active terminal scene header
020121E8, priority0FF0. Native route/terminal entry executes in core69015.
The first085CD0A0 entry sees timer121 and FIRST HP1: that FIRST change is
expected native terminal behavior, rather than an external P1 cheat.
The outer69016 snapshot has scene callback085CD0A0/timer120, common0080,
control07 and scene payload+52=0005.

## Exact bounded stall evidence

From outer69016 to final71927, the entire0x118-byte physical slot at each
of the following headers is byte-identical, across a2911-frame distance:

| Physical header | Object |
|---|---|
|020121E8|active terminal scene|
|020116F8|FIRST payload02011710|
|02011810|SECOND payload02011828|
|02011928|aux payload02011940|

All98 later30-frame samples retain scene timer120/phase52=5, common0080,
control07, FIRST HP1, SECOND HP0, upper callback085BDD00/counters26,1,0,
and aux085BF204/countersFF93,0,0. Final scene remains active, priority0FF0;
terminal controller owners are08374FAC/0837354C. No assertion that this
alone proves the scheduler's causal defect is made; source/caller analysis
belongs to the parallel investigation.

The exact registered actor entry hooks085BDD00 and085BF204 never record
an invocation, despite those installed callback pointers. Neither do their
later phases/no-ops, the next terminal phase, camera route, IRQ guard or
family, cleanup or mode8. This is absence at these registered hook points,
not a complete instruction trace. Aux+18 remains FIRST and+28 SECOND in
all dumps. The known native IRQ guard's alternate aux18 predicate is not
reached in this attempt, so it is not asserted as this stall's cause.

No invalid producer/overlap/scratch/dispatch, P1-death/root4 or script-error
record appears. The sole failure is the honest bounded outcome71927.
Its immediate scalar file contains that outcome/state and exactly the last
256 trace records before the final outer capture; it is not substituted
with a fabricated later phase.

## Genuine states and whole-Core qualification

Five genuine BizHawk2.11.1 GBA checkpoints pass ZIP CRC/entry structure,
ROM identity/native frame and equality of entire IWRAM/EWRAM/VRAM/palette/
OAM with their independent same-frame dumps:

|Checkpoint|Export core|FIRST/SECOND HP|Observed hook core|
|---|---:|---|---:|
|00-before|68927|4/37|68927|
|01-authorized-hp1|69000|4/1|69000|
|02-lethal-hit|69015|4/0|69014|
|03-terminal-route|69016|1/0|69015|
|04-bounded-no-completion|71927|1/0|71927|

Each has typed active physical FIRST/SECOND/aux owners, reciprocal
self/opponent/aux links, correct live controller task ownership for its
phase, unchanged SyncSettings and only the four authorized probe
arguments in UserData. PNGs are240×160 and display-register dumps are96
bytes. Full display-register dump equality to a separately decoded native
Core I/O region is not claimed; the five RAM-region equality is exact.

The complete restored Core equals the preceding successful1477 aim
trial's restored Core byte-for-byte, SHA
`4A282CF92BD125BC0C9045CF1546482B2AD6AB72DABF2009E4FE22AB5586F783`.
Original healthy Core is6A81. Its CRC-adjusted strict comparison still
fails with nine differences at326,327,330,342,343,384,385,393,397. Both raw
and CRC-adjusted differences are retained in the report without audio,
serial or other normalization. CPU banks, native extensions, managed
suffix and all five initial RAM regions are equal. Inherited HUD tiles do
not establish cold-entry HUD visual parity.

## Frozen independent artifacts

- `tools/verify_gba_shoot_terminal_capture.py` SHA256
  `1C19681BA22C6CF01B2A0B0B5C0EC8258456A94E27E4277E9F514511AF3AE5F5`.
- `build/gba-shoot-terminal-capture-qa-20261109/final-report.json` SHA256
  `1A88D19594D922A9B660CF6D86AFD86C2F2DC49E496D144825EB79D454661DBE`.
- Immutable launch inventory SHA256
  `D794BA5633B36882230BD6C7107960B930A959B956463BB1C9DB7313013AA7FE`.

```powershell
python -u -X utf8 tools/verify_gba_shoot_terminal_capture.py --root-completed --output <new-report-path>
```

The earlier `report.json` predates additional explicit native Right/B-edge
assertions; `final-report.json` is the completed frozen result. Observer,
host, ROM, actual capture, main and Git were untouched. No old full suite
was rerun. Terminal/IRQ completion, general source lifetime, historical E5
and final-port completion remain open.
