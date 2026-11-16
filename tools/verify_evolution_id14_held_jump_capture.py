"""Audit the ordinary ID14 held-jump baseline and its table-only retest."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re

import verify_evolution_music_three_capture as music
from verify_evolution_event_queue_capture import queue_rows
from verify_evolution_music_pause_capture import (
    COLLISION, EXE, INNER, ROOT, SIZES, SUCCESS, WRAPPED,
    core, fields, flat_inventory, h, need, read, sha, u, unique, word,
)

PROBE = 'tools/bizhawk_probe_evolution_id14_r2.lua'
TARGET = 0x6C
OTHER = {
    'bizhawk_probe_evolution_id14.lua': 'DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B',
    'bizhawk_observe_evolution_event_queue.lua': 'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
    'bizhawk_observe_collision_alignment.lua': 'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C',
}
PINS = {
    **{name: music.PINS[name] for name in (COLLISION, EXE, INNER, WRAPPED, music.OBSERVER)},
    **{'tools/' + name: digest for name, digest in OTHER.items()},
    PROBE: 'A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA',
}
VARIANTS = {
    'b': (
        'build/run_evolution_id14_r2_20261116.py',
        '1CADA94AF659EB8945A23FF2A48F90FD02E89F7074BA2FDEE1C3A6C9A8C85059',
        'build/impmon-evolution-clean15-20261116/component.gba',
        '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8',
    ),
    'c': (
        'build/run_evolution_id14_fixed_20261116.py',
        '0B45B9D60EE3E67E608AAD0CB4E1C19F8A29D54842345C5C81753ECA19A159D7',
        'build/evolution-transition-tables-20261116/component.gba',
        'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1',
    ),
}
BAD = 'failure:pause-target-not-completed'


def folder(slot):
    return ROOT / 'build' / f'bizhawk-id14-evolution-20261116-{slot}'


def inputs(slot):
    host, host_sha, rom, rom_sha = VARIANTS[slot]
    pins = {**PINS, host: host_sha, rom: rom_sha}
    need(all(sha(read(ROOT / path)) == digest for path, digest in pins.items()), 'all exact launch source pins')
    return host, rom, pins


def capture_inputs(directory, slot):
    host, rom_path, pins = inputs(slot)
    found = flat_inventory(directory)
    launch = json.loads(read(directory / 'launch.json'))
    alias = 'W:/build/' + directory.name
    expected_args = ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + PROBE,
                     '--userdata=output:' + alias + ';language:2;target_song:108;frames:24000;start_frame:2970',
                     alias + '/probe.gba']
    need(launch['arguments'] == expected_args and launch['language'] == 2 and launch['target_song'] == TARGET
         and launch['extra_dependency_sha256'] == OTHER and launch['guest_writes'] == []
         and all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'script_unchanged'))
         and all(launch[key] is False for key in ('visible', 'physical_background_input')), 'private ordinary ID14 launch')
    for key, path in (('base_script_sha256', COLLISION), ('exe_sha256', EXE), ('host_sha256', host),
                      ('script_sha256', PROBE), ('inner_script_sha256', INNER), ('wrapped_script_sha256', WRAPPED),
                      ('contact_script_sha256', music.OBSERVER), ('rom_sha256', rom_path)):
        need(launch[key] == pins[path], 'expected launch identity ' + key)
    need(launch['files'] == {name: digest for name, digest in found.items() if name != 'launch.json'},
         'independent fresh inventory matches every flat host artifact')
    config = json.loads(read(directory / 'config.json'))
    need(all(config[key] is False for key in (
        'SoundEnabled', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'AcceptBackgroundInput')),
         'silent private config with save and state autoload disabled')
    rom = read(directory / 'loaded-rom.bin')
    need(len(rom) == 0x1000000 and sha(rom) == pins[rom_path] and rom == read(directory / 'probe.gba'),
         'whole exact loaded and staged ROM')
    outcome = BAD if slot == 'b' else SUCCESS
    need(launch['outcome'] == outcome and read(directory / 'result-done.txt').decode('ascii') == outcome,
         'exact declared gameplay outcome')
    return rom, found, pins, outcome


def trace_and_snapshots(directory, outcome):
    trace = read(directory / 'trace.txt').decode('utf-8').splitlines()
    summary = fields(trace[-1])
    need(summary['outcome'] == outcome and summary['language'] == '2' and summary['battle'] == 'true',
         'native Korean battle route')
    snapshots = {row['capture']: row for row in map(fields, trace) if 'capture' in row}
    expected = ['options-staged', 'options-committed', 'title-committed', 'battle-enter']
    expected += (['result-enter', 'result-plus120', 'result-first-label', 'result-plus300', 'bounded-end']
                 if outcome == BAD else ['pause-end'])
    need(list(snapshots) == expected and all(row['timing'] == 'frame-boundary' for row in snapshots.values()),
         'complete exact frame-boundary capture sequence')
    for name in snapshots:
        for region, size in SIZES.items():
            need(len(read(directory / f'{name}-{region}.bin')) == size, 'whole capture ' + name + ' ' + region)
        need(read(directory / f'{name}.png').startswith(b'\x89PNG\r\n\x1a\n'), 'PNG signature')
    battle = read(directory / 'battle-enter-iwram.bin')
    terminal = expected[-1]
    iwram = read(directory / f'{terminal}-iwram.bin')
    ewram = read(directory / f'{terminal}-ewram.bin')
    first, cpu = (u(iwram, 0x489C + 4 * side) for side in (0, 1))
    need(battle[0x231A] == iwram[0x231A] == 14 and battle[0x231C] == iwram[0x231C] == 1
         and h(battle, 0x2310) == 7
         and first == 0x02011710 and cpu == 0x02011828
         and ewram[0x11720:0x11722] == b'\x00\x0e' and ewram[0x11838:0x1183A] == b'\x01\x01',
         'actual native P1 ID14 and CPU1')
    return trace, snapshots


def read_music(directory, outcome):
    raw = read(directory / 'music-lifetime.txt')
    if outcome == SUCCESS:
        return music.parse_music(raw)[:3]
    lines = raw.decode('utf-8').splitlines()
    need(lines[0] == 'start readonly=true policy=ordinary-target-contact-then-Start-pair '
         'hook_count=16 per_label_limit=32 max_event_rows=576 absence_is_not_coverage=true',
         'frozen read-only telemetry policy')
    event_lines, summary, count_lines = lines[1:-17], fields(lines[-17]), lines[-16:]
    need(all(line.startswith(('event=', 'contact ')) for line in event_lines)
         and all(line.startswith('count ') for line in count_lines), 'complete music telemetry')
    rows = [fields(line) for line in event_lines if line.startswith('event=')]
    counts = {row['event']: (int(row['observed']), int(row['emitted'])) for row in map(fields, count_lines)}
    emitted = Counter(row['event'] for row in rows)
    need(counts.keys() == music.HOOKS - {'pause-boundary', 'resume-boundary'} and emitted.keys() <= counts.keys()
         and all(observed == visible == emitted[label] <= 32 for label, (observed, visible) in counts.items()),
         'every old-route counter retained and verified')
    need([core(row) for row in rows] == sorted(core(row) for row in rows) and core(rows[-1]) < core(summary),
         'ordered native frames with complete terminal footer')
    return rows, counts, summary


def held_starts(trace, before_core):
    initial = int(fields(trace[0])['initial_core'])
    points = [fields(line) for line in trace if line.startswith('input ')]
    holds = []
    for left, right in zip(points, points[1:]):
        start, stop = int(left['relative']), int(right['relative'])
        core_at = start + initial
        if 8200 <= core_at < before_core and 'A' in left.get('keys', '').split(','):
            if 'A' not in right.get('keys', '').split(','):
                holds.append((core_at, start, stop))
    return holds


def baseline(rom, rows, counts, summary, queue, qsummary, trace):
    entry = unique(queue, 'selected-835A1EC', id='14')
    accepted = unique(queue, 'accepted', core=entry['core'], r8='00000004', r9='00000001')
    event = word(entry, 'r0')
    row = u(rom, word(entry, 'p1') - 0x08000000) + event * 16
    need(core(entry) == 8322 and word(entry, 'r8') == 0x0835A210 and word(entry, 'r1') == 14 * 2
         and event == h(rom, 0x35A210 + 2 * 14) == 0xB054 and row == 0x086C89E8
         and rom[row - 0x08000000:row - 0x08000000 + 16] == b'\xff' * 16,
         'actual original ID14 overread derived independently from loaded ROM')
    need(queue.index(entry) < queue.index(accepted) and qsummary['tick04'] == '0'
         and word(accepted, 'lr') == 0x08012918 and word(accepted, 'r0') == 0x04000020
         and accepted['p1'] == entry['p1'] and accepted['r5'] == entry['r5']
         and word(accepted, 'selected') == event
         and word(accepted, 'r1') == word(accepted, 'command') == word(accepted, 'cursor') == 0xFFFFFFFF,
         'same-core malformed event initializer accepts native type-one song 04')
    start04 = unique(rows, 'player-zero-start-return', core='8323', player_header='083820A8', cache='00000004')
    old_stage = unique(rows, 'stage-selector-return', core='4604', queue='0015')
    selector = unique(rows, 'evolution-selector', core='8382', actor_identity='0E', entry_identity='0000000E')
    queued = unique(rows, 'evolution-queue-return', core=selector['core'], queue='006C', type='0004')
    target = unique(rows, 'player-zero-start-return', core='8383', player_header='08D43CAC', cache='0000006C')
    need(queued['r4'] == selector['r4'] == entry['r4'] and word(queued, 'flags') & 0x100
         and word(selector, 'cache') == 4 and selector['player_header'] == start04['player_header']
         and word(selector, 'cache') != word(old_stage, 'queue') and summary['starts6C'] == '1',
         'real ID14 evolution plays 6C after dirtying the known stage cache')
    need(all(counts[name] == (0, 0) for name in
             ('pause-entry', 'pause-header-compare', 'resume-entry', 'resume-header-compare', 'mplay-resume'))
         and not any(fields(line).get('keys') == 'Start' and int(fields(line)['relative']) >= 8200
                     for line in trace if line.startswith('input ')),
         'strict stage baseline admission correctly prevented target pause')
    ending = unique(queue, 'selected-835A558', id='14', r0='00000019', r8='0835A580')
    devolution = unique(rows, 'devolution-return-site', r4=selector['r4'], stage_music_eligible='true')
    restored = unique(rows, 'player-zero-start-return', core=str(core(devolution) + 1),
                      player_header='08385D14', cache='00000015')
    need(core(ending) == 9612 and core(ending) < core(devolution) and ending['r4'] == entry['r4'],
         'natural ground event 25 and unpaused stage restoration')
    jumps = held_starts(trace, core(entry))
    need([(a, b) for _, a, b in jumps] == [(8240, 8260), (8282, 8302)], 'two ordinary twenty-frame A holds')
    return dict(entry=entry, bad_event_row=f'{row:08X}', accepted_type1_04=accepted, installed04=start04,
                selector=selector, evolution_queue=queued, target_start_return=target, ending=ending,
                unpaused_restored_stage=restored, prior_stage=old_stage, ordinary_held_A=jumps)


def fixed(rom, rows, counts, summary, queue, qsummary, trace, snapshots, directory):
    proof = music.verify_cycle(rows, counts, summary, rom, TARGET)
    entry = unique(queue, 'selected-835A1EC', id='14', r0='00000073', r8='08D3F000')
    ending = unique(queue, 'selected-835A558', id='14', r0='00000019')
    need(proof['actor'] == 14 and proof['category'] == 0 and proof['stage_id'] == 0x15
         and proof['selector']['r4'] == entry['r4'] == ending['r4'] == '02011710'
         and word(ending, 'r8') in (0x08D3F01E, 0x08D3F03C)
         and core(entry) < core(proof['selector']) < core(ending) < core(proof['devolution'])
         and qsummary['tick04'] == '0', 'real source-backed ID14 entry 115 and ending 25')
    need(not any(core(entry) <= core(row) <= core(proof['stage'][-1])
                 and ((row['event'] == 'accepted' and word(row, 'r8') == 4)
                      or (row['event'] == 'stack-accepted' and word(row, 'r0') == 4)) for row in queue),
         'no foreign 04 replacement in the watched lifecycle')
    prior_raw = read(folder('b') / 'trace.txt')
    need(sha(prior_raw) == '758E668558D561D2673C72B1A8131EEB4900C3C6B32A0F2E79F6BB5C727C44F6',
         'immutable baseline input witness')
    prior = prior_raw.decode('utf-8').splitlines()
    initial = int(fields(trace[0])['initial_core'])
    through_entry = lambda lines: [line for line in lines if line.startswith('input ')
                                   and int(fields(line)['relative']) <= core(entry) - initial]
    need(through_entry(trace) == through_entry(prior), 'ordinary input identical through entry event')
    _, schedule, _ = music.check_trace(trace, prior, proof['first'], core(summary))
    iwram = read(directory / 'pause-end-iwram.bin')
    ewram = read(directory / 'pause-end-ewram.bin')
    need(core(snapshots['pause-end']) == core(proof['stage'][-1]) + 1
         and h(iwram, 0x2310) == 7 and u(iwram, 0x489C) == 0x02011710
         and ewram[0x11720:0x11722] == b'\x00\x0e' and u(iwram, 0x4E98) == 0x15
         and u(iwram, 0x6B40) == 0x08385D14, 'restored native stage at next Korean battle boundary')
    return dict(cycle=proof, entry=entry, ending=ending, pause_input_schedule=schedule)


def audit(slot):
    directory = folder(slot)
    rom, inventory, pins, outcome = capture_inputs(directory, slot)
    trace, snapshots = trace_and_snapshots(directory, outcome)
    rows, counts, summary = read_music(directory, outcome)
    queue, qsummary = queue_rows(read(directory / 'evolution-event-queue.txt'))
    alignment = read(directory / 'collision-alignment.txt').decode('utf-8').splitlines()
    need(len(alignment) == 2 and alignment[0] ==
         'start readonly=true hooks=4 odd_rows_limit=16 absence_is_not_root_cause=true'
         and re.fullmatch(r'summary metadata=\d+ odd=0 confirmed=0 dispatch=\d+ e5=0', alignment[1]),
         'observed collision coverage only, no alignment or E5 event')
    need(counts['iwram-alias-request'] == counts['iwram-alias-cache'] == (0, 0), 'zero watched alias executions')
    evidence = (baseline(rom, rows, counts, summary, queue, qsummary, trace) if slot == 'b'
                else fixed(rom, rows, counts, summary, queue, qsummary, trace, snapshots, directory))
    need(flat_inventory(directory) == inventory and inputs(slot)[2] == pins, 'protected finished capture and inputs')
    return dict(status='MALFORMED_ID14_ENTRY_OBSERVED' if slot == 'b' else 'PASS', outcome=outcome,
                release_scope='Ordinary Korean ID14 on this loaded ROM only. Silent. E5 remains unreproduced.',
                proof=evidence, snapshots=snapshots, alignment=fields(alignment[1]), queue_summary=qsummary,
                music_summary=summary, notifications=counts, inventory=inventory, inputs=pins,
                verifier_sha256=sha(read(Path(__file__))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--slot', choices=VARIANTS, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(args.root_completed and not args.report.exists(), 'completed capture and fresh report required')
    result = audit(args.slot)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], result['outcome'], sha(read(args.report)))
