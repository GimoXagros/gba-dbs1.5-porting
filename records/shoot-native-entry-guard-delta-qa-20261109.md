# Native entry owner/checkpoint correction: independent delta QA

**PASS for observer7513's bounded correction.** The exact driverD40 and development
ROM D0A01 are unchanged. This review executed the changed Lua against the complete
actual IWRAM/EWRAM from the first run's positive-health refusal at export64230.
It launched no emulator, repeated no campaign and reran no old full suite.

The real fixture has FIRST02011710 HP8, SECOND02011828 HP37 and auxiliary02011940
flags0343. Its stage7 quartet of resource pointers matches the new bindings without
modification. The new predicate accepts this owned native kind3 auxiliary, makes
exactly one authorized SECOND+64 WORD1 write and saves the stage7 checkpoint only
after the outer frame. The original score/HP address/value/one-shot code is byte
unchanged. The later Shoot kind6/resource configuration is a separate fixture
derived from the reviewed source bindings, not an observed native stage11 arrival.

| Stage | Aux kind | SECOND P1/P0 | Auxiliary P1/P0 |
|---|---:|---|---|
| 7 | 3 | 0834DFE0 / 0834E27C | 08341C00 / 08341E70 |
| 11 | 6 | 085D0000 / 085D1000 | 085D029C / 085D1100 |

Seventeen actual-Lua refusal partitions cover other stages, crossed kinds and each
crossed resource at both valid stages. Stage11 ownership is accepted only with its
own quartet; no stage11 HP write occurs. Seven additional outer checkpoint denials
cover lost positive P1HP, bossHP no longer1, wrong mode/stage, changed resource,
invalid SECOND and lost input service. None invokes the stage7 save API.

The stage7 checkpoint is attempted once, after the write and outside callbacks.
Its metadata records the actual outer core, next input-relative position and
stage7_consumed=true. Repeated flush/hook calls neither save nor write again.
Both stage7 and healthy checkpoint APIs are tested with true, false, thrown error
and a truthy nonboolean result. Only boolean true permits success metadata and the
healthy outcome. This closes E620's save-failure false-success edge. Failure-only
diagnostic saves additionally exercise true/false/throw while preserving the first
named failure; a diagnostic checkpoint cannot turn failure into healthy success.

Ten semantic mutations are rejected: wrong stage7/Shoot kind, each missing resource
pin, accepting failed saves, accepting a nonboolean save result, repeated boss
checkpoint attempts and omission of the failure diagnostic. Text inversion confirms
every byte outside the changed pair/flush/finish functions, new checkpoint helper
and one new local flag equals the exact frozen E620 observer. DriverD40 is exact.
No old source/ARM/runtime suite was invoked by this distinct delta check.

| Artifact | SHA-256 |
|---|---|
| Corrected observer | 7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59 |
| Independent delta verifier | 7C3676A5B6CB8AECF83C87EF633734FB514008A13B0E4598B4DB9FB2601D3D35 |
| Final delta report | 351EB70B82D7C5126EFA1D16E8D2D160406EE505642E3C04018889CA593E724B |
| Actual IWRAM fixture | 17727C9E0A7B542781A4B1732B2A3D76C0A239AB550C6D61388E4A13069CD3AF |
| Actual EWRAM fixture | BEEBADB0B5A220CA1F4749DD0A91F6C2D09064CDB89909DAF50511C835E5601A |

Report: `build/gba-shoot-entry-guard-delta-qa-20261109/final-report.json`.
Reproduce with a fresh output filename:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -X utf8 tools/verify_gba_shoot_entry_guard_delta.py --output build/gba-shoot-entry-guard-delta-qa-20261109/new-report.json
~~~

API fixtures establish observer semantics, not a genuine saved GBA core, actual
native Shoot arrival or source parity. Those require the separately authorized
root-owned runtime capture and independent artifact audit. Full-port QA and E5's
actual first cause remain open.
