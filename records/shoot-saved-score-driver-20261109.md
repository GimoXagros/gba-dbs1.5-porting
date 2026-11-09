# Authorized score observation driver

`tools/bizhawk_probe_wsc_saved_score999.lua` is a thin original-WSC development
driver. It composes the separately reviewed DI observer and permitted P1
D Spirit999 module with the frozen v4 ordinary input policy. It introduces
no input strategy, stage transition, HP/register change, ROM edit or save-file
write. The score module alone owns the explicitly permitted guest score write.
The root launcher owns the authorized copy, hidden core, hashes and run budget.

Before loading either module or sending input, the driver compares all32768
live SRAM bytes with `authorized-cartridge-copy.bin`, substituting only the
exact startup values004E=01 and0073=00. Length and domain sizes are checked.
Initial SRAM/iEEPROM evidence is retained if this check fails. No byte mask or
additional normalization is allowed. Required userdata are `output`,
`callback_order="bizhawk2111-rew"`, exact original `source_sha256`, approved
copy `save_copy_sha256`, and integer `frames` in1..180000.

The five frozen policy dependencies are loaded without modifying their files:
v4 `70B73AB3`, v2 `85D7F25E`, short-hard parent `E382D2D1`, collector
`2AD5BB33`, and lifetime observer `0CC9B17C`. An `io.open` proxy makes only
the following in-memory composition changes:

- Remove the collector's seven old owner hooks, including its incorrect
  `diA` modulo65536 sample. DI v3 owns consumed-operand evidence. Older hard
  observer register logs remain contextual observations.
- Replace the hard observer's false no-save/no-write provenance with the
  authorized copy and score-only cheat declaration.
- Add actual DI paired-read/terminal readiness to the existing positive
  row-clear/IRQ/300-Shoot-frame early-stop condition.
- Capture RAM/SRAM/PNG once per newly seen stage, at most12 stages. Ordinary
  stages wait until the observed P1 score is999; stage7/11 do not require that
  score because the score module excludes them. Existing stage traces remain.
- Rename the base completion marker. Both modules must finish before the new
  `done.txt` is written as either `shoot-di-observed` or
  `bounded-observation-complete`. A bounded run without Shoot is not success.

`score.tick()` installs its single guarded source hook before the existing
loop starts. Its callback subsequently owns score enforcement; the driver
does not write score each frame. Existing Options, title, character choice,
ordinary battle, stage-seven boss input and final input release are retained.
The score cheat does not guarantee the unchanged boss policy will succeed.

Author validation `tools/verify_wsc_saved_score_driver.py` executes the actual
driver and all five frozen Lua policy files with the reused Lua54 harness.
Only DI/score interfaces are doubled; their actual implementations have
separate module QA. Synthetic startup data avoids reading any supplied save.
Nineteen routes pass, including all12 timer/difficulty starts, four existing
bounded failure routes, missing-DI bounded completion, and two fail-closed
startup mismatches. Six code mutations reject skipped save equality, restored
legacy hooks, absent DI completion gating, false reached markers, missing score
installation and missing score finalization. Stage captures and original input
release are checked. No emulator is launched by this validation.

Driver SHA256:
`A0ACBDA61D4CC5629637E385E5F8697C7FA4B682AE6D35505C28B83A0ABA287E`.
Author validator SHA256:
`8FADAB7D6A4830EAF102EF3835DB7F483DE712F002B930E181A4C778AD3D7919`.
Report: `build/wsc-saved-score-driver-20261109/author-qa-v2.json`.
Actual source gameplay/terminal results belong to the subsequent root-owned
run, not these mocked composition checks. Frozen files and saves are unchanged.
