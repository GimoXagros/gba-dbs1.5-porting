"""Isolated development title tree exposing the real, eligibility-gated Shoot scene.

The absent mode22 row is visibly unavailable. This is not final title parity.
Existing native prompt, palette task, timeout and common transitions remain.
"""
import argparse,bisect,hashlib,json,re,struct,types
from pathlib import Path
import verify_shoot_caller_resident as scanner
from mode23_linker import compose
from mode23_asset_scatter import place_bundle
import mode23_title_controller_r2 as controller
import mode23_title_tree as tree

BASE=0x08000000
INPUT='36A126206237A5C6A0670105C8023B5237FFA055733EF7795AE2A3A42A5E3B8A'
ASSETS='4BB3592128E231C49457551BE6C9DDB39734F8515FCFBBA6D8EA7CA817173CB4'
MANIFEST='A5FBAF732FC867A87CE470C8DE5A69204B331F5FAFA3D838ED3A102EE76AE518'
RANGE=(0xD90000,0x1000000)
ELIGIBILITY=0x08D8D200
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]

class Allocator:
 def __init__(self,native):
  self.native=native
  f=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=(RANGE,)),argdefs=scanner.inbound.__defaults__)
  self.hits=f(native);self.targets=sorted(set(v&0x1FFFFFF for _,_,v in self.hits))
  self.free=[];self.allocations=[]
  # Unlike the first scene, the current range contains live objects. Only actual
  # erased runs are candidates; every conservative inbound destination splits them.
  for run in re.finditer(b'\xff{4,}',native[RANGE[0]:RANGE[1]]):
   a,b=run.start()+RANGE[0],run.end()+RANGE[0]
   points=self.targets[bisect.bisect_left(self.targets,a):bisect.bisect_left(self.targets,b)]
   for target in points:
    if a<target:self.free.append((a,target))
    a=max(a,target+4)
   if a<b:self.free.append((a,b))
 def allocate(self,size,label,alignment=32):
  choices=[]
  for i,(a,b)in enumerate(self.free):
   at=(a+alignment-1)&-alignment
   if at+size<=b:choices.append((b-at-size,i,at))
  assert choices,('no strict zero-reference erased fit',label,size)
  _,i,at=min(choices);a,b=self.free.pop(i)
  if a<at:self.free.append((a,at))
  if at+size<b:self.free.append((at+size,b))
  assert self.native[at:at+size]==b'\xff'*size
  assert not any(at<=x<at+size for x in self.targets)
  self.allocations.append(dict(label=label,start=at,end=at+size,size=size,alignment=alignment,strict_inbound_count=0))
  return at

def asset_plan(data,meta):
 base=meta['base_address'];fixups=set();objects=[]
 for obj in meta['objects']:
  at=obj['offset'];assert sha(data[at:at+obj['size']])==obj['sha256']
  if obj['label']=='p2':continue  # Native title palette already byte-identical.
  objects.append(obj)
  if obj['label'].endswith('_p0'):
   fixups.update((at,at+4));table=u(data,at)-base;desc=u(data,at+4)-base
   fixups.update(table+i*8+4 for i in range(11));fixups.add(desc+4)
  elif obj['label']=='p1':
   fixups.add(at);table=u(data,at)-base
   for i in range(11):
    row=table+i*16;count=u(data,row);payload=u(data,row+4)-base
    assert count==1
    fixups.update(row+k for k in (4,8,12) if u(data,row+k))
    fixups.update(payload+j*16+12 for j in range(count) if u(data,payload+j*16+12))
  else:raise AssertionError('unknown typed object')
 return objects,[dict(offset=x,relative_target=u(data,x)-base)for x in sorted(fixups)]

def adapters(pointers):
 return f'''m23_eligibility_read:
b 0x{ELIGIBILITY:08X}
m23_title_sound:
push {{r4-r11,lr}}
sub r8,r0,#0x78
add r8,r8,#0x1e
mov r9,#1
mov r10,#0
mov r11,#0
bl 0x080d15c0
pop {{r4-r11,lr}}
bx lr
m23_title_select_p0:
push {{r0,r1}}
mrs r1,cpsr
ldr r0,=0x0300112f
ldrb r0,[r0]
sub r0,r0,#0xa0
cmp r0,#3
movhi r0,#0
adr r8,m23_title_p0_table
ldr r8,[r8,r0,lsl #2]
msr cpsr_f,r1
pop {{r0,r1}}
b 0x08090a1c
.ltorg
m23_title_p0_table:
.word {','.join(hex(pointers[x])for x in ('english_p0','japanese_p0','korean_p0','digicode_p0'))}
'''

