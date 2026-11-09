"""Audit actual A-edge copy ordering and six native controller frames."""
import argparse
import json
from pathlib import Path
import struct

import verify_gba_shoot_entry_capture_v2 as state
from verify_gba_shoot_entry_replay_capture import differences

ROOT = Path(__file__).resolve().parents[1]
ROM = '84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'


def signed(value):
    return value - 0x10000 if value & 0x8000 else value


def decode(iw, ew):
    result = dict(mode=state.prior.word(iw, 0x2310), stage=iw[0x231E], flags=state.prior.word(iw, 0x450A),
                  held=state.prior.word(iw, 0x1302), edge=state.prior.word(iw, 0x1306),
                  FIRST=state.prior.long(iw, 0x489C), SECOND=state.prior.long(iw, 0x48A0),
                  auxiliary=state.prior.long(iw, 0x4D3C))
    for name, pointer in (('p1', result['FIRST']), ('p2', result['SECOND']), ('aux', result['auxiliary'])):
        assert state.prior.actor(pointer)
        at = pointer - 0x02000000
        result[name] = dict(callback=state.prior.long(ew, at), kind=state.prior.word(ew, at + 4) & 15,
                            HP=state.prior.word(ew, at + 0x64), event=state.prior.word(ew, at + 0xBA),
                            held=state.prior.word(ew, at + 0x2C), edge=state.prior.word(ew, at + 0x2E),
                            flags6=state.prior.word(ew, at + 6), flags8=state.prior.word(ew, at + 8),
                            X=state.prior.word(ew, at + 0x34), Y=state.prior.word(ew, at + 0x36),
                            previous_X=state.prior.word(ew, at + 0x38), previous_Y=state.prior.word(ew, at + 0x3A),
                            motion={f'{offset:02X}': signed(state.prior.word(ew, at + offset)) for offset in (0x42, 0x44, 0x46, 0x48, 0x4A, 0x4C)})
    return result


