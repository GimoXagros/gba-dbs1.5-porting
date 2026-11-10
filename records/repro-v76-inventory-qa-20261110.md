# Completed v76 fresh-build independent inventory

PASS after root confirmed both full processes exited zero. Builds
`repro-v76-20261110-a` and `repro-v76-20261110-b` have exactly310 files with
identical relative paths and full hashes. All120 asset/layer manifest
entries independently close in both builds.

All307 v75 paths remain. Only build-manifest.json,current-candidate.gba
and current-candidate.json change among shared paths. The exact three new
paths are shoot-owner-link.gba,shoot-owner-link.json and intermediate/
shoot-display-epoch-verification.json. Preserved owner ROM/manifest exactly
equal the old v75 final; final280D and production reportAFC6 match pins.

Both original v75 directories still match every hash in the frozenB1A1
inventory before and after this audit. The new four spans total84 declared
bytes and69 actual changed bytes; complete inverse restores46B3. All old
main-manifest sections except layers/claim_scope remain unchanged; only
shoot_terminal_display_epoch is added, with the earliest runtime deadline
and final-port completion claims still false.

Frozen report: `build/repro-v76-final-audit-20261110/audit.json`, SHA256
130361D12CC96B26EDA90042A832F1D86304C8E725F459AD3AE5B76D1A5EBB5F.
It records every output/source hash and the auditor's identity.

No partial outputs, build execution, emulator, old semantic suite,
save/State, main edit or Git operation occurred in this audit. The v76
ordinary-KO and isolated terminal-mode8 captures are separate evidence.
