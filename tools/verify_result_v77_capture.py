#!/usr/bin/env python3
"""Audit a completed v77 KO capture against the frozen v76 run."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import struct

import verify_result_language_capture as q
from verify_result_v76_capture import changes, flat_inventory

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
OLD = BUILD / 'bizhawk-result-v76-20261110-a'
FRESH = BUILD / 'bizhawk-result-v77-20261110-a'
OUT = BUILD / 'result-v77-runtime-qa-20261116/final'
FINAL = 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
OBSERVER = 'tools/bizhawk_probe_result_music_lifetime.lua'
PRIOR_REPORT = 'build/result-v76-runtime-qa-20261110/ko-audit.json'
PRIOR_COMPARISON = 'build/result-v76-runtime-qa-20261110/v75-comparison.json'
PINS = {
    'tools/verify_result_language_capture.py': 'DA8D3AA45AFE81D6EDF328F084B69F333E138CF8FAEEA71BAA0AAF94347D1085',
    'tools/verify_result_language.py': '3607645DB4A8DD214A5EBBA02ECE12F725DA1D573015E7E131ED69E5653C86CA',
    'tools/verify_result_v76_capture.py': 'D5A9BAB2CC5924C05AC2185FFB7173BE85673C6E48C89A42EF9CA9514B77F244',
    'build/run_result_v77_r3_20261110.py': 'A6342D07460F21FB324005C31A717F6AA42E4232D478CDE69BC1EBE4ED28E339',
    'build/result-music-lifetime-wrapper-qa-20261110/report.json': '5C16B8D61EDD1549BD2B5E39938F12CAC870A9573075F2039BD46D05DD8F970B',
    PRIOR_REPORT: '2547A5562752AE0313E8928D72465BBF4EAFB7FAAC0AA92DDC2B7EB196FBD8D1',
    PRIOR_COMPARISON: '1E2C54B19978097345CC6241EE777F8F25815B080B0D724028984B3BE0595DFC',
}
HOOKS = {
    'evolution-selector', 'evolution-queue-return', 'music-request', 'player-zero-start',
    'player-zero-start-return', 'devolution-return-site', 'pause-entry', 'resume-entry',
    'pause-header-compare', 'resume-header-compare',
}
ROM_START = 0x08000000
OLD_TABLE = 0x08686800
NEW_TABLE = 0x08D33000
NEW_IDS = range(0x6C, 0x70)
IWRAM_START = 0x03000000
COPY_START, COPY_END, COPY_SOURCE = 0xBF0, 0xDB0, 0x37B33C
ADAPTER_START, ADAPTER_END = 0xD00, 0xD40


def pins():
    for name, digest in PINS.items():
        q.need(q.sha(q.read(ROOT / name)) == digest, 'frozen dependency ' + name)


def classify_iwram(word, old_rom, rom):
    address = word['offset']
    before, after = (int(word[key], 16) for key in ('before', 'after'))
    if address == 0xD0C and before == q.u(old_rom, 0x37B458) and after == q.u(rom, 0x37B458):
        return 'boot DMA copy of pause-cache branch'
    track_start, track_end = (q.u(rom, at) - IWRAM_START for at in (0x37FBB8, 0x37FBC4))
    if track_start <= address < track_end:
        return 'player-zero music track state'
    if 0x5A50 <= address < 0x5B50:
        return 'mixer channel state with v77 sample pointers'
    if (address, before, after) in ((0x7E08, 5, 0x0801140C), (0x7E0C, 1, 0x0801140C)):
        return 'stack range; producing write untraced'
    return 'unclassified'


def adapter_pointer_matches(data):
    matches = []
    for match in re.finditer(rb'(?=(...\x03))', data, re.S):
        value = int.from_bytes(match[1], 'little')
        if ADAPTER_START <= value & 0x7FFF < ADAPTER_END:
            matches.append(dict(at=match.start(), value=value, aligned=match.start() % 4 == 0))
    return matches


def maybe_arm_branch(data, address, target_predicate):
    hits = []
    for i, (word,) in enumerate(struct.iter_unpack('<I', data)):
        if word >> 28 == 15 or word & 0x0E000000 != 0x0A000000:
            continue
        site = address + 4 * i
        displacement = ((word & 0xFFFFFF) ^ 0x800000) - 0x800000
        target = site + 8 + 4 * displacement
        if target_predicate(target):
            hits.append([site, target])
    return hits


def copy_source_audit(rom, iwram):
    boot = tuple(q.u(rom, x) for x in range(0x22C, 0x24C, 4))
    q.need(boot == (0xE58670D8, 0xE59F4178, 0xE58640D4, 0xE3A04070,
                    0xE1C64DBC, 0xE1C68DBE, 0xE2877D07, 0xE58670D8)
           and q.u(rom, 0x3B0) == ROM_START + COPY_SOURCE + 1, 'pinned boot DMA3 copy')
    io_same = iwram[COPY_START:COPY_END] == rom[COPY_SOURCE:COPY_SOURCE + COPY_END - COPY_START]
    q.need(io_same and q.u(iwram, 0xCCC) == 0xE12FFF1E, 'whole copy and isolated BX LR entry')
    copy_holes = maybe_arm_branch(iwram, IWRAM_START, lambda t: 0x03000BF0 <= t < 0x03000DB0)
    mirror_hits = maybe_arm_branch(
        iwram, IWRAM_START, lambda t: t >> 24 == 3 and ADAPTER_START <= t & 0x7FFF < ADAPTER_END)
    rom_calls = maybe_arm_branch(rom, ROM_START, lambda t: t == 0x0837B44C)
    ram_pointers, rom_pointers = adapter_pointer_matches(iwram), adapter_pointer_matches(rom)
    q.need(copy_holes == [[0x03000AA0, 0x03000CCC], [0x03000AC4, 0x03000CCC], [0x03000D04, 0x03000D2C]]
           and mirror_hits == [[0x03000D04, 0x03000D2C]]
           and rom_calls == [[source, 0x0837B44C] for source in (0x080002F4, 0x080157F8, 0x080D1564, 0x080D15B0)]
           and not ram_pointers and not any(hit['aligned'] for hit in rom_pointers),
           'bounded direct ARM and literal search for copied adapter and mirrors')
    q.need(q.u(rom, 0x37FBB4) == 0x03006B40 and q.u(rom, 0x37FBB8) == 0x03004EA0
           and q.u(rom, 0x37FBC4) == 0x03005030 and q.u(rom, 0x37C258) == q.u(iwram, 0x7FF0) == 0x030059C0,
           'ROM music track and initialized sound info pointers')
    return dict(boot_dma=dict(config_at=0x0800022C, rom_source_literal=0x080003B0, rom_source=0x0837B33C,
                              iwram_destination=0x03000BF0, word_count=0x70),
                rom_branch=dict(site=0x0837B458, target=0x08D7DFC0),
                copied_branch=dict(site=0x03000D0C, target_if_executed=0x03A03874),
                ram_arm_direct_branch_encodings_to_copy=copy_holes, ram_arm_direct_branch_encodings_to_adapter_mirrors=mirror_hits,
                rom_direct_arm_branches_to_adapter=rom_calls, ram_raw_pointer_hits_to_adapter_mirrors=ram_pointers,
                rom_raw_pointer_hits_to_adapter_mirrors=rom_pointers,
                scope='Static direct-branch and raw literal scan plus ROM-path runtime telemetry. The run had no IWRAM execution hooks.')


def annotate_relocation(region, word, old_rom, rom):
    before, after = (int(word[key], 16) for key in ('before', 'after'))
    table_offset = before - OLD_TABLE
    if (region == 'iwram' and 0x7E00 <= word['offset'] < 0x8000 and
            0 <= table_offset < 108 * 8 and table_offset % 8 == 0 and
            after == NEW_TABLE + table_offset and
            old_rom[before - ROM_START:before - ROM_START + 8] == rom[after - ROM_START:after - ROM_START + 8]):
        return {'kind': 'relocated song-table row in IWRAM stack area',
                'ram_address': f'{0x03000000 + word["offset"]:08X}', 'song_id': table_offset // 8}
    return {'kind': classify_iwram(word, old_rom, rom) if region == 'iwram' else 'unclassified'}


def trace_compare(old_data, new_data):
    old = old_data.decode('utf-8').splitlines(keepends=True)
    new = new_data.decode('utf-8').splitlines(keepends=True)
    edits, frame_deltas = [], []
    for op, i, j, k, l in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if op == 'equal':
            continue
        edits.append(dict(op=op, old_start_line=i + 1, new_start_line=k + 1,
                          old=old[i:j], new=new[k:l]))
        if op == 'replace' and j - i == l - k:
            for n, (a, b) in enumerate(zip(old[i:j], new[k:l])):
                old_fields = q.fields(a.rstrip('\r\n'))
                new_fields = q.fields(b.rstrip('\r\n'))
                for key in ('core', 'relative', 'initial_core', 'result_age'):
                    if key in old_fields and key in new_fields and old_fields[key] != new_fields[key]:
                        before, after = int(old_fields[key]), int(new_fields[key])
                        frame_deltas.append(dict(old_line=i + n + 1, new_line=k + n + 1, field=key,
                                                 before=before, after=after, delta=after - before))
    return dict(byte_identical=old_data == new_data, old_lines=len(old), new_lines=len(new),
                raw_edits=edits, changed_frame_fields=frame_deltas)


def hex_field(row, field):
    return int(row[field], 16)


def music_audit(raw, rom, last_core):
    lines = raw.decode('utf-8').splitlines()
    q.need(lines[0] == 'start readonly=true policy=unchanged hook_count=10 per_label_limit=32 max_event_rows=320 absence_is_not_coverage=true',
           'pinned music trace policy')
    event_lines, summary_line, counter_lines = lines[1:-11], lines[-11], lines[-10:]
    q.need(summary_line.startswith('summary ') and all(line.startswith('count ') for line in counter_lines)
           and all(line.startswith('event=') for line in event_lines), 'closed music summary and ten footer counters')
    events = [q.fields(line) for line in event_lines]
    summary = q.fields(summary_line)
    counts = {row['event']: dict(observed=int(row['observed']), emitted=int(row['emitted']))
              for row in map(q.fields, counter_lines)}
    emitted = Counter(row['event'] for row in events)
    q.need(counts.keys() == HOOKS and emitted.keys() <= HOOKS and
           all(count['emitted'] == emitted[event] == min(32, count['observed']) for event, count in counts.items()),
           'closed music counts and row caps')
    cores = [int(event['core']) for event in events]
    q.need(cores == sorted(cores) and (not cores or cores[-1] <= int(summary['core'])) and int(summary['core']) >= last_core,
           'ordered music frames through final result capture')
    q.need(int(summary['evolution_entries']) == counts['evolution-selector']['observed'], 'selector summary')
    headers = {song: q.u(rom, NEW_TABLE - ROM_START + song * 8) for song in range(112)}
    start_counts = Counter()
    requests, starts, returns, covered = [], [], [], []
    for row in events:
        label, core = row['event'], int(row['core'])
        if label == 'music-request':
            song = hex_field(row, 'r8')
            q.need(song < 0x1E or song in NEW_IDS, 'pinned request ID filter')
            requests.append(dict(core=core, id=song, cache_at_request=hex_field(row, 'cache')))
        if label == 'player-zero-start':
            header = hex_field(row, 'requested_header')
            appended = next((song for song in NEW_IDS if headers[song] == header), -1)
            q.need(hex_field(row, 'r0') == 0x03006B40 and hex_field(row, 'r1') == header and
                   int(row['appended_id']) == appended, 'actual player-zero recipient and ROM song-header mapping')
            if appended >= 0:
                start_counts[appended] += 1
            request = next((r for r in reversed(requests) if r['core'] == core and
                            r['id'] != 0 and headers[r['id']] == header), None)
            start = dict(core=core, header=header, appended_id=appended, matching_request=request,
                         cache_at_start=hex_field(row, 'cache'), active_header_before=hex_field(row, 'player_header'))
            if request:
                q.need(start['cache_at_start'] == request['id'], 'observed matching request stored in cache at start')
            starts.append(start)
        if label == 'player-zero-start-return':
            start = next((s for s in reversed(starts) if s['core'] == core), None)
            active = hex_field(row, 'player_header')
            returns.append(dict(core=core, active_header=active, cache=hex_field(row, 'cache'), matching_start=start))
            if start and start['header'] == active and start['matching_request']:
                covered.append(dict(core=core, id=start['matching_request']['id'], active_header=active,
                                    cache=hex_field(row, 'cache')))
        if label in ('pause-header-compare', 'resume-header-compare'):
            q.need((row['equal'] == 'true') == (hex_field(row, 'active_header') == hex_field(row, 'requested_header')),
                   'header equality matches raw operands')
    if counts['player-zero-start']['observed'] == emitted['player-zero-start']:
        q.need(all(int(summary[f'starts{song:02X}']) == start_counts[song] for song in NEW_IDS), 'appended start summary')
    identities = [row for row in events if row['event'] == 'evolution-selector']
    queues = [row for row in events if row['event'] == 'evolution-queue-return']
    return_sites = [row for row in events if row['event'] == 'devolution-return-site']
    q.need(len(identities) == len(queues) == len(return_sites) == 1 and
           all(count['emitted'] == count['observed'] for count in counts.values()), 'one complete natural evolution cycle')
    selector, queue, return_site = identities[0], queues[0], return_sites[0]
    actor = hex_field(selector, 'actor_identity')
    selector_map = q.u(rom, 0xD14A8) - ROM_START
    selector_ids = q.u(rom, 0xD14AC) - ROM_START
    selected = rom[selector_ids + 2 * rom[selector_map + actor]]
    q.need(actor == hex_field(selector, 'entry_identity') == 1 and selected == hex_field(queue, 'queue') == 0x6E
           and hex_field(queue, 'flags') & 0x100 and hex_field(queue, 'type') == 4
           and int(queue['core']) == int(selector['core']), 'natural actor identity and ROM-derived 6E request')
    evolution_start = next(row for row in covered if row['id'] == selected)
    devolution_core = int(return_site['core'])
    restore = next(row for row in covered if row['core'] == devolution_core + 1)
    q.need(evolution_start['core'] == int(queue['core']) + 1 and evolution_start['cache'] == selected
           and hex_field(return_site, 'player_header') == headers[selected] and hex_field(return_site, 'cache') == selected
           and return_site['stage_music_eligible'] == 'true' and restore['id'] == restore['cache'] == 0x10
           and not any(evolution_start['core'] < row['core'] < restore['core'] for row in starts),
           'actual evolution cache, retained active header at de-evolution and stage start after eligible return')
    return dict(sha256=q.sha(raw), counts=counts, summary=summary, raw_event_lines=event_lines,
                ordinary_evolution=dict(actor=actor, selector_core=int(selector['core']), play=evolution_start,
                                        devolution_core=devolution_core, stage_restore=restore),
                requests=requests, starts=starts, returns=returns, active_cache_observations=covered,
                zero_observations=sorted(event for event, count in counts.items() if not count['observed']))


def audit():
    q.need(not OUT.exists(), 'fresh audit output directory')
    pins()
    inventories = [flat_inventory(directory) for directory in (OLD, FRESH)]
    prior = json.loads(q.read(ROOT / PRIOR_REPORT))
    prior_comparison = json.loads(q.read(ROOT / PRIOR_COMPARISON))
    q.need(prior['status'] == 'PASS' and prior['language'] == 'ko' and
           inventories[0] == prior_comparison['flat_capture_inventories'][1] and
           inventories[0]['launch.json'] == prior['launch_sha256'] and
           inventories[0]['trace.txt'] == prior['trace_sha256'], 'unchanged independently attested v76')
    rom = q.read(FRESH / 'probe.gba')
    old_rom = q.read(OLD / 'probe.gba')
    q.need(len(rom) == 0x1000000 and q.sha(rom) == FINAL and q.sha(old_rom) == prior['rom_sha256'],
           'actual v77 C344 and v76 280D images')
    report = q.audit(FRESH, rom, q.read(Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba')),
                     q.read(ROOT / OBSERVER))
    q.need((report['language'], report['snapshots'], report['writer_calls'], report['init_calls'], report['draw_calls'],
            report['rendered_label']['pixels']) == ('ko', 8, 1, 7, 88, 1508), 'ordinary KO and full WIN pixels')
    launch = json.loads(q.read(FRESH / 'launch.json'))
    alias = 'W:/build/' + FRESH.name
    q.need(launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + OBSERVER,
           '--userdata=output:' + alias + ';language:2;frames:24000;start_frame:2970', alias + '/probe.gba'],
           'exact approved ordinary-input arguments')
    config = json.loads(q.read(FRESH / 'config.json'))
    q.need(config['SoundEnabled'] is False and config['SoundOutputMethod'] == 3, 'observed completed silent method 3')

    traces = [q.read(directory / 'trace.txt') for directory in (OLD, FRESH)]
    caps = [{row['capture']: row for row in map(q.fields, raw.decode('utf-8').splitlines()) if 'capture' in row}
            for raw in traces]
    q.need(list(caps[0]) == list(caps[1]) and len(caps[0]) == 8, 'same eight capture labels in order')
    snapshots, issues = [], []
    copy = copy_source_audit(rom, q.read(FRESH / 'result-enter-iwram.bin'))
    for name, old_cap in caps[0].items():
        new_cap = caps[1][name]
        regions = {}
        for region, size in q.SIZES.items():
            before, after = (q.read(d / f'{name}-{region}.bin') for d in (OLD, FRESH))
            q.need(len(before) == len(after) == size, 'whole region length ' + name + '/' + region)
            if region == 'iwram':
                for ram, source in ((before, old_rom), (after, rom)):
                    q.need(ram[COPY_START:COPY_END] == source[COPY_SOURCE:COPY_SOURCE + COPY_END - COPY_START],
                           'entire boot copy matches its ROM in ' + name)
            diff = changes(before, after)
            for word in diff['aligned_words']:
                word.update(annotate_relocation(region, word, old_rom, rom))
            if any(word['kind'] == 'unclassified' for word in diff['aligned_words']):
                issues.append('raw changes to review in ' + name + '/' + region)
            regions[region] = dict(old_sha256=q.sha(before), new_sha256=q.sha(after), **diff)
        pngs = [q.read(d / f'{name}.png') for d in (OLD, FRESH)]
        if pngs[0] != pngs[1]:
            issues.append('PNG bytes differ at ' + name)
        snapshots.append(dict(capture=name, old_metadata=old_cap, new_metadata=new_cap,
                              core_delta=int(new_cap['core']) - int(old_cap['core']), regions=regions,
                              png_byte_identical=pngs[0] == pngs[1], png_sha256=list(map(q.sha, pngs))))
    q.need([snapshot['regions']['iwram']['changed_bytes'] for snapshot in snapshots] == [3, 3, 3, 3, 122, 122, 108, 108],
           'exact number of retained IWRAM byte differences per snapshot')
    trace = trace_compare(*traces)
    if not trace['byte_identical']:
        issues.append('raw result trace changes to review')
    music = music_audit(q.read(FRESH / 'music-lifetime.txt'), rom, int(caps[1]['result-plus300']['core']))
    q.need([flat_inventory(directory) for directory in (OLD, FRESH)] == inventories, 'capture inventories unchanged')
    pins()
    comparison = dict(status='REVIEW' if issues else 'PASS', issues=issues, dependencies=PINS,
                      checker_sha256=q.sha(q.read(Path(__file__))), flat_capture_inventories=inventories,
                      saved_sound_config={field: config[field] for field in ('SoundEnabled', 'SoundOutputMethod')},
                      snapshots=snapshots, trace=trace, music=music, copied_branch=copy)
    OUT.mkdir(exist_ok=False)
    files = {}
    for name, data in [('ko-audit.json', report), ('v76-comparison.json', comparison)]:
        path = OUT / name
        path.write_bytes((json.dumps(data, indent=2) + '\n').encode('utf-8'))
        files[name] = q.sha(q.read(path))
    print(json.dumps(dict(status=comparison['status'], issues=issues, files=files)))
    return bool(issues)


def selfcheck():
    result = trace_compare(b'first\r\nmode=8 core=4 relative=3\r\n', b'first\r\nmode=8 core=6 relative=5\r\n')
    q.need(not result['byte_identical'] and len(result['raw_edits']) == 1 and
           [row['delta'] for row in result['changed_frame_fields']] == [2, 2] and
           result['raw_edits'][0]['old'] == ['mode=8 core=4 relative=3\r\n'], 'exact raw trace/timing diff')
    raw = changes(bytes.fromhex('00686808'), bytes.fromhex('0030D308'))
    q.need(raw['changed_ranges'] == [dict(start=1, end=3, before='6868', after='30D3')],
           'original changed bytes remain visible')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    selfcheck()
    if not args.self_test:
        q.need(args.root_completed, 'root must confirm successful emulator exit and finalized launch before reading either capture')
        raise SystemExit(audit())

