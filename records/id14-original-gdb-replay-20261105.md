# Original E5 protocol replay — 2026-11-05

Prepared diagnostic only. Root owns invisible emulator execution. No ROM
repair, emulator launch, provided-save access or guest-memory write was
performed by this worker. The original E5 remains unresolved.

## Exact historical interaction

The preserved failure is
`build/runtime-waterfall-third-exit-20261023-a/probe.json`, SHA-256
`22A2F2D822688D1E2E7239C987F303AA2F6AA8FEE6AD0A5EBADA4437D16C9937`.
Its ROM is389F56FF…ABD7F1 and executable0D9A2779…54950288. It verified the
launched PID's GDB endpoint and ROM identity samples, not a complete loaded
ROM hash. Initial `qSupported` returned empty and initial `?` returnedS02.

The historical harness at commitbdc4389 then did:

1. `Z0,836d348,4`, followed by host-wall-clock timers and `c`.
2. Start at49.5seconds; A at55/65/88; Right76/80/84; Left91; twelve Down
   pulses56.0..61.5 at0.5second intervals. Every press lasts0.25seconds.
   Timers are created in A/Right/Left/Down/Start order, with their individual
   delays relative to each Timer's start. The240second deadline begins
   before the Timer creation loop. Timers continue while GDB has stopped CPU.
3. OneS05k at0836D348. All17 registers match the later seed-watch fixture:
   r0=08584B80,r1=08584B48,r2=1F,r3=2,r4=020120D0,r5=3,
   r6=03002608,r7=03004708,r8=03004CF8,r9=08584B00,
   r10=3F40,r11=0,r12=0837D5E9,SP=03007ED8,LR=0836D320,CPSR=10.
4. Read `g`; remove `z0,836d348,4`; read stack128bytes, table08485000/60,
   object020120D0/256, renderer030012C8/8 and phase03002568/4. r5=3 causes
   the presentation read to be skipped. The old harness also saves its JSON
   at several points while stopped. No failure-time RAM pair was captured.
5. One `s`, responseS05. There is no post-step register packet in the old
   report. Then `Z0,8585310,4` and `c`.
6. The exit breakpoint is not observed. At bounded timeout the harness sends
   Ctrl-C, obtainsS02 and reads `g`, mode and Waterfall fields only.

The final tuple coherently identifies typeE5: r1=1BA,r8=0836EBA8,
r9=PC=E28DD00C,LR=08353FF0,CPSR=40000010,SP=03007ECC.
The effective word0836EF1C containsE28DD00C. r4/r5 are actor addresses
02011710/02011828 at that point, not collision-record handles.

