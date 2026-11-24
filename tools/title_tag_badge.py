"""Paint the 1.5 title's win count and highest-rank badge during the Start prompt."""
def assembly(reader, tiles, palettes, font, font_palette):
    return f"""
@ Executed from the native title constructor with R4 pointing to the new task payload.
title_badge_init:
    strh r0,[r4]
    push {{r0-r12,lr}}
    sub sp,sp,#48
    mov r0,#0
    str r0,[r4,#0x28]
    mov r0,sp
    bl {reader:#x}
    cmp r0,#2
    cmpne r0,#0
    bne title_badge_init_done
    mov r0,#1
    strb r0,[r4,#0x28]
    mov r3,#10
    add r1,sp,#18
title_badge_highest:
    add r2,r1,r3,lsl #1
    ldrh r2,[r2]
    cmp r2,#0
    bne title_badge_rank
    subs r3,r3,#1
    bpl title_badge_highest
title_badge_rank:
    strb r3,[r4,#0x29]
    ldrh r0,[sp,#40]
    ldr r1,=999
    cmp r0,r1
    movhi r0,r1
    mov r1,#0x30
title_badge_hundreds:
    cmp r0,#100
    subhs r0,r0,#100
    addhs r1,r1,#1
    bhs title_badge_hundreds
    strb r1,[r4,#0x2c]
    mov r1,#0x30
title_badge_tens:
    cmp r0,#10
    subhs r0,r0,#10
    addhs r1,r1,#1
    bhs title_badge_tens
    strb r1,[r4,#0x2d]
    add r0,r0,#0x30
    strb r0,[r4,#0x2e]
title_badge_init_done:
    add sp,sp,#48
    pop {{r0-r12,lr}}
    b 0x08090c34
.ltorg

@ Source's separate title text task is retired before slide-in or attract mode.
title_badge_draw:
    push {{r0-r12,lr}}
    mov r4,r5
    ldrb r0,[r4,#0x28]
    cmp r0,#0
    beq title_badge_draw_done
    ldrb r0,[r4,#0x2a]
    cmp r0,#0
    bne title_badge_colors
    ldr r0,=0x050003a0
    add r1,r4,#0x30
    mov r2,#16
    bl title_badge_copy
    mov r0,#1
    strb r0,[r4,#0x2a]
title_badge_colors:
    ldr r0,={font_palette}
    ldr r1,=0x050003c0
    mov r2,#8
    bl title_badge_copy
    ldrb r5,[r4,#0x29]
    cmp r5,#10
    bhi title_badge_text
    adr r0,title_badge_palettes
    ldr r0,[r0,r5,lsl #2]
    ldr r1,=0x050003a0
    mov r2,#8
    bl title_badge_copy
    adr r0,title_badge_tiles
    ldr r6,[r0,r5,lsl #2]
    mov r8,#2
title_badge_row:
    mov r7,#166
title_badge_column:
    mov r0,r6
    mov r1,r7
    mov r2,r8
    mov r3,#0xd000
    bl title_badge_emit
    add r6,r6,#32
    add r7,r7,#8
    cmp r7,#222
    blo title_badge_column
    add r8,r8,#8
    cmp r8,#34
    blo title_badge_row
title_badge_text:
    mov r5,#0
title_badge_letter:
    cmp r5,#3
    addlo r0,r4,#0x2c
    adr r1,title_badge_label
    subhs r0,r1,#3
    ldrb r0,[r0,r5]
    sub r0,r0,#32
    ldr r6,={font}
    add r0,r6,r0,lsl #5
    mov r1,r5,lsl #3
    add r1,r1,#2
    cmp r5,#3
    addhs r1,r1,#8
    mov r2,#2
    mov r3,#0xe000
    bl title_badge_emit
    add r5,r5,#1
    cmp r5,#9
    blo title_badge_letter
title_badge_draw_done:
    pop {{r0-r12,lr}}
    ldr r8,=0x03002c0e
    b 0x08090db8
.ltorg

title_badge_exit:
    push {{r0-r12,lr}}
    ldrb r0,[r5,#0x2a]
    cmp r0,#0
    beq title_badge_exit_done
    add r0,r5,#0x30
    ldr r1,=0x050003a0
    mov r2,#16
    bl title_badge_copy
    mov r0,#0
    strb r0,[r5,#0x2a]
title_badge_exit_done:
    pop {{r0-r12,lr}}
    b 0x08090df8
.ltorg

@ One source 8x8 cell per native tile upload and 8-byte OAM entry. +8 is the GBA viewport border.
title_badge_emit:
    push {{r4-r8,lr}}
    ldr r4,=0x030012ca
    ldrb r5,[r4]
    cmp r5,#128
    bhs title_badge_emit_done
    mov r6,#0x02000000
    add r6,r6,r5,lsl #5
    ldmia r0!,{{r7,r8}}
    stmia r6!,{{r7,r8}}
    ldmia r0!,{{r7,r8}}
    stmia r6!,{{r7,r8}}
    ldmia r0!,{{r7,r8}}
    stmia r6!,{{r7,r8}}
    ldmia r0!,{{r7,r8}}
    stmia r6!,{{r7,r8}}
    ldr r6,=0x03001428
    add r6,r6,r5,lsl #3
    add r2,r2,#8
    strh r2,[r6]
    add r1,r1,#8
    strh r1,[r6,#2]
    orr r3,r3,r5
    orr r3,r3,#0x400
    strh r3,[r6,#4]
    mov r0,#0
    strh r0,[r6,#6]
    add r5,r5,#1
    strb r5,[r4]
title_badge_emit_done:
    pop {{r4-r8,pc}}
title_badge_copy:
    ldr r3,[r0],#4
    str r3,[r1],#4
    subs r2,r2,#1
    bne title_badge_copy
    bx lr
.ltorg
title_badge_label: .ascii "WIN[S]"
.align 2
title_badge_tiles: .word {','.join(map(str,tiles))}
title_badge_palettes: .word {','.join(map(str,palettes))}
"""
