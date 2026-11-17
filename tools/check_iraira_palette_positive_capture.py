"""Audit the finalized 574F Iraira render replay and its native palette writes."""
import argparse
import json
from pathlib import Path
import re
import struct

import check_iraira_palette_witness_capture as old
from verify_gba_shoot_entry_capture import ROOT, fields, ledger, long, sha, snapshot, word


RUN = 'bizhawk-iraira-palette-positive-v86-20261117-a'
WRAPPER = 'tools/bizhawk_probe_iraira_palette_positive.lua'
PIN = '9043796D65B29758EDEB21692748D97C70040C10CCFA7EC97FDF451D3F4B9681'
HOST = 'A36696E07BC2CA71DE2646B99D6EDDAA640B9135672EEF686A0EB199165B51BB'
PINS = '161A6ABE2131856A4D17C53437AF8FFEE18F0854ED18560BAEB01F585E91E4DD'
ROM = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
COMPONENT = ROOT / 'build/iraira-outer-palette-v86-20261117/component.gba'
COMPONENT_MANIFEST = '4BD830DB3203F961E45E587EAAC244A17B756C1D29A3FC3DA608CA9EE191CCF9'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OLD_MANIFEST = 'D0FDBBD22CF419BFB012AE784AAE1CBACBD6743F2136A7E232F2FC7D32420E4D'
AUTHOR = '966B9DB81F2B3D5894D8DDAD7908A7FDA26D33A3275FCE1126D6F3F9C8E35205'
INDEPENDENT = '6CABF43520F0F9C0C2DB7D8092CED29DC30585C283401C46E4B131B0F9A61454'
ACTOR_CAPTURE = '13-campaign-active-04'
# Palette address, table offset, counter index, stride, halfwords, store label.
GROUPS = ((0x42, 0, 2, 32, 11, 0xD8AD5C), (0x62, 0x80, 2, 16, 6, 0xD8AD8C),
          (0x82, 0xC0, 3, 16, 7, 0xD8ADBC), (0xA2, 0x130, 4, 16, 7, 0xD8ADEC),
          (0xC2, 0x190, 3, 16, 7, 0xD8AE1C))
read_lines = old.read_lines


