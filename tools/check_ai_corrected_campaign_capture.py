"""Independently verify all campaign evidence produced by the DEEE run."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct
from types import FunctionType

from PIL import Image

import check_ai_producer_provenance_capture as ai_replay
import check_type8_corrected_campaign_capture as prior
from check_ai_corrected_campaign import PIN, ROM
from verify_gba_shoot_entry_capture import ROOT, fields, ledger, sha, word


RUN = 'bizhawk-ai-corrected-v82-20261117-a'
WRAPPER = 'tools/bizhawk_probe_ai_corrected_campaign.lua'
HOST = 'F1397304FFEF2CEAAACC4DECEE774CE442A5317FAF101BA0A56F0B70C110706D'
PINSET = 'D7A7625DBEFBD84ACDE7C15F6AE41AF8557659A5A0CE862542943DB873660D7A'
INDEPENDENT = '12F002F22FA470582CBA27EAEC3259A0F8481B23D4007C6AD9584B8D3D27A1F9'


def pinned_scope(function, **bindings):
    return FunctionType(function.__code__, function.__globals__ | bindings, function.__name__)


def launch_binding(directory, host_exit):
    digest, launch = ai_replay.manifest(directory)
    _, reference = ai_replay.manifest(ROOT / 'build' / ai_replay.RUN)
    assert reference['outcome'] == ai_replay.FAIL
    assert launch['phase_kind'] == 'source-ai-corrected-assisted-eleven-encounter-to-healthy-shoot'
    assert host_exit == (0 if launch['outcome'] == prior.SUCCESS else 1)
    assert all(launch[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(launch[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                               'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert sha((ROOT / 'build/run_ai_corrected_v82_20261117.py').read_bytes()) == launch['launcher_sha256'] == HOST
    pins = (ROOT / 'build/ai-corrected-reviewed-pins-20261117.json').read_bytes()
    assert sha(pins) == launch['reviewed_pins_sha256'] == PINSET
    assert launch['pins'] == json.loads(pins) == reference['pins'] | {WRAPPER: PIN}
    assert len(launch['pins']) == 9
    assert {name: sha((ROOT / name).read_bytes()) for name in launch['pins']} == launch['pins']
    independent = ROOT / 'build/ai-corrected-delta-independent-20261117/report.json'
    assert sha(independent.read_bytes()) == INDEPENDENT
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == launch['rom_sha256'] == ROM
    assert rom == (directory / 'probe.gba').read_bytes() == (ROOT / 'build/character-ai-tables-v82-20261117/component.gba').read_bytes()
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == launch['exe_sha256'] == reference['exe_sha256']
    assert launch['guest_writes'] == reference['guest_writes']
    args = [arg.replace(ai_replay.RUN, RUN).replace(ai_replay.WRAPPER, WRAPPER).replace(prior.ROM, ROM)
            for arg in reference['arguments']]
    assert launch['arguments'] == args
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(item['Path'] == f'W:/build/{RUN}/data/{i}' for i, item in enumerate(config['PathEntries']['Paths']))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    generated = {name: value for name, value in launch['files'].items() if name.startswith('data/')}
    assert set(generated) <= {'data/104/probe.SaveRAM'}
    return digest, launch, reference, rom, generated


def campaign_capture(directory, rom, captures, producers, active, hud):
    for row in producers:
        cap = captures[f"campaign-producer-{int(row['progress']):02d}"]
        assert cap['trace']['observed_core'] == row['core'] and cap['trace']['registers'] == 'before-instruction'
        assert (cap['regs']['R4'], cap['regs']['R15']) == (0x03002310, 0x0808B710)
        iw = prior.raw(directory, cap, 'iwram')
        assert (iw[0x231E], iw[0x231C], iw[0x231D], iw[0x232E], iw[0x232F]) == tuple(
            int(row[key]) for key in ('stage', 'cpu', 'cpu_form', 'progress', 'row'))
    visuals = {}
    for row in active:
        number = int(row['progress'])
        cap = captures[f'campaign-active-{number:02d}']
        assert cap['trace']['observed_core'] == cap['trace']['export_core'] == row['core']
        prior.assert_active(cap, row)
        v = prior.visual(directory, cap)
        assert v['clock'] == int(row['clock'])
        if number == 10:
            s = cap['state']
            assert s['aux']['active'] and s['aux']['kind'] == 3
            assert s['p2']['child'] == s['aux_pointer'] and s['aux']['child'] == s['second']
            assert s['aux']['opponent'] == s['first']
        visuals[str(number)] = v
    if '4' in visuals and '5' in visuals:
        iraira, retail = (captures[f'campaign-active-{number:02d}'] for number in (4, 5))
        assert iraira['state']['stage'] == 10 and retail['state']['stage'] == 3
        vram, iw = (prior.raw(directory, iraira, name) for name in ('vram', 'iwram'))
        expected_map = rom[0x59D0C0:0x59D0C0 + 0x3F0]
        assert len(expected_map) == 18 * 56
        map_rows = sum(expected_map[i:i + 56] in vram[0xF000:0xF800] for i in range(0, len(expected_map), 56))
        assert map_rows == 18
        descriptors = [struct.unpack_from('<I', iw, offset)[0] for offset in (0x235C, 0x23AC)]
        assert descriptors == [0x08580480, 0x085804A0]
        tiles = rom[0x2C488:0x30488]
        palette = rom[0x2C32A:0x2C32A + 0xC0]
        tile_matches = []
        palette_matches = []
        for cap in (iraira, retail):
            live_tiles = prior.raw(directory, cap, 'vram')[0x4000:0x8000]
            live_palette = prior.raw(directory, cap, 'palette')[2:0xC2]
            tile_matches.append(sum(tiles[i:i + 32] == live_tiles[i:i + 32] for i in range(0, len(tiles), 32)))
            palette_matches.append(sum(left == right for left, right in zip(palette, live_palette)))
        assert tile_matches == [495, 495] and palette_matches == [69, 192]
        words = struct.unpack('<504H', expected_map)
        visuals['4']['background_evidence'] = dict(
            configured_descriptor_words=[f'{value:08X}' for value in descriptors],
            exact_bg1_rows_from_installed_ROM_map=map_rows, installed_map_rom_address='0859D0C0',
            installed_palette15_map_words=sum(word >> 12 == 15 for word in words),
            installed_FFFF_map_words=words.count(0xFFFF), reused_stage3_tile_slots_exact=tile_matches[0],
            adjacent_stage3_tile_slots_exact=tile_matches[1], captured_palette_vs_reused_static_bytes_exact=palette_matches[0],
            adjacent_stage3_palette_bytes_exact=palette_matches[1])
    hud_samples = {}
    for event in hud:
        progress = int(event['progress'])
        cap = captures[f'campaign-HUD-{progress:02d}']
        assert cap['trace']['observed_core'] == event['core'] and cap['trace']['registers'] == 'before-instruction'
        assert (cap['regs']['R5'], cap['regs']['R15']) == (0x0600E820, 0x080B6058)
        vram = prior.raw(directory, cap, 'vram')
        at = 0xE80E if progress == 9 else 0xE800
        expected = (0x2215, 0x2214, *([0x2201] * 7)) if progress == 9 else struct.unpack_from('<16H', rom, 0xB5FEA)
        actual = struct.unpack_from(f'<{len(expected)}H', vram, at)
        hud_samples[str(progress)] = dict(core=int(event['core']), file=cap['name'] + '.png',
                                          expected=[f'{value:04X}' for value in expected],
                                          outer_frame=[f'{value:04X}' for value in actual],
                                          outer_frame_exact=actual == expected,
                                          native_hook_verified_by_frozen_guard=True)
    return visuals, hud_samples


def authorized_ledger(directory, active, summary, outcome):
    write_path = directory / 'shoot-entry-writes.txt'
    writes, score, boss = ledger(ai_replay.read_lines(write_path) if write_path.is_file() else [])
    assert (int(summary['score_writes']), int(summary['boss_writes']), summary['stage11_writes']) == (score, boss, '0')
    stages = {row['stage']: int(row['core']) for row in active}
    assert all(row['stage'] in stages and int(row['core']) >= stages[row['stage']] - 1 for row in writes)
    if outcome == prior.SUCCESS:
        assert boss == 1 and {int(row['stage']) for row in writes if row['kind'] == 'score'} == set(range(11)) - {7}
    return writes, score, boss


def opt_terminal(directory, loop_trace, outcome, end):
    if outcome != 'bounded-no-activation':
        return None
    row = next(fields(line) for line in loop_trace if line.startswith('capture=bounded-no-hit '))
    assert row['frame'] == end['core'] and row['timing'] == 'frame-boundary'
    assert (directory / 'done.txt').read_text('utf-8').strip() == 'bounded-no-hit'
    regs = dict(line[4:].split('=', 1) for line in loop_trace if line.startswith('reg '))
    assert {'R15', 'CPSR'} <= regs.keys()
    iw = (directory / 'iwram.bin').read_bytes()
    assert (word(iw, 0x2310), iw[0x231E], iw[0x232E], word(iw, 0x4500)) == tuple(
        int(end[name]) for name in ('mode', 'stage', 'progress', 'clock'))
    with Image.open(directory / 'screen.png') as image:
        assert image.size == (240, 160) and image.mode == 'RGB'
        return dict(clock=word(iw, 0x4500), stage=iw[0x231E], progress=iw[0x232E],
                    cpu_registers=regs, screenshot='screen.png', colors=len(image.getcolors(1 << 24)))


def audit(directory, host_exit):
    launch_sha, launch, reference, rom, generated = launch_binding(directory, host_exit)
    outcome = launch['outcome']
    done = prior.SHOOT_SUCCESS if outcome == prior.SUCCESS else outcome
    assert (directory / 'campaign-complete-done.txt').read_text('utf-8').strip() == outcome
    assert (directory / 'shoot-entry-done.txt').read_text('utf-8').strip() == done
    events = pinned_scope(prior.events, ROM=ROM)
    rng, route, producers, active, hud, end = events(directory, rom, outcome)
    captures, trace = prior.capture_rows(directory, launch['files'])
    visuals, hud_samples = campaign_capture(directory, rom, captures, producers, active, hud)
    summary = fields(trace[-1])
    assert summary['outcome'] == done and summary['final_core'] == end['core'] and int(end['relative']) <= 120000
    writes, score, boss = authorized_ledger(directory, active, summary, outcome)
    checkpoint = pinned_scope(prior.checkpoint, RUN=RUN, ROM=ROM)
    boss_state = checkpoint(directory, rom, captures['stage7-checkpoint'], 'stage7-hp1') if 'stage7-checkpoint' in captures else None
    if boss_state:
        assert boss_state['state']['stage'] == 7 and boss_state['state']['P2HP'] == 1
    healthy = pinned_scope(prior.audit_handoff, checkpoint=checkpoint)(directory, rom, captures) if outcome == prior.SUCCESS else None
    failure = None
    if outcome.startswith('failure:'):
        line = ai_replay.read_lines(directory / 'shoot-entry-first-failure.txt')[0]
        assert fields(line)['outcome'] == outcome
        failure = dict(first=line)
        if 'failure-observed.State' in launch['files']:
            failure['checkpoint'] = checkpoint(directory, rom, captures[outcome.removeprefix('failure:')], 'failure-observed')
    assert outcome == prior.SUCCESS or 'healthy-activation.State' not in launch['files']
    loop = ai_replay.read_lines(directory / 'trace.txt')
    terminal = opt_terminal(directory, loop, outcome, end)
    journal = [fields(line) for line in trace if line.startswith('seq=')]
    assert [int(row['seq']) for row in journal] == list(range(int(journal[0]['seq']), int(journal[-1]['seq']) + 1))
    old_name = {name for name in reference['files'] if re.match(r'^\d+-[^/]+\.(?:bin|png)$', name)}
    same_captures = sorted(name for name in old_name if reference['files'][name] == launch['files'].get(name))
    return dict(status='DEEE_CAMPAIGN_CAPTURE_QA_PASS', outcome=outcome, completed_eleven_encounters=outcome == prior.SUCCESS,
                original_host_exit=host_exit, rom_sha256=ROM, launch_sha256=launch_sha, files_verified=len(launch['files']),
                rng_row=rng, source_route=list(route), producer_events=producers, active_owner_events=active,
                hud=hud_samples, visuals=visuals, score_writes=score,
                score_writes_by_stage=Counter(int(item['stage']) for item in writes if item['kind'] == 'score'),
                boss_writes=boss, stage11_writes=0, stage7_checkpoint=boss_state, ledger=writes,
                healthy_activation=healthy, finalized_native_summary=end, terminal_dump=terminal,
                failure=failure, last_native_journal_core=int(journal[-1]['core']),
                exact_snapshot_file_matches_to_75BD=same_captures, supplied_save_used=False,
                isolated_generated_saves=generated, capture_count=len(captures), auditor_started_emulator=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--host-exit', type=int, required=True)
    args = parser.parse_args()
    result = audit(ROOT / 'build' / RUN, args.host_exit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']} {result['outcome']} {sha(args.output.read_bytes())}")
