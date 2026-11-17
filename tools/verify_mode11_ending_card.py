"""Identify the retained native ending card and verify its ordinary A gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import unpack_from

from verify_gba_shoot_entry_capture import ROOT, fields, long, sha, word
from verify_gba_shoot_entry_capture_v2 import OFFSETS, parse_checkpoint
from verify_shoot_static_companion_clear import Machine, branch, need


RUN = 'bizhawk-shoot-checkpoint-results-v88r2-20261117-a'
LAUNCH = '6609F90CB2B3E4D842FD5A6716DB49D5DAFCFB964C08F488DC0B958530162311'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ROM = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
CREDITS = '16-bounded-no-terminal'
EARLIER = '15-wholeplay-ending-ready'
HEADER = 0x02010348
TASK = HEADER + 0x18
EDGE = 0x03001306
CONFIG = 0x03002310


def native_source(rom, source):
    need(sha(rom) == ROM and sha(source) == SOURCE, 'Exact current and source game images')
    need(source[0x74FA30 + 11 * 6:0x74FA30 + 12 * 6] == b'\x14' + bytes(5)
         and rom[0x15CC8 + 11 * 5:0x15CC8 + 12 * 5] == b'\x14' + bytes(4), 'Mode11 selector zero to mode20 in both')
    need(source[0x77A749:0x77A74C] == bytes.fromhex('a98000')
         and source[0x77A78D:0x77A790] == bytes.fromhex('a94000'), 'Original editor accepts B/A separately')
    need(source[0x77B207:0x77B22B] == bytes.fromhex(
         'f7470601007435f747060200752eb8000c8ec0bf5238268b4506a94000741d814f060200'),
         'Source implements the optional final card with rising A and separate fade bit')
    need(source[0x77B28F:0x77B29E] == bytes.fromhex('c745040100c745060000c745080000')
         and source[0x77B34D:0x77B355] == bytes.fromhex('b0ff3c007506b9fc'), 'Preserved routine is bypassed by source1.5 forced FF selector')
    need(long(rom, 0xC0F40) == 0xE92D403F and long(rom, 0xC1018) == 0xE59F50D0
         and long(rom, 0xC10CC) == 0xEBFD43D7 and branch(rom, 0xC10C8) == 0x0808B728, 'Actual retained native final card and writer')
    need(unpack_from('<3I', rom, 0x8B730) == (0xE1C580B4, 0xE1C590B6, 0xE1C5A0B8),
         'Exact native 1,0,0 request-store interface')
    need(unpack_from('<II', rom, 0x12130) == (0xE8BD403F, 0xE12FFF1E),
         'Fade service preserves caller timer R0 through return')


def captured_card(directory, rom):
    raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(raw)
    need(sha(raw) == LAUNCH and launch['completed'] and launch['loaded_rom_exact'] and launch['scripts_unchanged'],
         'Final original private run')
    files = ['loaded-rom.bin', 'wholeplay-trace.txt', 'shoot-entry-first-failure.txt', 'failure-observed.State',
             'failure-observed.txt', 'wholeplay-mode-writes.txt', f'{EARLIER}-ewram.bin']
    files += [f'{CREDITS}-{region}.bin' for region in OFFSETS]
    need(all(sha((directory / name).read_bytes()) == launch['files'][name] for name in files), 'Pinned actual capture bytes')
    native = {region: (directory / f'{CREDITS}-{region}.bin').read_bytes() for region in OFFSETS}
    detail = fields((directory / 'failure-observed.txt').read_text())
    saved = parse_checkpoint((directory / 'failure-observed.State').read_bytes(), detail, native, rom)
    trace = {row['event']: row for line in (directory / 'wholeplay-trace.txt').read_text().splitlines() for row in [fields(line)]}
    for event, core, pc in (('mode13-normal-request', '102010', '080CA3A0'),
                            ('ending-entry', '102012', '080BF1D4'), ('ending-ready', '102030', '080C0054')):
        need((trace[event]['core'], trace[event]['pc']) == (core, pc), 'Observed native event ' + event)
    need((trace['mode13-normal-request']['cursor'], trace['mode13-normal-request']['complete'],
          trace['mode13-normal-request']['request']) == ('22', '003F', '1,0,0'), 'Directly observed natural credits request')
    need(saved['frame'] == 105405 and launch['outcome'] == 'failure:bounded-no-terminal', 'Ending export at actual bound')
    iw, ew = native['iwram'], native['ewram']
    base = HEADER - 0x02000000
    first = (directory / f'{EARLIER}-ewram.bin').read_bytes()
    need((long(first, base), long(ew, base), long(ew, base + 4), word(ew, base + 0x10)) ==
         (0x080BFEA4, 0x080C0F40, 0x1000, 2), 'Same ending task header with a different live input callback')
    table, index, timer, flags, fade = unpack_from('<I4H', ew, base + 0x18)
    need((table, index, timer, flags, fade) == (0x080C1100, 5, 30, 1, 75),
         'Exact finished text and unarmed native fade')
    shown = long(rom, table - 0x08000000 + index * 4)
    need(rom[shown - 0x08000000:shown - 0x08000000 + 8] == b'KIMJOY\0\0', 'Final screenshot is a predefined native name card')
    need(tuple(word(iw, a) for a in (0x2310, 0x2314, 0x2316, 0x2318, 0x1302, 0x1306)) == (11, 0, 0, 0, 0, 0),
         'Ending mode and neutral sampled input with no pending transition')
    return dict(ending_constructor=102012, first_editor_hook=102030, elapsed_ending_frames=3393,
                last_core=105405, original_outcome=launch['outcome'], task_header=HEADER,
                earlier_input_callback=0x080BFEA4, final_input_callback=0x080C0F40,
                card='KIMJOY', card_table=table, card_index=index, flags=flags, fade_ticks_remaining=fade,
                complete_ending_input_schedule_logged=False, second_A_consumption_observed=False)


def check_input_and_request(rom):
    rows = []
    for state, edge, enables in ((0, 0x40, False), (1, 0, False), (1, 0x08, False),
                                 (1, 0x80, False), (1, 0x40, True), (3, 0x40, False)):
        m = Machine(rom)
        m.r[1] = TASK
        m.put(TASK + 8, state, 2)
        m.put(EDGE, edge, 2)
        m.services = {0x08000BA8: lambda vm: None}
        stop = m.run(0x080C1000, {0x080C1048})
        need(stop == 0x080C1048 and m.get(TASK + 8, 2) == (state | 2 if enables else state),
             'Only a fresh A on a finished card enables fading')
        need([row[1] for row in m.calls] == ([0x08000BA8] if enables else []), 'Palette capture begins only on fresh-A acceptance')
        rows.append(dict(initial_flags=state, input_edge=edge, new_fade=enables))
    for fade in (75, 2, 1):
        m = Machine(rom)
        m.r[1] = TASK
        m.put(TASK + 8, 3, 2)
        m.put(TASK + 0xA, fade, 2)
        sp = m.r[13]
        m.services = {addr: (lambda vm: None) for addr in (0x0801207C, 0x08012714, 0x0801565C)}
        stop = m.run(0x080C1048, {0x080C10CC, 0x080C10E8})
        need(m.r[13] == sp and m.get(TASK + 0xA, 2) == fade - 1, 'Exact native fade countdown')
        writes = [row for row in m.writes if CONFIG <= row[0] < CONFIG + 0xA]
        need((writes == [(CONFIG + 4, 1, 2), (CONFIG + 6, 0, 2), (CONFIG + 8, 0, 2)] and stop == 0x080C10CC)
             if fade == 1 else (not writes and stop == 0x080C10E8), 'Only fade zero invokes the actual native transition writer')
        rows.append(dict(fade_before=fade, fade_after=fade - 1, request_writes=writes))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    need(not args.report.exists(), 'Fresh report')
    directory = ROOT / 'build' / RUN
    rom = (directory / 'loaded-rom.bin').read_bytes()
    native_source(rom, args.source.read_bytes())
    report = dict(status='MODE11_ACTUAL_FINAL_CARD_INPUT_GATE_PASS', original_host_exit=1,
                  checker_sha256=sha(Path(__file__).read_bytes()), launch_sha256=LAUNCH,
                  observed=captured_card(directory, rom), native_fixtures=check_input_and_request(rom),
                  fixture_palette_only_modeled=True, proposed_pre_input_site=0x080C1018, proposed_post_request_site=0x080C10CC,
                  source_1_5_bypasses_optional_card=True, emulator_started_by_verifier=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
