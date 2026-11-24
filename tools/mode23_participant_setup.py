"""Source A30C and A650 participant allocation/intro placement bodies."""
import hashlib
import struct

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
DEPENDENCIES = ("m23_spawn", "m23_actor", "m23_actor_resources", "m23_event",
                "m23_base_param", "m23_evolved_param", "m23_full_evolved_resources",
                "m23_cb_B71C")


def tables(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 participant setup source mismatch")
    rounds = []
    for r in range(7):
        count, mask = source[0x74A34E + r * 2:0x74A350 + r * 2]
        if not 2 <= count <= 6 or mask >> count:
            raise ValueError("mode23 round population/evolution mask")
        op = 0x740900 + struct.unpack_from("<H", source, 0x74A35C + r * 2)[0]
        pos = 0x740900 + struct.unpack_from("<H", source, 0x74A394 + r * 2)[0]
        intro = 0x740900 + struct.unpack_from("<H", source, 0x74A412 + r * 2)[0]
        opponents = list(source[op:op + (count - 1) * 2])
        if max(opponents) >= 15:
            raise ValueError("mode23 opponent ID outside source mini resources")
        rounds.append({"round": r, "count": count, "mask": mask,
                       "opponents": opponents,
                       "positions": list(struct.unpack_from("<" + "h" * count * 2, source, pos)),
                       "intro": list(struct.unpack_from("<" + "h" * count * 2, source, intro))})
    return rounds


def assembly(source):
    rows = tables(source)
    out = ["""
m23_participants_create:
push {r4-r11,lr}
ldrb r0,[r4,#0x2a]
ldr r1,m23_setup_table_ptr
add r1,r1,r0,lsl #4
ldrb r7,[r1]
ldrb r11,[r1,#1]
ldr r8,[r1,#4]
ldr r9,[r1,#8]
strb r7,[r4,#0x2b]
strb r7,[r4,#0x2c]
mov r0,#255
strb r0,[r4,#0x2e]
mov r6,#0
m23_setup_loop:
ldrb r0,[r9]
sub r0,r0,r7
add r0,r0,r6
add r0,r0,#0x2000
ldr r1,m23_setup_idle
mov r2,r4
bl m23_spawn
add r1,r4,r6,lsl #2
str r0,[r1,#0xc]
add r10,r0,#0x18
strb r6,[r10,#2]
ldrb r0,[r4,#0x2d]
cmp r6,#0
beq m23_setup_identity
sub r1,r6,#1
add r1,r8,r1,lsl #1
ldrb r2,[r1]
cmp r2,r0
ldreqb r2,[r1,#1]
mov r0,r2
m23_setup_identity:
strb r0,[r10,#3]
ldrh r1,[r9]
strh r1,[r10,#4]
strh r1,[r10,#8]
ldrh r1,[r9,#2]
strh r1,[r10,#6]
strh r1,[r10,#0xa]
mov r1,#1
mov r1,r1,lsl r6
tst r11,r1
beq m23_setup_base
mov r1,#0x8000
strh r1,[r10]
bl m23_evolved_param
b m23_setup_param
m23_setup_base:
bl m23_base_param
m23_setup_param:
str r0,[r10,#0x20]
mov r0,r10
bl m23_actor_resources
mov r0,r10
mov r1,#0
bl m23_event
add r9,r9,#4
add r6,r6,#1
cmp r6,r7
bne m23_setup_loop
pop {r4-r11,lr}
bx lr

m23_intro_actors:
push {r4-r11,lr}
ldrb r0,[r4,#0x2a]
ldr r1,m23_setup_table_ptr
add r1,r1,r0,lsl #4
ldrb r7,[r1]
ldrb r11,[r1,#1]
ldr r9,[r1,#12]
mov r6,#0
m23_intro_actor_loop:
mov r0,r6
bl m23_actor
mov r10,r0
ldrh r1,[r10,#0x2c]
orr r1,r1,#0x2000
strh r1,[r10,#0x2c]
ldrh r1,[r10,#0x2e]
orr r1,r1,#0x2000
strh r1,[r10,#0x2e]
ldrh r0,[r9]
ldrh r1,[r9,#2]
strh r1,[r10,#6]
cmp r6,#0
addeq r0,r0,#0xb000
addne r0,r0,#0x5000
strh r0,[r10,#4]
mov r0,#0x600
rsbne r0,r0,#0
strh r0,[r10,#0xc]
mov r0,#1
mov r0,r0,lsl r6
tst r11,r0
beq m23_intro_actor_next
ldrh r0,[r10,#6]
sub r0,r0,#0x1800
strh r0,[r10,#6]
mov r0,r10
bl m23_full_evolved_resources
m23_intro_actor_next:
add r9,r9,#4
add r6,r6,#1
cmp r6,r7
bne m23_intro_actor_loop
pop {r4-r11,lr}
bx lr
m23_setup_idle: .word m23_cb_B71C
m23_setup_table_ptr: .word m23_setup_table
m23_setup_table:
"""]
    for r in rows:
        n = r["round"]
        out.append(f'.byte {r["count"]},{r["mask"]},0,0\n.word m23_setup_op_{n},m23_setup_pos_{n},m23_setup_intro_{n}\n')
    for r in rows:
        n = r["round"]
        out.append(f'm23_setup_op_{n}: .byte ' + ",".join(map(str, r["opponents"])) + "\n.align 2\n")
        for k in ("positions", "intro"):
            label = "pos" if k == "positions" else k
            out.append(f'm23_setup_{label}_{n}: .hword ' + ",".join(str(v & 65535) for v in r[k]) + "\n")
    out.append(".align 2\n")
    return "\n".join(out).replace("ldreqb", "ldrbeq")
