"""Independent Iraira source assets and native palette/display owner closure."""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
import verify_train_graphics_repair as native
BASE=0x08000000
BEFORE='E6B2C30E3E7D880BFFEE82A3201D0F69AE3DE0EBBEE5B523D24DD6D03FA08CF4'
AFTER='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST,LIMIT=0xD8AC00,0xD8B400
BG=(0x582548,0x58254C,0x582554,0x582560,0x582564,0x582568,0x582570,0x58257C)
SPANS=((0xD8AC00,140),(0xD8AD00,380),(0xD8AF00,52),(0xD8AF40,52),(0xD8AF80,32),(0x582544,4),*((x,4) for x in BG),(0x583C00,4),(0xC4BC0,4),(0xC4CC4,4),(0x582528,4),(0x583B28,4),(0x598000,222),(0x598100,16384),(0x59C100,8064))
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def rgb(v):
 r,g,b=(v>>8)&15,(v>>4)&15,v&15
 return (2*r+bool(r))|((2*g+bool(g))<<5)|((2*b+bool(b))<<10)
def target(b,a):
 w=u(b,a);need(w&0x0F000000==0x0A000000,'unconditional B instruction');n=w&0xFFFFFF
 return a+8+(n-0x1000000 if n&0x800000 else n)*4

