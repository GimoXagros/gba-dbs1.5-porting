"""Draw the source result assets with the retail OAM uploader and native BG maps."""


def assembly(p):
    def row(label, dst, width, height=1):
        return f'.word {p[label]}, {dst}, {width}, {height}'
    def rows(name, entries):
        return name + ':\n' + '\n'.join(entries) + '\n.word 0\n'
    code = """
m11_graphics_clear:
    push {r4-r5,lr}
    mov r0,#0
    ldr r1,=0x0600f000
    mov r2,#1024
m11_clear_maps:
    str r0,[r1],#4
    subs r2,r2,#1
    bne m11_clear_maps
    ldr r1,=0x06000000
    mov r2,#8
m11_clear_zero:
    str r0,[r1],#4
    subs r2,r2,#1
    bne m11_clear_zero
    ldr r1,=0x030012b8
    str r0,[r1]
    ldr r1,=0x05000000
    strh r0,[r1]
    ldr r1,=0x030012ca
    strb r0,[r1]
    mov r0,#0x04000000
    ldr r1,=0x1f02
    strh r1,[r0,#8]
    ldr r1,=0x1e03
    strh r1,[r0,#10]
    mvn r1,#7
    strh r1,[r0,#0x10]
    strh r1,[r0,#0x12]
    strh r1,[r0,#0x14]
    strh r1,[r0,#0x16]
    ldr r0,=0x030012b6
    mov r1,#7
    strh r1,[r0]
    pop {r4-r5,pc}

m11_transfers:
    push {r4-r8,lr}
    mov r4,r0
m11_transfer_next:
    ldr r0,[r4],#4
    cmp r0,#0
    beq m11_transfer_done
    ldmia r4!,{r1-r3}
m11_transfer_row:
    mov r5,r2
    mov r6,r1
m11_transfer_halfword:
    ldrh r7,[r0],#2
    strh r7,[r6],#2
    subs r5,r5,#1
    bne m11_transfer_halfword
    add r1,r1,#64
    subs r3,r3,#1
    bne m11_transfer_row
    b m11_transfer_next
m11_transfer_done:
    pop {r4-r8,pc}
.ltorg

@ r0=packed native tile, r1/r2=source origin x/y, r3=palette, r12=WSC flags.
m11_emit:
    push {r0-r8,lr}
    cmp r1,#232
    bge m11_emit_done
    cmn r1,#15
    blt m11_emit_done
    cmp r2,#152
    bge m11_emit_done
    cmn r2,#15
    blt m11_emit_done
    ldr r4,=0x030012ca
    ldrb r5,[r4]
    cmp r5,#127
    bhs m11_emit_done
    mov r6,#0x02000000
    add r6,r6,r5,lsl #5
    mov r7,#8
m11_emit_tile:
    ldr r8,[r0],#4
    str r8,[r6],#4
    subs r7,r7,#1
    bne m11_emit_tile
    ldr r6,=0x03001428
    add r6,r6,r5,lsl #3
    add r2,r2,#8
    and r2,r2,#255
    strh r2,[r6]
    add r1,r1,#8
    mov r1,r1,lsl #23
    mov r1,r1,lsr #23
    and r7,r12,#0xc000
    orr r1,r1,r7,lsr #2
    strh r1,[r6,#2]
    orr r3,r3,r5
    orr r3,r3,#0x400
    strh r3,[r6,#4]
    mov r7,#0
    strh r7,[r6,#6]
    add r5,r5,#1
    strb r5,[r4]
m11_emit_done:
    pop {r0-r8,pc}

@ r0=count followed by parts, r1/r2=origin, r3=palette, r12=tile payload.
m11_layout:
    push {r4-r10,lr}
    mov r10,#0
    mov r5,r0
    ldr r4,[r5],#4
m11_parts:
    mov r6,r1
    mov r7,r2
    mov r8,r12
m11_part_next:
    subs r4,r4,#1
    bmi m11_part_done
    ldrh r12,[r5]
    ldrsb r2,[r5,#2]
    ldrsb r1,[r5,#3]
    cmp r10,#0
    rsbne r1,r1,#0
    subne r1,r1,#8
    eorne r12,r12,#0x4000
    add r5,r5,#4
    mov r0,r12,lsl #23
    mov r0,r0,lsr #23
    add r0,r8,r0,lsl #5
    add r1,r1,r6
    add r2,r2,r7
    bl m11_emit
    b m11_part_next
m11_part_done:
    pop {r4-r10,pc}

@ r0=terminated source ASCII, r1/r2=origin. Fixed-cell source font.
m11_text:
    push {r0-r6,r12,lr}
    mov r3,#0x3000
    b m11_text_body
m11_name_text:
    push {r0-r6,r12,lr}
    mov r3,#0x8000
m11_text_body:
    mov r4,r0
    mov r12,#0
m11_text_next:
    ldrb r5,[r4],#1
    cmp r5,#0
    beq m11_text_done
    sub r5,r5,#32
    ldr r0,=m11_font_ptr
    ldr r0,[r0]
    add r0,r0,r5,lsl #5
    bl m11_emit
    add r1,r1,#8
    b m11_text_next
m11_text_done:
    pop {r0-r6,r12,pc}
.ltorg

@ r0=frame time, r1=event, r2=x, r3=y. The source costume owns the palette.
m11_fighter:
    push {r4-r10,lr}
    push {r1-r3,r12}
    ldr r7,=0x03004528
    ldrb r7,[r7]
    ldr r6,=0x0300231a
    add r6,r6,r7,lsl #1
    ldrb r5,[r6]
    cmp r5,#14
    bhi m11_fighter_invalid
    ldr r7,=0x084a80f8
    add r7,r7,r5,lsl #5
    ldr r8,[r7]
    ldr r9,[r7,#4]
    ldr r9,[r9]
    ldr r1,[sp]
    add r9,r9,r1,lsl #4
    ldr r10,[r9]
    ldr r9,[r9,#4]
    mov r1,r0
    mov r2,#0
m11_fighter_frame:
    add r3,r9,r2,lsl #4
    ldrb r0,[r3]
    cmp r1,r0
    blo m11_fighter_pose
    sub r1,r1,r0
    add r2,r2,#1
    cmp r2,r10
    moveq r2,#0
    b m11_fighter_frame
m11_fighter_pose:
    ldrh r0,[r3,#2]
    ldrh r2,[r3,#4]
    ldr r5,[r8,#4]
    add r5,r5,r2,lsl #3
    ldr r12,[r5,#4]
    ldr r4,[r8]
    add r5,r4,r0,lsl #3
    ldr r4,[r5]
    ldr r5,[r5,#4]
    ldrb r0,[r6,#1]
    cmp r0,#0
    ldreq r0,[r7,#8]
    ldrne r0,[r7,#12]
    add r0,r0,#6
    ldr r1,=0x05000280
    mov r2,#16
m11_fighter_palette:
    ldrh r3,[r0],#2
    strh r3,[r1],#2
    subs r2,r2,#1
    bne m11_fighter_palette
    ldr r1,[sp,#4]
    ldr r2,[sp,#8]
    ldr r10,[sp,#12]
    add sp,sp,#16
    mov r3,#0x4000
    b m11_parts
m11_fighter_invalid:
    add sp,sp,#16
m11_fighter_done:
    pop {r4-r10,pc}
.ltorg
"""
    code += rows('m11_score_assets', [
        row('shared',0x06007080,0x600),row('green',0x05000000,16),
        row('scorebg',0x06004000,0x290),row('scorebgpal',0x05000020,32),
        row('back',0x0600f000,32,18),row('front',0x0600f800,32,18),
        row('gold',0x05000260,16),row('digitpal',0x05000240,16)])
    for i in range(11):
        code += rows(f'm11_card_assets{i}',[
            row(f'tag{i}',0x06006540,(60 if i==10 else 28)*16),
            row(f'tagpal{i}',0x050001e0,16),row('getpal',0x05000240,16),
            row('specialmap' if i==10 else 'tagmap',
                0x0600f800+(2 if i==10 else 5)*64,10 if i==10 else 7,6 if i==10 else 4)])
    code += rows('m11_name_assets',[
        row('namebg',0x06004000,0x380),row('namebgpal',0x05000000,16),
        row('namebgmap',0x0600f000,28,18),row('nameink',0x05000300,16)])
    code += 'm11_card_asset_table: .word '+','.join(f'm11_card_assets{i}' for i in range(11))+'\n'
    for label in ('digits','get','get_frame0','total','font'):
        code += f'm11_{label}_ptr: .word {p[label]}\n'
    for label,count in (('digits_frame',16),('level',4)):
        code += f'm11_{label}_table: .word '+','.join(str(p[f'{label}{i}']) for i in range(count))+'\n'
    return code

