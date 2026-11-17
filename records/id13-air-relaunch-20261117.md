# ID13 shared aerial relaunch: isolated native component

The missing WSC 1.5 callback graph `8522:0577/0593/066E/0701` is implemented
in `tools/build_id13_air_relaunch.py`. This is a new native controller, not a
resource-only change. It adds the automatic ID13 fall transition and up to
three release/press relaunches, while retaining the existing landing, attack,
horizontal-motion, animation and enhanced-aerial services.

The input is v78 C91, SHA-256
`C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1`.
The isolated output `build/id13-air-relaunch-v79-20261117/component.gba` is
`FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD`.
Its exact writes and source contracts are in the adjacent `component.json`.
Author builder SHA-256 is
`F450172FC1ABFA99F895C1A46309D90E3F4E6A21BD9450B24325BE396171F5B3`.
There are 988 declared bytes and 968 changed bytes. Original ROMs are read-only.
Root owns main-pipeline integration and emulator execution; this record does
not treat isolated static success as completed integrated runtime validation.

## Why this remaining gap was selected

The old `records/iraira-floor-launch.md` correctly left the later ID13 aerial
branches open. The current builder still describes them as unimplemented.
In contrast, broad old claims that Shoot's stationary family is absent are
superseded by the v76 actual-runtime proof. Low-Y behavior still requires a
specific failing runtime witness, and Train's remaining private hazard owner
requires further identification. This ID13 graph has both a complete source
contract and a retained native consumer that visibly omits its identity branch.

Root's new unchanged-C91 capture
`build/bizhawk-id13-fall-entry-20261117-a` observes ID13 at native `0835732C`
at core 5312: callback `08357264`, vertical speed/acceleration `002E/002E`,
`A6=0000`, `A8=0019`, `AA=0000`, held input zero. The next frame keeps the old
callback and scratch fields. This proves actual entry to the omitted gate.
The earlier A hold at cores 4345–4364 is not established as the direct cause
of this later fall; see the independent baseline record.

## Every source entry and retained native route

The complete source graph is raw `785797..785993`, SHA-256
`95AF262178FE267C49AB7DE8DC687C93BDEE5D87430F5DB08567BE75C66E3F77`.
The direct far-pointer assignment to `8522:0577` occurs exactly four times:
`7682FA`, `7684D3`, `7688DF`, `768AD1`. Each has an identical preceding gate:
positive signed vertical velocity, source `+90 & 1 == 0`, actor `+8 & 0100 == 0`,
then identity 13 before the held-input test. All four 40-byte source gates
have SHA-256 `8EE323146B7793890D42DC85BEA3D2EF972560A668F23B178382CFD25F42C9C0`.

| Retained native input load | New selector | Source callers covered |
|---|---|---|
| `08357054` | `08D3F100` | first common fall |
| `0835732C` | `08D3F150` | second common fall |
| `083578D4` | `08D3F1A0` | common jump and Iraira jump |

Every replaced instruction is `E1D482BC`, `LDRH r8,[r4,#2C]`. Existing outer
gates remain in place. Each selector saves/restores its temporary r0 and NZCV;
non-ID13 executes the displaced load and continues at hook+4. ID13 assigns
INIT and returns through the original saved LR. INIT runs on the next actor
dispatch, matching the source assignment/return boundary.

Iraira wait `08627C00..48` branches to `0835774C`; that retained continuation
assigns `083577A8`, whose fall path reaches the third hook. No literal
`083577A8` is assumed to exist inside the private wait. Three native hooks
therefore cover all four source entry sites.

The source enhanced branch `8522:02BD` at raw `7854DD..7855BF` already maps to
`08357DD4`, with native subcallbacks `08357E28/08357E64`; the target is retained
at raw `357984`. ID13 reaches it through new READY when actor `+8 & 4000`
and held `0040` are set. This sets `A6 |= 1`, assigns the existing callback,
and returns without invoking it in the same update. No copied implementation
or changed old-character identity checks are needed.

The legacy input path's source `ID1 OR ID13` test for 02BD is dominated by
the earlier automatic ID13 assignment. Failed outer gates do not bypass the
automatic selector into that old identity test: they skip the entire input
and special-assignment block. The exact skipped intervals are:

