"""Execute the shipped stage 11 display guard on valid and invalid player owners."""
import argparse
import hashlib
import struct
from pathlib import Path

from verify_shoot_terminal_display_epoch import fixture


def check(rom: bytes) -> dict:
    # Read the descriptor address from the real player loader, independently of the patch.
    table = struct.unpack_from("<I", rom, 0x3534C0)[0] - 0x08000000
    rows = [struct.unpack_from("<II", rom, table + i * 32) for i in range(15)]
    machine, player, boss, aux, _ = fixture(rom)
    machine.put(aux + 4, 0x0326, 2)
    stack, stop = machine.r[13], 0x09000000

    def run():
        machine.r[13], machine.r[14] = stack, stop
        machine.run(0x086FF9C0, {stop})
        assert machine.r[13] == stack
        return machine.r[0]

    accepted = rejected = 0
    for fighter, (graphics, layouts) in enumerate(rows):
        machine.put(player + 0x11, fighter, 1)
        machine.put(player + 0xF4, graphics)
        machine.put(player + 0xF0, layouts)
        assert run() == 1, f"fighter {fighter} stalled"
        accepted += 1
        for addr, size in ((player + 0xF4, 4), (player + 0xF0, 4), (player + 0xBA, 2),
                           (player + 0x42, 2), (boss + 0x28, 4), (aux + 0x28, 4)):
            original = machine.get(addr, size)
            machine.put(addr, original ^ 1, size)
            assert run() == 0, f"foreign owner accepted at {addr:08X}"
            machine.put(addr, original, size)
            rejected += 1
    for invalid in range(15, 256):
        machine.put(player + 0x11, invalid, 1)
        assert run() == 0, f"invalid fighter {invalid} accepted"
        rejected += 1
    return {"image": hashlib.sha256(rom).hexdigest(), "valid": accepted, "rejected": rejected}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("rom", type=Path)
    print(check(cli.parse_args().rom.read_bytes()))
