"""Author actual-ARM palette checks. Shared mirror ownership remains a caller contract."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_palette_phases import assembly
BASE=0x08000000
CODE=0x08E00000
CTX=0x02001018
PAL=0x05000000
MIRROR=0x0203E000
NATIVE='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
def sha(v):return hashlib.sha256(v).hexdigest().upper()
def convert(v):return sum((2*((v>>s)&15)+bool((v>>s)&15))<<d for s,d in ((8,0),(4,5),(0,10)))
def step(v,up=False):return sum((min(15,((v>>s)&15)+1) if up else max(0,((v>>s)&15)-1))<<s for s in (0,4,8))
class PaletteMachine(Machine):
 def run_checked(self,start,positions):
  end=self.r[14];pc=start
  for _ in range(24000):
   if pc==end:return
   assert pc in positions,f'unlinked {pc:08X}'
   w=self.get(pc)
   if w&0x0E000090==0x00000090:
    self.r[15]=pc+8
    if self.condition(w>>28):
     assert w&0x00400000 and (w>>5)&3==1,'immediate halfword only'
     base,reg=(w>>16)&15,(w>>12)&15
     off=((w>>4)&0xF0)|(w&15)
     new=(self.r[base]+(off if w&0x800000 else -off))&0xFFFFFFFF
     addr=new if w&0x1000000 else self.r[base]
     assert addr%2==0,'aligned halfword'
     if w&0x100000:self.r[reg]=self.get(addr,2)
     else:self.put(addr,self.r[reg],2,True)
     if w&0x200000 or not w&0x1000000:self.r[base]=new
    pc+=4
   else:
    try:pc=super().run(pc,(positions-{pc})|{end},2)
    except ValueError as e:raise ValueError(f'{pc:08X} {w:08X} LR{self.r[14]:08X} end{end:08X}') from e
  raise AssertionError('palette instruction bound')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists()
 source=a.source.read_bytes();native=a.native.read_bytes();assert sha(native)==NATIVE
 names=['m23_palette_snapshot','m23_palette_prepare_fade_in','m23_palette_fade_out','m23_palette_fade_in']
 code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm('\n'.join('.word '+n for n in names)+'\n'+assembly(source),CODE)[0])
 sym=dict(zip(names,struct.unpack_from('<4I',code)))
 rom=bytearray(native);rom[CODE-BASE:CODE-BASE+len(code)]=code
 positions=set(range(CODE+16,CODE+len(code),4))|set(range(0x085C1900,0x085C1960,4))
 calls=0
 def run(m,name):
  nonlocal calls
  old=m.r[4:12].copy();sp=m.r[13]
  m.run_checked(sym[name],positions)
  assert m.r[4:12]==old and m.r[13]==sp,'callee state'
  calls+=1
 def create(flag):
  m=PaletteMachine(rom,seed=3,flags=(flag<<28)|31);m.r[4]=CTX
  for j in range(0x400):m.put(PAL+j,(j*73+19)&255,1);m.put(MIRROR+j,0xA7,1)
  for j in range(0x100):m.put(CTX+j,0xE1,1)
  colors=[(i*37)&4095 for i in range(256)]
  for i,v in enumerate(colors):m.put(PAL+(0 if i<128 else 0x100)+i*2,convert(v),2)
  for i in range(8):m.put(PAL+0x100+i*32,convert(colors[128+i*16]),2);m.put(PAL+0x200+i*32,0x1234,2)
  return m,colors
 for flag in range(16):
  m,c=create(flag);old={k:v for k,v in m.mem.items() if PAL<=k<PAL+0x400}
  run(m,'m23_palette_snapshot')
  assert {k:v for k,v in m.mem.items() if PAL<=k<PAL+0x400}==old
  assert m.get(CTX+0xD4,2)==0
  for i,v in enumerate(c):assert m.get(MIRROR+(0 if i<128 else 0x100)+i*2,2)==convert(v)
  run(m,'m23_palette_fade_out')
  for i,v in enumerate(c[:128]):assert m.get(PAL+i*2,2)==convert(step(v))
 m,c=create(7);run(m,'m23_palette_snapshot')
 for frame in range(32):
  run(m,'m23_palette_fade_out');assert m.r[0]==int(frame==31)
  for i,v in enumerate(c):
   n=(frame+2)//2 if i<128 else (frame+1)//2
   expected=v
   for _ in range(n):expected=step(expected)
   addr=PAL+(0 if i<128 else 0x100)+i*2
   if i>=128 and i%16==0:addr-=0x100
   assert m.get(addr,2)==convert(expected),(frame,i)
 m,c=create(2);untouched={k:v for k,v in m.mem.items() if PAL<=k<PAL+0x400 and not (k<PAL+0x100 or PAL+0x200<=k<PAL+0x300 or (k-PAL-0x100)%32<2 and k<PAL+0x200)}
 run(m,'m23_palette_prepare_fade_in')
 assert m.get(CTX+0xD4,2)==16
 for frame in range(16):
  run(m,'m23_palette_fade_in');assert m.r[0]==int(frame==15)
  for i,v in enumerate(c):
   expected=sum(min((v>>s)&15,frame+1)<<s for s in (0,4,8))
   addr=PAL+(0 if i<128 else 0x100)+i*2
   assert m.get(addr,2)==convert(expected),(frame,i)
   if i>=128 and i%16==0:assert m.get(addr-0x100,2)==convert(expected)
 assert all(m.mem[k]==v for k,v in untouched.items()),'unowned palette bytes unchanged'
 for v in range(4096):
  x=convert(v)
  down=sum(max(0,((x>>s)&31)-2 if ((x>>s)&31)>3 else 0)<<s for s in (0,5,10))
  assert down==convert(step(v))
 result=dict(status='MODE23_PALETTE_PHASES_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),source_sha256=sha(source),native_sha256=sha(native),module_sha256=sha((ROOT/'tools/mode23_palette_phases.py').read_bytes()),linked_code_sha256=sha(code),linked_bytes=len(code),actual_ARM_calls=calls,NZCV_patterns=16,complete_fade_out_calls=32,complete_fade_in_calls=16,source_color_algebra=4096,snapshot_service='actual resident085C1900 instructions',limits=['No game/emulator execution','Shared mirror exclusive lifetime and scene scheduling remain caller obligations','No ROM allocation or installed component'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
