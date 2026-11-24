"""Render the 15 installed selection portraits with their four installed headers."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build_character_select_name_assets import BASE, EN, JA, KO, unpack, sha
from build_character_select_name_scene_r3 import ASSETS
from verify_title_portrait_live_frames import color

def render(rom, assets, owner, font, captures=None):
    assert sha(assets) == ASSETS
    entries = json.loads(assets)['entries']
    table, end = owner['table_span']
    assert end - table == 60 * 4
    pointers = struct.unpack_from('<60I', rom, table)
    assert list(pointers) == owner['header_pointers']
    reports=[]
    for lang,folder in enumerate(captures or []):
        report=json.loads((folder/'launch.json').read_bytes())
        assert report['language']==lang and report['outcome']=='PASS' and report['rom_sha256']==sha(rom)
        assert report['loaded_rom_exact'] and report['guest_writes']==[] and not report['visible']
        assert report['copied_campaign_eeprom']=='AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D'
        reports.append(report)
    small, large = (ImageFont.truetype(str(font), n) for n in (20, 30))
    pitch, left, step = 231, 114, 278
    canvas = Image.new('RGB', (left + 4*pitch + 20, 110+15*step), '#171922')
    draw = ImageDraw.Draw(canvas)
    draw.text((20,14), '캐릭터 선택  /  초상화와 이름', font=large, fill='white')
    for lang, title in enumerate(('영어', '일본어', '한국어', '디지코드')):
        draw.text((left+lang*pitch,65), title, font=small, fill='#ffdb88')
    for i in range(15):
        y = 105 + i*step
        draw.text((18,y+4), f'ID {i:02d}', font=small, fill='#abb6c9')
        draw.text((18,y+39), KO[i], font=small, fill='white')
        palette, tiles = (v-BASE for v in struct.unpack_from('<II',rom,0x4A5BC0+8*i))
        colors = [color(v) for v in struct.unpack_from('<16H',rom,palette)]
        for lang in range(4):
            j = lang*15+i
            row = entries[j]
            assert (row['id'],row['native_palette_raw'],row['native_tiles_raw'])==(i,palette,tiles)
            if lang < 3: assert row['label']==(EN,JA,KO)[lang][i]
            at = pointers[j]-BASE
            header, body = rom[at:at+768], rom[tiles+768:tiles+6144]
            assert sha(header)==row['sha256'] and sha(body)==row['native_body_sha256']
            grid = unpack(header+body,height=128)
            im = Image.new('RGB',(96,128))
            im.putdata([colors[p] for r in grid for p in r])
            if captures:
                folder=captures[lang]
                name=f'fighter-{i:02d}'
                for suffix,want in (('-tiles.bin',header+body),('-palette.bin',rom[palette:palette+32])):
                    got=(folder/(name+suffix)).read_bytes()
                    assert got==want and sha(got)==reports[lang]['files'][name+suffix],(lang,i,suffix)
                assert sha((folder/(name+'.png')).read_bytes())==reports[lang]['files'][name+'.png']
                actual=Image.open(folder/(name+'.png')).convert('RGB').crop((124,16,220,144))
                assert actual.tobytes()==im.tobytes(),(lang,i,'physical frame')
                im=actual
            canvas.paste(im.resize((192,256),Image.Resampling.NEAREST),(left+lang*pitch,y))
    return canvas

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('rom','assets','owner','font','output'): p.add_argument('--'+arg,required=True,type=Path)
    p.add_argument('--captures',nargs=4,type=Path)
    a=p.parse_args()
    sheet=render(a.rom.read_bytes(),a.assets.read_bytes(),json.loads(a.owner.read_bytes()),a.font,a.captures)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    sheet.save(a.output)
    print('PASS 15 x 4',sheet.size,sha(a.output.read_bytes()))
