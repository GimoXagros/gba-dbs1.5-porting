"""Source-backed Iraira graphics, layer ownership and compact palette repair."""
import argparse, hashlib, json, struct, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
BASE=0x08000000
INPUT='E6B2C30E3E7D880BFFEE82A3201D0F69AE3DE0EBBEE5B523D24DD6D03FA08CF4'
ALIGNMENT_OWNER='4AFD13AEC814255B94F21D1C72D26EBF81A75E6F5FA7CC2FE89D028C48A2FA66'
DEEE='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST,LIMIT=0xD8AC00,0xD8B400
CYCLE,PROJECT,INIT_ROUTE,PROJECT_ROUTE,INIT_TAIL=0xD8AC00,0xD8AD00,0xD8AF00,0xD8AF40,0xD8AF80
OWNERS=(0x582548,0x58254C,0x582554,0x582560,0x582564,0x582568,0x582570,0x58257C)
def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def asm(s,a):return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(s,BASE+a)[0])
def color(v):return sum((0 if not (v>>s)&15 else 2*((v>>s)&15)+1)<<d for s,d in ((8,0),(4,5),(0,10)))
def tile(b):
 out=bytearray()
 for y in range(8):
  px=[sum(((b[y*4+p]>>(7-x))&1)<<p for p in range(4)) for x in range(8)]
  out.extend(px[x]|px[x+1]<<4 for x in range(0,8,2))
 return bytes(out)
def map_data(b):return struct.pack('<504H',*((v&511)|(512 if v&8192 else 0)|((v&0xC000)>>4)|(((v>>9)&15)<<12) for v, in struct.iter_unpack('<H',b)))
def source_contract(b,s):
 need(sha(b)==INPUT and sha(s)==SOURCE,'fixed whole-image identities')
 need(s[0x77CCF0+0x30+10]==0xCC and h(s,0x77CCF0+0x3C+20)+0x77CCF0==0x77DBE6,'source stage10 bank and graphics initializer')
 need(s[0x77DBE6:0x77DBEB]==bytes.fromhex('B80E368ED8'),'source DS360E')
 srcmaps=[]
 for ident in (37,38):
  p=0x3B4DD0+ident*24
  need(struct.unpack_from('<HH',s,p)==(2,2) and h(s,p+10)==0x360E,'source 2x2 resource segment')
  table=0x3B4970+h(s,p+8)
  for i in range(4):
   bank,mode,off=struct.unpack_from('<BBH',s,table+4*i)
   need((bank,mode)==(0xCC,1),'source direct map bank')
   srcmaps.append((bank&0x7F)*65536+0x360E*16+off-0x30000)
 need(srcmaps==[0x4CA1C0+i*0x3F0 for i in range(8)],'all source resource map addresses')
 d=Cs(CS_ARCH_X86,CS_MODE_16)
 def dis(a,z):return [(i.mnemonic,i.op_str) for i in d.disasm(s[a:z],0)]
 callbacks=dis(0x75F9EE,0x75FA64)
 need(len(callbacks)>50 and callbacks==dis(0x75FA64,0x75FAD9),'complete source display callback semantic identity')
 rows=struct.unpack_from('<256H',s,0x76AD13)
 need(b[0x584200:0x584400]==struct.pack('<256H',*(color(v) for v in rows)),'complete retained palette rows')
 initial=[h(s,i+2) for i in range(0x7835A1,0x78368D) if s[i:i+2]==b'\xc7\x04']
 zero=list(rows[:11])+list(rows[64:70])+list(rows[96:103])+list(rows[152:159])+list(rows[200:207])
 need(initial==zero and len(zero)==38,'all explicit source initial colors equal compact phase zero')
 for ident,start in ((25,0),(26,4)):
  desc=u(b,0x580000+ident*24+8)-BASE
  need([u(b,desc+8*i+4)-BASE for i in range(4)]==[0x59C100+0x3F0*(start+i) for i in range(4)],'native retained map aliases')
 return rows,dict(palette=0x4C60E0,tiles=0x4C61C0,maps=srcmaps,display_instructions=len(callbacks),initial_colors=initial)
