"""Audit a finalized fresh E212 campaign replay and its observed ending route."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from struct import unpack_from

import check_ai_aligned_iraira_capture as iraira
from check_ai_corrected_campaign_capture import pinned_scope
from check_ai_producer_provenance_capture import manifest
import check_type8_corrected_campaign_capture as campaign
from verify_gba_shoot_entry_capture import ROOT, fields, ledger, long, sha, word
from verify_shoot_checkpoint_results_v88_capture import MATCH_SEQUENCE


RUN = 'bizhawk-wholeplay-v88-20261117-a'
BASELINE = 'bizhawk-wholeplay-v87-20261117-a'
ROM = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
HOST = '42940495A768F9F6B5C6630EE6895E139F2BA18B310D33D0F17E718A8C8E5D3F'
PINSET = 'B33913F5C9A105A5A789598B2855C49DB5FFF84C4C6C0373F585260F8E9E4E0A'
SUCCESS = 'campaign-shoot-terminal-results-title'
EVENTS = {row[0]: row[1:] for row in MATCH_SEQUENCE}
EVENTS['result-ready'] = (8, 0x0808A528)
EVENTS['result-label'] = (8, None)
MODE_ROUTE = ((7, 8), (8, 12), (12, 13), (13, 11), (11, 20), (20, 3))


def need(ok, label):
    if not ok:
        raise ValueError(label)


def launch_binding(directory, host_exit):
    digest, report = manifest(directory)
    need(host_exit == (0 if report['outcome'] == SUCCESS else 1), 'Original completed private host exit')
    flags = ('visible', 'physical_background_input', 'supplied_save_used', 'final_gba_cheat',
             'host_stop_requested', 'host_deadline_reached')
    need(all(report[name] is False for name in flags) and report['loaded_rom_exact'] and report['scripts_unchanged'],
         'Exact private execution and isolated save scope')
    need(report['phase_kind'] == 'assisted-v88-full-campaign-shoot-terminal-title', 'Expected live run')
    need(report['launcher_sha256'] == HOST == sha((ROOT / 'build/run_wholeplay_v88_20261117.py').read_bytes()),
         'Reviewed host identity')
    pin_file = (ROOT / 'build/wholeplay-v88-reviewed-pins-20261117.json').read_bytes()
    pins = json.loads(pin_file)
    need(len(pins) == 12 and pins == report['pins'] and report['reviewed_pins_sha256'] == sha(pin_file) == PINSET,
         'Reviewed 12-script pin set')
    need({path: sha((ROOT / path).read_bytes()) for path in pins} == pins, 'Exact immutable Lua scripts')
    exe = ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe'
    need(report['exe_sha256'] == campaign.EXE == sha(exe.read_bytes()), 'Approved emulator binary')
    alias = 'W:/build/' + directory.name
    args = ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/tools/bizhawk_probe_campaign_wholeplay_v88.lua',
            '--userdata=output:' + alias + ';frames:120000;start_frame:2970;combat_profile:approach-jump;probe_sha256:' + ROM
            + ';score_authorization:user-approved-development-score999;boss_authorization:user-approved-development-boss-once-per-stage'
            + ';stage11_boss_authorization:user-approved-development-stage11-boss-hp1-once', alias + '/probe.gba']
    need(report['arguments'] == args and report['guest_writes'] == [
        'authorized ordinary active FIRST+0x66 WORD=999',
        'authorized active stage7 SECOND+0x64 WORD=1 once; actual attack required',
        'authorized live stage11 SECOND+0x64 WORD=1 once at first eligible B; actual lethal hit required'],
        'Preserved campaign input and exactly three authorized write classes')
    config = json.loads((directory / 'config.json').read_bytes())
    need(all(config[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
         and all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
         and all(v['Path'] == f'{alias}/data/{i}' for i, v in enumerate(config['PathEntries']['Paths'])), 'Private clean-start configuration')
    saves = {p: h for p, h in report['files'].items() if p.startswith('data/')}
    need(set(saves) <= {'data/104/probe.SaveRAM'}, 'Only native fresh save storage possible')
    loaded = (directory / 'loaded-rom.bin').read_bytes()
    need(len(loaded) == 0x1000000 and report['rom_sha256'] == sha(loaded) == ROM
         and loaded == (directory / 'probe.gba').read_bytes()
         == (ROOT / 'build/repro-v88-20261117-a/current-candidate.gba').read_bytes()
         == (ROOT / 'build/repro-v88-20261117-b/current-candidate.gba').read_bytes(), 'Both whole-build and actually loaded image bytes')
    return digest, report, loaded, saves


def open_campaign(directory, rom, outcome):
    prior_field = campaign.fields

    def decode(line):
        row = prior_field(line)
        if line.startswith('summary outcome='):
            need(row['stage11_writes'] == 'separate-guarded-ledger', 'Separate authorized stage 11 scope')
            row['stage11_writes'] = 'disabled'
        return row

    parse = pinned_scope(campaign.events, ROM=ROM, fields=decode)
    rng, route, producers, active, hud, end = parse(directory, rom, outcome)
    end['stage11_writes'] = 'separate-guarded-ledger'
    if outcome == SUCCESS:
        need(len(producers) == len(active) == 11 and len(hud) == 2 and end['mode'] == '3',
             'Eleven produced and live encounters, both late HUDs, and an actual title end')
    return rng, route, producers, active, hud, end


def tail(directory, cap, outcome):
    rows = [fields(line) for line in (directory / 'wholeplay-trace.txt').read_text(encoding='utf-8').splitlines()]
    names = [row['event'] for row in rows]
    need(len(names) == len(set(names)), 'Unique native tail witness events')
    for row in rows:
        mode, address = EVENTS[row['event']]
        need(int(row['mode']) == mode and (address is None or int(row['pc'], 16) == address),
             'Typed native witness ' + row['event'])
        if address is None:
            need(int(row['pc'], 16) in (0x0808B0B0, 0x0808B174, 0x0808B1A0), 'Source-backed language/result draw hook')
    ordered = [name for name in names if name not in ('result-label', 'result-ready')]
    expected = [row[0] for row in MATCH_SEQUENCE]
    need(ordered == (expected if outcome == SUCCESS else expected[:len(ordered)]), 'Ordered witnessed terminal milestones')
    need([int(row['core']) for row in rows] == sorted(int(row['core']) for row in rows), 'Monotonic native order')
    writes = [fields(line) for line in (directory / 'wholeplay-mode-writes.txt').read_text('utf-8').splitlines()]
    route = [(int(row['old']), int(row['new'])) for row in writes]
    need(route == list(MODE_ROUTE if outcome == SUCCESS else MODE_ROUTE[:len(writes)]), 'Physical mode-word writes')
    for row in writes:
        need((row['address'], row['pc'], row['lr']) == ('03002310', '08015B64', '08015AE4'),
             'Native mode-word producer every time')
    if 'hit-post' in names:
        pre = rows[names.index('hit-pre')]
        shot = cap['wholeplay-hit-post']
        regs = shot['regs']
        need(regs['R4'] == int(pre['FIRST'], 16) and regs['R5'] == int(pre['SECOND'], 16)
             and int(pre['before']) == 1 and int(pre['damage']) == regs['R0'] > 0
             and shot['state']['p2']['hp'] == int(pre['after'], 16) == regs['R8'] & 0xFFFF
             and (regs['R8'] & 0xFFFF == 0 or regs['R8'] & 0x8000), 'Real qualified lethal Shoot store')
    for label in ('mode12-constructor', 'mode12-request', 'mode13-constructor', 'mode13-request'):
        if label in names:
            iw = campaign.raw(directory, cap['wholeplay-' + label], 'iwram')
            need(word(iw, 0x1302) == word(iw, 0x1306) == 0, 'Neutral automatic interstitial at each capture')
    if outcome == SUCCESS:
        title = cap['wholeplay-title-ready']
        need(title['state']['mode'] == 3 and title['colors'] > 1
             and word(campaign.raw(directory, title, 'iwram'), 0x2310) == 3, 'Actual title frame returned')
    return dict(ordered_events=rows, physical_modes=[route[0][0], *(new for _, new in route)] if route else [],
                native_mode_writes=writes)


def write_scope(directory, captures, active, summary):
    rows, scores, boss = ledger((directory / 'shoot-entry-writes.txt').read_text('utf-8').splitlines())
    stages = {row['stage']: int(row['core']) for row in active}
    need(all(row['stage'] in stages and int(row['core']) >= stages[row['stage']] - 1 for row in rows), 'Each write follows the matching live owner')
    need(scores == int(summary['score_writes']) and boss == int(summary['boss_writes']) == 1, 'Observed stage 7 and score writes')
    need({int(row['stage']) for row in rows if row['kind'] == 'score'} == set(range(11)) - {7}, 'One or more authorized scores in all ten ordinary stages')
    raw = (directory / 'wholeplay-stage11-writes.txt').read_text('utf-8').splitlines()
    need(len(raw) == 1, 'One separate stage 11 HP write')
    stage11 = fields(raw[0])
    recorded = captures['wholeplay-stage11-hp1']['trace']
    need(stage11['core'] == recorded['observed_core'] and stage11['stage'] == '11' and stage11['bytes'] == '2'
         and int(stage11['address'], 16) == int(stage11['SECOND'], 16) + 0x64
         and 1 < int(stage11['before']) < 0x8000 and stage11['requested'] == stage11['after'] == '1'
         and stage11['verified'] == 'true' and stage11['authorization'] == 'user-approved-development-stage11-boss-hp1-once',
         'Exactly authorized live stage 11 HP word and verified readback')
    return dict(score_count=scores, score_counts_by_stage=Counter(row['stage'] for row in rows if row['kind'] == 'score'),
                stage7=[row for row in rows if row['kind'] == 'boss'][0], stage11=stage11)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-exit', type=int, choices=(0, 1), required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'Fresh report')
    directory = ROOT / 'build' / RUN
    digest, launch, rom, saves = launch_binding(directory, args.host_exit)
    outcome = launch['outcome']
    need(all((directory / name).read_text('utf-8').strip() == outcome for name in
             ('wholeplay-done.txt', 'campaign-complete-done.txt', 'shoot-entry-done.txt')), 'All completion scopes agree')
    rng, route, producers, active, hud, end = open_campaign(directory, rom, outcome)
    captures, trace = campaign.capture_rows(directory, launch['files'])
    visuals, hud_data = campaign.audit_captures(directory, rom, captures, producers, active, hud)
    need(all(row['outer_frame_exact'] for row in hud_data.values()), 'Actual late HUD tile words')
    summary = fields(trace[-1])
    need(summary['outcome'] == outcome and summary['final_core'] == end['core'] and 0 <= int(end['relative']) <= 120000,
         'Final forward-only native bound')
    scope = write_scope(directory, captures, active, summary)
    witnessed = tail(directory, captures, outcome)
    checkpoint = pinned_scope(campaign.checkpoint, RUN=RUN, ROM=ROM)
    activation = pinned_scope(campaign.audit_handoff, checkpoint=checkpoint)(directory, rom, captures)
    iraira_capture = iraira.checked_iraira_assets(directory, rom, visuals['4']['file'])
    need(iraira_capture['hardware_palette_0'] == '0000' and iraira_capture['backdrop_matches_shadow'],
         'Actual source black Iraira backdrop in the full campaign')
    _, old = manifest(ROOT / 'build' / BASELINE)
    prefix = {name: digest for name, digest in old['files'].items()
              if re.match(r'^(?:[0-3][0-9]|4[01])-.+\.(?:png|bin)$', name)}
    need(prefix and all(launch['files'].get(name) == digest for name, digest in prefix.items()),
         'Fresh campaign retained exact v87 framebuffer and memory prefix through healthy Shoot')
    report = dict(status='ACTUAL_E212_FULL_CAMPAIGN_TITLE_PASS' if outcome == SUCCESS else 'ACTUAL_E212_FULL_CAMPAIGN_BOUNDED',
                  original_host_exit=args.host_exit, outcome=outcome, launch_sha256=digest, files=len(launch['files']),
                  checker_sha256=sha(Path(__file__).read_bytes()), rng_row=rng, source_route=list(route), campaign_end=end,
                  campaign_producers=producers, campaign_active_owners=active, late_hud=hud_data, visuals=visuals,
                  exact_pre_shoot_capture_files=len(prefix), authorized_writes=scope, clean_start_no_supplied_save=True,
                  native_generated_save_files=saves, shoot_handoff=activation, iraira=iraira_capture, ending=witnessed,
                  mode23_observed=False, emulator_started_by_auditor=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
