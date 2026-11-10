# Actual palette-call repair trial: independent capture audit — 2026-11-09

PASS for integrity and controlled comparison of the completed FF3A trial
`build/bizhawk-gba-shoot-terminal-palette-20261109-a`. The actual result is
still **failure:bounded-no-completion** at71927 after3000 advances. The
repair passes the previous actor/scene stall and reaches terminal085CD510.
The observer reports a concrete auxiliary-owner guard refusal at69932;
accepted IRQ family, cleanup and mode8 are absent. This is progress and a
new bounded failure, not terminal completion.

All187 files match the finalized launch inventory. Frozen F0FB ROM-only
wrapper, unchanged964B observer,F6EC host,42A3 pins, four script pins,
exact FF3A copied/loaded ROM, checkpoint copies and private configuration
pass. No host stop/deadline occurred. No emulator, state load, guest write,
retry or evidence modification was performed by this reviewer.

## Controlled prior-trial comparison

The restored whole Core and each00-before/01-authorized-hp1/02-lethal-hit/
03-terminal-route whole Core equal their prior1477 terminal-trial
counterparts after changing **only** bytes12..15 of comparison buffers to
the FF3A ROM CRC. Nothing else is normalized, including audio or serial.
All five RAM dumps of the first four snapshots also equal the old trial.
All88 prefatal input records and the first190 complete scalar trace lines
are byte-identical through the03-terminal-route capture record at69016.
The next new record is actual upper085BDD00 entry in core69016; the old
trial instead proceeds to its frozen69017 outer frame record.

The sole approved write ledger is byte-identical: Q37→1 at69000, address
0201188C,16bits, consumed before the attempt, preserved neighboring
words2120/4, FIRST HP4/score0. The same fresh B produces the actual1→0
FIRST→SECOND hit/fatal adapter/healthy root5/case5 at69014. Native terminal
sets FIRST HP1 at69015. These are controlled identical input/hit prefixes;
no alternative starting state, input policy or extra write is hidden in
the comparison.

## Fresh native progression and actual refusal

|Milestone|Observed core|Outer export core|
|---|---:|---:|
|upper085BDD00→repair085CDA40→085BE000; aux085BF204→085CDA70→085BF400|69016|69017|
|aux final085BF600|69135|69136|
|terminal085CD120 /085CD270|69136 /69137|69137 /69138|
|upper085BE200 /085BE600|69196 /69253|69197 /69254|
|terminal085CD2B0 and camera call/adapter|69261|69262|
|terminal085CD340|69262|69263|
|upper repair085CDA60→085BEE00|69320|69321|
|upper final085BF200|69440|69441|
|terminal085CD3A0 /085CD420 /085CD4B0 /085CD510|69441 /69501 /69533 /69593|69442 /69502 /69534 /69594|

The03-terminal-route snapshot still has timer120/control07 as in the old
trial. The next actual69017 snapshot has timer119/control00 and progressed
actors. Camera capture at69261 passes the real R1=268, and return records
scene payload+52=0F58, exactly F00|(2×268−448). Camera is not replaced with
a tile row, forced constant, clamp or invented source-DI operand.

At69932, actual guard entry086FF9C0 records the observer's first refusal
`native-guard-aux18-not-upper`. Aux callback is final085BF600 and links
are+18=FIRST02011710,+28=SECOND02011828. Upper is final085BF200; FIRST is
grounded ready0835620C with zero held/edge/motion. Prepared and freshly
copied queue are both1/08587200. No guard-accepted, queue-substitution,
guarded display, custom IRQ entry/match/final, next-scroll or cleanup
record follows. Return R0=0 is not directly logged by the frozen observer,
so this report distinguishes its observed refusal predicate and lack of
accepted events from a fabricated return-register sample. Source proof
and any next owner-predicate change remain separate work.

Final outer71927 remains mode7/stage11, FIRST1/SECOND0, active scene
020121E8 callback085CD510, timer0, scene52=0F58, flags1486, common0090,
control00 and camera268. Terminal controllers remain08374FAC/0837354C;
upper/aux final callbacks remain installed and aux links retain FIRST/
SECOND. Final prepared count is1, copied count0, pointer08587200. This
later consumed-count sample is not misreported as the guard-time copied
count1. No actual mode8 or cleanup handoff is inferred from phase entry.

## Genuine state and evidence integrity

All19 genuine BizHawk2.11.1 GBA states pass ZIP CRC/entry structure,
ROM identity/frame and byte equality of the entire IWRAM/EWRAM/VRAM/
palette/OAM with their independent same-frame dumps. Their complete phase
timeline, actual hook/export epochs, scene callback/timer, flags/common/
control and camera are included in the machine-readable report. All retain
typed active FIRST/SECOND/aux slots, actual reciprocal links and correct
controller task owners for their phase. SyncSettings remain equal and
UserData contains only the four authorized probe arguments. PNGs are
240×160; display dumps are96 bytes. No full Core-I/O versus display-dump
equality or DMA visibility proof is invented from these facts.

The first-failure file exactly contains the bounded outcome/state and last
256 scalar trace records before the final outer capture. No script error,
P1-death/root4, invalid producer/overlap/scratch/dispatch or unlisted hook
event exists in the exact330-record trace. The original healthy Core's
strict identity and CRC-adjusted identity still fail with the same nine
non-CRC differences; raw and CRC-adjusted differences are retained without
normalization. CPU bank, native extensions, managed suffix and original
five initial RAM regions are equal. Inherited HUD tiles do not establish
cold-entry HUD parity.

Frozen independent files:

- `tools/verify_gba_shoot_terminal_palette_capture.py` SHA256
  `F31CC74D8C967359E94AFE7FE30AD38A0D74BD7988B18E233DFEFBCD7DD92E24`.
- `build/gba-shoot-terminal-palette-capture-qa-20261109/report.json` SHA256
  `91E07B23E25ABC5510B77B7D1F3C8D6930D51807A2D91D7A870E39E2B6018096`.

```powershell
python -u -X utf8 tools/verify_gba_shoot_terminal_palette_capture.py --root-completed --output <new-report-path>
```

No author/runtime file, main build or Git state changed; no old full suite
was rerun. Terminal/IRQ completion, source-DI identity, general moving
lifetimes, historical E5 and final-port completion remain open.
