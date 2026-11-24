"""Check the title's earned badge and win count against WSC tiles and the physical GBA frame."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib
from PIL import Image
from verify_title_portrait_live_frames import color
from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def check(source, save, folder):
    assert sha(source)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    report=json.loads((folder/'launch.json').read_bytes())
    assert report['outcome']=='PASS' and report['loaded_rom_exact'] and report['script_unchanged']
    assert not report['visible'] and not report['guest_writes'] and sha(save)==report['copied_campaign_eeprom']
    tail=b''.join(save[i:i+8][::-1] for i in range(27*8,34*8,8))
    if tail in (bytes(56),bytes([255])*56):
        counter,rank=0,-1
    else:
        assert tail[:8]==b'BS15TAG\1' and struct.unpack_from('<I',tail,52)[0]==zlib.crc32(tail[8:52])
        ranks=struct.unpack_from('<11H',tail,26)
        rank=max((i for i,n in enumerate(ranks) if n),default=-1)
        counter=min(struct.unpack_from('<H',tail,48)[0],999)
    cells={}
    def cell(x,y,raw,pal,bank):
        cells[x+8,y+8]=(convert_tile(source[raw:raw+32]),pal,bank)
    if rank>=0:
        off=0x2D9360+struct.unpack_from('<H',source,0x780288+rank*2)[0]
        pal=0x2D9360+struct.unpack_from('<H',source,0x78029e+rank*2)[0]
        for i in range(28):
            cell(166+8*(i%7),2+8*(i//7),off+i*32,pal,13)
    text=f'{counter:03d}'.encode()+source[0x7803F5:0x7803FB]
    for i,c in enumerate(text):
        cell(2+8*i+(8 if i>=3 else 0),2,0x43e9c0+(c-32)*32,0x43f1c0,14)
    def read(name):
        raw=(folder/name).read_bytes()
        assert report['files'][name]==sha(raw)
        return raw
    oam=read('title-oam.bin')
    root=read('root-oam.bin')
    vram=read('title-vram.bin')
    palette=struct.unpack('<512H',read('title-palette.bin'))
    read('title.png')
    with Image.open(folder/'title.png') as pic:
        picture=pic.convert('RGB')
    actual=set()
    ink=0
    for a0,a1,a2,_ in struct.iter_unpack('<4H',oam):
        bank=a2>>12
        if a0&0x300==0x200 or bank not in (13,14):
            continue
        x,y=a1&511,a0&255
        tile,raw,expected_bank=cells[x,y]
        assert a0==y and a1==x and bank==expected_bank and (x,y) not in actual
        actual.add((x,y))
        at=0x10000+(a2&1023)*32
        assert vram[at:at+32]==tile
        colors=tuple(convert_color(c) for c in struct.unpack_from('<16H',source,raw))
        assert palette[256+bank*16:272+bank*16]==colors
        for i in range(64):
            c=(tile[i//2]>>(4*(i%2)))&15
            if c:
                assert picture.getpixel((x+i%8,y+i//8))==color(colors[c])
                ink+=1
    assert actual==cells.keys()
    active=[a for a in struct.iter_unpack('<4H',root) if a[0]&0x300!=0x200]
    assert len(active)==110 and not any(a[2]>>12 in (13,14) for a in active)
    return dict(rank=rank,wins=counter,visible_source_cells=len(actual),exact_opaque_pixels=ink,root_objects=len(active))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('source','save','capture'):
        parser.add_argument(arg,type=Path)
    args=parser.parse_args()
    print('PASS',check(args.source.read_bytes(),args.save.read_bytes(),args.capture))
