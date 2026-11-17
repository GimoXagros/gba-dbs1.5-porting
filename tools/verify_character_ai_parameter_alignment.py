"""Independent aligned AI parameters with observed ARM7 odd-LDRH semantics."""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from verify_shoot_static_companion_clear import Machine as Parent
import verify_shoot_caller_resident as scanner
BASE=0x08000000
BEFORE='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST,LIMIT=0xD8AB00,0xD8AC00
ALIASES=(0xC7140,0xC714C,0xC7154,0xC715C,0xC7164,0xC716C,0xC7174,0xC717C,0xC7184,0xC718C,0xC7194,0xC719C,0xC71A4,0xC71AC,0xC71B4)
IDENTITIES=(*range(10),11,13,14)
PROJECTION=((0,2,2),(2,4,2),(4,6,1),(5,7,1),(6,28,1),(7,29,1),(8,30,1),(9,31,1),(10,32,1),(11,33,1),(12,34,2),(13,8,1),(14,9,1),(15,36,1),(16,37,1))
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def norm(i):return 7 if i==11 else i-5 if i>=13 else i

class Arm7(Parent):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.halfword_loads=[]
 def run(self,start,stops,max_steps=16000):
  for _ in range(512):
   try:return super().run(start,stops,max_steps)
   except ValueError as e:
    if str(e)!='immediate halfword transfer':raise
    pc=self.r[15]-8;w=self.get(pc)
    if w in (0xE0010190,0xE0000091):self.r[(w>>16)&15]=(self.r[w&15]*self.r[(w>>8)&15])&0xFFFFFFFF
    elif w==0xE19100B8:
     address=self.r[1]+self.r[8];value=self.get(address&~1,2)
     if address&1:value=((value>>8)|(value<<24))&0xFFFFFFFF
     self.r[0]=value;self.halfword_loads.append((pc,address,value))
    elif w==0xE19500F0:
     address=self.r[5]+self.r[0];need(not address&1,'aligned retained signed load')
     value=self.get(address,2);self.r[0]=(value-65536 if value&32768 else value)&0xFFFFFFFF
    else:raise ValueError(f'unreviewed ARM7 form {pc:08X}:{w:08X}')
    start=pc+4
  raise ValueError('bounded ARM7 continuation')

def fixture(rom,ident,difficulty=0,progress=0,flags=0):
 m=Arm7(rom,seed=7,flags=(flags<<28)|0x1F)
 for a,z in ((0x03002310,0x03002340),(0x03003D30,0x03003DB0),(0x03004D88,0x03004DE0)):
  for x in range(a,z):m.put(x,0,1)
 m.put(0x0300231C,ident,1);m.put(0x0300231F,difficulty,1);m.put(0x0300232E,progress,1)
 m.services[0x08012600]=lambda c:c.r.__setitem__(0,0x37)
 return m

def inverse(before,after,source):
 need(len(before)==len(after)==0x1000000,'16MiB images')
 expected=bytearray(before);blob=b''.join(source[0x782970+17*i:0x782970+17*(i+1)]+b'\x00' for i in range(10))
 expected[FIRST:FIRST+180]=blob
 for a in ALIASES:
  need(u(before,a)==0x08D88800,'old parameter reader')
  struct.pack_into('<I',expected,a,BASE+FIRST)
 need(u(before,0xC6D6C)==0xE3A01011,'old17byte stride')
 struct.pack_into('<I',expected,0xC6D6C,0xE3A01012)
 need(after==expected,'whole image matches only aligned view15aliases andstride')
 return blob

