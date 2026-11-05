# Shoot storage and initializer tail integration — 2026-11-05

This resumes the interrupted work from `af34f1ac85798e31e1552138d7d3a8017994192a`.
The adopted change composes the remaining source `4090:73E2..7534` storage
and existing tail phases into the disconnected entry `08629800`. It does
not install the scene/controller caller or claim a complete playable port.

## Implementation and independent verification

The main build preserves the exact v64 front as an intermediate, then runs:

| Layer | Output SHA-256 | Independent report SHA-256 |
|---|---|---|
| Retained front | `CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7` | `471C31326FEE5FDCD2BD7841FB227082EE38D8CAB782AD6EA967C27C7C9C881F` |
| Ordered storage | `66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF` | `BC75F6EACF9E9320463CC8436A731E7405F4DE15959882CA59B71DC32C90333E` |
| Existing tail | `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46` | `9C530F9BB055BAEB5CE52B279110721E063C07973297EBBE0FDB0A182937BC50` |

Storage independently passes 4,096 ABI/order/error cases, 2,048 source bank
aliases and 186 negative controls. Each source halfword clear rereads native
EEPROM block 25, changes two API-buffer bytes, and preserves the other six.
Read failure skips its corresponding write; the existing bounded native
writer handles retry. The selected functional-backend contract and unchanged
Options error handling are documented in [storage](shoot-initializer-storage.md).

The tail calls other-player restoration, HUD/scroll setup and selective palette
preparation in source order. Its independent checker covers 256 ABI cases,
142 negative controls, ten synchronous functions and 23 PC literals. The
dependency review repaired a truncated event-setter guard and includes the
full consumer through `080129C8` and its synchronous children. The inspected
tail stack bound is 176 bytes including the outer frame. See
[tail composition](shoot-initializer-tail-chain.md).

The complete v64-to-v65 delta is 115 actual changed bytes, all in raw
`[629818,62988C)`. Two separately declared writes overlap only at the previous
return, in explicit storage-then-tail order. Each layer restores its complete
predecessor through its checked inverse. Other callers/resources, the unused
`085C7800..085C8000` reservation and controller boundary remain unchanged.

GPT-6.1 Sol High reviewed the builder and integration/runtime boundary;
GPT-6 Astra High independently implemented and ran the final-artifact checker.
The independent checker imports no builder and consumes no builder manifest.

## Complete fresh builds

Both `build/repro-v65-20261105-a` and `-b` were rebuilt from the three original
ROMs and pinned font/license using `tools/build_current_candidate.py`.
Both processes exited zero with PASS. All **255 relative file paths and
SHA-256 values match**, including every intermediate ROM, source-derived
asset, manifest and independent verification report.

- Final ROM: `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46`.
- Build manifest: `C1C9EF216B9407CA82612D3C69CBD76390ADB2B2BC675474139BBB7820A7F9B2`.
- Comparison `build/repro-v65-20261105-comparison.json`:
  `B4963676C8AB8F3338E334AD0190D9B430DF9D852E8681101310B33C1498F7B7`.

