# Campaign entry: READY versus running fight — 2026-11-17

The first933C observation proves the source producer's stage8/CPU13 entry,
but its121 actor-boundary samples do not prove a running fight. Both retained
IWRAM dumps hold the initial clock7200 (`1C20`) and pause byte0. The input task
still uses a callback which clears P1 input rather than advancing the clock.
There is no ROM defect established by this early stopping condition.

Evidence is the immutable r2 candidate SHA-256
`933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775`
and `build/bizhawk-campaign-entry-v80-20261117-a/` first/stable-live IWRAM/EWRAM
dumps. At both retained boundaries, global03004510 points to task02011D88,
whose callback is08374E6C. P1/P2 bodies are02011710/02011828. The first actor
callback is083561D8 and the stable callback0835620C; these ordinary idle-body
callbacks alone do not distinguish READY from running play.

## Actual input and clock owner

The initial task is allocated at080D1BD4 with callback08374E6C and its pointer
stored to03004510 at080D1BE0. Its callback08374E6C..4EF8 updates presentation
and at08374EB0/B4 explicitly zeroes P1 held/edge fields+2C/+2E. It has no
battle-clock decrement. The observer's prior setup and pause conditions can
therefore be true while input remains suppressed.

The separate READY presentation task advances through callbacks
083779E8→08377A7C→08377AF8→08377B10→08377B3C→08377B54. The first two wait
for presentation flag+0A bit2000 before moving on. The remaining steps perform
object/stage setup. At08377B68 it resolves03004510, pushes the actual task,
and at08377B78 loads the new callback08374FF4 from literal08377BC4.
The08011E7C call at08377B84 replaces that task callback;08377B88 is the
immediate after-call observation point. No new callback is introduced here.

Running input callback08374FF4 calls08352B10, which tests pause byte03004529
mask07. If the mask is clear, it loads the clock from03004500 at08375010,
subtracts1 at08375014, and stores it at08375018 (`E1C890B0`). The immediate
after-store hook0837501C (`E59F8150`) still has R8=03004500 and R9 equal to
the newly stored clock. This is a positive clock-producer witness.

Later in the same callback,083750F8..75104 load the ordinary held/edge words
from03001302/03001306. After its input transformation and pause-bit4 gate,
08375138/13C write them to the selected P1 body+2C/+2E. A zero input value
is valid; entering this assignment proves the normal input path was reached,
but does not prove that a nonzero user action was exercised.

## Bounded continuation predicate

Keep the existing stage8/CPU13 producer and both getter witnesses. Retain the
actual live actor pairing, mode7, progress0, physical stage8, and pause-mask07
checks. Add the following positive running evidence:

1. Resolve03004510 as a normal task **header**, in02010000 plus52 slots of118
   bytes. It is not an actor body and must not use the body's+18 alignment rule.
2. Require that task's callback word to equal08374FF4, replacing08374E6C.
3. Observe0837501C with R8=03004500 and RAMclock=R9, with0<clock<7200.
   Optionally bind the preceding store's old clock as new+1, and retain the
   actual08375138/13C P1 assignment in the same running callback.
4. Start the tail only at this first running boundary; require120 additional
   qualifying boundaries and a decreasing positive clock. Capture the final
   frame and actual clock/task/actor state.

This gives a concrete READY-to-running transition and sustained clock activity.
It does not by itself prove a completed battle, subsequent campaign stages, or
final boss/Shoot completion. The read-only continuation may extend ordinary
input time; no stage, clock, callback, register, or guest-memory writes are
needed. The frozen933C ROM and both campaign builders remain unchanged.
