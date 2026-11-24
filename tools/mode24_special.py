"""Source link SPECIAL celebration with private state in the existing two scene tasks."""
import hashlib
import struct
from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color

SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PARENT='505DCE0601EA9ACCB7D27D9AE410132D27933E733580574F4B177541B05DA96D'
M24_SPECIAL_EXPORTS=('m24s_sprite','m24s_editor','m24s_party_init','m24s_particles',
                     'm24s_begin_party','m24s_name_begin','m24s_animate')


def assembly(source, before):
    digest=lambda b:hashlib.sha256(b).hexdigest().upper()
    assert digest(source)==SOURCE and digest(before)==PARENT
    # Source mode 24 really calls the same 73D3:00EE factory as an earned
    # ending tag, and 73D3:052E explicitly reassigns the 069D SPECIAL callback.
    assert source[0x773d5b:0x773d60]==source[0x77b315:0x77b31a]==bytes.fromhex('9aee00d373')
    assert source[0x774215:0x77421a]==bytes.fromhex('9a2e05d373')
    assert source[0x7742cf:0x7742d2]==bytes.fromhex('b89d06')
    source_tiles=source[0x3cd6b0:0x3cd8f0]
    assert before[0x192a8:0x194e8]==b''.join(convert_tile(source_tiles[i:i+32]) for i in range(0,576,32))
    palette=struct.unpack_from('<16H',source,0x3d7f76)
    assert before[0x194ee:0x1950e]==struct.pack('<16H',*(convert_color(c) for c in palette))
    assert before[0xbbb88:0xbbb88+120]==source[0x774ca8:0x774ca8+120]
    # Source 6D7F:1A1F retains SI after an offscreen particle respawns.
    # All potential velocity lookups in both ROM regions are kept verbatim.
    bank=0x76d7f0
    vectors=bytes(8)+source[bank+0x1b59:bank+0x1b59+512]+source[bank+0x5c7:bank+0x5c7+636]
    assert len(vectors)==1156
    table='m24s_vectors: .hword '+','.join(str(v[0]) for v in struct.iter_unpack('<H',vectors))
    return """
@ Input state is the existing renderer payload R4/handle R9 and controller
@ handle R10. All returns go to the original normal frame/exit paths.
m24s_sprite:
    cmp r7,#10
    bne m24s_original
    ldrh r0,[r4,#4]
    cmp r0,#3
    beq m24s_party
    ldr r0,=340
    cmp r5,r0
    blo m24s_original
    ldr r0,=388
    cmp r5,r0
    bhs m24s_fighter
    ldr r0,=340
    sub r0,r5,r0
    mov r1,#112
    sub r1,r1,r0,lsl #2
    tst r6,#0x8000
    ldr r2,=0x08ea5714
    ldreq r0,[r2,#60]
    ldreq r2,=0x08ea5700
    ldrne r0,=0x08ea5708
    ldrne r0,[r0]
    ldrne r2,=0x08ea5704
    ldr r12,[r2]
    mov r2,#90
    mov r3,#0x2000
    bl 0x08ea5174
    b 0x08ecab9c
m24s_original:
    tst r6,#0x8000
    b 0x08ecaa7c

m24s_fighter:
    ldr r0,=388
    sub r0,r5,r0
    cmp r0,#24
    bhs m24s_slow
    mov r1,#2
    mov r2,#240
    sub r2,r2,r0,lsl #1
    mov r3,#128
    mov r12,#0
    bl 0x08ea522c
    b 0x08ecab9c
m24s_slow:
    add r6,r10,#124
    cmp r0,#24
    moveq r1,#192
    streq r1,[r6,#60]
    mvneq r1,#0x1fc
    subeq r1,r1,#3
    streq r1,[r6,#64]
    ldr r1,[r6,#64]
    add r1,r1,#8
    str r1,[r6,#64]
    ldr r2,[r6,#60]
    add r2,r2,r1,asr #8
    str r2,[r6,#60]
    cmp r2,#112
    ble m24s_begin_party
    sub r0,r0,#24
    mov r1,#3
    mov r3,#128
    mov r12,#0
    bl 0x08ea522c
    b 0x08ecab9c
m24s_begin_party:
    mov r0,#3
    strh r0,[r4,#4]
    bl 0x08ea4ff4
    ldr r0,=0x08ea5690
    bl 0x08ea5074
    bl 0x08da097c
    mov r0,#128
    str r0,[r6,#60]
    mov r0,#0
    str r0,[r6,#64]
    str r0,[r6,#68]
    str r0,[r6,#72]
    str r0,[r6,#76]
    str r0,[r6,#80]
    str r0,[r6,#88]
    ldr r0,=0x03004528
    ldrb r0,[r0]
    ldr r1,=0x0300231a
    ldrb r0,[r1,r0,lsl #1]
    cmp r0,#14
    movhi r0,#0
    ldr r1,=0x08ea5974
    add r1,r1,r0,lsl #1
    ldrb r2,[r1]
    strb r2,[r6,#84]
    ldrb r2,[r1,#1]
    strb r2,[r6,#85]
    bl m24s_party_init
    b 0x08ecab9c
m24s_party:
    bl m24s_animate
    add r6,r10,#124
    ldr r0,[r6,#88]
    cmp r0,#151
    blo m24s_frame_done
m24s_name_begin:
    mov r0,#2
    strh r0,[r4,#4]
    add r0,r4,#16
    bl 0x08ea5994
    b 0x08ecab1c
m24s_frame_done:
    b 0x08ecab9c
m24s_editor:
    bl m24s_animate
    b 0x08ecab1c

m24s_animate:
    push {r0-r12,lr}
    add r4,r10,#124
    ldr r0,[r4,#88]
    add r0,r0,#1
    str r0,[r4,#88]
    bl 0x08ea4f18
    bl m24s_particles
    pop {r0-r12,pc}
.ltorg

@ Each 10B particle: int16 x/y, int8 clamped dx/dy, u16 force-table
@ byte offset, u8 scheduling threshold, u8 freshly loaded velocity flag.
@ Particles 0..14 use renderer payload+96. 15..29 use controller payload+0.
m24s_slot:
    cmp r0,#15
    addlo r1,r9,#120
    addhs r1,r10,#24
    subhs r0,r0,#15
    add r0,r0,r0,lsl #2
    add r0,r1,r0,lsl #1
    bx lr
m24s_party_init:
    push {r0-r8,lr}
    ldr r5,=0x080bbb88
    mov r4,#0
m24s_seed_next:
    mov r0,r4
    bl m24s_slot
    ldrh r1,[r5],#2
    strh r1,[r0]
    ldrh r1,[r5],#2
    strh r1,[r0,#2]
    mov r1,#0
    strh r1,[r0,#4]
    strh r1,[r0,#6]
    strh r1,[r0,#8]
    add r4,r4,#1
    cmp r4,#30
    blo m24s_seed_next
    ldr r1,=0x080194ee
    ldr r2,=0x05000260
    mov r3,#16
m24s_party_ink:
    ldrh r0,[r1],#2
    strh r0,[r2],#2
    subs r3,r3,#1
    bne m24s_party_ink
    pop {r0-r8,pc}

m24s_rng:
    push {r1-r12,lr}
    bl 0x08012600
    pop {r1-r12,pc}

@ Record 6D7F:1A1F is applied in source index order, including the
@ retained source-table cursor on respawn. RNG and geometry stay per peer.
m24s_particles:
    push {r0-r12,lr}
    sub sp,sp,#20
    bl m24s_rng
    and r0,r0,#15
    str r0,[sp]
    bl m24s_rng
    bl m24s_rng
    and r0,r0,#15
    mov r0,r0,lsl #3
    str r0,[sp,#4]
    bl m24s_rng
    and r0,r0,#31
    mov r0,r0,lsl #2
    add r0,r0,#520
    str r0,[sp,#8]
    mov r0,#8
    str r0,[sp,#12]
    mov r4,#0
m24s_particle_next:
    mov r0,r4
    bl m24s_slot
    mov r5,r0
    ldrh r0,[r5,#6]
    ldr r8,=m24s_vectors
    add r8,r8,r0
    ldrb r0,[r5,#9]
    cmp r0,#0
    ldrsbeq r1,[r5,#4]
    ldrsbeq r2,[r5,#5]
    ldrshne r1,[r8]
    ldrshne r2,[r8,#2]
    ldrsh r0,[r8,#4]
    add r1,r1,r0
    ldrsh r0,[r8,#6]
    add r2,r2,r0
    mov r1,r1,lsl #16
    mov r1,r1,asr #16
    mov r2,r2,lsl #16
    mov r2,r2,asr #16
    cmp r1,#7
    movgt r1,#7
    cmn r1,#7
    mvnlt r1,#6
    cmp r2,#7
    movgt r2,#7
    cmn r2,#7
    mvnlt r2,#6
    strb r1,[r5,#4]
    strb r2,[r5,#5]
    mov r0,#0
    strb r0,[r5,#9]
    ldrsh r6,[r5]
    ldrsh r7,[r5,#2]
    add r6,r6,r1
    add r7,r7,r2
    cmp r7,#0x980
    blt m24s_particle_store
    ldr r0,[sp,#8]
    str r0,[sp,#12]
    ldr r1,=m24s_vectors
    add r1,r1,r0
    ldrsh r6,[r1]
    ldrsh r7,[r1,#2]
m24s_particle_store:
    strh r6,[r5]
    strh r7,[r5,#2]
    ldrb r0,[r5,#8]
    ldr r1,[sp]
    cmp r0,r1
    bhi m24s_particle_draw
    bl m24s_rng
    and r0,r0,#15
    strb r0,[r5,#8]
    and r0,r4,#3
    ldr r1,[sp,#12]
    add r0,r1,r0,lsl #7
    ldr r1,[sp,#4]
    add r0,r0,r1
    strh r0,[r5,#6]
    mov r0,#1
    strb r0,[r5,#9]
m24s_particle_draw:
    add r0,r10,#124
    ldr r0,[r0,#88]
    ldr r1,=m24s_phase
    ldrb r1,[r1,r4]
    add r0,r0,r1
m24s_frame_mod:
    cmp r0,#30
    subhs r0,r0,#30
    bhs m24s_frame_mod
    cmp r0,#10
    movlo r1,#0
    movhs r1,#1
    cmp r0,#20
    movhs r1,#2
    ldr r0,=m24s_tiles_base
    ldrb r0,[r0,r4]
    add r0,r0,r1
    ldr r1,=0x080192a8
    add r0,r1,r0,lsl #5
    mov r1,r6,asr #4
    mov r2,r7,asr #4
    sub r1,r1,#4
    sub r2,r2,#4
    mov r3,#0x3000
    mov r12,#0
    bl 0x08ea50d8
    add r4,r4,#1
    cmp r4,#30
    blo m24s_particle_next
    add sp,sp,#20
    pop {r0-r12,pc}
.ltorg
""" + '\n' + table + '\nm24s_phase: .byte '+','.join(str(2*((i+1)//6)) for i in range(30))+'\nm24s_tiles_base: .byte '+','.join(str((0,9,6,3,12,15)[i%6]) for i in range(30))+'\n.align 2'

