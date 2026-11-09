#!/usr/bin/env python3
"""Independent combined stage11 probe QA; no production imports/services."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import itertools

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine as PriorMachine
import verify_shoot_score_hud_guard as hud

BASE,SITE,ADAPTER,RETURN=0x08000000,0x36E634,0x5CD9A0,0x09000000
ATTACKER,UPPER,AUX=0x02010018,0x02010248,0x02010478
BEFORE='84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
MACHINE='CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943'
ADAPTER_SHA='FAF0C722D88D307D08C32F20B2F5E06A9713ADC116B54CC2E22805C51CAF7404'

def need(ok,why):
 if not ok:raise ValueError(why)

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def half(b,a):return struct.unpack_from('<H',b,a)[0]
def listing(b,a,n):return [i.mnemonic+' '+i.op_str for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(b[a:a+n],BASE+a)]

class Machine(PriorMachine):
 """Only add the retained immediate post-index unsigned halfword transfers."""
 def __init__(self,data,seed=0,flags=0x10,snapshot=None):
  super().__init__(data,seed,flags);self.snapshot=snapshot or {}
 def get(self,address,size=4):
  for start,blob in self.snapshot.items():
   if start<=address and address+size<=start+len(blob):
    self.reads.append((address,size))
    return sum(self.mem.get(address+i,blob[address+i-start])<<(8*i)for i in range(size))
  return super().get(address,size)
 def run(self,start,stops,max_steps=16000):
  for _ in range(128):
   try:return super().run(start,stops,max_steps)
   except ValueError as e:
    if str(e)!='immediate halfword transfer':raise
    pc=self.r[15]-8;w=self.get(pc)
    need(w&0x0E000090==0x90 and w&0x01600060==0x00400020,
     'only immediate post-index unsigned halfword, no writeback alias')
    base,target=(w>>16)&15,(w>>12)&15
    need(base!=target and base!=15 and target!=15,'bounded halfword register owners')
    offset=((w>>4)&0xF0)|(w&15);address=self.r[base]
    if w&0x100000:self.r[target]=self.get(address,2)
    else:self.put(address,self.r[target],2,True)
    self.r[base]=(address+(offset if w&0x800000 else -offset))&0xFFFFFFFF
    start=pc+4
  raise ValueError('bounded post-index transfer count')

def structure(before,after):
 need(len(before)==len(after)==0x800000,'complete8MiB extent')
 need(u(before,SITE)==0xE59F805C and u(after,SITE)==0xEA097CD9,'exact displaced literal and nonlinking branch')
 inverse=bytearray(after)
 for at,size in((SITE,4),(hud.HOOK,4),(hud.CAVE,16)):inverse[at:at+size]=before[at:at+size]
 need(inverse==before,'entire24-byte combined inverse, no other storage/hook/body edit')
 intermediate=bytearray(after);intermediate[SITE:SITE+4]=before[SITE:SITE+4]
 hud.structure(before,bytes(intermediate))
 need(sha(after[ADAPTER:ADAPTER+156])==ADAPTER_SHA,'existing156-byte adapter exact')
 return {'declared_bytes':24,'changed_bytes':sum(x!=y for x,y in zip(before,after)),
  'whole_ROM_inverse':True,'new_nonfatal_reservation':False,'HUD_reservation':[hud.CAVE,hud.END]}

def composition(before,after,d0,c8):
 need(sha(d0)==hud.BEFORE and sha(c8)==hud.AFTER,'frozen independently approved D0/C8 references')
 present=[(a,before[a:a+4])for a in(0x5C9108,0x5C910C,0x5C9120,0x5C9174,0x5C91A4)]
 hud_delta=[(hud.HOOK,c8[hud.HOOK:hud.HOOK+4]),(hud.CAVE,c8[hud.CAVE:hud.END])]
 nonfatal=[(SITE,struct.pack('<I',0xEA097CD9))]
 spans=[(a,a+len(b))for family in(present,hud_delta,nonfatal)for a,b in family]
 need(all(z<=a2 or z2<=a for (a,z),(a2,z2)in itertools.combinations(spans,2)),'all component declared spans disjoint')
 inv=bytearray(before)
 for a,b in present:inv[a:a+4]=d0[a:a+4]
 need(inv==d0,'whole presentation inverse to D0')
 hud.structure(d0,c8)
 for order in itertools.permutations((present,hud_delta,nonfatal)):
  result=bytearray(d0)
  for family in order:
   for a,b in family:result[a:a+len(b)]=b
  need(result==after,'all six actual component orders commute byte-exactly')
 hud.ownership(before,(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes(),
  (ROOT/'build/shoot-guarded-transition-20261109/component-c.json').read_bytes(),
  (ROOT/'build/shoot-runtime-entry-probe-20261109/experimental.json').read_bytes())
 return {'component_orders_compared':6,'whole_D0_inverse':True,'strict_HUD_ownership_on_84D':True,
  'combined_declared_bytes_from_D0':44,'changed_bytes_from_D0':sum(a!=b for a,b in zip(d0,after))}

def bindings(before,after,retail,source):
 need(sha(after[0x132EC:0x133A8])=='10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B'
  and after[0x132EC:0x133A8]==retail[0x132EC:0x133A8],'real complete native palette consumer')
 need(listing(after,0x36E348,4)==['push {r1, r2, r3, r4, r5, lr}'] and listing(after,0x36E484,8)==[
  'pop {r1, r2, r3, r4, r5, lr}','bx lr'],'enclosing collision return frame')
 rows=[i.mnemonic+' '+i.op_str for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(source[0x76023A:0x760240],0x76023A)]
 need(rows[:2]==['cmp ax, 0xb','je 0x760266'],'real source positive-HP stage11 split')
 need(source[0x76027B:0x760280]==bytes.fromhex('C745600800') and source[0x760287:0x76028E]==bytes.fromhex('26F706D8033040'),
  'source timer8 and flash4030 predicate')
 need(listing(after,0x3730E8,24)==['stmdb sp!, {lr}','ldr r1, [r4, #0x28]',
  'ldrsh r0, [r1, #0x64]','ldrsh r8, [r1, #0x6a]','cmp r0, r8','bgt #0x837312c'],
  'non11 lower refresh full flags kill before consumer')
 need(u(after,0x3700F4)==0xEA085A81 and listing(after,0x586B24,8)==[
  'bl #0x8586c00','b #0x8370248'],'existing live stage11 main dispatcher')
 need(listing(after,0x586C6C,40)==['ldrsh r8, [r5, #0x74]','cmp r8, #0','beq #0x8586c94',
  'subs r8, r8, #1','strh r8, [r5, #0x74]','bne #0x8586c94','str r4, [sp, #-4]!',
  'mov r4, r5','bl #0x8587000','pop {r4}'],'already connected8-update timer expiry')
 need(listing(after,0x587044,4)==['bl #0x80132ec'] and listing(after,0x587064,4)==['bl #0x8586e00'],
  'real expiry P2 load and BG restoration call')
 need(sha((ROOT/'tools/verify_shoot_fatal_callback_route.py').read_bytes())==
  '48600765FC794FBB3A0859520125AB21B3736DCDAD76B491F020F71ADCFBFCF0','frozen prior shared attacker-tail flag proof')
 return {'palette_loader':'080132EC actual instructions, zero service models',
  'non11_NZCV_kill':0x083730F8,'stage11_shared_tail_proof_reused':True,
  'prior_proof':'verify_shoot_fatal_callback_route.py:flags_lifetime; entire shared tail unchanged',
  'timer_lifetime':'eight eligible stage11 main-loop updates, not unqualified video frames'}

def fixture(data,stage,flags=0,mask=0):
 m=Machine(data,stage%5,flags=(flags<<28)|0xD3)
 m.r[4],m.r[5],m.r[11],m.r[14]=ATTACKER,UPPER,0,RETURN
 for a,v,n in ((0x0300231E,stage,1),(0x0300450A,mask,2),(UPPER+0x28,AUX,4),
  (AUX+0x28,UPPER,4),(UPPER+0x64,10,2),(UPPER+0x68,24,2),(UPPER+0x6A,12,2),
  (UPPER+0x74,0x1234,2),(ATTACKER+4,0,2),(UPPER+4,3,2),(ATTACKER+0xA,0,2),
  (ATTACKER+0xC,0,2),(ATTACKER+0xB6,0,2),(ATTACKER+8,0,2),(0x03004D40,0,2)):
  m.put(a,v,n)
 # Actual shared tail's mode/optional-freeze globals, resolved from retained literals.
 m.put(u(data,0x36F870),7,2);m.put(u(data,0x36F874)+2,0,1)
 return m

def effects(m,sp):return [w for w in m.writes if not sp-0x100<=w[0]<sp]
def colors(data,resource,dest):
 slot=half(data,resource+4)-8+dest+16
 return [(0x05000000+32*slot+2+2*k,half(data,resource+8+2*k),2)for k in range(15)]

def joins(before,after):
 count=0
 for stage in range(256):
  if stage==11:continue
  for flags in range(16):
   old,new=fixture(before,stage,flags),fixture(after,stage,flags)
   old.run(BASE+SITE,{0x083730FC});new.run(BASE+SITE,{0x083730FC})
   need(old.r[:15]==new.r[:15] and old.cpsr==new.cpsr and old.writes==new.writes
    and new.reads==[(0x0300231E,1)]+old.reads and old.calls==new.calls,
    'non11 exact real-loader/lower-CMP join; sole added read is actual stage byte')
   count+=1
 shots=0
 for mask in (0,0x10,0x20,0x4000,0x4030):
  for flags in range(16):
   m=fixture(after,11,flags,mask);sp=m.r[13];saved=m.r[1:6]+[RETURN]
   m.run(0x0836E348,{0x0836E34C})
   need(m.r[13]==sp-24,'actual enclosing six-word collision frame')
   m.run(BASE+SITE,{0x0836E438})
   expected=colors(after,0x5C0B00,1)+[(UPPER+0x74,8,2)]
   if mask&0x4030==0:expected += [(0x05000000+32*k,0x1F,2)for k in range(24)]
   need(effects(m,sp)==expected,'exact stage11 palette15/timer8/conditional24 zero-color writes only')
   need(m.r[4]==ATTACKER and m.r[5]==UPPER and m.r[13]==sp-24,'actual loader preserves actors and balances20-byte argument frame')
   need(sum(c[1]==0x080132EC for c in m.calls)==1 and len(m.calls)==1,'one real native palette call, no modeled service')
   m.run(0x0836E438,{RETURN})
   need(m.r[1:6]+[m.r[14]]==saved and m.r[13]==sp,'real common return restores enclosing actors/registers/SP/LR')
   shots+=1
 return count,shots

def hp_prefix(data):
 count=0
 for hp,damage,evolved in ((10,1,0),(10,3,0),(10,3,0x4000),(1,1,0),(1,255,0),(1,1,0x4000)):
  m=fixture(data,11);m.put(UPPER+0x64,hp,2);m.put(ATTACKER+8,evolved,2)
  m.put(0x03004D24,damage,1)
  stop=m.run(0x0836E5C8,{BASE+SITE,0x0836E5EC})
  value=hp-(damage>>bool(evolved))
  need(m.get(UPPER+0x64,2)==value&0xFFFF and stop==(BASE+SITE if value>0 else 0x0836E5EC),
   'actual HP arithmetic reaches new hook only for positive post-hit HP')
  count+=1
 return count

def timer_cases(data):
 bridge=fixture(data,11);bridge.run(0x083700F4,{0x08586C00})
 need(any(c[1]==0x08586C00 for c in bridge.calls),'actual live main hook/dispatcher enters timer owner')
 count=0
 for hp,resource in ((1,0x587150),(12,0x587150),(13,0x587128),(24,0x587128),(25,0x587100)):
  for mask in (0,0x10,0x20,0x4000):
   m=fixture(data,11,0,mask);m.r[4],m.r[5]=ATTACKER,UPPER
   m.put(UPPER+0x64,hp,2);m.put(UPPER+0x74,8,2);sp=m.r[13]
   for step in range(1,9):
    before=len(m.writes);call_before=len(m.calls)
    m.run(0x08586C6C,{0x08586C94})
    need(m.get(UPPER+0x74,2)==8-step and m.r[13]==sp and m.r[4]==ATTACKER,'eight eligible updates and balanced expiry caller')
    if step<8:need(len(m.calls)==call_before,'no premature expiry call')
    else:
     writes=[w for w in m.writes[before:]if not sp-0x100<=w[0]<sp]
     expected=[(UPPER+0x74,0,2)]+colors(data,resource,1)
     if mask&0x4030==0:expected += [(0x05000000+32*k,half(data,0x586F40+2*k),2)for k in range(16)]
     need(writes==expected,'actual threshold P2 restoration and only sixteen BG color-zero entries')
     need(sum(c[1]==0x08587000 for c in m.calls)==1,'exactly one real timer-expiry call')
   before=len(m.writes);m.run(0x08586C6C,{0x08586C94})
   need(len(m.writes)==before,'zero timer cannot expire twice')
   count+=1
 return count

def healthy_capture(data,directory):
 pins={'ewram':'65D380F9ED988253D931269E944C94786B4428EA12F9E9940666A982F70E1DA6',
  'iwram':'9FC46E5351D0FEBB822C18591855E6B2BFE2FCDCC8077FB0EBCA6524B9C4E978',
  'palette':'56BF85590EAC946AE51E6F0A978089CB504A5E600C00218BBE08FE60D8490F68'}
 blobs={k:(directory/f'13-healthy-activation-{k}.bin').read_bytes()for k in pins}
 need({k:sha(v)for k,v in blobs.items()}==pins,'frozen actual healthy activation game RAM/palette')
 snapshot={0x02000000:blobs['ewram'],0x03000000:blobs['iwram'],0x05000000:blobs['palette']}
 first,upper,aux=0x02011710,0x02011828,0x02011940
 m=Machine(data,0,0xB0000010,snapshot)
 need(m.get(0x0300231E,1)==11 and m.get(0x0300489C)==first and m.get(0x030048A0)==upper
  and m.get(0x03004D3C)==aux and m.get(upper+0xF0)==0x085D0000 and m.get(upper+0xF4)==0x085D1000
  and m.get(aux+0xF0)==0x085D029C and m.get(aux+0xF4)==0x085D1100
  and m.get(upper+4,2)&15==3 and m.get(aux+4,2)&15==6,'actual typed healthy Shoot actors/resources')
 need(m.get(first+0x64,2)==4 and m.get(upper+0x64,2)==37,'actual positive captured FIRST4/SECOND37')
 m.r[4],m.r[5],m.r[11],m.r[14]=first,upper,0,RETURN
 sp=m.r[13];saved_first_callback=m.get(first);saved_upper_callback=m.get(upper)
 controllers=[(m.get(0x03004510),m.get(m.get(0x03004510))),(m.get(0x03004514),m.get(m.get(0x03004514)))]
 m.put(0x03004D24,1,1) # Isolated real collision damage input; not a claimed runtime hit.
 m.run(0x0836E348,{0x0836E34C});m.run(0x0836E5C8,{0x0836E438})
 want=[(upper+0x64,36,2)]+colors(data,0x5C0B00,1)+[(upper+0x74,8,2)]
 if m.get(0x0300450A,2)&0x4030==0:want += [(0x05000000+32*k,0x1F,2)for k in range(24)]
 need(effects(m,sp)==want,'captured initialized positive-hit HP37 to36, real P2 flash, timer8, no callback/task writes')
 need(m.get(first+0x64,2)==4 and m.get(first)==saved_first_callback and m.get(upper)==saved_upper_callback
  and all(m.get(header)==callback for header,callback in controllers),'player health and real actor/controller callbacks untouched')
 need(m.r[4]==first and m.r[5]==upper and m.r[13]==sp-24,'real loader preserves captured actor ownership and original collision frame')
 start=len(m.writes)
 for _ in range(8):m.run(0x08586C6C,{0x08586C94})
 need(m.get(upper+0x74,2)==0 and m.get(upper+0x64,2)==36,'actual captured timer expires after eight eligible fragment calls')
 need(sum(c[1]==0x08587000 for c in m.calls)==1,'one actual captured expiry call')
 expiry=[w for w in m.writes[start:]if not sp-0x100<=w[0]<sp]
 want_expiry=[(upper+0x74,v,2)for v in range(7,-1,-1)]+colors(data,0x587100,1)
 if m.get(0x0300450A,2)&0x4030==0:
  # Captured source color-state counter is not assumed zero; derive its actual restore step.
  bg=[w for w in expiry if 0x05000000<=w[0]<0x05000200 and (w[0]-0x05000000)%32==0]
  need(len(bg)==16,'actual restore touches sixteen BG zero entries')
  other=[w for w in expiry if w not in bg and w[0]!=0x03004D40]
 else:other=expiry
 need(other==want_expiry,'actual captured HP-threshold palette restored, no repeated flash callback/task writes')
 need(all(m.get(header)==callback for header,callback in controllers),'real controllers survive timer expiry')
 return {'capture_sha256':pins,'FIRST':first,'SECOND':upper,'auxiliary':aux,
  'isolated_damage_input':1,'native_HP_before':37,'native_HP_after':36,'P1_HP':4,
  'positive_hit_actual_ARM':True,'eligible_timer_updates':8,'expiry_calls':1,
  'not_actual_emulator_hit':True,'collision_tail_boundary':0x0836E438}

def controls(before,after):
 rejected=[]
 def reject(name,fn):
  try:fn()
  except ValueError:rejected.append(name)
  else:raise ValueError('negative survived '+name)
 for name,at,w in (('linked hook',SITE,u(after,SITE)|0x01000000),('wrong target',SITE,u(after,SITE)+1),
  ('outside hook',SITE+4,u(after,SITE+4)^1),('resident code changed',ADAPTER,u(after,ADAPTER)^1)):
  bad=bytearray(after);struct.pack_into('<I',bad,at,w);reject(name,lambda:structure(before,bad))
 for name,at,w,fn in (('lost palette argument balance',0x5CD9D4,0xE28DD010,lambda b:joins(before,b)),
  ('wrong flash timer',0x5CD9D8,0xE3A08007,lambda b:joins(before,b)),
  ('wrong flash palette destination',0x5CD9C8,0xE3A08000,lambda b:joins(before,b)),
  ('lower flags no longer killed',0x3730F8,0xE1A00000,lambda b:joins(before,b)),
  ('timer expires early',0x586C78,0xE2588002,timer_cases),
  ('expiry selects wrong HP threshold',0x587010,0xD59F805C,timer_cases)):
  bad=bytearray(after);struct.pack_into('<I',bad,at,w);reject(name,lambda:fn(bytes(bad)))
 return rejected

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('candidate','predecessor','retail','source'):p.add_argument(key,type=Path)
 p.add_argument('--manifest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--capture',type=Path,required=True)
 a=p.parse_args();need(not a.output.exists(),'fresh report path')
 need(sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes())==MACHINE,'frozen independent ARM machine')
 files=[getattr(a,k)for k in ('candidate','predecessor','retail','source','manifest')]
 need(all(x.suffix.lower()not in('.sav','.state')for x in files),'ROM/proof inputs only')
 after,before,retail,source,mb=[x.read_bytes()for x in files]
 need((sha(before),sha(retail),sha(source))==(BEFORE,RETAIL,SOURCE),'exact predecessor and original inputs')
 need(sha((ROOT/'tools/verify_shoot_score_hud_guard.py').read_bytes())=='AB2B16EBFFEFD5617ED0C7275F64B459077548473AF545159FCED2618BBB0407','frozen independent HUD proof helper')
 structure_result=structure(before,after)
 compose=composition(before,after,(ROOT/'build/shoot-runtime-entry-probe-20261109/experimental.gba').read_bytes(),
  (ROOT/'build/shoot-score-hud-guard-20261109/component.gba').read_bytes())
 binding=bindings(before,after,retail,source)
 non11,stage11=joins(before,after);hp=hp_prefix(after);timers=timer_cases(after);neg=controls(before,after)
 captured=healthy_capture(after,a.capture)
 manifest=json.loads(mb);need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==sha(after),'manifest identities')
 report=dict(schema=1,status='INDEPENDENT_STAGE11_RUNTIME_PROBE_PASS',candidate_sha256=sha(after),
  predecessor_sha256=sha(before),verifier_sha256=sha(Path(__file__).read_bytes()),manifest_sha256=sha(mb),
  structure=structure_result,composition=compose,bindings=binding,healthy_capture=captured,actual_non11_stage_NZCV_joins=non11,
  actual_stage11_mask_NZCV_collision_returns=stage11,actual_HP_prefix_cases=hp,
  actual_eight_update_timer_cases=timers,negative_controls=neg,service_models=0,
  interpreter_extension='Checked retained immediate post-index unsigned halfword transfers only',
  old_full_suites_rerun=False,emulator_or_save_access=False,healthy_nonfatal_runtime_proved=False,
  main_modified=False,complete_Shoot_or_E5_claim=False)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS {non11} non11 joins; {stage11} stage11 returns; {timers} timer cases; {len(neg)} controls')

if __name__=='__main__':main()
