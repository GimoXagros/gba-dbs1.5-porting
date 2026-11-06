# Earlier menu commit and first Waterfall seed — 2026-11-06

The next discriminator observes the seed before it is generated. Prior A/B
first-pattern stops both had r3=0 rather than the historical r3=2; the later
A65 confirmation delay therefore supplied no comparable E5 replay. This
record prepares one bounded earlier observation. Root alone launches it.

## Positive earlier commit and exact native recurrence

Read-only disassembly of exact historical ROM
`389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1`
establishes the menu callback at08090FA0. Its ordinary path at08090FFC
resolves current task `[0300133C]`, adds18, and increments both private
halfwords at+18/+1A before testing input. At08091080..B8 it reads native
new-key halfword0300130A and branches on ordinary A mask40 to08091110.
That commit writes the selected menu value to03002312, installs callback
08091310, and then initializes RNG before returning from this invocation.
The historical input plan places A55 before the twelve roster Down pulses
56..61.5 and final A65. The new stop timestamps will establish which posted
input actually reaches this earlier commit; A55 is the source-backed target
for the proposed comparator, not a claim of already measured host timing.

At08091164 LDRH loads r0 from the current task's private+1A halfword.
08091168 resolves030012B4 and0809116C LDRH loads its counter into r5.
The first stop08091170 is immediately before `PUSH {r0}`, followed by
`PUSH {r5}` and08091178 BL08012634. That helper resolves03001420,
loads `[SP+4]` into its first state halfword and `[SP]` into the second.
Thus preseed r0/r5 are exactly `(a,b)`; there is no guessed RNG state.

Native08012600..1262C computes each call as:

```text
raw = a + b + 3711h
state = (b, raw & FFFFh)
return = (raw >> 8) + ((raw & FFh) << 8)
```

The first three return low halfwords are stored by08091184/18C/194 into
03002322/24/26. Stop08091198 is before the fourth call. Comparing all three
stored words and both actual03001420 state halfwords positively checks the
prediction, including raw carry handling. Clean16-bit byte swap is invalid
when the raw addition carries. Both initial seed inputs are unsigned LDRH.

The Waterfall manager later reads signed config+16 at0836D25C and stores
the low halfword to03004CEE at0836D264. Its eventual pattern consumer is
**unsigned LDRH**, actual bytes `B000D8E1` at0836D310, resolving its literal
0836D410 to03004CEE. The divisor r5 is the positive row halfword3 loaded
at0836D308. Consequently unsigned stored-word modulo3 predicts the first
index; the earlier signed copy does not sign-extend the later LDRH input.

## Frozen diagnostic and launch

`tools/probe_collision_preseed.py`, SHA-256
`3A9348A00561102E9E9770B0738F16BA0C94C120267B999867617CD8E7A7042F`,
stops only at08091170,08091198 and the first0836D348. It records all17
registers, actual key/RSP timestamps, minimal menu ownership fields, all
three stored random words, both RNG state halfwords, and final4CEE/index.
There is no `s`, collision watch, replacement PC, register write or guest
memory write. It uses the pinned historical ROM/executable in a fresh
output-local ROM path; supplied saves and savestates are not inputs.

```powershell
python tools/probe_collision_preseed.py build/stage-priority-routing-20261023-a/current-candidate.gba build/collision-preseed-20261106-a --mgba local/mgba-dev-complete/mGBA-build-2026-08-23-win64-9127-fa977ccbc815efc93aefad9acddc9af0577d7827/mGBA.exe --timeout 160
```

Default input times match the original requested plan. Only after inspecting
this baseline, `--menu-delay .02` is the bounded normal-input comparator:
shift A55 and every later input by20ms, preserving earlier Start49.5 and
all pulse durations/order. Twenty host milliseconds do not guarantee one
guest frame or index2. The recorded actual seed inputs and exact prediction
determine whether the intended path changed; no later-battle reroll is used.

`--self-check` passes exact zero-state and overflow RNG vectors, stored-word
and state mismatches, both menu schedules and the read-only RSP boundary.
It launches no emulator and reads no ROM/save. Completion is
`preseed-done.txt`, written after closed report/journal files. Bounded misses
and prediction mismatches remain explicit outcomes, not reproduced E5.

