# v75 ordinary Korean KO capture — independent QA

PASS for the completed headless ordinary Options/title/battle/WIN run
`build/bizhawk-result-v75-20261110-a`, using exact final component
46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B.
The finalized launch declares completion, exact copied/loaded ROM,
unchanged observer and no guest writes. All 61 inventoried artifacts plus
launch.json are checked: 62 top-level files in this new capture.

All eight complete PNG files, all five complete memory regions and each
display dump are byte-identical to the independently audited v74 run.
This includes the entire IWRAM, with no stack exception or normalization.
The complete 128-line trace is byte-identical, including all raw initializer
records and every core/relative frame. All observed timing deltas are zero.

| Capture | v74 and v75 core |
|---|---:|
| options-staged | 3458 |
| options-committed | 3559 |
| title-committed | 3560 |
| battle-enter | 3999 |
| result-enter | 11519 |
| result-plus120 | 11639 |
| result-first-label | 11776 |
| result-plus300 | 11819 |

Native observations retain one writer entry, seven initializer entries and
88 text draws. The complete WIN label proves 30 parts and 1508 pixels.
The v74 flat directory has one extra `config.saving.json` file; it is
preserved and recorded, not invented in the fresh run. Shared files differ
only for config.json, launch.json, probe.gba and loaded-rom.bin.

The pinned B006 host configures SoundOutputMethod=3 before launch, while
the completed saved configuration records method1. SoundEnabled remains
false and autoload/autosave remain false. The report explicitly preserves
this difference; the actual audio backend is not inferred or called Dummy3.
The first run of the new draft v75 checker retained v74's strict saved
method3 assertion and failed with `ValueError: Dummy3 isolated runtime
config` before creating reports. That predicate was then changed in this
new v75 checker to require the actually saved method1 and unchanged
sound-disabled/autoload-disabled/autosave-disabled fields. The frozen v74
checker and its reports were not modified. The qualified pass is separate
from that initial strict-method failure.

| Artifact | SHA256 |
|---|---|
| tools/verify_result_v75_capture.py | 5319051EC877A4ADEADB0CBCD851F9266C5A651FA25D46EF9EBE50E42C55A797 |
| build/result-v75-runtime-qa-20261110/ko-audit.json | 49377964F075AD7779A4F5D1E35E0209A8C5B62E5C51C21EF416C8E07D2EC61F |
| build/result-v75-runtime-qa-20261110/v74-comparison.json | 820002D283597B18D7561CD30C71A3EBEE0CDBE38348921E7511774D8940E436 |

This audits ordinary KO regression only. Shoot terminal/IRQ and completion
remain separate. No full-build output was read for this audit: the completed
capture's exact probe ROM was used. No emulator, save/State access, old
manual suite, main/host/Git edit or capture mutation was performed.
