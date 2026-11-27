"""ARM scene callbacks for the D-Ark waiting screen."""
def assembly(scenery, fighters, headers, *, linked=False):
    open_link = 'bl dark_open_link' if linked else ''
    close_link = 'bl dark_close_link' if linked else ''
    update_link = """
    bl dark_link_frame
    ldrb r0,[r10,#0x40]
    cmp r0,#0
    bne dark_wait
""" if linked else ''
    wait_is_active = 'ldrb r0,[r10,#0x40]\ncmp r0,#0\nbne dark_input' if linked else ''
    skip_idle = """
    ldrb r0,[r10,#0x40]
    cmp r0,#0
    bne dark_end
""" if linked else ''
    return f"""
dark_init:
    mov r2,#1
    bx lr

dark_create:
    push {{r0-r12,lr}}
    adr r0,dark_frame
    push {{r0}}
    mov r0,#0
    push {{r0}}
    mov r0,#0x1000
    push {{r0}}
    mov r11,#0
    bl 0x08011ac4
    add sp,sp,#12
    add r10,r0,#0x18
    mov r0,#0
    str r0,[r10]
    str r0,[r10,#4]
    str r0,[r10,#8]
    str r0,[r10,#12]
    str r0,[r10,#16]
    mov r6,#0x04000000
    @ The native VBlank compositor owns the screen masks, scroll latches and
    @ background priorities. Save its live configuration before our scene starts.
    ldrh r0,[r6]
    strh r0,[r10,#0x20]
    ldrh r0,[r6,#4]
    strh r0,[r10,#0x22]
    ldr r0,[r6,#8]
    str r0,[r10,#0x24]
    ldr r0,[r6,#12]
    str r0,[r10,#0x28]
    ldr r0,[r6,#0x48]
    str r0,[r10,#0x2c]
    ldrh r0,[r6,#0x50]
    strh r0,[r10,#0x30]
    ldrh r0,[r6,#0x54]
    strh r0,[r10,#0x32]
    ldr r1,=0x030012b6
    ldrh r0,[r1]
    strh r0,[r10,#0x34]
    ldr r1,=0x030012b8
    ldr r0,[r1]
    str r0,[r10,#0x38]
    add r1,r6,#0x200
    ldrh r0,[r1]
    and r0,r0,#4
    strh r0,[r10,#0x36]
    mov r0,#128
    strh r0,[r6]
    bl dark_no_vcount
    ldr r7,={scenery}
    ldr r0,[r7]
    mov r1,#0x06000000
    ldr r2,[r7,#4]
    bl dark_copy
    ldr r0,[r7,#8]
    ldr r1,=0x0600a000
    mov r2,#2048
    bl dark_copy
    @ The no-device WAIT message starts after 70 source ticks.
    ldr r1,=0x0600a188
    mov r2,#4
    mov r3,#0
dark_hide_wait:
    str r3,[r1]
    str r3,[r1,#4]
    str r3,[r1,#8]
    str r3,[r1,#12]
    add r1,r1,#64
    subs r2,r2,#1
    bne dark_hide_wait
    ldr r0,[r7,#12]
    ldr r1,=0x0600a800
    mov r2,#2048
    bl dark_copy
    ldr r1,=0x0600b000
    mov r2,#512
    mov r3,#0
dark_clear_map:
    str r3,[r1],#4
    subs r2,r2,#1
    bne dark_clear_map
    ldr r0,[r7,#16]
    ldr r1,=0x06009000
    mov r2,#4096
    bl dark_copy
    ldr r0,[r7,#20]
    mov r1,#0x05000000
    mov r2,#32
    bl dark_copy
    ldr r0,[r7,#24]
    ldr r1,=0x05000040
    mov r2,#32
    bl dark_copy

    ldr r8,=0x0300231a
    ldrb r4,[r8]
    cmp r4,#14
    movhi r4,#0
    ldr r7,=0x084a5bc0
    add r7,r7,r4,lsl #3
    ldr r0,[r7,#4]
    ldr r1,=0x06002000
    mov r2,#6144
    bl dark_copy
    push {{r4,r7,r8,r10}}
    bl 0x08633400
    pop {{r4,r7,r8,r10}}
    rsb r0,r0,r0,lsl #4
    add r0,r0,r4
    ldr r1,={headers}
    ldr r0,[r1,r0,lsl #2]
    ldr r1,=0x06002000
    mov r2,#768
    bl dark_copy
    ldr r0,[r7]
    ldr r1,=0x05000020
    mov r2,#16
    ldr r12,=0x3def
dark_dim:
    ldrh r3,[r0],#2
    mov r3,r3,lsr #1
    and r3,r3,r12
    strh r3,[r1],#2
    subs r2,r2,#1
    bne dark_dim

    ldr r7,={fighters}
    ldr r7,[r7,r4,lsl #2]
    str r7,[r10,#20]
    ldr r0,[r7]
    ldr r1,=0x06004000
    mov r2,#0
    mov r3,#8
dark_clear_actor_zero:
    str r2,[r1],#4
    subs r3,r3,#1
    bne dark_clear_actor_zero
    ldr r2,[r7,#4]
    bl dark_copy
    ldrb r3,[r8,#1]
    tst r3,#1
    ldreq r0,[r7,#8]
    ldrne r0,[r7,#12]
    ldr r1,=0x05000060
    mov r2,#32
    bl dark_copy
    {open_link}
    bl dark_registers
    pop {{r0-r12,pc}}

dark_no_vcount:
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

dark_registers:
    mov r0,#0x04000000
    ldr r1,=0x1502
    strh r1,[r0,#8]
    ldr r1,=0x1403
    strh r1,[r0,#10]
    ldr r1,=0x1604
    strh r1,[r0,#12]
    ldr r1,=0x5202
    strh r1,[r0,#14]
    mov r1,#0
    str r1,[r0,#16]
    str r1,[r0,#20]
    str r1,[r0,#24]
    str r1,[r0,#28]
    strh r1,[r0,#0x50]
    strh r1,[r0,#0x54]
    ldr r1,=0x08e8
    strh r1,[r0,#0x40]
    ldr r1,=0x0898
    strh r1,[r0,#0x44]
    mov r1,#15
    strh r1,[r0,#0x48]
    mov r1,#0
    strh r1,[r0,#0x4a]
    ldr r2,=0x030012b6
    mov r1,#3
    strh r1,[r2]
    ldr r1,=0x080c0808
    ldr r2,=0x030012b8
    str r1,[r2]
    mov r1,#4
    strh r1,[r0,#16]
    ldr r1,=0x2f00
    strh r1,[r0]
    bx lr
.ltorg

dark_copy:
    ldr r3,[r0],#4
    str r3,[r1],#4
    subs r2,r2,#4
    bne dark_copy
    bx lr

dark_frame:
    push {{r0-r12,lr}}
    ldr r10,=0x0300133c
    ldr r10,[r10]
    add r10,r10,#0x18
    ldr r4,[r10]
    add r4,r4,#1
    str r4,[r10]
    ldr r7,[r10,#20]
    mov r6,#0x04000000
    bl dark_no_vcount
    ldr r5,[r10,#24]
    cmp r4,#1
    moveq r5,#0
    add r5,r5,#1
    cmp r5,#112
    movhs r5,#0
    str r5,[r10,#24]
    sub r5,r5,#8
    strh r5,[r6,#28]
    cmp r4,#56
    bne dark_input
    {wait_is_active}
    ldr r0,={scenery}
    ldr r0,[r0,#8]
    add r0,r0,#0x180
    add r0,r0,#8
    ldr r1,=0x0600a188
    mov r2,#4
dark_show_wait:
    ldmia r0,{{r5,r7,r8,r9}}
    stmia r1,{{r5,r7,r8,r9}}
    add r0,r0,#64
    add r1,r1,#64
    subs r2,r2,#1
    bne dark_show_wait
dark_input:
    {update_link}
    cmp r4,#56
    ldr r5,=0x03001306
    ldrh r5,[r5]
    tsths r5,#0x80
    beq dark_wait
    cmp r4,#56
    blo dark_wait
    ldr r0,[r10,#16]
    cmp r0,#0
    bne dark_wait
    mov r0,#24
    str r0,[r10,#16]
    mov r8,#0x20
    mov r9,#0
    mov r11,#0
    mov r10,#1
    bl 0x080d15c0
    ldr r10,=0x0300133c
    ldr r10,[r10]
    add r10,r10,#0x18
dark_wait:
    ldr r0,[r10,#16]
    cmp r0,#0
    beq dark_animate
    subs r0,r0,#1
    str r0,[r10,#16]
    bne dark_animate
    {close_link}
    mov r6,#0x04000000
    ldrh r0,[r10,#0x20]
    strh r0,[r6]
    ldrh r0,[r10,#0x22]
    strh r0,[r6,#4]
    ldr r0,[r10,#0x24]
    str r0,[r6,#8]
    ldr r0,[r10,#0x28]
    str r0,[r6,#12]
    ldr r0,[r10,#0x2c]
    str r0,[r6,#0x48]
    ldrh r0,[r10,#0x30]
    strh r0,[r6,#0x50]
    ldrh r0,[r10,#0x32]
    strh r0,[r6,#0x54]
    ldr r1,=0x030012b6
    ldrh r0,[r10,#0x34]
    strh r0,[r1]
    ldr r1,=0x030012b8
    ldr r0,[r10,#0x38]
    str r0,[r1]
    mov r1,#0
    str r1,[r6,#24]
    str r1,[r6,#28]
    add r1,r6,#0x200
    ldrh r0,[r1]
    bic r0,r0,#4
    ldrh r2,[r10,#0x36]
    orr r0,r0,r2
    strh r0,[r1]
    ldr r0,=0x03002310
    mov r1,#1
    strh r1,[r0,#4]
    mov r1,#0
    strh r1,[r0,#6]
    strh r1,[r0,#8]
    ldr r1,=0x0300133c
    ldr r1,[r1]
    push {{r1}}
    mov r1,#0
    push {{r1}}
    mov r11,#0
    bl 0x08011be4
    add sp,sp,#8
    pop {{r0-r12,pc}}

dark_animate:
    {skip_idle}
    ldr r7,[r10,#20]
    ldr r4,[r10]
    mov r6,#0x04000000
    add r1,r4,r4,lsr #2
    add r0,r1,#1
    mul r2,r0,r1
    mov r2,r2,lsr #4
    rsbs r0,r2,#120
    movlo r0,#0
    strh r0,[r6,#26]
    cmp r4,#35
    cmpne r4,#42
    moveq r0,#0
    streq r0,[r10,#4]
    streq r0,[r10,#8]
    cmp r4,#35
    addlo r8,r7,#16
    addhs r8,r7,#24
    cmp r4,#42
    addhs r8,r7,#32
    ldmia r8,{{r8,r9}}
    ldr r0,[r10,#8]
    cmp r0,#0
    subne r0,r0,#1
    strne r0,[r10,#8]
    bne dark_end
    ldr r0,[r10,#4]
    add r1,r8,r0,lsl #3
    ldmia r1,{{r1,r2}}
    sub r2,r2,#1
    str r2,[r10,#8]
    add r0,r0,#1
    cmp r0,r9
    movhs r0,#0
    str r0,[r10,#4]
    ldr r2,=0x0600b208
    mov r3,#10
dark_rows:
    ldmia r1!,{{r4,r5,r6,r7}}
    stmia r2,{{r4,r5,r6,r7}}
    add r2,r2,#64
    subs r3,r3,#1
    bne dark_rows
dark_end:
    pop {{r0-r12,pc}}
.ltorg
"""
