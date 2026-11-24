"""Mode23 participant callbacks, with explicit unresolved native service imports.

This emits ARM bodies only. It neither installs a scene nor supplies substitute
services. R4 is the scene context; R5 is the current task payload. All exported
helpers preserve R4..R11. Source arithmetic wraps at the original field width.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
ENTRIES = (0xB71C, 0xB740, 0xB7D9, 0xB950, 0xB999, 0xB99A,
           0xBC1C, 0xBC36, 0xBC5A)
HELPERS = ("m23_draw", "m23_draw_at", "m23_src_C775", "m23_src_C88D")
DEPENDENCIES = ("m23_actor", "m23_callback", "m23_event", "m23_frame",
                "m23_framecounter", "m23_sound", "m23_actor_resources",
                "m23_present_update_draw")


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 participants require immutable WSC1.5")
    def entry(addr, body):
        return f"m23_src_{addr:04X}:\npush {{r6-r9,lr}}\n{body}\n" + \
            f"m23_part_done_{addr:04X}:\npop {{r6-r9,lr}}\nbx lr\n"
    def callback(addr):
        return f"mov r0,r5\nldr r1,m23_part_cb_{addr:04X}\nbl m23_callback\n"
    def signed(reg):
        return f"mov {reg},{reg},lsl #16\nmov {reg},{reg},asr #16\n"
    def decrement():
        return "ldrh r0,[r5,#0x1e]\nsub r0,r0,#1\nstrh r0,[r5,#0x1e]\nmov r0,r0,lsl #16\ncmp r0,#0\n"
    out = [entry(0xB71C, "mov r0,r5\nbl m23_draw")]
    out.append(entry(0xB740, """
