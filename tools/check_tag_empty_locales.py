"""Check the installed empty-tag dispatcher and the tile/map bounds of its real copy loop."""
import argparse,json,struct
from pathlib import Path
from verify_shoot_static_companion_clear import Machine
from verify_mode23_completion_save import dump
from build_character_select_name_scene import sha

def check(rom,meta):
    cases=0
    for state in (1,8,16):
        for lang in (0,0xa0,0xa1,0xa2,0xa3,0xff):
            m=Machine(rom,seed=2)
            m.r[5]=state
            m.r[0]=0x02001110
            m.put(m.r[0],0x2000024)
            m.put(0x0300112f,lang,1)
            saved=m.r[4:14]
            custom=state==1 and lang in (0xa2,0xa3)
            pc=m.run(0x08f7aa88,{0x08f7ab88,0x08f7aa8c})
            if not custom:
                assert pc==0x08f7aa8c and m.r[0]==0x02000024
            else:
                assert pc==0x08f7ab88
                src,dst,n,r,mp,md,w,h,end=struct.unpack('<9I',dump(m,m.r[0],36))
                tag='ko' if lang==0xa2 else 'digicode'
                asset=next(a for a in meta['allocations'] if a['label']==tag+' empty tag glyphs')
                assert src==0x8000000+asset['start'] and mp+2*w*h==0x8000000+asset['end']
                assert dst==0x06000020 and r==1 and end==0 and 2*n==32*w*h and w*h<=64
                assert 0x0600f800<=md and md+(h-1)*64+2*w<=0x0600fc80
                # The bounded ARM walker delegates this one native post-increment form.
                post=0x08f7abb0
                assert m.get(post)==0xe0d070b2
                while True:
                    pc=m.run(pc,{post,0x08f7aab0})
                    if pc!=post: break
                    m.r[7]=m.get(m.r[0],2)
                    m.r[0]+=2
                    assert m.get(post+4)==0xe0c670b2
                    m.put(m.r[6],m.r[7],2)
                    m.r[6]+=2
                    pc=post+8
                assert dump(m,dst,n*2)==rom[src-0x8000000:mp-0x8000000]
                words=[m.get(md+y*64+x*2,2) for y in range(h) for x in range(w)]
                assert words==list(range(0x8001,0x8001+w*h))
            assert m.r[4:14]==saved
            cases+=1
    return cases
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for a in ('image','manifest'): p.add_argument(a,type=Path)
    a=p.parse_args();rom=a.image.read_bytes();meta=json.loads(a.manifest.read_bytes())
    assert sha(rom)==meta['output_sha256'] and meta['whole_image_inverse']
    print('PASS',check(rom,meta),'empty message and exception routes')
