"""ARM callbacks for the native Options task's seventh row and assist submenu."""

EXPORTS = ("assist_input", "assist_tick", "assist_draw_guard")


def assembly(assets, storage):
    resources = "\n".join(f".word {a['p0']}, {a['p1']}" for a in assets)
    return f"""
assist_input:
    push {{r1-r12,lr}}
    mov r6,r0
    bl 0x08633540
    cmp r0,#0
    beq assist_passthrough
    mov r4,r0
    ldr r5,assist_options
    ldrb r0,[r4,#248]
    cmp r0,#0
    bne assist_sub_input
    ldrh r0,[r4,#4]
    cmp r0,#0
    bne assist_passthrough
    ldrh r0,[r5,#6]
    cmp r0,#5
    bne assist_other_row
    ldrb r1,[r4,#249]
    cmp r1,#0
    bne assist_return_row
    tst r6,#0x40
    beq assist_more_down
    bl 0x{storage['assist_read']:08x}
    strh r0,[r4,#250]
    mov r0,#1
    strb r0,[r4,#248]
    mov r0,#0
    strb r0,[r4,#252]
    strb r0,[r4,#253]
    strh r0,[r4,#254]
    b assist_consume
assist_more_down:
    tst r6,#4
    beq assist_passthrough
    mov r0,#1
    strb r0,[r4,#249]
    b assist_consume
assist_return_row:
    tst r6,#1
    movne r0,#0
    strbne r0,[r4,#249]
    bne assist_consume
    tst r6,#4
    movne r0,#0
    strbne r0,[r4,#249]
    b assist_passthrough
assist_other_row:
    cmp r0,#0
    bne assist_passthrough
    tst r6,#1
    movne r0,#1
    strbne r0,[r4,#249]
assist_passthrough:
    mov r0,r6
    pop {{r1-r12,lr}}
    b 0x08633800
assist_sub_input:
    ldr r1,assist_keyinput
    ldrh r0,[r1]
    mvn r0,r0
    and r0,r0,#0x300
    ldrh r1,[r4,#254]
    strh r0,[r4,#254]
    bic r7,r0,r1
    tst r6,#0x80
    bne assist_close
    ldrb r8,[r4,#252]
    tst r6,#1
    subne r8,r8,#1
    andne r8,r8,#3
    strbne r8,[r4,#252]
    bne assist_consume
    tst r6,#4
    addne r8,r8,#1
    andne r8,r8,#3
    strbne r8,[r4,#252]
    bne assist_consume
    ldrh r9,[r4,#250]
    cmp r8,#0
    bne assist_not_spirit
    bic r2,r9,#0x400
    tst r7,#0x100
    addne r2,r2,#100
    bne assist_limit
    tst r7,#0x200
    subne r2,r2,#100
    bne assist_limit
    tst r6,#2
    addne r2,r2,#1
    tst r6,#8
    subne r2,r2,#1
assist_limit:
    cmp r2,#0
    movlt r2,#0
    cmp r2,#1000
    movgt r2,#1000
    and r9,r9,#0x400
    orr r9,r9,r2
    b assist_stage
assist_not_spirit:
    cmp r8,#1
    bne assist_action
    tst r6,#0x40
    eorne r9,r9,#0x400
    tst r6,#8
    bicne r9,r9,#0x400
    tst r6,#2
    orrne r9,r9,#0x400
assist_stage:
    strh r9,[r4,#250]
    b assist_consume
assist_action:
    tst r6,#0x40
    beq assist_consume
    cmp r8,#3
    beq assist_close
    mov r0,r9
    bl 0x{storage['assist_write']:08x}
    cmp r0,#0
    movne r0,#1
    strbne r0,[r4,#253]
    bne assist_consume
assist_close:
    mov r0,#0
    strb r0,[r4,#248]
    strb r0,[r4,#253]
assist_consume:
    mov r0,#0
    strh r0,[r5,#2]
    pop {{r1-r12,lr}}
    tst r0,#0x80
    bx lr
assist_options: .word 0x03004738
assist_keyinput: .word 0x04000130

assist_draw_guard:
    push {{r0-r7,lr}}
    ldr r6,[sp,#40]
    bl 0x08633540
    cmp r0,#0
    beq assist_draw_native
    ldrb r1,[r0,#248]
    cmp r1,#0
    bne assist_skip
    ldrh r7,[r6,#2]
    ldrb r1,[r0,#249]
    cmp r1,#0
    bne assist_window
    cmp r7,#126
    beq assist_skip
assist_draw_native:
    pop {{r0-r7,lr}}
    b 0x08012c28
assist_window:
    cmp r7,#36
    beq assist_skip
    cmp r7,#126
    beq assist_draw_native
    cmp r7,#36
    blo assist_draw_native
    cmp r7,#126
    bhi assist_draw_native
    sub r1,r7,#18
    strh r1,[r6,#2]
    ldr r0,[sp,#36]
    push {{r6,r7}}
    push {{r0,r6}}
    bl 0x08012c28
    add sp,sp,#8
    pop {{r6,r7}}
    strh r7,[r6,#2]
assist_skip:
    pop {{r0-r7,lr}}
    bx lr

assist_tick:
    push {{r0-r12,lr}}
    bl 0x0801201c
    mov r4,r0
    ldr r5,assist_options
    ldrh r1,[r5]
    tst r1,#0x8000
    bne assist_native_tick
    ldrh r1,[r5,#2]
    tst r1,#0x80
    bne assist_native_tick
    ldrb r1,[r4,#248]
    cmp r1,#0
    bne assist_render_page
    ldrb r1,[r4,#249]
    cmp r1,#0
    moveq r3,#126
    movne r3,#108
    mov r0,#0
    ldrh r2,[r5,#6]
    cmpeq r2,#5
    moveq r0,#1
    mov r1,#0
    mov r2,#40
    bl assist_text
assist_native_tick:
    pop {{r0-r12,lr}}
    b 0x08633e00
assist_render_page:
    ldrb r8,[r4,#252]
    ldrh r9,[r4,#250]
    mov r0,#1
    mov r1,#1
    mov r2,#40
    mov r3,#36
    bl assist_text
    mov r7,#0
assist_render_rows:
    cmp r8,r7
    moveq r0,#1
    movne r0,#0
    add r1,r7,#2
    mov r2,#42
    mov r3,#54
    add r3,r3,r7,lsl #4
    add r3,r3,r7,lsl #1
    bl assist_text
    cmp r8,r7
    bne assist_after_cursor
    mov r0,#1
    mov r1,#20
    mov r2,#32
    bl assist_text
assist_after_cursor:
    add r7,r7,#1
    cmp r7,#4
    blo assist_render_rows
    mov r0,#0
    mov r1,#19
    ldrb r2,[r4,#253]
    cmp r2,#0
    movne r1,#8
    mov r2,#42
    mov r3,#126
    bl assist_text
    cmp r8,#1
    moveq r0,#1
    movne r0,#0
    tst r9,#0x400
    moveq r1,#6
    movne r1,#7
    mov r2,#146
    mov r3,#72
    bl assist_text
    bic r7,r9,#0x400
    cmp r8,#0
    moveq r0,#1
    movne r0,#0
    mov r2,#146
    mov r3,#54
    cmp r7,#0
    bne assist_digits
    mov r1,#6
    bl assist_text
    b assist_page_done
assist_digits:
    sub r7,r7,#1
    mov r5,#0
assist_hundreds:
    cmp r7,#100
    subhs r7,r7,#100
    addhs r5,r5,#1
    bhs assist_hundreds
    mov r6,#0
assist_tens:
    cmp r7,#10
    subhs r7,r7,#10
    addhs r6,r6,#1
    bhs assist_tens
    cmp r5,#0
    beq assist_skip_hundreds
    add r1,r5,#9
    bl assist_text
    add r2,r2,#7
assist_skip_hundreds:
    orrs r1,r5,r6
    beq assist_units
    add r1,r6,#9
    bl assist_text
    add r2,r2,#7
assist_units:
    add r1,r7,#9
    bl assist_text
assist_page_done:
    pop {{r0-r12,lr}}
    bx lr

assist_text:
    push {{r0-r12,lr}}
    sub sp,sp,#0x50
    mov r7,sp
    mov r6,r4
    mov r4,#0
    mov r5,#0
assist_blank_object:
    str r4,[r7,r5]
    add r5,r5,#4
    cmp r5,#0x50
    blo assist_blank_object
    sub sp,sp,#0x3c
    mov r5,#0
assist_blank_args:
    str r4,[sp,r5]
    add r5,r5,#4
    cmp r5,#0x3c
    blo assist_blank_args
    str r7,[sp,#0x38]
    ldrh r6,[r6,#2]
    adr r5,assist_resources
    add r5,r5,r6,lsl #3
    ldr r4,[r5]
    str r4,[sp,#0x24]
    ldr r4,[r5,#4]
    str r4,[sp,#0x30]
    ldr r4,assist_p2
    str r4,[sp,#0x18]
    mov r4,#0x4000
    str r4,[sp,#0xc]
    mov r4,#0x1800
    str r4,[sp,#8]
    mov r4,#1
    str r4,[sp,#4]
    bl 0x080127e4
    add sp,sp,#0x3c
    mov r7,sp
    add r6,sp,#0x50
    ldr r1,[r6,#8]
    strh r1,[r7]
    ldr r1,[r6,#12]
    strh r1,[r7,#2]
    ldrh r1,[r7,#8]
    orr r1,r1,#0x2000
    strh r1,[r7,#8]
    mov r0,r7
    mov r1,#0
    ldr r2,[r6,#4]
    bl 0x08633d00
    ldr r1,[r6]
    strh r1,[r7,#0x10]
    push {{r7}}
    mov r1,#0
    push {{r1}}
    bl 0x08012c28
    add sp,sp,#8
    add sp,sp,#0x50
    pop {{r0-r12,lr}}
    bx lr
assist_p2: .word 0x080a05b8
assist_resources:
{resources}
"""
