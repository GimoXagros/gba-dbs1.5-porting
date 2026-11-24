"""Relocate existing mode tables and add only the source mode23 route.

Modes21/22 remain unregistered zero rows, with no new menu producer. The title
tree must not expose any extra mode until its complete scene is installed.
"""
import hashlib
import struct

BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'


def tables(source, native, address, constructor):
    if hashlib.sha256(source).hexdigest().upper() != SOURCE or hashlib.sha256(native).hexdigest().upper() != BEFORE:
        raise ValueError('mode23 dispatcher source/native identities')
    if address % 4 or constructor % 4 or not BASE <= address < 0x0A000000 or not BASE <= constructor < 0x0A000000:
        raise ValueError('aligned ROM mode23 table and constructor')
    if source[0x74FA48:0x74FA4E] != bytes.fromhex('0f0614120517') or source[0x74FABA:0x74FAC0] != bytes.fromhex('140000000000'):
        raise ValueError('source select/exit transitions')
    callbacks = native[0x15B70:0x15C6C] + bytes(24) + struct.pack('<III', 0x080159B0, constructor, 0x080159B0)
    dispatch = native[0x15C6C:0x15CC0] + bytes(8) + struct.pack('<I', 0x08015B40)
    transition = bytearray()
    for mode in range(24):
        row = native[0x15CC8 + mode * 5:0x15CCD + mode * 5] + bytes(1) if mode < 21 else bytes(6)
        transition.extend(row)
    transition[4 * 6 + 5] = 23
    transition[23 * 6] = 20
    return callbacks + dispatch + transition


def patches(source, native, address, constructor, selector):
    blob = tables(source, native, address, constructor)
    if selector % 4 or not BASE <= selector < 0x0A000000:
        raise ValueError('aligned selector hook')
    changes = {}

    def word(at, expected, value):
        if struct.unpack_from('<I', native, at)[0] != expected:
            raise ValueError(f'dispatch consumer changed at {at:06X}')
        changes[at] = struct.pack('<I', value)

    # ADR -> LDR at every existing reader; the old tables become pointer slots.
    for at, old, new in ((0x159E0, 0xE28F8F62, 0xE59F8188),
                         (0x159FC, 0xE28F8E17, 0xE59F8170),
                         (0x15A20, 0xE28F8F53, 0xE59F814C),
                         (0x15AD4, 0xE28F809C, 0xE59F809C),
                         (0x15AF8, 0xE28F8F5B, 0xE59F816C),
                         (0x15AF0, 0xE28F4E1D, 0xE59F41D0),
                         (0x15AE8, 0xE3A09005, 0xE1A09080),
                         (0x15AEC, 0xE0809100, 0xE0899100)):
        word(at, old, new)
    for at, value in ((0x15B70, address), (0x15B74, address + 4),
                      (0x15B78, address + 8), (0x15C6C, address + 24 * 12),
                      (0x15CC8, address + 24 * 16)):
        changes[at] = struct.pack('<I', value)
    delta = selector - (BASE + 0x81C80 + 8)
    if delta % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError('selector branch range')
    word(0x81C80, 0x0A00000B, 0x0A000000 | ((delta // 4) & 0xFFFFFF))
    return blob, changes


def selector_assembly():
    return '''m23_select_transition:
tst r8,#8
movne r1,#5
ldr pc,m23_select_continuation
m23_select_continuation: .word 0x08081cb4
'''
