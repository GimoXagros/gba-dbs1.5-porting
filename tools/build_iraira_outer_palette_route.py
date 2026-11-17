"""Restore the source stage10 outer palette consumer without altering stage3."""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
BASE=0x08000000
INPUT='3CB7A7137762AA77C7C8D9147CF32AB356CDB269E6CE819115B911DEF444E49E'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OWNERS=('2EDEA4E7EFF23EDD7A9C2F5E39262CF92089BBC379EE83F571665324E7E678DD','29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900','4AFD13AEC814255B94F21D1C72D26EBF81A75E6F5FA7CC2FE89D028C48A2FA66')
FIRST,LIMIT=0xD8B640,0xD8B6C0
def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def asm(s,a):return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(s,BASE+a)[0])
def color(v):return sum((2*((v>>s)&15)+(1 if (v>>s)&15 else 0))<<d for s,d in ((8,0),(4,5),(0,10)))
def contract(b,s):
 need(sha(b)==INPUT and sha(s)==SOURCE,'fixed input and source identities')
 need(0x768F70+h(s,0x768F70+20)==0x769361,'actual stage10 outer dispatch')
 need(s[0x769361:0x769367]==bytes.fromhex('9AB6024783C3'),'complete source outer10 common-projector-only body')
 need(0x783470+h(s,0x78370E+20)==0x783B90,'inner source stage10 palette handler')
 need(s[0x77CF86:0x77CF92]==bytes.fromhex('33C0BE800389048ED8A300FE'),'source physical black before stage initialization')
 need(b[0x3EEAC:0x3EEC0]==asm('mov r0,#0; ldr r4,[pc,#0x2c8]; strh r0,[r4]; mov r8,#0x05000000; strh r0,[r8]',0x3EEAC),'native physical black before stage initialization')
 need(struct.unpack_from('<I',b,0x3F180)[0]==0x03002654,'native backdrop shadow literal')
 need(s[0x77CFB2:0x77CFC2]==bytes.fromhex('33FFB8DE0B8EC0BE2000B91001FCF3A5'),'source common17tile overwrite after stage initialization')
 font=bytearray()
 for n in range(17):
  t=s[0x42FD80+n*32:0x42FDA0+n*32]
  for y in range(8):
   px=[sum(((t[y*4+p]>>(7-x))&1)<<p for p in range(4)) for x in range(8)]
   font.extend(px[x]|px[x+1]<<4 for x in range(0,8,2))
 need(bytes(font)==b[0x1FD50:0x1FF70],'all544 commonfont bytes source exact; no font repair')
 need(b[0xD0BD0:0xD0BD4]==asm('bl 0x08584A00',0xD0BD0),'native outer adapter hook')
 need(b[0xD0BE8:0xD0BEC]==asm('bl 0x086FF600',0xD0BE8),'retained common queue continuation')
 return dict(source_outer=0x769361,source_inner=0x783B90,source_display_registration=0x740D96,source_cycle=0x76AF13,source_line_callback=0x75FA64,source_physical_backdrop_clear=0x77CF8F,commonfont_source=0x42FD80,commonfont_native=0x1FD50,commonfont_bytes=544,commonfont_sha256=sha(font),font_repair=False)
