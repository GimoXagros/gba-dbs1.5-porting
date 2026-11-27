"""Exercise the installed Waterfall IRQ on both passes with either incoming BG0 state."""
import argparse
from pathlib import Path

from verify_mode23_scene_component import empty


def verify(rom):
    cpu = empty(rom)
    registers = cpu.r[:15]
    display = 0x04000000
    phase = 0x03002568
    for initial in (0, 0x100, 0x200, 0x300, 0x3F40, 0x8D20, 0xFFFF):
        for start in (0, 2):
            cpu.put(display, initial, 2)
            cpu.put(phase, start, 2)
            current = start
            for _ in range(4):
                cpu.run(0x08628380, {0x080C9000})
                assert cpu.r[14] == 0x08628388
                cpu.run(cpu.r[14], {registers[14]})
                assert cpu.r[:15] == registers
                # Original WSC port 00 outputs 5 or 7. Source display bit 1
                # selects GBA BG0; every unrelated hardware bit must survive.
                assert cpu.get(display, 2) == (initial & ~0x100) | 0x1200 | (current << 7)
                current ^= 2
                assert cpu.get(phase, 2) == current


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    verify(parser.parse_args().rom.read_bytes())
    print("PASS: 56 Waterfall display transitions")
