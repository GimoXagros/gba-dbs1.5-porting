# Campaign v80 main wiring and inventory

The new `tools/verify_campaign_main_inventory.py` passes independent preflight
for main builder `B82099CA9E1257148DF978F35BA763F7B8F78CFECBDFB90679C3ECD1E6A162BC`.
Report `build/campaign-main-inventory-20261117/preflight.json` is
`D031679E8C9DB26D7A52065D4D14788006FED7B65393C8E26A69EA32A485F638`.

The checker independently reads main's AST and checks the exact four added
production/verifier calls, every argument, four new path bindings, two pinned
report gates, image hashes and conservative metadata. Removing the additions,
retargeting the previous ID13 builder/verifier to their original final paths,
and reversing the three specific claim-scope edits reproduces the entire
previous CRLF main builder
`59F43FB5516E1500683A03FD90F197F8FFDDB1CA22A9CE028C0DF9A39C04D10C`.
This independently confirms all earlier calls and gates remain intact; it
does not execute or trust the root's integration script as its oracle.

## Exact three-image chain

| Build path | Content SHA-256 prefix | Owner |
|---|---|---|
| `id13-air-relaunch.gba` | FBD9CD19 | Previous complete v79 final image |
| `campaign-stage-progression.gba` | ADBF5D52 | Source default-mode campaign producer/getters |
| `current-candidate.gba` | 933C9434 | Additional progress-indexed AI and decimal HUD consumers |

The ID13 manifest is renamed alongside its unchanged image. The first new
verifier consumes FBD9→ADBF and must reproduce report
`1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0`.
The second consumes ADBF→933C and also receives that first verifier's report,
then must reproduce
`3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84`.
The source mode remains config+25 mask0001 clear; alternate mode, whole
campaign runtime and final port completion are not claimed by main metadata.

The checker pins both isolated images/manifests and both completed reports.
It independently enumerates all 14 producer spans and 29 consumer spans,
compares their exact before/after bytes, and reverses each full 16 MiB image.
The combined delta is 453 declared bytes and 423 actual changed bytes.
Existing fields outside those spans remain identical to FBD9.

## Inventory contract

The completed v79 audit is pinned to
`40FF6E21D86C7770C02337A524C6B1CE1074D7D820A02BDD7F5435A8B69900C6`:
328 files and 126 manifest entries in each prior build. Every production-tool
pin is retained, with the reviewed main replacement and four new campaign
tools. The generic inventory helpers are reused from the frozen, hash-pinned
ID13 inventory checker; its old semantic or main-preflight functions are not
executed.

The predicted new inventory is 334 files and 128 manifest entries. Exactly
six paths are added: the renamed ID13 image/manifest, the campaign producer
image/manifest, and two intermediate verification reports. Only
`build-manifest.json`, `current-candidate.gba` and `current-candidate.json`
may change among shared paths. All old metadata stays identical except the
specific campaign/getter/Train-shake scope wording; one qualified campaign
metadata section is added.

Final audit requires root confirmation that both fresh full builds exited
successfully. It then compares their entire file inventories, closes all 128
manifest entries against actual files, verifies both layer inverses, checks
both old 328-file inventories, and rechecks source pins. Preflight does not
stand in for that final audit. This workstream launches no emulator or whole
build and reruns no completed semantic suite.

```text
python tools/verify_campaign_main_inventory.py --root-completed \
  --build-a build/<fresh-a> --build-b build/<fresh-b> \
  --report build/<fresh-audit>/final.json
```

## Completed fresh-build audit

Root observed original exit code0 from both full-build sessions76521/83520,
using fresh `build/repro-v80-20261117-a` and `-b`. Both completed all producer
and verifier calls with final933C. The independently authored inventory
checker then ran unchanged and exited0 (root session51208).

`build/campaign-main-inventory-20261117/final.json` reports
`CAMPAIGN_TWO_BUILD_INVENTORY_PASS`, SHA-256
`55CEF6F5AA41755446C9B01B534B4A41D141B6436620A89DF96F7FC38113B4B4`.
Both complete334-file maps are identical, and all128 manifest entries close
against their files. There are exactly six added paths and three changed
shared paths relative to v79. Both old328-file inventories and all retained
source pins remain unchanged. Both layer inverses and the combined423-byte
change restore exactFBD9; declared spans total453 bytes. No files were copied
between the fresh builds or from prior output directories.
