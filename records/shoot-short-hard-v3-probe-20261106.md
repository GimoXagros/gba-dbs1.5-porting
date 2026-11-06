# Minimum jump hold after the observed stage1 trap

The v2 capture demonstrates two finite back-away movements, not a successful escape. Starts18586 and19185 both begin at X02E0; their ends reach0714/0698 before the ordinary chase returns to the same obstruction. The first PNG shows the player beside the left obstruction below a higher row of blocks. No new campaign success is claimed.

The first immutable escape RAM snapshot has SHA256 `1C77C078F317FFA27FF9C72C7A7E9DEB85FCD7B6036FF1B0D9E8D3A0284CA909`. Actor0C00:1784 is default identity0, evolved flags8=C008, params4E=006E, callback668E:19D0, short-jump latch8C=1, X/Y02E0/0FC8. Its observed short branch is a concrete input-policy discriminator; it does not identify every earlier jump or establish terrain reachability.

Source jump edge40 at766AB6 selects event4 and callback668E:16E8. Initialization767FCC clears8C. During startup768001 checks held40 before observing animation completion: release sets8C=1 unless actor6:80 is set. Launch768068 initially loads short vectors from params+14/+16, and768079 replaces them with full +4/+6 only when8C is not1. Actual evolved params3B84CE contain full VY=-804/AY16 and short VY=-512/AY20. The short branch therefore has substantially less height.

Default base event4 at32E08C has FF01,FF03 durations; evolved event4 at3ACCFC has FF03,FF03. The source animation decrements through zero and sets the completion flag on its following update. With the event selected on input frame0, base completion is observed for launch atframe6 and evolved atframe8. Therefore an uninterrupted evolved startup requires nine held input samples, whereas the old eight-sample pulse releases exactly at that launch boundary. Hit interruption, pause and a later eligibility start can alter timing; widening a modulo window alone would not establish a minimum hold.

The new wrapper applies a final-key hold after both the collector and wall-recovery policies. Every requested A rising edge starts twelve consecutive held samples; B is suppressed during that bounded hold. A target or orb change does not cancel an ongoing hold. Mode, stage, player or frame discontinuity resets it; nonbattle, Shoot stage11 and invalid player handles cannot arm it. The inherited original final-release setter still bypasses both policies. The frozen90/8 chase,45/5 collector and60-frame recovery schedules remain intact underneath this final hold. No terrain planner, character change, guest writes, state loading or emulator launch was added.

Frozen implementation:

- `tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua`: `DA9F8E3F76EEEBF425E577C1FA8D4C5FB8B0FF50C929C67B02FE9EE760405905`.
- `tools/verify_wsc_shoot_short_hard_v3.py`: `4B7FE7CCD8CF734DE40F08F1C4E332D8885937A8C3AD75F1F26198BA2A270284`.
- `build/shoot-short-hard-v3-20261106/mock-a.json`: `1EE175FD19BC665A7E101F2B96E7DF13EAE9020B7870E6CAC8223967E1D03455`.

The verifier executes the actual Lua chain for22 inherited routes and14 hold scenarios, including a late-window one-sample request, changing target, bounded rearm, all reset classes and final release during escape. Nine source/host mutations are rejected, including eight-sample hold, wrong collector/recovery ordering, Shoot leakage and unbounded hold. This is preparation for a root-owned fresh ordinary-input test. It does not prove successful navigation, actual Shoot entry or terminal completion.

Launch uses the unchanged fresh isolated configuration and userdata schema, with only the Lua entry replaced by `W:/tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua`; hash-check v3 plus frozen v2, E382, hard and collector dependencies. Keep the existing120000-frame/1500-second bound, positive Shoot/clear/IRQ completion checks, at-most-three escape PNG/RAM captures and honest partial-stop handling. Root alone owns the launch after independent review.

Independent review passed: terminal reviewer reran the full chain with byte-identical report1EE175FD and separately executed487 actual-policy scenarios with6 negative controls (checker2EDC6F74/report62CE4CE4). It also reviewed launcherA2BA7353. See records/shoot-jump-hold-v3-qa-20261106.md. DA9F is frozen and ready for the root-owned bounded run; runtime success remains unclaimed.

## Independent audit of the stopped v3 capture

Root subsequently launched the frozen DA9F chain and requested a partial host stop. Capture `build/bizhawk-wsc-short-hard-v3-20261106-a` has final launch SHA256 **FBE417FE65BCF1CC979DCF07D27C4E84C99054BC75C9BEA124B5CB9ED2A6907E**. `completed=false`, host stop requested, no host deadline, exact loaded ROM and unchanged five-script chain are consistent with the captured inventory. `stop.request` is preserved; there is no observer `done.txt`, final snapshot, completed summary or final release/calibration-completion evidence.

Independent report `build/shoot-short-hard-v3-capture-qa-20261106/audit.json` is **AEF4BEA943F6C69040C7C19E3B76D3824FF33B8AF761FD51660743E875A6B42B**, with its rerunnable incremental audit script beside it. All27 launch-inventoried files plus the launch itself match their hashes; no extra data files are present. Full loaded/probe ROMs are byte-identical and hash to originalC415. Executable, five frozen scripts and isolated/no-autoload/no-background-input configuration were checked.

The prior capture audits are reused. Seventeen of21 inherited snapshot files match v2 exactly, including all Options, first hard battle and progress4600 captures. Natural difficulty3 and selector0/6750-update90-second entry remain established. The Options boundary screenshot still displays120 before repaint. The trace matches v2 for139 lines, then the first ordinary-combat A pulse changes from relative5580..5587 to5580..5591: release5588 becomes5592. Thus this run changes ordinary jump/combat input before any wall-recovery attempt; it is not a recovery-only comparison.

The actual final joypad trace has **341 closed A intervals of exactly12 updates**, with B absent throughout each interval. There are also81 four-update and one one-update intervals, including UI/boundary inputs; the audit does not reconstruct every unlogged mode boundary. These are final `joypad.set` command intervals rather than a hardware key-scan trace. There is no `escape.txt` or escape RAM/PNG capture in this run, so no actual wall-recovery start is evidenced.

The4096-line trace contains118 state samples,213 added telemetry samples and213 actor samples. Stage8 first loses6/25 at result12600, then wins18/10 at result21000 and advances to stage1 at21289. Stage1 has four completed losing results and one tie:

| First result sample | P1 | P2 | Classification |
|---:|---:|---:|---|
| 28800 | 7 | 16 | Loss |
| 36900 | 10 | 16 | Loss |
| 45300 | 7 | 7 | Tie |
| 52800 | 7 | 11 | Loss |
| 60900 | 9 | 11 | Loss |

Stage1's142 battle actor samples have137 distinct P1 X values, spanning0060..1B9F, rather than the previous repeated fixed-wall sample. This establishes varied sampled movement, not terrain reachability or successful campaign navigation. At the last logged state/telemetry, relative69000/core69001, stage1 is still mode7 with timer0, HP8/8 and score14/16; it is **not** classified as a completed sixth stage1 result. Progress is0400 and recorded watched accesses remain0 at that sample.

Only stages0,8 and1 are logged. No Shoot stage11, early-stop line, actual Shoot entry, terminal/IRQ/storage lifetime completion or120000-frame completion is established. This audit does not infer a source-game defect or approve another policy. The proposed recovery-only extension is separate work. The reviewer launched no emulator, read no save-file content, wrote no guest state and reran no broad mock/source/v70 tests.
