# Ordinary-input ground interception wrapper

Frozen NEW `tools/bizhawk_probe_gba_shoot_positive_hit_aim.lua` SHA256
`00D1579B828E14AA55EEACE35A17E5BD9B203E74B0C950B34018794A8D783938`
loads the unchanged9F12 positive-hit observer. It normalizes CRLF to LF,
matching Lua long-string semantics, then makes exactly two unique,
literal substitutions: the approved ROM identity becomes1477F90E, and the
ordinary-input policy changes. Argument names, healthy68927 load/full-five-RAM
verification/resave, actual hit/flash/eight-update gates, failure hooks,
captures, marker and1200-frame bound remain unchanged. Actual wrapper
execution under the BizHawk Lua54 DLL consumes the raw observer,
performs both anchors, and verifies the entire generated source against
normalized9F12 plus exactly those two substitutions. The effective source
compiles and hashes to
`02D6B04C6072B53C15067E9C6A3235B9B04079635E994C38222642807E2754F6`.
The current9F12 observer has180 LF and zero CRLF. The earlier ED51 draft
was withdrawn for line-ending portability hardening, not an observed
current-file anchor failure. Independent QA also tests a synthetic CRLF
serialization of the same logical observer.

The previous1477 trial completed1200 frames through70127 with HP4/37 and no
accepted hit. Its first ground interception window begins68999 (relative72):
FIRST=(3584,5376), upper=(3698,5622), upper event1. Earlier traces show
repeated event57 attacks lasting about35 frames and consuming every A retry
while facing left. The descriptor080FDA20 has input/motion flags+0C=0;
held Right therefore cannot turn or move during this attack. When free,
running checks attack before jump/motion, so repeated B immediately locks
the next attack before ordinary movement executes.

The new policy first holds Right only while grounded, unfrozen, and in
idle/run callbacks35620C/3562B4/3562E4 until presentation+B4 bit4000 confirms
right-facing. It then releases direction and waits. A B edge is eligible
only in those same free callbacks, with prior actor B released, upper event
1/4/5, upperX−FIRSTX in96..384, and upperY−FIRSTY in128..256. It releases
through the complete attack/recovery and can retry only after a later free
callback satisfies the same predicate. It never presses A/Left/Up/Down or
changes guest memory, HP, positions, velocity, flags, callbacks or registers.
After the first confirmed hit the frozen observer releases all inputs.

Event57 command indices3/4 contain direct type8 attack rectangles at0D7940
and0D794A, with offsets(−352,−160)/(−496,−128), half extents136/136 and
120/104. Right-facing mirrors the X offsets. Upper vulnerable event1/4/5
has a112/112 victim rectangle. The ordinary producer uses FIRST as the list
owner and collision36E3B0 loads that owner as R4; this is compatible with
the unchanged direct-FIRST hit guard and requires no projectile ownership
normalization. The first active rectangle arrives approximately14 frames
after attack start in the observed timeline. The chosen window aims at the
upper's first upward passage; it is a source-informed input experiment,
not a promised collision or a predeclared success.

No frozen observer/wrapper, host, ROM, main, Git, emulator or save was edited.
Independent Lua execution QA and actual gameplay remain pending.
