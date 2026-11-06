# Observed ordinary-input chase trap

Read-only inspection of the active short-hard capture identifies a basic chase trap during the first stage1 bout. It does not establish that an orb is unreachable. The active E382 wrapper, frozen dependencies, emulator and game memory were not changed.

At relative frames18600,18900,19200 and19500, P1 X is02E0 while P2 X is0060. The sampled Y pairs are respectively1100/02C3,1100/057B,0F74/05A2 and1100/02BA. Scores remain4 versus8 and both HP values remain8. These are discrete samples, not proof that X never moved between them.

The input log holds X4 and pulses A for8 frames every90 frames throughout the sustained part of this interval: examples18000..18008,18090..18098,18720..18728 and19530..19538. That is the frozen basic chase cadence. The collector's distinct cadence is5 frames every45 core frames, seen earlier at17459..17464 and17504..17509. Therefore the long stall is not explained by continuous orb-collector override. The large vertical separation keeps the chase's B eligibility test false; the stationary fallback only repeats jumps while still holding toward the same obstruction.

`collect.txt` logs a slot1 selection at core17423 and another at20088, but it records only target-slot changes. Silence between those entries does not prove a fixed orb remained selected or stationary. The input cadence is the stronger discriminator.

For a future ordinary-input revision **after the current bounded run's outcome**, a minimal recovery is a finite back-away phase when repeated X samples show negligible progress and vertical separation remains large: release the wall-facing direction, move the opposite way for a bounded interval, issue one jump edge, then resume chase with a cooldown. This changes the observed failed input sequence without writing game state. It is a proposed escape attempt, not a proven route to the opponent; the logs do not identify enough stage1 terrain geometry to justify a path planner. No recovery wrapper or new long run was created.

The frozen excerpt fixture is `build/shoot-host-trap-20261106/fixture.json`; it contains the observed17700..19718 input/state lines and the two relevant collector entries. It deliberately does not hash the entire still-growing capture file or claim a final campaign result.
