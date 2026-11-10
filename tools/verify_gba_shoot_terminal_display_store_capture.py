"""Independent actual native terminal mode8 audit with exact executed-scroll witnesses."""
import argparse
from collections import Counter
import io
import json
from pathlib import Path
import zipfile

import verify_gba_shoot_terminal_display_epoch_capture as prior

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'build/bizhawk-gba-shoot-terminal-display-store-20261110-a'
OLD = prior.D
sha, fields, core, regs, stateqa = prior.sha, prior.fields, prior.core, prior.regs, prior.stateqa
event, half, long = prior.event, prior.half, prior.long
ROM = prior.wrapperqa.ROM
WRAPPER = '3A18BCE55CA83DF52300375B19BF7F5EAACDD08ED3498D18A0E4DC1D55CF934B'
HOST = '9636A1C3A3EAD031B25C2357B5E29DBDA41480B4813B10D5AD6B43F3B258B961'
PINS = '499AB2425B36F7749BE07930FA8E034F1086293B7AA5D7491615395685F60A3B'
P, Q, AUX, S = prior.oldqa.P, prior.oldqa.Q, prior.oldqa.AUX, prior.oldqa.S


def audit():
    assert sha(Path(prior.__file__).read_bytes()) == 'E1D32F152302C4C292F3DA0C14E85A0E4398D197FC8712B021A05A3F8B98522E'
    previous_raw = (ROOT / 'build/gba-shoot-terminal-display-epoch-capture-qa-20261110/report.json').read_bytes()
    assert sha(previous_raw) == '3F16D4035973A6B3D76CBFE33516339AF5F553F5DA2DAE01EF896497BC99B1AE'
    previous = json.loads(previous_raw)
    assert sha((ROOT / 'build/gba-shoot-terminal-display-store-wrapper-qa-20261110/report.json').read_bytes()) == '28680A5A77FB9AA88E8BF97F97A7D7FB0D8008F461E07D05B9FF1F6DD9894136'
    launch_raw = (D / 'launch.json').read_bytes()
    assert sha(launch_raw) == '9F943EBE1B3BFE1C257080A416E39A8CA79596B26A7446E37B43C4D883EA976B'
    launch = json.loads(launch_raw)
    assert launch['completed'] and launch['outcome'] == 'native-terminal-mode8'
    assert launch['done_text'] == (D / 'shoot-terminal-done.txt').read_text('utf8') == 'native-terminal-mode8\n'
    assert not any(launch[k] for k in ('visible','physical_background_input','supplied_save_used','host_stop_requested','host_deadline_reached'))
    inventory = {p.relative_to(D).as_posix(): sha(p.read_bytes()) for p in sorted(D.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files'] and len(inventory) == 258
    old_launch_raw = (OLD / 'launch.json').read_bytes(); assert sha(old_launch_raw) == previous['launch_sha256']
    old_launch = json.loads(old_launch_raw)

    def oldfile(name):
        blob = (OLD / name).read_bytes(); assert sha(blob) == old_launch['files'][name]
        return blob

    pins_raw = (ROOT / 'build/gba-shoot-terminal-display-store-pins-20261110.json').read_bytes()
    assert sha(pins_raw) == launch['reviewed_pins_sha256'] == PINS and launch['pins'] == json.loads(pins_raw)
    assert launch['pins']['tools/bizhawk_probe_gba_shoot_terminal_display_store.lua'] == WRAPPER
    for path, digest in launch['pins'].items():
        assert sha((ROOT / path).read_bytes()) == digest
    assert sha((ROOT / 'build/run_gba_shoot_terminal_display_store_20261110.py').read_bytes()) == launch['launcher_sha256'] == HOST
    rom = (D / 'loaded-rom.bin').read_bytes()
    assert rom == (D / 'probe.gba').read_bytes() == oldfile('loaded-rom.bin') and sha(rom) == launch['rom_sha256'] == ROM
    assert all(launch[k] for k in ('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged','authorized_write_verified','CPU_bank_equal','native_extensions_equal','managed_suffix_equal'))
    for key in ('source_core_sha256','source_rom_sha256','restored_core_sha256','expected_restored_core_sha256','all_Core_byte_differences','restored_core_exact_except_current_rom_crc','qualification','guest_writes_expected','guest_write_ledger','phase_kind','checkpoint_pins'):
        assert launch[key] == old_launch[key]
    assert launch['arguments'] == [s.replace(OLD.name,D.name).replace('bizhawk_probe_gba_shoot_terminal_display_epoch.lua','bizhawk_probe_gba_shoot_terminal_display_store.lua') for s in old_launch['arguments']]
    for name, digest in launch['checkpoint_pins'].items():
        assert (D / 'checkpoint' / name).read_bytes() == oldfile('checkpoint/' + name) and sha((D / 'checkpoint' / name).read_bytes()) == digest
    cfg = json.loads((D / 'config.json').read_bytes())
    assert all(cfg[k] is False for k in ('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
    assert all(v['Path'].startswith('W:/build/' + D.name + '/data/') for v in cfg['PathEntries']['Paths'])
    ledger_raw = (D / 'terminal-write-ledger.txt').read_bytes(); assert ledger_raw == oldfile('terminal-write-ledger.txt')
    ledger = fields(ledger_raw.decode().strip())
    assert ledger == dict(core='69000',actor='02011828',address='0201188C',bytes='2',before='37',requested='1',P1HP='4',P1score='0',left='2120',right='4',attempt_consumed='true',after='1',verified='true')
    source_blob = (D / 'checkpoint/healthy-activation.State').read_bytes()
    source_core, _ = stateqa.checkpoint_core(source_blob); restored, _ = stateqa.checkpoint_core((D / 'restored.State').read_bytes())
    assert sha(source_core) == launch['source_core_sha256'] and sha(restored) == launch['restored_core_sha256']
    assert (D / 'restored.State').read_bytes() == (D / '00-before.State').read_bytes()
    source_comparison = bytearray(source_core)
    source_comparison[12:16] = restored[12:16]
    assert [dict(offset=i,expected=a,actual=b) for i,(a,b) in enumerate(zip(source_comparison,restored)) if a!=b] == launch['all_Core_byte_differences']
    assert not launch['restored_core_exact_except_current_rom_crc'] and source_comparison != restored and len(source_core) == len(restored)
    length = long(source_core,0)
    assert source_core[0x24:0x134] == restored[0x24:0x134] and source_core[4+0x61000:4+length] == restored[4+0x61000:4+length] and source_core[4+length:] == restored[4+length:]
    lines = (D / 'terminal-trace.txt').read_text('utf8').splitlines(); oldlines = oldfile('terminal-trace.txt').decode().splitlines()
    assert lines[:349] == oldlines[:349] and 'kind=next-scroll-store-pre ' in lines[349] and 'kind=next-scroll-store ' in oldlines[349]
    assert event(lines,'input') == event(oldlines,'input') and len(event(lines,'input')) == 88
    for kind in ('guarded-display','irq-entry','irq-compare','irq-match','irq-match-stored','irq-final-install','irq-final-called','irq-final','next-display-scroll-pre'):
        assert event(lines,kind) == event(oldlines,kind), 'exactpreviousIRQandtiming:' + kind
    captures = event(lines,'capture'); assert len(captures) == 27 and len(list(D.glob('*.State'))) == 28
    with zipfile.ZipFile(io.BytesIO(source_blob)) as z:
        sync = json.loads(z.read('SyncSettings.json'))
    exact_cores, snapshots, ram, timeline = [], {}, {}, []
    for path in sorted(OLD.glob('*.State')):
        actual_core, _ = stateqa.checkpoint_core((D / path.name).read_bytes())
        previous_core, _ = stateqa.checkpoint_core(oldfile(path.name))
        assert actual_core == previous_core, 'exactpreviousCorewithoutnormalization:' + path.name
        exact_cores.append(dict(name=path.stem,sha256=sha(actual_core)))
    for n, row in enumerate(captures):
        c = fields(row); name = c['name']; frame = int(c['export_core'])
        assert name.startswith(f'{n:02d}-') and core(row) == frame
        regions = {k:(D / f'{name}-{k}.bin').read_bytes() for k in stateqa.OFFSETS}; iw, ew = regions['iwram'], regions['ewram']
        stateblob = (D / f'{name}.State').read_bytes()
        parsed = stateqa.parse_checkpoint(stateblob,prior.oldqa.prior.oldqa.helpers.metadata(iw,ew,frame),regions,rom)
        assert parsed['state']['mode'] == (8 if n == 26 else 7) and parsed['state']['stage'] == 11
        assert parsed['state']['P1HP'] == (4 if n <= 2 else 1) and parsed['state']['P2HP'] == (37 if n == 0 else 1 if n == 1 else 0)
        assert long(iw,0x489C) == P and long(iw,0x48A0) == Q and long(iw,0x4D3C) == AUX
        for a,kind in ((P,0),(Q,3),(AUX,6)):
            at=a-0x02000000; assert bool(half(ew,at-0x18+0x10)&2) == (n < 25) and half(ew,at+4)&15 == kind
        for a,v in ((P+0x14,P),(P+0x18,Q),(Q+0x14,Q),(Q+0x18,P),(Q+0x28,AUX),(AUX+0x18,P),(AUX+0x28,Q)):
            assert long(ew,a-0x02000000) == v
        if n >= 2:
            for at,cb in ((0x4510,0x08374FAC),(0x4514,0x0837354C)):
                h=long(iw,at); assert bool(half(ew,h-0x02000000+0x10)&2) == (n < 25) and long(ew,h-0x02000000) == cb
        if 3 <= n <= 24:
            assert half(ew,S-0x02000000+0x10)&2 and long(ew,S-0x02000000+4) == 0xFF0
        if n >= 25:
            assert half(ew,S-0x02000000+0x10)&2 == 0
        with zipfile.ZipFile(io.BytesIO(stateblob)) as z:
            assert z.testzip() is None and json.loads(z.read('SyncSettings.json')) == sync
            args=json.loads(z.read('UserData.txt'))['o']
            assert set(args) == {'$type','output','checkpoint_dir','probe_sha256','boss_authorization'}
            assert args['output'] == 'W:/build/'+D.name and args['checkpoint_dir'] == args['output']+'/checkpoint'
            assert args['probe_sha256'] == ROM and args['boss_authorization'] == 'user-approved-development-boss-once-per-stage'
        assert prior.oldqa.prior.oldqa.helpers.png((D / f'{name}.png').read_bytes()) == [240,160] and len((D / f'{name}-display.bin').read_bytes()) == 96
        if n <= 19:
            for k,b in regions.items():
                assert b == oldfile(f'{name}-{k}.bin')
            assert (D / f'{name}.png').read_bytes() == oldfile(f'{name}.png') and (D / f'{name}-display.bin').read_bytes() == oldfile(f'{name}-display.bin')
        for item in c['events'].split(','):
            if '@' in item:
                kind,observed=item.split('@'); assert any(core(s) == int(observed) for s in event(lines,kind))
                assert frame == int(observed)+(0 if kind in ('authorized-hp1','native-mode8') else 1)
        snapshots[name]=parsed;ram[name]=regions
        timeline.append(dict(name=name,core=frame,events=c['events'],mode=half(iw,0x2310),scene_active=bool(half(ew,S-0x02000000+0x10)&2),triplet=[half(iw,a) for a in (0x2314,0x2316,0x2318)]))
    counts=dict(Counter(s.split(' kind=',1)[1].split()[0] for s in lines))
    expected_counts=dict(previous['exact_hook_counts']);expected_counts.pop('next-scroll-store')
    expected_counts.update({'capture':27,'frame':135,'guard-accepted':429,'queue-substitution':429,'next-scroll-store-pre':1,'next-scroll-store-executed':1,'next-display-scroll':1,'next-display-scroll-post':1,'phase-85CD550':1,'phase-85CD5E0':1,'phase-85CD640':1,'phase-85CD6A0':1,'phase-85CD710':1,'phase-85CD740':1,'cleanup-entry':1,'cleanup-request':1,'native-mode8':1})
    assert counts == expected_counts and len(lines) == 1241
    witnessed=[]
    for kind,pc in (('next-scroll-store-pre',0x08000F40),('next-scroll-store-executed',0x08000F44),('next-display-scroll',0x085E7440)):
        row=event(lines,kind)[0];r=regs(row)
        assert core(row) == 69934 and r['R15'] == pc and r['R0'] == 0x70 and r['R10'] == 0x68 and r['R8'] == 0x030012B8 and r['R9'] == 0x04000000 and r['R14'] == 0x085E743C
        if kind != 'next-display-scroll':
            f=fields(row);assert f['address'] == '04000014' and f['bytes'] == '2' and f['value'] == '0068' and f['shadow'] == '70'
        witnessed.append(dict(kind=kind,core=core(row),PC=f'{pc:08X}',value='0068',shadow='70'))
    assert [lines.index(event(lines,k)[0]) for k in ('next-display-scroll-pre','next-scroll-store-pre','next-scroll-store-executed','next-display-scroll','next-display-scroll-post')] == sorted(lines.index(event(lines,k)[0]) for k in ('next-display-scroll-pre','next-scroll-store-pre','next-scroll-store-executed','next-display-scroll','next-display-scroll-post'))
    phases={kind:core(event(lines,kind)[0]) for kind in counts if kind.startswith('phase-')}
    assert phases == {'phase-85CD0A0':69015,'phase-85CD120':69136,'phase-85CD270':69137,'phase-85CD2B0':69261,'phase-85CD340':69262,'phase-85CD3A0':69441,'phase-85CD420':69501,'phase-85CD4B0':69533,'phase-85CD510':69593,'phase-85CD550':70124,'phase-85CD5E0':70188,'phase-85CD640':70248,'phase-85CD6A0':70308,'phase-85CD710':70410,'phase-85CD740':70441}
    for kind in phases:
        row=event(lines,kind)[0];assert fields(row)['current'] == fields(row)['scene'] == f'{S:08X}'
    assert core(event(lines,'actor-85BF600')[0]) == 69135 and core(event(lines,'actor-85BF200')[0]) == 69440
    cleanup_entry,cleanup,mode8=event(lines,'cleanup-entry')[0],event(lines,'cleanup-request')[0],event(lines,'native-mode8')[0]
    assert core(cleanup_entry) == core(cleanup) == 70441 and core(mode8) == 70443
    assert fields(cleanup_entry)['mode'] == fields(cleanup)['mode'] == '7' and fields(mode8)['mode'] == '8'
    assert lines.index(event(lines,'phase-85CD740')[0]) < lines.index(cleanup_entry) < lines.index(cleanup) < lines.index(mode8)
    iw25,iw26=ram['25-phase-85CD740']['iwram'],ram['26-native-mode8']['iwram']
    assert half(iw25,0x2310) == 7 and [half(iw25,a) for a in (0x2314,0x2316,0x2318)] == [1,0,0]
    assert iw25[0x475E] == 1 and iw25[0x475F] == 0 and iw25[0x452A] == 0
    assert half(iw26,0x2310) == 8 and [half(iw26,a) for a in (0x2314,0x2316,0x2318)] == [0,0,0]
    assert long(iw26,0x133C) == long(iw26,0x1344) == 0x02010000
    assert not (D / 'terminal-first-failure.txt').exists() and not (D / 'terminal-error.txt').exists()
    assert core(lines[-1]) == 70443 and 70443-68927 == 1516 < 3000
    return dict(status='ACTUAL_NATIVE_TERMINAL_MODE8_CAPTURE_INTEGRITY_AND_CHAIN_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),launch_sha256=sha(launch_raw),files_verified=258,genuine_states=snapshots,capture_timeline=timeline,exact_previous_whole_Cores_no_normalization=exact_cores,all20_previous_snapshots5RAM_png_display_equal=True,identical_previous_trace_prefix_lines=349,same88_input_records=True,sole_approved_guest_write_ledger=ledger,actual_outcome=launch['outcome'],actual_advances=1516,actual_scroll_store_witnesses=witnessed,actual_IRQ_matches=previous['actual_IRQ_matches'],actual_first_compare=previous['actual_first_compare'],observed_counter143_timing_only=True,earliest_counter1_timing_tested=False,actual_final_IRQ=previous['actual_final_IRQ'],all15_phase_hook_milestones=phases,terminal_D000_entry_core=69015,upper_final_core=69440,auxiliary_final_core=69135,cleanup_entry_core=70441,cleanup_request_core=70441,cleanup_request_mode=7,retired_scene_mode7_checkpoint_core=70442,actual_later_mode8_core=70443,mode8_genuine_State_confirmed=True,exact_hook_counts=counts,strict_source_Core_nine_nonCRC_differences_unchanged=launch['all_Core_byte_differences'],write_only_MMIO_readback_not_asserted=True,source_DI_restore_claim=False,all_hardware_timing_or_historical_E5_closure_claim=False,final_port_completion_claim=False,emulator_launched=False,savestate_loaded=False,guest_memory_written_by_reviewer=False,old_full_suite_rerun=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    report=audit()
    report.update(actor_and_controller_headers_retired_by_mode7_core70442=True,visual_review=dict(native_PNGs_inspected=['18-irq-queue-selected','21-phase-85CD5E0','26-native-mode8'],repeating_lettered_tiles_in_boss_area18=True,later_field_clear21=True,final_mode8_black_stage_border=True,transition_textures_not_compared_to_WSC=True,visual_parity_claim=False))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS258files/27genuineStates/actual8IRQ/executedscroll/cleanup70441→latermode870443;soleapprovedword')


if __name__ == '__main__':
    main()
