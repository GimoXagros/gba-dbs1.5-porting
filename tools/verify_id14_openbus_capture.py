"""Verify the frozen 8C72 ID14 collision producer and its post-instruction RAM row."""

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
HOST_SHA = '1B4F3E01CB6436CC520F00CF91A6C58EC777F87643B07F0338A71B1A8A4F7E76'
OUTCOME = 'collision-openbus-producer-observed'
P1, PRESENTATION, RESOURCE, RECORD = 0x02011710, 0x020117BC, 0x086184A0, 0x030048C8
OPCODES = {
    0x08352830: 0xE1D480B4, 0x08353BCC: 0xE5954024, 0x08353CA4: 0xE594400C,
    0x08353CA8: 0xE59F10D4, 0x08353D20: 0xE1D400B0, 0x08353D24: 0xE1C100B4,
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def h(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def w(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def fields(line):
    return dict(re.findall(r'([\w-]+)=(\S+)', line))


def numbers(row, **expected):
    for key, value in expected.items():
        need(int(row[key], 10 if key in {'core', 'id'} else 16) == value, f'{row.get("event")} {key}')


def verify_inventory(capture, host):
    launch = (capture / 'launch.json').read_bytes()
    report = json.loads(launch)
    files = {p.name: p.read_bytes() for p in capture.iterdir() if p.is_file() and p.name != 'launch.json'}
    need(len(files) == 51 and {name: sha(data) for name, data in files.items()} == report['files'], 'complete 51-file top-level manifest')
    need(report['completed'] and report['loaded_rom_exact'] and report['script_unchanged'] and
         report['outcome'] == OUTCOME and files['result-done.txt'].decode().strip() == OUTCOME, 'closed run')
    need(not report['visible'] and not report['physical_background_input'] and report['guest_writes'] == [] and
         (report['language'], report['target_song']) == (2, 0x6C), 'ordinary Korean ID14 host run')
    need(sha(host.read_bytes()) == report['host_sha256'] == HOST_SHA, 'actual inspected host identity')
    need(sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes()) == report['exe_sha256'] ==
         'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD', 'emulator executable')
    alias = 'W:/build/' + capture.name
    need(report['arguments'] == ['--gdi', '--config=' + alias + '/config.json',
         '--lua=W:/tools/bizhawk_probe_id14_openbus.lua',
         f'--userdata=output:{alias};language:2;target_song:108;frames:24000;start_frame:2970',
         alias + '/probe.gba'], 'isolated host argument vector')
    dependencies = {
        'bizhawk_probe_id14_openbus.lua': report['script_sha256'],
        'bizhawk_probe_evolution_music_three.lua': report['contact_script_sha256'],
        'bizhawk_probe_gba_collision.lua': report['base_script_sha256'],
        'bizhawk_probe_result_languages.lua': report['wrapped_script_sha256'],
        'bizhawk_probe_result_music_lifetime.lua': report['inner_script_sha256'],
        **report['extra_dependency_sha256'],
    }
    need(len(dependencies) == 10 and all(sha((ROOT / 'tools' / name).read_bytes()) == digest
         for name, digest in dependencies.items()), 'ten host Lua bindings')
    need(dependencies['bizhawk_probe_id14_openbus.lua'] == '30A3145E14C6C316978866BC8AF5EF088DBC5027FA9FC84D124CB67CB5EFB57A' and
         dependencies['bizhawk_observe_collision_openbus.lua'] == '2E92FCF81D391E558AC72E1D0D65A23661382DAFFB48B61AEFD13D1A77C43C88', 'inspected entry and observe scripts')
    rom = files['loaded-rom.bin']
    need(len(rom) == 0x1000000 and sha(rom) == report['rom_sha256'] == ROM_SHA and
         rom == files['probe.gba'], 'complete loaded 8C72 identity')
    cfg = json.loads(files['config.json'])
    need(all(cfg[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled')) and
         set(re.findall(rb'"AutoLoad"\s*:\s*(\w+)', files['config.json'])) == {b'false'}, 'private input and autoload configuration')
    need(all(entry['Path'] == f'{alias}/data/{index}' for index, entry in enumerate(cfg['PathEntries']['Paths'])), 'all data paths isolated')
    return files, sha(launch)


def verify_store(before, after):
    row = RECORD - 0x03000000
    before_row, after_row = before[row:row + 20], after[row:row + 20]
    need(w(before_row, 0) == P1 and w(before_row, 16) == 0xFFFFFFFF and
         (h(before_row, 4), h(after_row, 4)) == (8, 0xE5) and
         before_row[:4] == after_row[:4] and before_row[6:] == after_row[6:], 'only P1 type 0008 to 00E5 in row')
    return before_row.hex().upper(), after_row.hex().upper()


def verify_producer(files):
    rom = files['loaded-rom.bin']
    base = 0x08000000
    need(all(w(rom, address - base) == opcode for address, opcode in OPCODES.items()), 'actual producer instructions')
    queue_lines = files['evolution-event-queue.txt'].decode().splitlines()
    selected, accepted = [fields(line) for line in queue_lines if line.startswith('event=')]
    need((selected['event'], accepted['event']) == ('selected-835A1EC', 'accepted'), 'selector and accepted event sequence')
    numbers(selected, core=8322, pc=0x0835A1F0, r0=0xB054, r1=28, r4=P1, r5=PRESENTATION, r8=0x0835A210, id=14, p1=RESOURCE)
    numbers(accepted, core=8322, pc=0x080D15D4, lr=0x08012918, r5=PRESENTATION, p1=RESOURCE,
            selected=0xB054, command=0xFFFFFFFF, cursor=0xFFFFFFFF, r8=4)
    event = h(rom, 0x0835A210 - base + 14 * 2)
    event_row = w(rom, RESOURCE - base) + 16 * event
    need(event == 0xB054 and event_row == 0x086C89E8 and rom[event_row - base:event_row - base + 16] == bytes([255]) * 16, 'actual selected malformed ROM row')
    lines = files['collision-openbus.txt'].decode().splitlines()
    gate, before, after, write = [fields(line) for line in lines if line.startswith('event=')]
    need(tuple(row['event'] for row in (gate, before, after, write)) ==
         ('actor-gate', 'B-before', 'B-after', 'command-type'), 'ordered first producer hooks')
    for row in (gate, before, after, write):
        numbers(row, core=8322, r5=PRESENTATION, presentation=PRESENTATION, actor_flags=0xF780,
                event_id=event, command_index=0, command_count=0xFFFF, command_base=0xFFFFFFFF,
                command=0xFFFFFFFF, A=0xFFFFFFFF, event_B=0xFFFFFFFF, P1=RESOURCE)
    numbers(gate, pc=0x08352834, r4=P1)
    numbers(before, pc=0x08353CA8, lr=0x08352850, r4=0xFFFFFFFF, effective_read=0x0000000B)
    numbers(after, pc=0x08353CAC, lr=0x08352850, r4=0xA02004E3, loaded_B=0xA02004E3)
    numbers(write, pc=0x08353D28, lr=0x08352850, r0=0x9F0000E5, r1=RECORD, r4=0xA02004E3,
            dst=RECORD, B=0xA02004E3, loaded_type32=0x9F0000E5, stored_type16=0xE5, A_record=0xFFFFFFFF)
    need(files['collision-openbus-produced.txt'].decode().strip() == 'core=8322 B=A02004E3 loaded=9F0000E5 stored=00E5', 'producer marker')
    expected_counts = dict(zip(('actor-gate', 'B-before', 'B-after', 'event-type', 'command-type', 'overlap', 'metadata-before', 'metadata-after'), (1, 1, 1, 0, 1, 0, 0, 0)))
    counts = re.findall(r'^summary event=(\S+) count=(\d+)$', '\n'.join(lines), re.M)
    need(len(counts) == 8 and {name: int(count) for name, count in counts} == expected_counts and
         lines[-1] == 'complete=true invalid_captured=true e5_captured=true', 'producer witness closure and no observed overlap of tracked row')
    need(files['collision-alignment.txt'].decode().splitlines()[-1] == 'summary metadata=7 odd=0 confirmed=0 dispatch=7 e5=0', 'no E5 consumer observed')
    trace = files['trace.txt'].decode()
    need(trace.count('capture=pause-end core=8323 mode=7 tag=A2 ') == 1 and
         'guest_writes=none input=joypad-only' in trace and f'summary outcome={OUTCOME} ' in trace, 'immediate post-frame boundary')
    pre = 'collision-openbus-first-command'
    for ext, length in (('iwram', 0x8000), ('ewram', 0x40000)):
        witness = files[f'{pre}-{ext}.bin']
        need(len(witness) == len(files[f'pause-end-{ext}.bin']) == length and
             all(files[f'collision-openbus-first-{tag}-{ext}.bin'] == witness for tag in ('invalid', 'e5')), 'same pre-store callback, three named snapshots')
    for stem in (pre, 'pause-end'):
        i, e = files[f'{stem}-iwram.bin'], files[f'{stem}-ewram.bin']
        actor, p = P1 - 0x02000000, PRESENTATION - 0x02000000
        need(h(i, 0x2310) == 7 and w(i, 0x489C) == P1 and h(e, actor - 8) & 2 and
             e[actor + 0x10:actor + 0x12] == bytes((0, 14)) and w(e, actor + 0x14) == P1 and h(e, actor + 4) == 0xF780,
             'current actor and active player zero slot')
        need(h(e, p + 0xE) == event and h(e, p + 0x1A) == 0 and h(e, p + 0x1C) == 0xFFFF and
             e[p + 0x20:p + 0x30] == bytes([255]) * 16 and w(e, p + 0x44) == RESOURCE, 'actual malformed event and four presentation words in RAM')
    return verify_store(files[f'{pre}-iwram.bin'], files['pause-end-iwram.bin'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists() and args.capture.resolve() not in args.report.resolve().parents, 'fresh report outside the frozen capture')
    files, launch_sha = verify_inventory(args.capture, args.host)
    before, after = verify_producer(files)
    result = dict(status='ID14_OPENBUS_CAPTURE_QA_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  launch_sha256=launch_sha, files_verified=len(files), rom_sha256=ROM_SHA,
                  producer_core=8322, post_store_core=8323, actor='02011710', selected_event='B054',
                  presentation='020117BC', resource='086184A0', wrapped_read='0000000B',
                  loaded_B='A02004E3', loaded_type='9F0000E5', record='030048C8', type_store='030048CC',
                  record_before=before, record_after=after, tracked_overlap_observed=False,
                  e5_consumer_observed=False, historical_timeout_reproduced=False, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    with args.report.open('xb') as output:
        output.write(payload)
    print(result['status'], sha(payload))


if __name__ == '__main__':
    main()
