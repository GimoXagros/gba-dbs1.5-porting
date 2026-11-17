"""Compare the completed v79 non-ID13 KO with its already-frozen v77 baseline."""

import argparse
import json
from pathlib import Path
import re

import verify_result_language_capture as q
from verify_result_v76_capture import changes, flat_inventory

ROOT = Path(__file__).resolve().parents[1]
OLD_ROM = 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
NEW_ROM = 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
OLD_LAUNCH = '7DFB96EF420692625422E82B96FCF6F63A0816A0EA22A3C3151F9B688087089B'
PINS = {
    'script_sha256': 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
    'base_script_sha256': '7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9',
    'wrapped_script_sha256': '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
    'inner_script_sha256': '5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF',
}
SCRIPTS = ('bizhawk_probe_result_music_lifetime.lua', 'bizhawk_probe_gba_collision.lua',
           'bizhawk_probe_result_languages.lua', 'bizhawk_probe_result_languages_16m.lua')


def host_inverse():
    old, new = (q.read(ROOT / 'build' / name) for name in
                ('run_result_v77_r3_20261110.py', 'run_result_v79_20261117.py'))
    q.need(q.sha(old) == 'A6342D07460F21FB324005C31A717F6AA42E4232D478CDE69BC1EBE4ED28E339' and
           q.sha(new) == 'E905593C31CADA6CBA84CC404C39A4A181DCD023EC44586F76AD1BEF33DBAF1D', 'exact host pins')
    inverse = new
    for before, after in (('bizhawk-result-v79-20261117-', 'bizhawk-result-v77-20261110-'),
                          ('id13-air-relaunch-v79-20261117/component.gba', 'evolution-music-pause-cache-20261110/component.gba'),
                          (NEW_ROM, OLD_ROM), ("print((out/'result-done.txt')", "print((out/'trace.txt')")):
        q.need(inverse.count(before.encode()) == 1, 'unique host change ' + before)
        inverse = inverse.replace(before.encode(), after.encode())
    q.need(inverse == old, 'complete old host inverse')
    return q.sha(new)


def capture(directory, expected_rom):
    files = flat_inventory(directory)
    manifest = json.loads(q.read(directory / 'launch.json'))
    q.need(manifest['files'] == {name: value for name, value in files.items() if name != 'launch.json'}, 'complete top-level manifest')
    q.need(all(manifest[key] == value for key, value in PINS.items()), 'frozen observer family')
    q.need(manifest['completed'] and manifest['loaded_rom_exact'] and manifest['script_unchanged'] and
           manifest['language'] == 2 and manifest['visible'] is False and manifest['physical_background_input'] is False and
           manifest['guest_writes'] == [], 'closed Korean run with only ordinary inputs')
    q.need(manifest['exe_sha256'] == q.EXE and
           manifest['rom_sha256'] == files['loaded-rom.bin'] == files['probe.gba'] == expected_rom and
           (directory / 'loaded-rom.bin').stat().st_size == (directory / 'probe.gba').stat().st_size == 0x1000000, 'complete loaded ROM and executable identity')
    alias = 'W:/build/' + directory.name
    q.need(manifest['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/tools/' + SCRIPTS[0],
           f'--userdata=output:{alias};language:2;frames:24000;start_frame:2970', alias + '/probe.gba'], 'same input schedule and isolated arguments')
    raw_cfg = q.read(directory / 'config.json')
    cfg = json.loads(raw_cfg)
    q.need(all(cfg[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled')) and
           set(re.findall(rb'"AutoLoad"\s*:\s*(\w+)', raw_cfg)) == {b'false'} and
           all(entry['Path'] == f'{alias}/data/{n}' for n, entry in enumerate(cfg['PathEntries']['Paths'])), 'isolated paths, no autoload or background input')
    q.need(q.read(directory / 'result-done.txt').strip() == b'result-label-observed', 'actual result marker')
    return files, q.read(directory / 'trace.txt')


def compare(old, fresh):
    hosts = host_inverse()
    q.need(q.sha(q.read(ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe')) == q.EXE and
           all(q.sha(q.read(ROOT / 'tools' / script)) == sha for script, sha in zip(SCRIPTS, PINS.values())), 'runtime and probe file pins')
    old_files, old_trace = capture(old, OLD_ROM)
    new_files, new_trace = capture(fresh, NEW_ROM)
    q.need(old_files['launch.json'] == OLD_LAUNCH and len(old_files) == 65, 'frozen v77 comparison identity')
    q.need(old_trace == new_trace, 'entire ordered trace and frame numbering')
    lines = new_trace.decode().splitlines()
    snaps = [q.fields(line) for line in lines if line.startswith('capture=')]
    summary = q.fields(lines[-1])
    q.need(len(snaps) == 8 and (summary['writer_calls'], summary['init_calls'], summary['draw_calls']) == ('1', '7', '88') and
           all(summary[k] == 'true' for k in ('committed', 'title', 'battle', 'result', 'label', 'plus120', 'plus300')), 'ordinary result through +300')
    iwram = []
    for snap in snaps:
        name = snap['capture']
        q.need(q.read(old / (name + '.png')) == q.read(fresh / (name + '.png')), 'complete screenshot ' + name)
        for region, size in q.SIZES.items():
            filename = f'{name}-{region}.bin'
            before, after = [q.read(folder / filename) for folder in (old, fresh)]
            q.need(len(before) == len(after) == size, 'complete region ' + filename)
            if region == 'iwram' and before != after:
                iwram.append(dict(capture=name, before_sha256=old_files[filename], after_sha256=new_files[filename], **changes(before, after)))
            elif region != 'iwram':
                q.need(before == after, 'complete region identity ' + filename)
    for name in (snap['capture'] for snap in snaps if snap['capture'].startswith('result-')):
        ir = q.read(fresh / (name + '-iwram.bin'))
        er = q.read(fresh / (name + '-ewram.bin'))
        ptrs = [q.u(ir, off) for off in (0x489C, 0x48A0)]
        q.need(ptrs == [0x02011710, 0x02011828] and
               [(er[p - 0x02000000 + 0x10], er[p - 0x02000000 + 0x11]) for p in ptrs] == [(0, 0), (1, 1)], 'result records hold actual non-ID13 actors')
    q.need(flat_inventory(old) == old_files and flat_inventory(fresh) == new_files, 'both capture directories stayed frozen')
    return dict(status='ID13_SHARED_FALL_KO_IWRAM_REVIEW' if iwram else 'ID13_SHARED_FALL_KO_QA_PASS',
                old_launch_sha256=old_files['launch.json'], new_launch_sha256=new_files['launch.json'], host_sha256=hosts,
                matched_pngs=8, matched_non_iwram_ram_regions=40, ordered_trace_lines=len(lines), ordered_trace_sha256=q.sha(new_trace),
                snapshot_core_frames={snap['capture']: int(snap['core']) for snap in snaps}, non_id13_actor_ids=[0, 1],
                audio_observer_bytes_match=old_files['music-lifetime.txt'] == new_files['music-lifetime.txt'],
                old_inventory_without_launch=len(old_files) - 1, new_inventory_without_launch=len(new_files) - 1,
                iwram_differences=iwram, emulator_launched=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    old = ROOT / 'build/bizhawk-result-v77-20261110-a'
    q.need(not args.report.exists() and args.capture.resolve() not in args.report.resolve().parents and
           old.resolve() not in args.report.resolve().parents, 'fresh report outside frozen captures')
    result = compare(old, args.capture)
    result['checker_sha256'] = q.sha(q.read(Path(__file__)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(result['status'], q.sha(payload))


if __name__ == '__main__':
    main()
