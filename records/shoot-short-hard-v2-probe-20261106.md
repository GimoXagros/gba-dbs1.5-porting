# Bounded ordinary-input wall recovery

This new wrapper addresses the captured stage1 chase trap without changing the frozen E382 observer or the completed partial run. The earlier run was stopped by root after repeated stage1 failures; this document makes no successful runtime recovery or Shoot-entry claim.

`tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua` loads E382 and intercepts only its read of the frozen collector source. Exact single anchors insert a host input policy after the collector chooses keys. All original files remain unchanged. Applying recovery last prevents the collector from replacing its finite detour; E382's final release still uses the captured original `joypad.set`, bypassing both policies.

Recovery requires180 consecutive eligible samples: battle mode7 outside Shoot stage11, valid P1/P2 handles, an opponent more than0300 fixed units above and more than0100 units away horizontally, and an actual held direction toward that opponent. X must stay within0020 units of the stationary anchor. Movement beyond that tolerance, missing/wrong direction or insufficient separation restarts the detector. Stage, player handle, target handle and frame discontinuities reset state; invalid handles and nonbattle/Shoot modes bypass and reset it.

On detection, the policy moves in the opposite horizontal direction for60 frames, suppresses attacks during that interval, and generates exactly one8-frame jump pulse at ages4 through11. It then resumes the inherited policy with360 frames of cooldown. Continued eligibility requires another180 samples before retrying. Inclusive sample counting makes the minimum start-to-start frame-index difference599; it does not omit a cooldown update.

`escape.txt` records start/end, stage, coordinates, away direction, remaining updates and cooldown. Only the first three starts in the entire run capture a PNG and64KiB RAM snapshot, named `escape-N-stage-S-frame-F`. These are observations, not guest writes. No terrain planner, synthesized coordinates, save state or emulator register change is used.

The90-second Options choice, difficulty3, stage7 attack path, score collector for ordinary rounds, HP/score telemetry, stage11-specific clear/IRQ completion and unconditional final release are inherited from E382. Early completion still requires one actual Shoot row clear, a Shoot IRQ and300 observed Shoot frames. The proposed detour is bounded; success in the real stage remains an observation to obtain, not a test assumption.

## Verification and launcher

The actual Lua wrapper chain passes22 mocked routes: the prior16 UI/completion/release cases plus left/right wall traps, a moving player, insufficient vertical separation, repeated cooldown recovery and final release during an active detour. The repeated-recovery case produces at least four starts and verifies the three-capture cap. Six mutations reject omission of the policy, immediate triggering, wrong direction, doubled duration, missing cooldown and collector-overridden final release. The mock runs Lua54 against read-only simulated APIs; it does not launch a game core.

| Artifact | SHA256 |
|---|---|
| v2 wrapper | 85D7F25E2C6A8AA4C24AFBCDB95A51E7F9A3414FA3E97635FCD7C9EC3436ADE4 |
| v2 mock verifier | 1FF0ABF8FCF259719DA7F57ADD82CE613761B36303BD49277F4375277BA0A667 |
| `build/shoot-short-hard-v2-20261106/mock-b.json` | 45FA597D64DC3EE25C8B6E5504E00F547BD7C0410D161748EDCB073A5B7DD4D8 |

Run the mock with `verify_wsc_shoot_short_hard_v2.py SOURCE.wsc --output FRESH.json`. It hash-checks the frozen2479 prior mock, E382 parent, 0CC9 hard observer and2AD5 collector. `terminal_path` independently reviews the final wrapper and state-boundary behavior before root launch.

Root's fresh isolated launcher uses the same configuration and userdata contract as the prior probe, changing only the Lua entry to `W:/tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua`. Hash-check all four Lua files and keep the original source ROMC415. Use a new output/config/save directory; do not resume or overwrite the earlier partial run. No launch was performed by this worker.

## Independent audit of the stopped v2 capture

Root subsequently launched `build/bizhawk-wsc-short-hard-v2-20261106-a` and requested a host stop after three stage1 losses. The final launch is **1AE169E8BCF7CEC8411FF74419140CDAC96F2AB43311581E9DBE9DB2931464BD**, with `completed=false`, `host_stop_requested=true`, `host_deadline_reached=false`, exact loaded ROM and unchanged scripts. `stop.request` is preserved. There is no observer `done.txt`, final snapshot, completed summary or final release/calibration-completion evidence. The last logged input is relative37710/core37711; process termination need not coincide with that exact update.

Independent report `build/shoot-short-hard-v2-capture-qa-20261106/audit.json` is **7897214D8666D62B8EBB7D00239E1A645CB78B994136E709619D632542372C5A**; its rerunnable script is beside it. It verifies all32 launch-inventoried files plus the launch itself, including both new escape RAM/PNG pairs and `escape.txt`. Full loaded/probe ROMs are byte-identical and hash to C415; executable, all four scripts and isolated/no-autoload configuration match the declared pins. No additional data-directory files are present.

The prior independent capture audit F85A85F3 is reused. All21 inherited snapshot files are byte-identical to that capture, and the first1033 trace lines also match exactly. Natural difficulty3, timer selector0 and6750-update/90-second battle entry are therefore retained. The Options boundary screenshot still shows120 before repaint, as documented in the prior audit. The first changed input is relative18585/core18586; no repeated mock/source or v70 tests were used here.

The new recovery evidence is precise about its two clocks: `escape.txt` uses absolute **core frames**, whereas trace relative frames equal core−1.

| Attempt | Core override interval, inclusive | Relative interval | Jump pulse | Logged P1 movement |
|---|---|---|---|---|
| 1 | 18586..18645 | 18585..18644 | core18590..18597 | `02E0,0FC8 → 0714,1100` |
| 2 | 19185..19244 | 19184..19243 | core19189..19196 | `02E0,1058 → 0698,1100` |

The frozen joypad trace confirms exactly60 consecutive right-away updates per attempt, no left/attack during either interval, and one8-update jump pulse at ages4..11. The next update resumes left. Both end rows report cooldown360; start-to-start separation is599 core frames, matching the bounded policy's inclusive counting. The capture therefore establishes delivery of the intended detours, not successful navigation.

The two64KiB start snapshots match their logged P1 and target coordinates at actor offsets D784 and D894. P1 raw word `+8C` is1 in both; the source meaning and jump-duration implications belong to the separate source analysis. No escape SRAM snapshot exists, so the initial battle handles are reused only after those actual coordinate matches. Both screenshots were visually inspected. Later telemetry has P1 back at `02E0,1100` with left held at relative18900 and19500. This supports return to the same trap after each back-away interval.

The2239-line trace has65 state samples,108 added telemetry samples and108 actor samples. Stage8 again wins15/9 and advances to stage1. Stage1 records three losing results: relative20700 at4/8,28800 at9/15 and36900 at6/9. Last telemetry at37500 is mode9, stage1, timer0, HP8/8, score6/9; the last state at37200 has progress0400 and watched-access count0. Only stages0,8 and1 occur in the logged states. No Shoot stage11, early-stop line, actual Shoot entry or terminal/storage lifetime completion is observed.

This is a successful evidence audit of an unsuccessful, deliberately shortened policy attempt. It does not establish a game/core defect, completed campaign or successful wall escape. The independent reviewer launched no emulator, read no save-file contents and wrote no guest state, main file or ROM. Revised input policy/source proof is separate work.
