"""Audit the finalized 933C assisted campaign stop and its saved boundary."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

from PIL import Image, ImageChops

import verify_gba_shoot_entry_capture_v2 as state
from verify_gba_shoot_entry_capture import fields, ledger, long, sha, snapshot, word


ROOT = Path(__file__).resolve().parents[1]
RUN = 'bizhawk-campaign-complete-v80-20261117-a'
ROM = '933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
OUTCOME = 'failure:first-invalid-producer'
FAILURE = '05-first-invalid-producer'
WRAPPER = 'tools/bizhawk_probe_campaign_complete.lua'
PINS = dict(state.PINS, **{WRAPPER: 'F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF'})
FIXED = {
    'build/run_campaign_complete_v80_20261117.py': '1E18406F7CAC6A8112585FB0839A528CE785BC1B4A35920BAFC528619FEA738B',
    'build/campaign-complete-reviewed-pins-20261117.json': '957B695B9D53BDD406660457CD25FF94E11C531C5B8343318B28EBB112810C5C',
    'local/BizHawk-2.11.1/EmuHawk.exe': 'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD',
    'tools/mgba_headless_gdb_capture.py': 'A3DE346280D736D7B1590D9450DFC901854F11F53EC2615432D594FBDEEAB60E',
    'build/campaign-complete-independent-20261117/final.json': 'AF3F215A2F6F13084BD84F48B443DF9E4A8DAC7C681BA564E934DFE957027ED4',
}


def attest_launch(directory, inventory):
    launch_bytes = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_bytes)
    assert inventory == launch['files'] and len(inventory) == 47
    assert not any(name.startswith('data/') for name in inventory)
    assert launch['outcome'] == OUTCOME
    assert all(launch[key] is True for key in ('completed', 'loaded_rom_exact', 'scripts_unchanged'))
    assert all(launch[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                               'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert launch['phase_kind'] == 'assisted-source-eleven-encounter-to-healthy-shoot'
    assert launch['pins'] == PINS
    assert launch['launcher_sha256'] == FIXED['build/run_campaign_complete_v80_20261117.py']
    assert launch['reviewed_pins_sha256'] == FIXED['build/campaign-complete-reviewed-pins-20261117.json']
    assert launch['exe_sha256'] == FIXED['local/BizHawk-2.11.1/EmuHawk.exe']
    for path, digest in (FIXED | PINS).items():
        assert sha((ROOT / path).read_bytes()) == digest, path
    assert json.loads((ROOT / 'build/campaign-complete-reviewed-pins-20261117.json').read_bytes()) == PINS
    assert launch['rom_sha256'] == ROM
    alias = 'W:/build/' + RUN
    userdata = dict(output=alias, frames=120000, start_frame=2970, combat_profile='approach-jump',
                    probe_sha256=ROM, score_authorization='user-approved-development-score999',
                    boss_authorization='user-approved-development-boss-once-per-stage')
    assert launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + WRAPPER,
                                   '--userdata=' + ';'.join(f'{k}:{v}' for k, v in userdata.items()), alias + '/probe.gba']
    assert launch['guest_writes'] == ['authorized ordinary active FIRST+0x66 WORD=999',
                                      'authorized active stage7 SECOND+0x64 WORD=1 once; actual attack required']
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    for index, entry in enumerate(config['PathEntries']['Paths']):
        assert entry['Path'] == f'{alias}/data/{index}'
    return sha(launch_bytes), userdata


def row_store(before_failure, final_trace):
    before = [line for line in before_failure if line.startswith('seq=')]
    final = [line for line in final_trace if line.startswith('seq=')]
    start = final.index(before[-1])
    assert before[-(start + 1):] == final[:start + 1]
    row = fields(final[start])
    store = fields(final[start + 1])
    assert row == dict(seq='39000', core='8672', kind='producer', pc='08353D24', dst='030048C8',
                       index='0', count='0', type='8070', B='E59F80D4', source_type='FFFFFFFFFFFFFFFF',
                       actor='02011828', selector_A0='1', event='36', command_index='0', command_count='FF05',
                       command_base='1000C', command='1000C', A='0', event_B='0', P1='861CF0C')
    assert store == dict(seq='39001', core='8672', kind='list-type-write', address='030048CC',
                         value='FFFF8070', flags='2000', old='8')
    prior_cpu = fields(next(line for line in before if line.startswith('seq=38989 ')))
    assert [prior_cpu[key] for key in ('core', 'actor', 'event', 'command_count', 'command_base', 'P1')] == [
        '8671', row['actor'], 'C', '2', '861D3D4', row['P1']]
    prior_row = fields(next(line for line in before if line.startswith('seq=38988 ')))
    assert [prior_row[key] for key in ('core', 'address', 'value')] == ['8671', store['address'], '8']
    tail = [fields(line) for line in final[start + 2:]]
    assert [(item['core'], item['kind'], int(item['seq'])) for item in tail] == [
        ('8672', 'producer', 39002), ('8672', 'list-type-write', 39003),
        ('8672', 'producer', 39004), ('8672', 'list-type-write', 39005)]
    assert [item['value'] for item in tail[1::2]] == ['0', '8']
    return row, store, prior_cpu


def audit(directory):
    inventory = {path.relative_to(directory).as_posix(): sha(path.read_bytes())
                 for path in sorted(directory.rglob('*')) if path.is_file() and path.name != 'launch.json'}
    launch_hash, userdata = attest_launch(directory, inventory)
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM
    assert rom == (directory / 'probe.gba').read_bytes()
    assert rom == (ROOT / 'build/campaign-stage-progression-v80-20261117-r2/component.gba').read_bytes()
    for done in ('campaign-complete-done.txt', 'shoot-entry-done.txt'):
        assert (directory / done).read_text('utf-8').strip() == OUTCOME
    for path in ('stage7-hp1.State', 'healthy-activation.State'):
        assert path not in inventory
    campaign = (directory / 'campaign-complete-trace.txt').read_text('utf-8').splitlines()
    assert len(campaign) == 4
    assert campaign[1].startswith('event=producer ') and campaign[2].startswith('event=active-owner ')
    producer, active, end = map(fields, campaign[1:])
    assert [item['core'] for item in (producer, active, end)] == ['3522', '3932', '8673']
    for item in (producer, active, end):
        assert [item[key] for key in ('progress', 'row', 'stage', 'cpu')] == ['0', '2', '8', '13']
    assert end['highest'] == '0' and end['outcome'] == OUTCOME
    pre = (directory / 'shoot-entry-first-failure.txt').read_text('utf-8').splitlines()
    trace = (directory / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    assert pre[0].startswith(f'outcome={OUTCOME} core=8672 timing=before-instruction detail=')
    assert fields(pre[1]) == dict(mode='7', stage='8', difficulty='2', progress='0000',
                                  FIRST='02011710', SECOND='02011828', flags='0000')
    row, store, prior_cpu = row_store(pre, trace)
    assert fields(pre[0].split(' detail=', 1)[1]) == {k: v for k, v in row.items() if k not in ('seq', 'core', 'kind')}
    capture_lines = [line for line in trace if re.match(r'^capture=\S+ observed_core=', line)]
    captures = {fields(line)['capture']: fields(line) for line in capture_lines}
    assert len(captures) == len(capture_lines) == 5
    captured = {name: snapshot(directory, name) for name in captures}
    failure = captures[FAILURE]
    assert [failure[key] for key in ('observed_core', 'export_core', 'registers', 'memory')] == [
        '8672', '8673', 'before-instruction', 'outer-frame-boundary']
    assert {key: failure[key] for key in row if key not in ('seq', 'core', 'kind')} == {
        key: value for key, value in row.items() if key not in ('seq', 'core', 'kind')}
    registers = dict(line[4:].split('=', 1) for line in pre if line.startswith('reg '))
    captured_registers = dict(line.split(' reg ', 1)[1].split('=', 1) for line in trace
                              if line.startswith(f'capture={FAILURE} reg '))
    assert registers == captured_registers and len(registers) == 18
    assert [registers[key] for key in ('R0', 'R1', 'R4', 'R5', 'R14', 'R15', 'CPSR')] == [
        '00008070', '030048C8', 'E59F80D4', '020118D4', '08352850', '08353D28', '40000010']
    assert long(rom, 0x08353D24 - 0x08000000) == 0xE1C100B4  # STRH r0,[r1,#4].
    assert trace[-2] == 'failure_checkpoint_saved=true'
    summary = fields(trace[-1])
    assert [summary[key] for key in ('outcome', 'score_writes', 'boss_writes', 'stage7_consumed',
                                    'stage11_writes', 'initial_core', 'final_core')] == [
        OUTCOME, '2', '0', 'false', '0', '1', '8673']
    writes, scores, bosses = ledger((directory / 'shoot-entry-writes.txt').read_text('utf-8').splitlines())
    assert (scores, bosses) == (2, 0)
    assert [(item['core'], item['before']) for item in writes] == [('3931', '0'), ('6368', '250')]
    for item in writes:
        assert [item[key] for key in ('address', 'stage', 'FIRST', 'SECOND', 'P1HP', 'neighbor_right')] == [
            '02011776', '8', '02011710', '02011828', '8', '96']
    assert captured['03-first-score999']['p1']['score'] == 999
    actors = captured[FAILURE]
    for index, (owner, opponent, point) in enumerate(((actors['first'], actors['second'], actors['p1']),
                                                     (actors['second'], actors['first'], actors['p2']))):
        assert point['active'] and point['hp'] == 8
        assert (point['kind'], point['index'], point['fighter'], point['self'], point['opponent']) == (
            index, index, (0, 13)[index], owner, opponent)
    assert actors['services'] == {
        'input': dict(header=0x02011D88, active=True, callback=0x08374FF4),
        'battle': dict(header=0x02011EA0, active=True, callback=0x083735BC)}
    regions = {name: (directory / f'{FAILURE}-{name}.bin').read_bytes() for name in state.OFFSETS}
    iw, ew = regions['iwram'], regions['ewram']
    assert (long(iw, 0x48C8), word(iw, 0x48CC), word(iw, 0x4D20)) == (0x02011828, 0x8070, 8)
    cpu = 0x11828
    assert (word(ew, cpu+0xA0), word(ew, cpu+0xBA), word(ew, cpu+0xC6), word(ew, cpu+0xC8)) == (1, 0x36, 0, 0xFF05)
    assert tuple(long(ew, cpu+offset) for offset in (0xCC, 0xD0, 0xD4, 0xD8, 0xF0)) == (
        0x1000C, 0x1000C, 0, 0, 0x0861CF0C)
    checkpoint_path = directory / 'failure-observed.State'
    checkpoint = fields((directory / 'failure-observed.txt').read_text('utf-8').strip())
    assert checkpoint['core'] == '8673' and checkpoint['input_relative'] == '8672'
    assert checkpoint['stage7_consumed'] == 'false'
    saved = state.parse_checkpoint(checkpoint_path.read_bytes(), checkpoint, regions, rom)
    with ZipFile(checkpoint_path) as archive:
        sync = json.loads(archive.read('SyncSettings.json'))['o']
        assert 'Nintendo.GBA.MGBAHawk+SyncSettings' in sync['$type'] and sync['SkipBios'] is True
        checkpoint_userdata = json.loads(archive.read('UserData.txt'))['o']
        assert {k: v for k, v in checkpoint_userdata.items() if k != '$type'} == userdata
        with Image.open(BytesIO(archive.read('Framebuffer.bmp'))) as bmp, Image.open(directory / f'{FAILURE}.png') as png:
            assert bmp.size == png.size == (240, 160)
            assert ImageChops.difference(bmp.convert('RGB'), png.convert('RGB')).getbbox() is None
    changed = [line.replace('flags=2000 old=8', 'flags=2000 old=9') if line.startswith('seq=39001 ') else line
               for line in trace]
    try:
        row_store(pre, changed)
    except AssertionError:
        pass
    else:
        raise AssertionError('corrupted bus-write evidence accepted')
    return dict(status='CAMPAIGN_FIRST_INVALID_PRODUCER_CAPTURE_QA_PASS', outcome=OUTCOME,
                launch_sha256=launch_hash, rom_sha256=ROM, file_count=len(inventory), capture_count=len(captures),
                launch_binding=FIXED, reviewed_lua=PINS, campaign_summary=end, write_ledger=writes,
                hook_registers=registers, producer=row, bus_store=store, prior_cpu_producer=prior_cpu,
                boundary=dict(capture=failure, actors=actors, collision_owner='02011828', collision_type='8070',
                              overlap_scratch='0008', checkpoint=saved, embedded_framebuffer_rgb_exact=True,
                              checkpoint_sha256=inventory['failure-observed.State']),
                observer_stop_after_completed_frame=True, later_same_core_valid_store_count=2,
                invalid_overlap_dispatch_observed=False, checkpoint_reloaded_by_auditor=False,
                next_evidence_needed='CPU presentation command selection before the producer hook')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    report = audit(ROOT / 'build' / RUN)
    output = parser.parse_args().output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")
