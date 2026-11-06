# Shoot controller producer assessment — OPEN_DOMAIN

The combined source assessment is reproducible from the immutable WSC1.5 and exact v68 candidate. It explicitly reports `complete_controller_input_domain=false` and `external_scene_entry_authorized=false`. It is evidence for reviewing an internal resident connection while the external scene route stays unchanged; it does not authorize actual Shoot entry.

Run `tools/analyze_shoot_controller_domain.py SOURCE.wsc V68.gba --output FRESH.json`. The checker reads tracked source components and the supplied originals/candidate, not ignored evidence files. Final checker SHA256 is `7C14BFDED19A93C7CA69351A7BFFA70A28CD1C5FE84E09678C40E8B012A277CD`. The fresh result `build/shoot-controller-domain-20261106/open-b.json` has SHA256 `5DBB2620877D5ADEE92338B87B285610914CA07F2C484077846A602EDA707B46`. Four direct contract mutations are rejected, in addition to the opponent/drop component mutations. All four new player-owned Python components compile.

## Closed components and their scope

- `analyze_shoot_opponent_controls.py` (`30052414FDC255B5E553ED23243956A30933C8D4A4D72574A16622DB8B330F64`) pins the actual reused opponent as kind3, initialized held/edge zero. Mode2 input/link dispatch bypasses input assignment; the finite boss, borrowed, freeze and damage callback families preserve zero controls. Root independently reviewed the orb and visual child ownership. P1's grabbed-victim entry requires the other actor's nonzero horizontal held bits, so that entry is excluded under these audited owners. This is not an assertion that no opponent attack or auxiliary hit can occur.
- `analyze_shoot_drop_path.py` (`73749E10126AE7B2CF2EBAA7318D065E330378F082CC1F5636F359BCB0DA8314`) covers all30 base/evolved stat records and radius6/heights30,48,56. Actual positive-Y drop support excludes the solid sidewalls. The finite interior check covers1,321,920 horizontal cases and73,728 vertical transitions; the maximum first drop step is143 and final supported-row continuation reaches at most5902, before the bottom6400 barrier. The empty-gap callback clears drop-through before another collision. General airborne motion outside this positive-Y interior contract remains separate.
- The unchanged607-row action checker proves no generic parent-X/Y attachment descriptor and validates35 landing successor rows. It does not exclude the distinct direct-X shift at7819CD or input/hit exits from every landing-wait state.
- Lower tracking initialization clears hit/body production bits6000. The actual pair body-push call uses065C/065E, excluding lower071E. Accepted lower damage retires tracking; linked kind3 freeze marks the lower object to skip horizontal wiggle and preserves its tracking timer/motion together. The combined report pins these positive owners.
- Existing independent pursuit evidence remains conditional:5,462,663 states,245 updates, signed lowerX−5839..7198, provided P1 targets remain0..7167 and the stated motion/timing owners hold. That expensive completed calculation was not repeated. Its checker and independent record are pinned by hash.

## Why the whole domain remains open

The source's small-motion phase guard allows a solid-wall corner to snap outside the tempting horizontal envelopes. The independently checked example is7009→7136→7137→7264→7265→7392 for deltas−1,+1,−1,+1,−1. These are instruction-model counterstates, not a demonstrated normal-input trajectory. Therefore neither a full-footprint interval nor the looser0..7199 interval is an unconditional invariant. A reachable coupled X/Y argument is still required.

Velocity becomes world-coordinate displacement through source742322/742325 `SAR4`. This gives useful finite ascent bounds for individual jumps and launches, but counting one aerial attack is insufficient. Base14 action19 is an endtype2 landing wait with a key exit to22. A fresh hit during22 can take22→18→20→19 and enable another22. Source781904 enters the shared transition logic before landing; the combined checker pins this cycle. Action23 instead has no such key/hit exit. Actual hit target positions and auxiliary lifetimes must be correlated before limiting repetitions.

The complete607-row inventory also identifies one direct-X shift: base4 action30 at3BCA7A, with descriptor+D bit08 and value24; source7819CD moves X by facing-signed384 coordinate units. Its actual wall-action/material6 entry ownership remains a separate positive reachability obligation. The generic parent-copy exclusion does not cover this writer.

No whole-player nonnegativeY, capturedY upper bound, or unconditional lower selector domain is claimed. No ROM, main builder, emulator, supplied save or guest memory was changed by this assessment.

## Separate camera component

`analyze_shoot_camera_step_bounds.py` is frozen at `200D8681881D02FD97E5D219AF8951EE3C5502B029284695FD16E9CFD0A5BE48`. Its147,968 source camera substeps and four mutations establish the height3/nonwrapping, reset-at-zero local camera range0..288. Actual caller ownership, stage shake, terminal branch reachability and graphics lifetimes remain separate. It is not used to claim the controller input domain closed.
