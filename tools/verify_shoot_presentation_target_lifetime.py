#!/usr/bin/env python3
"""Independent captured native receiver-lifetime QA; no builder imports."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine as PriorMachine

BASE,ENTRY,RETURN=0x08000000,0x085C9100,0x09000000
OBJECT,TARGET,SCENE=0x020112B0,0x02011828,0x020121E8
BEFORE='D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
AFTER='84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
EWRAM='64F86BFA9A8EE96086998E2FF7294BDB1D4212457E2F7263EBAE3674B8EF5ACB'
IWRAM='BC10319BFC772FCE8D379D02E78061B9D2C00E21116EA19A47EBE9DCA3929B12'
WORDS=((0x5C9108,0xE5941014,0xE5946014),(0x5C910C,0xE1D103F4,0xE1D603F4),
 (0x5C9120,0xE1D133F6,0xE1D633F6),(0x5C9174,0xE1D103F4,0xE1D603F4),
 (0x5C91A4,0xE1D103F6,0xE1D603F6))
BIOS_REFERENCE='https://raw.githubusercontent.com/mgba-emu/mgba/9660a668f2093cb4aba5983f52bebf8878dc5b8b/src/gba/bios.c'

def need(ok,why):
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def signed(v,bits):return v-(1<<bits)if v&(1<<(bits-1))else v

class Machine(PriorMachine):
 """Run actual MUL/LDRSH and ARM thunk; model only the pinned Thumb SWI6 ABI."""
 special={0x080126D8,0x080126FC,0x08012358,0x0837D5E9}
 def __init__(self,data,snapshot=None,flags=0):
  super().__init__(data,3,(flags<<28)|0xD3)
  self.snapshot=snapshot or {};self.bios=[];self.visited=[]
 def get(self,address,size=4):
  for start,blob in self.snapshot.items():
   if start<=address and address+size<=start+len(blob):
    self.reads.append((address,size))
    return sum(self.mem.get(address+i,blob[address+i-start])<<(8*i)for i in range(size))
  return super().get(address,size)
 def run(self,start,stops,max_steps=16000):
  for _ in range(256):
   pc=super().run(start,set(stops)|self.special,max_steps)
   if pc in stops:return pc
   self.visited.append(pc)
   if pc==0x0837D5E9:
    need(self.rom[0x37D5E8:0x37D5EC]==bytes.fromhex('06DF7047'),'real Thumb SWI6/BX LR bytes')
    n,d=signed(self.r[0],32),signed(self.r[1],32)
    need(d!=0,'division-by-zero path intentionally outside model')
    q=abs(n)//abs(d)
    if (n<0)!=(d<0):q=-q
    remainder=n-q*d
    self.bios.append((n,d,q,remainder,self.r[6]))
    self.r[0],self.r[1],self.r[3]=q&0xFFFFFFFF,remainder&0xFFFFFFFF,abs(q)
    self.cpsr=(self.cpsr&0x0FFFFFFF)|0xB0000000
    start=self.r[14];continue
   word=self.get(pc);self.r[15]=pc+8
   if pc==0x08012358:
    need(word==0xE19800F9,'actual register-offset signed-halfword load')
    self.r[0]=signed(self.get(self.r[8]+self.r[9],2),16)&0xFFFFFFFF
   else:
    need(word==0xE0000093,'actual non-S MUL r0,r3,r0')
    self.r[0]=(self.r[0]*self.r[3])&0xFFFFFFFF
   start=pc+4
  raise ValueError('bounded actual helper transitions')

def structure(before,after):
 need(len(before)==len(after)==0x800000,'complete8MiB ROM extent')
 inverse=bytearray(after)
 for a,old,new in WORDS:
  need(u(before,a)==old and u(after,a)==new,'independent five instruction encodings')
  struct.pack_into('<I',inverse,a,old)
 need(inverse==before,'entire five-word inverse; every other byte identical')
 need(sha(before[0x5C9100:0x5C9208])=='A150F3C5A715F6131D6DB358676C75E011482B14C6BF331E807076CF2395CB0D','original homing body pin')
 return {'declared_bytes':20,'changed_bytes':sum(a!=b for a,b in zip(before,after)),
  'whole_ROM_inverse':True,'new_code_or_cave':False}

def source_and_helpers(before,after,retail,source):
 ins=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(source[0x7735D4:0x773650],0x7735D4))
 relevant=[(x.address,x.mnemonic,x.op_str)for x in ins if x.address in(0x7735D4,0x773611,0x773624)]
 need(relevant==[(0x7735D4,'mov','bx, word ptr [si + 0x12]'),
  (0x773611,'mov','ax, word ptr [bx + 0x26]'),(0x773624,'mov','ax, word ptr [bx + 0x28]')],
  'source receiver BX spans angle/trig and both completion reads')
 need(u(after,0x5C9100)==0xE92D5FFF and u(after,0x5C91F4)==0xE8BD5FFF,'incoming/outgoing full r0-r12/LR frame including r6')
 decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM);decoder.detail=True
 calls=set()
 for a,z in ((0x12560,0x12600),(0x12650,0x12710),(0x1233C,0x12360)):
  need(before[a:z]==retail[a:z]==after[a:z],'actual callee instruction identity')
  rows=list(decoder.disasm(after[a:z],BASE+a));need(sum(i.size for i in rows)==z-a,'whole helper decode')
  for i in rows:
   need('r6'not in[i.reg_name(r)for r in i.regs_access()[1]],'r6 preserved by every instruction on closed helper bodies')
   if i.mnemonic=='bl':calls.add(int(i.op_str[1:],16))
 need(calls=={0x08012650,0x080126A4,0x0837DB3C},'closed angle helper direct-call graph')
 need(u(after,0x126DC)==u(after,0x12700)==0xE1A01009,'both actual division branches overwrite r1')
 need(after[0x37DB3C:0x37DB48]==bytes.fromhex('00C09FE51CFF2FE1E9D53708'),'real ARM thunk to Thumb SWI6')
 return {'source_receiver':'BX','native_persistent_receiver':'r6',
  'helper_r6_preservation':'All actual instructions in closed angle/trig bodies decoded; SWI6 callee-preserved ABI qualified separately',
  'BIOS_reference':BIOS_REFERENCE,'BIOS_body_executed':False,'divide_zero_modeled':False}

def fixture(data,snapshot,flags=0,delta=None,offset=None):
 m=Machine(data,snapshot,flags);m.r[4],m.r[14]=OBJECT,RETURN
 if delta is not None:
  for a,v in((0x34,delta[0]),(0x36,delta[1])):
   m.put(OBJECT+a,(m.get(TARGET+a,2)-v)&0xFFFF,2)
 if offset is not None:m.put(OBJECT+0xA0,offset&0xFFFF,2)
 return m

def effects(m,sp):return [w for w in m.writes if not sp-0x200<=w[0]<sp]

def actual_case(before,after,snapshot,flags=0):
 old,new=fixture(before,snapshot,flags),fixture(after,snapshot,flags)
 need(old.get(OBJECT)==ENTRY and old.get(OBJECT+0x14)==TARGET and old.get(SCENE)==0x085C8400,'actual typed callback/target/waiting scene')
 need([old.get(a,2)for a in(OBJECT+0x34,OBJECT+0x36,TARGET+0x34,TARGET+0x36)]==[0x13A1,0xCFB,0x13A1,0xD2B],'actual captured inside-box geometry')
 initial=new.r[:15];sp=new.r[13]
 old.run(ENTRY,{0x085C9174});new.run(ENTRY,{0x085C9174})
 need(old.r[1]==0 and new.r[6]==TARGET,'actual nested division loses original r1 while repaired r6 remains target')
 need(effects(old,sp)==effects(new,sp),'repair does not alter angle/trig velocity writes')
 need(not any(a==0x03004508 for a,v,n in old.writes),'original stops before invalid receiver access without invented BIOS memory')
 new.run(0x085C9174,{RETURN})
 need(new.r[:15]==initial,'actual callback restores all incoming saved general registers/SP/LR')
 need(new.get(0x03004508,2)==0x12 and new.get(OBJECT+0xA,2)&0x8000
  and new.get(OBJECT+4,2)&0x20,'natural completion event and real presentation release markers')
 need(new.get(OBJECT-0x18)==u(after,0x352560) and any(c[1]==0x083524C4 for c in new.calls),
  'real native pool-release callback installed on actual owning header')
 return old,new

def natural_scene_progress(before,after,snapshot):
 _,new=actual_case(before,after,snapshot)
 old=fixture(before,snapshot)
 for m in(old,new):
  m.put(0x0300133C,SCENE);m.r[14]=RETURN
 need(old.get(SCENE+0x18+0x50,2)==6,'actual waiting timer6')
 need(old.run(0x085C8400,{RETURN,0x085C8E00})==RETURN and old.get(SCENE+0x18+0x50,2)==6,'original scene remains waiting with absent natural event')
 need(new.run(0x085C8400,{RETURN,0x085C8E00})==0x085C8E00
  and new.get(SCENE+0x18+0x50,2)==5 and new.get(0x03004508,2)&0x10==0,
  'repaired real event naturally consumed by scene, timer6 to5, next spawn boundary')
 return {'old_scene_waits':True,'repaired_natural_event_consumed':True,
  'scene_timer_before':6,'scene_timer_after':5,'actual_next_spawn_entry':0x085C8E00,
  'new_spawn_body_executed':False}

def cases(before,after,snapshot):
 for flags in range(16):actual_case(before,after,snapshot,flags)
 count=0;visited=set()
 for x in(-257,-256,-255,0,255,256,257):
  for y in(-257,-256,-1,1,256,257):
   for flags in(0,5,10,15):
    m=fixture(after,snapshot,flags,(x,y));initial=m.r[:15];m.run(ENTRY,{RETURN})
    arrived=abs(x)<=256 and abs(y)<=256
    need(bool(m.get(0x03004508,2)&0x10)==arrived,'exact inclusive +/-100 completion boundary after actual helper calls')
    need(m.r[:15]==initial,'full frame restoration for every inside/outside quadrant')
    need(any(c[1]==0x083524C4 for c in m.calls)==arrived,'release only after true target arrival')
    visited.update(m.visited);count+=1
 need({0x080126D8,0x080126FC,0x08012358,0x0837D5E9}<=visited,'both real division arms and actual table trig executed')
 # Native scale branch at4000 and all four angle quadrants, independently of presentation box.
 helper_count=0
 for x,y in((1,0),(0,1),(1,2),(2,1),(0x3FFF,1),(0x4000,1),(0x4001,0x7FFF)):
  for sx,sy in((1,1),(-1,1),(1,-1),(-1,-1)):
   m=Machine(after);m.r[6]=TARGET;m.r[14]=RETURN;sp=m.r[13]
   m.put(sp,x*sx&0xFFFFFFFF);m.put(sp+4,y*sy&0xFFFFFFFF)
   m.run(0x08012560,{RETURN})
   need(m.r[6]==TARGET and m.r[13]==sp and m.r[14]==RETURN,'actual angle all quadrant/4000 branch preserves r6/SP/LR')
   helper_count+=1
 return {'actual_captured_pose_NZCV_cases':16,'box_boundary_quadrant_cases':count,
  'angle_quadrant_scale_branch_cases':helper_count,'actual_special_sites':sorted(visited),
  'service_model':'Only Thumb SWI6 arithmetic/r0,r1,r3 outputs; native ARM thunk, angle, trig and release execute instructions'}

def controls(before,after,snapshot):
 rows=[]
 def reject(name,fn):
  try:fn()
  except ValueError:rows.append(name)
  else:raise ValueError('negative survived '+name)
 for a,old,new in WORDS:
  bad=bytearray(after);struct.pack_into('<I',bad,a,old)
  reject('missing receiver substitution '+hex(a),lambda:structure(before,bad))
 for name,a in(('offtarget event store',0x5C91E0),('angle body changed',0x126DC),('entry selector changed',0x6FF380)):
  bad=bytearray(after);bad[a]^=1;reject(name,lambda:structure(before,bad))
 for name,a,w in(('postcall X reload uses scratch again',0x5C9174,0xE1D103F4),
  ('postcall Y reload uses scratch again',0x5C91A4,0xE1D103F6),
  ('completion event missing',0x5C91E0,0xE1A00000),('outer r6 not restored',0x5C91F4,0xE8BD5FBF)):
  bad=bytearray(after);struct.pack_into('<I',bad,a,w)
  reject(name,lambda:actual_case(before,bytes(bad),snapshot))
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in('candidate','predecessor','retail','source'):p.add_argument(k,type=Path)
 p.add_argument('--capture',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists(),'fresh independent report path')
 need(sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes())=='CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943','frozen independent primitive')
 after,before,retail,source,mb=[getattr(a,k).read_bytes()for k in('candidate','predecessor','retail','source','manifest')]
 need((sha(before),sha(retail),sha(source))==(BEFORE,RETAIL,SOURCE),'exact inputs')
 er,ir=(a.capture/'ewram.bin').read_bytes(),(a.capture/'iwram.bin').read_bytes()
 need((sha(er),sha(ir))==(EWRAM,IWRAM),'frozen actual completed capture RAM')
 snapshot={0x02000000:er,0x03000000:ir}
 st=structure(before,after);binding=source_and_helpers(before,after,retail,source)
 semantic=cases(before,after,snapshot);progress=natural_scene_progress(before,after,snapshot)
 negative=controls(before,after,snapshot)
 manifest=json.loads(mb);need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==sha(after)==AFTER,'frozen candidate identity')
 report=dict(schema=1,status='INDEPENDENT_PRESENTATION_RECEIVER_LIFETIME_PASS',candidate_sha256=sha(after),
  predecessor_sha256=sha(before),verifier_sha256=sha(Path(__file__).read_bytes()),manifest_sha256=sha(mb),
  structure=st,source_and_ABI=binding,actual_ARM=semantic,natural_scene_progress=progress,negative_controls=negative,
  capture_sha256={'ewram.bin':sha(er),'iwram.bin':sha(ir)},BIOS_machine_code_executed=False,
  emulator_or_save_access=False,full_entry_runtime_claim=False,main_modified=False,old_full_suites_rerun=False)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS: natural scene6→5; {semantic["box_boundary_quadrant_cases"]} arrival cases; {len(negative)} controls')

if __name__=='__main__':main()
