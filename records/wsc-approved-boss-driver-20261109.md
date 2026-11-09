# Approved HP1 driver and real damage evidence

The user explicitly approved one original-reference boss HP reduction to1,
followed by an actual game hit. New driver
`tools/bizhawk_probe_wsc_saved_boss_hp1.lua` composes frozen saved-score driver
A0ACBDA6 with approved moduleCBD4EC42. It requires the explicit approval token.
The underlying driver still performs its complete normalized32KiB startup
comparison before loading any score or boss module. Input, all five frozen
policy files, score-only module and DI observer remain unchanged on disk.

The wrapper intercepts the existing score-module load, which occurs after that
startup guard, then installs the one-shot module and four bounded read-only
source hooks. No guest write API exists in the wrapper itself. The score
module still owns score999; only the approved boss module owns HP1.

- At760185, observe the original `SUB WORD[DI+50],AX` only when SECOND is the
  active typed/indexed/linked stage7 boss, DS0=0C00, DI=SECOND, prior HP=1 and
  damageAX is1..255. SI is recorded as the engine attacker; it need not equal
  FIRST. Callback/kind/index/id are captured for valid attacker payloads, and
  only SI==FIRST is labeled direct-FIRST ownership. Child ownership is not
  invented. This allows genuine delayed/projectile hits during death windows.
- At760188, require the same PS, PC=prePC+3, DS0, SI, DI, SP and AX. Read the
  actual result and require HP=(1-AX) modulo65536 with signed HP<=0. Underflow
  is valid and is not incorrectly restricted to exact zero. Only one pair is
  captured, with bounded pre/post RAM/SRAM snapshots.
- At7417F3, observe the pinned source `PUSH5; LCALL71F0:0000` branch with the
  owned pair, DS0=0C00, DS1=1000, BX=SECOND and nonpositive signed boss HP.
  The branch is recorded separately from the preceding damage pair.
- At7417DB, observe the competing pinned root4 call with FIRST HP0/state003E
  and BX=FIRST. It permanently cancels victory linkage for the one-shot attempt,
  retaining any damage evidence. Later retries cannot reuse the same handles
  to claim that first attempt's victory. The HP module is never rearmed.

Source damage setup760177 zero-extends the damage byte and optionally halves
it; the collision entry establishes SI as attacker and DI as victim. The
normal HP branches prioritize root4 over root5 and precede timeout. Three
exact source byte spans cover damage and both root calls; all match the pinned
C415 original. The wrapper compiles with the pinned Lua54 library.

The only in-memory change to A0AC is an additional completion condition:
one HP write, an observed real lethal engine hit, its subsequent native root5,
no root4 cancellation, and the existing positive Shoot DI/terminal evidence.
Thus `shoot-di-observed` requires this complete evidence chain; a run without
it retains `bounded-observation-complete`. Boss module finalization and a
truthful one-shot/hit/victory/cancellation summary occur before that marker.

Frozen candidate SHA256:
`FEB4253C8CE153C42CE0C7A4F2CA1DE1B268FB227F90E5A701A51C61E5F00008`.
Independent integration QA is separately owned. This authoring task launches
no emulator and accesses no save file or real guest state; root owns the new
hidden original-only runtime. No runtime hit, victory or Shoot result is
claimed by source pins, compilation or mocked checks alone.