def bind(directory, host_exit):
    assert host_exit == 0, 'wait for the original host to exit successfully'
    build = ROOT / 'build'
    baseline = build / old.RUN
    digest, run = old.full.prior.ai_replay.manifest(directory)
    ref_digest, ref = old.full.prior.ai_replay.manifest(baseline)
    assert ref_digest == OLD_MANIFEST and ref['outcome'] == run['outcome'] == old.DONE
    assert run['phase_kind'] == 'readonly-source-corrected-iraira-palette-121-native-clocks'
    assert all(run[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(run[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                            'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert sha((build / 'run_iraira_palette_positive_v86_20261117.py').read_bytes()) == run['launcher_sha256'] == HOST
    pin_raw = (build / 'iraira-palette-positive-reviewed-pins-20261117.json').read_bytes()
    assert sha(pin_raw) == run['reviewed_pins_sha256'] == PINS
    assert run['pins'] == json.loads(pin_raw) == ref['pins'] | {WRAPPER: PIN} and len(run['pins']) == 12
    assert {name: sha((ROOT / name).read_bytes()) for name in run['pins']} == run['pins']
    assert sha((build / 'iraira-palette-positive-qa-20261117/lua.json').read_bytes()) == AUTHOR
    assert sha((build / 'iraira-palette-positive-delta-independent-20261117/report.json').read_bytes()) == INDEPENDENT
    assert sha(COMPONENT.with_suffix('.json').read_bytes()) == COMPONENT_MANIFEST
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == run['rom_sha256'] == ROM
    assert rom == COMPONENT.read_bytes() == (directory / 'probe.gba').read_bytes()
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == run['exe_sha256'] == ref['exe_sha256']
    assert run['guest_writes'] == ref['guest_writes']
    assert run['arguments'] == [arg.replace(old.RUN, RUN).replace(old.WRAPPER, WRAPPER).replace(old.full.ROM, ROM)
                                for arg in ref['arguments']]
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(item['Path'] == f'W:/build/{RUN}/data/{i}' for i, item in enumerate(config['PathEntries']['Paths']))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    assert not any(name.endswith('.State') for name in run['files'])
    assert {name for name in run['files'] if name.startswith('data/')} <= {'data/104/probe.SaveRAM'}
    return digest, run, ref, rom, baseline


def checked_prefix(directory, baseline, launch, ref):
    assert (directory / 'iraira-palette-witness-done.txt').read_text().strip() == old.DONE
    for name in ('campaign-complete-done.txt', 'shoot-entry-done.txt'):
        assert (directory / name).read_text().strip() == old.BOUNDED
    def compare(name, start=0):
        current, original = (read_lines(path / name) for path in (directory, baseline))
        assert current[start:] == original[start:], name
        return current

    campaign = compare('campaign-complete-trace.txt', 1)
    end = fields(campaign[-1])
    assert (end['outcome'], end['highest'], end['progress'], end['stage'], end['cpu']) == (old.BOUNDED, '4', '4', '10', '11')
    files = sorted(name for name in launch['files'] if re.match(r'^\d+-[^/]+\.(?:bin|png)$', name))
    assert len(files) == 13 * 7 and set(files) <= ref['files'].keys()
    unchanged = [name for name in files if launch['files'][name] == ref['files'][name]]
    earlier = [name for name in files if int(name[:2]) < 12]
    assert set(earlier) <= set(unchanged)
    assert f'{ACTOR_CAPTURE}-palette.bin' not in unchanged and f'{ACTOR_CAPTURE}.png' not in unchanged
    traces = [old.full.prior.ai_replay.register_order_only(path / 'shoot-entry-trace.txt')
              for path in (directory, baseline)]
    prior_captures = [tuple(line for line in trace if line.startswith('capture=') and
                            int(line[len('capture='):len('capture=')+2]) < 12) for trace in traces]
    assert prior_captures[0] == prior_captures[1]
    assert fields(traces[0][-1])['outcome'] == old.BOUNDED and fields(traces[0][-1])['final_core'] == end['core']
    assert 'failure_checkpoint_saved=false' in traces[0] and fields(traces[0][-1])['stage11_writes'] == '0'
    inputs = compare('trace.txt')
    for name in ('type8-event-provenance.txt', 'ai-producer-provenance.txt', 'iraira-clock-phase.txt'):
        compare(name)
    writes, scores, bosses = ledger(compare('shoot-entry-writes.txt'))
    assert scores == 12 and bosses == 0 and int(fields(traces[0][-1])['score_writes']) == scores
    clock = old.full.checked_clock(directory, True, end['core'])
    return end, clock, dict(earlier_snapshot_files_exact=len(earlier), captures_exact=len(unchanged),
                            changed_capture_files=sorted(set(files) - set(unchanged)),
                            exact_input_lines=len(inputs), exact_gameplay_events=len(campaign)-1,
                            pre_iraira_capture_register_lines_exact=len(prior_captures[0]),
                            authorized_writes=writes, score_writes=scores, boss_writes=bosses)


def counters(row):
    return tuple(map(int, row['counters'].split(',')))


def projected_color(raw, dimmed):
    if not dimmed:
        return raw
    reduced = (raw & 0x739C) >> 1
    return reduced | bool(reduced & 0x1E) | (bool(reduced & 0x3C0) << 5) | (bool(reduced & 0x7800) << 10)


def validate_projector_store(group, row, rom):
    address, offset, index, stride, size, store_pc = group
    flag, disabled, dimmed = (int(item, 16) for item in row['gates'].split(','))
    assert not flag & 16 and disabled == 0
    phase = counters(row)[index]
    subscript = size - int(row['r3'], 16)
    src = 0x584200 + offset + phase * stride + subscript * 2
    target = 0x05000000 + address + subscript * 2
    color = projected_color(word(rom, src), dimmed)
    assert int(row['pc'], 16) == 0x08000000 + store_pc + 4
    assert 0 <= subscript < size and int(row['r9'], 16) == phase
    assert int(row['r1'], 16) == 0x08000000 + src + 2 and int(row['r2'], 16) == target
    assert int(row['r0'], 16) == color
    return target, color


def checked_witness(directory, rom, end, clock):
    rows = read_lines(directory / old.WITNESS)
    header = fields(rows[0])
    assert (header['core'], header['samples'], header['disposition'], header['guest_writes'], header['input']) == (
        end['core'], '121', old.BOUNDED, 'none', 'frozen-parent')
    counters_rows = [fields(line) for line in rows if line.startswith('count ')]
    counts = {row['kind']: (int(row['total']), int(row['after_first_clock'])) for row in counters_rows}
    assert len(counts) == len(counters_rows)
    assert all(total > 0 and 0 <= active <= total for total, active in counts.values())
    serial = int(header['serial'])
    assert sum(total for total, _ in counts.values()) == serial
    front_rows = [fields(line) for line in rows if line.startswith('frontdoor ')]
    assert [int(row['stage']) for row in front_rows] == list(range(12))
    front = {int(row['stage']): int(row['total']) for row in front_rows}
    assert front[10] == counts['palette-dispatch'][0]
    assert all(front[stage] > 0 for stage in (8, 1, 9, 6))
    assert all(kind not in counts for kind in ('legacy-stage-return', 'legacy-stage-branch',
                                               'retail-stage3-handler', 'retail-gradient-backdrop'))
    expected_calls = counts['legacy-stage-getter']
    for kind in ('palette-dispatch', 'palette-route', 'palette-route-branch', 'projector-enter', 'projector-exit'):
        assert counts[kind] == expected_calls
    assert expected_calls[1] == counts['cycle'][1] == 120
    first = {row['kind']: row for line in rows if line.startswith('first seq=') for row in [fields(line)]}
    ring = [fields(line) for line in rows if line.startswith('seq=')]
    assert [int(row['seq']) for row in ring] == list(range(max(1, serial-255), serial+1))
    assert all(row['kind'] in counts for row in ring) and set(first) == set(counts)
    route = [first[kind] for kind in ('legacy-stage-getter', 'palette-dispatch', 'palette-route',
                                      'palette-route-branch', 'projector-enter', 'projector-exit')]
    assert len({row['core'] for row in route}) == 1
    assert [int(row['seq']) for row in route] == sorted(int(row['seq']) for row in route)
    assert [r['pc'] for r in route] == ['080D0BD4', '080C4CC8', '08D8AF44', '08D8AF64', '08D8AD04', '08D8AE30']
    assert long(rom, 0xD0BD0) == 0xEB32EA9A
    assert int(route[3]['cpsr'], 16) & 0x40000000
    assert all(row['lr'] == '080D0BE8' for row in route[1:])

    group_by_kind = {f'source-store-{g[0]:02X}': g for g in GROUPS}
    successful = set()
    for kind, group in group_by_kind.items():
        total, active = counts[kind]
        assert total % group[4] == active % group[4] == 0
        successful.add((total // group[4], active // group[4]))
        assert validate_projector_store(group, first[kind], rom)[0] == 0x05000000 + group[0]
    assert len(successful) == 1
    project_total, project_active = successful.pop()
    assert project_total <= expected_calls[0] and project_active == expected_calls[1]
    expected_destinations = [0x05000000 + address + i*2 for address, _, _, _, size, _ in GROUPS for i in range(size)]
    transactions = []
    current = None
    bus_write_by_pc = {0x08000000 + group[5] + 8: group[0] for group in GROUPS}
    for row in ring:
        kind = row['kind']
        if kind == 'projector-enter':
            current = dict(core=int(row['core']), counters=counters(row), words=[], bus=[])
        elif current is not None and kind in group_by_kind:
            assert int(row['core']) == current['core'] and counters(row) == current['counters']
            current['words'].append(validate_projector_store(group_by_kind[kind], row, rom))
        elif current is not None and kind in ('write-42', 'write-82', 'write-C2'):
            port = bus_write_by_pc[int(row['pc'], 16)]
            addr = 0x05000000 + port
            value = int(row['value'], 16)
            assert int(row['address'], 16) == addr and current['words'][-1] == (addr, value)
            current['bus'].append((addr, value))
        elif current is not None and kind == 'projector-exit':
            assert [addr for addr, _ in current['words']] == expected_destinations
            assert [addr for addr, _ in current['bus']] == [0x05000042, 0x05000082, 0x050000C2]
            transactions.append(current)
            current = None
    assert transactions
    assert len({item['counters'] for item in transactions}) > 1

    samples = [fields(line) for line in rows if line.startswith('sample ')]
    lo, hi = (int(row['core']) for row in clock['first_and_last_clock'])
    assert [int(row['index']) for row in samples] == list(range(1, 122))
    assert [int(row['core']) for row in samples] == list(range(lo, hi+1))
    assert [int(row['clock']) for row in samples] == list(range(7199, 7078, -1))
    assert hi+1 == int(end['core'])
    assert all(row['shadow'] == row['colors'].split(',')[0] == '0000' for row in samples)
    for row in samples:
        assert validate_sample(row, rom)
        core = row['core']
        assert row['last_writers'].split(',') == [
            f'{core}:03000ECC:0801122C',
            f'{core}:08D8AD64:08D8AD5C',
            f'{core}:08D8ADC4:08D8ADBC',
            f'{core}:08D8AE24:08D8AE1C',
        ]
    return dict(frontdoor_by_stage=front, counts=counts, first_corrected_route=route,
                successful_38_word_projections=project_total, successful_after_first_clock=project_active,
                retained_complete_projector_executions=transactions, active_backdrop_samples=len(samples),
                sampled_three_ports_exact_current_phase=len(samples),
                first_clock=samples[0], last_clock=samples[-1],
                all_journals_finalized_at_core=int(end['core']))


def validate_sample(row, rom):
    ports = {0x42, 0x82, 0xC2}
    actual = tuple(int(item, 16) for item in row['colors'].split(',')[1:])
    phase = counters(row)
    dimmed = int(row['gates'].split(',')[2], 16)
    return actual == tuple(projected_color(word(rom, 0x584200 + offset + phase[index]*stride), dimmed)
                           for address, offset, index, stride, _, _ in GROUPS if address in ports)


def packed_tiles(blob):
    for at in range(0, len(blob), 4):
        row = blob[at:at+4]
        pixels = [sum(((plane >> bit) & 1) << i for i, plane in enumerate(row)) for bit in range(7, -1, -1)]
        yield from (pixels[i] | pixels[i+1] << 4 for i in range(0, 8, 2))


def translated_map(blob):
    return b''.join(struct.pack('<H', (v & 0x1FF) | ((v & 0x1E00) << 3) |
                                ((v & 0x2000) >> 4) | ((v & 0xC000) >> 4))
                    for v, in struct.iter_unpack('<H', blob))


def translated_color(value):
    components = [(value >> shift) & 15 for shift in (8, 4, 0)]
    return sum((component * 2 + int(component > 0)) << (i*5) for i, component in enumerate(components))


def checked_assets(directory, baseline, rom, source):
    assert sha(source) == SOURCE
    stage = snapshot(directory, ACTOR_CAPTURE)
    assert (stage['mode'], stage['stage']) == (7, 10) and stage['p1']['active'] and stage['p2']['active']
    assert stage['p1']['hp'] == stage['p2']['hp'] == 8 and stage['p1']['score'] == 999
    assets = old.full.checked_iraira_assets(directory, rom, ACTOR_CAPTURE + '.png')
    vram = (directory / f'{ACTOR_CAPTURE}-vram.bin').read_bytes()
    old_vram = (baseline / f'{ACTOR_CAPTURE}-vram.bin').read_bytes()
    palette = (directory / f'{ACTOR_CAPTURE}-palette.bin').read_bytes()
    assert assets['hardware_palette_0'] == '0000'
    assert assets['projection_words_matching_current_counters'] == assets['projection_words_compared'] == 38
    assert bytes(packed_tiles(source[0x4C61C0:0x4C61C0+495*32])) == rom[0x598100:0x598100+495*32] == vram[0x4000:0x7DE0]
    assert bytes(packed_tiles(source[0x42FD80:0x42FFA0])) == rom[0x1FD50:0x1FF70] == vram[0x7DE0:0x8000]
    assert translated_map(source[0x4CA1C0:0x4CA1C0+8*0x3F0]) == rom[0x59C100:0x59C100+8*0x3F0]
    assert vram[0xF000:0x10000] == old_vram[0xF000:0x10000]
    values = struct.unpack_from('<256H', source, 0x76AD13)
    assert tuple(map(translated_color, values)) == struct.unpack_from('<256H', rom, 0x584200)
    assert word(palette, 0) == 0
    return dict(source_atlas_pixels=495*64, common_font_pixels=17*64, source_map_words=8*504,
                exact_retained_live_map_bytes=0x1000, original_source_projector_colors=len(values),
                active_actor_hp=[stage['p1']['hp'], stage['p2']['hp']], score=stage['p1']['score'], snapshot=assets)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--host-exit', required=True, type=int)
    args = parser.parse_args()
    directory = ROOT / 'build' / RUN
    digest, launch, ref, rom, baseline = bind(directory, args.host_exit)
    end, clock, replay = checked_prefix(directory, baseline, launch, ref)
    witness = checked_witness(directory, rom, end, clock)
    source = (ROOT / 'local/BizHawk-2.11.1/ref15.wsc').read_bytes()
    assets = checked_assets(directory, baseline, rom, source)
    result = dict(status='IRAIRA_PALETTE_POSITIVE_ACTUAL_QA_PASS', original_host_exit=args.host_exit,
                  rom_sha256=ROM, launch_sha256=digest, files_verified=len(launch['files']),
                  checker_sha256=sha(Path(__file__).read_bytes()), replay=replay, witness=witness,
                  assets=assets, scoped_outcome=old.DONE, full_campaign_run=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']} {sha(args.report.read_bytes())}")


if __name__ == '__main__':
    main()
