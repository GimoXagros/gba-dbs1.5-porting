# Independent QA: finite wall-escape input policy

Accepted the new ordinary-input wrapper for a fresh parent-owned run. No emulator was launched in this review and no actual escape or Shoot entry is claimed.

- Wrapper `tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua`: `85D7F25E2C6A8AA4C24AFBCDB95A51E7F9A3414FA3E97635FCD7C9EC3436ADE4`.
- Author's actual-Lua checker `tools/verify_wsc_shoot_short_hard_v2.py`: `1FF0ABF8FCF259719DA7F57ADD82CE613761B36303BD49277F4375277BA0A667`.
- Independently rerun full mock report `build/shoot-wall-escape-qa-20261106/full-mock-independent.json`: `45FA597D64DC3EE25C8B6E5504E00F547BD7C0410D161748EDCB073A5B7DD4D8`, identical to the author's final report. All22 routes and six negative controls pass.
- Independent edge checker `tools/verify_wsc_wall_escape_edges.py`: `3872CBD838B9498C006584E8C66966891A6FD540EB11D1DCD179074528F2069D`.
- Independent edge report `build/shoot-wall-escape-qa-20261106/edges-a.json`: `70BF185B63C9FA00CE2B5C2B649F2D12B3477932C5B6FFC5861C7EF41F15C932`. All22 actual-policy scenarios and four semantic negative controls pass.

The new policy runs after the existing collector selects ordinary buttons. It requires180 consecutive samples within32 fixed coordinate units of the X anchor, an opponent more than0300 units above and more than0100 units horizontally away, and exactly one held horizontal direction pointing toward that opponent. It then sends60 frames in the opposite direction, with attack released and one eight-frame jump pulse at ages4..11. A full360-frame cooldown follows before a fresh stationary interval can accrue. Under continuous eligibility the first two starts occur at frame indices179 and778; the599-index difference follows inclusive sample counting and does not shorten any cooldown.

Independent edge tests exercise every guard, equality boundaries, no/both/wrong direction, sustained slow motion, direction reversal, signed negative coordinates, discontinuous frame sampling, player/target handle changes, invalid handles, mode changes and stage11 entry during an active recovery. State is reset at these discontinuities. Entering stage11 cancels recovery immediately; returning to a regular stage requires a fresh180 samples. The first three recovery starts alone capture PNG and64KiB RAM snapshots; this ceiling persists across policy-state resets.

The frozen E382 parent, 2AD5 collector and0CC9 observer are loaded without rewriting their files. Options navigation to short timer0/difficulty3, the stage7 HP-boss input path, source-owner hooks, positive stage11 row-clear/IRQ completion and callback calibration remain intact. The parent captures the original joypad setter before collector installation; final release calls it directly even during recovery. The full nested-wrapper mock explicitly checks release during an active escape and retains all16 prior route/completion regressions.

The ignored host launcher `build/run_wsc_short_hard_v2_20261106.py` was read-only reviewed at SHA256 `D27CA11607394DC89CB9760FF7169A7DCEF232978B99D36F23A4FCE55A336766`. It requires the reviewed wrapper hash as an argument, pins the three dependencies and original WSC/core identities, copies the ROM to a fresh isolated output directory, redirects save/config paths, disables autoload and SaveRAM autosave, and uses the existing private-desktop process context. Its120000-frame/1500-second bound and host `stop.request` produce truthful incomplete reports without creating a completion marker. No change to the launcher was made here.

```powershell
python tools/verify_wsc_shoot_short_hard_v2.py SOURCE.wsc --output FRESH_FULL_REPORT.json
python tools/verify_wsc_wall_escape_edges.py --output FRESH_EDGE_REPORT.json
```