def source_and_scope(before,after,s,manifest,alignment):
 need(s[0x75F9EE:0x75FA63]==s[0x75FA64:0x75FAD9],'exact117byte source display callback identity')
 need(before[0x628300:0x628424]==after[0x628300:0x628424],'proven native display and compact clear retained')
 need(u(after,0x583B28)==0x08628300,'Iraira queues source-equivalent display callback')
 need(u(after,0x582544)==0 and u(before,0x582544)==0x23D,'source black backdrop replaces clone value')
 need(s[0x77CF88:0x77CF8D].hex()=='be80038904','source common backdrop zero store')
 need(u(after,0x377C18)==0x03002654 and u(after,0x377BF0)==0xE1D800B0 and u(after,0x377BF8)==0xE1C800B0,'native backdrop copied to palette0')
 for k,a in enumerate(BG):need(u(after,a)==(0x03002388 if k<4 else 0x03002338),'source37Screen2/source38Screen1 owner swap')
 for a,t in ((0x583C00,0xD8AC00),(0xC4BC0,0xD8AF00),(0xC4CC4,0xD8AF40),(0x582528,0xD8AF80)):
  need(target(after,a)==t,'native replacement branch')
 need([(w['offset'],w['size']) for w in manifest['writes']]==list(SPANS),'exact22declared spans')
 inverse=bytearray(after)
 for w in manifest['writes']:
  a,z=w['offset'],w['offset']+w['size']
  need(sha(before[a:z])==w['before_sha256'] and sha(after[a:z])==w['after_sha256'],'declared actual span hashes')
  inverse[a:z]=before[a:z]
 need(inverse==before,'whole-file inverse and no undeclared changes')
 need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'newcode reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 need(not scan(before),'zero conservative inbound references')
 for w in alignment['writes']:
  a,z=w['offset'],w['offset']+w['size'];need(after[a:z]==before[a:z]==bytes.fromhex(w['after_hex']),'all alignedAIwrites retained')
 need(all(not max(a,FIRST)<min(z,LIMIT) for a,z in alignment['reservations']),'alignedAI reservation disjoint')
 for i in range(111):need(h(after,0x598000+i*2)==rgb(h(s,0x4C60E2+i*2)),'all111 dedicated source palette colors')
 for tile in range(512):
  for y in range(8):
   for x in range(8):
    v=sum(((s[0x4C61C0+tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
    actual=(after[0x598100+tile*32+y*4+x//2]>>(4*(x&1)))&15
    need(v==actual,'source planar pixel equals installed native pixel')
 for k in range(8):
  ident=37+k//4;desc=0x3B4DD0+24*ident
  need((h(s,desc),h(s,desc+2),h(s,desc+10))==(2,2,0x360E),'source2x2resource segment')
  row=0x3B4970+h(s,desc+8)+4*(k%4);bank,mode,off=struct.unpack_from('<BBH',s,row)
  physical=(bank&127)*65536+0x360E*16+off-0x30000
  need(bank==0xCC and mode==1 and physical==0x4CA1C0+k*1008,'source actual map descriptor')
  for cell in range(504):
   v=h(after,0x59C100+1008*k+cell*2)
   restored=(v&511)|((v&512)<<4)|((v&3072)<<4)|((v>>12)<<9)
   need(restored==h(s,physical+cell*2),'all4032native map entries invert to source')
 rows=struct.unpack_from('<256H',s,0x76AD13)
 need([h(after,0x584200+2*i) for i in range(256)]==[rgb(v) for v in rows],'source animator table retained')
 return rows

def fixture(after):
 m=Machine(after,seed=6,flags=0xA000001F)
 for x,z in ((0x03003D20,0x03003D60),(0x03002560,0x03002580),(0x05000000,0x05000200)):
  for at in range(x,z):m.put(at,0xA5,1)
 return m

def cases(after,rows):
 # The compact clear owns exactly32bytes, adjacent AI and display phase survive.
 m=fixture(after);original=m.mem.copy();regs=m.r[:];m.run(0x08628400,{m.r[14]})
 need(all(m.get(a,1)==0 for a in range(0x03003D30,0x03003D50)),'compact initializer clears32bytes')
 need(all(m.mem[a]==v for a,v in original.items() if not 0x03003D30<=a<0x03003D50),'initializer adjacent owners preserved')
 need(m.r[:15]==regs[:15],'compact initializer ABI')
 state=[0]*5
 for n in range(3360):
  for i,v in enumerate(state):m.put(0x03003D30+i*2,v,2)
  before=m.mem.copy();m.writes=[];m.run(0x08D8AC00,{m.r[14]})
  tick,delay,a,b,c=state;tick=(tick+1)%8;delay+=1
  if tick==0:a=(a+1)%4
  if tick in (0,4):b=(b+1)%7
  if delay==5:delay=0;c=(c+1)%6
  state=[tick,delay,a,b,c]
  need([m.get(0x03003D30+i*2,2) for i in range(5)]==state,'full3360tick source period')
  need(all(m.mem[x]==v for x,v in before.items() if not 0x03003D30<=x<0x03003D3A),'cycle only five compact counters')
 need(state==[0]*5,'complete phase period closes')
 count=0
 for a in range(4):
  for b in range(7):
   for c in range(6):
    for dim in (0,1):
     q=fixture(after);original=q.mem.copy();regs=q.r[:]
     q.put(0x03003D34,a,2);q.put(0x03003D36,b,2);q.put(0x03003D38,c,2)
     q.put(0x03004506,0,2);q.put(0x0300260B,0,1);q.put(0x03004529,dim,1)
     q.run(0x08D8AD00,{q.r[14]});expected={}
     for start,step,phase,n,dst in ((0,16,a,11,0x42),(64,8,a,6,0x62),(96,8,b,7,0x82),(152,8,c,7,0xA2),(200,8,b,7,0xC2)):
      for i in range(n):
       value=rows[start+step*phase+i]
       if dim:value=sum((((value>>shift)&15)//2)<<shift for shift in (0,4,8))
       expected[dst+2*i]=rgb(value)
     need(all(q.get(0x05000000+off,2)==expected.get(off,0xA5A5) for off in range(0,512,2)),'all38source colors and untouched palette gaps')
     need(q.r[:15]==regs[:15],'projector register ABI')
     need(q.get(0x03002568,2)==0xA5A5 and q.get(0x03003D50,4)==0xA5A5A5A5,'display phase and AI untouched by projector')
     count+=1
 for flags,disabled in ((16,0),(0,1),(0xFFFF,255)):
  q=fixture(after);q.put(0x03004506,flags,2);q.put(0x0300260B,disabled,1);q.run(0x08D8AD00,{q.r[14]})
  need(all(q.get(0x05000000+i,1)==0xA5 for i in range(512)),'palette suppression gates')
 routecount=0
 for physical in range(12):
  for logical in range(12):
   for start,good,old in ((0x08D8AF00,0x08628400,0x08628680),(0x08D8AF40,0x08D8AD00,0x086286C0)):
    q=fixture(after);q.put(0x0300231E,physical,1);q.services[0x080D1C78]=lambda m:m.r.__setitem__(0,logical)
    regs=q.r[:];end=q.run(start,{good,old})
    need(end==(good if physical!=11 and logical==10 else old) and q.r[:15]==regs[:15],'stage10 routes preserve all other paths includingShoot')
    routecount+=1
 slots=native.SLOTS
 try:
  native.SLOTS=((0x582400,0x130,0x50),(0xD8AF80,28,4));w=native.Walker(after);w.r[11]=0
  w.write(0x03002568,0xCCDD,2,False);w.write(0x0300256A,0xBEEF,2,False);w.run(0x08582400)
  for owner,resource,mapbase,ports in ((0x03002338,26,0x0600F000,0x030012B8),(0x03002388,25,0x0600F800,0x030012BA)):
   need([w.read(owner+i,4) for i in (0,4,8,0x24)]==[ports,ports+1,mapbase,u(after,0x580000+resource*24+8)],'actual twoBG initializer source owner map/port routing')
  need(w.read(0x03002654,2)==0 and w.read(0x03002568,4)==0xBEEF0000,'black backdrop and isolated phase initialization')
  need(w.r[13:15]==[0x03007000,0x01000000],'clone tail stack balance')
 finally:native.SLOTS=slots
 return dict(cycle_ticks=3360,projector_phase_dim_cases=count,suppression_cases=3,route_cases=routecount,full_initializer_cases=1)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before','after','source','manifest','alignment_owner','report'):p.add_argument('--'+k.replace('_','-'),dest=k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 before,after,s=(getattr(a,k).read_bytes() for k in ('before','after','source'))
 need(tuple(map(sha,(before,after,s)))==(BEFORE,AFTER,SOURCE),'pinned complete inputs')
 raw=a.manifest.read_bytes();owner=a.alignment_owner.read_bytes()
 need(sha(raw)=='29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900' and sha(owner)=='4AFD13AEC814255B94F21D1C72D26EBF81A75E6F5FA7CC2FE89D028C48A2FA66','frozen author manifests')
 rows=source_and_scope(before,after,s,json.loads(raw),json.loads(owner));proof=cases(after,rows)
 report=dict(status='IRAIRA_RENDER_CONSUMERS_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),before_sha256=sha(before),after_sha256=sha(after),
  spans=len(SPANS),declared_bytes=sum(z for _,z in SPANS),changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_image_inverse=True,
  aligned_AI_writes_preserved=17,source_map_entries=4032,source_pixels=32768,source_palette_colors=111,
  owner=[0x03003D30,0x03003D50],phase_owner=0x03002568,black_backdrop=True,**proof,
  limitations=['Native copy/BG services in initializer use existing explicit summaries; no emulator or visual result claimed.',
   'Existing Waterfall display callback is reused byte-exact with identical source body; prior full callback audit is not repeated.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
