"""Audit the focused 6F queue traces before and after the event-table repair."""
import argparse
import json
from pathlib import Path

import verify_evolution_music_6f_campaign_capture as common
from verify_evolution_music_pause_capture import core, fields, need, read, sha, u, unique, word

ROOT = common.ROOT
OUTER = 'tools/bizhawk_probe_evolution_campaign_queue.lua'
EXTRA = {
    'bizhawk_probe_evolution_campaign_alignment_r2.lua': '049D0E891ED4CD35AAFBCC352FA6A6F6317D0DD6341587CBDFEA215A117BE122',
    'bizhawk_observe_evolution_event_queue.lua': 'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
}
HOSTS = {
    'baseline': ('build/run_evolution_music_6f_queue_20261116.py',
                 '16097026B24071385BB10FD0D93356464833169809D0F0363A2CF34FF87296F0', 'b'),
    'fixed': ('build/run_evolution_music_6f_tables_20261116.py',
              'E3039ED34DD098A7C2871258344E68602DB1CB66569A98C5E6A5650E35CCCE95', 'c'),
}
FIXED_ROM = 'build/evolution-transition-tables-20261116/component.gba'
FIXED_SHA = 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
FIRST = ROOT / 'build/bizhawk-music-three-6f-20261116-a'
PRESERVED = (
    'loaded-rom.bin', 'probe.gba', 'trace.txt', 'music-lifetime.txt', 'score999-writes.txt',
    'collision-alignment.txt', 'round3-pause-end-iwram.bin', 'round3-pause-end-ewram.bin',
)


def queue_rows(data):
    lines = data.decode('utf-8').splitlines()
    need(lines[0] == 'start readonly=true hooks=5 selection_ids=11..14 queue_ids=04,6F'
         and lines[-1].startswith('summary ') and all(line.startswith('event=') for line in lines[1:-1]),
         'closed exact queue witness')
    rows, summary = [fields(line) for line in lines[1:-1]], fields(lines[-1])
    need([core(row) for row in rows] == sorted(core(row) for row in rows), 'ordered witnessed frames')
    need(int(summary['selections']) == sum(row['event'].startswith('selected-') for row in rows)
         and int(summary['tick04']) == sum(row['event'] == 'tick04' for row in rows),
         'all selection and tick rows retained')
    return rows, summary


def baseline_chain(directory, audit, rows, summary):
    need(audit['status'] == 'OBSERVED_FAILURE' and audit['outcome'] == 'failure:unexpected-player-zero-restart',
         'retain exact observed failure')
    for name in PRESERVED:
        need(audit['inventory'][name] == sha(read(FIRST / name)), 'identical preserved first 6F artifact ' + name)
    entry = unique(rows, 'selected-835A1EC', id='11')
    selection = unique(rows, 'selected-835A558', id='11')
    accepted = unique(rows, 'accepted', core=selection['core'], r8='00000004', r9='00000001')
    evo = unique(rows, 'accepted', core='33689', r8='0000006F', r9='00000004')
    rom = read(directory / 'loaded-rom.bin')
    bad = u(rom, word(selection, 'p1') - 0x08000000) + word(selection, 'r0') * 16
    need(word(entry, 'r0') == 0 and word(entry, 'r8') == 0x0835A210
         and word(selection, 'r0') == 0x4000 and word(selection, 'r1') == 22
         and word(selection, 'r8') == 0x0835A596
         and u(rom, 0x35A5AC) == 0xE92D4000 and word(selection, 'p1') == 0x0861B4BC
         and u(rom, bad - 0x08000000 + 4) == 0xFFFFFFFF, 'invalid extended-character event is actual ARM-table overread')
    need(rows.index(selection) < rows.index(accepted) and int(summary['tick04']) == 0
         and word(accepted, 'lr') == 0x08012918
         and accepted['r5'] == selection['r5'] == '020118D4'
         and accepted['p1'] == selection['p1'] and word(accepted, 'selected') == 0x4000
         and word(accepted, 'r1') == word(accepted, 'command') == word(accepted, 'cursor') == 0xFFFFFFFF,
         'invalid event reaches native event-initializer and accepted type-one song 04')
    music, _, _, _ = common.parse_music(read(directory / 'music-lifetime.txt'))
    restart = unique(music, 'player-zero-start', core=str(core(accepted) + 1), r8='00000004', type='0001')
    need(word(restart, 'requested_header') == 0x083820A8 and word(restart, 'player_header') == common.TARGET_HEADER,
         'actual player-zero takeover in next frame')
    return dict(entry=entry, evolution_queue=evo, bad_air_selection=selection, accepted_type1_04=accepted,
                invalid_event_row=f'{bad:08X}', actual_takeover=restart, unchanged_first_capture=list(PRESERVED))


