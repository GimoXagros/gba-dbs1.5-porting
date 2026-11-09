# v71: static companion terminal clear integration

The source terminal clear can erase fixed companion tiles. v71 records the four logical blank tiles in the existing terminal payload+52, projects them through the retained native dynamic renderer, and expires them on the actual preload. The actor tasks enqueue presentations; the priority6000 battle task renders after fighter preloads. The supported subset is30 recognized static companion resources at base49 and camera BX261..288. Primary fighter banks, other owners, IRQ/camera lifetime and the external Shoot route remain open.

The isolated review found a real draft bug: native R5 at35346C is a resource byte offset. The corrected preload resolves the P0 through084A82D8+R5. Withdrawn31790830 was never integrated. See [implementation and source ownership](shoot-terminal-upload-lifetime-20261106.md) and [independent actual-ARM QA](shoot-static-companion-qa-20261109.md).

## Integrated files and reproducibility

The main builder preserves v70 as shoot-spatial-subset.gba/json and appends the independently verified static companion layer. Its seven writes declare984 bytes and change964; reversing those writes restores exact v70. No new RAM or task allocation was introduced. The runtime verifier accepts only the corrected exact ROM through that inverse; eight corrupted images and the withdrawn draft are rejected before capture I/O.

| Artifact | SHA-256 |
|---|---|
| Main builder | `65D09A099B18ECC060117287FBB0926D50BC4A147ADBA35FD2A913B058800785` |
| Final development ROM | `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` |
| Independent component report | `DF06DEBA3B9BF1B405F6BFE81DE3188DC6002F935723491DEB45A0AB999422CC` |
| Complete build audit | `A864BD691118545B651643EA3D94422DE22ABEC57BECC052E34B46E44539F77A` |
| Runtime verifier | `249EDF4E32838E8DC623A2CCEDEE676AA6B62F63177902AD943E5E1034A4C381` |
| Hidden runtime audit | `23F56022C242F78F6C224D8DFD08FE245829E9E7E2A94AA06A207E46DC25E5F1` |

Fresh original-input builds build/repro-v71-20261109-a and -b both exited0. All284 relative file paths and hashes match, including the new final ROM and frozen independent report. The audit in build/repro-v71-final-audit-20261109/audit.json recomputes every file and manifest entry, checks the complete inverse and unchanged external entry. Prior verifiers were not manually rerun after their exact frozen outputs were established by the full builds.

## Hidden regression and limits

The fresh private-desktop run build/bizhawk-result-v71-20261109-a used ordinary controls, language2 and isolated settings/data paths. No supplied save or guest-memory write was used. The process exited0; loaded-ROM and script identities matched. The independent report in build/result-v71-runtime-qa-20261109/ko-audit.json checks61 files,8 snapshots,1,508 exact WIN pixels and five negative controls.

All eight screenshots and EWRAM/VRAM/palette/OAM buffers equal the v70 capture. The exact absolute timing after Options commit is one core frame later; battle-to-result duration remains7,520 frames. Raw IWRAM/display differences are retained in the comparison, so this is not a claim of complete RAM or performance equivalence. The owned emulator and temporary W: mapping were closed after the run.

Actual Shoot entry, complete terminal clearing, DRAW/LAST CHANCE occurrence, complete campaign, audio, fresh-process persistence and final hardware QA were not established. E5 remains unresolved. The next bounded93E7 work uses [source alias ownership](shoot-6d-alias-lifetime-20261109.md) and [typed P2 reload eligibility](shoot-p2-reload-eligibility-20261109.md); no simple shared-pixel substitution is authorized by this checkpoint. This is a development checkpoint, not a final port or release patch.