def helper():
 return asm('''push {r0,r1,r2,lr}
 mrs r2,cpsr
 ldr r1,config
 ldrb r0,[r1,#14]
 cmp r0,#10
 beq iraira
 msr cpsr_f,r2
 pop {r0,r1,r2,lr}
 b 0x08584A00
iraira:
 msr cpsr_f,r2
 pop {r0,r1,r2,lr}
 ldr lr,continuation
 b 0x080C4CC4
config:.word 0x03002310
continuation:.word 0x080D0BE8
''',FIRST)
def validate(before,after,source):
 parity=0
 for ident in range(256):
  if ident==10:continue
  for flags in range(16):
   pair=[]
   for rom in (before,after):
    m=Machine(rom,seed=3,flags=(flags<<28)|0x1F);m.put(0x0300231E,ident,1)
    m.run(0x080D0BD0,{0x080D0BD4});pair.append((m.r[:15],m.cpsr))
   need(pair[0]==pair[1],'all non10 identities exact adapter registers/CPSR/SP/LR parity');parity+=1
 rows=struct.unpack_from('<256H',source,0x76AD13);cases=0
 for p in range(4):
  for q in range(7):
   for r in range(6):
    for mode in range(4):
     m=Machine(after,seed=4,flags=0xA000001F)
     m.put(0x0300231E,10,1);m.put(0x03004506,16 if mode==2 else 0,2)
     m.put(0x0300260B,1 if mode==3 else 0,1);m.put(0x03004529,1 if mode==1 else 0,1)
     for at,v in ((0x03003D34,p),(0x03003D36,q),(0x03003D38,r)):m.put(at,v,2)
     for i in range(0,512,2):m.put(0x05000000+i,0x6B5A,2)
     regs=list(m.r);m.run(0x080D0BC0,{0x080D0BE8})
     expected={}
     if mode<2:
      for off,phase,count,dst in ((0,p*16,11,0x42),(64,p*8,6,0x62),(96,q*8,7,0x82),(152,r*8,7,0xA2),(200,q*8,7,0xC2)):
       for i in range(count):
        v=rows[off+phase+i]
        if mode==1:v=(v&0xEEE)>>1
        expected[dst+2*i]=color(v)
     need(all(m.get(0x05000000+i,2)==expected.get(i,0x6B5A) for i in range(0,512,2)),'actual outer entry reaches all38 source colors and preserves backdrop/gaps')
     need(m.r[13]==regs[13]-28 and m.r[14]==0x080D0BE8,'original outer stack and common continuation')
     need(all(m.r[i]==regs[i] for i in (6,7,9,10,11,12)),'unrelated outer registers preserved')
     cases+=1
 return dict(non10_actual_ARM_adapter_fullstate_cases=parity,stage10_actual_ARM_outer_prefix_palette_cases=cases,full_outer_continuation='Independent reviewer owns subsequent queue/IRQ execution; author stops at retained D0BE8.',no_emulator=True)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('before','source','output','manifest'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--owners',type=Path,nargs=3,required=True);a=p.parse_args()
 need(not a.output.exists() and not a.manifest.exists(),'fresh outputs')
 b,s=a.before.read_bytes(),a.source.read_bytes();proof=contract(b,s)
 need(b[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'complete128byte reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 hits=scan(b);need(not hits,'zero conservative inbound references')
 writes=[];out=bytearray(b)
 for at,data,label in ((FIRST,helper(),'stage10 typed outer palette route'),(0xD0BD0,asm(f'bl 0x{BASE+FIRST:X}',0xD0BD0),'outer display adapter interception')):
  need(at!=FIRST or len(data)<=LIMIT-FIRST,'helper fits reservation')
  writes.append(dict(offset=at,size=len(data),before_hex=b[at:at+len(data)].hex(),after_hex=data.hex(),label=label));out[at:at+len(data)]=data
 preserved=0
 for path,pin in zip(a.owners,OWNERS):
  raw=path.read_bytes();need(sha(raw)==pin,'explicit frozen owner');owner=json.loads(raw)
  for lo,hi in owner['reservations']:need(not max(lo,FIRST)<min(hi,LIMIT),'disjoint reservations')
  for w in owner['writes']:
   lo,hi=w['offset'],w['offset']+w['size'];need(out[lo:hi]==b[lo:hi],'all preceding mode20/Iraira/alignment spans unchanged');preserved+=1
 inverse=bytearray(out)
 for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
 need(bytes(inverse)==b,'whole3CB7 inverse')
 checks=validate(b,bytes(out),s)
 report=dict(status='PASS',input_sha256=INPUT,output_sha256=sha(out),source_sha256=SOURCE,owner_sha256=list(OWNERS),reservations=[[FIRST,LIMIT]],writes=writes,declared_bytes=sum(w['size'] for w in writes),changed_bytes=sum(x!=y for x,y in zip(b,out)),new_RAM_bytes=0,inbound_hits=hits,source_contract=proof,validation=checks,preceding_writes_preserved=preserved,whole_image_inverse=True,actual_runtime_verified=False,limits=['Native stage3 and all non10 identities retained.','No new backdrop writes, font repair, timers, menu or stage priority changes.','Actual positive caller witness remains separate.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.manifest.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_bytes(out);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(dict(status='PASS',output_sha256=sha(out),manifest_sha256=sha(a.manifest.read_bytes()),declared_bytes=report['declared_bytes'],changed_bytes=report['changed_bytes'],validation=checks)))
if __name__=='__main__':main()
