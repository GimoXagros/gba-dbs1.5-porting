"""First invalid overlap-to-scratch producer, with guest-update battle input.

Reuses the exact-triplet ordinary menu/seed protocol; root alone launches.
"""
import argparse
import json
from pathlib import Path
import re
import socket
import time

import probe_collision_frame_menu as frame
from mgba_headless_gdb_capture import GdbRemote, sha256

BASE_SHA = '775D20B23B122A16BF04439CB8C4D65F4F7AF355E4430159856ADB79D9DF3183'
MAIN, MAIN_NEXT, PRODUCER, PRODUCER_NEXT = 0x080002A4, 0x080002A8, 0x0836E370, 0x0836E374


def permitted(command):
    return frame.permitted(command) or bool(re.fullmatch(r'[Zz]0,(?:80002a4|80002a8|836e370|836e374),4', command))


class ProducerGdb(frame.FrameGdb):
    def _packet(self, payload):
        command = payload.decode('ascii')
        if not permitted(command):
            raise ValueError('unplanned or guest-write RSP command: ' + command)
        self.journal('rsp-send', payload=command)
        return GdbRemote._packet(payload)


def battle_inputs():
    events = []
    for seconds, key in frame.following_inputs():
        if seconds >= 20:
            target = round(seconds * 60)
            events.extend(((target, key, True), (target + 15, key, False)))
    return sorted(events)


def observe(remote, connection, deadline, stopped, capture, report, key):
    report['producer_tool_sha256'] = sha256(Path(__file__))
    report['observation'] = 'first invalid overlap type before STRH03004D20; not first list append'
    report['battle_input_clock'] = 'counted actual080002A4 main updates after seed; initial ordinal from prebattle native counter minus observed menu counter'
    report['source_contract'] = '0836E364 LDRH r0,[r4,#4]; E368 actor[r4]->r1; E36C literal03004D20->r8; E370 STRH; saved record handles SP+0C/+10'
    start = (int.from_bytes(remote.read_memory(0x030012B4, 2), 'little') - report['input_frame_after'][1]) & 0xFFFF
    report['initial_main_update_ordinal'] = start
    events = battle_inputs()
    if start >= events[0][0]:
        raise RuntimeError('first guest-update battle input target already passed before observer arm')
    report['battle_input_events'] = events
    ordinal, event_index, overlaps, ring = start, 0, 0, []
    max_updates = start + 12000

    def bp(address, add):
        if remote.command(f"{'Z' if add else 'z'}0,{address:x},4") != b'OK':
            raise RuntimeError('producer breakpoint rejected')

    def finish(reason, regs, stop):
        report['outcome'] = reason
        report['final_stop'] = stop
        report['final_registers'] = [f'{value:08X}' for value in regs]
        report['main_updates_observed'] = ordinal - start
        report['valid_overlap_producers'] = overlaps
        report['last_128_overlap_types'] = ring[-128:]
        if regs[15] == PRODUCER:
            record = regs[4]
            if 0x030048C8 <= record < 0x03004AA8 and (record - 0x030048C8) % 20 == 0:
                report['actual_attack_record_before_scratch_store'] = {
                    'address': f'{record:08X}', 'hex': remote.read_memory(record, 20).hex(),
                    'future_first_writer_watch_address': f'{record + 4:08X}'}
        capture(remote, 'producer-final', regs)

    bp(MAIN, True); bp(PRODUCER, True)
    while True:
        connection.settimeout(max(.01, deadline - time.monotonic()))
        remote.start_continue()
        try:
            stop = remote.receive_packet().decode('ascii')
        except TimeoutError:
            connection.settimeout(10); stop = remote.interrupt().decode('ascii')
        connection.settimeout(10)
        regs = frame.registers(remote)
        pc = regs[15]
        if pc == PRODUCER:
            ring.append({'main_update': ordinal, 'type': regs[0], 'attack_record': f'{regs[4]:08X}',
                         'defense_record': f'{regs[5]:08X}', 'attack_actor': f'{regs[1]:08X}'})
            if len(ring) > 128: ring.pop(0)
            if regs[8] != 0x03004D20:
                finish('unexpected-producer-owner', regs, stop); break
            if regs[0] >= 26:
                finish('first-invalid-overlap-prestore', regs, stop); break
            overlaps += 1
            next_pc = PRODUCER_NEXT
        elif pc == MAIN:
            ordinal += 1
            mode = int.from_bytes(remote.read_memory(0x03002310, 2), 'little')
            counts = list(remote.read_memory(0x03004C4C, 3))
            if any(value > 12 for value in counts[1:]):
                report['invalid_counts_world_command_event'] = counts
                finish('collision-count-outside-12-slots', regs, stop); break
            if mode != 7:
                report['mode_when_first_battle_ended'] = mode
                finish('first-battle-ended-without-invalid-producer', regs, stop); break
            while event_index < len(events) and events[event_index][0] <= ordinal:
                target, button, pressed = events[event_index]
                if key(button, pressed, f'guest-update target{target} observed{ordinal}') <= 0:
                    raise RuntimeError('battle key had no owned window')
                event_index += 1
            if ordinal >= max_updates:
                finish('bounded-12000-main-updates-without-invalid-producer', regs, stop); break
            next_pc = MAIN_NEXT
        else:
            finish('bounded-other-state', regs, stop); break
        # Ordinary continue executes exactly one instruction before rearming.
        bp(pc, False)
        successor, successor_stop = stopped(remote, connection, next_pc, deadline, require=False)
        if successor[15] != next_pc:
            finish('bounded-before-producer-rearm', successor, successor_stop); break
        bp(pc, True)
    for address in (MAIN, PRODUCER): bp(address, False)
    for button in (0x58, 0x27, 0x25): key(button, False, 'producer observer cleanup')


def self_check():
    events = battle_inputs()
    assert events == [(1260,39,True),(1275,39,False),(1500,39,True),(1515,39,False),
                      (1740,39,True),(1755,39,False),(1980,88,True),(1995,88,False),
                      (2160,37,True),(2175,37,False)]
    for command in ('M3004d20,2:e500','P0=e5','c836e370','Z2,30048c8,1e0'):
        assert not permitted(command)
    for command in ('Z0,836e370,4','z0,836e374,4','Z0,80002a4,4','m3004c4c,3'):
        assert permitted(command)
    frame.self_check()
    print('PASS: exact guest-update battle key plan and producer-only read/control boundary; no emulator/ROM/save I/O')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', nargs='?', type=Path); parser.add_argument('output', nargs='?', type=Path)
    parser.add_argument('--mgba', type=Path); parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--self-check', action='store_true'); args = parser.parse_args()
    if args.self_check: self_check(); return
    if args.rom is None or args.output is None or args.mgba is None: parser.error('ROM OUTPUT --mgba EXE required')
    if sha256(Path(frame.__file__)) != BASE_SHA: raise ValueError('frozen shared frame protocol changed')
    frame.FrameGdb = ProducerGdb
    frame.run(args, observe_after_seed=observe)


if __name__ == '__main__': main()
