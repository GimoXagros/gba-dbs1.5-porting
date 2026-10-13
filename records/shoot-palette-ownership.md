# Shoot palette representation and bounded native operations

Investigation date: 2026-10-13. Starting image: exact static v50,
`C294106D381C1492D02D1FF0CBD3DBB6BDC07BF783C044A0D6E10BE0A6E2A0B1`.
This record extends `SHOOT-PALETTE-01`. It does not supersede the main audit's
runtime boundary or claim that the external Shoot scene is connected.

## Source capture has a concrete owner and lifetime

The palette source is not an arbitrary spare buffer. `71F0:0161`, raw
`772061..77208B`, resets source counter `1000:03E8` and copies all 512 palette
bytes into `1000:03EA`. Shoot callback `71F0:1043` calls it at raw `772F73`
(`71F0:1073`), **before** filling the hardware palette with black and setting
`FE00` white. The continuation runs the active-player presentation and
`11F7` white transition, calls `4090:7168` at `71F0:1243`, runs `1267` for
32 alternating half-palette decrements, holds in `12C6` for 150 source ticks,
then runs `1331` for 32 alternating restores from the saved mirror. The hold
requests source sound `D2` at remaining count 130. The successor is `139C`.

Source capture range SHA-256:
`760581E89D46555951EAD46CC68139A6F4881444F5D28E9A9D432ED1ECF5BE04`.
The complete `1043..139C` source interval SHA-256:
`7757A292434FEABC9B696BD172909FDA0FA33A95AA08336B78C75BFE4CD83C6D`.

This establishes source ordering. It does not establish native concurrent
ownership. In particular, source `03D4` bit 2 is a display-interrupt selection
flag, not proof that a pause task cannot run. The eventual native scene caller
must exclude the competing mirror writers throughout this interval.

## Actual native consumers split the source palette

Two independent consumers establish the mapping:

- `080132EC`, specifically `08013308..08013328`, reads a source P2 base,
  subtracts 8, adds the object slot and 16, multiplies by 32, and writes from
  color 1. Thus source rows 8..15 become native OBJ rows 0..7.
- `08000CF8` branches to `08011454`. At `0801145C..0801146C`, the native
  display helper calculates `05000000 + ((control & FF00) >> 7)`, reads that
  halfword, and writes it to hardware BG0. Consequently all sixteen native
  BG row-zero positions are real background-color lookup entries. The lack
  of stage-map references to BG8..15 does not make their zero colors unused.

The mapping used by the resident operations is:

| Source row | Full native row | Native saved row | Additional hardware alias |
|---|---|---|---|
| 0..7 | BG0..7, `05000000..05000100` | `0203E000..0203E100` | None |
| 8..15 | OBJ0..7, `05000200..05000300` | `0203E200..0203E300` | Corresponding BG8..15 color zero |

The canonical saved population is 512 bytes in two existing 256-byte native
mirror ranges. Hardware has eight additional two-byte aliases, totaling
528 bytes. Native BG8..15 colors 1..15, OBJ8..15, and the entire native mirror
gap `0203E100..0203E200` are preserved. In particular, the retail capture's
missing BG15 mirror is not assumed to be available memory.

Native P2 loaders do not populate OBJ color zero. The snapshot operation
therefore first copies both full canonical ranges, then reads BG8..15 zero
colors and places them in the corresponding OBJ saved zero slots. Later
restoration copies the canonical OBJ zeros back to the BG hardware aliases.

The existing common capture `0833FDC0` is still unsuitable for the initializer
tail: it copies BG0..14 and OBJ0..7, whereas the source tail replaces only
rows 0..7, 9..11, and 13, totaling 384 bytes. Rows 8, 12, 14, and 15 remain
from the earlier snapshot, except for the source-proved conditional other-
player refresh of rows 8 and 12. All sixteen source zero colors are then
replaced by the gray table.

## Existing native mirror users and limits

The exact retail USA ROM contains five aligned ARM BL encodings targeting
`0833FDC0`: `08340110`, `083403BC`, `08340728`, `08340C18`, and `08340EC0`.
`08340A68..08340A8C` restores the captured BG and OBJ populations.

Pause entry `08375360` copies OBJ hardware into `0203E200` and dims the
hardware palette. Pause continuations at `08375624`, `08375754`, and
`083757AC` restore this same saved population. A Shoot caller that permits
those competing tasks during the transition would corrupt the saved target.
The finite all-aligned-word scan is recorded by the analyzer; it does not
exclude indirect writers or prove scheduler exclusivity.

