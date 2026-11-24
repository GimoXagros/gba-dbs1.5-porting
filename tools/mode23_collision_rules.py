"""Source BF42..C774 collision body, linked into the owned mode23 scene.

R4 is the scene context; all R4..R11 are preserved. No ROM/RAM allocation.
The pickup presentation transaction is supplied by the scene author. Arithmetic
keeps source halfword truncation, Newton termination, and asymmetric responses.
Source atan(0,0) and sqrt(0) divide by zero; those inputs are NOT a parity claim.
"""
import hashlib

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
DEPENDENCIES = ('m23_actor', 'm23_callback', 'm23_sound',
                'm23_collision_pickup', 'm23_cb_B7D9', 'm23_cb_BC1C',
                'm23_sin', 'm23_cos')


def assembly(source):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError('collision source is not the immutable WSC1.5 image')
    if source[0x74D074] != 0xCB or source[0x74D18C] != 0xCB:
        raise ValueError('collision/angle-difference return boundary')

    def sx(reg):
        return f'mov {reg},{reg},lsl #16\nmov {reg},{reg},asr #16\n'

    # Product is shifted as a signed 32-bit value, THEN narrowed to AX.
    def product():
        return 'mul r2,r0,r1\nmov r0,r2,asr #8\n' + sx('r0')

    text = r'''
m23_src_BF42:
push {r4-r11,lr}
sub sp,sp,#4
ldrb r10,[r4,#0x2b]
mov r8,r10
m23_bf42_clear:
sub r8,r8,#1
mov r0,r8
bl m23_actor
mov r1,#0
strh r1,[r0,#0x18]
strh r1,[r0,#0x1a]
strh r1,[r0,#0x1c]
cmp r8,#0
bne m23_bf42_clear
mov r8,#0
m23_bf42_outer:
mov r0,r8
bl m23_actor
mov r6,r0
ldrh r0,[r6]
tst r0,#1
bne m23_bf42_next_i
add r9,r8,#1
m23_bf42_inner:
mov r0,r9
bl m23_actor
mov r7,r0
ldrh r0,[r7]
tst r0,#1
bne m23_bf42_next_j
mov r0,r6
mov r1,r7
bl m23_bf42_distance
cmp r0,#0
bge m23_bf42_next_j
rsb r0,r0,#0
mov r0,r0,lsl #16
mov r0,r0,lsr #16
bl m23_bf42_separate
mov r0,r6
mov r1,r7
mov r2,#0
bl m23_bf42_response
mov r0,r7
mov r1,r6
mov r2,#1
bl m23_bf42_response
'''
    for actor in ('r6', 'r7'):
        for velocity, correction in ((0xC, 0x14), (0xE, 0x16)):
            text += f'ldrh r0,[{actor},#{velocity}]\nldrh r1,[{actor},#{correction}]\nadd r0,r0,r1\nstrh r0,[{actor},#{velocity}]\n'
        text += f'mov r0,{actor}\nldr r1,m23_bf42_cb_b7d9\nbl m23_callback\n'
    # All three source strength branches write the identical sound request.
    # The otherwise uninitialized stack strength is not consumed elsewhere.
    text += r'''
mov r0,#0xd9
mov r1,#1
bl m23_sound
m23_bf42_next_j:
add r9,r9,#1
cmp r9,r10
blt m23_bf42_inner
m23_bf42_next_i:
add r8,r8,#1
sub r0,r10,#1
cmp r8,r0
blt m23_bf42_outer
mov r8,r10
m23_bf42_average_loop:
sub r8,r8,#1
mov r0,r8
bl m23_actor
mov r6,r0
ldrh r7,[r6,#0x18]
cmp r7,#0
beq m23_bf42_average_next
'''
    for correction, position in ((0x1A, 4), (0x1C, 6)):
        text += f'ldrsh r0,[r6,#{correction}]\nmov r1,r7\nbl m23_bf42_sdiv\nstrh r0,[r6,#{correction}]\nldrh r1,[r6,#{position}]\nadd r0,r0,r1\nstrh r0,[r6,#{position}]\n'
    text += r'''
m23_bf42_average_next:
cmp r8,#0
bne m23_bf42_average_loop
ldrh r0,[r4,#0x24]
tst r0,#4
beq m23_bf42_done
ldr r7,[r4,#8]
add r7,r7,#0x18
mov r8,#0
m23_bf42_aux_loop:
mov r0,r8
bl m23_actor
mov r6,r0
ldrh r0,[r6]
tst r0,#1
bne m23_bf42_aux_next
mov r0,r6
mov r1,r7
bl m23_bf42_distance
cmp r0,#0
bge m23_bf42_aux_next
ldrh r0,[r4,#0x24]
bic r0,r0,#4
strh r0,[r4,#0x24]
ldrh r0,[r6]
tst r0,#0x8000
beq m23_bf42_pickup
mov r0,r7
ldr r1,m23_bf42_cb_bc1c
bl m23_callback
mov r0,#0x9a
mov r1,#1
bl m23_sound
b m23_bf42_done
m23_bf42_pickup:
mov r0,r6
mov r1,r7
bl m23_collision_pickup
b m23_bf42_done
m23_bf42_aux_next:
add r8,r8,#1
cmp r8,r10
blt m23_bf42_aux_loop
m23_bf42_done:
add sp,sp,#4
pop {r4-r11,lr}
bx lr
m23_bf42_cb_b7d9:
.word m23_cb_B7D9
m23_bf42_cb_bc1c:
.word m23_cb_BC1C

m23_bf42_distance:
ldrsh r2,[r0,#4]
ldrsh r3,[r1,#4]
mov r2,r2,asr #4
sub r2,r2,r3,asr #4
mul r12,r2,r2
mov r12,r12,lsr #4
ldrsh r2,[r0,#6]
ldrsh r3,[r1,#6]
mov r2,r2,asr #4
sub r2,r2,r3,asr #4
mul r0,r2,r2
add r0,r12,r0,lsr #4
sub r0,r0,#0x1000
bx lr

m23_bf42_relative:
ldrsh r0,[r7,#0xa]
ldrsh r1,[r6,#0xa]
sub r0,r0,r1
mov r0,r0,lsl #16
mov r0,r0,asr #16
ldrsh r1,[r7,#8]
ldrsh r2,[r6,#8]
sub r1,r1,r2
mov r1,r1,lsl #16
mov r1,r1,asr #16
bx lr

m23_bf42_separate:
push {r8-r9,lr}
sub sp,sp,#4
bl m23_bf42_sqrt
mov r0,r0,lsl #6
mov r0,r0,lsl #16
mov r9,r0,asr #16
bl m23_bf42_relative
bl m23_bf42_atan
mov r8,r0
'''
    for trig, offset in (('cos', 0x1A), ('sin', 0x1C)):
        text += f'mov r0,r8\nbl m23_bf42_{trig}\nmov r1,r9\n' + product()
        # Source SAR AX,1 follows the eight DX:AX shifts.
        text += f'mov r0,r0,asr #1\nldrh r1,[r7,#{offset}]\nadd r1,r1,r0\nstrh r1,[r7,#{offset}]\nldrh r1,[r6,#{offset}]\nsub r1,r1,r0\nstrh r1,[r6,#{offset}]\n'
    text += r'''
ldrh r0,[r6,#0x18]
add r0,r0,#1
strh r0,[r6,#0x18]
ldrh r0,[r7,#0x18]
add r0,r0,#1
strh r0,[r7,#0x18]
add sp,sp,#4
pop {r8-r9,lr}
bx lr

m23_bf42_response:
push {r6-r11,lr}
sub sp,sp,#4
mov r6,r0
mov r7,r1
mov r11,r2
ldrsh r0,[r6,#0xc]
mul r2,r0,r0
mov r2,r2,lsr #8
ldrsh r0,[r6,#0xe]
mul r1,r0,r0
add r0,r2,r1,lsr #8
mov r0,r0,lsl #16
movs r0,r0,lsr #16
beq m23_bf42_response_done
bl m23_bf42_sqrt
mov r0,r0,lsl #4
mov r0,r0,lsl #16
mov r8,r0,asr #16
bl m23_bf42_relative
mov r9,r1
mov r10,r0
cmp r11,#0
bne m23_bf42_response_second
bl m23_bf42_atan
mov r11,r0
ldrsh r0,[r6,#0xe]
ldrsh r1,[r6,#0xc]
bl m23_bf42_atan
and r0,r0,#255
and r11,r11,#255
sub r0,r11,r0
cmp r0,#0
ble m23_bf42_angle_negative
cmp r0,#0x7f
rsbge r0,r0,#0
b m23_bf42_response_angle
m23_bf42_angle_negative:
rsb r0,r0,#0
b m23_bf42_response_angle
m23_bf42_response_second:
ldrsh r2,[r6,#0xe]
sub r0,r10,r2
mov r0,r0,lsl #16
mov r0,r0,asr #16
ldrsh r2,[r6,#0xc]
sub r1,r9,r2
mov r1,r1,lsl #16
mov r1,r1,asr #16
bl m23_bf42_atan
m23_bf42_response_angle:
bl m23_bf42_cos
mov r1,r8
'''
    text += product() + r'''
cmp r0,#0
rsblt r0,r0,#0
mov r0,r0,lsl #16
mov r8,r0,asr #16
mov r0,r10
mov r1,r9
bl m23_bf42_atan
mov r11,r0
'''
    for trig, offset in (('cos', 0x14), ('sin', 0x16)):
        text += f'mov r0,r11\nbl m23_bf42_{trig}\nmov r1,r8\n' + product()
        text += f'strh r0,[r7,#{offset}]\nrsb r0,r0,#0\nstrh r0,[r6,#{offset}]\n'
    text += r'''
m23_bf42_response_done:
add sp,sp,#4
pop {r6-r11,lr}
bx lr

m23_bf42_sdiv:
push {r4,lr}
mov r4,r0
cmp r0,#0
rsblt r0,r0,#0
bl m23_bf42_udiv
cmp r4,#0
rsblt r0,r0,#0
pop {r4,lr}
bx lr

m23_bf42_udiv:
mov r2,#0
mov r3,#32
mov r12,#0
m23_bf42_div_loop:
movs r0,r0,lsl #1
adc r2,r2,r2
cmp r2,r1
subhs r2,r2,r1
adc r12,r12,r12
subs r3,r3,#1
bne m23_bf42_div_loop
mov r0,r12
bx lr

m23_bf42_sqrt:
push {r4-r7,lr}
mov r4,r0
mov r5,r0
mov r6,#0
m23_bf42_sqrt_loop:
add r6,r6,#1
mov r0,r4
mov r1,r5
bl m23_bf42_udiv
add r0,r0,r5
mov r0,r0,lsl #16
mov r7,r0,lsr #17
sub r0,r7,r5
mov r0,r0,lsl #16
mov r0,r0,asr #16
cmp r0,#0
rsblt r0,r0,#0
mov r0,r0,lsl #16
mov r0,r0,asr #16
mov r5,r7
cmp r6,#40
bge m23_bf42_sqrt_limit
cmp r0,#2
bgt m23_bf42_sqrt_loop
mov r0,r7
b m23_bf42_sqrt_done
m23_bf42_sqrt_limit:
mvn r0,#1
mov r0,r0,lsl #16
mov r0,r0,lsr #16
m23_bf42_sqrt_done:
pop {r4-r7,lr}
bx lr

m23_bf42_atan:
push {r4-r5,lr}
mov r4,#0
cmp r0,#0
blt m23_bf42_atan_negative
cmp r1,#0
bge m23_bf42_atan_quadrant
rsb r1,r1,#0
mov r2,r0
mov r0,r1
mov r1,r2
mov r4,#0x40
b m23_bf42_atan_quadrant
m23_bf42_atan_negative:
rsb r0,r0,#0
cmp r1,#0
rsblt r1,r1,#0
movlt r4,#0x80
blt m23_bf42_atan_quadrant
mov r2,r0
mov r0,r1
mov r1,r2
mvn r4,#0x3f
m23_bf42_atan_quadrant:
mov r0,r0,lsl #16
mov r0,r0,asr #16
mov r1,r1,lsl #16
mov r1,r1,asr #16
mov r5,#0
cmp r0,r1
ble m23_bf42_atan_ratio
mov r2,r0
mov r0,r1
mov r1,r2
mov r5,#1
m23_bf42_atan_ratio:
mov r0,r0,lsl #16
mov r0,r0,lsr #16
mov r1,r1,lsl #16
mov r1,r1,lsr #16
cmp r0,#0x4000
movlo r0,r0,lsl #1
movhs r1,r1,lsr #1
cmp r0,r1
movhi r2,#13
movls r2,#19
push {r4}
mov r4,#0
movhi r4,#6
mul r3,r0,r2
mov r0,r3
bl m23_bf42_udiv
add r0,r0,r4
pop {r4}
cmp r5,#0
rsbne r0,r0,#0x40
add r0,r0,r4
mov r0,r0,lsl #16
mov r0,r0,asr #16
pop {r4-r5,lr}
bx lr

m23_bf42_cos:
b m23_cos
m23_bf42_sin:
b m23_sin
'''
    return text
