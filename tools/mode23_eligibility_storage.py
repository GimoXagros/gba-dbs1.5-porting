"""Native backing for the source mode 23 eligibility bit on the clear/save path."""
from __future__ import annotations

import hashlib
import struct


SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PREDECESSORS = {
    '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC',
    'C64741E95CECC53BFE7EFBD61D046BD87EFDE021803E835C5DD7B28EA77FC2AA',
}
BASE = 0x08000000
BLOCK = 26
OPEN_MARKER = b'BS15M23\x01'
EXPORTS = ('m23_eligibility_read', 'm23_eligibility_result_stage',
           'm23_eligibility_commit_after_clear', 'm23_eligibility_reset_then_save')
SOURCE_ANCHORS = {
    (0x777049, 0x777074): '048FE02C0757CB5341D9601A57AA22887F7D671C883B73DA82C6F60CB6E06E86',
    (0x778491, 0x7784D9): 'C935EE615EAA46CA6128F0495ADF7131C711F37BC1DF3B07BDB26BE3008EC4D9',
    (0x778534, 0x77856E): 'A324410976BBD63AD8FAA648585408704375060E7EF57C1BD5C54C164F24271F',
    (0x780E68, 0x780E90): '740B6B5F49F804FD09ADB9D1CAFD5750E9DE8E3791A192C5568B32AE290FBB37',
    (0x785E81, 0x785EAB): 'C47E5966F371D5B68EC7F7ED3E0D47CDA307E9009CD8AB899C334E2B652414A5',
    (0x7860CF, 0x786147): 'D4861B6BB6EE391BD16ED49B2DAF6CC15D2050D04EFCB1BC37CA8B4EAAF08483',
}
NATIVE_ANCHORS = {
    (0x89534, 0x89574): '6C65980BCA7D35C0352E71F75603381784CF97038F1AFD095CC19B166CF486AE',
    (0x8B334, 0x8B3A4): '1D175D268A0BECA56603133FBE4A92E0710171663EE98AC74F22CC0EDDF4A55E',
    (0x1F894, 0x1F9D4): '2F3BFF42F0E3B4C05D10F5D8EDAE7BAA88C999FA56C6EC3A2276DCF97ACA7036',
    (0x1FC40, 0x1FD30): '71B20F5A992DF508F862B1536B5A459D9C89356A066D72A4A992C10BCDE4E4CD',
    (0x629820, 0x629898): 'CF7D71C4F38A18146EA81B8F25F5FB9DF07B5E12660742A0969D0A013A6769B8',
    (0x37DB54, 0x37DB6C): 'B014D1AFC2E22F57B83E733F4011BCC2B8E6D26FB83F48B550F9C6F605B31CC3',
}


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def require_authorized_source(source):
    if sha(source) != SOURCE or any(sha(source[a:b]) != pin for (a, b), pin in SOURCE_ANCHORS.items()):
        raise ValueError('mode 23 eligibility source identity')


def require_native(native):
    if sha(native) not in PREDECESSORS or any(sha(native[a:b]) != pin for (a, b), pin in NATIVE_ANCHORS.items()):
        raise ValueError('mode 23 eligibility native identity')
    if struct.unpack_from('<IHHB', native, 0x3877D0) != (512, 64, 0x0300, 6):
        raise ValueError('mode 23 EEPROM geometry')


def assembly(source, native):
    require_authorized_source(source)
    require_native(native)
    first, last = struct.unpack('<2I', OPEN_MARKER)
    return f"""
m23_eligibility_read:
push {{r1-r12,lr}}
sub sp,sp,#12
mov r0,#{BLOCK}
mov r1,sp
bl 0x0837db60
cmp r0,#0
bne m23_eligibility_read_closed
ldr r1,[sp]
ldr r2,m23_eligibility_open
cmp r1,r2
ldreq r1,[sp,#4]
ldreq r2,m23_eligibility_open_last
cmpeq r1,r2
moveq r0,#1
b m23_eligibility_read_done
m23_eligibility_read_closed:
mov r0,#0
m23_eligibility_read_done:
add sp,sp,#12
pop {{r1-r12,lr}}
bx lr

m23_eligibility_result_stage:
cmp r8,#7
cmpne r8,#11
b 0x0808953c

m23_eligibility_commit_after_clear:
push {{r0-r12,lr}}
mrs r4,cpsr
cmp r0,#0
bne m23_eligibility_commit_done
bl m23_eligibility_read
cmp r0,#0
bne m23_eligibility_commit_done
mov r0,#{BLOCK}
adr r1,m23_eligibility_open
bl 0x0837db54
m23_eligibility_commit_done:
msr cpsr_f,r4
pop {{r0-r12,lr}}
add sp,sp,#8
b 0x0808b398

m23_eligibility_reset_then_save:
push {{r0-r12,lr}}
mov r0,#{BLOCK}
adr r1,m23_eligibility_closed
bl 0x0837db54
cmp r0,#0
pop {{r0-r12,lr}}
bxne lr
b 0x0801fbd0
.align 2
m23_eligibility_open: .word 0x{first:08x}
m23_eligibility_open_last: .word 0x{last:08x}
m23_eligibility_closed: .word 0,0
"""


def patches(native, symbols):
    """Relocate two proven native transition instructions into the adapters."""
    require_native(native)
    out = {}
    for offset, expected, symbol, link in (
        (0x89538, 0xE3580007, 'm23_eligibility_result_stage', False),
        (0x8B394, 0xE28DD008, 'm23_eligibility_commit_after_clear', False),
        (0x1F9C4, 0xEB000081, 'm23_eligibility_reset_then_save', True),
    ):
        if struct.unpack_from('<I', native, offset)[0] != expected:
            raise ValueError(f'eligibility hook displaced instruction {offset:06X}')
        target = symbols[symbol]
        delta = target - (BASE + offset + 8)
        if not BASE <= target < 0x09000000 or delta % 4 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f'eligibility hook branch target {target:08X}')
        word = 0xEA000000 | (int(link) << 24) | ((delta // 4) & 0xFFFFFF)
        out[offset] = struct.pack('<I', word)
    return out

