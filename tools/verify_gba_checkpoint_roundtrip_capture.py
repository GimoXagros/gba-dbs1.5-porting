"""Audit the one no-frame control; retain functional restore differences."""
import argparse
import json
from pathlib import Path
import struct
import zlib

import verify_gba_shoot_entry_capture_v2 as state
from verify_gba_shoot_entry_replay_capture import differences

ROOT = Path(__file__).resolve().parents[1]


def audit(directory):
    launch_bytes = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_bytes)
    assert launch['launcher_sha256'] == '5AA85E58C28217D5C5605F27951E338E9922BE5E2F2631767EA18C90F86936B0'
    assert launch['completed'] and launch['outcome'] == 'checkpoint-roundtrip-only'
    assert launch['loaded_rom_exact'] and launch['scripts_unchanged'] and launch['checkpoint_copies_unchanged']
    assert launch['guest_writes'] == [] and launch['matched_fixed_core_except_rom_crc']
    assert launch['restored_core_exact_except_current_rom_crc'] is False
    inventory = {p.relative_to(directory).as_posix(): state.prior.sha(p.read_bytes())
                 for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    assert inventory == launch['files']
    fixed_dir = ROOT / 'build/bizhawk-gba-shoot-entry-replay-20261109-a'
    fixed_launch = json.loads((fixed_dir / 'launch.json').read_bytes())
    old_audit = ROOT / 'build/gba-shoot-entry-replay-capture-qa-20261109/report.json'
    assert state.prior.sha(old_audit.read_bytes()) == '5FF3EC35673391DF6A53462A035E28654E937DEE35688C5E9E8EB1FCDFBB225D'
    old_report = json.loads(old_audit.read_bytes())
    assert state.prior.sha((fixed_dir / 'launch.json').read_bytes()) == old_report['launch_sha256']
    expected_pins = dict(fixed_launch['pins'], **{'tools/bizhawk_gba_checkpoint_roundtrip_control.lua':
                                               '592083E4C310E48AED75DA08E992821E0CC0B7BE6EF69625CD660AE20ABC45F5'})
    assert launch['pins'] == expected_pins
    for name, digest in expected_pins.items():
        assert state.prior.sha((ROOT / name).read_bytes()) == digest
    assert state.prior.sha((ROOT / 'build/run_gba_checkpoint_roundtrip_20261109.py').read_bytes()) == launch['launcher_sha256']
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert state.prior.sha(rom) == launch['rom_sha256'] == state.prior.ROM
    assert rom == (directory / 'probe.gba').read_bytes()
    baseline = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-b'
    for name, digest in launch['checkpoint_pins'].items():
        b = (directory / 'checkpoint' / name).read_bytes()
        assert state.prior.sha(b) == digest and b == (baseline / name).read_bytes()
    original, _ = state.checkpoint_core((directory / 'checkpoint/stage7-hp1.State').read_bytes())
    control, _ = state.checkpoint_core((directory / 'restored.State').read_bytes())
    fixed, _ = state.checkpoint_core((fixed_dir / 'restored.State').read_bytes())
    assert state.prior.sha(original) == 'C6E8036B8E316D0DC83D091B559414C08635FABEA3EE2467880A110B6216CA6F'
    assert state.prior.sha(fixed) == '42448E25FAF97F523C2FDEFA26C64B6E71414ABC424F937A5B31EB3B9809D72E'
    expected_control = bytearray(fixed)
    struct.pack_into('<I', expected_control, 12, zlib.crc32(rom))
    assert control == bytes(expected_control), 'all control vs fixed postload bytes except ROMCRC must equal'
    assert state.prior.sha(control) == '09D83694EE7BABF9B32E2C2275CA21E9925BFCCC7A811723F656A78D94D5E7CA'
    assert control != original and launch['restored_core_sha256'] == state.prior.sha(control)
    assert launch['expected_restored_core_sha256'] == state.prior.sha(original)
    diff = differences(original, control)
    assert diff == old_report['unapproved_Core_differences']
    assert sum(row['core_end'] - row['core_start'] for row in diff) == 12
    meta = state.prior.fields((directory / 'checkpoint/stage7-hp1.txt').read_text('utf-8').strip())
    regions = {name: (directory / ('checkpoint/05-stage7-checkpoint-' + name + '.bin')).read_bytes() for name in state.OFFSETS}
    parsed = state.parse_checkpoint((directory / 'restored.State').read_bytes(), meta, regions, rom)
    replay = state.prior.fields((directory / 'replay.txt').read_text('utf-8').strip())
    assert parsed['frame'] == 64230 and replay['restored_core'] == '64230' and replay['input_epoch'] == '1'
    assert replay['frames'] == '1' and replay['guest_writes'] == 'none' and replay['new_boss_writes'] == '0'
    assert not (directory / 'trace.txt').exists() and not (directory / 'shoot-entry-trace.txt').exists()
    assert not (directory / 'shoot-entry-writes.txt').exists()
    cfg = json.loads((directory / 'config.json').read_bytes())
    for name in ('SoundEnabled', 'AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM'):
        assert cfg[name] is False
    arithmetic = {}
    for name, env_offset, last_offset, periods in (('square1', 0x130, 0x140, 84), ('square2', 0x144, 0x150, 93)):
        before = struct.unpack_from('<I', original, 4 + env_offset)[0]
        after = struct.unpack_from('<I', control, 4 + env_offset)[0]
        old_last = struct.unpack_from('<i', original, 4 + last_offset)[0]
        new_last = struct.unpack_from('<i', control, 4 + last_offset)[0]
        assert ((before >> 21 & 7) + periods) % 8 == after >> 21 & 7
        assert new_last - old_last == periods * 32768
        arithmetic[name] = dict(periods=periods, period_cycles=32768, old_relative_time=old_last, new_relative_time=new_last)
    lfsr = struct.unpack_from('<I', original, 4 + 0x17C)[0]
    for _ in range(28):
        feedback = (lfsr ^ (lfsr >> 1) ^ 1) & 1
        lfsr >>= 1
        lfsr = lfsr | 0x4000 if feedback else lfsr & ~0x4000
    assert lfsr == struct.unpack_from('<I', control, 4 + 0x17C)[0] == 0x7A94
    old_last, new_last, next_event = (struct.unpack_from('<I', data, 4 + offset)[0]
                                     for data, offset in ((original, 0x184), (control, 0x184), (control, 0x188)))
    assert new_last - old_last == 28 * 32 and next_event - new_last == 64
    arithmetic['noise'] = dict(steps=28, old_live_period=32, restored_period=64,
                              old_lfsr=0x2BB7, new_lfsr=lfsr, last_event_advance=896)
    assert struct.unpack_from('<H', original, 4 + 0x528)[0] == struct.unpack_from('<H', control, 4 + 0x528)[0] == 0x200F
    assert struct.unpack_from('<H', original, 4 + 0x534)[0] == 1 and struct.unpack_from('<H', control, 4 + 0x534)[0] == 0
    return dict(status='SAME_ROM_NO_FRAME_CONTROL_MATCHES_FIXED_POSTLOAD', file_count=len(inventory),
                launch_sha256=state.prior.sha(launch_bytes), control_Core_sha256=state.prior.sha(control),
                fixed_Core_sha256=state.prior.sha(fixed), original_Core_sha256=state.prior.sha(original),
                postload_equal_except_ROM_CRC=True, original_exact_Core_equivalence=False,
                strict_original_Core_failure_preserved=True, functional_changed_bytes=12,
                all_actual_differences=diff, square_phase_arithmetic=arithmetic,
                serial_RCNT_change=dict(original=1, postload=0, SIOCNT=0x200F, functional_SC_bit=True),
                parsed_control=parsed, no_game_frame_or_policy=True, new_guest_writes=0,
                original_checkpoint_copies_unchanged=True, no_difference_normalization=True,
                qualification='12 functional audio/serial restore changes reproduce on D0 without the five-word patch; healthy fixed-ROM activation is observed under that controlled loaded state, not proven equivalent to the original exact Core',
                emulator_launched_by_auditor=False, state_loaded_by_auditor=False)


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
