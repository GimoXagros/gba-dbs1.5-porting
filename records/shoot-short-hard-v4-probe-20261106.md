# Final recovery jump after a ground-input callback

The final v4 variant keeps frozen v2's menu, ordinary chase, collection and bounded wall-recovery behavior. During a recovery it waits for default Agumon to reach a source callback that accepts a fresh jump edge, then holds A for twelve samples. It starts at most one pulse, at age4..48, so the entire pulse fits inside the original60-sample back-away. If no acceptable state appears by48, it skips the jump; it does not extend recovery or add a navigation planner.

The actual v2 first escape begins at frame18586 in airborne callback668E:19D0, actor6=9601,48=0,Y0FC8,VY250/AY22, short-jump latch8C=1. Evolved identity0 does not accept an ordinary jump edge in that callback. The no-hit recurrence reaches the observed floor1100 only after about13 updates. A fixed edge atage4 can therefore be ignored before landing, and continued holding cannot recreate a fresh edge. This is why merely widening the original fixed pulse was withdrawn before launch.

The accepted callbacks are segment668E offsets115D (idle, source767A3D) and11C9 (walk,767AA9). Their actual paths call jump helper1D6 at767A5B and767AC7 before ordinary movement. Earlier attack helper224 tests edge80, while helpers36D and175 require Down; recovery supplies B=false and only accepts the start when Down is false. The jump helper766AB6 tests fresh edge40 and selects startup16E8/event4. The host additionally requires identity0, airborne bit6:1 clear and form flag8:100 clear. Base and evolved default forms share these accepted callbacks. Landing callback1D9F is deliberately not accepted because its animation-completion branch can return to idle without polling the edge.

The source's evolved event4 needs nine held samples in an uninterrupted startup, as documented in `shoot-short-hard-v3-probe-20261106.md`; the chosen pulse supplies twelve. Four initial released samples and waiting with A=false establish a fresh edge. A later external hit or pause can still prevent acceptance or interrupt startup; neither source inspection nor host mocks claim otherwise. A new `escape-jump` log records the actual chosen start for runtime evaluation.

Unchanged v2 behavior includes90/8 ordinary chase,45/5 collection, boss policy,180-sample stationary trigger,60-sample back-away,360-sample cooldown, reset behavior, cap3 PNG/RAM captures and original final-release bypass. There is no v3 global hold extender. Before the first recovery this is the same input policy for identical observed states; actual fresh-run trajectory identity must still be observed.

Final frozen files:

- `tools/bizhawk_probe_wsc_shoot_short_hard_v4.lua`: `70B73AB398EAEEC83B117EEF06DD5FFFCEF9B7FACDA107C656B5E140F1D08C91`.
- `tools/verify_wsc_shoot_short_hard_v4.py`: `A550927476A9DA3871565BA04E2ADE47E69F875E039EF92F840AC5F59E3DB284`.
- `build/shoot-short-hard-v4-20261106/mock-b.json`: `57E9E06FE2255C545FCFE3A1F93D16CD285B7A5E8DFA276F8F38FF8C3367FF57`.

The actual Lua chain passes22 inherited routes. Seventeen focused scenarios execute the actual expanded recovery policy for airborne-until13, start48, too-late49, no landing, default base/evolved walk, every acceptance guard, one pulse, next-recovery reset and existing mode/stage/player/frame cancellation. Eight source/host mutations are rejected, including short pulse, missing initial release, clipped late pulse, airborne callback acceptance and stale pulse reuse. All underlying observer files remain hash pinned. No completed broad domain proof was repeated.

The withdrawn unlaunched fixed-age wrapper2ECB80B5, verifierB76232E0 and report977BC236 are preserved byte-for-byte under `build/shoot-short-hard-v4-20261106/withdrawn-fixed-age/`. Their host-only PASS does not justify launching that old candidate.

Root alone may launch the final candidate after independent review, using the existing fresh isolated configuration and userdata schema with Lua entry `W:/tools/bizhawk_probe_wsc_shoot_short_hard_v4.lua`. Pin final70B7 plus frozen v2/E382/hard/collector dependencies. Keep the120000-frame/1500-second bound and truthful partial-stop/positive Shoot-clear-IRQ completion rules. This is the last planned policy variation here. Clearing the obstruction, winning Stage1 and reaching Shoot remain hypotheses to test; no successful runtime is claimed.

Independent final review passed:22 full Lua routes plus17 acceptance cases and8 negatives reproduced57E9 exactly, and source idle/walk poll sequences were reviewed. See records/shoot-recovery-grounded-v4-qa-20261106.md. Root subsequently launched exact70B7 in a fresh isolated capture; launch itself is not a navigation or Shoot success claim.
