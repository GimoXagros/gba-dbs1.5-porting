# Shoot initializer components and resource lifetime (2026-10-13)

This record covers the new resident initializer components, the two P0 preload
consumers, and the remaining outer-initializer gaps. It does **not** establish a
playable Shoot entry. No emulator, save file, or visible application was used.

## Fixed artifacts and ownership

- Builder: `tools/build_shoot_initializer.py`.
- Independent source/resource reader: `tools/analyze_shoot_initializer_lifetime.py`.
- Separately authored final-code verifier: `tools/verify_shoot_initializer.py`.
- Exact predecessor: palette layer
  `2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE`.
- Result: `build/shoot-initializer-20261013/initializer.gba`, SHA-256
  `726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`.
- Reports beside it: `initializer.json`, `independent.json`, `verification.json`.

All eight writes were planned against immutable predecessor `FF` bytes. The
reserved raw window is `[5C4000,5C6000)`; only the ranges below are written.
There is no native hook, menu change, new call site, or `9908` boundary change.

| Native address | Size | Implemented contract |
|---|---:|---|
| `085C4000` | 120 | Common BG-map/control/staging resets and existing Shoot graphics clone; partial `7CCF:0FC4` |
| `085C4300` | 84 | Stage byte 11 and source `71A4..71C7` timer/flags/stage-manager setup |
| `085C4400` | 28 | Only the proven source `1000:0660` halfword clear |
| `085C4500` | 140 | `93E7` presentation-resource constructor call, `r5=presentation` |
| `085C4600` | 140 | `888B` presentation-resource constructor call, `r5=presentation` |
| `085C4800` | 332 | Relocated P1 from WSC raw `3D23B0` |
| `085C4C00` | 404 | Relocated P1 from WSC raw `0DFEC0` |
| `085C5000` | 40 | P2 from WSC raw `3D7AC0` |

Every code entry preserves `r0-r12`, `lr`, and `sp`; flags are clobbered. Native
helpers needing the game's zero `r11` convention receive zero inside the saved
register frame. The two resource entries require an existing valid native
presentation. They do not allocate objects, install callbacks, select events,
or load the palette directly.

Three aligned predecessor words resemble ARM branches to reserved gaps:
raw `1152B8 -> 5C4EC0`, `2EA4A4 -> 5C4378`, and `2F8B7C -> 5C580C`. Their roles
are not inferred. Those destinations remain untouched `FF`; the scan rejects
all preexisting aligned pointers or branch-like targets into installed bytes.

## Timer and stage-manager proof

Source `4090:7168` selects stage 11, calls the graphics helper, then writes
`1000:03CE=4650`, clears `03D4/03D6/03D8`, ORs `03D4` with `0010`, and calls
`4090:36C0`. The resident stage-manager component preserves the observable
write order: timer, `03D4=0`, `03D6=0`, `03D8=0`, `03D4=10`, manager call.

Timer conversion is a consumer-backed commercial mapping, not a guessed
constant. WSC 1.0 raw `390A33..390A73` and WSC 1.5 raw `740C73..740CB3` are
identical after relocating five globals: `0354/0356/0358/035A/035C` to
`03CE/03D0/03D2/03D4/03D6`. They produce `6750/9000/13500` frames and the stage-7
override `18000`. Native `080D17F8..080D1858` produces `5400/7200/10800` and
override `14400` (`3840`), storing the timer at `03004500`.

WSC 1.0 HUD raw `39FEAC` and WSC 1.5 HUD raw `7875AC` divide that timer by 75,
then 60. Native `08373D34..08373D48` divides by 60, then 60. Native
`0837500C..08375018` decrements the same halfword once; WSC 1.5 raw `741115`
decrements `ES:03CE`. Thus the Shoot timer `18000` becomes native `14400`.

Source `4090:36C0` raw `743FC0..7440C7` is stage-manager setup, not fighter
allocation. Its native counterpart is `0836D224`; the existing candidate
branches at raw `36D2C0` to `08584D40`, which indexes the existing twelve-stage
configuration at `08584C00`. These dependencies are hash/byte guarded.

The existing native stage getter `080D1C78` is already redirected to
`08582C40`. Battle-state byte `+0A` values `0B/0D/0E` override the stage to
`10/8/9`; otherwise it reads stage byte `+0E`. The component therefore requires
that the selected stage resolve to 11. Writing `0300231E=11` alone does not
establish that precondition under the three overrides.

## Existing objects and the segment distinction

Source `71D1..7394` loads existing active/other objects from `ES:065E/065C` and
uses the existing auxiliary object at `ES:071E`. The corresponding resident
bindings use `030048A0/0300489C/03004D3C`. `36C0` cannot be used as evidence that
these objects have just been allocated. The ordinary auxiliary allocation path
starts at source `4090:4DC5`, calls allocator `4090:172A` with pool 5, and stores
`ES:071E`; the commercial native lineage uses pool 5 and `03004D3C`.

Source `73D6..73F0` explicitly sets `ES=1000` and clears three halfwords:
`0660`, `3CD8`, and `3CDA`. Only `0660 -> 030048A4` is installed. The mapping is
proved by the common fighter producer at raw `7432F8` / native `08352B44`, and
two independent indexed consumers:

| Source consumer | Native consumer | Shared behavior |
|---|---|---|
| raw `743465..743473` | `08352DC4..08352DE8` | Character `+10` times 4, base `0660` / `030048A4`, shifts two halfwords |
| raw `766ED4..766EE9` | `08355EE8..08355F08` | Same indexed base, selects `+0/+2` from the translated object flag |

