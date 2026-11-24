"""Independently compare both real cable-result frames against WSC card and sprite tiles."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from PIL import Image
from render_wsc_asset_frames import layout_frames
from verify_link_tag_capture import eeprom
from verify_mode23_completion_save import sha


def colors(source, at):
    # WonderSwan's 4-bit color channels expand to the converter's 5-bit GBA representation.
    def one(c):
        red,green,blue=(c>>8)&15,(c>>4)&15,c&15
        return ((red<<1)|bool(red)) | (((green<<1)|bool(green))<<5) | (((blue<<1)|bool(blue))<<10)
    return tuple(one(c) for c in struct.unpack_from('<16H',source,at))


def tile(source,offset):
    plane=source[offset:offset+32]
    return [[sum(((plane[4*y+b]>>(7-x))&1)<<b for b in range(4)) for x in range(8)] for y in range(8)]


def gba_tile(values):
    return bytes(row[x]|(row[x+1]<<4) for row in values for x in range(0,8,2))


def pixels(pic, x, y, values, pal, flipx=False, flipy=False):
    checked=0
    for dy in range(8):
        for dx in range(8):
            index=values[7-dy if flipy else dy][7-dx if flipx else dx]
            if not index:
                continue
            color=pal[index]
            rgb=tuple(((v<<3)|(v>>2)) for v in ((color>>s)&31 for s in (0,5,10)))
            assert pic.getpixel((x+dx,y+dy))==rgb,((x+dx,y+dy),pic.getpixel((x+dx,y+dy)),rgb)
            checked+=1
    return checked


def inspect(source,folder,player,require_audio):
    prefix=f'p{player}-card-'
    def read(name):
        return (folder/(prefix+name+'.bin')).read_bytes()
    log=(folder/f'p{player}.txt').read_text()
    snapshots=re.findall(r'card f=(\d+) elapsed=(\d+) token=([0-9A-F]+) ext=D675',log)
    full=[s for s in snapshots if int(s[1])==150]
    assert len(full)==1
    frame,_,token=full[0];token=int(token,16)
    rank=token&0x7fff;assert 0<=rank<10
    acquired=bool(token&0x8000)
    rows=re.findall(r'f=(\d+) mode=(\d+)',log)
    entered=max(int(f) for f,m in rows if m=='24' and int(f)<=int(frame))
    done=min(int(f) for f,m in rows if m=='4' and int(f)>int(frame))
    before,old=eeprom(folder/f'initial-{player}.bin')
    after,new=eeprom(folder/f'player{player}.sav')
    sounds=[(int(f),int(song,16),int(priority)) for f,song,priority in re.findall(r'card-audio f=(\d+) song=([0-9A-F]+) priority=(\d+)',log)]
    if require_audio:
        assert [(song,prio) for _,song,prio in sounds]==[(0x7b,1),(0x7c if acquired else 0x7d,4)]
        assert sounds[1][0]-sounds[0][0]==111
    assert before[200:216]==after[200:216] and before[272:]==after[272:]
    count=lambda data:struct.unpack_from('<H',data,18+rank*2)[0]
    assert count(new)==count(old)+(1 if acquired else -1)
    assert struct.unpack_from('<H',new,40)[0]==(struct.unpack_from('<H',old,40)[0]+1 if acquired else 0)
    unchanged=old.copy()
    unchanged[18+rank*2:20+rank*2]=new[18+rank*2:20+rank*2]
    unchanged[40:42]=new[40:42]
    assert unchanged==new
    original_tile,original_palette=struct.unpack_from('<2H',source,0x77407c+4*rank)
    base=0x2d9360;cardpal=colors(source,base+original_palette)
    vram=read('vram');palette=struct.unpack('<512H',read('palette'));oam=read('oam')
    assert palette[240:256]==cardpal
    with Image.open(folder/(prefix+'150.png')) as raw:
        picture=raw.convert('RGB')
    assert picture.size==(240,160)
    card_ink=0
    for i in range(28):
        cell=struct.unpack_from('<H',vram,0xf800+64*(5+i//7)+2*(i%7))[0]
        tiles=tile(source,base+original_tile+32*i)
        assert cell&1023==0x32a+i and cell>>12==15
        assert vram[32*(cell&1023):32*(cell&1023)+32]==gba_tile(tiles)
        card_ink+=pixels(picture,92+i%7*8,48+i//7*8,tiles,cardpal)
    orig_sprite,orig_layout,orig_pal,which=(0x3c6fc0,0x3d5340,0x3d8726,0) if acquired else (0x3a0000,0x3cb870,0x3d7eb6,15)
    expected=layout_frames(source,orig_layout)[which]
    objpal=colors(source,orig_pal)
    assert palette[288:304]==objpal
    active=[v for v in struct.iter_unpack('<4H',oam) if v[0]&0x300!=0x200]
    assert len(active)==len(expected)
    obj_ink=0
    for (word,dx,dy),(a0,a1,a2,_) in zip(expected,active):
        x,y=120+dx,98+dy
        assert (a0&255,a1&511,a2>>12)==(y,x,2)
        assert (a1>>12)&3==(word>>14)&3
        at=0x10000+32*(a2&1023)
        tiles=tile(source,orig_sprite+(word&511)*32)
        assert vram[at:at+32]==gba_tile(tiles)
        obj_ink+=pixels(picture,x,y,tiles,objpal,bool(word&0x4000),bool(word&0x8000))
    return dict(player=player,rank=rank,kind='obtained' if acquired else 'lost',physical_score_change=count(new)-count(old),
                entered=entered,returned_to_select=done,actual_card_pixels=card_ink,actual_sprite_pixels=obj_ink,
                visible_objects=len(active),audio_dispatches=sounds,physical_save_sha256=sha((folder/f'player{player}.sav').read_bytes()),
                screen_sha256=sha((folder/(prefix+'150.png')).read_bytes()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','capture','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--image-sha256',required=True)
    parser.add_argument('--audio-installed',action='store_true')
    a=parser.parse_args();source=a.source.read_bytes()
    assert sha(source)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    launch=json.loads((a.capture/'launch.json').read_bytes())
    assert not launch['visible'] and not launch['guest_writes'] and launch['card_screens']
    assert launch['rom_sha256']==a.image_sha256 and all(sha((a.capture/f'player{i}.gba').read_bytes())==a.image_sha256 for i in (1,2))
    if a.audio_installed:assert launch['finished']==[True,True]
    rows=[inspect(source,a.capture,i,a.audio_installed) for i in (1,2)]
    assert sorted(row['kind'] for row in rows)==['lost','obtained'] and rows[0]['rank']==rows[1]['rank']
    result=dict(status='SOURCE_MODE24_PAIRED_CARDS_PASS',image_sha256=a.image_sha256,players=rows,host_completion_flags=launch['finished'],
                checker_sha256=sha(Path(__file__).read_bytes()))
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
