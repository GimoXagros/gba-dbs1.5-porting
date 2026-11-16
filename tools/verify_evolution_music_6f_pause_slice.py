"""Verify the actual 6F pause and resume slice of the preserved campaign failure."""
import argparse
import json
from pathlib import Path

from verify_evolution_music_6f_campaign_capture import (
    PLAYER, ROOT, ROM, STOPPED, TARGET, TARGET_HEADER, core, fields, h, need,
    parse_music, read, sha, u, unique, word,
)

FRESH = ROOT / 'build/bizhawk-music-three-6f-20261116-a'
BASE = ROOT / 'build/evolution-music-three-capture-qa-20261116/audit-6f-a.json'
BASE_SHA = '272577BEC925F3216ACF6EE1D2A72BBF94C6E22A62503E03D3448AEA808277FA'


def audit():
    raw = read(BASE)
    need(sha(raw) == BASE_SHA, 'frozen whole-capture failure audit')
    baseline = json.loads(raw)
    need(baseline['status'] == 'OBSERVED_FAILURE'
         and baseline['outcome'] == 'failure:unexpected-player-zero-restart', 'actual terminal reason')

    def load(name):
        data = read(FRESH / name)
        need(sha(data) == baseline['inventory'][name], 'frozen artifact ' + name)
        return data

    rom = load('loaded-rom.bin')
    need(rom == read(ROOT / ROM) and u(rom, 0xD33000 + TARGET * 8) == TARGET_HEADER, 'exact loaded 8C72')
    rows, _, counts, summary = parse_music(load('music-lifetime.txt'))
    need(counts['iwram-alias-request'] == counts['iwram-alias-cache'] == (0, 0)
         and counts['campaign-cpu11-selection'] == (1, 1)
         and baseline['alignment_summary']['e5'] == '0', 'canonical execution counters')
    decision = unique(rows, 'campaign-cpu11-selection', r0='0000000B')
    selector = unique(rows, 'evolution-selector', entry_identity='0000000B', actor_identity='0B')
    queue = unique(rows, 'evolution-queue-return', core=selector['core'], queue='006F')
    start = unique(rows, 'player-zero-start', appended_id='111')
    returned = unique(rows, 'player-zero-start-return', core=start['core'])
    need(core(decision) < core(selector) == core(queue) == core(start) - 1
         and word(decision, 'flags') == 0x60 and decision['progress'] == '3'
         and word(queue, 'type') == 4 and word(queue, 'flags') & 0x100
         and word(start, 'r0') == PLAYER and word(start, 'r1') == TARGET_HEADER
         and word(start, 'cache') == TARGET and int(summary['starts6F']) == 1,
         'actual CPU11 native queue and 6F player-zero start')

    def active(row):
        return word(row, 'cache') == TARGET and word(row, 'player_header') == TARGET_HEADER

    need(active(returned), 'actual native target start return')
    first = core(start) + 1
    chains = {}
    for phase, service, lr, age, before_stop in (
        ('pause', 'mplay-stop', '0837C36F', 0, False),
        ('resume', 'mplay-resume', '0837C3A3', 34, True),
    ):
        entry = unique(rows, phase + '-entry')
        compare = unique(rows, phase + '-header-compare')
        call = unique(rows, service, lr=lr)
        need(first + age <= core(entry) == core(compare) == core(call) < first + age + 4
             and rows.index(entry) < rows.index(compare) < rows.index(call)
             and all(active(row) for row in (entry, compare, call))
             and word(compare, 'requested_header') == word(compare, 'active_header') == TARGET_HEADER
             and word(compare, 'r1') == word(compare, 'r0') == TARGET_HEADER
             and compare['equal'] == 'true' and word(call, 'r0') == PLAYER
             and bool(word(call, 'player_status') & STOPPED) == before_stop, 'real native ' + phase)
        chains[phase] = [entry, compare, call]
    boundaries = [unique(rows, 'pause-boundary', age='4'), unique(rows, 'pause-boundary', age='33'),
                  unique(rows, 'resume-boundary', age='38')]
    need([core(row) - first for row in boundaries] == [4, 33, 38] and all(active(row) for row in boundaries)
         and [bool(word(row, 'player_status') & STOPPED) for row in boundaries] == [True, True, False],
         'held and resumed same active/cache header')
    trace = load('trace.txt').decode('utf-8').splitlines()
    relative = first - int(fields(trace[0])['initial_core'])
    index = trace.index(f'input relative={relative} keys=Start')
    need([line for line in trace[index:] if line.startswith('input ')] == [
        f'input relative={relative + age} keys={key}' for age, key in ((0, 'Start'), (4, ''), (34, 'Start'), (38, ''))],
        'target actual input 4 Start, 30 neutral, 4 Start, then neutral')
    after_resume = [row for row in rows if core(row) > core(boundaries[-1])]
    replacement = unique(after_resume, 'player-zero-start', requested_header=f'{u(rom, 0xD33000 + 4 * 8):08X}')
    replacement_return = unique(after_resume, 'player-zero-start-return', core=replacement['core'])
    need(not any(row['event'] in ('devolution-return-site', 'stage-selector-return') for row in after_resume)
         and word(replacement, 'r8') == word(replacement, 'cache') == 4
         and word(replacement, 'type') == 1 and word(replacement, 'r0') == PLAYER
         and word(replacement_return, 'player_header') == word(replacement, 'requested_header')
         and core(replacement_return) + 1 == core(summary), 'type-one song 04 replaces 6F without a stage return')

    iwram, ewram = (load(f'round3-pause-end-{region}.bin') for region in ('iwram', 'ewram'))
    p1, cpu = (u(iwram, at) for at in (0x489C, 0x48A0))
    cpu_at = cpu - 0x02000000
    need(cpu == word(selector, 'r4') and iwram[0x231C] == 11 and ewram[cpu_at + 0x10:cpu_at + 0x12] == bytes((1, 11))
         and h(iwram, 0x2310) == 7 and u(ewram, cpu_at) == 0x0835A5F8
         and [h(ewram, actor - 0x02000000 + 0x64) for actor in (p1, cpu)] == [8, 8]
         and h(ewram, cpu_at + 0x94) == 58 and h(iwram, 0x4500) == 1933,
         'alive CPU is still evolved with nonzero countdown and battle timer at failure')
    need(len(baseline['score_writes']) == 7 and all(core(row) < first for row in baseline['score_writes']),
         'only seven prior approved score writes, before the target input')
    return dict(status='PAUSE_RESUME_PASS_STAGE_RETURN_OPEN', input_sha256=baseline['launch']['rom_sha256'],
                actual_failed_outcome=baseline['outcome'], cpu_decision=decision, native_selector=selector,
                evolution_start=start, pause=chains['pause'], resume=chains['resume'], boundaries=boundaries,
                replacement=replacement, replacement_return=replacement_return,
                terminal=dict(core=core(summary), mode=7, player_hp=8, cpu_hp=8, cpu_evolution_timer=58, battle_timer=1933),
                score_writes=len(baseline['score_writes']), canonical_alias_executions=[0, 0],
                telemetry_music_request_rows=dict(observed=counts['music-request'][0], emitted=counts['music-request'][1]),
                whole_failure_audit_sha256=BASE_SHA, verifier_sha256=sha(read(Path(__file__))),
                scope='Score-assisted isolated 8C72 runtime. Observed pause and resume; queue-time source of replacing request and stage return remain separate.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh audit output')
    result = audit()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], sha(args.report.read_bytes()))