def cycle_code():return asm('''
 push {r0-r2,lr}
 ldr r1,owner
 ldrh r0,[r1]
 add r0,r0,#1
 and r0,r0,#7
 strh r0,[r1]
 cmp r0,#0
 bne third
 ldrh r2,[r1,#4]
 add r2,r2,#1
 and r2,r2,#3
 strh r2,[r1,#4]
third:
 tst r0,#11
 bne fourth
 ldrh r2,[r1,#6]
 add r2,r2,#1
 cmp r2,#7
 movhs r2,#0
 strh r2,[r1,#6]
fourth:
 ldrh r2,[r1,#2]
 add r2,r2,#1
 cmp r2,#5
 blo delay
 mov r2,#0
 strh r2,[r1,#2]
 ldrh r2,[r1,#8]
 add r2,r2,#1
 cmp r2,#6
 movhs r2,#0
 strh r2,[r1,#8]
 b done
delay:strh r2,[r1,#2]
done:pop {r0-r2,lr}
 bx lr
owner:.word 0x03003D30
''',CYCLE)
def project_code():
 code='''push {r0-r10,lr}
 ldr r8,flags
 ldrh r0,[r8]
 tst r0,#16
 bne done
 ldr r8,disabled
 ldrb r0,[r8]
 cmp r0,#0
 bne done
 ldr r8,dimmed
 ldrb r4,[r8]
 ldr r8,owner
 ldr r7,rows
 ldr r6,palette
 ldr r10,mask
'''
 for i,(off,phase,shift,count,dst) in enumerate(((0,4,5,11,0x42),(0x80,4,4,6,0x62),(0xC0,6,4,7,0x82),(0x130,8,4,7,0xA2),(0x190,6,4,7,0xC2))):
  code+=f'''ldrh r9,[r8,#{phase}]
 add r1,r7,#{off}
 add r1,r1,r9,lsl #{shift}
 add r2,r6,#{dst}
 mov r3,#{count}
copy{i}:ldrh r0,[r1]
 add r1,r1,#2
 bl shade
 strh r0,[r2]
 add r2,r2,#2
 subs r3,r3,#1
 bne copy{i}
'''
 code+='''done:pop {r0-r10,lr}
 bx lr
shade:cmp r4,#0
 bxeq lr
 and r0,r0,r10
 lsr r0,r0,#1
 tst r0,#0x1e
 orrne r0,r0,#1
 tst r0,#0x3c0
 orrne r0,r0,#0x20
 tst r0,#0x7800
 orrne r0,r0,#0x400
 bx lr
flags:.word 0x03004506
disabled:.word 0x0300260B
dimmed:.word 0x03004529
owner:.word 0x03003D30
rows:.word 0x08584200
palette:.word 0x05000000
mask:.word 0x739c
'''
 return asm(code,PROJECT)
