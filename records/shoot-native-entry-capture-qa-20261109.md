# First native entry capture: independent QA

**Capture integrity passes; native Shoot activation was not reached.** The completed
root-owned hidden run `build/bizhawk-gba-shoot-entry-20261109-a` ended normally with
`failure:continue-reached` at core70147. Final mode9/stage7 has P1HP0 and bossHP36.
The host reports completed=true, exact loaded ROM and unchanged scripts. No healthy
checkpoint, root5/hit/restore/activation proof or first E5 failure was produced.

The independent auditor verifies all51 recursively inventoried files, six complete
snapshot sets and PNG dimensions, exact8MiB loaded D0A01 ROM/copy equality, frozen
D40/E620/base7BE2/producer146D scripts and launcher019A. The four exact Lua files are
preserved under `build/gba-shoot-entry-capture-qa-20261109/frozen-lua` so a later
observer correction cannot change the evidence used to reproduce this audit.
This reviewer launched no emulator and changed no runtime file, ROM, main or Git state.

All26 ledger entries are verified two-byte FIRST+66 writes to999 in allowed ordinary
stages with positive P1HP and valid actor-pool handles. There are zero boss HP writes,
stage7_consumed=false and zero stage11 writes. The score writer's existing guard
implementation is pinned; full snapshots are later frame exports and are not claimed
to be simultaneous RAM images of each ledger intervention. Six independent ledger
controls reject stage11, zero P1HP, zero requested HP, P1 HP address, unverified write
and a repeated boss action.

The actual positive-health refusal resolves the next concrete observer issue:

| Fact | Actual observation |
|---|---|
| Refusal | callback core64229, exported core64230 |
| Battle | mode7, stage7, difficulty2, gamekind2, progress01C0 |
| FIRST | 02011710, active, kind0/index0/id0, HP8 |
| SECOND | 02011828, active, kind3/index1/id0F, HP37 |
| Auxiliary | 02011940, active, flags0343, low kind3/index2 |
| Reciprocal links | FIRST↔SECOND, SECOND+28→aux, aux+28→SECOND, aux+18→FIRST |
| Failed frozen actor check | auxiliary kind6 only |

All other independently decoded actor checks pass. Source review identifies the
native stage7 constructor literal370094=0343 and store through352374, whereas the
later translated Shoot operation5BC270..5BC284 changes the low kind to6. The frozen
observer applied that later kind6 guard to stage7. This capture supports a correction
to stage-specific positive ownership checks; it does not justify accepting arbitrary
kind3-or-kind6 objects or weakening links. The root owns any corrected experiment.

Snapshots record first ordinary battle/score at3920→3921, ordinary generic-grab
event48 at10470→10471, the positive typed refusal64229→64230, root4 loss69904→69905
and Continue70147 at the outer frame. The event48 hook alone is not the conditional
upper Shoot null-frame consumer. Callback R15 values are hook+4, for example
373638→37363C; these are retained raw rather than normalized to fixture PCs.

The output paths are isolated and autoload/autosave/background input remain false.
The host requested SoundOutputMethod3; the final emulator-written config records1.
SoundEnabled remains false. This audit therefore does not claim final Dummy3
configuration. A fresh generated `data/104/probe.SaveRAM` is inventoried; no supplied
save was staged or read by this auditor.

The independent checkpoint-failure issue noted in the Lua QA record was not exercised:
this run created no healthy state and makes no healthy claim. The capture auditor
independently refuses a healthy outcome without a nonempty actual checkpoint and
matching healthy captures. Source-derived guard and save-failure corrections require
new observer QA before another root-owned run; no prior source fights were repeated.

| Artifact | SHA-256 |
|---|---|
| Completed launch.json | 1C67BB4137D4EA8062E9D9EE5679208CA8B28A64CA35E42BD14D791D2CC539D0 |
| tools/verify_gba_shoot_entry_capture.py | 970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D |
| Final independent report | FD6789512ED31EEE82ADA0C8443F46E14686F986FA03640C14C4258407C6E269 |

Report: `build/gba-shoot-entry-capture-qa-20261109/final-report.json`.
Reproduce with a fresh output filename:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/verify_gba_shoot_entry_capture.py build/bizhawk-gba-shoot-entry-20261109-a --output build/gba-shoot-entry-capture-qa-20261109/new-report.json
~~~

No terminal bot, successful native Shoot arrival, E5 cause, source parity, campaign
completion or final port QA is established by this failed entry attempt.