ldrh r6,[r5,#0x10]
and r6,r6,#255
mov r6,r6,lsr #3
sub r6,r6,#8
and r6,r6,#31
ldrh r0,[r5,#0x12]
cmp r0,r6
beq m23_part_angle_same
mov r0,#0xd5
mov r1,#1
bl m23_sound
m23_part_angle_same:
strh r6,[r5,#0x12]
add r0,r4,#0x84
mov r1,#0
mov r2,r6
bl m23_frame
mov r0,r5
add r1,r4,#0x84
bl m23_draw_at
mov r0,r5
bl m23_draw
"""))
    body = """
ldrh r0,[r5,#4]
strh r0,[r5,#8]
ldrh r1,[r5,#0xc]
add r0,r0,r1
strh r0,[r5,#4]
ldrh r0,[r5,#6]
strh r0,[r5,#0xa]
ldrh r1,[r5,#0xe]
add r0,r0,r1
strh r0,[r5,#6]
mov r0,r5
bl m23_src_C775
mov r6,r0,lsl #16
mov r6,r6,asr #16
"""
    for field in (0xC, 0xE):
        body += f"ld r0,[r5,#{field}]\n".replace("ld ", "ldrsh ")
        body += "mul r1,r0,r6\nmov r1,r1,asr #8\n" + signed("r1")
        # The source retains exactly +16 and -16; only the open interval dies.
        body += f"cmp r1,#16\nbge m23_part_velocity_{field}\ncmp r1,#-16\nmovgt r1,#0\nm23_part_velocity_{field}:\nstrh r1,[r5,#{field}]\n"
    body += """
ldrh r0,[r5,#0xc]
ldrh r1,[r5,#0xe]
orrs r0,r0,r1
bne m23_part_bounds
""" + callback(0xB71C) + """
m23_part_bounds:
ldrsh r0,[r5,#4]
ldrsh r1,[r5,#6]
cmp r0,#-0x5800
blt m23_part_eliminate
cmp r1,#-0x4000
blt m23_part_eliminate
cmp r0,#0x5800
bgt m23_part_eliminate
cmp r1,#0x4000
bgt m23_part_eliminate
mov r0,r5
bl m23_draw
b m23_part_done_B7D9
m23_part_eliminate:
ldrb r1,[r5,#2]
mov r0,#1
mov r0,r0,lsl r1
ldrh r1,[r4,#0x26]
orr r0,r0,r1
strh r0,[r4,#0x26]
ldrb r0,[r4,#0x2c]
sub r0,r0,#1
strb r0,[r4,#0x2c]
ldrh r0,[r5]
orr r0,r0,#1
strh r0,[r5]
mov r0,#75
strh r0,[r5,#0x1e]
""" + callback(0xB950) + """
ldrh r0,[r5]
bic r0,r0,#0x8000
strh r0,[r5]
mov r0,r5
bl m23_actor_resources
mov r0,r5
mov r1,#2
bl m23_event
mov r0,#0xda
mov r1,#1
bl m23_sound
bl m23_src_C88D
"""
    out.append(entry(0xB7D9, body))
    out.append(entry(0xB950, decrement() + "bne m23_part_fall_blink\n" + callback(0xB999) + """
m23_part_fall_blink:
bl m23_framecounter
tst r0,#4
beq m23_part_done_B950
mov r0,r5
bl m23_draw
"""))
    out.append(entry(0xB999, ""))
    out.append(entry(0xB99A, """
ldrh r0,[r5]
bic r0,r0,#0x8000
strh r0,[r5]
mov r0,r5
bl m23_actor_resources
mov r0,r5
mov r1,#3
bl m23_event
mov r0,r5
bl m23_draw
""" + callback(0xB71C)))
    out.append(entry(0xBC1C, ""))
    out.append(entry(0xBC36, "mov r0,r5\nbl m23_draw"))
    out.append(entry(0xBC5A, decrement() + "bne m23_part_aux_draw\n" + callback(0xBC1C) + """
m23_part_aux_draw:
mov r0,r5
bl m23_draw
"""))
    # B9F1 takes actor and presentation independently (the aiming overlay is
    # context+84, while blink/coordinates still belong to the current actor).
    out.append("""
m23_draw:
add r1,r0,#0x24
b m23_draw_at
m23_draw_at:
push {r4-r11,lr}
mov r6,r0
mov r7,r1
ldrh r0,[r6]
tst r0,#2
beq m23_part_project
bl m23_framecounter
tst r0,#4
bne m23_part_draw_return
m23_part_project:
ldrh r0,[r6,#4]
add r0,r0,#0x7000
mov r0,r0,lsl #16
mov r0,r0,lsr #24
strh r0,[r7]
ldrh r0,[r6,#6]
rsb r0,r0,#0x4800
mov r0,r0,lsl #16
mov r0,r0,lsr #24
strh r0,[r7,#2]
mov r0,r7
bl m23_present_update_draw
m23_part_draw_return:
pop {r4-r11,lr}
bx lr

m23_src_C775:
push {r4-r11,lr}
mov r6,r0
ldr r7,[r6,#0x20]
mov r8,#0xf0
ldrsh r0,[r6,#4]
ldrsh r1,[r6,#0xc]
cmp r0,#-0x4800
bge m23_part_friction_ylo
cmp r1,#0
blt m23_part_friction_edge
m23_part_friction_ylo:
ldrsh r0,[r6,#6]
ldrsh r1,[r6,#0xe]
cmp r0,#-0x3000
bge m23_part_friction_xhi
cmp r1,#0
blt m23_part_friction_edge
m23_part_friction_xhi:
ldrsh r0,[r6,#4]
ldrsh r1,[r6,#0xc]
cmp r0,#0x4800
ble m23_part_friction_yhi
cmp r1,#0
bgt m23_part_friction_edge
m23_part_friction_yhi:
ldrsh r0,[r6,#6]
ldrsh r1,[r6,#0xe]
cmp r0,#0x3000
ble m23_part_friction_scale
cmp r1,#0
ble m23_part_friction_scale
m23_part_friction_edge:
ldrh r0,[r7,#4]
mov r0,r0,lsr #5
cmp r0,r8
movhs r0,#0xef
sub r8,r8,r0
m23_part_friction_scale:
ldrh r0,[r7]
mul r1,r0,r8
mov r0,r1,lsl #8
mov r0,r0,lsr #16
pop {r4-r11,lr}
bx lr

m23_src_C88D:
push {r4-r11,lr}
mov r0,#0
bl m23_actor
mov r6,r0
ldrh r0,[r6]
tst r0,#1
bne m23_part_round_loss
ldrb r0,[r4,#0x2c]
cmp r0,#1
bhi m23_part_round_return
mov r0,r6
ldr r1,m23_part_cb_B99A
bl m23_callback
mov r0,#0x18
mov r1,#4
bl m23_sound
b m23_part_round_end
m23_part_round_loss:
ldrb r0,[r4,#0x2e]
bl m23_actor
mov r6,r0
mov r0,#0x1c
mov r1,#4
bl m23_sound
ldrb r0,[r6,#2]
cmp r0,#0
beq m23_part_round_end
mov r0,r6
ldr r1,m23_part_cb_B99A
bl m23_callback
m23_part_round_end:
mov r0,r4
ldr r1,m23_part_cb_AC67
bl m23_callback
mov r6,#0
m23_part_stop_all:
mov r0,r6
bl m23_actor
mov r1,#0
strh r1,[r0,#0xc]
strh r1,[r0,#0xe]
add r6,r6,#1
ldrb r0,[r4,#0x2b]
cmp r6,r0
bne m23_part_stop_all
m23_part_round_return:
pop {r4-r11,lr}
bx lr
""")
    for addr in (0xB71C, 0xB950, 0xB999, 0xB99A, 0xBC1C, 0xAC67):
        out.append(f"m23_part_cb_{addr:04X}: .word m23_cb_{addr:04X}\n")
    return "\n".join(out)
