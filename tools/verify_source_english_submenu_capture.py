"""Read the captured English title tree and compare its visible ink with both source banks."""
import argparse
import json
from PIL import Image
from pathlib import Path
import struct
from verify_source_english_submenus import BASE, OUTPUT, SOURCE, USA, decode, sha
from verify_title_portrait_live_frames import color,frame


def check(directory,name,expected_events,original):
    if name=='english-shoot-selected':
        def load(s):return (directory/(name+'-'+s+'.bin')).read_bytes()
        png=Image.open(directory/(name+'.png')).convert('RGB')
        ram,vram,objects=load('IWRAM'),load('VRAM'),load('OAM')
        palette=struct.unpack('<512H',load('PALRAM'))
    else:
        png,ram,vram,palette,objects=frame(directory,name)
    count=0
    pixels=0
    assert ram[0x112f]==(0x20 if name=='english-shoot-selected' else 0xa0) and struct.unpack_from('<H',ram,0x2310)[0]==3
    for row,expected in enumerate(expected_events):
        x,y=struct.unpack_from('<hh',ram,0x2a78+row*80)
        event=struct.unpack_from('<H',ram,0x2a86+row*80)[0]
        assert event==expected and struct.unpack_from('<I',ram,0x2ac0+row*80)[0]==0x08E9A820
        source=original[event]
        parts=8 if event==0 else 22
        actual={}
        for i in range(parts):
            a0,a1,a2=struct.unpack_from('<3H',objects,8*count)
            assert a0&0x300==0 and a0&0xE000==0 and a1&0xC000==0
            tile=(a2&1023)*32+0x10000
            for yy in range(8):
                for xx in range(8):
                    tx,ty=(7-xx if a1&0x1000 else xx),(7-yy if a1&0x2000 else yy)
                    c=vram[tile+(ty*4)+tx//2]>>(4*(tx%2))&15
                    if not c:continue
                    pos=((a1&511)+xx,(a0&255)+yy)
                    assert 0<=pos[0]<240 and 0<=pos[1]<160
                    actual.setdefault((pos[0]-x-8,pos[1]-y-8),c)
                    assert png.getpixel(pos)==color(palette[256+(a2>>12)*16+c])
            count+=1
        assert actual==source
        pixels+=len(actual)
    assert count==struct.unpack_from('<H',ram,0x12d6)[0]
    return dict(events=expected_events,parts=count,pixels=pixels)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('usa','source','capture','report'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--unlocked',type=Path)
    a=p.parse_args()
    usa,source=a.usa.read_bytes(),a.source.read_bytes()
    assert (sha(usa),sha(source))==(USA,SOURCE)
    originals=decode(usa,0x8fd08,5)+decode(source,0x3c43d0,11,True)[5:]
    launch=json.loads((a.capture/'launch.json').read_bytes())
    assert launch['outcome']=='ordinary-language-title-portrait-complete' and launch['rom_sha256']==OUTPUT
    assert sha((a.capture/'loaded-rom.bin').read_bytes())==OUTPUT
    assert not launch['visible'] and not launch['guest_writes'] and not launch['supplied_save_used']
    assert launch['script_unchanged'] and launch['loaded_rom_exact']
    for f,s in launch['files'].items():assert sha((a.capture/f).read_bytes())==s
    result={n:check(a.capture,n,events,originals)for n,events in (
        ('prompt',[0]),('root',[1,2,3,4,5]),('versus-visible',[6,7]),('collection-visible',[10,10]))}
    if a.unlocked:
        assert sha((a.unlocked/'loaded-rom.bin').read_bytes())==OUTPUT
        result['collection-earned']=check(a.unlocked,'english-shoot-selected',[10,9],originals)
    report=dict(status='PASS',rom=OUTPUT,live=result,checker=sha(Path(__file__).read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS',sha(a.report.read_bytes()))


if __name__=='__main__':main()
