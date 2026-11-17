"""Audit the finalized 75BD replay that observes the first bad AI branch."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

from PIL import Image, ImageChops

import check_type8_corrected_campaign_capture as campaign
from check_ai_producer_provenance import FAIL, PIN
from check_type8_event_provenance_capture import register_order_only
from verify_gba_shoot_entry_capture import ROOT, fields, ledger, long, sha, word
import verify_gba_shoot_entry_capture_v2 as state


RUN = 'bizhawk-ai-provenance-v82-20261117-a'
BASELINE = ROOT / 'build' / campaign.RUN
WRAPPER = 'tools/bizhawk_probe_ai_producer_provenance.lua'
HOST = 'BBB6960EB4C55A927946F190399BFD947695B64A830BA3C149769BC653531FC3'
PINSET = 'C994BC261745B10FCA9B156BA70C43254E95A9AD1572CC351BEFED3E17B421A3'
INDEPENDENT = 'F6491ADA5182D17032235C40ACCC2A6E723E3E834FEC6860336E053B50069F19'
BASELINE_MANIFEST = '18F2BA67F432CE11037FFEE8F8D2F1ECB3DA16DC76831FD9886A42284520578A'
JOURNAL = 'ai-producer-provenance.txt'


def read_lines(path):
    return path.read_text('utf-8').splitlines()


def manifest(directory):
    raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(raw)
    assert launch['completed'] is True
    actual = {path.relative_to(directory).as_posix(): sha(path.read_bytes()) for path in sorted(directory.rglob('*'))
              if path.is_file() and path.name != 'launch.json'}
    assert actual == launch['files']
    return sha(raw), launch


def binding(directory, host_exit):
    assert host_exit == 0, 'original replay process must have reported its expected observer stop'
    ref_sha, original = manifest(BASELINE)
    digest, replay = manifest(directory)
    assert ref_sha == BASELINE_MANIFEST and original['outcome'] == 'bounded-no-activation'
    assert replay['outcome'] == FAIL and replay['phase_kind'] == 'readonly-first-invalid-ai-parameter-and-target'
    assert all(replay[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(replay[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                                'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert sha((ROOT / 'build/run_ai_provenance_v82_20261117.py').read_bytes()) == replay['launcher_sha256'] == HOST
    pin_bytes = (ROOT / 'build/ai-provenance-reviewed-pins-20261117.json').read_bytes()
    assert sha(pin_bytes) == replay['reviewed_pins_sha256'] == PINSET
    assert replay['pins'] == json.loads(pin_bytes) == original['pins'] | {WRAPPER: PIN}
    assert {name: sha((ROOT / name).read_bytes()) for name in replay['pins']} == replay['pins']
    report = (ROOT / 'build/ai-producer-delta-independent-20261117/report.json').read_bytes()
    assert sha(report) == INDEPENDENT
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == original['rom_sha256'] == replay['rom_sha256'] == campaign.ROM
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == replay['exe_sha256'] == original['exe_sha256']
    assert rom == (directory / 'probe.gba').read_bytes() == (BASELINE / 'loaded-rom.bin').read_bytes()
    assert replay['guest_writes'] == original['guest_writes']
    expected_args = [arg.replace(campaign.RUN, RUN).replace(campaign.WRAPPER, WRAPPER) for arg in original['arguments']]
    assert replay['arguments'] == expected_args
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(item['Path'] == f'W:/build/{RUN}/data/{i}' for i, item in enumerate(config['PathEntries']['Paths']))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    generated = {name: x for name, x in replay['files'].items() if name.startswith('data/')}
    assert set(generated) <= {'data/104/probe.SaveRAM'}
    return digest, original, replay, rom, generated


def shared_prefix(directory, original, replay):
    files = [name for name in original['files'] if re.match(r'^0[1-9]-.*\.(?:bin|png)$', name)]
    assert len(files) == 63
    assert {name: replay['files'][name] for name in files} == {name: original['files'][name] for name in files}
    input_base, input_new = (read_lines(folder / 'trace.txt') for folder in (BASELINE, directory))
    assert input_new == input_base[:len(input_new)]
    old_campaign, new_campaign = (read_lines(folder / 'campaign-complete-trace.txt') for folder in (BASELINE, directory))
    assert old_campaign[:-1] == new_campaign[:-1]
    trace = {folder: register_order_only(folder / 'shoot-entry-trace.txt') for folder in (BASELINE, directory)}
    old_prefix = [line for line in trace[BASELINE] if line.startswith('capture=')]
    new_prefix = [line for line in trace[directory] if line.startswith('capture=')]
    assert new_prefix[:len(old_prefix)] == old_prefix
    old_ring = [line for line in trace[BASELINE] if line.startswith('seq=')]
    new_ring = [line for line in trace[directory] if line.startswith('seq=')]
    assert old_ring == new_ring
    assert (directory / 'shoot-entry-writes.txt').read_bytes() == (BASELINE / 'shoot-entry-writes.txt').read_bytes()
    writes, scores, bosses = ledger(read_lines(directory / 'shoot-entry-writes.txt'))
    assert (scores, bosses) == (6, 0)
    type8_base, type8_new = (read_lines(folder / 'type8-event-provenance.txt') for folder in (BASELINE, directory))
    assert type8_base[1:] == type8_new[1:]
    assert fields(trace[directory][-1])['stage11_writes'] == '0'
    return len(files), len(input_new), len(old_prefix), len(old_ring), fields(new_campaign[-1]), writes


def checked_journal(directory, rom):
    lines = read_lines(directory / JOURNAL)
    summary = fields(lines[0])
    assert summary['guest_writes'] == 'none' and summary['input'] == 'frozen-parent'
    first = [fields(line) for line in lines if line.startswith('first seq=')]
    ring = [fields(line) for line in lines if line.startswith('seq=')]
    count = int(summary['serial'])
    assert [int(row['seq']) for row in ring] == list(range(max(1, count - 127), count + 1))
    assert [int(row['core']) for row in ring] == sorted(int(row['core']) for row in ring)
    assert all((row['progress'], row['stage'], row['cpu']) == ('2', '9', '14') for row in first + ring)
    assert [row['kind'] for row in first] == [
        'raw-id', 'row-index', 'first-read', 'first-copy', 'parameter-copies-complete', 'selector-write']
    raw, index, read, first_store, final_parameters, selector = first
    assert [int(row['seq']) for row in first] == sorted({int(row['seq']) for row in first})
    assert raw['raw_id'] == index['effective_id'] == '14'
    assert int(raw['r0'], 16) == int(index['r0'], 16) == int(raw['raw_id'])
    assert raw['config_cpu_address'] == '0300231C' and index['stride'] == '17' and int(index['r1'], 16) == 17
    assert [int(row['reported_pc'], 16) for row in first[:5]] == [
        0x080C6D64, 0x080C6D74, 0x080C6D80, 0x080C6D88, 0x080C6EB4]
    assert read['row_base'] == '080C6C7C' and read['offset'] == '238' and read['src'] == '080C6D6A'
    assert int(read['r8'], 16) + int(read['r1'], 16) == int(read['src'], 16)
    assert int(read['src'], 16) >= int(read['row_base'], 16) + 8 * 17
    source = rom[0xC6D6A:0xC6D6A+17]
    assert read['row17'] == source.hex().upper() and read['halfword'] == f'{word(source, 0):04X}'
    assert first_store['dst'] == '03004D8A' and first_store['value'] == read['halfword']
    assert int(first_store['r0'], 16) & 0xFFFF == int(read['halfword'], 16)
    assert int(first_store['r8'], 16) + 2 == int(first_store['dst'], 16)
    params = bytes.fromhex(final_parameters['params_03004D88'])
    assert len(params) == 0x26
    copies = [params[2:6], params[6:8], params[0x1C:0x22], params[0x22:0x23], params[8:10], params[0x24:0x26]]
    assert b''.join(copies) == source and params[0x23] == 0
    assert long(rom, 0xC6D68) == 0xE92D0001 and long(rom, 0xC6D6C) == 0xE3A01011
    assert selector['address'] == '03003D50' and selector['value'] == '000F'
    load, branch = ring[-2:]
    assert (load['kind'], branch['kind']) == ('selector-load', 'target')
    assert (load['reported_pc'], branch['reported_pc']) == ('080C65F0', '080C65F4')
    assert int(selector['seq']) < int(load['seq']) < int(branch['seq'])
    assert all(row['selector'] == '000F' and row['index'] == '0F' and row['table'] == '080C65F4'
               and row['slot'] == '080C6630' and row['word'] == 'E3A00000' for row in (load, branch))
    assert branch['pc'] == '080C65F0' and branch['target'] == branch['r9'] == 'E3A00000'
    assert long(rom, int(branch['slot'], 16) - 0x08000000) == int(branch['target'], 16)
    assert long(rom, 0xC65F0) == 0xE12FFF19
    return summary, first, ring[-6:]


def checked_stop(directory, rom, final, branch):
    trace = read_lines(directory / 'shoot-entry-trace.txt')
    prior = read_lines(directory / 'shoot-entry-first-failure.txt')
    header, detail = prior[0].split(' detail=', 1)
    first_failure = fields(header) | fields(detail)
    assert first_failure['outcome'] == FAIL and first_failure['timing'] == 'before-instruction'
    assert first_failure['core'] == branch['core'] and int(final['core']) == int(branch['core']) + 1
    assert [first_failure[name] for name in ('pc', 'selector', 'index', 'slot', 'target')] == [
        branch[name] for name in ('pc', 'selector', 'index', 'slot', 'target')]
    assert 'failure_checkpoint_saved=true' in trace
    name = next(fields(line)['capture'] for line in trace if re.match(r'^capture=\d+-first-invalid-ai-collider-target observed_core=', line))
    raw = {region: (directory / f'{name}-{region}.bin').read_bytes() for region in state.OFFSETS}
    iw = raw['iwram']
    assert word(iw, 0x3D50) == 0xF and word(iw, 0x4500) == 7177
    metadata = fields((directory / 'failure-observed.txt').read_text('utf-8').strip())
    checkpoint = directory / 'failure-observed.State'
    saved = state.parse_checkpoint(checkpoint.read_bytes(), metadata, raw, rom)
    assert saved['frame'] == int(final['core'])
    core, _ = state.checkpoint_core(checkpoint.read_bytes())
    saved_cpu = dict(zip([f'R{x}' for x in range(16)] + ['CPSR'], struct.unpack_from('<17I', core, 4 + 0x20)))
    assert saved_cpu['R9'] == int(branch['target'], 16) and saved_cpu['R15'] == int(branch['target'], 16) + 4
    assert saved_cpu['CPSR'] & 0x1F == 0x10
    saved['reg_R15_after_branch'] = f"{saved_cpu['R15']:08X}"
    saved['CPSR_after_branch'] = f"{saved_cpu['CPSR']:08X}"
    with ZipFile(checkpoint) as archive:
        data = json.loads(archive.read('UserData.txt'))['o']
        assert data['output'] == 'W:/build/' + RUN and data['probe_sha256'] == campaign.ROM
        with Image.open(BytesIO(archive.read('Framebuffer.bmp'))) as image, Image.open(directory / f'{name}.png') as png:
            assert ImageChops.difference(image.convert('RGB'), png.convert('RGB')).getbbox() is None
    with Image.open(BASELINE / 'screen.png') as late, Image.open(directory / f'{name}.png') as early:
        saved['screenshot_rgb_equal_to_cap'] = ImageChops.difference(late.convert('RGB'), early.convert('RGB')).getbbox() is None
    equal_late = {region: raw[region] == (BASELINE / f'{region}.bin').read_bytes() for region in state.OFFSETS}
    return first_failure, saved, equal_late, raw


def action_and_behavior(rom, raw, selector):
    iw, ew = raw['iwram'], raw['ewram']
    # The bus hook sees the previous LDRH's post-incremented source.
    assert selector['reported_pc'] == '080110EC' and selector['lr'] == '080C69B8'
    assert (selector['r5'], selector['r8'], selector['old'], selector['bus_flags']) == ('03003D50', '0000000F', '0000', '2000')
    assert struct.unpack_from('<2I', rom, 0x110E0) == (0xE0D480B2, 0xE0C580B2)
    assert long(rom, 0xC69B4) == 0xEBFD29C8
    ordinal_owner, writer_dst, actions = struct.unpack_from('<3I', rom, 0xC6A34)
    assert (ordinal_owner, writer_dst, actions) == (0x03003D68, 0x03003D50, 0x080C4FC4)
    ordinal = word(iw, ordinal_owner - 0x03000000)
    assert ordinal == 0xFFFF and ordinal * 18 == int(selector['r1'], 16) == 0x0011FFEE
    selected = actions + ordinal * 18
    assert selected == 0x081E4FB2 and int(selector['r4'], 16) == selected + 2
    full_record = rom[selected - 0x08000000:selected - 0x08000000 + 18]
    assert full_record == iw[0x3D50:0x3D50 + 18] and word(full_record, 0) == 0xF
    assert selected >= actions + 258 * 18
    field = dict(read_from=f'{selected:08X}', action_table=f'{actions:08X}', ordinal=f'{ordinal:04X}',
                 ordinal_owner=f'{ordinal_owner:08X}', action_bytes=full_record.hex().upper(),
                 writer_instruction='080110E4', callback_reported_pc=selector['reported_pc'])
    # Reconstruct the unhooked behavior read using the stopped owner's fields.
    cpu = 0x11828
    assert word(ew, cpu + 8) & 0x4000 == 0
    ai = 0x4D88
    assert struct.unpack_from('<2h', iw, ai + 0x10) == (8, 80)
    assert 80 <= iw[ai + 0x1C] and 8 > iw[ai + 0x1E]  # Group remains 2 in 080C6468..080C6494.
    bank = word(iw, ai + 0xA)
    assert bank == 14 * 384 and bank >= 8 * 384
    assert long(rom, 0xC658C) == 0x080C3FC0 and word(iw, 0x4DC4) & 3 == 0
    random_word = word(iw, 0x4DB2)
    cell = ((random_word >> 1) & 31) * 2
    assert random_word == 0x6E0A and cell == 10
    address = 0x080C3FC0 + bank + 2 * 64 + cell
    assert address == 0x080C554A and word(rom, address - 0x08000000) == ordinal
    return field, dict(bank_offset=bank, group=2, cell_byte_offset=cell, address=f'{address:08X}',
                       word=f'{ordinal:04X}', directly_hooked=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--host-exit', type=int, required=True)
    args = parser.parse_args()
    directory = ROOT / 'build' / RUN
    digest, original, replay, rom, generated = binding(directory, args.host_exit)
    for name in ('campaign-complete-done.txt', 'shoot-entry-done.txt'):
        assert (directory / name).read_text('utf-8').strip() == FAIL
    common_count, input_count, trace_count, ring_count, final, writes = shared_prefix(directory, original, replay)
    summary, first, tail = checked_journal(directory, rom)
    assert summary['core'] == final['core'] and final['outcome'] == FAIL
    stop, checkpoint, terminal_equal, raw = checked_stop(directory, rom, final, tail[-1])
    action, behavior = action_and_behavior(rom, raw, first[-1])
    result = dict(status='AI_PRODUCER_ACTUAL_CAPTURE_QA_PASS', outcome=FAIL, original_host_exit=args.host_exit,
                  rom_sha256=campaign.ROM, launch_sha256=digest, files_verified=len(replay['files']),
                  shared_snapshot_files_exact=common_count, input_trace_prefix_lines_exact=input_count,
                  shared_capture_trace_lines_equivalent=trace_count, shared_frozen_native_rows_exact=ring_count,
                  authorized_writes_exact=writes, isolated_saves=generated,
                  first_parameter_and_selector_records=first, last_ai_journal_rows=tail,
                  first_failure=stop, checkpoint=checkpoint, terminal_dump_bytes_equal_to_cap=terminal_equal,
                  parameter_overread_confirmed=True, action_copy_confirmed=action, behavior_read_reconstruction=behavior,
                  parameter_overread_sole_cause_proven=False,
                  emulator_launched_by_auditor=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']} {sha(args.output.read_bytes())}")


if __name__ == '__main__':
    main()
