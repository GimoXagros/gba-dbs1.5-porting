# Authorized one-time original boss HP1 module

The user explicitly approved this action after reviewing the proposal:
“보스전에서는 보스의 체력을 1로 수정하는 치트를 넣어 공격1대를 적중시켜서 테스트를 이어”.
This extends the earlier P1 D-Spirit999 authorization to the exact one-time
original-reference boss HP1 action below. The module remains standalone,
disabled by default, and absent from the frozen saved-score driver. No emulator,
guest write, save, ROM or final GBA change was performed for this proposal.

Authorized effect: once during a separately reviewed original-reference
run, reduce the active stage7 SECOND boss's positive HP greater than1 to1.
Do not hold1, set0, replenish P1, or change stage/progress/registers. A later
accepted positive-damage attack is still required for the original victory
route; this does not guarantee that the bot lands that hit before losing.

| Artifact | SHA256 |
| --- | --- |
| tools/bizhawk_wsc_boss_hp1_once.lua | CBD4EC42A0106C9F10ADEFF27338E9F5FEE80F724D819822E4180639EB90F952 |
| tools/verify_wsc_boss_hp1_once.py | 86BBA1C122CEE86F15E509464F262335515B983050840BFCE5BC4138F3CE0E64 |
| build/wsc-boss-hp1-proposal-20261109/proof-approved.json | A00D8E926DE6F5C0A2B63866536BB4DFC97B300CD1272A809FB830371D7E32B8 |

Source is immutable WSC1.5 SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
The source hash userdata is a caller contract; a future reviewed launcher
must verify the actual loaded ROM, as it does for the existing source run.

## Positive active lifetime and owner

Stage7 initialization740CA1 sets timer03CE=4650 (18000) and selects kind2.
The dedicated intro intentionally sets FIRST HP0 at76C42B and restores8 at
76C783/81A. Timer18000 and mode7 alone therefore cannot identify active combat.
The intro exit76B880..8A9 passes main task handles03DE/03E0 to4FFF:0BC7,
installing4090:07FA and4090:0D0B. That helper750BB7..BD4 writes the two
callback words at the passed task address. Active07FA/raw7410FA decrements
03CE at741115; active0D0B/raw74160B executes collision before7417A1.

The proposal requires both exact active callbacks, valid active task slots,
and unsigned timer0..17999. This excludes the identified intro, includes
timer0 before its next decrement, and excludes negative timer words. The
fixed calibrated7417A1 opcode hook is inside that active post-task, after
current collision processing and before HUD/HP-result checks. It verifies
PS:PC physical address417A2 on each eligible callback delivery.

Additional guards require root mode7, SRAM0050=0, game-kind03D0=2, stage7,
controlled player03CC=0, and unpaused03CD low3bits clear. FIRST065C and
SECOND065E must be distinct active payload slots0024..3654, stride0110;
active task status is payload-6 bit2. Main task handles are the corresponding
header slots0014..3644; callback storage precedes payload by0010.
Allocator4FFF:0980/raw75097D scans those header slots in0110 steps,
tests[slot+0A]&2 at750980..987 and sets[slot+0A]=2 at7509A3..9A6.

The normal constructor743630 writes player index+10, HP WORD+50 and score
WORD+52. Stage7 constructor740D6E creates SECOND kind3/idF;74333F supplies
kind3 to the second allocator, and745640 retains that kind and sets idF.
The module requires FIRST kind0/index0 linked to SECOND and SECOND
kind3/index1/idF linked back to FIRST.
Constructor call743388..392 passes index1, FIRST as opponent and SECOND as
actor;743630..633 stores the index,74364E..651 stores the opponent link.
Both HP words must be positive signed values; SECOND HP must exceed1.
It derives the address from the live SECOND
handle, never from the stale first-stage07 snapshot or a fixed actor address.

## Sole write and natural continuation