The preseed stops add timing perturbations. Even matching the first pattern
and the complete historical17-register tuple does not turn this observer
into an identical historical protocol replay. It neither steps the seed
store nor follows the old exit breakpoint. Actual first bad collision writer,
historical E5 reproduction and a justified repair remain open.

## Completed preseed A/B and frame delivery correction

Independent audit of A verifies all133 journal entries, complete input/copy
ROM identity, 28 actual ROM-read chunks covering all20 declared loaded-ROM
sample windows, endpoint PID consistency, all three stored random words and
both RNG state words. A55 was posted at55.016s relative to the input epoch;
the preseed stop was55.031s, before Down56 and final A65. The earlier menu
commit is therefore measured, not only inferred from the source branch.
The30 posted key transitions before the first pattern stop were within17ms
of requested wall times. No `s` or guest-write RSP command was sent.

A's actual inputs are63637/3291; its three stored words are33340/28032/65523,
RNG state32877/62463, and first index0. One additional menu/main update,
63638/3292, predicts33852/28800/1268 and index2. Two additional updates
predict first index1; three return to0. This follows positive actual writes:
main080002A4..2B0 increments030012B4 and menu0809100C..20 increments the
task private halfwords before each A test.

Root's fresh B with20ms requested menu delay instead measured inputs
63639/3293: **two** additional updates. All three words34364/29568/2548,
state32883/62473 and first index1 match the independent prediction and
actual journal reads. B's A was posted at55.031s and its preseed stop was
55.046s. Host milliseconds are therefore not an exact guest-update selector.
No further milliseconds comparator is proposed.

| Independent audit | SHA-256 |
| --- | --- |
| `build/collision-preseed-qa-20261106/audit-a.json` | `B3E757816627BFB250FB1644B8CC805DC5FFD49E2DA5F3748BB8BC324B04CA07` |
| Same directory `audit-b.json` | `1959701ECFC46987AFC9FA2869452060137CDAA68A8CC9A761040E8D7E216E70` |

The subsequent frame observer selects an actual neutral menu update at
080910B4, after R0 has already latched zero new keys. Posting ordinary A
while stopped cannot change that current R0 or make its A predicate true.
It chooses only a measured state whose next+1/+1 private/counter prediction
is index2, then observes the next callback at08091088, immediately after
the native new-key LDRH. Only actual+1/+1 state and latched R0 exactly40
permit continuing to the full historical17-register seed gate.

The first frame observer revision `FE79F714…A17AA3D` stopped after268 neutral
updates at63637/3291 with the correct next-index2 prediction. Its separate
attempt to acknowledge A through KEYINPUT while CPU-paused failed: A was
posted to nine owned windows, but it was released by the old250ms timer
before the paused polling check ever accepted it. The report remains
session_finished=false, no completion marker or `s` exists, and its partial
report/journal are preserved under `build/collision-frame-menu-20261106-a`.
This is a diagnostic delivery-check failure, not a game/core defect or E5.

The corrected `tools/probe_collision_frame_menu.py`, SHA-256
`58CAEBB48B66717C9593813D817C9CFDE14FB72FDB1120948AF52572B6FC1B1F`,
removes that paused-hardware acknowledgment and timed early release. It
requires a positive owned-window PostMessage count, continues to the next
actual native key latch, and releases A only after observing that latch.
The+1/+1 and R0=40 checks remain mandatory; any latency or prediction mismatch
captures state and ends without `s`. No hidden retries, memory writes or
replacement PC are introduced. A's failed revision is not overwritten.

After a valid latch, remaining normal input offsets are anchored to actual
delivery. The first Waterfall stop must match all17 historical registers
and the independently predicted three stored words/snapshot. Only then does
the diagnostic use the original small read order, `s`, successor check and
original exit breakpoint. Final full RAM and collision decoder are preserved
for exit, invalid target or bounded other state. These earlier menu stops and
input anchoring make it an instrumented protocol variant, not identical
historical host timing. Self-check covers one-update/mask negatives, ordinary
input offsets and the read-only command boundary. Root alone launches it.

```powershell
python tools/probe_collision_frame_menu.py build/stage-priority-routing-20261023-a/current-candidate.gba build/collision-frame-menu-20261106-b --mgba local/mgba-dev-complete/mGBA-build-2026-08-23-win64-9127-fa977ccbc815efc93aefad9acddc9af0577d7827/mGBA.exe --timeout 240
```

