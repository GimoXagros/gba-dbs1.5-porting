# Changed ordinary-input Shoot campaign probe

This is a new, unlaunched probe variant. It changes two concrete input decisions from the previous k/l collector campaign: select the shortest legal round timer in Options, and retain attacks during the HP-based stage7 boss instead of pursuing score orbs. It does not force a stage, change game memory, load a state, or establish that Shoot has been reached.

The real Options timer is row0. Its task constructor at `77609F..7760B7` selects callback7564:12C3 and row index0. The handler `776994..7769C8` changes SRAM005E between0 and2 with Left/Right. Ordinary battle initialization `740C62..740C88` maps the three values to6750,9000 and13500 updates (90/120/180 seconds at75Hz). There is no30/60-second choice. Prior i/j/k/l `options-hard-sram.bin` captures all have difficulty3 and timer selector1; selecting0 therefore saves2250 updates per ordinary timed round.

Stage7 overrides the timer to18000 updates at `740CA1`, irrespective of Options. Its upper HP must reach zero for battle `7417E6..7417F3` to invoke rootcase5. Timer expiration instead invokes rootcase0 at `7417FE..74180F`. Accordingly the new wrapper excludes stage7 from the existing collector's orb diversion. The original attack/chase inputs then remain active. This does not claim that the inherited bot can defeat the boss.

`tools/bizhawk_probe_wsc_shoot_short_hard.lua` reads and expands the frozen collector and observer in memory. It requires exactly one match for each replacement and never rewrites either file. Existing calibration, storage observations, owner hooks, terminal captures, final key release, output flush and completion marker remain. Additional telemetry every300 frames records stage, mode, timer selector/count, both HP values and both scores. The shortest-timer and difficulty3 conditions are asserted before any battle inputs.

Early stopping requires all three: at least300 observed Shoot frames, at least one row-clear live-in hit while stage11 is active, and a positive final-IRQ observation while stage11 is active. It then performs the final release through the captured original joypad.set (bypassing the collector), followed by the existing snapshot/calibration checks and writes `done.txt`. This is a bounded observation target, not a claim that the entire terminal transition completed. Reaching the configured frame limit also finishes through those checks; the log's presence or absence of `short_hard early-stop` distinguishes the two outcomes. Root alone owns launch and wall-clock termination.

## Launcher contract

Use the existing isolated fresh-boot launcher and invisible configuration. All paths below are in its existing W: workspace mapping. No provided save is used.

```
--gdi
--config=W:/build/NEW/config.json
--lua=W:/tools/bizhawk_probe_wsc_shoot_short_hard.lua
--userdata=output:W:/build/NEW;frames:120000;callback_order:bizhawk2111-rew
W:/build/NEW/probe.wsc
```

`output` is a new directory matching `W:/build/[%w%-%_/]+`; `frames` is the relative update budget, and `callback_order` must be the exact2.11.1 contract string. The ROM must be originalC415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7. Hash-check all three scripts before launch:

| Script | SHA256 |
|---|---|
| short_hard wrapper | E382D2D1462B7507090483548FD12DBC97A0342BA0C90D617268D6460A63ABD0 |
| frozen hard_v2 | 0CC9B17CAE00E7B7EFA33976788B1A66F595F15473EE78A597A77ADF68F42D69 |
| frozen collect_v2 | 2AD5BB33BB5FA85A654E5A36ECDF002195076CC85FB62C4E7A7033797BA37A17 |

## Mock verification

`tools/verify_wsc_shoot_short_hard.py SOURCE.wsc --output FRESH.json` checks the source menu/timer/boss contracts and executes the actual wrapper plus both frozen dependencies in Lua54 with mocked read-only game APIs. Sixteen cases cover all three initial timer values and four initial difficulties, plus bounded boss, ordinary-orb, no-Shoot-clear and no-Shoot-IRQ runs. The successful cases emit exactly one actual Shoot clear; simulated pre-Shoot clear/IRQ hits cannot satisfy completion. They check legal UI completion, retained ordinary orb collection, active boss attacks despite a present orb, telemetry, retained terminal hooks, early/bounded completion and final key release. Five mutations reject wrong timer direction, renewed boss orb suppression, premature completion, collector-overridden final release and an erroneous repeated-clear requirement.

The self-check report is `build/shoot-short-hard-20261106/mock-b.json`, SHA256 `A13034C95FA2586A2274DD15DBD7C269AE7F9F2B9E3D6DAFB45F3886BCD2597C`. Verifier SHA256 is `2479D74DFA73F84E85EBECE0F047171F7401E9448B254DAE1D223EEC7AF3DE83`. `terminal_path` independently reviews this observer before root launch. No emulator/core was launched by the author or the mock verifier.

Final independent review passed the E382 wrapper and2479 verifier. Its fresh `build/shoot-short-hard-qa-20261106/mock-independent.json` is byte-identical to A13034C9. The review's single-clear and collector-overridden-release findings are both closed with regression cases. Root owns the subsequent fresh run; this preparation record makes no runtime result claim.
