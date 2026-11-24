"""Isolate four-language portrait header installation on the corrected title base."""
import argparse,hashlib,json,struct
from pathlib import Path
from build_mode23_title_scene_r2 import Allocator
import character_select_name_overlay as overlay

BASE=0x08000000
INPUT='9F0DA0316B76CA6D2634DF7F89CCE1FFD1F1B0AC2CB37B2EDCDC0753466B228A'
TITLE_OWNER='A54778FA9FCA9A689E6B632C477DBF457B50B5BAFD5CEB4A324B1AA463A87324'
SCENE_OWNER='3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B'
ASSETS='9F479B7C13FA4BCECDBD24E3170628377369C31CC5FD4563D311B9B49A1C3C11'
ALLOCATOR='72DAE8227C22A4F4B03D95D5AB3912F0288BF01BCA5D7DDEF12454FCA1D97E6C'
OVERLAY='4156DDC0A8AD9FD2B9D3C5E2B2745DEEF5E17034D98BCC32B9D83B3F94B76824'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def exclude(allocator,spans):
 for lo,hi in spans:
  free=[]
  for a,b in allocator.free:
   if b<=lo or a>=hi:free.append((a,b));continue
   if a<lo:free.append((a,lo))
   if hi<b:free.append((hi,b))
  allocator.free=free
def build(before,headers,meta,scene,title):
 assert sha(before)==INPUT and len(before)==0x1000000
 assert sha(Path(__file__).with_name('build_mode23_title_scene_r2.py').read_bytes())==ALLOCATOR
 assert sha(Path(overlay.__file__).read_bytes())==OVERLAY
 assert len(headers)==60 and all(len(x)==768 for x in headers)
 assert struct.unpack_from('<I',before,overlay.HOOK-BASE)[0]==overlay.OLD_WORD
 assert sha(before[0x633400:0x63341C])==overlay.GETTER_SHA
 assert title['output_sha256']==INPUT and scene['output_sha256']=='B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
 # Exclude the complete declared code/root reservation, including erased slack,
 # plus all prior typed object extents. Do not infer ownership from FF alone.
 assert scene['root_entry_reservation']==[0xDB4400,0xDB5C04]
 prior=[(0xDB0404,0xDB5C04)]+[(r['start'],r['end'])for owner in(scene,title)for r in owner['allocations']]
 allocator=Allocator(before);exclude(allocator,prior)
 code_raw=allocator.allocate(len(overlay.assemble(0x08F00000,0x08F00200)),'portrait-header overlay ARM',4)
 table_raw=allocator.allocate(240,'four-language fifteen-ID header pointer table',4)
 writes=[];pointers=[]
 for index,b in enumerate(headers):
  row=meta['entries'][index];at=allocator.allocate(768,f"header-{row['language']}-{row['id']:02d}",32)
  writes.append((at,b,f"header-{row['language']}-{row['id']:02d}"));pointers.append(BASE+at)
 code=overlay.assemble(BASE+code_raw,BASE+table_raw)
 writes.extend(((code_raw,code,'portrait-header overlay ARM'),(table_raw,struct.pack('<60I',*pointers),'four-language fifteen-ID header pointer table'),(overlay.HOOK-BASE,overlay.hook(BASE+code_raw),'post-portrait DMA localized header branch')))
 spans=sorted((at,at+len(b))for at,b,label in writes)
 assert len(spans)==63 and all(a[1]<=b[0]for a,b in zip(spans,spans[1:]))
 after=bytearray(before);rows=[]
 for at,b,label in writes:
  old=before[at:at+len(b)]
  if at!=overlay.HOOK-BASE:
   assert old==b'\xff'*len(b)and not any(at<=t<at+len(b)for t in allocator.targets)
   assert all(at+len(b)<=lo or at>=hi for lo,hi in prior)
  after[at:at+len(b)]=b
  rows.append(dict(offset=at,size=len(b),label=label,before_hex=old.hex()if at==overlay.HOOK-BASE else None,before_fill=None if at==overlay.HOOK-BASE else 255,before_sha256=sha(old),after_sha256=sha(b)))
 inverse=bytearray(after)
 for r in rows:
  at,n=r['offset'],r['size'];inverse[at:at+n]=bytes.fromhex(r['before_hex'])if r['before_hex']else b'\xff'*n
 assert inverse==before
 report=dict(status='ISOLATED_CHARACTER_SELECT_HEADERS',input_sha256=INPUT,output_sha256=sha(after),builder_sha256=sha(Path(__file__).read_bytes()),overlay_sha256=OVERLAY,allocator_sha256=ALLOCATOR,assets_manifest_sha256=ASSETS,scene_owner_sha256=SCENE_OWNER,title_owner_sha256=TITLE_OWNER,prior_excluded_extents=prior,allocations=allocator.allocations,writes=rows,code_span=[code_raw,code_raw+len(code)],table_span=[table_raw,table_raw+240],header_pointers=pointers,declared_bytes=sum(r['size']for r in rows),changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_image_inverse=True,new_OAM=0,new_global_RAM_bytes=0,palette_writes=0,physical_header=[0x06005780,0x06005A80],physical_body_retained=[0x06005A80,0x06006F80],actual_runtime_verified=False,limits=['Strict scanner is applied to the entire merged input; no reference exemptions.','Whole scene code/root reservation and every prior scene/title allocation excluded, including FF slack.','Native portrait/palette/selection/IRQ consumers unchanged except typed post-DMA hook.','Independent installation QA and live capture remain separate.'])
 return bytes(after),report,allocator.hits
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('input','assets','scene-owner','title-owner','output-dir'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 raw=(a.assets/'manifest.json').read_bytes();sr=a.scene_owner.read_bytes();tr=a.title_owner.read_bytes()
 assert (sha(raw),sha(sr),sha(tr))==(ASSETS,SCENE_OWNER,TITLE_OWNER)
 meta=json.loads(raw);headers=[]
 for row in meta['entries']:
  b=(a.assets/row['file']).read_bytes();assert sha(b)==row['sha256'];headers.append(b)
 after,report,hits=build(a.input.read_bytes(),headers,meta,json.loads(sr),json.loads(tr))
 a.output_dir.mkdir(parents=True);(a.output_dir/'component.gba').write_bytes(after)
 census=(json.dumps(dict(input_sha256=INPUT,range=[0xD90000,0x1000000],hits=hits,new_allocation_hits=0),indent=2)+'\n').encode();(a.output_dir/'allocation-census.json').write_bytes(census);report['allocation_census_sha256']=sha(census)
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS',report['output_sha256'],sha(path.read_bytes()))
if __name__=='__main__':main()
