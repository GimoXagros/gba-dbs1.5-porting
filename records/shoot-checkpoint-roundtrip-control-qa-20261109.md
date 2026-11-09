# Same-ROM no-advance checkpoint control: preflight QA

**PASS for Lua5920 and host5AA.** This authorizes the root's single hidden diagnostic
control, not normalization of the original strict Core mismatch.

Actual Lua executes the exact reviewed A73 load/resave prefix against the complete
five-region checkpoint fixture. The control reads no observer/driver policy,
installs no hook, sends no controller input and advances no emulated frame. It
loads and exports the proof state once, writes loaded-ROM evidence and exits
immediately. False/thrown load/save calls, wrong frame, all five RAM mismatches
before/after export and missing/duplicate extraction anchors refuse success.
Three semantic mutations reject retaining the policy tail, omitting loaded-ROM
evidence and omitting the immediate exit.

The host's actual read-only D0/438C/C6E8 preflight was executed before any executable,
directory or process operation. The remaining host was reviewed for exact seven
dependency pins, private isolated output, no supplied save, disabled sound/input,
one unused frame-budget argument and60-second deadline. The original strict Core
gate remains a reported false result. A separate full comparison tests the D0
control against the already observed fixed-ROM post-load Core after changing only
CRC bytes12..15 in an expected buffer. The predicted matching D0 Core SHA256 is
09D83694EE7BABF9B32E2C2275CA21E9925BFCCC7A811723F656A78D94D5E7CA.

| Artifact | SHA-256 |
|---|---|
| Actual-Lua checker | 6FC15D91B368885B3A54F105EA42E7795FC50602A0799356C6B0C168049BA242 |
| Machine report | B102379E65BD67B52935B3D5F9E36CE1B38DF083416E8C972BFE5EDF59017CE3 |

Checker: `tools/verify_gba_checkpoint_roundtrip_control.py`.
Report: `build/gba-checkpoint-roundtrip-control-qa-20261109/report.json`.
No emulator or real state load was performed by this QA. A matching control would
establish patch independence of the12 functional audio/serial changes, not original
exact state equivalence. Source functional-state qualifications remain necessary.
