# Source Shoot causal observer contracts

Read-only support for a separate observer,2026-11-09. Immutable WSC1.5 SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No observer, input policy, emulator, guest memory or save changed here.

## Correct FIRST loss instruction

760185/188 is kind3-victim boss damage; it is not the ordinary FIRST loss
writer. The fighter's actual kind2 HP loss is4090:3030/raw743930:
74396D loads byte[SI+58] into already-zero AX,743970..975 caps AX to current
positive HP,74397F requires game-kind2, and743987 SUB WORD[SI+50],AX.
The next instruction begins74398A. Bytes are`29 44 50 81 64 0C FF BF`.

At that pair DS0=0C00,ES=1000 and SI is the victim fighter payload. Capture
only actual SI=liveFIRST, preHP>0 and0<AX<=preHP; pair the same PS,DS0,SI,SP
and PC advancing3, with each calibrated physical fetch at43987/4398A reporting
its own address+1. PostHP must equal preHP-AX. This shows the real loss
instruction rather than treating a later sparse HP0 poll as a causal event.

The common damage path760C46 stores attacker SI into victim DI+16, and
760C57..60 stores pending damage into victim+58/+59. The later3030 routine
is called by specific hurt/freeze continuations. Capture victim+16 and its
actor identity/callback/links as the last-damage-owner field. Without a matched
original collision/field-write event it remains an ownership candidate;
do not assume every delayed loss proves the currently visible opponent hit.

## Accepted jump and active boundary

Normal jump helper668E:01D6/raw766AB6 requires fresh edge0040.
766ABF is the accepted branch before installing actor callback668E:16E8;
766AC8 is after both callback stores. Bytes766AB6..AC7 are
`33C0F7442040007444C704E816C744028E66`. SI must equal liveFIRST with
actual source held/edge and DS0=0C00. Callback16E8 initializes the jump at
767FC8, then1721 waits the animation. Actual takeoff starts76804D when
presentation end-bit2000 is reached; velocity+34 is written76806C and
acceleration+38 at768073. Label acceptance and actual takeoff separately.

77345F sets03D8 bit4;773466..48A installs active07FA/D0B. A checkpoint at
that real boundary is different from the earlier initializer snapshot.
The observer author/root independently own the official savestate API and
completion semantics; no reconstructed RAM checkpoint is proposed here.

## Real calibration and finish route

750EBD is4FFF:0ECD, the normal frame-wait helper, not the IRQ body. It enables
B2 bit40, waits onC00:3754, clears that byte and returns. IRQ750EF0..F0D sets
3754=1 and acknowledges40. The ordinary task scheduler750B1F calls the wait
at750B7F independently of stage. A resumed normal run can therefore obtain
the real recurring750EBD calibration; absent delivery must fail closed.

Stage11 success still requires SECOND upper HP<=0→7417F3 root5. Source
7601EE/1FA changes the defeated upper/linked body callbacks to4090:7AB1/7D8D;
the pre-hit upper resource triple0:2F41:BC remains the correct identity.
Do not reuse the HP module's five live movement callbacks as a post-death
observer whitelist. Root5 stage11 chooses0653 at771FA3;772569 calls1750.
FIRST HP0 plus event+A4=3E instead takes7417DB root4→0C00. Timer expiry
takesroot0. Neither loss nor elapsed survival alone reaches1750.
