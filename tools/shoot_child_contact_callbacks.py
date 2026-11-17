"""Source stage11 contact successor966A/96E6/973E and typed collision route.

The scene builder supplies a proven native effect constructor address. This
module does not install a menu, allocate RAM, or substitute a missing service.
"""
import hashlib

SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def assembly(source, effect_constructor):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError("immutable WSC1.5 source required")
    if not isinstance(effect_constructor, int) or not 0x08000000 <= effect_constructor < 0x09000000 or effect_constructor & 3:
        raise ValueError("proven aligned native visual-effect constructor required")
    return f"""
child_contact_route:
push {{r0-r3,lr}}
mrs r3,cpsr
ldr r0,child_config
ldrb r0,[r0,#14]
cmp r0,#11
beq child_source_route
msr cpsr_f,r3
pop {{r0-r3,lr}}
ldr r8,child_retail_callback
b 0x0836f780
child_source_route:
ldr r8,child_contact_first
str r8,[r4]
ldrh r8,[r4,#4]
bic r8,r8,#0xc100
strh r8,[r4,#4]
ldr r1,[r4,#0x14]
ldr r1,[r1,#0x20]
ldr r9,child_duration
strh r9,[r1,#0x76]
pop {{r0-r3,lr}}
b 0x0836e484
child_config: .word 0x03002310
child_retail_callback: .word 0x083723e0
child_duration: .word 0x465
child_contact_first: .word child_contact_966a

child_contact_966a:
push {{r0-r12,lr}}
ldr r1,[r4,#0x18]
ldrh r8,[r1,#8]
orr r8,r8,#0x10
bic r8,r8,#0x800
orr r8,r8,#0x8000
strh r8,[r1,#8]
push {{r4,r5}}
mov r5,r1
mov r11,#0
push {{r1}}
mov r8,#0
push {{r8}}
push {{r8}}
push {{r8}}
mov r8,#3
push {{r8}}
bl 0x{effect_constructor:08X}
add sp,sp,#20
pop {{r4,r5}}
ldr r8,child_hold_duration
strh r8,[r4,#0x94]
mov r8,#0x4a
mov r9,#1
mov r10,#0
bl 0x080d15c0
mov r0,#1
bl child_contact_event
ldr r8,child_contact_wait
str r8,[r4]
ldr r0,child_match_flags
ldrh r1,[r0]
orr r1,r1,#0x10
strh r1,[r0]
ldr r0,child_scroll_counter
mvn r1,#0
strh r1,[r0]
pop {{r0-r12,lr}}
bx lr
child_hold_duration: .word 0x465
child_contact_wait: .word child_contact_96e6
child_match_flags: .word 0x0300450a
child_scroll_counter: .word 0x03004d40

child_contact_96e6:
push {{r0-r12,lr}}
bl child_contact_update
ldr r1,[r4,#0x18]
ldrh r8,[r1,#8]
tst r8,#0x4000
movne r8,#1
strhne r8,[r4,#0x94]
ldrh r8,[r4,#0x94]
sub r8,r8,#1
strh r8,[r4,#0x94]
movs r8,r8,lsl #16
bne child_contact_follow
ldrh r8,[r1,#8]
bic r8,r8,#0x10
orr r8,r8,#0x800
strh r8,[r1,#8]
mov r0,#2
bl child_contact_event
ldr r8,child_contact_release
str r8,[r4]
ldr r0,child_wait_flags
ldrh r1,[r0]
bic r1,r1,#0x10
strh r1,[r0]
pop {{r0-r12,lr}}
bx lr
child_contact_release: .word child_contact_973e
child_wait_flags: .word 0x0300450a

child_contact_973e:
push {{r0-r12,lr}}
ldrh r8,[r5,#0xa]
tst r8,#0x2000
bne child_contact_retire
bl child_contact_update
b child_contact_follow
child_contact_retire:
push {{r4}}
mov r8,#0
push {{r8}}
bl 0x083524c4
add sp,sp,#8
ldr r0,child_retire_flags
ldrh r1,[r0]
bic r1,r1,#0x40
strh r1,[r0]
pop {{r0-r12,lr}}
bx lr
child_retire_flags: .word 0x0300450a

child_contact_follow:
ldrh r8,[r4,#4]
eor r8,r8,#0x20
strh r8,[r4,#4]
ldr r1,[r4,#0x18]
ldrh r0,[r1,#0xb4]
and r0,r0,#0x4000
ldrh r8,[r5,#8]
bic r8,r8,#0x4000
orr r8,r8,r0
strh r8,[r5,#8]
ldrh r0,[r1,#0x34]
strh r0,[r4,#0x34]
ldrh r0,[r1,#0x36]
sub r0,r0,#0x100
strh r0,[r4,#0x36]
pop {{r0-r12,lr}}
bx lr

child_contact_event:
push {{lr}}
push {{r5}}
mov r8,#0
push {{r8}}
push {{r0}}
bl 0x08012874
add sp,sp,#12
pop {{lr}}
bx lr
child_contact_update:
push {{lr}}
push {{r5}}
mov r8,#0
push {{r8}}
mov r8,#1
push {{r8}}
bl 0x08012a84
add sp,sp,#12
pop {{lr}}
bx lr
"""