def build(source,native,original,data,meta,owner):
 assert sha(source)==tree.SOURCE and sha(native)==INPUT and sha(original)==controller.NATIVE
 assert sha(data)==ASSETS and meta['sha256']==ASSETS
 assert len(native)==len(original)==0x1000000
 assert u(native,0x90C70)==0x08090C7C and u(native,0x90E34)==0x08090E58 and u(native,0x90BBC)==0x0808FC58
 assert native[0x90A18:0x90A1C]==original[0x90A18:0x90A1C]
 assert u(native,0x15B74)==0x08DB4404,'actual expanded constructor column'
 assert u(native,0xDB4404+22*12)==0 and u(native,0xDB4404+23*12)!=0,'mode22 unavailable, real mode23 registered'
 obj=next(o for o in meta['objects']if o['label']=='p2');assert data[obj['offset']:obj['offset']+obj['size']]==native[0x90878:0x90878+obj['size']]
 allocator=Allocator(native)
 assert owner['output_sha256']=='B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
 prior=[(0xDB0404,0xDB5C04)]+[(r['start'],r['end'])for r in owner['allocations']]
 for lo,hi in prior:
  free=[]
  for a,b in allocator.free:
   if b<=lo or a>=hi:free.append((a,b));continue
   if a<lo:free.append((a,lo))
   if b>hi:free.append((hi,b))
  allocator.free=free
 objects,fixups=asset_plan(data,meta)
 values=[controller.assembly(source,original),tree.assembly(source)]
 exports=list(controller.CALLBACKS)+['m23_title_select_p0','m23_title_event','m23_title_sound','m23_title_tree_init','m23_title_tree_action','m23_title_tree_apply','m23_title_tree_move','m23_title_exit_config']
 provisional={o['label']:meta['base_address']+o['offset']for o in objects}
 sizing,_,_=compose(values+[adapters(provisional)],0x08E10000,exports)
 code_raw=allocator.allocate(len(sizing),'complete title controller and adapters',4)
 writes,resolve,places=place_bundle(data,objects,fixups,allocator,'title-')
 pointers={o['label']:BASE+resolve(o['offset'])for o in objects}
 code,symbols,link=compose(values+[adapters(pointers)],BASE+code_raw,exports)
 assert len(code)==len(sizing)
 writes.append((code_raw,code,'complete title controller and adapters'))
 target=symbols['m23_title_select_p0'];delta=target-(BASE+0x90A18)-8;assert delta%4==0 and -(1<<25)<=delta<(1<<25)
 writes.extend([(0x90A18,struct.pack('<I',0xEA000000|((delta//4)&0xFFFFFF)),'four-language expanded title atlas selector'),
                (0x90BBC,struct.pack('<I',pointers['p1']),'eleven source title events'),
                (0x90C70,struct.pack('<I',symbols['m23_title_init_callback']),'title task initialization and cached actual eligibility'),
                (0x90E34,struct.pack('<I',symbols['m23_title_enter_root']),'native prompt enters complete title tree')])
 spans=sorted((at,at+len(payload))for at,payload,label in writes)
 assert all(a[1]<=b[0]for a,b in zip(spans,spans[1:]))
 after=bytearray(native);declared=[]
 for at,payload,label in writes:
  before=native[at:at+len(payload)]
  if at>=RANGE[0]:
   assert before==b'\xff'*len(payload) and not any(at<=t<at+len(payload)for t in allocator.targets)
  after[at:at+len(payload)]=payload
  declared.append(dict(offset=at,size=len(payload),label=label,before_hex=before.hex() if at<RANGE[0]else None,before_fill=255 if at>=RANGE[0]else None,before_sha256=sha(before),after_sha256=sha(payload)))
 inverse=bytearray(after)
 for row in declared:
  at,n=row['offset'],row['size'];inverse[at:at+n]=b'\xff'*n if row['before_fill']==255 else bytes.fromhex(row['before_hex'])
 assert inverse==native
 report=dict(status='DEVELOPMENT_TITLE_REAL_MODE23_ENTRY_MODE22_GUARDED',input_sha256=INPUT,output_sha256=sha(after),source_sha256=sha(source),assets_sha256=ASSETS,asset_manifest_sha256=MANIFEST,
             builder_sha256=sha(Path(__file__).read_bytes()),module_sha256={p:sha(Path(__file__).with_name(p+'.py').read_bytes())for p in('mode23_title_controller_r2','mode23_title_tree','mode23_linker','mode23_asset_scatter','verify_shoot_caller_resident')},
             prior_scene_owner_sha256='3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B',prior_excluded_extents=prior,code_span=[code_raw,code_raw+len(code)],symbols=symbols,link=link,asset_pointers=pointers,asset_objects=objects,typed_fixups=fixups,object_placements=places,allocations=allocator.allocations,writes=declared,
             declared_bytes=sum(r['size']for r in declared),changed_bytes=sum(x!=y for x,y in zip(native,after)),new_global_RAM_bytes=0,private_title_payload_bytes=0x24,
             eligibility_read=ELIGIBILITY,source_unlock_not_bypassed=True,mode22_registered_handler_guard=True,simultaneous_root_parts={k:v['root_parts']for k,v in meta['languages'].items()},
             whole_image_inverse=True,actual_runtime_verified=False,final_source_title_parity=False,limits=['Mode22 absent: its row remains explicitly unavailable in this development component','Source extra E6 counter overlay not implemented; no additional OAM overlay budget claimed','Normal title/character-select/Shoot/exit still require actual installed runtime validation','Native prompt, timeout and palette timing retained; new source submenu slides use source eight-pixel steps'])
 return bytes(after),report,allocator.hits

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in('source','input','native','assets_dir','scene_owner','output_dir'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 raw=(a.assets_dir/'manifest.json').read_bytes();assert sha(raw)==MANIFEST
 owner_raw=a.scene_owner.read_bytes();assert sha(owner_raw)=='3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B'
 after,report,hits=build(a.source.read_bytes(),a.input.read_bytes(),a.native.read_bytes(),(a.assets_dir/'assets.bin').read_bytes(),json.loads(raw),json.loads(owner_raw))
 a.output_dir.mkdir(parents=True);(a.output_dir/'component.gba').write_bytes(after)
 census=(json.dumps(dict(input_sha256=INPUT,range=RANGE,hits=hits,actual_allocation_hits=0),indent=2)+'\n').encode()
 (a.output_dir/'allocation-census.json').write_bytes(census);report['allocation_census_sha256']=sha(census)
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(report['status'],report['output_sha256'],sha(path.read_bytes()))
if __name__=='__main__':main()
