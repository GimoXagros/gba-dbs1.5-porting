"""Single-block native EEPROM settings for optional single-player battle assists."""

from mode23_linker import compose

EXPORTS = ("assist_read", "assist_write")
MAGIC = 0x31534142  # BAS1
BLOCK = 34


def assemble(address):
    return compose((f"""
assist_read:
    push {{r1-r12, lr}}
    sub sp, sp, #12
    mov r0, #{BLOCK}
    mov r1, sp
    bl 0x0837db60
    cmp r0, #0
    bne assist_disabled
    ldr r1, [sp]
    ldr r2, assist_magic
    cmp r1, r2
    bne assist_disabled
    ldrh r0, [sp, #4]
    ldrh r1, [sp, #6]
    eor r1, r1, r0
    add r1, r1, #1
    cmp r1, #0x10000
    bne assist_disabled
    bl assist_range
    bls assist_finish
assist_disabled:
    mov r0, #0
assist_finish:
    add sp, sp, #12
    pop {{r1-r12, lr}}
    bx lr
assist_range:
    cmp r0, #0x800
    movhs r1, #0x800
    biclo r1, r0, #0x400
    cmp r1, #1000
    bx lr
assist_write:
    push {{r1-r12, lr}}
    sub sp, sp, #12
    bl assist_range
    movhi r0, #1
    bhi assist_finish
    ldr r1, assist_magic
    str r1, [sp]
    strh r0, [sp, #4]
    mvn r1, r0
    strh r1, [sp, #6]
    mov r0, #{BLOCK}
    mov r1, sp
    bl 0x0837db54
    b assist_finish
assist_magic: .word {MAGIC}
""",), address, EXPORTS)
