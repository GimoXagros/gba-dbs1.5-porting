"""Native ending controller for the source score, tag card and name entry."""
def assembly(reader):
    return """
@ Enter from the persisted award's saved-register frame. The old native A5 fade
@ owner has an unused 256-byte task payload; its two sibling handles are live.
m11_present:
    mov r4,r1
    str r6,[r4,#36]
    ldr r2,=0x030012b6
    ldrh r3,[r2]
    strh r3,[r4,#48]
    ldr r2,=0x030012b8
    ldr r3,[r2]
    str r3,[r4,#52]
    ldr r2,=0x04000050
    ldrh r3,[r2]
    strh r3,[r4,#88]
    ldrh r3,[r2,#4]
    strh r3,[r4,#90]
    strh r0,[r4,#4]
    mov r0,#0
    str r0,[r4]
    str r0,[r4,#8]
    str r0,[r4,#12]
    str r0,[r4,#16]
    str r0,[r4,#60]
    str r0,[r4,#64]
    str r0,[r4,#68]
    str r0,[r4,#72]
    str r0,[r4,#76]
    str r0,[r4,#80]
    ldr r0,=0x03003040
    ldr r1,[r0]
    ldr r2,[r1]
    str r2,[r4,#24]
    ldr r2,[r1,#0x110]
    str r2,[r4,#56]
    str r4,[r1,#0x110]
    ldr r2,=m11_audio_render
    str r2,[r1]
    ldr r0,=0x03003cf8
    ldr r1,[r0]
    ldr r2,[r1]
    str r2,[r4,#28]
    ldr r2,=m11_dormant
    str r2,[r1]
    ldr r0,=0x030012e0
    ldr r1,[r0]
    str r1,[r4,#32]
    ldr r1,=0x08f7a7d8
    str r1,[r0]
    ldr r0,=m11_controller
    str r0,[r4,#-24]
    bl m11_irq_off
    bl m11_graphics_clear
    ldr r0,=m11_score_assets
    bl m11_transfers
    ldr r0,=0x030012ba
    mov r1,#4
    strb r1,[r0]
    ldr r0,=0x03003d02
    ldrh r0,[r0]
    mov r5,#0
    add r6,r4,#40
    ldr r7,=m11_divisors
m11_decimal_place:
    ldrh r1,[r7],#2
    mov r2,#0
m11_decimal_sub:
    cmp r0,r1
    subhs r0,r0,r1
    addhs r2,r2,#1
    bhs m11_decimal_sub
    add r3,r2,#48
    strb r3,[r6],#1
    add r5,r5,#1
    cmp r5,#4
    blo m11_decimal_place
    mov r0,#0
    strb r0,[r6]
    ldr r6,[r4,#36]
    msr cpsr_f,r6
    pop {r0-r12,lr}
    b 0x080c0ed8
m11_dormant:
    bx lr
m11_divisors: .hword 1000,100,10,1
.ltorg

m11_audio_render:
    push {r0-r12,lr}
    bl 0x080d14fc
    ldr r0,=0x0300133c
    ldr r0,[r0]
    ldr r0,[r0,#0x110]
    cmp r0,#0
    beq m11_audio_done
    ldrh r1,[r0,#2]
    cmp r1,#0
    bne m11_audio_done
    bl m11_irq_off
    ldr r2,=0x030012b8
    ldrb r1,[r2]
    sub r1,r1,#1
    strb r1,[r2]
    and r1,r1,#255
    sub r1,r1,#8
    mov r0,#0x04000000
    strh r1,[r0,#0x14]
    mov r0,#16
    bl 0x08000c10
    bl 0x08000d18
m11_audio_done:
    pop {r0-r12,pc}
m11_irq_off:
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
.ltorg

m11_controller:
    push {r0-r12,lr}
    bl 0x0801201c
    mov r4,r0
    ldrh r5,[r4]
    add r5,r5,#1
    strh r5,[r4]
    ldrh r0,[r4,#2]
    cmp r0,#0
    beq m11_score
    cmp r0,#1
    beq m11_card
    b m11_editor
m11_score:
    ldr r0,=710
    cmp r5,r0
    bhs m11_begin_card
    mov r6,#0
m11_score_reels:
    add r1,r4,r6
    ldrb r0,[r1,#41]
    sub r0,r0,#48
    ldrb r1,[r4,#40]
    cmp r1,#48
    movhi r0,#9
    ldr r1,=318
    cmp r5,r1
    bhs m11_reel_draw
    mov r0,#0
    cmp r5,#92
    blo m11_reel_draw
    sub r0,r5,#92
    rsb r1,r6,#2
    add r0,r0,r1,lsl #2
m11_reel_modulo:
    cmp r0,#12
    subhs r0,r0,#12
    bhs m11_reel_modulo
m11_reel_draw:
    add r0,r0,#2
    ldr r1,=m11_digits_frame_table
    ldr r0,[r1,r0,lsl #2]
    mov r1,r6,lsl #4
    add r1,r1,#92
    mov r2,#32
    mov r3,#0x2000
    ldr r12,=m11_digits_ptr
    ldr r12,[r12]
    bl m11_layout
    add r6,r6,#1
    cmp r6,#3
    blo m11_score_reels
    ldr r0,=350
    cmp r5,r0
    blo m11_score_actor
    ldr r0,=0x0300231f
    ldrb r0,[r0]
    cmp r0,#3
    bhi m11_score_actor
    ldr r1,=m11_level_table
    ldr r0,[r1,r0,lsl #2]
    ldrb r1,[r0],#1
    mov r2,#64
    bl m11_text
    ldr r0,=m11_total_ptr
    ldr r0,[r0]
    mov r1,#56
    mov r2,#80
    bl m11_text
    add r0,r4,#40
    mov r1,#96
    mov r2,#96
    bl m11_text
m11_score_actor:
    mov r0,r5
    mov r1,#0
    cmp r5,#92
    subhs r0,r5,#92
    addhs r0,r0,r0,lsl #1
    addhs r0,r0,#92
    ldr r2,=318
    cmp r5,r2
    subhs r0,r5,r2
    movhs r1,#86
    mov r2,#112
    mov r3,#128
    mov r12,#0
    bl m11_fighter
    mov r0,r5
    ldr r1,=649
    cmp r5,r1
    ldrhs r1,=710
    subhs r0,r1,r5
    bl m11_fade
    b m11_frame_end
m11_begin_card:
    ldrh r6,[r4,#4]
    ldr r0,=0xffff
    cmp r6,r0
    beq m11_native_exit
    bic r6,r6,#0x8000
    cmp r6,#10
    bhi m11_native_exit
m11_set_card:
    mov r0,#1
    strh r0,[r4,#2]
    mov r0,#0
    strh r0,[r4]
    bl m11_irq_off
    bl m11_graphics_clear
    ldr r0,=m11_card_asset_table
    ldr r0,[r0,r6,lsl #2]
    bl m11_transfers
    mov r0,#0x7b
    mov r1,#1
    bl m11_tag_audio
    mov r0,#60
    bl m11_fade
    mov r5,#0
m11_card:
    ldrh r6,[r4,#4]
    bic r7,r6,#0x8000
    cmp r7,#10
    moveq r0,#0xb8
    movne r0,#0xac
    mov r1,r5,lsl #2
    add r1,r1,#32
    cmp r1,r0
    movhi r1,r0
    ldr r2,=0x030012ba
    strb r1,[r2]
    sub r1,r1,#8
    mov r2,#0x04000000
    strh r1,[r2,#0x10]
    cmp r7,#10
    moveq r0,#114
    movne r0,#112
    cmp r5,r0
    blo m11_frame_end
    bne m11_card_visible
    tst r6,#0x8000
    moveq r0,#0x7d
    movne r0,#0x7c
    cmp r0,#0x7c
    cmpeq r7,#10
    moveq r0,#0x7e
    mov r1,#4
    bl m11_tag_audio
m11_card_visible:
    cmp r7,#10
    bne m11_card_actor
    ldr r0,=340
    cmp r5,r0
    blo m11_card_actor
    ldr r0,=388
    cmp r5,r0
    bhs m11_special_fighter
m11_card_actor:
    tst r6,#0x8000
    ldreq r0,=m11_digits_frame_table
    ldreq r0,[r0,#60]
    ldreq r12,=m11_digits_ptr
    ldrne r0,=m11_get_frame0_ptr
    ldrne r0,[r0]
    ldrne r12,=m11_get_ptr
    ldr r12,[r12]
    mov r1,#112
    cmp r7,#10
    bne m11_draw_card_actor
    ldr r2,=340
    cmp r5,r2
    subhs r2,r5,r2
    subhs r1,r1,r2,lsl #2
m11_draw_card_actor:
    mov r2,#90
    mov r3,#0x2000
    bl m11_layout
    cmp r7,#10
    beq m11_frame_end
    ldr r0,=398
    sub r0,r0,r5
    bl m11_fade
    ldr r0,=398
    cmp r5,r0
    blo m11_frame_end
    sub sp,sp,#44
    mov r0,sp
    bl READER
    cmp r0,#0
    ldrheq r0,[sp,#38]
    movne r0,#0
    add sp,sp,#44
    cmp r0,#0
    beq m11_native_exit
    mov r6,#10
    orr r0,r6,#0x8000
    strh r0,[r4,#4]
    b m11_set_card

@ The GET marker leaves to the left, then the selected fighter runs in with
@ source events 2 and 3. Velocity -512 gains eight units each update.
m11_special_fighter:
    ldr r0,=388
    sub r0,r5,r0
    cmp r0,#24
    bhs m11_fighter_slow
    mov r1,#2
    mov r2,#240
    sub r2,r2,r0,lsl #1
    mov r3,#128
    mov r12,#0
    bl m11_fighter
    b m11_frame_end
m11_fighter_slow:
    cmp r0,#24
    moveq r1,#192
    streq r1,[r4,#60]
    mvneq r1,#0x1fc
    subeq r1,r1,#3
    streq r1,[r4,#64]
    ldr r1,[r4,#64]
    add r1,r1,#8
    str r1,[r4,#64]
    ldr r2,[r4,#60]
    add r2,r2,r1,asr #8
    str r2,[r4,#60]
    cmp r2,#112
    ble m11_begin_celebration
    sub r0,r0,#24
    mov r1,#3
    mov r3,#128
    mov r12,#0
    bl m11_fighter
    b m11_frame_end
m11_begin_celebration:
    mov r0,#2
    strh r0,[r4,#2]
    mov r0,#0
    strh r0,[r4]
    bl m11_graphics_clear
    ldr r0,=m11_name_assets
    bl m11_transfers
    ldr r0,=m11_card_asset_table
    ldr r0,[r0,#40]
    bl m11_transfers
    ldr r2,=0x030012ba
    mov r1,#0xb8
    strb r1,[r2]
    ldr r2,=0x030012bb
    mov r1,#0
    strb r1,[r2]
    ldr r2,=0x030012b9
    mov r1,#246
    strb r1,[r2]
    bl m11_start_confetti
    ldr r0,=0x03003cf8
    ldr r0,[r0]
    ldr r1,[r4,#28]
    str r1,[r0]
    mov r0,#128
    str r0,[r4,#60]
    mov r0,#0
    str r0,[r4,#68]
    str r0,[r4,#72]
    str r0,[r4,#76]
    str r0,[r4,#80]
    ldr r0,=0x03004528
    ldrb r0,[r0]
    ldr r1,=0x0300231a
    ldrb r0,[r1,r0,lsl #1]
    cmp r0,#14
    movhi r0,#0
    ldr r1,=m11_jump_ticks
    add r1,r1,r0,lsl #1
    ldrb r2,[r1]
    strb r2,[r4,#84]
    ldrb r2,[r1,#1]
    strb r2,[r4,#85]
    b m11_frame_end
m11_celebration:
    bl m11_jump_actor
    cmp r5,#151
    blo m11_frame_end
    mov r0,#3
    strh r0,[r4,#2]
    mov r0,#0
    strh r0,[r4]
    add r0,r4,#8
    bl tag_name_init
    b m11_name_draw
m11_editor:
    cmp r0,#2
    beq m11_celebration
    bl m11_jump_actor
    add r0,r4,#8
    ldr r1,=0x0300130a
    ldrh r1,[r1]
    bl tag_name_step
    mov r5,r0
    cmp r1,#0
    beq m11_no_key_sfx
    @ Map to the retail name control's native requests: navigate BF/03D0,
    @ accept C0154, back C006C and final confirmation C0134.
    cmp r1,#0x78
    moveq r8,#0x1e
    cmp r1,#0x79
    moveq r8,#0x1f
    cmp r1,#0x7a
    moveq r8,#0x20
    cmp r1,#6
    moveq r8,#0x21
    mov r9,#1
    cmp r1,#6
    moveq r9,#2
    mov r10,#0
    mov r11,#0
    bl 0x080d15c0
m11_no_key_sfx:
    cmp r5,#2
    bne m11_name_draw
    add r0,r4,#8
    bl tag_name_save
    cmp r0,#0
    beq m11_native_exit
    mov r0,#4
    strh r0,[r4,#2]
    mov r0,#0
    strb r0,[r4,#15]
    ldrb r1,[r4,#12]
    mov r0,#0x28
    add r2,r4,#8
    strb r0,[r2,r1]
m11_name_draw:
    ldrb r0,[r4,#15]
    cmp r0,#0
    ldrbne r0,[r4,#14]
    movne r1,r0
    mov r0,#60
    movne r0,r1
    bl m11_fade
    ldrh r0,[r4,#2]
    cmp r0,#4
    bne m11_name_no_error
    ldr r0,=m11_retry
    mov r1,#60
    mov r2,#80
    bl m11_text
m11_name_no_error:
    add r0,r4,#8
    mov r1,#100
    mov r2,#46
    bl m11_name_text
    ldrb r0,[r4,#15]
    cmp r0,#0
    bne m11_frame_end
    ldrb r0,[r4,#13]
    tst r0,#16
    bne m11_frame_end
    ldr r0,=m11_underscore
    ldrb r1,[r4,#12]
    mov r1,r1,lsl #3
    add r1,r1,#100
    mov r2,#48
    bl m11_name_text
m11_frame_end:
    pop {r0-r12,pc}

m11_native_exit:
    ldr r2,=0x04000050
    ldrh r3,[r4,#88]
    strh r3,[r2]
    ldrh r3,[r4,#90]
    strh r3,[r2,#4]
    bl m11_irq_off
    ldr r0,=0x030012e0
    ldr r1,[r4,#32]
    str r1,[r0]
    ldr r0,=0x03003040
    ldr r0,[r0]
    ldr r1,[r4,#24]
    str r1,[r0]
    ldr r1,[r4,#56]
    str r1,[r0,#0x110]
    ldr r0,=0x03003cf8
    ldr r0,[r0]
    ldr r1,[r4,#28]
    str r1,[r0]
    ldr r0,=0x030012b8
    ldr r1,[r4,#52]
    str r1,[r0]
    ldr r0,=0x030012b6
    ldrh r1,[r4,#48]
    strh r1,[r0]
    pop {r0-r12,lr}
    push {r0-r5,lr}
    ldr r8,=0x03004528
    b 0x080c0d18
m11_retry: .asciz "SAVE ERROR: PRESS A"
m11_underscore: .asciz "_"
.align 2
.ltorg

@ Native BLDY affects the source play area. All three GBA target classes used
@ by its source scene (BG0/BG1/OBJ) fade together over sixty source ticks.
m11_fade:
    cmp r0,#60
    movhs r0,#60
    add r0,r0,#2
    mov r0,r0,lsr #2
    rsb r0,r0,#15
    cmp r0,#15
    moveq r0,#16
    mov r1,#0x04000000
    add r1,r1,#0x50
    cmp r0,#0
    movne r2,#0xf3
    moveq r2,#0
    strh r2,[r1]
    strh r0,[r1,#4]
    bx lr

@ Linked by the source audio-bank installer only after four new table entries
@ and all five retail audio load sites belong to the same image.
@ r0=typed native song id 7B..7E, r1=source priority. All registers preserved.
m11_tag_audio:
    push {r0-r12,lr}
    ldr r2,=m11_tag_audio_ready
    ldr r2,[r2]
    cmp r2,#1
    bne m11_tag_audio_return
    cmp r0,#0x7b
    blo m11_tag_audio_return
    cmp r0,#0x7e
    bhi m11_tag_audio_return
    mov r8,r0
    mov r9,r1
    mov r10,#0
    mov r11,#0
    bl 0x080d15c0
m11_tag_audio_return:
    pop {r0-r12,pc}
m11_tag_audio_ready: .word 0
.ltorg

@ Source 73D3:0AEF..0BB7. The native selected entity supplies the durations
@ of the grounded and landing clips, while the other phases use signed 8.8 velocity.
m11_jump_actor:
    push {r4-r9,lr}
    ldr r6,[r4,#68]
    ldr r7,[r4,#72]
    ldr r8,[r4,#60]
    ldr r9,[r4,#64]
    cmp r6,#0
    beq m11_grounded
    cmp r6,#4
    beq m11_landed
    add r9,r9,#30
    add r8,r8,r9,asr #8
    cmp r6,#1
    bne m11_jump_peak
    cmn r9,#32
    blt m11_jump_draw
    b m11_jump_next
m11_jump_peak:
    cmp r6,#2
    bne m11_jump_fall
    cmp r9,#0
    blt m11_jump_draw
    b m11_jump_next
m11_jump_fall:
    cmp r8,#128
    blt m11_jump_draw
    mov r8,#128
    b m11_jump_next
m11_grounded:
    ldrb r0,[r4,#84]
    cmp r7,r0
    blo m11_jump_draw
    mvn r9,#0x1fc
    sub r9,r9,#3
    b m11_jump_next
m11_landed:
    ldrb r0,[r4,#85]
    cmp r7,r0
    blo m11_jump_draw
    ldr r0,[r4,#80]
    eor r0,r0,#1
    str r0,[r4,#80]
    mov r6,#0
    b m11_jump_reset
m11_jump_next:
    add r6,r6,#1
m11_jump_reset:
    mov r7,#0
m11_jump_draw:
    str r6,[r4,#68]
    str r8,[r4,#60]
    str r9,[r4,#64]
    add r0,r7,#1
    str r0,[r4,#72]
    mov r0,r7
    add r1,r6,#4
    cmp r6,#4
    moveq r1,#17
    mov r2,#112
    mov r3,r8
    ldr r12,[r4,#80]
    bl m11_fighter
    pop {r4-r9,pc}
.ltorg
""".replace('bl READER',f'bl {reader:#010x}')

