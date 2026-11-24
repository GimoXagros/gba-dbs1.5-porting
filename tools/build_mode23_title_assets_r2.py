"""Prepare eleven source title events in four languages; no ROM installation.

Revision 2 keeps full Digicode ink in open sixteen-row panels with clear
spacing. Added English labels use retail seven-row bold letterforms plus
explicitly documented extensions. No ROM or controller is installed.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from build_title_language import native_pixels, tile_layouts, bounds, remap_text, attach
from build_options_korean_poc import FONT_SHA, LICENSE_SHA, font_glyphs, text_pixels
from digicode_glyphs import font_glyphs as dg_glyphs, text_pixels as dg_pixels
from encode_digicode_reading import CATALOG, encode
from render_wsc_asset_frames import layout_frames
from build_full_asset_poc import convert_tile
from mode23_scene_resources import parsed_p1
from mode23_title_visual_layout import bold_glyphs, bold_text, spaced_digicode, open_digicode_panel
from build_shoot_initializer import convert_p1
from convert_wsc_palette_block import convert_block

SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
BASE=0x08000000
JA=('スタートボタンをおしてね！','ひとりでバトル','ともだちとバトル','オプション','D-ARK','コレクション','Ver.1.5とバトル','バトスピとバトル','テイマータグ','デジモンシュート','?')
EN={5:'COLLECTION',6:'BATTLE VER.1.5',7:'VS BATTLE SPIRIT',8:'TAMER TAG',9:'DIGIMON SHOOT'}
KO={5:'컬렉션',6:'Ver.1.5와 대전',7:'배틀 스피릿과 대전',8:'테이머 태그',9:'디지몬 슈트'}
DG={1:'ひとりでバトル',2:'ともだちとバトル',3:'おぷしよん',5:'これくしよん',7:'ばとすぴとばとる',8:'ていまーたぐ',9:'でじもんしゆーと'}

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,at):return struct.unpack_from('<I',b,at)[0]
def native_frames(native,raw):
 table,desc=u(native,raw)-BASE,u(native,raw+4)-BASE
 size,pixels=struct.unpack_from('<II',native,desc);pixels-=BASE
 assert size%32==0 and 0<size<=8192
 tiles=[native[p:p+32]for p in range(pixels,pixels+size,32)]
 out=[]
 for i in range(5):
  count,at=struct.unpack_from('<II',native,table+8*i);at-=BASE
  parts=[struct.unpack_from('<Hbb',native,at+j*4)for j in range(count)]
  out.append(native_pixels(parts,tiles))
 return out

def pack(parts,tiles,address):
 assert len(parts)==11 and 0<len(tiles)<=256
 out=bytearray(16+len(parts)*8)
 for i,layout in enumerate(parts):
  assert 0<len(layout)<=128
  struct.pack_into('<II',out,16+8*i,len(layout),address+len(out))
  for tile,y,x in layout:out.extend(struct.pack('<Hbb',tile,y,x))
 desc=len(out);out.extend(struct.pack('<II',len(tiles)*32,address+desc+8));out.extend(b''.join(tiles))
 # Word8=5 is the source static-atlas flag word, not the layout count.
 struct.pack_into('<IIHHHH',out,0,address+16,address+desc,5,len(tiles)-1,(len(tiles)-1)*32,8)
 return bytes(out)

def build(source,native,font,license_data,address=0x08E00000):
 assert (sha(source),sha(native),sha(font),sha(license_data))==(SOURCE,NATIVE,FONT_SHA,LICENSE_SHA)
 assert source[0x780148:0x780151]==bytes.fromhex('33c033c03d00007551')
 assert source[0x3C3FE0:0x3C3FF0]==bytes.fromhex('10000000e928bd0005008d00a0110800')
 layouts=[[(t,y,x)for t,x,y in p]for p in layout_frames(source,0x3C3FE0)]
 assert len(layouts)==11 and [len(p)for p in layouts]==[17]+[22]*10
 tiles=[convert_tile(source[p:p+32])for p in range(0x396300,0x3974C0,32)]
 japanese=[native_pixels(p,tiles)for p in layouts]
 english=native_frames(native,0x8FD08);korean=native_frames(native,0x63D000);old_dg=native_frames(native,0x63E000)
 assert native_frames(native,0x63A800)==japanese[:5]
 marker={(x,y):v for (x,y),v in japanese[1].items()if -43<=x<=-30 and -7<=y<=6}
 assert len(marker)==196
 characters=set(''.join(EN.values())+''.join(KO.values()))
 glyphs=font_glyphs(font,characters-{'.'})
 period='STARTCHAR U+002E\nENCODING 46\nSWIDTH 266 0\nDWIDTH 4 0\nBBX 1 1 1 1\nBITMAP\n80\nENDCHAR'
 assert period in font.decode('utf-8').replace('\r\n','\n')
 glyphs['.']=(4,{(1,-2)})  # Exact pinned BDF side bearing; old helper accepts only bearing0.
 catalog=json.loads(CATALOG.read_text(encoding='utf-8'));dg=dg_glyphs(catalog)
 def button(pixels,width):
  extent=max(88,((width+19+7)//8)*8)
  assert extent<=144 and all(-8<=y<=7 for x,y in pixels)
  left=-extent//2;right=left+extent-1
  frame={(x,y):(13 if x in(left,right)or y in(-8,7)else 15)for y in range(-8,8)for x in range(left,right+1)}
  frame.update({(x+left+44,y):v for(x,y),v in marker.items()})
  start=left+16+(extent-17-width)//2
  assert start>=left+16 and start+width-1<right
  frame.update({(x+start,y):v for(x,y),v in pixels.items()})
  assert all(frame[x+left+44,y]==v for(x,y),v in marker.items())
  return frame
 bold, retail_letters, extended_letters=bold_glyphs(english)
 for event in range(5,10):
  english.append(button(*bold_text(EN[event],bold)))
  korean.append(button(*remap_text(*text_pixels(KO[event],glyphs),5)))
 english.append(japanese[10]);korean.append(japanese[10])
 hyphen={(x,y):v for(x,y),v in japanese[4].items()if -7<=x<=-2 and y==-1}
 # Only source digits/punctuation remain literal. Latin Ver uses chart glyphs.
 version={(x,y):v for(x,y),v in japanese[6].items()if -8<=x<=4 and -4<=y<=2 and v in(13,14)}
 assert bounds(version)==[-7,-4,4,2]
 digicode=[old_dg[0]];reading_ids={}
 for event in range(1,10):
  if event==4:
   text,width=spaced_digicode('D',catalog,dg)
   text,width=attach(text,width,hyphen)
   tail,tw=spaced_digicode('ARK',catalog,dg)
   text.update({(x+width+2,y):v for(x,y),v in tail.items()});width+=2+tw
   reading_ids[event]=encode('DARK',catalog)
  elif event==6:
   text,width=spaced_digicode('Ver',catalog,dg)
   text,width=attach(text,width,version)
   tail,tw=spaced_digicode('とばとる',catalog,dg)
   text.update({(x+width+2,y):v for(x,y),v in tail.items()});width+=2+tw
   reading_ids[event]=encode('Verとばとる',catalog)
  else:
   text,width=spaced_digicode(DG[event],catalog,dg);reading_ids[event]=encode(DG[event],catalog)
  digicode.append(open_digicode_panel(text,width,marker))
 digicode.append(japanese[10])
 frames={'english':english,'japanese':japanese,'korean':korean,'digicode':digicode}
 blob=bytearray();objects=[];metadata={}
 for language,images in frames.items():
  parts,atlas=tile_layouts(images)
  assert len(atlas)<=256,(language,'unique tiles',len(atlas))
  counts=[len(p)for p in parts]
  assert max(counts[0],sum(counts[1:6]),sum(counts[6:8]),sum(counts[8:10]))<=128,(language,counts)
  while len(blob)%4:blob.append(0)
  offset=len(blob);data=pack(parts,atlas,address+offset);blob.extend(data)
  objects.append(dict(label=language+'_p0',offset=offset,size=len(data),sha256=sha(data)))
  metadata[language]=dict(address=address+offset,tiles=len(atlas),parts=counts,root_parts=sum(counts[1:6]),subtrees=[sum(counts[6:8]),sum(counts[8:10])],preserved_first_five=language!='digicode',bounds=[bounds(p)for p in images])
 parsed=parsed_p1(source,0x3D3A80)
 assert parsed['payloads']==[[(0xFF01,i,i,0,0,0)]for i in range(11)]
 for label,datafn in [('p1',lambda at:convert_p1(parsed,at-BASE)),('p2',lambda at:convert_block(source[0x3D7EE0:0x3D7EE0+38]))]:
  while len(blob)%4:blob.append(0)
  offset=len(blob);data=datafn(address+offset);blob.extend(data)
  objects.append(dict(label=label,offset=offset,size=len(data),sha256=sha(data)))
 return bytes(blob),dict(schema=2,visual_revision='r2-open-Digicode-and-retail-bold-English',retail_english_glyph_rectangles=retail_letters,constructed_english_glyphs=['C']+list(extended_letters),visual_helper_sha256=sha(Path(__file__).with_name('mode23_title_visual_layout.py').read_bytes()),status='PREPARED_TITLE_ELEVEN_EVENTS_NO_INSTALLATION',source_sha256=SOURCE,native_sha256=NATIVE,font_sha256=FONT_SHA,license_sha256=LICENSE_SHA,base_address=address,objects=objects,languages=metadata,source_text=JA,english_additions=EN,korean_additions=KO,digicode_readings=DG,digicode_glyph_ids=reading_ids,normalization=['source smallョ in options/collection maps explicitly to fullヨ','source smallュ in Shoot maps explicitly to fullユ'],literal_punctuation=dict(version_source_bounds=bounds(version),version_pixels=len(version),hyphen_pixels=len(hyphen)),limits=['No native menu/controller/ROM modification','Mode22 remains absent and requires a separate implementation availability guard','Digicode open black panels keep exact ink with two clear inter-glyph columns and six clear right/marker columns; enclosing white border removed to avoid touching fourteen-row voiced ink','Actual native OAM/tile staging and root/subtree controller lifetime still require linked consumer verification'])

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','font','license','output_dir'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 blob,meta=build(a.source.read_bytes(),a.native.read_bytes(),a.font.read_bytes(),a.license.read_bytes())
 meta.update(builder_sha256=sha(Path(__file__).read_bytes()),bytes=len(blob),sha256=sha(blob))
 a.output_dir.mkdir(parents=True);(a.output_dir/'assets.bin').write_bytes(blob)
 (a.output_dir/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(meta['status'],meta['sha256'],json.dumps({k:(v['tiles'],v['root_parts'])for k,v in meta['languages'].items()}))
if __name__=='__main__':main()
