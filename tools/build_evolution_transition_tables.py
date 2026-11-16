"""Extend the three retained evolution presentation selectors from source 1.5."""
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
from verify_shoot_attack_dispatch import Machine
import verify_shoot_caller_resident as scanner
import build_impmon_evolution_gate as gate

INPUT='8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
MANIFEST='AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91'
SCANNER='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'
GATE='C7D88E9E07E683DF73D56F5097EA422DF484D111D4EDCF70CAF76119274EBF73'
START,END=0xD3F000,0xD3F05A
# Original table, source table, relocated table, instruction, aligned pointer literal.
ROWS=((0x35A210,0x7679C2,START,0x35A1E4,0x35A210),
      (0x35A580,0x7679E0,START+30,0x35A54C,0x35A580),
      (0x35A596,0x7679FE,START+60,0x35A550,0x35A598))
OPCODES=(0xE28F8024,0x028F802C,0x128F803E)
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
u=lambda b,a:struct.unpack_from('<I',b,a)[0]
h=lambda b,a:struct.unpack_from('<H',b,a)[0]
def need(ok,label):
 if not ok:raise ValueError(label)

def source_proof(before,source):
 decoder=Cs(CS_ARCH_X86,CS_MODE_16)
 expected={0x7673BA:(0x7673C6,['xor bx, bx','mov bl, byte ptr [si + 0x11]','shl bx, 1','mov ax, word ptr cs:[bx + 0x10e2]']),
  0x7675BB:(0x7675D3,['xor bx, bx','mov bl, byte ptr [si + 0x11]','shl bx, 1','mov ax, word ptr cs:[bx + 0x1100]','test word ptr [si + 6], 1','je 0x7675d3','mov ax, word ptr cs:[bx + 0x111e]'])}
 for at,(end,text)in expected.items():
  instructions=list(decoder.disasm(source[at:end],at))
  need(sum(i.size for i in instructions)==end-at and [i.mnemonic+' '+i.op_str for i in instructions]==text,'exact source selector '+hex(at))
 values=[]
 for old,src,new,site,literal in ROWS:
  need(before[old:old+22]==source[src:src+22],'all eleven retained source entries exact')
  values.append(list(struct.unpack_from('<15H',source,src)))
 need(values[0]==[109,119,94,109,126,98,111,98,119,98,98,105,109,109,115] and values[1]==[24]*14+[25] and values[2]==[25]*15,'three source populations')
 return values

def ownership(before,raw):
 need(sha(raw)==MANIFEST,'frozen production allocation manifest')
 m=json.loads(raw)
 need([0xD33000,0xD40000]in m['reservations'],'existing audio reservation owner')
 writes=[w for w in m['writes']if 0xD33000<=w['offset']<0xD40000]
 need(max(w['offset']+w['size']for w in writes)==0xD3EA01,'exact earlier allocation frontier')
 for w in writes:need(sha(before[w['offset']:w['offset']+w['size']])==w['after_sha256'],'prior audio allocation unchanged')
 need(before[0xD3EA01:0xD40000]==b'\xff'*(0xD40000-0xD3EA01),'complete declared unused tail retained')
 need(sha(Path(scanner.__file__).read_bytes())==SCANNER,'frozen conservative scanner')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((START,END),)),argdefs=scanner.inbound.__defaults__)
 hits=scan(before);need(not hits,'no predecessor pointer/ARM/Thumb encodings into new allocation')
 return dict(owner_manifest_sha256=MANIFEST,reservation=[0xD33000,0xD40000],prior_used_end=0xD3EA01,
  new_suballocation=[START,END],purpose='Three source-derived evolution transition tables, 15 halfwords each',
  conservative_inbound_hits=hits,scanner_sha256=SCANNER,remaining_tail=[END,0xD40000])

def selection(rom,ident,which,flags):
 m=Machine(rom,seed=5,flags=(flags<<28)|0x1F);m.r[4]=0x02011828
 m.put(m.r[4]+0x11,ident,1);m.put(m.r[4]+6,int(which==2),2)
 start,stop=(0x0835A1DC,0x0835A1EC)if which==0 else(0x0835A53C,0x0835A558)
 # Imported interpreter excludes register-offset halfword loads. Decode the
 # final pinned LDRH/LDRSH locally rather than replacing it with a service.
 last=stop-4;need(m.run(start,{last})==last,'actual ARM lookup prefix terminates')
 word=m.get(last);need(word==(0xE19100B8 if which==0 else 0xE19100F8),'exact actual register-offset halfword load')
 m.r[15]=last+8;value=m.get(m.r[1]+m.r[8],2)
 m.r[0]=(value-65536 if which!=0 and value&0x8000 else value)&0xFFFFFFFF
 return m