The unused menu-delay option briefly prepared for the original replay was
removed before any launch. Its source again matches frozen `A1FBA1F3…227CD9`;
the original default schedule and full-tuple guard are unchanged. No game
ROM repair is justified by the evidence collected so far.

## Frame B: exact known seed packet, different retained random words

Root completed `build/collision-frame-menu-20261106-b` with frozen
`58CAEBB4…6FC1B1F`. Independent audit verifies all8,905 journal entries,
40 owned-window key posts, all20 loaded-ROM sample windows and29 actual ROM
read chunks, both complete final RAM dumps against the journal bytes, and
the completion marker. Ordinary A was delivered in exactly one observed
menu/main update:63637/3291→63638/3292, R0=40. A was held for16ms and released
after that latch. First Down was56.032s, later A65.032s; the original harness
requested56.0/65.0 and250ms A holds, without actual-post timestamps.

All17 first-pattern registers exactly match the historical failure. All five
small seed regions also match, byte for byte, including addresses:128-byte
stack,60-byte table,256-byte object,8-byte renderer state and4-byte phase;
**456 bytes total**. The single actual `s` produced precisely PC0836D34C,
halfword2 at03004CF8 and unchanged other registers/flags. This positively
narrows the investigation: the known seed packet plus one normal STRH step
does not by itself force the old invalid target.

B ended at the240s bound in native mode9, PC08011200 (native wait on the
030012D4 owner), list counts0/0/0, scratch type9 and hazard active gate0.
The original failure ended in mode7 and the E28DD00C invalid target.
No timestamp of B's mode transition, third-pattern constructor execution or
exit lifetime was observed. The final wait stack is not a collision dispatch
stack; its saved-handle decoder output must not be treated as such.

A stronger positive difference survives in the original report's
`timeout_native_mode_hex`: config03002322/24/26 contains
**963C/8B80/31F4**, while B contains**843C/7080/04F4**. Both third words have
remainder2, so matching r3 was insufficient to match these battle random
words. The three values influence the manager's timing as well as its index.
Their exact native recurrence has a unique inverse among the possible raw
carry cases: original inputs63647/3301, with raw additions81045/32907/62513.
The difference from B's inputs is+9/+9; private-minus-counter60346 is the
same in the observed baseline and reconstructed historical tuple.

The next revision therefore selects **all three historical words**, both
when choosing the neutral update and in the observed one-update gate.
Frozen `tools/probe_collision_frame_menu.py` SHA-256 is
`86FD4DE6DC7CFE130A8035F9F02D6277CC711D96C56F6064C20A3B3747154366`.
Its self-check accepts63646/3300→63647/3301 and rejects B's same-index2 but
different random triplet. Existing full17-register and five-region reads,
normal `s`, exit breakpoint and final-RAM capture remain unchanged. There
are no extra producer traps in this revision. Root alone chooses its launch.

Independent B evidence:
`build/collision-frame-menu-qa-20261106/audit-b.json`, SHA-256
`DBEAA73C3E720D0BBBC3B64A1661ECA496B373F5537440EBE48FC7CB13497BB1`.
This is a controlled narrowing, not an E5 repair or identical full-state claim.

## Historical native save/config eligibility — metadata and code only

Historical `bdc4389:tools/probe_physics_consumers.py` launches the requested
ROM path directly with repository cwd and only the two pause-related config
overrides. It makes no isolated ROM copy or save/config directory override.
The generated GBA sibling
`build/stage-priority-routing-20261023-a/current-candidate.sav` exists with
length512 bytes, creation2026-10-23T07:50:28Z and last-write07:50:29Z. The
original E5 report was created08:15:53Z, so this save predated that launch.
Only filesystem metadata was inspected; no save bytes were opened or loaded.