## Installed-operation design

`tools/build_shoot_palette_transition.py` supplies four resident ARM7TDMI
subroutines and a source-derived 32-byte table. It allocates no RAM and
installs no external call or task callback.

| Entry | Operation | Code / total bytes |
|---|---|---:|
| `085C1900` | Snapshot the canonical source palette before `1073` destructive changes | 96 / 100 |
| `085C1C00` | Selective 384-byte capture, sixteen gray saved zeros, white 528-byte hardware projection | 208 / 220 |
| `085C1D00` | One source decrement for the selected half | 208 / 208 |
| `085C1F00` | One source restore increment for the selected half | 272 / 276 |
| `085C2300` | Converted sixteen-level source gray table | 0 / 32 |

Every subroutine preserves `r0..r12` and LR and may change condition flags.
The two step entries require `r0` to be the remaining **source** callback
count, descending 32..1; other values return without writing. Even counts
update low BG rows, odd counts update OBJ rows and their high-BG zero aliases.
The scene caller owns counter storage, decrement, callback assignment, hold
duration, sound request, and final other-player flag change.

The native display helper aliases the selected background color into BG0,
so blindly reading hardware BG0 as the source's row-zero state would make
the restore fade follow the selected background color instead of target
gray zero. On even decrement calls, canonical BG0 is re-derived from the
confirmed white starting state and exact remaining count. On even restore
calls it is restored to the source gray target zero. This is bounded by the
32..1 precondition and is not a generic fade rule.

The established source-to-native channel expansion is `0 -> 0`, otherwise
`n -> 2*n+1`. Source fade cadence therefore requires native `3 -> 0` on
decrement, and `0 -> 3` followed by steps of 2 on restore. Retained native
even-valued targets are never inversely quantized; the final step clamps to
the exact saved 5-bit endpoint. The retail one-step helpers cannot provide
this source cadence. The separate native helper at `08012228` also masks
the same operand for both sides of its green comparison, so it is not used.

All four current code populations assemble/disassemble round-trip at their
final placements (196 instructions total). Exact preexisting expansion
bytes, aligned pointers, ARM branches, all five Expected Writes, preserved
gaps and the whole-image diff are guarded by the builder. This is static
machine-code verification; the parent milestone's independent verifier
owns final instruction, mutation-mask and semantic negative checks.

The separate `tools/verify_shoot_palette_transition.py` passed on the final
palette layer: 196 instructions, all 16 source channel values, all 32 retained
native endpoints, both mutation masks, and eleven deliberately corrupted
variants rejected. Its report is
`build/shoot-palette-20261013/verification.json`, SHA-256
`7A6A9632EEDA2A98498405A2EAD2F78A27AB4BC6CEF142CEC9CBDF1FD9B96AAB`.
The check explicitly excludes scene scheduling and runtime evidence.

The palette layer takes the guarded rules-layer image
`FD4E69C29003325D47A6189C3A05005D38FF7B4B6D442B31A271D360A9A0DE5C`
and writes `build/shoot-palette-20261013/palette.gba`, SHA-256
`2008EC0520554F09C84351220B8A30931E1E636A7CEEE9BF3CBBB12C28C1B5AE`.
The manifest is the sibling `palette.json`. Exactly 792 bytes differ, all
inside these five half-open raw intervals:
`5C1900..5C1964`, `5C1C00..5C1CDC`, `5C1D00..5C1DD0`,
`5C1F00..5C2014`, and `5C2300..5C2320`.

The all-aligned-word scan reports no candidate pointer or ARM branch target
inside any of those five write intervals. It does report two candidates
inside the enclosing window's preserved gaps: an ARM-branch-like encoding
at raw `10E458` targeting raw `5C2060`, and the aligned word `085C1B00` at
raw `37DA94`. Their role is not classified as code or data. Both targets and
all enclosing gaps remain byte-for-byte unchanged. The preparation entry
was moved to `085C1C00` specifically to preserve the second target.

The ownership analyzer's deterministic report is generated from only the
three ROMs. Current report SHA-256:
`2F5FA817B464F13A7606388F9650549A41C801A8FEB439A4FE51A2430A3048ED`.
It checks the 16 source channel values across 17 steps and all 32 native
channel endpoints, plus actual native consumer instructions and guarded
source ranges. It reports the native lifecycle as unresolved.

No emulator, supplied save, display window, or runtime verification was used.
These operations do not complete the scene controller, initialization,
normal-play reachability, source timing in native frames, or visual parity.
