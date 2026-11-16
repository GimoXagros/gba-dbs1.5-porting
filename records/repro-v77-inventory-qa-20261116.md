# v77 independent build inventory

PASS. Both fresh builds, `repro-v77-20261110-c` and
`repro-v77-20261110-d`, produced their post-gate completion manifest. The
historical process exit codes are unavailable. The two builds match by
relative path and SHA-256 across all 319 build artifacts. All 123 asset
and ROM-layer manifest entries in each build match the files on disk.

The directories contain 319 and 320 files respectively. The only
extra path is `repro-v77-20261110-d/current-candidate.sav`. Its recorded
modification time is later than the build completion manifest. The
audit counted this path and left the save in place without opening or
hashing it. An independent check of the exclusion confirms that ordinary
extra files appear in the inventory and a save at any other path is rejected.

## Preservation and ROM checks

Both v76 reference builds still match all 310 hashes in the frozen
inventory. v77 retains all 310 relative paths and adds nine. Of the
shared paths, 307 still match byte for byte. The three changes are
`build-manifest.json`, `current-candidate.gba`, and `current-candidate.json`.
The original v76 final ROM and layer manifest are reproduced exactly
as `shoot-display-epoch.gba` and `shoot-display-epoch.json`. The
original v76 build manifest remains in both reference builds.

The display and music layers compose without overlapping writes.
Reversing display in the composed image restores the complete music
image. Reversing music from the standalone and composed images restores
the complete owner and display images respectively, including the
erased expansion. Music declares 104,245 bytes and changes 104,216.
The pause fix declares 24 bytes and changes 23. Reversing it restores
the complete composed image. The production global music-stop
instruction remains present.

The two 16 MiB final ROMs have SHA-256
`C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278`.

## Evidence

- Report `build/repro-v77-final-audit-20261116/audit.json` has SHA-256
  `0EBBA5EFBEA7292990F54E7E138C1527E853BF58047BEF73260B6BBFF352ECFE`.
- Verifier `tools/verify_repro_v77_inventory.py` has SHA-256
  `5BD29DC5F676D012D1CBD793AAA8A9F848F8ED50BEFCA1E7143916DF4E9CAE7A`.
- Frozen v76 inventory has SHA-256
  `130361D12CC96B26EDA90042A832F1D86304C8E725F459AD3AE5B76D1A5EBB5F`.

The audit reused the existing semantic evidence. It performed no
build, emulator run, or save content checks. Gameplay and final port
completion require separate evidence.
