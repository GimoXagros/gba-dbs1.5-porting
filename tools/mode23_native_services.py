"""Typed mode23 adapters to established native task/presentation services.

Unresolved display/audio/save ownership is not represented by a no-op. These
adapters preserve R4..R11 even where the underlying commercial ABI does not.
"""
import hashlib

BASE_SHA = "574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"


def assembly(native):
    if hashlib.sha256(native).hexdigest().upper() not in (BASE_SHA, "5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC"):
        raise ValueError("native mode23 service predecessor mismatch")
    return """
m23_actor:
add r0,r4,r0,lsl #2
ldr r0,[r0,#0xc]
add r0,r0,#0x18
bx lr
m23_callback:
str r1,[r0,#-0x18]
bx lr
m23_held:
ldr r0,m23_native_input
ldrh r0,[r0]
bx lr
m23_pressed:
ldr r0,m23_native_input
ldrh r0,[r0,#4]
bx lr
m23_native_input: .word 0x03001302
m23_framecounter:
ldr r0,m23_native_frame
ldrb r0,[r0]
bx lr
m23_native_frame: .word 0x030012d0
m23_selected:
ldr r0,m23_native_game_config
ldrb r0,[r0,#0xa]
bx lr
m23_native_game_config: .word 0x03002310
m23_request_exit:
ldr r1,m23_native_game_config
mov r0,#1
strh r0,[r1,#4]
mov r0,#0
strh r0,[r1,#6]
strh r0,[r1,#8]
bx lr

m23_display_zero:
ldr r1,m23_display_shadow
mov r0,#0
strh r0,[r1]
bx lr
m23_display_low:
ldr r1,m23_display_shadow
strb r0,[r1]
bx lr
m23_display_enable:
ldr r1,m23_display_shadow
ldrb r0,[r1]
orr r0,r0,#0x8000
strh r0,[r1]
bx lr
m23_bg2_enable:
ldr r1,m23_display_shadow
ldrb r2,[r1]
cmp r0,#0
biceq r2,r2,#2
orrne r2,r2,#2
strb r2,[r1]
bx lr
m23_window_left:
ldr r1,m23_display_shadow
strb r0,[r1,#6]
bx lr
m23_window_top:
ldr r1,m23_display_shadow
strb r0,[r1,#8]
bx lr
m23_window_right:
ldr r1,m23_display_shadow
strb r0,[r1,#7]
bx lr
m23_window_bottom:
ldr r1,m23_display_shadow
strb r0,[r1,#9]
bx lr
m23_scroll2_step:
ldr r1,m23_display_shadow
ldrb r0,[r1,#4]
sub r0,r0,#1
strb r0,[r1,#4]
bx lr
m23_scroll2_zero:
ldr r1,m23_display_shadow
mov r0,#0
strb r0,[r1,#4]
bx lr
m23_scroll_reset:
ldr r1,m23_display_shadow
mov r0,#0
str r0,[r1,#2]
bx lr
m23_display_shadow: .word 0x030012b6
m23_retire_vcount:
mov r0,#0x04000000
add r1,r0,#0x200
ldrh r2,[r1]
bic r2,r2,#4
strh r2,[r1]
ldrh r2,[r0,#4]
bic r2,r2,#0x20
strh r2,[r0,#4]
mov r2,#4
strh r2,[r1,#2]
bx lr
m23_obj_color0:
mov r1,#0x05000000
add r1,r1,#0x100
strh r0,[r1]
add r1,r1,#0x100
strh r0,[r1]
bx lr

m23_atan:
b m23_bf42_atan
m23_rng:
push {r4-r11,lr}
mov r11,#0
bl 0x08012600
pop {r4-r11,lr}
bx lr
m23_audio_reset:
push {r4-r11,lr}
mov r11,#0
bl 0x0801565c
pop {r4-r11,lr}
bx lr
m23_audio_service:
push {r4-r11,lr}
mov r11,#0
bl 0x080d1500
pop {r4-r11,lr}
bx lr
m23_cos:
push {r4-r11,lr}
push {r0}
mov r11,#0
bl 0x0801233c
add sp,sp,#4
pop {r4-r11,lr}
bx lr
m23_sin:
push {r4-r11,lr}
push {r0}
mov r11,#0
bl 0x08012348
add sp,sp,#4
pop {r4-r11,lr}
bx lr

m23_priority:
push {r4-r11,lr}
sub r0,r0,#0x18
mov r1,r1,lsl #16
mov r1,r1,asr #16
push {r0}
mov r2,#0
push {r2}
push {r1}
mov r11,#0
bl 0x08011e54
add sp,sp,#12
pop {r4-r11,lr}
bx lr

m23_spawn:
push {r4-r11,lr}
mov r6,r2
push {r1}
mov r2,#0
push {r2}
push {r0}
mov r11,#0
bl 0x08011ac4
add sp,sp,#12
add r1,r0,#0x18
mov r2,#0
mov r3,#64
m23_native_clear_payload:
str r2,[r1],#4
subs r3,r3,#1
bne m23_native_clear_payload
str r6,[r0,#0x114]
pop {r4-r11,lr}
bx lr
m23_release:
push {r4-r11,lr}
push {r0}
mov r1,#0
push {r1}
mov r11,#0
bl 0x08011be4
add sp,sp,#8
pop {r4-r11,lr}
bx lr

m23_event:
add r0,r0,#0x24
b m23_present_event
m23_present_event:
push {r4-r11,lr}
push {r0}
mov r2,#0
push {r2}
push {r1}
mov r11,#0
bl 0x08012874
add sp,sp,#12
pop {r4-r11,lr}
bx lr
m23_frame:
push {r4-r11,lr}
push {r0}
mov r3,#0
push {r3}
push {r1}
push {r2}
mov r11,#0
bl 0x080129c8
add sp,sp,#16
pop {r4-r11,lr}
bx lr
m23_present_update_draw:
push {r4-r11,lr}
mov r6,r0
push {r6}
mov r1,#0
push {r1}
mov r1,#1
push {r1}
mov r11,#0
bl 0x08012a84
add sp,sp,#12
push {r6}
mov r1,#0
push {r1}
mov r11,#0
bl 0x08012c28
add sp,sp,#8
pop {r4-r11,lr}
bx lr
m23_present_update:
push {r4-r11,lr}
push {r0}
mov r1,#0
push {r1}
mov r1,#1
push {r1}
mov r11,#0
bl 0x08012a84
add sp,sp,#12
pop {r4-r11,lr}
bx lr
m23_present_draw:
push {r4-r11,lr}
push {r0}
mov r1,#0
push {r1}
mov r11,#0
bl 0x08012c28
add sp,sp,#8
pop {r4-r11,lr}
bx lr

m23_present_construct:
push {r4-r11,lr}
sub sp,sp,#60
mov r6,sp
mov r7,#0
mov r8,#15
m23_native_ctor_args:
str r7,[r6],#4
subs r8,r8,#1
bne m23_native_ctor_args
str r0,[sp,#56]
ldr r0,[r1]
str r0,[sp,#48]
ldr r0,[r1,#4]
str r0,[sp,#36]
ldr r0,[r1,#8]
str r0,[sp,#24]
mov r0,#0x4000
str r0,[sp,#12]
mov r0,#0x1800
str r0,[sp,#8]
str r2,[sp,#4]
str r3,[sp]
mov r11,#0
bl 0x080127e4
add sp,sp,#60
pop {r4-r11,lr}
bx lr

m23_palette:
push {r4-r11,lr}
push {r0}
mov r2,#0
push {r2}
push {r2}
push {r2}
push {r1}
mov r11,#0
bl 0x080132ec
add sp,sp,#20
pop {r4-r11,lr}
bx lr

m23_full_evolved_resources:
push {r4-r11,lr}
mov r6,r0
ldrb r0,[r6,#3]
ldr r1,m23_full_evolved_table
add r1,r1,r0,lsl #5
add r0,r6,#0x24
ldrh r3,[r0,#0x10]
mov r12,#0
bl m23_full_view
ldrh r0,[r6,#0x2e]
orr r0,r0,#0x2000
strh r0,[r6,#0x2e]
pop {r4-r11,lr}
bx lr
m23_full_base_resources:
push {r4-r11,lr}
mov r12,r2
ldr r2,m23_full_base_table
add r1,r2,r1,lsl #5
mov r3,#0
bl m23_full_view
pop {r4-r11,lr}
bx lr
m23_full_view:
push {r4-r11,lr}
sub sp,sp,#12
ldr r2,[r1,#4]
str r2,[sp]
ldr r2,[r1]
str r2,[sp,#4]
ldr r2,[r1,#8]
str r2,[sp,#8]
mov r1,sp
mov r2,#0x80
bl m23_view_install
add sp,sp,#12
pop {r4-r11,lr}
bx lr
m23_full_evolved_table: .word 0x0860b000
m23_full_base_table: .word 0x084a80f8
"""


def wrappers(entries):
    """Each native callback resolves only its own initialized context pointer."""
    out = []
    for address in sorted(set(entries)):
        out.append(f"""
m23_cb_{address:04X}:
push {{r0-r12,lr}}
ldr r5,m23_current_{address:04X}
ldr r5,[r5]
add r5,r5,#0x18
ldr r4,[r5,#0xfc]
bl m23_src_{address:04X}
pop {{r0-r12,lr}}
bx lr
m23_current_{address:04X}: .word 0x0300133c
""")
    return "\n".join(out)
