#!/usr/bin/env python3
"""Read-only audit of completed ordinary-input result captures; never opens saves."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import Image
from verify_result_language import native, PINS

SCRIPT = '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
EXE = 'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
RESULT = (0x080B8210, 0x08651AE0, 0x086DA640, 0x087DFC20)
TITLE = (0x0808FD08, 0x0863A800, 0x0863D000, 0x0863E000)
SIZES = dict(iwram=0x8000, ewram=0x40000, vram=0x18000, palette=0x400, oam=0x400, display=0x60)
INIT = {0x808998C, 0x80899F0, 0x8089C00, 0x8089C64, 0x8089DA0, 0x8089F38}
DRAW = {0x808B0AC, 0x808B170, 0x808B19C}


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state'), 'save/state path forbidden')
    return path.read_bytes()


def h(data, at):
    return struct.unpack_from('<H', data, at)[0]


def u(data, at):
    return struct.unpack_from('<I', data, at)[0]


def fields(line):
    return dict(re.findall(r'(\w+)=([^ ]+)', line))


def checksum(ir, tag):
    need(ir[0x112F] == tag and sum(ir[0x1120:0x11E0]) == u(ir, 0x11E0), 'committed tag and full native checksum')


def task(er, priority):
    found = [a for a in range(0x10000, 0x10000 + 52 * 0x118, 0x118)
             if h(er, a + 0x10) & 2 and u(er, a + 4) == priority]
    need(len(found) == 1, 'unique active native task')
    return found[0]


def renderer(ir, retail):
    need(ir[0x200:0x380] == retail[0x12C58:0x12DD8], 'entire native copied renderer')


def oam_check(oam):
    need(len(oam) == 1024, '128 complete interleaved hardware OAM records')
    active = []
    for i in range(128):
        a, b, c = struct.unpack_from('<3H', oam, i * 8)
        if a & 0x300 == 0x200:
            continue
        need(a & 0xFF00 == 0 and b & 0xCE00 == 0, 'native regular 8x8 4bpp OBJ geometry')
        need(c & 1023 == len(active), 'native sequential OBJ tile allocation')
        active.append((a, b, c))
    need(len(active) <= 127, 'native OAM capacity without overflow')
    return active


def label_hardware(snap, obj, resource, rom, screenshot):
    """Require the full ordered layout, tile bytes, flips, palette and screenshot pixels."""
    ir, er, vr, pal, oa = (snap[k] for k in ('iwram', 'ewram', 'vram', 'palette', 'oam'))
    at = obj - 0x02000000
    need(0 <= at <= len(er) - 0x50, 'actual result presentation address')
    need(tuple(u(er, at + off) for off in (0x44, 0x48, 0x4C)) ==
         (0x080B9004, resource['p0'] + 0x08000000, 0x080B9144), 'captured live label P1/P0/P2')
    layout, event = h(er, at + 0x18), h(er, at + 0xE)
    need(event in (0, 1, 3) and layout in (0, 1, 14), 'actual result label event/layout')
    parts = resource['layouts'][layout]
    x, y = struct.unpack_from('<hh', er, at)
    flags, bank = h(er, at + 8), h(er, at + 0x10)
    need(flags & 0xC000 == 0, 'captured label has no whole-object flip')
    active = oam_check(oa)
    need(h(ir, 0x12D6) == len(active), 'stable label hardware/staging OAM count')
    need(vr[0x10000:0x10000 + len(active) * 32] == er[:len(active) * 32], 'complete active staging reached OBJ VRAM')
    matches = []
    for start in range(len(active) - len(parts) + 1):
        good = True
        for j, (f, top, left) in enumerate(parts):
            a, b, c = active[start + j]
            expected_bank = bank + ((f >> 9) & 7)
            tile = resource['atlas'][(f & 255) * 32:((f & 255) + 1) * 32]
            good &= (a == (y + top + 8) & 255 and b == ((x + left + 8) & 511) | ((f & 0xC000) >> 2)
                     and c >> 12 == expected_bank and c & 0xC00 == (0x800 if flags & 0x2000 else 0xC00)
                     and vr[0x10000 + (c & 1023) * 32:0x10000 + ((c & 1023) + 1) * 32] == tile)
        if good:
            matches.append(start)
    need(len(matches) == 1, 'unique full native label layout in actual hardware OAM/VRAM')
    palette_bank = active[matches[0]][2] >> 12
    live = pal[0x200 + palette_bank * 32:0x220 + palette_bank * 32]
    side_override = bool(h(ir, 0x4738) & 0x20)
    expected = rom[0x89374:0x89394] if side_override else rom[0xB914A:0xB916A]
    need(live == expected, 'all16 live label palette words match retained native winner-side producer')
    image = Image.open(screenshot).convert('RGB')
    need(image.size == (240, 160), 'native screenshot dimensions')
    pixels = resource['frames'][layout]
    for (px, py), index in pixels.items():
        sx, sy = x + px + 8, y + py + 8
        need(0 <= sx < 240 and 0 <= sy < 160, 'entire label on physical screen')
        color = h(live, index * 2)
        rgb = tuple((((color >> shift) & 31) * 255 + 15) // 31 for shift in (0, 5, 10))
        need(image.getpixel((sx, sy)) == rgb, 'every actual screenshot label pixel equals native resource and live palette')
    return dict(event=event, layout=layout, oam_start=matches[0], parts=len(parts), pixels=len(pixels),
                palette_bank=palette_bank, winner_side_override=side_override, palette_sha256=sha(live),
                full_screenshot_pixel_match=True, active_oam=len(active),
                boundary_dispcnt=f'{h(snap["display"], 0):04X}')


def selfchecks(retail):
    rejected = []
    ir = bytearray(0x8000); ir[0x112F] = 0xA2
    struct.pack_into('<I', ir, 0x11E0, sum(ir[0x1120:0x11E0]))
    checksum(ir, 0xA2)
    ir[0x1120] ^= 1
    bad_oam = bytearray(struct.pack('<4H', 0x200, 0, 0, 0) * 128)
    struct.pack_into('<H', bad_oam, 0, 0x4000)
    good_ir = bytearray(0x8000); good_ir[0x200:0x380] = retail[0x12C58:0x12DD8]
    renderer(good_ir, retail); good_ir[0x201] ^= 1
    for name, fn in [('checksum', lambda: checksum(ir, 0xA2)), ('OAM shape', lambda: oam_check(bad_oam)),
                     ('copied renderer', lambda: renderer(good_ir, retail))]:
        try:
            fn()
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('negative selfcheck accepted: ' + name)
    return rejected


def audit(directory, rom, retail, observer):
    result_predecessor = rom
    if sha(result_predecessor) == '72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC':
        restored = bytearray(result_predecessor)
        need(restored[0x5C0A00:0x5C0A04] == bytes.fromhex('BE1600EA'), 'reviewed controller bridge')
        restored[0x5C0A00:0x5C0A04] = bytes.fromhex('1EFF2FE1')
        result_predecessor = bytes(restored)
        need(sha(result_predecessor) == '9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738',
             'exact whole-ROM inverse of controller bridge')
    if sha(result_predecessor) == '9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738':
        restored = bytearray(result_predecessor)
        for start, end in ((0x5C6500, 0x5C652C), (0x6FC300, 0x6FC334)):
            restored[start:end] = b'\xff' * (end - start)
        result_predecessor = bytes(restored)
    need(sha(result_predecessor) == PINS['after'] and sha(retail) == PINS['gba'],
         'immutable result ROM or exact whole-ROM inverse of reviewed resident callers')
    need(sha(observer) == SCRIPT, 'reviewed frozen ordinary-input observer')
    need(not re.search(rb'(memory\.write|emu\.setregister|savestate\.|loadstate)', observer), 'no guest state-write APIs')
    launch = json.loads(read(directory / 'launch.json'))
    for key in ('completed', 'loaded_rom_exact', 'script_unchanged'):
        need(launch.get(key) is True, 'completed launch evidence: ' + key)
    need(launch['visible'] is False and launch['physical_background_input'] is False and launch['guest_writes'] == [], 'private ordinary-input launch')
    need(launch['script_sha256'] == SCRIPT and launch['rom_sha256'] == sha(rom) and launch['exe_sha256'] == EXE, 'pinned launch identities')
    root = Path(__file__).resolve().parents[1]
    need(sha(read(root / 'tools/bizhawk_probe_gba_collision.lua')) == launch['base_script_sha256'], 'unchanged base observer')
    need(sha(read(root / 'local/BizHawk-2.11.1/EmuHawk.exe')) == EXE, 'actual pinned emulator executable')
    names = {p.name for p in directory.iterdir() if p.is_file() and p.name != 'launch.json'}
    need(names == set(launch['files']), 'complete final top-level capture inventory')
    for name, digest in launch['files'].items():
        need(Path(name).name == name and sha(read(directory / name)) == digest, 'frozen capture identity: ' + name)
    need(read(directory / 'loaded-rom.bin') == rom == read(directory / 'probe.gba'), 'complete actual loaded8MB ROM')
    cfg = json.loads(read(directory / 'config.json'))
    for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM'):
        need(cfg[key] is False, 'isolated configuration: ' + key)
    def recurse(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'AutoLoad':
                    need(child is False, 'all recursive autoloads disabled')
                recurse(child)
        elif isinstance(value, list):
            for child in value:
                recurse(child)
    recurse(cfg)
    prefix = 'W:/build/' + directory.name + '/data/'
    need(all(e['Path'].startswith(prefix) for e in cfg['PathEntries']['Paths']), 'all data paths isolated to run')
    language = launch['language']; need(language in range(4), 'language domain')
    text = read(directory / 'trace.txt').decode('utf-8')
    lines = text.splitlines(); summary = fields(lines[-1])
    need(lines[-1].startswith('summary ') and summary['outcome'] == read(directory / 'result-done.txt').decode() == 'result-label-observed', 'post-flush successful result completion')
    for key in ('committed', 'title', 'battle', 'result', 'label', 'plus120', 'plus300'):
        need(summary[key] == 'true', 'actual route complete: ' + key)
    need(summary['language'] == str(language), 'summary language')
    writers = [fields(l) for l in lines if l.startswith('native-writer-entry ')]
    need(len(writers) == int(summary['writer_calls']) > 0 and all(int(e['tag'], 16) == 0xA0 + language for e in writers), 'actual native EEPROM writer entry')
    snaps, capture_meta = {}, {}
    for l in lines:
        if not l.startswith('capture='):
            continue
        info = fields(l); name = info['capture']; capture_meta[name] = info
        snap = {k: read(directory / (name + '-' + k + '.bin')) for k in SIZES}
        need(all(len(snap[k]) == size for k, size in SIZES.items()), 'complete snapshot regions')
        renderer(snap['iwram'], retail)
        need(h(snap['iwram'], 0x2310) == int(info['mode']), 'capture actual mode')
        snaps[name] = snap
    staged = snaps['options-staged']; at = task(staged['ewram'], 0x1500)
    need(h(staged['iwram'], 0x473E) == 4 and h(staged['ewram'], at + 0x18) == language and h(staged['ewram'], at + 0x1C) == 0, 'actual staged Options row/language/error')
    checksum(snaps['options-committed']['iwram'], 0xA0 + language)
    need(int(capture_meta['options-staged']['core']) <= int(writers[0]['core']) < int(capture_meta['options-committed']['core']), 'native writer between staging and committed capture')
    title = snaps['title-committed']['iwram']
    need(all(tuple(u(title, 0x2A78 + i * 0x50 + off) for off in (0x44, 0x48, 0x4C)) == (0x0808FC58, TITLE[language], 0x08090878) for i in range(5)), 'five actual title P1/P0/P2 triples')
    init = [fields(l) for l in lines if l.startswith('initialized ')]
    draws = [fields(l) for l in lines if l.startswith('text-draw ')]
    for events, allowed in ((init, INIT), (draws, DRAW)):
        need(bool(events), 'actual result hook calibration')
        for event in events:
            callback = int(event['callback'], 16)
            need(callback in allowed and int(event['exposed_PC'], 16) == callback + 4, 'actual ARM callback and exposed PC')
    need(len(init) == int(summary['init_calls']) and all(int(e['P0'], 16) == RESULT[language] for e in init), 'every actual result initializer selected correct P0')
    labels = [e for e in draws if int(e['P0'], 16) == RESULT[language] and int(e['event']) in (0, 1, 3)]
    need(labels and all(int(e['P1'], 16) == 0x080B9004 and int(e['P2'], 16) == 0x080B9144 for e in labels), 'actual selected label draw with retained P1/P2')
    start = int(capture_meta['result-enter']['core'])
    battle_relative = next(int(fields(l)['relative']) for l in lines if l.startswith('stage=battle '))
    need(all(not fields(l)['keys'] for l in lines if l.startswith('input ') and int(fields(l)['relative']) >= battle_relative), 'no combat or result button input')
    for name, age in [('result-plus120', 120), ('result-plus300', 300)]:
        need(int(capture_meta[name]['core']) - start == age and int(capture_meta[name]['mode']) == 8, 'actual mode8 capture age')
    need(all(start <= int(e['core']) <= int(capture_meta['result-plus300']['core']) for e in init + draws), 'hooks within actual result interval')
    # Whole retained consumer spans, including palette override and copied renderer.
    for lo, hi in ((0x89A24, 0x89A60), (0x8A39C, 0x8A3A4), (0x89374, 0x89394), (0xB9144, 0xB916A), (0x12C58, 0x12DD8), (0xBA8, 0xBD0)):
        need(rom[lo:hi] == retail[lo:hi], 'unchanged retail palette/renderer consumer')
    final = snaps['result-plus300']; resource = native(rom, RESULT[language] - 0x08000000)
    rendered = label_hardware(final, int(labels[0]['object'], 16), resource, rom, directory / 'result-plus300.png')
    negatives = selfchecks(retail)
    for region, offset in (('vram', 0x10000), ('palette', 0x24C)):
        changed = dict(final); data = bytearray(changed[region]); data[offset] ^= 1; changed[region] = bytes(data)
        try:
            label_hardware(changed, int(labels[0]['object'], 16), resource, rom, directory / 'result-plus300.png')
        except ValueError:
            negatives.append('actual label ' + region)
        else:
            raise ValueError('mutated label hardware accepted')
    counts = {name: len(oam_check(snap['oam'])) for name, snap in snaps.items()}
    return dict(status='PASS', language=('en', 'ja', 'ko', 'digicode')[language], rom_sha256=sha(rom),
                launch_sha256=sha(read(directory / 'launch.json')), trace_sha256=sha(read(directory / 'trace.txt')),
                observer_sha256=SCRIPT, files_verified=len(names), snapshots=len(snaps), writer_calls=len(writers),
                init_calls=len(init), draw_calls=int(summary['draw_calls']), unique_draws=len(draws), rendered_label=rendered,
                oam_counts=counts, native_renderer_sha256=sha(retail[0x12C58:0x12DD8]),
                last_chance_observed=any(int(e['event']) == 3 for e in labels), negative_selfchecks=negatives,
                limitations=['Current session native commit; no fresh-process persistence test.',
                             'Title capture establishes selected presentations, not settled menu visibility.',
                             'First draw hook precedes hardware DMA; full pixel proof uses +300 capture.',
                             'Boundary display-register dump is not a scanline trace; screenshot independently proves visible pixels.',
                             'No forced last-chance/draw, full campaign, hardware or complete localization claim.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('capture', 'rom', 'retail', 'observer', 'output'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    need(a.output.resolve().parent != a.capture.resolve(), 'audit output must not modify frozen capture inventory')
    report = audit(a.capture, read(a.rom), read(a.retail), read(a.observer))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