def execute(before,after,source):
 observed=fixture(before,14);observed.r[0]=14
 observed.run(0x080C6D60,{0x080C6D88})
 need(observed.halfword_loads==[(0x080C6D7C,0x08D88899,0x0F0000E4)] and observed.r[0]==0x0F0000E4 and observed.get(0x03004D8A,2)==0xE4,'actual frozen capture row9 rotation and store reproduced')
 oldrows=[];newrows=[];projectioncases=0
 for ident in IDENTITIES:
  index=norm(ident);row=source[0x782970+index*17:0x782970+(index+1)*17]
  for flags in range(16):
   m=fixture(after,ident,flags=flags);m.r[0]=ident;sp=m.r[13]
   m.run(0x080C6D60,{0x080C6EB0})
   need(len(m.halfword_loads)==2 and all(not address&1 for _,address,_ in m.halfword_loads),'both parameter halfwords aligned')
   for src,dst,size in PROJECTION:
    wanted=row[src] if src==12 else int.from_bytes(row[src:src+size],'little')
    need(m.get(0x03004D88+dst,size)==wanted,'all15 source parameter fields exact')
   m.run(0x080C7020,{0x080C7040});need(m.r[13]==sp and m.get(0x03004D92,2)==index*384,'behavior offset unaffected by storage stride')
   projectioncases+=1
  if ident<10:
   q=fixture(before,ident);q.r[0]=ident;q.run(0x080C6D60,{0x080C6EB0})
   oldrows.append(q.get(0x03004D8A,2));newrows.append(h(row,0))
 full=equal=changed=0
 for ident in IDENTITIES:
  for diff in range(3):
   for progress in range(13):
    q=fixture(after,ident,diff,progress);q.run(0x080C6D04,{q.r[14]})
    row=source[0x782970+norm(ident)*17:0x782970+(norm(ident)+1)*17]
    need(q.get(0x03004D8A,2)==h(row,0) and q.get(0x03004D8C,2)==h(row,2),'full initializer source threshold words')
    need(q.get(0x03004D92,2)==norm(ident)*384,'full initializer same behavior bank')
    old=fixture(before,ident,diff,progress);old.run(0x080C6D04,{old.r[14]})
    if norm(ident)%2==0:
     need((q.r,q.cpsr,q.mem)==(old.r,old.cpsr,old.mem),'all even-row complete native states unchanged');equal+=1
    else:
     need(old.get(0x03004D8A,2)==row[0] and q.get(0x03004D8A,2)==h(row,0),'odd-row behavior change explicit and source-correct');changed+=1
    full+=1
 return dict(observed_old_row9_R0='0F0000E4',observed_old_row9_store='00E4',old_first_words=oldrows,source_first_words=newrows,
  projected_all15_fields_cases=projectioncases,full_initializer_cases=full,even_row_fullstate_equal=equal,odd_row_source_correction_cases=changed)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before','after','source','owner','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 before,after,source=(getattr(a,k).read_bytes() for k in ('before','after','source'))
 need((sha(before),sha(source))==(BEFORE,SOURCE),'immutable source inputs')
 inverse(before,after,source);need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'entire fresh reservation blank')
 hits=[]
 for site in ALIASES:
  need(before.find(struct.pack('<I',0x08D88800),site)==site,'known inputalias')
 start=-1
 while True:
  start=before.find(struct.pack('<I',0x08D88800),start+1)
  if start<0:break
  hits.append(start)
 need(tuple(hits)==ALIASES,'complete old parameter aliases')
 ownerraw=a.owner.read_bytes();owner=json.loads(ownerraw)
 need(owner['output_sha256']==BEFORE,'prior AI owner identifiesinput')
 need(owner['reservations']==[[0xD88800,0xD8AB00]],'prior reservation boundary')
 need(all(not max(FIRST,w['offset'])<min(LIMIT,w['offset']+w['size']) for w in owner['writes']),'new reservation disjoint from previouswrites')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 need(not scan(before),'zero inbound references into aligned reservation')
 checks=execute(before,after,source)
 report=dict(status='AI_PARAMETER_ALIGNMENT_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),before_sha256=sha(before),after_sha256=sha(after),
  owner_sha256=sha(ownerraw),declared_spans=17,declared_bytes=244,changed_bytes=sum(x!=y for x,y in zip(before,after)),reservation=[FIRST,LIMIT],whole_image_inverse=True,**checks,
  limitations=['Odd retained rows intentionally change from commercial truncated values to source halfwords; no blanket legacy equality claim.',
   'Behavior/action tables, normalization helper and all nonparameter readers remain byte-exact DEEE.',
   'ARM7 odd-halfword rule is tied to actual D469F3BA capture evidence; no shared interpreter modified.',
   'This verifier does not run the emulator or claim an aligned live witness.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
