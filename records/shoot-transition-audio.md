# Shoot transition audio: native service and content lineage

This is ROM-only static evidence. No save was accessed and no emulator was
run. `tools/analyze_shoot_transition_audio.py` pins the three original ROMs,
reads the actual caller arguments and payloads, and rejects six mutations.
Its initial report is `build/shoot-transition-audio-20261013/analysis.json`,
SHA-256 `48424A2F144A1C41035111E75363E624D5E2A84F9FF9A2E7D9AD4A71B57B6D1B`.

## Sound requests

| Ver. 1.5 | WSC 1.0 exact payload | Native ID / type | Commercial caller evidence |
|---|---|---|---|
| `9A` | `98`, SHA `294EEC3F03A83C756EB7BA4FC71F30F644B56E69CD4EB0C5A6298CCAAFE0495C` | `5A / 1` | source raw `392835..39288D` and native `08354758..083547D0` preserve the helper call, request, participant comparison, linked count increment and `250` cap |
| `A9` | `A7`, SHA `68CA1B6E09B82F7BAB3F0BA06D37FFF0FB539E0D85A75BAEBCBA12DEE89736FF` | `4C / 2` | source raw `395B5E` and native request `083719C0`; also in the established audio-lineage oracle |
| `06` | `06` (also identical to `04`, `05`, `07`), SHA `74F2F3EC29390063B2FE7C5B0D3D403E42C011E60D27A4124D297ABE128FE17F` | `00 / 2` | source raw `3BEAFB..3BEB28` and native `08340378..08340398` set the common `20` flag then request stop |

Every row uses native writer `080D15C0`, zero delay, and its existing busy-slot
check. Equal numeric IDs or a constant subtraction were not used as proof.
The `9A -> 5A` row specifically disproves a tempting arithmetic `9A -> 3D`.

## Reset and pre-fade services

Ver. 1.5 `4FFF:50F2` (raw `7550E2..755220`) has a concrete commercial native
counterpart at `0801565C`, through literals ending at `0801580C`. Both set
request status bit 0, make eight channel/side reset calls, clear halfwords
`0,2,4,6,8,C,E,10`, set `A=FFFF`, and clear status bit 0. Native request owner
is `030022F0`. The native routine ends by calling `0837B44C` with `r8=0`;
`0837B47C -> 0837DB84 -> Thumb 0837C3B0` iterates the existing music-player
records and stops them. This is the reset entry to use, not the unrelated
retail no-op at `080D14FC`, or the request-processing helper `080D15A8`.

The channel helper `4FFF:4EE0` (raw `754ED0..754F74`) is byte-identical to WSC
1.0 raw `39BA00..39BAA4`. The eight corresponding calls in native reset are
all to **`080158C8`, an existing `BX LR` implementation**. Shoot's pre-fade
sequence at raw `773051..7730D9` requests both sides of all four channels for
32 ticks. Calling the commercial helper preserves the established backend
translation, but does not reproduce the WSC intermediate volume envelope.
This limitation must remain explicit in the final audio QA record; a static
call-graph check cannot establish an audible fade.

The native reset preserves `r0..r5` and LR, but uses the commercial scratch
registers. A ported scene must preserve any live values in `r8..r12` around it.
The five native stack arguments to the channel helper are caller-owned and
must be removed after each invocation, even though the retail body is a no-op.

## Limits

`CF` and `D1` have no identical WSC 1.0 payload. They need separate native
reconstruction and consumer checks; this record does not assign replacement
IDs to them. First-milestone completion also requires the real ordered
initializer, complete lower controller, and scene connection. This analysis
does not make those paths reachable.
