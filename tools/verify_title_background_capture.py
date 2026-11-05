#!/usr/bin/env python3
"""Read-only verification of a completed ordinary-input title capture."""
import argparse,json,struct
from pathlib import Path
from verify_title_background import sha,need,TILE_A,TILE_B,MAP,PAL

def main():
    p=argparse.ArgumentParser()
    for name in ('rom','capture','output'):p.add_argument(name,type=Path)
    p.add_argument('--title-label',default='title');p.add_argument('--selection-label',default='selection')
    a=p.parse_args();need(not a.output.exists(),'preserve previous reports')
    rom=a.rom.read_bytes();launch=json.loads((a.capture/'launch.json').read_text(encoding='utf-8'))
    need(sha(rom)==launch['rom_sha256'],'captured exact ROM')
    need(launch['completed'] and not launch['visible'] and launch['guest_writes']==[],'completed hidden ordinary-input capture')
    for name,digest in launch['files'].items():need(sha((a.capture/name).read_bytes())==digest,'capture manifest '+name)
    need((a.capture/'loaded-rom.bin').read_bytes()==rom,'actual loaded ROM full identity')
    def read(suffix):return (a.capture/(a.title_label+'-'+suffix+'.bin')).read_bytes()
    iw,ew,vr,pa,display=(read(n) for n in ('iwram','ewram','vram','palette','display'))
    half=lambda data,at:struct.unpack_from('<H',data,at)[0]
    need(half(iw,0x2310)==3,'actual title mode3')
    selection=(a.capture/(a.selection_label+'-iwram.bin')).read_bytes()
    need(half(selection,0x2310)==4,'actual subsequent character-selection mode4')
    tiles=rom[TILE_A:TILE_A+8192]+rom[TILE_B:TILE_B+4864]
    need(vr[0x3200:0x6500]==tiles,'all408 live VRAM tiles')
    for row in range(18):need(vr[0xF000+row*64:0xF000+row*64+56]==rom[MAP+row*56:MAP+row*56+56],'live28cell map row')
    need(ew[0x1E400:0x1E500]==rom[PAL:PAL+256],'full palette source staging')
    # Native0914E4 decrements, then exits without painting at current<=target.
    # The last painted numerator is therefore target+1, not the final stored current.
    current,target,denominator,unused,flags=struct.unpack_from('<5H',iw,0x2C08)
    need((current,target,denominator,flags)==(2,2,5,0),'settled native menu dim state')
    original=struct.unpack_from('<128H',ew,0x1E400);destination=struct.unpack_from('<128H',ew,0x1E800)
    need(destination==(0,)*128,'native fade target is black')
    expected=tuple(sum((((x>>shift)&31)*(target+1)//denominator)<<shift for shift in (0,5,10)) for x in original)
    need(struct.unpack_from('<128H',pa,0x20)==expected,'all128 live palette entries match completed3/5 menu dim')
    control,bg1=half(display,0),half(display,0xA)
    need(control&7==0 and control&0x200 and not control&0x80,'active textBG1 in mode0 without forcedblank')
    need(bg1&0xC08C==0 and (bg1>>8)&31==30,'BG1 4bpp charbase0 screenbaseF000 32x32')
    report={'status':'PASS_CAPTURE','rom_sha256':sha(rom),'launch_sha256':sha((a.capture/'launch.json').read_bytes()),
            'semantic_labels':{a.title_label:'settled title menu, mode3',a.selection_label:'character selection, mode4'},
            'title_mode':3,'selection_mode':4,'live_tiles':408,'live_map_cells':504,'live_palette_entries':128,
            'palette_source_staging_exact':True,'completed_menu_dim':{'stored_counter':current,'target':target,'last_painted_numerator':target+1,'denominator':denominator},
            'display':{'DISPCNT':control,'BG1CNT':bg1},'checked_capture_files':launch['files'],
            'limitations':['A captured ordinary-input title/selection path, not whole-game or hardware certification.','Scroll registers read as open-bus values in these dumps; no scroll-value proof is claimed.']}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'report_sha256':sha(a.output.read_bytes())}))

if __name__=='__main__':main()
