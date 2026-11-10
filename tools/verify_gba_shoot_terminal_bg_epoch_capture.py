"""Independent completed scalar-telemetry delta audit; exact same-ROM Core comparison."""
import argparse
from collections import Counter
from datetime import datetime
import io
import json
from pathlib import Path
import zipfile

import verify_gba_shoot_terminal_owner_capture as oldqa
import verify_gba_shoot_terminal_bg_epoch_wrapper as wrapperqa

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'build/bizhawk-gba-shoot-terminal-bg-epoch-20261110-a'
OLD = oldqa.D
sha, fields, core, regs, stateqa = oldqa.sha, oldqa.fields, oldqa.core, oldqa.regs, oldqa.stateqa


def audit():
    assert sha(Path(oldqa.__file__).read_bytes()) == 'E2A1BB1E716B709AACE6E6F155BE3B48273E5AAFE19E021A7DBCE1F521A377A4'
    assert sha(Path(wrapperqa.__file__).read_bytes()) == '5214292C4649385FA6F7732C63BC2E7F0E5EF92C8F1A4E0C9A4393BFB2A04B5F'
    report_raw = (ROOT / 'build/gba-shoot-terminal-owner-capture-qa-20261110/report.json').read_bytes()
    assert sha(report_raw) == '324821AF9C2945AF244A90F59DCA13045F1F357268C57829369FF3028426D2D7'
    previous_report = json.loads(report_raw)
    assert sha((ROOT / 'build/gba-shoot-terminal-bg-epoch-wrapper-qa-20261110/report.json').read_bytes()) == 'E52F68CB7BF818DC2E9448470ADEE3532A2B498F29868CBFAE0EF4DCB6482AD1'
    launch_raw = (D / 'launch.json').read_bytes()
    assert sha(launch_raw) == 'ED01EC465717267F3B015E07266BE4DCCAC4FD2A07F2240157341F089CB5B472'
    launch = json.loads(launch_raw)
    assert launch['completed'] and launch['outcome'] == 'failure:bounded-no-completion'
    assert launch['done_text'] == (D / 'shoot-terminal-done.txt').read_text('utf8') == 'failure:bounded-no-completion\n'
    assert not any(launch[k] for k in ('visible', 'physical_background_input', 'supplied_save_used', 'host_stop_requested', 'host_deadline_reached'))
    inventory = {p.relative_to(D).as_posix(): sha(p.read_bytes()) for p in sorted(D.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files'] and len(inventory) == 187
    old_launch_raw = (OLD / 'launch.json').read_bytes()
    assert sha(old_launch_raw) == previous_report['launch_sha256']
    old_launch = json.loads(old_launch_raw)

    def oldfile(name):
        blob = (OLD / name).read_bytes(); assert sha(blob) == old_launch['files'][name]
        return blob

    pins_raw = (ROOT / 'build/gba-shoot-terminal-bg-epoch-pins-20261110.json').read_bytes()
    assert sha(pins_raw) == launch['reviewed_pins_sha256'] == wrapperqa.PINS
    assert launch['pins'] == json.loads(pins_raw)
    for path, digest in launch['pins'].items():
        assert sha((ROOT / path).read_bytes()) == digest
    assert sha((ROOT / 'build/run_gba_shoot_terminal_bg_epoch_20261110.py').read_bytes()) == launch['launcher_sha256'] == wrapperqa.HOST
    rom = (D / 'loaded-rom.bin').read_bytes()
    assert rom == (D / 'probe.gba').read_bytes() == oldfile('loaded-rom.bin') and sha(rom) == oldqa.ROM == launch['rom_sha256']
    assert all(launch[k] for k in ('loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged', 'authorized_write_verified', 'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal'))
    for key in ('source_core_sha256', 'source_rom_sha256', 'restored_core_sha256', 'expected_restored_core_sha256', 'all_Core_byte_differences', 'restored_core_exact_except_current_rom_crc', 'qualification', 'guest_writes_expected', 'guest_write_ledger', 'phase_kind', 'checkpoint_pins'):
        assert launch[key] == old_launch[key]
    assert launch['arguments'] == [s.replace(OLD.name, D.name).replace('bizhawk_probe_gba_shoot_terminal_owner.lua', 'bizhawk_probe_gba_shoot_terminal_bg_epoch.lua') for s in old_launch['arguments']]
    for name in launch['checkpoint_pins']:
        assert (D / 'checkpoint' / name).read_bytes() == oldfile('checkpoint/' + name)
    cfg = json.loads((D / 'config.json').read_bytes())
    previous_cfg = json.loads(oldfile('config.json').decode().replace(OLD.name, D.name).replace('bizhawk_probe_gba_shoot_terminal_owner.lua', 'bizhawk_probe_gba_shoot_terminal_bg_epoch.lua'))
    assert datetime.fromisoformat(cfg['UpdateLastCheckTimeUtc']) > datetime.fromisoformat(previous_cfg['UpdateLastCheckTimeUtc'])
    config_update_times = {'previous': previous_cfg['UpdateLastCheckTimeUtc'], 'current': cfg['UpdateLastCheckTimeUtc']}
    previous_cfg['UpdateLastCheckTimeUtc'] = cfg['UpdateLastCheckTimeUtc']
    assert cfg == previous_cfg, 'onlyreviewedpathsandemulatorupdatechecktimestampdiffer'
    assert (D / 'terminal-write-ledger.txt').read_bytes() == oldfile('terminal-write-ledger.txt')
    lines = (D / 'terminal-trace.txt').read_text('utf8').splitlines()
    telemetry = [s for s in lines if ' kind=bg-epoch ' in s]
    assert [s for s in lines if ' kind=bg-epoch ' not in s] == oldfile('terminal-trace.txt').decode().splitlines()
    assert len(lines) == 351 and len(telemetry) == 20 <= 22
    assert Counter(core(s) for s in telemetry) == {69932: 11, 69933: 9}
    points = ['shake-before', 'shake-after', 'guard', 'guard-return', 'clear-before', 'clear-between', 'clear-after', 'fallback', 'map-call', 'map-before', 'map-after']
    assert [fields(s)['point'] for s in telemetry[:11]] == points
    assert [fields(s)['point'] for s in telemetry[11:]] == points[2:]
    addresses = dict(zip(points, (0x085E716C, 0x085E7170, 0x086FF9C0, 0x086FF698, 0x080D0C18, 0x080D0C1C, 0x080D0C20, 0x080C97B8, 0x08000FEC, 0x08001010, 0x08001014)))
    bysite = {}; scalar_rows = []
    for row in telemetry:
        values, r = fields(row), regs(row); point = values['point']; frame = core(row)
        assert values['first_core'] == '69932' and values['mode'] == '7' and values['stage'] == '11' and int(values['flags'], 16) & 0x400
        assert r['R15'] == addresses[point] + 4 and (frame, point) not in bysite
        bysite[frame, point] = values
        scalar_rows.append(dict(core=frame, point=point, velocities=values['velocities'], map_selector=values['map_selector'], BG0CNT=values['BG0CNT'], BG1CNT=values['BG1CNT'], planned_BG1CNT=values['planned_BG1CNT'], copied=values['copied'], R0=f'{r["R0"]:08X}', PC=f'{r["R15"]:08X}'))
        if point == 'guard-return':
            assert r['R0'] == 0
        if point.startswith('map-'):
            assert r['R0'] == 0x12 and values['planned_BG1CNT'] == '1F03'
        else:
            assert values['planned_BG1CNT'] == 'none'
    zero, shake = '0000,0000,0000,0000', '0000,0200,0000,0000'
    assert bysite[69932, 'shake-before']['velocities'] == zero
    for point in ('shake-after', 'guard', 'guard-return', 'clear-before', 'clear-between'):
        assert bysite[69932, point]['velocities'] == shake
    for point in ('clear-after', 'fallback', 'map-call', 'map-before', 'map-after'):
        assert bysite[69932, point]['velocities'] == zero
    assert all(v['velocities'] == zero for (frame, _), v in bysite.items() if frame == 69933)
    assert bysite[69932, 'map-call']['map_selector'] == '21' and bysite[69932, 'map-before']['map_selector'] == '12'
    assert bysite[69932, 'map-before']['BG1CNT'] == '1E03' and bysite[69932, 'map-after']['BG1CNT'] == '1F03'
    assert bysite[69933, 'guard']['BG1CNT'] == '1F03'
    for frame, reason in ((69932, 'BG-velocity'), (69933, 'hardware-BG-mapping')):
        guard = next(s for s in telemetry if core(s) == frame and fields(s)['point'] == 'guard')
        returned = next(s for s in telemetry if core(s) == frame and fields(s)['point'] == 'guard-return')
        refusal = next(s for s in lines if core(s) == frame and ' kind=guard-refusal ' + reason + ' ' in s)
        assert lines.index(guard) < lines.index(refusal) < lines.index(returned)
    captures = oldqa.event(lines, 'capture'); assert len(captures) == 19 and len(list(D.glob('*.State'))) == 20
    snapshots = {}; exact_cores = []
    for path in sorted(D.glob('*.State')):
        actual_core, _ = stateqa.checkpoint_core(path.read_bytes())
        previous_core, _ = stateqa.checkpoint_core(oldfile(path.name))
        assert actual_core == previous_core, 'exact whole Core without normalization:' + path.name
        exact_cores.append(dict(name=path.stem, sha256=sha(actual_core)))
        with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as z:
            assert z.testzip() is None
            args = json.loads(z.read('UserData.txt'))['o']
            assert args['output'] == 'W:/build/' + D.name and args['checkpoint_dir'] == args['output'] + '/checkpoint'
            assert args['probe_sha256'] == oldqa.ROM and args['boss_authorization'] == 'user-approved-development-boss-once-per-stage'
            assert set(args) == {'$type', 'output', 'checkpoint_dir', 'probe_sha256', 'boss_authorization'}
    for row in captures:
        c = fields(row); name = c['name']; frame = int(c['export_core'])
        regions = {k: (D / f'{name}-{k}.bin').read_bytes() for k in stateqa.OFFSETS}
        for k, blob in regions.items():
            assert blob == oldfile(f'{name}-{k}.bin')
        snapshots[name] = stateqa.parse_checkpoint((D / f'{name}.State').read_bytes(), oldqa.prior.oldqa.helpers.metadata(regions['iwram'], regions['ewram'], frame), regions, rom)
        assert (D / f'{name}.png').read_bytes() == oldfile(f'{name}.png')
        assert (D / f'{name}-display.bin').read_bytes() == oldfile(f'{name}-display.bin')
    failure = (D / 'terminal-first-failure.txt').read_text('utf8').splitlines()
    assert failure[0] == 'failure:bounded-no-completion' and failure[2:] == lines[:-1][-256:]
    assert core(lines[-1]) == 71927 and not (D / 'terminal-error.txt').exists()
    return dict(status='ACTUAL_BG_EPOCH_CAPTURE_EXACT_PREVIOUS_CORE_AND_SCALAR_CHRONOLOGY_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), launch_sha256=sha(launch_raw), files_verified=187, exact_previous_whole_Core_no_normalization=exact_cores, all19_states_all5_RAM_png_display_exact_previous=True, genuine_states=snapshots, entire_previous331_trace_records_exact_after_only20_telemetry_lines_removed=True, same88_inputs_and_sole16bit_HP_ledger=True, config_only_reviewed_paths_and_update_check_time_differ=config_update_times, actual_outcome=launch['outcome'], actual_advances=3000, scalar_record_count=20, scalar_core_counts={'69932':11,'69933':9}, scalar_chronology=scalar_rows, both_actual_guard_return_R0_zero_directly_observed=True, actual_map_calls_R0=['12'], actual_selector21_map_call_observed=False, first_core_shake2356='0000to0200to0000', first_map_BG1CNT='1E03to1F03', next_core_all_velocities_zero_BG1CNT='1F03', accepted_queue_or_IRQ_family_observed=False, cleanup_observed=False, actual_mode8_observed=False, strict_Core_qualification_unchanged=True, source_DI_restore_claim=False, historical_E5_closure_claim=False, emulator_launched=False, savestate_loaded=False, guest_memory_written_by_reviewer=False, old_full_suite_rerun=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = audit(); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('PASS187files/20exactCores/19genuineStates/20boundedscalarrecords;actualshakeclearfallbackepochs')


if __name__ == '__main__':
    main()
