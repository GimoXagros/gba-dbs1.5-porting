# Completed v75 fresh-build inventory audit

PASS after root confirmed both fresh build processes exited zero.
`build/repro-v75-20261110-a` and `build/repro-v75-20261110-b` contain
exactly 307 files with identical relative paths and complete SHA256 hashes.
All 119 asset/layer manifest entries were independently recomputed in both.

The completed v74 audit remains bound by SHA256
02DAA8035A04909CD0277410944D1052FA4A0423CDA6E31C8319FBAF4483DDE6.
Both complete v74 inventories remain unchanged before and after this audit.
Every one of the 301 old paths is retained; only build-manifest.json,
current-candidate.gba and current-candidate.json change in the new output.
Six paths are added: the preserved child-rectangle ROM/manifest, palette-call
ROM/manifest, and the two new capture-free production verification reports.

The exact original v74 final1477 ROM and rectangle manifest are preserved.
The new chain is 1477 → FF3A → 46B3. Manifest old/new word values match the
actual complete ROMs. Both per-layer inverses and the complete inverse to
1477 pass: five disjoint four-byte spans, 20 declared bytes, 13 changed bytes.
The existing v74 194-byte declared changes remain intact. Six mutations
outside the five new spans are rejected in each build.

All old manifest fields except claim_scope/layers remain identical. The
two new palette-call/terminal-owner sections match frozen main literals.
The 94F9 palette and 8CE3 owner production reports match their exact pins.
Main F5CD and generic inverse verifier C317 are explicitly pinned; all
other inherited source pins remain checked. Both fresh inventories and
source pins remained unchanged throughout the audit.

The frozen result is `build/repro-v75-final-audit-20261110/audit.json`, SHA256
B1A1B933658967298554D12FBDF1D565AB75A27C31A82E4565B7BD2FAEE4FC08.
The report records the auditor's own hash and every source/output hash.

No partial build output was read. No full build, old component semantic
suite, emulator, save/State access, main/ROM modification or Git command
was performed. Ordinary KO capture has its separate v75 audit; terminal
acceptance, IRQ and final-port completion remain separate gates.
