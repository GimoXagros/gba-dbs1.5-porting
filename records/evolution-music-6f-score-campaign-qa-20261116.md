# 6F score-assisted campaign capture

The isolated 8C72 run verifies actual 6F pause and resume. The
launcher returned exit code 1 when another song replaced 6F
before natural devolution. The full stage-return check remains open.

A private Korean game reached the native CPU Impmon campaign
decision at core 29256, with progress 3, physical stage 5, and
flags 0x60. The event records native R0=11 just before the commit
branch. The live terminal CPU is independently bound to global
SECOND 030048A0, actor 02011828, side 1 and identity 11.
Seven logged assist writes changed only the live P1 u16 score
at 02011776 to 999. The last write was at core 29473, before
the target sequence.

| Core | Actual observation |
| --- | --- |
| 33689 | CPU actor 11 naturally queues category 3 song 6F. |
| 33690 | Player zero starts 6F with header 08D782CC and cache 6F. |
| 33691 | Actual equal header comparison and one matching MPlay Stop. |
| 33695 and 33724 | Header and cache match while the stopped bit is set. |
| 33726 | Actual equal header comparison and one matching MPlay Continue. |
| 33729 | Header and cache match while the stopped bit is clear. |
| 34955 | Player zero starts type-1 song 04 with header 083820A8. |
| 34956 | The capture ends in mode 7. Both fighters have HP 8. Impmon remains on evolution callback 0835A5F8 with 58 countdown units. The battle timer is still 1933. |

The trace contains exactly four Start frames, 30 neutral frames,
and four Start frames, followed by neutral input. The two canonical
IWRAM execution counters are zero and the alignment journal shows
83 metadata observations, 80 dispatch observations, zero odd
pointers, and zero E5 observations in this run.

The whole-capture audit independently matches all 86 top-level
artifacts and 11 complete capture sets. A separate verifier checks
the actual target pause and resume, and verifies that there is no
eligible devolution or stage-selector return after resume and before
song 04 takes over. The broader music request counter reports 54
observations and 32 emitted rows because of the frozen row cap. The
producer of the late type-1 request is therefore still open.
The retained group-1 Impmon P1 has no ID-04 command in its 164
declared commands. This excludes that normal table population
as a direct descriptor source, while leaving other producers open.

| Evidence | SHA-256 |
| --- | --- |
| tools/verify_evolution_music_6f_campaign_capture.py | 1D198E442B0BFCC5462302044672E2A25D18FB0C07E2435808745AAD6F147F12 |
| Whole actual failure audit | 272577BEC925F3216ACF6EE1D2A72BBF94C6E22A62503E03D3448AEA808277FA |
| tools/verify_evolution_music_6f_pause_slice.py | DC23980C45E4C4B3F8E6C3D768D1DCE10799A28C05C4EFD67BDB5BCA49DCA5F3 |
| Actual pause slice audit | B7C5D257ABFB8769231A24D76ADB8A789EB513195488EAFB2C8BB08CEB050C05 |
| Launch manifest | 022432F2115F9030134B9E3427C46B740CAB55D398134D0A6FF3187E0F12A90E |
| Music telemetry | 3DF69F7096569EEFAD74EE3B946AC79BF832D4E1FB655D6A35D83E45B6763ED9 |

This was a silent score-assisted isolated route. The observed
replay verifies the player's native pause and resume states.
The later natural stage-music restore and audible outcome remain
separate gameplay evidence.
