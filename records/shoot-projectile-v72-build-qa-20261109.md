# v72 independent reproducibility and byte-boundary audit

PASS on the first audit execution, 2026-11-09. Fresh builds
`build/repro-v72-20261109-a` and `build/repro-v72-20261109-b` contain exactly
289 files each with identical complete relative-path/SHA256 inventories.
All113 declared asset/layer manifest entries in each build were independently
hashed against the frozen main builder's expected dictionaries.

| Evidence | SHA256 |
| --- | --- |
| `build/repro-v72-final-audit-20261109/audit_inputs.py` | `77CE7925254F0CB024ED16D1FB4462851D912FF2DE223D70BB2BBFBF2EAE4D10` |
| `build/repro-v72-final-audit-20261109/audit.json` | `1643B67D7179360B1DAB8E8D34E5CEA8F0556A5276E42D5DF2180A2D6178F6D1` |
| Frozen main builder | `23C6FA4BD215ECDA2A688FE71D8438E1E4669BCA8DE528BDBCE1276C81383480` |
| Each final `current-candidate.gba` | `025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA` |
| Each final `current-candidate.json` | `ACF245F90EA2DEA53E03E3872DD3D8474A34F522453319127DB4E9858BA27198` |
| Exact v71 predecessor | `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` |
| Reused v71 inventory/inverse audit | `A864BD691118545B651643EA3D94422DE22ABEC57BECC052E34B46E44539F77A` |
| Reused independent component QA | `95458CCEBEBDBCD5BE5D2CE703D32490F106629BE58DDEAAC280203DA0830C38` |
| Explicit lower source graph | `37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281` |
| Bounded no-reload composition | `2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990` |

Both final ROMs are byte-identical to the independently tested
`build/shoot-projectile-clear-explicit-20261109/component.gba`. Both new
component QA reports match the exact isolated report bytes. The regenerated
lower graph and no-reload composition likewise match the explicit isolated
input artifacts byte-for-byte. No verifier or source graph was rerun by this
audit; their previously executed proofs were reused by exact identity.

The only new writes are76 selector bytes at `6FF240..6FF28C` and the four-byte
dispatcher pointer at `12C50`. Each payload hash and exact span was checked;
80 bytes are declared and73 differ. The full-ROM inverse restores the exact
v71 predecessor, including its original dispatcher pointer and all retained
companion code/hooks. The76-byte reservation was entirely FF. An additional
mutation immediately after its end fails the inverse without a final-output
hash gate. Both physical v71 predecessor ROM files remain unchanged.

All prior build artifacts and verification reports retain their pinned bytes
except the expected `build-manifest.json`, `current-candidate.gba` and
`current-candidate.json`. The five new paths are `shoot-static-companion-clear.gba`,
`shoot-static-companion-clear.json`, `intermediate/shoot-rule-graph.json`,
`intermediate/shoot-p2-reload-eligibility.json` and
`intermediate/shoot-projectile-clear-verification.json`. The carried-forward
layer/manifest equal the exact old final pair. Existing build-manifest contracts
are unchanged apart from claim text, layer inventory and the new bounded
`shoot_projectile_clear` section. Source/tool hashes and both full inventories
remain unchanged through the audit. The audit script/report use LF.

Approval remains bounded to exact static93E7/base6D under the retained normal
source callback graph and ordinary exclusive ownership. The manifest and QA
retain false flags for full post-clear reload exclusion, complete terminal
clear and external entry. Side1 companions, other tile owners, IRQ/camera,
nonpattern targets and historical E5 remain open. This audit performs no
emulator run, save/state access, guest write or ROM modification; root's
separate runtime evidence is outside this inventory audit.
