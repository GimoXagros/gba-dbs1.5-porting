"""Independent completed 46B3 owner-repair capture audit; no emulator or state load."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib

import verify_gba_shoot_terminal_palette_capture as prior
import verify_gba_shoot_terminal_owner_wrapper as wrapperqa

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'build/bizhawk-gba-shoot-terminal-owner-20261109-a'
OLD = prior.D
sha, half, long, fields = prior.sha, prior.half, prior.long, prior.fields
event, core, regs = prior.event, prior.core, prior.regs
stateqa, P, Q, AUX, S = prior.stateqa, prior.P, prior.Q, prior.AUX, prior.S
ROM = wrapperqa.NEW


def audit():
    assert sha(Path(prior.__file__).read_bytes()) == 'F31CC74D8C967359E94AFE7FE30AD38A0D74BD7988B18E233DFEFBCD7DD92E24'
    assert sha(Path(wrapperqa.__file__).read_bytes()) == '0D39EBF680CABA0D88B73933B64673C8EB07A91DBDF7F0C3C2FE8021CF54AF7F'
    qa_raw = (ROOT / 'build/gba-shoot-terminal-owner-wrapper-qa-20261109/report.json').read_bytes()
    assert sha(qa_raw) == '3AAA9BE2B0E41A7A012E805A0F75185707DD20BD831BDA2DDCD8A4A038BEB3FB'
    previous_report_raw = (ROOT / 'build/gba-shoot-terminal-palette-capture-qa-20261109/report.json').read_bytes()
    assert sha(previous_report_raw) == '91E07B23E25ABC5510B77B7D1F3C8D6930D51807A2D91D7A870E39E2B6018096'
    previous_report = json.loads(previous_report_raw)
    launch_raw = (D / 'launch.json').read_bytes()
    assert sha(launch_raw) == '5CB274F7EEEB2E56C4C73D9AD06AF466F2C027C0DFFD3F6EA262AE4CE293F551'
    launch = json.loads(launch_raw)
    assert launch['completed'] and launch['outcome'] == 'failure:bounded-no-completion'
    assert launch['done_text'] == (D / 'shoot-terminal-done.txt').read_text('utf8') == 'failure:bounded-no-completion\n'
    assert not any(launch[k] for k in ('visible', 'physical_background_input', 'supplied_save_used', 'host_stop_requested', 'host_deadline_reached'))
    inventory = {p.relative_to(D).as_posix(): sha(p.read_bytes()) for p in sorted(D.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files'] and len(inventory) == 187
    pins_raw = (ROOT / 'build/gba-shoot-terminal-owner-pins-20261109.json').read_bytes()
    assert sha(pins_raw) == launch['reviewed_pins_sha256'] == wrapperqa.PINS
    assert launch['pins'] == json.loads(pins_raw)
    for path, digest in launch['pins'].items():
        assert sha((ROOT / path).read_bytes()) == digest
    assert sha((ROOT / 'build/run_gba_shoot_terminal_owner_20261109.py').read_bytes()) == launch['launcher_sha256'] == wrapperqa.HOST
    assert all(launch[k] for k in ('authorized_write_verified', 'loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged'))
    rom = (D / 'loaded-rom.bin').read_bytes()
    assert rom == (D / 'probe.gba').read_bytes() == (ROOT / 'build/shoot-terminal-owner-link-20261109/component.gba').read_bytes()
    assert sha(rom) == launch['rom_sha256'] == ROM
    assert launch['arguments'] == ['--gdi', '--config=W:/build/' + D.name + '/config.json', '--lua=W:/tools/bizhawk_probe_gba_shoot_terminal_owner.lua', '--userdata=output:W:/build/' + D.name + ';checkpoint_dir:W:/build/' + D.name + '/checkpoint;probe_sha256:' + ROM + ';boss_authorization:user-approved-development-boss-once-per-stage', 'W:/build/' + D.name + '/probe.gba']
    baseline = ROOT / 'build/bizhawk-gba-shoot-entry-replay-20261109-a'
    for name, digest in launch['checkpoint_pins'].items():
        assert sha((D / 'checkpoint' / name).read_bytes()) == sha((baseline / name).read_bytes()) == digest
    cfg = json.loads((D / 'config.json').read_text('utf8'))
    assert all(cfg[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(v['Path'].startswith('W:/build/' + D.name + '/data/') for v in cfg['PathEntries']['Paths'])
    old_launch_raw = (OLD / 'launch.json').read_bytes()
    assert sha(old_launch_raw) == previous_report['launch_sha256'] == '7CD51DD9A571F35A101BFFA68B7D811C611A10870998A298D85FCB0D5D1EE252'
    old_launch = json.loads(old_launch_raw)

    def oldfile(name):
        blob = (OLD / name).read_bytes()
        assert sha(blob) == old_launch['files'][name]
        return blob

    source_blob = (D / 'checkpoint/healthy-activation.State').read_bytes()
    source_core, _ = stateqa.checkpoint_core(source_blob)
    restored, _ = stateqa.checkpoint_core((D / 'restored.State').read_bytes())
    assert (D / 'restored.State').read_bytes() == (D / '00-before.State').read_bytes()
    assert sha(source_core) == launch['source_core_sha256'] == '6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
    assert sha(restored) == launch['restored_core_sha256']
    expected = bytearray(source_core); struct.pack_into('<I', expected, 12, zlib.crc32(rom))
    assert len(source_core) == len(restored)
    differences = [dict(offset=i, expected=a, actual=b) for i, (a, b) in enumerate(zip(expected, restored)) if a != b]
    rawdiff = [dict(offset=i, original=a, actual=b) for i, (a, b) in enumerate(zip(source_core, restored)) if a != b]
    assert differences == launch['all_Core_byte_differences'] == previous_report['CRC_adjusted_Core_differences'] and len(differences) == 9
    assert restored != expected and not launch['restored_core_exact_except_current_rom_crc'] and sha(expected) == launch['expected_restored_core_sha256']
    length = long(source_core, 0)
    assert source_core[0x24:0x134] == restored[0x24:0x134] and launch['CPU_bank_equal']
    assert source_core[4+0x61000:4+length] == restored[4+0x61000:4+length] and launch['native_extensions_equal']
    assert source_core[4+length:] == restored[4+length:] and launch['managed_suffix_equal']
    lines = (D / 'terminal-trace.txt').read_text('utf8').splitlines()
    oldlines = oldfile('terminal-trace.txt').decode().splitlines()
    assert lines[:260] == oldlines[:260] and lines[260] != oldlines[260]
    assert event(lines, 'input') == event(oldlines, 'input') and len(event(lines, 'input')) == 88
    assert [core(s) for s in event(lines, 'input') if fields(s)['Right'] == 'true'] == [68927, 68928]
    assert [core(s) for s in event(lines, 'input') if fields(s)['B'] == 'true'] == [69000]
    ledger = (D / 'terminal-write-ledger.txt').read_text('utf8').strip()
    assert ledger == launch['guest_write_ledger'] == oldfile('terminal-write-ledger.txt').decode().strip()
    assert fields(ledger) == previous_report['actual_one_word_ledger']
    assert launch['guest_writes_expected'] == [dict(actor='02011828', address='0201188C', bytes=2, before=37, after=1, count=1)]

    captures = event(lines, 'capture'); assert len(captures) == 19
    assert len(list(D.glob('*.State'))) == 20
    with zipfile.ZipFile(io.BytesIO(source_blob)) as z:
        sync = json.loads(z.read('SyncSettings.json'))
    snapshots, ram, timeline, crc_equal = {}, {}, [], []
    previous_restored, _ = stateqa.checkpoint_core(oldfile('restored.State'))
    expected_restored = bytearray(previous_restored); struct.pack_into('<I', expected_restored, 12, zlib.crc32(rom))
    assert restored == expected_restored; crc_equal.append('restored')
    for n, row in enumerate(captures):
        c = fields(row); name = c['name']; frame = int(c['export_core'])
        assert name.startswith(f'{n:02d}-') and core(row) == frame
        regions = {k: (D / f'{name}-{k}.bin').read_bytes() for k in stateqa.OFFSETS}
        iw, ew = regions['iwram'], regions['ewram']
        stateblob = (D / f'{name}.State').read_bytes()
        parsed = stateqa.parse_checkpoint(stateblob, prior.oldqa.helpers.metadata(iw, ew, frame), regions, rom)
        assert parsed['state']['mode'] == 7 and parsed['state']['stage'] == 11
        assert parsed['state']['P1HP'] == (4 if n <= 2 else 1) and parsed['state']['P2HP'] == (37 if n == 0 else 1 if n == 1 else 0)
        assert long(iw, 0x489C) == P and long(iw, 0x48A0) == Q and long(iw, 0x4D3C) == AUX
        for a, kind in ((P, 0), (Q, 3), (AUX, 6)):
            at = a - 0x02000000
            assert half(ew, at-0x18+0x10) & 2 and half(ew, at+4) & 15 == kind
        for a, v in ((P+0x14, P), (P+0x18, Q), (Q+0x14, Q), (Q+0x18, P), (Q+0x28, AUX), (AUX+0x18, P), (AUX+0x28, Q)):
            assert long(ew, a-0x02000000) == v
        for at, cb in ((0x4510, 0x08374FF4 if n <= 1 else 0x08374FAC), (0x4514, 0x083735BC if n <= 1 else 0x0837354C)):
            h = long(iw, at); assert half(ew, h-0x02000000+0x10) & 2 and long(ew, h-0x02000000) == cb
        if n >= 2:
            assert half(ew, S-0x02000000+0x10) & 2 and long(ew, S-0x02000000+4) == 0xFF0
        assert prior.oldqa.helpers.png((D / f'{name}.png').read_bytes()) == [240, 160]
        assert len((D / f'{name}-display.bin').read_bytes()) == 96
        with zipfile.ZipFile(io.BytesIO(stateblob)) as z:
            assert json.loads(z.read('SyncSettings.json')) == sync
            args = json.loads(z.read('UserData.txt'))['o']
            assert set(args) == {'$type', 'output', 'checkpoint_dir', 'probe_sha256', 'boss_authorization'}
            assert args['probe_sha256'] == ROM and args['boss_authorization'] == 'user-approved-development-boss-once-per-stage'
            assert args['output'] == 'W:/build/' + D.name and args['checkpoint_dir'] == args['output'] + '/checkpoint'
        if n == 0:
            for k, b in regions.items():
                assert b == (D / 'checkpoint' / f'13-healthy-activation-{k}.bin').read_bytes()
        if n <= 17:
            previous, _ = stateqa.checkpoint_core(oldfile(name + '.State'))
            comparison = bytearray(previous); struct.pack_into('<I', comparison, 12, zlib.crc32(rom))
            actual, _ = stateqa.checkpoint_core(stateblob)
            assert actual == comparison, 'whole-Core CRC-only:' + name
            crc_equal.append(name)
            for k, b in regions.items():
                assert b == oldfile(f'{name}-{k}.bin')
        for item in c['events'].split(','):
            if '@' in item:
                kind, observed = item.split('@')
                assert any(core(x) == int(observed) for x in event(lines, kind))
                assert frame == int(observed) + (0 if kind in ('authorized-hp1', 'bounded-no-completion') else 1)
        snapshots[name] = parsed; ram[name] = regions
        timeline.append(dict(name=name, export_core=frame, events=c['events'], scene_callback=f'{long(ew,S-0x02000000):08X}', timer=half(ew,S-0x02000000+0x18+0x50), flags=f'{half(iw,0x450A):04X}', common=f'{half(iw,0x4506):04X}', control=iw[0x4529], camera=half(iw,0x451E)))

    counts = dict(Counter(row.split(' kind=', 1)[1].split()[0] for row in lines))
    expected_counts = dict(previous_report['exact_hook_event_counts'], **{'guard-refusal': 2})
    assert counts == expected_counts and len(lines) == 331
    for kind, frame in previous_report['observed_new_native_milestones'].items():
        assert core(event(lines, kind)[0]) == frame
    cam, ret = event(lines, 'camera-capture')[0], event(lines, 'camera-return')[0]
    assert core(cam) == core(ret) == 69261 and regs(cam)['R1'] == 268 and fields(ret)['scene52'] == '0F58'
    refusals = event(lines, 'guard-refusal')
    assert [core(s) for s in refusals] == [69932, 69933]
    assert 'kind=guard-refusal BG-velocity ' in refusals[0] and 'BG1CNT=1E03' in refusals[0]
    assert 'kind=guard-refusal hardware-BG-mapping ' in refusals[1] and 'BG1CNT=1F03' in refusals[1]
    for row in refusals:
        assert regs(row)['R15'] == 0x086FF9C4 and regs(row)['R14'] == 0x086FF698
        assert 'prepared=1/08587200 copied=1/08587200' in row
        assert 'actor=02011940 cb=085BF600' in row and 'links=02011710,02011828' in row
    assert not any(event(lines, k) for k in ('guard-accepted', 'queue-substitution', 'irq-queue-selected', 'guarded-display', 'irq-entry', 'irq-match', 'irq-final', 'cleanup-entry', 'cleanup-request', 'native-mode8'))
    final = ram['18-bounded-no-completion']; iw, ew = final['iwram'], final['ewram']; at = S-0x02000000
    assert long(ew, at) == 0x085CD510 and half(ew, at+0x18+0x50) == 0 and half(ew, at+0x18+0x52) == 0xF58
    assert half(iw,0x450A) == 0x1486 and half(iw,0x4506) == 0x90 and iw[0x4529] == 0 and half(iw,0x451E) == 268
    assert long(ew,Q-0x02000000) == 0x085BF200 and long(ew,AUX-0x02000000) == 0x085BF600
    assert long(iw,0x2474) == 1 and long(iw,0x2478) == 0x08587200 and long(iw,0x4574) == 0 and long(iw,0x4578) == 0x08587200
    failure = (D / 'terminal-first-failure.txt').read_text('utf8').splitlines()
    assert failure[0] == 'failure:bounded-no-completion' and failure[2:] == lines[:-1][-256:]
    assert core(lines[-1]) == 71927 and not (D / 'terminal-error.txt').exists()
    return dict(status='ACTUAL_TERMINAL_OWNER_REPAIR_NEXT_GUARD_REFUSALS_CAPTURE_INTEGRITY_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), launch_sha256=sha(launch_raw), files_verified=len(inventory), genuine_states=snapshots, capture_timeline=timeline, actual_outcome=launch['outcome'], advances=3000, actual_one_word_ledger=fields(ledger), same88_prefatal_input_records=True, identical_initial_trace_lines=260, crossROM_whole_Core_equal_after_only_CRC12_to16=crc_equal, all_five_RAM_equal_previous_trial_snapshots00_through17=True, observed_native_milestones=previous_report['observed_new_native_milestones'], guard_refusals=[dict(core=core(row), reason=row.split('kind=guard-refusal ',1)[1].split()[0], BG1CNT=fields(row)['BG1CNT'], aux18='02011710', aux28='02011828', prepared_and_copied='1/08587200') for row in refusals], old_owner_refusal_absent=True, guard_return_R0_not_directly_logged=True, accepted_queue_or_IRQ_family_observed=False, cleanup_observed=False, actual_mode8_observed=False, final_scene_callback='085CD510', final_scene_timer=0, final_HP=[1,0], final_prepared_count=1, final_copied_count=0, exact_hook_event_counts=counts, all19_genuine_states_all5_RAM_exact=True, source_whole_Core_equal=False, CRC_adjusted_source_Core_equal=False, raw_original_Core_differences=rawdiff, CRC_adjusted_Core_differences=differences, CPU_extensions_managed_equal=True, synthetic_owner_fixture_not_runtime_eligibility_proof=True, raw_IO_or_mixed_epoch_does_not_predict_native_acceptance=True, source_DI_restore_claim=False, inherited_HUD_not_cold_visual_proof=True, terminal_or_IRQ_completion_claim=False, historical_E5_closure_claim=False, emulator_launched=False, savestate_loaded=False, guest_memory_written_by_reviewer=False, old_full_suite_rerun=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('PASS187immutablefiles/19genuineStates/19CRC-onlyCores;actualnextguardrefusals;noIRQcompletion')


if __name__ == '__main__':
    main()
