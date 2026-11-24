"""Verify a prolonged normal name-entry session following an arbitrary number of real tied matches."""
import argparse
import json
from pathlib import Path
import re
import struct
from PIL import Image
from verify_link_tag_capture import eeprom
from verify_mode24_link_capture import colors, pixels, tile
from verify_mode24_celebration_capture import run
from verify_mode23_completion_save import sha


def matches(source,image,folder):
    result=[]
    for p in (1,2):
        stem=f'p{p}'
        log=(folder/f'{stem}.txt').read_text()
        scores=[tuple(map(int,row)) for row in re.findall(r'pc=0837AB8C f=\d+ role=\d+ side=(\d+) score=(\d+):(\d+)',log)]
        assert scores and all(s[1]==s[2] for s in scores[:-1])
        raw,old=eeprom(folder/f'initial-{p}.bin');saved,new=eeprom(folder/f'player{p}.sav')
        assert sha((folder/f'player{p}.gba').read_bytes())==sha(image)
        assert raw[200:216]==saved[200:216] and raw[272:]==saved[272:]
        assert list(struct.unpack_from('<11H',old,18))==[0]*9+[9,0]
        counter=struct.unpack_from('<H',old,40)[0]
        for side,one,two in scores:
            assert side in (0,1)
            won=(one>two if side==0 else two>one)
            counter=min(999,counter+1) if won else 0
        assert scores[-1][1]!=scores[-1][2]
        expected=old.copy()
        struct.pack_into('<HHH',expected,36,0 if won else 8,1 if won else 0,counter)
        if won:expected[14:18]=b'AAA\0'
        assert expected==new
        events=[(int(song,16),int(pr)) for song,pr in re.findall(r'card-audio f=\d+ song=([0-9A-F]+) priority=(\d+)',log)]
        expected_sounds=[(123,1),(124,4),(123,1),(126,4),(31,1),(31,1),(31,1),(33,2)] if won else [(123,1),(125,4)]
        assert events==expected_sounds
        ink=0
        if won:
            gfx,pal=struct.unpack_from('<HH',source,0x77407c+40);palette=colors(source,0x2d9360+pal)
            with Image.open(folder/f'{stem}-card-540.png') as src:pic=src.convert('RGB')
            for i in range(60):
                ink+=pixels(pic,80+8*(i%10),24+8*(i//10),tile(source,0x2d9360+gfx+32*i),palette)
        result.append(dict(player=p,won=won,scores=scores,counter=counter,source_master_visible_pixels=ink,
                           name=bytes(new[14:18]).hex(),physical_eeprom_sha256=sha((folder/f'player{p}.sav').read_bytes()),
                           sounds=events))
    assert {r['won'] for r in result}=={True,False}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','image','capture','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();source=a.source.read_bytes();image=a.image.read_bytes()
    launch=json.loads((a.capture/'launch.json').read_bytes())
    assert launch['name_idle_frames']==7200 and launch['finished']==[True,True]
    assert launch['rom_sha256']==sha(image) and not launch['guest_writes'] and not launch['visible']
    saves=matches(source,image,a.capture)
    result=run(source,image,a.capture,saves)
    winner=next(p['player'] for p in saves if p['won'])
    log=(a.capture/f'p{winner}.txt').read_text()
    events=[(int(f),int(w),int(h)) for f,w,h in re.findall(r'idle f=(\d+) waited=(\d+) phase=(\d+)',log)]
    assert [w for f,w,h in events]==[0,1800,3600,5400,7200]
    assert all(f-events[0][0]==w and h==151+w%30 for f,w,h in events)
    assert 'idle-complete held=7200 min=151 max=180' in log
    result.update(status='CABLE_NAME_REAL_7200_TICK_IDLE_PASS',uninterrupted_name_idle_frames=7200,
                  name_animation_clock_extrema=[151,180])
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()
