# Separate combined Shoot development probe

This isolated component starts with approved presentation-receiver repair84D,
adds the exact independently reviewed C8 HUD delta, and connects the existing
normal-hit adapter with one four-byte branch. It does not alter main or any
prior component, running probe, checkpoint, or emulator state.

The HUD delta remains exactly raw373ED8 (4 bytes) plus6FF400 (16 bytes).
The builder proves that applying these bytes to84D equals applying the five
receiver-fix words toC8, and checks both inverse paths back through84D/C8 toD0.
It repeats the strict pointer/ARM/Thumb scanner on84D for the complete new
HUD cave16-byte range. The1394-interval/70-layer ownership ledger, IRQ
reservations, fatal hook, and full128-byte entry reservation are pinned and
retained. There are no inbound references or instruction-interior exemptions.

The only subsequent change is raw36E634:
`5C809FE5` becomes `D97C09EA`, branching to resident085CD9A0. Its156-byte
body stays unchanged. Damage halving, signed subtraction, HP store, positive
branch and the existing fatal callback route all remain unchanged. Non11
executes the displaced palette load and returns to0836E638. Stage11 loads
Shoot P2 at085C0B00, sets victim+74 to8, and performs the conditional flash
before rejoining the common attacker tail at0836E438. No new nonfatal code,
RAM, task, callback store, or lifetime owner is introduced.

Checks use the actual healthy activation RAM from the completed84D replay:
FIRST02011710 HP4, SECOND02011828 HP37 with resources085D0000/085D1000,
and linked auxiliary02011940 with resources085D029C/085D1100. Finite fixture
changes are confined to the offline checks; no runtime state is forced.

The author checks cover:

- 4,080 non11 stage-byte/NZCV joins with exact displaced-load registers.
- 48 linked non11 calls through real080132EC and the old lower callback's
  actual CMP at083730F8, proving the new stage comparison's flags are dead.
- 128 stage11 cases through the real palette loader, verifying fifteen
  OBJ1 palette colors, the exact twenty-four conditional color-zero writes,
  timer8, preserved actor registers, and balanced stack arguments.
- 48 actual damage-prefix boundary cases, retaining evolved-damage and
  positive/lethal decisions, and one collision entry-save/HP-suffix/return
  frame check in the typed default-fighter no-freeze context.
- 384 actual wrapper updates: six HP-threshold cases, eight flag masks,
  and eight calls each through3700F0 ->586B00 ->586C00. At expiry587000
  loads the correct threshold palette and586E00 restores sixteen BG-zero
  entries when permitted. The eight transparent OBJ-zero entries are not
  rewritten by expiry. These are eligible loop updates, not guaranteed
  video-frame counts.

All executed imports use their actual ARM bodies; no BIOS or other service
model is used. The interpreter adds only immediate post-index halfword
transfers needed by the retained palette loader and loops. The collision
frame test executes the actual entry PUSH and the damage suffix through POP
and return; its unrelated hit-effect/audio construction prefix is explicitly
outside that check. Existing per-bit shared-tail flag proof is reused.

The final component has23 changed bytes within24 declared bytes relative
to84D. Exact ExpectedWrites and whole-ROM inverses reject eight off-target
or corrupted-write controls. This author result does not establish an actual
positive hit, completed ending, or absence/cause of historical E5. Independent
QA and gameplay checks remain separate gates.

Frozen artifacts:

- Builder `tools/build_shoot_stage11_runtime_probe.py`, SHA256
  `1C6CF23798A362A6ABE0B6D5B37C9B61F849FAE524B4F3D4D85C90FC7475BAE0`.
- HUD intermediate `build/shoot-stage11-runtime-probe-20261109/hud-intermediate.gba`,
  SHA256 `8AA1A58844C31681EAB9816D1131C072F89FE4DD5EFA6F001F5C0F641088279D`.
- Combined `build/shoot-stage11-runtime-probe-20261109/component.gba`, SHA256
  `6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331`.
- Manifest `build/shoot-stage11-runtime-probe-20261109/component.json`, SHA256
  `75F2CE1EEB3CB038A52FA95E74D696EC2084CDF45748CC290A2910C7DA65DB8C`.
