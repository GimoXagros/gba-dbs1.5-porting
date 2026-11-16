# Bounded ordinary-input evolution pause probe

Author source freeze: `tools/bizhawk_probe_evolution_music_pause.lua`
SHA256 `8ABD117B123BD7A501C8DC66E4301FF20AC2AE108C5E22E5B53064692C0EA535`.
Checker `tools/check_evolution_music_pause.py`
SHA256 `9CAF1B0015A66C2035F57B724744935289A612E32AF749B6AC3E19E28418D6E9`.
Run `python tools/check_evolution_music_pause.py --report <fresh.json>`.
Author result: `build/evolution-music-pause-probe-20261116/author-report-final.json`.
The earlier `author-report.json` predates the final LR guards and is retained.

The completed ordinary KO capture `bizhawk-result-v77-20261110-a` established
one natural evolution selector at core9075, actual player-zero 6E start-return
at9076 with header08D75728/cache6E, eligible devolution at10364, and actual
stage10 start-return at10365 with header08384BF8/cache10. It did not observe
pause or resume. This new probe exercises that remaining input route.

The source extracts the unchanged CE19C883 lifetime telemetry and composes
the unchanged 928186AE ordinary controller. Six unique exact replacements
change only full16MiB capture, the15000-frame cap, the post-6E button override,
the terminal check, explicit target-absence failure, and telemetry flush before
the completion marker. Effective source SHA256 is
`C41612BB0190CDBBDEF54325C9875A46467B3177B63DC9C63A85BCD5CBD33E5C`.
The 5D626406 wrapper is not executed or modified; its full-image dump change
is reproduced directly. Frozen sources and C344 ROM remain unchanged.

Before completed6E player-zero start-return, input is exactly the ordinary
controller. Then the input schedule is4 Start frames,30 neutral frames,
4 Start frames, and neutral until natural stage return. Only actual Start
input is introduced: no guest memory/register/state writes, cheat, save
loading, random/bot battle movement, or forced evolution. It bounds the run
to15000 total frames and3000 after the evolution witness.

Read-only observations retain the original ten hooks and add actual MPlay
stop0837C9C8 and resume0837C1A8. The witness requires native pause0837B48C
or resume0837B4A8 in its scheduled phase, matching header comparison at
0837C364/0837C398 in that same core, player-zero pointer03006B40, and the
actual Thumb caller LR0837C36F/0837C3A3. Every neutral hold frame checks
header/cache6E and status stop bit31; boundaries at ages4/33 log that state.
The age38 boundary requires matching active header/cache and cleared stop
bit after real resume. No actual sound/output playback claim follows solely
from these status observations.

Only after that boundary can an eligible native devolution site, still with
active6E and running status, arm completion. Stage10 must then reach actual
player-zero start-return within two cores. An unexpected player-zero restart
fails. Successful completion is `evolution-pause-resume-stage-return` in
`result-done.txt`; absence or unrelated ordinary result cannot count. Logs
are closed before that marker. Arguments remain output/language/frames/
start_frame; existing prebattle captures remain, with a terminal pause-end
capture. Event rows are capped per label32, conservatively448 total.

The author gate uses actual Lua54, checks the complete effective composition
and syntax, and exercises10 mocked scenarios: success, absence, wrong cache,
missing stop, wrong player, stale comparison, missing resume, premature
return, foreign restart, and deadline. This is source/policy verification;
root owns independent review, host, emulator launch and actual runtime proof.
No main source, Git, host, emulator, or old full-suite operation was performed.
