# Shoot terminal scene, damage adapters and same-update repairs

This layer contains actual ARM callbacks and four active repairs to the existing
upper callbacks. The retail damage hooks and root scene dispatch remain unchanged.
It uses existing native object, task, palette, audio, presentation and mode owners.
No emulator, save file, new RAM owner or replacement engine was used.

## Frozen layer

- Builder: `tools/build_shoot_terminal.py`.
- Source/native proof: `tools/analyze_shoot_terminal.py`.
- Independent verifier: `tools/verify_shoot_terminal.py`; imports neither builder
  nor source analyzer and does not assemble or execute game instructions.
- Predecessor: `build/handshake-integrated-v3-20261013/handshake.gba`, SHA-256
  `F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF`.
- Output: `build/shoot-terminal-20261013/terminal.gba`, SHA-256
  `39936F49AB455032B4B71355C2C12127DC35D281670C2D72F48D4273F466CD0D`.
- Builder report: `build/shoot-terminal-20261013/build.json`, SHA-256
  `379A2B913306820CA5BD5E1325927CF55861C5FDC95EE8B660464CD6EFBE8D83`.
- Independent report: `build/shoot-terminal-20261013/verify.json`, SHA-256
  `4D6FE917B45ADF7E26E9F0E4FAE4EF938AF1AC84D91D06B63BC0798D06C466BF`.

There are 26 new blocks, 587 ARM instructions, 30 disjoint Expected Writes and
2,519 changed bytes. The occupied resident footprint ends at raw `5CDA84`.
Each actual block is guarded as FF in the exact predecessor. Byte-aligned pointer
and aligned ARM-like branch scans cover the predecessor. None reaches an actual
resident write. Candidate targets `5CDBA0`, `5CE1A0`, `5CE1E0`, `5CE210`,
`5CED34`, `5CED50`, `5CFB84`, `5CFE70` remain untouched. These are candidate
encodings, not proven data or proven control flow. The entire remaining gap is
preserved by the full-ROM diff check.

## Terminal source graph and native entries

Source logical addresses use scene base raw `771F00` for segment `71F0`.
The graph covers source `1750..1E22`. Its 17 callback assignment sites are decoded
and checked against the complete source population, including unused `18EE`.

| Source | Native | Effect |
| --- | --- | --- |
| 1750 | 085CD000 | Release existing object list, initialize countdown, set P1 HP1, clear common400, D2 sound, fall through to17DF |
| 17DF | 085CD0A0 | Countdown/blink; set Shoot80 and advance |
| 182F | 085CD120 | Center P1, select existing native jump if needed |
| 18EE | 085CD210 | Unreferenced source input phase retained for audit |
| 193B | 085CD270 | Wait for native player+6 bit4 |
| 197A | 085CD2B0 | Consume Shoot100, initialize existing transition scratch, bounded tilemap clear |
| 19F2 | 085CD340 | Consume second Shoot100, set common10, delay |
| 1A42 | 085CD3A0 | Set Shoot20/1000 and scroll owner1; begin palette phase |
| 1A95 | 085CD420 | 16 decrement steps over32 callbacks, BG3/4/5 colors2..9 |
| 1B15 | 085CD4B0 | Delay then Shoot200 |
| 1B55 | 085CD510 | Wait for stage-transition Shoot100 |
| 1B97 | 085CD550 | 16 increment steps over64 callbacks, same24colors |
| 1C17 | 085CD5E0 | Delay then Shoot2000 |
| 1C5C | 085CD640 | Construct existing result presentation and request34/type4 |
| 1D41 | 085CD6A0 | Update/draw until completion; initialize native final fade |
| 1DA0 | 085CD710 | Native final fade; fall through to1DC3 when complete |
| 1DC3 | 085CD740 | Existing native08340C54 cleanup, retirement and parent-mode handoff |

