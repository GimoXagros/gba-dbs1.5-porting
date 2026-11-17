"""Portable independent outer-route gate with explicit reachable native owner fixtures."""
import argparse,hashlib,json,struct,types
from pathlib import Path
from verify_iraira_palette_outer_reconstruction import GradientMachine as Machine
import verify_shoot_caller_resident as scanner
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def color(v):return sum((2*((v>>s)&15)+bool((v>>s)&15))<<d for s,d in ((8,0),(4,5),(0,10)))
FIRST,LIMIT=0xD8B640,0xD8B6C0
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before','after','source','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();before,after,s=(getattr(a,k).read_bytes() for k in ('before','after','source'))
 assert tuple(map(sha,(before,after,s)))==('3CB7A7137762AA77C7C8D9147CF32AB356CDB269E6CE819115B911DEF444E49E','574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76','C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7')
 helper=struct.pack('<15I',0xE92D4007,0xE10F2000,0xE59F1024,0xE5D1000E,0xE350000A,0x0A000002,0xE128F002,0xE8BD4007,0xEADFE4E6,0xE128F002,0xE8BD4007,0xE59FE004,0xEACCE593,0x03002310,0x080D0BE8)
 expected=bytearray(before);expected[FIRST:FIRST+60]=helper;struct.pack_into('<I',expected,0xD0BD0,0xEB32EA9A)
 assert after==expected and before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST) and u(before,0xD0BD0)==0xEB12CF8A
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__);assert not scan(before)
 assert 0x768F70+h(s,0x768F70+20)==0x769361 and s[0x769361:0x769367]==bytes.fromhex('9AB6024783C3')
 assert 0x783470+h(s,0x78370E+20)==0x783B90 and s[0x77CF86:0x77CF92]==bytes.fromhex('33C0BE800389048ED8A300FE')
 assert before[0xD0BE8:0xD0C70]==after[0xD0BE8:0xD0C70] and before[0xD0ED0:0xD101C]==after[0xD0ED0:0xD101C]
 parity=0
 for stage in range(256):
  if stage==10:continue
  for flag in range(16):
   pair=[]
   for rom in (before,after):
    m=Machine(rom,seed=3,flags=(flag<<28)|31);m.put(0x0300231E,stage,1);sp=m.r[13];m.run(0x080D0BD0,{0x080D0BD4});pair.append(m)
   x,y=pair;assert x.r[:15]==y.r[:15] and x.cpsr==y.cpsr and y.r[13]==sp
   diffs={k for k in x.mem.keys()|y.mem.keys() if x.mem.get(k)!=y.mem.get(k)}
   assert all(sp-16<=k<sp for k in diffs),'only retired helper stack bytes differ'
   parity+=1
 # Explicit reachable fixture derived from the frozen first-active source10 state.
 # It contains no capture dependency and no guest save-state blob.
 memory={0x03000000+i:0 for i in range(0x8000)}
 memory.update((0x05000000+i,0xA5) for i in range(1024))
 memory.update((0x04000000+i,0) for i in range(96))
 def put(address,value,size=4):
  memory.update((address+i,(value>>(8*i))&255) for i in range(size))
 for address,value,size in ((0x0300231E,10,1),(0x0300231C,11,1),(0x0300232E,4,1),
  (0x03003D30,5,2),(0x03003D32,1,2),(0x03003D34,2,2),(0x03003D36,3,2),
  (0x03002474,1,2),(0x03002478,0x08628300,4),(0x03002518,7,2),(0x03004668,2,2),
  (0x0300133C,0x020120D0,4),(0x03004518,0x020120D0,4),(0x03001344,0x020120D0,4),
  (0x0203F000,0,2)):
  put(address,value,size)
 # Native display task satisfies the copied-queue guard's typed object checks.
 # Its callback queue is the actual Iraira display callback, not the Shoot callback.
 for k,v in enumerate((0x08352268,0xFFFFF000,0x02011EA0,0x020120D0,2,0,0,0)):
  put(0x020120D0+k*4,v)
 # Execute real native copied IRQ code including its PC-relative literal pool.
 assert u(after,0xC9064)==0x03000DB0
 memory.update((0x03000DB0+i,v) for i,v in enumerate(after[0xC9008:0xC9074]))
 rows=struct.unpack_from('<256H',s,0x76AD13);full=0
 for flag in range(16):
  for mode in range(4):
   pair=[]
   for rom in (before,after):
    m=Machine(rom,seed=1,flags=(flag<<28)|31);m.mem=memory.copy();m.put(0x05000000,0,2)
    m.put(0x03004506,16 if mode==2 else 0,2);m.put(0x0300260B,int(mode==3),1);m.put(0x03004529,int(mode==1),1)
    m.put(0x04000200,0x3FFF if flag&1 else 0,2);m.put(0x04000208,1,2)
    regs=m.r[:];sp=regs[13];m.run(0x080D0BC0,{regs[14]});assert m.r[13]==sp;pair.append(m)
   old,new=pair;assert old.r[:15]==new.r[:15] and old.cpsr==new.cpsr,'complete common continuation register/flag parity'
   assert old.get(0x05000000,2)==0x033D and new.get(0x05000000,2)==0,'wrong retail gradient removed; initialized black retained'
   expected_colors={}
   if mode<2:
    for off,step,phase,n,dst in ((0,16,2,11,0x42),(64,8,2,6,0x62),(96,8,3,7,0x82),(152,8,0,7,0xA2),(200,8,3,7,0xC2)):
     for k in range(n):
      v=rows[off+step*phase+k]
      if mode==1:v=(v&0xEEE)>>1
      expected_colors[dst+k*2]=color(v)
   for off in range(2,512,2):
    prior=memory[0x05000000+off]|memory[0x05000001+off]<<8
    assert new.get(0x05000000+off,2)==expected_colors.get(off,prior),'complete final palette source output/gaps'
   diffs={k for k in old.mem.keys()|new.mem.keys() if old.mem.get(k)!=new.mem.get(k)}
   # The unchanged common guard saves14 registers below the outer7-register frame.
   assert u(after,0x6FF60C)==0xE92D5FFF
   assert all(0x05000000<=k<0x05000200 or sp-84<=k<sp for k in diffs),'no nonpalette live-memory divergence'
   assert new.get(0x03004574,2)==old.get(0x03004574,2)
   assert any(dst==0x08017758 for _,dst,_ in new.calls) and any(dst==0x080C9000 for _,dst,_ in new.calls),'actual common queue and copied IRQ path executed'
   assert not new.services,'no service summaries'
   full+=1
 result=dict(status='IRAIRA_OUTER_ROUTE_PORTABLE_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),before_sha256=sha(before),after_sha256=sha(after),spans=2,declared_bytes=64,changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_image_inverse=True,reservation=[FIRST,LIMIT],
  non10_register_flags_and_stack_cases=parity,full_outer_explicit_fixture_cases=full,no_service_summaries=True,source_palette_colors=38,existing_inner_projector_and_stage3_unchanged=True,
  limits=['Explicit reachable source10 owners, task and queue seed the complete native continuation; IRQ code comes from the built ROM. IE/IME are synthetic inputs. No capture files or service summaries are used.',
   'Retired helper stack bytes may differ; live memory parity excludes only bounded dead stack and intended palette destinations.',
   'All-phase inner projector/source proof remains the frozen0112 gate; these64 portable cases cover the new complete outer route, final palette, gates and queue/IRQ continuation. Frozen852F separately retains captured-state supplemental evidence.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
