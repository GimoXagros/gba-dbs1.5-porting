# Shoot player action and landing domain — 2026-11-05

## Result and exact scope

The finite character action population is now checked against the immutable source: **30 base/evolved resources, 607 indexed action rows, and all 35 end-type-2 landing rows**. None enables the generic parent-coordinate rewrite. Every checked end-type-2 landing successor starts with zero or upward vertical motion; ordinary landing stops both velocity and acceleration. The complete source Shoot collision grid equals the v67 native grid and contains no material/conveyor metadata.

These are positive source properties, not a complete invariant for every reachable fighter callback. The checker deliberately reports `complete_player_domain_proved:false`. It does not justify enabling the external caller or accepting the existing out-of-domain idle fallback as gameplay. No ROM, builder, guest state, save, input policy, or emulator process was modified by this work.

## Frozen inputs and reproduction

Baseline: `9dbfab9669f673bcecad6f15c17287f951250a76` / v67.

| Artifact | SHA-256 |
|---|---|
| Original WSC `Digimon Tamers - Battle Spirit Ver 1.5.wsc` | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| `build/repro-v67-20261105-a/current-candidate.gba` | `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F` |
| `tools/analyze_shoot_player_domain.py` | `9317949258F182498CC266704FEDA301AE8D94E00BCE26BDFF83AEC567D9875D` |
| `build/shoot-player-domain-20261105/evidence.json` | `651A4B612A75BFFF8F2C20354929AC5879282346C04BFCD3E75FAAC8D8BF0CFB` |

From the repository root:

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 tools/analyze_shoot_player_domain.py 'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' build/repro-v67-20261105-a/current-candidate.gba --output build/shoot-player-domain-20261105/evidence.json
```

Observed result: `PASS607 action rows, 35 landing transitions, full no-force grid; whole-route ownership remains explicit`. Four in-memory negative controls are rejected: parent-attach action flag, ordinary landing branch mutation, type-11 dispatch ownership mutation, and grid metadata mutation. They do not modify either ROM. The analyzer imports the existing lifetime analyzer's exact-instruction and hash helpers; vendor Capstone is the existing decoder dependency.

## Proven finite consumers

Addresses below are raw WSC offsets unless written as segment:offset. Constructor `743811..743826` loads each character action triple from the base/evolved table and calls `80EA:0000`. `780EC8` resolves the indexed action pointer from actor `+64/+66/+68`. The checker follows all 15 identities in both forms; each resource's count, contiguous 36-byte rows, seven internal links, motion selector and end selector are validated. Resource hashes are included individually in the JSON.

The direct generic parent X/Y writer at `781503/78150B` requires descriptor `+A` bit `20` through `781480`. None of the 607 rows sets it. This excludes that particular writer for these resources; it does not exclude the separate grabbed-victim callback or every external coordinate writer.

Generic action update `80EA:0482` checks downward velocity and airborne state at `781648`. Fighter kinds 0..2 use ordinary landing `668E:03C3`, except end type 2. End type 2 instead tests the same collision low bits at `7818EF`, clears airborne, and enters completion. The checker follows the actual completion links (`+16`, plus `+18/+1A` when enabled). All 35 rows have only native-idle outcomes or successors without pre-motion redirects, inherited/additive vertical motion, or vertical homing. Their decoded motion assignments produce `vy + ay <= 0`; zero vertical velocity also has zero vertical acceleration. This proves the immediate landing transition, not an unbounded trajectory after arbitrary future inputs.

Ordinary landing `766CA3` checks actor `+48 & 3`; the normal material branch `766E62..766E8E` zeros actor `+32/+34/+36/+38` and installs `668E:1D5E`. Neutral idle initializer `668E:113C` also zeros all four fields before `115D`. The specialized flight descent at `785773` calls native idle on the same collision bits; its explicit upward coordinate correction at `78572B..785737` is to Y=`0200`, not an out-of-world downward write.

The full 56×54 grid at source `33CA20` equals native `08607000`. All 3,024 first halfwords are only 0/1/2/3; all second halfwords are zero. Thus the landing material-kind-4 exception cannot be selected from this grid, and no conveyor/material field can introduce motion. Central columns 24..32 have type 2 at row 42 (336 pixels), type 1 at row 50 (400 pixels), and type 3 at rows 51..53. Landing alone therefore does **not** establish a camera-compatible Y of at most 192 pixels. All 15 base fighter stat rows have collision radius 6 and height 30; this statement is intentionally limited to the checked base stat rows.

The two apparent terrain-disable writes at `760E69/760E82` are dispatched through `76006F` by the attack-side actor's low kind nibble. Only type 11 reaches this handler. They therefore do not clear terrain for ordinary player kinds 0..2 or lower kind 6. This is a positive type-dispatch exclusion, not a literal-opcode absence claim.

## Actual scene interval and outstanding ownership

The accepted player reset installs flags `E700/0040/0000/0000`, current/previous X=`0E00`, and current/previous Y=`FF80`. Scene `1331` clears freeze, `139C` waits for ground, and `1540` restores ordinary input `4090:07FA` and battle `4090:0D0B`. The input dispatch's kind-2 branch skips assignment of ordinary enemy AI input, but P1 retains full held/edge controls. There is no established Shoot-only restriction that removes all ordinary player attacks.

The following remain positive proof obligations before the earlier conditional lower-domain result becomes a whole-route result:

1. Exclude or model the actual grabbed-victim callback `5FFD:2D78`. Its write at `762D92` can clear terrain for a fighter; calling this merely a child-object path would be incorrect. The kind-2 input branch skips ordinary enemy AI assignment, but that alone does not prove every boss-input/damage writer is absent.
2. Close drop-through, sidewall and later action trajectories, including external displacement owners. Downward collision `76FD6B` integrates the current delta and zeroes the delta; it does not snap Y to the floor. The newly proved landing transitions are necessary to stop later penetration, but do not by themselves prove all prior or subsequent callback transitions.
3. Close exclusive lower movement ownership through its target capture (`7496A6..7496AC`) and selector `4090:8EF3`. Reuse the existing finite lower-X result in `records/shoot-spatial-independent-20261105.md` and `tools/analyze_shoot_pursuit_bounds.py`; do not replace its explicit assumptions with an unconditional claim.

Terminal neutral-player ownership is a narrower, separate interval: the scene agent positively identified that terminal battle callback `4090:0B8B` omits ordinary `0D0B` attack/victim and body-push calls. The no-force grid and zero-motion landing facts here can be consumed by that terminal proof. Those omissions must not be applied retroactively to the pursuit interval after `1540`, which restores `0D0B`.

## Implementation consequence

No source-correct native repair follows from these facts alone. In particular, deleting the existing `signed X < 1E00` / `signed captured Y <= 1B00` guard in `tools/build_shoot_lower_rules.py` would expose selector behavior outside the currently translated source table domain; retaining an artificial idle there is not a completed port either. The immediate integration product is the frozen source-action/landing evidence above. The concrete remaining route work is to bind actual kind-2 boss/player callback ownership and target-capture trajectories, then either remove a proved unreachable guard or translate the identified reachable source path. A coordinate clamp or invented idle transition is not proposed.

The read-only source campaign owned by the root agent may provide discriminating actual callbacks. A finite runtime trace cannot by itself prove their exhaustive absence. Storage consumers, IRQ/terminal DI lifetime, terminal camera handling and final external entry integration remain their respective owners' scope.
