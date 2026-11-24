"""Mode 22 task-owned viewer callbacks. R0 handoff follows native 080159F0..5A08."""
from convert_wsc_palette_block import convert_color


def assembly(snapshot_reader, song_id):
    assert snapshot_reader % 4 == 0 and 0x08000000 <= snapshot_reader < 0x0A000000
    assert song_id == 122
    return f"""
m22_init:
push {{r1,r3-r12,lr}}
mov r11,#0
ldr r0,=0x030012b6
mov r1,#0
strb r1,[r0]
bl m22_irq_off
sub sp,sp,#44
mov r0,sp
bl 0x{snapshot_reader:08x}
mov r1,r0
mov r0,sp
bl m22_snapshot_classify
mov r6,r0
ldr r0,=0xf100
ldr r1,=m22_render
bl m22_spawn
mov r7,r0
add r4,r7,#0x18
strb r6,[r4,#26]
cmp r6,#8
bhs m22_init_view
add r0,sp,#14
mov r1,r4
mov r2,#13
m22_copy_snapshot:
ldrh r3,[r0],#2
strh r3,[r1],#2
subs r2,r2,#1
bne m22_copy_snapshot
cmp r6,#2
bne m22_init_view
mov r0,sp
bl m22_source_highest
strb r0,[r4,#27]
m22_init_view:
add sp,sp,#44
mov r0,r4
bl m22_prepare
mov r0,r7
mov r2,#1
pop {{r1,r3-r12,pc}}
.ltorg

m22_create:
push {{r0-r12,lr}}
mov r4,r0
mov r8,#{song_id}
mov r9,#4
mov r10,#0
mov r11,#0
bl 0x080d15c0
ldr r0,=0x030012e0
ldr r1,[r0]
str r1,[r4,#0x38]
ldr r1,=m22_line_irq
str r1,[r0]
mov r0,#0x1000
ldr r1,=m22_controller
bl m22_spawn
str r4,[r0,#0x114]
pop {{r0-r12,pc}}
.ltorg

m22_spawn:
push {{r4-r11,lr}}
push {{r1}}
mov r2,#0
push {{r2}}
push {{r0}}
mov r11,#0
bl 0x08011ac4
add sp,sp,#12
add r1,r0,#0x18
mov r2,#0
mov r3,#64
m22_zero_task:
str r2,[r1],#4
subs r3,r3,#1
bne m22_zero_task
pop {{r4-r11,pc}}

m22_release:
push {{r4-r11,lr}}
push {{r0}}
mov r1,#0
push {{r1}}
mov r11,#0
bl 0x08011be4
add sp,sp,#8
pop {{r4-r11,pc}}

m22_render:
push {{r0-r12,lr}}
mov r11,#0
bl 0x080d1500
ldr r0,=0x0300133c
ldr r4,[r0]
add r4,r4,#0x18
bl m22_irq_off
ldr r1,=0x030012b8
ldrb r0,[r1]
sub r0,r0,#1
strb r0,[r1]
and r0,r0,#255
sub r0,r0,#8
mov r1,#0x04000000
strh r0,[r1,#0x14]
mov r0,#16
bl 0x08000c10
bl 0x08000d18
ldrh r0,[r4,#28]
add r0,r0,#1
cmp r0,#19
strhlo r0,[r4,#28]
blo m22_render_done
mov r0,#0
strh r0,[r4,#28]
ldrb r1,[r4,#30]
add r1,r1,#1
and r1,r1,#3
strb r1,[r4,#30]
mov r2,#0x05000000
add r2,r2,#2
ldr r3,={convert_color(0x70)}
mov r5,#0
m22_cycle_rows:
cmp r5,r1
strheq r0,[r2]
strhne r3,[r2]
strh r3,[r2,#2]
strheq r3,[r2,#4]
strhne r0,[r2,#4]
add r2,r2,#6
add r5,r5,#1
cmp r5,#4
blo m22_cycle_rows
m22_render_done:
pop {{r0-r12,pc}}
.ltorg

@ Source848F:0647. VBlank projects the top offset. Both source byte counters
@ start at zero and step oppositely, so IRQ needs no pointer to a scene task.
m22_line_irq:
push {{r0-r3,lr}}
mov r1,#0x04000000
ldrh r0,[r1,#4]
mov r2,r0,lsr #8
cmp r2,#16
bne m22_irq_bottom
and r0,r0,#255
orr r0,r0,#0x9000
strh r0,[r1,#4]
mvn r0,#7
b m22_irq_write_scroll
m22_irq_bottom:
ldr r0,=0x030012b8
ldrb r0,[r0]
rsb r0,r0,#0
and r0,r0,#255
sub r0,r0,#8
m22_irq_write_scroll:
strh r0,[r1,#0x14]
pop {{r0-r3,pc}}
.ltorg

m22_irq_off:
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

m22_controller:
push {{r0-r12,lr}}
ldr r0,=0x0300133c
ldr r6,[r0]
ldr r7,[r6,#0x114]
add r4,r7,#0x18
ldr r1,=0x0300130a
ldrh r0,[r1]
tst r0,#0xc0
beq m22_draw
@ Source still draws the current frame. Release last after all owner reads.
bl m22_draw_body
ldr r1,=0x03002310
mov r0,#1
strh r0,[r1,#4]
mov r0,#0
strh r0,[r1,#6]
strh r0,[r1,#8]
bl m22_irq_off
ldr r1,=0x030012e0
ldr r0,[r4,#32]
str r0,[r1]
ldr r1,=0x030012b8
mov r0,#0
strb r0,[r1]
strb r0,[r1,#2]
mov r1,#0x04000000
mvn r0,#7
strh r0,[r1,#0x10]
strh r0,[r1,#0x14]
mov r0,r6
bl m22_release
mov r0,r7
bl m22_release
pop {{r0-r12,pc}}
m22_draw:
bl m22_draw_body
pop {{r0-r12,pc}}
.ltorg

m22_draw_body:
push {{r4-r11,lr}}
ldrb r0,[r4,#26]
cmp r0,#4
beq m22_name
cmp r0,#2
bne m22_draw_done
mov r5,#9
m22_count:
add r0,r4,r5,lsl #1
ldrh r0,[r0,#4]
cmp r0,#0
beq m22_next_count
add r0,r0,#1
ldr r1,=m22_digit_positions
add r1,r1,r5,lsl #1
ldrh r1,[r1]
and r2,r1,#255
mov r1,r1,lsr #8
mov r3,#0xf000
bl m22_emit_obj
mov r0,#11
sub r1,r1,#8
bl m22_emit_obj
m22_next_count:
subs r5,r5,#1
bpl m22_count
b m22_draw_done
m22_name:
mov r5,#0
m22_name_next:
ldrb r0,[r4,r5]
cmp r0,#0
beq m22_draw_done
sub r0,r0,#31
mov r1,r5,lsl #3
add r1,r1,#100
mov r2,#62
mov r3,#0x8000
bl m22_emit_obj
add r5,r5,#1
cmp r5,#4
blo m22_name_next
m22_draw_done:
pop {{r4-r11,pc}}
.ltorg

@ Append one packed 8x8 tile and OAM entry to the native 11708 uploader.
m22_emit_obj:
push {{r0-r8,lr}}
ldr r4,=0x030012ca
ldrb r5,[r4]
cmp r5,#127
bhs m22_obj_done
mov r0,r0,lsl #23
mov r0,r0,lsr #23
mov r6,#0x06000000
add r6,r6,r0,lsl #5
mov r7,#0x02000000
add r7,r7,r5,lsl #5
mov r8,#8
m22_copy_tiles:
ldr r0,[r6],#4
str r0,[r7],#4
subs r8,r8,#1
bne m22_copy_tiles
ldr r6,=0x03001428
add r6,r6,r5,lsl #3
add r2,r2,#8
strh r2,[r6]
add r1,r1,#8
strh r1,[r6,#2]
orr r3,r3,#0x400
orr r3,r3,r5
strh r3,[r6,#4]
mov r0,#0
strh r0,[r6,#6]
add r5,r5,#1
strb r5,[r4]
m22_obj_done:
pop {{r0-r8,pc}}
.ltorg
"""
