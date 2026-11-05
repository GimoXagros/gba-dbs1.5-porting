# Shoot source consumers and calibrated lifetime observation

Baseline: exact v65 `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46`.
No ROM, external caller, main pipeline, or emulator binary is changed by this work.

## Additional positive storage mappings

`tools/analyze_shoot_lifetime_consumers.py` checks all thirteen direct `D8 3C` /
`DA 3C` operand occurrences in the fixed source ROM, then verifies three additional
actual source/native consumers against both retail USA and final v65 bytes:

| Source raw | Native address | Effect |
| --- | --- | --- |
| `760554..760561` | `0836EB18..0836EB2C` | Target player index times two; regeneration delay = 150 |
| `760C7B..760C88` | `0836F470..0836F484` | Same index, owner, and delay after a collision branch |
| `7672E5..7672F2` | `0835A080..0835A094` | Current player index times two; regeneration delay = 150 |

The real native literal owner at all three is `030048AC`. Under the existing
normal task `DS=0C00` contract these are source `FCD8/FCDA`, not the distinct
SRAM words `13CD8/13CDA`. The following source `7672F2` adds four to the index:
its remaining four apparent `3CD8` accesses actually use `FCDC/FCDE`, the decay
timers represented by `030048B0/B2`. Both original and native delay constants
are **150** here; no blanket 75-to-60 conversion is appropriate.

This accounts for the direct operand population, including the known common
initializer and regeneration reader. It does not exclude indirect aliases or
descriptor consumers, and identifies no positive reader of distinct SRAM.
EEPROM block 25 must remain distinct; clearing ordinary regeneration timers
would still be incorrect.

## Complete source spatial exhaustion behavior

The same analyzer models the exact two bounded `LOOP` instructions in source
`8EF3`, including their fallthrough when no comparison succeeds. It partitions
all 65,536 signed Y values into six selected records and evaluates all 65,536
X values for each record, covering all **4,294,967,296** input pairs without
assuming that gameplay reaches them.

The exhausted Y loop does not return. It reads the first X record as a sixth
Y record, giving count `1` and pointer `0800`. That points into source code;
the resulting selectors are `C08E` or `3A20`, whose indirect jumps select source
`EB4C` or `E59A`. For `X >= 1E00`, the first four legal Y partitions fall through
to patterns `1,1,1,0`; the final legal Y partition instead reads selector `32`
and jumps to `0A80`.

Consequently, merely removing the native guards and preserving 16-bit wrapping
does not implement a total spatial-selection function. The actual actor domain
or additional reachable source behavior is required. No clamp, guessed pattern,
or unrelated source-code execution has been installed.

Four negative controls reject a changed source loop step, a changed final
native timer-owner literal, a changed boss-stage prerequisite, and a changed
Options difficulty cap. Output:
`build/shoot-lifetime-consumers-20261105/evidence.json`.

## Concrete observer bug found and repaired

The first hidden original-WSC smoke run reached a fresh stage-8 battle but
received zero callbacks when named `ROM`/`SRAM` scopes were used. The core's
actual callback scope is only `System Bus`. The second smoke delivered positive
data reads after switching to physical addresses, but no expected execution
or stage-write callbacks. Both failures are retained and are **not** no-access
evidence.

The exact BizHawk 2.11.1 source identifies the cause beyond scope selection.
Its managed `SetMemoryCallbacks` passes `(read, write, execute)` to a native
function whose parameters are `(read, execute, write)`. Thus the Lua callback
names for execution and writes are exchanged in this backend. Earlier traces
which reported an "execution" callback address `3116` alongside an unrelated
`PS:PC` were observing a RAM write, not execution at `3116`.

Immutable upstream commit: `bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5`.

