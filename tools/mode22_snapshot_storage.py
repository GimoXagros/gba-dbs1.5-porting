"""Stack-backed storage for the Tamer Tag viewer's source BE..E7 snapshot.

The native prefix, Shoot save, and eligibility marker use EEPROM blocks 0..26.
This module assembles development code; callers install it only after verifying
the input image's EEPROM owners. CA in this snapshot is reserved and zero.
"""
from mode23_linker import compose

EXPORTS = ("m22_read_snapshot", "m22_write_snapshot")
FIRST_BLOCK, LAST_BLOCK = 27, 33
SNAPSHOT_SIZE = 42

def assemble(address):
    # Block 27 identifies the schema. The next 48 bytes contain the 42-byte
    # snapshot, two zero padding bytes and the little-endian CRC32 of the 44.
    code = """
m22_read_snapshot:
    push {r1-r12,lr}
    sub sp,sp,#60
    mov r4,r0
    mov r5,#27
    mov r6,sp
m22_load:
    mov r0,r5
    mov r1,r6
    bl 0x0837db60
    cmp r0,#0
    bne m22_device_error
    add r6,r6,#8
    add r5,r5,#1
    cmp r5,#34
    bne m22_load
    ldr r1,[sp]
    ldr r2,m22_magic
    cmp r1,r2
    ldreq r1,[sp,#4]
    ldreq r2,m22_version
    cmpeq r1,r2
    bne m22_check_empty
    add r0,sp,#8
    bl m22_crc
    ldr r2,[sp,#52]
    cmp r0,r2
    ldrbeq r2,[sp,#20]
    cmpeq r2,#0
    ldrheq r2,[sp,#50]
    cmpeq r2,#0
    bne m22_invalid
    add r1,sp,#8
    mov r2,#0
m22_copy_out:
    ldrb r3,[r1,r2]
    strb r3,[r4,r2]
    add r2,r2,#1
    cmp r2,#42
    bne m22_copy_out
    mov r0,#0
    b m22_return
m22_check_empty:
    ldrb r1,[sp]
    cmp r1,#0
    cmpne r1,#255
    bne m22_invalid
    mov r2,#1
m22_blank_byte:
    ldrb r3,[sp,r2]
    cmp r1,r3
    bne m22_invalid
    add r2,r2,#1
    cmp r2,#56
    bne m22_blank_byte
    mov r2,#0
    mov r3,#0
m22_clear_out:
    strb r3,[r4,r2]
    add r2,r2,#1
    cmp r2,#42
    bne m22_clear_out
    mov r0,#2
    b m22_return
m22_invalid:
    mov r0,#3
    b m22_return
m22_device_error:
    mov r0,#1
m22_return:
    add sp,sp,#60
    pop {r1-r12,lr}
    bx lr
m22_write_snapshot:
    push {r1-r12,lr}
    sub sp,sp,#60
    mov r4,r0
    mov r2,#0
    add r6,sp,#8
m22_copy_in:
    ldrb r3,[r4,r2]
    strb r3,[r6,r2]
    add r2,r2,#1
    cmp r2,#42
    bne m22_copy_in
    mov r3,#0
    strb r3,[r6,#12]
    strh r3,[r6,#42]
    mov r0,r6
    bl m22_crc
    str r0,[sp,#52]
    mov r5,#28
m22_write_body:
    mov r0,r5
    mov r1,r6
    bl 0x0837db54
    cmp r0,#0
    bne m22_device_error
    add r6,r6,#8
    add r5,r5,#1
    cmp r5,#34
    bne m22_write_body
    mov r0,#27
    adr r1,m22_magic
    bl 0x0837db54
    cmp r0,#0
    movne r0,#1
    b m22_return
m22_crc:
    mvn r1,#0
    mov r2,#0
    ldr r12,m22_polynomial
m22_crc_byte:
    ldrb r3,[r0,r2]
    eor r1,r1,r3
    mov r3,#8
m22_crc_bit:
    tst r1,#1
    mov r1,r1,lsr #1
    eorne r1,r1,r12
    subs r3,r3,#1
    bne m22_crc_bit
    add r2,r2,#1
    cmp r2,#44
    bne m22_crc_byte
    mvn r0,r1
    bx lr
.align 2
m22_magic: .word 0x35315342
m22_version: .word 0x01474154
m22_polynomial: .word 0xedb88320
"""
    return compose([code], address, EXPORTS)
