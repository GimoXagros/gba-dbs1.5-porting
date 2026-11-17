"""Check the isolated stage 11 Results repair against source and the v87 capture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import verify_shoot_caller_resident as scanner
from verify_gba_shoot_entry_capture_v2 import checkpoint_core, parse_checkpoint
from verify_mode23_eligibility_storage import EEPROMFixture
from verify_shoot_static_companion_clear import Machine, Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16


BASE, CONFIG, RESULT = 0x08000000, 0x03002310, 0x03004738
FIRST, HOOK, CONTINUATION, ADAPTER = 0x08089534, 0x89538, 0x0808953C, 0xD8CB20
INIT_STOPS, CREATE_STOPS = {0x08089574, 0x08089668}, {0x080897EC, 0x080897F4}
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
AFTER = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
MANIFEST = '3056D7601D1C89C84FDE341EEFEAD50B68B27AE7F7415B9A047A2D0657FB6770'
OWNER = '162C4A9D2B8A684582EF2C3F22D8E60B6887E832BEBE4CB23730169C2198425C'
STAGE_SOURCE = {
    (0x777049, 0x777074): '048FE02C0757CB5341D9601A57AA22887F7D671C883B73DA82C6F60CB6E06E86',
    (0x777200, 0x77725C): 'EA344B44DB82E91A34B2443A75F929CE2F5E356ABE9261F0CAA7E42536979FC3',
    (0x777AA3, 0x777B18): 'E527E3C75E935F9FCB36A611BABA77980084028DB8098F41F05FD2F361FA0427',
}
NATIVE = {
    (0x89534, 0x89574): '6C65980BCA7D35C0352E71F75603381784CF97038F1AFD095CC19B166CF486AE',
    (0x897AC, 0x897F4): 'A615625B94422AC0306E1F1570E44A9967D934498D3881015D2DF120452C2D1C',
    (0x8A698, 0x8A7B4): '6DA9535558B3C42FA5843CF1446453475743FE87B1142B84CD39351861E849F6',
    (0x8B638, 0x8B674): 'FED8CF8995F68FD2B88C3F41E6796D3B81AD279414217E7638F8FDF8EB38BB16',
    (0x8B728, 0x8B748): 'E98417F7D8374339A84131D434601F954A2CEEC3E9EB9E0BA292A165D595A1A3',
    (0x15B40, 0x15B70): '53642FC1679B6A22799CAFC0D9C1337BF4B079F9791E79AAEEC06650B6950416',
}
need, sha = scanner.need, scanner.sha


def words(data, offset, count=1):
    return struct.unpack_from(f'<{count}I', data, offset)


def half(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def exact(data, offset, rows, arm=False):
    arch, mode, origin = (CS_ARCH_ARM, CS_MODE_ARM, BASE) if arm else (CS_ARCH_X86, CS_MODE_16, 0)
    decoded = list(Cs(arch, mode).disasm(data[offset:offset + 256], origin + offset, count=len(rows)))
    found = [f'{ins.mnemonic} {ins.op_str}'.strip() for ins in decoded]
    need(found == list(rows), f'exact decoded source/native lineage at {offset:06X}: {found}')


def admitted_artifacts(source, before, after, manifest_raw, owner_raw):
    need(tuple(map(sha, (source, before, after, manifest_raw, owner_raw))) == (SOURCE, BEFORE, AFTER, MANIFEST, OWNER),
         'exact pinned source, prior, component, manifest')
    for image, checked in ((source, STAGE_SOURCE), (before, NATIVE)):
        for (start, end), digest in checked.items():
            need(sha(image[start:end]) == digest, f'ownership anchor {start:06X}')
    exact(source, 0x777049, ('cmp byte ptr [di + 0xe], 0xb', 'je 0x777055',
                             'cmp byte ptr [di + 0xe], 7', 'jne 0x777074'))
    exact(source, 0x777060, ('test ax, 0x10', 'je 0x77706d', 'lcall 0x76f1, 0x1581',
                             'mov dx, 0x4000', 'or word ptr es:[si + 6], dx'))
    exact(source, 0x777224, ('test word ptr es:[si + 6], 0x4000', 'jne 0x777237',
                             'test word ptr es:[si + 6], 0x8000', 'jne 0x77723a'))
    exact(source, 0x777237, ('mov dx, 3', 'push di', 'push ds', 'mov di, 0x1000', 'mov ds, di',
                             'mov di, 0x4e', 'mov word ptr [di + 4], 1', 'mov word ptr [di + 6], dx',
                             'mov word ptr [di + 8], 0'))
    exact(before, 0x897BC, ('ldrh r8, [r4, #6]', 'tst r8, #0x4000', 'bne #0x80897d8'), arm=True)
    exact(after, ADAPTER, ('cmp r8, #7', 'cmpne r8, #0xb', 'b #0x808953c'), arm=True)
    exact(after, HOOK, ('b #0x8d8cb20', 'bne #0x8089574'), arm=True)
    need(before[ADAPTER:ADAPTER + 12] == b'\xff' * 12 and len(before) == len(after) == 0x1000000, 'only approved blank span')
    inverse = bytearray(after)
    inverse[HOOK:HOOK + 4], inverse[ADAPTER:ADAPTER + 12] = before[HOOK:HOOK + 4], before[ADAPTER:ADAPTER + 12]
    need(inverse == before, 'whole-image inverse')
    census = FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((ADAPTER, ADAPTER + 12),)),
                          argdefs=scanner.inbound.__defaults__)
    need(not census(before), 'full predecessor strict zero inbound')
    need(census(after) == [('ARM branch', HOOK, BASE + ADAPTER)], 'only intended installed incoming branch')
    manifest = json.loads(manifest_raw)
    owner = json.loads(owner_raw)
    need(owner['output_sha256'] == BEFORE and owner['reservations'] == [[0xD8C800, 0xD8CE00]],
         'serial child-contact reservation identity')
    code, hook = owner['writes']
    used_start, used_stop = code['offset'], code['offset'] + code['size']
    need((used_start, used_stop, hook['offset'], hook['size']) == (0xD8C800, 0xD8CA68, 0x36F77C, 4)
         and used_stop <= ADAPTER < ADAPTER + 12 <= 0xD8CE00, 'narrow tail of earlier claimed envelope')
    for row in (code, hook):
        start, stop = row['offset'], row['offset'] + row['size']
        need(before[start:stop] == after[start:stop] == bytes.fromhex(row['after_hex']),
             'earlier child-contact code and route are preserved byte-for-byte')
    serial = dict(manifest_sha256=OWNER, reserved_span=[0xD8C800, 0xD8CE00],
                  prior_payload_span=[used_start, used_stop], borrowed_tail_span=[ADAPTER, ADAPTER + 12])
    need(manifest['serial_child_contact_tail'] == serial, 'tail suballocation reported')
    need({(row['offset'], row['size']) for row in manifest['writes']} == {(HOOK, 4), (ADAPTER, 12)}, 'exact small emitted span list')
    for mode, selector, result in ((8, 3, 12), (12, 0, 13), (13, 0, 11), (11, 0, 20), (20, 0, 3)):
        need(source[0x74FA30 + 6 * mode + selector] == result == after[0x15CC8 + 5 * mode + selector],
             'original mode-route selector and native target')
    need(before[0xD3FB50:0xD3FB80] == after[0xD3FB50:0xD3FB80], 'ordinary progress table and following bytes exact')
    return dict(ordinary_progress_rows=11, ending_transition_modes=[8, 12, 13, 11, 20, 3],
                terminal_request=[1, 3, 0], patches=manifest['writes'], whole_image_inverse=True,
                serial_child_contact_tail=serial)


def capture_and_reconstruct(capture, before):
    launch_raw = (capture / 'launch.json').read_bytes()
    launch = json.loads(launch_raw)
    need(launch['completed'] and launch['loaded_rom_exact'] and launch['scripts_unchanged']
         and launch['outcome'] == 'failure:bounded-no-terminal', 'completed pinned failure capture')
    need((capture / 'loaded-rom.bin').read_bytes() == before, 'exact failure ROM')
    failed = '12-bounded-no-terminal'
    dumps = {name: (capture / f'{failed}-{name}.bin').read_bytes()
             for name in ('iwram', 'ewram', 'vram', 'palette', 'oam')}
    prior = (capture / '11-wholeplay-result-label-iwram.bin').read_bytes()
    state = (capture / 'failure-observed.State').read_bytes()
    text = (capture / 'failure-observed.txt').read_text(encoding='utf-8')
    metadata = dict(re.findall(r'(\w+)=([\da-fA-F]+)(?:\s|$)', text))
    identity = parse_checkpoint(state, metadata, dumps, before)
    raw, _ = checkpoint_core(state)
    registers = words(raw, 0x24, 16)
    iw = dumps['iwram']
    need((iw[0x232E], prior[0x232E], iw[0x231E], half(iw, 0x2310)) == (11, 10, 11, 8),
         'observed progress 10 to 11 during stage 11 Results')
    need((half(iw, 0x4738), half(iw, 0x473E)) == (0x8697, 0x3F03), 'actual win and ready bits')
    active = words(iw, 0x1344)[0]
    need(words(dumps['ewram'], active - 0x02000000)[0] == 0x0808A698, 'actual last task is ordinary result exit')
    expected = {0: 11, 1: 44, 4: CONFIG, 5: RESULT, 8: 0x08D3FB50, 9: 0xFFFFFFFF}
    need(all(registers[i] == v for i, v in expected.items()), 'saved mGBA native general register bank')
    bug = Machine(before)
    for addr, count, data in ((0x03002310, 0x40, iw[0x2310:0x2350]), (0x03004738, 0x40, iw[0x4738:0x4778])):
        for offset, value in enumerate(data[:count]):
            bug.put(addr + offset, value, 1)
    bug.put(CONFIG + 0x1E, prior[0x232E], 1)
    stopped = bug.run(0x0808A6A0, {0x0808B670}, max_steps=200)
    need(stopped == 0x0808B670 and bug.get(CONFIG + 0x1E, 1) == 11, 'reconstructed ordinary result increments through actual producer selector')
    need(all(bug.r[i] == v for i, v in expected.items()), 'reproduced exact saved selector registers before BX')
    need(words(before, 0xD3FB50 + 11 * 4)[0] == 0xFFFFFFFF, 'first word past the ordinary table')
    return dict(launch_sha256=sha(launch_raw), failure_checkpoint_sha256=sha(state), same_frame_state=identity['frame'],
                state_sections=identity['compared_regions'], physical_stage=11, mode=8,
                observed_progress=[10, 11], observed_active_callback=0x0808A698,
                observed_saved_registers={f'R{index}': registers[index] for index in (*expected, 15)},
                replay_entered_at=0x0808A6A0, reconstructed_stopped_before=0x0808B670,
                unexecuted_invalid_branch_target=0xFFFFFFFF)


def fixture(rom):
    m = EEPROMFixture(rom, bytes(8))
    for i in range(0x40):
        m.put(RESULT + i, 0, 1)
    m.put(CONFIG, 8, 2)
    m.put(CONFIG + 0x1E, 10, 1)
    return m


def call_to_constructor(rom, stage, win, last_zero, continued):
    m = fixture(rom)
    m.put(CONFIG + 0xE, stage, 1)
    m.put(CONFIG + 0x1A, int(continued), 2)
    m.r[4], m.r[5], m.r[0], m.r[3] = RESULT, CONFIG, (0x10 if win else 0), int(not last_zero)
    init = m.drive(FIRST, INIT_STOPS)
    sp = m.r[13]
    construct = m.drive(0x080897AC, CREATE_STOPS)
    calls = [target for _, target, _ in m.calls]
    need(m.r[13] == sp - 28, 'constructor normal 7-word prologue frame')
    request = tuple(m.get(CONFIG + off, 2) for off in (4, 6, 8))
    stage_progress = m.get(CONFIG + 0x1E, 1)
    return m, init, construct, request, stage_progress, calls


def program_cases(before, after):
    m = Machine(after)
    # Compare eligibility routing at the exact overwritten CMP without changing stage in a game.
    for stage in range(256):
        m.r[8] = stage
        m.run(BASE + HOOK, {CONTINUATION})
        need(m.r[8] == stage and bool(m.cpsr & 0x40000000) == (stage in (7, 11)), 'target condition for each physical stage byte')
    summary = []
    for stage in (0, 7, 10, 11, 12):
        for win, last_zero, continued in ((True, True, False), (True, True, True), (False, True, False), (True, False, False)):
            m, init, constr, request, progress, calls = call_to_constructor(after, stage, win, last_zero, continued)
            special = stage in (7, 11)
            terminal_win = special and win and last_zero
            need((init, constr) == ((0x08089668, 0x080897EC) if special else (0x08089574, 0x080897F4)),
                 'normal/final constructor control flow')
            need(request == ((1, (3 if terminal_win else 1), 0) if special else (0, 0, 0))
                 and progress == 10, 'only native correct final-stage request, no ordinary progress increment')
            need(m.get(RESULT + 6, 2) == (0x4000 if terminal_win else 0x8000 if special else 0),
                 'actual result flag written into known shared owner')
            need((0x0808B334 in calls) == terminal_win and 0x0808B638 not in calls,
                 'source save callback and denied ordinary producer')
            if stage != 11:
                previous = call_to_constructor(before, stage, win, last_zero, continued)
                need((init, constr, request, progress, calls) == previous[1:], 'prior non-11 behavior preserved')
            if terminal_win and stage == 11:
                m.r[4], m.r[5] = BASE + 0x15CC8 + 8 * 5, CONFIG
                m.run(0x08015B40, {0x08015B60})
                need(m.get(CONFIG, 2) == 12 and all(m.get(CONFIG + off, 2) == 0 for off in (4, 6, 8)),
                     'actual native dispatcher consumes request into mode 12')
            summary.append((stage, win, last_zero, continued))
    old = call_to_constructor(before, 11, True, True, False)
    need(old[1:5] == (0x08089574, 0x080897F4, (0, 0, 0), 10), 'old stage 11 entered ordinary result constructor')
    return dict(compare_cases=256, initializer_and_constructor_cases=len(summary),
                positive_stage_11_dispatch_to_mode_12=True, exact_native_non11_controls=16)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'before', 'after', 'manifest', 'owner', 'report'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--capture', type=Path)
    a = p.parse_args()
    need(not a.report.exists(), 'fresh report')
    source, before, after, manifest, owner = [getattr(a, key).read_bytes()
                                              for key in ('source', 'before', 'after', 'manifest', 'owner')]
    lineage = admitted_artifacts(source, before, after, manifest, owner)
    observed = capture_and_reconstruct(a.capture, before) if a.capture else None
    programs = program_cases(before, after)
    result = dict(status='SHOOT_STAGE11_RESULTS_ROUTE_QA_PASS', source_sha256=SOURCE, candidate_sha256=AFTER,
                  checker_sha256=sha(Path(__file__).read_bytes()),
                  lineage=lineage, actual_old_capture=observed, modeled_native_execution=programs,
                  patched_game_runtime=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()