The original hashes rechecked before work are USA GBA
`996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED`,
WSC 1.0 `58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735`,
and WSC 1.5 `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The main build enforces these hashes again. Output directories were fresh;
old v64, standalone storage and interrupted tail artifacts were preserved.

A separate final read-only audit independently recalculated both complete
inventories and the comparison report, checked the two layer inverses and
combined inverse, and rehashed all three originals plus the frozen builders
and seven inherited verifier dependencies. The integrated main script hash
is `9FCB4BD5956804DE9D49C76DAFA81A4061234A3397D622AB58A5AA7DD642A4FC`.

Pre-sync checking found `core.autocrlf=true` could change newly checked-out
verifier bytes and break their frozen source pins. `.gitattributes` now fixes
Python line endings explicitly: LF by default, with the six existing CRLF
files retained exactly (including the palette verifier and main builder).
An initial LF-only export exposed those six differences and was not accepted.
The corrected `git checkout-index` export at
`build/checkout-v65-python-20261105b` matches all **267 Python files** byte for
byte against the files used by the completed builds/runtime. No Python code
or built ROM changed. Checkout report SHA-256:
`5E80ADDEE169004887CFDD9DF25F93441C85DB808F610360D690DA69FB87431B`.

## Hidden runtime regression on the exact integrated ROM

Two completed runs, `build/bizhawk-collision-v65-20261105-b` and `-c`, used
the exact final ROM and unchanged `tools/bizhawk_probe_gba_collision.lua`.
Each advanced 30,000 relative frames from core frame 1 to 30001, exercising
ID14 selection, battle, result/next battle and continue through normal input.
Both exited zero with all trajectory assertions passing. Each observed 84
overlap callbacks and 79 dispatch callbacks without an invalid result;
sampled command/event/world count maxima were `3,4,4`.

The eight final files (`iwram.bin`, `ewram.bin`, `vram.bin`, `oam.bin`,
`palette.bin`, `screen.png`, `loaded-rom.bin`, `done.txt`) are byte-identical.
All non-register trace lines match in original order; register/value pairs
match after sorting only those lines, whose Lua iteration order is unspecified.
The seven non-ROM outputs also equal the historical v62 bounded run.
The parent visually reviewed the captured waterfall battle frame; it shows
the arena and fighters coherently. Screenshot SHA-256:
`A02BAEAF693CBDA635262783DBE7D57D760037590F1CE7A8BD1C7D778BFD4323`.

- Runtime comparison: `build/bizhawk-collision-v65-20261105-comparison.json`,
  SHA-256 `8171A330F303499F6AFF804F7DF6C70445BF6EEE26A5020ABD93F8578D7D08A3`.
- Run B launch: `1DDFB69613C02733231D1FB1EC02B567D124BC15C5581165781ABF9134C9E065`.
- Run C launch: `5C63389D349A2B7D0D6B7889E08CBBC26B9C6A630C1CA3F7CF86FE3ED622271F`.
- Local runner `build/run_collision_v65_20261105_480.py`:
  `7E09818794ABD3CD0488B6980A499C17C6D3F05E5347A95C3C3A15BE24D040AD`.
- BizHawk 2.11.1 executable:
  `F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD`.
- Collision Lua: `7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9`.
  Its mock-Lua self-check separately passed all 18 dispatch rows and ten
  invalid cases plus sampling/input/capture checks before execution.

The first attempt, suffix `-a`, hit the runner's 240-second host deadline.
Its last logged input was relative frame 26867; that is not an exact final
CPU frame or a completed result. Its `completed=false` manifest and trace
remain preserved. Only the runner deadline changed to 480 seconds for fresh
`-b/-c`; ROM, Lua, frame count and controller schedule stayed unchanged.

The local invocation was `python build/run_collision_v65_20261105_480.py
bizhawk-collision-v65-20261105-b`, then the `-c` suffix sequentially. The
runner requires the verified `W:` workspace alias and frozen local baseline
configuration. It compares the complete loaded ROM, rejects existing output
directories, verifies alias identity with `samefile`, and uses
`PrivateDesktopProcess` on a separate nonvisible desktop. No visible fallback
or GDB memory intervention was used. All 284 configured paths point into
fresh run-local directories; nested autoload, background input, sound and
SaveRAM autosave are disabled. Native game SaveRAM created on process exit
remains isolated local output; no supplied WSC save is opened or hashed.

This is bounded ordinary gameplay regression only. The new initializer is
not exercised by this input route; its lack of an external caller is the
static ownership result, not runtime hit-count evidence. No physical EEPROM,
sound parity, live Shoot palette/IRQ lifecycle or E5 causal repair is claimed.
Separate read-only runtime QA independently rechecked both complete ROMs,
all eight outputs, ordered traces, launch/configuration pins, isolated path
settings and the preserved incomplete attempt; it reached the same result.

## Remaining gates

The source body is composed through its return under inherited contracts.
Earlier snapshot `085C1900` must run before source `1073` destructive colors,
and exclusive canonical palette ownership must continue through `1331`.
Actual source storage observers, external scene/controller entry, live stack
and IRQ/camera lifetime remain unresolved. The finite reference checks do
not exclude arbitrary computed aliases; dynamic resource and asynchronous
audio/task lifetimes remain inherited preconditions.

The E5 collision producer is still unresolved. Ordinary gameplay regression
cannot exercise this disconnected initializer or prove physical EEPROM
behavior. Whole-game four-language support, remaining content, final BPS
and complete playthrough/hardware QA are not part of this checkpoint's claim.
Provided WSC saves are excluded from all inputs and runtime launches.
