"""Keep opening background selectors on their own rows in the native map table."""
import hashlib
import struct


# Each native call loads its descriptor base, pushes the row, then calls 08013BF8.
# The expanded gameplay table retains native rows 0..20 only.
OPENING_LOADS = (
    (0x83B88, 25), (0x83FA4, 26), (0x842B4, 27), (0x84B1C, 22),
    (0x85250, 28), (0x855EC, 29), (0x85AF0, 30), (0x86044, 31),
    (0x866B8, 23), (0x86BE0, 24),
)


def apply(rom: bytearray, source: bytes) -> None:
    native_table = 0x7F8E0
    rows = rom[native_table + 22 * 24:native_table + 33 * 24]
    if hashlib.sha256(rows).hexdigest() != 'd0b55110ef64d54db111fa2d62ed348310ea631860e60b1d3de724fb46ca18ab':
        raise ValueError('Unexpected native opening background descriptors')
    # The initial frame passes row 32 in r9 to a separate wrapper.
    if (struct.unpack_from('<2I', rom, 0x83418) != (0xE3A09020, 0xEBFE44A3)
            or rom[0x146BC:0x146D0].hex() != '18809fe500012de900082de900022de949fdffeb'
            or struct.unpack_from('<I', rom, 0x146DC)[0] != 0x08580000):
        raise ValueError('Unexpected opening row-32 wrapper')
    literals = [0x146DC]
    for pc, row in OPENING_LOADS:
        load, push_table, push_flags, select, push_row, call = struct.unpack_from('<6I', rom, pc)
        if (load & 0xFFFFF000, push_table, push_flags, select, push_row, call) != (
            0xE59F8000, 0xE92D0100, 0xE92D0800, 0xE3A08000 | row, 0xE92D0100,
            0xEB000000 | (((0x13BF8 - (pc + 28)) // 4) & 0xFFFFFF),
        ):
            raise ValueError(f'Unexpected opening map call at {pc:06X}')
        literal = pc + 8 + (load & 0xFFF)
        if struct.unpack_from('<I', rom, literal)[0] != 0x08580000:
            raise ValueError(f'Unexpected opening map base at {literal:06X}')
        literals.append(literal)
    # Four WSC scene changes switch from fading to white to revealing the next actor.
    # WSC durations of 5 and 30 frames translate to 4 and 24 GBA frames.
    helper = 0xE787D0
    def branch(pc, target, opcode):
        return opcode | (((target - pc - 8) // 4) & 0xFFFFFF)
    words = [
        0xE3A09004, 0xEA000000, 0xE3A09018,  # short entry skips the long duration
        0xE59FC018, 0xE58C9000,              # packed duration and zero elapsed time
        0xE59FC014, 0xE3A09082, 0xE4CC9001,  # resume native fade-in
        0xE3A09000, 0xE1CC90B0,
        branch(helper + 40, 0x12008, 0xEA000000),  # original task setter, same LR/r8
        0x0300267C, 0x030012CB,
    ]
    blob = struct.pack('<13I', *words)
    if rom[helper:helper + len(blob)] != b'\xff' * len(blob):
        raise ValueError('Opening fade adapter overlaps another owner')
    calls = []
    for pc, src, ticks in ((0x5B6194, 0x757189, 5), (0x5B68CC, 0x7574E5, 30),
                           (0x5B7110, 0x7577B0, 30), (0x5B7968, 0x757A6A, 5)):
        expected = bytes.fromhex('c7061609') + struct.pack('<H', ticks) + bytes.fromhex('a31809c70620092000c7061a09b604c7061c09b603')
        if source[src:src + len(expected)] != expected or struct.unpack_from('<I', rom, pc)[0] != branch(pc, 0x12008, 0xEB000000):
            raise ValueError(f'Unexpected opening fade transition at {pc:06X}')
        calls.append((pc, branch(pc, helper + (8 if ticks == 30 else 0), 0xEB000000)))
    # The source supplies the presentation table at 03C0 (row 30) for all five actors.
    for start, selector in ((0x756F05, 13), (0x7571CF, 14), (0x757521, 8),
                            (0x7577EC, 9), (0x757AB0, 3)):
        if source[start:start + 12] != bytes.fromhex('68c0036a006a') + bytes([selector]) + bytes.fromhex('9acc4c8c55'):
            raise ValueError(f'Unexpected source actor view at {start:06X}')
    # The retail constructor returns the actor in r4 and clobbers r5 with the asset row.
    # Retain incoming x/y/event on the stack, then recover them into r5/r6/r7.
    actors = ((0x5B8100, 0xE92D40F0, 0xE92D40FE), (0x5B8130, 0xE59F4034, 0xE89D00E0),
              (0x5B8160, 0xE8BD40F0, 0xE8BD40FE), (0x853F4, 0x085B5400, 0x0860B000),
              (0x5B8168, 0x085B5400, 0x0860B000))
    for pc, old, new in actors:
        if struct.unpack_from('<I', rom, pc)[0] != old:
            raise ValueError(f'Unexpected opening actor adapter at {pc:06X}')
        calls.append((pc, new))
    rom[helper:helper + len(blob)] = blob
    for pc, word in calls:
        struct.pack_into('<I', rom, pc, word)
    for literal in literals:
        struct.pack_into('<I', rom, literal, 0x08000000 + native_table)