The only guest-write API expression is
`mainmemory.write_u16_le(C000+SECOND+50,1)`: little-endian bytes01 00,
exactly2bytes. The module consumes its one-shot state before this call and
permanently refuses later writes, including after a Continue or a later HP
increase. Existing0/1 or signed-negative boss HP is untouched. P1 HP/score
and boss adjacent+4E/+52/+54 words are read back unchanged. Its ledger records
the actual handle/address, old HP, frame, timer and those preservation witnesses.

At7417E6..7F3 the original consumer compares the SECOND HP WORD to0 and
invokes root5 only when it is signed<=0. The proposed1 is positive, so it
cannot itself select that victory. A later source damage handler760185 can
subtract positive AX from the same victim+50 word. FIRST-death handling at
7417C7..7E3 remains unchanged and can still take priority; no victory guarantee
or direct progression write is claimed.

## Interface, default disablement and local check

`dofile` returns tick/status/finish. Without exact caller userdata
`boss_hp1_approval=user-approved-original-reference-once`, tick installs no
hook, creates no ledger and performs no guest-memory access. A future approved
installation additionally requires WSWAN, the pinned source_sha256,
callback_order=bizhawk2111-rew and an isolated W:/build output. Status exposes
approved/installed/enabled/applied/finished/hits/writes. Finish is idempotent.
Nothing in this proposal supplies that approval token to an existing driver.

The actual module executes in local Lua54 against explicit host mocks:
43 scenarios cover default disablement, the single reduction, full65536-byte
RAM comparison for each guarded scenario, timer/HP boundaries, owner/task
identity, paused/intro/result modes, idempotent install, bad opcode rejection,
finish, and permanent one-shot behavior after the boss is again43 or reaches0.
Four semantic mutations (wrong owner, direct0, repeated fixed1, intro allowed)
are rejected. Source instruction guards bind the timer, task callback install,
post-collision hook, boss identity, damage word and original victory compare.
This is a host self-check, not an emulator run or independent review.

## Read-only proof of the subsequent actual hit

Reducing HP to1 is distinct from observing an attack. A separate approved
driver can observe source760185 immediately before the damage SUB and760188
immediately after it, without modifying the frozen HP module. Active post-task
74160B establishes DS=0C00. Collision7426D7..72A supplies attack/victim list
entries to5FFD:0000 only after ownership/flags and rectangle overlap tests.
At760033/35 that handler loads SI=[attack entry] and DI=[victim entry], so they
are actor payload handles by the time it reaches760185. Requiring actual
DS0=0C00, SI=liveFIRST and DI=liveSECOND binds a direct P1-owned boss hit.
It deliberately does not attribute a projectile child to P1 without a separate
source ownership contract.

Source760177..188 bytes are
`33C08A46FCF7440800407402D1E8294550837D5000`: zero AX, load damage AL,
optionally halve it for attacker+8 bit4000, SUB WORD[DI+50],AX, then CMP
WORD[DI+50],0. The SUB is exactly3bytes `29 45 50`; the post-site CMP begins
`83 7D 50 00`. A calibrated pre-fetch at physical60185 sees the pre-SUB
state; physical60188 sees the next instruction before CMP executes. Pair
the same PS, DS0, SI, DI and SP, with logical PC advancing3; each callback's
physical PS:PC must equal its own opcode address+1. Require pre HP1 and
AX1..255, then post HP=(1-AX) modulo65536 and signed post HP<=0. This proves
the source damage instruction consumed positive damage against that same
boss word; HP1 alone does not satisfy the observation.

Natural continuation is separately observable at physical417F3/raw7417F3.
Source7417E6 reloads SECOND into BX,7417EB compares its HP WORD to0, and
7417EF skips the route only when positive. The taken route has literal
7417F1 PUSH5 followed by7417F3 LCALL71F0:0000; bytes7417F1..7FA are
`6A059A0000F07183C402`. Require calibrated opcode, actual DS0=0C00,
DS1=1000, BX=the same liveSECOND and stage7/kind2, associated with the
successful damage pair. The fixed source PUSH5 and call establish root5;
no guessed stack-domain read is needed. P1 death priority and any missing
pair remain reportable limits rather than being assumed away.
