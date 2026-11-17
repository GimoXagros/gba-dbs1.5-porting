# ID13 main wiring and build inventory

The new `tools/verify_id13_main_inventory.py` passes preflight for main builder
`59F43FB5516E1500683A03FD90F197F8FFDDB1CA22A9CE028C0DF9A39C04D10C`.
The report `build/id13-main-inventory-20261117/preflight.json` is
`ABEFFC4BB77BB59B30876422D182FA658A86A8502595761DD4DAD65E58CB5B6E`.

The verifier checks the new production/verifier calls and every argument,
their independent report pin, the intermediate paths, conservative manifest
claims and exact final image hash. Removing those additions, restoring the
two evolution-table output/verifier targets, and reversing the specific
claim-scope sentence reconstructs the complete old CRLF main builder
`07B5A946051F4E823F1AAB9B7A8A1B3D7BC3FD7C29E4AA686C3059EC8E82158C`.
Thus prior production calls and gates are unchanged, rather than merely
sampling a few nearby lines. Read-only Git diff inspection agrees with this
complete inverse; the checker itself does not depend on Git.

The former C91 final image becomes `evolution-transition.gba`, accompanied
by its unchanged `evolution-transition.json`. The old table verifier still
checks that exact C91 layer. The ID13 builder consumes it and produces FBD9
as `current-candidate.gba`; the new independent verifier checks FBD9 and must
produce report `AF427CBB5E7FCD208D20E624CD907DDF4F3A3573408A67AD8272FB198DFFD6C0`.
The verifier's new report path is `intermediate/id13-air-relaunch-verification.json`.

The previous independent v78 inventory report is pinned to
`C59C5FA1B43994A24C6F3851B03A25A658E3C8394EEA1E0CE555BBF1085AF97B`.
All its production-source pins are retained, with only main replaced and the
two new tools added. The frozen isolated C91/FBD9 images, their manifests,
and the independent ID13 report are checked. Reversing the independently
enumerated ten spans restores all 16 MiB of C91: 988 declared bytes and 968
changed bytes, with no change elsewhere.

The expected fresh-build inventory is 328 files and 126 manifest entries.
Exactly three relative paths are added to the prior 325-file inventory.
Only `build-manifest.json`, `current-candidate.gba` and `current-candidate.json`
may differ among shared paths. The added ID13 metadata states that runtime,
wall-clock parity and final port completion are not established by this build
gate; existing metadata is preserved except the exact obsolete aerial-gap
sentence. Runtime evidence is tracked separately.

Full inventory audit requires root's explicit completion of both fresh builds.
It checks both complete file maps for equality, all 126 actual manifest
entries, the three-file difference, each new layer inverse, preserved old
build inventories, and unchanged tools at the end. Preflight does not claim
that those fresh builds have already completed. This auditor launches no
emulator or whole build and reruns no earlier semantic suite.

```text
python tools/verify_id13_main_inventory.py --root-completed \
  --build-a build/<fresh-a> --build-b build/<fresh-b> \
  --report build/<fresh-audit>/audit.json
```

## Completed fresh-build audit

Root confirmed both original full-build processes exited 0 before the final
audit: `build/repro-v79-20261117-a` and `build/repro-v79-20261117-b`.
The inventory checker then exited 0 with `ID13_TWO_BUILD_INVENTORY_PASS`.
Final report `build/id13-main-inventory-20261117/final.json` has SHA-256
`40FF6E21D86C7770C02337A524C6B1CE1074D7D820A02BDD7F5435A8B69900C6`.

Both complete inventories contain the same 328 files and hashes. Every one
of the 126 manifest entries closes against its actual file. Final ROMs are
identical FBD9; both ten-span inverses restore C91 exactly. Relative to each
frozen v78 inventory, only the three declared shared files change and the
three named new paths are added. Both prior 325-file inventories remain
unchanged. The original tool pins and reviewed main builder also remain
unchanged at the end of the audit. No semantic suite, build or emulator was
rerun by this final inventory check.
