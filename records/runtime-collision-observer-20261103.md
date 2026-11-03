# Bounded collision observer repeatability

Date: 2026-11-03. Two parent-owned BizHawk runs reproduced the same bounded
observation on the exact historical v62 candidate `389F56FF...ABD7F1`.
Neither run observed an invalid collision type or dispatch. This is not
a causal repair of the original E5 failure, a full stability result, or
runtime evidence for the current v64 candidate.

## Evidence and identity pins

The completed runs are `build/bizhawk-collision-20261103-a` and `-b`.
Each has its own `launch.json`, `config.json`, trace, and output files.
Both launch manifests report `completed=true`, `loaded_rom_exact=true`,
`script_unchanged=true`, `visible=false`, `physical_background_input=false`,
and no diagnostic guest-memory writes. Their process IDs are 19300 and
15748 respectively. The runner compared each complete `loaded-rom.bin`
against the pinned input ROM, rather than relying on samples.

| Item | SHA-256 |
|---|---|
| Input, isolated `probe.gba`, and complete loaded ROM | `389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1` |
| `local/BizHawk-2.11.1/EmuHawk.exe` | `F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD` |
| `tools/bizhawk_probe_gba_collision.lua` | `7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9` |
| `tools/verify_bizhawk_probe_gba_collision.py` | `74022D6763527EF04169B1CB7625D512BE34C2A8A75B8EC5EBCC222F60FF20F5` |
| `build/run_collision_20261103.py` | `414C771419399A282F129CCD345BE5DB491476305EDEAF1DB9BDD19846F44905` |
| Run A `launch.json` | `AA69831C558598AB8659B753AFB3F096D554FD312EF3F80203E9268D6DBE9C3A` |
| Run B `launch.json` | `BBBD211993163E914D1C10C867E43640CDC7C1463329FCDECEB2B916F3D846F9` |
| Run A `config.json` | `F1FAD56C2F1CD8C9C6F2983F54C3E566C2903B24FEAACAAFF2BB03DB1927A4BB` |
| Run B `config.json` | `282817B3D88912399BB4E4F3C309965B15A4F10E4F98BEB3E7D531B95FEA91AB` |
| `build/bizhawk-collision-20261103-comparison.json` | `1946A5339DBC0DE2661307B379304D25280B5AF606D30B4CB0D09F302B089669` |

The comparison report's PASS means repeatable bounded observation, not
collision repair. Its eight compared outputs are byte-identical:
`iwram.bin`, `ewram.bin`, `vram.bin`, `oam.bin`, `palette.bin`,
`screen.png`, `loaded-rom.bin`, and `done.txt`. Their complete individual
hashes are recorded in that pinned report and both launch manifests.
The common screenshot hash is
`A02BAEAF693CBDA635262783DBE7D57D760037590F1CE7A8BD1C7D778BFD4323`.

The trace files are not byte-identical: run A hashes to
`A43E7739659D1B8760A09B39378EA26FBF8111CB74FBF31B41CE7EE072E35B9A`,
run B to `C2DA4CE72D485B1E7BDBFD2879ED121D3E48912DCD0B019207060127BC5F7B52`.
All non-register lines match in their original sequence. Only the `reg `
lines are sorted separately for comparison, because Lua `pairs` does not
fix iteration order; their register/value pairs also match. The report
explicitly records `non_register_trace_sequence_equal=true`. No input or
event ordering was discarded to obtain that result.

## Launch and input scope

The completed local invocations were:

```powershell
python build/run_collision_20261103.py bizhawk-collision-20261103-a
python build/run_collision_20261103.py bizhawk-collision-20261103-b
```

The runner remains available under ignored `build/` as investigation
source; it is not a portable product tool. It requires the local `W:`
workspace alias, existing BizHawk installation and baseline configuration,
and refuses an already existing output directory. These commands identify
the completed runs, rather than instructions to overwrite them.

For run A, its manifest preserves these exact EmuHawk argument entries:

```text
--gdi
--config=W:/build/bizhawk-collision-20261103-a/config.json
--lua=W:/tools/bizhawk_probe_gba_collision.lua
--userdata=output:W:/build/bizhawk-collision-20261103-a;frames:30000;start_frame:2970
W:/build/bizhawk-collision-20261103-a/probe.gba
```

Run B substitutes `-b` for the run-directory suffix. The runner launches
through `PrivateDesktopProcess` with a newly created, nonvisible Windows
desktop and a 240-second host deadline. This reuses the process helper,
not its GDB probing routine; these observations use Lua execution
callbacks without GDB breakpoint/step commands.

All 284 configured path entries point inside each run's own `data/`
directory. Both actual configurations disable background physical input,
automatic last-save-slot loading, SaveRAM autosaving, sound, and every
nested `AutoLoad` setting. The ROM copy is isolated in the run directory.
No supplied WSC save is part of these launches. Sound and save persistence
were not evaluated.

The pinned Lua script supplies ordinary controller inputs on relative
frame numbers. Start occurs at relative frame 2970; menu selection uses
the fixed schedule in that script. From frame 5550, mode 7 receives
periodic A/B and directional input, while mode 9 receives periodic A.
The trace records every input-state change. All eleven declared buttons
are explicitly assigned false before applying each frame's presses and
are explicitly released at the end. This is an automated input sequence,
not uncontrolled user play or a replay of the original wall-clock GDB
input schedule.

## Observation and limits

Both runs start at core frame 1 and complete 30,000 advances at core frame
30001. Their terminal capture is:

```text
capture=bounded-no-hit frame=30001 valid=84 hooks=84 dispatch_hooks=79 timing=frame-boundary
collision_count_maxima=3,4,4
screenshot_timing=post-frame frame=30001 capture_frame=30001 hooks=84 dispatch_hooks=79
```

The 84 overlap callbacks at `0836E370` all pass the type filter. All 79
visits to `0836EBA4` pass the exact dispatch contract: r1 is even in the
decimal range 0..34, r8 is `0836EBA8`, and r9 equals the ROM word at
`36EBA8+r1*2`. Callbacks run before the observed instruction; logged
callback addresses and exposed R15 values are separate fields.

The maxima are sampled command/event/world counts, in that order, from
IWRAM `4C4D`, `4C4E`, and `4C4C`. Samples occur at frame boundaries and
the two callbacks. They are not complete append-time telemetry and do
not prove maximum simultaneous list occupancy on all game paths.

The last periodic trace entry, at core frame 29401, reports mode 7 and
fighter 14. The parent inspected the actual common screenshot and found
a coherent battle scene. That screenshot is post-frame evidence. It is
not an instruction-time image or proof that all game systems are correct.
The final exposed R15 is `0000001C` with CPSR `60000092`; a sampled BIOS
IRQ address alone is not classified as a game fault.

The Lua self-check passed all eighteen valid dispatch rows and ten
invalid cases with mocked APIs, including count order, explicit input
release, and capture/screenshot timing. The record author independently
rechecked the comparison report hash, all eight output byte comparisons,
ordered non-register traces, and separately sorted register/value pairs.
This record adds no emulator run or game-code change.

The first E5 producer or overwrite remains unknown. Repeating one
deterministic no-hit trajectory increases confidence in the observation's
repeatability; it does not invalidate the original failure, prove a
repair, or establish current v64 runtime behavior. See
[the collision investigation](id14-collision-type.md), including its
2026-11-03 GDB observer-artifact audit, for the unresolved causal boundary.
