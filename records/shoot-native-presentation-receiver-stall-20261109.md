# Actual entry stalls at presentation completion

The completed native D0 run `build/bizhawk-gba-shoot-entry-20261109-b`
reached the real healthy case5 path: actual FIRST hit changed stage7 boss HP
1 to 0 at core66972 with FIRST HP4. Scene entry saved4 at core66973. At the
120001 bound, the initializer had not run. This is a presentation receiver ABI
defect before initialization, not a failed case5 predicate or unhealthy entry.

The initial completed `12-scene-saved-health` RAM export at core66974 has
scene task `020121E8`, active status2, callback `085C8100`; its payload
`02012200` has timer150 and savedHP4 after the immediate first countdown.
The final RAM has that same active task with callback `085C8400` (source
`71F0:10DD`), timer6, savedHP4. FIRST X=`0DCB` is inside the required strict
`0DC0..0E40` interval; the positioning and 200-call phases already completed.
Input and battle task callbacks remain the intended `08374FAC`/`0837354C`.

At final RAM, `03004508=0002`. The exact waiting instruction is `5C8418`
`TST r2,#10`, with `5C841C BEQ` returning without changing timer6. Source
`772FF6..772FFF` waits on the corresponding `1000:03D6 & 0010` event.

The first presentation exists and runs: actor `020112B0`, callback
`085C9100`, kindB, target `+14=02011828` (stage7 upper boss), opponent
`+18=02011710`. Its final X/Y are `13A1/0CFB`; the target is `13A1/0D2B`.
Both differences lie inside the completion box of inclusive +/-0100. The
scene should therefore receive its event and release this presentation.

## Lost receiver across the real native angle helper

`5C9108 LDR r1,[r4,#14]` loads the target. `5C913C BL 08012560` computes
an angle, after which the callback calls the cosine and sine helpers.
`5C9174` and `5C91A4` then dereference r1 again as the target pointer.
However the real angle implementation enters `080126A4`; both division
branches explicitly overwrite r1 (`126DC MOV r1,r9` or `12700 MOV r1,r9`)
before calling `0837DB3C`. Neither angle nor trig restores the old r1.
Consequently those final box tests read an unrelated address. In the final
capture, an object already inside the true target box never reports event10.

Source `7735D4` puts the receiver in BX and `773611/773624` use BX again
after its angle/trig calls. The translation assigned that lasting receiver to
a native scratch register. Its full outer register save does not preserve r1
*between* the nested calls.

The no-cave proposal is five instruction-word changes: use r6 as the receiver
at `5C9108`, and use base r6 at `5C910C`, `5C9120`, `5C9174`, `5C91A4`.
The complete homing callback already saves/restores r6. The bounded native
angle and trig instruction bodies do not use r6. A repair must still check
the native division boundary explicitly and demonstrate the real callback
event/release and outer register/frame restoration; this record makes no
patched or actual-runtime repair claim. No flag forcing or timeout bypass is
appropriate.

Original bytes at those five sites, in order:
`141094E5`, `F403D1E1`, `F633D1E1`, `F403D1E1`, `F603D1E1`.
Existing homing body `5C9100..5C9208` SHA256:
`A150F3C5A715F6131D6DB358676C75E011482B14C6BF331E807076CF2395CB0D`.

Capture SHA256:

- Final EWRAM: `64F86BFA9A8EE96086998E2FF7294BDB1D4212457E2F7263EBAE3674B8EF5ACB`
- Final IWRAM: `BC10319BFC772FCE8D379D02E78061B9D2C00E21116EA19A47EBE9DCA3929B12`
- Initial saved-health EWRAM: `678E647941542B110DCE71D43BE95F1333C924ABC6EB68502798D7ABE42A905C`
- Initial saved-health IWRAM: `81BC812F7309B26237430B788AD119A086D5F3026E2620F0EAE706378685500F`

Read-only diagnosis only. No ROM, observer, running process, checkpoint, or Git
state was changed. The separate nonfatal caller component was left uncreated
while this earlier actual-entry blocker was investigated.
