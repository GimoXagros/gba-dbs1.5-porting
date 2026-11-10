"""Independent completed display-epoch/actual IRQ capture and scroll-observer audit."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib

import verify_gba_shoot_terminal_owner_capture as oldqa
import verify_gba_shoot_terminal_display_epoch_wrapper as wrapperqa

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'build/bizhawk-gba-shoot-terminal-display-epoch-20261110-a'
OLD = oldqa.D
sha, fields, core, regs, stateqa = oldqa.sha, oldqa.fields, oldqa.core, oldqa.regs, oldqa.stateqa
event, half, long = oldqa.event, oldqa.half, oldqa.long


def audit():
    assert sha(Path(oldqa.__file__).read_bytes()) == 'E2A1BB1E716B709AACE6E6F155BE3B48273E5AAFE19E021A7DBCE1F521A377A4'
    assert sha(Path(wrapperqa.__file__).read_bytes()) == '519893D88AA1353C259CD987E3D2F8A317EC301F7DE378EE746E221D85AB04D4'
    report_raw = (ROOT / 'build/gba-shoot-terminal-owner-capture-qa-20261110/report.json').read_bytes()
    assert sha(report_raw) == '324821AF9C2945AF244A90F59DCA13045F1F357268C57829369FF3028426D2D7'
    previous_report = json.loads(report_raw)
    assert sha((ROOT / 'build/gba-shoot-terminal-display-epoch-wrapper-qa-20261110/report.json').read_bytes()) == 'F83AD61046BD5CC1D7762B074CA77DF794479F9D135F863F47812F017FB23567'
    launch_raw = (D / 'launch.json').read_bytes()
    assert sha(launch_raw) == 'C538496FDF8E0B06A29694FFCC7CE6252494B36F1F7317397700D93422B5A6DE'
    launch = json.loads(launch_raw)
    assert launch['completed'] and launch['outcome'] == 'failure:next-scroll-store'
    assert launch['done_text'] == (D / 'shoot-terminal-done.txt').read_text('utf8') == 'failure:next-scroll-store\n'
    assert not any(launch[k] for k in ('visible', 'physical_background_input', 'supplied_save_used', 'host_stop_requested', 'host_deadline_reached'))
    inventory = {p.relative_to(D).as_posix(): sha(p.read_bytes()) for p in sorted(D.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files'] and len(inventory) == 196
    old_launch_raw = (OLD / 'launch.json').read_bytes(); assert sha(old_launch_raw) == previous_report['launch_sha256']
    old_launch = json.loads(old_launch_raw)

    def oldfile(name):
        blob = (OLD / name).read_bytes(); assert sha(blob) == old_launch['files'][name]
        return blob

    pins_raw = (ROOT / 'build/gba-shoot-terminal-display-epoch-pins-20261110.json').read_bytes()
    assert sha(pins_raw) == launch['reviewed_pins_sha256'] == wrapperqa.PINS and launch['pins'] == json.loads(pins_raw)
    for path, digest in launch['pins'].items():
        assert sha((ROOT / path).read_bytes()) == digest
    assert sha((ROOT / 'build/run_gba_shoot_terminal_display_epoch_20261110.py').read_bytes()) == launch['launcher_sha256'] == wrapperqa.HOST
    rom = (D / 'loaded-rom.bin').read_bytes()
    assert rom == (D / 'probe.gba').read_bytes() == (ROOT / 'build/shoot-terminal-display-epoch-20261110/component.gba').read_bytes()
    assert sha(rom) == wrapperqa.ROM == launch['rom_sha256']
    assert all(launch[k] for k in ('loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged', 'authorized_write_verified', 'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal'))
    for key in ('source_core_sha256', 'source_rom_sha256', 'all_Core_byte_differences', 'restored_core_exact_except_current_rom_crc', 'qualification', 'guest_writes_expected', 'guest_write_ledger', 'phase_kind', 'checkpoint_pins'):
        assert launch[key] == old_launch[key]
    expected_args = [s.replace(OLD.name, D.name).replace('bizhawk_probe_gba_shoot_terminal_owner.lua', 'bizhawk_probe_gba_shoot_terminal_display_epoch.lua').replace(oldqa.ROM, wrapperqa.ROM) for s in old_launch['arguments']]
    assert launch['arguments'] == expected_args
    for name in launch['checkpoint_pins']:
        assert (D / 'checkpoint' / name).read_bytes() == oldfile('checkpoint/' + name)
    cfg = json.loads((D / 'config.json').read_bytes())
    assert all(cfg[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(v['Path'].startswith('W:/build/' + D.name + '/data/') for v in cfg['PathEntries']['Paths'])
    assert (D / 'terminal-write-ledger.txt').read_bytes() == oldfile('terminal-write-ledger.txt')
    source_blob = (D / 'checkpoint/healthy-activation.State').read_bytes()
    source_core, _ = stateqa.checkpoint_core(source_blob)
    restored, _ = stateqa.checkpoint_core((D / 'restored.State').read_bytes())
    assert sha(source_core) == launch['source_core_sha256'] and sha(restored) == launch['restored_core_sha256']
    assert (D / 'restored.State').read_bytes() == (D / '00-before.State').read_bytes()
    expected = bytearray(source_core); struct.pack_into('<I', expected, 12, zlib.crc32(rom))
    assert len(source_core) == len(restored)
    differences = [dict(offset=i, expected=a, actual=b) for i, (a, b) in enumerate(zip(expected, restored)) if a != b]
    assert differences == launch['all_Core_byte_differences'] and len(differences) == 9
    assert restored != expected and not launch['restored_core_exact_except_current_rom_crc'] and sha(expected) == launch['expected_restored_core_sha256']
    length = long(source_core, 0)
    assert source_core[0x24:0x134] == restored[0x24:0x134]
    assert source_core[4+0x61000:4+length] == restored[4+0x61000:4+length] and source_core[4+length:] == restored[4+length:]
    lines = (D / 'terminal-trace.txt').read_text('utf8').splitlines(); oldlines = oldfile('terminal-trace.txt').decode().splitlines()
    assert lines[:261] == oldlines[:261] and lines[261] != oldlines[261]
    assert event(lines, 'input') == event(oldlines, 'input') and len(event(lines, 'input')) == 88
    captures = event(lines, 'capture'); assert len(captures) == 20 and len(list(D.glob('*.State'))) == 21
    with zipfile.ZipFile(io.BytesIO(source_blob)) as z:
        sync = json.loads(z.read('SyncSettings.json'))
    snapshots, ram, crc_equal, timeline = {}, {}, [], []
    previous_restored, _ = stateqa.checkpoint_core(oldfile('restored.State'))
    previous_restored = bytearray(previous_restored); struct.pack_into('<I', previous_restored, 12, zlib.crc32(rom))
    assert restored == previous_restored; crc_equal.append('restored')
    for n, row in enumerate(captures):
        c = fields(row); name = c['name']; frame = int(c['export_core'])
        assert name.startswith(f'{n:02d}-') and core(row) == frame
        regions = {k: (D / f'{name}-{k}.bin').read_bytes() for k in stateqa.OFFSETS}; iw, ew = regions['iwram'], regions['ewram']
        stateblob = (D / f'{name}.State').read_bytes()
        parsed = stateqa.parse_checkpoint(stateblob, oldqa.prior.oldqa.helpers.metadata(iw, ew, frame), regions, rom)
        assert parsed['state']['mode'] == 7 and parsed['state']['stage'] == 11
        assert parsed['state']['P1HP'] == (4 if n <= 2 else 1) and parsed['state']['P2HP'] == (37 if n == 0 else 1 if n == 1 else 0)
        assert long(iw, 0x489C) == oldqa.P and long(iw, 0x48A0) == oldqa.Q and long(iw, 0x4D3C) == oldqa.AUX
        for a, kind in ((oldqa.P, 0), (oldqa.Q, 3), (oldqa.AUX, 6)):
            at = a-0x02000000; assert half(ew, at-0x18+0x10) & 2 and half(ew, at+4) & 15 == kind
        for a, v in ((oldqa.P+0x18, oldqa.Q), (oldqa.Q+0x18, oldqa.P), (oldqa.Q+0x28, oldqa.AUX), (oldqa.AUX+0x18, oldqa.P), (oldqa.AUX+0x28, oldqa.Q)):
            assert long(ew, a-0x02000000) == v
        with zipfile.ZipFile(io.BytesIO(stateblob)) as z:
            assert json.loads(z.read('SyncSettings.json')) == sync
            args = json.loads(z.read('UserData.txt'))['o']
            assert set(args) == {'$type', 'output', 'checkpoint_dir', 'probe_sha256', 'boss_authorization'}
            assert args['output'] == 'W:/build/' + D.name and args['checkpoint_dir'] == args['output'] + '/checkpoint'
            assert args['probe_sha256'] == wrapperqa.ROM and args['boss_authorization'] == 'user-approved-development-boss-once-per-stage'
        assert oldqa.prior.oldqa.helpers.png((D / f'{name}.png').read_bytes()) == [240, 160] and len((D / f'{name}-display.bin').read_bytes()) == 96
        if n <= 17:
            previous, _ = stateqa.checkpoint_core(oldfile(name + '.State'))
            previous = bytearray(previous); struct.pack_into('<I', previous, 12, zlib.crc32(rom))
            actual, _ = stateqa.checkpoint_core(stateblob)
            assert actual == previous, 'onlyCRC12:16:' + name
            crc_equal.append(name)
            for k, b in regions.items():
                assert b == oldfile(f'{name}-{k}.bin')
        for item in c['events'].split(','):
            if '@' in item:
                kind, observed = item.split('@'); assert any(core(s) == int(observed) for s in event(lines, kind))
                assert frame == int(observed) + (0 if kind == 'authorized-hp1' else 1)
        snapshots[name] = parsed; ram[name] = regions; timeline.append(dict(name=name, core=frame, events=c['events']))
    counts = dict(Counter(s.split(' kind=', 1)[1].split()[0] for s in lines))
    expected_counts = dict(previous_report['exact_hook_event_counts'])
    expected_counts.pop('bounded-no-completion'); expected_counts.update({'capture':20,'frame':118,'guard-refusal':1,'guard-accepted':2,'irq-queue-selected':1,'queue-substitution':2,'guarded-display':1,'irq-first-entry':1,'irq-entry':30,'irq-compare':30,'irq-match':8,'irq-match-stored':8,'irq-final-install':1,'irq-final-called':1,'irq-final':1,'next-display-scroll-pre':1,'next-scroll-store':1})
    assert counts == expected_counts and len(lines) == 351
    selected, displayed = event(lines, 'irq-queue-selected')[0], event(lines, 'guarded-display')[0]
    assert core(selected) == core(displayed) == 69933 and lines.index(selected) < lines.index(displayed)
    assert regs(displayed)['R15'] == 0x086FF760 and regs(displayed)['R0'] == 0x086FFE10 and regs(displayed)['R14'] == 0x086FF6EC
    comparisons, matches, stored = event(lines, 'irq-compare'), event(lines, 'irq-match'), event(lines, 'irq-match-stored')
    offsets = [0, 2, 4, 7, 10, 13, 17, 21]
    for row in comparisons:
        f, r = fields(row), regs(row); state = [int(x,16) for x in f['state'].split(',')]
        assert r['R4'] == 0x03004710 and r['R5'] == state[3] and r['R6'] == offsets[r['R5']]
        assert r['R1'] == ((state[2] & 255) + r['R6']) & 255 and r['R0'] == (int(f['VCOUNT'])-8) & 255
        assert r['R15'] == 0x086FFE4C
    assert regs(comparisons[0])['R0'] == 142 and regs(comparisons[0])['R1'] == 143 and fields(comparisons[0])['VCOUNT'] == '150'
    match_timeline = []
    for i, (matched, written) in enumerate(zip(matches, stored)):
        f, r = fields(matched), regs(matched); before = [int(x,16) for x in f['state'].split(',')]
        after = [int(x,16) for x in fields(written)['state'].split(',')]
        assert before[2] == 143+i and before[3] == i and r['R5'] == i and r['R6'] == offsets[i]
        assert r['R0'] == r['R1'] == 143+i+offsets[i]
        assert after[2] == before[2]+1 and after[3] == i+1 and regs(written)['R5'] == i+1
        assert core(matched) == core(written) and lines.index(matched)+1 == lines.index(written)
        match_timeline.append(dict(index=i, offset=offsets[i], core=core(matched), counter_before=before[2], compared_line=r['R0'], hardware_VCOUNT=int(f['VCOUNT']), counter_after=after[2]))
    assert [v['hardware_VCOUNT'] for v in match_timeline] == [151,154,157,161,165,169,174,179]
    final = event(lines, 'irq-final')[0]
    assert core(final) == 69934 and fields(final)['VCOUNT'] == '180' and fields(final)['slot'] == '086FFEBC'
    install = regs(event(lines, 'irq-final-install')[0]); assert install['R0'] == 0x030012E0 and install['R1'] == 0x086FFEBC and install['R5'] == 8
    pre, failed = event(lines, 'next-display-scroll-pre')[0], event(lines, 'next-scroll-store')[0]
    assert core(pre) == core(failed) == 69934 and lines.index(final) < lines.index(pre) < lines.index(failed)
    pending = int(fields(pre)['tuple'],16) >> 16 & 255; r = regs(failed)
    assert pending == 0x70 and r['R0'] == pending and r['R10'] == pending-8 and r['R8'] == 0x030012B8 and r['R9'] == 0x04000000 and r['R14'] == 0x085E743C
    assert rom[0xF2C:0xF44] == bytes.fromhex('74809fe50000c8e50193a0e308a040e2b4a1c9e11eff2fe1')
    final_iw = ram['19-irq-final-install']['iwram']; assert final_iw[0x12B8] == final_iw[0x456E] == pending
    final_core, _ = stateqa.checkpoint_core((D / '19-irq-final-install.State').read_bytes())
    serialized_IO14 = half(final_core, 4+0x400+0x14)
    raw_dump_IO14 = half((D / '19-irq-final-install-display.bin').read_bytes(), 0x14)
    assert serialized_IO14 == 0x68 and raw_dump_IO14 == 0xFFFC and serialized_IO14 != raw_dump_IO14
    failure = (D / 'terminal-first-failure.txt').read_text('utf8').splitlines()
    assert failure[0] == 'failure:next-scroll-store' and failure[2:] == lines[:-1][-256:]
    assert core(lines[-1]) == 69935 and not (D / 'terminal-error.txt').exists()
    return dict(status='ACTUAL_DISPLAY_EPOCH_IRQ8_AND_SCROLL_OBSERVER_FAILURE_CAPTURE_INTEGRITY_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), launch_sha256=sha(launch_raw), files_verified=196, genuine_states=snapshots, capture_timeline=timeline, known_prefix_whole_Core_equal_only_CRC12_to16=crc_equal, all18_known_phase_snapshots5RAM_equal=True, identical_initial_trace_lines=261, same88_inputs_and_sole16bit_HP_ledger=True, actual_outcome=launch['outcome'], final_export_core=69935, actual_guarded_display_core=69933, actual_IRQ_entry_compare_count=30, actual_IRQ_matches=match_timeline, actual_first_compare=dict(core=69933,hardware_VCOUNT=150,compared_line=142,target=143,margin_in_compare_lines=1), actual_first_match_hardware_VCOUNT=151, earliest_counter1_timing_tested=False, observed_counter143_timing_only=True, actual_final_IRQ=dict(core=69934,hardware_VCOUNT=180,slot='086FFEBC'), actual_scroll_failure=dict(core=69934,return_PC='085E743C',R0=pending,R10=r['R10'],R8='030012B8',R9='04000000',final_outer_shadow=final_iw[0x12B8],final_outer_serialized_IO14=serialized_IO14,final_outer_raw_SystemBus_dump_IO14=raw_dump_IO14), failure_does_not_prove_guest_scroll_store_wrong=True, no_instruction_time_MMIO_value_invented=True, source_store_bytes_bound=True, cleanup_observed=False, mode8_observed=False, source_DI_restore_claim=False, historical_E5_closure_claim=False, strict_source_Core_nine_nonCRC_differences_unchanged=differences, exact_hook_counts=counts, emulator_launched=False, savestate_loaded=False, guest_memory_written_by_reviewer=False, old_full_suite_rerun=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root-completed', action='store_true', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = audit(); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('PASS196files/20genuineStates/actual8IRQmatches;counter143only;scrollobserverfailurepreserved')


if __name__ == '__main__':
    main()
