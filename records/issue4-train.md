# Train right-edge movement and roaming actor (issue #4)

The far-right floor of Train launches both players in the original WonderSwan Color fight. Its five rightmost cells in row 25 of the 56 × 36 collision map are class 5. Both engines selected that same class at the edge. The port overestimated the height of the bounce.

## Spring and CPU

The source class-5 handler at WSC file offset `0x742E0F` selects vertical velocity −957 and acceleration 16 at `0x742EA2`. The short variant at `0x768789` selects −445 and 16. At the GBA update rate, the original velocity is multiplied by 5/4 and acceleration by (5/4)². GBA velocities −1196 and −556 were already correct. Both original GBA launch paths used acceleration 20 instead of 25.

The correction uses the live stage and floor class in the launch producer. The later short-launch animation has already cleared its floor cell, so it inherits the initial spring's acceleration. The build executes both installed branches against 12 stage IDs, all 16 floor classes and three previous accelerations. It also checks preservation of ARM flags, stack and other registers.

The table reports the first CPU spring in an actual Guilmon–Patamon match, with the right direction held. Coordinates use sixteenths of a pixel. The launch surface is at y=3200.

| ROM | Apex y, sampled every frame | Rise | CPU left right edge |
| --- | ---: | ---: | --- |
| WSC Ver. 1.5 | 1430 | 110.625 px | Frame 7312 |
| GBA v1.0 | 980 | 138.750 px | Yes, in the baseline run without the parity assertion |
| GBA v1.0.1 | 1427 | 110.813 px | Frame 5058 |

In a second v1.0.1 match, Guilmon held right and pulsed jump for 40 out of every 90 frames, then reversed direction at input frame 8500. At frame 5592 both fighters reached x=7071. At frame 8964 Guilmon was at x=96 and Patamon had followed to x=2748. The match reached the result at frame 10943 and the next VS at 11481. Both corrected GBA runs retained the input SaveRAM byte for byte.

## Train field Digimon

The v1.0.1 review traced Calumon alone. Train has two separate creatures. The evolution pickup Calumon owns pool 1, type `1108`, and WSC handle `06FA`. The neutral item Digimon owns pool 5, type `4106`, and handle `06E8`. Their native GBA handles are `03004CE8` and `03004CD0`. Both appeared in the same match on each platform. Calumon already follows an airborne path on both.

The field Digimon in the WSC version is DemiDevimon. Version 1.0.1 used stage 0's Mushroomon and walked it at the fixed heights from its native stage, leaving it visibly above Train's platforms. The WSC field dispatcher at `0x7638EC` selects Train's timer `0x763AF6` and constructor `0x76424C`. Its 32-byte stage 8 graphic descriptor at `0x740880` matches the stage 2 DemiDevimon descriptor byte for byte. The two stages use different motion and entry patterns. The source Train actor launches from (7424, 2432) or (1024, 2432), follows the signed sine table, and exits at the opposite end.

The fix selects the native stage 2 sprite, palette and one-hit actor initialization for Train. It supplies Train's own direction sequence, delay, movement, effect, collision window and exit. The dispatcher checks both stage identifiers and the incoming profile. Existing stage 2 play still uses its own movement. If both neutral slots are occupied, the corrected timer leaves the current occupants, pending counter and direction index intact. The native allocator itself would otherwise select the last occupied slot. An installed-instruction test covered 48 combinations of pool status and existing owner, and a separate selector comparison covered 88 ordinary and 183 stale or mismatched stage/profile cases.

The WSC and corrected GBA captures include ordinary attacks. In each, both entrance directions traversed the stage. After a monster entered its defeat callback, the observer checked the same actor immediately after the game wrote item type `9325`. The native conversion uses the existing source-equivalent Train drop table. A separate CPU spring run on the final ROM again reached apex y=1427 and left the right edge before the battle result. Independent sprite inspection identified both species in the [three-way screenshot comparison](../docs/screenshots/issue-4-train-roaming.png).

At the same six world coordinates, sampled height differed by at most 1 display pixel. The regression allows 2 pixels for the difference between 75 Hz WSC and 60 Hz GBA sampling. Coordinates below are sixteenths of a pixel.

| Direction | World x | WSC y | Corrected GBA y |
| --- | ---: | ---: | ---: |
| From the right | 6912 | 2560 | 2560 |
| From the right | 5824 | 3009 | 3018 |
| From the right | 4352 | 2307 | 2323 |
| From the left | 1536 | 2139 | 2138 |
| From the left | 2816 | 2502 | 2502 |
| From the left | 3840 | 2487 | 2498 |

