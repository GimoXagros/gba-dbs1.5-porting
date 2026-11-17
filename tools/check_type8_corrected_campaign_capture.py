"""Audit the finalized 75BD campaign route, allowed writes, and visual captures."""
import argparse
from collections import Counter
from io import BytesIO
import json
from pathlib import Path
import re
import struct
from zipfile import ZipFile

from PIL import Image, ImageChops

import verify_gba_shoot_entry_capture_v2 as state
from check_campaign_first_invalid_producer import PINS as CAMPAIGN_PINS
from check_type8_corrected_campaign import NEW as ROM, PIN as CORRECTED_PIN
from check_type8_event_provenance import PIN as PROVENANCE_PIN
from verify_gba_shoot_entry_capture import ROOT, SIZES, fields, ledger, long, sha, snapshot, word


RUN = 'bizhawk-type8-corrected-v81-20261117-a'
SUCCESS = 'campaign-eleven-stages-and-healthy-shoot-activation'
SHOOT_SUCCESS = 'healthy-native-shoot-activation'
WRAPPER = 'tools/bizhawk_probe_type8_corrected_campaign.lua'
HOST_PATH = 'build/run_type8_corrected_v81_20261117.py'
HOST = '18DDDFCFE48DD615B6F64A2B46755D270831428FE951B72A2859CCB747366864'
PIN_PATH = 'build/type8-corrected-reviewed-pins-20261117.json'
PIN_DIGEST = '0126D44047D3AD655DA84C34E3DF75CBC33360CAD5B3450CE335B57AAD0DCD2B'
EXE = 'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
OPENING = bytes((8, 1, 9, 6, 10))
ROUTES = tuple(bytes(row) for row in (
    (5, 0, 3, 2, 4), (0, 3, 2, 4, 5), (3, 2, 4, 5, 0), (2, 4, 5, 0, 3),
    (4, 5, 0, 3, 2), (5, 0, 3, 2, 4), (0, 3, 2, 4, 5), (2, 4, 5, 0, 3)))
CPUS = bytes((0, 1, 2, 5, 6, 4, 3, 15, 13, 14, 11))


