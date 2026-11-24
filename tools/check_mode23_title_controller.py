"""Author native title phase/renderer/task fixtures; normal game entry remains external."""
import argparse,json,struct
from pathlib import Path
from check_mode23_scene_resources import ResourceMachine
from verify_shoot_static_companion_clear import Machine
from mode23_linker import compose
from build_mode23_title_assets import sha
import mode23_title_controller as controller,mode23_title_tree as tree,mode23_native_services as services
CODE=0x08E10000;BASE=0x08000000;PRES=0x03002A78
class NextInstruction:
 current=0
 def __contains__(self,address):return address!=self.current

class FastResourceMachine(ResourceMachine):
 # Identical instruction/halfword checks; avoid allocating a full PC set each step.
 def run_checked(self,start,positions):
  end=self.r[14];pc=start;stops=NextInstruction()
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
   else:
    stops.current=pc
    pc=Machine.run(self,pc,stops,2)
  raise AssertionError('native resource instruction bound')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','scene','assets_dir','report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();s=a.source.read_bytes();native=a.native.read_bytes();scene=a.scene.read_bytes()
 assert sha(scene)=='B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
 meta=json.loads((a.assets_dir/'manifest.json').read_text(encoding='utf-8'));assets=(a.assets_dir/'assets.bin').read_bytes()
 fixtures='''m23_title_sound: ldr r1,qa_sound
str r0,[r1]
bx lr
m23_eligibility_read: ldr r1,qa_eligibility
ldr r0,[r1]
bx lr
m23_bf42_atan: bx lr
m23_view_install: bx lr
qa_sound: .word 0x02003020
qa_eligibility: .word 0x02003024
'''
 exports=list(controller.CALLBACKS)+['m23_spawn','m23_present_construct','m23_present_event','m23_title_tree_init']
 code,sym,proof=compose([controller.assembly(s,native),tree.assembly(s),services.assembly(native),fixtures],CODE,exports)
 image=bytearray(scene);image[0xE00000:0xE00000+len(assets)]=assets;image[CODE-BASE:CODE-BASE+len(code)]=code
 positions=set(range(CODE,CODE+len(code),4))|set(range(0x08011AC4,0x08012020,4))|set(range(0x08012600,0x08012650,4))|set(range(0x08012710,0x08012DD8,4))|set(range(0x086FEA00,0x086FF28C,4))
 p1=0x08E00000+next(x['offset']for x in meta['objects']if x['label']=='p1');p2=0x08E00000+next(x['offset']for x in meta['objects']if x['label']=='p2')
 calls=0;highest=0;results=[]
 def invoke(m,address):
  nonlocal calls
  m.r[14]=0x12345678;m.run_checked(address,positions);calls+=1
 def fresh(language,eligible):
  m=FastResourceMachine(image,seed=73,flags=0x6000001F)
  for start,size in ((0x02010000,52*0x118),(PRES,0x300),(0x03001428,0x400),(0x02000000,0x1000)):
   for at in range(start,start+size):m.put(at,0,1)
  for at in (0x03001338,0x0300133C,0x03001340,0x03001344,0x030012D0):m.put(at,0)
  for at in range(0x03002310,0x03002350):m.put(at,0,1)
  for at in (0x030012CA,0x030012B6,0x030012CC,0x030012CE,0x0300130A):m.put(at,0,2)
  for at in range(0x030012BC,0x030012C0):m.put(at,0,1)
  for at in range(0x03002C08,0x03002C58):m.put(at,0,1)
  for at in range(0x03002C18,0x03002C58):m.put(at,(at*3)&255,1)
  m.put(0x02003024,eligible);m.put(0x02003020,0)
  m.r[0]=0x1000;m.r[1]=sym['m23_title_enter_root'];m.r[2]=0;invoke(m,sym['m23_spawn']);header=m.r[0];state=header+0x18
  m.r[0]=0xF000;m.r[1]=0x080914E4;m.r[2]=0;invoke(m,sym['m23_spawn']);palette=m.r[0]
  m.put(0x0300133C,header);m.put(0x03002A74,palette)
  m.r[0]=state;invoke(m,sym['m23_title_tree_init'])
  for i,pointer in enumerate((p1,meta['languages'][language]['address'],p2)):m.put(0x02003000+i*4,pointer)
  for i in range(5):
   m.r[0]=PRES+i*0x50;m.r[1]=0x02003000;m.r[2]=1;m.r[3]=i;invoke(m,sym['m23_present_construct'])
   m.r[0]=PRES+i*0x50;m.r[1]=i;invoke(m,sym['m23_present_event'])
  return m,header,state,palette
 def step(m,header,keys=0):
  nonlocal highest
  m.put(0x0300130A,keys,2);m.put(0x030012CA,0,2);m.put(0x030012D0,m.get(0x030012D0)+1)
  saved=m.r[:13].copy();sp=m.r[13];invoke(m,m.get(header));assert m.r[:13]==saved and m.r[13]==sp
  count=m.get(0x030012CA,2);assert count<=128;highest=max(highest,count);return count
 def to_idle(m,header):
  for i in range(160):
   if m.get(header)==sym['m23_title_idle']:return i
   step(m,header)
  raise AssertionError('menu slide did not finish')
 for language in meta['languages']:
  for eligible in (0,1):
   for selected in (0,1,2,3,4):
    print('scenario',language,eligible,selected,flush=True)
    m,header,state,palette=fresh(language,eligible);root_ticks=to_idle(m,header)
    assert m.get(state+4,1)==0 and m.get(state+6,1)==5
    assert step(m,header)==meta['languages'][language]['root_parts']
    for _ in range(selected):step(m,header,4)
    assert m.get(state+5,1)==selected
    step(m,header,0x40)
    if selected in(1,4):
     to_idle(m,header);assert m.get(state+4,1)==(1 if selected==1 else 2)
     if selected==4:
      step(m,header,0x40);assert m.get(header)==sym['m23_title_idle'] and m.get(0x02003020)==0x7A
      step(m,header,4)
      step(m,header,0x40)
      if not eligible:
       assert m.get(header)==sym['m23_title_idle'] and m.get(0x02003020)==0x7A
       step(m,header,0x80);to_idle(m,header);assert m.get(state+4,1)==0
       step(m,header,0x80);assert m.get(header)==0x08091598
       results.append(dict(language=language,eligible=eligible,root_row=selected,result='locked Shoot, back to root, native timeout fade requested',root_slide_ticks=root_ticks));continue
     else:step(m,header,0x40)
    assert m.get(header)==sym['m23_title_confirm_exit']
    for ticks in range(100):
     step(m,header)
     if m.get(0x03001338)==0:break
    else:raise AssertionError('title root retirement did not complete')
    assert m.get(0x03002314,2)==1 and m.get(0x03002318,2)==0
    assert m.get(0x030012BC,1)==m.get(0x030012BE,1)==0 and m.get(0x030012BD,1)==224 and m.get(0x030012BF,1)==144
    assert m.get(0x0300232A,2)==(8 if selected==4 else 5 if selected==1 else 2 if selected==3 else 0)
    assert m.get(0x03002316,2)==(2 if selected==2 else 0)
    results.append(dict(language=language,eligible=eligible,root_row=selected,result='actual native controller and palette task retirement',root_slide_ticks=root_ticks,window_ticks=ticks+1))
 report=dict(status='TITLE_PHASE_CONTROLLER_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),modules={x.__name__:sha(Path(x.__file__).read_bytes())for x in(controller,tree,services)},scene_sha256=sha(scene),assets_sha256=sha(assets),link=proof,callbacks_executed=calls,scenarios=results,maximum_simultaneous_parts=highest,limits=['Five presentation construction starts from an explicit cleared initializer fixture; full installed title initializer remains integration work','Existing native palette task execution and physical OAM/IRQ upload not modeled in these task snapshots','Source sound requests and cached eligibility are explicit fixtures; no guessed command IDs or EEPROM execution','Native prompt/timeout callback provenance is static; phase fixture begins at the first root-entry callback'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'],calls,sha(a.report.read_bytes()))
if __name__=='__main__':main()
