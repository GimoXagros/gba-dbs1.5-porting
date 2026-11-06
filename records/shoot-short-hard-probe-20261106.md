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

## Independent audit of the deliberately stopped run

The preceding unlaunched description is preparation history. Original-source capture `build/bizhawk-wsc-short-hard-20261106-a` was subsequently launched by root and deliberately stopped after repeated stage1 losses. It is **partial**, with no `done.txt`, no final snapshot, no completed summary and no execution of the observer's end-of-run calibration assertions. Its last logged input is relative77148/core77149; that is the last logged update, not a claim that process termination occurred on exactly that update.

The final launch SHA256 is `4E243BABFF0E66AFC3B15580B750C5A1E4DB811DCF60E756B13DF513345837A7`. Independent audit `build/shoot-short-hard-capture-qa-20261106/audit.json` is **F85A85F37E82F64D2A22F28A81AA6EA4FA3D7D2C1D6E2E79A7328D940E3DD1F0**; its rerunnable audit script is beside it. All26 launch-inventoried files match their hashes, and the launch itself makes27 hashed files. A recursive file inventory confirms that there are no additional files hidden in the isolated data directories. Full8MB `loaded-rom.bin` and `probe.wsc` are byte-identical to the original C415 source ROM. The actual executable and all three frozen scripts match launch pins. Configuration paths are isolated to this run; background input, auto-loads and automatic save-RAM persistence are disabled. The reviewer launched no emulator, read no save-file contents and wrote no guest state or ROM. Captured SRAM-domain `.bin` snapshots are evidence, not provided save files.

Natural UI events are positive: difficulty3 at relative4381, timer selector0 at4501, and verified battle entry at5387. The complete captured fields independently show Options difficulty1/timer1 initially, difficulty3/timer1 after the difficulty inputs, and difficulty3/timer0 on row0 after the timer input. The first battle snapshot is stage8/mode7 with timer6750, corresponding to90 seconds at the source75Hz rate. **The immediate `options-short-hard.png` still visibly shows120**, because snapshot4501 precedes the menu repaint. The RAM selector0 and battle6750 establish the90-second selection; this capture does not establish visible90 text in that Options screenshot.

The4791-line trace contains131 state samples,240 added telemetry samples and240 actor samples. Only stages0,8 and1 are logged. Stage8 reaches mode8 result samples at12600/12900 with P1 score15 versus P2 score9; progress becomes0100 and stage1 begins at13099. This positively establishes the stage8 win and subsequent progression.

Stage1 then has seven sampled completed losing rounds:

| First mode8 result sample | P1 score | P2 score |
|---:|---:|---:|
| 20700 | 4 | 8 |
| 28800 | 9 | 15 |
| 36900 | 6 | 9 |
| 45300 | 4 | 15 |
| 53400 | 3 | 23 |
| 61500 | 6 | 19 |
| 69900 | 6 | 11 |

The sampled movement supports a policy stall, not an emulator hang. At18600 and18900 P1 remains `02E0,1100` with left held (`0008`), while P2 is at X0060 and much smaller Y. At34800/35100/35400 P1 remains `009C,0E80` while P2 Y changes `06FE→0467→02F0`; both scores stay6/9. These are equal-position samples spanning300 and600 updates, respectively, not proof of continuous immobility between samples. Later frames and inputs continue. At77100 the next stage1 battle is still mode7, timer570, HP8/8 and score2/16. The last state sample is76800 with progress0400 and zero recorded watched accesses.

No stage11/Shoot state, Shoot entry capture, row-clear completion, early-stop line or final IRQ/lifetime completion is recorded. This run does not establish Shoot reachability or absence of future watched accesses. No campaign completion, terminal lifetime closure, emulator defect or guest-state repair is inferred from the stalled input policy. The proposed replacement input policy is separate work.
