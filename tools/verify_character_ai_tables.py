"""Independent source AI table closure and actual native consumer checks."""
import argparse
import hashlib
import json
import struct
import sys
import types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16,CS_ARCH_ARM,CS_MODE_ARM
from verify_shoot_static_companion_clear import Machine as Parent
import verify_shoot_caller_resident as scanner

BASE=0x08000000
BEFORE='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OLD='58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
FIRST,LIMIT=0xD88800,0xD8AB00
PARAM,HELPER,BEHAVIOR,ACTION=0xD88800,0xD888AC,0xD88900,0xD89800
PREF=(0xC7140,0xC714C,0xC7154,0xC715C,0xC7164,0xC716C,0xC7174,0xC717C,0xC7184,0xC718C,0xC7194,0xC719C,0xC71A4,0xC71AC,0xC71B4)
AREF={0xC6A2C:14,0xC6A3C:0,0xC6B2C:0,0xC6B34:0,0xC6BB4:16,0xC6BB8:17,0xC6BBC:16}
DOMAIN=(*range(8),11,13,14)
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def norm(i):return 7 if i==11 else i-5 if i>=13 else i
def branch(a,z):return 0xEA000000|(((z-a-8)//4)&0xFFFFFF)

class Machine(Parent):
 """Execute retained MUL, register halfwords and actual halfword copy loop."""
 def run(self,start,stops,max_steps=16000):
  for _ in range(1024):
   try:return super().run(start,stops,max_steps)
   except ValueError as e:
    if str(e)!='immediate halfword transfer':raise
    pc=self.r[15]-8;w=self.get(pc)
    if w in (0xE0010190,0xE0000091,0xE0010093):
     self.r[(w>>16)&15]=(self.r[w&15]*self.r[(w>>8)&15])&0xFFFFFFFF
    elif w in (0xE19100B8,0xE19100F8):
     v=self.get(self.r[1]+self.r[8],2)
     self.r[0]=(v-65536 if w==0xE19100F8 and v&32768 else v)&0xFFFFFFFF
    elif w==0xE19500F0:
     v=self.get(self.r[5]+self.r[0],2);self.r[0]=(v-65536 if v&32768 else v)&0xFFFFFFFF
    elif w in (0xE0D480B2,0xE0C580B2):
     if w==0xE0D480B2:self.r[8]=self.get(self.r[4],2);self.r[4]+=2
     else:self.put(self.r[5],self.r[8],2,True);self.r[5]+=2
    else:raise ValueError(f'unreviewed native form {pc:08X}:{w:08X}')
    start=pc+4
  raise ValueError('native extension budget')

def source_contract(before,s,o,g):
 params=s[0x782970:0x782A1A];behavior=s[0x74EB2A:0x74FA2A];actions=bytearray(s[0x74D89A:0x74EB2A])
 need(params[:136]==o[0x3C3250:0x3C32D8]==before[0xC6C7C:0xC6D04],'eight retained parameter rows')
 need(before[0xC3FC0:0xC4BC0]==o[0x3AB1EE:0x3ABDEE],'eight native behavior rows')
 need(before[0xC3FC0:0xC4BC0]==g[0xC3FC0:0xC4BC0] and before[0xC4FC4:0xC61E8]==g[0xC4FC4:0xC61E8],'retail data lineage')
 need([i for i in range(258*18) if actions[i]!=o[0x3A9FCA+i]]==[216,2664],'two source retained action changes')
 need([i for i in range(258*18) if before[0xC4FC4+i]!=o[0x3A9FCA+i]]==[769],'single meaningful native mask exception')
 need(h(actions,42*18+12)==0xFF7E and h(before,0xC4FC4+42*18+12)==0x007E,'explicit mask values')
 actions[769]=0
 lines=[(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(s[0x782B46:0x782B63],0x782B46)]
 need(lines==[('xor','ah, ah'),('cmp','ax, 0xb'),('jne','0x782b53'),('mov','ax, 7'),('jmp','0x782b5b'),('cmp','ax, 0xd'),('jb','0x782b5b'),('sub','ax, 5'),('push','ax'),('mov','bx, 0x11'),('mul','bx'),('mov','bx, ax')],'source mapping before pushed identity')
 need(s[0x782D23:0x782D2A].hex()=='58f7e326a39606','source saved identity reaches behavior offset')
 need(s[0x74D45E:0x74D46A].hex()=='26031e960603da2e8b873a18','source behavior reader')
 cells=struct.unpack('<1920H',behavior)
 need(max(cells)==262 and min(cells)==0,'all behavior indices inside264 actions')
 need(all(h(actions,i*18+14)<264 for i in range(264)),'all action continuations closed')
 need(sorted({h(actions,i*18)&255 for i in range(264)})==[0,1,2,3,5,6,7,8,9,10],'source low-state population excludes15')
 need(all(actions[i*18+16]<11 for i in range(264)),'sub-dispatch index population')
 need(struct.unpack_from('<3H',s,0x740CD2)==(0x3D8,0x416,0x46E),'source normal/other/boss paths')
 need(s[0x740C97:0x740CB3].hex()=='a15000803e5c0007750fc706ce035046c706d2032846050200a3d003','source stage7 selects boss mode')
 need(struct.unpack_from('<3I',before,0xD1888)==(0x080D18B8,0x080D1918,0x080D19AC),'native normal/other/boss paths')
 need(u(before,0xD1834)==0xE3590007 and u(before,0xD1850)==0xE2800002,'native stage7 adds2 to mode')
 native=Cs(CS_ARCH_ARM,CS_MODE_ARM)
 boss=list(native.disasm(before[0xD19AC:0xD19F0],0x080D19AC))
 need([i.op_str for i in boss if i.mnemonic=='bl']==['#0x837db00','#0x8352b24'],'boss constructor path skips ordinary AI initializer')
 need(u(before,0xD19C8)==0xE3A0800C and u(before,0xD19D8)==0xE3A08003,'retained native dedicated boss identity/kind')
 need(u(before,0xD190C)==0xEB0A9153,'normal branch calls AI375E60')
 return params,behavior,bytes(actions)

def inverse(before,after,data):
 need(len(before)==len(after)==0x1000000,'16MiB extent')
 expected=bytearray(before);writes=[]
 def put(a,b):expected[a:a+len(b)]=b;writes.append((a,len(b)))
 params,behavior,actions=data
 for a,b in ((PARAM,params),(BEHAVIOR,behavior),(ACTION,actions)):put(a,b)
 helper=struct.pack('<8I',0xE52D8004,0xE10F8000,0xE350000D,0x22400005,0xE128F008,0xE49D8004,0xE52D0004,branch(HELPER+28,0xC6D6C))
 put(HELPER,helper);put(0xC6D68,struct.pack('<I',branch(0xC6D68,HELPER)))
 for a in PREF:put(a,struct.pack('<I',BASE+PARAM))
 put(0xC658C,struct.pack('<I',BASE+BEHAVIOR))
 for a,off in AREF.items():put(a,struct.pack('<I',BASE+ACTION+off))
 need(after==expected,'entire corrected image independently reconstructed')
 need(len(writes)==28 and sum(n for _,n in writes)==8890,'exact declared write scope')
 return writes

def aliases(before):
 found=[{}, {}, {}];ranges=((0xC6C7C,136),(0xC3FC0,3072),(0xC4FC4,258*18))
 for align in range(4):
  end=len(before)-(len(before)-align)%4
  for n,(v,) in enumerate(struct.iter_unpack('<I',before[align:end])):
   for k,(a,size) in enumerate(ranges):
    if BASE+a<=v<BASE+a+size:found[k][align+4*n]=v-BASE-a
 need(found==[dict.fromkeys(PREF,0),{0xC658C:0},AREF],'complete aligned and unaligned alias census')

def cases(before,after,data):
 params,behavior,actions=data;helpercases=initcases=0
 for ident in DOMAIN:
  for flags in range(16):
   m=Machine(after,seed=3,flags=(flags<<28)|0x1F);m.r[0]=7 if ident==11 else ident
   regs=m.r[:];psr=m.cpsr;m.run(BASE+HELPER,{0x080C6D6C})
   need(m.r[0]==norm(ident) and m.get(m.r[13])==norm(ident) and m.r[13]==regs[13]-4,'actual normalized push')
   need(m.r[1:13]==regs[1:13] and m.r[14]==regs[14] and m.cpsr==psr,'helper ABI and16NZCV')
   helpercases+=1
  m=Machine(after);m.r[0]=ident;sp=m.r[13]
  m.put(0x03003D82,0,2)
  for a in range(0x03004D88,0x03004DAE):m.put(a,0xA5,1)
  m.run(0x080C6D60,{0x080C6EB0});row=params[norm(ident)*17:norm(ident)*17+17]
  for x,y,n in ((0,2,2),(2,4,2),(4,6,1),(5,7,1),(6,28,1),(7,29,1),(8,30,1),(9,31,1),(10,32,1),(11,33,1),(12,34,2),(13,8,1),(14,9,1),(15,36,1),(16,37,1)):
   value=row[x] if x==12 else int.from_bytes(row[x:x+n],'little')
   need(m.get(0x03004D88+y,n)==value,'all15 actual parameter copy fields')
  m.run(0x080C7020,{0x080C7040})
  need(m.get(0x03004D92,2)==norm(ident)*384 and m.r[13]==sp,'saved identity actual downstream product')
  initcases+=1
 for ident in range(10):
  for cell in range(192):
   m=Machine(after);m.put(0x03004D92,ident*384,2);m.r[1]=cell*2;m.r[3]=0
   m.run(0x080C64D4,{0x080C64EC})
   need(m.r[0]==h(behavior,ident*384+cell*2),'actual behavior selected ordinal')
   need(m.r[1]+m.r[8]==BASE+BEHAVIOR+ident*384+cell*2,'bounded physical behavior read')
 for index in range(264):
  for start,stop in ((0x080C6978,0x080C69BC),(0x080C6A5C,0x080C6AB0)):
   m=Machine(after);m.r[1]=index*18;m.put(0x03003D68,index,2)
   m.put(0x03003D6C,0,2)
   m.run(start,{stop})
   need(bytes(m.get(0x03003D50+i,1) for i in range(18))==actions[index*18:index*18+18],'actual9halfword native action copy')
   need(m.get(0x03003D6A,2)==h(actions,index*18+14),'actual continuation field')
  m=Machine(after);m.r[1]=index*18
  stop=m.run(0x080C6B54,{0x080C6B84,0x080C6C34})
  kind,value=actions[index*18+16:index*18+18]
  if kind:need(stop==0x080C6B84 and m.r[1]==kind and m.r[0]==value,'actual interior byte alias value/kind')
  else:need(stop==0x080C6C34,'zero byte kind bypass')
 # All meaningful old action data retained except the two source revisions.
 need([i for i in range(258*18) if before[0xC4FC4+i]!=actions[i]]==[216,2664],'native exception and all other old action bytes retained')
 full=parity=0
 for ident in DOMAIN:
  for difficulty in range(3):
   for progress in range(13):
    def fixture(rom):
     q=Machine(rom,seed=5,flags=0xA000001F)
     for x,z in ((0x03002310,0x03002340),(0x03003D30,0x03003DB0),(0x03004D88,0x03004DE0)):
      for at in range(x,z):q.put(at,0,1)
     q.put(0x0300231C,ident,1);q.put(0x0300231F,difficulty,1);q.put(0x0300232E,progress,1)
     q.services[0x08012600]=lambda c:c.r.__setitem__(0,0x37)
     return q
    q=fixture(after);q.run(0x080C6D04,{q.r[14]})
    need(q.get(0x03004D92,2)==norm(ident)*384,'full initializer saved behavior row')
    row=params[norm(ident)*17:norm(ident)*17+17]
    for off in range(6):need(q.get(0x03004DA4+off,1)==row[6+off],'full initializer threshold fields retained')
    if ident<8 or ident==11:
     prior=fixture(before);prior.run(0x080C6D04,{prior.r[14]})
     need((prior.r,prior.cpsr,prior.mem)==(q.r,q.cpsr,q.mem),'old identity full initializer parity')
     parity+=1
    full+=1
 return dict(helper_16NZCV_cases=helpercases,parameter_and_saved_identity_cases=initcases,
   full_initializer_cases=full,legacy_full_state_cases=parity,
   actual_behavior_load_cases=1920,actual_action_copy_cases=528,actual_interior_byte_reader_cases=264)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before','after','source','old','gba','report'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--owners',type=Path,nargs=6,required=True);a=p.parse_args();need(not a.report.exists(),'fresh report')
 before,after,s,o,g=(getattr(a,k).read_bytes() for k in ('before','after','source','old','gba'))
 need(tuple(map(sha,(before,s,o,g)))==(BEFORE,SOURCE,OLD,RETAIL),'pinned immutable source inputs')
 data=source_contract(before,s,o,g);aliases(before);writes=inverse(before,after,data)
 need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'entire new reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 need(not scan(before),'zero encoded inbound references with no exceptions')
 ownerpins=('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91','4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6','64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD','54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55','6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C','06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230')
 retained=0
 for path,pin in zip(a.owners,ownerpins):
  raw=path.read_bytes();need(sha(raw)==pin,'prior owner pin');owner=json.loads(raw)
  for w in owner['writes']:
   x,z=w['offset'],w['offset']+w['size'];need(before[x:z]==after[x:z],'prior owner bytes retained');need(not max(x,FIRST)<min(z,LIMIT),'prior owner disjoint');retained+=1
  for x,z in owner.get('reservations',[]):need(not max(x,FIRST)<min(z,LIMIT),'prior reservation disjoint')
 checks=cases(before,after,data)
 report=dict(status='CHARACTER_AI_TABLES_INDEPENDENT_PASS',before_sha256=sha(before),after_sha256=sha(after),checker_sha256=sha(Path(__file__).read_bytes()),
  declared_spans=28,declared_bytes=8890,changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_image_inverse=True,
  reservation=[FIRST,LIMIT],inbound_references=[],prior_writes_preserved=retained,normal_identity_domain=list(DOMAIN),**checks,
  dedicated_stage7_boss_skips_ordinary_initializer=True,
  limitations=['Native row42 +0C input mask007E retained instead of sourceFF7E; meaningful full-word source parity exception.',
   'Raw IDs10/12/15 do not belong to ten-row ordinary initializer domain; dedicated boss route ownership is separate.',
   'No emulator execution or complete campaign success claimed.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
