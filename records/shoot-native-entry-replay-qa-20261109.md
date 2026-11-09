# Native checkpoint replay wrapper: independent QA

**PASS for wrapperA73E and the host421D read-only preflight.** No emulator was
launched, no real state was loaded and the original438C checkpoint was not changed.
The corrected84D ROM's separate component approval remains separate from these
loader checks. Actual restore/resave equality still requires the root-owned run.

The actual wrapper, observer7513 and driverD40 execute in the installed Lua54 DLL
with the complete five checkpoint memory regions and real checkpoint metadata.
The API fixture proves load occurs before hooks and input; old checkpoint userdata
is cleared and only six explicit arguments are rebound. Restored output/probe
values replace the old checkpoint path and stale userdata. All five regions match
before and after the proof export, and the restored frame must remain64230.

The reused driver resumes epoch1 with its next ordinary controller phase64229,
keeps a bounded loop and releases controls. No new guest write API is reached.
A forced ordinary score request is stopped by the replay's explicit write denial.
The injected historical consumed-stage7 flag also permits the later direct-hit
root5 observer path in actual Lua without repeating a boss HP action.

False/thrown load and export calls, wrong frame before/after export, each of five
memory mismatches on either side, wrong domain size, metadata epoch/consumption,
bad state signature, userdata clear/rebind error, missing/duplicate module anchors,
missing driver anchor, invalid paths and invalid budgets refuse continuation.
Eight semantic controls reject retained stale userdata, wrong input epoch, lost
historical consumption, removed write denial, ignored proof export failure,
removed RAM equality, removed frame checks and removed reviewed epoch checks.

The exact host's immutable ROM/checkpoint preflight was executed up to its first
executable/output-directory section, which was excluded. Actual84D equals D0A01
after exactly the five reviewed ARM word changes at5C9108/10C/120/174/1A4; title
and game code match. The actual438C checkpoint, C6E8 full Core and all five memory
regions pass the previously pinned parser. No process or output directory is
created by that preflight execution.

The remaining host was statically reviewed: six exact dependency pins, fresh
isolated private desktop/data paths, disabled background input/autoload/autosave
and sound, explicit8000-frame/240-second limits, unchanged checkpoint copies and
loaded-ROM/script checks. Its post-run comparison changes only decompressed Core
bytes12..15 in an expected buffer to the corrected ROM CRC. All other Core bytes
must match. No checkpoint file is rewritten.

| Artifact | SHA-256 |
|---|---|
| Replay wrapper | A73E59919E77FCA67A2DAE6EEA214E1571604818F05008B405CB919300E2C397 |
| Replay host | 421D809E76B91CBC1D122BB44D1BCDD476A224F501717188CCE5F786B2820172 |
| Independent checker | FC5652C31F03149219C133447CCCFB26D4090A6A4F1F9C711232638D0C942C74 |
| Machine report | 8556D3538DE36FA32F86AFE723E0F772D13333DC02811C830596F19BD350F2A2 |

Report: `build/gba-shoot-entry-replay-qa-20261109/report.json`.
Reproduce with a fresh output filename:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/verify_gba_shoot_entry_replay.py --output build/gba-shoot-entry-replay-qa-20261109/new-report.json
~~~

Actual restored Core equality, behavior under84D, initializer/activation, E5 cause
and final port QA remain unverified by this fixture/preflight review.
