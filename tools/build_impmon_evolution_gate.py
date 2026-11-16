"""Restore Impmon's source flag-clear 1.5 Calumon route in an isolated image."""
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
import verify_character_p1_completion as p1
from verify_character_resource_routing import palette_check,p4_check,far,ADDED

INPUT='C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
OLD='58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SITE=0x354700
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
 if not ok:raise ValueError(label)

def source_proof(before,gba,old,source):
 need(tuple(map(sha,(before,gba,old,source)))==(INPUT,GBA,OLD,SOURCE),'four exact immutable inputs')
 need(len(before)==0x1000000,'sixteen MiB predecessor')
 decoder=Cs(CS_ARCH_X86,CS_MODE_16)
 def seq(blob,a,z,expected):
  actual=list(decoder.disasm(blob[a:z],a))
  need(sum(i.size for i in actual)==z-a and [f'{i.mnemonic} {i.op_str}'for i in actual]==expected,'exact source instructions '+hex(a))
 seq(old,0x3927ED,0x3927F8,['cmp ax, 8','jne 0x392835','cmp byte ptr [di + 0x11], 0xb','jne 0x392818'])
 seq(source,0x742ACD,0x742AE0,['cmp ax, 8','jne 0x742b1d','test byte ptr es:[0x73], 1','je 0x742b00','cmp byte ptr [di + 0x11], 0xb','jne 0x742b00'])
 seq(source,0x742B00,0x742B1D,['cmp byte ptr [di + 0x11], 0xf','jne 0x742b09','jmp 0x742b75','mov word ptr [di], 0xa33','mov word ptr [di + 2], 0x668e','mov word ptr [si + 0x12], di','lcall 0x4090, 0x3968','jmp 0x742b75'])
 seq(source,0x7787F3,0x7787FA,['test byte ptr es:[di + 0x25], 1','jne 0x778807'])
 need(before[0x3546F0:0x354738]==gba[0x3546F0:0x354738],'retained retail Impmon denial before normal gate')
 need(struct.unpack_from('<I',before,SITE)[0]==0x1A00000C,'exact conditional branch to normal route')
 need(struct.unpack_from('<I',before,0x35473C)[0]==0xE358000F,'existing relocated boss15 denial; playable12 already admitted')
 need(struct.unpack_from('<I',before,0x354904)[0]==0x0835A0F8,'normal fighter evolution callback literal')
 need(sha(before[0x628000:0x628080])=='865C8CC29792AA98C64DEFDCB9B9619325FE54433AFC9F9E0AE264FBC92E5C4A','installed source flag-clear roster views')
 need(struct.unpack_from('<I',before,0x5B0030)[0]==0xE3A0200D,'installed unconditional thirteen-character clean-mode count')
 return dict(source_predicate='742AD2 tests ES1000:0073 bit0; clear takes normal742B00 even for11',
  mode_scope='Existing flag-clear Ver1.5 roster policy only; no alternate-mode or invented RAM flag',
  old_denial='3927F2 / native3546F8 unconditional ID11 special case',
  actor12='Normal in source742B00 and existing native35473C; boss sentinel15 remains refused',
  source_ranges=[dict(start=a,end=z,sha256=sha(source[a:z]))for a,z in((0x742ACD,0x742B1D),(0x7787DB,0x778848))])

def route(rom,ident,nzcv,kind=8):
 m=Machine(rom,seed=3,flags=(nzcv<<28)|0x1F)
 cal,fighter=0x02011940,0x02011828
 m.r[0]=kind;m.r[4]=cal;m.r[5]=fighter
 for address in(cal,fighter):
  for off in range(0,0x100,4):m.put(address+off,0)
 m.put(fighter+0x11,ident,1);m.put(cal+4,0x1008,2)
 m.services={0x0835972C:lambda m:None}
 stop=m.run(0x083546F0,{0x08354758,0x083547D0})
 return m,stop

