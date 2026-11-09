# Bounded ordinary-input Shoot positive-hit probe

`tools/bizhawk_probe_gba_shoot_positive_hit.lua` is a separate development
driver for approved combined ROM 6D883A52. It accepts only `output`,
`checkpoint_dir`, and `probe_sha256`. It loads the genuine healthy68927
checkpoint, verifies all five RAM regions before and after immediate resave,
exports `restored.State` and `loaded-rom.bin`, and checks typed FIRST0,
SECOND3/idF, aux6, reciprocal links, resources, live mode7/stage11/gamekind2,
normal input/battle tasks, and HP4/37 before installing callbacks.

Actual first-input captures show A produces native held/edge0040, event4,
then at relative6 callback356D40/event8, Y1500→14D9, VY−609, AY31.
The upper callback becomes5BFC00 at X0E00/Y1880 and remains there through
relative6. The initial activation X1262/Y0DFB was replaced by route setup.
The probe preserves A1 plus five released frames. From relative7 it pulses B
every12 frames, repeats A every60, and holds one horizontal direction only
when upper/player X differ by more than24 pixels. It never presses Up/Down,
Start/Select, L/R, changes guest memory, or sets registers. This is a bounded
input experiment, not a guaranteed hit strategy. Native355898 tests attack
edge80; jump35582C tests40. The runtime checks actual input copies and A/B
held masks at375140. All buttons are released after the first confirmed hit
and at exit. Maximum execution is1200 ordinary frames.

The first FIRST→SECOND hit must have positive player HP and exact
`before > damage > 0`, positive `after=before−damage`, actual36E5E4 pre-store,
36E5E8 post-store,36E634 branch, and5CD9A0 adapter. At5CDA20 it verifies
victim+74=8, fifteen native P2 palette halfwords against5C0B08, and all24
red color-zero entries under the observed clear4030 mask. Each actual
586C7C store must count8→0 in sequence. Expiry must enter587000 through
LR586C90 with SECOND and zero timer, then reach587068 with the correct
HP-threshold palette. This is eight eligible updates, not eight video frames.
The script does not claim that all24 red entries are restored: the existing
owner restores16 BG zeros; OBJ zeros remain transparent.

Scalar hooks keep register/actor facts and first invalid producer, overlap,
scratch consumer, or dispatch evidence. The first failure is synchronously
written as text; full five-region dumps, screenshots and genuine State files
are exported only at outer frame boundaries. Hook and export epochs are
separately labeled. First hit, timer8 and expiry are separate evidence labels;
same-frame exports may contain identical memory. Action selector is actor+A0,
event+BA, command index/count+C6/C8, command+D0, event A/B+D4/D8;
velocity+42/+44, acceleration+46/+48, presentation facing flags+B4.

Terminal marker `shoot-positive-hit-done.txt` begins
`positive-hit-flash-expired` or `failure:*`. Player death, typed/live owner
loss, a second hit before expiry, incomplete adapter, bad palette/timer,
invalid dispatch/producer, script error, or exhausted1200-frame budget
cannot produce a successful marker. Actual BizHawk Lua54 compilation passes;
independent mocked API execution and actual gameplay remain separate QA.
No emulator, existing builder/observer, ROM, save, main, or Git was changed.
