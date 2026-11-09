# Native entry observation: source boundaries

Read-only findings against frozen experimental `D0A01A7F` and retained source
`C415F227`. No ROM, build input, emulator, save or Git mutation was performed.

## Actual menu path and difficulty limitation

The frozen `bizhawk_probe_gba_collision.lua` schedule is not a difficulty
selection. Its actual `build/bizhawk-collision-20261103-a/trace.txt` observes
mode4 during twelve Down pulses3360..3690, then A3900 and mode7/fighter14 by
4200. Roster order is `0..10,13,14`; Down selects index12. The later Right
4560/4800/5040, A5280 and Left5460 are battle inputs. Omit the twelve Down
pulses to retain default fighter0. Generic character-selection Right changes
palette variant, but those particular late Right pulses occur after selection.

The existing `bizhawk_probe_result_languages.lua` supplies a verified normal
Options route: title task priority1000, callback090C7C accepts Start; callback
090FA0 uses byte03002C5E, with row2 Options and row0 Single Battle. Options is
mode14; its row is halfword0300473E, difficulty row1. Right changes difficulty
byte0300231F; B returns to title. Confirm the default character with A only.

Current native Options cannot select difficulty3: `080C3A90 CMP r1,#2`, its
equal branch and `080C3AC0 STRB r1,[r5,#0F]` cap it at2. Existing difficulty
event3 has labels/frames0..2. A four-byte cap edit alone does not establish a
valid fourth rendered choice. Root selected one actual hard2/default0 run,
with no Continue and actual case5 eligibility logged, stopping if excluded.

Normal single-player game-kind word03004502 is **0**, not2. `080D1828` reads
mode03002312; only stage7 adds2 atD1850, thenD1858 stores4502. Frozen actual
collision IWRAM confirms mode7/game-kind0. Require0 for ordinary score/input,
2 for stage7/Shoot HP combat; a universal2 gate suppresses the whole campaign.

## Typed actors, controller and first active edge

FIRST/SECOND globals0300489C/030048A0 contain actor payloads. Native task
headers use02010000+n*118, n0..51, with live bit2 at header+10; payload=header+18.
Global0300133C contains the current **header**; getter0801201C adds18.
Actor kind is low nibble of word+4, player index byte+10, character byte+11,
self pointer+14 and opponent+18. Ordinary FIRST/SECOND kinds0/1 come from
D18F4→352B24; stage7 kinds0/3 come fromD19E8. Boss initially passes constructor
ID0C, then36FD84/88 positively overwrites it with0F before active play.

Shoot reuses SECOND(kind3); auxiliary global03004D3C has kind6. Corrected
5BC294..2A8 gives aux+28=SECOND and aux+18=FIRST;5BC380 gives SECOND+28=aux.
Upper presentation+AC has P1 at actor+F0=085D0000 and P0+F4=085D1000;
auxiliary P1=085D029C/P0=085D1100. These are presentation pointers, not actor
callbacks. FIRST retains its normal character resources.

Input/battle globals03004510/03004514 hold **task headers**. Their active
callbacks are08374FF4/083735BC. Native input copies globals03001302/03001306
to controlled actor held+2C/edge+2E at375138/13C; control4529 bit4 clears them.
The battle producer gates4529&7==0. Only game-kind2 tests FIRST HP0/event3E
before SECOND signedHP<=0; case5 producer is3736B0. A scene current-task is
not interchangeable with either actor payload or those controller headers.

Scene5C8070 saves FIRST HP into current payload+54 and5C8078 temporarily
sets HP1. At5C8B2C it restores the saved value. Flag450A bit4 is written at
5C8D2C; input and battle callbacks restore at5C8D3C/4C, then scene retires at
5C8D50. Capture saved and restored health, and use the next outer boundary
after the entire tail for activation. Release through intro, then send a fresh
A edge after positive restored health, stage11, flag4 and real active callbacks
are observed. Initialization alone or temporary HP1 is not active health proof.

For real boss-hit causality, before0836E5E4 captures R5 victim, old word[R5+64],
R4 attacker, damageR0 and computed new signedR8. E5E4 is the actual HP store;
beforeE5E8 captures its result. E5DC/E5E0 perform signed load/subtraction.
R4's evolved flag4000 may halve damage atE5D0..D8. Bind victim to SECOND and
attacker to actual FIRST (or explicitly classify a legitimate owned attack);
approved one-shot HP1 followed by root5 alone is weaker than this paired proof.

## Stage11 score HUD: held minimal fix proposal

Source78769E..7876AA returns for stage7 **and11**. Native373ED0 loads stage,
373ED8 compares7 and373EDC returns only for7. Otherwise it reads the selected
actor score+66 and writes digits at0600D804/+2/+4. This is a real UI mismatch,
not evidence of an invalid pointer or BG1F000 corruption.

Smallest clear proposal: replace only373ED8 with a branch to a new16-byte
wrapper: `CMP r9,#11; BXEQ lr; CMP r9,#7; B 08373EDC`. Total20 declared bytes.
Non11 rejoins the original conditional return with the exact original CMP7
flags and unchanged registers;11 returns before actor/score/VRAM access.
No RAM, stack, literal pool, extra call or storage write is introduced.

Direct callers are373538,3735A4 and37364C; the first two immediately return,
the last loads game-kind and compares it before branch consumption. A whole
image aligned ARM BL scan found those three callers, and an unaligned byte
search found no exact08373ED0 pointer. This is not a replacement for strict
new-cave ownership checks. Probe reservation6FF380..6FF400 includes its erased
tail; it cannot be silently reused. Previously rejected5C9900 stays rejected.

An ephemeral in-memory execution of the proposed16 bytes tested all256 stage
bytes ×16 incoming NZCV patterns (4096 cases), unchanged registers/no writes,
and exact CMP7 NZCV for all non11 cases. No ROM file was emitted and the test
placement was not approved as a cave. Eventual implementation requires a fresh
owned span, exact20-byte inverse against the frozen predecessor, source/caller
pins and independent verification. Root held the fix to preserve the first
actual D0 observation. No full entry, ending or E5 closure follows here.

## New observer source-address review

One read-only pass of `bizhawk_probe_gba_shoot_entry.lua` and
`bizhawk_gba_shoot_entry_observer.lua` checked the source/ABI contracts above.
The saved/restore hooks correctly observe before the relevant store; activation
5C8D50 is before retirement but after both callback stores, with retirement
checked later at the outer boundary. Damage E5E4/E5E8 correctly binds R4/R5,
computed signed WORD R8 and damageR0. Event48 hooks128A4/128BC correctly use
R3 event, R5 presentation and R1 table/frame pointer respectively. The updated
ordinary0/boss2 gate is correct. No blocking source-address finding remained
in that pass. This does not replace the independent Lua harness or actual
runtime/capture audit, and is not a freeze of files still under author/QA edits.

The final menu follow-up retains the existing two-callback title contract after
Options B as well. Options exitC33CC..E0 writes2314=1 and2316/2318=0; it does
not directly choose a title callback. Constructor90BF4 installs090C7C, whose
90D40 tests Start bit20, not A; menu animation later installs090FA0. This narrow
review did not establish whether return-submode1 bypasses the prompt, so the
driver must reuse Start for090C7C and cursor Up/A only for090FA0 instead of
assuming every mode3 frame is already the menu.