def validate(before,after,values):
 cases=0
 for ident in range(15):
  for which in range(3):
   for flags in range(16):
    m=selection(after,ident,which,flags);cases+=1
    need(m.r[0]==values[which][ident],'source event from actual ARM lookup')
    if ident<11:
     old=selection(before,ident,which,flags)
     need(old.r[:8]==m.r[:8] and old.r[9:]==m.r[9:] and old.cpsr==m.cpsr and old.mem==m.mem and old.writes==m.writes,'all original identities preserve observable lookup state except relocated R8')
 need(sha(Path(gate.__file__).read_bytes())==GATE,'frozen clean-mode gate model')
 for flags in range(16):
  m,stop=gate.route(after,15,flags)
  need(stop==0x083547D0 and m.get(0x02011828)==0 and not m.calls,'actual boss15 denied before table selection')
 resources=[]
 for ident in range(15):
  for which in range(3):
   group=0x4A80F8 if which==0 else 0x60B000
   p1=u(after,group+ident*32+4)-0x08000000;table=u(after,p1)-0x08000000
   count=(u(after,table+4)-0x08000000-table)//16
   event=values[which][ident]
   need(table==p1+8 and 0<=event<count<256,'selected event in actual resource table')
   row=table+event*16;n=u(after,row);cmd=u(after,row+4)-0x08000000
   need(0<n<=255 and 0<=cmd<=len(after)-16*n,'actual command extent bounded')
   resources.append(dict(id=ident,selector=which,P1=p1,event=event,event_count=count,commands=n))
 return dict(actual_ARM_lookup_cases=cases,boss15_exclusion_cases=16,all0_to10_lookup_state_preserved=True,
  all0_to14_source_events=True,resources=resources,resource_contents_changed=False,index15_table_read_permitted=False)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in('before','wsc15','allocation-manifest','output','manifest'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();paths=[a.before,a.wsc15,a.allocation_manifest,a.output,a.manifest]
 need(len({x.resolve()for x in paths})==5 and not a.output.exists()and not a.manifest.exists(),'fresh nonalias outputs')
 before,source=a.before.read_bytes(),a.wsc15.read_bytes()
 need(sha(before)==INPUT and len(before)==0x1000000 and sha(source)==SOURCE,'exact immutable inputs')
 values=source_proof(before,source);owned=ownership(before,a.allocation_manifest.read_bytes())
 after=bytearray(before);writes=[]
 def patch(at,blob):
  need(not any(max(at,w['offset'])<min(at+len(blob),w['offset']+w['size'])for w in writes),'disjoint writes')
  writes.append(dict(offset=at,size=len(blob),before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex()));after[at:at+len(blob)]=blob
 for index,(old,src,new,site,literal)in enumerate(ROWS):
  need(u(before,site)==OPCODES[index] and literal%4==0,'exact original ADR and aligned ARM7 literal')
  displacement=literal-site-8;need(0<=displacement<4096,'positive literal reach')
  patch(site,struct.pack('<I',(OPCODES[index]&0xF0000000)|0x059F8000|displacement))
  patch(literal,struct.pack('<I',0x08000000+new));patch(new,source[src:src+30])
 after=bytes(after);arm=validate(before,after,values)
 inverse=bytearray(after)
 for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
 need(bytes(inverse)==before,'whole sixteen MiB inverse')
 rejected=[]
 for label,at in [('old air selector',0x35A550),('wrong new ID11 air event',START+60+22)]:
  bad=bytearray(after);bad[at:at+(4 if at==0x35A550 else 2)]=before[at:at+4]if at==0x35A550 else b'\x00\x40'
  try:validate(before,bytes(bad),values)
  except (ValueError,AssertionError):rejected.append(label)
  else:raise ValueError('harmful mutation accepted')
 report=dict(status='SOURCE_EVOLUTION_TRANSITION_TABLES_AUTHOR_PASS',input_sha256=INPUT,output_sha256=sha(after),source_sha256=SOURCE,
  allocation=owned,source_values=values,source_tables=[x[1]for x in ROWS],native_old_tables=[x[0]for x in ROWS],new_tables=[x[2]for x in ROWS],
  writes=writes,declared_bytes=sum(w['size']for w in writes),changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_inverse=True,ARM=arm,
  rejected_mutations=rejected,builder_sha256=sha(Path(__file__).read_bytes()),actual_runtime_verified=False,audio_suppression=False,
  historical_ID14_old_events=[h(before,x[0]+28)for x in ROWS],historical_ID14_failure_cause_proven=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
 a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_bytes((json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps({k:report[k]for k in('status','output_sha256','declared_bytes','changed_bytes','builder_sha256')},indent=2))
if __name__=='__main__':main()
