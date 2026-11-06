"""Frame-bound ordinary A delivery, then historical full-seed/s/exit control.

Root alone launches runtime. Never changes guest registers, memory or saves.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import threading
import time

from mgba_headless_gdb_capture import GdbRemote, PrivateDesktopProcess, connect_gdb, sha256
from mgba_capture_provenance import verify_gdb_owner, verify_loaded_rom_samples
from probe_collision_original_replay import HISTORICAL, EMULATOR, SEED, EXIT, SEED_REGISTERS, registers, schedule, step_check, collision_state
from probe_collision_preseed import ReadOnlyGdb, prediction

EARLY, LATE = 0x08091088, 0x080910B4
HISTORICAL_WORDS = [0x963C, 0x8B80, 0x31F4]
DEPENDENCIES = {'probe_collision_original_replay.py': 'A1FBA1F31946739A99BFD93424282C4F41A060856CEAB1525B52A24B23227CD9',
                'probe_collision_preseed.py': '3A9348A00561102E9E9770B0738F16BA0C94C120267B999867617CD8E7A7042F'}


def permitted(command):
    return command in ('qSupported', '?', 'g', 'c', 's') or bool(
        re.fullmatch(r'm[0-9a-f]+,[0-9a-f]+', command)
        or re.fullmatch(r'[Zz]0,(?:8091088|80910b4|836d348|8585310),4', command))


class FrameGdb(ReadOnlyGdb):
    def _packet(self, payload):
        command = payload.decode('ascii')
        if not permitted(command):
            raise ValueError('unplanned or guest-write RSP command: ' + command)
        self.journal('rsp-send', payload=command)
        return GdbRemote._packet(payload)


def one_update(before, after, mask):
    return after == [((value + 1) & 0xFFFF) for value in before] and mask == 0x40 and prediction(*after)['stored_12_14_16'] == HISTORICAL_WORDS


def following_inputs():
    return [(at - 55, key) for at, key in schedule() if at > 55]


def run(args, observe_after_seed=None):
    if any(p.suffix.lower() in ('.sav', '.state') for p in (args.rom, args.mgba, args.output)):
        raise ValueError('save/state paths forbidden')
    if sha256(args.rom) != HISTORICAL or sha256(args.mgba) != EMULATOR:
        raise ValueError('exact historical ROM/executable required')
    if not 120 <= args.timeout <= 300:
        raise ValueError('timeout must be120..300 seconds')
    for name, digest in DEPENDENCIES.items():
        if sha256(Path(__file__).with_name(name)) != digest:
            raise ValueError('frozen dependency changed: ' + name)
    image = args.rom.read_bytes()
    if image[0x91088:0x9108C] != bytes.fromhex('0010A0E3') or image[0x910B4:0x910B8] != bytes.fromhex('400010E3'):
        raise ValueError('actual key-latch/menu predicate instructions changed')
    args.output.mkdir(parents=True, exist_ok=False)
    isolated = args.output / 'probe.gba'; shutil.copyfile(args.rom, isolated)
    rows, timers = [], []
    origin = time.monotonic()
    report = {'rom_sha256': HISTORICAL, 'emulator_sha256': EMULATOR, 'tool_sha256': sha256(Path(__file__)),
              'dependencies_sha256': DEPENDENCIES, 'visible': False, 'guest_writes': [], 'timeout': args.timeout,
              'protocol_variant': 'frame-bound-ordinary-menu-A; instrumented, not historical host timing',
              'session_finished': False, 'events': [], 'neutral_menu_updates': 0}

    def journal(kind, **fields):
        rows.append({'time': time.monotonic() - origin, 'kind': kind, **fields})

    def bp(remote, address, add):
        if remote.command(f"{'Z' if add else 'z'}0,{address:x},4") != b'OK':
            raise RuntimeError('breakpoint rejected')

    def stopped(remote, connection, address, deadline, require=True):
        bp(remote, address, True)
        connection.settimeout(max(.01, deadline - time.monotonic()))
        remote.start_continue()
        try:
            stop = remote.receive_packet().decode('ascii')
        except TimeoutError:
            connection.settimeout(10); stop = remote.interrupt().decode('ascii')
        connection.settimeout(10)
        values = registers(remote)
        journal('observed-stop', target=f'{address:08X}', pc=f'{values[15]:08X}')
        bp(remote, address, False)
        if require and values[15] != address:
            raise RuntimeError(f'bounded stop did not reach {address:08X}: {values[15]:08X}/{stop}')
        return values, stop

    def menu_state(remote):
        task = int.from_bytes(remote.read_memory(0x0300133C, 4), 'little')
        if not 0x02000000 <= task <= 0x0203FFE4:
            raise ValueError('unexpected active menu task')
        private = int.from_bytes(remote.read_memory(task + 0x1A, 2), 'little')
        counter = int.from_bytes(remote.read_memory(0x030012B4, 2), 'little')
        return [private, counter]

    def capture(remote, name, values):
        iwram = remote.read_memory(0x03000000, 0x8000)
        ewram = remote.read_memory(0x02000000, 0x40000)
        (args.output / (name + '-iwram.bin')).write_bytes(iwram)
        (args.output / (name + '-ewram.bin')).write_bytes(ewram)
        report['final_collision_state'] = collision_state(values, iwram, ewram, image)
        report['final_memory'] = {'iwram': sha256(args.output / (name + '-iwram.bin')),
                                  'ewram': sha256(args.output / (name + '-ewram.bin'))}

    try:
        with PrivateDesktopProcess(args.mgba.resolve(), ['-g', '-C', 'pauseOnMinimize=0', '-C', 'pauseOnFocusLost=0', str(isolated.resolve())], args.output.resolve()) as process:
            with connect_gdb(2345, 10, expected_pid=process.pid) as connection:
                report['pid'] = process.pid
                report['endpoint'] = verify_gdb_owner(connection, process.pid)
                remote = FrameGdb(connection, journal)
                report['supported'] = remote.command('qSupported').decode('ascii')
                report['initial_stop'] = remote.command('?').decode('ascii')
                report['loaded_rom_samples'] = verify_loaded_rom_samples(remote, isolated)
                epoch = time.monotonic(); deadline = epoch + args.timeout
                report['input_epoch_from_setup_start'] = epoch - origin

                def key(code, pressed, label):
                    windows = process.post_key_state(code, pressed)
                    journal('key-post', key=code, pressed=pressed, label=label,
                            actual_elapsed=time.monotonic() - epoch, windows=windows)
                    return windows

                def later(delay, code, pressed, label):
                    timer = threading.Timer(delay, key, (code, pressed, label)); timers.append(timer); timer.start()

                later(49.5, 13, True, 'original Start'); later(49.75, 13, False, 'original Start')
                current, _ = stopped(remote, connection, LATE, deadline)
                before = None
                for _ in range(600):
                    state = menu_state(remote)
                    if current[0] != 0:
                        raise RuntimeError('menu frame did not latch neutral keys')
                    # Preserve the measured baseline neighborhood, then choose by guest state.
                    if state[1] >= 3291 and prediction(*[((v + 1) & 65535) for v in state])['stored_12_14_16'] == HISTORICAL_WORDS:
                        before = state; break
                    stopped(remote, connection, EARLY, deadline)
                    current, _ = stopped(remote, connection, LATE, deadline)
                    report['neutral_menu_updates'] += 1
                if before is None:
                    raise RuntimeError('bounded menu predicate did not select an input frame')
                report['input_frame_before'] = before
                report['predicted_next'] = prediction(*[((v + 1) & 65535) for v in before])
                report['latched_mask_before'] = current[0]
                report['held_A_posted_windows'] = key(0x58, True, 'frame-gated menu A')
                if report['held_A_posted_windows'] <= 0:
                    raise RuntimeError('ordinary A was not posted to an owned window')
                latched, _ = stopped(remote, connection, EARLY, deadline)
                after = menu_state(remote)
                report['A_release_windows'] = key(0x58, False, 'after observed next latched mask')
                report['input_frame_after'] = after; report['latched_mask_after'] = latched[0]
                report['one_update_delivery'] = one_update(before, after, latched[0])
                if not report['one_update_delivery']:
                    report['outcome'] = 'input-latency-or-seed-prediction-mismatch'
                    capture(remote, 'input-mismatch', latched)
                else:
                    # Anchor remaining ordinary inputs to the actual observed delivery.
                    report['following_inputs_from_delivery'] = following_inputs()
                    for at, code in following_inputs():
                        if observe_after_seed is None or at < 20:
                            later(at, code, True, 'after delivered menu A'); later(at + .25, code, False, 'after delivered menu A')
                    seed, stop = stopped(remote, connection, SEED, deadline)
                    event = {'stop': stop, 'registers': [f'{v:08X}' for v in seed]}; report['events'].append(event)
                    report['seed_registers_equal_original'] = seed == SEED_REGISTERS
                    stored = list(struct.unpack('<3H', remote.read_memory(0x03002322, 6)))
                    snapshot = int.from_bytes(remote.read_memory(0x03004CEE, 2), 'little')
                    report['actual_stored_12_14_16'] = stored; report['pattern_snapshot'] = snapshot
                    report['prediction_matches_actual'] = stored == prediction(*after)['stored_12_14_16'] and snapshot == stored[2] and seed[3] == 2
                    if seed != SEED_REGISTERS or not report['prediction_matches_actual']:
                        report['outcome'] = 'seed-not-comparable'; capture(remote, 'seed-mismatch', seed)
                    else:
                        for name, address, size in (('stack', seed[13], 128), ('table', 0x08485000, 60),
                                ('object', seed[4], 256), ('renderer_state', 0x030012C8, 8), ('waterfall_phase_mode', 0x03002568, 4)):
                            event[name] = {'address': f'{address:08X}', 'hex': remote.read_memory(address, size).hex()}
                        event['step_stop'] = remote.command('s').decode('ascii')
                        successor = registers(remote)
                        halfword = int.from_bytes(remote.read_memory(0x03004CF8, 2), 'little')
                        event['post_step_registers'] = [f'{v:08X}' for v in successor]
                        event['step_check'] = step_check(seed, successor, halfword)
                        if observe_after_seed is None:
                            final, final_stop = stopped(remote, connection, EXIT, deadline, require=False)
                            report['final_stop'] = final_stop; report['final_registers'] = [f'{v:08X}' for v in final]
                            capture(remote, 'final', final)
                            report['outcome'] = ('original-invalid-target-reproduced' if final[15] == final[9] == 0xE28DD00C else
                                                 'original-exit-observed' if final[15] == EXIT else 'bounded-other-state')
                        else:
                            observe_after_seed(remote, connection, deadline, stopped, capture, report, key)
                report['session_finished'] = True
    finally:
        for timer in timers: timer.cancel()
        for timer in timers: timer.join()
        report['journal_entries'] = len(rows)
        (args.output / 'frame-menu.json').write_bytes((json.dumps(report, indent=2) + '\n').encode())
        (args.output / 'rsp-and-input.jsonl').write_bytes(b''.join((json.dumps(row) + '\n').encode() for row in rows))
        if report['session_finished']:
            (args.output / 'frame-menu-done.txt').write_text(report['outcome'], encoding='ascii')
    print(json.dumps({k: report[k] for k in ('outcome', 'one_update_delivery', 'seed_registers_equal_original') if k in report}))


def self_check():
    assert prediction(63647, 3301)['stored_12_14_16'] == HISTORICAL_WORDS
    assert one_update([63646, 3300], [63647, 3301], 0x40)
    for state, mask in (([63648,3302],0x40), ([63647,3300],0x40), ([63647,3301],0), ([63647,3301],0x41)):
        assert not one_update([63646,3300],state,mask)
    assert not one_update([63637,3291], [63638,3292],0x40)  # Same index2, wrong historical RNG triplet.
    assert following_inputs()[0] == (10, 0x58) and len(following_inputs()) == 18
    for value in ('M3002326,2:0200', 'P0=0', 'c8091088', 's836d348', 'Z3,3004cee,2'):
        assert not permitted(value)
    for value in ('c','s','g','m4000130,2','Z0,8091088,4','z0,80910b4,4'):
        assert permitted(value)
    print('PASS: one-update delivery/latched-mask negatives, anchored ordinary inputs and read-only command boundary; no emulator/ROM/save I/O')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', nargs='?', type=Path); parser.add_argument('output', nargs='?', type=Path)
    parser.add_argument('--mgba', type=Path); parser.add_argument('--timeout', type=float, default=240)
    parser.add_argument('--self-check', action='store_true'); args = parser.parse_args()
    if args.self_check: self_check(); return
    if args.rom is None or args.output is None or args.mgba is None: parser.error('ROM OUTPUT --mgba EXE required')
    run(args)


if __name__ == '__main__': main()
