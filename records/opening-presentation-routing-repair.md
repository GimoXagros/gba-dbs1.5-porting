# Opening presentation routing and native OAM overflow, 2026-10-16

The opening's new selector 13 still used the eleven-row retail resource view.
Its unintended auxiliary P1/P0 pair caused the observed native renderer
overflow. The repair changes only the callback's resource-view literal. The
root-owned invisible run of the repaired artifact reaches the first battle;
this is not complete-game or Shoot validation.

## Exact cause and runtime evidence

The failed ROM was `build/repro-v54-20261015-a/shoot-other-player.gba`, SHA-256
`93A325538474B6BB7978854CFD55BC3161B129DCDEF884E5B076507FA708EA1E`.
The read-only endpoint-verified observation is
`build/physics-consumers-20261016-overflow/probe.json`, SHA-256
`F548E7E9C1F5EAE8FA035908E5AC69171E538127DDA8A3649A85A38D196A0D8C`.
It records the expected process owner of port 2345 and ROM sample comparisons;
these samples are not a full hash of loaded ROM memory. There were no guest
memory writes. The supplied save was not opened, loaded, or hashed.

At `080851CC`, callback 6 assigns selector `13`. Its literal load at
`080851DC` still reads raw `0853F4 = 080D42B8`. Constructor `08088250` indexes
this view using a 32-byte row. Row 13 lies beyond its eleven opening rows and
contains auxiliary resources `P0=082A02EC`, `P1=082A0040`, `P2=082A0988`.
The actual runtime presentation at `03002908` retains exactly these three
pointers. Its tile descriptor at `082A0500` supplies pixel base `082A0508`,
also exactly the watched `r11`.

The auxiliary P1 contains six events. The inserted callback 7 invokes event
`21` (hexadecimal); its out-of-range event row yields command pointer
`00700000`. This follows directly from the ROM and native event consumer.
The runtime observation supplies the subsequent malformed frame index rather
than assuming a particular open-bus result:

| Value | ROM consumer or observed state |
| --- | --- |
| Presentation layout index at `+18` | `E1D1` |
| P0 layout table | `082A02FC` |
| Indexed entry raw address | `311184` |
| Count at that entry | `00F223F3` |
| Item pointer at that entry | `00F2223F` |
| Completed loop iterations | `128` |
| Observed remaining count `r2` | `00F223F3 - 128 = 00F22373` |
| Observed item pointer `r10` | `00F2223F + 128*4 = 00F2243F` |
| Observed OAM index `r0` | `128` |
| Observed OAM pointer `r12` | `03001428 + 128*8 = 03001828` |

The watchpoint stops on `03001828`, the first OAM record beyond the 128-entry
buffer. Reported PC `030002A0` is immediately after attr0 store `0300029C`.
The exact count and pointer deltas independently connect the selected wrong
resources to this overflow. Stack data contains return address `085B6134`
inside the inserted opening callback 7.

## Why the undefined instruction was in IWRAM

This renderer is copied native code, not a newly generated overlay or a
decompression failure. Boot instruction `0800018C` loads literal raw `00039C`
(`08012C58`); DMA copies `0x60` words to `03000200`. Native wrapper `08012C28`
enters the copy at `03000204`. The copied `0x180` bytes have SHA-256
`D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685`.

The renderer checks OAM count against 127 on entry, then trusts the selected
frame's part count. Each emitted item advances the OAM destination by eight
bytes. The malformed count runs past the OAM buffer into other IWRAM owners.
The later dump in `build/physics-consumers-20261016-far-exec/iwram.bin`
(SHA-256 `A19133AC4D51A5F56B3CED985172C78838F8A1062EC4E5435EA2C2E0740A1255`)
contains repeated OAM-shaped eight-byte writes over the copied renderer and
stack. Its eventual `S04`, PC `00000004`, and undefined-mode LR `030032B2`
must not be interpreted as an ordinary valid caller chain. The renderer itself
is preserved; the repair fixes the malformed resource selection upstream.

## Guarded repair and independent validation

`tools/build_opening_presentation_routing_repair.py` consumes the fixed
physics-repaired predecessor:

`build/character-physics-routing-20261016/current-candidate.gba`

SHA-256 `8B91E5DA0147E16CC949785F73F6447878529B404949CB27EEA81B47275A77C2`.

Its only Expected Write is the four-byte literal at raw `0853F4`:
`080D42B8 -> 085B5400`. Three byte values change. The expanded view already
exists; no instructions, renderer, memory allocation, or asset bytes change.
Selector 13 now supplies `P0=082DA800`, `P1=082D9A94`, `P2=082F8D28`.
These are the proven commercial selector 7 resources reused for WSC1.5's
selector 13. Source constructor bytes at raw `756F05..756F11` explicitly pass
table `03C0`, slot 0, selector 13. The first eleven expanded rows remain
byte-identical to the retail view.

The builder checks every native layout entry in all fifteen expanded rows:
contiguous part extents, complete table/descriptor boundaries, and at most
36 parts per layout. This does not prove an arbitrary multi-object OAM total.
The independent verifier imports no builder. It checks the complete ROM diff
and exact inverse, 23 native consumer instructions, all old/new view pointer
occurrences, all fifteen rows' command-to-layout indices, and all 155 commands
and their tile extents for the repaired selector 13. Nine semantic negative
cases reject bad selectors, bad resource pointers, excessive counts, and
unrelated modifications.

| Artifact | SHA-256 |
| --- | --- |
| `build/opening-presentation-routing-20261016/current-candidate.gba` | `E2B700D26818148C0C196DC1C594AB5CE5FD6CBDD348384F7617D168CC62AE4D` |
| `build/opening-presentation-routing-20261016/manifest.json` | `1EF4CD8F0217D16D130E2FFB4226F763881C27217F43F39665F7920930474604` |
| `build/opening-presentation-routing-20261016/verification.json` | `E7E453C645762232D0B4668FEA6FA760A5C76F7DE1B50094144218841FB9C42A` |
| `build/opening-presentation-routing-20261016/overflow-analysis.json` | `A54BA3255116776AD07C8B0B8083EC7DA62E80F4FD9B973BBFE85F72EE8F8054` |

The last report is reproduced by `tools/analyze_opening_renderer_overflow.py`
from the frozen failed ROM and actual overflow probe. It independently
reconstructs the literal, resource, malformed frame, native copy, and loop
arithmetic; it does not execute an emulator or import a builder.

## Bounded runtime outcome and remaining scope

Root tested the identical repaired ROM on an invisible private desktop for
70 host seconds, with Start at 50 seconds and A at 55 and 60. The run ends
with manual `S02`, no asynchronous fault, a first-battle display showing
`1:57`, and live player pointers `02011710`/`02011828` with IDs 0/1. Capture
`build/runtime-opening-routing-menu-20261016/capture.json` has SHA-256
`51F21600F9167AE7E483B04D560FF2C8699C8A7AA5DE1AB0C26B90DC87829BA7`.
Its endpoint and loaded-ROM samples are verified. This shows the repaired
opening progresses to battle; it does not establish complete battle graphics,
added-roster behavior, or any later Shoot transition.

The one-literal repair also does not settle source callback 6's event/flip
differences, selector 12's later truncated tile descriptors, or the three
dynamic gameplay consumers still using the retail view. Those are explicit
separate implementation work, not silently included in this validation.
