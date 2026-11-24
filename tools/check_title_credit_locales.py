"""Check both real title transfer paths, language fallbacks, ABI and map bounds."""
import argparse,json,struct
from pathlib import Path
from verify_mode20_title_assets import DMA, BASE
from verify_mode23_completion_save import dump
from build_character_select_name_scene import sha

def check(rom,owner):
    pointers=owner['credit_tiles']
    tally=0
    for site,stop,mapbase in ((0x8090924,0x8090938,0x0600f000),(0x80406dc,0x80406ec,0x0600f800)):
        for marker in (0,1,0xa0,0xa1,0xa2,0xa3,0xff):
            for flags in (0,5,10,15):
                m=DMA(rom,seed=4,flags=flags<<28|0x1f)
                saved=m.r[:]
                m.put(0x0300112f,marker,1)
                normal=0x329d
                dest=mapbase+0x3f0
                m.put(dest-2,0xCAFE,2)
                m.put(dest,normal,2)
                m.put(dest+2,0xBEEF,2)
                m.run(site,{stop})
                assert all(m.r[i]==saved[i] for i in (0,1,3,6,7,9,10,11,13))
                assert m.r[14]==stop and m.r[2]==0x4c0 and m.r[4]==0x08719240 and m.r[5]==0x06006500
                assert m.cpsr==flags<<28|0x1f
                if site==0x8090924:
                    m.run(0x8090958,{0x809095c})
                    assert m.r[8]==0 and m.cpsr==flags<<28|0x1f
                lang={0xa1:'ja',0xa2:'ko',0xa3:'dg'}.get(marker,'en')
                expected=rom[0x712680:0x714680]+rom[0x717f40:0x719240]
                patched=bytearray(expected)
                if lang!='ja':
                    at=pointers[lang]-BASE
                    patched[0x2aa0:0x2f60]=rom[at:at+1216]
                    if lang=='en': patched[0x21a0:0x21c0]=rom[at+1216:at+1248]
                assert dump(m,0x06003200,0x3300)==patched
                assert [m.get(dest+i,2) for i in (-2,0,2)]==[0xCAFE,0x529d if lang=='en' else normal,0xBEEF]
                tally+=1
    return tally
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('image','manifest'):p.add_argument(arg,type=Path)
    a=p.parse_args()
    rom=a.image.read_bytes();owner=json.loads(a.manifest.read_bytes())
    assert sha(rom)==owner['output_sha256'] and owner['whole_image_inverse']
    print('PASS',check(rom,owner),'title transfers')
