"""Audit a completed natural v77 6C or 6D gameplay music pause capture."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

import verify_evolution_music_pause_capture as previous
from verify_evolution_music_pause_capture import (
    COLLISION, EXE, INNER, PLAYER, PRIOR, ROM, ROOT, SIZES, STOPPED, SUCCESS, WRAPPED,
    core, fields, flat_inventory, h, need, read, sha, u, unique, word,
)

HOST = 'build/run_evolution_music_three_pause_20261116.py'
OBSERVER = 'tools/bizhawk_probe_evolution_music_three.lua'
PINS = {name: previous.PINS[name] for name in (COLLISION, EXE, INNER, WRAPPED, ROM)}
PINS.update({
    HOST: '9F6B1926F6D4A893346897C3AF01FCCC1DE8222EC3B8739B30B89F55D0E9719B',
    OBSERVER: 'B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881',
    'tools/verify_evolution_music_pause_capture.py': 'E2AEB4A488CF76B47DE758C7BBF0CDC0B1E3357B9E17A1C2F95B549ED3082F91',
    'build/bizhawk-result-v77-20261110-a/trace.txt': previous.PINS['build/bizhawk-result-v77-20261110-a/trace.txt'],
})
HEADERS = {0x6C: 0x08D43CAC, 0x6D: 0x08D47D64}
CHARACTER = {0x6C: 5, 0x6D: 3}
STAGE_SONGS = {*range(0x0F, 0x17), 0x18}
HOOKS = previous.HOOKS | {'stage-selector-queue', 'stage-selector-return'}


def pin_inputs():
    for path, digest in PINS.items():
        need(sha(read(ROOT / path)) == digest, 'immutable input ' + path)


def parse_music(raw):
    lines = raw.decode('utf-8').splitlines()
    need(lines[0] == 'start readonly=true policy=ordinary-target-contact-then-Start-pair '
         'hook_count=16 per_label_limit=32 max_event_rows=576 absence_is_not_coverage=true',
         'reviewed read-only policy')
    event_lines, summary_line, footer = lines[1:-19], lines[-19], lines[-18:]
    need(summary_line.startswith('summary ') and all(line.startswith('count ') for line in footer)
         and all(line.startswith(('event=', 'contact ')) for line in event_lines), 'closed telemetry')
    rows = [fields(line) for line in event_lines if line.startswith('event=')]
    counts = {row['event']: (int(row['observed']), int(row['emitted'])) for row in map(fields, footer)}
    emitted = Counter(row['event'] for row in rows)
    need(counts.keys() == HOOKS and emitted.keys() <= HOOKS
         and all(observed == visible == emitted[label] <= 32 for label, (observed, visible) in counts.items()),
         'all eighteen footer counters and all event rows')
    need(counts['iwram-alias-request'] == counts['iwram-alias-cache'] == (0, 0),
         'zero executions at both canonical IWRAM addresses')
    summary = fields(summary_line)
    cores = [core(fields(line)) for line in event_lines]
    need(cores == sorted(cores) and cores[-1] <= core(summary), 'ordered observed frames')
    return rows, counts, summary, [fields(line) for line in event_lines if line.startswith('contact ')]


def song_headers(rom):
    return {sid: u(rom, 0xD33000 + 8 * sid) for sid in (*STAGE_SONGS, 0x6C, 0x6D)}


def verify_cycle(rows, counts, summary, rom, target):
    headers = song_headers(rom)
    pointer, sounds = (u(rom, raw) - 0x08000000 for raw in (0xD14A8, 0xD14AC))
    need(headers[target] == HEADERS[target]
         and rom[pointer:pointer + 16] == bytes((2, 2, 2, 1, 1, 0, 0, 0, 0, 1, 1, 3, 3, 0, 0, 2)),
         'actual ROM song and selector tables')
    order = lambda *events: all(a < b for a, b in zip(
        [rows.index(row) for row in events], [rows.index(row) for row in events[1:]]))

    def active(row, sid=target):
        return (word(row, 'cache'), word(row, 'player_header')) == (sid, headers[sid])

    def song_start(start, sid):
        at = start['core']
        request = unique(rows, 'music-request', core=at, r8=f'{sid:08X}')
        returned = unique(rows, 'player-zero-start-return', core=at)
        need(order(request, start, returned) and word(start, 'r0') == PLAYER
             and word(start, 'r1') == word(start, 'requested_header') == headers[sid]
             and word(start, 'cache') == sid and active(returned, sid),
             'actual native song start and matching return')
        return [request, start, returned]

    actual_evolution = unique(rows, 'player-zero-start', appended_id=str(target))
    evolution = song_start(actual_evolution, target)
    first = core(actual_evolution) + 1
    queue = unique([row for row in rows if 0 <= core(actual_evolution) - core(row) <= 4],
                   'evolution-queue-return', queue=f'{target:04X}')
    selector = unique(rows, 'evolution-selector', core=queue['core'])
    identity = word(selector, 'actor_identity')
    need(0 <= identity < 16 and identity == word(selector, 'entry_identity')
         and rom[sounds + 2 * rom[pointer + identity]] == target
         and word(queue, 'type') == 4 and word(queue, 'flags') & 0x100
         and order(selector, queue, evolution[0])
         and int(summary[f'starts{target:02X}']) == 1,
         'natural actor and its ROM-derived evolution request')

    chains = {}
    for label, service, lr, begin in (
        ('pause', 'mplay-stop', '0837C36F', first),
        ('resume', 'mplay-resume', '0837C3A3', first + 34),
    ):
        window = [row for row in rows if begin <= core(row) < begin + 4]
        entry = unique(window, label + '-entry')
        compare = unique(window, label + '-header-compare')
        call = unique(window, service, lr=lr)
        need(core(entry) == core(compare) == core(call) and order(entry, compare, call)
             and all(active(row) for row in (entry, compare, call))
             and word(compare, 'r0') == word(compare, 'r1') == headers[target] and compare['equal'] == 'true'
             and word(call, 'r0') == PLAYER, 'native matching pause or resume chain')
        chains[label] = [entry, compare, call]
    boundaries = [unique(rows, 'pause-boundary', age='4'), unique(rows, 'pause-boundary', age='33'),
                  unique(rows, 'resume-boundary', age='38')]
    need([core(row) - first for row in boundaries] == [4, 33, 38]
         and all(active(row) for row in boundaries)
         and [bool(word(row, 'player_status') & STOPPED) for row in boundaries] == [True, True, False]
         and counts['pause-boundary'] == (2, 2) and counts['resume-boundary'] == (1, 1),
         'same header and cache through stopped hold and live resume')
    candidate = [row for row in rows if core(row) > core(boundaries[-1])]
    devolution = unique(candidate, 'devolution-return-site', r4=selector['r4'], stage_music_eligible='true')
    need(active(devolution) and not word(devolution, 'player_status') & STOPPED, 'same actor naturally devolves while playing')

    def stage_queue(queued, sid):
        at = queued['core']
        call = unique(rows, 'stage-selector-queue', core=at, r8=f'{sid:08X}')
        need(order(call, queued) and word(queued, 'type') == 4 and word(queued, 'flags') & 0x100,
             'actual native stage queue and pending flag')
        return [call, queued]

    queued = unique(rows, 'stage-selector-return', core=devolution['core'])
    stage_id = word(queued, 'queue')
    need(stage_id in STAGE_SONGS and active(selector, stage_id), 'restore the actual prior stage music')
    stage_queue_return = stage_queue(queued, stage_id)
    start = unique([row for row in rows if 0 < core(row) - core(devolution) <= 2],
                   'player-zero-start', requested_header=f'{headers[stage_id]:08X}')
    stage = song_start(start, stage_id)
    need(order(devolution, *stage_queue_return, *stage) and core(stage[-1]) + 1 == core(summary)
         and not any(core(actual_evolution) < core(row) < core(start)
                     for row in rows if row['event'] == 'player-zero-start'),
         'eligible devolution directly restores the natural stage track')
    earlier = [row for row in rows[:rows.index(selector)] if row['event'] == 'player-zero-start'
               and word(row, 'requested_header') == headers[stage_id]]
    need(earlier, 'actual pre-evolution stage track start')
    original_stage = song_start(earlier[-1], stage_id)
    earlier_queues = [row for row in rows[:rows.index(original_stage[0])] if row['event'] == 'stage-selector-return'
                      and 0 <= core(original_stage[0]) - core(row) <= 4 and word(row, 'queue') == stage_id]
    need(earlier_queues, 'prior stage track was also queued by native stage selector')
    original_queue = stage_queue(earlier_queues[-1], stage_id)
    return dict(actor=identity, category=rom[pointer + identity], first=first, stage_id=stage_id,
                original_stage_queue=original_queue, original_stage=original_stage, selector=selector,
                evolution_queue=queue, evolution=evolution, pause=chains['pause'], resume=chains['resume'],
                boundaries=boundaries, devolution=devolution, stage_queue=stage_queue_return, stage=stage)


def check_trace(trace, prior, first, last):
    initial = int(fields(trace[0])['initial_core'])
    menu = next(i for i, line in enumerate(trace) if line.startswith('stage=battle-select'))
    need(trace[:menu + 1] == prior[:menu + 1], 'ordinary Korean route through native character selection')
    start = trace.index(f'input relative={first - initial} keys=Start')
    schedule = [line for line in trace[start:] if line.startswith('input ')]
    need(schedule == [f'input relative={first - initial + age} keys={key}'
                      for age, key in ((0, 'Start'), (4, ''), (34, 'Start'), (38, ''))],
         'four Start, thirty neutral, four Start, then neutral')
    snapshots = {row['capture']: row for row in map(fields, trace) if 'capture' in row}
    need(list(snapshots) == ['options-staged', 'options-committed', 'title-committed', 'battle-enter', 'pause-end']
         and core(snapshots['pause-end']) == last and snapshots['pause-end']['timing'] == 'frame-boundary'
         and snapshots['pause-end']['mode'] == '7' and snapshots['pause-end']['tag'] == 'A2',
         'actual final boundary remains in Korean battle')
    summary = fields(trace[-1])
    need(summary['outcome'] == SUCCESS and summary['language'] == '2' and summary['battle'] == 'true'
         and summary['result'] == 'false', 'target closes during gameplay')
    return snapshots, schedule, menu + 1


def audit(directory, song):
    need(directory.parent == ROOT / 'build'
         and re.fullmatch(rf'bizhawk-music-three-{song:02x}-20261116-[a-z]', directory.name),
         'fresh named capture directory')
    pin_inputs()
    inventory = flat_inventory(directory)
    launch = json.loads(read(directory / 'launch.json'))
    alias = 'W:/build/' + directory.name
    need(launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + OBSERVER,
         '--userdata=output:' + alias + f';language:2;target_song:{song};frames:24000;start_frame:2970', alias + '/probe.gba'],
         'exact private target launch arguments')
    need(all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'script_unchanged'))
         and launch['visible'] is False and launch['physical_background_input'] is False
         and launch['guest_writes'] == [] and launch['language'] == 2 and launch['target_song'] == song
         and launch['outcome'] == SUCCESS and read(directory / 'result-done.txt') == SUCCESS.encode('ascii'),
         'completed target gameplay without guest writes')
    for key, name in (('host_sha256', HOST), ('script_sha256', OBSERVER), ('inner_script_sha256', INNER),
                      ('wrapped_script_sha256', WRAPPED), ('base_script_sha256', COLLISION),
                      ('exe_sha256', EXE), ('rom_sha256', ROM)):
        need(launch[key] == PINS[name], 'launch pin ' + key)
    need(launch['files'] == {name: value for name, value in inventory.items() if name != 'launch.json'},
         'all flat capture artifacts independently rehashed')
    cfg = json.loads(read(directory / 'config.json'))
    need(all(cfg[key] is False for key in (
        'SoundEnabled', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'AcceptBackgroundInput')),
        'silent private config with save and state autoload disabled')
    rom = read(directory / 'loaded-rom.bin')
    need(len(rom) == 0x1000000 and rom == read(directory / 'probe.gba') and sha(rom) == PINS[ROM], 'exact 16 MiB C344')
    rows, counts, summary, diagnostics = parse_music(read(directory / 'music-lifetime.txt'))
    proof = verify_cycle(rows, counts, summary, rom, song)
    snapshots, schedule, prefix = check_trace(read(directory / 'trace.txt').decode('utf-8').splitlines(),
        read(PRIOR / 'trace.txt').decode('utf-8').splitlines(), proof['first'], core(summary))
    for name in snapshots:
        for region, length in SIZES.items():
            need(len(read(directory / f'{name}-{region}.bin')) == length, 'whole capture region ' + region)
        need(read(directory / f'{name}.png').startswith(b'\x89PNG\r\n\x1a\n'), 'capture PNG signature')
    iwram = read(directory / 'pause-end-iwram.bin')
    ewram = read(directory / 'pause-end-ewram.bin')
    actor = word(proof['selector'], 'r4')
    offset = actor - 0x02000000
    need(0 <= offset < len(ewram) - 0x11 and ewram[offset + 0x11] == proof['actor'], 'terminal live actor identity')
    side = ewram[offset + 0x10]
    need(side in (0, 1) and actor == u(iwram, 0x489C + 4 * side)
         and iwram[0x231A] == CHARACTER[song] and iwram[0x231A + side * 2] == proof['actor'],
         'actual physical fighter side and native chosen roster ID')
    need(h(iwram, 0x2310) == 7 and u(iwram, 0x4E98) == proof['stage_id']
         and u(iwram, 0x6B40) == song_headers(rom)[proof['stage_id']]
         and iwram[0xBF0:0xDB0] == rom[0x37B33C:0x37B4FC], 'native restored stage state and exact boot copy')
    need(flat_inventory(directory) == inventory, 'protected capture')
    pin_inputs()
    return dict(status='PASS', song=f'{song:02X}', captured_actor_side=side, menu_p1=CHARACTER[song], proof=proof,
                launch=launch, inventory=inventory, inputs=PINS, notifications=counts,
                requested_sound_output_method=3, saved_sound_output_method=cfg['SoundOutputMethod'],
                contact_diagnostics=diagnostics, input_schedule=schedule, initial_trace_prefix_lines=prefix,
                snapshots=snapshots, verifier_sha256=sha(read(Path(__file__))),
                limits='Silent runtime for this target. Both execution counts cover the observed canonical addresses.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--song', choices=('6C', '6D'), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(args.root_completed and not args.report.exists(), 'completed capture and new report required')
    result = audit(args.capture.resolve(), int(args.song, 16))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print('PASS', args.song, sha(read(args.report)))