Resident helpers are result constructor `085CD760`, fade span `085CD840`,
bounded row clear `085CD920`, fatal adapter `085CD960`, nonfatal adapter
`085CD9A0`. Scene callbacks/helper calls preserve r0-r12/lr, set native ignored
segment argument r11 to0, and restore their callers. Flags are scratch.

Elapsed counters use the established commercial 75-to-60 conversion:
151→121, 75→60, 117→93. The 32/64 palette counters retain their source values
because those determine 16 color steps. The result P1 command word `FF64` and
the presentation's `150` field retain the exact retail values.

## Native consumer evidence

### Task and object lifetime

Source current task+10 maps to native `[0300133C]+18` through `0801201C`;
callback setter `08012008` writes the current task's first word.
Source scene timer+42 maps to native+50 through the earlier commercial countdown
proof. Object list/count use native `03004760`/`0300475E`; native `083524C4`
consumes stack ignored/object and marks/releases the existing native object.
Its transitive helper path preserves r6/r7 used by the release loop.

An important native exception is event `08012874`: it can call sound requester
`080D15C0`, which overwrites r6/r7. Source182F holds a current-task pointer across
this event. The implementation explicitly pushes/pops r6 around the call before
writing task+50; its negative case removes this preservation and must fail.

### Player jump

Source jump668E:1E51 at raw768731 has the same commercial ancestor at3ADBF7;
native entry is `08357670`. Source argument producer raw742DCA matches old392AE2
and native08354C24: FC43→FB54,10→14,0C→0F, field92→A8. The source jump-age
increment/saturation at74348F..4AB matches old393064..080 and native08352E1C..44;
the matching consumer source1EA3 uses30, native083576FC uses24. This supports
the terminal source age20→native16 on the same field and same increment cadence.
No virtual phase was introduced.

### Scroll and scratch ownership

Existing commercial source0300:EA scratch maps to native `03004710` through
two independent producer pairs documented in the stage-handshake layer.
Terminal197A initializes seven halfwords `(0154,008F,008F,0000,IN11,0048,0000)`.

Logical WS port11 must not be inferred from GBA BG numbering. Old source
390796..3907A0 reads auxiliary+BE and OUT10,AX; native080C97FC..080C9810 reads
auxiliary+E0/E1 and calls08000F2C/F44. F44 stores the logical byte at030012B9,
then subtracts8 only for hardware BG1VOFS. Terminal197A therefore reads030012B9.
The adjacent source ports12/13 map to nativeF5C/F74 instead.

The source clear uses live BX, shifts it six bits, adds0800 and clears64halfwords.
The candidate corresponding native camera snapshot is0300451E, paired with the
source input path's last BX. The helper maps Y0..62 to two native tilemaps
0600F000..0600FFFF and writes exactly64halfwords. Outside that domain it returns
without writing. **This guard does not prove the upstream range or close the
source live-in contract.** Normal gameplay restores full input/battle callbacks;
the original camera initializer's zero does not establish Y=0 at termination.

### Palette semantics

Source1A95 and1B97 modify source FE64/FE84/FEA4, eight colors each: native BG3/4/5
colors2..9. Native color channels in the source image are0 or odd3..31. Decrement
uses 3→0 and otherwise-2; increment uses0→3 and otherwise+2, clamped31. All32
native channel inputs reach exact terminal endpoints after16steps. The mask
touches24colors, not zero/backdrop entries or the adjacent palette rows.

The final common fade uses the existing paired native0833FDC0/0833FF00 services.
Native0833FDC0 can clobber r11; the terminal resets it before subsequent native
calls. The 1DA0 completion path assigns and calls1DC3 in the same update.

### Result resources and parent-mode handoff

Native P1 `08374824` reconstructs source3D8750 exactly, which also equals old
2B6150. The one command preserves its commercial `FF64` word and native padding.
Native P0 `08374854` reconstructs all44 layout records from source2DFF20 and all
41 tiles from source3BE1F0. Native P2 `08374E44` inversely reconstructs all16
RGB444 colors at source3D7400. The independent verifier reads the **resulting
candidate**, not only the untouched retail ROM, for these checks.

