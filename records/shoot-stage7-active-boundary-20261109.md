# Original stage7 intro and conditional melee geometry

Read-only investigation, 2026-11-09. Immutable source SHA256:
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No emulator, input policy, hooks, module, ROM or save changes. This note does
not establish a new boss strategy.

## Intro is not ordinary defeat

Run-a trace first announces stage7 at relative84559. At84600 it still reports
mode6 and the previous actors/scores. The first saved-stage07 snapshot at84839
therefore does not prove initialized boss state. Actual84900/85200 mode7
samples report timer18000, P1HP8/P2HP44;85500..86700 report P1HP0 while that
timer remains18000;87000..87900 restore P1HP8 with timer still18000.

Source740C9A..CB0 explicitly selects stage7 game-kind2 and timer4650=18000.
Initializer6B4A:0000 at76B4C9..4FF selects its dedicated0DAA intro when the
mode is2 and progress0200 is clear. Within that script,76C427 starts a019A
countdown,76C42B explicitly sets FIRST HP WORD+50 to0, and76C467..46F
installs callback6B4A:0FD7. Later callback6B4A:128B/raw76C72B tests its
countdown:76C783 restores HP8 at00CD, and76C81A restores8 again at0069.
These are positive scripted HP stores, not inferred damage or resurrection.

The intro ultimately enters6B4A:01D1 at76CA63..6B. Its short presentation
sequence finishes at76B85B..8BF by replacing the owned main tasks with
4090:07FA (raw7410FA) and4090:0D0B (raw74160B), then deleting itself.
The active pre-task decrements timer03CE at741115 when unpaused; active
post-task executes collision at74161F and HP/result checks at7417B5.
Thus mode7 alone is not the active-combat boundary. The observed timer is
still18000 at87900 and17774 at88200, positively bounding active entry between
those samples without claiming an exact frame from sparse logging.

Actual active samples later show P1HP loss, P2HP44 at91500 and43 at91800.
Consequently ordinary inputs can damage this boss; the early scripted HP0
samples do not establish a bot failure. Root separately observed the first
ordinary defeat/Continue cycle; it is not inferred from the stale stage image.

## Boss body and the existing vertical input gate

Existing actual snapshot
`build/bizhawk-wsc-score999-20261109-a/escape-2-stage-7-frame-100088-ram.bin`
has SHA256
`7FC5577D87CA5BF729FACD327E0D40B0088444E45DA08F17B127C47BBCF343B5`.
It is post-defeat: P1HP0, current attack/victim counts0, SECONDflags4=2303
without registration bit4000. It therefore does not capture an enabled
active-combat victim list.

It does positively bind SECOND=1894, callback4090:64C0, source P1BC:2F23
(raw3CF230), current B-relative01BA (raw3CF3EA). That body is
`(type0,x0,y-64,halfW176,halfH232)`. Callback64C0/raw746DC0 explicitly parks
SECOND Y atFE20. Its linked visible object19A4 is distinct; that object's Y
cannot replace the damage proxy's Y in an overlap calculation.

Source7424D6..57C reads actor position and presentation B pointer to register
victim geometry when enabled;7426B0..72A compares attacker/victim entries.
The actual rectangle helper4FFF:21B9/raw7521A9..2205 uses center distance
strictly less than the sum of half-extents on each axis. The last two body
words are half-extents, not top-left rectangle dimensions.

Base Agumon neutral event87 has active Y/halfH pairs(-128,104),(-160,136);
continuation event88 has(-128,112),(-160,144). Against the bound boss event3
body, possible root delta d=P1Y-bossY is -272<d<464 for87 and-280<d<472
for88. The existing abs(d)<512 B gate contains both intervals. Across all
six nonnull boss event0..5 body descriptors, the largest positive boundary
is520 (event88/body0); widening512 could admit only an8-unit extra margin
there, not explain the observed large vertical gaps. Hidden FE20 or the
large0Axx-to1080 separation is not evidence that the vertical gate rejects
an otherwise overlapping neutral attack.

These bounds concern the explicitly bound base neutral87/88 resources and
conditional enabled boss bodies. They do not cover every projectile, air
action, evolved form or future boss phase. No broad removal of the vertical
gate is justified by this investigation; an actual live attack/registration
capture is required before choosing a corrective policy.
