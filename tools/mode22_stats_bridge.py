"""Move native link-stat rows 12..14 from the USA prefix into the Ver.1.5 snapshot."""
import hashlib
import struct

from mode23_linker import compose

BASE = 0x08000000
PREDECESSOR = '8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
EXPORTS = ('m22_stat_row', 'm22_reset_snapshot_then_save')
STATS = 0x33ED84
RESET = 0x1F9C4


def assemble(address, read_entry, write_entry):
    for entry in (address, read_entry, write_entry):
        if entry % 4 or not BASE <= entry < 0x09000000:
            raise ValueError(f'expected aligned cartridge ARM code at {entry:08X}')
    code = f"""
m22_stat_row:
    cmp r0,#12
    blo m22_native_row
    cmp r0,#15
    bhs 0x0833ee0c
    sub sp,sp,#44
    sub r4,r0,#12
    add r4,sp,r4,lsl #2
    mov r0,sp
    bl 0x{read_entry:08x}
    cmp r0,#0
    cmpne r0,#2
    bne m22_skip_stat
    ldrh r2,[r4,#2]
    ldr r3,m22_count_limit
    cmp r2,r3
    bhs m22_skip_stat
    add r2,r2,#1
    strh r2,[r4,#2]
    ldr r2,m22_scores
    ldrb r1,[r2]
    ldrb r2,[r2,#1]
    cmp r9,#0
    movne r3,r1
    movne r1,r2
    movne r2,r3
    cmp r1,r2
    ldrhhi r1,[r4]
    addhi r1,r1,#1
    strhhi r1,[r4]
m22_save_stat:
    mov r0,sp
    bl 0x{write_entry:08x}
    cmp r0,#0
    add sp,sp,#44
    bne 0x0833ee0c
    b 0x0833edf4
m22_skip_stat:
    add sp,sp,#44
    b 0x0833ee0c
m22_native_row:
    mov r0,r0,lsl #2
    b 0x0833ed88

m22_reset_snapshot_then_save:
    push {{r0-r12,lr}}
    sub sp,sp,#48
    ldr r0,[sp,#140]
    cmp r0,#0
    bne m22_reset_confirmed
    mov r4,#0
    mov r5,#0
    mov r7,#0
m22_recheck_block:
    mov r0,r4
    mov r1,sp
    bl 0x0837db60
    cmp r0,#0
    bne m22_reset_cancel
    cmp r4,#0
    bne m22_recheck_checksum
    ldr r2,m22_signature
    ldr r3,[sp]
    cmp r3,r2
    ldreq r2,m22_signature_last
    ldreq r3,[sp,#4]
    cmpeq r3,r2
    movne r7,#1
m22_recheck_checksum:
    cmp r4,#24
    beq m22_recheck_complete
    mov r1,#0
m22_sum_byte:
    ldrb r2,[sp,r1]
    add r5,r5,r2
    add r1,r1,#1
    cmp r1,#8
    bne m22_sum_byte
    add r4,r4,#1
    b m22_recheck_block
m22_recheck_complete:
    ldr r2,[sp]
    cmp r2,r5
    cmpeq r7,#0
    beq m22_reset_cancel
m22_reset_confirmed:
    mov r0,#0
    mov r1,#0
m22_reset_word:
    str r0,[sp,r1]
    add r1,r1,#4
    cmp r1,#44
    bne m22_reset_word
    mov r0,sp
    bl 0x{write_entry:08x}
    cmp r0,#0
    bne m22_reset_cancel
    add sp,sp,#48
    pop {{r0-r12,lr}}
    b 0x08d8d290
m22_reset_cancel:
    add sp,sp,#48
    pop {{r0-r12,lr}}
    bx lr
.align 2
m22_count_limit: .word 999
m22_scores: .word 0x0300475e
m22_signature: .word 0x504d4944
m22_signature_last: .word 0x65562053
"""
    return compose((code,), address, EXPORTS)


def patches(native, symbols, *, predecessor_sha256=PREDECESSOR):
    anchors = {
        (0x33ed64, 0x33ee30): 'dcbc318c8450558bfc3235d9fbbc8a0fad4610204b29758349d26a2f63d2a091',
        (0x8b3a4, 0x8b3ec): '15c01710fc97d564f08964efe646464bfe0702b6e6be5033b1ffd3d13194d9ee',
        (0x1f894, 0x1fa18): '7083d6958638b355df79dd25a2867af00910c16d7fca979f82b65ce575c9ef29',
        (0xd8d290, 0xd8d2ac): '492e2b1ec90aba2d8a1106f6b24d506a645d2f8620f3a9f8157ce60889592c8b',
        (0x37d7e4, 0x37da18): 'bdde1d43fc6768268cffc276e843506b5663b49e3704a7eab18ebbdcd4c856f5',
        (0x37db54, 0x37db6c): 'b014d1afc2e22f57b83e733f4011bcc2b8e6d26fb83f48b550f9c6f605b31cc3',
        (0x1fbd0, 0x1fd30): '01f43cf82067a774bdab0046737bcc74f11a511b171d2280b36ba6bbe65f22f6',
    }
    if (hashlib.sha256(native).hexdigest().upper() != predecessor_sha256 or
            any(hashlib.sha256(native[a:b]).hexdigest() != pin for (a,b), pin in anchors.items())):
        raise ValueError('mode 22 stat/reset predecessor identity')
    out = {}
    for offset, expected, symbol, link in (
        (STATS, 0xE1A00100, EXPORTS[0], False),
        (RESET, 0xEB35B631, EXPORTS[1], True),
    ):
        if struct.unpack_from('<I', native, offset)[0] != expected:
            raise ValueError(f'unexpected displaced instruction at {offset:06X}')
        target = symbols[symbol]
        delta = target - (BASE + offset + 8)
        if not BASE <= target < 0x09000000 or delta % 4 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f'out-of-range ARM branch to {target:08X}')
        out[offset] = struct.pack('<I', 0xEA000000 | (int(link) << 24) | ((delta // 4) & 0xffffff))
    return out
