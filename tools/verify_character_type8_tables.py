"""Independent source identities, exact inverse and actual event-row consumption."""
import argparse
import hashlib
import json
import struct
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner

BASE=0x08000000
BEFORE='933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OLD='58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
TABLES=(0xD3FD04,0xD3FD40,0xD3FD7C,0xD3FE90)
SPANS=((0xD3FD04,0xD3FDB8),(0xD3FE90,0xD3FECC))
ALIASES=((0x36F7AC,),(0x36F7B0,),(0x36F7B4,),(0x36CAA8,0x36F7B8))
VICTIM=0x02011828

def need(ok,label):
 if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]

def expected(source,old,retail,before):
 decoder=Cs(CS_ARCH_X86,CS_MODE_16)
 rows=list(decoder.disasm(source[0x76060E:0x760632],0x76060E))
 need(sum(i.size for i in rows)==0x24,'whole source selector decode')
 need([(i.mnemonic,i.op_str)for i in rows if i.mnemonic=='mov']==
      [('mov','bx, 0x3002'),('mov','bx, 0x3020'),('mov','bx, 0x303e'),('mov','bx, 0x305c')], 'actual four source table immediates')
 need([(i.mnemonic,i.op_str)for i in rows if i.mnemonic=='test']==
      [('test','word ptr [di + 6], 1'),('test','word ptr [di + 8], 0x4000'),('test','word ptr [di + 6], 1')],'source air/evolution selector flags')
 data=[]
 for k in range(4):
  src_table=0x762FD2+30*k;old_table=0x3A6DDA+24*k
  native_table=0x36BE44+48*k;native_record=0x36C12C+128*k
  src_record=0x763258+128*k;old_record=0x3A6FCE+128*k
  need(struct.unpack_from('<15H',source,src_table)==(src_record-0x75FFD0,)*15,'all fifteen actual source rows')
  population=13 if k==3 else 12
  need(struct.unpack_from('<'+str(population)+'H',old,old_table)==(old_record-0x3A45B0,)*population,'old source original rows')
  need(struct.unpack_from('<'+str(population)+'I',retail,native_table)==(BASE+native_record,)*population,'commercial oracle original rows')
  need(before[native_table:native_table+4*population]==retail[native_table:native_table+4*population],'short native table retained in failing candidate')
  need(h(source,src_table+30)!=h(source,src_table) and u(retail,native_table+4*population)!=BASE+native_record,'independent next-table boundaries')
  events=[]
  for variant in range(4):
   s=src_record+variant*32;o=old_record+variant*32;n=native_record+variant*32
   need(source[s:s+4]==old[o:o+4]==retail[n:n+4] and h(source,s)==0,'same source flag-zero event')
   need(source[s+8:s+32]==old[o+8:o+32],'source metadata retained across releases')
   need(before[n:n+32]==retail[n:n+32],'full native record retained')
   need(struct.unpack_from('<HH',source,s+4)==((0xFE2,0x1146)[k%2],0x5FFD),'source callback identity')
   need(u(retail,n+4)==(0x0836A834,0x0836AAC0)[k%2],'native callback identity')
   events.append(h(source,s+2))
  needle=struct.pack('<I',BASE+native_table);found=[];at=-1
  while True:
   at=before.find(needle,at+1)
   if at<0:break
   found.append(at)
  need(tuple(found)==ALIASES[k],'complete native aliases including second air consumer')
  data.append(events)
 for evolved in range(2):
  for ident in range(15):
   off,seg,bank=struct.unpack_from('<3H',source,0x740006+32*(ident+30*evolved))
   physical=16*seg+off
   need(0x20000<=physical<0x30000 and 0x80<=bank<=0xFF,'source P1 bank pointer')
   p1=(bank&127)*0x10000+physical-0x20000
   need(u(source,p1)==4,'source P1 direct table origin')
   count=(h(source,p1+6)-4)//8
   native=u(before,(0x4A80F8,0x60B000)[evolved]+ident*32+4)-BASE
   table=u(before,native)-BASE
   need((u(before,table+4)-BASE-table)//16==count,'source/native P1 populations')
   for event in set(data[2*evolved]+data[2*evolved+1]):
    need(event<count and h(source,p1+4+8*event)==u(before,table+16*event),'source-selected event and command count in native P1')
 return data

def inverse(before,after):
 need(len(before)==len(after)==0x1000000,'16MiB extent')
 need(all(before[x:y]==b'\xff'*(y-x)for x,y in SPANS),'unused exact reservation')
 want=bytearray(before)
 for k,sites in enumerate(ALIASES):
  want[TABLES[k]:TABLES[k]+60]=struct.pack('<15I',*((BASE+0x36C12C+128*k,)*15))
  for a in sites:struct.pack_into('<I',want,a,BASE+TABLES[k])
 need(after==want,'entire file equals independently constructed nine-span correction')
 return sum(a!=b for a,b in zip(before,after))

def ownership(before,after,paths):
 pins=('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
       '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
       '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD',
       '54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55',
       '6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C')
 retained=0
 for k,(path,pin)in enumerate(zip(paths,pins)):
  b=path.read_bytes();need(sha(b)==pin,'frozen prior owner manifest')
  owner=json.loads(b)
  if k==0:need([0xD33000,0xD40000]in owner['reservations'],'enclosing existing reservation')
  if k==4:need(owner['output_sha256']==BEFORE,'immediate preceding owner output')
  for w in owner['writes']:
   a,z=w['offset'],w['offset']+w['size']
   need(not any(max(a,x)<min(z,y)for x,y in SPANS),'new spans disjoint from all prior writes')
   if 0xD33000<=a<0xD40000:
    pin=w.get('after_sha256')or sha(bytes.fromhex(w['after_hex']))
    need(sha(before[a:z])==sha(after[a:z])==pin,'prior enclosing-reservation contents retained')
    retained+=1
 need(all(0xD33000<=x<y<=0xD40000 for x,y in SPANS),'allocation contained in existing reservation')
 return dict(manifest_sha256=pins,prior_enclosing_writes_retained=retained)

def run(rom,ident,evolved,air,variant,flags=0):
 m=Machine(rom,seed=9,flags=(flags<<28)|0x10)
 m.r[4],m.r[5],m.r[11]=0x02011710,VICTIM,0
 m.put(VICTIM+6,air,2);m.put(VICTIM+8,evolved*0x4000,2)
 m.put(VICTIM+0x11,ident,1);m.put(0x03004D26,variant,1)
 p1=u(rom,(0x4A80F8,0x60B000)[evolved]+ident*32+4)
 m.put(VICTIM+0xF0,p1)
 m.run(0x0836EC68,{0x083555D0})
 record=m.r[1]
 m.run(0x083555D0,{0x08012874})
 need(m.r[4]==VICTIM and m.r[5]==VICTIM+0xAC and m.r[14]==0x08355620,'actual generic-to-setter ABI')
 m.run(0x08012874,{0x080128BC})
 return record,p1,m

def cases(before,after,events):
 count=legacy=0
 for ident in range(15):
  for evolved in range(2):
   for air in range(2):
    k=2*evolved+air
    for variant in range(4):
     for flags in (0,15):
      record,p1,m=run(after,ident,evolved,air,variant,flags)
      event=events[k][variant];table=u(after,p1-BASE)
      total=(u(after,table-BASE+4)-table)//16
      need(record==BASE+0x36C12C+128*k+32*variant,'source selected metadata record')
      need(event<total and m.get(VICTIM+0xBA,2)==event,'actual event store within selected P1')
      row=struct.unpack_from('<4I',after,table-BASE+16*event)
      need(m.get(VICTIM+0xC8,2)==row[0] and m.get(VICTIM+0xCC)==row[1] and m.get(VICTIM+0xD0)==row[1],'actual command count/base/current stores')
      need(m.get(VICTIM+0xD4)==row[2] and m.get(VICTIM+0xD8)==row[3],'actual A/B metadata stores')
      need(0<row[0]<256 and BASE<=row[1]<=BASE+len(after)-16*row[0],'first command read will be bounded')
      need(BASE<=row[2]<=BASE+len(after)-8 and (row[3]==0 or BASE<=row[3]<=BASE+len(after)-10),'bounded A/B objects')
      count+=1
      if ident<12 or (ident==12 and k==3):
       r0,p0,m0=run(before,ident,evolved,air,variant,flags)
       need((r0,p0,m0.r,m0.cpsr,m0.mem,m0.writes)==(record,p1,m.r,m.cpsr,m.mem,m.writes),'all original valid identity full execution states preserved')
       legacy+=1
 # Reproduce the actual failing row at the last safe instruction, without a BIOS model.
 record,p1,m=run(before,13,1,1,0)
 need((record,p1,m.get(VICTIM+0xBA,2),m.get(VICTIM+0xC8,2),m.get(VICTIM+0xCC))==
      (0x0836C32C,0x0861CF0C,0x36,0xFF05,0x1000C),'failing candidate exact row corruption')
 # Second literal uses its existing byte-at-R5+11 ABI; do not invent its owner.
 for ident in range(15):
  m=Machine(after);m.r[5]=VICTIM;m.r[11]=0;m.put(VICTIM+0x11,ident,1)
  m.run(0x0836CA40,{0x083555D0})
  need(m.r[1]==0x0836C2AC,'second evolved-air consumer same extended table')
 return dict(actual_setter_cases=count,legacy_full_state_equal=legacy,second_consumer_index_cases=15,old_failure_reproduced=True)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('before','after','source','old','gba','report'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--owners',type=Path,nargs=5,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 before,after,source,old,gba=(getattr(a,k).read_bytes()for k in ('before','after','source','old','gba'))
 need(tuple(map(sha,(before,source,old,gba)))==(BEFORE,SOURCE,OLD,RETAIL),'immutable inputs')
 events=expected(source,old,gba,before);changed=inverse(before,after);owners=ownership(before,after,a.owners)
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=SPANS),argdefs=scanner.inbound.__defaults__)
 need(not scan(before),'no encoded inbound references into new allocation')
 validations=cases(before,after,events)
 rejected=0
 for site in [x for row in ALIASES for x in row]+[TABLES[0]+52,TABLES[1]+56,TABLES[2]+48,TABLES[3]+52]:
  mutant=bytearray(after);mutant[site]^=1
  try:inverse(before,bytes(mutant))
  except ValueError:rejected+=1
 need(rejected==9,'all redirect/new identity mutations rejected')
 report=dict(status='TYPE8_TABLES_INDEPENDENT_PASS',before_sha256=sha(before),after_sha256=sha(after),checker_sha256=sha(Path(__file__).read_bytes()),
             events=events,declared_spans=9,declared_bytes=260,changed_bytes=changed,whole_file_inverse=True,
             allocation=SPANS,inbound_references=[],scope_mutations_rejected=rejected,ownership=owners,**validations,
             limitations=['No emulator execution by this verifier.','Second consumer owner lifetime unchanged; only its actual byte-index ABI is covered.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(report['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
