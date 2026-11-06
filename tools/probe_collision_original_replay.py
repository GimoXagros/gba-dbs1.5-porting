"""Replay the original wall-clock seed/step/exit probe with minimal early reads.

Only root should invoke this emulator launcher. --self-check never launches one.
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

HISTORICAL = "389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1"
CURRENT = "A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F"
EMULATOR = "0D9A2779ADD78D41A093C3AF8CEC7D72CC07A5451C8A1E1B167B48CD54950288"
SEED, NEXT, EXIT = 0x0836D348, 0x0836D34C, 0x08585310
SEED_REGISTERS = [int(v, 16) for v in (
    "08584B80 08584B48 0000001F 00000002 020120D0 00000003 03002608 03004708 "
    "03004CF8 08584B00 00003F40 00000000 0837D5E9 03007ED8 0836D320 0836D348 00000010"
).split()]


def schedule(confirm_delay=0.0):
    # Preserve the historical Timer creation order, including Start last.
    return ([(t + (confirm_delay if t >= 65 else 0), 0x58) for t in (55., 65., 88.)]
            + [(t + confirm_delay, 0x27) for t in (76., 80., 84.)] + [(91. + confirm_delay, 0x25)]
            + [(56. + n * .5, 0x28) for n in range(12)] + [(49.5, 0x0D)])


def permitted(command):
    return command in ("qSupported", "?", "g", "s", "c") or bool(
        re.fullmatch(r"m[0-9a-f]+,[0-9a-f]+", command)
        or re.fullmatch(r"[Zz]0,(?:836d348|836d34c|8585310),4", command))


class LoggedGdb(GdbRemote):
    def __init__(self, connection, journal):
        super().__init__(connection)
        self.journal = journal

    def _packet(self, payload):
        text = payload.decode("ascii")
        if not permitted(text):
            raise ValueError("non-read-only/unplanned RSP command: " + text)
        self.journal("rsp-send", payload=text)
        return GdbRemote._packet(payload)

    def receive_packet(self, started=False):
        result = super().receive_packet(started)
        self.journal("rsp-receive", payload=result.decode("ascii"))
        return result

    def interrupt(self):
        self.journal("rsp-control", payload="03")
        return super().interrupt()


def registers(remote):
    raw = remote.command("g").decode("ascii")
    if len(raw) != 17 * 8:
        raise ValueError("unexpected GDB register packet length")
    return list(struct.unpack("<17I", bytes.fromhex(raw)))


def comparable_seed(values):
    return values == SEED_REGISTERS


def step_check(before, after, halfword):
    expected = before.copy()
    expected[15] += 4
    return {"expected_instruction": "0836D348: STRH r3,[r8]", "expected_destination": "03004CF8",
            "expected_halfword": 2, "observed_halfword": halfword,
            "store_halfword_matches": halfword == (before[3] & 0xFFFF),
            "exact_strh_register_successor": after == expected,
            "register_differences": [{"register": n, "before": f"{a:08X}", "after": f"{b:08X}", "expected": f"{e:08X}"}
                for n, (a, b, e) in enumerate(zip(before, after, expected)) if b != e]}


def collision_state(regs, iwram, ewram, rom):
    def read(address, size):
        for base, data in ((0x02000000, ewram), (0x03000000, iwram), (0x08000000, rom)):
            if base <= address and address + size <= base + len(data):
                return int.from_bytes(data[address - base:address - base + size], "little")
        return None

    known = {}
    for group, table in enumerate((0x4A80F8, 0x4A82D8, 0x60B000, 0x60B1E0)):
        for identity in range(15):
            p1 = read(0x08000000 + table + identity * 32 + 4, 4)
            known.setdefault(p1, []).append([group, identity])

    def record(address):
        if address is None:
            return None
        owner, kind, metadata = read(address, 4), read(address + 4, 2), read(address + 16, 4)
        result = {"record_address": f"{address:08X}", "actor": owner, "type": kind, "A": metadata}
        if owner is None or not 0x02000000 <= owner <= 0x0203FEFC:
            return result
        p = owner + 0xAC
        fields = {"event": (0x0E, 2), "command_index": (0x1A, 2), "command_count": (0x1C, 2),
                  "command_base": (0x20, 4), "command_current": (0x24, 4), "A": (0x28, 4),
                  "event_B": (0x2C, 4), "P1": (0x44, 4)}
        presentation = {name: read(p + off, size) for name, (off, size) in fields.items()}
        result["presentation"] = presentation
        p1 = presentation["P1"]
        result["declared_resource_matches"] = known.get(p1, [])
        if not result["declared_resource_matches"]:
            return result
        table = read(p1, 4)
        first_commands = read(table + 4, 4) if table is not None else None
        count = ((first_commands - table) // 16 if first_commands is not None and first_commands >= table
                 and (first_commands - table) % 16 == 0 else None)
        result["native_event_count"] = count
        event = presentation["event"]
        result["event_in_declared_domain"] = count is not None and 0 < count <= 256 and event < count
        if not result["event_in_declared_domain"]:
            return result
        row = table + event * 16
        n, base, a, b = (read(row + offset, 4) for offset in (0, 4, 8, 12))
        index = presentation["command_index"]
        expected_command = base + index * 16 if base is not None else None
        result["selected_event_row"] = {"address": row, "count": n, "commands": base, "A": a, "B": b}
        result["command_index_in_domain"] = n is not None and index < n
        result["command_pointer_matches_index"] = presentation["command_current"] == expected_command
        result["event_B_matches_row"] = presentation["event_B"] == b
        result["A_matches_row"] = presentation["A"] == a
        command_b = read(expected_command + 12, 4) if expected_command is not None and result["command_index_in_domain"] else None
        actual_command_b = read(presentation["command_current"] + 12, 4) if presentation["command_current"] is not None else None
        result["declared_command_B"] = command_b
        result["actual_command_B"] = actual_command_b
        result["event_B_type"] = read(b, 2) if b else None
        result["actual_command_B_type"] = read(actual_command_b, 2) if actual_command_b else None
        role = ("command" if 0x030048C8 <= address < 0x030049B8 else
                "event" if 0x030049B8 <= address < 0x03004AA8 else "outside-two-lists")
        result["list_role"] = role
        selected_type = result["actual_command_B_type"] if role == "command" else result["event_B_type"] if role == "event" else None
        result["record_matches_current_B_type"] = None if selected_type is None else kind == selected_type
        return result

    sp = regs[13]
    handles = [read(sp + offset, 4) for offset in (0x0C, 0x10)]
    actor_views = []
    for owner in regs[4:6]:
        if 0x02000000 <= owner <= 0x0203FEFC:
            actor_views.append({"actor": f"{owner:08X}", "P1": read(owner+0xAC+0x44,4),
                "event": read(owner+0xAC+0x0E,2), "command_index": read(owner+0xAC+0x1A,2),
                "command_count": read(owner+0xAC+0x1C,2), "command_current": read(owner+0xAC+0x24,4),
                "event_B": read(owner+0xAC+0x2C,4)})
        else:
            actor_views.append(None)
    return {"scratch_type": read(0x03004D20, 2), "counts_command_event_world": [read(a, 1) for a in (0x03004C4D, 0x03004C4E, 0x03004C4C)],
            "saved_record_handles_at_SP_0C_10": handles, "saved_records": [record(p) for p in handles],
            "r4_r5_actor_views": actor_views,
            "scope": "Saved record slots apply only if the captured stack still belongs to the dispatch predecessor; r4/r5 are not assumed to be record handles."}


def run(args):
    if any(p.suffix.lower() == ".sav" for p in (args.rom, args.mgba, args.output)):
        raise ValueError("save paths forbidden")
    if sha256(args.rom) not in (HISTORICAL, CURRENT) or sha256(args.mgba) != EMULATOR:
        raise ValueError("unpinned ROM/emulator")
    if args.timeout < 100 or args.timeout > 480:
        raise ValueError("bounded replay timeout must be100..480 seconds")
    rom = args.rom.read_bytes()
    if rom[0x36D348:0x36D34C] != bytes.fromhex("B030C8E1"):
        raise ValueError("seed STRH opcode changed")
    args.output.mkdir(parents=True, exist_ok=False)
    isolated = args.output / "probe.gba"
    shutil.copyfile(args.rom, isolated)
    journal_rows = []
    origin = time.monotonic()

    def journal(kind, **fields):
        journal_rows.append({"time": time.monotonic() - origin, "kind": kind, **fields})

    report = {"rom_sha256": sha256(args.rom), "emulator_sha256": EMULATOR, "guest_writes": [], "visible": False,
              "step_mode": args.step_mode, "timeout": args.timeout, "scheduled_inputs": schedule(args.confirm_delay),
              "confirm_delay": args.confirm_delay,
              "protocol_variant": "original" if args.confirm_delay == 0 else "normal-input-confirm-delay",
              "new_isolated_ROM": str(isolated), "events": []}
    timers = []
    inputs_done = False

    def save():
        (args.output / "replay.json").write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))

    def capture(remote, name, regs):
        iwram, ewram = remote.read_memory(0x03000000, 0x8000), remote.read_memory(0x02000000, 0x40000)
        for suffix, data in (("iwram", iwram), ("ewram", ewram)):
            (args.output / (name + "-" + suffix + ".bin")).write_bytes(data)
        report["final_collision_state"] = collision_state(regs, iwram, ewram, rom)
        report["final_memory"] = {suffix: hashlib.sha256(data).hexdigest().upper() for suffix, data in (("iwram", iwram), ("ewram", ewram))}

    def wait_stop(remote, connection, deadline):
        connection.settimeout(max(.01, deadline - time.monotonic()))
        remote.start_continue()
        try:
            stop = remote.receive_packet().decode("ascii")
        except TimeoutError:
            connection.settimeout(10)
            stop = remote.interrupt().decode("ascii")
        connection.settimeout(10)
        return stop

    try:
        with PrivateDesktopProcess(args.mgba.resolve(), ["-g", "-C", "pauseOnMinimize=0", "-C", "pauseOnFocusLost=0", str(isolated.resolve())], args.output.resolve()) as process:
            with connect_gdb(2345, 10, expected_pid=process.pid) as connection:
                report["pid"] = process.pid
                report["endpoint"] = verify_gdb_owner(connection, process.pid)
                remote = LoggedGdb(connection, journal)
                report["supported"] = remote.command("qSupported").decode("ascii")
                report["initial_stop"] = remote.command("?").decode("ascii")
                report["loaded_rom_samples"] = verify_loaded_rom_samples(remote, isolated)
                if remote.command(f"Z0,{SEED:x},4") != b"OK":
                    raise RuntimeError("seed breakpoint rejected")
                save()
                epoch = time.monotonic()
                deadline = epoch + args.timeout
                report["input_epoch_from_setup_start"] = epoch - origin

                def key(at, code, pressed):
                    windows = process.post_key_state(code, pressed)
                    journal("key-post", scheduled=at, actual_elapsed=time.monotonic() - epoch, key=code, pressed=pressed, windows=windows)

                for at, code in schedule(args.confirm_delay):
                    for when, pressed in ((at, True), (at + .25, False)):
                        timer = threading.Timer(when, key, (when, code, pressed));timers.append(timer);timer.start()
                first_stop = wait_stop(remote, connection, deadline)
                before = registers(remote)
                event = {"stop": first_stop, "registers": [f"{v:08X}" for v in before]}
                report["events"].append(event)
                report["seed_registers_equal_original"] = comparable_seed(before)
                remote.command(f"z0,{SEED:x},4")
                if not comparable_seed(before):
                    report["outcome"] = "seed-not-comparable"
                    capture(remote, "seed-mismatch", before)
                else:
                    # Same small read order as the failed probe; no full early RAM dump.
                    for name, address, size in (("stack", before[13], 128), ("table", 0x08485000, 60),
                            ("object", before[4], 256), ("renderer_state", 0x030012C8, 8), ("waterfall_phase_mode", 0x03002568, 4)):
                        event[name] = {"address": f"{address:08X}", "hex": remote.read_memory(address, size).hex()}
                    if args.step_mode == "gdb":
                        event["step_stop"] = remote.command("s").decode("ascii")
                    else:
                        if remote.command(f"Z0,{NEXT:x},4") != b"OK":
                            raise RuntimeError("next-instruction breakpoint rejected")
                        event["step_stop"] = wait_stop(remote, connection, min(deadline, time.monotonic() + 10))
                        remote.command(f"z0,{NEXT:x},4")
                    after = registers(remote)
                    halfword = int.from_bytes(remote.read_memory(0x03004CF8, 2), "little")
                    event["post_step_registers"] = [f"{v:08X}" for v in after]
                    event["step_check"] = step_check(before, after, halfword)
                    save()
                    if remote.command(f"Z0,{EXIT:x},4") != b"OK":
                        raise RuntimeError("original exit breakpoint rejected")
                    stop = wait_stop(remote, connection, deadline)
                    final = registers(remote)
                    report["final_stop"] = stop
                    report["final_registers"] = [f"{v:08X}" for v in final]
                    capture(remote, "final", final)
                    report["outcome"] = ("original-invalid-target-reproduced" if final[15] == 0xE28DD00C and final[9] == 0xE28DD00C
                        else "original-exit-observed" if final[15] == EXIT else "bounded-other-state")
                inputs_done = True
    finally:
        for timer in timers:
            timer.cancel()
        for timer in timers:
            timer.join()
        # No runtime emulator is launched by imports/self-checks.
        report["session_finished"] = inputs_done
        report["journal_entries"] = len(journal_rows)
        save()
        (args.output / "rsp-and-input.jsonl").write_bytes(b"".join((json.dumps(row) + "\n").encode("utf-8") for row in journal_rows))
        if inputs_done:
            (args.output / "replay-done.txt").write_bytes(report["outcome"].encode("ascii"))
    print(json.dumps({k: report[k] for k in ("outcome", "seed_registers_equal_original", "journal_entries")}))


def self_check():
    assert comparable_seed(SEED_REGISTERS.copy())
    for index in range(17):
        changed = SEED_REGISTERS.copy()
        changed[index] ^= 1
        assert not comparable_seed(changed)
    for command in ("g", "s", "c", "?", "qSupported", "m3004d20,2", "Z0,836d348,4", "z0,8585310,4"):
        assert permitted(command)
    for command in ("M3004d20,2:e500", "P1=ba010000", "G00", "X3004d20,1:x", "c836e348", "s836d348", "Z3,836ef1c,4"):
        assert not permitted(command)
    after = SEED_REGISTERS.copy();after[15] += 4
    assert step_check(SEED_REGISTERS, after, 2)["exact_strh_register_successor"]
    after[1] = 0xE5
    assert not step_check(SEED_REGISTERS, after, 2)["exact_strh_register_successor"]
    assert schedule()[-1] == (49.5, 13) and len(schedule()) == 20
    delayed = schedule(.25)
    assert len(delayed) == 20 and delayed[0] == schedule()[0] and delayed[1] == (65.25, 0x58)
    assert all(new == (at + (.25 if at >= 65 else 0), key)
               for new, (at, key) in zip(delayed, schedule()))
    rom, iwram, ewram = bytearray(0x800000), bytearray(0x8000), bytearray(0x40000)
    def put(data, offset, value, size=4):data[offset:offset+size]=value.to_bytes(size,"little")
    actor, record, p1, table, command, b = 0x02011710, 0x030048C8, 0x086184A0, 0x086184A8, 0x086184C8, 0x08618500
    put(rom,0x4A80F8+14*32+4,p1);put(rom,p1-0x08000000,table)
    put(rom,table-0x08000000,1);put(rom,table-0x08000000+4,command)
    put(rom,command-0x08000000+12,b);put(rom,b-0x08000000,8,2)
    put(ewram,actor-0x02000000+0xAC+0x44,p1)
    put(ewram,actor-0x02000000+0xAC+0x20,command);put(ewram,actor-0x02000000+0xAC+0x24,command)
    put(iwram,record-0x03000000,actor);put(iwram,record-0x03000000+4,0xE5,2)
    regs=[0]*17;regs[13]=0x03007ECC
    put(iwram,0x7ED8,record);put(iwram,0x7EDC,0x030049B8);put(iwram,0x4D20,0xE5,2)
    result=collision_state(regs,iwram,ewram,rom)
    assert result["saved_records"][0]["type"]==0xE5
    assert result["saved_records"][0]["actual_command_B_type"]==8
    assert not result["saved_records"][0]["record_matches_current_B_type"]
    put(rom,b-0x08000000,0xE5,2)
    assert collision_state(regs,iwram,ewram,rom)["saved_records"][0]["record_matches_current_B_type"]
    put(ewram,actor-0x02000000+0xAC+0x0E,9,2)
    assert not collision_state(regs,iwram,ewram,rom)["saved_records"][0]["event_in_declared_domain"]
    print("PASS: read-only command boundary, seed successor, original schedule, saved-record/current-P1 discriminator; no emulator/ROM/save I/O")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom",type=Path,nargs="?");parser.add_argument("output",type=Path,nargs="?")
    parser.add_argument("--mgba",type=Path);parser.add_argument("--timeout",type=float,default=240)
    parser.add_argument("--step-mode",choices=("gdb","next-exec"),default="gdb")
    parser.add_argument("--confirm-delay", type=float, choices=(0.0, .25), default=0.0,
                        help="Controlled normal-input variant; does not guarantee the historical random selector")
    parser.add_argument("--self-check",action="store_true")
    args=parser.parse_args()
    if args.self_check:self_check();return
    if args.rom is None or args.output is None or args.mgba is None:parser.error("ROM OUTPUT --mgba EXE are required")
    run(args)


if __name__=="__main__":main()
