"""Drive unmodified WSC Battle Spirit 1.5 to its D-ARK UART waiting scene."""
import argparse
from pathlib import Path

from wsc_dark_link import Core


def frames(core, count, keys=0):
    for _ in range(count):
        core.frame(keys)


def tap(core, key):
    frames(core, 3, key)
    frames(core, 31)


def wait_mode(core, mode, limit):
    for _ in range(limit):
        if core.sram[0x4e] == mode:
            return
        core.frame()
    raise RuntimeError(f"Expected mode {mode}, got {core.sram[0x4e]} at frame {core.frame_id}")


def wait_scene(core, fighter, out=None):
    wait_mode(core, 3, 6100)
    frames(core, 175)
    tap(core, "Start")
    frames(core, 142)
    for _ in range(3):
        tap(core, "Down")
    tap(core, "A")
    wait_mode(core, 4, 260)
    if not core.sram[0x68] & 2:
        raise RuntimeError("Character select is outside the D-ARK route")
    frames(core, 145)
    for _ in range(fighter):
        tap(core, "Down")
        frames(core, 35)
    frames(core, 95)
    if out:
        core.screen().save(out / "selection.png")
    frames(core, 3, "A")
    wait_mode(core, 18, 200)
    frames(core, 120)
    if core.sram[0x58] != fighter or core.sram[0x4e] != 18:
        raise RuntimeError("Selected fighter did not reach the D-ARK waiting scene")
    if out:
        core.screen().save(out / "waiting.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("dll", "rom", "out"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--fighter", type=int, default=1)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    core = Core(args.dll, args.rom)
    try:
        wait_scene(core, args.fighter, args.out)
        (args.out / "ready.state").write_bytes(core.state())
        print(f"Frame {core.frame_id}, mode {core.sram[0x4e]}, fighter {core.sram[0x58]}")
    finally:
        core.close()
