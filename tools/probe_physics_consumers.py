"""Invisible, bounded GDB read-watch experiment; never modifies guest memory."""
import argparse
import json
from pathlib import Path
import struct
from contextlib import ExitStack
import threading

from mgba_headless_gdb_capture import PrivateDesktopProcess, GdbRemote, connect_gdb, sha256
from mgba_capture_provenance import verify_loaded_rom_samples, verify_gdb_owner


def main():
    p = argparse.ArgumentParser()
    p.add_argument('rom', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--mgba', type=Path, required=True)
    p.add_argument('--hits', type=int, default=8)
    p.add_argument('--exec-address', type=lambda s: int(s, 0))
    p.add_argument('--exec-kind', type=int, choices=(2, 4), default=4)
    p.add_argument('--then-write-address', type=lambda s: int(s, 0))
    p.add_argument('--timeout', type=float, default=45)
    p.add_argument('--press-start-at', type=float)
    p.add_argument('--press-a-at', type=float, action='append', default=[])
    p.add_argument('--press-right-at', type=float, action='append', default=[])
    p.add_argument('--press-down-at', type=float, action='append', default=[])
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    report = {'rom_sha256': sha256(a.rom), 'emulator_sha256': sha256(a.mgba),
              'monitor_visible': False, 'guest_writes': [], 'events': [],
              'configuration': {key: str(value) if isinstance(value, Path) else value
                                for key, value in vars(a).items()}}
    def save():
        (a.output / 'probe.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    with PrivateDesktopProcess(a.mgba.resolve(), ['-g', '-C', 'pauseOnMinimize=0',
            '-C', 'pauseOnFocusLost=0', str(a.rom.resolve())], Path.cwd()) as process, ExitStack() as cleanup:
        with connect_gdb(2345, 10, expected_pid=process.pid) as connection:
            remote = GdbRemote(connection)
            report['endpoint'] = verify_gdb_owner(connection, process.pid)
            report['supported'] = remote.command('qSupported').decode()
            report['initial_stop'] = remote.command('?').decode()
            report['loaded_rom_samples'] = verify_loaded_rom_samples(remote, a.rom)
            watches = ([f'0,{a.exec_address:x},{a.exec_kind}'] if a.exec_address else
                       [f'3,{address:x},4' for address in (0x08485030, 0x08485034, 0x08485038)])
            for watch in watches:
                result = remote.command('Z' + watch).decode()
                if result != 'OK':
                    raise RuntimeError(f'read watch unsupported: {result!r}')
            save()
            timers = []
            def stop_inputs():
                for timer in timers:
                    timer.cancel()
                for timer in timers:
                    timer.join()
            cleanup.callback(stop_inputs)
            schedule = [(at, 0x58) for at in a.press_a_at]
            schedule += [(at, 0x27) for at in a.press_right_at]
            schedule += [(at, 0x28) for at in a.press_down_at]
            if a.press_start_at is not None:
                schedule.append((a.press_start_at, 0x0D))
            report['scheduled_inputs'] = schedule
            for at, key in schedule:
                if at < 0 or at + 0.25 >= a.timeout:
                    raise ValueError('input outside the bounded probe interval')
                for when, pressed in ((at, True), (at + 0.25, False)):
                    timer = threading.Timer(when, process.post_key_state, (key, pressed))
                    timers.append(timer)
                    timer.start()
            connection.settimeout(a.timeout)
            for _ in range(a.hits):
                remote.start_continue()
                try:
                    stop = remote.receive_packet().decode()
                except TimeoutError:
                    report['bounded_timeout_stop'] = remote.interrupt().decode()
                    save()
                    break
                registers = remote.command('g').decode()
                words = struct.unpack('<17I', bytes.fromhex(registers))
                event = {'stop': stop, 'registers': [f'{x:08X}' for x in words]}
                report['events'].append(event)
                save()
                for watch in watches:
                    remote.command('z' + watch)
                for name, address, size in [('stack', words[13], 128),
                    ('table', 0x08485000, 60), ('object', words[4], 256),
                    ('presentation', words[5], 0x50), ('renderer_state', 0x030012C8, 8)]:
                    if name in ('object', 'presentation') and not 0x02000000 <= address < 0x03008000:
                        continue
                    event[name] = {'address': f'{address:08X}',
                                   'hex': remote.read_memory(address, size).hex()}
                event['asynchronous_stops'] = list(remote.asynchronous_stops)
                if a.then_write_address is not None:
                    event['watched_halfword'] = {
                        'address': f'{a.then_write_address:08X}',
                        'hex': remote.read_memory(a.then_write_address, 2).hex(),
                    }
                save()
                if stop.startswith(('S04', 'S0b')):
                    for name, address, size in [('iwram', 0x03000000, 0x8000),
                                                ('ewram', 0x02000000, 0x40000)]:
                        (a.output / (name + '.bin')).write_bytes(remote.read_memory(address, size))
                    break
                event['step_stop'] = remote.command('s').decode()
                save()
                if a.then_write_address is not None:
                    watches = [f'2,{a.then_write_address:x},2']
                for watch in watches:
                    remote.command('Z' + watch)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
