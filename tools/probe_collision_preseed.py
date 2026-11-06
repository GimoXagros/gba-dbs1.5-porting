"""Read-only menu-commit -> RNG -> first Waterfall selector discriminator.

Root alone launches runtime. --self-check performs no emulator/ROM/save I/O.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import threading
import time

from mgba_headless_gdb_capture import GdbRemote, PrivateDesktopProcess, connect_gdb, sha256
from mgba_capture_provenance import verify_gdb_owner, verify_loaded_rom_samples
from probe_collision_original_replay import EMULATOR, HISTORICAL, SEED_REGISTERS, registers, schedule

PRESEED, STORED, PATTERN = 0x08091170, 0x08091198, 0x0836D348


def plan(delay):
    return [(at + (delay if at >= 55 else 0), key) for at, key in schedule()]


def prediction(a, b):
    values = []
    for _ in range(3):
        raw = a + b + 0x3711
        a, b = b, raw & 0xFFFF
        values.append(((raw >> 8) + ((raw & 255) << 8)) & 0xFFFF)
    return {"stored_12_14_16": values, "state_after_third": [a, b],
            "first_pattern_index": values[2] % 3}


def permitted(command):
    return command in ("qSupported", "?", "g", "c") or bool(
        re.fullmatch(r"m[0-9a-f]+,[0-9a-f]+", command)
        or re.fullmatch(r"[Zz]0,(?:8091170|8091198|836d348),4", command))


class ReadOnlyGdb(GdbRemote):
    def __init__(self, connection, journal):
        super().__init__(connection)
        self.journal = journal

    def _packet(self, payload):
        command = payload.decode("ascii")
        if not permitted(command):
            raise ValueError("unplanned or guest-write RSP command: " + command)
        self.journal("rsp-send", payload=command)
        return GdbRemote._packet(payload)

    def receive_packet(self, started=False):
        result = super().receive_packet(started)
        self.journal("rsp-receive", payload=result.decode("ascii"))
        return result

    def interrupt(self):
        self.journal("rsp-control", payload="03")
        return super().interrupt()


def observed_prediction(expected, words, state):
    return words == expected["stored_12_14_16"] and state == expected["state_after_third"]


def run(args):
    if any(p.suffix.lower() in (".sav", ".state") for p in (args.rom, args.mgba, args.output)):
        raise ValueError("save/state paths forbidden")
    if sha256(args.rom) != HISTORICAL or sha256(args.mgba) != EMULATOR:
        raise ValueError("exact historical ROM and pinned executable required")
    if not 100 <= args.timeout <= 240:
        raise ValueError("timeout must be100..240 seconds")
    image = args.rom.read_bytes()
    if (image[0x91170:0x91178] != bytes.fromhex("01002DE920002DE9") or
            image[0x91194:0x91198] != bytes.fromhex("B601C4E1") or
            image[0x36D348:0x36D34C] != bytes.fromhex("B030C8E1")):
        raise ValueError("preseed/store/pattern instruction contract")
    args.output.mkdir(parents=True, exist_ok=False)
    isolated = args.output / "probe.gba"
    shutil.copyfile(args.rom, isolated)
    journal_rows, timers = [], []
    origin = time.monotonic()
    report = {"rom_sha256": HISTORICAL, "emulator_sha256": EMULATOR,
              "tool_sha256": sha256(Path(__file__)), "visible": False, "guest_writes": [],
              "menu_delay": args.menu_delay, "scheduled_inputs": plan(args.menu_delay),
              "timeout": args.timeout, "events": [], "session_finished": False,
              "scope": "Instrumented earlier menu commit and first Waterfall selector; no s/exit or historical E5 reproduction claim"}

    def journal(kind, **fields):
        journal_rows.append({"time": time.monotonic() - origin, "kind": kind, **fields})

    def breakpoint(remote, address, add):
        if remote.command(f"{'Z' if add else 'z'}0,{address:x},4") != b"OK":
            raise RuntimeError("breakpoint operation rejected")

    def stop_at(remote, connection, address, deadline):
        breakpoint(remote, address, True)
        connection.settimeout(max(.01, deadline - time.monotonic()))
        remote.start_continue()
        try:
            stopped = remote.receive_packet().decode("ascii")
        except TimeoutError:
            connection.settimeout(10)
            stopped = remote.interrupt().decode("ascii")
        connection.settimeout(10)
        values = registers(remote)
        journal("observed-stop", target=f"{address:08X}", pc=f"{values[15]:08X}")
        report["events"].append({"target": f"{address:08X}", "stop": stopped,
                                 "registers": [f"{v:08X}" for v in values],
                                 "elapsed": time.monotonic() - origin})
        breakpoint(remote, address, False)
        return values

    try:
        with PrivateDesktopProcess(args.mgba.resolve(), ["-g", "-C", "pauseOnMinimize=0", "-C", "pauseOnFocusLost=0", str(isolated.resolve())], args.output.resolve()) as process:
            with connect_gdb(2345, 10, expected_pid=process.pid) as connection:
                report["pid"] = process.pid
                report["endpoint"] = verify_gdb_owner(connection, process.pid)
                remote = ReadOnlyGdb(connection, journal)
                report["supported"] = remote.command("qSupported").decode("ascii")
                report["initial_stop"] = remote.command("?").decode("ascii")
                report["loaded_rom_samples"] = verify_loaded_rom_samples(remote, isolated)
                epoch = time.monotonic()
                deadline = epoch + args.timeout
                report["input_epoch_from_setup_start"] = epoch - origin

                def key(at, code, pressed):
                    windows = process.post_key_state(code, pressed)
                    journal("key-post", scheduled=at, actual_elapsed=time.monotonic() - epoch,
                            key=code, pressed=pressed, windows=windows)

                for at, code in plan(args.menu_delay):
                    for when, pressed in ((at, True), (at + .25, False)):
                        timer = threading.Timer(when, key, (when, code, pressed))
                        timers.append(timer)
                        timer.start()
                pre = stop_at(remote, connection, PRESEED, deadline)
                if pre[15] != PRESEED:
                    report["outcome"] = "preseed-not-observed"
                else:
                    expected = prediction(pre[0] & 0xFFFF, pre[5] & 0xFFFF)
                    report["seed_inputs"] = {"task_private_halfword": pre[0] & 0xFFFF,
                                              "counter": pre[5] & 0xFFFF}
                    report["prediction"] = expected
                    task = int.from_bytes(remote.read_memory(0x0300133C, 4), "little")
                    if pre[4] != 0x03002310 or not (0x02000000 <= task <= 0x0203FFE4 or 0x03000000 <= task <= 0x03007FE4):
                        raise ValueError("unexpected native menu task/config owner")
                    report["menu_commit"] = {"task": f"{task:08X}",
                        "callback": remote.read_memory(task, 4).hex(),
                        "private": remote.read_memory(task + 0x18, 4).hex(),
                        "new_key_mask": remote.read_memory(0x0300130A, 2).hex(),
                        "selected_mode": remote.read_memory(0x03002312, 2).hex()}
                    post = stop_at(remote, connection, STORED, deadline)
                    if post[15] != STORED:
                        report["outcome"] = "third-RNG-store-not-observed"
                    else:
                        words = list(struct.unpack("<3H", remote.read_memory(0x03002322, 6)))
                        state = list(struct.unpack("<2H", remote.read_memory(0x03001420, 4)))
                        report["actual_stored_12_14_16"] = words
                        report["actual_rng_state_after_third"] = state
                        report["prediction_matches_actual"] = observed_prediction(expected, words, state)
                        if not report["prediction_matches_actual"]:
                            report["outcome"] = "three-RNG-prediction-mismatch"
                        else:
                            final = stop_at(remote, connection, PATTERN, deadline)
                            if final[15] != PATTERN:
                                report["outcome"] = "first-pattern-not-observed"
                            else:
                                snapshot = int.from_bytes(remote.read_memory(0x03004CEE, 2), "little")
                                report["pattern_snapshot"] = snapshot
                                report["pattern_prediction_matches_actual"] = snapshot == words[2] and final[3] == expected["first_pattern_index"]
                                report["full17_equal_historical"] = final == SEED_REGISTERS
                                report["outcome"] = ("first-pattern-prediction-confirmed" if report["pattern_prediction_matches_actual"] else "pattern-prediction-mismatch")
                report["session_finished"] = True
    finally:
        for timer in timers:
            timer.cancel()
        for timer in timers:
            timer.join()
        report["journal_entries"] = len(journal_rows)
        (args.output / "preseed.json").write_bytes((json.dumps(report, indent=2) + "\n").encode())
        (args.output / "rsp-and-input.jsonl").write_bytes(b"".join((json.dumps(r) + "\n").encode() for r in journal_rows))
        if report["session_finished"]:
            (args.output / "preseed-done.txt").write_text(report["outcome"], encoding="ascii")
    print(json.dumps({k: report[k] for k in ("outcome", "session_finished", "seed_inputs", "prediction") if k in report}))


def self_check():
    assert prediction(0, 0) == {"stored_12_14_16": [0x1137, 0x226E, 0x44DC],
                                 "state_after_third": [0x6E22, 0xDC44], "first_pattern_index": 0}
    expected = prediction(0xFFFF, 0xFFFF)
    # Carries in raw add survive into the returned byte mix.
    assert expected["stored_12_14_16"] == [0x1137, 0x206E, 0x3FDC]
    assert observed_prediction(expected, expected["stored_12_14_16"], expected["state_after_third"])
    for key in ("stored_12_14_16", "state_after_third"):
        bad = expected[key].copy(); bad[-1] ^= 1
        assert not observed_prediction(expected, bad if key == "stored_12_14_16" else expected["stored_12_14_16"],
                                       bad if key == "state_after_third" else expected["state_after_third"])
    assert plan(0) == schedule()
    assert plan(.02)[0] == (55.02, 0x58) and plan(.02)[-1] == schedule()[-1]
    assert all(new == (at + (.02 if at >= 55 else 0), code) for new, (at, code) in zip(plan(.02), schedule()))
    for command in ("s", "P0=00", "M3002326,2:0200", "c8091170", "Z3,3004cee,2", "Z0,8091174,4"):
        assert not permitted(command)
    for command in ("g", "c", "?", "qSupported", "m3002322,6", "Z0,8091170,4", "z0,836d348,4"):
        assert permitted(command)
    print("PASS: exact three-RNG recurrence/carry, stored/state mutations, earlier-menu schedule and read-only RSP boundary; no emulator/ROM/save I/O")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--mgba", type=Path)
    parser.add_argument("--timeout", type=float, default=160)
    parser.add_argument("--menu-delay", type=float, choices=(0.0, .02), default=0.0,
                        help="Shift A55 and all later inputs; .02 is a measured normal-input comparator, not a guaranteed guest frame")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if args.rom is None or args.output is None or args.mgba is None:
        parser.error("ROM OUTPUT --mgba EXE required")
    run(args)


if __name__ == "__main__":
    main()
