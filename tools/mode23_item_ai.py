"""Source mode23 item creation, pickup transaction and computer targeting.

No native addresses are allocated here. Resource installers and native service
adapters are required imports, not fallback implementations.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
DEPENDENCIES = ("m23_actor", "m23_callback", "m23_priority", "m23_sound",
                "m23_rng", "m23_framecounter", "m23_atan", "m23_item_resources",
                "m23_pickup_resources", "m23_actor_resources", "m23_evolved_param",
                "m23_cb_BC36", "m23_cb_BC5A")


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("mode23 item/AI source mismatch")
    if source[0x74A346:0x74A34E] != bytes((1, 1, 1, 1, 1, 1, 0, 1)):
        raise ValueError("source computer targeting distribution")
    # Three noise blocks intentionally multiply zero: retain the RNG advance
    # and the original zero effect, rather than inventing the apparent intent.
    for at in (0x74C6D1, 0x74C776, 0x74C7FA):
        if source[at:at + 2] != bytes.fromhex("2bc0"):
            raise ValueError(f"source zero-noise anchor {at:X}")
    return """
m23_src_BA57:
push {r4-r11,lr}
ldrh r0,[r4,#0x28]
m23_item_mod3:
cmp r0,#3
subhs r0,r0,#3
bhs m23_item_mod3
cmp r0,#0
bne m23_item_return
ldrh r0,[r4,#0x24]
tst r0,#4
bne m23_item_return
orr r0,r0,#4
strh r0,[r4,#0x24]
ldr r6,[r4,#8]
add r6,r6,#0x18
mov r0,r6
ldr r1,m23_item_cb_BC36
bl m23_callback
mov r0,r6
mov r1,#0x2200
bl m23_priority
mov r0,#0xac
mov r1,#1
bl m23_sound
mov r0,r6
bl m23_item_resources
bl m23_rng
and r0,r0,#255
sub r0,r0,#128
mov r0,r0,lsl #8
cmp r0,#0x4800
movgt r0,#0x4800
cmp r0,#-0x4800
movlt r0,#0x4800
rsblt r0,r0,#0
strh r0,[r6,#4]
bl m23_rng
and r0,r0,#127
sub r0,r0,#64
mov r0,r0,lsl #8
cmp r0,#0x3000
movgt r0,#0x3000
cmp r0,#-0x3000
movlt r0,#0x3000
rsblt r0,r0,#0
strh r0,[r6,#6]
mov r7,#0
m23_item_check_position:
mov r0,r7
bl m23_actor
ldrh r1,[r0]
tst r1,#1
bne m23_item_next_position
ldrsh r1,[r6,#4]
ldrsh r2,[r0,#4]
mov r1,r1,asr #4
sub r1,r1,r2,asr #4
cmp r1,#0
rsblt r1,r1,#0
cmp r1,#0x180
bge m23_item_next_position
ldrsh r1,[r6,#6]
ldrsh r2,[r0,#6]
mov r1,r1,asr #4
sub r1,r1,r2,asr #4
cmp r1,#0
rsblt r1,r1,#0
cmp r1,#0x180
bgt m23_item_next_position
ldrh r0,[r6,#4]
add r0,r0,#0x1000
mov r0,r0,lsl #16
mov r0,r0,asr #16
cmp r0,#0x4800
blt m23_item_store_step
mov r0,#0x4800
rsb r0,r0,#0
ldrh r1,[r6,#6]
add r1,r1,#0x1000
mov r1,r1,lsl #16
mov r1,r1,asr #16
cmp r1,#0x3000
movge r1,#0x3000
rsbge r1,r1,#0
strh r1,[r6,#6]
m23_item_store_step:
strh r0,[r6,#4]
mov r7,#0
b m23_item_check_position
m23_item_next_position:
add r7,r7,#1
ldrb r0,[r4,#0x2b]
cmp r7,r0
bne m23_item_check_position
m23_item_return:
pop {r4-r11,lr}
bx lr

m23_collision_pickup:
push {r4-r11,lr}
mov r6,r0
mov r7,r1
mov r0,r7
ldr r1,m23_item_cb_BC5A
bl m23_callback
mov r0,r7
mov r1,#0x1800
bl m23_priority
mov r0,r7
bl m23_pickup_resources
mov r0,#0x28
strh r0,[r7,#0x1e]
ldrh r0,[r6,#4]
strh r0,[r7,#4]
ldrh r0,[r6,#6]
sub r0,r0,#0xe00
strh r0,[r7,#6]
ldrh r0,[r6]
orr r0,r0,#0x8000
strh r0,[r6]
mov r0,r6
bl m23_actor_resources
ldrb r0,[r6,#3]
bl m23_evolved_param
str r0,[r6,#0x20]
mov r0,#0
strh r0,[r6,#0xc]
strh r0,[r6,#0xe]
mov r0,#0x98
mov r1,#1
bl m23_sound
pop {r4-r11,lr}
bx lr

m23_src_BC9C:
push {r4-r11,lr}
ldrb r0,[r4,#0x2e]
bl m23_actor
mov r6,r0
ldrsh r0,[r6,#4]
cmp r0,#-0x4800
blt m23_ai_center
cmp r0,#0x4800
bgt m23_ai_center
ldrsh r0,[r6,#6]
cmp r0,#-0x3000
blt m23_ai_center
cmp r0,#0x3000
bgt m23_ai_center
ldr r7,[r4,#8]
add r7,r7,#0x18
ldrh r0,[r4,#0x24]
tst r0,#4
beq m23_ai_select
ldrsh r0,[r7,#4]
cmp r0,#-0x4000
blt m23_ai_select
cmp r0,#0x4000
bgt m23_ai_select
ldrsh r0,[r7,#6]
cmp r0,#-0x4000
blt m23_ai_select
cmp r0,#0x4000
bgt m23_ai_select
bl m23_framecounter
tst r0,#1
beq m23_ai_target
m23_ai_select:
bl m23_rng
and r0,r0,#7
cmp r0,#6
beq m23_ai_random_target
mov r0,#0
bl m23_actor
mov r7,r0
b m23_ai_target
m23_ai_random_target:
bl m23_rng
and r8,r0,#15
ldrb r9,[r4,#0x2b]
m23_ai_index_mod:
cmp r8,r9
subhs r8,r8,r9
bhs m23_ai_index_mod
m23_ai_index_test:
ldrb r0,[r6,#2]
cmp r8,r0
beq m23_ai_index_next
mov r0,#1
mov r0,r0,lsl r8
ldrh r1,[r4,#0x26]
tst r0,r1
beq m23_ai_index_found
m23_ai_index_next:
add r8,r8,#1
cmp r8,r9
movge r8,#0
b m23_ai_index_test
m23_ai_index_found:
mov r0,r8
bl m23_actor
mov r7,r0
m23_ai_target:
bl m23_rng
and r0,r0,#0x3f
add r0,r0,#0x10
strb r0,[r4,#0x2f]
ldrsh r1,[r7,#4]
ldrsh r2,[r6,#4]
mov r1,r1,asr #8
sub r1,r1,r2,asr #8
ldrsh r0,[r7,#6]
ldrsh r2,[r6,#6]
mov r0,r0,asr #8
sub r0,r0,r2,asr #8
b m23_ai_angle
m23_ai_center:
bl m23_rng
and r0,r0,#15
add r0,r0,#0x20
strb r0,[r4,#0x2f]
ldrh r1,[r6,#4]
rsb r1,r1,#0
mov r1,r1,lsl #16
mov r1,r1,asr #16
ldrh r0,[r6,#6]
rsb r0,r0,#0
mov r0,r0,lsl #16
mov r0,r0,asr #16
m23_ai_angle:
bl m23_atan
mov r7,r0
bl m23_rng
strh r7,[r6,#0x10]
pop {r4-r11,lr}
bx lr
m23_item_cb_BC36: .word m23_cb_BC36
m23_item_cb_BC5A: .word m23_cb_BC5A
"""
