"""Audit the finalized 3FE5 diagnostic against the unchanged full-campaign prefix."""
import argparse
import json
from pathlib import Path
import re
import struct

import check_ai_aligned_iraira_capture as full
from check_iraira_palette_witness import PIN
from verify_gba_shoot_entry_capture import ROOT, fields, ledger, long, sha, word


RUN = 'bizhawk-iraira-palette-v84-20261117-a'
WRAPPER = 'tools/bizhawk_probe_iraira_palette_witness.lua'
HOST = '30098F3E355A5BFAD11C39BE0E32B144B6E7332C240E7A425F3AA8DA6705520D'
PINSET = '091B716B400CF054B707B490D7A059FC047AD74D8BBB9003D52BCBF66FFB2AF7'
INDEPENDENT = 'A3FCD87544AF16119D14ADB62DB69CDF4D7CE43C71BAA96471805E8C7B7E3829'
REFERENCE = '89D1EBAC7F15C697004AD150239A257A4C928F5EE3126438732ADEBC03C0AB3B'
WITNESS = 'iraira-palette-witness.txt'
DONE = 'palette-witness-121-frames'
BOUNDED = 'bounded-no-activation'
read_lines = full.prior.ai_replay.read_lines


def bind(directory, host_exit):
    assert host_exit == 0, 'wait for the original host to exit with its expected diagnostic outcome'
    root = ROOT / 'build'
    base = root / full.RUN
    previous, ref = full.prior.ai_replay.manifest(base)
    digest, launch = full.prior.ai_replay.manifest(directory)
    assert previous == REFERENCE and ref['outcome'] == full.prior.prior.SUCCESS
    assert launch['phase_kind'] == 'readonly-iraira-palette-producer-121-native-clocks' and launch['outcome'] == DONE
    assert all(launch[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(launch[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                               'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert sha((root / 'run_iraira_palette_v84_20261117.py').read_bytes()) == launch['launcher_sha256'] == HOST
    pin_raw = (root / 'iraira-palette-reviewed-pins-20261117.json').read_bytes()
    assert sha(pin_raw) == launch['reviewed_pins_sha256'] == PINSET
    assert launch['pins'] == json.loads(pin_raw) == ref['pins'] | {WRAPPER: PIN}
    assert len(launch['pins']) == 11
    assert {name: sha((ROOT / name).read_bytes()) for name in launch['pins']} == launch['pins']
    assert sha((root / 'iraira-palette-delta-independent-20261117/report.json').read_bytes()) == INDEPENDENT
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == launch['rom_sha256'] == full.ROM
    assert rom == (directory / 'probe.gba').read_bytes() == (base / 'loaded-rom.bin').read_bytes()
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == launch['exe_sha256'] == ref['exe_sha256']
    assert launch['guest_writes'] == ref['guest_writes']
    assert launch['arguments'] == [arg.replace(full.RUN, RUN).replace(full.WRAPPER, WRAPPER) for arg in ref['arguments']]
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(item['Path'] == f'W:/build/{RUN}/data/{i}' for i, item in enumerate(config['PathEntries']['Paths']))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    assert not any(name.endswith('.State') for name in launch['files'])
    assert {name for name in launch['files'] if name.startswith('data/')} <= {'data/104/probe.SaveRAM'}
    return digest, launch, ref, rom, base


def shared(directory, base, launch, ref):
    assert (directory / 'iraira-palette-witness-done.txt').read_text('utf-8').strip() == DONE
    for name in ('campaign-complete-done.txt', 'shoot-entry-done.txt'):
        assert (directory / name).read_text('utf-8').strip() == BOUNDED
    actual, original = (read_lines(folder / 'campaign-complete-trace.txt') for folder in (directory, base))
    assert actual[:-1] == original[:len(actual)-1]
    end = fields(actual[-1])
    assert (end['outcome'], end['highest'], end['progress'], end['stage'], end['cpu']) == (BOUNDED, '4', '4', '10', '11')
    cap_names = sorted(name for name in launch['files'] if re.match(r'^\d+-[^/]+\.(?:bin|png)$', name))
    assert len(cap_names) == 13*7
    assert all(ref['files'][name] == launch['files'][name] for name in cap_names)
    traces = [full.prior.ai_replay.register_order_only(folder / 'shoot-entry-trace.txt') for folder in (directory, base)]
    captures = [[line for line in trace if line.startswith('capture=')] for trace in traces]
    assert captures[0] == captures[1][:len(captures[0])]
    assert fields(traces[0][-1])['outcome'] == BOUNDED and fields(traces[0][-1])['final_core'] == end['core']
    assert 'failure_checkpoint_saved=false' in traces[0]
    inputs = [read_lines(folder / 'trace.txt') for folder in (directory, base)]
    assert inputs[0] == inputs[1][:len(inputs[0])]
    for name in ('type8-event-provenance.txt', 'ai-producer-provenance.txt', 'iraira-clock-phase.txt'):
        diagnostic, full_run = (read_lines(folder / name) for folder in (directory, base))
        assert fields(diagnostic[0])['core'] == end['core']
        assert diagnostic[1:] == full_run[1:]
    write_file = 'shoot-entry-writes.txt'
    score_lines = read_lines(directory / write_file)
    original_lines = [line for line in read_lines(base / write_file) if int(fields(line)['core']) < int(end['core'])]
    assert score_lines == original_lines
    scores, count, boss = ledger(score_lines)
    assert boss == 0 and int(fields(traces[0][-1])['score_writes']) == count
    assert fields(traces[0][-1])['stage11_writes'] == '0'
    clock = full.checked_clock(directory, True, end['core'])
    return end, clock, dict(exact_snapshot_files=len(cap_names), exact_input_prefix_lines=len(inputs[0]),
                            equivalent_capture_log_lines=len(captures[0]), writes=scores)


def check_dispatch(rom, row):
    assert row['r1'] == '00000003' and row['r8'] == '080D0C38' and row['r9'] == '080D0ED0'
    assert long(rom, 0xD0C38 + 3*4) == int(row['r9'], 16)


def checked_witness(directory, rom, end, clock):
    rows = read_lines(directory / WITNESS)
    header = fields(rows[0])
    assert (header['core'], header['samples'], header['disposition'], header['guest_writes'], header['input']) == (
        end['core'], '121', BOUNDED, 'none', 'frozen-parent')
    counters = [fields(line) for line in rows if line.startswith('count ')]
    counts = {row['kind']: (int(row['total']), int(row['after_first_clock'])) for row in counters}
    assert len(counts) == len(counters)
    assert all(total > 0 and 0 <= after <= total for total, after in counts.values())
    assert sum(total for total, _ in counts.values()) == int(header['serial'])
    front_rows = [fields(line) for line in rows if line.startswith('frontdoor ')]
    assert [int(row['stage']) for row in front_rows] == list(range(12))
    front = {row['stage']: int(row['total']) for row in front_rows}
    assert front['10'] == counts.get('palette-dispatch', (0, 0))[0]
    first = {row['kind']: row for line in rows if line.startswith('first seq=') for row in [fields(line)]}
    ring = [fields(line) for line in rows if line.startswith('seq=')]
    total = int(header['serial'])
    assert [int(row['seq']) for row in ring] == list(range(max(1, total - 255), total + 1))
    assert all(row['kind'] in counts for row in ring) and set(first) == set(counts)
    for row in first.values():
        assert 1 <= int(row['seq']) <= total
    stage = first['legacy-stage-return']
    branch = first['legacy-stage-branch']
    start = first['retail-stage3-handler']
    assert stage['r0'] == '00000003' and stage['pc'] == '080D0BD8'
    assert branch['pc'] == '080D0BE8' and start['pc'] == '080D0ED4'
    assert [int(row['seq']) for row in (stage, branch, start)] == sorted(int(row['seq']) for row in (stage, branch, start))
    check_dispatch(rom, branch)
    changed = {**branch, 'r9': '080D0C58'}
    try:
        check_dispatch(rom, changed)
    except AssertionError:
        pass
    else:
        raise AssertionError('wrong retail dispatch target accepted')
    gradient = first['retail-gradient-backdrop']
    assert gradient['pc'] == '080C9330' and gradient['r8'] == '05000000'
    assert long(rom, 0xC932C) == 0xE1C810B0 and word(rom, 0xC9338) == 0x033D
    writes = [row for row in [*first.values(), *ring] if row['kind'] == 'write-00']
    actual = [row for row in writes if row['pc'] == '080C9334' and row.get('value') == '033D']
    assert actual and all(row['address'] == '05000000' for row in actual)
    samples = [fields(line) for line in rows if line.startswith('sample ')]
    assert [int(row['index']) for row in samples] == list(range(1, 122))
    lo, hi = (int(row['core']) for row in clock['first_and_last_clock'])
    assert [int(row['core']) for row in samples] == list(range(lo, hi+1))
    assert [int(row['clock']) for row in samples] == list(range(7199, 7078, -1))
    assert hi+1 == int(end['core'])
    through_clock = {str(i): sum(row['last_writers'].split(',')[i] != 'none' for row in samples) for i in range(4)}
    return dict(samples=len(samples), first_clock=samples[0], last_clock=samples[-1], frontdoor_by_stage=front,
                counts=counts, legacy_return=stage, legacy_branch=branch, legacy_handler=start,
                actual_palette0_gradient_writes=actual, sampled_last_writer_coverage=through_clock,
                projector_exec_count=counts.get('projector-enter', (0, 0))[0],
                projector_active_count=counts.get('projector-enter', (0, 0))[1],
                all_journals_finalized_at_core=int(end['core']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--host-exit', type=int, required=True)
    args = parser.parse_args()
    directory = ROOT / 'build' / RUN
    digest, launch, ref, rom, base = bind(directory, args.host_exit)
    end, clock, replay = shared(directory, base, launch, ref)
    witness = checked_witness(directory, rom, end, clock)
    result = dict(status='IRAIRA_PALETTE_ACTUAL_WITNESS_QA_PASS', disposition=BOUNDED, launch_sha256=digest,
                  files_verified=len(launch['files']), original_host_exit=args.host_exit, rom_sha256=full.ROM,
                  replay_prefix=replay, window=witness, campaign_completed=False, supplied_save_used=False,
                  auditor_started_emulator=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']} {sha(args.output.read_bytes())}")
