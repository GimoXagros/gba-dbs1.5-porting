# Original Shoot boundary observer and checkpoint

The new baseline uses the frozen approved stage7 HP1 driver and unchanged
input policy. `tools/bizhawk_probe_wsc_shoot_boundary.lua` intercepts the
existing score-module load only after the full authorized-copy startup guard,
then loads `tools/bizhawk_observe_wsc_shoot_boundary.lua`. Its joypad proxy
records the final submitted table without modifying it. Its frame proxy calls
the real frame advance before the observer. Finalization occurs before the
frozen completion marker. No new userdata options or guest writes are added.

The helper exports `tick()`, `after_frame({relative,core_before,keys})`, and
`finish()`. Seven fixed execution hooks use the already calibrated BizHawk
2.11.1 managed R,W,E passed to native R,E,W mapping and independently check physical address
and PS:PC after opcode fetch. Four byte spans match original C415 exactly:

- 747A68 initializer entry latches a checkpoint request; it never saves inside
  an execution callback.
- 77345F observes the activation flag before change; 77348F observes the two
  installed input/post callbacks after the actual calls. The latter requires
  active bit4 and owned task callbacks4090:07FA and4090:0D0B. Instruction-time
  RAM/SRAM and event frame are separate from outer-frame visual captures.
- 743987/74398A bracket the actual P1 `SUB [SI+50],AX` in4090:3030. Require
  stage11/gamekind2, typed FIRST, DS0=0C00/DS1=1000, positive HP/damage, the
  same PS/SI/SP/DS/ES/AX and PC+3, then exact HP subtraction. Victim+16 is
  labeled candidate damage-owner context, not assumed current attacker.
  The boss-kind3 subtraction760185 is not mislabeled as the P1 loss writer.
- 766ABF/766AC8 bracket accepted jump callback stores668E:16E8, with FIRST,
  edge40 and matching instruction stream. At most eight acceptances are
  logged; acceptance alone is not a claim of later physical takeoff.

After the first safe frame following initializer entry, checkpoint capture
requires stage11, typed FIRST, activation bit4 clear, and no activation hook
already observed. `savestate.save(path,true)` runs only outside callbacks.
Require true, a fresh nonempty ZIP file, unchanged frame/RAM/SRAM, and save
paired 64KiB RAM and32KiB SRAM plus a screenshot. The record distinguishes
initializer hook frame, captured core frame, next relative input index and
the last consumed key table. Two fixed native-write observers then watch the
initial FIRST HP bytes, at most64 events. Their backing reads are neutrally
labeled at-callback values; no callback timing assumption establishes a
completed word write. An unmatched outer-frame HP decrease is explicitly
unpaired, with no guessed instruction owner.

Every final key table after the checkpoint through stage11 exit is recorded
with before/after core and relative frame, capped at3000 lines with an explicit
truncation marker. The first active frame and first loss frame each add one
outer-frame screenshot and paired RAM/SRAM, explicitly distinguished from
their instruction hook times. There is no checkpoint load in this driver.

The exact official tag2.11.1 SaveStateLuaLibrary rejects state operations in
input/memory callbacks. SaveStateApi can suppress an underlying API exception,
so its Boolean alone is insufficient; actual file existence is also checked.
SavestateFile is a full ZIP container including native and managed core state.
It may restore the userdata bag; future resume must rebind output, budget and
approval fields. Lua closures, policy locals and installed callbacks are not
serialized. The recorded input stream permits a separate replay-equivalence
check before a changed controller trial. Independent QA owns deeper container
and native-state equivalence validation; a mock ZIP is not such evidence.

Official sources were archived under `build/wsc-shoot-boundary-20261109`:
[SaveStateLuaLibrary](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.Common/lua/CommonLibs/SaveStateLuaLibrary.cs),
[SaveStateApi](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.Common/Api/Classes/SaveStateApi.cs),
[SavestateFile](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.Common/savestates/SavestateFile.cs),
[WonderSwan state](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Emulation.Cores/Consoles/WonderSwan/WonderSwan.IStatable.cs).

Frozen SHA256:

- Helper: `CEC38BBF31562C0741D9707452F653AB1B4C0FABDCC457AF6B7D9C33D5E61B9A`.
- Thin driver: `9B2D848EA7731B24EEC0A3212961469E93528B236369E63DD17EC1E50B8C27FA`.

The minimal author selfcheck in
`build/wsc-shoot-boundary-20261109/selfcheck.py` passed actual Lua54 execution:
all four original byte pins, seven fixed hooks, deferred single checkpoint,
activation and paired loss/jump, two safe-frame images, exact final keys,
stage exit and finish. Wrapper syntax also passed. Independent QA separately
tests actual composition and refusal cases. No emulator was launched by this
authoring/checking work, no save was accessed, and no actual Shoot success,
terminal DI or final-port completion is claimed here.
