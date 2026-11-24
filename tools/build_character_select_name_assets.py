"""Build four-language 96x16 portrait headers; no ROM writes or allocation."""
import argparse, hashlib, json, struct
from pathlib import Path
from build_full_asset_poc import convert_tile
from build_options_korean_poc import FONT_SHA, LICENSE_SHA, font_glyphs, text_pixels
from digicode_glyphs import font_glyphs as dg_font, text_pixels as dg_pixels
from encode_digicode_reading import CATALOG, encode

SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
JA=('ギルモン','テリアモン','レナモン','ブイモン','ワームモン','アグモン','スカモン','アグモン','ロップモン','ガブモン','アグモン','インプモン','ギルモン','パタモン','テイルモン')
EN=('GUILMON','TERRIERMON','RENAMON','VEEMON','WORMMON','AGUMON','SUKAMON','AGUMON','LOPMON','GABUMON','AGUMON','IMPMON','GUILMON','PATAMON','GATOMON')
KO=('길몬','테리어몬','레나몬','브이몬','추추몬','아구몬','스카몬','아구몬','로프몬','파피몬','아구몬','임프몬','길몬','파닥몬','가트몬')
SOURCE_TILES=(0x424A90,0x427AD0,0x42AAF0,0x460020,0x463040,0x466060,0x450020,0x453040,0x456060,0x440020,0x443040,0x446060,0x449080,0x469080,0x459080)
# Background, text ink and English shadow in the retained native palette.
COLORS=((15,8,7),(15,11,8),(14,15,5),(15,4,6),(15,10,9),(15,2,5),(13,11,12),(14,15,4),(15,14,2),(1,2,11),(3,15,6),(6,14,2),(4,1,2),(1,15,12),(3,1,2))
BASE=0x08000000
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def unpack(b,height=16):
 assert len(b)==96*height//2
 return [[(b[(y//8*12+x//8)*32+y%8*4+x%8//2]>>(4*(x%2)))&15 for x in range(96)]for y in range(height)]
def pack(p):
 return bytes(p[ty+y][tx+x]|p[ty+y][tx+x+1]<<4 for ty in range(0,len(p),8)for tx in range(0,96,8)for y in range(8)for x in range(0,8,2))
def protected(i,x,y):return y==0 or x<=(6 if i==1 else 12) or x>=(89 if i==1 else 83)
def source_header(source,i,english):
 at=SOURCE_TILES[i]+(0x1800 if english else 0)
 return unpack(b''.join(convert_tile(source[p:p+32])for p in range(at,at+768,32)))

def build(source,native,font,license_data):
 assert tuple(map(sha,(source,native,font,license_data)))==(SOURCE,NATIVE,FONT_SHA,LICENSE_SHA)
 catalog=json.loads(CATALOG.read_text(encoding='utf-8'));dg=dg_font(catalog)
 ko=font_glyphs(font,set(''.join(KO)));rows=[];headers=[]
 for lang in range(4):
  for i in range(15):
   pal,tiles=struct.unpack_from('<II',native,0x4A5BC0+i*8);pal-=BASE;tiles-=BASE
   old=unpack(native[tiles:tiles+768]);bg,ink,shade=COLORS[i]
   assert old[1][48]==bg
   out=[[old[y][x]if protected(i,x,y)else bg for x in range(96)]for y in range(16)]
   info={}
   if lang<2:
    src=source_header(source,i,lang==0)
    src_bg=src[1][48];edge=6 if src[1][10]==src_bg else 12
    glyph={(x,y):src[y][x]for y in range(1,16)for x in range(edge+1,95-edge)if src[y][x]!=src_bg}
    assert glyph and all(not protected(i,x,y)for x,y in glyph)
    if i==11:
     assert set(glyph.values())=={2,3};glyph={p:{2:14,3:2}[v]for p,v in glyph.items()}
    for(x,y),v in glyph.items():out[y][x]=v
    info={'source_header_raw':SOURCE_TILES[i]+(0x1800 if lang==0 else 0),'source_glyph_pixels':len(glyph),'source_border_width':edge,'index_remap':{'2':14,'3':2}if i==11 else {}}
    label=(EN,JA)[lang][i]
   else:
    label=KO[i]if lang==2 else JA[i].replace('ッ','ツ')
    points,width=(text_pixels(label,ko)if lang==2 else dg_pixels(label,catalog,dg,outline=False))
    # Center complete glyph bounds; no scaling, clipping or voiced-mark removal.
    y0=min(y for x,y in points);y1=max(y for x,y in points);height=y1-y0+1
    assert width<=70 and height<=15
    left=(96-width)//2;top=1+(15-height)//2
    glyph={(left+x,top+y-y0):(ink if v==1 else shade)for(x,y),v in points.items()}
    assert all(not protected(i,x,y)for x,y in glyph)
    for(x,y),v in glyph.items():out[y][x]=v
    info={'width':width,'height':height,'left':left,'top':top,'pixels':len(glyph),'unscaled_glyphs':True}
    if lang==3:info.update(reading=label,glyph_ids=encode(label,catalog),outline=False,small_kana_normalization={'ッ':'ツ'}if 'ッ'in JA[i]else {})
   assert all(out[y][x]==old[y][x]for y in range(16)for x in range(96)if protected(i,x,y))
   blob=pack(out);headers.append(blob)
   rows.append(dict(language=('en','ja','ko','dg')[lang],id=i,label=label,file=f'{lang}-{i:02d}.bin',sha256=sha(blob),bytes=len(blob),native_palette_raw=pal,native_tiles_raw=tiles,native_body_sha256=sha(native[tiles+768:tiles+6144]),protected_pixels=sum(protected(i,x,y)for y in range(16)for x in range(96)),colors=dict(background=bg,ink=ink,shadow=shade),**info))
 return headers,rows

def previews(native,headers,rows,outdir):
 from PIL import Image,ImageDraw
 sheet=Image.new('RGB',(4*104+24,15*24+20),(32,32,32));draw=ImageDraw.Draw(sheet)
 for lang,name in enumerate(('EN','JA','KO','DG')):draw.text((24+lang*104,1),name,fill='white')
 for i in range(15):
  draw.text((0,20+i*24),str(i),fill='white')
  for lang in range(4):
   index=lang*15+i;row=rows[index];p=unpack(headers[index]);pal=struct.unpack_from('<16H',native,row['native_palette_raw'])
   colors=[tuple(((c>>shift)&31)*255//31 for shift in(0,5,10))for c in pal]
   im=Image.new('RGB',(96,16));im.putdata([colors[v]for r in p for v in r]);sheet.paste(im,(24+lang*104,20+i*24))
   body=native[row['native_tiles_raw']+768:row['native_tiles_raw']+6144]
   full=unpack(headers[index]+body,128);portrait=Image.new('RGB',(96,128));portrait.putdata([colors[v]for r in full for v in r]);portrait.save(outdir/f'portrait-{row["language"]}-{i:02d}.png')
 sheet.save(outdir/'headers-native.png');sheet.resize((sheet.width*3,sheet.height*3),Image.Resampling.NEAREST).save(outdir/'headers-3x.png')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in('source','native','font','license','output-dir'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists();a.output_dir.mkdir(parents=True)
 inputs=[getattr(a,k).read_bytes()for k in('source','native','font','license')];headers,rows=build(*inputs)
 for b,row in zip(headers,rows):(a.output_dir/row['file']).write_bytes(b)
 (a.output_dir/'headers.bin').write_bytes(b''.join(headers));previews(inputs[1],headers,rows,a.output_dir)
 result=dict(schema=1,status='standalone-assets-not-installed',source_sha256=sha(inputs[0]),native_sha256=sha(inputs[1]),font_sha256=sha(inputs[2]),license_sha256=sha(inputs[3]),builder_sha256=sha(Path(__file__).read_bytes()),catalog_sha256=sha(CATALOG.read_bytes()),digicode_glyph_tool_sha256=sha(Path(__file__).with_name('digicode_glyphs.py').read_bytes()),header_size=768,atlas_size=6144,headers_sha256=sha(b''.join(headers)),entries=rows,new_OAM=0,new_persistent_RAM=0,palette_writes=0,scope='Only 96x16 header. Native border indices and all 96x112 portrait pixels below retained. Source glyph geometry preserved; ID11 ink/shadow remapped to existing native palette.',limits=['No ROM allocation, integration, emulator or four-language live capture claimed.','Korean labels approved canonical names; Digicode uses existing chart transcription and explicit small-tsu normalization.'])
 (a.output_dir/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS',sha((a.output_dir/'manifest.json').read_bytes()))
if __name__=='__main__':main()
