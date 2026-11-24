"""Author resource pixel/layout checks and actual native presentation consumers."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from mode23_linker import compose
from verify_shoot_static_companion_clear import Machine
import mode23_scene_resources as resources
import mode23_native_services as services
CODE=0x08E00000;ASSETS=0xE20000;BASE=0x08000000;PRES=0x02001040

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def u(b,a):return struct.unpack_from('<I',b,a)[0]
class ResourceMachine(Machine):
 def run_checked(self,start,positions):
  end=self.r[14];pc=start
  for _ in range(24000):
   if pc==end:return
   assert pc in positions,f'unlinked {pc:08X}'
   w=self.get(pc)
   if w&0x0E000090==0x00000090:
    self.r[15]=pc+8
    if self.condition(w>>28):
     assert w&0x00400000,'immediate halfword offset'
     base,reg=(w>>16)&15,(w>>12)&15
     off=((w>>4)&0xF0)|(w&15);kind=(w>>5)&3
     new=(self.r[base]+(off if w&0x800000 else -off))&0xFFFFFFFF
     addr=new if w&0x1000000 else self.r[base];size=1 if kind==2 else 2
     assert size==1 or addr%2==0,'aligned halfword'
     if w&0x100000:
      value=self.get(addr,size)
      if kind in (2,3) and value&(1<<(size*8-1)):value-=1<<(size*8)
      self.r[reg]=value&0xFFFFFFFF
     else:assert kind==1;self.put(addr,self.r[reg],2,True)
     if w&0x200000 or not w&0x1000000:self.r[base]=new
    pc+=4
   else:pc=super().run(pc,(positions-{pc})|{end},2)
  raise AssertionError('native resource instruction bound')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();s=a.source.read_bytes();native=a.native.read_bytes()
 data,meta=resources.build(s,ASSETS);body=resources.assembly(meta['tables'])+'\n'+services.assembly(native)
 labels=set(re.findall(r'^(\w+):',body,re.M));external=set(re.findall(r'\bm23_\w+',body))-labels
 assert external=={'m23_bf42_atan'}
 code,sym,proof=compose([body,'m23_bf42_atan:bx lr'],CODE,['m23_view_install'])
 rom=bytearray(native);rom[CODE-BASE:CODE-BASE+len(code)]=code;rom[ASSETS:ASSETS+len(data)]=data
 positions=set(range(CODE,CODE+len(code),4))|set(range(0x080127E4,0x080129C8,4))|set(range(0x080132EC,0x080133A8,4))
 pixels=0
 for r in meta['resources']:
  if r['kind']!='p0':continue
  source=r['source'];target=r['target'];layouts=r['layouts']
  for i in range(layouts):
   count,off=struct.unpack_from('<2H',s,source+16+4*i)
   n,ptr=struct.unpack_from('<2I',rom,u(rom,target)-BASE+8*i)
   assert count==n and rom[ptr-BASE:ptr-BASE+count*4]==s[source+off:source+off+count*4]
  desc=resources.far((0,h(s,source+4),h(s,source+6)))
  for i in range(r['descriptors']):
   length,physical=resources.parse_wsc_far_descriptor(s,desc+i*8)
   n,ptr=struct.unpack_from('<2I',rom,u(rom,target+4)-BASE+i*8);assert n==length
   raw=rom[ptr-BASE:ptr-BASE+n]
   for t in range(n//32):
    for y in range(8):
     for x in range(8):
      want=sum(((s[physical+t*32+y*4+k]>>(7-x))&1)<<k for k in range(4))
      assert (raw[t*32+y*4+x//2]>>(4*(x%2)))&15==want
      pixels+=1
 cases=0
 for vi,v in enumerate(meta['views']):
  parsed=resources.parsed_p1(s,v['p1'])
  for event,command in enumerate(parsed['commands']):
   m=ResourceMachine(rom,seed=13,flags=0xA000001F)
   for first,size in ((PRES,0x100),(0x05000000,0x400)):
    for j in range(size):m.put(first+j,0x19,1)
   # Every valid source mini/common event, no native stub or palette summary.
   row=0x02002000
   for i,pointer in enumerate(v['native']):m.put(row+i*4,pointer)
   m.r[0]=PRES;m.r[1]=row;m.r[2]=0x100;m.r[3]=0;m.r[12]=event
   saved=m.r[4:12].copy();sp=m.r[13]
   m.run_checked(sym['m23_view_install'],positions)
   assert m.r[4:12]==saved and m.r[13]==sp
   p1,p0,p2=v['native'];first=u(rom,p1-BASE)+event*16
   assert [m.get(PRES+x) for x in (0x44,0x48,0x4C)]==[p1,p0,p2]
   assert m.get(PRES+0xE,2)==event and m.get(PRES+0x1C,2)==command[0]
   assert m.get(PRES+0x20)==m.get(PRES+0x24)==u(rom,first-BASE+4)
   assert m.get(PRES+0x28)==u(rom,first-BASE+8) and m.get(PRES+0x2C)==u(rom,first-BASE+12)
   assert m.get(PRES+0x14,2)==0x100 and m.get(PRES+0x10,2)==0 and m.get(PRES+8,2)&0x2000
   palrow=h(rom,p2-BASE+4);dst=0x05000000+(palrow-8+16)*32+2
   assert bytes(m.get(dst+j,1) for j in range(30))==rom[p2-BASE+8:p2-BASE+38]
   cases+=1
 result=dict(status='MODE23_PRESENTATION_RESOURCES_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),source_sha256=sha(s),native_sha256=sha(native),resource_module_sha256=sha((ROOT/'tools/mode23_scene_resources.py').read_bytes()),service_module_sha256=sha((ROOT/'tools/mode23_native_services.py').read_bytes()),assets_bytes=len(data),assets_sha256=sha(data),views=len(meta['views']),resources=len(meta['resources']),source_pixels=pixels,actual_native_event_cases=cases,linked_bytes=len(code),link_proof=proof,limits=['No game/renderer/OAM execution','Native constructor,event setter,palette uploader executed; atan placeholder is unreachable','Full-character views used by intro/completion are prior canonical assets, outside this new37-view corpus'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