def arm_proof(before,after):
 cases=0
 for ident in range(16):
  for nzcv in range(16):
   old,os=route(before,ident,nzcv);new,ns=route(after,ident,nzcv);cases+=2
   need(os==ns==0x083547D0,'actual Calumon branch completion')
   if ident!=11:
    need(old.r==new.r and old.mem==new.mem and old.writes==new.writes and old.calls==new.calls and old.cpsr==new.cpsr,'all non11 exact ARM behavior')
   expected=0 if ident==15 else 0x0835A0F8
   need(new.get(0x02011828)==expected,'source clean-mode fighter callback for all16 IDs')
   if ident==11:
    need(old.get(0x02011828)==0 and new.get(0x02011940+0x14)==0x02011828,'only11 gains actual evolution callback/collector link')
    need([x[1]for x in new.calls]==[0x0836D718],'actual retained normal Calumon continuation')
 for kind in (5,7,9):
  old,os=route(before,11,0,kind);new,ns=route(after,11,0,kind)
  need(os==ns==0x08354758 and old.r==new.r and old.writes==new.writes,'non-Calumon branch untouched');cases+=2
 m=Machine(after,seed=4);m.r[4]=0x02011828;m.put(m.r[4]+0x10,1,1);m.put(m.r[4]+0x11,11,1)
 calls=[]
 m.services={0x08353304:lambda vm:calls.append(tuple(vm.get(vm.r[13]+i*4)for i in range(3)))}
 need(m.run(0x0835A424,{0x0835A440})==0x0835A440 and calls==[(1,11,1)],'actual downstream group1/id11/side1 loader call')
 return dict(actual_ARM_executions=cases+1,all16_ids_all16_NZCV=True,non11_full_state_equivalent=True,nonCalumon_kinds=[5,7,9],group1_loader_arguments=calls,
  boundary='Effect creation is an explicit imported service; real group1 caller executes to loader boundary; no runtime transition claim')

def resource_proof(after,source,old,gba):
 need(struct.unpack_from('<I',after,0x3534B8)[0]==0x0860B000,'real loader group1 record owner')
 row=0x60B000+11*32;fields=struct.unpack_from('<8I',after,row)
 need(fields==(0x084B0000,0x0861B4BC,0x084A1390,0x084A1390,0x08568000,0,0,0),'actual group1 ID11 complete resource row')
 spec=next(s for s in p1.SPECS if s[0]==41)
 def scoped_need(ok,label):
  if label!='all fourteen source populations':p1.need(ok,label)
 # Reuse the existing complete event/renderer walk for the one newly reachable record.
 check=types.FunctionType(p1.all_resources.__code__,dict(p1.__dict__,SPECS=(spec,),need=scoped_need),argdefs=p1.all_resources.__defaults__)
 rows,totals=check(after,source)
 counts=[]
 for field in(2,3):counts.append(palette_check(after,fields[field]-0x08000000,source,far(source,0x740000+41*32+field*6)))
 p4=p4_check(after,source,next(s for s in ADDED if s[0]==41),old,gba)
 return dict(native_row=row,fields=fields,P1_and_P0=rows,complete_event_totals=totals,palette_profiles=counts,P4=p4,
  resource_changes=False,scope='Complete source record41 P1 graph, renderer P0/layout/tile bounds, both palettes and typed P4; no new art or attack parity claim')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('before','gba','wsc10','wsc15','output','manifest'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();paths=[getattr(a,n).resolve()for n in('before','gba','wsc10','wsc15','output','manifest')]
 need(len(set(paths))==6 and not a.output.exists() and not a.manifest.exists(),'fresh nonalias isolated outputs')
 before,gba,old,source=[getattr(a,n).read_bytes()for n in('before','gba','wsc10','wsc15')]
 proof=source_proof(before,gba,old,source)
 after=bytearray(before);struct.pack_into('<I',after,SITE,0xEA00000C);after=bytes(after)
 inverse=bytearray(after);inverse[SITE:SITE+4]=before[SITE:SITE+4]
 need(bytes(inverse)==before and sum(a!=b for a,b in zip(before,after))==1,'whole sixteen MiB inverse and exact one-byte delta')
 arm=arm_proof(before,after);resources=resource_proof(after,source,old,gba)
 negative=[]
 for label,word in(('restore retail denial',0x1A00000C),('skip boss identity compare',0xEA00000E)):
  bad=bytearray(after);struct.pack_into('<I',bad,SITE,word)
  try:arm_proof(before,bytes(bad))
  except ValueError:negative.append(label)
  else:raise ValueError('mutation accepted '+label)
 report=dict(status='IMPMON_EVOLUTION_CLEAN15_AUTHOR_PASS',input_sha256=INPUT,output_sha256=sha(after),source_proof=proof,ARM=arm,resource_proof=resources,
  writes=[dict(offset=SITE,size=4,before_hex=before[SITE:SITE+4].hex(),after_hex=after[SITE:SITE+4].hex())],declared_bytes=4,changed_bytes=1,whole_inverse=True,
  rejected_mutations=negative,builder_sha256=sha(Path(__file__).read_bytes()),emulator_launched=False,runtime_evolution_verified=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
 a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_bytes((json.dumps(report,indent=2)+'\n').encode())
 print(json.dumps({k:report[k]for k in('status','input_sha256','output_sha256','declared_bytes','changed_bytes','builder_sha256')},indent=2))

if __name__=='__main__':main()
