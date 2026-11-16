# Independent preflight for the v77 evolution music pause probe

GO for the bounded gameplay capture on the exact 16 MiB v77 candidate
C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278.

The read-only comparison used the completed ordinary Korean trace. Its
single selected evolution song 6E starts in player zero at core 9076,
with cached song 6E and active header 08D75728. The eligible devolution
site is reached at core 10364 while that header is active. At core
10365, a same-frame player-zero start and return establish stage song
10 with header 08384BF8. The frozen trace SHA-256 is
2B7FE19431AE73E0E0DBC5F9F12D8C4B19BC575D506E103751F1A03CA72D750F.

The effective composition independently matches byte for byte. It takes
the CE19 telemetry block with only a local observer call and policy
description change, and applies exactly six anchored substitutions to
the 9281 controller. The ordinary input schedule is preserved until
the live 6E start-return arms the probe in battle mode. At most one
pair of four-frame Start presses is scheduled, with 30 neutral frames
between the presses. The hold requires cache and header continuity
and the player stopped bit for each neutral frame. The resume boundary
requires that bit to be clear with the same cached song and header.
The service hooks are the ROM's decoded MPlay Stop and Continue
targets 0837C9C8 and 0837C1A8, with their specific caller link registers
0837C36F and 0837C3A3 and matching header comparisons in the same frame.

The route completes only after the validated resume boundary and an
eligible devolution with a playing 6E header, followed within two core
frames by a same-frame stage-song start and return with actual cache
10 and header 08384BF8. Telemetry closes before the completion marker.
A foreign stage-song start by itself fails. The post-arm deadline is
3,000 frames and the total cap is 15,000 frames. Missing the target
produces a failure marker.

Eleven independent Lua 5.4 mocks used the actual ROM scalar values and
stubbed I/O. They compiled the exact composed Lua and entered its
controller at the battle phase, without running the menu. The positive
case checked exact 4/30/4 input and the close-before-marker ordering.
Negatives covered absent 6E, stage restart without devolution,
devolution before resume validation, wrong header compare, lost pause
hold, late stage start, no stage return by deadline, wrong Stop caller,
wrong Continue caller, and a set stopped bit at the resume boundary.

| Input or composed body | SHA-256 |
| --- | --- |
| tools/bizhawk_probe_evolution_music_pause.lua | 8ABD117B123BD7A501C8DC66E4301FF20AC2AE108C5E22E5B53064692C0EA535 |
| tools/bizhawk_probe_result_music_lifetime.lua | CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430 |
| tools/bizhawk_probe_result_languages.lua | 928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC |
| Effective Lua | C41612BB0190CDBBDEF54325C9875A46467B3177B63DC9C63A85BCD5CBD33E5C |

The review executed no emulator, guest writes, save or state access.
The actual capture must independently count the matching stop and
resume chains within the two press windows and verify the complete
observed return. The preflight does not establish actual playback
or verify audio output.

## Independent review of revision 2

Revision 2 is cleared for the bounded capture. Reversing two callback
additions and the counter banner reproduces the entire frozen first
revision exactly. The ordinary and targeted input behavior follows the
same controller. The additions watch execution at the specific
canonical IWRAM addresses 03000D00 and 03000D0C.

The Lua 5.4 delta checks covered three cases.

- The normal pause, resume and stage return still completes with both
  alias counters explicitly zero at close.
- Forty D00 calls emit 32 rows and retain all 40 in the observed count.
  The next controller boundary writes failure:copied-request-entry-executed.
- With D00 followed by D0C in the same frame, D0C logs the event and
  closes the telemetry including both counters before the exact
  failure:copied-cache-branch-executed marker closes. The callback then
  errors before the mock frame advances.

| Revision 2 input or composed body | SHA-256 |
| --- | --- |
| tools/bizhawk_probe_evolution_music_pause_r2.lua | 450AE932AA673C2C631A698EB597C48F566587BFCEC97E2A665C81DCE2E4DA51 |
| Effective Lua | 97198C5DBAD38D6F68F7475D6E48DF57C49B3740EDE834184E8A2A612FF26F2E |

The actual run must report both counters as zero. That observation
covers the two canonical addresses during the captured route.
