# Shoot Results checkpoint replay preflight

The replay uses the healthy v87 checkpoint from core 89405 and the isolated E2127521 ROM. The independent check verified the original state, metadata and all five memory dumps against the completed v87 launch inventory. The checkpoint's native ROM identity is 5284435A. Its source Core SHA-256 is BCA24A090D8AA084D25A4B6F7F31820DD8636054FD84898D201081D3C01793F8. The new launcher copies those seven files byte-for-byte and qualifies the source Core for comparison by setting only its ROM CRC field at bytes 12–15.

The previous same-ROM restored Core E62AE99E differs from the original captured Core at 15 offsets. The new preflight retains that entire difference list. The report supplies both the source Core with the candidate CRC and the prior restored Core with the candidate CRC, so a completed run can establish whether the cross-ROM restore added any differences.

The new host AB4E5668 reverses exactly to the frozen lead host 3F78FF14 after seven replacement groups. A single logical script substitution affects both the pin set and the command line. The host retains the private desktop, disabled background input, disabled automatic state loading and SaveRAM autosave, a fresh save path and the 360-second wall-clock bound. Its six-file pin set changes only the active wrapper. The approved write remains one stage 11 HP halfword after the original live-pair and input checks.

The independent harness executes both outer Lua wrappers against the frozen parent bytes, verifies the exact resulting programs and compiles them with the same Lua DLL used by the author fixture. They share the exact previous 15-frame lead policy. The new code admits modes 12 and 13, where the existing input controller stays neutral. Four new callbacks check the native constructors and the already executed requests. All 29 hook opcodes match E2127521. Native instruction fixtures verify that the mode 12 countdown reaches 080BD8E8 with zero and request (1,0,0), while a nonzero countdown leaves the request untouched. The mode 13 code stores (1,0,0) before 080CBCC0. The existing native transition rows map 8→12→13→11→20→3. The existing hit, terminal and title guards retain their original code.

- Independent preflight 525314AEE0D4B9BF99C3285F5F61B7952DA111E09715872A2CD09F9B5D94F4DE at build/shoot-checkpoint-results-v88-preflight-independent-20261117/report.json
- Root author Lua fixture report 1848B207FBE0A9BB9157093D0D4A148FA124D5F4573E6C2DFA8EADD136C7492B

The private replay supplies evidence for the actual new-ROM restore, controller hit and autonomous mode progression.

