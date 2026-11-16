"""Check a completed private v77 evolution music pause capture."""
import argparse
from collections import Counter
import json
from pathlib import Path

from verify_result_language_capture import SIZES, fields, h, need, read, sha, u
from verify_result_v76_capture import flat_inventory

ROOT = Path(__file__).resolve().parents[1]
FRESH = ROOT / 'build/bizhawk-music-pause-20261116-a'
PRIOR = ROOT / 'build/bizhawk-result-v77-20261110-a'
HOST = 'build/run_evolution_music_pause_20261116.py'
OUTER = 'tools/bizhawk_probe_evolution_music_pause_r2.lua'
INNER = 'tools/bizhawk_probe_result_music_lifetime.lua'
WRAPPED = 'tools/bizhawk_probe_result_languages.lua'
COLLISION = 'tools/bizhawk_probe_gba_collision.lua'
EXE = 'local/BizHawk-2.11.1/EmuHawk.exe'
ROM = 'build/evolution-music-pause-cache-20261110/component.gba'
PINS = {
    HOST: '9CFAB93DF9F15F558EDFE53D1320F52C41DFBED2F599A5DB5C9C5AD42604F2CB',
    OUTER: '450AE932AA673C2C631A698EB597C48F566587BFCEC97E2A665C81DCE2E4DA51',
    INNER: 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
    WRAPPED: '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
    COLLISION: '7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9',
    EXE: 'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD',
    ROM: 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278',
    'build/result-v77-runtime-qa-20261116/final/ko-audit.json': '19A5D7B9E92E174AD09B65158DE8413127CC627005AA377A8C9F30B4887671D1',
    'build/result-v77-runtime-qa-20261116/final/v76-comparison.json': 'DBD0CC1A55BBD914E9154D9A6AD399BE8A2340F9ACE3CFD1131B2D0040E7D11C',
    'build/bizhawk-result-v77-20261110-a/trace.txt': '9FC08B1C1A21E071AEDF1014F2EAED39D73EE28874BB3B3F89C960FD3B77CA1E',
    'build/bizhawk-result-v77-20261110-a/music-lifetime.txt': '2B7FE19431AE73E0E0DBC5F9F12D8C4B19BC575D506E103751F1A03CA72D750F',
}
HOOKS = {
    'evolution-selector', 'evolution-queue-return', 'music-request', 'player-zero-start',
    'player-zero-start-return', 'devolution-return-site', 'pause-entry', 'resume-entry',
    'pause-header-compare', 'resume-header-compare', 'mplay-stop', 'mplay-resume',
    'iwram-alias-request', 'iwram-alias-cache', 'pause-boundary', 'resume-boundary',
}
PLAYER = 0x03006B40
STOPPED = 0x80000000
SUCCESS = 'evolution-pause-resume-stage-return'


def pin_inputs():
    for name, digest in PINS.items():
        need(sha(read(ROOT / name)) == digest, 'immutable input ' + name)


def core(row):
    return int(row['core'])


def word(row, key):
    return int(row[key], 16)


def unique(rows, event, **values):
    matches = [row for row in rows if row['event'] == event
               and all(row[key] == value for key, value in values.items())]
    need(len(matches) == 1, 'unique ' + event + ' ' + str(values))
    return matches[0]


def rows_and_counts(lines):
    banner = ('start readonly=true policy=ordinary-until-6E-then-Start-pair hook_count=14 '
              'per_label_limit=32 max_event_rows=512 absence_is_not_coverage=true')
    need(lines[0] == banner, 'r2 telemetry policy')
    event_lines, summary_line, count_lines = lines[1:-17], lines[-17], lines[-16:]
    need(summary_line.startswith('summary ') and all(row.startswith('event=') for row in event_lines)
         and all(row.startswith('count ') for row in count_lines), 'ordered events and closed footer')
    rows = [fields(row) for row in event_lines]
    summary = fields(summary_line)
    counts = {row['event']: (int(row['observed']), int(row['emitted'])) for row in map(fields, count_lines)}
    emitted = Counter(row['event'] for row in rows)
    need(counts.keys() == HOOKS and emitted.keys() <= HOOKS and
         all(observed == visible == emitted[label] <= 32 for label, (observed, visible) in counts.items()),
         'every event row visible and all sixteen counters present')
    need([core(row) for row in rows] == sorted(core(row) for row in rows)
         and core(rows[-1]) <= core(summary), 'ordered core frames')
    for label in ('iwram-alias-request', 'iwram-alias-cache'):
        need(counts[label] == (0, 0), 'zero executions at canonical ' + label)
    return rows, counts, summary


