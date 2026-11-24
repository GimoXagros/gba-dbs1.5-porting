"""Source B1E5..B71B turn controller; linked by the mode23 native builder.

Bodies receive R4=context and R5=current payload. Native service adapters
preserve R4..R11; callback pointers refer to the enclosing builder's wrappers.
This module neither allocates ROM/RAM nor exposes an unfinished menu.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ENTRIES = (0xB1E5, 0xB212, 0xB276, 0xB355, 0xB3BF, 0xB46D,
           0xB533, 0xB657, 0xB6C4, 0xB6EA)
DEPENDENCIES = (
    "m23_actor", "m23_event", "m23_callback", "m23_held", "m23_pressed",
    "m23_cos", "m23_sin", "m23_sound", "m23_window_top",
    "m23_bg2_enable", "m23_src_BA57", "m23_src_BC9C", "m23_src_BF42",
)


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 rules require the immutable WSC1.5 source")
    # These producers fix timer widths, strength progression and launch shifts.
    anchors = {
        0x74BAEF: "26c7061e004b00",
        0x74BC74: "f70654380600",
        0x74BC91: "f70658384000",
        0x74BD92: "2680061d0002",
        0x74BE97: "816710f800",
        0x74BFA8: "531eb8000c8ed8",
    }
    for at, expected in anchors.items():
        if source[at:at + len(bytes.fromhex(expected))] != bytes.fromhex(expected):
            raise ValueError(f"source rule anchor {at:X}")

    def entry(address, body):
        return f"m23_src_{address:04X}:\npush {{r6-r9,lr}}\n{body}\n" + \
            f"m23_rule_done_{address:04X}:\npop {{r6-r9,lr}}\nbx lr\n"

    def current_actor():
        return "ldrb r0,[r4,#0x2e]\nbl m23_actor\nmov r6,r0\n"

    def next_callback(address):
        return f"mov r0,r5\nldr r1,m23_rule_ptr_{address:04X}\nbl m23_callback\n"

    def timer(value):
        return f"mov r0,#{value}\nstrh r0,[r4,#0x30]\n"

    def decrement(address):
        # Source DEC is a 16-bit operation: zero follows truncation.
        return "ldrh r0,[r4,#0x30]\nsub r0,r0,#1\nstrh r0,[r4,#0x30]\n" + \
            f"mov r0,r0,lsl #16\ncmp r0,#0\nbne m23_rule_done_{address:04X}\n"

    def active_event_one():
        return """ldrh r0,[r6]
tst r0,#0x8000
bne m23_rule_event_one_skip_TAG
mov r0,r6
mov r1,#1
bl m23_event
m23_rule_event_one_skip_TAG:
"""

    out = [entry(0xB1E5, timer(0x4B) + next_callback(0xB212))]
    out.append(entry(0xB212, decrement(0xB212) + """
