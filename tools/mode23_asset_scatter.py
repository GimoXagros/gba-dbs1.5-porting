"""Strict-reference-free mode23 object allocation and typed local relocation.

No files or ROM are changed. Every final object lies in originalFF bytes and
contains no conservative inbound target from the immutable predecessor.
"""
import hashlib,struct,types
import verify_shoot_caller_resident as scanner
import mode23_scene_resources as resources
import mode23_scene_graphics as graphics
BASE=0x08000000
RANGE=(0xD90000,0x1000000)
CODE_RESERVE=(0xDB0404,0xDB5C04)
def u(b,a):return struct.unpack_from('<I',b,a)[0]
class Allocator:
 def __init__(self,native,hits=None):
  assert hashlib.sha256(native).hexdigest().upper()=='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
  self.native=native
  assert native[RANGE[0]:RANGE[1]]==b'\xff'*(RANGE[1]-RANGE[0])
  if hits is None:
   f=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=(RANGE,)),argdefs=scanner.inbound.__defaults__);hits=f(native)
  self.hits=hits;self.targets=sorted(set(v&0x1FFFFFF for _,_,v in hits));points=[RANGE[0]-4]+self.targets+[RANGE[1]]
  gaps=[(a+4,b) for a,b in zip(points,points[1:]) if b>a+4]
  self.free=[]
  for a,b in gaps:
   if b<=CODE_RESERVE[0] or a>=CODE_RESERVE[1]:self.free.append((a,b));continue
   if a<CODE_RESERVE[0]:self.free.append((a,CODE_RESERVE[0]))
   if b>CODE_RESERVE[1]:self.free.append((CODE_RESERVE[1],b))
  self.allocations=[]
 def allocate(self,size,label,alignment=32):
  assert size>0 and alignment in (4,32)
  choices=[]
  for i,(a,b) in enumerate(self.free):
   at=(a+alignment-1)&-alignment
   if at+size<=b:choices.append((b-at-size,i,at))
  assert choices,('no exact zero-reference fit',label,size)
  _,i,at=min(choices);a,b=self.free.pop(i)
  if a<at:self.free.append((a,at))
  if at+size<b:self.free.append((at+size,b))
  assert self.native[at:at+size]==b'\xff'*size
  assert not any(at<=x<at+size for x in self.targets)
  self.allocations.append(dict(label=label,start=at,end=at+size,size=size,alignment=alignment,strict_inbound_count=0))
  return at

def resource_plan(source):
 data,meta=resources.build(source,0);other,_=resources.build(source,0x100000)
 objects=[dict(label=f"presentation-{r['kind']}-{r['source']:06X}",offset=r['target'],size=r['bytes']) for r in meta['resources']]
 tail=meta['tables']['base_params']-BASE;objects.append(dict(label='presentation-views-and-parameters',offset=tail,size=len(data)-tail))
 fixups=set()
 for r in meta['resources']:
  at=r['target']
  if r['kind']=='p0':
   fixups.update((at,at+4));layouts=u(data,at)-BASE;desc=u(data,at+4)-BASE
   fixups.update(layouts+8*i+4 for i in range(r['layouts']))
   fixups.update(desc+8*i+4 for i in range(r['descriptors']))
  elif r['kind']=='p1':
   fixups.add(at);table=u(data,at)-BASE
   for i in range(r['events']):
    row=table+i*16;count=u(data,row);payload=u(data,row+4)-BASE
    fixups.update(row+k for k in (4,8,12) if u(data,row+k))
    fixups.update(payload+j*16+12 for j in range(count) if u(data,payload+j*16+12))
 for name,ptr in meta['tables'].items():
  if name in ('base_params','evolved_params'):continue
  n=90 if name=='participant_views' else 3
  fixups.update(ptr-BASE+4*i for i in range(n))
 expected=bytearray(data)
 for at in fixups:struct.pack_into('<I',expected,at,u(data,at)+0x100000)
 assert bytes(expected)==other,'complete typed relocation inverse'
 return data,meta,objects,[dict(offset=x,relative_target=u(data,x)-BASE) for x in sorted(fixups)]

def place_bundle(data,objects,fixups,allocator,prefix=''):
 # Object fields partition all pointer-bearing/live bytes; padding stays FF.
 spans=sorted((o['offset'],o['offset']+o['size'],o) for o in objects)
 assert all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
 placement={}
 for o in sorted(objects,key=lambda x:(-x['size'],x['offset'])):placement[o['offset']]=allocator.allocate(o['size'],prefix+o['label'])
 def resolve(offset):
  hits=[(a,o) for a,b,o in spans if a<=offset<b];assert len(hits)==1,('local target outside typedobject',offset)
  a,o=hits[0];return placement[a]+offset-a
 relocated=bytearray(data)
 for f in fixups:
  resolve(f['offset']);struct.pack_into('<I',relocated,f['offset'],BASE+resolve(f['relative_target']))
 writes=[(placement[o['offset']],bytes(relocated[o['offset']:o['offset']+o['size']]),prefix+o['label']) for o in objects]
 return writes,resolve,placement

def place_resources(source,allocator):
 data,meta,objects,fixups=resource_plan(source);writes,resolve,placement=place_bundle(data,objects,fixups,allocator)
 meta={**meta,'scattered':True,'typed_fixups':fixups,'object_placements':placement,
       'tables':{name:BASE+resolve(ptr-BASE) for name,ptr in meta['tables'].items()},
       'views':[{**v,'native':[BASE+resolve(p-BASE) for p in v['native']]} for v in meta['views']]}
 return writes,meta

def place_graphics(source,allocator):
 data,meta=graphics.build(source,0)
 objects=[dict(label='BG-'+name,offset=row['address']-BASE,size=row['bytes']) for name,row in meta['tables'].items()]
 writes,resolve,placement=place_bundle(data,objects,[],allocator)
 meta={**meta,'scattered':True,'tables':{name:{**row,'address':BASE+resolve(row['address']-BASE)} for name,row in meta['tables'].items()}}
 return writes,meta