Five WSC and eight GBA neutral actors converted in place to items during these independent matches. Exact counts depend on the fight. The first conversions occurred at frames 5242 and 6142 respectively. The WSC reached its result at frame 13461. GBA reached the result at 10943 and the next VS at 11481; its SaveRAM hash matched the input. On the v1.0.1 negative control, the observer found neither authored crossing direction at the expected speed.

## Repeat the headless regression

Use the release harness prerequisites, the verified WSC ROM, a locally built GBA ROM and the existing 15-fighter game-earned GBA SaveRAM. The snippets below run from the repository root in PowerShell 7. Supply the paths and expected GBA hash for the desired build. The harness copies each ROM and any SaveRAM into its own fresh output folder. WSC starts without a save.

```powershell
$edge = New-Item -ItemType Directory -Path build/issue4-train-replay
Copy-Item tools/run_flow_release.py $edge
foreach ($driver in 'bizhawk_flow_release.lua','bizhawk_flow_release_train.lua') {
    $observer = Get-Content -Raw tools/bizhawk_issue4_train_edge.lua
    $play = Get-Content -Raw (Join-Path tools $driver)
    Set-Content -Encoding utf8NoBOM -Path (Join-Path $edge $driver) -Value ($observer + "`n" + $play)
}
$env:PYTHONPATH = (Resolve-Path tools).Path
$run = Join-Path $edge run_flow_release.py
python $run --rom $wsc --expected C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7 --original-train --out (Join-Path $edge wsc)
python $run --rom $gba --expected $gbaSha256 --save $earnedSave --fighter 0 --out (Join-Path $edge gba)
```

Each run records the loaded ROM checksum, controller and result in `report.json`. `edge.txt` records the first spring, minimum y, CPU reaching the rightmost coordinate, CPU leaving it and the match result. The acceptance window is 2 pixels around the observed WSC apex. GBA v1.0 fails that assertion at frame 3962.

To test the field Digimon, repeat the commands in a fresh output folder with `tools/bizhawk_issue4_train_roamer.lua` as the observer. It keeps the normal controllers and writes `roamer.txt` with both flight directions, six world landmarks and the frames of the confirmed item conversions.

| Input or additional capture | SHA-256 |
| --- | --- |
| Baseline GBA v1.0 | `AA6BB1EB93027464F842D6EB0CC69A68959F26B38460FAF1B0C63BDD5FFA4BB1` |
| GBA v1.0.1 | `95E5A25622AFFC038BF7073FEA26B0950EAEBEF1AD9E576AED5B3A4E830E3EB7` |
| Game-earned GBA SaveRAM | `AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D` |
| Two-fighter right-edge and reversal run, events | `531EF743C2D98841CA1D67EFE3A192715897D4695308E14FD2AFBDB587C9DF88` |
| WSC parity report.json | `276E299E3FDDD38BA386179CC0ED1D1E6AF6DBE9B7F492B9155322309845B612` |
| WSC parity edge.txt | `A110376CA9F5812C7134BEDCCCFF349323874B9CA16DDBE33AEC41BABB790409` |
| GBA parity report.json | `27433914E2DDE4A2684EA799BA7A12BEF4CD970545B96271A25F43BF8E7DFA9B` |
| GBA parity edge.txt | `0C6EC0AD90E5599506F18A1CBAE614A827E752ABDA2690521F22F7625E60FFF0` |
| Corrected Train field actor GBA | `F32BEFB1673B57A94498BAAB6E62D0A1351C3AE3614601B3F8F3EC1C7EFE0090` |
| WSC field actor coordinates and drops, roamer.txt | `EDCAC7A2DB99A5DF6B2025BDE1ED5C2A1090406E0B336BAA47CE41D55F2FF3E7` |
| GBA field actor coordinates and drops, roamer.txt | `39BAFBB87496942260CFBD716D72EB12650D5FDEF580978A978A7CD573EF854B` |
| WSC field actor final report.json | `7496C467E50FBCE9A28407D91C2EDF5D56FF5B833BBA8664653F8438FCF5B678` |
| GBA field actor final report.json | `A223B869D1D6727FC02B7A89612E1E713AD61E6A40CFB3978D95559037DA9EA9` |
