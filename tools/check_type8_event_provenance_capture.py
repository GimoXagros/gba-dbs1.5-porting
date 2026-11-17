"""Audit the finalized 933C replay against its frozen failure and native predecessor."""
import argparse
from itertools import groupby
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

from check_campaign_first_invalid_producer import FAILURE, OUTCOME, PINS, ROM, ROOT, RUN, row_store
from check_type8_event_provenance import HOOKS, PIN
from verify_gba_shoot_entry_capture import fields, long, sha, word
import verify_gba_shoot_entry_capture_v2 as state


BASELINE = ROOT / 'build' / RUN
REPLAY = 'bizhawk-type8-provenance-v80-20261117-a'
PROVENANCE = 'type8-event-provenance.txt'
EXIT_SAVE = 'data/104/probe.SaveRAM'
EXIT_SAVE_SHA = 'A10123E71ACE848DD3B9760BACB345EBB5AF994AFB98BEF1DBD356CCD3037C11'
WRAPPER = 'tools/bizhawk_probe_type8_event_provenance.lua'
HOST_PATH = 'build/run_type8_provenance_v80_20261117.py'
HOST = '5D7B422DFDF4DFD77C1996B8E5B1BBBB4CBEC71343825D537949049AE9B2742A'
PIN_PATH = 'build/type8-provenance-reviewed-pins-20261117.json'
PIN_DIGEST = 'D7A86B26C2B07D027E806BF44042207026F1EF92BCB597E1CD4BDFAB7C05DA63'
BASELINE_MANIFEST = 'EC21774EAE3E46C420B17D83C0C1AACDDBAA3BF922120064EDC0851326DFF571'
REFERENCE_QA = '33EAF8EEBC738AD265A90A70B9A6B57FE333C75854CD9F7E2FF5A7BF382D206A'
MODEL_QA = 'A20FB90505A8032457C1C898AD43AE93924F4C534A57AA11AF03144AF37CEF12'
OWNER = '02011828'
RESOURCE = '0861CF0C'


def manifest(path, pinned_hash=None):
    blob = (path / 'launch.json').read_bytes()
    if pinned_hash:
        assert sha(blob) == pinned_hash
    launch = json.loads(blob)
    assert launch['completed'] is True and launch['outcome'] == OUTCOME
    actual = {p.relative_to(path).as_posix(): sha(p.read_bytes()) for p in sorted(path.rglob('*'))
              if p.is_file() and p.name != 'launch.json'}
    assert actual == launch['files']
    return launch, sha(blob)


def register_order_only(path):
    def key(line):
        match = re.fullmatch(r'(?:(capture=\S+) )?reg \w+=[0-9A-F]+', line)
        return (match[1] or 'first-failure-registers') if match else None

    lines = path.read_text('utf-8').splitlines()
    return [line for group, members in groupby(lines, key) for line in (sorted(members) if group else members)]