def check_sound(rows, counts, summary, rom, first):
    header = {song: u(rom, 0xD33000 + song * 8) for song in (0x6E, 0x10)}
    need(header == {0x6E: 0x08D75728, 0x10: 0x08384BF8}, 'ROM song headers')

    def active(row, song=0x6E):
        return word(row, 'cache') == song and word(row, 'player_header') == header[song]

    selector = unique(rows, 'evolution-selector')
    queue = unique(rows, 'evolution-queue-return')
    need(word(selector, 'actor_identity') == word(selector, 'entry_identity') == 1
         and word(queue, 'queue') == 0x6E and core(selector) == core(queue) == 9075,
         'ordinary actor queues natural evolution')
    need([int(summary['starts' + song]) for song in ('6C', '6D', '6E', '6F')] == [0, 0, 1, 0]
         and int(summary['evolution_entries']) == 1, 'single natural evolution start')

    def song_start(at, song):
        request = unique(rows, 'music-request', core=str(at), r8=f'{song:08X}')
        start = unique(rows, 'player-zero-start', core=str(at), requested_header=f'{header[song]:08X}')
        returned = unique(rows, 'player-zero-start-return', core=str(at))
        need(rows.index(request) < rows.index(start) < rows.index(returned)
             and word(start, 'r0') == PLAYER and word(start, 'r1') == header[song]
             and word(start, 'cache') == song and active(returned, song), 'native song start and return')
        return returned

    evolution = song_start(9076, 0x6E)
    need(first == core(evolution) + 1, 'first Start directly after actual 6E start')
    chains = {}
    for label, service, lr, start_frame in (
        ('pause', 'mplay-stop', '0837C36F', first),
        ('resume', 'mplay-resume', '0837C3A3', first + 34),
    ):
        entry = unique(rows, label + '-entry')
        compare = unique(rows, label + '-header-compare')
        call = unique(rows, service, lr=lr)
        need(start_frame <= core(entry) == core(compare) == core(call) < start_frame + 4
             and rows.index(entry) < rows.index(compare) < rows.index(call)
             and all(active(row) for row in (entry, compare, call))
             and word(compare, 'r0') == word(compare, 'r1') == header[0x6E]
             and word(compare, 'active_header') == word(compare, 'requested_header') == header[0x6E]
             and compare['equal'] == 'true' and word(call, 'r0') == PLAYER,
             'matching same-frame native chain for ' + label)
        chains[label] = [entry, compare, call]

    boundaries = [unique(rows, 'pause-boundary', age='4'), unique(rows, 'pause-boundary', age='33'),
                  unique(rows, 'resume-boundary', age='38')]
    need([core(row) - first for row in boundaries] == [4, 33, 38]
         and all(active(row) for row in boundaries)
         and [bool(word(row, 'player_status') & STOPPED) for row in boundaries] == [True, True, False]
         and counts['pause-boundary'] == (2, 2) and counts['resume-boundary'] == (1, 1),
         'held same header/cache with stopped status, then live resume')
    devolution = unique(rows, 'devolution-return-site')
    need(core(devolution) > core(boundaries[-1]) and devolution['stage_music_eligible'] == 'true'
         and active(devolution) and not word(devolution, 'player_status') & STOPPED,
         'eligible natural devolution after validated resume while evolution music plays')
    stage_requests = [row for row in rows if row['event'] == 'music-request' and word(row, 'r8') == 0x10
                      and 0 < core(row) - core(devolution) <= 2]
    need(len(stage_requests) == 1, 'bounded stage-10 request after natural devolution')
    stage = song_start(core(stage_requests[0]), 0x10)
    need(not any(core(evolution) < core(row) < core(stage) for row in rows if row['event'] == 'player-zero-start'),
         'no player-zero restart before natural stage music return')
    return dict(evolution=evolution, pause=chains['pause'], resume=chains['resume'],
                state_boundaries=boundaries, devolution=devolution, stage_return=stage)


def check_trace(trace, prior, first, last):
    initial = int(fields(trace[0])['initial_core'])
    first_line = f'input relative={first - initial} keys=Start'
    index = trace.index(first_line)
    need(trace[:index] == prior[:index] and prior[index] != first_line, 'same ordinary trace until target input')
    schedule = [line for line in trace[index:] if line.startswith('input ')]
    need(schedule == [f'input relative={first - initial + age} keys={button}'
                      for age, button in ((0, 'Start'), (4, ''), (34, 'Start'), (38, ''))],
         'exact four Start, thirty neutral, four Start, then neutral')
    snapshots = {row['capture']: row for row in map(fields, trace) if 'capture' in row}
    need(list(snapshots) == ['options-staged', 'options-committed', 'title-committed', 'battle-enter', 'pause-end']
         and core(snapshots['pause-end']) == last
         and snapshots['pause-end']['timing'] == 'frame-boundary'
         and snapshots['pause-end']['mode'] == '7' and snapshots['pause-end']['tag'] == 'A2',
         'actual pause-end frame-boundary snapshot in Korean battle')
    summary = fields(trace[-1])
    need(summary['outcome'] == SUCCESS and summary['language'] == '2' and summary['battle'] == 'true'
         and summary['result'] == 'false', 'target capture completes in battle')
    return snapshots, schedule, index


