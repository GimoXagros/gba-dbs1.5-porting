#!/usr/bin/env python3
"""Independent narrow HUD guard QA; actual ARM joins, no production imports."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner

BASE,ENTRY,HOOK,CAVE,END=0x08000000,0x373ED0,0x373ED8,0x6FF400,0x6FF410
JOIN,BODY,RETURN=0x08373EDC,0x08373EE0,0x09000000
BEFORE='D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
AFTER='C8E810258B41A979A4DCE514119D8CAF139D615D63355F18F1C2E49AD72332F6'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
LAYOUT='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
IRQ='D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C'
ENTRY_MANIFEST='DF4EB38EA39F845B936A08CE0923B966BE8ECC729B697AD5FDEED16F3A08E746'
PRIMITIVES={
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
 'verify_shoot_attack_dispatch.py':'695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698',
 'verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}

def need(ok,why):
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def branch(at,to):return 0xEA000000|(((to-at-8)//4)&0xFFFFFF)
def destination(at,w):
 d=w&0xFFFFFF
 return BASE+at+8+4*(d-(0x1000000 if d&0x800000 else 0))
def listing(b,a,n):
 rows=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[a:a+n],BASE+a))
 need(sum(x.size for x in rows)==n,'whole ARM decode')
 return [x.mnemonic+' '+x.op_str for x in rows]

def structure(before,after):
 need(len(before)==len(after)==0x800000,'complete8MiB extent')
 need(u(before,HOOK)==0xE3590007 and before[CAVE:END]==b'\xff'*16,'original CMP7 and erased16B cave')
 expected={HOOK:struct.pack('<I',branch(HOOK,CAVE)),CAVE:struct.pack('<4I',
  0xE359000B,0x012FFF1E,0xE3590007,branch(CAVE+12,JOIN-BASE))}
 inverse=bytearray(after)
 for at,data in expected.items():
  need(after[at:at+len(data)]==data,'independent expected hook/wrapper encoding')
  inverse[at:at+len(data)]=before[at:at+len(data)]
 need(inverse==before,'whole20B inverse and all other bytes unchanged')
 return {'declared_bytes':20,'changed_bytes':sum(a!=b for a,b in zip(before,after)),
  'whole_ROM_inverse':True,'non11_body_unchanged':[0x373EE0,0x373F68]}

def ownership(before,ledger_blob,irq_blob,entry_blob):
 need((sha(ledger_blob),sha(irq_blob),sha(entry_blob))==(LAYOUT,IRQ,ENTRY_MANIFEST),'frozen ownership inputs')
 ledger,irq,entry=map(json.loads,(ledger_blob,irq_blob,entry_blob))
 need(ledger['normalized_interval_count']==1394 and ledger['layer_count']==70,'complete1394 interval70 layer inventory')
 need(entry['output_sha256']==BEFORE and entry['ownership']['ranges']==[['6FF380','6FF400']],
  'complete entry128B reservation, including24 erased tail bytes')
 owned=[[0,0x400000]]+ledger['merged_union']+irq['reservations']+[
  [0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0],[0x33FD04,0x33FD08],[0x6FF380,0x6FF400]]
 need(not any(a<END and CAVE<z for a,z in owned),'disjoint original/v73/entry reservations including erased tails')
 scanner.SPANS=((CAVE,END),)
 need(not scanner.inbound(before),'strict all-alignment mirrored pointer/ARM/Thumb inbound; zero exemptions')
 return {'reservation':[CAVE,END],'entry_reservation':[0x6FF380,0x6FF400],
  'all_alignment_mirrors_ARM_Thumb':True,'exemptions':0,'normalized_intervals':1394}

def source_and_callers(source,retail,before,after):
 rows=[i.mnemonic+' '+i.op_str for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(source[0x78769E:0x7876AC],0x78769E)]
 need(rows==['cmp byte ptr [0x5c], 7','je 0x7876ec','cmp byte ptr [0x5c], 0xb','je 0x7876ec'],
  'actual source stage7+11 skip to same epilogue')
 need(sha(source[0x78768C:0x7876F5])=='8119592B6032FC462770AE561830DF57F639BDA61A2F38408EEEB09013130224'
  and source[0x7876EC:0x7876F5]==bytes.fromhex('9D1F075E5B5A5958CB'),'complete source flags/register restore')
 need(before[ENTRY:0x373F68]==retail[ENTRY:0x373F68],'retail score consumer lineage')
 need(u(before,0x373F54)==0x03002310 and listing(before,ENTRY,8)==[
  'ldr r8, [pc, #0x7c]','ldrb sb, [r8, #0xe]'],'actual native stage byte owner')
 direct=[]
 for at in range(0,len(before),4):
  w=u(before,at)
  if w&0x0E000000==0x0A000000 and destination(at,w)==BASE+ENTRY:direct.append((at,w>>24))
 need(direct==[(0x373538,0xEB),(0x3735A4,0xEB),(0x37364C,0xEB)],'all aligned direct HUD references are three BL callers')
 need(before.find(struct.pack('<I',BASE+ENTRY))<0,'no absolute HUD pointer at any alignment')
 for at in (0x37353C,0x3735A8):
  need(listing(after,at,8)==['ldm sp!, {lr}','bx lr'],'two unconditional tail returns')
 need(listing(after,0x373650,16)==['ldr r8, [pc, #0xc8]','ldrh sb, [r8, #2]',
  'cmp sb, #2','bne #0x83736bc'],'battle caller defines all NZCV before branch')
 need(listing(after,0x11DD8,28)==['pop {r2, r5, lr}','ldr r8, [pc, #0x64]',
  'ldr r4, [r8]','ldr r0, [r4, #4]','ldr r8, [r5, #4]',
  'cmp r8, r0','ldr r5, [r5, #0xc]'],'ordinary scheduler overwrites all NZCV before conditional use')
 need(u(before,0xD1C1C)==0x083734F0 and u(before,0x33FDA4)==0x0837354C
  and u(before,0x6FFD88)==0x0837354C,'retained positive task callback owners')
 need(before[0x37DB3C:0x37DB48]==bytes.fromhex('00C09FE51CFF2FE1E9D53708')
  and before[0x37D5E8:0x37D5EC]==bytes.fromhex('06DF7047'),'unchanged ARM/Thumb BIOS divider boundary pinned, not executed')
 return {'direct_BL_callers':[a for a,_ in direct],
  'flags_dead_at':[0x08011DEC,0x08373658],
  'qualified_ABI':'Two tail-return callers use the retained ordinary native task scheduler; no arbitrary external callback ABI claim',
  'source_restores_flags':True,'stage11_intermediate_CPSR_equality_claim':False}

def fixture(data,stage,flags):
 m=Machine(data,stage%7,flags=(flags<<28)|0xD3)
 m.r[14]=RETURN;m.put(0x0300231E,stage,1)
 return m

def semantics(before,after,stages=range(256),flag_values=range(16)):
 count=0
 for stage in stages:
  for flags in flag_values:
   old,new=fixture(before,stage,flags),fixture(after,stage,flags)
   old.run(BASE+ENTRY,{JOIN})
   if stage==11:
    need(new.run(BASE+ENTRY,{RETURN,BODY,JOIN})==RETURN,'stage11 returns before original BX/body')
    need(old.r[:15]==new.r[:15],'stage11 wrapper changes no register/SP/LR beyond retained stage prefix')
    need(new.reads==[(0x0300231E,1)] and not new.writes and not new.calls,
     'stage11 no actor/global-selection/stack/VRAM/BIOS access')
   else:
    need(new.run(BASE+ENTRY,{JOIN,RETURN,BODY})==JOIN,'non11 rejoins exact original conditional return')
    need(old.r[:15]==new.r[:15] and old.cpsr==new.cpsr and old.reads==new.reads
     and not new.writes and not new.calls,'exact non11 registers/CPSR/reads/writes at unchanged body boundary')
    a=old.run(JOIN,{BODY,RETURN});b=new.run(JOIN,{BODY,RETURN})
    need(a==b==(RETURN if stage==7 else BODY),'original stage7 return and other stage body route')
   count+=1
 return count

def caller_flags(data):
 count=0
 for call,ret,stop in ((0x373538,0x37353C,0x08011DF0),(0x3735A4,0x3735A8,0x08011DF0),
                       (0x37364C,0x373650,0x0837365C)):
  traces=[]
  for flags in range(16):
   m=fixture(data,11,flags)
   sp=m.r[13]
   # Actual outer task callback saves LR before the HUD call; scheduler restores its own frame.
   for at,value in ((sp,0x08011DD8),(sp+4,7),(sp+8,0x02010000),(sp+12,RETURN),
    (0x03001344,0x02010118),(0x02010004,0x6000),(0x0201011C,0x6000),(0x03004502,2)):
    m.put(at,value)
   need(m.run(BASE+call,{stop})==stop,'actual linked HUD caller and subsequent native NZCV kill')
   traces.append((m.r[:15],m.cpsr,m.writes))
   need(not m.writes,'stage11 real caller writes no score/stack/VRAM')
   # Independently vary flags at the return site, rather than letting CMP11 normalize them first.
   tail=fixture(data,11,flags);tail.r[:15]=m.r[:15]
   tail.r[13]=sp;tail.mem=dict(m.mem);tail.cpsr=(flags<<28)|0xD3
   tail.run(BASE+ret,{stop})
   need(tail.cpsr==m.cpsr,'tail has no dependency on any incoming NZCV before its full compare')
   count+=1
  need(all(t==traces[0] for t in traces),'all16 caller entry NZCV converge through native flag kill')
 return count

def controls(before,after,source,retail):
 rows=[]
 def reject(name,fn):
  try:fn()
  except ValueError as e:rows.append({'mutation':name,'rejected_by':str(e)})
  else:raise ValueError('control survived: '+name)
 for name,at,value in (
  ('wrong11 compare',CAVE,0xE359000A),('missing early return',CAVE+4,0xE1A00000),
  ('inverted early return',CAVE+4,0x112FFF1E),('lost CMP7 flags',CAVE+8,0xE1A00000),
  ('wrong retained7 compare',CAVE+8,0xE3590006),('wrong rejoin',CAVE+12,branch(CAVE+12,BODY-BASE))):
  bad=bytearray(after);struct.pack_into('<I',bad,at,value)
  reject(name,lambda:semantics(before,bytes(bad),(0,7,11,255),(0,15)))
 for name,at in (('offtarget body store',0x373F20),('entry erased tail',0x6FF3F0),
  ('adjacent cave byte',END),('progress producer',0xB9E68),('fatal route',0x36E5EC)):
  bad=bytearray(after);bad[at]^=1;reject(name,lambda:structure(before,bytes(bad)))
 bad=bytearray(source);bad[0x7876A8]^=1
 reject('source skip11 changed',lambda:source_and_callers(bytes(bad),retail,before,after))
 # Small positioned scanner controls exercise all pointer alignments/mirrors and instruction forms.
 scanner.SPANS=((CAVE,END),)
 for mirror in (0x08000000,0x0A000000,0x0C000000):
  for align in range(4):
   blob=bytearray(32);struct.pack_into('<I',blob,align,mirror+CAVE+3)
   need(scanner.inbound(blob),'all-alignment mirrored pointer injection detected')
   rows.append({'mutation':f'pointer {mirror:08X}+alignment{align}','rejected_by':'strict scanner direct evidence'})
 origin=CAVE-0x200
 for name,w in (('ARM B',branch(origin,CAVE)),('ARM literal',0xE59F01F8),('ARM ADR',0xE28F0F7E)):
  blob=struct.pack('<I',w)
  need(scanner.inbound(blob,origin),'actual '+name+' inbound detected')
  rows.append({'mutation':name,'rejected_by':'strict scanner direct evidence'})
 for name,blob,at in (('Thumb literal',struct.pack('<H',0x487F),origin),
  ('Thumb ADR',struct.pack('<H',0xA07F),origin),('Thumb B',struct.pack('<H',0xE0FE),origin),
  ('Thumb conditional',struct.pack('<H',0xD03E),CAVE-0x80),
  ('Thumb BL',struct.pack('<HH',0xF000,0xF8FE),origin),
  ('Thumb BLX',struct.pack('<HH',0xF000,0xE8FE),origin)):
  need(scanner.inbound(blob,at),'actual '+name+' inbound detected')
  rows.append({'mutation':name,'rejected_by':'strict scanner direct evidence'})
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('candidate','predecessor','retail','source'):p.add_argument(key,type=Path)
 p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 args=p.parse_args();need(not args.output.exists(),'fresh independent report path')
 for name,digest in PRIMITIVES.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen independent primitive '+name)
 paths=[getattr(args,k)for k in ('candidate','predecessor','retail','source','manifest')]
 need(all(v.suffix.lower()not in('.sav','.state')for v in paths),'ROM/proof inputs only')
 after,before,retail,source,manifest_blob=[v.read_bytes()for v in paths]
 need((sha(before),sha(retail),sha(source))==(BEFORE,RETAIL,SOURCE),'exact independently pinned inputs')
 manifest=json.loads(manifest_blob)
 need(sha(manifest_blob)=='BD1DF6DC17B0E3474F969CA617031B3BEB56FCF6CB300209A12976F28CBD4DAD','frozen author manifest')
 need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==sha(after)
  and manifest['complete_entry_ending_E5_claim']is False,'bounded manifest identity/scope')
 result=structure(before,after)
 own=ownership(before,(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes(),
  (ROOT/'build/shoot-guarded-transition-20261109/component-c.json').read_bytes(),
  (ROOT/'build/shoot-runtime-entry-probe-20261109/experimental.json').read_bytes())
 source_proof=source_and_callers(source,retail,before,after)
 entries=semantics(before,after);callers=caller_flags(after);negative=controls(before,after,source,retail)
 need(sha(after)==AFTER,'frozen candidate hash after semantic verification')
 report=dict(schema=1,status='INDEPENDENT_HUD_GUARD_PASS',candidate_sha256=sha(after),
  predecessor_sha256=sha(before),verifier_sha256=sha(Path(__file__).read_bytes()),manifest_sha256=sha(manifest_blob),
  primitive_sha256=PRIMITIVES,structure=result,ownership=own,source_and_flags=source_proof,
  actual_ARM_stage_NZCV_cases=entries,actual_linked_stage11_caller_cases=callers,
  semantic_and_ownership_controls=negative,imported_service_models=0,
  execution_boundary='Non11 exact register/CPSR/reads/no-write join into byte-identical original body; divider/Thumb/BIOS body not executed',
  emulator_or_save_access=False,main_modified=False,release_approved=False,complete_entry_ending_E5_claim=False)
 args.output.parent.mkdir(parents=True,exist_ok=True)
 args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS: {entries} actual ARM stage/NZCV joins; {callers} linked caller cases; {len(negative)} controls')

if __name__=='__main__':main()
