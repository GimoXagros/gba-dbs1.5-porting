# Source collector v2 read-only audit — 2026-11-05

The revised ordinary-input selector correctly uses source object kind `flags & 0xF`, the allocated task's payload at `header + 0x10`, and the collectible's owner byte at payload `+0x10`. This audit reads the frozen wrapper/base scripts, original source ROM and root-owned run `build/bizhawk-wsc-lifetime-20261105-l` artifacts. It does not run or alter an emulator, supplied save, guest state or active script.

| Frozen input | SHA-256 |
|---|---|
| `tools/bizhawk_probe_wsc_shoot_collect_v2.lua` | `2AD5BB33BB5FA85A654E5A36ECDF002195076CC85FB62C4E7A7033797BA37A17` |
| Included `tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua` | `0CC9B17CAE00E7B7EFA33976788B1A66F595F15473EE78A597A77ADF68F42D69` |
| Run l full `loaded-rom.bin` | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |

Source allocator `74204E/742051` selects flags `1000:0640` and fifteen pool-0 slots. It finds free flag `FF`, marks allocation zero, retrieves the header via `060C + 2*slot` at `742081..742090`, and adds `10` at `7420A3`. The wrapper scans exactly slots 0..14, rejects `FF`, validates header alignment and the normal task-slot envelope, and reads `C000+header+10`. Its “active” test is per-slot allocation status, not the aggregate `0658` count. It correctly avoids treating the scheduler header as the actor payload.

At pickup source `742A79` resolves the collision-row actor, `742A7B` loads actor flags and `742A7E` masks `000F`. At `742B48..742B5A` an owner byte different from the collector's `+10` increments collector score `+52`, capped at `FA`. Same-owner behavior in kind 2 instead reaches the linked actor HP increment at `742B6F/742B72`. The wrapper's target-owner inequality therefore has a positive point-award consumer; it is not inferred from `+12/+14` linked handles. Its three small built-in selector assertions cover enemy-owner preference, no eligible owner, and weighted nearest choice.

The superseded k wrapper used `%128 == 7`. Flags `9317` have low kind 7 but fail that filter. Root detected this input-policy error and stopped k; k is not evidence that the corrected collection route failed. The v2 wrapper uses `%16 == 7`. Both versions changed only ordinary joypad choices, not gameplay memory.

The wrapper overrides only normal battle mode 7 outside stage 11, choosing horizontal approach, brief jump when the selected collectible is above P1, and no attack while a target exists. The underlying hard-mode UI/chase policy remains the fallback. The seven extra terminal hooks only read registers/memory and write host log/dump files. Their `on_bus_write` use is the existing hash-guarded BizHawk 2.11.1 execute-callback adaptation, not a guest write. The launcher checks the exact executable and both core DLLs, the base-script hash, fresh output paths, disabled save autoload/background physical input, and a 900-second bound. The wrapper and included base contain no memory/register/state setter.

At audit time l remained in progress: launch contained the initial manifest, without completion/final unchanged fields. Its full loaded ROM independently matched the original hash, its current wrapper hash matched the launch hash, and `collect.txt` contained positive target choices through frame 19954. The source-appropriate pool decoding was also checked against the immutable frame-9000 snapshots (slot 0 header `0234` resolves payload `0244`, callback `4090:4C13`, flags `0029`, and is correctly excluded as kind 9). This is not a claim of final completion, Shoot entry, score improvement, universal callback ownership, or absence of storage/IRQ activity. Final launch status and calibration totals must be read after root's bounded run ends.

Remaining policy limits: distance is a heuristic, not pathfinding; allocation/type/owner alone does not guarantee a collectible is currently reachable or collision-enabled. The collector wrapper can also intercept the base script's final key-release call while mode 7 remains active; no further frame is advanced before exit, so it does not fabricate gameplay, but that call should not be described as independently verified all-buttons-release. No active script was edited to change these limitations.

## Independent terminal-checker rerun

Independently ran frozen `tools/analyze_shoot_terminal_lifetime.py` (SHA `DD760E9426C12D0C89F01CE1259C1E006D5A9662C3BD6ED1957B8F914E09BF3B`) against the original WSC into fresh `build/shoot-terminal-lifetime-20261105/evidence-independent.json`. It passed, reproducing the sibling's final evidence SHA `E26DB8A79B215058DFFA6ECF9498870B1236BE9BEDA49F9B2262C37B5E9E3B4E`.

Reviewed the actual exact-instruction contracts and complete 0B8B call population. The conditional conclusions are appropriately narrow: current/previous coordinate equality skips the battle camera update; stage 0400 clears BG1 while ongoing shake updates BG0; terminal flag20 suppresses the timer scroll consumer; ordinary hit/pair/bodypush calls are absent from the scene battle root. The checker still explicitly leaves actor stationarity, actual terminal BX/DI lifetime, common tile-zero preservation and external entry open. Its algebraic equality cases and semantic mutation negatives must not be reported as a complete post-ground player lifetime proof or applied to ordinary pursuit callback 0D0B. No changes to the sibling's files were needed.


## 2026-11-06 interruption audit

On resumption neither k nor l had a completion marker or finalized launch report,
and neither owned emulator remained active. k ended at logged frame16118 after
the root stopped its ineffective kind filter. l ended at logged frame50179 when
the work was interrupted. Neither observed a Shoot execution site. Both full
loaded-ROM dumps still match the immutable source. These are partial observations,
not completed90000-frame tests or evidence that the entire source route is safe.
The independent resumption inventory is
`build/resume-interruption-audit-20261106.json`; original launch/trace files were
preserved without inventing completion fields. Do not repeat the same failing
campaign policy as if it were a new discriminator.
