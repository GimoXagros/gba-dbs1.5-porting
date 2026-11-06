# Terminal owner and camera lifetime — 2026-11-05

This narrow continuation uses the immutable WSC1.5 source and existing reviewed
terminal/IRQ code. It does not open an external caller or assert a runtime result.
`tools/analyze_shoot_terminal_lifetime.py` produces
`build/shoot-terminal-lifetime-20261105/evidence-final.json`.

## Exact source destination must determine the implementation

The source `197A` operation remains `DI=(0800+(BX<<6))&FFFF`, followed by
64 zero halfword stores. The input callback `07D6` leaves BX equal to BG0's
pixel camera Y and copies it to `0C00:3A16`. Its scheduler ownership through the
terminal callback and the actually reached value still need evidence.

The original Shoot graphics initializer positively assigns:

| Source owner | Range / use | Producer |
|---|---|---|
| BG0 descriptor `1000:01CE` | map `1000..17FF`, logical ports12/13 | `77DD9A..77DDAA` |
| BG1 descriptor `1000:020E` | map `0800..0FFF`, logical ports10/11 | `77DDE1..77DDF1` |
| HUD map | first four cells `3000..3007` | `77DE2E..77DE46` |
| Transition scratch `0300:00EA` | physical `30EA..30F7` | `773895..7738C5` |

Common-bank tile graphics start at physical4000, while the separate stage bank
loads at8000. Therefore a wider camera input cannot simply continue the native
screen-map offset calculation. As an arithmetic witness only, BX268 clears
`4B00..4B7F`, four common-bank tiles. A real implementation must reproduce the
reached owner's effects, not clamp BX or ignore the operation because it lies
outside the present screen-map helper. No claim is made that BX268 was observed.

The full collision grid independently has only values0/1/2/3 and all auxiliary
words zero. In center columns24..32 the first platform is row42 (336px), followed
by the floor at row50 (400px); rows above42 are empty in those columns. This
positive geometry does not support inferring cameraY<=62 from the forced jump
or a grounded flag. The sibling's player lifetime work owns exact reachable Y.

## Three concrete refill paths are narrowed

The previous IRQ row-coverage proof still applies: 1,678,080 source line/base/count
cases sample only rows cleared in earlier updates. The new checks establish
which concrete code could repopulate those rows:

1. In scene battle callback `0B8B`, equal current/previous P1 X and Y yield zero
   movement after the actual `FFF0` masks, for all65536 coordinate words on each
   axis. CX remains zero and `7415A2` skips both camera3367 and bounds11BC. Thus
   the latter cannot copy BG0 velocity into BG1 on that stationary path. The
   initial tests of screen coordinates and negative Y only skip more work.
2. When stage update `0E0B` completes0200, it zeroes BG1 velocities before setting
   0400. Its subsequent0400 path performs row clears, with no BG1 camera call.
   Ongoing1000 shake is **not** a general camera freeze: it explicitly calls3367
   for BG0 descriptor01CE, whose map is1000, not the cleared BG1 map0800.
3. Terminal1A42 sets Shoot20 before1B15 sets0200. Timer helper989C's actual4030
   test excludes its scroll call while20 remains owned by that terminal path.

A positive callback-ownership check also excludes the three ordinary collision
consumers during this terminal path. Scene root771F53 installs0B8B in the real
battle task. Normal0D0B calls7426B0,7427FB and74273B at74161F..74162F. The first
intersects the registered hit/victim rectangles then calls5FFD:0000;74273B adds
to the actors' +3A displacement fields for body pushing. Complete decoding of
0B8B checks its entire nine-call population, which contains none of these three
consumers. This is a concrete exclusion of ordinary hit, pair-command collision
and bodypush processing, not an assumption that the boss is already harmless.
It applies only after the terminal task replacement; ordinary Shoot pursuit
uses the restored0D0B callback and cannot inherit this exclusion.

These are conditional code facts, not a complete stationary-player proof.
The remaining concrete requirement is that post-ground P1 current/previous
coordinates remain equal through0400, accounting for its real callbacks and
existing hit/object owners. The sibling has positively identified neutral idle
and landing velocity resets; those alone are not substituted for that lifetime.
The absence of conveyor/force metadata is now a checked source fact.

## IRQ and common tile zero

Final callback0DEC still reads `0300:[interruptedDI+A]`; its local `BX=EA` does
not change that effective address. The reachable common tile-zero initializer
at755916 and the existing source row-coverage result are reused. Uniform tile
preservation through the final sampled lines remains to be connected to the
actual transfer/object lifetime. Neither a guessed DI nor an omitted visible
write has been installed.

The smallest useful natural-execution observations are7738CA (liveBX and full
64KiB source RAM),75FC98 (actual DI+A read),75FD36 (enter0400),75FD87 (cleared row),
and the camera/parallax entry sites. Root owns those read-only observations.
No provided save, emulator launch, source execution or guest write was used here.

## Checks and artifacts

The analyzer checks the complete source identity, exact decoded owner/control
sequences, all3024 grid cells, 131072 coordinate equality cases and eight semantic
mutation negatives. The source mutation tests bypass the full identity guard so
that the actual instruction predicates must reject the changed behavior.

- Analyzer SHA256: `DD760E9426C12D0C89F01CE1259C1E006D5A9662C3BD6ED1957B8F914E09BF3B`.
- Evidence SHA256: `E26DB8A79B215058DFFA6ECF9498870B1236BE9BEDA49F9B2262C37B5E9E3B4E`.

The separate actual resident-code result is documented in
[the synchronous caller component](shoot-caller-resident-20261105.md). There is
no invented requirement to prove the absence of every possible SRAM alias:
source distinct writes remain represented by EEPROM block25, and this work
identifies no missing positive SRAM reader on the translated Shoot path.
