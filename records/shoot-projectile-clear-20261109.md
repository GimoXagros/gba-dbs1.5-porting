# Bounded resident93E7 terminal-clear component

The isolated component extends the existing terminal mask to the exact static93E7 projectile resource at base6D. Its new76-byte selector reuses the frozen renderer, owner, capture and expiration routines. It adds no persistent RAM, texture storage or task. Independent complete-renderer QA is pending; no main/runtime integration is claimed here.

## Exact artifacts

| Artifact | SHA256 |
| --- | --- |
|Input corrected v71 component|35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A|
|Original WSC1.5 source|C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7|
|Builder `tools/build_shoot_projectile_clear.py`|FC1679A216FBF3AD4A0667C1E85EEBFF435437C219F109F628FAB97E4CE782DF|
|Output `build/shoot-projectile-clear-explicit-20261109/component.gba`|025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA|
|Manifest `build/shoot-projectile-clear-explicit-20261109/component.json`|ACF245F90EA2DEA53E03E3872DD3D8474A34F522453319127DB4E9858BA27198|
|Bounded reload proof `build/shoot-projectile-clear-explicit-20261109/reload-proof.json`|2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990|
|Fresh lower graph `build/shoot-projectile-clear-explicit-20261109/lower-graph.json`|37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281|

There are exactly two writes:76bytes at6FF240..6FF28C and4bytes at12C50, changing the renderer pointer from086FEA00 to086FF240. Eighty bytes are declared and73 actually differ. The pointer is the intentional replacement of one previous v71 write; all six remaining v71 code/hook spans are byte-identical. Full-ROM inverse restores the exact35D4 input, including its original renderer pointer.

## Consumer behavior and source contract

The selector recognizes only presentation P0=085DB300, base006D and flag2clear. Every other presentation tails to the existing renderer entry086FEA00. Recognized presentations pushR9 once, fetch the existing terminal mask through owner086FE800, subtract36 only from a nonzero mask, and enter the frozen original renderer body at086FEA50. Its existing epilogue restores that one R9 word and the native dispatcher frame. The retained logical73-based test therefore evaluates logical109-based93E7 tiles without changing any existing renderer bytes. Maskzero stayszero and the four live bits are preserved.

The builder pins the exact reviewed callback-proof report and recomputes its source composition, rather than trusting status booleans alone. It also reruns the frozen alias source/native contracts. Within the retained43-lower/775-upper/790-borrowed normal graph, SECONDkind3 cannot enter generic form reload; the introduction writer has retired. The explicit93E7 preload consequently remains the pixel owner after197A in this bounded subset. Static child creation/events do not restore pixels. No new-child exclusion is assumed.

This does not include side1 companion rendering, arbitrary computed callbacks, source8F24 nonpattern targets or external Shoot entry. Those gates remain closed.93E7's24 tiles are109..132; only109..131 can overlap the scoped retained captures.888B is base137 and is excluded.

## Build checks

The original suggested6FEC88..6FEE00 placement failed the strict scanner and was not used. The actual76-byte span is entirelyFF and has zero incoming references under the unchanged whole-ROM scanner, with no ARM/Thumb exemption. Existing code and mask ABI are pinned explicitly, including original entry086FEA50 and epilogue086FEBDC.

The builder executes actual selector bytes in the frozen ARM interpreter, modeling only the already verified owner's ABI:749 recognition/owner/mask cases pass. All28 captured first-tile values,16 live-bit combinations and24 resource tiles give10,752 matching logical-clear arithmetic cases. Nine direct execution mutations reject wrong base, indexed gate, unmatched destination, saved register, initial mask, zero subtraction, translation, original-body target and exactP0. Four output mutations reject selector/pointer corruption, undeclared writes and frozen-clone changes. These checks are intentionally narrower than the independent verifier's required real-owner/full-renderer execution.

To reproduce, first run `analyze_shoot_rule_callback_graph.py ORIGINAL --output OWN_DIRECTORY/lower-graph.json`. Then run `analyze_shoot_p2_reload_eligibility.py ORIGINAL OWN_DIRECTORY/reload-proof.json --lower-graph OWN_DIRECTORY/lower-graph.json`. Finally run the new builder with corrected35D4 input, original WSC1.5 source, a fresh `.gba` output, required `--reload-proof OWN_DIRECTORY/reload-proof.json`, required `--lower-graph OWN_DIRECTORY/lower-graph.json` and a fresh `--manifest` path. It requires six distinct input/output paths and rejects existing outputs. No shared ignored build file is copied or mutated.

The explicit-input correction supersedes builder28A076E5 and manifest42C1A30E. A fresh graph generated directly from the original source reproduces37BAFE3E, the explicitly selected graph reproduces proof2E96EEEE, and the rebuilt component remains byte-identical025C1C5E. Two additional negative controls reject missing and wrong graph paths, bringing the builder total to15. These use temporary private fixtures and leave the supplied graph unchanged.

Skipped: no emulator, supplied save, guest-memory writes, actual Shoot entry, external route enablement, main build or whole terminal-clear completion. Independent actual owner/full-renderer QA is the integration gate; inherited external/nonpattern and other-clear-owner limitations remain.
