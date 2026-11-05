# Shoot resident scene connection — 2026-11-05

The translated scene now calls the real source-ordered initializer directly at
`085C853C -> 08629800`. This is a resident scene component over exact v65;
the normal game cannot enter it yet. The external case-5 route and controller
boundary remain gated. No emulator, supplied save, guest-memory write, or
runtime proof was used for this component.

## Exact component and reproducibility

| Item | SHA-256 |
|---|---|
| v65 predecessor | `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46` |
| Resident scene ROM | `428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281` |
| Builder manifest | `64A64E4D6707E3FA2A9A75F734C34F22611B6986424D80971CAAA1C1E6873824` |
| Dependencies JSON | `FB046AEC736302303855126CA550F62952E5BF82C288B9813D0FD73E142FBFA6` |
| Final verifier report | `AC1D7CCFBC2753D1439B2AFCA364240F7AFC0D26C1E030860898B82ED99DD15D` |
| Scene builder | `05ED0259FFC5FDC85957342518F11BB891D6A05912C728CEDF68B906A89ADCBF` |
| Scene verifier | `C0DDEDA8F011C81EDFE2268479D5352C64080B330080C1309853490FBBF0A51D` |

Fresh component directories are `build/shoot-scene-resident-20261105-a` and
`-b`. Their `scene.gba`, `manifest.json`, `dependencies.json`, and
`independent-verification-final.json` are byte-identical. The earlier report
in A is retained as superseded evidence, not counted as the final checker.

The builder emits 22 placements, 3,032 declared bytes and 2,948 changed bytes.
The independent checker decodes all 648 ARM instructions, checks 15 semantic
negative controls and six ownership negative controls, and reverses all
placements to recover the entire predecessor. Its source/resource checks
remain separate from the builder: it imports no builder or converter and
does not consume the builder manifest. The implementing agent adapted this
previously independently authored checker; root final-artifact review remains
a separate review step.

The initializer dependency is exactly `08629800`, 140 bytes, SHA-256
`8FEDEC3D4115A92339E37D1F78CAC2A1DE4A435A074CF641339FF22EC90B5F13`.
Both builders' contract checks reject the obsolete `085C7800` entry, a shorter
body, or a changed body fingerprint. The scene builder also pins the complete
v65 predecessor, so a caller-provided manifest cannot accept changed palette
or other resident dependencies. Its CLI and the checker reject existing output
paths before reading ROM inputs.

## Preserved ownership and exact old-profile inversion

The former draft reserved all of `5C8000..5CA000`. Current v65 has four
branch-like words whose target addresses lie inside that window:

| Existing raw word location | Raw target |
|---|---|
| `60C730` | `5C872C` |
| `60C770` | `5C86EC` |
| `60C7B0` | `5C8734` |
| `60C7F0` | `5C87F4` |

Two destinations overlap the old proposed hold phase. Their roles are not
guessed or dismissed. Source phase `12C6` moves from `085C8700` to `085C9B00`;
every candidate word and destination remains byte-for-byte unchanged. All
other placements retain the old draft addresses. Ownership scans cover exact
emitted intervals, and every enclosing gap remains unchanged by the full
inverse check. These are finite aligned-pointer/ARM-encoding checks, not a
proof excluding arbitrary computed aliases.

The checker reconstructs three complete original reviewed profiles:

- `11F7`: reverse only the initializer BL target to its former draft target.
- `1267`: reverse only the hold callback literal to `085C8700`.
- `12C6`: reverse the three external BL relocations to the old placement.

Their original full profile hashes match exactly after those reversals. Thus
relocation and the actual initializer call are the only executable changes
relative to those old profiles. Remaining profiles match their original hashes.

## Source order, ABI and gates

The scene uses the native current-task ABI and preserves `r0-r12`, LR and SP.
The initializer independently preserves that same register set. The call is
direct and keeps the scene's `r4` task-data pointer valid; no wrapper is added.
The source immediate fallthrough edges and counters remain unchanged.

`1043` invokes `085C9500`, which calls snapshot `085C1900` before its first
destructive hardware palette write. The earlier `0203F000` write clears a
source-derived counter, not the canonical palette mirror. The saved palette
is consumed through `1331`, before the input and battle callbacks are restored
in `1540`. The existing normal-battle, single-scene-owner proof is documented
in [scene ownership](shoot-scene-ownership.md) and the retained fighter/auxiliary
pool proof in [object survival](shoot-scene-object-pools.md). This component
does not turn those conditional invariants into arbitrary-entry safety.

The route builder's dependency entry now agrees with `08629800` and its exact
140-byte body. An explicit unpinned-predecessor gate prevents it from emitting
an externally reachable scene. The controller adapter retains its existing
unpinned gate and `085C0A00` remains `BX LR`. Its existing 44-byte adapter,
SELECT/APPLY/table and complete 6,432-byte lower-family fingerprints still
match the v65 predecessor; none needs reimplementation just to connect them.

Before opening those gates, the remaining actual source storage observers,
terminal camera/row ownership, interrupted-DI IRQ behavior and lower pursuit
`8EF3` reachable domain must be established. The existing pursuit helper's
signed target-Y `<=1B00` and current-X `<1E00` preconditions cannot be waived
by its idle return outside that domain. No clamp, rollback or fallback change
was introduced. Main integration, runtime behavior, full Shoot playability,
language completion and hardware QA are outside this component's claim.

## Final main-build audit

Both complete fresh main builds, `build/repro-v66-20261105-a` and `-b`,
finished with the exact scene ROM above. A separate read-only audit recomputed
all 259 relative paths and hashes in each directory and compared them with the
parent's comparison report. All files match. Comparison report SHA-256:
`A7D7DAC45B1B4636A40954C245D776FD3D6F0C2F3FBFD37606C2C12E5DDAA9A5`;
build manifest SHA-256:
`CF8EEAEBEB8EB92E26DBC391F0D9247B41FA6CB81D8E6C80C073659268FF9A04`.

The audit reran the independent scene verifier against the actual main-build
final image and original ROMs, obtaining the exact recorded report again. It
also independently reversed the 22 placements to the complete original v65
image, checked identical scene manifest/dependencies against the component,
and confirmed unchanged external route, progress, controller and damage-hook
words plus the all-FF old initializer slot. This is more than final-hash equality.

Audit artifact: `build/repro-v66-final-audit-20261105/audit.json`, SHA-256
`FF3B019C0BB9B67B27B87B2A916A32EEDAB155F07FB4F7BE8E95F94B9D349F0D`.
It adds no runtime, active scene entry or lifetime-gate claim.
