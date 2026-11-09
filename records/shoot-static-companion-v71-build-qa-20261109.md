# v71 independent build and byte-boundary audit

PASS on the first audit execution, 2026-11-09. The two fresh builds
`build/repro-v71-20261109-a` and `build/repro-v71-20261109-b` contain exactly
284 files each, with identical complete relative-path/SHA256 inventories.
All 112 declared asset/layer entries in each build manifest were independently
hashed and matched the frozen main builder's expected dictionaries.

| Evidence | SHA256 |
| --- | --- |
| `build/repro-v71-final-audit-20261109/audit_inputs.py` | `B8E15BCA139FAC11BFF56E0583614223C7C4B5926FDF224F94208FA51D5056EC` |
| `build/repro-v71-final-audit-20261109/audit.json` | `A864BD691118545B651643EA3D94422DE22ABEC57BECC052E34B46E44539F77A` |
| Frozen `tools/build_current_candidate.py` | `65D09A099B18ECC060117287FBB0926D50BC4A147ADBA35FD2A913B058800785` |
| Each final `current-candidate.gba` | `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` |
| Each final `current-candidate.json` | `D8B5207060441EA60025ED88AC56F272B9E8615CD711C144BA94AEFF33476E75` |
| Exact carried-forward v70 predecessor | `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717` |
| Reused isolated actual-ARM QA report | `DF06DEBA3B9BF1B405F6BFE81DE3188DC6002F935723491DEB45A0AB999422CC` |
| Frozen independent component verifier | `CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943` |
| Reused prior v70 audit | `D87DBF8491B363F0DE75264E49F04DA750A1598B417F891A46F176129A920A7E` |

Both final ROMs are byte-identical to the independently tested corrected
`build/shoot-static-companion-20261109/fixed-component.gba`. Each build's
`intermediate/shoot-static-companion-clear-verification.json` is byte-identical
to the frozen isolated `build/shoot-static-companion-qa-20261109/audit.json`.
Those new reports and this audit's new outputs use LF. The audit reuses the
frozen v70 helper/proof and does not execute any component verifier again.

The seven declared writes total 984 bytes, with 964 actual changed bytes.
Each write's offset, length and payload hash was independently checked against
the frozen component manifest; the spans do not overlap. Replacing exactly
those spans with predecessor bytes restores the entire exact v70 ROM,
including untouched reservation padding. An additional mutation outside those
spans is rejected by this inverse check without using a final-output hash gate.
The whole `6FE800..6FF000` reservation is erased in the predecessor. Both
physical v70 predecessor ROM files remain exact and unchanged.

The retained external case5 span `33FCCC..33FDC0`, progress span
`0B9E48..0B9E78`, and callback span `34059C..3407F4` remain byte-identical to
both v70 and retail USA. The unused external-selector span `5C9900..5C9B00`
remains entirely FF. Whole-ROM inversion additionally establishes preservation
of every other byte outside the seven declared writes.

Relative to the pinned v70 inventory, the only changed existing paths are
`build-manifest.json`, `current-candidate.gba` and `current-candidate.json`.
The only new paths are `shoot-spatial-subset.gba`, `shoot-spatial-subset.json`
and `intermediate/shoot-static-companion-clear-verification.json`.
The first two carry forward the exact prior final ROM and component manifest.
All prior intermediates and verification reports retain their exact recorded
bytes. Existing build-manifest contracts also remain identical, except its
updated claim text/layer inventory and the one new bounded
`shoot_static_companion_clear` section. Source/tool hashes and fullbuild
inventories remained unchanged through the audit.

This is a reproducibility and bounded integration pass. The reused component
QA covers 577 owner cases, 69 captures, 6,476 renderer cases over 30 resources
and 219 layouts, 30,720 expirations, 120 same-frame cases and 19 semantic
negatives. It does not prove actual Shoot gameplay or authorize external entry.
Complete terminal clear, primary parity, other owners, IRQ/camera lifetime and
the historical E5 cause remain open. No emulator, save/state file, guest memory
or ROM was modified by this audit; root's runtime capture is separate evidence.
