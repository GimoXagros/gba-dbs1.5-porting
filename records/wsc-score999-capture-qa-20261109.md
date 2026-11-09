# Original score999 capture: bounded Lua completion, host cleanup failure

The original-only run completed its120,000-frame Lua budget and finalized both modules, but **did not reach Shoot**. It ended at stage7's CONTINUE screen: final mode9, P1 HP0 and opponent HP42. The host launcher exited1 during cleanup with WinError5. Independent recovery-aware checks verify the retained capture; they do not change that host exit into runtime success.

## Preserved records and recovery

| Artifact | SHA256 |
| --- | --- |
| Original initial-only `launch.json`, unchanged | `02949C9A8F3FF66A9F05DF672AD51D3191E36C65F82DF685C858273E1ACC92E2` |
| Explicit `completion-recovery.json` | `0E833291D8826315667762E4DB5B0346E1700F10239D7435DE4BAE2739789E3C` |
| Independent `build/wsc-score999-capture-qa-20261109/audit.json` | `A2E4E9B82F20D862F8D502A1343ED8E6157165C96246EB1BDE4788041CD65392` |
| Rerunnable audit script | `53E57CDE733849F174D574AB3F04E45F3EC06FC0D54FB7D2E3B98E793A83CBE9` |
| Score ledger | `F3563B462BBC6C551B7F784D31EB054161F2F527C9498D649B1AA84B796620D6` |
| Actual trace | `83B672B1F39F5B97C2DFB89D2D232C2C4E0AA45E9B6AB40F09337147475724DB` |

Capture directory: `build/bizhawk-wsc-score999-20261109-a`. The independent audit/report use LF. Reproduce with the pinned Python runtime:

```text
python build/wsc-score999-capture-qa-20261109/audit.py --recovery build/bizhawk-wsc-score999-20261109-a/completion-recovery.json
```

The audit requires the recovery file explicitly, checks its hash link to the unchanged initial launch and requires every initial field to remain equal. It separately preserves `lua_bounded_complete=true`, `host_exit=1`, cleanup phase `PrivateDesktopProcess.close`, WinError5 and `postchecks_recovered=true`. The copied PTY diagnostic is included in the verified inventory. Root observed the emulator process absent afterward; this is recorded as root's observation, not a new emulator run.

All80 final recursive files, excluding the initial launch and recovery itself, match the recovery inventory. The exact loaded8MB originalC415, three reviewed modules, five frozen policies, emulator and both core DLLs match their pins. Launcher19AC4B67 and reviewed-pins35B8483A remain exact. Neither capture nor runtime source was rewritten by the auditor.

## Authorized write scope and actual progress

The ledger contains109 writes, all exactly a WORD999 at validated P1 `1784+ C000 +52 = D7D6`. Every write occurs in an allowed ordinary stage0..10 excluding7; none occurs in stage7 or11. The previous values are only0 or250. The finished module records93,907 hook hits,67,510 eligible hits and109 writes. Frozen sole-write code and prior actual-Lua comparisons support this scope; natural game writes are not a claim of whole-guest-state equality.

First observed battle-stage fields follow:

`8 →1 →9 →6 →10 →2 →4 →5 →0 →3 →7`

All11 corresponding RAM/SRAM snapshot sets agree with their logged stage, mode7, P1 handle and score word. These are first-field/transition captures, not necessarily initialized battle displays. Most later stage screenshots are all black; `saved-stage-07` still contains an earlier actor state before the boss constructor. It must not supply the initial boss HP or a visible999 claim.

The independently viewed `progress-9000.png` visibly shows P1 HUD999. The first stage8 screenshot instead shows the earlier000 display despite score RAM999, illustrating capture/render latency. The final screenshot visibly shows CONTINUE? YES/NO.

Actual periodic stage7/mode7 samples begin at relative84900 with P1 HP8 and opponent HP44. The107 samples include six P1 zero-to-positive transitions and five opponent HP rises, consistent with ordinary continue/reset cycles; this is not one uninterrupted fight. The last periodic sample at119700 is HP0/42, and the complete final RAM agrees: mode9, stage7, game kind2, P1 callback5FFD:229B/HP0/score0 and opponent callback4090:649A/HP42/score8. First44/final42 must not be described as only two damage over the entire run.

## DI and completion limits

DI v3 records two valid calibration hooks, **zero paired operand reads**, zero terminal hits and zero distinct DI snapshots. Its finish states no pending pair and `actual_final_irq_observed=false`. The driver agrees, writes `bounded-observation-complete` and never claims `shoot-di-observed`. The base trace ends at core120001, corresponding to the explicit120,000-frame budget. There was no stop request or reported host deadline. The launch-to-done file-mtime difference is1232.318 seconds; it corroborates ordering/bound but is not a precise process-duration or performance measurement.

The initial native SaveRAM wrapper is exact fresh1,024-byte internal EEPROM plus the unchanged authorized32K copy, SHA D855BBDE. The live initial SRAM equals that copy after only source startup004E→01/0073→00. The final isolated native SaveRAM differs, SHA98753D35; its backup equals the original wrapper. Those are development-copy changes. Original-save preservation is the launcher's hash attestation; the independent auditor reads only the staged copy and capture, never the original `.sav`.

This establishes the authorized counter operation, visible999 and natural progression to stage7, followed by bounded loss/continue. It establishes neither actual Shoot/DI, a completed original campaign, final GBA QA nor E5 repair. No emulator, save write, HP/stage/register/progress injection or identical retry was performed by this audit. Any future intervention requires its own explicit scope; this capture used only the approved P1 score write.