def fixed_chain(directory, audit, rows, summary):
    need(audit['status'] == 'PASS', 'actual whole fixed 6F route must pass')
    proof = audit['proof']
    entry = unique(rows, 'selected-835A1EC', id='11')
    selection = unique(rows, 'selected-835A558', id='11')
    evo = unique(rows, 'accepted', core=proof['selector']['core'], r8='0000006F', r9='00000004')
    need(word(entry, 'r0') == 105 and word(entry, 'r8') == 0x08D3F000
         and word(selection, 'r0') in (24, 25) and word(selection, 'r8') in (0x08D3F01E, 0x08D3F03C)
         and entry['r4'] == selection['r4'] == proof['selector']['r4']
         and int(summary['tick04']) == 0, 'source-backed entry and ordinary end event execute on actual CPU11')
    within = [row for row in rows if core(proof['start']) <= core(row) <= core(proof['stage_return'])]
    need(not any(row['event'] in ('accepted', 'stack-accepted')
             and (row.get('r8') == '00000004' if row['event'] == 'accepted' else row.get('r0') == '00000004')
             for row in within), 'no replacing ID04 through actual restoration')
    need(core(selection) >= core(proof['resume'][-1]) and core(selection) < core(proof['stage_return']),
         'valid ending event belongs to the gameplay lifecycle')
    return dict(entry=entry, evolution_queue=evo, source_ending_selection=selection,
                actual_stage_return=proof['stage_return'], canonical_alias_executions=[0, 0])


def audit(variant):
    host, host_sha, slot = HOSTS[variant]
    common.HOST, common.OUTER = host, OUTER
    common.EXTRA.update(EXTRA)
    common.PINS.update({host: host_sha, OUTER: 'E661F3170AA233C869A5F8EFE7E42EB085E8DBBBABFDE237F5829BA67F6A0FC6',
                        **{'tools/' + name: digest for name, digest in EXTRA.items()}})
    if variant == 'fixed':
        common.ROM = FIXED_ROM
        common.PINS.update({FIXED_ROM: FIXED_SHA,
             'build/evolution-transition-tables-independent-qa-20261116/gate.json':
             'A787F41CD3A78BD0B509F2A7EC96C10133BDB825292BC11EDB169D162AA2469B'})
    directory = ROOT / f'build/bizhawk-music-three-6f-20261116-{slot}'
    report = common.audit(directory)
    raw = read(directory / 'evolution-event-queue.txt')
    need(sha(raw) == report['inventory']['evolution-event-queue.txt'], 'unchanged queue witness')
    rows, summary = queue_rows(raw)
    verify = baseline_chain if variant == 'baseline' else fixed_chain
    report.update(queue_provenance=verify(directory, report, rows, summary), queue_summary=summary,
                  queue_verifier_sha256=sha(read(Path(__file__))))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--variant', choices=HOSTS, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(args.root_completed and not args.report.exists(), 'completed known capture and fresh report required')
    report = audit(args.variant)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    print(report['status'], report['outcome'], sha(read(args.report)))
