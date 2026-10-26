"""Invisible, bounded GDB read-watch experiment; never modifies guest memory."""
import argparse
import json
from pathlib import Path
import struct
from contextlib import ExitStack
import threading
import time

from mgba_headless_gdb_capture import PrivateDesktopProcess, GdbRemote, connect_gdb, sha256
from mgba_capture_provenance import verify_loaded_rom_samples, verify_gdb_owner


def main():
    p = argparse.ArgumentParser()
    p.add_argument('rom', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--mgba', type=Path, required=True)
    p.add_argument('--hits', type=int, default=8)
    first_watch = p.add_mutually_exclusive_group()
    first_watch.add_argument('--exec-address', type=lambda s: int(s, 0))
    first_watch.add_argument('--read-address', type=lambda s: int(s, 0))
    p.add_argument('--exec-kind', type=int, choices=(2, 4), default=4)
    p.add_argument('--first-register-equals', nargs=2, type=lambda s: int(s, 0), metavar=('REGISTER', 'VALUE'))
    p.add_argument('--stop-on-invalid-rom-register', type=int, choices=range(16))
    next_watch = p.add_mutually_exclusive_group()
    next_watch.add_argument('--then-write-address', type=lambda s: int(s, 0))
    next_watch.add_argument('--then-exec-address', type=lambda s: int(s, 0))
    next_watch.add_argument('--then-read-address', type=lambda s: int(s, 0))
    write_stop = p.add_mutually_exclusive_group()
    write_stop.add_argument('--stop-on-zero-write', action='store_true')
    write_stop.add_argument('--stop-on-invalid-rom-callback-write', action='store_true')
    p.add_argument('--timeout', type=float, default=45)
    p.add_argument('--press-start-at', type=float)
    p.add_argument('--press-a-at', type=float, action='append', default=[])
    p.add_argument('--press-b-at', type=float, action='append', default=[])
    p.add_argument('--press-right-at', type=float, action='append', default=[])
    p.add_argument('--press-left-at', type=float, action='append', default=[])
    p.add_argument('--press-down-at', type=float, action='append', default=[])
    a = p.parse_args()
    if a.stop_on_invalid_rom_register is not None and a.exec_address is None:
        p.error('register callback check requires --exec-address')
    if a.first_register_equals is not None and (a.exec_address is None or
            not 0 <= a.first_register_equals[0] <= 16 or
            not 0 <= a.first_register_equals[1] <= 0xFFFFFFFF):
        p.error('first register condition requires an execution address, register 0..16 and uint32 value')
    if (a.stop_on_zero_write or a.stop_on_invalid_rom_callback_write) and a.then_write_address is None:
        p.error('conditional write stop requires --then-write-address')
    if a.timeout <= 0 or a.hits <= 0:
        p.error('--timeout and --hits must be positive')
    a.output.mkdir(parents=True, exist_ok=False)
    report = {'rom_sha256': sha256(a.rom), 'emulator_sha256': sha256(a.mgba),
              'monitor_visible': False, 'guest_writes': [], 'events': [],
              'configuration': {key: str(value) if isinstance(value, Path) else value
                                for key, value in vars(a).items()}}
    def save():
        (a.output / 'probe.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    def valid_rom_callback(value):
        return (any(base <= (value & ~1) < base + a.rom.stat().st_size for base in (0x08000000, 0x0A000000, 0x0C000000))
                and (value & 1 or value % 4 == 0))
    def timeout_snapshot(remote, stop):
        report['bounded_timeout_stop'] = stop
        report['timeout_registers_hex'] = remote.command('g').decode()
        report['timeout_program_counter'] = f"{struct.unpack('<17I', bytes.fromhex(report['timeout_registers_hex']))[15]:08X}"
        report['timeout_native_mode_hex'] = remote.read_memory(0x03002310, 0x20).hex()
        report['timeout_waterfall_phase_mode_hex'] = remote.read_memory(0x03002568, 4).hex()
        report['timeout_memory'] = {}
        for name, address, size in [('iwram', 0x03000000, 0x8000), ('ewram', 0x02000000, 0x40000)]:
            path = a.output / (name + '.bin')
            path.write_bytes(remote.read_memory(address, size))
            report['timeout_memory'][path.name] = {'address': f'{address:08X}', 'size': size, 'sha256': sha256(path)}
        save()
    with PrivateDesktopProcess(a.mgba.resolve(), ['-g', '-C', 'pauseOnMinimize=0',
            '-C', 'pauseOnFocusLost=0', str(a.rom.resolve())], Path.cwd()) as process, ExitStack() as cleanup:
        with connect_gdb(2345, 10, expected_pid=process.pid) as connection:
            remote = GdbRemote(connection)
            report['endpoint'] = verify_gdb_owner(connection, process.pid)
            report['supported'] = remote.command('qSupported').decode()
            report['initial_stop'] = remote.command('?').decode()
            report['loaded_rom_samples'] = verify_loaded_rom_samples(remote, a.rom)
            watches = ([f'0,{a.exec_address:x},{a.exec_kind}'] if a.exec_address else
                       [f'3,{a.read_address:x},4'] if a.read_address is not None else
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
            schedule += [(at, 0x5A) for at in a.press_b_at]
            schedule += [(at, 0x27) for at in a.press_right_at]
            schedule += [(at, 0x25) for at in a.press_left_at]
            schedule += [(at, 0x28) for at in a.press_down_at]
            if a.press_start_at is not None:
                schedule.append((a.press_start_at, 0x0D))
            report['scheduled_inputs'] = schedule
            deadline = time.monotonic() + a.timeout
            for at, key in schedule:
                if at < 0 or at + 0.25 >= a.timeout:
                    raise ValueError('input outside the bounded probe interval')
                for when, pressed in ((at, True), (at + 0.25, False)):
                    timer = threading.Timer(when, process.post_key_state, (key, pressed))
                    timers.append(timer)
                    timer.start()
            connection.settimeout(a.timeout)
            for _ in range(a.hits):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    connection.settimeout(10)
                    timeout_snapshot(remote, remote.command('?').decode())
                    break
                connection.settimeout(remaining)
                remote.start_continue()
                try:
                    stop = remote.receive_packet().decode()
                except TimeoutError:
                    connection.settimeout(10)
                    timeout_snapshot(remote, remote.interrupt().decode())
                    break
                connection.settimeout(10)
                if (a.stop_on_zero_write or a.stop_on_invalid_rom_callback_write) and stop.startswith('T05watch:'):
                    value = int.from_bytes(remote.read_memory(a.then_write_address, 4), 'little')
                    valid_callback = valid_rom_callback(value)
                    skip = value != 0 if a.stop_on_zero_write else valid_callback
                    if skip:
                        key = 'nonzero_writes_skipped' if a.stop_on_zero_write else 'valid_callback_writes_skipped'
                        report[key] = report.get(key, 0) + 1
                        continue
                    report['zero_write_observed' if a.stop_on_zero_write else 'invalid_callback_write_observed'] = True
                    report['observed_callback_word'] = f'{value:08X}'
                registers = remote.command('g').decode()
                words = struct.unpack('<17I', bytes.fromhex(registers))
                if a.stop_on_invalid_rom_register is not None:
                    value = words[a.stop_on_invalid_rom_register]
                    if valid_rom_callback(value):
                        report['valid_register_callbacks_skipped'] = report.get('valid_register_callbacks_skipped', 0) + 1
                        for watch in watches:
                            remote.command('z' + watch)
                        remote.command('s')
                        for watch in watches:
                            remote.command('Z' + watch)
                        continue
                    report['invalid_register_callback_observed'] = True
                event = {'stop': stop, 'registers': [f'{x:08X}' for x in words]}
                report['events'].append(event)
                save()
                for watch in watches:
                    remote.command('z' + watch)
                for name, address, size in [('stack', words[13], 128),
                    ('table', 0x08485000, 60), ('object', words[4], 256),
                    ('presentation', words[5], 0x50), ('renderer_state', 0x030012C8, 8),
                    ('waterfall_phase_mode', 0x03002568, 4)]:
                    if name in ('object', 'presentation') and not 0x02000000 <= address < 0x03008000:
                        continue
                    event[name] = {'address': f'{address:08X}',
                                   'hex': remote.read_memory(address, size).hex()}
                event['asynchronous_stops'] = list(remote.asynchronous_stops)
                if a.read_address is not None or a.then_read_address is not None or report.get('invalid_register_callback_observed'):
                    event['memory'] = {}
                    for name, address, size in [('iwram', 0x03000000, 0x8000), ('ewram', 0x02000000, 0x40000)]:
                        path = a.output / f"event-{len(report['events'])}-{name}.bin"
                        path.write_bytes(remote.read_memory(address, size))
                        event['memory'][path.name] = {'address': f'{address:08X}', 'size': size, 'sha256': sha256(path)}
                if a.then_write_address is not None:
                    event['watched_halfword'] = {
                        'address': f'{a.then_write_address:08X}',
                        'hex': remote.read_memory(a.then_write_address, 2).hex(),
                    }
                save()
                if len(report['events']) == 1 and a.first_register_equals is not None:
                    register, expected = a.first_register_equals
                    report['first_register_condition_met'] = words[register] == expected
                    save()
                    if not report['first_register_condition_met']:
                        break
                if report.get('zero_write_observed') or report.get('invalid_callback_write_observed') or report.get('invalid_register_callback_observed'):
                    break
                if stop.startswith(('S04', 'S0b')):
                    for name, address, size in [('iwram', 0x03000000, 0x8000),
                                                ('ewram', 0x02000000, 0x40000)]:
                        (a.output / (name + '.bin')).write_bytes(remote.read_memory(address, size))
                    break
                event['step_stop'] = remote.command('s').decode()
                save()
                if a.then_write_address is not None:
                    watches = [f'2,{a.then_write_address:x},2']
                elif a.then_exec_address is not None:
                    watches = [f'0,{a.then_exec_address:x},{a.exec_kind}']
                elif a.then_read_address is not None:
                    watches = [f'3,{a.then_read_address:x},4']
                for watch in watches:
                    remote.command('Z' + watch)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
