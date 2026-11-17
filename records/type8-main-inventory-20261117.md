# Type8 main integration and build inventory

The main integration is frozen at
`1665CA2BD6E562662577A6102F8F2656946E0E92B53836576E9ACCFC37BD0A1B`.
The standalone inventory checker is
`tools/verify_type8_main_inventory.py`, SHA-256
`D81CCF6764A6D77C7D5DDE11756CD19DC10297480DDCFDFCBA785AAC61E9CE15`.
It does not import the type8 builder or execute an emulator or full build.
The same worker authored the data-only builder and this integration checker;
the native layer's independent review is the separate checker and gate below.

## Main preflight

`build/type8-main-inventory-20261117/preflight.json` is PASS, SHA-256
`79BC8136DBC8052E0677D9DD690702F66D326E2A318ECBF12A66ABC3856BBEF0`.

The checker independently parses the new bindings, builder call, verifier
call, all five explicit owner manifests, the verification gate, layer hashes
and bounded metadata claims. Removing the new lines and reversing the two
predecessor retargets reconstructs the complete B820 main byte-for-byte:
`B82099CA9E1257148DF978F35BA763F7B8F78CFECBDFB90679C3ECD1E6A162BC`.
This whole-file inverse preserves every previous call, gate, metadata item
and claim-scope sentence; it is not a selected-string presence check.

The former933C final is now explicitly retained as
`campaign-progress-consumers.gba/json`. The final candidate is75BD, with
the independently reviewed type8 layer. The expected new files are exactly:

- `campaign-progress-consumers.gba`
- `campaign-progress-consumers.json`
- `intermediate/type8-tables-verification.json`

The independently encoded four15-row views and five pointer redirects
reconstruct the entire75BD image. The nine declared ranges contain260 bytes,
of which255 changed. Reverting them reconstructs the complete933C image.
The final type8 manifest is
`06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230`.
The separate native verifier gate is
`0A5EB8355D74AF38C61A90C74ECAD636BDCF6250066C786119DC4EC2513C8896`,
from checker `32699530…`; see
[independent native layer review](character-type8-tables-independent-20261117.md).

Preflight also checks all inherited source/tool hashes, all frozen isolated
components and gates, and both prior334-file build inventories against
the completed campaign inventory `55CEF6F5…`. None changed.

## Fresh builds and final inventory

Root completed independent full builds in `build/repro-v81-20261117-a` and
`build/repro-v81-20261117-b`. Both original sessions91052 and6736 exited0.
Root then executed the frozen checker in original session55624, also exit0.
`build/type8-main-inventory-20261117/final.json` reports
`TYPE8_TWO_BUILD_INVENTORY_PASS`, SHA-256
`B00CFE9AE706A660C6A4DCFA61123440E0DD9B1EC9074C92D7D273727C4776F9`.
The completed inventory is337 files and129 manifest entries per build;
these are verified actual counts. No copied output or old build is accepted
as either fresh build.

The final audit verifies identical complete inventories, the three exact
added paths above, only the existing shared `build-manifest.json` and
`current-candidate.gba/json` changing, all129 actual asset/layer hashes,
both full ROM inverses, and unchanged historical inventories before and
after the audit. Metadata retains the prior campaign scope and keeps the
new runtime/full-campaign/final-completion flags false.

This inventory does not establish campaign completion or repaired runtime
behavior. Those are separate capture and gameplay gates.
The corrected actual run passed the first Train fight but did not exercise
the specifically instrumented evolved-air event16 chain; its counter is
absent. It later stopped in a distinct Waterfall CPU exception. Neither this
inventory nor that partial runtime progress proves actual event16 execution
or a complete campaign.
