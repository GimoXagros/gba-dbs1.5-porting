# v73 complete-build inventory and inverse audit

PASS on the first audit execution after both fresh builds completed with
exit0. `build/repro-v73-20261109-a` and `build/repro-v73-20261109-b` each
contain295 files with identical complete relative-path/SHA256 inventories.
All115 declared asset/layer entries in each build were independently hashed
against the frozen main builder's expected dictionaries.

| Evidence | SHA256 |
| --- | --- |
| Inventory audit script | `4D5C0AD35E8674F180E5D561E21E04FCC98D28410E8A5C6896CBCC9E62A0595F` |
| Inventory report `build/repro-v73-final-audit-20261109/audit.json` | `C512D0F62F05DB54CF4FD0A4315B14C6B313D09663C600BA34D079F8CE0120F6` |
| Frozen main builder | `2800E6F883C64AA8617CB8E23004D7374A416FA48314575AB04D070741900C12` |
| Runtime inverse verifier | `989EA9640E4CB7AF35F73A9FAC6BFC73093EEF92F31CBB4BB8CDA9BC517235FE` |
| Each final ROM | `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7` |
| Each final component manifest | `69D9E5140216D8479124DD230A5F1ED19676491FA10686D61542FD3DA28F5EE8` |
| Guarded IRQ intermediate | `18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1` |
| Guarded IRQ component manifest | `D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C` |
| Retained v72 predecessor | `025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA` |
| Reused v72 complete-build audit | `1643B67D7179360B1DAB8E8D34E5CEA8F0556A5276E42D5DF2180A2D6178F6D1` |
| Independent guarded IRQ QA | `555554FDADF48C80F74DE2A9700B7ECD6FC798F859C151B6A4AC440A9C6925FB` |
| Independent fatal-route QA | `61656691CD4126193003FB2E43B851F3CAA57A8C6C78A147ED602B181F2F2FD4` |

The audit script is `build/repro-v73-final-audit-20261109/audit_inputs.py`.
It reuses the exact pinned v72 audit and v70 inventory/inverse helpers;
no old verifier or isolated-component suite was rerun by this audit.
All frozen main, source-contract, builder, verifier, interpreter and layout
ledger hashes were checked before and after reading the complete outputs.

The four IRQ spans are D0BE8 (4 bytes),6FF600 (288),6FF9C0 (1092), and
6FFE10 (192). The fatal route adds only36E5EC (4 bytes). Each layer's
full-ROM inverse and the combined five-span inverse restore the exact
predecessor:1580 bytes declared and1554 actually changed in total. Four
additional mutations in the gap after the adapter, the gap before the IRQ,
the retail instruction after the fatal hook, and the retained fatal adapter
all fail the inverse without relying on the final output hash.

Each build's IRQ intermediate and final ROM equal the separately tested
isolated artifacts byte-for-byte. Both regenerated component QA reports
equal the frozen independent reports exactly. The two physical v72 final
ROM files also remain equal to the carried-forward predecessor.

Compared with the complete v72 inventory, only `build-manifest.json`,
`current-candidate.gba` and `current-candidate.json` change among existing
paths. The six additions are:

- `shoot-projectile-clear.gba` and `.json`, preserving the exact v72 final pair.
- `shoot-guarded-transition.gba` and `.json`.
- `intermediate/shoot-guarded-transition-verification.json`.
- `intermediate/shoot-fatal-callback-verification.json`.

Every previous build artifact and verification report otherwise retains its
exact bytes. Prior build-manifest contracts remain identical except claim
text, layer inventory and the two new bounded feature sections. Both complete
inventories and all source/tool pins remain unchanged through the audit.

This is approval of reproducible integration of the stationary native IRQ
family and stage11 fatal callback route. It does not close moving low-Y
entry, the external Shoot scene route, historical E5, or complete Shoot.
The audit performs no emulator run, save/state access, guest-memory write,
ROM modification or Git operation. Root's separate hidden KO check is outside
this inventory audit.
