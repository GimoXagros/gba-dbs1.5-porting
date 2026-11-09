# Actual zero-HP Shoot entry and ordinary Continue recovery

Read-only source/snapshot finding,2026-11-09. SourceWSC1.5 SHA256
`C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.
No P1HP, guest memory, input policy, emulator, save or ROM change.

## Proven cause and withdrawal

Both `build/bizhawk-wsc-score999-boss1-20261109-a` and
`build/bizhawk-wsc-shoot-boundary-20261109-a` boss-hit pre/post/root5 RAM
show FIRST1784 HP0,event+A4=005B. The actual direct P1 attack reduces SECOND
HP1→0, but the player did not survive it with1 HP. The earlier survivor-HP1
interpretation is withdrawn. Source7417D2 requires death-event003E before
root4;005B therefore permits the actually observed root5 despite P1HP0.

Stage11 initializer/preactivation RAM shows FIRSTHP1 while the actual scene
taskheader2324/payload2334 stores savedHP0 at+46. Source772E3C..42 saved
the real0, then temporarily wrote1. The baseline's exact writes at93549 to
D7D4/D7D5 report PS:PC71F0:1462,DS0C00,SI2334,DI1784. They are77335F's
restore of that saved0, before activation93570. Activation pre/post RAM still
has scene+46=0 and FIRSTHP0. No3030 damage pair explains this transition.
Two later jumps accepted while HP0 cannot repair it. The owned earlier
input-boundary record has been corrected; fresh jump is not a remedy for
this checkpoint and the HP1 module's positive-P1 guard must remain intact.

## Positive ordinary Continue route

The genuine replay final snapshot at core95185 in
`build/bizhawk-wsc-shoot-replay-20261109-a` has mode9,stage7,difficulty3,
progress0080 and all global previous/held/edge/repeat words zero. Only the
mode-dispatch/support tasks are active; the Continue menu is not yet ready.

Mode9 initializer77F222..228 maps stage11 back to7. Its main creates the
menu whose eventual ready callback is7F20:05DA. The selection byte at its
payload+C6 is initialized1 at77F546, the Continue choice. The positive
confirmation at77F983 tests A0040 from the global385C input mask;77F98B
tests that choice bit. The chosen path sets0068 bit0200 at77FA00 and later
77FC11..19 requests transition0; the mode9 transition table's first byte
is6. Ordinary A press/release after the ready callback therefore returns to
mode6 initialization of the same stage7, without replaying ten rounds.

Stage7 initialization creates FIRSTHP8 at743636 and ID0/difficulty3
SECONDHP44 at7455F3..61D. Continue bit0200 selects76B4DA's explicit HP8
and normal get-ready path instead of the long scripted death/restore intro.
76B880..8A9 installs active07FA/D0B. Difficulty3 still takes the source
stage7 root5→stage11 branch after Continue.

Get-ready priority0EF0 precedes active input0F00, so the new input task may
run in the same scheduler invocation in which it is installed. An outer-frame
checkpoint should report actual mode7/stage7,owned07FA/D0B,HP8/44 and pending
damage BYTE FIRST+58=0 with all keys released. These are positive healthy
snapshot conditions, not a blanket guarantee that no non-damaging collision
has occurred. The new checkpoint driver and official savestate API are owned
and independently reviewed by the other agent/root. No source health write
or old one-shot module rearm is needed to obtain this ordinary checkpoint.