def route(a,target,previous):return asm(f'''
 push {{r0,r8,lr}}
 ldr r8,battle
 ldrb r0,[r8,#14]
 cmp r0,#11
 beq old
 bl 0x080D1C78
 cmp r0,#10
 pop {{r0,r8,lr}}
 beq 0x{BASE+target:X}
 b 0x{BASE+previous:X}
old:pop {{r0,r8,lr}}
 b 0x{BASE+previous:X}
battle:.word 0x03002310
''',a)
def build(b,s):
 rows,contract=source_contract(b,s)
 need(b[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'entire new code reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 hits=scan(b);need(not hits,'zero conservative inbound references')
 writes=[];out=bytearray(b)
 def put(a,data,label):
  need(not any(max(a,w['offset'])<min(a+len(data),w['offset']+w['size']) for w in writes),'disjoint writes')
  writes.append(dict(offset=a,size=len(data),before_sha256=sha(b[a:a+len(data)]),after_sha256=sha(data),label=label))
  out[a:a+len(data)]=data
 for a,data,limit,label in ((CYCLE,cycle_code(),PROJECT,'five compact source palette counters'),(PROJECT,project_code(),INIT_ROUTE,'38-color gated source palette projection'),(INIT_ROUTE,route(INIT_ROUTE,0x628400,0x628680),PROJECT_ROUTE,'stage10 compact init route'),(PROJECT_ROUTE,route(PROJECT_ROUTE,PROJECT,0x6286C0),INIT_TAIL,'stage10 projection route'),(INIT_TAIL,asm('push {r0,r1}; ldr r1,phase; mov r0,#0; strh r0,[r1]; pop {r0,r1}; pop {lr}; bx lr; phase:.word 0x03002568',INIT_TAIL),LIMIT,'source graphics initializer phase clear')):
  need(a+len(data)<=limit,'routine allocation '+label);put(a,data,label)
 need(u(b,0x582544)==color(0xE80)==0x23D,'retail stage3 backdrop literal')
 need(s[0x77CF88:0x77CF8D]==bytes.fromhex('BE80038904'),'source common backdrop clear')
 put(0x582544,struct.pack('<I',0),'source Iraira black backdrop global')
 for a in OWNERS:
  old=0x03002338 if a<0x582564 else 0x03002388
  need(u(b,a)==old,'typed source BG owner Expected Write')
  put(a,struct.pack('<I',0x03002388 if old==0x03002338 else 0x03002338),'source background owner')
 need(u(b,0x583B28)==0x08583E00 and u(b,0x582528)==0xE8BD4000,'callback and tail expected writes')
 need(b[0xC4BC0:0xC4BC4]==asm('b 0x08628680',0xC4BC0) and b[0xC4CC4:0xC4CC8]==asm('b 0x086286C0',0xC4CC4),'preceding Waterfall routes')
 for a,target,label in ((0x583C00,CYCLE,'replace wrong palette owner writer'),(0xC4BC0,INIT_ROUTE,'palette init dispatcher'),(0xC4CC4,PROJECT_ROUTE,'palette projection dispatcher'),(0x582528,INIT_TAIL,'graphics tail phase clear')):put(a,asm(f'b 0x{BASE+target:X}',a),label)
 put(0x583B28,struct.pack('<I',0x08628300),'source-equivalent proven display callback')
 put(0x598000,struct.pack('<111H',*(color(h(s,0x4C60E2+2*i)) for i in range(111))),'correct dedicated Iraira palette')
 put(0x598100,b''.join(tile(s[a:a+32]) for a in range(0x4C61C0,0x4CA1C0,32)),'correct dedicated Iraira tiles')
 put(0x59C100,b''.join(map_data(s[a:a+0x3F0]) for a in contract['maps']),'correct dedicated Iraira eight maps')
 inverse=bytearray(out)
 for w in writes:
  a,z=w['offset'],w['offset']+w['size'];inverse[a:z]=b[a:z]
 need(bytes(inverse)==b,'whole-image inverse')
 return bytes(out),dict(status='PASS',input_sha256=INPUT,output_sha256=sha(out),source_sha256=SOURCE,reservations=[[FIRST,LIMIT]],source_contract=contract,writes=writes,declared_bytes=sum(w['size'] for w in writes),actual_changed_bytes=sum(x!=y for x,y in zip(b,out)),new_RAM_bytes=0,inbound_hits=hits,whole_image_inverse=True,actual_runtime_verified=False)
def validation(after,s):
 rows=struct.unpack_from('<256H',s,0x76AD13)
 def fixture():
  m=Machine(after,seed=4,flags=0x1F)
  for a,z in ((0x03003D20,0x03003D60),(0x05000000,0x05000200)):
   for p in range(a,z):m.put(p,0,1)
  return m
 phases=[0]*5;cycle_cases=0
 m=fixture()
 for tick in range(3360):
  phases[0]=(phases[0]+1)&7
  if phases[0]==0:phases[2]=(phases[2]+1)&3
  if phases[0]&11==0:phases[3]=(phases[3]+1)%7
  phases[1]+=1
  if phases[1]>=5:phases[1]=0;phases[4]=(phases[4]+1)%6
  regs=list(m.r);m.run(BASE+CYCLE,{m.r[14]})
  need([m.get(0x03003D30+2*i,2) for i in range(5)]==phases,'actual cycle counters')
  need(m.r[:15]==regs[:15],'cycle registers preserved');cycle_cases+=1
 need(phases==[0]*5,'full source palette period')
 projects=0
 for p in range(4):
  for q in range(7):
   for r in range(6):
    for mode in range(4):
     m=fixture();m.put(0x03003D34,p,2);m.put(0x03003D36,q,2);m.put(0x03003D38,r,2)
     m.put(0x03004506,16 if mode==2 else 0,2);m.put(0x0300260B,1 if mode==3 else 0,1);m.put(0x03004529,1 if mode==1 else 0,1)
     regs=list(m.r);m.run(BASE+PROJECT,{m.r[14]})
     need(m.r[:15]==regs[:15],'projector registers preserved')
     expected={}
     if mode<2:
      for off,phase,count,dst in ((0,p*16,11,0x42),(64,p*8,6,0x62),(96,q*8,7,0x82),(152,r*8,7,0xA2),(200,q*8,7,0xC2)):
       for i in range(count):
        v=rows[off+phase+i]
        if mode==1:v=(v&0xEEE)>>1
        expected[dst+2*i]=color(v)
     need(all(m.get(0x05000000+i,2)==expected.get(i,0) for i in range(0,512,2)),'all source palette outputs and untouched gaps');projects+=1
 for stage in range(12):
  for config in (0,11):
   for a,target,prev in ((INIT_ROUTE,0x628400,0x628680),(PROJECT_ROUTE,PROJECT,0x6286C0)):
    m=fixture();m.put(0x0300231E,config,1);m.services[0x080D1C78]=lambda z:z.r.__setitem__(0,stage)
    regs=list(m.r);end=m.run(BASE+a,{BASE+target,BASE+prev})
    need(end==BASE+(target if stage==10 and config!=11 else prev) and m.r[:15]==regs[:15],'all stage route register and target cases')
 import verify_train_graphics_repair as service_arm
 saved_slots=service_arm.SLOTS
 try:
  service_arm.SLOTS=((0x582400,0x130,0x50),(INIT_TAIL,28,4))
  w=service_arm.Walker(after);w.r[11]=0
  w.write(0x03002568,0xA5A5,2,False);w.write(0x0300256A,0xB6B6,2,False)
  w.run(0x08582400)
  for owner,resource,mapbase,ports in ((0x03002338,26,0x0600F000,0x030012B8),(0x03002388,25,0x0600F800,0x030012BA)):
   need([w.read(owner+i,4) for i in (0,4,8,0x24)]==[ports,ports+1,mapbase,u(after,0x580000+resource*24+8)],'full initializer source map and port ownership')
  need(w.read(0x03002654,2)==0,'source black backdrop global')
  need(w.read(0x03002568,4)==0xB6B60000 and w.r[13:15]==[0x03007000,0x01000000],'source phase clear with adjacent owner and stack retained')
  need(bytes(w.read(0x05000002+i,1) for i in range(222))==after[0x598000:0x5980DE],'complete111color initializer copy')
  need(bytes(w.read(0x06004000+i,1) for i in range(0x4000))==after[0x598100:0x59C100],'complete512tile initializer copy')
 finally:service_arm.SLOTS=saved_slots
 return dict(actual_ARM_cycle_cases=cycle_cases,actual_ARM_project_cases=projects,actual_ARM_route_cases=48,full_initializer_cases=1,initializer_services='Explicit native copy/BG summaries; not emulator execution.',full_period_frames=3360)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('before','source','output','manifest'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--alignment-owner',type=Path,required=True)
 a=p.parse_args();need(not a.output.exists() and not a.manifest.exists(),'fresh isolated outputs')
 b,s=a.before.read_bytes(),a.source.read_bytes();out,report=build(b,s)
 ownerbytes=a.alignment_owner.read_bytes();need(sha(ownerbytes)==ALIGNMENT_OWNER,'frozen alignment owner')
 owner=json.loads(ownerbytes);aligned_inverse=bytearray(b)
 for w in owner['writes']:
  lo,hi=w['offset'],w['offset']+w['size']
  need(b[lo:hi]==bytes.fromhex(w['after_hex']) and out[lo:hi]==b[lo:hi],'all17 aligned AI spans retained')
  need(not any(max(lo,x['offset'])<min(hi,x['offset']+x['size']) for x in report['writes']),'AI and Iraira write spans disjoint')
  aligned_inverse[lo:hi]=bytes.fromhex(w['before_hex'])
 need(sha(aligned_inverse)==DEEE,'whole aligned predecessor inverse to DEEE')
 need(all(not max(lo,FIRST)<min(hi,LIMIT) for lo,hi in owner['reservations']),'AI and Iraira reservations disjoint')
 report['alignment_owner_sha256']=ALIGNMENT_OWNER;report['preserved_alignment_writes']=len(owner['writes']);report['alignment_inverse_sha256']=DEEE
 report['validation']=validation(out,s)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(out);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(status='PASS',output_sha256=sha(out),manifest_sha256=sha(a.manifest.read_bytes()),declared_bytes=report['declared_bytes'],changed=report['actual_changed_bytes'],validation=report['validation'])))
if __name__=='__main__':main()