The extra `k` inS05k is intentional in this emulator's breakpoint response,
not evidence of a malformed packet: the pinned source formats that response
when hardware/software breakpoint capability negotiation is absent.
Its `s` handler enters the ordinary core step path. These are implementation
facts, not a claim that this binary/core has no broader timing defect.
[Pinned mGBA GDB implementation](https://github.com/mgba-emu/mgba/blob/fa977ccbc815efc93aefad9acddc9af0577d7827/src/debugger/gdb-stub.c#L69-L119).

## Why the earlier no-hit observations do not replay this failure

The immediate ROM-read-watch run armed0836EF1C from launch, without the first
seed stop/step. The later seed-watch reached the exact same17-register seed
tuple but added294,912bytes of full RAM reads before `s`, then installed the
ROM read watch. Both retain the same intended wall-clock input schedule;
their different stop duration can move key events between paused/running
intervals. Neither report timestamps actual key posting or post-step state.
Frame-indexed BizHawk18k/30k trajectories also do not reproduce this interaction.

## One targeted replay and its controlled continuation

`tools/probe_collision_original_replay.py` preserves the original small seed
read order and original second exit breakpoint. It adds no collision/read
watchpoints and no full RAM dump before stepping. Its default `--step-mode
gdb` performs the original `s`. Immediately afterwards it records registers
and the actual03004CF8 halfword. A normal successor of the stopped STRH is
PC0836D34C with all other registers/flags unchanged and halfword2 stored.
Differences are reported, not automatically classified as a ROM/core bug;
scheduled exception processing is a possible separate explanation.

The replay records actual wall times, virtual key codes, pressed/released
state and number of owned windows posted to. Its in-memory RSP journal logs
complete command/response payloads and Ctrl-C timing; byte-level ACK traffic
is not logged. It writes the journal after stopping, avoiding per-byte disk
logging during the delicate seed interaction. At the final stop/timeout it
always preserves complete IWRAM/EWRAM and all registers.

The final decoder uses saved SP+0C/+10 record handles as candidates only
while that stack remains the dispatch predecessor. It reports actual list
records, scratch/counts, active presentation event/index/count/base/current,
A/B/P1 pointers, matched declared resource rows, event domain and pointer
consistency, and the selected ROM B types. It separately treats r4/r5 as
actor views. A current-B mismatch narrows the investigation but does not
prove a writer: an earlier collision could legitimately have changed the
actor's presentation after append. The first actual E5 append/overwrite
remains the repair gate.

If the default replay reproduces or its post-step state diverges, the same
tool's `--step-mode next-exec` is the narrow control: replace only `s` with
a hardware breakpoint at0836D34C, `c`, stop, remove that breakpoint, then
record the same successor and continue to the same exit breakpoint. A fresh
second process/output is required. This executes the STRH through ordinary
continue rather than the GDB step API. Different late outcomes alone are
not a causal finding unless seed state and actual input/timing evidence are
comparable. Do not repeat a general18k input loop as a substitute.

## Exact launch handoff

Tool SHA-256:
`3B1B2C13DCFD5D55CCEF451E3C2A97A94ABCA6979A0254B6163C479BBDDE5DB3`.
The tool refuses any unpinned ROM/executable and any existing output folder.
It copies the ROM to a fresh output-local `probe.gba`, so no adjacent existing
native save is needed. Only read/control/breakpoint RSP commands are allowed;
register writes, memory writes and continue/step with replacement addresses
are rejected. No supplied WSC save or savestate is an input.

```powershell
python tools/probe_collision_original_replay.py build/stage-priority-routing-20261023-a/current-candidate.gba build/collision-original-replay-20261105-a --mgba local/mgba-dev-complete/mGBA-build-2026-08-23-win64-9127-fa977ccbc815efc93aefad9acddc9af0577d7827/mGBA.exe --step-mode gdb --timeout 240
```

The historical ROM and exact executable hashes are checked against the
original fixture. CurrentA4CB752A…85328F is also explicitly accepted for a
later current-candidate check; this does not replace the historical replay
or roll back the main candidate. Root launches one private desktop at a time.

Completion is `replay-done.txt`, written only after `replay.json`, all final
RAM and `rsp-and-input.jsonl` close. Outcomes distinguish original-invalid-
target reproduction, original exit observed, seed-not-comparable and other
bounded state. A setup/protocol error leaves session_finished=false and no
success marker. The self-check covers read-only command boundaries, the
seed successor, original schedule, saved-record resolution, current-ROM B
mismatch/match and out-of-domain event detection without emulator/ROM/save I/O.

Limits: the old report has no actual key timestamps, exact pause durations,
full loaded-ROM hash or pinned initial native EEPROM/configuration. The new
post-step reads add small host delay. This is an instrumented protocol replay,
not a claim of identical historical host timing. No new E5 fix is asserted.

## Root execution A: first pattern differs

Root ran the frozen tool invisibly against the exact historical ROM and
executable in `build/collision-original-replay-20261105-a`. The session
finished normally, preserved its final RAM/journal, and reported
`seed-not-comparable`. At the first breakpoint, all17 registers matched the
historical seed except r3: the new value was0, while the original was2.
No `s` command was sent and no exit-path or E5 observation is claimed.

This value is the Waterfall pattern selector, not a collision type:
0836D310 loads the random word, 0836D31C calls0837DB3C with divisor r5=3,
0836D320 copies the remainder r1 into r3, and0836D348 stores it at03004CF8.
Waiting for another battle's breakpoint would change the tested trajectory;
writing the historical value would falsify it. Neither was done.
The complete input journal contains30 key posts before stopping; the later
scheduled inputs were cancelled during cleanup. The captured RAM belongs
to this producer seed, so its stack slots are not failure-time dispatch
records. The report's candidate stack decoder must not be read as such.

| Artifact | SHA-256 |
| --- | --- |
| `replay.json` | `90664D3C2A8F1509AC7F73797FF2D1201A04D513DF4B9C65FD06C3CD9803DF57` |
| `rsp-and-input.jsonl` | `6145226C4594E102650C62FD0F70748E7C61DD13E366FDA86B09A06174B86516` |
| `seed-mismatch-iwram.bin` | `E1F6533181AEC0D73002695785B861AA47F544D3672FEDD3EDB9F96CF5381C51` |
| `seed-mismatch-ewram.bin` | `57EDC8F6825B61060448D473FDF9868D4292E0543F915472ACABE2D6D76A27AE` |

The old report does not pin initial native EEPROM/configuration or actual
input timing. An identical ROM and requested schedule therefore do not
establish an identical random selector or gameplay path. E5 remains open.

## Independent seed-owner review and one timing comparator — 2026-11-06

Read-only disassembly of the exact historical `389F56FF…ABD7F1` image binds
the immediate pattern input to `03004CEE`: `0836D30C` resolves its literal
at `0836D410` to that address, `0836D310` loads its halfword, and division
by the source row's `r5=3` produces the remainder stored through `r3`.
The earlier config-owner description remains correct through a snapshot:
`0836D258..264` resolves `03002310`, reads signed offset `16`, and copies
its low halfword from `03002326` to `03004CEE` before pattern selection.
Replay A's captured value is `FFF3` (unsigned65523), whose remainder is0.
The consumer uses LDRH, so signed interpretation of this value is incorrect.

The positive producer is the third RNG call at `08091190`, followed by
`08091194: STRH r0,[r4,#16]` with `r4=03002310`. Its initializer at
`08091154..178` seeds native RNG `08012634` with the halfword at
`[[0300133C]+1A]` and counter `030012B4`. Native `08012600..1262C`
uses state halfwords at `03001420/+2`. For state `(a,b)`, each call computes
`raw=a+b+3711`, stores `(b,raw&FFFF)`, and returns
`(raw>>8)+((raw&FF)<<8)`; the third return's low16 bits are stored at2326.
The raw carry byte matters: this return is not always a clean16-bit byte
swap of the stored state. These actual native bytes are the oracle; this
review does not claim that a fixed host delay guarantees a chosen residue.

The smallest proposed comparator changes only final roster-confirm A65.0s
to65.25s, with subsequent battle inputs shifted by the same0.25s. This is
ordinary input on a fresh process and isolated ROM, with no guest writes,
save inputs or later-battle reroll. It is explicitly a timing variant,
not an identical historical replay. Before attributing its later behavior,
require all17 seed registers to equal the historical tuple, including
`r3=2`; a mismatch remains exploratory and cannot close the original E5.

The existing replay records full-tuple equality but originally permitted
step/continue after checking only PC/r3/r8. This review identified that
classification gap to root before interpreting variant B. A run already
in progress must keep its diagnostic source frozen; any false full-tuple
flag excludes a comparable-replay claim even if that older guard continued.
Only root launches runtime. This independent review performed no emulator,
supplied-save, guest-memory-write or ROM modification operation.

## Variant B and revised comparability gate — independent audit

Root's completed hidden timing variant is
`build/collision-original-replay-20261106-b`. Independent read-only review
checked its completion marker, requested 20-input schedule with0.25s confirm
delay, all17 registers, complete RSP journal and both final RAM hashes.
It again stopped with only `r3=0` different from the historical `r3=2`;
the other16 registers match. Its entire journal contains no `s` command.
Both A and B therefore remain seed-not-comparable observations; changing
the requested timing did not reproduce the historical E5 interaction.
No equivalent timing retry or repair follows from these two results.

After B ended, root replaced the old PC/r3/r8 predicate with exact equality
to the complete historical17-register tuple. Independent rerun of the
read-only self-check passed, including17 single-register changes, each
required to be rejected before step/continue. The schedule's default stays
historical; `--confirm-delay 0.25` names the separate timing variant.
The read-only RSP command boundary and mismatch capture/cleanup remain intact.

| Artifact | SHA-256 |
| --- | --- |
| Current diagnostic, full-tuple guard | `A1FBA1F31946739A99BFD93424282C4F41A060856CEAB1525B52A24B23227CD9` |
| B report | `96B66744799F98FFE93453A9E3FB63D343F14B4F61724D3DA97467518E82DA4D` |
| B journal | `F07C0F00C5A480B17C66D437DBB8119D041AF5FD976896FFB57666D5A66B1C2E` |
| B IWRAM | `B20E7E2B8FB5FA9D75C289263A4059047EFCEA3D529D8844D8A6FBD9A0507734` |
| B EWRAM | `8AE43CEAF27530FF76547EA7CE5465BCAB64C5929B4B6AEBC79E7F11C49DE73A` |

B used the earlier confirm-delay revision, before the stricter tuple guard;
the current diagnostic hash is not attributed retroactively to its launch.
Reversing only the full-tuple helper/guard/self-check edit reconstructs
predecessor hash `F5511664EDC67620E6E2FFED4F9053293C95CA78744F7883A283E8EACD4DBED5`.
That is a source reconstruction, not a hash sampled by B's launch report.
Independent evidence is
`build/collision-original-replay-qa-20261106/audit.json`. E5 remains open.
