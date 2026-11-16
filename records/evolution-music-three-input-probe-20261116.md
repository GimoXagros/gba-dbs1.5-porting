# Remaining evolution songs: ordinary menu/contact probe

Author source: `tools/bizhawk_probe_evolution_music_three.lua`, SHA256
`B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881`.
Checker: `tools/check_evolution_music_three.py`, SHA256
`69915CF6EB6760696ECCB09D5DDB7FFCBB7AB1172013184753CBB26F985A6376`.
Run `python tools/check_evolution_music_three.py --report <fresh.json>`.
Report: `build/evolution-music-three-probe-20261116/author-report-final.json`.
Effective source SHA256:
`1A614096DADF265224FD783BD2EFDEC2DA05B6CD0B103E27E4693D6B717DF283`.

This new source retains the frozen450AE932 pause/alias protocol and CE19
telemetry over the9281 ordinary controller. Every frozen source remains
unchanged. The new userdata parameter is `target_song`, decimal108/109/111;
110 is refused because6E is already observed. Existing output, language,
frames and start_frame parameters remain. The total budget is capped24000
frames; the post-start deadline remains3000. Marker/output names remain
the pause probe's names, including exact success
`evolution-pause-resume-stage-return`.

Mode4 selects fighter5 for6C/category0, or fighter3 for6D/category1. It reads
the native cursor/mirror and the installed immutable roster view at
08628000+((unlockByte&30)*2), using ordinary Down/A pulses. For6F/category3,
this menu profile selects fighter12 if legitimately unlocked by bit20,
otherwise11 if unlocked by bit10, and explicitly fails when neither is
available. It writes neither unlock flags nor score. A separate normal
campaign CPU11 route is under independent investigation; it is not silently
enabled here.

Native collision354678 reads the object's low-nibble kind. Kind8 at3546F0
reaches354744, which installs the actual evolution callback35A0F8 on the
fighter, followed by36D718; ID11 has its retained special branch. Spawn
36D5E4 reads the Calumon object pointer at03004CE8 and sets actor index2.
36D804/810 initialize world coordinates+34/+36. The contact helper requires
a live typed pool object, kind8, index2 and collectible flag1000;36D718 clears
that flag after contact. The selected P1 must have a live reciprocal P2 pair,
index0 and the expected selected character. It moves toward Calumon, pulses
A when Calumon is above, and never attacks. Native1190C/11910 maps A to jump
edge40 and B to80, independently confirmed by the earlier actual input QA.
There are at most200 scalar diagnostic rows, every120 frames, recording
actual pointers, identities, coordinates, callbacks and collectible state.
Movement reachability is not established by these source facts or mocks.

Either fighter can supply the successful natural evolution witness. The
actual selector's entry stack identity must equal actor+11 and the exact
sixteen-byte source category table must map it to the requested song. The
actor address, identity and side are retained through devolution. A song
header alone cannot arm the input schedule.

Stage restoration is not hardcoded to10. Hooks at native stage-selector
D149C/D14A0 observe its queued song and successful pending request, then
actual player-zero start-return establishes the current stage header/cache.
Only that verified stage baseline, still actively playing when the target
evolution selector runs, can arm the target cycle. After successful actual
pause/resume, the same actor's eligible devolution must queue that stage
song through the native selector, dispatch the real request, and reach the
player-zero start-return within two frames. Another evolution song is never
accepted as the stage baseline.

Author verification uses actual Lua54 for39 scenarios across the three
parameters, including wrong category/cache/stage request, locked roster,
missing stop/resume, wrong player, stale compare, early return, restart and
deadline. It also checks typed Calumon contact inputs, canonical alias
failure, exact complete composition and syntax. No emulator, save, ROM,
host, main file or Git operation was performed. Runtime reachability and
independent preflight remain separate work.
