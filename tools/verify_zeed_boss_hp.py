"""Differentially execute WSC and GBA stage 7 HP initializers (Unicorn 2.x)."""
import argparse
import hashlib
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_ARCH_X86, UC_MODE_ARM, UC_MODE_16
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_R5
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES


def words(core, base, offsets):
    return tuple(struct.unpack("<H", core.mem_read(base + off, 2))[0] for off in offsets)


def verify(rom, source):
    assert hashlib.sha256(source).hexdigest() == "c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7"
    ws = Uc(UC_ARCH_X86, UC_MODE_16)
    ws.mem_map(0, 0x100000)
    ws.reg_write(UC_X86_REG_CS, 0x4090)
    ws.reg_write(UC_X86_REG_DS, 0x0C00)
    ws.reg_write(UC_X86_REG_ES, 0x0300)
    ws.mem_write(0x40900, source[0x740900:0x750900])
    ws.mem_write(0x365C, struct.pack("<HH", 0x2000, 0x2200))
    arm = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    arm.mem_map(0x08000000, len(rom))
    arm.mem_write(0x08000000, rom)
    arm.mem_map(0x02000000, 0x40000)
    arm.mem_map(0x03000000, 0x8000)
    player, boss = 0x02011710, 0x02011828
    arm.reg_write(UC_ARM_REG_R4, boss)
    arm.reg_write(UC_ARM_REG_R5, player)
    for fighter in range(15):
        ws.mem_write(0xC000 + 0x2011, bytes([fighter]))
        arm.mem_write(player + 0x11, bytes([fighter]))
        for difficulty in range(256):
            ws.mem_write(0x305D, bytes([difficulty]))
            arm.mem_write(0x0300231F, bytes([difficulty]))
            ws.emu_start(0x40900 + 0x4CDD, 0x40900 + 0x4D2D, count=80)
            arm.emu_start(0x0836FD1C, 0x0836FD58, count=40)
            expected = words(ws, 0xC000 + 0x2200, (0x50, 0x54, 0x56))
            actual = words(arm, boss, (0x64, 0x68, 0x6A))
            assert expected[0] > 0 and actual == expected, (fighter, difficulty, expected, actual)
    return {"rom": hashlib.sha256(rom).hexdigest(), "equal": 15 * 256}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("rom", type=Path)
    cli.add_argument("source", type=Path)
    args = cli.parse_args()
    print(verify(args.rom.read_bytes(), args.source.read_bytes()))
