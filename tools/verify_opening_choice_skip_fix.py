"""Check the opening correction, with optional original and GBA screen and timing captures."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import Image

from build_new_base_p1_assets import wsc_pointer
from convert_wsc_palette_block import convert_block


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def check_image(source, prior, image, owner):
    assert digest(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert owner['input_sha256'] == digest(prior) and owner['output_sha256'] == digest(image)
    assert owner['source_sha256'] == digest(source) and len(prior) == len(image) == 0x1000000
    assert source[0x75a58c:0x75a59a] == bytes.fromhex('55 8bec 8b4606 c1e005 8b7e0a 03f8')
    assert image[0x88250:0x88260] == bytes.fromhex('00402de9 0c009de5 04509de5 805285e0')
    view = word(image, 0x5b4254) - 0x08000000
    palettes = []
    for side, call in enumerate((0x7593d1, 0x7593fd)):
        actor = 13 + side
        assert source[call:call+12] == bytes.fromhex('68c0036a00' if not side else '68c0036a01') + bytes([0x6a, actor]) + bytes.fromhex('9acc4c8c55')
        source_row = struct.unpack_from('<H', source, call+1)[0] + actor * 32
        src = wsc_pointer(source, 0x740000+source_row+12)
        block = source[src:src+38]
        target = word(image, view+actor*32+8) - 0x08000000
        assert image[target:target+40] == convert_block(block)
        prev = word(prior, 0x5b4254) - 0x08000000
        incorrect = word(prior, prev+actor*32+8) - 0x08000000
        assert prior[incorrect:incorrect+40] != image[target:target+40]
        palettes.append(block)
    assert source[0x757623:0x75762e] == bytes.fromhex('26c70616093000 26a31809')
    assert source[0x75a227:0x75a230] == bytes.fromhex('a11809 3b061609 7703')
    assert image[0x87e74:0x87e88] == bytes.fromhex('64809fe5 f090d8e1 f200d8e1 090050e1 0000008a')
    assert word(image, 0x5b8488) == word(image, 0x87e74+8+0x64) == 0x0300267c
    assert image[0x83c74:0x83c84] == bytes.fromhex('c0809fe5 2690a0e3 b090c8e1 b200c8e1')
    assert word(image, 0x83c74+8+0xc0) == 0x0300267c
    inverse = bytearray(image)
    for offset, original in ((0x5b4254,0x085b5400),(0x5b8488,0x03002338)):
        assert word(prior, offset) == original
        struct.pack_into('<I', inverse, offset, original)
    assert inverse == prior
    return palettes


def capture(folder, expected, skip):
    launch = json.loads((folder/'launch.json').read_bytes())
    assert launch['status'] == 'title' and launch['choice_detail'] and launch['skip'] == skip
    assert launch['loaded_rom_exact'] and not launch['visible'] and not launch['supplied_save'] and not launch['guest_writes']
    assert launch['rom_sha256'] == digest((folder/'loaded-rom.bin').read_bytes()) == expected
    log = (folder/'trace.txt').read_bytes()
    assert digest(log) == launch['trace_sha256']
    return log.decode().replace('\r\n', '\n')


def actor_pixels(path, side, ws):
    with Image.open(path) as frame:
        im = frame.convert('RGB')
    assert im.size == ((224,144) if ws else (240,160))
    if not ws:
        im = im.crop((8,8,232,152))
    pixels = {}
    for y in range(im.height):
        row = [im.getpixel((x,y)) for x in range(im.width)]
        background, count = Counter(row).most_common(1)[0]
        assert count > 112
        for x in range(112*side, 112*(side+1)):
            if row[x] != background:
                pixels[x,y] = tuple(channel >> 4 for channel in row[x])
    left = min(x for x,y in pixels)
    top = min(y for x,y in pixels)
    return {(x-left,y-top):rgb for (x,y),rgb in pixels.items()}, (left,top)


def check_art(ws, gba, palettes, hashes):
    for folder, sha in zip((ws,gba),hashes):
        log = capture(folder, sha, False)
        assert re.findall(r'callback frame=\d+ id=(19|20|21|22|23) state=', log) == ['19','20','21','23']
        assert re.findall(r'mode frame=\d+ id=3 choice=(\d+)', log)[-1] == '4'
    ram = (ws/'choice3-16-ram.bin').read_bytes()
    palram = (gba/'choice3-16-palette.bin').read_bytes()
    assert len(ram)==65536 and len(palram)==1024
    for side, block in enumerate(palettes):
        w = 0xff22+32*side
        g = 0x222+32*side
        assert ram[w:w+30] == block[8:38]
        assert palram[g:g+30] == convert_block(block)[8:38]
    evidence = []
    for side, source_age, native_age, count in ((0,16,16,1307),(1,16,16,1326),(1,20,16,1326),
                                                (0,40,32,1379),(0,60,48,1462)):
        original, wpos = actor_pixels(ws/f'choice3-{source_age:02}.png',side,True)
        native, gpos = actor_pixels(gba/f'choice3-{native_age:02}.png',side,False)
        assert original == native and len(native) == count
        evidence.append(dict(side=side, source_age=source_age, native_age=native_age,
                             source_origin=wpos, native_origin=gpos, matched_pixels=count))
    return dict(palette_entries_per_actor=15, matches=evidence)


def check_skip(folder, sha, ws):
    log = capture(folder, sha, True)
    pressed, = map(int,re.findall(r'^Start frame=(\d+) callback=8$',log,re.M))
    title, = map(int,re.findall(r'^mode frame=(\d+) id=3 choice=0$',log,re.M))
    fades = [tuple(map(int,m)) for m in re.findall(r'^fade frame=(\d+) step=(\d+) limit=(\d+) elapsed=(\d+)$',log,re.M)]
    limit = 48 if ws else 38
    assert [f for f, _, _, _ in fades] == list(range(pressed+1,title))
    assert all(threshold == limit for _,_,threshold,_ in fades)
    for phase, last in ((25,limit+int(ws)),(24,limit+1)):
        assert [elapsed for _,step,_,elapsed in fades if step == phase] == list(range(last+1))
    clocks_per_frame = Fraction(256*159,3072000) if ws else Fraction(280896,16777216)
    duration = (title-pressed)*clocks_per_frame
    return dict(start=pressed,title=title,frames=title-pressed,seconds=float(duration)), duration


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source','prior','image','owner','report'):
        p.add_argument('--'+name, type=Path, required=True)
    for name in ('wsc-art','gba-art','wsc-skip','gba-skip'):
        p.add_argument('--'+name,type=Path)
    a = p.parse_args()
    src, prior, image = (f.read_bytes() for f in (a.source,a.prior,a.image))
    palettes = check_image(src,prior,image,json.loads(a.owner.read_bytes()))
    report = dict(source=digest(src),prior=digest(prior),image=digest(image),owner=digest(a.owner.read_bytes()),
                  original_actor_rows=[43,44],native_fade_state='0300267C',whole_image_inverse=True)
    captures = (a.wsc_art,a.gba_art,a.wsc_skip,a.gba_skip)
    if any(captures):
        assert all(captures)
        hashes = (digest(src),digest(image))
        report['art'] = check_art(a.wsc_art,a.gba_art,palettes,hashes)
        source_skip, ws_time = check_skip(a.wsc_skip,hashes[0],True)
        native_skip, gba_time = check_skip(a.gba_skip,hashes[1],False)
        difference = abs(ws_time-gba_time)
        assert difference < Fraction(1,500)
        report['skip'] = dict(wsc=source_skip,gba=native_skip,difference_ms=float(difference*1000))
    with a.report.open('x', encoding='utf8', newline='\n') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print('Opening choice and Start skip PASS',digest(a.report.read_bytes()))


if __name__ == '__main__':
    main()
