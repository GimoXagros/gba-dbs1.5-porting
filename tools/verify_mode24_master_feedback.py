"""Exercise all four native name-control sounds and validate a real linked decimal carry."""
import argparse
import json
from pathlib import Path
import re
import struct

from PIL import Image
from verify_mode22_stats_bridge import Device, encode_snapshot
from verify_mode23_completion_save import dump, fill, sha
from verify_link_tag_capture import eeprom
from verify_mode24_link_capture import colors, tile, pixels

CARD_CALL,INPUT_CMP=0x08ecab10,0x08ecab2c


def abi(image,meta):
    total=0
    for action,song,priority in ((0,None,None),(0x78,0x1e,1),(0x79,0x1f,1),(0x7a,0x20,1),(6,0x21,2)):
        for result in (0,1,2):
            for n in (0,4,10,15):
                m=Device(image,encode_snapshot(bytes(42)))
                m.r[0:2]=[result,action];m.cpsr=n<<28|31
                old=m.r[:15]
                pc=m.drive(INPUT_CMP,{0x080d15c0,INPUT_CMP+4})
                if song is not None:
                    assert pc==0x080d15c0 and m.r[8:12]==[song,priority,0,0]
                    for i in (0,1,2,3,8,9,10,11,12):m.r[i]=0x7c00+i
                    m.drive(m.r[14],{INPUT_CMP+4})
                else:assert pc==INPUT_CMP+4
                assert m.r[:15]==old and bool(m.cpsr&0x40000000)==(result==2)
                total+=1
    return total


def capture(source,folder,image_sha):
    run=json.loads((folder/'launch.json').read_bytes())
    assert run['finished']==[True,True] and run['carry_to_special'] and run['card_screens']
    assert run['rom_sha256']==image_sha and not run['guest_writes'] and not run['visible']
    players=[]
    for p in (1,2):
        assert sha((folder/f'player{p}.gba').read_bytes())==image_sha
        l=(folder/f'p{p}.txt').read_text()
        pre,old=eeprom(folder/f'initial-{p}.bin');post,new=eeprom(folder/f'player{p}.sav')
        assert pre[200:216]==post[200:216] and pre[272:]==post[272:]
        assert list(struct.unpack_from('<11H',old,18))==[0]*9+[9,0]
        matches=re.findall(r'card f=(\d+) elapsed=150 token=([0-9A-F]+) ext=D675',l)
        assert len(matches)==1
        token=int(matches[0][1],16);won=bool(token&0x8000)
        assert token&0x7fff==9
        sounds=[(int(v,16),int(pr)) for v,pr in re.findall(r'card-audio f=\d+ song=([0-9A-F]+) priority=(\d+)',l)]
        target=old.copy();ink=0
        if won:
            assert sounds==[(0x7b,1),(0x7c,4),(0x7b,1),(0x7e,4),(0x1f,1),(0x1f,1),(0x1f,1),(0x21,2)]
            struct.pack_into('<HH',target,36,0,1);target[14:18]=b'AAA\0'
            struck=struct.unpack_from('<H',old,40)[0]+1
            struct.pack_into('<H',target,40,struck)
            a,b=struct.unpack_from('<2H',source,0x77407c+40)
            with Image.open(folder/f'p{p}-card-540.png') as raw:screen=raw.convert('RGB')
            pal=colors(source,0x2d9360+b)
            for i in range(60):
                ink+=pixels(screen,80+8*(i%10),24+8*(i//10),tile(source,0x2d9360+a+32*i),pal)
            assert (folder/f'p{p}-card-860.png').exists()
        else:
            assert sounds==[(0x7b,1),(0x7d,4)]
            struct.pack_into('<HH',target,36,8,0)
            struct.pack_into('<H',target,40,0)
        assert target==new
        moves=re.findall(r'f=(\d+) mode=(\d+)',l)
        entered=max(int(f) for f,m in moves if m=='24' and int(f)<=int(matches[0][0]))
        returned=min(int(f) for f,m in moves if m=='4' and int(f)>int(matches[0][0]))
        players.append(dict(player=p,won=won,source_master_visible_pixels=ink,source_name=bytes(new[14:18]).hex(),
                            counter=struct.unpack_from('<H',new,40)[0],actual_requests=sounds,entered=entered,returned=returned,
                            physical_eeprom_sha256=sha((folder/f'player{p}.sav').read_bytes())))
    assert {i['won'] for i in players}=={True,False}
    return players


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('image','owner','report'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--capture',type=Path)
    p.add_argument('--source',type=Path)
    a=p.parse_args();rom=a.image.read_bytes();meta=json.loads(a.owner.read_bytes())
    assert meta['output_sha256']==sha(rom) and meta['whole_image_inverse']
    result=dict(status='NATIVE_MODE24_MASTER_FEEDBACK_PASS',image_sha256=sha(rom),keyboard_abi_cases=abi(rom,meta),
                checker_sha256=sha(Path(__file__).read_bytes()))
    if a.capture:
        src=a.source.read_bytes();assert sha(src)==meta['source_sha256']
        result['players']=capture(src,a.capture,sha(rom))
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
