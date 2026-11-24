"""Compare the real Korean title credit before and after the seven-pixel font change."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
from build_character_select_name_scene import sha

def shot(folder):
    report=json.loads((folder/'launch.json').read_bytes())
    raw=(folder/'title.png').read_bytes()
    assert report['outcome']=='PASS' and report['loaded_rom_exact'] and not report['visible']
    assert sha(raw)==report['files']['title.png']
    return Image.open(folder/'title.png').convert('RGB')

def draw_review(before,after,en,ja,font):
    old,new=shot(before),shot(after)
    changes=ImageChops.difference(old,new).getbbox()
    assert changes and 60<=changes[0]<changes[2]<=200 and 127<=changes[1]<changes[3]<=141,changes
    def bounds(frame):
        ink=[(x,y) for y in range(128,140) for x in range(61,208) if frame.getpixel((x,y))==(255,255,255)]
        return (max(x for x,y in ink)-min(x for x,y in ink)+1,max(y for x,y in ink)-min(y for x,y in ink)+1)
    shots=[old,new,shot(en),shot(ja)]
    geometry=[bounds(im) for im in shots]
    assert [h for _,h in geometry]==[11,7,7,8],geometry
    sheet=Image.new('RGB',(812,4*154+20),'#171922')
    pen=ImageDraw.Draw(sheet)
    face=ImageFont.truetype(str(font),20)
    for i,(pic,label,(width,height)) in enumerate(zip(shots,
            ('수정 전 · 한국어','수정 후 · 한국어','원더스완 영문 표기','일본어 원본 표기'),geometry)):
        y=12+154*i
        pen.text((14,y),f'{label}  /  글자 높이 {height}px',font=face,fill='#fee09b' if i==1 else '#d8deeb')
        crop=pic.crop((24,124,220,154))
        sheet.paste(crop.resize((784,120),Image.Resampling.NEAREST),(14,y+28))
    return sheet,geometry,changes

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('before','after','en','ja','font','output'): p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    sheet,geometry,changes=draw_review(a.before,a.after,a.en,a.ja,a.font)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(a.output)
    print('PASS',geometry,changes,sha(a.output.read_bytes()))
