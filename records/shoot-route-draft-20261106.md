# Shoot source-correct route draft — 2026-11-06

Completed the interrupted route draft against the exact resident-caller image
`9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738`.
The external build gate remains `INPUT_SHA256=None`. No ROM was emitted and
neither external allocation/progress hook was changed.

## Correct default callback

Source case 5 selects `71F0:0653` on the ordinary branch. That callback itself
checks stage 11 at raw `772564`, calls `71F0:1750` and returns. The old draft's
direct default `0834059C` bypassed this source terminal dispatch. The draft now
selects the already verified resident router `086FC300`; its stage-11 path
selects resident `085CD000`, and its other path preserves `0834059C`.
The initial stage/difficulty/progress selection and single existing allocation
remain unchanged. The initializer dependency is the actual `08629800` body,
not the obsolete `085C7800` location.

Both dependencies are exact size/hash contracts. The independent verifier
checks the actual terminal router, its stage-byte owner, both restored-stack
and restored-flags continuations, and the raw source compare/call/return.
It inverses the one changed selector literal to the earlier reviewed complete
code profile. It never imports the builder.

## Frozen checks

Fresh runs `build/shoot-route-draft-20261106-b` and `-c` have byte-identical
`dependencies.json`, `draft.json`, and `verified.json`. The draft contains two
code records, 188 bytes / 36 ARM instructions. Its in-memory image is used only
for verification; no patched image file is written.

- 131,072 selector combinations and 262,144 complete progress-word cases pass.
- Twelve direct negative controls reject seven code mutations, two obsolete
  dependencies, and three source terminal stage/target/return mutations.
- Five CLI checks reject ordinary emission while gated, a ROM output supplied
  to draft mode, missing ordinary output, an existing manifest and an existing
  verifier output. Existing output bytes remain untouched; rejected commands
  create no ROM or new manifest.
- The same final tools pass Python compilation.

| File | SHA-256 |
|---|---|
| Builder | `6E431B580F24E59B2114E3378CE9B927810F669844E5218D5962A3281F0D9263` |
| Independent verifier | `7FCFEB897F0D29D97DC25086D9BFD75A45F022C311168C2782425BDE010FEE36` |
| Dependencies | `33D8693091EA866FFB41C95838B9ADB48128EBE14CF1945FBC0D41D3D92B945F` |
| Draft code records | `CD7F38BC80557BC2B060D59FFD1B1E0C42A16AA1088AEEC198794C02C51F1377` |
| Independent verification | `D6B8F047A0193A29A4E5D376A46CE5AE11D3635C019D5C9C08C1811E6458393D` |

Commands use the existing resident-caller ROM, the three immutable originals,
and the dependency file:

```text
python tools/build_shoot_scene_route.py BEFORE GBA WSC10 WSC15 DEPENDENCIES --manifest DRAFT_JSON --draft-proof
python tools/verify_shoot_scene_route.py BEFORE DRAFT_JSON GBA WSC10 WSC15 DEPENDENCIES --output REPORT_JSON --draft-proof
```

## Terminal scope and withdrawn lead

A review of the original terminal generator initially suggested missing
`193B -> 197A` same-invocation fallthrough. Checking every caller and the actual
current image showed that v54 already repairs it: `5CD290` contains
`5AF300EA` (`B 0860A000`), and the 12-byte body at `60A000` calls `08012008`,
then `085CD2B0`, then branches to the inherited epilogue `085CD294`.
Its current payload hash is
`BE5A29E023BA174209198F78C584EBAD5F06A0FDE2E759FF5CC8FAC3CAC8176B`.
The existing spatial repair verifier already checks this behavior. The
suspected new defect is withdrawn; no duplicate repair was added.

Actual `197A` BX destination ownership, the low-Y branch's actor motion,
post-ground camera/refill lifetime and final IRQ/common-tile visibility remain
separate unresolved contracts. In particular, `182F` unsigned Y<=0C00 bypasses
`193B`'s grounded wait and cannot inherit a post-ground stationarity claim.
No wider graphics projection, clamp, omitted clear, emulator execution, supplied
save access, or guest write was used here. The draft is not enabled gameplay.
