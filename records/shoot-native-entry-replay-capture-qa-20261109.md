# Repaired native entry replay: independent capture QA

**Actual native Shoot activation is observed with positive HP; strict original-Core
restoration failed.** These are separate results. The fixed-ROM replay host exited1
because its CRC-only complete-Core equality gate did not pass. That failed gate and
the original capture/report remain unchanged. No difference has been masked.

The independent capture auditor verifies109 inventoried files and13 snapshot sets
for `build/bizhawk-gba-shoot-entry-replay-20261109-a`. Loaded84D ROM, six pinned
dependencies, copied438C checkpoint and proof memory are exact. The replay begins
at core64230 with original input epoch1/next relative64229 and actual first input
Right. There are zero new score or boss writes; the one historical boss HP action
is retained only through the validated checkpoint and explicit consumed flag.

| Native event | Actual core |
|---|---:|
| FIRST damage1, HP1→0, healthy root5 and eligible case5 | 66972 |
| Scene entry and savedHP4 | 66973 |
| Ordered initializer call / return | 67786 / 67788 |
| SavedHP4 restore | 68815 |
| Activation tail | 68926 |
| Healthy outer checkpoint | 68927 |

The actual damage registers retain FIRST as attacker and SECOND as victim. The
selected callback is085C8000. At the healthy checkpoint native stage11 is active,
flags=0006, P1HP4 and upperHP37. Its genuine ZIP/Core passes the source-bound parser
and all five complete memory regions equal the same-frame exports. Core SHA256 is
6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93.
No terminal continuation or E5 cause is established by this entry-only observation.

The initial restored Core has the same length, CPU register bank, full IWRAM/EWRAM/
VRAM/palette/OAM, native extensions and21-byte managed suffix as the source state.
After the permitted expected-buffer ROM CRC update it still differs in12 bytes:
native132,142,146,151..152,17C..17D,184..185,188..189 and534. They are functional
audio oscillator phase and serial control state, not padding. The strict failed
comparison is therefore retained as false, including in the machine report.

One separately approved **same-D0 load/resave-only control** then completed in
`build/bizhawk-gba-checkpoint-roundtrip-20261109-a`, without input, hook, policy or
frame advancement. Its14 inventoried files, unchanged source copies, frame64230
and all five memory regions verify independently. Its complete post-load Core
09D83694EE7BABF9B32E2C2275CA21E9925BFCCC7A811723F656A78D94D5E7CA equals the fixed-ROM
post-load Core after changing only ROM CRC bytes12..15 in a comparison buffer.
Its12 differences from the original Core are byte-for-byte the same as the failed
fixed-ROM comparison. This isolates the observed loader changes from the five-word
ROM correction. It does not establish literal equivalence to the original state.

The source-derived arithmetic is also checked against those actual bytes: square
channels catch up84 and93 periods of32768 cycles with matching duty indices; noise
executes28 inverted-XOR feedback steps2BB7→7A94 under the prior live32-cycle period,
advances896 cycles, then schedules with the restored64-cycle period. RCNT changes
SC bit0 from1 to0 while SIOCNT remains200F. The source diagnosis explains the
register-write ordering and live low-bit preservation, including why these fields
must not receive a blanket harmlessness or padding exemption. See the
[pinned source diagnosis](shoot-state-load-audio-serial-delta-20261109.md).

The supported result is healthy native activation **under this controlled post-load
state**, with exact CPU/RAM preservation and independently demonstrated patch-
independent loader differences. Original complete-Core equivalence, every future
audio/serial consequence, source timing parity and final port QA remain open.

| Artifact | SHA-256 |
|---|---|
| Original full Core | C6E8036B8E316D0DC83D091B559414C08635FABEA3EE2467880A110B6216CA6F |
| CRC-only expected fixed Core | C486433ACFE8E50BE6ACE3E10DE0B9215FA7155198CAE3E77DD18DE0C3E6683F |
| Actual fixed-ROM restored Core | 42448E25FAF97F523C2FDEFA26C64B6E71414ABC424F937A5B31EB3B9809D72E |
| Strict-mismatch capture report | 5FF3EC35673391DF6A53462A035E28654E937DEE35688C5E9E8EB1FCDFBB225D |
| Replay capture checker | 3E02DA4D62D9FF1BDA8176541C1CD9D1466F9B42FC169DE99E3F844A29EBABCB |
| Same-ROM control report | 6126B270F17BE65203113631195F9B36007A8FC7B71E9BA552B2F6F228D160DC |
| Same-ROM control checker | 5E519B404D89988135A9FCDA82E6A8E92A129B2817EA428D542FEB8A66421A7C |

Reports: `build/gba-shoot-entry-replay-capture-qa-20261109/report.json` and
`build/gba-checkpoint-roundtrip-capture-qa-20261109/final-report.json`.
Both auditors are read-only and require fresh report paths. No emulator, state load,
state edit, new guest write, ROM/main change or Git operation was performed by QA.