def bind_launch(directory, host_exit):
    raw = (directory / 'launch.json').read_bytes()
    launch = json.loads(raw)
    assert launch['completed'] is True, 'wait for the finalized host manifest and original exit'
    assert host_exit == (0 if launch['outcome'] == SUCCESS else 1)
    assert all(launch[key] is True for key in ('loaded_rom_exact', 'scripts_unchanged'))
    assert all(launch[key] is False for key in ('visible', 'physical_background_input', 'supplied_save_used',
                                               'final_gba_cheat', 'host_stop_requested', 'host_deadline_reached'))
    assert launch['phase_kind'] == 'type8-corrected-assisted-eleven-encounter-to-healthy-shoot'
    assert launch['launcher_sha256'] == HOST == sha((ROOT / HOST_PATH).read_bytes())
    pin_raw = (ROOT / PIN_PATH).read_bytes()
    pins = CAMPAIGN_PINS | {WRAPPER: CORRECTED_PIN, 'tools/bizhawk_probe_type8_event_provenance.lua': PROVENANCE_PIN}
    assert launch['reviewed_pins_sha256'] == PIN_DIGEST == sha(pin_raw)
    assert launch['pins'] == json.loads(pin_raw) == pins
    assert {name: sha((ROOT / name).read_bytes()) for name in pins} == pins
    assert launch['exe_sha256'] == EXE == sha((ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe').read_bytes())
    inventory = {path.relative_to(directory).as_posix(): sha(path.read_bytes())
                 for path in sorted(directory.rglob('*')) if path.is_file() and path.name != 'launch.json'}
    assert inventory == launch['files']
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x1000000 and launch['rom_sha256'] == ROM == sha(rom)
    assert rom == (directory / 'probe.gba').read_bytes()
    assert rom == (ROOT / 'build/character-type8-tables-r2-20261117/component.gba').read_bytes()
    alias = 'W:/build/' + RUN
    assert launch['arguments'] == ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/' + WRAPPER,
                                   '--userdata=output:' + alias + ';frames:120000;start_frame:2970;combat_profile:approach-jump;probe_sha256:' + ROM
                                   + ';score_authorization:user-approved-development-score999;boss_authorization:user-approved-development-boss-once-per-stage',
                                   alias + '/probe.gba']
    assert launch['guest_writes'] == ['authorized ordinary active FIRST+0x66 WORD=999',
                                      'authorized active stage7 SECOND+0x64 WORD=1 once; actual attack required']
    config = json.loads((directory / 'config.json').read_bytes())
    assert all(config[key] is False for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM', 'SoundEnabled'))
    assert all(value == 'false' for value in re.findall(r'"AutoLoad"\s*:\s*(\w+)', json.dumps(config)))
    for index, entry in enumerate(config['PathEntries']['Paths']):
        assert entry['Path'] == f'{alias}/data/{index}'
    generated = {name: digest for name, digest in inventory.items() if name.startswith('data/')}
    assert set(generated) <= {'data/104/probe.SaveRAM'}
    return sha(raw), launch, rom, generated


def events(directory, rom, outcome):
    assert rom[0xD3FB10:0xD3FB15] == OPENING
    assert rom[0xD3FB18:0xD3FB40] == b''.join(ROUTES)
    assert rom[0xD3FB40:0xD3FB4B] == CPUS
    lines = (directory / 'campaign-complete-trace.txt').read_text('utf-8').splitlines()
    assert fields(lines[0])['ROM'] == ROM
    end = fields(lines[-1])
    assert end['outcome'] == outcome and end['assisted'] == 'true' and end['stage11_writes'] == 'disabled'
    tagged = [fields(line) for line in lines[1:-1]]
    assert all('event' in row or 'failure' in row for row in tagged)
    assert set(row.get('event') for row in tagged) <= {'producer', 'active-owner', 'HUD', None}
    producer, active, hud = ([row for row in tagged if row.get('event') == name]
                             for name in ('producer', 'active-owner', 'HUD'))
    assert producer, 'no first encounter evidence'
    rng = int(producer[0]['row'])
    assert 0 <= rng < len(ROUTES)
    route = OPENING + ROUTES[rng] + bytes((7,))
    assert sorted(route) == list(range(11))
    for row in [*producer, *active, *hud]:
        progress = int(row['progress'])
        assert 0 <= progress <= 10 and int(row['row']) == rng
        stage = route[progress]
        assert (int(row['stage']), int(row['cpu']), int(row['cpu_form'])) == (stage, CPUS[stage], int(CPUS[stage] == 0))
        assert row['difficulty'] == '2' and row['player'] == '0'
        assert int(row['relative']) == int(row['core']) - 1
    assert [int(row['progress']) for row in producer] == list(range(len(producer)))
    assert int(end['highest']) == len(producer) - 1
    assert [int(row['progress']) for row in active] == list(range(len(active)))
    assert [int(row['progress']) for row in hud] in ([], [9], [9, 10])
    assert [int(row['core']) for row in tagged] == sorted(int(row['core']) for row in tagged)
    for row in active + hud:
        assert int(producer[int(row['progress'])]['core']) <= int(row['core'])
    if outcome == SUCCESS:
        assert len(producer) == len(active) == 11 and len(hud) == 2
        assert end['stage'] == '11' and end['progress'] == '10'
    return rng, route, producer, active, hud, end


def capture_rows(directory, inventory):
    lines = (directory / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    captures = {}
    registers = {}
    for line in lines:
        if line.startswith('capture='):
            row = fields(line)
            if 'observed_core' in row:
                name = row['capture']
                assert name not in captures and int(row['export_core']) in range(int(row['observed_core']), int(row['observed_core']) + 2)
                assert row['memory'] == 'outer-frame-boundary'
                captures[name] = row
                registers[name] = {}
            else:
                match = re.fullmatch(r'capture=(\S+) reg (\S+)=([0-9A-F]+)', line)
                assert match and match[2] not in registers[match[1]]
                registers[match[1]][match[2]] = int(match[3], 16)
    expected = {f'{name}-{suffix}.bin' for name in captures for suffix in SIZES}
    expected |= {name + '.png' for name in captures}
    assert {name for name in inventory if re.match(r'^\d+-.*\.(bin|png)$', name)} == expected
    decoded = {}
    for name, row in captures.items():
        assert {'R' + str(i) for i in range(16)} | {'CPSR'} <= registers[name].keys()
        role = name.split('-', 1)[1]
        assert role not in decoded
        decoded[role] = dict(name=name, trace=row, regs=registers[name], state=snapshot(directory, name))
        with Image.open(directory / (name + '.png')) as image:
            assert image.size == (240, 160) and image.mode == 'RGB'
            decoded[role]['colors'] = len(image.getcolors(1 << 24))
    return decoded, lines


def raw(directory, capture, region):
    return (directory / f"{capture['name']}-{region}.bin").read_bytes()


def visual(directory, cap):
    iw, ew = (raw(directory, cap, name) for name in ('iwram', 'ewram'))
    display = raw(directory, cap, 'display')
    oam = raw(directory, cap, 'oam')
    camera = struct.unpack_from('<hh', iw, 0x451C)
    bg0 = struct.unpack_from('<hh', iw, 0x2348)
    valid = sum(word(oam, offset) & 0x300 != 0x200 for offset in range(0, len(oam), 8))
    result = dict(file=cap['name'] + '.png', clock=word(iw, 0x4500), camera=camera, bg0_camera=bg0,
                  enabled_oam=valid, rgb_colors=cap['colors'], dispcnt=f'{word(display, 0):04X}', actors={})
    for name, field in (('p1', 'first'), ('p2', 'second')):
        point = cap['state'][name]
        a = cap['state'][field] - 0x02000000
        world = struct.unpack_from('<hh', ew, a + 0x34)
        previous = struct.unpack_from('<hh', ew, a + 0x38)
        on_screen = struct.unpack_from('<hh', ew, a + 0xAC)
        projection = [candidate for candidate, location in (('current', world), ('previous', previous))
                      if tuple((value >> 4) - origin for value, origin in zip(location, camera)) == on_screen]
        result['actors'][name] = dict(fighter=point['fighter'], hp=point['hp'], world=world, previous=previous,
                                      presentation=on_screen, projection=projection,
                                      center_within_view=0 <= on_screen[0] < 240 and 0 <= on_screen[1] < 160)
    return result


def layer_overlap(directory, cap):
    iw, vram, palettes, oam, display = (
        raw(directory, cap, name) for name in ('iwram', 'vram', 'palette', 'oam', 'display'))
    assert word(display, 0) & 0x1100 == 0x1100 and word(display, 8) == 0x1F02
    sprite = {}
    priorities = set()
    for slot in range(12):
        a0, a1, a2 = struct.unpack_from('<3H', oam, slot * 8)
        assert a0 & 0xFF00 == 0 and a1 & 0xE000 == 0 and a2 >> 12 == 0
        priorities.add(a2 >> 10 & 3)
        x, y = a1 & 511, a0 & 255
        for sy in range(8):
            for sx in range(8):
                pixel = 7 - sx if a1 & 0x1000 else sx
                packed = vram[0x10000 + (a2 & 1023) * 32 + sy * 4 + pixel // 2]
                index = packed >> (4 * (pixel % 2)) & 15
                if index:
                    sprite[x + sx, y + sy] = word(palettes, 0x200 + 2 * index)
    assert len(priorities) == 1

    def rgb(color):
        channels = (color >> shift & 31 for shift in (0, 5, 10))
        return tuple(value << 3 | value >> 2 for value in channels)

    def bg0_visible(x, y):
        x = (x + iw[0x12BA]) & 255
        y = (y + iw[0x12BB]) & 255
        tile = word(vram, 0xF800 + 2 * (y // 8 * 32 + x // 8))
        sx, sy = x % 8, y % 8
        if tile & 0x0400:
            sx = 7 - sx
        if tile & 0x0800:
            sy = 7 - sy
        packed = vram[(tile & 1023) * 32 + sy * 4 + sx // 2]
        return bool(packed >> (4 * (sx % 2)) & 15)

    with Image.open(directory / (cap['name'] + '.png')) as image:
        exact = sum(image.getpixel(point) == rgb(color) for point, color in sprite.items())
    return dict(obj_priority=next(iter(priorities)), bg0_priority=word(display, 8) & 3,
                opaque_obj_pixels=len(sprite), exact_obj_pixels_in_png=exact,
                opaque_bg0_pixels_over_obj=sum(bg0_visible(*point) for point in sprite))


def assert_active(cap, expected):
    s = cap['state']
    assert s['mode'] == 7 and s['stage'] == int(expected['stage']) and s['difficulty'] == 2
    assert s['game_kind'] == (2 if s['stage'] == 7 else 0)
    p1, p2 = s['p1'], s['p2']
    assert s['first'] != s['second'] and p1['active'] and p2['active']
    assert (p1['kind'], p1['index'], p1['fighter']) == (0, 0, 0)
    assert (p2['kind'], p2['index'], p2['fighter']) == ((3 if s['stage'] == 7 else 1), 1, int(expected['cpu']))
    assert p1['self'] == p2['opponent'] == s['first'] and p2['self'] == p1['opponent'] == s['second']
    assert all(0 < actor['hp'] < 0x8000 for actor in (p1, p2))
    assert s['services']['input']['active'] and s['services']['input']['callback'] == 0x08374FF4
    assert s['services']['battle']['active'] and s['services']['battle']['callback'] == 0x083735BC


def audit_captures(directory, rom, captures, producer, active, hud):
    for row in producer:
        cap = captures[f"campaign-producer-{int(row['progress']):02d}"]
        assert cap['trace']['observed_core'] == row['core'] and cap['trace']['registers'] == 'before-instruction'
        assert (cap['regs']['R4'], cap['regs']['R15']) == (0x03002310, 0x0808B710)
        iw = raw(directory, cap, 'iwram')
        assert (iw[0x231E], iw[0x231C], iw[0x231D], iw[0x232E]) == tuple(int(row[key]) for key in ('stage', 'cpu', 'cpu_form', 'progress'))
    visual_samples = {}
    for row in active:
        progress = int(row['progress'])
        cap = captures[f'campaign-active-{progress:02d}']
        assert cap['trace']['observed_core'] == cap['trace']['export_core'] == row['core']
        assert_active(cap, row)
        v = visual(directory, cap)
        assert v['clock'] == int(row['clock'])
        assert v['rgb_colors'] > 1 and v['enabled_oam'] > 0
        if progress in (0, 1):
            expected = ((0, 116), ((64, 68), (392, 76)), 12) if progress == 0 else ((152, 44), ((112, 68), (32, 68)), 26)
            assert v['camera'] == v['bg0_camera'] == expected[0] and v['enabled_oam'] == expected[2]
            assert tuple(actor['presentation'] for actor in v['actors'].values()) == expected[1]
            assert all(actor['projection'] == ['current', 'previous'] for actor in v['actors'].values())
        if progress in (0, 2):
            overdraw = layer_overlap(directory, cap)
            known = (2, 503, 0) if progress == 0 else (3, 0, 503)
            assert tuple(overdraw[key] for key in ('obj_priority', 'exact_obj_pixels_in_png', 'opaque_bg0_pixels_over_obj')) == known
            assert overdraw['opaque_obj_pixels'] == 503
            v['p1_sprite_pixels'] = overdraw
        visual_samples[str(progress)] = v
    hud_samples = {}
    for row in hud:
        progress = int(row['progress'])
        cap = captures[f'campaign-HUD-{progress:02d}']
        assert cap['trace']['observed_core'] == row['core'] and cap['trace']['registers'] == 'before-instruction'
        assert (cap['regs']['R5'], cap['regs']['R15']) == (0x0600E820, 0x080B6058)
        vram = raw(directory, cap, 'vram')
        at = 0xE80E if progress == 9 else 0xE800
        expected = (0x2215, 0x2214, *([0x2201] * 7)) if progress == 9 else struct.unpack_from('<16H', rom, 0xB5FEA)
        actual = struct.unpack_from(f'<{len(expected)}H', vram, at)
        hud_samples[str(progress)] = dict(file=cap['name'] + '.png', observed_core=int(row['core']),
                                          export_core=int(cap['trace']['export_core']),
                                          tilemap_address=f'{0x06000000 + at:08X}',
                                          tilemap_words=[f'{value:04X}' for value in actual],
                                          expected_words=[f'{value:04X}' for value in expected],
                                          outer_frame_exact=actual == expected,
                                          runtime_hook_exact=True)
    return visual_samples, hud_samples


def checkpoint(directory, rom, cap, name):
    path = directory / f'{name}.State'
    metadata = fields((directory / f'{name}.txt').read_text('utf-8').strip())
    regions = {region: raw(directory, cap, region) for region in state.OFFSETS}
    saved = state.parse_checkpoint(path.read_bytes(), metadata, regions, rom)
    assert saved['frame'] == int(cap['trace']['export_core'])
    with ZipFile(path) as archive:
        data = json.loads(archive.read('UserData.txt'))['o']
        assert data['output'] == 'W:/build/' + RUN and data['probe_sha256'] == ROM
        with Image.open(BytesIO(archive.read('Framebuffer.bmp'))) as bmp, Image.open(directory / f"{cap['name']}.png") as png:
            assert bmp.size == png.size == (240, 160)
            assert ImageChops.difference(bmp.convert('RGB'), png.convert('RGB')).getbbox() is None
    return saved


def audit_handoff(directory, rom, captures):
    names = ('boss-hit-pre', 'boss-hit-post', 'healthy-root5', 'scene-saved-health',
             'saved-health-restore', 'activation-tail', 'healthy-activation')
    steps = [captures[label] for label in names]
    assert [int(cap['trace']['observed_core']) for cap in steps] == sorted(int(cap['trace']['observed_core']) for cap in steps)
    pre, post, root, scene, restore, activation, healthy = steps
    p, q = (int(pre['trace'][name], 16) for name in ('actual_attacker', 'victim'))
    assert pre['trace']['before'] == '1' and pre['trace']['FIRST'] == f'{p:08X}' and pre['trace']['SECOND'] == f'{q:08X}'
    for cap, pc in ((pre, 0x0836E5E8), (post, 0x0836E5EC)):
        assert (cap['regs']['R4'], cap['regs']['R5'], cap['regs']['R15']) == (p, q, pc)
    assert int(pre['trace']['computed'], 16) == pre['regs']['R8'] & 0xFFFF
    fatal = pre['regs']['R8'] & 0xFFFF
    assert fatal == 0 or fatal >= 0x8000
    hp = int(root['trace']['P1HP'])
    assert hp > 0 and int(scene['trace']['saved']) == int(restore['trace']['restored']) == healthy['state']['p1']['hp'] == hp
    assert scene['trace']['owner'] == restore['trace']['owner']
    assert healthy['state']['stage'] == 11 and healthy['state']['mode'] == 7 and healthy['state']['game_kind'] == 2
    assert healthy['state']['flags'] & 4 and healthy['state']['p1']['active']
    saved = checkpoint(directory, rom, healthy, 'healthy-activation')
    return dict(player_hp=hp, checkpoint=saved, ordered={label: int(cap['trace']['observed_core']) for label, cap in zip(names, steps)})


def audit_terminal_dump(directory, rom, ordered_input, end, outcome):
    if outcome != 'bounded-no-activation':
        return None
    at = next(index for index, line in enumerate(ordered_input) if line.startswith('capture=bounded-no-hit '))
    capture = fields(ordered_input[at])
    assert capture['frame'] == end['core'] and capture['timing'] == 'frame-boundary'
    assert (directory / 'done.txt').read_text('utf-8').strip() == 'bounded-no-hit'
    screenshot = fields(next(line for line in ordered_input if line.startswith('screenshot_timing=')))
    assert screenshot['capture_frame'] == screenshot['frame'] == end['core']
    regs = dict(line[4:].split('=', 1) for line in ordered_input[at:] if line.startswith('reg '))
    assert {'R15', 'CPSR'} <= regs.keys()
    regions = {key: (directory / f'{key}.bin').read_bytes() for key in state.OFFSETS}
    assert {name: len(data) for name, data in regions.items()} == {name: size for name, (_, size) in state.OFFSETS.items()}
    iw, ew, oam = (regions[region] for region in ('iwram', 'ewram', 'oam'))
    mode = word(iw, 0x2310)
    clock = word(iw, 0x4500)
    assert end['mode'] == str(mode) and end['clock'] == str(clock) and end['stage'] == str(iw[0x231E])
    assert end['row'] == str(iw[0x232F]) and end['progress'] == str(iw[0x232E])
    pairs = {}
    for label, address in (('p1', 0x489C), ('cpu', 0x48A0)):
        actor = struct.unpack_from('<I', iw, address)[0]
        offset = actor - 0x02000000
        assert 0 <= offset < len(ew) - 0x118
        pairs[label] = dict(address=f'{actor:08X}', fighter=ew[offset+0x11],
                            health=word(ew, offset+0x64), score=word(ew, offset+0x66),
                            world=struct.unpack_from('<hh', ew, offset+0x34),
                            previous_world=struct.unpack_from('<hh', ew, offset+0x38),
                            presentation=struct.unpack_from('<hh', ew, offset+0xAC),
                            held=word(ew, offset+0x2C), edge=word(ew, offset+0x2E),
                            callback=f'{struct.unpack_from("<I", ew, offset)[0]:08X}')
    services = {}
    for label, address in (('input', 0x4510), ('battle', 0x4514)):
        task = struct.unpack_from('<I', iw, address)[0]
        offset = task - 0x02000000
        assert 0 <= offset < len(ew) - 0x18
        services[label] = dict(address=f'{task:08X}', active=bool(word(ew, offset+0x10) & 2),
                               callback=f'{struct.unpack_from("<I", ew, offset)[0]:08X}')
    with Image.open(directory / 'screen.png') as screen:
        assert screen.mode == 'RGB' and screen.size == (240, 160)
        colors = len(screen.getcolors(1 << 24))
    exception = None
    if int(regs['CPSR'], 16) & 0x1F == 0x1B:
        words = struct.unpack_from('<8I', rom, 0xC65D4)
        assert words == (0xE59F8050, 0xE1D820B0, 0xE3120A01, 0x1A0000A9,
                         0xE20250FF, 0xE28F8004, 0xE7989105, 0xE12FFF19)
        owner = long(rom, 0xC662C)
        assert owner == 0x03003D50
        flags = word(iw, owner - 0x03000000)
        index = flags & 0xFF
        assert flags == int(regs['R2'], 16) == 0xF and index == int(regs['R5'], 16)
        table = int(regs['R8'], 16)
        assert table == 0x080C65F4
        selected_at = table + 4 * index
        target = long(rom, selected_at - 0x08000000)
        assert target == int(regs['R9'], 16) == 0xE3A00000
        assert int(regs['R14'], 16) == target + 4
        assert int(regs['SPSR'], 16) & 0x1F == 0x10
        assert regs['R15'] == '00000394'
        exception = dict(mode='ARM undefined instruction', native_dispatch='080C65D4..080C65F0',
                         selector_owner=f'{owner:08X}', selector_flags=f'{flags:04X}', index=index,
                         table_base=f'{table:08X}', slot_address=f'{selected_at:08X}',
                         target_word=f'{target:08X}', fault_lr=regs['R14'])
    return dict(clock=clock, mode=mode, stage=iw[0x231E], progress=iw[0x232E],
                exception=exception,
                pause=f'{iw[0x4529]:02X}', battle_exit_flags=f'{word(iw, 0x4508):04X}',
                actors=pairs, services=services, camera=struct.unpack_from('<hh', iw, 0x451C),
                bg0_camera=struct.unpack_from('<hh', iw, 0x2348),
                enabled_oam=sum(word(oam, offset) & 0x300 != 0x200 for offset in range(0, len(oam), 8)),
                input_register_shadow=[f'{word(iw, offset):04X}' for offset in (0x1302, 0x1306)],
                screenshot_file='screen.png', screenshot_colors=colors, registers=regs)


def audit(directory, host_exit):
    launch_sha, launch, rom, generated = bind_launch(directory, host_exit)
    outcome = launch['outcome']
    assert (directory / 'campaign-complete-done.txt').read_text('utf-8').strip() == outcome
    assert (directory / 'shoot-entry-done.txt').read_text('utf-8').strip() == (SHOOT_SUCCESS if outcome == SUCCESS else outcome)
    rng, route, producer, active, hud, end = events(directory, rom, outcome)
    captures, trace = capture_rows(directory, launch['files'])
    visual_samples, hud_samples = audit_captures(directory, rom, captures, producer, active, hud)
    summary = fields(trace[-1])
    assert summary['outcome'] == (SHOOT_SUCCESS if outcome == SUCCESS else outcome)
    assert summary['final_core'] == end['core'] and int(end['relative']) <= 120000
    ledger_path = directory / 'shoot-entry-writes.txt'
    writes, scores, bosses = ledger(ledger_path.read_text('utf-8').splitlines() if ledger_path.exists() else [])
    assert int(summary['score_writes']) == scores and int(summary['boss_writes']) == bosses
    assert summary['stage11_writes'] == '0'
    active_stage = {row['stage']: int(row['core']) for row in active}
    for row in writes:
        assert row['stage'] in active_stage and int(row['core']) >= active_stage[row['stage']] - 1
    by_stage = Counter(int(row['stage']) for row in writes if row['kind'] == 'score')
    if outcome == SUCCESS:
        assert set(by_stage) == set(route) - {7} and bosses == 1
    ordered_input = (directory / 'trace.txt').read_text('utf-8').splitlines()
    input_rows = [fields(line) for line in ordered_input if line.startswith('input relative=')]
    assert [int(row['core']) for row in input_rows] == sorted({int(row['core']) for row in input_rows})
    assert all(int(row['relative']) == int(row['core']) - 1 for row in input_rows)
    terminal = audit_terminal_dump(directory, rom, ordered_input, end, outcome)
    handoff = audit_handoff(directory, rom, captures) if outcome == SUCCESS else None
    boss = checkpoint(directory, rom, captures['stage7-checkpoint'], 'stage7-hp1') if 'stage7-checkpoint' in captures else None
    failure = (directory / 'shoot-entry-first-failure.txt').read_text('utf-8').splitlines()[0] if outcome.startswith('failure:') else None
    assert not failure or fields(failure)['outcome'] == outcome
    failure_state = 'failure-observed.State' in launch['files']
    assert failure_state == ('failure_checkpoint_saved=true' in trace)
    stop = checkpoint(directory, rom, captures[outcome.removeprefix('failure:')], 'failure-observed') if failure_state else None
    assert outcome == SUCCESS or 'healthy-activation.State' not in launch['files']
    ring = [fields(line) for line in trace if line.startswith('seq=')]
    assert len(ring) <= 256
    assert [int(row['seq']) for row in ring] == list(range(int(ring[0]['seq']), int(ring[-1]['seq']) + 1))
    assert [int(row['core']) for row in ring] == sorted(int(row['core']) for row in ring)
    for change in ({**active[0], 'cpu': '12'}, {**active[0], 'stage': '1'}):
        try:
            assert_active(captures['campaign-active-00'], change)
        except AssertionError:
            pass
        else:
            raise AssertionError('wrong stage or CPU accepted')
    return dict(status='CORRECTED_CAMPAIGN_CAPTURE_QA_PASS', outcome=outcome, eleven_stage_completion=outcome == SUCCESS,
                original_host_exit=host_exit, launch_sha256=launch_sha, files_verified=len(launch['files']),
                rom_sha256=ROM, supplied_save_used=False, isolated_generated_saves=generated,
                rng_row=rng, source_route=list(route), actual_producers=producer, actual_active_owners=active,
                actual_hud=hud_samples, visual_samples=visual_samples, final_core=int(end['core']),
                final_campaign_state=end, final_native_journal_core=int(ring[-1]['core']),
                native_journal_tail=ring[-8:], terminal_frame_dump=terminal,
                score_writes=scores, score_writes_by_stage=by_stage, boss_writes=bosses, ledger=writes,
                stage11_writes=0, first_failure=failure, failure_checkpoint=stop,
                stage7_checkpoint=boss, healthy_handoff=handoff, input_trace_sha256=launch['files']['trace.txt'],
                capture_count=len(captures), input_transitions=len(input_rows), auditor_ran_emulator=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--host-exit', type=int, required=True)
    args = parser.parse_args()
    report = audit(ROOT / 'build' / RUN, args.host_exit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {report['outcome']} {sha(args.output.read_bytes())}")
