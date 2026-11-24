"""Native-size and integer4x Start-prompt comparison, not a game screenshot."""
import argparse,json,struct
from pathlib import Path
from PIL import Image,ImageDraw
from build_title_language import native_pixels

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('before','after','output_dir'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 image=Image.new('RGB',(896,112),(40,40,48));draw=ImageDraw.Draw(image)
 for row,folder in enumerate((a.before,a.after)):
  data=(folder/'assets.bin').read_bytes();meta=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));base=meta['base_address']
  paloff=next(x['offset']for x in meta['objects']if x['label']=='p2')
  palette=[(40,40,48)]+[tuple(((w>>shift)&31)*255//31 for shift in(0,5,10))for w in struct.unpack_from('<15H',data,paloff+8)]
  for col,(lang,view)in enumerate(meta['languages'].items()):
   table,desc=struct.unpack_from('<II',data,view['address']-base);size,ptr=struct.unpack_from('<II',data,desc-base);count,layout=struct.unpack_from('<II',data,table-base)
   tiles=[data[i:i+32]for i in range(ptr-base,ptr-base+size,32)];pixels=native_pixels([struct.unpack_from('<Hbb',data,layout-base+i*4)for i in range(count)],tiles)
   draw.text((col*224+4,row*56+3),f'{lang} / '+('before'if row==0 else'after'),fill=(185,185,185))
   for(x,y),value in pixels.items():image.putpixel((col*224+112+x,row*56+35+y),palette[value])
 a.output_dir.mkdir(parents=True);image.save(a.output_dir/'prompts-native.png');image.resize((image.width*4,image.height*4),Image.Resampling.NEAREST).save(a.output_dir/'prompts-4x.png')
 print(a.output_dir)
if __name__=='__main__':main()
