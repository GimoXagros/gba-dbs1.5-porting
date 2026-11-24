"""Native-size deterministic pixel previews of prepared title assets, not screenshots."""
import argparse,json,struct,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from build_title_language import native_pixels
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--assets-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();assert not a.output_dir.exists()
 b=(a.assets_dir/'assets.bin').read_bytes();m=json.loads((a.assets_dir/'manifest.json').read_text(encoding='utf-8'));base=m['base_address']
 p2=next(o['offset']for o in m['objects']if o['label']=='p2')
 palette=[(40,40,48)]+[tuple(((w>>shift)&31)*255//31 for shift in(0,5,10))for w in struct.unpack_from('<15H',b,p2+8)]
 sheet=Image.new('RGB',(896,440),(40,40,48));roots=Image.new('RGB',(896,164),(40,40,48));draw=ImageDraw.Draw(sheet);rootdraw=ImageDraw.Draw(roots)
 for column,(lang,row)in enumerate(m['languages'].items()):
  raw=row['address']-base;table,desc=struct.unpack_from('<II',b,raw);table-=base;desc-=base;n,pixels=struct.unpack_from('<II',b,desc);pixels-=base;tiles=[b[i:i+32]for i in range(pixels,pixels+n,32)]
  for event in range(11):
   count,at=struct.unpack_from('<II',b,table+8*event);at-=base;parts=[struct.unpack_from('<Hbb',b,at+4*i)for i in range(count)];image=native_pixels(parts,tiles)
   draw.text((column*224+3,event*40+2),f'{lang} event {event} ({count} parts)',fill=(180,180,180))
   for(x,y),v in image.items():sheet.putpixel((column*224+112+x,event*40+25+y),palette[v])
   if 1<=event<=5:
    y0=(32,50,68,88,106)[event-1]
    for(x,y),v in image.items():roots.putpixel((column*224+112+x,20+y0+y),palette[v])
  rootdraw.text((column*224+3,2),f"{lang}: 5 rows / {row['root_parts']} parts",fill=(180,180,180))
 a.output_dir.mkdir(parents=True);sheet.save(a.output_dir/'contact-sheet.png');roots.save(a.output_dir/'root-menus.png')
 report={'status':'DETERMINISTIC_NATIVE_PIXEL_PREVIEWS_NOT_GAME_CAPTURE','assets_sha256':hashlib.sha256(b).hexdigest().upper(),'scale':1,'files':{name:hashlib.sha256((a.output_dir/name).read_bytes()).hexdigest().upper()for name in('contact-sheet.png','root-menus.png')},'limits':['No background image, selection highlight animation or physical screen capture','Source extra E6 counter text task is absent in this interim native controller; adding any overlay requires a new aggregate OAM check']}
 (a.output_dir/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'])
if __name__=='__main__':main()
