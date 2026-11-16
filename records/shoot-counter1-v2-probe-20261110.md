# Natural counter1 v2: bind the complete witness to one core

The independent reviewer found a real v1 evidence gap: actual Lua54 could
observe first compare at69937, then accept all eight remaining matches,
stores and final callback at69938. V1's local compare/match checks did not
bind the complete target cycle to its initialization core. The frozen
C625 file and its earlier author report remain unchanged as history.

NEW `tools/bizhawk_probe_gba_shoot_counter1_v2.lua` reads immutable C625
and adds exactly six `target.core==emu.framecount()` guards, one after
each target-presence gate at first IRQ entry, compare, match, counter store,
final installation and final call. Counter store additionally requires
`pending.core==emu.framecount()`. No hook, input, guest-write, capture,
argument, output filename,200-frame bound or100-record limit changes.
Target1's eight hardware matches are expected within visible lines9..37,
before the emulated frame boundary160; a later-core completion cannot
serve as that witness.

The wrapper requires exactly six original target-presence anchors and
one unique pending-store anchor. Its entire composed body is C625 plus
only these checks. Actual Lua54 parses and executes the wrapper against
the raw base with exact composed-body equality. The effective SHA256 is
`EA950EF5CA0CB4709879DD38F4665F727E42C1A39CDEF91AB6CA15A82C3AE60B`.

The small author gate retains all six prior affected cases and adds an
ordinary-frame advance between first compare69937 and remaining work
69938. V2 returns `failure:target-cycle-core`; same-core positive remains
accepted. Removing the six guards and pending-core condition recreates
the false acceptance and is rejected by the semantic control. No emulator
or genuine State was loaded by the gate, and no old full suite was rerun.

Frozen artifacts:

- NEW wrapper SHA256:
  `053FD747027B9B5ED68769643EBA138BB5313249DFBAC4384427375F6F4F64A6`.
- Immutable base SHA256:
  `C625D710C9B2DE44D128D1846066B4F5C2326E7EC37B6875FFF98805B0A59C6C`.
- NEW `tools/check_gba_shoot_counter1_v2_probe.py` SHA256:
  `D697ECBE54C59F71F1FEFC895B2B421CF52377DCFAA73824A39B6ECF61EA7AD5`.
- NEW `build/shoot-counter1-v2-probe-20261110/author-report.json` SHA256:
  `6113AE6D762DB2DD109291DF6F885F1483AEFFB0BD3D1C423D82F88A4B039626`.

```powershell
python -u -X utf8 tools/check_gba_shoot_counter1_v2_probe.py --output <new-report-path>
```

The three UserData arguments remain output/checkpoint_dir/probe_sha256,
using the same original19-irq-final-install.State69935/same280D ROM.
Completion marker remains counter1-done.txt and successful text remains
earliest-counter1-irq-complete. Root owns a NEW v2 host/pin set; the earlier
unexecuted host is preserved. Independent gate and actual counter1 timing
remain separate requirements. No host, emulator, ROM, existing evidence,
main build or Git file was changed by this author task.
