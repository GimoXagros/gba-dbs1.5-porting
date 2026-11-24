"""Cross-check both peers' saves and the promoted player's real sprite, particles and name transition."""
import argparse
import json
from pathlib import Path
import re
import struct

from PIL import Image
from verify_mode24_master_feedback import capture
from verify_mode24_link_capture import colors, gba_tile, tile
from verify_mode23_completion_save import sha


def pose_candidates(image, active, vram, palette, y, event, facing):
    def word(at):
        return struct.unpack_from('<I',image,at-0x08000000)[0]
    found=[]
    for character in range(15):
        row=0x084a80f8+32*character
        p0,p1,pal0,pal1=(word(row+j) for j in (0,4,8,12))
        candidates=[i for i,p in enumerate((pal0,pal1)) if image[p-0x08000000+6:p-0x08000000+38]==palette]
        if not candidates:continue
        sequence=word(p1)+16*event
        for idx in range(word(sequence)):
            f=word(sequence+4)+16*idx
            layout,art=struct.unpack_from('<2H',image,f-0x08000000+2)
            desc=word(p0)+layout*8
            if word(desc)!=len(active):continue
            tex=word(word(p0+4)+8*art+4)-0x08000000
            for i,(a0,a1,a2,_) in enumerate(active):
                flags,dy,dx=struct.unpack_from('<Hbb',image,word(desc+4)-0x08000000+4*i)
                if facing:
                    dx=-dx-8;flags^=0x4000
                offset=32*(flags&511)
                start=32*(a2&1023)
                if ((a0&255,a1&511,(a1>>12)&3)!=(y+dy+8,120+dx,(flags>>14)&3)
                    or vram[start:start+32]!=image[tex+offset:tex+offset+32]):
                    break
            else:found.append([character,candidates,event,idx])
    assert found
    return found


def run(source,image,folder):
    saves=capture(source,folder,sha(image))
    player=next(p['player'] for p in saves if p['won'])
    def read(age,name):
        return (folder/f'p{player}-card-party-{age}-{name}.bin').read_bytes()
    def states(age):
        return list(struct.iter_unpack('<hhbbHBB',read(age,'first')+read(age,'second')))
    seeded=states(0)
    assert len(seeded)==30 and all(not any(r[2:]) for r in seeded)
    assert [r[:2] for r in seeded]==list(struct.iter_unpack('<hh',source[0x774ca8:0x774d20]))
    text=(folder/f'p{player}.txt').read_text()
    stages={int(t):(int(s),int(y),int(j),int(d)) for t,s,y,j,d in re.findall(r'party f=\d+ tick=(\d+) phase=(\d+) y=(\d+) jump=(\d+) facing=(\d+)',text)}
    assert stages[0]==(3,128,0,0) and stages[150][0]==3 and stages[152][0]==2
    assert states(99)!=states(100) and states(100)!=states(101)
    frames=[]
    for age in (100,101):
        # Frame callback follows VBlank. Physical OBJ/VRAM contains the immediately preceding update.
        previous=age-1
        objects=[entry for entry in struct.iter_unpack('<4H',read(age,'oam')) if entry[0]&0x300!=0x200]
        confetti=[entry for entry in objects if entry[2]>>12==3]
        actor=[entry for entry in objects if entry[2]>>12==4]
        assert len(confetti)+len(actor)==len(objects) and actor and confetti
        pal=read(age,'palette');vram=read(age,'vram')
        assert struct.unpack_from('<16H',pal,3*32)==colors(source,0x3d7f76)
        emitted=[]
        for index,(x,y,*_) in enumerate(states(previous)):
            x=x//16-4;y=y//16-4
            if -15<=x<232 and -15<=y<152:
                frame=((previous+2*((index+1)//6))%30)//10
                source_tile=(0,9,6,3,12,15)[index%6]+frame
                emitted.append(((y+8)&255,(x+8)&511,source_tile))
        assert len(emitted)==len(confetti)
        for (ay,ax,a2,_),(y,x,t) in zip(confetti,emitted):
            assert (ay,ax)==(y,x)
            at=32*(a2&1023)
            assert vram[at:at+32]==gba_tile(tile(source,0x3cd6b0+32*t))
        _,ground_y,jump,facing=stages[previous]
        poses=pose_candidates(image,actor,vram,pal[128:160],ground_y,17 if jump==4 else jump+4,facing)
        # Resolve OBJ ordering independently and compare every visible foreground pixel.
        painted={}
        for a0,a1,a2,_ in reversed(objects):
            x,y=a1&511,a0&255
            if x>=256:x-=512
            if y>=160:y-=256
            offset=32*(a2&1023)
            for iy in range(8):
                for ix in range(8):
                    if not(0<=x+ix<240 and 0<=y+iy<160):continue
                    src=(7-iy if a1&0x2000 else iy)*8+(7-ix if a1&0x1000 else ix)
                    index=(vram[offset+src//2]>>(4*(src%2)))&15
                    if not index:continue
                    color=struct.unpack_from('<H',pal,2*((a2>>12)*16+index))[0]
                    painted[x+ix,y+iy]=tuple(((c<<3)|(c>>2)) for c in ((color>>s)&31 for s in (0,5,10)))
        with Image.open(folder/f'p{player}-party-{age}-frame.png') as pic:
            screen=pic.convert('RGB')
            # The retained border covers the top/bottom and left/right 8 pixels.
            # Its texture is already visible on the same physical Master card before any particles.
            with Image.open(folder/f'p{player}-card-540.png') as before_party:
                border=before_party.convert('RGB')
                for point,rgb in painted.items():
                    x,y=point
                    if not (8<=x<232 and 8<=y<152):
                        rgb=border.getpixel(point)
                    assert screen.getpixel(point)==rgb,(age,point,screen.getpixel(point),rgb)
        frames.append(dict(age=age,visible_particles=len(confetti),actor_parts=len(actor),actor_matches=poses,
                           verified_overlay_pixels=len(painted)))
    assert any(a[0]==b[0] for a in frames[0]['actor_matches'] for b in frames[1]['actor_matches'])
    return dict(status='MODE24_LINK_MASTER_PRESENTATION_PASS',image_sha256=sha(image),players=saves,
                source_particle_seeds=30,frames=frames,source_phases=stages)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','image','capture','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    report=run(a.source.read_bytes(),a.image.read_bytes(),a.capture)
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
