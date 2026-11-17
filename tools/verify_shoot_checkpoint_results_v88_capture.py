"""Audit the finalized E212 Shoot replay and its last observed native phase."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

from PIL import Image

import verify_gba_shoot_entry_capture_v2 as stateqa
import verify_shoot_checkpoint_results_v88_preflight as preflight
from verify_shoot_static_companion_clear import ROOT, need, sha


SUCCESS = 'shoot-checkpoint-aim-terminal-results-title'
BOUNDED = 'failure:bounded-no-terminal'
RUN = 'bizhawk-shoot-checkpoint-results-v88-20261117-a'
LEAD_RUN = 'bizhawk-shoot-checkpoint-lead-v87-20261117-a'
BASE_RUN = 'bizhawk-wholeplay-v87-20261117-a'
LEAD_LAUNCH = '6ED83048E72D6E0D7DE19BD7A29A8170E0F0187B6015241E6ED434A473FC346F'
PREFLIGHT = '525314AEE0D4B9BF99C3285F5F61B7952DA111E09715872A2CD09F9B5D94F4DE'
FIELDS = re.compile(r'(?:^|\s)([A-Za-z0-9_]+)=(\S+)')
REG = re.compile(r'capture=([-\w]+) reg (R\d+|CPSR|SPSR)=([0-9A-F]+)')
MATCH_SEQUENCE = [
    ('healthy', 7, 0), ('stage11-hp1', 7, 0), ('hit-pre', 7, 0x0836E5E8),
    ('hit-post', 7, 0x0836E5EC), ('fatal-adapter', 7, 0x085CD964),
    ('fatal-pair', 7, 0x0836E608), ('root5', 7, 0x083736B4), ('case5', 7, 0x0833FD0C),
    ('terminal-entry', 7, 0x085CD004), ('terminal-middle', 7, 0x085CD344),
    ('terminal-display', 7, 0x086FF760), ('terminal-irq-final', 7, 0x086FFEC0),
    ('terminal-final', 7, 0x085CD744), ('cleanup-entry', 7, 0x08340C58),
    ('cleanup-request', 7, 0x08340CAC), ('results-constructor', 8, 0x080897B0),
    ('mode12-constructor', 12, 0x080BBC28), ('mode12-request', 12, 0x080BD8EC),
    ('mode13-constructor', 13, 0x080CA250), ('mode13-request', 13, 0x080CBCC4),
    ('ending-entry', 11, 0x080BF1D4), ('ending-ready', 11, 0x080C0054),
    ('mode20-entry', 20, 0x0804044C), ('mode20-art', 20, 0x08040720),
    ('mode20-return-request', 20, 0x0804060C), ('title-ready', 3, 0x08090C80),
]
RAM_TYPES = dict(iwram=0x8000, ewram=0x40000, vram=0x18000, palette=0x400, oam=0x400, display=0x60)


def fields(row):
    return dict(FIELDS.findall(row))


def word(blob, at):
    return struct.unpack_from('<H', blob, at)[0]


def address(blob, at):
    return struct.unpack_from('<I', blob, at)[0]


def assert_file_id(path, digest):
    raw = path.read_bytes()
    need(sha(raw) == digest, f'exact artifact {path}')
    return raw


def bind(directory, host_exit):
    pre = ROOT / 'build/shoot-checkpoint-results-v88-preflight-independent-20261117/report.json'
    preflight_report = json.loads(assert_file_id(pre, PREFLIGHT))
    launch_raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_raw)
    outcomes = {0: SUCCESS, 1: BOUNDED}
    need(launch['completed'] and launch['outcome'] == outcomes[host_exit], 'original host exit matches finalized outcome')
    for key in ('visible', 'physical_background_input', 'supplied_save_used', 'host_stop_requested', 'host_deadline_reached'):
        need(launch[key] is False, 'scope ' + key)
    for key in ('loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged',
                'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal'):
        need(launch[key] is True, 'finalized launch ' + key)
    current_inventory = {p.relative_to(directory).as_posix(): sha(p.read_bytes())
                         for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'launch.json'}
    need(launch['files'] == current_inventory, 'complete immutable capture inventory')
    host_name = 'build/run_shoot_checkpoint_results_v88_20261117.py'
    pins_name = 'build/shoot-checkpoint-results-v88-pins-20261117.json'
    for key, filename in (('launcher_sha256', host_name), ('reviewed_pins_sha256', pins_name)):
        need(launch[key] == preflight.FILES[filename] == sha((ROOT / filename).read_bytes()), 'frozen launcher ' + key)
    pins = json.loads((ROOT / pins_name).read_bytes())
    need(len(pins) == 6 and pins == launch['pins'] == preflight_report['host']['scope_pins'], 'six-script pin set')
    for name, digest in pins.items():
        assert_file_id(ROOT / name, digest)
    prefix = 'W:/build/' + directory.name
    need(launch['arguments'] == ['--gdi', '--config=' + prefix + '/config.json',
                                 '--lua=W:/tools/' + preflight.RESULT,
                                 '--userdata=output:' + prefix + ';checkpoint_dir:' + prefix + '/checkpoint;probe_sha256:'
                                 + preflight.NEW + ';stage11_boss_authorization:user-approved-development-stage11-boss-hp1-once',
                                 prefix + '/probe.gba'], 'exact approved private arguments')
    settings = json.loads((directory / 'config.json').read_bytes())
    need(all(settings[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled')),
         'private configured input, state and save scope')
    need(all(row['Path'] == f'{prefix}/data/{i}' for i, row in enumerate(settings['PathEntries']['Paths'])),
         'fresh isolated per-surface data paths')
    need(all(v == 'false' for v in re.findall(r'"AutoLoad":\s*(\w+)', json.dumps(settings))), 'all explicit AutoLoad switches disabled')
    for name in ('shoot-checkpoint-aim-done.txt', 'shoot-entry-done.txt'):
        need((directory / name).read_text(encoding='utf-8').strip() == launch['outcome'], 'finalized journal ' + name)
    for name in ('shoot-entry-first-failure.txt', 'failure-observed.State', 'failure-observed.txt'):
        need((name in current_inventory) == (launch['outcome'] == BOUNDED), 'bounded-state artifact ' + name)
    for name in ('shoot-checkpoint-aim-error.txt', 'shoot-entry-writes.txt', 'stop.request'):
        need(name not in current_inventory, 'no failure, stop or extra script write file ' + name)
    need(launch['guest_writes'] == ['stage11 live boss HP WORD1 once at a qualified ordinary B input'], 'exact sole authorization')
    need({name for name in current_inventory if name.startswith('data/')} <= {'data/104/probe.SaveRAM'},
         'files only in the native private save area')
    rom = (directory / 'loaded-rom.bin').read_bytes()
    need(sha(rom) == launch['rom_sha256'] == preflight.NEW and len(rom) == 0x1000000, 'active exact 16 MiB image')
    need(rom == (directory / 'probe.gba').read_bytes()
         == (ROOT / 'build/shoot-stage11-results-route-20261117-r2/component.gba').read_bytes(), 'launched/loaded bytes exact')
    return sha(launch_raw), launch, rom, preflight_report


def checkpoint_check(directory, launch, rom, preflight_report):
    base, lead = (ROOT / 'build' / name for name in (BASE_RUN, LEAD_RUN))
    old_launch = json.loads(assert_file_id(lead / 'launch.json', LEAD_LAUNCH))
    source_launch = json.loads(assert_file_id(base / 'launch.json', preflight.BASELINE))
    need(len(launch['checkpoint_pins']) == 7 == len(old_launch['checkpoint_pins']), 'state/metadata/five-memory checkpoint')
    for name, digest in launch['checkpoint_pins'].items():
        need((directory / 'checkpoint' / name).read_bytes() == (base / name).read_bytes()
             == (lead / 'checkpoint' / name).read_bytes(), 'exact original checkpoint copies ' + name)
        need(digest == source_launch['files'][name] == old_launch['checkpoint_pins'][name], 'source manifest mapping ' + name)
    source_state = (directory / 'checkpoint/healthy-activation.State').read_bytes()
    current_state = (directory / 'restored.State').read_bytes()
    source_core, _ = stateqa.checkpoint_core(source_state)
    restored, _ = stateqa.checkpoint_core(current_state)
    old_resave, _ = stateqa.checkpoint_core((lead / 'restored.State').read_bytes())
    need((sha(source_core), sha(old_resave)) == (preflight.SOURCE_CORE, preflight.LEAD_CORE), 'exact source and prior resave Core')
    expect = bytearray(source_core)
    expect_prior = bytearray(old_resave)
    checksum = zlib.crc32(rom)
    for core in (expect, expect_prior):
        struct.pack_into('<I', core, 12, checksum)
    need(len(source_core) == len(restored) == len(old_resave), 'complete restored Core extents')
    drift = [dict(offset=i, expected=a, actual=b) for i, (a, b) in enumerate(zip(expect, restored, strict=True)) if a != b]
    need(sha(restored) == launch['restored_core_sha256'] and sha(expect) == launch['expected_restored_core_sha256']
         and drift == launch['all_Core_byte_differences']
         and launch['restored_core_exact_except_current_rom_crc'] == (restored == expect), 'exact non-normalized host comparison')
    need(restored == expect_prior and sha(restored) == preflight_report['checkpoint']['prior_restored_with_candidate_crc_sha256'],
         'cross-ROM change matches prior full resave after only the CRC field is qualified')
    need([v['offset'] for v in drift] == preflight.RESAVE_OFFSETS, 'preserved actual baseline source-to-resave deltas')
    meta = stateqa.prior.fields((directory / 'checkpoint/healthy-activation.txt').read_text(encoding='utf-8').strip())
    regions = {region: (directory / f'01-checkpoint-before-{region}.bin').read_bytes() for region in stateqa.OFFSETS}
    for region, data in regions.items():
        need(data == (directory / f'checkpoint/41-healthy-activation-{region}.bin').read_bytes(), 'strict restored native ' + region)
    state = stateqa.parse_checkpoint(current_state, meta, regions, rom)
    with zipfile.ZipFile(io.BytesIO(source_state)) as previous, zipfile.ZipFile(io.BytesIO(current_state)) as current:
        need(previous.read('SyncSettings.json') == current.read('SyncSettings.json'), 'same core sync configuration')
        user = json.loads(current.read('UserData.txt'))['o']
        need(set(user) == {'$type', 'output', 'checkpoint_dir', 'probe_sha256', 'stage11_boss_authorization'}
             and user['probe_sha256'] == preflight.NEW, 'exact scoped checkpoint metadata')
    return dict(reference_frame=state['frame'], state_regions=state['compared_regions'], actual_core_sha256=sha(restored),
                only_CRC_difference_relative_to_prior_resaved_core=True, exact_source_comparison_deltas=drift)


def route_and_captures(directory, launch, rom):
    bounded = launch['outcome'] == BOUNDED
    traces = (directory / 'wholeplay-trace.txt').read_text(encoding='utf-8').splitlines()
    entries = [fields(line) for line in traces]
    need([(e['event'], int(e['mode']), int(e['pc'], 16)) for e in entries] ==
         (MATCH_SEQUENCE[:19] if bounded else MATCH_SEQUENCE),
         'ordered actual combat/cleanup/interstitial/ending/title code hooks')
    indexed = {e['event']: e for e in entries}
    need(all(int(b['core']) >= int(a['core']) for a, b in zip(entries, entries[1:])), 'nondecreasing actual event cores')
    need(all(e['stage'] == '11' for e in entries[:16]), 'actual physical stage 11 through Results')
    baseline = ROOT / 'build' / LEAD_RUN
    expect_entries = (baseline / 'wholeplay-trace.txt').read_text(encoding='utf-8').splitlines()
    need(traces[:15] == expect_entries[:15], 'same measured inputs and hit/terminal route through native cleanup')
    decisions = (directory / 'shoot-checkpoint-aim-decisions.txt').read_bytes()
    need(decisions == (baseline / 'shoot-checkpoint-aim-decisions.txt').read_bytes(), 'complete ordinary input decision prefix exact')
    hits = [fields(line) for line in decisions.decode().splitlines() if 'B_candidate=true' in line]
    need(len(hits) == 1 and (hits[0]['core'], hits[0]['facing'], hits[0]['held'], hits[0]['reason']) ==
         ('89469', 'left', '0000', 'eligible'), 'one qualified mirrored B with earlier released input')
    ledgers = (directory / 'wholeplay-stage11-writes.txt').read_bytes()
    need(ledgers == (baseline / 'wholeplay-stage11-writes.txt').read_bytes() and len(ledgers.splitlines()) == 1,
         'same one consumed script write')
    ledger = fields(ledgers.decode().strip())
    for k, v in dict(core='89469', stage='11', FIRST='02011710', SECOND='02011828', AUX='02011940',
                     address='0201188C', bytes='2', before='37', after='1', requested='1', verified='true',
                     authorization='user-approved-development-stage11-boss-hp1-once').items():
        need(ledger[k] == v, 'actual write and read-back ' + k)
    writes = [fields(line) for line in (directory / 'wholeplay-mode-writes.txt').read_text(encoding='utf-8').splitlines()]
    route = [(int(item['old']), int(item['new'])) for item in writes]
    source_route = [(7, 8), (8, 12), (12, 13), (13, 11), (11, 20), (20, 3)]
    need(route == (source_route[:3] if bounded else source_route), 'physical mode writes only along source route')
    for action, version in zip(writes, ('results-constructor', 'mode12-constructor', 'mode13-constructor',
                                       'ending-entry', 'mode20-entry', 'title-ready')):
        need(action['address'] == '03002310' and int(action['pc'], 16) == 0x08015B64
             and int(action['core']) <= int(indexed[version]['core']), 'authoritative mode writer before typed constructor')
    run_trace = (directory / 'shoot-entry-trace.txt').read_text(encoding='utf-8').splitlines()
    captures = [fields(line) for line in run_trace if line.startswith('capture=') and 'observed_core=' in line]
    regs = {}
    for line in run_trace:
        matched = REG.fullmatch(line)
        if matched:
            name, key, value = matched.groups()
            regs.setdefault(name, {})[key] = int(value, 16)
    shots = {}
    earlier = json.loads((baseline / 'launch.json').read_bytes())['files']
    for num, capture in enumerate(captures, 1):
        name = capture['capture']
        need(name.startswith(f'{num:02d}-') and int(capture['export_core']) >= int(capture['observed_core']),
             'actual outer capture order and boundary')
        values = {region: (directory / f'{name}-{region}.bin').read_bytes() for region in RAM_TYPES}
        need(all(len(raw) == RAM_TYPES[region] for region, raw in values.items()), 'complete snapshot dump lengths')
        png = (directory / f'{name}.png').read_bytes()
        with Image.open(io.BytesIO(png)) as image:
            need(image.format == 'PNG' and image.size == (240, 160), 'valid GBA framebuffer')
            color_count = len(image.convert('RGB').getcolors(240 * 160))
        if num <= 8:
            for extension in ('.png', *(f'-{region}.bin' for region in RAM_TYPES)):
                key = name + extension
                need(launch['files'][key] == earlier[key], 'bit-identical pre-repair snapshot ' + key)
        iw, ew = values['iwram'], values['ewram']
        shots[name.split('-', 1)[1]] = dict(name=name, observed_core=int(capture['observed_core']),
            export_core=int(capture['export_core']), mode=word(iw, 0x2310), physical_stage=iw[0x231E], progress_byte=iw[0x232E],
            held=word(iw, 0x1302), edge=word(iw, 0x1306), colors=color_count, registers=regs.get(name, {}),
            SECOND_HP=word(ew, 0x1188C))
    damage = shots['wholeplay-hit-post']
    need((damage['observed_core'], damage['SECOND_HP'], damage['registers']['R4'], damage['registers']['R5'],
          damage['registers']['R0'], damage['registers']['R8']) == (89483, 0, 0x02011710, 0x02011828, 1, 0),
         'actual FIRST does real lethal damage to the guarded SECOND')
    for title in ('wholeplay-mode12-constructor', 'wholeplay-mode12-request', 'wholeplay-mode13-constructor',
                  'bounded-no-terminal' if bounded else 'wholeplay-mode13-request'):
        shot = shots[title]
        need((shot['held'], shot['edge']) == (0, 0), 'actual neutral outer input captures during automatic interstitials')
    if bounded:
        credits = credits_at_boundary(directory, rom, shots)
    else:
        need(shots['wholeplay-title-ready']['mode'] == 3 and shots['wholeplay-title-ready']['colors'] > 1,
             'native title framebuffer and true game mode')
        credits = None
    return dict(authorized_write=ledger, contiguous_stage11_prehit_input_exact=True, asserted_capture_prefix_snaps=8,
                physical_mode_chain=[route[0][0], *(new for _, new in route)], native_events=indexed,
                snapshots=shots, credits_at_boundary=credits)


def credits_at_boundary(directory, rom, shots):
    entry, final = (shots[name] for name in ('wholeplay-mode13-constructor', 'bounded-no-terminal'))
    need(final['observed_core'] - entry['observed_core'] == 4688 and final['mode'] == 13, 'actual bounded credits duration')
    note = (directory / 'shoot-entry-first-failure.txt').read_text(encoding='utf-8').splitlines()[0]
    need(note.startswith(f'outcome={BOUNDED} core=97405 timing=outer-frame-boundary detail=mode=13 stage=11 '),
         'only bounded disposition is reported')
    details = fields((directory / 'failure-observed.txt').read_text(encoding='utf-8').strip())
    need(details['input_relative'] == '8000' and details['stage7_consumed'] == 'false', 'native-only credits input scope')
    memories = {r: (directory / f'{final["name"]}-{r}.bin').read_bytes() for r in stateqa.OFFSETS}
    state = stateqa.parse_checkpoint((directory / 'failure-observed.State').read_bytes(), details, memories, rom)
    first_iw = (directory / f'{entry["name"]}-iwram.bin').read_bytes()
    last_iw = memories['iwram']
    page = [word(iw, 0x428E) for iw in (first_iw, last_iw)]
    pointer = [address(iw, 0x4290) for iw in (first_iw, last_iw)]
    states = [word(iw, 0x4272) for iw in (first_iw, last_iw)]
    need(page == [1, 8] and pointer == [0x080CF598, 0x080CFB18] and states == [0x0800, 0x0822],
         'mode13 native text descriptors and phase advance within the bound')
    for index, ptr in zip(page, pointer):
        need(address(rom, 0xCF4F0 + (index - 1) * 12) == ptr, 'native credit page pointer backed by the typed ROM descriptor')
    expected_tasks = {0x02010000: 0x08015AB4, 0x02010230: 0x080CAFAC,
                      0x02010348: 0x080CAD44, 0x02010460: 0x080CA7F0}
    for ew in ((directory / f'{entry["name"]}-ewram.bin').read_bytes(), memories['ewram']):
        tasks = {0x02000000 + off: address(ew, off) for off in range(0x10000, 0x10000 + 52 * 0x118, 0x118)
                 if address(ew, off + 0x10) & 2}
        need(tasks == expected_tasks, 'four valid active native credits tasks in both snapshots')
    need(final['colors'] > 1 and final['registers']['R15'] == 0x1C and final['registers']['CPSR'] & 0x1F == 0x12,
         'captured credits framebuffer and normal IRQ register bank')
    need(word(last_iw, 0x3DB2) == 50, 'live overlay hold at bound')
    return dict(native_mode=13, elapsed_frames=4688, next_page_indices=page, current_text_pointers=pointer,
                controller_values=states, remaining_current_overlay_hold_frames=50, native_active_tasks=expected_tasks,
                terminal_mode13_request_observed=False, final_state_frame=state['frame'],
                final_state_dump_comparisons=state['compared_regions'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, default=ROOT / 'build' / RUN)
    p.add_argument('--host-exit', type=int, choices=(0, 1), required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    need(not args.report.exists(), 'fresh report')
    launch_sha, launch, rom, preflight_report = bind(args.capture, args.host_exit)
    state = checkpoint_check(args.capture, launch, rom, preflight_report)
    route = route_and_captures(args.capture, launch, rom)
    status = ('ACTUAL_E212_SHOOT_RESULTS_AND_TITLE_PASS' if args.host_exit == 0
              else 'ACTUAL_E212_SHOOT_RESULTS_TO_LIVE_CREDITS_BOUNDED')
    result = dict(status=status, verifier_sha256=sha(Path(__file__).read_bytes()),
                  launch_sha256=launch_sha, rom_sha256=preflight.NEW, verified_files=len(launch['files']),
                  original_host_exit=args.host_exit, ending_title_observed=args.host_exit == 0,
                  checkpoint=state, observed_route=route, reviewer_ran_emulator=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()

