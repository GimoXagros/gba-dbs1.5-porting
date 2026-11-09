# Independent combined stage11 development probe QA — 2026-11-09

PASS for separate component
`6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331`
over presentation-fixed84D predecessor. This combines the independently
approved stage11 score-HUD skip with one nonfatal-hit caller branch into the
already resident adapter. It does not modify main or prove a real emulator
positive hit, complete Shoot lifetime, E5 resolution or release readiness.
The reviewer started no emulator, loaded no state and edited no author file.

The verifier imports only frozen independent ARM/scanner/HUD-proof primitives,
never the new production builder. The previously unexecuted nonfatal draft
was renamed and completed as `verify_shoot_stage11_runtime_probe.py`.

## Exact composition and ownership

Over84D, only HUD373ED8(4B), HUD6FF400(16B), and nonfatal36E634(4B) change.
The last replaces retail `LDR r8,[pc,#5C]` with nonlinking `B 085CD9A0`.
The resident156-byte adapter remains byte-exact. There are24 declared and23
changed bytes; reversing those three spans recovers the complete84D ROM.

The independent verifier also reverses the five presentation words back to
D0, independently validates the approved D0→C8 HUD delta, and constructs all
six orders of presentation/HUD/nonfatal application from D0. Every complete
8MiB result equals the final component. All declared spans are disjoint;
the composite has44 declared/28 changed bytes from D0. No new nonfatal code,
cave, task or private RAM is allocated.

The frozen independent HUD ownership routine performs a fresh strict scan
against84D, not just D0: all byte-alignment mirrored pointers, ARM and Thumb
inbound encodings, with zero exemptions. Full1394-interval/70-layer ownership,
original4MiB, v73 IRQ/fatal hooks/reservations and the full entry128-byte
reservation including its erased tail remain disjoint from6FF400..410.

## Newly connected native behavior

Actual source76023A splits positive-HP stage11 from the legacy palette path;
source76027B installs timer8 and760287 tests flash-mask4030. The adapter
retains those mapped operations. Its native stage read adds one deliberate
read on non11 paths. All255 non11 stage bytes ×16 incoming NZCV combinations,
4,080 cases, execute the real native palette loader and lower refresh to
3730FC. Registers, complete CPSR, ordered writes and calls match the original;
the read sequence differs only by that one stage byte. Actual3730F8 CMP kills
the adapter's stage-CMP flags before a condition consumes them.

Eighty stage11 mask/NZCV cases execute the actual36E348 six-word collision
save, new adapter, real080132EC palette loader and a bounded default-kind0
common return. Loader arguments occupy20 balanced bytes. Actual palette
copies are15 halfwords at05000222..23E; timer+74 becomes8; flash4030 clear
adds24 red color-zero writes. Blocked masks suppress those24 writes.
The existing collision POP/BX restores saved r1-r5/LR and SP. No palette,
task or callback service is modeled. This synthetic return fixture explicitly
uses the no-freeze branch of the unchanged common tail; the earlier frozen
fatal-route shared-tail flag proof is reused for its bounded remaining owners.
The unrelated pre-hit visual/audio constructor graph36E34C..36E5C8 is not
executed or claimed as new evidence here.

Six actual HP-prefix cases cover positive/fatal and evolved half-damage
boundaries. Only positive post-hit HP reaches36E634; fatal handling remains
unchanged. Twenty timer/threshold/mask cases execute eight successive eligible
586C6C..94 update fragments and the actual587000 expiry and586E00 restoration.
Expiry occurs once at zero and cannot repeat on another zero-timer update.
Low/middle/high HP threshold palettes are read by the real P2 loader. The
unblocked expiry restores16 BG color-zero entries; it does not claim to
restore all24 flash entries, including transparent OBJ zeros. This verifier
executes the actual3700F4→586B00 dispatch to the main-loop entry, and the
timer fragment/expiry instructions. The author's broader full-wrapper tests
are separate evidence; these fragments are not relabeled as whole-frame runs.

The ARM runner extends its frozen implementation only for checked immediate
post-index unsigned-halfword transfers already present in these retained
loader/flash/restoration bodies. Zero BIOS or other imported service models
are installed. No unchanged prior full suite is rerun.

## Positive-HP actual-capture fixture

The genuine healthy replay's separate game-RAM/palette captures are inputs:

| Capture | SHA-256 |
| --- | --- |
| `13-healthy-activation-ewram.bin` | `65D380F9ED988253D931269E944C94786B4428EA12F9E9940666A982F70E1DA6` |
| `13-healthy-activation-iwram.bin` | `9FC46E5351D0FEBB822C18591855E6B2BFE2FCDCC8077FB0EBCA6524B9C4E978` |
| `13-healthy-activation-palette.bin` | `56BF85590EAC946AE51E6F0A978089CB504A5E600C00218BBE08FE60D8490F68` |

Actual FIRST02011710 has HP4; SECOND02011828 has HP37 and initialized Shoot
P1/P0 resources085D0000/085D1000; auxiliary02011940 is kind6 with resources
085D029C/085D1100. The sparse readonly fixture supplies this actual memory.
It binds the ordinary collision actor registers, executes the real collision
save, and supplies an isolated scratch damage input1. Actual HP instructions
produce37→36, the new adapter installs the real flash palette and timer8, and
only the expected HP/palette/timer effects occur outside the stack. Player HP4,
actor callbacks and actual input/battle controller callbacks remain unchanged.
At the explicit shared-tail36E438 boundary, eight real timer-fragment calls
then yield one actual expiry call and the correct high-HP palette restoration.

This is an isolated actual-ARM positive-hit fixture derived from real healthy
memory, not a claim that a controller attack hit in an emulator. It does not
depend on the previous HP1 lethal shortcut. Real gameplay reachability of
the nonfatal path, palette lifetime and controller health remain separate
root-owned hidden-run/capture gates. No Core compatibility exception is used
to weaken these exact game-RAM input pins.

Ten controls reject a linked hook, wrong target, off-target word, changed
resident adapter, unbalanced palette arguments, wrong flash timer/destination,
lost lower-CMP flags, early timer expiry and wrong HP-threshold palette.
Behavioral controls execute before output-hash rejection.

| Frozen artifact | SHA-256 |
| --- | --- |
| `tools/verify_shoot_stage11_runtime_probe.py` | `259061E232A4B3C2462112711B48196EEFF736194C35E904EB1803E5B3B885E7` |
| `build/shoot-stage11-runtime-probe-qa-20261109/report.json` | `CDD10F8D2943DA5DCFDD1BDD558956439D19BB38A8EDE197FD2F3FBC7A051C6C` |
| Source builder | `1C6CF23798A362A6ABE0B6D5B37C9B61F849FAE524B4F3D4D85C90FC7475BAE0` |
| Component manifest | `75F2CE1EEB3CB038A52FA95E74D696EC2084CDF45748CC290A2910C7DA65DB8C` |

Reproduce from repository root with a fresh report path:

~~~powershell
python -u -X utf8 tools/verify_shoot_stage11_runtime_probe.py build/shoot-stage11-runtime-probe-20261109/component.gba build/shoot-presentation-target-lifetime-20261109/component.gba 'C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba' 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --capture build/bizhawk-gba-shoot-entry-replay-20261109-a --manifest build/shoot-stage11-runtime-probe-20261109/component.json --output build/shoot-stage11-runtime-probe-qa-20261109/new-report.json
~~~
