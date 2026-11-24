"""Compare the four fresh Options runs with physical tiles, palettes and final 240x160 frames."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw
from verify_character_select_name_scene import grid, sha
from verify_initial_portrait_header import AFTER


def color(word):
    return tuple(round(((word >> shift) & 31) * 255 / 31) for shift in (0,5,10))


def frame(directory, name):
    load = lambda ext: (directory / (name + '-' + ext + '.bin')).read_bytes()
    png = Image.open(directory / (name + '.png')).convert('RGB')
    assert png.size == (240,160)
    return png, load('iwram'), load('vram'), struct.unpack('<512H',load('palette')), load('oam')


def title(directory, name, index, bank, atlas, base):
    png, ram, vram, palette, objects = frame(directory,name)
    assert ram[0x112f] == 0xa0 + index
    table, descriptor = struct.unpack_from('<II',atlas,bank - base)
    _, tiles = struct.unpack_from('<II',atlas,descriptor - base)
    parts = 0
    drawn = {}
    for row,event in enumerate([0] if name=='prompt' else range(1,6)):
        cx,cy = struct.unpack_from('<hh',ram,0x2a78 + row*0x50)
        count,layout = struct.unpack_from('<II',atlas,table-base+event*8)
        for i in range(count):
            tile,dy,dx = struct.unpack_from('<Hbb',atlas,layout-base+i*4)
            a0,a1,a2 = struct.unpack_from('<3H',objects,parts*8)
            x,y = cx+dx+8,cy+dy+8
            assert (a0&255,a1&511)==(y,x)
            physical = vram[0x10000+(a2&1023)*32:0x10020+(a2&1023)*32]
            start = tiles-base+(tile&0x3fff)*32
            assert physical==atlas[start:start+32]
            assert ((a1>>12)&3)==(tile>>14)
            for yy in range(8):
                for xx in range(8):
                    tx = 7-xx if tile&0x4000 else xx
                    ty = 7-yy if tile&0x8000 else yy
                    v = physical[4*ty+tx//2] >> (4*(tx%2)) & 15
                    if v: drawn.setdefault((x+xx,y+yy),color(palette[256+(a2>>12)*16+v]))
            parts += 1
    assert parts==struct.unpack_from('<H',ram,0x12d6)[0]
    for pos,rgb in drawn.items():
        assert png.getpixel(pos)==rgb,(name,index,pos,rgb,png.getpixel(pos))
    return parts,len(drawn)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('build','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    assets=a.build/'mode23-title-assets-r4-20261117'
    atlas=(assets/'assets.bin').read_bytes()
    assert sha(atlas)=='4BB3592128E231C49457551BE6C9DDB39734F8515FCFBBA6D8EA7CA817173CB4'
    meta=json.loads((assets/'manifest.json').read_bytes())
    rows=[]
    sheet=Image.new('RGB',(960,4*160+18))
    for i,(lang,bank) in enumerate(meta['languages'].items()):
        d=a.build / ('bizhawk-title-headers-fixed-20261124-lang'+str(i))
        record=json.loads((d/'launch.json').read_bytes())
        assert sha((d/'loaded-rom.bin').read_bytes())==record['rom_sha256']==AFTER
        assert record['outcome']=='ordinary-language-title-portrait-complete' and record['script_unchanged']
        assert record['visible'] is False and record['guest_writes']==[] and record['supplied_save_used'] is False
        for f,pin in record['files'].items(): assert sha((d/f).read_bytes())==pin
        stages={}
        for j,name in enumerate(('prompt','root','portrait','portrait-next')):
            png,ram,vram,pal,oam=frame(d,name)
            sheet.paste(png,(240*i,18+160*j))
            if j<2:
                stages[name]=title(d,name,i,bank['address'],atlas,meta['base_address'])
            else:
                header=(a.build/'character-select-name-assets-r3-20261117'/f'{i}-{j-2:02d}.bin').read_bytes()
                assert header==vram[0x5780:0x5a80] and ram[0x112f]==0xa0+i
                for (x,y),p in grid(header).items():
                    pos=(124+x,16+y)
                    assert png.getpixel(pos)==color(pal[16+p]),(name,i,pos,png.getpixel(pos),color(pal[16+p]))
                stages[name]=1536
        ImageDraw.Draw(sheet).text((i*240+6,3),lang,fill='white')
        rows.append(dict(language=lang,launch=sha((d/'launch.json').read_bytes()),screens=stages))
    a.output.mkdir(parents=True,exist_ok=True)
    sheet.save(a.output/'live-four-languages.png')
    result=dict(status='PASS',rom=AFTER,checks=rows,checker_sha256=sha(Path(__file__).read_bytes()))
    report=a.output/'report.json';report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS',sha(report.read_bytes()))


if __name__=='__main__':
    main()
