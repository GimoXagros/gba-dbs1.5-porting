"""Revision 2: retain all r1 pixels, move whole Digicode labels down one row."""
import argparse,copy,json
from pathlib import Path
import build_character_select_name_assets as prior

PRIOR_BUILDER='EDFF86405B6BFE5AABFDEFECAEF507CBDC016767C5888243CE6D3A979387C959'
def build(source,native,font,license_data):
 assert prior.sha(Path(prior.__file__).read_bytes())==PRIOR_BUILDER
 headers,rows=prior.build(source,native,font,license_data)
 headers=list(headers);rows=copy.deepcopy(rows)
 for index in range(45,60):
  row=rows[index];i=row['id'];old=prior.unpack(headers[index]);bg=row['colors']['background']
  glyph={(x,y):old[y][x]for y in range(1,16)for x in range(96)if not prior.protected(i,x,y)and old[y][x]!=bg}
  assert glyph and min(y for x,y in glyph)>=1 and max(y for x,y in glyph)<=14
  out=[[old[y][x]if prior.protected(i,x,y)else bg for x in range(96)]for y in range(16)]
  for(x,y),v in glyph.items():
   assert not prior.protected(i,x,y+1);out[y+1][x]=v
  assert all(out[1][x]==bg for x in range(96)if not prior.protected(i,x,1))
  assert all(out[y][x]==old[y][x]for y in range(16)for x in range(96)if prior.protected(i,x,y))
  headers[index]=prior.pack(out);row.update(sha256=prior.sha(headers[index]),top=row['top']+1,vertical_translation=1,
   top_clear_rows=min(y for x,y in glyph),bottom_clear_rows=14-max(y for x,y in glyph),
   prior_header_sha256=prior.sha(prior.pack(old)),preserved_glyph_pixels=len(glyph))
 return headers,rows
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('source','native','font','license','output-dir'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists();a.output_dir.mkdir(parents=True)
 inputs=[getattr(a,k).read_bytes()for k in('source','native','font','license')];headers,rows=build(*inputs)
 for b,row in zip(headers,rows):(a.output_dir/row['file']).write_bytes(b)
 (a.output_dir/'headers.bin').write_bytes(b''.join(headers));prior.previews(inputs[1],headers,rows,a.output_dir)
 result=dict(schema=2,status='standalone-assets-not-installed',builder_sha256=prior.sha(Path(__file__).read_bytes()),prior_builder_sha256=PRIOR_BUILDER,source_sha256=prior.sha(inputs[0]),native_sha256=prior.sha(inputs[1]),font_sha256=prior.sha(inputs[2]),license_sha256=prior.sha(inputs[3]),catalog_sha256=prior.sha(prior.CATALOG.read_bytes()),digicode_glyph_tool_sha256=prior.sha(Path(prior.__file__).with_name('digicode_glyphs.py').read_bytes()),header_size=768,atlas_size=6144,headers_sha256=prior.sha(b''.join(headers)),entries=rows,new_OAM=0,new_persistent_RAM=0,palette_writes=0,change='Only DG full glyph translation (0,+1); at least one background row between top frame and any DG ink. No glyph clipping/scaling.',limits=['R1 EN/JA/KO exact. Protected native border and portrait body remain exact.','No installed allocation or runtime claim.'])
 (a.output_dir/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS',prior.sha((a.output_dir/'manifest.json').read_bytes()))
if __name__=='__main__':main()
