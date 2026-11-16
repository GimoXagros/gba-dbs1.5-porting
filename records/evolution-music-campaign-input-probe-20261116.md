# CPU11 campaign probe: bounded score assistance

Use new `tools/bizhawk_probe_evolution_music_campaign_r2.lua`, SHA256
`337EBF093EC6591CC8B39A07CB5A33C120453C66B36975CC6E43305B749BF6BD`.
It composes frozenB93 three-song probe. Earlier BDAC campaign source remains
unchanged and is superseded: its CPU-kind0 predicate incorrectly excluded
the actual ordinary CPU, whose low-nibble kind is1 (frozen6E final RAM F721).
The r2 source differs only by correcting that predicate from0 to1.

Author checker `tools/check_evolution_music_campaign_r2.py` SHA256
`7F581FB5B1A2DB5A710E3B1BCCBB0CA790F4D0C7C8995ACC3B0AA5127FCA5D6C`
passes8 score-guard cases and6 native result-mode continuations in actual
Lua54. Report and complete composed source are in
`build/evolution-music-campaign-probe-20261116/r2/`.
Effective source SHA256:
`6B5918CDC2430120F65172C3CC3CC4F9FB9A119E1B0A0A9B0F7852810B365234`.
Run `python tools/check_evolution_music_campaign_r2.py --report <fresh.json>`
from the repository root, with a fresh output directory.

Parameters: target_song111, language2, frames60000,
score_authorization=`user-approved-development-score999`, and the usual
output/start_frame. The actual target pause/return deadline stays3000.
This selects default player0, requires native Normal difficulty1 and uses
neutral battle input. Ordinary A pulses advance native result/VS screens;
real Continue or title return fails. Every capture has a roundN prefix, so
new bouts cannot overwrite earlier evidence. No mode, stage, progress,
unlock, player HP, CPU HP, register or ROM changes are made.

The sole authorized development intervention is an EWRAM u16 write of999
to the live P1 score field at actor+66 when its current value differs.
Guards require ordinary mode7/game kind0 with active gameplay, two distinct
live pool objects, P1 kind0/index0/id0, CPU kind1/index1, reciprocal self and
opponent links, and both HP positive. The code verifies score readback,
unchanged P1/CPU HP and unchanged following four bytes. At most512 writes
are allowed. Each write is immediately flushed to `score999-writes.txt`
with core, round, actual progress/stage, actor/address, old/new value and HP.
The assistance ends when the target evolution arms the pause protocol.
This is score-assisted gameplay, not an ordinary no-write capture.

The source route discovered independently can schedule CPU11 through the
native campaign challenge condition. Hook0808B694 records the decision
R0=11 before the branch to the eventual assignment; its logged global CPU
byte is explicitly pre-commit. The successful evolution witness separately
requires actual globalSECOND/index1/id11, the selector's stack identity and
source category3. Periodic bounded campaign rows retain native progress,
stage, flags, actor identities, score, HP and callbacks.

**Activation remains an unresolved source risk, not a success claim.**
The current native Calumon collision special-cases Impmon11 at3546F8/6FC:
354704..354734 calls36D734, while normal354744 installs fighter callback
35A0F8. The special Calumon callback is36DEEC. Root and independent QA were
alerted to compare the source route before a long capture. Reaching CPU11
does not itself prove that it can naturally invoke category3 music.

No emulator, host, save, ROM, main file or Git operation was performed.
All earlier sources and captures are preserved; actual campaign completion
and music pause/return remain unobserved by this author.