- [Managed call order](https://github.com/TASEmulators/BizHawk/blob/bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5/src/BizHawk.Emulation.Cores/Consoles/WonderSwan/WonderSwan.cs)
- [Managed native declaration](https://github.com/TASEmulators/BizHawk/blob/bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5/src/BizHawk.Emulation.Cores/Consoles/WonderSwan/BizSwan.cs)
- [Native binding](https://github.com/TASEmulators/BizHawk/blob/bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5/wonderswan/system.cpp)
- [Fetch timing](https://github.com/TASEmulators/BizHawk/blob/bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5/wonderswan/v30mz-private.h) and [read/write hook timing](https://github.com/TASEmulators/BizHawk/blob/bdddf4a58aa1a022afb11dc73294a81a5aa7bbd5/wonderswan/v30mz.cpp)

Local backend hashes:

| File | SHA-256 |
| --- | --- |
| `EmuHawk.exe` | `F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD` |
| `dll/bizswan.dll` | `41BCEE9234055EA70461EFC196872F5BFF5CCE4CE1AEEE003E78BF31035DA038` |
| `dll/BizHawk.Emulation.Cores.dll` | `444BC157418E9B5DF5D07E987FC7AD1D2D1C6993676F5B864368027CB4F054D5` |

`tools/bizhawk_probe_wsc_shoot_lifetime.lua` compensates only for these host
callback bindings. It contains no guest memory/register writes or savestate
operations. The root runner must verify the backend hashes and pass the explicit
`callback_order:bizhawk2111-rew` contract. CPU opcode-fetch observation binds
through `on_bus_write`; CPU memory-write observation binds through `on_bus_exec`.
CPU read observation is unchanged.

The opcode callback runs after `FETCHOP` increments PC but before execution, so
the calibrated `PS*16+PC` must equal the callback address plus one. The native
write hook runs after `Write20`; its supplied callback value is always zero,
so the observer labels the actual backing-byte peek separately.

Completion requires positive delivery of the known frame-wait opcode and both
source stage-field read/write callbacks. This prevents another silent-scope or
callback-order failure from being reported as no access. The source operand
watch covers both `13CD8..13CDB` and `1BCD8..1BCDB`; SRAM's established 32 KiB
mapping makes C1 selections irrelevant to those backing-byte identities.

## Calibrated ordinary-input results and next probe

The root's fresh hidden `build/bizhawk-wsc-lifetime-20261105-c` run completed
4,500 frames with 4,475 calibrated frame-wait fetches, 11 stage reads and three
stage writes. Its loaded ROM and script matched the runner's exact files.
The end snapshot was the first normal stage-8 battle; common-bank tile zero's
32 bytes were all zero. That is a snapshot, not a lifetime proof.

The subsequent unchanged-script `-d` run completed 30,000 frames with 29,915
calibrated fetches, 171,819 stage reads and 11 stage writes. Neither Shoot nor
the distinct SRAM accesses nor the terminal hooks were reached. Inspection of
the final screenshot showed the title screen, and retained player score fields
were 1 versus the opponent's 14. This input sequence lost/exited the battle;
its calibrated no-hit result cannot establish the missing Shoot contracts.

The separate `tools/bizhawk_probe_wsc_shoot_lifetime_chase.lua` preserves that
frozen script and uses ordinary input informed by existing player positions.
It validates the two handles against the established 52-slot task payload
domain before reading actor coordinates. Source idle consumers `766B04` and
`766AB6` distinguish attack edge `80` and jump edge `40`; the new input policy
chases the opponent, pulses attacks, and jumps for a higher target or stalled
movement. It does not alter positions, scores, flags, RNG, or callbacks.

The new probe also observes all 32 common-bank tile-zero write addresses and
the real `8EF3` X/captured-Y arguments. Its three input-policy self-checks ran
in the local Lua 5.4 library, and both scripts passed that library's syntax
parser. These are host-script checks, not emulated gameplay. Actual win/scene
reachability remains an observed outcome, never a forced precondition.

The root's 18,000-frame `-e` run completed with 17,906 calibrated fetches,
247,329 stage reads, four stage writes, and 224 common tile-zero byte writes.
It did not enter Shoot. The first bout ended 3 versus 11, then normal input
continued into another bout. Its source file is preserved verbatim as
`build/shoot-lifetime-consumers-20261105/chase-e.lua`, SHA-256
`0B9377B1CBBC28B57DA104C11E53674D2581BD5BB15485E3DA04490D05687544`.
The revised chase profile attacks only within 48 horizontal / 32 vertical pixels,
gives a jump priority over attack, and detects stalled movement over 90-frame
windows. Its four host-Lua policy assertions pass. The revision is a new input
experiment, not a claim of success.

## Reached common blank-tile initialization

The calibrated `-e` write observer identifies a concrete original producer:
at frame 518, `PS:PC=558C:0058` follows the `REP STOSW` at raw `755916` and
all 32 writes to `4000..401F` are zero. This is source `558C:0000`, selected
by mode 2's first function pointer at raw `74FAE4` in the actual main-mode
dispatcher. It is separate from the old unvalidated `74FEA0` lead.

The analyzer now checks the real mode*12 calculation, table binding and
instruction sequence: AX is zero, ES becomes zero, DI becomes `4000`, CX
becomes 16, and `REP STOSW` clears exactly the common-bank tile-zero bytes.
Thus the previously missing **reachable initial uniform tile supply** has a
positive producer and a natural-execution observation. Preservation of that
tile until/during Shoot and exclusion of camera refills remain separate.

## Actual normal-input prerequisite: boss depletion, not first-bout victory

The revised `-f` ordinary-input run naturally won the first stage-8 bout and
continued to stage 1 by frame 15,000, with progress `0100`. It completed 18,000
frames without entering Shoot. This prompted a check of the caller before
choosing a longer input route.

Source `740C97..740CB0` computes SRAM `03D0` as the 16-bit sum of mode `0050`
and two only when stage byte `005C` is 7. The analyzer checks its exact
instructions and all 65,536 mode values for both branches. For single-player
mode zero, only stage 7 gives kind 2. Other mode values are not assumed to be
reachable single-player states.

Source `7417BF` permits the relevant result branch only for kind 2. The first
actor has priority: HP `+50 == 0` and state `+A4 == 003E` calls root case 4.
Otherwise the second actor, obtained from SRAM `065E`, must have signed
16-bit HP `+50 <= 0` for `7417F3` to call root case 5. Expiration of timer
`03CE` instead calls root case 0 at `74180F`. Ordinary timer victory or defeat
in the first bout therefore cannot reach this Shoot caller.

The complete fixed-ROM population of literal `LCALL 71F0:0000` encodings is
six sites, each checked with its immediately preceding argument: `7417DB:4`,
`7417F3:5`, `74180F:0`, `7418AC:2`, `76C241:3`, `7864F9:1`.
This is a finite direct-call inventory; it does not exclude constructed or
indirect calls. After the actual case-5 call, the existing scene predicate
still applies: stage must not be 11, and difficulty must be 3 or be nonzero
with progress bit `0400` clear. The selected allocator at `771FE3..771FF4`
creates source task `71F0:0EEA` through `4FFF:0980` with stack `0FF0`.

The root's next bounded campaign probe `-g` uses the exact frozen `-f` v2
observer/input script with only the frame budget raised to 90,000. It tests
the actual natural route to stage 7 and boss depletion. A first-bout win is
no longer treated as an expected Shoot trigger. No difficulty, HP, stage,
progress, or other game-state field is forced.

The `-g` probe subsequently acquired progress `0400` after a continue in stage 1.
At difficulty 1 that bit excludes the Shoot branch even if a later boss is
defeated. The root therefore stopped this as a deliberate partial experiment;
it is not a completed 90,000-frame acceptance run.

The separate `tools/bizhawk_probe_wsc_shoot_lifetime_hard.lua` follows the real
Options UI before battle. Title root row 2's table record is `(FFFF,2,0,0)`;
title mode 3 transition 2 selects mode 14 (`7564:0000`). The ready title task
callback is `7FFB:067B`; its payload `+4/+5` holds tree/selection. The observer
reads those values only from matching task slots, presses down to root row 2,
then A. Options cursor `0300:0118` selects row 1, whose actual task allocation
at `775B5A..775B72` binds `7564:13FE` and row identity 1. The right-input edge
`02` reaches `776AEC..776B05`, increments difficulty byte `1000:005D` up to
3, and B edge `80` leaves through the existing controller. The script then
resumes the same chase function used in `-f/-g`.

The analyzer pins the menu records, mode bindings, row producer and actual
difficulty consumer, including a rejected cap mutation. The new script passed
the local Lua syntax parser and six host-Lua UI transition assertions. Its
acceptance additionally requires an observed Options mode, observed difficulty
3, and an actual battle still at difficulty 3; execution is the root's separate
test. Earlier observers and their runtime hashes remain unchanged.

The fresh `-h` run confirmed that UI path: title rows 0,1,2 were observed at
frames 4020,4080,4140; Options entered at4218; the two ordinary right presses
raised difficulty1→2→3, with3 observed at4381; title returned at4525. Its
post-Options input then sent only Start at the reopened title menu, so it did
not reach battle and is not accepted as a complete route. The separate
`tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua` fixes that host input
handoff: A confirms root row0; up returns other root rows to0; Start handles
the initial prompt. It retains the entire source observer and chase behavior.
The frozen `-h` script is unchanged. The v2 script passes the Lua syntax parser
and has SHA-256 `0CC9B17CAE00E7B7EFA33976788B1A66F595F15473EE78A597A77ADF68F42D69`.

The fresh `-i`9,000-frame run then passed the complete ordinary-input hard
route. It observed difficulty3 in battle,8,943 calibrated frame-wait fetches,
119,943 stage reads and five stage writes. Its loaded ROM and script matched
the runner files. It did not reach Shoot, lower8EF3, distinct SRAM or terminal
hooks. The root's one further bounded `-j` campaign uses the same frozen v2
script for up to90,000 frames/900 seconds; its outcome is recorded separately.

## Actual pursuit terrain and finite follower bound

`tools/analyze_shoot_pursuit_bounds.py` verifies the actual source and native
terrain consumers, using the immutable WSC1.5 and exact v65 candidate. Both
source resources39/40 select collision grid `33CA20`; native resources29/30
select `08607000`. All3,024 four-byte cells are identical. This is the complete
56×54-cell grid, with live collision dimensions448×432 pixels, rather than a
guess from visible maps or the older cached world limits.

Source battle `7418C7` walks26 objects and calls `6F76:03B1` before committing
`+3A/+3C` displacement into `+26/+28`. The world helper derives width/height
from live BG fields at `76FC1B..76FC36`. Its real right-edge correction at
`76FED4..76FEFA` produces `width-radius-1` and clears deltaX. Movement is capped
to signed `[-127,127]` when terrain flag8000 is enabled and bypass0800 is clear.

The accepted source player reset at `747D74..747D9D` starts P1 at X=`0E00`,
Y=`FF80`, with flags `E700/0040/0000/0000`; the scene clears freeze40 and waits
for ground0800 before restoring ordinary input/battle. The lower object targets
that exact P1: `747C15..18` installs saved065C in lower+14, and `7496A6..AC`
captures its Y at the end of the225-tick tracking phase.

The bottom grid has no holes: row50 is entirely solid lowbits1/3 and rows51–53
are entirely3. Drop-through tiles occur only on rows33,39,42,44. The final such
row is separated from the bottom by five empty interior rows. Source
`766A55..766A89` requires jump-edge40, held-down4 and ground lowbits2 to enter
drop-through; `768619..768629` clears its flag on empty ground. These are real
predicates, but a complete Y invariant still needs callback lifetime: downward
collision at `76FD6B` writes proposed Y, not a snapped floor boundary. Later
landing handling must stop subsequent gravity. The separate scene reviewer
identified this same limitation; no universal Y clamp is claimed.

For lower X, the new finite model allows **arbitrary** target X in `0..1BFF`
on every update. It preserves the source unsigned comparisons, band-edge
subtraction wrap and 16-bit position wrap. All65,536 possible current-X values
have their available actions independently checked by integer inequalities.
It then visits5,462,663 abstract states over224 normal tracking updates, one
expiry update retaining the previous velocity,19 final following updates and
one stop. The maximum signed X is7198 (`1C1E`), below the selector's `1E00`
boundary; the minimum is−5839. This component proof requires P1 to remain in
the stated X domain and the lower object to receive only its own velocity
integration. It does not replace the remaining fighter/bypass/landing and
external-displacement ownership proof. Two negative controls reject a changed
floor cell and a changed tracking operand. No game code was changed.

The separate scene reviewer reproduced the same5,462,663-state result using
algebraic action predicates without importing this analyzer. A proposed
off-by-one concern was checked against exact source bytes: `76FEED:E90600`
jumps to `76FEF6:4B` (`DEC BX`), followed by the current-X store at76FEF7.
Thus the right-edge current-X expression above includes the final decrement.
The cached-height deletion at743B5C was also classified as a dropped-item
callback, not the ordinary P1 landing path.

Frozen bounded analysis artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `tools/analyze_shoot_lifetime_consumers.py` | `8A4E822195A10606E429976ED481ADCBDFDB59C463F6882DA4FC032B9AD04D1B` |
| `build/shoot-lifetime-consumers-20261105/evidence.json` | `DB34A93C45B176A877D9C432858B987913C65D04B345F48D21F32F66E3FE40E9` |
| `tools/analyze_shoot_pursuit_bounds.py` | `FB817D4890E09E0EC3B8ED02674FF11BDFF0FF79DE6287B88B0E03285C4D17AE` |
| `build/shoot-lifetime-consumers-20261105/pursuit.json` | `56BB8C1EE7A856AE66442666B415C599882993C55DE63C4369CE7A8F8F64F251` |

## Bounded hard campaign j: host deadline, not a completed route

The root's `build/bizhawk-wsc-lifetime-20261105-j` run ended at its900-second
host deadline. Its finalized launch report records `completed:false`,
`loaded_rom_exact:true`, and `script_unchanged:true`. There is no `done.txt`
and no final RAM snapshot. The requested90,000-frame experiment was therefore
**not completed**. The root confirmed the owned emulator had exited; this
audit performed no process operation and launched no further experiment.

The preserved trace reaches a logged relative frame78,900. Its last regular
state sample at78,600 has stage9, difficulty3, progress0400, camera005C,
78,492 calibrated frame-wait callbacks and zero watched storage accesses.
The last actor sample at78,900 remains battle mode7. There are positive stage
read and write callbacks, so this is a functioning partial observer rather
than the earlier silent-scope failure. No non-calibration execution site or
distinct-SRAM access was logged on this observed path. It never supplied a
Shoot or terminal lifetime observation; the missing hits establish no absence
outside that path and no safe external entry.

The normal UI route was positively observed again: Options4218, difficulty3
at4381, title return4525 and battle confirmation5297. Read-only audit verified
both loaded/probe ROMs against the immutable original SHA, the frozen v2
observer, every file hash in the finalized launch manifest, all redirected
data paths, disabled background input/save autoload, and all eight recursive
AutoLoad settings being false. No supplied WSC save was read or hashed.

| Final artifact | SHA-256 |
| --- | --- |
| `j/launch.json` | `73BEAAA2FE642D11DF7E57B885CB9C790C350261C05C10876AE91381683CF2F4` |
| `j/trace.txt` | `7277D64D487BD7B0FD4CE87435ACF47830B30AC84BCEFF18530B8203B5DEA831` |
| `j/config.json` | `B29A0CD490C18C91B8F10604C3D906859C47FCD93EB0E455255728FDE350FD99` |
| `build/shoot-lifetime-consumers-20261105/j-timeout-audit.json` | `83A4C875A1F14C5A8C636128D72F3860A8B6FFA4BB830A0385C2377EC307AC9C` |

The root owns hidden fresh-boot execution and its results. This record does not
yet claim a reached Shoot scene, proven camera/DI lifetime, an EEPROM observer
mapping, or safe external scene entry. No supplied WSC save is accessed.
