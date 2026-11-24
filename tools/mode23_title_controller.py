"""Expanded title task phases; preserve native prompt, timeout and palette task.

No ROM writes here. New tree/root drawing is mutually exclusive and reuses
five existing presentations. Native paired timeout/window/blink timing stays
at its existing hardware values; new source submenu slides use eight pixels.
"""
import hashlib,struct
from mode23_title_tree import contract,SOURCE
NATIVE='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
CALLBACKS=('m23_title_init_callback','m23_title_enter_root','m23_title_slide_in','m23_title_idle','m23_title_slide_out','m23_title_confirm_exit')

def assembly(source,native):
 contract(source)
 assert hashlib.sha256(native).hexdigest().upper()==NATIVE
 assert struct.unpack_from('<I',native,0x90E10)[0]==0x665
 assert struct.unpack_from('<I',native,0x90E34)[0]==0x08090E58
 out=[]
 def entry(name,body):
  return name+''':
push {r0-r12,lr}
mov r11,#0
ldr r5,=0x0300133c
ldr r5,[r5]
add r4,r5,#0x18
'''+body+'''
pop {r0-r12,lr}
bx lr
.ltorg
'''
 out.append(entry(CALLBACKS[0],'''
mov r0,r4
bl m23_title_tree_init
ldr r0,=0x08090c7c
str r0,[r5]
bl 0x08090c7c
'''))
 out.append(entry(CALLBACKS[1],'''
mov r0,r4
bl m23_title_tree_apply
mov r0,#0
str r0,[r4,#0x20]
ldr r0,=m23_title_slide_in
str r0,[r5]
bl m23_title_slide_body
'''))
 out.append(entry(CALLBACKS[2],'''bl m23_title_slide_body'''))
 out.append('''m23_title_slide_body:
push {r4-r11,lr}
ldr r0,=0x0300130a
ldrh r0,[r0]
tst r0,#0x45
beq m23_title_slide_normal
tst r0,#0x40
ldrne r1,=0x03002c10
ldrhne r2,[r1]
orrne r2,r2,#1
strhne r2,[r1]
ldr r6,=0x03002a78
ldrb r7,[r4,#6]
mov r0,#112
m23_title_slide_skip:
strh r0,[r6]
add r6,r6,#0x50
subs r7,r7,#1
bne m23_title_slide_skip
ldrb r0,[r4,#6]
str r0,[r4,#0x20]
ldr r0,=m23_title_idle
str r0,[r5]
b m23_title_slide_draw
m23_title_slide_normal:
ldr r6,=0x03002a78
ldrb r7,[r4,#6]
mov r8,#0
m23_title_slide_rows:
ldr r0,[r4,#0x20]
cmp r0,r8
bne m23_title_slide_next
ldrh r0,[r6,#2]
cmp r0,#200
beq m23_title_slide_advance
ldrsh r0,[r6]
add r0,r0,#8
strh r0,[r6]
cmp r0,#112
blt m23_title_slide_next
mov r0,#112
strh r0,[r6]
m23_title_slide_advance:
add r0,r8,#1
str r0,[r4,#0x20]
cmp r0,r7
ldrge r0,=m23_title_idle
strge r0,[r5]
m23_title_slide_next:
add r6,r6,#0x50
add r8,r8,#1
cmp r8,r7
blo m23_title_slide_rows
m23_title_slide_draw:
mvn r0,#0
mov r1,#0
bl m23_title_draw_rows
pop {r4-r11,lr}
bx lr
.ltorg
''')
 out.append(entry(CALLBACKS[3],'''
ldr r0,=0x0300130a
ldrh r6,[r0]
ldr r7,=0x03002c10
ldrh r0,[r7]
tst r0,#1
orrne r6,r6,#0x40
mov r0,r4
mov r1,r6
bl m23_title_tree_action
mov r8,r0
cmp r8,#3
beq m23_title_idle_timeout
ldrh r0,[r4]
add r0,r0,#1
strh r0,[r4]
ldrh r1,[r4,#2]
add r1,r1,#1
strh r1,[r4,#2]
ldr r1,=0x665
cmp r0,r1
bge m23_title_idle_timeout
cmp r8,#2
beq m23_title_idle_confirm
cmp r8,#1
ldreq r0,=m23_title_slide_out
streq r0,[r5]
beq m23_title_idle_draw
@ The temporary absent22 guard must not trap a queued skip-animation A.
@ Source first row is normally activatable; this path is target-only.
ldrb r0,[r4,#4]
cmp r0,#2
bne m23_title_idle_move
ldrb r0,[r4,#5]
cmp r0,#0
bne m23_title_idle_move
bl m23_title_handler22_available
cmp r0,#0
bne m23_title_idle_move
ldrh r0,[r7]
bic r0,r0,#1
strh r0,[r7]
m23_title_idle_move:
mov r0,r4
mov r1,r6
bl m23_title_tree_move
b m23_title_idle_draw
m23_title_idle_timeout:
ldr r0,=0x08091598
str r0,[r5]
ldrh r0,[r7]
orr r0,r0,#2
strh r0,[r7]
ldr r1,=0x03002c08
mov r0,#16
strh r0,[r1]
mov r0,#0
strh r0,[r1,#2]
mov r0,#40
strh r0,[r1,#4]
b m23_title_idle_draw
m23_title_idle_confirm:
ldr r0,=m23_title_confirm_exit
str r0,[r5]
bl m23_title_begin_confirm
m23_title_idle_draw:
ldrb r0,[r4,#5]
mov r1,#0
bl m23_title_draw_rows
'''))
 out.append(entry(CALLBACKS[4],'''
ldr r6,=0x03002a78
ldrb r7,[r4,#6]
m23_title_out_rows:
ldrh r0,[r6]
add r0,r0,#8
strh r0,[r6]
add r6,r6,#0x50
subs r7,r7,#1
bne m23_title_out_rows
mov r8,r0
ldrb r0,[r4,#5]
mov r1,#0
bl m23_title_draw_rows
cmp r8,#272
blo m23_title_out_done
mov r0,r4
bl m23_title_tree_apply
mov r0,#0
str r0,[r4,#0x20]
ldr r0,=m23_title_slide_in
str r0,[r5]
m23_title_out_done:
'''))
 out.append('''m23_title_begin_confirm:
push {r4-r11,lr}
ldrb r0,[r4,#5]
ldr r1,[r4,#0x18]
add r1,r1,r0,lsl #2
ldrh r2,[r1,#2]
ldr r1,=0x030012bc
mov r0,#72
strb r0,[r1]
strb r0,[r1,#1]
strb r2,[r1,#2]
strb r2,[r1,#3]
ldr r1,=0x030012b6
ldrh r0,[r1]
orr r0,r0,#0x27
strh r0,[r1]
ldr r1,=0x03002c0e
mov r0,#0
strh r0,[r1]
ldr r6,=0x03002310
strb r0,[r6,#0xe]
strb r0,[r6,#0x1e]
strb r0,[r6,#0x1f]
ldrh r0,[r4,#2]
push {r0}
ldr r0,=0x030012d0
ldrh r0,[r0]
push {r0}
mov r11,#0
bl 0x08012634
add sp,sp,#8
bl 0x08012600
strh r0,[r6,#0x12]
bl 0x08012600
strh r0,[r6,#0x14]
bl 0x08012600
strh r0,[r6,#0x16]
bl 0x08012600
and r0,r0,#7
strb r0,[r6,#0x1f]
pop {r4-r11,lr}
bx lr
.ltorg
''')
 out.append(entry(CALLBACKS[5],'''
ldr r7,=0x030012bc
mov r6,#0
ldrb r0,[r7]
subs r0,r0,#3
movle r0,#0
addle r6,r6,#1
strb r0,[r7]
ldrb r0,[r7,#2]
subs r0,r0,#3
movle r0,#0
addle r6,r6,#1
strb r0,[r7,#2]
ldrb r0,[r7,#1]
add r0,r0,#3
cmp r0,#224
movhs r0,#224
addhs r6,r6,#1
strb r0,[r7,#1]
ldrb r0,[r7,#3]
add r0,r0,#3
cmp r0,#144
movhs r0,#144
addhs r6,r6,#1
strb r0,[r7,#3]
ldr r7,=0x03002c0e
ldrh r0,[r7]
add r0,r0,#1
strh r0,[r7]
tst r0,#6
and r0,r0,#0x8000
eor r0,r0,#0x8000
strhne r0,[r7]
mov r1,r0,lsr #15
ldrb r0,[r4,#5]
bl m23_title_draw_rows
cmp r6,#4
blo m23_title_exit_done
mov r0,r4
bl m23_title_exit_config
ldr r6,=0x03002a74
ldr r6,[r6]
push {r5}
mov r0,#0
push {r0}
mov r11,#0
bl 0x08011be4
add sp,sp,#8
push {r6}
mov r0,#0
push {r0}
mov r11,#0
bl 0x08011be4
add sp,sp,#8
bl 0x08012714
m23_title_exit_done:
'''))
 out.append('''m23_title_draw_rows:
push {r4-r11,lr}
mov r6,r0
mov r7,r1
@ Exactly two existing palette owners; no third sprite/overlay task.
ldr r0,=0x03002c18
ldr r1,=0x05000220
mov r2,#8
m23_title_copy_selected:
ldr r3,[r0],#4
str r3,[r1],#4
subs r2,r2,#1
bne m23_title_copy_selected
mov r2,#8
m23_title_copy_unselected:
ldr r3,[r0],#4
str r3,[r1],#4
subs r2,r2,#1
bne m23_title_copy_unselected
ldr r8,=0x03002a78
ldrb r9,[r4,#6]
mov r10,#0
m23_title_draw_loop:
cmp r10,r6
moveq r0,#1
movne r0,#2
strh r0,[r8,#0x10]
bne m23_title_draw_visible
cmp r7,#0
bne m23_title_draw_next
m23_title_draw_visible:
@ Native renderer uses R8-R11 scratch: protect the loop's live values.
push {r4-r11}
push {r8}
mov r0,#0
push {r0}
mov r11,#0
bl 0x08012c28
add sp,sp,#8
pop {r4-r11}
m23_title_draw_next:
add r8,r8,#0x50
add r10,r10,#1
cmp r10,r9
blo m23_title_draw_loop
pop {r4-r11,lr}
bx lr
.ltorg

m23_title_event:
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
.ltorg
''')
 return '\n'.join(out)
