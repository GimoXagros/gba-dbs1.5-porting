# v77 additional evolution music pause attempts

The frozen C344 Korean capture for song 6D passed the actual
gameplay audit. The separate first attempt for 6C finished with a
bounded target miss and stays preserved.

## Independent preflight

The reviewed probe B93 takes CE19's telemetry and preserves the
ordinary 9281 controller through the character selection transition.
The exact effective Lua hash is
1A614096DADF265224FD783BD2EFDEC2DA05B6CD0B103E27E4693D6B717DF283.
The independent reconstruction matched all bytes, including the seven
anchored controller substitutions. Lua 5.4 samples confirmed stable
cursor navigation and precisely targeted selection for actors 5 and
3 with actual ROM roster data, along with refusal of locked 6F.
The title, ROM and native checkpoint APIs used by the controller
remain read-only. The private launcher 9F6B pins the reviewed
observer, the exact 16 MiB C344 ROM and the two transitive Lua sources.

## 6D actual pass

At the native character-selection transition, the first 54 trace
lines match the previous Korean route. The input-selected P1 actor
3 enters the fight. The battle's real selector queues category 1
song 6D at core 8276. At core 8277, the actual player-zero start
installs header 08D47D64, with cached song 6D.

| Core | Observation |
| --- | --- |
| 8278 | One pause entry, equal header comparison and matching MPlay Stop call. |
| 8282 and 8311 | Header and cache are retained during the 30 neutral frames. Boundary status is 80000007. |
| 8313 | One resume entry, equal header comparison and matching MPlay Continue call. |
| 8316 | Status becomes 00000007 with the same header and cache. |
| 9600–9601 | The same actor naturally de-evolves. Native stage selection queues song 10, and player zero starts it in the next frame. |
| 9602 | The battle snapshot records cache 10 and stage header 08384BF8. |

Both canonical IWRAM hook counts are zero. All 42 top-level
artifacts match the final launcher inventory. The fixture has five
complete frame-boundary capture sets. The source requested sound
output method 3, and the emulator persisted method 1 on this run.
SoundEnabled, physical background input, autosave and state autoload
were false. Sound output was not measured.

Four in-memory contradictions were rejected, covering wrong actor
identity, an absent pending bit on native stage enqueue, a wrong
prior stage cache, and a stopped player at the resume boundary.

## First 6C attempt

The separate 6C attempt selected actor 5 and closed with
failure:pause-target-not-completed. The sole observed evolution was
opposing actor 1 with song 6E at core 8213–8214. The target 6C start
and pause counters are zero. The route remains an observation of
the target miss.

| Evidence | SHA-256 |
| --- | --- |
| tools/verify_evolution_music_three_capture.py | 7C63D2E061F643D879C97FB0F7E178E820CE4D52569D85ACA3494644BCEFEF13 |
| build/evolution-music-three-capture-qa-20261116/audit-6d-a.json | 286E9188BCEE94389A29D80E9F02BC7DCAA95F0B43F6E05B20258A26E1D5830F |
| 6D launch manifest | 4FDA0DDAE9842D4CDA11A65EA49B1DD53B815F5A14A141E0252942F7867DCF96 |
| 6D music telemetry | 65031E1F3C97AB1D15527EF5857CD78395EA3A8A3F013EDAC78BE3297AFB335D |
| First 6C launch manifest | 2B76B30DF0112E4632741AC6DDEDD37B19737DDF7729DFA4307E6B2864C3FB3A |
| First 6C music telemetry | 5A5E1880EA305EF267AC0BB41254FF1BB3CF23200D19261D21FA054A37126D2F |

The 6D evidence concerns this Korean route and its observed canonical
IWRAM execution addresses. The 6C retry and 6F gameplay remain open.
