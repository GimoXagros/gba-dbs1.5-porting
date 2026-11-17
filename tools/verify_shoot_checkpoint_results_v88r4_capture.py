"""Audit the complete E212 Shoot-to-title replay on its finalized original host."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import unpack_from

import check_type8_corrected_campaign_capture as campaign
from verify_gba_shoot_entry_capture import fields, long, sha, word
import verify_shoot_checkpoint_results_v88_capture as prior
from verify_shoot_static_companion_clear import ROOT, need


RUN = 'bizhawk-shoot-checkpoint-results-v88r4-20261117-a'
HOST = '66DCE81003CBACF61A6FFE224387C6431FB37A29DB525F5D323C2EE9FE84F994'
PINSET = '6FAFA233B0ED5B18D4D633E66325B3F0DC452833CB46B2C09D5C70CEC005577A'
PROBE = 'tools/bizhawk_probe_gba_shoot_checkpoint_results_v88r4.lua'
PROBE_HASH = '6533778C81A901F173DEC973EAD1365A9511AEBB1E76AD3144A663F25388B311'
ROM = prior.preflight.NEW
SUCCESS = prior.SUCCESS
PREFIX = prior.MATCH_SEQUENCE[:19]
TAIL = [('mode13-normal-request', 13, 0x080CA3A0), ('ending-entry', 11, 0x080BF1D4),
        ('ending-ready', 11, 0x080C0054), ('ending-card-ready', 11, 0x080C101C),
        ('ending-card-request', 11, 0x080C10D0), ('mode20-entry', 20, 0x0804044C),
        ('mode20-art', 20, 0x08040720), ('mode20-return-request', 20, 0x0804060C),
        ('title-ready', 3, 0x08090C80)]
MODE_WRITES = [(7, 8), (8, 12), (12, 13), (13, 11), (11, 20), (20, 3)]


def bind(directory):
    raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(raw)
    flags = ('visible', 'physical_background_input', 'supplied_save_used', 'host_stop_requested', 'host_deadline_reached')
    conditions = ('completed', 'loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged',
                  'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal')
    need(all(launch[x] is False for x in flags) and all(launch[x] is True for x in conditions)
         and launch['outcome'] == SUCCESS, 'Finalized successful original host')
    need(launch['files'] == {p.relative_to(directory).as_posix(): sha(p.read_bytes())
                            for p in directory.rglob('*') if p.is_file() and p.name != 'launch.json'}, 'All finalized files')
    pins = prior.assert_file_id(ROOT / 'build/shoot-checkpoint-results-v88r4-pins-20261117.json', PINSET)
    need(launch['launcher_sha256'] == HOST == sha((ROOT / 'build/run_shoot_checkpoint_results_v88r4_20261117.py').read_bytes())
         and launch['reviewed_pins_sha256'] == PINSET, 'Reviewed host and pins')
    launch_pins = json.loads(pins)
    need(launch_pins == launch['pins'] and len(launch_pins) == 6 and launch_pins[PROBE] == PROBE_HASH, 'Exact six-callsite dependencies')
    for relative, digest in launch_pins.items():
        prior.assert_file_id(ROOT / relative, digest)
    alias = 'W:/build/' + directory.name
    args = ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + PROBE,
            '--userdata=output:' + alias + ';checkpoint_dir:' + alias + '/checkpoint;probe_sha256:' + ROM
            + ';stage11_boss_authorization:user-approved-development-stage11-boss-hp1-once', alias + '/probe.gba']
    need(launch['arguments'] == args and launch['guest_writes'] == ['stage11 live boss HP WORD1 once at a qualified ordinary B input'],
         'Exact restored private replay and approved guest write')
    cfg = json.loads((directory / 'config.json').read_bytes())
    need(all(cfg[k] is False for k in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
         and all(ent['Path'] == f'{alias}/data/{i}' for i, ent in enumerate(cfg['PathEntries']['Paths'])),
         'Native private data only')
    rom = (directory / 'loaded-rom.bin').read_bytes()
    need(launch['rom_sha256'] == sha(rom) == ROM and len(rom) == 0x1000000
         and rom == (ROOT / 'build/repro-v88-20261117-a/current-candidate.gba').read_bytes()
         and rom == (directory / 'probe.gba').read_bytes(), 'Exact current E212 image')
    for file in ('shoot-checkpoint-aim-done.txt', 'shoot-entry-done.txt'):
        need((directory / file).read_text().strip() == SUCCESS, 'Native evaluator completion sentinels')
    forbidden = ('shoot-checkpoint-aim-error.txt', 'shoot-entry-first-failure.txt', 'failure-observed.State',
                 'shoot-entry-writes.txt', 'stop.request')
    need(not set(forbidden) & launch['files'].keys(), 'No hidden extra writes, faults or host stop')
    preflight = json.loads(prior.assert_file_id(ROOT / 'build/shoot-checkpoint-results-v88-preflight-independent-20261117/report.json',
                                               prior.PREFLIGHT))
    return sha(raw), launch, rom, prior.checkpoint_check(directory, launch, rom, preflight)


def audit_route(directory, launch):
    actual = (directory / 'wholeplay-trace.txt').read_text().splitlines()
    examined = [fields(row) for row in actual]
    need([(r['event'], int(r['mode']), int(r['pc'], 16)) for r in examined] == PREFIX + TAIL,
         'Actual hit, terminal, credits, card, mode20 and title code chain')
    entries = {r['event']: r for r in examined}
    need([int(r['core']) for r in examined] == sorted(int(r['core']) for r in examined), 'Physical route chronology')
    previous = ROOT / 'build/bizhawk-shoot-checkpoint-results-v88r3-20261117-a'
    original = (previous / 'wholeplay-trace.txt').read_text().splitlines()
    need(actual[:len(original)] == original, 'Prior observations identical up to mode20')
    for replay_file in ('wholeplay-stage11-writes.txt', 'shoot-checkpoint-aim-decisions.txt'):
        need((directory / replay_file).read_bytes() == (previous / replay_file).read_bytes(), 'One retained ordinary-input/HP journal')
    ledger = (directory / 'wholeplay-stage11-writes.txt').read_text().splitlines()
    need(len(ledger) == 1 and fields(ledger[0])['address'] == '0201188C' and fields(ledger[0])['after'] == '1'
         and fields(ledger[0])['verified'] == 'true', 'Exactly one verified user-authorized 2-byte write')
    physical = [fields(row) for row in (directory / 'wholeplay-mode-writes.txt').read_text().splitlines()]
    need([(int(r['old']), int(r['new'])) for r in physical] == MODE_WRITES
         and all((r['pc'], r['lr'], r['address']) == ('08015B64', '08015AE4', '03002310') for r in physical),
         'All six actual dispatch mode changes')
    caps, _ = campaign.capture_rows(directory, launch['files'])
    hit = caps['wholeplay-hit-post']
    need(hit['state']['p2']['hp'] == 0 and hit['regs']['R0'] == 1 and hit['regs']['R4'] == 0x02011710
         and hit['regs']['R5'] == 0x02011828, 'Real lethal hit by the retained actor')
    need(entries['mode13-normal-request']['cursor'] == '22' and entries['mode13-normal-request']['complete'] == '003F'
         and entries['mode13-normal-request']['request'] == '1,0,0', 'Actual natural credits readiness and native request')
    card = entries['ending-card-ready']
    need((card['owner'], card['flags'], card['timer']) == ('02010348', '0001', '75')
         and entries['ending-card-request']['request'] == entries['mode20-return-request']['request'] == '1,0,0',
         'Final card and native mode20 return both issue ordinary requests')
    art = caps['wholeplay-mode20-art']
    iw, ew = (campaign.raw(directory, art, region) for region in ('iwram', 'ewram'))
    owner = int(entries['mode20-art']['owner'], 16)
    off = owner - 0x02000000
    need((long(ew, off), long(ew, off + 4), word(iw, 0x4738) & 2, word(iw, 0x2310)) ==
         (0x0804074C, 0xFFFFF100, 2, 20) and word(ew, off + 0x10) & 2, 'Live signed art task and completed native assets')
    title = caps['wholeplay-title-ready']
    need(title['colors'] > 1 and title['state']['mode'] == 3, 'Observed nonblank actual mode3 title')
    return dict(events=examined, mode_writes=physical, title_frame=title['name'] + '.png',
                title_frame_export_core=int(title['trace']['export_core']), title_frame_rgb_colors=title['colors'],
                authorized_guest_write=fields(ledger[0]), prior_r3_route_prefix_exact=True)


def mode20_source_art(directory, launch, rom, original):
    need(sha(original) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
         'Exact source mode20 assets')
    need(long(rom, 0x4072C) == 0x086FBDA8 and long(rom, 0x40728) == 0x0600F800
         and long(rom, 0x4073C) == 0x086FC198, 'Actual source map and palette DMA aliases')
    tiles = rom[0x712680:0x714680] + rom[0x717F40:0x719240]
    colors = unpack_from('<96H', original, 0x4AB6B0)
    def gba_color(old):
        r, g, b = ((old >> shift) & 15 for shift in (8, 4, 0))
        return (2 * r + bool(r)) | ((2 * g + bool(g)) << 5) | ((2 * b + bool(b)) << 10)
    projected_colors = tuple(gba_color(word) for word in colors)
    source_map = unpack_from('<504H', original, 0x4A80C0)
    map_words = tuple((w & 511) | ((w & 0x2000) >> 4) | ((w & 0xC000) >> 4)
                      | ((w & 0x1E00) << 3) for w in source_map)
    for tile in range(408):
        for y in range(8):
            original_at = 0x4A84B0 + tile * 32 + y * 4
            for x in range(8):
                bit = 1 << (7 - x)
                source_index = sum(1 << plane for plane in range(4) if original[original_at + plane] & bit)
                actual_index = tiles[tile * 32 + y * 4 + x // 2] >> (4 * (x % 2)) & 15
                need(source_index == actual_index, 'Exact source planar pixel to installed native tile')
    samples = []
    for label in ('wholeplay-mode20-art', 'wholeplay-mode20-return-request'):
        path, = directory.glob(f'*-{label}-vram.bin')
        name = path.name.removesuffix('-vram.bin')
        def read(region):
            return prior.assert_file_id(directory / f'{name}-{region}.bin', launch['files'][f'{name}-{region}.bin'])
        vram, palette, display = (read(x) for x in ('vram', 'palette', 'display'))
        need(vram[0x3200:0x6500] == tiles, 'All 408 mode20 tiles actually loaded and retained')
        need(tuple(word(vram, 0xF800 + row * 64 + col * 2) for row in range(18) for col in range(28)) == map_words,
             'All 504 actual BG0 map cells equal the source')
        need(palette[0x20:0x120] == rom[0x6FC198:0x6FC298]
             and unpack_from('<96H', palette, 0x20) == projected_colors, 'Actual source palette words and native padding')
        need(word(display, 0) & 0x180 == 0x100 and word(display, 8) == 0x1F02, 'Hardware BG0 selects correct screen/map bank')
        samples.append(dict(frame=name + '.png', full_source_indices=408 * 64, source_map_cells=504, source_palette_words=96,
                            preserved_native_palette_words=32, dispcnt=word(display, 0), bg0cnt=word(display, 8)))
    return dict(exact_live_source_assets=samples, framebuffer_full_raster_equality_claimed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host-exit', type=int, choices=(0,), required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    need(not a.report.exists(), 'Fresh independent report')
    directory = ROOT / 'build' / RUN
    digest, launch, rom, checkpoint = bind(directory)
    result = dict(status='ACTUAL_E212_CHECKPOINT_SHOOT_TO_TITLE_PASS', launch_sha256=digest, files_verified=len(launch['files']),
                  checker_sha256=sha(Path(__file__).read_bytes()), original_host_exit=a.host_exit, restored=checkpoint,
                  ending=audit_route(directory, launch), mode20_graphics=mode20_source_art(directory, launch, rom, a.source.read_bytes()),
                  independent_auditor_started_emulator=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
