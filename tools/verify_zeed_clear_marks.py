"""Compare the original winning path and both GBA save operations for each fighter."""
import argparse
import hashlib
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SP, UC_X86_REG_SS
from verify_mode23_completion_save import BUFFER, CONFIG, StorageMachine, fill


def source_writes(source, fighter):
    ws = Uc(UC_ARCH_X86, UC_MODE_16)
    ws.mem_map(0, 0x100000)
    ws.mem_write(0x60000, source[0x760000:0x800000])
    ws.reg_write(UC_X86_REG_CS, 0x76F1)
    ws.reg_write(UC_X86_REG_SS, 0x2000)
    ws.reg_write(UC_X86_REG_SP, 0x4000)
    ws.mem_write(0x10058, bytes([fighter]))
    ws.mem_write(0x1006A, b"\x01\x00")
    pc = 0x78491
    observed = []
    for stop in (0x784C1, 0x784CD):
        ws.emu_start(pc, stop, count=200000)
        assert ws.reg_read(UC_X86_REG_CS)*16 + ws.reg_read(UC_X86_REG_IP) == stop
        observed.append(tuple(struct.unpack("<H", ws.mem_read(addr, 2))[0] for addr in
                              (0x1006A, 0xC000 + 0x392C + 0x10, 0x10076 + 0x10)))
        pc = stop
    return observed


def native_writes(rom, fighter):
    # The native battle write to CONFIG+1C is also observed in real gameplay.
    arm = StorageMachine(rom, 0)
    fill(arm, BUFFER, bytes(200))
    arm.put(CONFIG + 0x1C, 1 | (1 << fighter), 2)
    arm.put(BUFFER + 0x10, 1, 2)
    stack, stop = arm.r[13], 0x09000000
    observed = []
    for selector in (1, 2):
        arm.put(stack, 0)
        arm.put(stack + 4, selector)
        arm.r[14] = stop
        arm.run(0x0801FBD0, {stop}, max_steps=100000)
        assert arm.r[13] == stack
        observed.append((arm.get(CONFIG + 0x1C, 2), arm.get(BUFFER + 0x10, 2),
                         struct.unpack_from("<H", arm.blocks, 0x10)[0]))
    return observed


def verify(rom, source):
    assert hashlib.sha256(source).hexdigest() == "c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7"
    for fighter in range(15):
        ws, gba = source_writes(source, fighter), native_writes(rom, fighter)
        assert ws[1] == gba[1]
        assert ws[1][2] == (1 | (1 << fighter)) & 0x3FFF
        if fighter == 14:
            assert ws == [(0x4001, 0x4001, 0x4001), (0x4001, 1, 1)]
            assert gba == [(0x4001, 1, 1), (0x4001, 1, 1)]
        else:
            assert ws == gba
    return {"rom": hashlib.sha256(rom).hexdigest(), "matching_final_records": 15}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("rom", type=Path)
    cli.add_argument("source", type=Path)
    args = cli.parse_args()
    print(verify(args.rom.read_bytes(), args.source.read_bytes()))
