"""Render the 15 installed selection portraits with their four installed headers."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from build_character_select_name_assets import BASE, EN, JA, KO, unpack, sha
from build_character_select_name_scene_r3 import ASSETS
from verify_title_portrait_live_frames import color

def render(rom, assets, owner, font):
    assert sha(assets) == ASSETS
    entries = json.loads(assets)['entries']
    table, end = owner['table_span']
    assert end - table == 60 * 4
    pointers = struct.unpack_from('<60I', rom, table)
    assert list(pointers) == owner['header_pointers']
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
            canvas.paste(im.resize((192,256),Image.Resampling.NEAREST),(left+lang*pitch,y))
    return canvas

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('rom','assets','owner','font','output'): p.add_argument('--'+arg,required=True,type=Path)
    a=p.parse_args()
    sheet=render(a.rom.read_bytes(),a.assets.read_bytes(),json.loads(a.owner.read_bytes()),a.font)
    a.output.parent.mkdir(exist_ok=True,parents=True)
    sheet.save(a.output)
    print('PASS 15 x 4',sheet.size,sha(a.output.read_bytes()))
