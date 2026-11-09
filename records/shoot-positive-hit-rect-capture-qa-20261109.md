# Rectangle-repair trial: independent runtime capture audit — 2026-11-09

PASS for integrity of the completed1477 observation in
`build/bizhawk-gba-shoot-positive-hit-rect-20261109-a`. The same input policy
passes the previous69165 dispatch-refusal boundary and reaches70127 after
1200 advances, then stops as `failure:bounded-no-completion`, updates0.
No accepted FIRST→SECOND positive hit or flash expiry was observed. FIRST
HP4 and SECOND HP37 remain unchanged throughout. This is not a successful
positive-hit or whole Shoot completion result.

All29 files exactly match the finalized launch inventory, including the
unchanged619AA wrapper, original9F12 observer,03CAD host/four script pins,
exact copied/loaded1477 ROM and seven checkpoint files. Source and copied
checkpoint bytes are identical to the previous trial and original healthy
checkpoint. Configuration paths are isolated; background physical input,
SaveRAM autosave and automatic last-state loading are disabled. The launch
completed without host stop or deadline. No emulator, state load, evidence
edit, retry, clamp or guest write was performed by this reviewer.

## Controlled comparison with the previous6D trial

The complete decompressed new1477 restored Core equals the previous6D
restored Core after changing **only** bytes12..15 of the comparison buffer
to the new ROM CRC. No audio, timing, memory, CPU, loader or other field is
normalized. All five initial RAM regions also equal both the old trial and
the original healthy checkpoint. SyncSettings remain identical; UserData
contains only the new output/checkpoint/probe arguments.

Every one of the first239 input records is byte-identical to the old trial.
The first238 complete actor-frame records also match. The old observer
rejected its dispatch target during core69165's next advance; the new trial
has no invalid-dispatch-target record and continues through core69166 to
70127. These exact starting-state/input comparisons strengthen this bounded
comparison. They do not establish a historical E5 cause or certify every
possible child-rectangle trajectory.

All1200 input/frame pairs are contiguous and match the frozen policy and
the previous frame's measured horizontal distance. The actual counts are
20 A pulses,100 B pulses,137 Left frames and858 Right frames. Native A40/B80
held bits agree with those commands. No controller, timing or input-policy
change is hidden in this comparison.

## Result and genuine captures

Both00-before and bounded-no-completion are genuine BizHawk2.11.1 GBA states.
ZIP CRCs/entries, ROM identity and frames68927/70127 pass. Entire decompressed
IWRAM/EWRAM/VRAM/palette/OAM equal their independent same-frame dumps. Both
snapshots retain live input08374FF4 and battle083735BC task owners, mode7,
stage11, player HP4 and boss HP37. PNGs are valid native240×160 captures.

The final scalar failure file exactly equals the trace prefix through the
bounded outcome, before the full outer capture. Its observed/export core
are both70127 because this is an outer-loop budget result. There are no
invalid producer/overlap/scratch/dispatch, P1-death/root4, positive-damage,
nonfatal adapter, timer-update or expiry records in this run.

Final actor coordinates and the auxiliary counter are retained verbatim in
the report. For example FIRST's later Y6400 is an observation, not an
automatic bug classification; source aim/control analysis owns that question.
The absence of a positive hit remains open even though the previous dispatch
refusal no longer occurs on the controlled trajectory.

Strict equality against the original healthy Core remains **false**. It is
also false against the source Core with only the new ROM CRC expectation.
Every actual expected/actual difference is retained. The original offsets
are12,13,14,15,326,327,330,342,343,384,385,393,397; the CRC-expectation
comparison differs at326,327,330,342,343,384,385,393,397. No older difference
pattern is used as an exemption. CPU-bank bytes, native extension data and
managed suffix remain equal to source. This qualification is independent of
the stronger new-versus-old restored-Core comparison above.

Restored VRAM is the source checkpoint's exact old VRAM, so inherited score
tiles are expected to persist. No new cold-entry visual HUD parity claim or
RAM erase is made here.

| Frozen artifact | SHA-256 |
| --- | --- |
| `tools/verify_gba_shoot_positive_hit_rect_capture.py` | `F0BB14AF04ED208C2450C802AE51277FD135C61AD1153C299CBB31D4566335F9` |
| `build/gba-shoot-positive-hit-rect-capture-qa-20261109/report.json` | `687866978FAEAFA6360AFE772FA151BA502C5BA93E51FE4E4ACCA9AF6A1D3767` |
| Actual launch manifest | `55576FED940005370EE7D0350407AEA06364B59C5FDEB6768D640EE402785D88` |

Reproduce to a fresh output report after completed capture:

~~~powershell
python -u -X utf8 tools/verify_gba_shoot_positive_hit_rect_capture.py --root-completed --output build/gba-shoot-positive-hit-rect-capture-qa-20261109/new-report.json
~~~

No unchanged Lua/component full suite was rerun. Rectangle component QA,
next input-cadence exploration and historical E5 investigation remain separate.
