"""Cold boot a copy of the genuine linked winner's EEPROM and check the title and named tag."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import time
from PIL import Image
from mgba_headless_gdb_capture import PrivateDesktopProcess
from run_link_tag_capture import EXE
from verify_title_tag_badge_capture import check
from verify_mode24_link_capture import colors, gba_tile, pixels, tile
from verify_link_tag_capture import eeprom
from verify_mode22_viewer_scene import maps


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','image','save','emulator','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    assert Path('W:/').samefile(root)
    alias=Path('W:/')/out.relative_to(root)
    image=a.image.read_bytes();source=a.source.read_bytes()
    before=a.save.read_bytes()
    _,snap=eeprom(a.save)
    assert len(image)==0x1000000 and len(before)==512 and snap[14:18]==b'AAA\0'
    assert digest(a.emulator.read_bytes())==EXE
    for original,name in ((a.image,'winner.gba'),(a.save,'winner.sav'),(a.emulator,'mGBA.exe')):
        shutil.copyfile(original,out/name)
    (out/'portable.ini').touch()
    (out/'config.ini').write_text('[ports.qt]\naudioSync=0\nvideoSync=0\nmute=1\nvolume=0\n',encoding='ascii')
    (out/'qt.ini').write_text('[General]\nfirstRun=false\n',encoding='ascii')
    script=Path(__file__).with_name('mgba_link_reward_cold.lua')
    raw=script.read_text(encoding='utf8').replace('@@OUTPUT@@',alias.as_posix())
    (out/'probe.lua').write_text(raw,encoding='utf8',newline='\n')
    with PrivateDesktopProcess(out/'mGBA.exe',['--script',str(alias/'probe.lua'),str(alias/'winner.gba')],out):
        deadline=time.monotonic()+120
        while not (out/'finished.txt').exists() and time.monotonic()<deadline:
            time.sleep(.25)
    outcome=(out/'finished.txt').read_text()
    report=dict(outcome=outcome,loaded_rom_exact=(out/'winner.gba').read_bytes()==image,
                rom_sha256=digest(image),script_unchanged=(out/'probe.lua').read_text(encoding='utf8')==raw,
                guest_writes=[],visible=False,copied_campaign_eeprom=digest(before),
                files={i.name:digest(i.read_bytes()) for i in out.iterdir() if i.suffix in ('.bin','.png')})
    (out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    assert a.save.read_bytes()==before and (out/'winner.sav').read_bytes()==before
    title=check(source,before,out)
    vram=(out/'tag-vram.bin').read_bytes()
    assert vram[0xf000:0x10000]==maps(source,snap,4,10)
    oam=(out/'tag-oam.bin').read_bytes()
    objs=[a for a in struct.iter_unpack('<4H',oam) if a[0]&0x300!=0x200]
    assert len(objs)==3
    font=tile(source,0x43e9c0+(ord('A')-32)*32)
    paldata=(out/'tag-palette.bin').read_bytes()
    actual_palette=struct.unpack_from('<16H',paldata,0x300)
    ink=0
    with Image.open(out/'tag.png') as pic:
        screen=pic.convert('RGB')
        for i,(a0,a1,a2,_) in enumerate(objs):
            assert (a0,a1,a2)==(70,108+8*i,0x8400+i)
            start=0x10000+(a2&1023)*32
            assert vram[start:start+32]==gba_tile(font)
            ink+=pixels(screen,a1,a0,font,actual_palette)
    result=dict(status='COLD_LINK_REWARD_TITLE_AND_NAMED_TAG_PASS',image_sha256=digest(image),
                eeprom_sha256=digest(before),title=title,viewer_name='AAA',viewer_name_pixels=ink,
                viewer_map_bytes=4096,screens=report['files'])
    dst=out/'verified.json';dst.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(result['status'],digest(dst.read_bytes()))


if __name__=='__main__':
    main()
