"""Apply WSC Train spring acceleration in GBA update units at the floor-launch producer."""
import struct

from build_mode24_link_cards import branch
from mode23_linker import compose


START = 0xDE887C
BASE = 0x08000000


def apply(rom: bytearray, source: bytes) -> None:
    # WSC class-5 spring sets -957 velocity and 16 acceleration, including the short launch.
    for offset in (0x742EA2, 0x768789):
        velocity = -957 if offset == 0x742EA2 else -445
        expected = b"\xc7\x84\x8a\x00" + struct.pack("<h", velocity) + bytes.fromhex("c7848c001000")
        assert source[offset:offset + len(expected)] == expected
    assert struct.unpack_from("<H", source, 0x742C1F + 5 * 2)[0] == 0x250F
    assert struct.unpack_from("<I", rom, 0x3549FC + 5 * 4)[0] == 0x08354C98
    assert struct.unpack_from("<I", rom, 0x3F16C)[0] == 0x03002656
    sites = ((0x354D54, "floor_spring"), (0x357710, "short_spring"))
    assert all(struct.unpack_from("<I", rom, at)[0] == 0xE3A09014 for at, _ in sites)
    # The floor cell is live at the producer but cleared by the animation before takeoff.
    # A shortened launch must retain the gravity that its own initial producer selected.
    code, entries, _ = compose(["""
floor_spring:
    push {r8}
    mrs r8,cpsr
    ldr r9, stage_slot
    ldrh r9, [r9]
    cmp r9, #8
    ldrheq r9, [r4,#0x5a]
    andeq r9,r9,#0x3c
    cmpeq r9,#0x14
    moveq r9,#25
    movne r9,#20
    msr cpsr_f,r8
    pop {r8}
    b 0x08354D58
short_spring:
    push {r8}
    mrs r8,cpsr
    ldr r9, stage_slot
    ldrh r9, [r9]
    cmp r9, #8
    ldrheq r9,[r4,#0xa2]
    cmpeq r9,#25
    movne r9,#20
    msr cpsr_f,r8
    pop {r8}
    b 0x08357714
stage_slot: .word 0x03002656
"""], BASE + START, [name for _, name in sites])
    assert rom[START:START + len(code)] == b"\xff" * len(code)
    for at, name in sites:
        rom[at:at + 4] = branch(BASE + at, entries[name])
    rom[START:START + len(code)] = code
    verify(rom)

def verify(rom):
    """Exercise the installed ARM for every floor class and both spring launch lengths."""
    from verify_mode23_scene_component import empty

    cpu = empty(rom)
    actor = 0x02011000
    for stage in range(12):
        for cls in range(16):
            for old_gravity in (0, 20, 25):
                for offset in (0x354D54, 0x357710):
                    regs = list(range(16))
                    regs[4], regs[13] = actor, 0x03007E00
                    flags = 31 | (cls << 28)
                    cpu.r = regs.copy()
                    cpu.cpsr = flags
                    cpu.put(0x03002656, stage, 2)
                    cpu.put(actor + 0x5A, 0x1801 | (cls << 2), 2)
                    cpu.put(actor + 0xA2, old_gravity, 2)
                    cpu.run(BASE + offset, {BASE + offset + 4})
                    spring = cls == 5 if offset == 0x354D54 else old_gravity == 25
                    regs[9] = 25 if stage == 8 and spring else 20
                    assert cpu.r[:15] == regs[:15] and cpu.cpsr == flags
