"""Source mode24 card controller and result latch in the completed native link slot."""


def assembly(imports, sites, writer):
    s=imports
    return f"""
@ The native command 82 sends one 16-byte descriptor. Its final local result
@ occupies +10 only after the transfer completed. No native command reads
@ those bytes before the mode8 dispatch and fresh mode24 constructor.
m24_accept_init:
    mrs r11,cpsr
    ldr r1,=0x03002335
    ldrb r2,[r1]
    tst r2,#1
    ldreq r1,=0x03002168
    mvneq r2,#0
    strheq r2,[r1,#10]
    b 0x{sites['accept_resume']:08x}
m24_write_result:
    bl 0x{writer:08x}
    cmp r0,#0
    bne m24_write_done
    ldr r1,=0x03002168
    cmp r8,r9
    orrhi r2,r7,#0x8000
    ldrhls r2,[r1,#6]
    strh r2,[r1,#10]
m24_write_done:
    b 0x{sites['write_resume']:08x}
m24_dispatch:
    push {{r1-r2}}
    mrs r2,cpsr
    ldrb r1,[r5,#0x25]
    tst r1,#1
    moveq r0,#24
    movne r0,#4
    msr cpsr_f,r2
    pop {{r1-r2}}
    b 0x08015b28
.ltorg

m24_init:
    push {{r1,r3-r12,lr}}
    ldr r0,=0x03002168
    ldrh r4,[r0,#10]
    ldrh r2,[r0,#8]
    ldr r3,=0xd675
    cmp r2,r3
    mvnne r4,#0
    bic r1,r4,#0x8000
    cmp r1,#10
    bhi m24_empty
    ldr r0,=0xf100
    ldr r1,=m24_render
    bl m24_spawn
    mov r7,r0
    strh r4,[r7,#0x18]
    mov r0,#0x04000000
    ldr r2,=0x030012b6
    ldrh r1,[r2]
    strh r1,[r7,#0x38]
    ldr r2,=0x030012b8
    ldr r1,[r2]
    str r1,[r7,#0x3c]
    ldrh r1,[r0,#0x54]
    strh r1,[r7,#0x40]
    ldrh r1,[r0,#0x50]
    strh r1,[r7,#0x3a]
    mov r1,#0
    strh r1,[r0,#0x50]
    strh r1,[r0,#0x54]
    bl 0x{s['m11_irq_off']:08x}
    ldr r2,=0x030012e0
    ldr r1,[r2]
    str r1,[r7,#0x24]
    ldr r1,=0x08f7a7d8
    str r1,[r2]
    bl 0x{s['m11_graphics_clear']:08x}
    mov r0,r4
    bl m24_load_card
    mov r0,r7
    b m24_init_done
m24_empty:
    mov r0,#0
m24_init_done:
    mov r2,#1
    pop {{r1,r3-r12,pc}}

m24_create:
    push {{r0-r12,lr}}
    cmp r0,#0
    beq m24_create_empty
    mov r4,r0
    mov r0,#0x1000
    ldr r1,=m24_controller
    bl m24_spawn
    str r4,[r0,#0x114]
    pop {{r0-r12,pc}}
m24_create_empty:
    bl m24_request_exit
    pop {{r0-r12,pc}}

m24_load_card:
    push {{r4-r6,lr}}
    mov r4,r0
    bic r1,r4,#0x8000
    ldr r2,=0x{s['m11_card_asset_table']:08x}
    ldr r0,[r2,r1,lsl #2]
    bl 0x{s['m11_transfers']:08x}
    tst r4,#0x8000
    ldreq r0,=0x{s['digitpal']:08x}
    ldrne r0,=0x{s['getpal']:08x}
    ldr r1,=0x05000240
    mov r2,#8
m24_obj_palette:
    ldr r3,[r0],#4
    str r3,[r1],#4
    subs r2,r2,#1
    bne m24_obj_palette
    mov r0,#0x20
    ldr r1,=0x030012ba
    strb r0,[r1]
    sub r0,r0,#8
    mov r1,#0x04000000
    strh r0,[r1,#0x10]
    mov r0,#0x7b
    mov r1,#1
    bl 0x{s['m11_tag_audio']:08x}
    pop {{r4-r6,pc}}
.ltorg

m24_spawn:
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
m24_zero:
    str r2,[r1],#4
    subs r3,r3,#1
    bne m24_zero
    pop {{r4-r11,pc}}
m24_release:
    push {{r4-r11,lr}}
    push {{r0}}
    mov r1,#0
    push {{r1}}
    mov r11,#0
    bl 0x08011be4
    add sp,sp,#8
    pop {{r4-r11,pc}}

m24_render:
    push {{r0-r12,lr}}
    mov r11,#0
    bl 0x080d1500
    bl 0x{s['m11_irq_off']:08x}
    mov r0,#16
    bl 0x08000c10
    bl 0x08000d18
    pop {{r0-r12,pc}}
m24_request_exit:
    ldr r1,=0x03002310
    mov r0,#1
    strh r0,[r1,#4]
    mov r0,#0
    strh r0,[r1,#6]
    strh r0,[r1,#8]
    bx lr

m24_controller:
    push {{r0-r12,lr}}
    ldr r0,=0x0300133c
    ldr r10,[r0]
    ldr r9,[r10,#0x114]
    add r4,r9,#0x18
    ldrh r6,[r4]
    ldrh r5,[r4,#2]
    add r5,r5,#1
    strh r5,[r4,#2]
    bic r7,r6,#0x8000
    cmp r7,#10
    moveq r8,#0xb8
    movne r8,#0xac
    mov r0,r5,lsl #2
    add r0,r0,#0x20
    cmp r0,r8
    movhi r0,r8
    ldr r1,=0x030012ba
    strb r0,[r1]
    sub r0,r0,#8
    mov r1,#0x04000000
    strh r0,[r1,#0x10]
    ldrh r0,[r4,#4]
    cmp r0,#2
    beq m24_editor
    cmp r7,#10
    moveq r0,#114
    movne r0,#112
    cmp r5,r0
    blo m24_frame_end
    bne m24_sprite
    tst r6,#0x8000
    moveq r0,#0x7d
    movne r0,#0x7c
    cmp r0,#0x7c
    cmpeq r7,#10
    moveq r0,#0x7e
    mov r1,#4
    bl 0x{s['m11_tag_audio']:08x}
m24_sprite:
    tst r6,#0x8000
    ldreq r0,=0x{s['digits_frame15']:08x}
    ldreq r12,=0x{s['digits']:08x}
    ldrne r0,=0x{s['get_frame0']:08x}
    ldrne r12,=0x{s['get']:08x}
    mov r1,#112
    mov r2,#90
    mov r3,#0x2000
    bl 0x{s['m11_layout']:08x}
    ldr r0,=399
    cmp r5,r0
    blo m24_frame_end
    cmp r7,#10
    beq m24_start_name
    sub sp,sp,#44
    mov r0,sp
    bl 0x{s['reader']:08x}
    cmp r0,#0
    ldrheq r0,[sp,#38]
    movne r0,#0
    add sp,sp,#44
    cmp r0,#0
    beq m24_exit
    mov r6,#10
    orr r6,r6,#0x8000
    strh r6,[r4]
    mov r0,#0
    strh r0,[r4,#2]
    bl 0x{s['m11_graphics_clear']:08x}
    mov r0,r6
    bl m24_load_card
    b m24_frame_end

m24_start_name:
    mov r0,#2
    strh r0,[r4,#4]
    bl 0x{s['m11_graphics_clear']:08x}
    ldr r0,=0x{s['m11_name_assets']:08x}
    bl 0x{s['m11_transfers']:08x}
    mov r0,r6
    bl m24_load_card
    add r0,r4,#16
    bl 0x{s['tag_name_init']:08x}
m24_editor:
    add r0,r4,#16
    ldr r1,=0x0300130a
    ldrh r1,[r1]
    bl 0x{s['tag_name_step']:08x}
    cmp r0,#2
    bne m24_draw_name
    add r0,r4,#16
    bl 0x{s['tag_name_save']:08x}
    cmp r0,#0
    beq m24_exit
    mov r0,#0
    strb r0,[r4,#23]
    ldrb r1,[r4,#20]
    add r0,r4,#16
    mov r2,#0x28
    strb r2,[r0,r1]
m24_draw_name:
    add r0,r4,#16
    mov r1,#100
    mov r2,#46
    bl 0x{s['m11_name_text']:08x}
    ldrb r0,[r4,#23]
    cmp r0,#0
    bne m24_frame_end
    ldrb r0,[r4,#21]
    tst r0,#16
    bne m24_frame_end
    ldr r0,=0x{s['m11_underscore']:08x}
    ldrb r1,[r4,#20]
    mov r1,r1,lsl #3
    add r1,r1,#100
    mov r2,#48
    bl 0x{s['m11_name_text']:08x}
m24_frame_end:
    pop {{r0-r12,pc}}
m24_exit:
    bl 0x{s['m11_irq_off']:08x}
    ldr r2,=0x030012e0
    ldr r1,[r4,#12]
    str r1,[r2]
    mov r0,#0x04000000
    ldrh r1,[r9,#0x40]
    strh r1,[r0,#0x54]
    ldr r2,=0x030012b6
    ldrh r1,[r9,#0x38]
    strh r1,[r2]
    ldrh r1,[r9,#0x3a]
    strh r1,[r0,#0x50]
    ldr r2,=0x030012b8
    ldr r1,[r9,#0x3c]
    str r1,[r2]
    bl m24_request_exit
    mov r0,r10
    bl m24_release
    mov r0,r9
    bl m24_release
    pop {{r0-r12,pc}}
.ltorg
"""
