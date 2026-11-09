"""Completed replay evidence audit; retain every strict full-Core mismatch."""
import argparse
import json
from pathlib import Path
import re
import struct
import zlib

import verify_gba_shoot_entry_capture_v2 as state

ROOT = Path(__file__).resolve().parents[1]
ROM = '84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
HOST = '421D809E76B91CBC1D122BB44D1BCDD476A224F501717188CCE5F786B2820172'


def differences(original, actual):
    assert len(original) == len(actual)
    ranges = []
    for index, (a, b) in enumerate(zip(original, actual)):
        if a != b:
            if ranges and ranges[-1][1] == index:
                ranges[-1][1] += 1
            else:
                ranges.append([index, index + 1])
    return [dict(core_start=a, core_end=b, native_start=a - 4, native_end=b - 4,
                 expected=original[a:b].hex().upper(), actual=actual[a:b].hex().upper()) for a, b in ranges]


def audit(directory):
    launch_bytes = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_bytes)
    assert launch['launcher_sha256'] == HOST and launch['rom_sha256'] == ROM
    expected_pins = dict(state.PINS)
    expected_pins.pop('tools/bizhawk_probe_gba_collision_producer.lua')
    expected_pins.update({'tools/bizhawk_replay_gba_shoot_entry.lua': 'A73E59919E77FCA67A2DAE6EEA214E1571604818F05008B405CB919300E2C397',
                          'tools/verify_gba_shoot_entry_capture_v2.py': '4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68',
                          'tools/verify_gba_shoot_entry_capture.py': '970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D'})
    assert launch['pins'] == expected_pins
    assert launch['loaded_rom_exact'] and launch['scripts_unchanged'] and launch['checkpoint_copies_unchanged']
    assert launch['completed'] and launch['guest_writes'] == []
    inventory = {path.relative_to(directory).as_posix(): state.prior.sha(path.read_bytes())
                 for path in sorted(directory.rglob('*')) if path.is_file() and path.name != 'launch.json'}
    assert inventory == launch['files']
    assert state.prior.sha((ROOT / 'build/run_gba_shoot_entry_replay_20261109.py').read_bytes()) == HOST
    for name, digest in expected_pins.items():
        assert state.prior.sha((ROOT / name).read_bytes()) == digest
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x800000 and state.prior.sha(rom) == ROM and rom == (directory / 'probe.gba').read_bytes()
    cfg = json.loads((directory / 'config.json').read_bytes())
    for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'):
        assert cfg[key] is False
    assert all(x['Path'].startswith('W:/build/' + directory.name + '/data/') for x in cfg['PathEntries']['Paths'])
    reference = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-b'
    for name, digest in launch['checkpoint_pins'].items():
        data = (directory / 'checkpoint' / name).read_bytes()
        assert state.prior.sha(data) == digest and data == (reference / name).read_bytes()
    original_state = (directory / 'checkpoint/stage7-hp1.State').read_bytes()
    assert state.prior.sha(original_state) == '438C859880FBC9D8F6B700641288E6E62FCEF079075EA64D29A83708EFB51204'
    original, _ = state.checkpoint_core(original_state)
    restored, _ = state.checkpoint_core((directory / 'restored.State').read_bytes())
    assert state.prior.sha(original) == 'C6E8036B8E316D0DC83D091B559414C08635FABEA3EE2467880A110B6216CA6F'
    expected = bytearray(original)
    struct.pack_into('<I', expected, 12, zlib.crc32(rom))
    diff = differences(bytes(expected), restored)
    strict = restored == bytes(expected)
    assert launch['restored_core_exact_except_current_rom_crc'] == strict
    assert launch['restored_core_sha256'] == state.prior.sha(restored)
    assert launch['expected_restored_core_sha256'] == state.prior.sha(bytes(expected))
    length = struct.unpack_from('<I', original)[0]
    assert struct.unpack_from('<I', restored)[0] == length
    assert original[4 + 0x20:4 + 0x130] == restored[4 + 0x20:4 + 0x130], 'CPU state changed during restore'
    assert original[4 + 0x61000:4 + length] == restored[4 + 0x61000:4 + length], 'native extensions changed'
    assert original[-21:] == restored[-21:], 'managed state changed'
    meta = state.prior.fields((directory / 'checkpoint/stage7-hp1.txt').read_text('utf-8'))
    regions = {name: (directory / ('checkpoint/05-stage7-checkpoint-' + name + '.bin')).read_bytes() for name in state.OFFSETS}
    restored_info = state.parse_checkpoint((directory / 'restored.State').read_bytes(), meta, regions, rom)
    replay = state.prior.fields((directory / 'replay.txt').read_text('utf-8').strip())
    assert replay['restored_core'] == '64230' and replay['input_epoch'] == '1' and replay['next_input_relative'] == '64229'
    assert replay['frames'] == '8000' and replay['guest_writes'] == 'none' and replay['new_boss_writes'] == '0'
    assert replay['historical_stage7_consumed'] == 'true' and replay['target_rom'] == ROM
    lines = (directory / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    summaries = [state.prior.fields(line) for line in lines if line.startswith('summary ')]
    assert len(summaries) == 1
    summary = summaries[0]
    assert summary['score_writes'] == summary['boss_writes'] == summary['stage11_writes'] == '0'
    assert summary['stage7_consumed'] == 'true' and summary['initial_core'] == '1'
    assert 64230 <= int(summary['final_core']) <= 72230
    ledger = directory / 'shoot-entry-writes.txt'
    assert not ledger.exists() or ledger.read_bytes() == b'', 'replay must make no new guest writes'
    outcome = (directory / 'shoot-entry-done.txt').read_text('utf-8').strip()
    assert outcome == summary['outcome'] == launch['outcome']
    headers, registers, decoded = {}, {}, {}
    for line in lines:
        if line.startswith('capture='):
            row = state.prior.fields(line)
            if 'observed_core' in row:
                assert row['capture'] not in headers and int(row['observed_core']) <= int(row['export_core'])
                headers[row['capture']] = row
            else:
                match = re.fullmatch(r'capture=(\S+) reg (\S+)=([0-9A-F]+)', line)
                assert match
                registers.setdefault(match[1], {})[match[2]] = int(match[3], 16)
    names = {name.split('-', 1)[1]: name for name in headers}
    for name in headers:
        assert all('R' + str(i) in registers[name] for i in range(16))
        decoded[name] = state.prior.snapshot(directory, name)
    route = {}
    if 'boss-hit-post' in names:
        pre, post = (headers[names[name]] for name in ('boss-hit-pre', 'boss-hit-post'))
        rp, rq = (registers[names[name]] for name in ('boss-hit-pre', 'boss-hit-post'))
        assert pre['before'] == '1' and post['P2HP'] == '0' and 0 < int(pre['P1HP']) < 0x8000
        assert rp['R4'] == rq['R4'] == int(pre['actual_attacker'], 16) == int(pre['FIRST'], 16)
        assert rp['R5'] == rq['R5'] == int(pre['victim'], 16) == int(pre['SECOND'], 16)
        assert rp['R8'] & 0xFFFF == int(pre['computed'], 16) == 0 and rp['R0'] == int(pre['damage']) == 1
        assert rp['R15'] == 0x0836E5E8 and rq['R15'] == 0x0836E5EC
        ordered = ['boss-hit-pre', 'boss-hit-post', 'healthy-root5', 'case5-predicate', 'case5-selected', 'scene-entry', 'scene-saved-health']
        ordered += [name for name in ('initializer-call', 'initializer-return', 'saved-health-restore', 'activation-tail', 'healthy-activation') if name in names]
        cores = [int(headers[names[name]]['observed_core']) for name in ordered]
        assert cores == sorted(cores)
        assert headers[names['case5-predicate']]['eligible'] == 'true'
        assert registers[names['case5-selected']]['R8'] == 0x085C8000
        route = {name: int(headers[names[name]]['observed_core']) for name in ordered}
    checkpoints = {}
    if outcome == 'healthy-native-shoot-activation':
        required = ('initializer-call', 'initializer-return', 'saved-health-restore', 'activation-tail', 'healthy-activation')
        assert all(name in names for name in required) and route
        healthy = decoded[names['healthy-activation']]
        saved = headers[names['scene-saved-health']]
        restored_hp = headers[names['saved-health-restore']]
        hp = int(saved['saved'])
        assert 0 < hp < 0x8000 and int(restored_hp['restored']) == healthy['p1']['hp'] == hp
        assert saved['owner'] == restored_hp['owner']
        assert healthy['stage'] == 11 and healthy['mode'] == 7 and healthy['flags'] & 4
        assert healthy['p1']['active'] and healthy['p2']['active'] and healthy['p2']['hp'] > 0
        for name in ('healthy-activation',):
            metadata = state.prior.fields((directory / (name + '.txt')).read_text('utf-8'))
            cap = names[name]
            memory = {region: (directory / (cap + '-' + region + '.bin')).read_bytes() for region in state.OFFSETS}
            checkpoints[name] = state.parse_checkpoint((directory / (name + '.State')).read_bytes(), metadata, memory, rom)
            assert metadata['stage7_consumed'] == 'true' and int(metadata['input_relative']) == int(metadata['core']) - 1
    inputs = [state.prior.fields(line) for line in (directory / 'trace.txt').read_text('utf-8').splitlines() if line.startswith('input ')]
    assert inputs and inputs[0]['core'] == '64230' and inputs[0]['keys'] == 'Right'
    return dict(status='REPLAY_CAPTURE_INTEGRITY_PASS_STRICT_CORE_MISMATCH' if not strict else 'REPLAY_CAPTURE_INTEGRITY_PASS',
                host_strict_restoration_pass=strict, original_full_Core_sha256=state.prior.sha(original),
                restored_full_Core_sha256=state.prior.sha(restored), expected_CRC_only_Core_sha256=state.prior.sha(bytes(expected)),
                unapproved_Core_differences=diff, unapproved_Core_changed_bytes=sum(row['core_end'] - row['core_start'] for row in diff),
                CPU_register_bank_equal=True, all_five_RAM_regions_equal=True, native_extensions_equal=True, managed_suffix_equal=True,
                launch_sha256=state.prior.sha(launch_bytes), file_count=len(inventory), outcome=outcome,
                native_runtime_activation_observed=outcome == 'healthy-native-shoot-activation',
                exact_checkpoint_replay_equivalence_proven=strict, new_guest_writes=0, historical_boss_writes=1,
                restored_checkpoint=restored_info, capture_count=len(headers), captures=decoded,
                native_route=route, checkpoints=checkpoints, final_sound_method=cfg['SoundOutputMethod'], sound_enabled=False,
                emulator_launched_by_auditor=False, state_loaded_by_auditor=False, no_difference_normalization=True,
                limits=['actual native progress is observed, but the strict CRC-only full-Core restore gate did not pass' if not strict else 'full-port parity remains open'])


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
    print(report['status'], state.prior.sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
