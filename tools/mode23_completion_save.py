"""Source B059 pending unlock and save-mode2 over the native EEPROM record.

The existing checksum writer owns physical storage. Its C0-byte record must
not be enlarged over the separately allocated Shoot EEPROM block25.
"""
import hashlib

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'


def sanitizer_patches(native):
    if hashlib.sha256(native[0x1FA98:0x1FC64]).hexdigest().upper() != 'B9F6759F5A773EA913AD95205D38C061D5CB9298E8ED44A04ABA2C0DECEBEEFA':
        raise ValueError('native serializer predecessor differs')
    # Keep buffer64 mask1F: only the permanent unlock field gains bit5.
    return {0x1FAB8: bytes.fromhex('3f8008e2'),
            0x1FB08: bytes.fromhex('0e0050e3')}


def assembly(source, native):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE:
        raise ValueError('mode23 source differs')
    sanitizer_patches(native)
    if hashlib.sha256(native[0xC12EC:0xC1400]).hexdigest().upper() != '3DEB97A0004B6E99966A3859ED0CBFB5E664604779A14B4172A1BB389A6D8EA7':
        raise ValueError('native score sorter differs')
    return """
m23_completion_save:
push {r0-r12,lr}
ldr r1,m23_completion_config
ldrb r2,[r1,#0x19]
mov r0,#0x10
bic r0,r0,r2
ldrb r2,[r1,#0x18]
orr r2,r2,r0
strb r2,[r1,#0x18]
bl 0x0801fa98
bl 0x080c12ec
ldr r1,m23_completion_config
ldrb r0,[r1,#0x19]
ldr r1,m23_completion_buffer
strh r0,[r1,#0x12]
bl 0x0801fc5c
pop {r0-r12,pc}
m23_completion_config: .word 0x03002310
m23_completion_buffer: .word 0x03001120
"""
