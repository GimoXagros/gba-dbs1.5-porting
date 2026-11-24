"""Compare the five unforced opening paths and a separate cold Start skip on the two platforms."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from PIL import Image, ImageDraw


def sha(b):return hashlib.sha256(b).hexdigest().upper()


def read_route(folder,ws,skip):
    meta=json.loads((folder/'launch.json').read_bytes())
    rom=(folder/'loaded-rom.bin').read_bytes()
    assert meta['status']=='title' and meta['loaded_rom_exact'] and meta['rom_sha256']==sha(rom)
    assert not meta['visible'] and not meta['guest_writes'] and not meta['supplied_save'] and meta['skip']==skip
    trace=(folder/'trace.txt').read_bytes();assert sha(trace)==meta['trace_sha256']
    owner='RAM@C234' if ws else 'EWRAM@10118'
    cycle=None;routes=[];start=None
    for line in trace.decode().splitlines():
        m=re.fullmatch(r'mode frame=(\d+) id=(\d+) choice=(\d+)',line)
        if m:
            frame,mode,state=map(int,m.groups())
            if mode==2:
                assert cycle is None
                cycle={'mode_entry':frame,'choice_before':state,'callbacks':[]}
            elif mode==3 and cycle:
                cycle.update(title=frame,choice_after=state)
                routes.append(cycle);cycle=None
        m=re.fullmatch(r'callback frame=(\d+) id=(\d+) state=(\d+) mode=(\d+) owner=(\S+)',line)
        if m:
            f,c,s,mode,slot=m.groups()
            if cycle is None:continue
            assert slot==owner and int(mode)==2
            cycle['callbacks'].append((int(c),int(f)))
        if line.startswith('Start frame='):
            f,c=map(int,re.findall(r'\d+',line));assert c==8 and start is None;start=f
    ordered=[19,20,21,23,22]
    assert len(routes)==(1 if skip else 5)
    for i,route in enumerate(routes):
        ids=[c for c,_ in route['callbacks']]
        expected=list(range(9))+[25,24] if skip else list(range(19))+[ordered[i],24]
        assert ids==expected,(folder,i,ids)
        assert route['choice_before']==i and route['choice_after']==(i if skip else (i+1)%5)
        assert route['title']>route['callbacks'][-1][1]
        for c,f in route['callbacks']:
            if c!=25:assert (folder/f'frame-{f+8:05d}-step{c:02d}.png').is_file()
        assert (folder/f'frame-{route["title"]:05d}-step26.png').is_file()
    if skip:
        assert start and start==routes[0]['callbacks'][8][1]+15
    return dict(rom_sha256=sha(rom),trace_sha256=sha(trace),routes=routes,start_input=start,
                start_to_title_frames=routes[0]['title']-start if skip else None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('gba-full','gba-skip','wsc-full','wsc-skip','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();summary={};frames={}
    for platform in ('wsc','gba'):
        for mode in ('full','skip'):
            folder=getattr(a,f'{platform}_{mode}')
            r=read_route(folder,platform=='wsc',mode=='skip')
            summary[f'{platform}_{mode}']=r
            if mode=='full':
                for route in r['routes']:
                    c,f=route['callbacks'][-2];frames[platform,c]=folder/f'frame-{f+8:05d}-step{c:02d}.png'
    a.output.mkdir(parents=True,exist_ok=False)
    sheet=Image.new('RGB',(5*248,2*188),'#26282c');draw=ImageDraw.Draw(sheet)
    for row,platform in enumerate(('wsc','gba')):
        for i,c in enumerate((19,20,21,23,22)):
            with Image.open(frames[platform,c]) as pic:
                pic=pic.convert('RGB')
                assert pic.width in (224,240) and pic.height in (144,160)
                x=i*248+4+(240-pic.width)//2;y=row*188+21+(160-pic.height)//2
                sheet.paste(pic,(x,y))
            draw.text((i*248+5,row*188+3),f'{platform.upper()}   choice {i}',fill='white')
    sheet.save(a.output/'opening-choices.png')
    summary.update(status='COLD_OPENING_FIVE_CHOICES_AND_START_SKIP_PASS',static_expected_linear_callbacks=19,
                   source_gba_choice_identity=['5+7','1+8','0+9','13+14','12+11'],
                   capture_scope='Task transitions, title entry, representative screens and Start skip; no PCM acquisition.')
    dst=a.output/'verified.json'
    dst.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8',newline='\n')
    print(summary['status'],sha(dst.read_bytes()))


if __name__=='__main__':main()