Constructor080127E4 consumes the same15stack arguments as native08340A94..AF0.
Event0, object flags2000, position70/48, field50=150 and native P2 loader follow
the existing result code. No extra P0 copy is invented: the retail native result
uses this existing presentation pipeline with the exact same resource pointers.

Source sound34's48-byte payload3F37AE..3F37DD equals old2D35C2..2D35F1.
The corresponding old request uses ID34/type4 and native08340B60..6C uses ID0B/type4.
Shoot's delay0 is retained; the ordinary retail result request used delay1.

Source1DC3 clears object counts, releases the presentation, retires its task and
sets existing mode words+4/+6/+8 to `(1,0,0)`. The matching full native function
`08340C54` is reused. This is an existing result/exit path. The source scene does
not add score, currency or unlock writes, and this layer invents none. The parent
mode's later behavior and the loss/time-out root dispatch remain route-owner work.

## Stage11 damage adapters and four same-update repairs

Source5EEA damage arithmetic at760177 has the same commercial prefix as old3A4757.
Native0836E5C8..5E8 reads damage, applies attacker4000 halving, subtracts targetHP64
and selects fatal versus nonfatal. The adapters leave those existing calculations
untouched and inspect the stage byte at03002310+E.

- Fatal adapter085CD960 gives stage11 active/link callbacks085BDD00/085BF204,
  then resumes shared native cleanup0836E604. Other stages resume0836E5F0 after
  reproducing the displaced `mov r0,r5`.
- Nonfatal adapter085CD9A0 loads existing Shoot P2variant3 at085C0B00, target
  flash timer74=8, and reproduces source red-zero flash only when Shoot4030 is
  clear. It writes native BG0..15 and OBJ0..7 zero entries, then resumes0836E438.
  Other stages reproduce the displaced **0834F836** palette literal and resume
 0836E638. An earlier draft value0834E832 was rejected by the literal proof.

Future hook sites36E5EC/36E634 and their exact before/after bytes are recorded in
the builder manifest. Neither is changed in this layer.

Four existing upper callbacks assigned their successor then returned, whereas
the WSC source falls into the successor during that same call. This layer replaces
only each final callback store with a branch to a tiny bridge:

| Source edge | Existing store | Bridge | Inherited saved frame |
| --- | --- | --- | --- |
| 7AB1→7B1B | 085BDD8C | 085CDA40 | r6,r7,lr |
| 7BFF→7C64 | 085BE69C | 085CDA50 | lr |
| 7C64→7CE5 | 085BEAB8 | 085CDA60 | lr |
| 7D8D→7DA9 | 085BF224 | 085CDA70 | none; bridge saveslr |

Each bridge reproduces the store, calls the existing successor, restores the
correct inherited frame and returns. Existing wait branches still reach their
original returns. All four original complete blocks and displaced stores are
guarded before mutation. Their existing motion/cadence implementation is otherwise
unchanged.

## Validation and remaining gates

Independent verification checks the complete reviewed block identities, ordered
native calls, every literal/use, all reachable instruction CFGs and stack joins,
constructor/event/P2/release consumers, exact write geometry and whole-ROM gaps.
Finite checks cover4096source colors, all32native channels, all65536flash flags,
256stage values,65536camera values and65536signed X positions. Nineteen semantic
negative cases run without relying on the complete-block hashes: wrong callees,
lost r6, wrong fields/stack/stage/stride/cadence/layer/literal, resource corruption,
missing order repair, undeclared writes and premature external damage hooks.

The following are still explicit route gates:

1. Source IRQ0DEC's interrupted-DI dependency. The new stage display's actual400
   effect path must not be connected through a guessed DI value.
2. Source197A BX ownership/range and its exact mapped row clear. The bounded
   resident helper alone does not establish the full domain.
3. Complete initializer/object lifetime, controller and scene prerequisites
   before either damage adapter or terminal1750 is selected by an external hook.

Static completion of this layer is not a runtime fidelity or playability claim.
