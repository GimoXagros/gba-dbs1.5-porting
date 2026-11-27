"""Read added-stage dimensions from the WSC rows in the existing stage-size helper."""
import struct

from build_stage_integration import assemble_arm, build_stage_dimension_map_helper
from build_mode24_link_cards import branch

BASE = 0x08000000
HELPER = 0x584A80
TABLE = 0x3F058
SOURCE_TABLE = 0x77CCF0


def apply(rom: bytearray, source: bytes) -> None:
    rows = source[SOURCE_TABLE:SOURCE_TABLE + 48]
    if rows[:32] != rom[TABLE:TABLE + 32] or len(rows) != 48:
        raise ValueError("Unexpected retail stage sizes")
    if rom[0x3EE70:0x3EE84] != bytes.fromhex("021715eaf4429fe5768f8fe2050098e7000084e5"):
        raise ValueError("Unexpected stage size consumer")
    old = build_stage_dimension_map_helper()
    if rom[HELPER:HELPER + len(old)] != old:
        raise ValueError("Unexpected stage size adapter")
    # The caller already scales the stage index by four. Bias the four-row
    # extension by eight records so either table accepts the actual stage ID.
    code = assemble_arm("""
        cmp r1, #8
        ldrlo r8, native
        subhs r8, pc, #28
        b 0x0803EE7C
    native:
        .word 0x0803F058
    """, HELPER) + rows[32:]
    assert len(code) <= len(old)
    rom[HELPER:HELPER + len(code)] = code
    struct.pack_into('<I', rom, 0x3EE70, 0xE1A05101)
    rom[0x3EE78:0x3EE7C] = branch(BASE + 0x3EE78, BASE + HELPER)