The pinned frontend reads Qt/core configuration at startup, and the core's
save-autoload path opens its configured save directory using the ROM's `.sav`
suffix. Thus that adjacent generated save is eligible under the default
save-directory policy. The old report does not establish which file actually
loaded, the old config values, or any causal effect on E5. An output-local
ROM copy alone also does not prove fresh global configuration or a fresh
save backend if a custom save directory is configured. No supplied WSC save
was accessed. See pinned
[Qt configuration startup](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/platform/qt/ConfigController.cpp#L122-L149)
and [native save autoload](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/core/core.c#L240-L251).

## Exact-triplet C and causal-observer handoff

Root's completed `build/collision-frame-menu-20261106-c` positively matches
all17 registers, all456 small-read bytes and all three historical random
words. Actual input delivery is63646/3300→63647/3301 with latched R0=40;
normal `s` again has the exact17-register successor and halfword2. All final
RAM bytes match the recorded RSP reads, all20 ROM sample windows match,
and40 key posts target nine owned windows each. C ends bounded in native
mode9/PC08011204, scratch9 and counts0/0/0. It neither reproduces nor resolves
the historical E5. Its independent audit is
`build/collision-frame-menu-qa-20261106/audit-c.json`, SHA-256
`4858EE0A89E7B4503DD46FA61E02AFB6779583953E6E1A558E6935D31BB813E4`.

The exact C diagnostic source is preserved at
`build/collision-frame-menu-qa-20261106/frozen-frame-menu-86FD.py`, retaining
its original86FD4DE6 hash. The shared frame protocol now takes one explicit
post-seed observer callback; the default exit-only path is unchanged. In
the causal path, only the initial roster inputs remain on host timers.
Remaining battle inputs use counted actual080002A4 main-update entries,
with the initial prebattle ordinal read from native counter minus the
observed menu counter. Later battle counter changes cannot shift this
counted ordinal. Presses occur at1260/1500/1740 updates for Right,1980 for A
and2160 for Left, each held15 counted updates. The observer stops on the
first battle ending or6,000 further updates/deadline, rather than idling
through Continue or repeating an18,000-frame trajectory.

The actual historical image independently establishes the narrow causal
point0836E370:0836E364 loads the type halfword from attack record `[r4+4]`,
0836E368 loads its actor from `[r4]` into r1,0836E36C resolves03004D20 into
r8, and0836E370 is its pending STRH. Function-entry PUSH saves current
record handles at SP+0C/+10. At a type>=26 stop, full RAM therefore retains
the actual invalid record before its scratch copy and enough source/P1/B
provenance to distinguish malformed selection from a later overwrite.
This is the first observed invalid overlap-to-scratch producer, **not** a
claim to have caught the earlier list append or first corrupting writer.

`tools/probe_collision_first_invalid.py`, SHA-256
`362AABD926179983D04B0886B2CB3B5D45B37ECC176C294DCA22C5833A48C9FF`,
uses shared frame source `775D20B23B122A16BF04439CB8C4D65F4F7AF355E4430159856ADB79D9DF3183`.
It keeps the exact-triplet/full17/normal-step gates, then observes0836E370.
Valid overlaps retain only registers and a128-row ring. Main-update stops
read mode and three count bytes; only command/event counts are checked
against their positive12-slot owners. Full RAM is dumped only at a terminal
observation, including an invalid type, count violation, battle end or bound.
One-instruction execution breakpoints rearm without any additional `s`.
The actual bad record and its `+4` address are preserved for a subsequent
first-write watch if needed. Its self-check verifies the complete guest-update
input plan and read/control command boundary. Root alone launches runtime.

```powershell
python tools/probe_collision_first_invalid.py build/stage-priority-routing-20261023-a/current-candidate.gba build/collision-producer-frame-20261106-a --mgba local/mgba-dev-complete/mGBA-build-2026-08-23-win64-9127-fa977ccbc815efc93aefad9acddc9af0577d7827/mGBA.exe --timeout 240
```

No single wide GDB watch is used: the pinned stub initializes its watch
range as one byte and ignores the requested length, so a claimed whole-list
watch would be false. See
[pinned watchpoint construction](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/debugger/gdb-stub.c#L574-L603).
No corrective ROM edit follows from the current no-hit runs.

Root-authorized inspection of the current generic pinned-emulator config
found portable.ini length0, config.ini length46 and qt.ini length1637.
Both config files currently have no explicit save-directory, state-autoload,
BIOS or timing overrides among the inspected option names. Their modification
time2026-11-06T05:03:54Z is later than the original October failure, so this
does not reconstruct that historical configuration. No save content was read.

## Causal producer A audit and original-window extension

`build/collision-producer-frame-20261106-a` completed at its6,000-update
bound. Independent review counts all135,230 journal entries, exactly6,000
actual MAIN register packets,5,999 MAIN_NEXT packets, seven E370 pre-store
packets and seven corresponding NEXT packets. All ten battle key posts occur
at their requested counted update, with no additional `s` or guest-write
command. Exact historical triplet, all17 seed registers, all456 small-read
bytes and normal STRH successor remain verified. All complete final RAM bytes
and20 loaded-ROM sample windows match the journal.

The observed overlap-to-scratch types are8/10/8/8/14/8/8. No invalid type is
observed in that bounded window. Final native mode7 remains an active battle,
PC080002A4, scratch8, world/command/event counts0/1/3 and display/hazard words
0000/0103. The observation ends near174.4 host seconds, while the historical
fault was preserved at the240s bound with display/hazard words0002/0103.
The source clocks and phase therefore expose an actual coverage gap; this
run does not cover the original late observation window or establish absence
of E5. The final MAIN stack is not an overlap/dispatch stack.

Independent A audit:
`build/collision-producer-frame-qa-20261106/audit-a.json`, SHA-256
`57383041FFF353AC91691ACBB46C6EDCAD5A456940F91A3E4F703D578E9E069B`.
The362A observer source is archived byte-exact as
`build/collision-producer-frame-qa-20261106/frozen-first-invalid-362A.py`.

Root authorized one original-window extension:12,000 post-seed main updates
and300s host bound, enough for200 guest seconds after the seed rather than
the prior100. Only three textual substitutions change the prior tool:
the update bound, outcome label and default deadline. Reversing those three
substitutions reconstructs the entire362A source byte for byte. All seed,
input, normal-step and producer observation code remains exact. The new
`tools/probe_collision_first_invalid.py` SHA-256 is
`541C222A69BA7FB592FA6141F8FDA376BE12D3E1C2F07825E6A3F7E02A29A0DA`;
its read-only self-check passes. The next output is a fresh
`build/collision-producer-frame-20261106-b` with `--timeout 300`.
Further timing retries are not inferred from a
bounded no-hit. Only a captured invalid producer/overwrite can justify repair.

## Extended producer B: first battle ended, E5 remains unresolved

Root's fresh `build/collision-producer-frame-20261106-b` completed with
`first-battle-ended-without-invalid-producer`. It observed7,340 actual
post-seed main updates and the same seven valid overlap types before native
mode8. Independent audit verifies all163,370 journal entries,7,339 MAIN_NEXT
continuations, seven E370/NEXT pairs, all ten battle posts at their requested
guest-update ordinals, no additional `s`, both complete final RAM dumps and
all20 loaded-ROM sample windows. The first6,000 MAIN register packets and
all seven overlap rows are byte-identical to A's prefix, positively checking
that the extension retained that observed trajectory.

The first actual mode8 read is timestamp196.234s after setup,195.156s after
the input epoch, and122.328s after the seed step. The later196.719s input-
epoch cleanup post follows the RAM dump and is not the battle-end timestamp.
Final display/hazard words remain0000/0103, counts0/0/0 and scratch8. The
12,000-update cap was not reached because this battle ended first. The
historical240s sample was still mode7 with display phase2 and invalid target;
this observation therefore does **not** establish the same historical late
trajectory or failure-window coverage.

All three retained initial random words, all17 registers and all456 small-
region bytes match the historical packet, and the normal seed store is
verified. Complete historical RAM, the current native RNG state/counter at
that seed, exact host pauses/input deliveries and loaded EEPROM/config were
not captured historically. Their equivalence is not established by those
known matches. No invalid producer, first corrupting list writer or causal
E5 repair is demonstrated. Root requested no further replay from these
bounded observations; the original E5 remains open.

Independent extended B audit:
`build/collision-producer-frame-qa-20261106/audit-b.json`, SHA-256
`5F52C9E0E98AE8DD3DE26E147CCA91CBC9EE9B46F5CD4964F2652F6A3197C1DE`.
All observer source and partial/completed artifacts remain preserved. This
reviewer launched no emulator, read no save content and wrote no guest state.
