"""Install the Waterfall IRQ's frame-specific foreground enable on GBA."""

OFFSET = 0x628380
END = OFFSET + 0x44
# Display helper, its two literal words, and one unused word in the same reservation.
PREIMAGE = bytes.fromhex(
    "0f402de9 1d83eaeb 28009fe5 b010d0e1 121c81e3 20309fe5 b020d3e1 020012e3"
    " 011c8113 b010c0e1 022022e2 b020c3e1 0f40bde8 1eff2fe1 00000004 68250003 ffffffff"
)


def apply(rom: bytearray, source: bytes) -> None:
    if source[0x75FA4A:0x75FA5C] != bytes.fromhex("33c0e4000c050b068203e600813682030200"):
        raise ValueError("Unexpected WSC Waterfall display read, combine, output or phase toggle")
    if rom[OFFSET:END] != PREIMAGE:
        raise ValueError("Unexpected GBA Waterfall IRQ or literal pool")
    body = bytearray(PREIMAGE[:-4])
    body[8] += 4
    body[0x14] += 4
    # The WSC callback reads 1 before both the 5 and 7 outputs. GBA retains
    # BG0 across frames, so explicitly clear it when the retained phase is zero.
    body[0x24:0x24] = bytes.fromhex("011cc103")  # biceq r1, r1, #0x100
    rom[OFFSET:END] = body