def audit(directory):
    launch_bytes = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_bytes)
    assert launch['launcher_sha256'] == 'DDC1E38B514032299FB7CA43EBFE8E421B58E9DEFB687FF9F1862196B2FECA01'
    assert launch['completed'] and launch['outcome'] == 'six-input-frames-captured'
    pins = {'tools/bizhawk_probe_gba_shoot_first_input.lua': '32D7C0D83CC2C4C030A90D8A1F554FD38EF82637408DC017C9E7C556B55D457A',
            'tools/verify_gba_shoot_entry_capture_v2.py': '4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68',
            'tools/verify_gba_shoot_entry_capture.py': '970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D'}
    assert launch['pins'] == pins and launch['guest_writes'] == []
    assert launch['visible'] is False and launch['physical_background_input'] is False and launch['supplied_save_used'] is False
    assert launch['loaded_rom_exact'] and launch['scripts_unchanged'] and launch['checkpoint_copies_unchanged']
    inventory = {p.relative_to(directory).as_posix(): state.prior.sha(p.read_bytes())
                 for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files']
    for name, digest in pins.items():
        assert state.prior.sha((ROOT / name).read_bytes()) == digest
    assert state.prior.sha((ROOT / 'build/run_gba_shoot_first_input_20261109.py').read_bytes()) == launch['launcher_sha256']
    cfg = json.loads((directory / 'config.json').read_bytes())
    for key in ('SoundEnabled', 'AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM'):
        assert cfg[key] is False
    assert all(x['Path'].startswith('W:/build/' + directory.name + '/data/') for x in cfg['PathEntries']['Paths'])
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert state.prior.sha(rom) == ROM and rom == (directory / 'probe.gba').read_bytes()
    baseline = ROOT / 'build/bizhawk-gba-shoot-entry-replay-20261109-a'
    for name, digest in launch['checkpoint_pins'].items():
        data = (directory / 'checkpoint' / name).read_bytes()
        assert state.prior.sha(data) == digest and data == (baseline / name).read_bytes()
    samples, hooks, pending = [], [], None
    for line in (directory / 'first-input-trace.txt').read_text('utf-8').splitlines():
        row = state.prior.fields(line)
        if line.startswith('kind='):
            samples.append(row)
            pending = row if row['kind'].startswith('before-083') else None
        else:
            assert line.startswith('regs ') and pending is not None
            hooks.append(dict(sample=pending, registers={key: int(value, 16) for key, value in row.items()}))
            pending = None
    assert len(samples) == 25 and len(hooks) == 18
    outer = [row for row in samples if not row['kind'].startswith('before-083')]
    assert [row['kind'] for row in outer] == ['before-input'] + ['after-' + str(i) for i in range(1, 7)]
    snapshots, memory = [], []
    for index, row in enumerate(outer):
        name = '00-before' if index == 0 else f'{index:02d}-after'
        blobs = {region: (directory / f'{name}-{region}.bin').read_bytes() for region in state.OFFSETS}
        assert all(len(blobs[region]) == size for region, (_, size) in state.OFFSETS.items())
        png = (directory / (name + '.png')).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', png, 16) == (240, 160)
        decoded = decode(blobs['iwram'], blobs['ewram'])
        assert int(row['core']) == 68927 + index and decoded['mode'] == 7 and decoded['stage'] == 11 and decoded['flags'] == 6
        assert decoded['FIRST'] == 0x02011710 and decoded['SECOND'] == 0x02011828
        assert decoded['p1']['HP'] == int(row['P1HP']) == 4 and decoded['p2']['HP'] == int(row['P2HP']) == 37
        for key, value in dict(held=decoded['held'], edge=decoded['edge'], pheld=decoded['p1']['held'], pedge=decoded['p1']['edge'],
                               x=decoded['p1']['X'], y=decoded['p1']['Y'], callback=decoded['p1']['callback'], event=decoded['p1']['event']).items():
            assert int(row[key], 16) == value, 'raw trace/RAM ' + key
        expected = 0x40 if index == 1 else 0
        assert decoded['held'] == decoded['edge'] == decoded['p1']['held'] == decoded['p1']['edge'] == expected
        decoded['core'] = int(row['core'])
        snapshots.append(decoded)
        memory.append(blobs)
    for index in range(6):
        current, previous = (0x40 if index == 0 else 0), (0x40 if index == 1 else 0)
        for step, address in enumerate((0x08375138, 0x0837513C, 0x08375140)):
            hook = hooks[index * 3 + step]
            row, r = hook['sample'], hook['registers']
            assert row['kind'] == f'before-{address:08X}' and int(row['core']) == int(outer[index + 1]['core']) - 1
            assert r['R4'] == 0x02011710 and r['R3'] == 0 and r['R0'] == r['R1'] == current and r['R15'] == address + 4
            assert int(row['held'], 16) == int(row['edge'], 16) == current
            assert int(row['pheld'], 16) == (previous if step == 0 else current)
            assert int(row['pedge'], 16) == (current if step == 2 else previous)
    source_meta = state.prior.fields((directory / 'checkpoint/healthy-activation.txt').read_text('utf-8').strip())
    original, _ = state.checkpoint_core((directory / 'checkpoint/healthy-activation.State').read_bytes())
    restored, _ = state.checkpoint_core((directory / 'restored.State').read_bytes())
    assert state.prior.sha(original) == '6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
    raw_diff = [dict(offset=i, expected=a, actual=b) for i, (a, b) in enumerate(zip(original, restored)) if a != b]
    assert len(original) == len(restored) and raw_diff == launch['all_Core_byte_differences']
    strict = original == restored
    assert launch['restored_core_exact_except_current_rom_crc'] == strict
    assert launch['CPU_bank_equal'] and original[0x24:0x134] == restored[0x24:0x134]
    length = struct.unpack_from('<I', original)[0]
    assert launch['native_extensions_equal'] and original[4 + 0x61000:4 + length] == restored[4 + 0x61000:4 + length]
    assert launch['managed_suffix_equal'] and original[4 + length:] == restored[4 + length:]
    restored_info = state.parse_checkpoint((directory / 'restored.State').read_bytes(), source_meta, memory[0], rom)
    final_meta = dict(source_meta, core='68933', input_relative='68932', P1HP='4', P2HP='37')
    final_state = state.parse_checkpoint((directory / 'after-input.State').read_bytes(), final_meta, memory[-1], rom)
    assert snapshots[0]['p1']['callback'] == 0x0835620C and snapshots[0]['p1']['event'] == 0
    assert snapshots[1]['p1']['callback'] == 0x08356B78 and snapshots[1]['p1']['event'] == 4
    assert snapshots[-1]['p1']['callback'] == 0x08356D40 and snapshots[-1]['p1']['event'] == 8
    assert snapshots[-1]['p1']['Y'] < snapshots[0]['p1']['Y'] and snapshots[-1]['p1']['motion']['44'] < 0
    return dict(status='ACTUAL_FIRST_NATIVE_A_EDGE_AND_JUMP_PASS', launch_sha256=state.prior.sha(launch_bytes),
                file_count=len(inventory), snapshot_sets=7, hook_records=len(hooks),
                actual_A_edge_mask=0x40, write_order_verified=True, R15_pipeline_delta=4,
                snapshots=snapshots, raw_hook_records=hooks, new_guest_writes=0,
                jump_accepted_callback_event=True, actual_vertical_motion_after_six_frames=True,
                restored_checkpoint=restored_info, after_six_frames_checkpoint=final_state,
                original_full_Core_exact=strict, strict_restore_changed_bytes=len(raw_diff),
                all_actual_Core_differences=differences(original, restored),
                normalization_performed=False, emulator_launched_by_auditor=False,
                final_sound_method=cfg['SoundOutputMethod'], sound_enabled=False,
                qualification='actual controller acceptance and jump under the loaded healthy state; strict full-Core restore difference remains reported independently')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    report = audit(a.capture.resolve())
    report['verifier_sha256'] = state.prior.sha(Path(__file__).read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', state.prior.sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
