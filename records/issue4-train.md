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
| Combined GBA correction | 1427 | 110.813 px | Frame 5058 |

In a second combined GBA match, Guilmon held right and pulsed jump for 40 out of every 90 frames, then reversed direction at input frame 8500. At frame 5592 both fighters reached x=7071. At frame 8964 Guilmon was at x=96 and Patamon had followed to x=2748. The match reached the result at frame 10943 and the next VS at 11481. Both corrected GBA runs retained the input SaveRAM byte for byte.

## Roaming actor

The WSC Train initializer and update alter the scenery, palette and shake state. The crossing creature comes from the shared Calumon actor. Its two entry directions have their own initial position and airborne movement. For the rightward entrance, source callback `0x7445D5` uses the signed sine table at `0x7519C9`. The corresponding 512 bytes at GBA offset `0x12360` are identical. In the WSC fight, live Calumon crossed from x=−364, y=3439 to x=6608, y=3229 before its callback changed. In the corrected GBA fight it entered from the other side at x=7411, y=2326 and changed both height and action. No other stage-specific roaming monster constructor appears in the Train initializer. The original report contains no screenshot identifying a different creature.

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

| Input or additional capture | SHA-256 |
| --- | --- |
| Baseline GBA v1.0 | `AA6BB1EB93027464F842D6EB0CC69A68959F26B38460FAF1B0C63BDD5FFA4BB1` |
| Combined GBA candidate | `95E5A25622AFFC038BF7073FEA26B0950EAEBEF1AD9E576AED5B3A4E830E3EB7` |
| Game-earned GBA SaveRAM | `AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D` |
| Two-fighter right-edge and reversal run, events | `531EF743C2D98841CA1D67EFE3A192715897D4695308E14FD2AFBDB587C9DF88` |
| WSC parity report.json | `276E299E3FDDD38BA386179CC0ED1D1E6AF6DBE9B7F492B9155322309845B612` |
| WSC parity edge.txt | `A110376CA9F5812C7134BEDCCCFF349323874B9CA16DDBE33AEC41BABB790409` |
| GBA parity report.json | `27433914E2DDE4A2684EA799BA7A12BEF4CD970545B96271A25F43BF8E7DFA9B` |
| GBA parity edge.txt | `0C6EC0AD90E5599506F18A1CBAE614A827E752ABDA2690521F22F7625E60FFF0` |
