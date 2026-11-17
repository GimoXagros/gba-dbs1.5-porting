"""Bind the natural mode 13 credit exit to its original source and capture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import unpack_from

from verify_gba_shoot_entry_capture import ROOT, fields, long, sha, word
from verify_gba_shoot_entry_capture_v2 import OFFSETS, parse_checkpoint
from verify_shoot_static_companion_clear import Machine, need


RUN = 'bizhawk-wholeplay-v88-20261117-a'
LAUNCH = '2BFD40718A37D23E528F705082165939ED70E006C2949EFDEA86FFFEF5F6C5DB'
ROM = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ENTRY, STORE_END = 0x080CA310, 0x080CA39C
STATE_NAME = '53-wholeplay-ending-before-mode13-exit'
SERVICES = [0x08012714, 0x08011BE4, 0x08011BE4, 0x080D15C0]
REQUEST = [(0x03002314, 1, 2), (0x03002316, 0, 2), (0x03002318, 0, 2)]


def verify_source(original, rom):
    need(sha(original) == SOURCE, 'Exact WSC source image')
    need(original[0x74FA30 + 13 * 6:0x74FA30 + 14 * 6] == b'\x0b' + bytes(5)
         and rom[0x15CC8 + 13 * 5:0x15CC8 + 14 * 5] == b'\x0b' + bytes(4), 'Slot 13 selector zero routes to ending on both engines')
    need(unpack_from('<6H', original, 0x74FACC + 13 * 12) == (0, 0x5A7D, 0x0201, 0x5A7D, 0x0287, 0x4FA3),
         'Original registered mode13 constructor')
    need(bytes.fromhex('680010687d5a684a029a8009ff4f') in original[0x75A9D1:0x75AA1A]
         and long(rom, 0xCA2B0) == 0x080CA2C0, 'Both constructors schedule the matched owner callback')
    need(original[0x75AA6B:0x75AA81] == bytes.fromhex('26833e0200167303e98e0026833e0a043f7403e94002'),
         'Original natural cursor and exact done flags guards')
    need(original[0x75AA8D:0x75AAA7] == bytes.fromhex('26ff3610049a320aff4f83c40468000c26ff3612049a320aff4f'),
         'Original retirement of the two credit tasks')
    need(original[0x75AADA:0x75AAE9] == bytes.fromhex('c745040100c745060000c745080000'),
         'Original credits callback writes native-equivalent request 1,0,0')
    words = unpack_from('<36I', rom, ENTRY - 0x08000000)
    need(words[2] == 0xE3590016 and words[7] == 0xE359003F and words[8:10] == (0x0A000000, 0xEA0000F3),
         'Native cursor and exact complete-flags compare')
    need(words[30] == 0xE1C590B4 and words[32] == 0xE1C590B6 and words[34] == 0xE1C590B8 and words[35] == 0xE8BD0020,
         'Exact native request tuple stores and natural post-store opcode')
    need(long(rom, 0xCBCC0) == 0xE8BD0020 and long(rom, 0xCBCA4) != long(rom, 0xCA380),
         'Separate existing fade-producer hook')


def observed_bound(directory, rom):
    launch_raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_raw)
    need(sha(launch_raw) == LAUNCH and launch['completed'] and launch['loaded_rom_exact']
         and launch['outcome'] == 'failure:wholeplay-ending-before-mode13-exit', 'Original closed run and exact outcome')
    selected = ['loaded-rom.bin', 'wholeplay-mode-writes.txt', 'wholeplay-trace.txt',
                'shoot-entry-first-failure.txt', 'failure-observed.State', 'failure-observed.txt',
                '52-wholeplay-mode13-constructor-ewram.bin']
    selected.extend(f'{STATE_NAME}-{region}.bin' for region in OFFSETS)
    for path in selected:
        need(sha((directory / path).read_bytes()) == launch['files'][path], 'Actual frozen evidence file ' + path)
    physical = [fields(row) for row in (directory / 'wholeplay-mode-writes.txt').read_text().splitlines()]
    need((physical[-1]['core'], physical[-1]['pc'], physical[-1]['lr'], physical[-1]['old'], physical[-1]['new']) ==
         ('102011', '08015B64', '08015AE4', '13', '11'), 'Actual physical credits exit and native dispatcher')
    tail = [fields(row) for row in (directory / 'wholeplay-trace.txt').read_text().splitlines()]
    need(tail[-1]['event'] == 'mode13-constructor' and tail[-1]['core'] == '92717'
         and not any(row['event'] == 'mode13-request' for row in tail), 'Prior observer did not record its selected fade hook')
    failure = (directory / 'shoot-entry-first-failure.txt').read_text().splitlines()
    detail = fields(failure[0])
    need((detail['core'], detail['timing'], fields(failure[1])['mode']) == ('102012', 'before-instruction', '11')
         and 'reg R15=080BF1D4' in failure, 'Observer stopped during valid machine mode11 constructor')
    native = {kind: (directory / f'{STATE_NAME}-{kind}.bin').read_bytes() for kind in OFFSETS}
    state = parse_checkpoint((directory / 'failure-observed.State').read_bytes(),
                             fields((directory / 'failure-observed.txt').read_text()), native, rom)
    iw, ew = native['iwram'], native['ewram']
    need(tuple(word(iw, a) for a in (0x2310, 0x3DA2, 0x4270, 0x428E, 0x1302, 0x1306)) ==
         (11, 22, 0x3F, 14, 0, 0) and long(iw, 0x4290) == 0x080D0038,
         'Neutral exit with completed cursor, flags, and final credit page')
    old_owners = [long(iw, a) for a in (0x4278, 0x427C)]
    entry_ew = (directory / '52-wholeplay-mode13-constructor-ewram.bin').read_bytes()
    def headers(memory):
        return [(long(memory, ptr - 0x02000000), word(memory, ptr - 0x02000000 + 0x10) & 2) for ptr in old_owners]
    need(old_owners == [0x02010230, 0x02010460] and headers(entry_ew) == [(0x080CAFAC, 2), (0x080CA7F0, 2)]
         and headers(ew) == [(0x080C07F4, 2), (0x080CA7F0, 0)], 'One original credit slot was reused by the ending, the other retired')
    return iw, dict(credits_constructor_core=92717, native_mode13_to_11_core=102011,
                    ending_constructor_core=102012, final_checkpoint_frame=state['frame'],
                    credits_cursor=22, finished_flags=63, final_page_index=13,
                    credits_task_headers=old_owners, ending_task_slot_reused=old_owners[0],
                    inactive_original_task_slot=old_owners[1], direct_natural_request_hook_observed=False)


def execute_gate(rom, iw):
    cases = []
    for cursor, flags, expected in ((21, 0x3F, 0x080CA3A8), (22, 0x3E, 0x080CA708),
                                    (22, 0x13F, 0x080CA708), (22, 0x3F, STORE_END),
                                    (23, 0x3F, STORE_END)):
        m = Machine(rom, seed=17)
        m.services = dict.fromkeys(SERVICES, lambda vm: None)
        before_sp = m.r[13]
        m.put(0x03002310, 13, 2)
        m.put(0x03003DA2, cursor, 2)
        m.put(0x03004270, flags, 2)
        for off in (0x4278, 0x427C):
            m.put(0x03000000 + off, long(iw, off))
        m.r[5] = 0x15555555
        done = m.run(ENTRY, {0x080CA3A8, 0x080CA708, STORE_END})
        need(done == expected, 'Actual native branch gate')
        calls = [row[1] for row in m.calls]
        writes = [change for change in m.writes if 0x03002310 <= change[0] <= 0x03002318]
        if done == STORE_END:
            need(calls == SERVICES and writes == REQUEST and m.get(m.r[13]) == 0x15555555
                 and m.r[13] == before_sp - 4 and m.r[5] == 0x03002310,
                 'Two retirement service calls, sound, ordered request, stack pre-return')
        else:
            need(not writes and not calls and m.r[13] == before_sp, 'Blocked gates do not request or retire')
        cases.append(dict(cursor=cursor, flags=flags, reached=done, service_targets=calls, ordered_request_writes=writes))
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    need(not args.report.exists(), 'Fresh report')
    directory = ROOT / 'build' / RUN
    rom = (directory / 'loaded-rom.bin').read_bytes()
    need(sha(rom) == ROM, 'Exact observed game image')
    verify_source(args.source.read_bytes(), rom)
    iw, observed = observed_bound(directory, rom)
    report = dict(status='MODE13_NATIVE_NORMAL_EXIT_SOURCE_AND_CAPTURE_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  original_host_exit=1, launch_sha256=LAUNCH, rom_sha256=ROM, source_sha256=SOURCE,
                  normal_post_store_hook=STORE_END, normal_post_store_opcode=0xE8BD0020,
                  alternate_fade_post_store_hook=0x080CBCC0, observed=observed,
                  exact_ARM_gate_fixtures=execute_gate(rom, iw), fixture_native_imports_modeled=True,
                  another_emulator_launched_by_checker=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
