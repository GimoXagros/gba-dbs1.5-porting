"""Restore the original stage 7 boss HP row for every selectable fighter."""
import hashlib
import struct

from build_shoot_guarded_transition_irq import asm

SOURCE_TABLE = 0x7457F8
ROM_TABLE = 0x5C1400
RANGES = ((0x36FD20, 0x36FD44), (0x370044, 0x370048))


def apply(image: bytearray, source: bytes) -> None:
    for data, start, end, expected in (
        (source, 0x7455DD, 0x74562D, "357087feb92b822cb61ba6998d8b240135d15417b33ae8b346aa0be79baf3bb2"),
        (source, SOURCE_TABLE, SOURCE_TABLE + 30, "f19bb19802488ba10e6948937e946af4385760bf7e88ce4fbdc4a7006346b98e"),
        (image, 0x36FD1C, 0x36FD58, "ac157634f817a8db519efd8e13fa1538cd5946f3299335cdbbd675140d319e8a"),
        (image, 0x370044, 0x370054, "c14799c2d24bcf74f88d787643a00c32b8f0b7534ab730aa604954bfbcfa39fc"),
    ):
        if hashlib.sha256(data[start:end]).hexdigest() != expected:
            raise ValueError(f"Unexpected stage 7 boss HP preimage at {start:06X}")
    rows = source[SOURCE_TABLE:SOURCE_TABLE + 30]
    if image[ROM_TABLE:ROM_TABLE + 30] != rows or any(rows[1::2]):
        raise ValueError("Resident HP rows differ from the original stage 7 halfwords")
    (start, end), (literal, literal_end) = RANGES
    # The native constructor has already loaded the selected player ID into R1.
    # Each pinned source halfword fits in one byte. WSC adds/subtracts quarters
    # of the unadjusted base. Its values above difficulty 3 use one extra quarter.
    instructions = asm("""
        ldr r8,[pc,#0x31c]
        ldrb r10,[r8,r1,lsl #1]
        mov r0,r10,asr #2
        ldr r8,[pc,#0x330]
        ldrb r9,[r8,#0xf]
        cmp r9,#3
        movhi r9,#2
        sub r9,r9,#1
        mla r10,r9,r0,r10
    """, start)
    assert len(instructions) == end - start
    image[start:end] = instructions
    image[literal:literal_end] = struct.pack("<I", 0x08000000 + ROM_TABLE)
