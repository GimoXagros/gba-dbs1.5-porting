"""The source special-tag editor and its four-byte save, for the rank-10 presentation."""
import hashlib

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
EXPORTS = ('tag_name_init', 'tag_name_step', 'tag_name_save')


def assembly(source, reader, writer):
    assert hashlib.sha256(source).hexdigest().upper() == SOURCE
    assert source[0x774917:0x77491B] == bytes.fromhex('c6450c41')
    assert source[0x774A29:0x774A2C] == bytes.fromhex('803f28')
    assert source[0x774BB5:0x774BC8] == bytes.fromhex('bff8398b0726890583c30283c7028b07268905')
    return f"""
@ Private eight-byte task state: four name bytes, cursor, blink, timer, phase.
tag_name_init:
    mov r1,#0x41
    str r1,[r0]
    mov r1,#0
    str r1,[r0,#4]
    bx lr

@ r0=editor, r1=repeat-enabled input. r0=0 editing,1 confirmed,2 save due.
@ r1 returns the source navigation sound request (0 if no request).
tag_name_step:
    push {{r4-r7,lr}}
    mov r4,r0
    mov r5,r1
    mov r0,#0
    mov r1,#0
    ldrb r2,[r4,#7]
    cmp r2,#0
    bne tag_name_countdown
    ldrb r2,[r4,#5]
    add r2,r2,#1
    and r2,r2,#31
    strb r2,[r4,#5]
    ldrb r6,[r4,#4]
    ldrb r7,[r4,r6]
    cmp r6,#3
    beq tag_name_buttons
    tst r5,#15
    movne r1,#0x78
    tst r5,#3
    beq tag_name_decrease
    add r7,r7,#1
    cmp r7,#0x60
    moveq r7,#0x20
tag_name_decrease:
    tst r5,#12
    beq tag_name_store
    sub r7,r7,#1
    cmp r7,#0x20
    movlt r7,#0x5f
tag_name_store:
    strb r7,[r4,r6]
tag_name_buttons:
    tst r5,#0x80
    beq tag_name_confirm
    mov r1,#0x7a
    cmp r6,#0
    beq tag_name_confirm
    strb r0,[r4,r6]
    sub r6,r6,#1
    strb r6,[r4,#4]
    b tag_name_return
tag_name_confirm:
    tst r5,#0x40
    beq tag_name_return
    cmp r7,#0x28
    beq tag_name_end
    mov r1,#0x79
    add r6,r6,#1
    strb r6,[r4,#4]
    cmp r6,#3
    moveq r7,#0x28
    movne r7,#0x41
    strb r7,[r4,r6]
    b tag_name_return
tag_name_end:
    strb r0,[r4,r6]
    mov r2,#61
    strb r2,[r4,#6]
    mov r0,#1
    strb r0,[r4,#7]
    mov r1,#6
    b tag_name_return
tag_name_countdown:
    ldrb r2,[r4,#6]
    cmp r2,#0
    subne r2,r2,#1
    strbne r2,[r4,#6]
    moveq r0,#2
tag_name_return:
    pop {{r4-r7,pc}}

@ Merge only CC..CF into the current validated extension. D0..E5 and
@ the preceding native stat pairs can have changed since scene entry.
tag_name_save:
    push {{r4-r6,lr}}
    sub sp,sp,#48
    mov r4,r0
    mov r0,sp
    bl {reader:#010x}
    cmp r0,#0
    bne tag_name_save_return
    ldrh r2,[sp,#0x26]
    cmp r2,#0
    moveq r0,#3
    beq tag_name_save_return
    ldrh r1,[r4]
    ldrh r2,[r4,#2]
    strh r1,[sp,#14]
    strh r2,[sp,#16]
    mov r0,sp
    bl {writer:#010x}
tag_name_save_return:
    add sp,sp,#48
    pop {{r4-r6,pc}}
"""
