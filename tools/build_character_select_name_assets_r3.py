"""Revision 3: two clear pixels between complete Korean syllable outlines."""
import argparse,copy,json
from pathlib import Path
import build_character_select_name_assets as original
import build_character_select_name_assets_r2 as prior
from build_options_korean_poc import font_glyphs,text_pixels

PRIOR_BUILDER='1CA43B82F49B3C7F6974F0D88B2FE694C25E113FA32A4C67F8EEF6482EE309DC'
GAP=2
def tracked(text,font):
 assert text and all(0xAC00<=ord(ch)<=0xD7A3 for ch in text)
 glyphs=font_glyphs(font,set(text));pixels={};cursor=0;parts=[]
 for ch in text:
  p,_=text_pixels(ch,glyphs)
  lo=min(x for x,y in p);hi=max(x for x,y in p)
  q={(cursor+x-lo,y):v for(x,y),v in p.items()}
  assert not pixels.keys()&q.keys()
  parts.append(dict(character=ch,left=cursor,right=cursor+hi-lo,pixels=len(q),shape_sha256=original.sha(json.dumps(sorted((x-lo,y,v)for(x,y),v in p.items())).encode())))
  pixels.update(q);cursor+=hi-lo+1+GAP
 width=cursor-GAP
 assert all(b['left']-a['right']-1==GAP for a,b in zip(parts,parts[1:]))
 assert all(all((x,y)not in pixels for x in range(a['right']+1,b['left'])for y in range(-12,1))for a,b in zip(parts,parts[1:]))
 return pixels,width,parts
def build(source,native,font,license_data):
 assert original.sha(Path(prior.__file__).read_bytes())==PRIOR_BUILDER
 headers,rows=prior.build(source,native,font,license_data);headers=list(headers);rows=copy.deepcopy(rows)
 for index in range(30,45):
  row=rows[index];i=row['id'];old=original.unpack(headers[index]);bg,ink,shadow=(row['colors'][key]for key in('background','ink','shadow'))
  points,width,parts=tracked(original.KO[i],font);lo=min(y for x,y in points);hi=max(y for x,y in points);height=hi-lo+1
  assert width<=70 and height==row['height']
  left=(96-width)//2;top=row['top']
  out=[[old[y][x]if original.protected(i,x,y)else bg for x in range(96)]for y in range(16)]
  for(x,y),v in points.items():
   at=(left+x,top+y-lo);assert not original.protected(i,*at)
   out[at[1]][at[0]]=ink if v==1 else shadow
  for p in parts:p.update(left=p['left']+left,right=p['right']+left)
  headers[index]=original.pack(out)
  row.update(sha256=original.sha(headers[index]),width=width,left=left,pixels=len(points),syllable_clear_columns=GAP,syllables=parts,prior_header_sha256=original.sha(original.pack(old)),prior_width=row['width'])
 return headers,rows
def comparison(native,old,new,rows,outdir):
 from PIL import Image,ImageDraw
 import struct
 sheet=Image.new('RGB',(228,380),(32,32,32));d=ImageDraw.Draw(sheet);d.text((24,1),'BEFORE',fill='white');d.text((132,1),'AFTER +2px',fill='white')
 for i in range(15):
  row=rows[30+i];d.text((0,20+i*24),str(i),fill='white');pal=struct.unpack_from('<16H',native,row['native_palette_raw']);colors=[tuple(((c>>s)&31)*255//31 for s in(0,5,10))for c in pal]
  for col,headers in enumerate((old,new)):
   im=Image.new('RGB',(96,16));im.putdata([colors[v]for r in original.unpack(headers[30+i])for v in r]);sheet.paste(im,(24+col*108,20+i*24))
 sheet.save(outdir/'korean-before-after-native.png');sheet.resize((sheet.width*3,sheet.height*3),Image.Resampling.NEAREST).save(outdir/'korean-before-after-3x.png')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('source','native','font','license','output-dir'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists();a.output_dir.mkdir(parents=True)
 inputs=[getattr(a,k).read_bytes()for k in('source','native','font','license')];headers,rows=build(*inputs);old,_=prior.build(*inputs)
 for b,row in zip(headers,rows):(a.output_dir/row['file']).write_bytes(b)
 (a.output_dir/'headers.bin').write_bytes(b''.join(headers));original.previews(inputs[1],headers,rows,a.output_dir);comparison(inputs[1],old,headers,rows,a.output_dir)
 result=dict(schema=3,status='standalone-assets-not-installed',builder_sha256=original.sha(Path(__file__).read_bytes()),prior_builder_sha256=PRIOR_BUILDER,source_sha256=original.sha(inputs[0]),native_sha256=original.sha(inputs[1]),font_sha256=original.sha(inputs[2]),license_sha256=original.sha(inputs[3]),catalog_sha256=original.sha(original.CATALOG.read_bytes()),digicode_glyph_tool_sha256=original.sha(Path(original.__file__).with_name('digicode_glyphs.py').read_bytes()),header_size=768,atlas_size=6144,headers_sha256=original.sha(b''.join(headers)),entries=rows,new_OAM=0,new_persistent_RAM=0,palette_writes=0,change='Only KO: exact individual glyph ink+outline with two complete background columns between syllables. EN/JA/DG equal r2.',limits=['No installed allocation or runtime claim.','Spacing is measured between complete outlined glyph bounds, not merely font advance.'])
 (a.output_dir/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS',original.sha((a.output_dir/'manifest.json').read_bytes()))
if __name__=='__main__':main()
