# Ver. 1.5 final-boss route and GBA integration

## Evidence boundary

All observations in this record are static ROM analysis. The supplied WSC
SRAM was not opened or used, and emulator/runtime validation remains deferred
until the complete content population is integrated.

## WonderSwan Ver. 1.5 route

The Ver. 1.5 battle initializer at raw `0x740C97` derives its setup selector
from the current mode and adds two when stage `7` is active. Selector `2` uses
the dedicated setup path at raw `0x740D6E`; its additional boss setup is called
at `0x740E23` and resolves to raw `0x7455A6`. That routine assigns runtime
character ID `15` and loads the Zeed container at `0x3BE710`.

The common damage path at raw `0x760191` selects one of two boss-death state
machines. Stage `0x0B` has its own special path. For the normal campaign:

- difficulty `0` takes the ordinary completion path;
- difficulty `3` takes the extended boss path;
- difficulties `1` and `2` take the extended path only before the global
  completion/continue gate has been set.

The two state machines begin at raw `0x745F0E` and `0x746036`. Their movement
and timing sequences are structurally identical, but the first waits for
effect-completion bits `0..2`, while the second waits for bit `3`. The result
dispatcher at raw `0x771F69` applies the same difficulty and continuation
split. This establishes a real conditional second-final-boss transition, not
an unused Zeed graphic.

## Zeed graphics ABI proof

The original WSC boss header `0x2A5470`, the Ver. 1.5 Zeed header `0x3BE710`,
and the USA GBA boss header `0x34E27C` all contain 17 layouts and eight tile
payloads. The complete `1,116` layout-record bytes are byte-identical between
the Zeed source and the native GBA boss:

`07772EC9E40EAD1EDCF6BE4E7CE87FCB6CECFF219CF80AE9AC522D3D24D6AC9A`

All eight descriptor lengths also match. Converting the eight WSC planar
payloads therefore requires no inferred frame remapping. The converted Zeed
palette is byte-identical to the retail GBA boss palette.

## GBA integration

`tools/build_boss_integration.py` consumes the progression-integrated build
and the deterministic Zeed bundle. It makes three checked changes:

1. Complete the boss sentinel relocation by changing the dedicated boss setup
   assignment at `0x36FD84` from ID `12` to ID `15`.
2. Replace the sprite-header load at `0x36FDE8` with a selector that uses the
   retail Millenniummon header for phase one and the relocated Zeed header for
   phase two.
3. Replace the boss HP read at `0x340344` with a checked hook. On the first
   zero-HP event, ID `15`, Normal-or-harder difficulty, and a no-continue run
   set private run bit `0x8000` and reinitialize the boss object with the Zeed
   header. The second zero-HP event clears that bit and resumes the retail
   completion path. Easy or continued runs retain the retail one-boss path.

The current internal artifact is `build/full-integrated-v31.gba`, SHA-256
`16F4C7A827F3F9D241A3E5C2AE3D2EB2803447F7693BDD1F88400EA2D97BE4AC`.
It is built from current stage v30 through progression v5 before the boss
layer, rather than retaining the older isolated boss candidate.
It is not a deliverable ROM. Runtime transition, loss, continue, and second
victory behavior are part of the single final integrated validation pass.
