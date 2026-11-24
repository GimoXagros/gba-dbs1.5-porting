"""Compare every credit strip tile and displayed pixel on four actual language runs."""
import argparse,json,struct
from pathlib import Path
from PIL import Image
from verify_title_portrait_live_frames import color
from build_character_select_name_scene import sha
from build_title_background import TILES1,TILES2,MAP

def verify(rom,owner,folders):
    native=rom[TILES1:TILES1+8192]+rom[TILES2:TILES2+4864]
    entries=[]
    for i,lang in enumerate(('en','ja','ko','dg')):
        folder=folders[i]
        launch=json.loads((folder/'launch.json').read_bytes())
        assert launch['language']==i and launch['rom_sha256']==sha(rom) and launch['outcome']=='PASS'
        assert launch['loaded_rom_exact'] and not launch['visible'] and not launch['guest_writes']
        load=lambda name:(folder/name).read_bytes()
        for name in ('title-palette.bin','title-vram.bin','title.png','main.png'):
            assert sha(load(name))==launch['files'][name]
        expected=bytearray(native)
        offset=(0x2e5-400)*32
        if lang!='ja':
            at=owner['credit_tiles'][lang]-0x08000000
            expected[offset:offset+1216]=rom[at:at+1216]
            if lang=='en':
                edge=(0x29d-400)*32
                expected[edge:edge+32]=rom[at+1216:at+1248]
        vr=load('title-vram.bin')
        assert vr[0x3200:0x6500]==expected,(lang,'VRAM')
        pal=struct.unpack('<512H',load('title-palette.bin'))
        frame=Image.open(folder/'title.png').convert('RGB')
        for y in range(120,144):
            for x in range(40,200):
                cell=struct.unpack_from('<H',vr,0xf000+(y//8)*64+(x//8)*2)[0]
                want=struct.unpack_from('<H',rom,MAP+2*(y//8*28+x//8))[0]
                if lang=='en' and (x//8,y//8)==(24,15): want=0x529d
                assert cell==want
                sx,sy=(7-x%8 if cell&1024 else x%8),(7-y%8 if cell&2048 else y%8)
                b=vr[(cell&1023)*32+4*sy+sx//2]
                index=b>>(sx%2*4)&15
                rgb=color(pal[(cell>>12)*16+index])
                assert frame.getpixel((8+x,8+y))==rgb,(lang,x,y,rgb,frame.getpixel((8+x,8+y)))
        entries.append(dict(language=lang,verified_title_tiles=408,verified_credit_and_year_pixels=3840,
                            capture_sha256=sha(load('title.png')),launch_sha256=sha(load('launch.json'))))
    return entries

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('rom','owner','output'): p.add_argument('--'+arg,type=Path,required=True)
    p.add_argument('folders',type=Path,nargs=4)
    a=p.parse_args()
    rom=a.rom.read_bytes()
    report=dict(rom_sha256=sha(rom),captures=verify(rom,json.loads(a.owner.read_bytes()),a.folders))
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS 4 x 3840',sha(a.output.read_bytes()))
