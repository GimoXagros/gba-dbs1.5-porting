"""Use the current roster row to recognize the stationary Zeed ending player."""
import hashlib
import struct

from build_shoot_guarded_transition_irq import asm

BASE = 0x08000000
ROSTER = 0x4A80F8
RANGES = ((0x6FFAC4, 0x6FFACC), (0x6FFB64, 0x6FFB94), (0x6FFDA4, 0x6FFDA8))


def apply(image: bytearray, source: bytes) -> None:
    # 08353304 selects row ID * 32 for the normal form. Its first two words
    # reach presentation +48/+44, or actor +F4/+F0, through 080127E4.
    for data, start, end, expected in (
        (source, 0x75FADA, 0x75FBFC, "942169d587b8e437fd23ea635b6233b2144bf7a2470c544e791c5664d34893b9"),
        (image, 0x353344, 0x3533F0, "c8180ce208c9c925ed77e187bb9f46fa3b0df4ce3cd561a42de3318953489312"),
        (image, 0x127E4, 0x12808, "95c77c0e831d6f6ad1e7ed6b89dd7f5638724d4661a69607c9903b033d9ea71a"),
        (image, ROSTER, ROSTER + 15 * 32, "336f628d90606b41cff9bb6e37b8e0cee7a5865b5f86ede285b855e29ba2f627"),
        (image, 0x6FF9C0, 0x6FFE10, "1dd1939661c5aa934823824cc76290ec6940f7714585b87e4762c6badc6779ac"),
    ):
        if hashlib.sha256(data[start:end]).hexdigest() != expected:
            raise ValueError(f"Unexpected ending/roster preimage at {start:06X}")
    if struct.unpack_from("<I", image, 0x3534C0)[0] != BASE + ROSTER:
        raise ValueError("Player loader descriptor table moved")
    (id_start, id_end), (resource_start, resource_end), (literal, end) = RANGES
    # Keep ID 15 (boss), foreign IDs, evolved forms, non-idle events and foreign
    # graphics out of this display path. R7 is scratch after checking the tasks.
    image[id_start:id_end] = asm("cmp r0,#14\nbhi 0x086ffd3c", id_start)
    check = asm("""
        ldrb r0,[r4,#0x11]
        ldr r7,[pc,#0x234]
        add r7,r7,r0,lsl #5
        ldr r0,[r7]
        ldr r1,[r4,#0xf4]
        cmp r0,r1
        ldreq r0,[r7,#4]
        ldreq r1,[r4,#0xf0]
        cmpeq r0,r1
        ldrheq r0,[r4,#0xba]
        cmpeq r0,#0
        bne 0x086ffd3c
    """, resource_start)
    assert len(check) == resource_end - resource_start
    image[resource_start:resource_end] = check
    image[literal:end] = struct.pack("<I", BASE + ROSTER)
