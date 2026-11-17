# Character AI main integration and build inventory

The main integration is frozen at
`BADCCD5949EBBD04C8AF2DF4FAD20D8868DD492061F3079E0E16A80B08B948A6`.
New checker `tools/verify_character_ai_main_inventory.py` is frozen at
`C3E6A9AD45CAF7328A4D3025EE6F056CB3AA80D382D4FF62918822E77F07E579`.
It reads files without importing the AI builder, executing a full build,
launching an emulator, changing main, or using Git. The same author wrote
the isolated AI layer and this integration checker; the separate native
consumer/source verifier supplies the independent semantic gate below.

## Completed main preflight

`build/character-ai-main-inventory-20261117/preflight.json` reports
`CHARACTER_AI_MAIN_PREFLIGHT_PASS`, original exit0, SHA-256
`8C8121E2FFFCBCA9F7B0DF5BFD4621EAF598FD961274CBC78BF944B760DBE689`.

The checker parses the new main bindings, builder and verifier calls, all
six owner arguments, independent verification gate and bounded metadata.
Removing exactly the new statements/metadata and reversing the predecessor
retargets reconstructs the complete previous main byte-for-byte:
`1665CA2BD6E562662577A6102F8F2656946E0E92B53836576E9ACCFC37BD0A1B`.
This preserves every prior call, gate, metadata section and scope sentence.

The predecessor75BD is retained as `character-type8-tables.gba/json`.
The new current candidate is
`DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98`,
with manifest
`2645FA80910F747BEB4A07239645449536BCFA51652194D191749CF03DF063B3`.
Independent native verifier `tools/verify_character_ai_tables.py` is
`2A7FA8725CCF3BDD396060AA6A78DD83D9A22370618990DC1D1937A65C5237A1`;
its frozen report `build/character-ai-independent-final-20261117/report.json`
is `B1B21A1C119028B2EBD70602BCCB82F6580CF02A38932E69EB58187A7B885FC7`.
The main requires that exact gate.

The whole DEEE image is reconstructed independently from original WSC1.5
parameter/behavior/action slices, a literal reviewed helper encoding, the
branch encoding, and all23 table-pointer redirects. The commercial action42
mask exception007E is retained explicitly. All28 declared ranges match the
manifest:8890 declared bytes and8128 changed bytes. Reversing them restores
the complete75BD image, including untouched padding and every earlier layer.
The source ROM is read from the current user's Downloads/JUS directory and
pinned toC415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7.
This reconstruction is an integration/inverse check, not another gameplay
or prior semantic-suite execution.

All inherited source/tool hashes and frozen isolated artifacts remain exact.
Both historical337-file inventories are compared against completed audit
`build/type8-main-inventory-20261117/final.json`, SHA-256
`B00CFE9AE706A660C6A4DCFA61123440E0DD9B1EC9074C92D7D273727C4776F9`.
They remain unchanged.

## Pending fresh builds

Root will schedule two fresh full builds after the separate positive DEEE
runtime gate. No new build completion or340-file inventory is claimed yet.
The expected final closure is340 files and130 manifest entries per build,
with exactly these three new relative paths:

- `character-type8-tables.gba`
- `character-type8-tables.json`
- `intermediate/character-ai-tables-verification.json`

Only the shared `build-manifest.json` and `current-candidate.gba/json` may
change. The final audit requires identical complete inventories, all130
actual manifest hashes, both whole-ROM inverses and unchanged historical
inventories before and after checking. The one new metadata section must
state8890/8128/0RAM, preserve the action42 source/native exception, and keep
actual-runtime/full-campaign/final-completion claims false. All previous
metadata must remain equal.

After root confirms both original build sessions exited0, run the frozen
checker with `--root-completed --build-a <fresh-a> --build-b <fresh-b>` and
`--report build/character-ai-main-inventory-20261117/final.json`.
The checker requires distinct fresh directories and a new report path.
This deterministic build inventory does not establish campaign completion
or substitute for the separately reviewed positive runtime capture.

## Completed two-build inventory

Root confirmed both original full-build sessions24029 and82171 exited0 for `build/repro-v82-20261117-a` and `-b`. Root then ran the frozen checker in original session31652, exit0. Final report `build/character-ai-main-inventory-20261117/final.json` SHA-256 `83C5AF9A71EFBE9771C318690E7C75AAF422EF232D55B35D0CDE0528C7896855` reports `CHARACTER_AI_TWO_BUILD_INVENTORY_PASS`:340 files and130 manifest entries in each fresh build, complete matching inventories, all historical337 files preserved as specified, and exact whole-main and component inverses. This completes the formerly pending inventory step above.

This is the historical DEEE/BADCCD deterministic checkpoint. Subsequent actual ARM7 execution exposed odd-address LDRH rotation in the source17-byte parameter rows; the earlier static Machine used flat memory reads and therefore overstated source-halfword parity. A separate aligned18-byte layout layer is being reviewed, and Iraira graphics require a separate source repair. The unchanged historical inventory proves repeatable bytes, not complete source parity or visual correctness. No frozen checker, prior gate, ROM, main, or build output was rewritten to hide that limitation.