| Source gate | Failed-gate destination | Legacy 02BD assignment | Native failed destination / assignment |
|---|---|---|---|
| `7682DC` | `768367` | `76835E` | `083570DC` / `083570D8` |
| `7684B5` | `768540` | `768537` | `083573B4` / `083573B0` |
| `7688C1` | `76894C` | `768943` | `0835795C` / `08357958` |
| `768AB3` | `768B3E` | `768B35` | shared jump continuation above |

For each row, nonpositive velocity, A6/source90 bit1, and actor+8 bit0100 all
branch to the destination after the old special store. Passing those gates
with ID13 assigns 0577 and returns before the held-input test. The first
destination continues ordinary fall handling; the other source destinations
advance animation. Thus leaving the dominated legacy native ID1 comparison
unchanged does not omit a reachable ID13 special route through these callers.
The reachable ID13 special route is READY's source `7857CC`, implemented here.

## State graph and update boundaries

| Source state | Native callback | Behavior |
|---|---|---|
| `0577` | `08D3F200` | Set packed counter/latch A8=0100, horizontal parameter A0=00F0; assign READY and fall through immediately |
| `0593` | `08D3F280` | Horizontal motion; release clears A8 high byte; fresh held40 starts a relaunch; otherwise descending, landing and interruptions |
| `066E` | `08D3F500` | Wait for positive vertical velocity; perform descending setup/landing; count<3 returns READY, otherwise SPENT |
| `0701` | `08D3F700` | Horizontal motion, descending, landing and interruptions; no additional relaunch |

A relaunch sets latch bit 0100, clears AA, stores state byte 10, acceleration
0018 and signed velocity FD80, increments only the low byte of A8, selects
event 72, and assigns BOOST. It returns directly: source `785819` jumps to
the RETF at `785992`, so advancing animation on this initialization update
would consume the first command early. Independent review caught that draft
error before the frozen FBD9 output was emitted.

Release uses `AND 00FF`, clearing the entire high byte. Increment reproduces
`INC AL`, including wrap from FF to 00 without carrying into the high byte.
The first READY update may release the initial latch immediately when input
40 is not held. BOOST does not process horizontal input. On its first positive
velocity, source can select event 7/A in both descending setup and the final
transition; this duplicate setter order is preserved.

Descending setup runs only when AA is zero, sets AA=1, and selects acceleration
0016/event A for A2=1, otherwise 001E/event7. Landing is attempted only for
positive velocity. A successful landing or interruption returns immediately
without overwriting the callback installed by that shared service. Ordinary
frame advancement uses presentation step 1 only on the source advance paths.

## Field ownership, aliases and physical units

| Source actor | Native actor | Role in this graph |
|---|---|---|
| `32/34` | `42/44` | signed horizontal/vertical velocity |
| `36/38` | `46/48` | signed horizontal/vertical acceleration |
| `1E` | `2C` | held input |
| `5A` | `6E` | state byte |
| `8A/8C` | `A0/A2` | horizontal parameter / descending mode |
| `90` | `A6` | existing aerial-use flag |
| `92` | `A8` | packed held latch and relaunch count |
| `94` | `AA` | descending-initialized flag |

These are callback-owned aliases, not globally exclusive new fields. The
source `+90` test at `7688CA` matches native `+A6` at `083578BC`. The existing
class-5 jump producer proves source `+92` maps to native `+A8`; source `+94`
writer at `78557B` matches existing 02BD native `08357EDC..EE0` writing `+AA`.
Source action entry `76698D..999` overwrites `+92/+94` from action descriptor
`+1C/+1E`; native `08355674..680` overwrites `+A8/+AA` from its translated
descriptor `+1A/+1C`. That same native entry has already assigned the new
callback at `08355608`. Attack follow-up `0836AE14` interprets AA as its own
variant index, demonstrating why field adjacency alone would be insufficient.

The global actor dispatcher `083525B8..C8` invokes one current callback.
INIT unconditionally resets stale A8 (the baseline actually contains 0019).
Each relaunch resets AA; descending initializes AA once. The ordinary landing
and attack services preserve their existing ownership transitions. This is
the source lifetime translated onto the already shared actor fields, with
no extra RAM allocation or asynchronous owner. It is not a global writer census.

