# Added-stage runtime follow-up — 2026-10-16

The v57 checkpoint remains a reproducible prefix. Its natural character-13
route initialized Train graphics but retained a null BG0 collision pointer,
used progression-stage updates/spawns, and selected wrong source maps. The
temporary character-to-arena route is not a complete campaign implementation.

## Collision-only observation

Candidate `7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD`
was run through normal input on a private Windows desktop with the pinned mGBA
binary. No supplied save was accessed and no game-memory writes were used.
Start at 50 seconds, A at 55, eleven Down presses at 56..61 in half-second
steps, A at 65, capture at 77 seconds.

Evidence directory: `build/runtime-collision-id13-20261016`.
Capture manifest SHA-256:
`20DA6F22D16A58D46840F5A1293C6B593F94BF41F5DF5DB75C868036CE1A53BA`.

- Character byte `0300231A` is 13; progression byte `0300231E` is still 1.
- Active BG0 collision pointer `03002360` is `08622000`, proving the bound
  source grid reached the native background owner.
- First fighter world coordinates at `02011744/46` are `129F/0BC4`, rather
  than the previous capture's below-stage `D08A` Y coordinate.
- The OAM producer count is 9; hardware OAM contains 32 enabled entries.
  The previous v57 added-character capture produced zero objects.
- Final debugger stop is the requested `S02`; no asynchronous fault was seen.
  Copied renderer bytes still match the original USA routine.

The screenshot list is empty in this capture. These memory observations do
not establish visual correctness, full collision behavior, or complete stage
effects. The independent collision verifier separately proves exact source
cells, bounded class selection and expected writes. Train graphics, logical
spawn selection, and the Iraira class-14 effect are subsequent layers.

## Logical-stage spawn observation

Candidate `83B80FAAF0B983B9FC3BD4085FF682C07D28EC9DEA8362F2BDE2534E341E43FD`
was reached through the same natural character-13 menu input. An execution
breakpoint at `083530CC` then a write watchpoint at `02011744` recorded the
initial coordinate store, before subsequent movement could mask its origin.

Evidence: `build/logical-spawn-writes-id13-20261016/probe.json`, SHA-256
`DEB4D84BD0787FFDB1897A0A3D78431A93AEE69F7045A0A278AB4CE7B89AAEF1`.
The constructor receives character ID `0D`. At `08582F4C`, the first X write
uses source-table index `90` (hex) and value `0400`. The next movement write
has X `03FA`, Y `0B80`. This is the source Train row, replacing the earlier
progression-stage-1 spawn (`1080/0700`). The debugger's `S05` and watch stops
are the requested instrumentation, not faults. The probe records no guest
memory writes and no monitor-visible window. This closes the observed spawn
consumer mismatch; it does not certify Train graphics or campaign progression.

## Train graphics observation

Candidate `96638ACB58BD615B35C306B886C03F1A6206ADB0B4123AB539D7D03DEC12D530`
was run with the same natural character-13 input and 77-second capture.
`build/runtime-train-repair-id13-20261016/capture.json` has SHA-256
`5E373FCF33C085A9CD3C8D39A482DAF316631E7D20DD35841052747C6FCD1775`.
The native screenshot `current-candidate-0.png` has SHA-256
`A1718E1F1C95A5A595AEFE35FB22BACA38BF4F2C97652DBBC4B2557135DD091F`.

The screenshot shows the Train foreground, mountain background, both fighters
on the train, and timer 1:55. The former large flat-color background and absent
fighters are not present in this observation. The first fighter is at world
`0400/0B80`; the OAM producer count and enabled hardware entries are both 28.
BG1 at `03002388` has source geometry 48×2; native tile 0 is blank. Final stop
is the requested `S02`, with no asynchronous fault and intact copied renderer.

This is a bounded visible/runtime result, not proof of every stage action,
long-run timing, collision boundary or Train hazard. The source-only hazard
seed/private state machine and temporary campaign routing remain incomplete.

Independent review also resolved an apparent scroll-owner mismatch without
changing ROM: native `08017768..17798` copies `03002478..03002607` to the
display snapshot at `03004578`. Producer `03002568` therefore becomes consumer
`03004668`; normal frame `080D0BE8` performs the copy before the queued display
callback. Source `768FD7..FEB` has the matching `0330`→`00A6` snapshot role.
These distinct producer and display addresses must not be collapsed.