def audit():
    pin_inputs()
    inventory = flat_inventory(FRESH)
    launch = json.loads(read(FRESH / 'launch.json'))
    alias = 'W:/build/' + FRESH.name
    need(launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + OUTER,
         '--userdata=output:' + alias + ';language:2;frames:15000;start_frame:2970', alias + '/probe.gba'],
         'exact private launch arguments')
    need(all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'script_unchanged'))
         and launch['visible'] is False and launch['physical_background_input'] is False
         and launch['guest_writes'] == [] and launch['language'] == 2 and launch['outcome'] == SUCCESS
         and read(FRESH / 'result-done.txt') == SUCCESS.encode('ascii'), 'completed target marker and isolation')
    for key, name in (('host_sha256', HOST), ('script_sha256', OUTER), ('inner_script_sha256', INNER),
                      ('wrapped_script_sha256', WRAPPED), ('base_script_sha256', COLLISION),
                      ('exe_sha256', EXE), ('rom_sha256', ROM)):
        need(launch[key] == PINS[name], 'launch pin ' + key)
    need(launch['files'] == {name: digest for name, digest in inventory.items() if name != 'launch.json'},
         'closed final artifact inventory')
    cfg = json.loads(read(FRESH / 'config.json'))
    need(cfg['SoundOutputMethod'] == 3 and all(cfg[key] is False for key in (
         'SoundEnabled', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'AcceptBackgroundInput')),
         'silent isolated target config')
    rom = read(FRESH / 'loaded-rom.bin')
    need(len(rom) == 0x1000000 and rom == read(FRESH / 'probe.gba') and sha(rom) == PINS[ROM],
         'exact loaded 16 MiB v77 C344 image')
    music = read(FRESH / 'music-lifetime.txt').decode('utf-8').splitlines()
    rows, counts, summary = rows_and_counts(music)
    prior_rows = [line for line in read(PRIOR / 'music-lifetime.txt').decode('utf-8').splitlines()
                  if line.startswith('event=') and core(fields(line)) <= 9076]
    need([line for line in music if line.startswith('event=') and core(fields(line)) <= 9076
          and fields(line)['event'] not in ('mplay-stop', 'mplay-resume')] == prior_rows,
         'original telemetry identical through natural 6E start')
    proof = check_sound(rows, counts, summary, rom, first=9077)
    last = core(summary)
    need(core(proof['stage_return']) + 1 == last, 'capture completes at first boundary after actual stage return')
    snapshots, schedule, prefix = check_trace(read(FRESH / 'trace.txt').decode('utf-8').splitlines(),
        read(PRIOR / 'trace.txt').decode('utf-8').splitlines(), first=9077, last=last)
    for capture in snapshots:
        for region, length in SIZES.items():
            need(len(read(FRESH / f'{capture}-{region}.bin')) == length, 'whole capture region ' + region)
        need(read(FRESH / f'{capture}.png').startswith(b'\x89PNG\r\n\x1a\n'), 'capture PNG signature')
    iwram = read(FRESH / 'pause-end-iwram.bin')
    need(h(iwram, 0x2310) == 7 and u(iwram, 0x4E98) == 0x10 and u(iwram, 0x6B40) == 0x08384BF8
         and iwram[0xBF0:0xDB0] == rom[0x37B33C:0x37B4FC], 'native restored stage state and whole copied ROM span')
    need(flat_inventory(FRESH) == inventory, 'unchanged actual capture artifacts')
    pin_inputs()
    return dict(status='PASS', launch=launch, inventory=inventory, inputs=PINS, proof=proof,
                telemetry_summary=summary, telemetry_counts=counts, input_schedule=schedule,
                identical_ordinary_trace_prefix_lines=prefix, snapshots=snapshots,
                verifier_sha256=sha(read(Path(__file__))),
                limits='Silent target capture for Korean actor 1 and song 6E. The zero counts cover the two canonical IWRAM addresses in this run. Actual audio and complete port coverage are separate.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(args.root_completed and not args.report.exists(), 'completed launch and fresh report required')
    result = audit()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes((json.dumps(result, indent=2) + '\n').encode('utf-8'))
    print('PASS', sha(read(args.report)))