ldrb r7,[r4,#0x2e]
m23_rule_next_turn:
add r7,r7,#1
and r7,r7,#255
ldrsb r1,[r4,#0x2b]
mov r0,r7,lsl #24
mov r0,r0,asr #24
cmp r1,r0
bgt m23_rule_test_eliminated
mov r7,#0
ldrh r0,[r4,#0x28]
add r0,r0,#1
strh r0,[r4,#0x28]
bl m23_src_BA57
m23_rule_test_eliminated:
mov r0,#1
mov r0,r0,lsl r7
ldrh r1,[r4,#0x26]
tst r0,r1
bne m23_rule_next_turn
strb r7,[r4,#0x2e]
""" + timer(0x21) + next_callback(0xB276)))
    out.append(entry(0xB276, current_actor() + """
ldrh r0,[r6]
orr r0,r0,#2
strh r0,[r6]
""" + decrement(0xB276) + """
ldrh r0,[r6]
bic r0,r0,#2
strh r0,[r6]
ldrb r0,[r6,#2]
cmp r0,#0
beq m23_rule_human_turn
""" + timer(0x1E) + """
mov r0,#0x84
mov r1,#1
bl m23_sound
""" + active_event_one().replace("TAG", "B276") + next_callback(0xB6EA) + """
b m23_rule_done_B276
m23_rule_human_turn:
mov r0,#0
strh r0,[r6,#0x10]
mov r0,#0x18
strh r0,[r6,#0x12]
mov r0,r6
ldr r1,m23_rule_ptr_B740
bl m23_callback
""" + next_callback(0xB355)))
    out.append(entry(0xB355, current_actor() + """
bl m23_held
ldrh r1,[r6,#0x10]
tst r0,#6
subne r1,r1,#1
tst r0,#9
addne r1,r1,#1
and r1,r1,#255
strh r1,[r6,#0x10]
bl m23_pressed
tst r0,#0x40
beq m23_rule_done_B355
""" + timer(0x11) + next_callback(0xB3BF)))
    out.append(entry(0xB3BF, current_actor() + decrement(0xB3BF) + """
mov r0,r6
ldr r1,m23_rule_ptr_B71C
bl m23_callback
mov r0,#1
strb r0,[r4,#0x2f]
mov r0,#0x80
bl m23_window_top
mov r0,#0xd6
mov r1,#1
bl m23_sound
""" + active_event_one().replace("TAG", "B3BF") + next_callback(0xB46D)))
    out.append(entry(0xB46D, """
mov r0,#1
bl m23_bg2_enable
ldrb r7,[r4,#0x2f]
add r7,r7,#2
and r7,r7,#255
strb r7,[r4,#0x2f]
cmp r7,#0x50
bls m23_rule_power_window
mov r7,#1
strb r7,[r4,#0x2f]
mov r0,#0xd6
mov r1,#1
bl m23_sound
m23_rule_power_window:
cmp r7,#0x4e
movhi r0,#1
rsbls r0,r7,#0x70
bl m23_window_top
bl m23_pressed
tst r0,#0x40
beq m23_rule_done_B46D
""" + timer(0x11) + """
mov r0,#0x84
mov r1,#1
bl m23_sound
""" + next_callback(0xB533)))
    out.append(entry(0xB533, current_actor() + decrement(0xB533) + "bl m23_rule_launch\n"))
    out.append(entry(0xB657, """
bl m23_src_BF42
mov r7,#0
m23_rule_wait_motion:
mov r0,r7
bl m23_actor
ldrh r1,[r0]
tst r1,#1
bne m23_rule_wait_next
ldrh r1,[r0,#0x0c]
cmp r1,#0
bne m23_rule_done_B657
ldrh r1,[r0,#0x0e]
cmp r1,#0
bne m23_rule_done_B657
m23_rule_wait_next:
add r7,r7,#1
and r7,r7,#255
ldrb r0,[r4,#0x2b]
cmp r7,r0
bne m23_rule_wait_motion
""" + next_callback(0xB6C4)))
    # B69F's comparison branches to its own fallthrough; it has no state effect.
    out.append(entry(0xB6C4, next_callback(0xB1E5)))
    out.append(entry(0xB6EA, current_actor() + decrement(0xB6EA) + """
bl m23_src_BC9C
bl m23_rule_launch
"""))
    out.append("""
m23_rule_launch:
push {r7-r9,lr}
ldr r0,[r6,#0x20]
ldrh r1,[r0,#2]
ldrb r2,[r4,#0x2f]
mul r0,r1,r2
mov r0,r0,lsr #8
add r0,r0,r0,lsr #1
add r0,r0,#0x14
mov r7,r0,lsl #16
mov r7,r7,asr #16
ldrh r0,[r6,#0x10]
and r0,r0,#0xf8
strh r0,[r6,#0x10]
bl m23_cos
mul r1,r0,r7
mov r1,r1,asr #4
strh r1,[r6,#0x0c]
ldrh r0,[r6,#0x10]
bl m23_sin
mul r1,r0,r7
mov r1,r1,asr #4
strh r1,[r6,#0x0e]
mov r0,r6
ldr r1,m23_rule_ptr_B7D9
bl m23_callback
mov r0,#0
bl m23_bg2_enable
mov r0,#0xd7
mov r1,#2
bl m23_sound
mov r0,r6
mov r1,#0
bl m23_event
mov r0,r5
ldr r1,m23_rule_ptr_B657
bl m23_callback
pop {r7-r9,lr}
bx lr
""")
    for address in sorted(set(ENTRIES) | {0xB71C, 0xB740, 0xB7D9}):
        out.append(f"m23_rule_ptr_{address:04X}: .word m23_cb_{address:04X}\n")
    return "\n".join(out)
