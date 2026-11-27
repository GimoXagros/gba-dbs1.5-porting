"""Verify a genuine D-Project UART battle using two unmodified WonderSwan ROMs."""
import argparse
import hashlib
import json
from pathlib import Path

from wsc_dark_link import Core, linked_frame
from wsc_dark_setup import wait_scene


def u16(buf, at):
    return int.from_bytes(buf[at:at + 2], "little")


def photo(bs, dp, folder, name):
    bs.screen().save(folder / f"{name}-battle-spirit.png")
    dp.screen().save(folder / f"{name}-d-project.png")


def verify(args):
    args.out.mkdir(parents=True, exist_ok=True)
    bs = Core(args.dll, args.battle_rom)
    dp = Core(args.dll, args.peer_rom)
    try:
        if args.battle_state:
            bs.restore(args.battle_state.read_bytes())
            bs.frame()
        else:
            wait_scene(bs, args.fighter, args.out)
        dp.restore(args.peer_state.read_bytes())
        dp.frame()
        if bs.sram[0x4e] != 18:
            raise ValueError("Battle Spirit is not at the D-ARK waiting screen")
        slots = [i for i in range(0xc014, 0xf800, 0x110)
                 if u16(bs.ram, i) in (0x572, 0x5ee) and u16(bs.ram, i + 2) == 0x7b62]
        if len(slots) != 1:
            raise ValueError(f"Expected one waiting controller, got {slots}")
        controller = slots[0]
        serial = 0xc010 + u16(bs.ram, 0xf850)
        keys = {}
        for entry in args.peer_input:
            frame, key, duration = entry.split(":")
            for i in range(int(frame), int(frame) + int(duration)):
                keys.setdefault(i, []).append(key)

        profile_entry = u16(bs.ram, 0xf990)
        profile_changes = []
        last_profile = profile_entry
        wire, events = [], []
        initial_stats = [core.uart_stats() for core in (bs, dp)]
        last = None
        outcome = None
        result_frame = None
        combat_photo_saved = False
        dp_outcome = None
        dp_result_frame = None
        dp_returned = False
        dp_entry = None
        dp_last = None
        dp_events = []
        bs_return_frame = None
        started = False
        return_mode = None
        photo(bs, dp, args.out, "00-waiting")
        for frame in range(args.limit):
            dp_key = keys.get(frame, ())
            if dp_result_frame is not None and frame == dp_result_frame + 60:
                dp_key = ("A",)
            linked_frame(bs, dp, right_keys=dp_key, trace=wire)
            dp_pc = u16(dp.ram, 0x1f44)
            dp_hp = list(dp.ram[0x1ef4:0x1ef6])
            dp_snapshot = (dp_pc, *dp_hp)
            if dp_snapshot != dp_last:
                dp_events.append(dict(frame=frame, callback=f"{dp_pc:04X}", hp=dp_hp))
                dp_last = dp_snapshot
            if dp_pc == 0x7078 and dp_entry is None:
                dp_entry = frame
            if dp_entry is not None and dp_result_frame is None:
                if bytes(dp.ram[0x0c00:0x1d20]).find(bytes.fromhex("d4 d2 00 c0")) >= 0:
                    if dp_hp[0] == 0 or dp_hp[0] >= 128:
                        dp_outcome = "D-Project loss"
                    elif dp_hp[1] == 0 or dp_hp[1] >= 128:
                        dp_outcome = "D-Project win"
                    dp_result_frame = frame
            if dp_result_frame is not None:
                if frame == dp_result_frame + 30:
                    photo(bs, dp, args.out, "02-peer-result")
                if frame > dp_result_frame + 60 and dp_pc in (0x8110, 0x8184):
                    dp_returned = True
            mode = bs.sram[0x4e]
            profile = u16(bs.ram, 0xf990)
            if profile != last_profile:
                profile_changes.append((frame, profile))
                last_profile = profile
            pc = u16(bs.ram, controller)
            seg = u16(bs.ram, controller + 2)
            if mode != 18:
                if bs_return_frame is None:
                    return_mode = mode
                    bs_return_frame = frame
                if frame == bs_return_frame + 80:
                    photo(bs, dp, args.out, "03-return")
                if dp_returned and frame >= bs_return_frame + 80 and frame >= dp_result_frame + 150:
                    break
                continue
            if seg != 0x7b62:
                continue
            hp = list(bs.ram[controller + 0x12:controller + 0x14])
            turn = bs.ram[controller + 0x16]
            state = (pc, *hp, turn)
            if state != last:
                events.append(dict(frame=frame, callback=f"7B62:{pc:04X}", hp=hp, turn=turn))
                last = state
            if pc == 0x7bb and not started:
                started = True
                photo(bs, dp, args.out, "01-handshake")
                (args.out / "decoded.json").write_text(json.dumps({
                    "frame": frame, "controller_hp": hp,
                    "serial_work": bytes(bs.ram[serial:serial + 0x24]).hex()
                }, indent=2), encoding="utf-8")
            if pc == 0x92d and not combat_photo_saved:
                photo(bs, dp, args.out, "01-combat")
                combat_photo_saved = True
            if not outcome and pc in (0xbf6, 0xc27, 0xd2a):
                if hp[0] == 0 or hp[0] >= 128:
                    outcome = "Battle Spirit loss"
                elif hp[1] == 0 or hp[1] >= 128:
                    outcome = "Battle Spirit win"
                if outcome:
                    result_frame = frame
            if result_frame is not None and frame == result_frame + 30:
                photo(bs, dp, args.out, "02-result")
        photo(bs, dp, args.out, "04-last")
        streams = [
            bytes(byte for _, _, side, byte in wire if side == direction)
            for direction in (0, 1)
        ]
        for game, stream in zip(("battle-spirit", "d-project"), streams):
            print(game, "->", stream.hex(" "))
        clean_exchange = all(len(stream) == 8 for stream in streams)
        for core, before in zip((bs, dp), initial_stats):
            after = core.uart_stats()
            clean_exchange &= all(after[key] - before[key] == 8 for key in ("sent", "received"))
            clean_exchange &= all(after[key] == before[key] for key in ("overrun", "lost"))
        report = {
            "battle_rom_sha256": hashlib.sha256(bs.rom).hexdigest(),
            "peer_rom_sha256": hashlib.sha256(dp.rom).hexdigest(),
            "peer_entry_state_sha256": hashlib.sha256(args.peer_state.read_bytes()).hexdigest(),
            "fighter": bs.sram[0x58], "frame_budget": args.limit,
            "peer_input": args.peer_input, "events": events, "trace": wire,
            "peer_events": dp_events, "peer_handshake_frame": dp_entry,
            "peer_result_frame": dp_result_frame, "peer_outcome": dp_outcome,
            "peer_returned": dp_returned,
            "battle_uart": bs.uart_stats(), "peer_uart": dp.uart_stats(),
            "profile_entry": profile_entry, "profile_changes": profile_changes,
            "profile_return": u16(bs.ram, 0xf990), "entered": started,
            "result_frame": result_frame, "battle_return_frame": bs_return_frame,
            "outcome": outcome, "return_mode": return_mode, "clean_exchange": clean_exchange,
        }
        (args.out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print("battle started", started, "outcome", outcome, "return mode", return_mode)
        return bool(started and return_mode == 20 and dp_returned and clean_exchange and
                    (outcome, dp_outcome) in {("Battle Spirit win", "D-Project loss"),
                                               ("Battle Spirit loss", "D-Project win")})
    finally:
        dp.close()
        bs.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("dll", "battle_rom", "peer_rom", "peer_state", "out"):
        p.add_argument(field, type=Path)
    p.add_argument("--battle-state", type=Path, help="Optional genuine waiting-scene state")
    p.add_argument("--fighter", type=int, default=1)
    p.add_argument("--limit", type=int, default=3600)
    p.add_argument("--peer-input", action="append", default=[],
                   help="D-Project input as relative-frame:key:duration, repeatable")
    raise SystemExit(0 if verify(p.parse_args()) else 1)