`tools/check_id13_air_lifetime_units.py` pins ten exact source/native anchors.
Its report `build/id13-air-relaunch-v79-20261117/lifetime-units.json` is
`85B3B804CF5542A927B54CAA46F5B4F81E3C63A5A4EE87B85E3C0B6B97380437`.
Source `742309..312` and native `083527A4..BC` add signed halfword acceleration
to velocity. Source `742325` / native `083527D8` shifts vertical velocity right
arithmetically by four before accumulating the movement delta. The separate
screen projection shifts the 1/16-pixel world position by four again. Velocity
therefore uses 1/256-pixel per-update units; FD80 is -640 in those units.
It is not -640 pixels, nor a value to multiply speculatively by 1.25.

Ordinary commercial jump tuning is documented separately in the Iraira record.
The retained special-aerial family instead preserves source literal gravity2,
velocity64, duration126 and horizontal128 at `08357A44/7A58/7DF4/7F00`.
This graph uses that demonstrated special-family per-update convention for
F0, FD80, 18, 16 and 1E. No 75/60 Hz wall-clock, trajectory, or audible parity
claim follows from this bounded translation.

## Helper ABI and resource availability

| Source helper | Retained native target |
|---|---|
| `668E:06E5` horizontal | `0835604C` |
| `668E:03C3` landing | `08355B54` |
| `668E:02BA` attack | `08355998` |
| `668E:0398` other interruption | `08355B04` |
| `4FFF:24CB` event setter | `08012874` |
| `4FFF:2862` frame advance | `08012A84` |

Callbacks use r4=actor and r5=presentation, save one LR, and return with the
same stack. INIT enters READY after READY's push so its fall-through has one
saved LR. Event and advance calls preserve the engine's stacked presentation,
r11 and argument layout. Landing/attack/other return nonzero to stop processing.
The base ID13 P1 selected through canonical group `084A80F8` is `086156B4`.
Its events 7, A, 26, 27 and 72 exist and contain bounded command arrays; event72
has 17 commands at `0861816C`. The evolved P1 group is a different resource
owner and must not be substituted for the base ID13 presentation.

## ROM allocation and verification scope

The existing audio reservation is raw `D33000..D40000`. Pinned preceding audio
manifest `build/repro-v78-20261116-a/evolution-music.json` is
`AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91`.
The preceding tables manifest `build/evolution-transition-tables-20261116/component.json`
is `4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6`.
Audio ends at D3EA01, tables occupy D3F000..D3F05A, and the latter explicitly
owns the remaining blank tail D3F05A..D40000. Every earlier declared write is
verified before allocating D3F100..D3FA00. A pinned conservative whole-ROM
encoded-pointer/ARM/Thumb/literal/ADR scan reports no inbound reference into
this new suballocation. Blank bytes alone are not treated as ownership proof.

The builder reconstructs the entire C91 input by reversing only its declared
writes. Author actual-ARM checks cover 720 selectors across all 15 identities
and all NZCV combinations, balanced stacks, three relaunches and fourth-press
rejection, packed-byte wrap/release, enhanced 02BD assignment, and actual event
availability. Horizontal helper executes actual existing native instructions;
landing/attack/other/event/advance are explicit service boundaries in those
tests. Independent verification is separately authored in
`tools/verify_id13_air_relaunch.py`; its final report and runtime outcomes are
recorded separately, rather than inferred from these author checks.

Independent offline review now passes for the frozen FBD9 component. See
`records/id13-air-relaunch-independent-v79-20261117.md` and
`build/id13-air-relaunch-independent-v79-20261117/audit.json`: 927 state cases,
3,252 outer-gate/identity cases, an 11-update sequence, exact write ownership,
whole-image inverse and targeted semantic mutation rejection. Its explicit
shared-service models do not replace the pending runtime landing observation.

The planned runtime discriminator is ordinary input into one eligible fall
gate, automatic INIT, three release/press cycles in READY, SPENT, and an actual
successful shared landing followed by ordinary actor dispatch and the next
frame boundary. Fourth-press rejection is an actual-ARM test here; the parent
runtime probe does not send that fourth press. No forced callback, RAM edit,
Calumon chase, or repeat of completed
music/evolution/Shoot suites is required. Other two native gates and the
Iraira route have static caller proof; this does not claim each has been
individually observed in the new emulator probe.
