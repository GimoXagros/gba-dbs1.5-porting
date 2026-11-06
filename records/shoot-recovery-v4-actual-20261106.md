# Actual first grounded recovery comparison

The final70B7 original-WSC run uses ordinary input only. Through relativeframe18585 its826 input-change events (frame and key set) equal the frozen v2 run exactly. The first recovery snapshot atcoreframe18586 is byte-identical between the two runs: SHA256 `1C77C078F317FFA27FF9C72C7A7E9DEB85FCD7B6036FF1B0D9E8D3A0284CA909`. Both start P1 at02E0,0FC8. This provides a concrete same-start comparison for the new timing.

V4 waits until `escape-jump` atcoreframe18612, recoveryage26, with P1 at03FC,1100. The policy guard establishes that it read one of the accepted grounded idle/walk callbacks, but the note does not record which callback word. Actual input changes show A held from relative18611 to18623, exactly12 samples. Atcoreframe18645 recovery ends at067B,0D4A; v2 ended0714,1100. The new endpoint is59.375 pixels higher. This is an observed gameplay change, not merely a host-mock result.

Subsequent300-frame samples no longer show the old repeated02E0 trap: at18900 P1 is039F,0EF6;19200 X1136;19500 X1B9F;19800 X0E25. The opponent also leaves0060. Only one recovery was logged through this bout. These samples establish escape from the observed stationary pattern; they do not reconstruct every collision or prove which platform was crossed.

The first Stage1 bout nevertheless ends5:8 in results at20700/21000. A second bout begins21600. No Stage1 win or Shoot entry is claimed. No active observer was changed and no additional policy variant is proposed.

Evidence: `build/shoot-short-hard-v4-trajectory-20261106/first-recovery.json` preserves the prefix/snapshot comparison and exact recovery notes; `after-recovery.json` preserves the subsequent sampled trajectory. Root owns the continuing bounded run and its final capture audit.

## Final partial capture audit

Root stopped this run through the host stop request after repeated later Stage1 losses. The launcher cleaned up its private-desktop process and wrote `completed=false`, `host_stop_requested=true`, `host_deadline_reached=false`, exact loaded ROM and unchanged scripts. No observer completion marker, final snapshot or end-of-run calibration/release completion is claimed. The last logged input is relative57558; the last telemetry is relative57300, Stage1 mode7, timer3990, score4:5. No Stage11/Shoot appears. No further input-policy variants are planned from these observations.

Final launch SHA256: `863C84782227D2BCCA71DCD0F4EE0210F94813A8D100BC1C1157E66321E4ED1E`. Root independently checked all31 files including launch, the complete recursive inventory, copied/loaded original C415 ROM, all five frozen script pins, isolated configuration paths and disabled background input/autoload/automatic SaveRAM persistence. It independently repeated the826-event prefix and identical first RAM comparison, the actual12-sample A interval with B suppressed, and the59.375-pixel endpoint difference. No source or guest state was changed, and no supplied save was accessed.

Audit: `build/shoot-short-hard-v4-capture-qa-20261106/audit-root.json`, SHA256 `A4E1D4B2A23270A5DE239317D4E9A9695D12FF26257A92A3FF881ECEF2E7F6AB`. This is successful validation of a partial observation and its narrow recovery result, not campaign completion or Shoot lifetime closure.
