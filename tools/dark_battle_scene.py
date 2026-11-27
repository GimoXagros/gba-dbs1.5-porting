"""Connected D-Ark scene. Battle rules and turn order follow 7B62:07BB..0C4A."""


def assembly(actors, grid, front, shots, colors, categories):
    return f"""
dark_battle_begin:
    ldr r0,={grid}
    ldr r1,=0x0600a000
    mov r2,#2048
    bl dark_copy
    ldr r0,={front}
    ldr r1,=0x0600a800
    mov r2,#2048
    bl dark_copy
    ldr r0,={shots}
    ldr r1,=0x06003000
    mov r2,#768
    bl dark_copy
    ldr r0,={colors}
    ldr r1,=0x05000080
    mov r2,#32
    bl dark_copy
    ldr r1,=0x0600b000
    mov r2,#512
    mov r0,#0
dark_battle_clear:
    str r0,[r1],#4
    subs r2,r2,#1
    bne dark_battle_clear
    ldr r1,=0x0300231a
    ldrb r0,[r1]
    cmp r0,#14
    movhi r0,#0
    ldr r2,={categories}
    ldrb r2,[r2,r0]
    add r2,r2,#0x6c
    strb r2,[r10,#0x62]
    ldr r1,={actors}
    ldr r1,[r1,r0,lsl #2]
    str r1,[r10,#0x68]
    mov r1,#255
    strb r1,[r10,#0x63]
    mov r0,#1
    strb r0,[r10,#0x40]
    mov r0,#0
    str r0,[r10,#0x44]

dark_battle_frame:
    ldr r5,[r10,#0x44]
    ldrb r4,[r10,#0x40]
    add r0,r5,#1
    str r0,[r10,#0x44]
    mov r7,#0x04000000
    mov r1,#0
    strh r1,[r7,#26]
    cmp r4,#1
    bne dark_turn
    rsbs r1,r5,#45
    movlo r1,#0
    add r1,r1,r1,lsr #2
    strh r1,[r7,#24]
    cmp r5,#45
    movlo r0,#1
    movhs r0,#0
    cmp r5,#239
    blo dark_display
    ldrb r0,[r10,#0x62]
    bl dark_music
    mov r4,#2
    b dark_new_phase
dark_turn:
    cmp r4,#6
    beq dark_result_fade
    cmp r4,#4
    bhs dark_result
    bl dark_draw_shots
    cmp r4,#2
    bne dark_retaliation
    mov r0,#2
    cmp r5,#26
    movhs r0,#3
    cmp r5,#72
    movhs r0,#0
    cmp r5,#131
    blo dark_display
    ldrb r1,[r10,#0x5a]
    ldrb r2,[r10,#0x5d]
    movs r2,r2,lsr r1
    tst r2,#1
    beq dark_damage_home
    ldrb r2,[r10,#0x5b]
    ldrb r3,[r10,#0x5e]
    add r6,r10,#0x61
    b dark_damage
dark_damage_home:
    ldrb r2,[r10,#0x5c]
    ldrb r3,[r10,#0x5f]
    add r6,r10,#0x60
dark_damage:
    mov r2,r2,lsr r1
    and r2,r2,#1
    add r3,r3,r2
    ldrb r2,[r6]
    sub r2,r2,r3
    strb r2,[r6]
    mov r4,#3
    b dark_new_phase
dark_retaliation:
    mov r0,#0
    cmp r5,#52
    blo dark_reaction_ready
    cmp r5,#94
    bhs dark_reaction_ready
    ldrb r1,[r10,#0x5a]
    ldrb r2,[r10,#0x5d]
    mov r2,r2,lsr r1
    tst r2,#1
    moveq r0,#5
    movne r0,#4
dark_reaction_ready:
    ldrsb r1,[r10,#0x60]
    cmp r1,#0
    movle r0,#6
    cmp r5,#131
    blo dark_display
    cmp r1,#0
    movle r4,#5
    ble dark_new_phase
    ldrsb r1,[r10,#0x61]
    cmp r1,#0
    movle r4,#4
    ble dark_new_phase
    ldrb r1,[r10,#0x5a]
    add r1,r1,#1
    cmp r1,#5
    moveq r1,#0
    strb r1,[r10,#0x5a]
    mov r4,#2
dark_new_phase:
    cmp r4,#4
    moveq r0,#4
    bleq dark_music
    cmp r4,#5
    moveq r0,#0x1a
    bleq dark_music
    strb r4,[r10,#0x40]
    mov r0,#0
    str r0,[r10,#0x44]
    b dark_link_done
dark_result:
    cmp r4,#5
    moveq r0,#7
    beq dark_loss_timer
    mov r0,#8
    cmp r5,#24
    movhs r0,#9
    cmp r5,#239
    bhs dark_finish
    ldr r1,=0x03001306
    ldrh r1,[r1]
    tst r1,#0xc0
    bne dark_finish
    b dark_display
dark_loss_timer:
    cmp r5,#48
    blo dark_display
dark_finish:
    mov r4,#6
    b dark_new_phase
dark_result_fade:
    @ 7B62:0D74 fades the palette once per eight source ticks for 128 ticks.
    @ 16 discrete BLDY steps over 102 GBA frames reproduce that cadence.
    mov r0,#0xff
    strh r0,[r7,#0x50]
    add r0,r5,r5,lsr #2
    mov r0,r0,lsr #3
    strh r0,[r7,#0x54]
    cmp r5,#102
    blo dark_link_done
    mov r0,#1
    str r0,[r10,#16]
    b dark_link_done

dark_music:
    @ 8719:00EF selects the generation song. WSC 18 and 70 are the win/loss cues.
    push {{r0-r12,lr}}
    mov r8,r0
    mov r9,#4
    mov r10,#0
    mov r11,#0
    bl 0x080d15c0
    pop {{r0-r12,pc}}

dark_display:
    ldrb r1,[r10,#0x63]
    cmp r1,r0
    beq dark_hold
    strb r0,[r10,#0x63]
    mov r1,#0
    strh r1,[r10,#0x64]
    strh r1,[r10,#0x66]
dark_hold:
    ldrh r1,[r10,#0x66]
    cmp r1,#0
    subne r1,r1,#1
    strhne r1,[r10,#0x66]
    bne dark_link_done
    ldr r1,[r10,#0x68]
    ldr r1,[r1,r0,lsl #2]
    ldrh r2,[r10,#0x64]
    add r3,r1,r2,lsl #3
    ldr r8,[r3,#4]
    ldr r3,[r3,#8]
    sub r3,r3,#1
    strh r3,[r10,#0x66]
    add r2,r2,#1
    ldr r3,[r1]
    cmp r2,r3
    movhs r2,#0
    strh r2,[r10,#0x64]
    ldr r0,[r8]
    ldr r1,=0x06004020
    ldr r2,[r8,#4]
    cmp r2,#0
    blne dark_copy
    ldr r1,[r8,#8]
    ldr r2,=0x0600b212
    mov r3,#10
dark_pose_rows:
    mov r4,#12
dark_pose_cells:
    ldrh r0,[r1],#2
    strh r0,[r2],#2
    subs r4,r4,#1
    bne dark_pose_cells
    add r2,r2,#40
    subs r3,r3,#1
    bne dark_pose_rows
    b dark_link_done

dark_draw_shots:
    @ Clear only the 15 interior columns used by a shot. Keep the right frame.
    push {{r4-r9,lr}}
    ldr r8,=0x0600ab1c
    mov r0,#0
    mov r2,#4
dark_clear_shot_row:
    mov r1,#7
dark_shot_clear:
    str r0,[r8],#4
    subs r1,r1,#1
    bne dark_shot_clear
    strh r0,[r8]
    add r8,r8,#36
    subs r2,r2,#1
    bne dark_clear_shot_row
    ldrb r7,[r10,#0x5a]
    cmp r4,#2
    ldrbeq r6,[r10,#0x5b]
    ldrbne r6,[r10,#0x5c]
    mov r6,r6,lsr r7
    tst r6,#1
    ldr r9,=0x0600ab40
    subne r9,r9,#64
    bl dark_one_shot
    tst r6,#1
    beq dark_shots_done
    @ The source creates two projectiles at the same time, sixteen pixels apart.
    add r9,r9,#128
    bl dark_one_shot
dark_shots_done:
    pop {{r4-r9,pc}}
dark_one_shot:
    cmp r4,#2
    bne dark_incoming
    subs r7,r5,#20
    bxmi lr
    cmp r7,#45
    bxhs lr
    mov r1,r7,lsr #2
    add r1,r1,#14
    b dark_shot_at
dark_incoming:
    cmp r5,#42
    bxhs lr
    add r1,r5,r5,lsl #1
    add r1,r1,r5,lsr #3
    rsb r1,r1,#240
    mov r1,r1,lsr #3
    mov r7,r5
dark_shot_at:
    add r8,r9,r1,lsl #1
    mov r2,r7,lsr #2
    and r2,r2,#3
    cmp r2,#3
    moveq r2,#1
    ldr r3,=0x4180
    add r3,r3,r2,lsl #3
    cmp r4,#2
    addeq r3,r3,#3
    orreq r3,r3,#0x400
    moveq r7,#-1
    movne r7,#1
    mov r2,#4
dark_shot_cell:
    cmp r1,#28
    strhls r3,[r8]
    add r0,r3,#4
    strhls r0,[r8,#64]
    add r1,r1,#1
    add r8,r8,#2
    add r3,r3,r7
    subs r2,r2,#1
    bne dark_shot_cell
    bx lr
.ltorg
"""