def compare(run):
    base, _ = manifest(BASELINE, BASELINE_MANIFEST)
    launch, digest = manifest(run)
    assert sha((ROOT / HOST_PATH).read_bytes()) == launch['launcher_sha256'] == HOST
    pin_raw = (ROOT / PIN_PATH).read_bytes()
    assert sha(pin_raw) == launch['reviewed_pins_sha256'] == PIN_DIGEST
    pins = PINS | {WRAPPER: PIN}
    assert json.loads(pin_raw) == launch['pins'] == pins and base['pins'] == PINS
    assert {name: sha((ROOT / name).read_bytes()) for name in pins} == pins
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == launch['exe_sha256']
    baseline_qa = ROOT / 'build/campaign-first-invalid-producer-qa-20261117/actual.json'
    model_qa = ROOT / 'build/type8-event-provenance-qa-20261117/lua.json'
    assert sha(baseline_qa.read_bytes()) == REFERENCE_QA and sha(model_qa.read_bytes()) == MODEL_QA
    for key in ('rom_sha256', 'exe_sha256', 'loaded_rom_exact', 'scripts_unchanged', 'visible',
                'physical_background_input', 'supplied_save_used', 'final_gba_cheat', 'guest_writes',
                'host_stop_requested', 'host_deadline_reached'):
        assert launch[key] == base[key], key
    assert launch['rom_sha256'] == ROM and launch['phase_kind'] == 'readonly-type8-predecessor-known-failure-replay'
    old_args = [arg.replace(RUN, REPLAY).replace('tools/bizhawk_probe_campaign_complete.lua', WRAPPER)
                for arg in base['arguments']]
    assert launch['arguments'] == old_args
    assert set(launch['files']) == set(base['files']) | {PROVENANCE, EXIT_SAVE}
    assert launch['files'][EXIT_SAVE] == EXIT_SAVE_SHA and (run / EXIT_SAVE).stat().st_size == 131088
    differing = {name for name, checksum in base['files'].items() if launch['files'][name] != checksum}
    assert differing <= {'config.json', 'failure-observed.State', 'shoot-entry-first-failure.txt', 'shoot-entry-trace.txt'}, differing
    for name in ('shoot-entry-first-failure.txt', 'shoot-entry-trace.txt'):
        assert register_order_only(run / name) == register_order_only(BASELINE / name), name
    old_config = json.loads((BASELINE / 'config.json').read_text('utf-8').replace(RUN, REPLAY))
    new_config = json.loads((run / 'config.json').read_bytes())
    assert old_config['RecentLua']['recentlist'][0] == r'W:\tools\bizhawk_probe_campaign_complete.lua'
    old_config['RecentLua']['recentlist'][0] = r'W:\tools\bizhawk_probe_type8_event_provenance.lua'
    assert re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z', new_config['UpdateLastCheckTimeUtc'])
    old_config['UpdateLastCheckTimeUtc'] = new_config['UpdateLastCheckTimeUtc']
    assert new_config == old_config
    assert len([name for name in base['files'] if re.match(r'^0[1-5]-.*\.(bin|png)$', name)]) == 35
    rom = (run / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM and rom == (run / 'probe.gba').read_bytes()
    pre = (run / 'shoot-entry-first-failure.txt').read_text('utf-8').splitlines()
    final = (run / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    _, store, _ = row_store(pre, final)
    assert 'score_writes=2 boss_writes=0' in final[-1]
    checkpoint = run / 'failure-observed.State'
    checkpoint_meta = fields((run / 'failure-observed.txt').read_text('utf-8').strip())
    regions = {name: (run / f'{FAILURE}-{name}.bin').read_bytes() for name in state.OFFSETS}
    saved = state.parse_checkpoint(checkpoint.read_bytes(), checkpoint_meta, regions, rom)
    assert saved['frame'] == 8673
    with ZipFile(BASELINE / checkpoint.name) as old, ZipFile(checkpoint) as new:
        assert old.namelist() == new.namelist()
        for name in old.namelist():
            if name == 'UserData.txt':
                expected = json.loads(old.read(name))
                assert expected['o']['output'] == 'W:/build/' + RUN
                expected['o']['output'] = 'W:/build/' + REPLAY
                assert json.loads(new.read(name)) == expected
            elif name == 'Core.bin.zst':
                old_core, _ = state.checkpoint_core((BASELINE / checkpoint.name).read_bytes())
                new_core, _ = state.checkpoint_core(checkpoint.read_bytes())
                assert new_core == old_core, 'native state differs'
            else:
                assert new.read(name) == old.read(name), name
    return rom, digest, store, differing, saved, launch['files'][PROVENANCE]


def verify_chain(lines, rom):
    summary = fields(lines[0])
    assert summary['core'] == '8673' and summary['timing'] == 'before-instruction'
    assert summary['guest_writes'] == 'none' and summary['input'] == 'frozen-parent'
    rows = list(map(fields, (line for line in lines if line.startswith('seq='))))
    serial = int(summary['serial'])
    assert len(rows) <= 256
    assert [int(row['seq']) for row in rows] == list(range(max(1, serial - 255), serial + 1))
    assert all(row['actor'] == OWNER for row in rows)
    assert [int(row['core']) for row in rows] == sorted(int(row['core']) for row in rows)
    assert all(int(row['core']) <= 8672 for row in rows)
    count_rows = [line.removeprefix('count ').split('=', 1) for line in lines[1:] if line.startswith('count ')]
    counts = {name: int(value) for name, value in count_rows}
    assert len(counts) == len(count_rows)
    assert sum(counts.values()) == serial
    assert all(sum(item['kind'] == name for item in rows) <= count for name, count in counts.items())
    assert {item['kind'] for item in rows} <= set(counts)
    commands = (
        ('type8-air-selector', 0x0836EC90, {'conditional_NE': 'true', 'literal': '0836BED4', 'r5': OWNER}),
        ('damage-table-entry', 0x0836F3B8, {'id': '13', 'table': '0836BED4', 'indexed': '0836C32C', 'subtype': '0'}),
        ('damage-record-selected', 0x0836F3CC, {'r1': '0836C32C'}),
        ('metadata-entry', 0x083555D0, {'r1': '0836C32C', 'r4': OWNER, 'r5': '020118D4', 'lr': '0836F3E0'}),
        ('setter-entry', 0x08012874, {'selected': '00000036', 'lr': '08355620'}),
        ('event-store', 0x08012884, {'selected': '00000036', 'saved_lr': '08355620', 'r5': '020118D4'}),
        ('hitstop-entry', 0x0836A69C, {'event': '0036'}),
    )
    next_index = 0
    witness = []
    marker = next(index for index, row in reversed(list(enumerate(rows)))
                  if row['kind'] == 'event-store' and row['selected'] == '00000036')
    window = rows[max(0, marker - 32):]
    for name, pc, required in commands:
        matches = [i for i, row in enumerate(window) if i >= next_index and row['kind'] == name
                   and all(row[key] == value for key, value in required.items())]
        assert len(matches) == 1, (name, matches)
        next_index = matches[0] + 1
        row = window[next_index - 1]
        assert int(row['pc'], 16) == pc + 4
        assert long(rom, pc - 0x08000000) == HOOKS[pc]
        assert row['P1'] == RESOURCE
        witness.append(row)
    selector, table, chosen, metadata, setter, store, hitstop = witness
    assert int(selector['cpsr'], 16) & 0x40000000 == 0
    assert int(selector['scratch'].split(',')[0], 16) & 0xFFFF == 8
    assert long(rom, 0x0836BED4 - 0x08000000 + 13 * 4) == int(table['indexed'], 16)
    record = rom[0x36C32C:0x36C34C]
    assert word(record, 2) == 0x36 and long(record, 4) == 0x0836AE94
    actual_record = ','.join(f'{value:08X}' for value in struct.unpack('<8I', record))
    assert chosen['record'] == metadata['record'] == actual_record
    assert setter['stack'].split(',')[2] == '020118D4'
    assert [int(row['seq']) for row in witness] == [5368, 5369, 5370, 5371, 5372, 5373, 5375]
    assert [row['core'] for row in witness] == ['8671'] * 6 + ['8672']
    assert store['event'] == '000C' and store['table'] == '0861CF14'
    table_at = int(store['table'], 16) - 0x08000000
    actual_row = struct.unpack_from('<4I', rom, table_at + 0x36 * 16)
    assert actual_row == (0x000AFF05, 0x0001000C, 0, 0)
    assert store['row'] == ','.join(f'{value:08X}' for value in actual_row)
    dispatch = next(row for row in rows if row['seq'] == '5374')
    assert [dispatch[key] for key in ('core', 'kind', 'target', 'event')] == [
        '8672', 'actor-dispatch', '0836AE94', '0036']
    actual_stack = hitstop['stack'].split(',')
    assert actual_stack[0] == '0000000A' and actual_stack[2] == '0836AF64' and actual_stack[4] == OWNER
    return serial, counts, witness


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    directory = ROOT / 'build' / REPLAY
    rom, launch_sha, bus_store, differing, checkpoint, journal_sha = compare(directory)
    lines = (directory / PROVENANCE).read_text('utf-8').splitlines()
    serial, counts, witness = verify_chain(lines, rom)
    changed = [line.replace('indexed=0836C32C', 'indexed=0836C2AC') if line.startswith('seq=5369 ') else line
               for line in lines]
    try:
        verify_chain(changed, rom)
    except AssertionError:
        pass
    else:
        raise AssertionError('wrong selected damage record accepted')
    report = dict(status='TYPE8_EVENT_PROVENANCE_ACTUAL_QA_PASS', outcome=OUTCOME,
                  rom_sha256=ROM, launch_sha256=launch_sha, predecessor_journal_sha256=journal_sha,
                  baseline_launch_sha256=BASELINE_MANIFEST, baseline_file_count=47, replay_file_count=49, isolated_exit_save_sha256=EXIT_SAVE_SHA,
                  raw_changed_common_files=sorted(differing), common_snapshots_byte_equal=35,
                  exact_input_trace=True, exact_authorized_ledger=True, score_writes=2, boss_writes=0,
                  snapshot_boundary_core=8673, checkpoint_core_sha256=checkpoint['core_sha256'],
                  checkpoint_core_byte_equal=True, checkpoint_rom_context_verified=True,
                  dynamic_witness=witness, producer_bus_store=bus_store, hook_counts=counts,
                  journal_total_events=serial, replay_emulator_started_by_auditor=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