The common fighter producer sets **ES=0C00** before clearing `3CD8/3CDA`.
Those native HP-related globals are `030048AC/030048AE`, but Shoot's clear sets
**ES=1000**. Their linear addresses are respectively `FCD8/FCDA` and
`13CD8/13CDA`. Reusing the known HP globals would conflate distinct source
memory domains.

A bounded scan of raw `[700000,800000)` found 11 `D8 3C` patterns and two
`DA 3C` patterns. The additional known accesses are the fighter recharge/decay
paths, not a proven later reader of `1000:3CD8/3CDA`. This negative search is
not proof that the Shoot writes are unused: indexed aliases and mapper state
still matter. The same range has 22 `E6 C1` byte patterns; one at raw `753D7F`
is inside another instruction's operand and is not an OUT instruction. A real
helper at raw `7638F6` saves C1, `76391F` selects `FF`, and `763975` restores its
previous value. Constant mapper state must not be assumed from one nearby
`FF` selection. The analyzer records exact pattern locations and these three
guarded bank operations. No fake clear or safe-omission claim is made.

## P0 preloads are consumed through native presentation resources

Source `73A9..73D6` calls `4FFF:226E` for:

| Source P0 | Source tile base | Later constructor | Existing native P0 |
|---|---:|---|---|
| bank BD, `244E:0000` (raw `3D44E0`) | `006D` | `4090:93E7` | `085DB300` |
| bank BD, `20CA:0000` (raw `3D0CA0`) | `0137` | `4090:888B` | `085DB400` |

The source helper derives its VRAM address from the explicit tile base and
copies raw source pixels. The corresponding native presentation constructor
`080127E4` stores P1/P0/P2 at presentation `+44/+48/+4C`, tile identity at
`+14`, and palette at `+10`.

For these native resources, P0 flags are `0008`, so draw dispatch
`08012C28..08012C58` selects the routine copied from ROM `08012C58` to IWRAM
`03000200` at startup; its callable entry is `03000204`. The routine obtains
the descriptor/pixels through presentation `+48`, selects layout tiles, and
copies their 32-byte pixels into the native staging buffer at
`02000000 + dynamic_tile_index*32`. OAM tile attributes use that dynamic index.
The bounded routine does not read presentation `+14` to choose the staging
address. Therefore no fixed-VRAM upload at source IDs `006D/0137` is emitted.
The identities remain exact constructor arguments; the native renderer owns
the actual dynamic tile placement.

## New P1 data and independent reverse checks

P1 raw `3D23B0` has one command with 15 items; raw `0DFEC0` has three commands
with 6, 8, and 6 items. The previous generic parser excluded the valid
single-command population. Both also contain nonzero item word 5 references:
five references to five ten-byte records in the former, and eight references
to one ten-byte record in the latter.

The commercial source P1 at `2AE180` and native P1 at `350248` contain 17 such
references to 11 unique ten-byte records. Reading the native tail pointers
proves all 11 target records are source-identical. The existing formula
`0835032C + source_word5` describes that commercial container's relocation;
it is not valid for an arbitrary newly converted P1. The new converter copies
and relocates each referenced record within its own resident container.
Metadata A records retain eight-byte identity; non-null metadata B records
retain ten-byte identity. Null pointers stay null.

- `085C4800` P1 SHA-256:
  `447CB640585411B6027544D57882206D283337CB90DAA0C9099A4E455D0C4AE4`.
- `085C4C00` P1 SHA-256:
  `C3A099E04431467D752A25D9AF10ED9C2C4F046D2CB4468DF6EAC968758AA7AD`.

The independent reader imports no generator or converter. It reverses native
command/payload/A/B/tail pointers, checks source bytes and bounds, and
reconstructs all 15 constructor arguments from final decoded instructions.
Negative controls reject a tail redirected into the retail container, a
wrong command count, and a swapped P0. The separate final verifier checks
all 111 final ARM instructions and literals, inverse P2 colors, full-ROM
write ownership, inbound references, and five instruction regressions.

## Exact remaining outer-initializer effects

The graphics subset at `085C4000` implements the commercial four BG descriptor
control pairs, map clear `0807FBF8`, backdrop-shadow high-byte clear via
`08000CD8`, staging resets `08015D38/0801369C`, and the already resident Shoot
graphics clone `08582A00`. It requires exclusive scene ownership and a safe
display/IRQ state. It does not establish the whole `7CCF:0FC4` contract.

The remaining source effects are the `7168` display/scanline-IRQ preamble;
the stage/dimension and shared screen-state preparation around the graphics
load; dedicated HUD palette/font upload and four `2FFF` map entries in raw
`77DE04..77DE47`; the final `7CCF:1240` display/scroll call; and the two
unresolved `ES1000:3CD8/3CDA` clears. The three existing object lifetimes must
also be proved through whichever scene entry eventually invokes this order.

Calling the whole native `0803EE08` is not justified merely because the
candidate already patches the dimension index and main stage dispatch.
The later native HUD branch still reads actual stage `03002656` at
`0803EF08`, treats only stage 7 specially, and otherwise indexes the original
table at raw `3F078` using `stage << 5` plus a mode offset (`0803EF18..0803EF44`).
That is a concrete remaining stage-11 table consumer, and its generic HUD
path is not the dedicated source Shoot HUD sequence. The subset avoids that
unproved call. No full ordered wrapper or palette orchestration is installed
until these effects and lifetimes have an actual native contract.
