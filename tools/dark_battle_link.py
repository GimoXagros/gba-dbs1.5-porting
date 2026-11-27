"""Native 9600 baud D-Ark slave, ported from 4FFF:1504..1832.

The remote game supplies each two-byte request. Only the four actual replies from the
local ROM travel back through SIODATA8. After the exchange both cartridges play out
the already negotiated attacks independently.
"""


def assembly(patterns, stats):
    return f"""
dark_open_link:
    add r0,r10,#0x40
    mov r1,#0
    mov r2,#20
dark_clear_link:
    str r1,[r0],#4
    subs r2,r2,#1
    bne dark_clear_link
    ldr r3,=0x04000128
    ldrh r0,[r3]
    strh r0,[r10,#0x78]
    ldrh r0,[r3,#12]
    strh r0,[r10,#0x7a]
    strh r1,[r3,#12]
    ldr r0,=0x3d80
    strh r0,[r3]
    bx lr
dark_close_link:
    ldr r3,=0x04000128
    mov r0,#0
    strh r0,[r3]
    ldrh r0,[r10,#0x7a]
    strh r0,[r3,#12]
    ldrh r0,[r10,#0x78]
    strh r0,[r3]
    bx lr

dark_link_frame:
    push {{r0-r9,r11,r12,lr}}
    ldr r0,[r10,#16]
    cmp r0,#0
    bne dark_link_done
    ldrb r0,[r10,#0x40]
    cmp r0,#0
    bne dark_battle_frame
    ldr r7,=0x04000128
    ldrb r4,[r10,#0x58]
    ldrb r0,[r10,#0x4a]
    cmp r0,#0
    bne dark_reply_pending
    cmp r4,#0
    beq dark_drain
    ldrh r0,[r10,#0x48]
    add r0,r0,#1
    strh r0,[r10,#0x48]
    cmp r0,#720
    bhs dark_restart_link
dark_drain:
    ldrh r0,[r7]
    tst r0,#0x20
    bne dark_link_done
    ldrb r1,[r7,#2]
    add r2,r10,#0x50
    strb r1,[r2,r4]
    add r4,r4,#1
    strb r4,[r10,#0x58]
    tst r4,#1
    bne dark_drain
    @ A live two-byte frame must be consumed exactly, as in 4FFF:173D.
    ldrh r0,[r7]
    tst r0,#0x20
    beq dark_overflow
    @ 4FFF:1600/166C latches a received word. Its 1616 responder runs at
    @ the NEXT scene tick, after the peer has reconfigured its RX interrupt.
    mov r0,#1
    strb r0,[r10,#0x4a]
    b dark_link_done
dark_reply_pending:
    mov r0,#0
    strb r0,[r10,#0x4a]
    cmp r4,#2
    bne dark_word_two
    ldrh r0,[r10,#0x50]
    mov r0,r0,lsr #4
    and r0,r0,#31
    strb r0,[r10,#0x5c]
    bl 0x08012600
    and r0,r0,#15
    ldr r1,={patterns}
    ldrb r0,[r1,r0]
    strb r0,[r10,#0x5b]
    ldr r6,=0xc20f
    orr r6,r6,r0,lsl #4
    b dark_add_checksum
dark_word_two:
    cmp r4,#4
    bne dark_word_three
    @ The disconnected/fresh Battle Spirit profile at 7B62:052C is 0x58.
    ldr r6,=0x58f
    ldr r0,={stats}
    ldrb r1,[r0,#20]
    strb r1,[r10,#0x60]
    ldrb r1,[r0,#21]
    strb r1,[r10,#0x5e]
    ldrh r2,[r10,#0x52]
    mov r3,r2,lsr #6
    and r3,r3,#60
    add r0,r0,r3
    ldrb r1,[r0],#1
    strb r1,[r10,#0x61]
    mov r2,r2,lsr #12
    and r2,r2,#3
    ldrb r1,[r0,r2]
    strb r1,[r10,#0x5f]
    b dark_add_checksum
dark_word_three:
    cmp r4,#6
    bne dark_word_four
    ldrh r2,[r10,#0x54]
    mov r1,r2,lsr #12
    ldr r0,={stats+64}
    add r0,r0,r1,lsl #1
    ldrb r1,[r0]
    ldrb r3,[r10,#0x61]
    add r3,r3,r1
    strb r3,[r10,#0x61]
    ldrb r1,[r0,#1]
    ldrb r3,[r10,#0x5f]
    add r3,r3,r1
    strb r3,[r10,#0x5f]
    mov r2,r2,lsr #4
    mvn r2,r2
    and r2,r2,#31
    strb r2,[r10,#0x5d]
    ldr r6,=0x080f
    orr r6,r6,r2,lsl #4
dark_add_checksum:
    ldrb r1,[r10,#0x59]
    mov r0,r6,lsr #4
    and r0,r0,#15
    add r1,r1,r0
    mov r0,r6,lsr #8
    and r0,r0,#15
    add r1,r1,r0
    add r1,r1,r6,lsr #12
    strb r1,[r10,#0x59]
    b dark_transmit
dark_word_four:
    ldrb r1,[r10,#0x59]
    rsb r1,r1,#0
    and r1,r1,#15
    mov r6,#15
    orr r6,r6,r1,lsl #12
dark_transmit:
    @ Wait about 2.17 ms per byte as the WSC sender does (30 GBA lines).
    @ A bounded transmit-ready interval prevents a dead serial peripheral
    @ from blocking the scene. No host callback is required for normal B cancel.
    bl dark_uart_byte
    cmp r0,#0
    beq dark_restart_link
    mov r6,r6,lsr #8
    bl dark_uart_byte
    cmp r0,#0
    beq dark_restart_link
    mov r0,#0
    strh r0,[r10,#0x48]
    cmp r4,#8
    bne dark_link_done
    @ 4FFF:1695 validates the remote header after all four replies.
    ldrh r0,[r10,#0x50]
    tst r0,#0x200
    beq dark_restart_link
    tst r0,#0xc00
    bne dark_restart_link
    @ D-Project type 3 (2000:7CB6) compares 16, not 0, for a zero
    @ checksum. We have already sent the original wire word. For its
    @ 02xx/03xx initiator header, stay ready for its menu-driven retry.
    tst r0,#0xf000
    bne dark_battle_begin
    and r1,r0,#15
    cmp r1,#15
    bne dark_battle_begin
    cmp r6,#0
    beq dark_restart_link
    b dark_battle_begin
dark_overflow:
    mov r2,#4
dark_discard:
    ldrb r0,[r7,#2]
    ldrh r0,[r7]
    tst r0,#0x20
    bne dark_restart_link
    subs r2,r2,#1
    bne dark_discard
dark_restart_link:
    mov r0,#0
    strb r0,[r10,#0x58]
    strb r0,[r10,#0x59]
    strb r0,[r10,#0x4a]
    strh r0,[r10,#0x48]
dark_link_done:
    pop {{r0-r9,r11,r12,pc}}

dark_uart_byte:
    ldr r3,=0x04000006
    ldrh r2,[r3]
    mov r1,#0
dark_uart_delay:
    ldrh r0,[r3]
    cmp r2,r0
    beq dark_uart_delay
    mov r2,r0
    add r1,r1,#1
    cmp r1,#30
    blo dark_uart_delay
    ldrh r0,[r7]
    tst r0,#16
    beq dark_uart_send
    cmp r1,#60
    blo dark_uart_delay
    mov r0,#0
    bx lr
dark_uart_send:
    strb r6,[r7,#2]
    mov r0,#1
    bx lr
.ltorg
"""
