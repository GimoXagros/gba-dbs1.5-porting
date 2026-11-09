# First native Shoot controller edge: independent QA

**Actual fresh A input is copied and accepted; vertical jump motion follows.**
The completed six-frame probe has P1HP4 and upperHP37 throughout. It preserves the
loaded-state qualification: exact original full-Core restoration still fails.
This reviewer launched no emulator, loaded no state and changed no runtime or ROM.

The source review corrected the draft's WSC input globals and A mask before launch.
Native0801190C/11910 maps physical A to0040; B maps to0080. The poller stores held
at03001302 and computes edge at03001306 as newheld & (oldheld ^ newheld). Input
375138 stores R0 to selected actor+2C;37513C stores R1 to+2E. At375140 both stores
have completed. For FIRST, R4 is02011710 and selectorR3 is0; callback R15=hook+4.
Actor callback is+0, event is+BA, positions are+34/+36 and motion fields+42..48.

Actual Lua54 QA passed against the complete healthy checkpoint fixture: A for one
frame, five released frames, no B or memory-write API, callback scalar capture
outside bulk/disk exports, load/save false/throw and invalid RAM/frame/controller/
held-A preconditions, failure cleanup and bounded advances. Five semantic mutations
reject wrong A bit1, two-frame A, B input, WSC globals and ignored proof-save failure.
The host's actual read-only84D/healthy-Core preflight passed before process creation.

The independent actual capture audit verifies57 inventoried files, seven complete
five-region+PNG snapshot sets and18 CPU-hook records. All copied source files and
three dependency pins match. At core68927:

| Hook | Global held/edge | FIRST held/edge | Registers |
|---|---|---|---|
| Before375138 | 0040/0040 | 0000/0000 | R0/R1=40, R4=FIRST, R3=0, R15=37513C |
| Before37513C | 0040/0040 | 0040/0000 | Same operands, R15=375140 |
| Before375140 | 0040/0040 | 0040/0040 | Same operands, R15=375144 |

The following frame's release is also proved in order: the first hook sees old
FIRST0040/0040 with global0/0, then held clears, then edge clears. Subsequent hooks
and outer snapshots retain0/0. No hook/frame timing is inferred from an outer dump.

| Core | FIRST callback / event | Y | Motion+44 /+48 |
|---|---|---|---|
| 68927 | 0835620C /0 | 1500 | 0 /0 |
| 68928 | 08356B78 /4 | 1500 | 0 /0 |
| 68929..68932 | 08356BC8 /4 | 1500 | 0 /0 |
| 68933 | 08356D40 /8 | 14D9 | FD9F(-609) /001F(31) |

The last Y is39 native position units above the initial value. Raw FIRST/SECOND/
auxiliary positions, callbacks, events, flags and signed motion fields for every
frame are retained in the report for subsequent source cadence work. The genuine
after-input.State at68933 matches all five final memory regions exactly; its full
Core is002FE364E6951FA4BF25BC26D0D9A02FC350FF4CE5387CADDAEBEFE6609B9BB5.

The newly restored Core is independently compared with the healthy source Core,
without assuming the prior12-byte result. This restore differs in9 bytes, all
preserved explicitly. CPU bank, native extensions, managed suffix and all five RAM
regions match. Original full-Core equality remains false; no normalization occurs.
Input acceptance and motion are observations under that loaded state.

| Artifact | SHA-256 |
|---|---|
| Preflight Lua QA report | B7D4B205A7DBA010808C96D1533B133AA91EDC44E90AEB72FE4340650861C938 |
| Actual capture checker | 369CDE9688A57D4AD1EE7D4DE87E1814BDEAF8782D1B2F72D2A2D717D0A730B1 |
| Final actual capture report | EEDA506A924054EAC17F0E4FBE8E85E82D1621B59A2163ADFEFC5F8566C493A2 |
| Genuine after-input.State | DDE92C367E9ABCBD760B442948F4DF960820735A4FE976577632DC14F064C5DF |

Reports: `build/gba-shoot-first-input-qa-20261109/report.json` and
`build/gba-shoot-first-input-capture-qa-20261109/final-report.json`.
No actual B hit, terminal continuation, full source parity, E5 cause or final port
QA follows from this six-frame controller probe.
