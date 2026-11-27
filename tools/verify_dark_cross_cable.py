"""Replay a real GBA D-ARK menu and link it to a D-Project checkpoint in a second emulator."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from gba_dark_link import Cable, GameBoyAdvance, WonderSwan

MODE = 0x03002310
TASK = 0x0300133C
FRAME_CYCLES = 280896


def advance(gba, frames=1, keys=0):
    gba.set_keys(keys)
    goal = gba.lib.cable_gba_frame() + frames
    while gba.lib.cable_gba_frame() < goal:
        remaining = goal - gba.lib.cable_gba_frame()
        gba.lib.cable_gba_until(gba.lib.cable_gba_clock() + FRAME_CYCLES * remaining)


def enter(gba, fighter=0, settle=120):
    def wait(mode, limit):
        for _ in range(limit):
            if gba.read16(MODE) == mode:
                return
            advance(gba)
        raise RuntimeError(f'Expected mode {mode}, reached {gba.read16(MODE)}')

    def tap(key):
        advance(gba, 3, key)
        advance(gba, 31)

    wait(3, 6200)
    advance(gba, 175)
    tap('Start')
    advance(gba, 142)
    for _ in range(3):
        tap('Down')
    tap('A')
    wait(4, 260)
    if not (gba.read16(MODE + 26) & 2):
        raise ValueError('Character selection did not enter from D-ARK')
    advance(gba, 145)
    order = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 11, 12)
    for _ in order:
        if order[gba.read16(0x0300473C)] == fighter:
            break
        tap('Down')
        advance(gba, 40)
    else:
        raise RuntimeError(f'Fighter {fighter} unavailable')
    advance(gba, 95)
    advance(gba, 3, 'A')
    wait(18, 200)
    advance(gba, settle)


def task(gba):
    ptr = (gba.read16(TASK) | gba.read16(TASK + 2) << 16)
    if not 0x02000000 <= ptr < 0x02040000:
        raise ValueError(f'Invalid D-ARK task {ptr:08X}')
    return ptr + 0x18


def run(a):
    output = a.output
    output.mkdir(parents=True, exist_ok=True)
    gba = GameBoyAdvance(a.gba_core, a.gba)
    try:
        enter(gba, a.fighter, a.settle)
        if a.wait_frames:
            advance(gba, a.wait_frames)
        gba.screen().save(output / 'gba-wait.png')
        context = task(gba)
        if a.disconnected:
            advance(gba, 300)
            assert gba.read16(MODE) == 18 and gba.read16(context + 0x40) & 255 == 0
            advance(gba, 3, 'B')
            advance(gba, 200)
            assert gba.read16(MODE) == 3
            print('PASS: genuine cold boot, D-ARK character selection, wait and cancel')
            return
        ws = WonderSwan(a.ws_core, a.dproject, a.peer_save)
        try:
            if a.state is not None:
                ws.restore(a.state.read_bytes())
            else:
                from prepare_dproject_link_save import play
                play(ws, ['.300,s3,.80,s3,.160,d3,.20,a3,.120,d3,.20,a3,.100',
                          'a3,.40,u3,.40,a3,.100,d3,.25,a3,.80'])
                if int.from_bytes(ws.ram[0x1f44:0x1f46], 'little') != 0x6f21:
                    raise ValueError('D-Project did not reach CONNECTION from its cartridge save')
            ws.frame()
            cable = Cable(gba, ws)
            trace, phases = [], []
            keys = dict((int(f), k) for f, k in json.loads(a.buttons.read_text()) ) if a.buttons else {5:'A', 6:'A', 7:'A'}
            ended = None
            dp_entered = False
            dp_result = None
            gba_hp = []
            dp_hp = []
            dp_result_frame = None
            dp_returned = False
            for frame in range(a.frames):
                ack = dp_result_frame is not None and 60 <= frame - dp_result_frame < 64
                cable.frame(ws_keys=keys.get(frame, 'A' if ack else 0), trace=trace)
                phase = (gba.read16(context + 0x40) & 255) if gba.read16(MODE) == 18 else None
                if int.from_bytes(ws.ram[0x1f44:0x1f46], 'little') == 0x7078:
                    dp_entered = True
                if dp_entered and dp_result is None:
                    hp = tuple(int.from_bytes(ws.ram[i:i + 1], 'little', signed=True) for i in (0x1ef4, 0x1ef5))
                    if not dp_hp or dp_hp[-1][1:] != hp:
                        dp_hp.append((frame, *hp))
                    if min(hp) <= 0:
                        dp_result = 'loss' if hp[0] <= 0 else 'win'
                        ws.screen().save(output / 'dproject-adjudication.png')
                if dp_entered and dp_result_frame is None and bytes.fromhex('D4 D2 00 C0') in ws.ram[0xc00:0x1d20].tobytes():
                    dp_result_frame = frame
                if dp_result_frame is not None and frame == dp_result_frame + 30:
                    ws.screen().save(output / 'dproject-result.png')
                if dp_result_frame is not None and int.from_bytes(ws.ram[0x1f44:0x1f46], 'little') == 0x8110:
                    dp_returned = True
                if phase in (1, 2, 3, 4, 5):
                    pair = gba.read16(context + 0x60).to_bytes(2, 'little')
                    hp = tuple(v - 256 if v >= 128 else v for v in pair)
                    if not gba_hp or gba_hp[-1][1:] != hp:
                        gba_hp.append((frame, *hp))
                if ended is not None and frame == ended + 30:
                    gba.screen().save(output / 'gba-result.png')
                if not phases or phases[-1][1] != phase:
                    phases.append((frame, phase))
                    gba.screen().save(output / f'gba-phase-{phase}.png')
                    ws.screen().save(output / f'dproject-phase-{phase}.png')
                if phase in (4, 5) and ended is None:
                    ended = frame
                    gba_result = 'win' if phase == 4 else 'loss'
                if ended is not None and gba.read16(MODE) == 3 and frame >= ended + 450 and dp_returned:
                    break
            gba.screen().save(output / 'gba-final.png')
            ws.screen().save(output / 'dproject-final.png')
            report = dict(gba_sha256=sha256(a.gba.read_bytes()).hexdigest(),
                          fighter=a.fighter, dproject_sha256=sha256(ws.rom).hexdigest(), phases=phases, returned_to_title=gba.read16(MODE) == 3,
                          gba_result=gba_result if ended is not None else None, dproject_result=dp_result,
                          dproject_result_frame=dp_result_frame, dproject_returned=dp_returned,
                          dproject_entered=dp_entered, dproject_hp=dp_hp, gba_hp=gba_hp, completed_gba_bytes=cable.tx_count, completed_wsc_bytes=cable.rx_count,
                          gba_overruns=cable.overruns, wsc_uart=ws.uart_stats(), trace=trace)
            (output / 'trace.json').write_text(json.dumps(report, indent=2), encoding='utf8')
            if [entry[1:] for entry in gba_hp] != [(remote, local) for _, local, remote in dp_hp]:
                raise RuntimeError('The two cartridges disagree on per-turn hit points')
            if ended is None or cable.tx_count < 8 or cable.rx_count < 8 or cable.overruns or not report['returned_to_title'] or not dp_result or gba_result == dp_result or not dp_returned:
                raise RuntimeError(f'Incomplete cable run: phases {phases}, bytes {cable.tx_count}/{cable.rx_count}')
        finally:
            ws.close()
    finally:
        gba.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('gba-core', 'gba', 'output', 'ws-core', 'dproject', 'state', 'buttons', 'peer-save'):
        p.add_argument('--' + name, type=Path, required=name in ('gba-core', 'gba', 'output'))
    p.add_argument('--settle', type=int, default=120)
    p.add_argument('--wait-frames', type=int, default=0)
    p.add_argument('--fighter', type=int, choices=range(15), default=1)
    p.add_argument('--frames', type=int, default=12000)
    p.add_argument('--disconnected', action='store_true')
    args = p.parse_args()
    if not args.disconnected and (not args.ws_core or not args.dproject or bool(args.state) == bool(args.peer_save)):
        p.error('Connected verification requires both cartridges and exactly one of --state or --peer-save')
    run(args)
