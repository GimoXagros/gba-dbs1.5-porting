"""Independent audit of the completed 6F CPU Impmon campaign capture."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from verify_evolution_music_pause_capture import (
    COLLISION, EXE, INNER, PLAYER, ROOT, SIZES, STOPPED, SUCCESS, WRAPPED,
    core, fields, flat_inventory, h, need, read, sha, u, unique, word,
)
from verify_evolution_music_three_capture import HOOKS, PINS as BASE_PINS, STAGE_SONGS

HOST = 'build/run_evolution_music_6f_alignment_20261116.py'
OUTER = 'tools/bizhawk_probe_evolution_campaign_alignment_r2.lua'
CONTACT = 'tools/bizhawk_probe_evolution_music_three.lua'
ROM = 'build/impmon-evolution-clean15-20261116/component.gba'
EXTRA = {
    'bizhawk_probe_evolution_music_campaign_r2.lua': '337EBF093EC6591CC8B39A07CB5A33C120453C66B36975CC6E43305B749BF6BD',
    'bizhawk_observe_collision_alignment.lua': 'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C',
}
PINS = {name: BASE_PINS[name] for name in (COLLISION, EXE, INNER, WRAPPED, CONTACT)}
PINS.update({
    HOST: '3C86C6FB7DA03671ED2A9CB0E30A30ACFFC3AC5F0FE01EA5F02D14F042315712',
    OUTER: '049D0E891ED4CD35AAFBCC352FA6A6F6317D0DD6341587CBDFEA215A117BE122',
    ROM: '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8',
    'build/impmon-evolution-clean15-independent-qa-20261116/gate.json': 'D727C5DC1D35E2C743F8C3B8E6D24BC096AFFACBE45172FE078DD5196A250661',
    **{'tools/' + name: digest for name, digest in EXTRA.items()},
})

TARGET = 0x6F
TARGET_HEADER = 0x08D782CC
SCORE_DECLARATION = 'validated live P1 actor+0x66 u16 score=999, maximum512 changes; no HP/mode/stage/unlock writes'


def pin_inputs():
    for name, digest in PINS.items():
        need(sha(read(ROOT / name)) == digest, 'immutable input ' + name)


def active_pool(pointer):
    return 0x02010018 <= pointer <= 0x02010018 + 51 * 0x118 and (pointer - 0x02010018) % 0x118 == 0


def parse_ledger(raw):
    lines = raw.decode('utf-8').splitlines()
    need(lines[0] == 'development_assist=P1-score999-only no_HP_stage_mode_unlock_register_writes=true',
         'exact approved ledger policy')
    writes = [fields(line) for line in lines[1:]]
    need(len(writes) <= 512 and [int(row['write']) for row in writes] == list(range(1, len(writes) + 1)),
         'ordered bounded score ledger')
    for row in writes:
        p, q, address = (word(row, key) for key in ('p1', 'p2', 'address'))
        need(active_pool(p) and active_pool(q) and p != q and address == p + 0x66
             and row['width'] == '2' and row['after'] == '999' and row['before'] != '999'
             and 0 < int(row['hp']) < 0x8000 and 0 < int(row['qhp']) < 0x8000,
             'sole two-byte live P1 score write')
    need([core(row) for row in writes] == sorted({core(row) for row in writes}), 'at most one score write per frame')
    return writes


def parse_music(raw):
    lines = raw.decode('utf-8').splitlines()
    need(lines[0] == ('start readonly=true policy=ordinary-target-contact-then-Start-pair '
         'hook_count=17 per_label_limit=32 max_event_rows=608 absence_is_not_coverage=true'), 'campaign policy')
    items = [fields(line) for line in lines[1:] if line.startswith(('event=', 'campaign '))]
    rows = [row for row in items if 'event' in row]
    campaign = [row for row in items if 'event' not in row]
    need([core(row) for row in items] == sorted(core(row) for row in items), 'ordered music and campaign frames')
    counters = [fields(line) for line in lines if line.startswith('count ')]
    counts = {row['event']: (int(row['observed']), int(row['emitted'])) for row in counters}
    summaries = [fields(line) for line in lines if line.startswith('summary ')]
    need(len(summaries) <= 1 and len(counts) == len(counters), 'unique telemetry footer')
    for row in campaign:
        need(row['difficulty'] == '1' and row['p1id'] == '0' and row['mode'] == '7'
             and row['score'] == '999' and active_pool(word(row, 'p1')) and active_pool(word(row, 'p2')),
             'actual Normal campaign in validated live matchup')
    if counts:
        emitted = Counter(row['event'] for row in rows)
        need(counts.keys() >= HOOKS - {'pause-boundary', 'resume-boundary'}
             and all(visible == emitted[label] == min(32, observed) for label, (observed, visible) in counts.items()),
             'all observed event rows agree with counters and caps')
    return rows, campaign, counts, summaries[0] if summaries else {}


def verify_cycle(rows, counts, summary, rom):
    header = lambda song: u(rom, 0xD33000 + 8 * song)
    map_at, songs_at = (u(rom, at) - 0x08000000 for at in (0xD14A8, 0xD14AC))
    need(header(TARGET) == TARGET_HEADER and rom[map_at + 11] == 3
         and rom[songs_at + 2 * rom[map_at + 11]] == TARGET, 'ROM CPU Impmon song')
    need(int(summary['starts6F']) == 1 and counts['iwram-alias-request'] == counts['iwram-alias-cache'] == (0, 0),
         'one target start and no copied IWRAM executions')
    decision = unique(rows, 'campaign-cpu11-selection', r0='0000000B')
    need(word(decision, 'flags') & 0x60 == 0x60 and not word(decision, 'flags') & 1
         and int(decision['progress']) in (3, 4), 'native clean CPU11 challenge decision')

    def ordered(*items):
        indexes = [rows.index(row) for row in items]
        return indexes == sorted(set(indexes))

    def active(row, song=TARGET):
        return word(row, 'cache') == song and word(row, 'player_header') == header(song)

    natural_start = unique(rows, 'player-zero-start', appended_id=str(TARGET))
    natural_return = unique(rows, 'player-zero-start-return', core=natural_start['core'])
    first = core(natural_start) + 1
    window = [row for row in rows if 0 <= core(natural_start) - core(row) <= 4]
    queued = unique(window, 'evolution-queue-return', queue='006F')
    selector = unique(window, 'evolution-selector', core=queued['core'], entry_identity='0000000B', actor_identity='0B')
    need(core(decision) < core(selector) and ordered(selector, queued, natural_start, natural_return)
         and word(queued, 'type') == 4 and word(queued, 'flags') & 0x100
         and word(natural_start, 'r0') == PLAYER and word(natural_start, 'r1') == TARGET_HEADER
         and word(natural_start, 'cache') == TARGET and active(natural_return), 'ordinary CPU11 actual evolution start')

    chains = {}
    for label, service, lr, begin in (('pause', 'mplay-stop', '0837C36F', first),
                                     ('resume', 'mplay-resume', '0837C3A3', first + 34)):
        window = [row for row in rows if begin <= core(row) < begin + 4]
        entry, compare = (unique(window, event) for event in (label + '-entry', label + '-header-compare'))
        call = unique(window, service, lr=lr)
        need(core(entry) == core(compare) == core(call) and ordered(entry, compare, call)
             and all(active(row) for row in (entry, compare, call))
             and word(compare, 'r0') == word(compare, 'r1') == TARGET_HEADER
             and compare['equal'] == 'true' and word(call, 'r0') == PLAYER, 'one real pause or resume chain')
        chains[label] = [entry, compare, call]
    bounds = [unique(rows, 'pause-boundary', age='4'), unique(rows, 'pause-boundary', age='33'),
              unique(rows, 'resume-boundary', age='38')]
    need([core(row) - first for row in bounds] == [4, 33, 38] and all(active(row) for row in bounds)
         and [bool(word(row, 'player_status') & STOPPED) for row in bounds] == [True, True, False],
         'same header/cache and stopped bit across hold and resume')
    window = [row for row in rows if core(row) > core(bounds[-1])]
    devolution = unique(window, 'devolution-return-site', r4=selector['r4'], stage_music_eligible='true')
    stage_row = unique(rows, 'stage-selector-return', core=devolution['core'])
    stage_song = word(stage_row, 'queue')
    need(stage_song in STAGE_SONGS and active(selector, stage_song) and active(devolution)
         and not word(devolution, 'player_status') & STOPPED and word(stage_row, 'type') == 4
         and word(stage_row, 'flags') & 0x100, 'same CPU naturally returns to prior native stage track')
    stage_entry = unique(rows, 'stage-selector-queue', core=devolution['core'], r8=f'{stage_song:08X}')
    window = [row for row in rows if 0 < core(row) - core(devolution) <= 2]
    stage_start = unique(window, 'player-zero-start', requested_header=f'{header(stage_song):08X}')
    stage_return = unique(rows, 'player-zero-start-return', core=stage_start['core'])
    need(ordered(devolution, stage_entry, stage_row, stage_start, stage_return)
         and word(stage_start, 'r0') == PLAYER and word(stage_start, 'cache') == stage_song
         and active(stage_return, stage_song) and core(stage_return) + 1 == core(summary)
         and not any(core(natural_start) < core(row) < core(stage_start)
                     for row in rows if row['event'] == 'player-zero-start'), 'actual native stage start and return')
    return dict(decision=decision, selector=selector, queued=queued, start=natural_start, first=first,
                pause=chains['pause'], resume=chains['resume'], bounds=bounds, devolution=devolution,
                stage_song=stage_song, stage_queue=stage_row, stage_start=stage_start, stage_return=stage_return)


def audit(directory):
    pin_inputs()
    coverage = flat_inventory(directory)
    launch = json.loads(read(directory / 'launch.json'))
    alias = 'W:/build/' + directory.name
    need(launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + OUTER,
         '--userdata=output:' + alias + ';language:2;target_song:111;frames:60000;start_frame:2970;'
         'score_authorization:user-approved-development-score999', alias + '/probe.gba'],
         'exact private approved campaign launch')
    need(all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'script_unchanged'))
         and launch['visible'] is False and launch['physical_background_input'] is False
         and launch['language'] == 2 and launch['target_song'] == TARGET
         and launch['guest_writes'] == [SCORE_DECLARATION], 'completed private launch and explicit score assist')
    for key, name in (('host_sha256', HOST), ('script_sha256', OUTER), ('inner_script_sha256', INNER),
                      ('wrapped_script_sha256', WRAPPED), ('base_script_sha256', COLLISION),
                      ('contact_script_sha256', CONTACT), ('exe_sha256', EXE), ('rom_sha256', ROM)):
        need(launch[key] == PINS[name], 'launch pin ' + key)
    need(launch['extra_dependency_sha256'] == EXTRA
         and launch['files'] == {name: digest for name, digest in coverage.items() if name != 'launch.json'},
         'all frozen dependencies and flat artifact hashes')
    outcome = read(directory / 'result-done.txt').decode('ascii')
    need(outcome == launch['outcome'] and (outcome == SUCCESS or outcome.startswith('failure:')),
         'preserved actual terminal marker')
    config = json.loads(read(directory / 'config.json'))
    need(all(config[key] is False for key in ('SoundEnabled', 'AutoLoadLastSaveSlot',
         'AutosaveSaveRAM', 'AcceptBackgroundInput')), 'silent private configuration')
    rom = read(directory / 'loaded-rom.bin')
    need(len(rom) == 0x1000000 and rom == read(directory / 'probe.gba') and sha(rom) == PINS[ROM],
         'actual exact 8C72 loaded')
    writes = parse_ledger(read(directory / 'score999-writes.txt'))
    rows, campaign, counts, summary = parse_music(read(directory / 'music-lifetime.txt'))
    alignment_lines = read(directory / 'collision-alignment.txt').decode('utf-8').splitlines()
    need(alignment_lines[-1].startswith('summary '), 'closed read-only alignment journal')
    alignment = fields(alignment_lines[-1])
    trace = read(directory / 'trace.txt').decode('utf-8').splitlines()
    captures = {row['capture']: row for row in map(fields, trace) if 'capture' in row}
    for name in captures:
        need(re.fullmatch(r'round[0-9]+-[a-z0-9-]+', name), 'bounded unique snapshot label')
        for region, length in SIZES.items():
            need(len(read(directory / f'{name}-{region}.bin')) == length, 'complete snapshot ' + region)
        need(read(directory / f'{name}.png').startswith(b'\x89PNG\r\n\x1a\n'), 'valid snapshot signature')
    proof = {}
    if outcome == SUCCESS:
        need(alignment['e5'] == '0', 'no witnessed collision alignment terminal failure')
        proof = verify_cycle(rows, counts, summary, rom)
        need(all(core(row) < proof['first'] for row in writes), 'score assist ends before the target pause')
        first = proof['first'] - int(fields(trace[0])['initial_core'])
        index = trace.index(f'input relative={first} keys=Start')
        need([line for line in trace[index:] if line.startswith('input ')] == [
            f'input relative={first + age} keys={key}' for age, key in ((0, 'Start'), (4, ''), (34, 'Start'), (38, ''))],
            'exact 4/30/4 start schedule ending neutral')
        last = next(name for name in captures if name.endswith('-pause-end'))
        need(core(captures[last]) == core(summary) and captures[last]['mode'] == '7'
             and captures[last]['timing'] == 'frame-boundary' and captures[last]['tag'] == 'A2', 'Korean final battle state')
        iwram, ewram = (read(directory / f'{last}-{region}.bin') for region in ('iwram', 'ewram'))
        actor = word(proof['selector'], 'r4')
        need(active_pool(actor) and actor == u(iwram, 0x48A0)
             and ewram[actor - 0x02000000 + 0x10:actor - 0x02000000 + 0x12] == bytes((1, 11))
             and iwram[0x231A] == 0 and iwram[0x231C] == 11 and iwram[0x2329] & 0x30 == 0,
             'actual CPU Impmon and untouched P1 unlocks in live terminal snapshot')
        stage = proof['stage_song']
        need(h(iwram, 0x2310) == 7 and u(iwram, 0x4E98) == stage
             and u(iwram, 0x6B40) == u(rom, 0xD33000 + stage * 8), 'native stage song restored at terminal boundary')
    need(flat_inventory(directory) == coverage, 'completed capture unchanged')
    pin_inputs()
    return dict(status='PASS' if proof else 'OBSERVED_FAILURE', outcome=outcome, proof=proof,
                launch=launch, inventory=coverage, inputs=PINS, score_writes=writes,
                campaign_diagnostics=campaign, telemetry_summary=summary, counters=counts,
                alignment_summary=alignment, snapshots=captures, verifier_sha256=sha(read(Path(__file__))),
                scope='Isolated 8C72 score-only-assisted gameplay. Not an ordinary score route or complete port claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    directory = args.capture.resolve()
    need(args.root_completed and not args.report.exists() and directory.parent == ROOT / 'build'
         and re.fullmatch(r'bizhawk-music-three-6f-20261116-[a-z]', directory.name),
         'completed known capture and fresh report required')
    result = audit(directory)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], result['outcome'], sha(read(args.report)))
