"""Audit the two completed ordinary ID14 air captures without replaying either."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest().upper()
FIELDS = lambda line: dict(re.findall(r'([A-Za-z_][A-Za-z_0-9]*)=([^\s]+)', line))
OBS = '6F6DF7F2B94030585C80A5302A5D5B2F3394A6F58F96C32A819B97E855BAD7AB'
PINS = {
    'a': ('F5819E91307940E0E1CAB3E04694C39434FA3E515734B2733922303A050F0F5A',
          'build/impmon-evolution-clean15-20261116/component.gba',
          '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8',
          '0835A596', 'FFFFE3A0'),
    'b': ('E0702B0050A4F7CC1C207A20996C0ADA0171710F405794B3C4714BE0007673F7',
          'build/evolution-transition-tables-20261116/component.gba',
          'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1',
          '08D3F03C', '00000019'),
}
COMMON = {
    'tools/bizhawk_probe_evolution_id14_air.lua': OBS,
    'tools/bizhawk_probe_evolution_id14_r2.lua': 'A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA',
    'tools/bizhawk_probe_evolution_id14.lua': 'DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B',
    'tools/bizhawk_probe_evolution_music_three.lua': 'B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881',
    'tools/bizhawk_probe_result_languages.lua': '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
    'tools/bizhawk_probe_result_music_lifetime.lua': 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
    'tools/bizhawk_observe_evolution_event_queue.lua': 'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
    'tools/bizhawk_observe_collision_alignment.lua': 'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C',
}


def lines(directory, name):
    return (directory / name).read_text(encoding='utf-8').splitlines()


def unique(rows, **wanted):
    found = [row for row in rows if all(row.get(key) == value for key, value in wanted.items())]
    assert len(found) == 1, (wanted, found)
    return found[0]


def audit(slot):
    host_sha, rom_path, rom_sha, table, event = PINS[slot]
    directory = ROOT / 'build' / f'bizhawk-id14-air-20261117-{slot}'
    assert directory.is_dir()
    host = ROOT / 'build' / ('run_evolution_id14_air_20261117.py' if slot == 'a'
                             else 'run_evolution_id14_air_fixed_20261117.py')
    assert SHA(host.read_bytes()) == host_sha
    assert SHA((ROOT / rom_path).read_bytes()) == rom_sha
    launch = json.loads((directory / 'launch.json').read_text(encoding='utf-8'))
    flat = {p.name: SHA(p.read_bytes()) for p in directory.iterdir() if p.is_file() and p.name != 'launch.json'}
    assert flat == launch['files'] and not any(name.lower().endswith(('.sav', '.state', '.saveram')) for name in flat)
    assert launch['host_sha256'] == host_sha and launch['script_sha256'] == OBS
    assert launch['rom_sha256'] == rom_sha and launch['guest_writes'] == []
    assert all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'script_unchanged'))
    assert all(launch[key] is False for key in ('visible', 'physical_background_input'))
    assert launch['language'] == 2 and launch['target_song'] == 108
    alias = 'W:/build/' + directory.name
    assert launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json',
                                    '--lua=W:/tools/bizhawk_probe_evolution_id14_air.lua',
                                    '--userdata=output:' + alias + ';language:2;target_song:108;frames:24000;start_frame:2970',
                                    alias + '/probe.gba']
    config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
    assert all(config[key] is False for key in
               ('SoundEnabled', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'AcceptBackgroundInput'))
    loaded = (directory / 'loaded-rom.bin').read_bytes()
    assert len(loaded) == 0x1000000 and SHA(loaded) == rom_sha
    assert loaded == (directory / 'probe.gba').read_bytes()
    assert launch['outcome'] == (directory / 'result-done.txt').read_text().strip()

    music = lines(directory, 'music-lifetime.txt')
    assert music[0].startswith('start readonly=true') and any(row.startswith('summary ') for row in music)
    music_rows = [FIELDS(row) for row in music if row.startswith('event=')]
    trigger = unique(music_rows, event='air-jump-trigger')
    release = unique(music_rows, event='air-jump-release')
    windows = [row for row in music_rows if row.get('event') == 'air-jump-window']
    start, stop = int(trigger['core']), int(release['core'])
    assert len(windows) >= 1 and int(trigger['timer']) in (47, 48)
    assert any(int(row['core']) == start and row['timer'] == trigger['timer']
               and row['actor'] == trigger['actor'] for row in windows)
    assert trigger['actor'] == '02011710' and trigger['callback'] == '0835620C'
    assert int(trigger['flags6'], 16) & 0x61 == 0 and stop - start == 20
    assert not any(row.get('event') == 'air-jump-missed' for row in music_rows)
    trace = lines(directory, 'trace.txt')
    initial = int(FIELDS(trace[0])['initial_core'])
    inputs = [FIELDS(row) for row in trace if row.startswith('input ')]
    held = [(int(left['relative']) + initial, int(right['relative']) + initial)
            for left, right in zip(inputs, inputs[1:])
            if left.get('keys') == 'A' and right.get('keys', '') == '']
    assert (start, stop) in held
    assert FIELDS(trace[-1])['outcome'] == launch['outcome']

    queue = lines(directory, 'evolution-event-queue.txt')
    assert queue[0].startswith('start readonly=true') and queue[-1].startswith('summary ')
    qrows = [FIELDS(row) for row in queue if row.startswith('event=')]
    selected = unique(qrows, event='selected-835A558', id='14')
    assert selected['r4'] == trigger['actor'] and selected['r8'] == table
    assert selected['r0'] == event and int(selected['core']) > stop
    assert selected['r1'] == '0000001C' and selected['p1'] == '0861DB48'
    air_core = int(selected['core'])
    accepted04 = [row for row in qrows if row.get('event') == 'accepted'
                  and row.get('r8') == '00000004' and int(row['core']) == air_core]
    if slot == 'a':
        bad = unique(accepted04, selected='E3A0', command='FFFFFFFF', cursor='FFFFFFFF')
        assert bad['lr'] == '08012918' and bad['r0'] == '04000020'
        assert struct.unpack_from('<H', loaded, 0x35A5B2)[0] == 0xE3A0
        assert launch['outcome'] == 'failure:pause-target-not-completed'
        assert not any(row.get('event') in ('pause-entry', 'mplay-resume') and
                       int(row['core']) >= start for row in music_rows)
    else:
        assert not accepted04 and struct.unpack_from('<H', loaded, 0xD3F058)[0] == 25
        selector = unique(music_rows, event='evolution-selector', actor_identity='0E')
        pause = unique(music_rows, event='pause-entry', player_header='08D43CAC')
        stopped = unique(music_rows, event='mplay-stop', lr='0837C36F', player_header='08D43CAC')
        resume = unique(music_rows, event='resume-entry', player_header='08D43CAC')
        continued = unique(music_rows, event='mplay-resume', lr='0837C3A3', player_header='08D43CAC')
        devolution = unique(music_rows, event='devolution-return-site', r4=trigger['actor'])
        restored = unique(music_rows, event='player-zero-start-return',
                          core=str(int(devolution['core']) + 1),
                          cache='00000015', player_header='08385D14')
        assert int(selector['core']) < int(pause['core']) == int(stopped['core'])
        assert int(pause['core']) < int(resume['core']) == int(continued['core']) < start
        assert air_core < int(devolution['core']) < int(restored['core'])
        assert launch['outcome'] == 'evolution-pause-resume-stage-return'

    collision = lines(directory, 'collision-alignment.txt')
    assert collision[0].startswith('start readonly=true') and collision[-1].startswith('summary ')
    counts = {key: int(value) for key, value in FIELDS(collision[-1]).items()}
    assert counts['metadata'] > 0 and counts['dispatch'] > 0
    assert counts['e5'] == sum('event=e5-before-dispatch' in row for row in collision)
    if counts['e5'] == 0:
        assert counts['odd'] == counts['confirmed'] == 0
    return dict(directory=directory.relative_to(ROOT).as_posix(), files=len(flat) + 1,
                sha256_by_file=flat, launch_sha256=SHA((directory / 'launch.json').read_bytes()),
                outcome=launch['outcome'], jump_core=start, jump_timer=int(trigger['timer']),
                release_core=stop, air_core=air_core, air_table=table, air_event=event,
                same_core_song04=len(accepted04), collision=counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    assert all(SHA((ROOT / path).read_bytes()) == digest for path, digest in COMMON.items())
    results = {slot: audit(slot) for slot in ('a', 'b')}
    report = dict(status='ID14_AIR_PAIR_QA_PASS', source_sha256=COMMON,
                  variants=results, actual_air_branch_both=True,
                  old_malformed_event_and_song04=True, fixed_event25_without_same_core_song04=True,
                  historical_e5_cause_proven=False, emulator_launched_by_auditor=False,
                  old_suite_rerun=False, checker_sha256=SHA(Path(__file__).read_bytes()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], SHA(args.report.read_bytes()))


if __name__ == '__main__':
    main()
