"""Audit the combined aligned-AI/Iraira campaign, source assets, and native clock."""
import argparse
import json
from pathlib import Path
import re
import struct

import check_ai_corrected_campaign_capture as prior
from check_ai_aligned_iraira import ROM, PIN
from verify_gba_shoot_entry_capture import ROOT, fields, sha, word


RUN = 'bizhawk-ai-iraira-v84-20261117-a'
WRAPPER = 'tools/bizhawk_probe_ai_aligned_iraira.lua'
HOST = '2E68861ADF5D4CC5BC9CFE404557D62F37DDCAD54EFA3227DF8A2B9460161140'
PINSET = '56E388FF5987CF82CBE019C21C82197AE2228AD9C3DA50F1865BF5CCCF6E67D0'
COMPONENT = ROOT / 'build/iraira-render-repair-v84-20261117/component.gba'
COMPONENT_MANIFEST = '29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900'
CLOCK_FILE = 'iraira-clock-phase.txt'
SOURCE_REVIEW = '0112FDCC4B6EB2A64DB67A22CB57583847840FEC6A96DA11ACB91614702DABCC'
OBSERVER_REVIEW = 'FA07E06E715BF2C7B5FF3EFBD47AF6F331854FE85AD386D45758911E36353849'


def launch_binding(directory, host_exit):
    digest, run = prior.ai_replay.manifest(directory)
    _, ref = prior.ai_replay.manifest(ROOT / 'build' / prior.RUN)
    assert ref['outcome'] == prior.prior.SUCCESS
    assert run['phase_kind'] == 'aligned-ai-iraira-assisted-eleven-encounter-to-healthy-shoot'
    assert host_exit == (0 if run['outcome'] == prior.prior.SUCCESS else 1)
    assert all(run[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(run[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                             'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert sha((ROOT / 'build/run_ai_iraira_v84_20261117.py').read_bytes()) == run['launcher_sha256'] == HOST
    pin_raw = (ROOT / 'build/ai-iraira-reviewed-pins-20261117.json').read_bytes()
    assert sha(pin_raw) == run['reviewed_pins_sha256'] == PINSET
    assert run['pins'] == json.loads(pin_raw) == ref['pins'] | {WRAPPER: PIN}
    assert len(run['pins']) == 10
    assert {name: sha((ROOT / name).read_bytes()) for name in run['pins']} == run['pins']
    assert sha(COMPONENT.with_suffix('.json').read_bytes()) == COMPONENT_MANIFEST
    assert sha((ROOT / 'build/iraira-render-independent-20261117/report.json').read_bytes()) == SOURCE_REVIEW
    assert sha((ROOT / 'build/ai-iraira-delta-independent-20261117/report.json').read_bytes()) == OBSERVER_REVIEW
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == run['rom_sha256'] == ROM
    assert rom == COMPONENT.read_bytes() == (directory / 'probe.gba').read_bytes()
    assert sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == run['exe_sha256'] == ref['exe_sha256']
    assert run['guest_writes'] == ref['guest_writes']
    args = [arg.replace(prior.RUN, RUN).replace(prior.WRAPPER, WRAPPER).replace(prior.ROM, ROM)
            for arg in ref['arguments']]
    assert run['arguments'] == args
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(item['Path'] == f'W:/build/{RUN}/data/{i}' for i, item in enumerate(config['PathEntries']['Paths']))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    saves = {name: value for name, value in run['files'].items() if name.startswith('data/')}
    assert set(saves) <= {'data/104/probe.SaveRAM'}
    return digest, run, ref, rom, saves


def campaign_capture(directory, rom, captures, producers, active, hud):
    # Audit each active capture individually. The prior paired capture contract
    # deliberately asserts the DEEE Iraira corruption and would mislabel 3FE5.
    base, hud_samples = prior.campaign_capture(directory, rom, captures, producers, [], hud)
    for event in active:
        visual, _ = prior.campaign_capture(directory, rom, captures, [], [event], [])
        base.update(visual)
    return base, hud_samples


def checked_ai(directory, rom):
    rows = {row['kind']: row for line in prior.ai_replay.read_lines(directory / 'ai-producer-provenance.txt')
            if line.startswith('first seq=') for row in [fields(line)]}
    if not rows:
        return None
    raw, route, src, first, dest = (rows[k] for k in ('raw-id', 'row-index', 'first-read',
                                                      'first-copy', 'parameter-copies-complete'))
    assert raw['raw_id'] == '14' and route['effective_id'] == '9' and route['stride'] == '18'
    assert src['row_base'] == '08D8AB00' and src['offset'] == '162' and src['src'] == '08D8ABA2'
    source = rom[0xD8ABA2:0xD8ABB4]
    assert source[-1] == 0 and src['halfword'] == first['value'] == '02E4'
    assert int(first['r0'], 16) == 0x02E4 and first['dst'] == '03004D8A'
    assert src['row17'] == source[:17].hex().upper()
    copied = bytes.fromhex(dest['params_03004D88'])
    fields15 = [(2, 2), (4, 2), (6, 1), (7, 1), (0x1C, 1), (0x1D, 1), (0x1E, 1), (0x1F, 1),
                (0x20, 1), (0x21, 1), (0x22, 1), (8, 1), (9, 1), (0x24, 1), (0x25, 1)]
    assert b''.join(copied[at:at+size] for at,size in fields15) == source[:17] and copied[0x23] == 0
    action, target = rows.get('action-first-copy'), rows.get('target')
    if action:
        actual = int(action['src'], 16) - 0x08000000
        ordinal = int(action['ordinal'], 16)
        assert 0 <= ordinal < 264 and action['bank'] == '0D80'
        assert actual == 0xD89800 + ordinal * 18
        assert action['action18'] == rom[actual:actual + 18].hex().upper()
        assert int(action['word'], 16) == word(rom, actual)
    if target:
        index = int(target['index'], 16)
        assert 0 <= index < 12 and target['target'] == target['word']
        assert int(target['word'], 16) == struct.unpack_from('<I', rom, 0xC65F4 + index * 4)[0]
    return dict(source_row=src, first_native_copy=first, complete_field_count=len(fields15), action=action, target=target)


def checked_clock(directory, phase_required, expected_final):
    lines = prior.ai_replay.read_lines(directory / CLOCK_FILE)
    summary = fields(lines[0])
    assert summary['core'] == expected_final and summary['guest_writes'] == 'none' and summary['input'] == 'frozen-parent'
    phase = [fields(line) for line in lines if line.startswith('phase ')]
    clock = [fields(line) for line in lines if line.startswith('clock ')]
    assert len(phase) == min(32, int(summary['phase_total'])) == int(summary['phase_kept'])
    assert len(clock) == int(summary['clock_streak']) <= min(121, int(summary['clock_observed']))
    assert all(row['address'] == '03002568' and row['flags'] == '2000' for row in phase)
    clear = [row for row in phase if row['role'] == 'init-clear']
    toggled = [row for row in phase if row['role'] == 'display-toggle']
    assert all(row['pc'] == '08D8AF94' and row['value'] == '0000' for row in clear)
    assert all(row['pc'] == '086283B4' and int(row['old'], 16) in (0, 2) and
               int(row['value'], 16) == int(row['old'], 16) ^ 2 for row in toggled)
    assert all(row['owner'] == '03004500' and row['pc'] == '08375020' and row['backdrop'] == '0000' and
               row['phase'] in ('0000', '0002') and int(row['r9'], 16) & 65535 == int(row['value']) for row in clock)
    if clock:
        start = int(clock[0]['core'])
        first = int(clock[0]['value'])
        assert [(int(row['core']), int(row['value'])) for row in clock] == [(start+i, first-i) for i in range(len(clock))]
    if phase_required:
        assert len(clock) == 121 and len(clear) >= 1
        assert {(item['old'], item['value']) for item in toggled} == {('0000', '0002'), ('0002', '0000')}
    return dict(summary=summary, first_and_last_clock=clock[::len(clock)-1] if len(clock) > 1 else clock,
                first_init_clear=clear[:1], sampled_toggles=toggled[:6])


def mapped_rows(vram_map, rom, map_start):
    def run_length(row):
        return max((size for size in range(56, 7, -2)
                    if any(row[start:start+size] in vram_map for start in range(0, 56-size+1, 2))), default=0)

    candidates = []
    for m in range(map_start, map_start + 4):
        source = 0x59C100 + m * 0x3F0
        rows = [rom[source + y*56:source + (y+1)*56] for y in range(18)]
        matches = [run_length(row) for row in rows]
        candidates.append((sum(matches), m, matches))
    count, m, matches = max(candidates)
    return dict(rom_map=f'{0x0859C100+m*0x3F0:08X}', exact_full_rows=matches.count(56),
                matching_row_subsequence_bytes=count, matched_bytes_by_row=matches)


def checked_iraira_assets(directory, rom, captured):
    def read(name):
        return (directory / (captured.removesuffix('.png') + '-' + name + '.bin')).read_bytes()

    iw, vram, palette, display = (read(region) for region in ('iwram', 'vram', 'palette', 'display'))
    assert (iw[0x231E], iw[0x231C], iw[0x232E]) == (10, 11, 4)
    assert word(iw, 0x2654) == 0
    owners = ((0x2388, 0x08580480, 0x0600F800, 0x030012BA), (0x2338, 0x085804A0, 0x0600F000, 0x030012B8))
    for address, desc, hw_map, port in owners:
        assert struct.unpack_from('<3I', iw, address) == (port, port+1, hw_map)
        assert struct.unpack_from('<I', iw, address+0x24)[0] == desc
        assert struct.unpack_from('<2H', iw, address+0xC) == (2, 2)
    maps = [mapped_rows(vram[0xF800:0x10000], rom, 0), mapped_rows(vram[0xF000:0xF800], rom, 4)]
    assert all(row['matching_row_subsequence_bytes'] > 500 for row in maps)
    pattern = rom[0x598100:0x59C100]
    tiles = vram[0x4000:0x8000]
    exact_tiles = sum(pattern[i:i+32] == tiles[i:i+32] for i in range(0, len(pattern), 32))
    assert pattern[:495 * 32] == tiles[:495 * 32]
    counters = struct.unpack_from('<5H', iw, 0x3D30)
    assert all(value < high for value, high in zip(counters, (8, 5, 4, 7, 6)))
    assert not (word(iw, 0x4506) & 16) and iw[0x260B] == iw[0x4529] == 0
    _, _, p, q, r = counters
    banks = [(0, p, 32, 4, 11, 0x42), (0x80, p, 16, 4, 6, 0x62), (0xC0, q, 16, 7, 7, 0x82),
             (0x130, r, 16, 6, 7, 0xA2), (0x190, q, 16, 7, 7, 0xC2)]
    dynamic_offsets = set()
    projection = []
    for base, phase, stride, phase_count, count, address in banks:
        def palette_row(phase_index):
            offset = 0x584200 + base + phase_index * stride
            return struct.unpack_from(f'<{count}H', rom, offset)

        want = palette_row(phase)
        actual = struct.unpack_from(f'<{count}H', palette, address)
        projection.append(dict(palette_address=f'{0x05000000 + address:08X}', expected_phase=phase,
                               exact_at_capture=actual == want,
                               matched_color_words=sum(left == right for left, right in zip(actual, want)),
                               matching_source_phases=[k for k in range(phase_count) if actual == palette_row(k)],
                               expected=[f'{value:04X}' for value in want], captured=[f'{value:04X}' for value in actual]))
        dynamic_offsets.update(range(address, address+count*2))
    static_palette = rom[0x598000:0x598000+222]
    assert all(palette[2+i] == color for i,color in enumerate(static_palette) if 2+i not in dynamic_offsets)
    return dict(file=captured, dispcnt=f'{word(display,0):04X}', maps=maps, source_tile_slots_exact=exact_tiles,
                contiguous_source_tile_pixels=495 * 64, independent_source_asset_binding=SOURCE_REVIEW,
                source_palette_unprojected_bytes=sum(2+i not in dynamic_offsets for i in range(222)),
                projection_words_compared=38,
                projection_words_matching_current_counters=sum(row['matched_color_words'] for row in projection),
                projected_palette_matches_current_counters=all(row['exact_at_capture'] for row in projection),
                projection=projection, palette_counters=counters, backdrop_shadow='0000',
                hardware_palette_0=f'{word(palette,0):04X}', backdrop_matches_shadow=word(palette,0)==0,
                palette_phase=f'{word(iw,0x2568):04X}', dynamic_banks=len(banks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--host-exit', type=int, required=True)
    args = parser.parse_args()
    directory = ROOT / 'build' / RUN
    result = prior.pinned_scope(prior.audit, RUN=RUN, ROM=ROM, launch_binding=launch_binding,
                                campaign_capture=campaign_capture)(directory, args.host_exit)
    result['status'] = 'ALIGNED_AI_IRAIRA_ACTUAL_CAPTURE_QA_PASS'
    result['aligned_ai'] = checked_ai(directory, COMPONENT.read_bytes())
    successful = result['completed_eleven_encounters']
    passed_iraira = any(event['progress'] == '5' for event in result['producer_events'])
    result['iraira_clock_and_phase'] = checked_clock(directory, passed_iraira, result['finalized_native_summary']['core'])
    result['iraira_assets'] = checked_iraira_assets(directory, COMPONENT.read_bytes(), result['visuals']['4']['file']) if '4' in result['visuals'] else None
    if successful:
        assert result['aligned_ai']['action'] and result['aligned_ai']['target'] and result['iraira_assets']
        assert all(item['outer_frame_exact'] for item in result['hud'].values())
        original = ROOT / 'build' / prior.RUN
        try:
            checked_iraira_assets(original, COMPONENT.read_bytes(), '13-campaign-active-04.png')
        except AssertionError:
            result['old_deee_iraira_snapshot_rejected'] = True
        else:
            raise AssertionError('old Iraira background accepted')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"{result['status']} {result['outcome']} {sha(args.output.read_bytes())}")


if __name__ == '__main__':
    main()
