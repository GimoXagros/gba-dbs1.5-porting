"""Independent source partitions and actual ARM checks for ID13 air relaunch.

Implementation addresses and storage checks are completed against the frozen
candidate before this verifier is run; this file imports no production builder.
"""
import argparse
import hashlib
import itertools
import json
import struct
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local/pydeps'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine
from verify_shoot_caller_resident import signed
import verify_shoot_caller_resident as reference_scanner

BASE=0x08000000
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE='C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
ACTOR=0x02011710
PRESENT=ACTOR+0xAC
RETURN=0x08001234
HORIZONTAL,LANDING,ATTACK,OTHER,EVENT,TICK=(0x0835604C,0x08355B54,0x08355998,0x08355B04,0x08012874,0x08012A84)
STATES={'init':0x08D3F200,'ready':0x08D3F280,'boost':0x08D3F500,'spent':0x08D3F700}
HOOKS=((0x357054,0xD3F100,0x357030,0x3570DC),(0x35732C,0xD3F150,0x357308,0x3573B4),(0x3578D4,0xD3F1A0,0x3578B0,0x35795C))
FIRST,LIMIT=0xD3F100,0xD3FA00

def need(ok,label):
 if not ok:raise ValueError(label)

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def word(b,at):return struct.unpack_from('<I',b,at)[0]
def half(b,at):return struct.unpack_from('<H',b,at)[0]

def source_expectation(state,initial,helpers,states):
 """State transitions transcribed from source785797..785992, not ARM output."""
 values=dict(initial);calls=[]
 def event(n):calls.append(('event',n))
 def horizontal():
  calls.append(('horizontal',None));values[0x42]=0;values[0x46]=0
  if values[0x2C]&0xA:
   values[0xB4]|=0x4000
   values[0x42]=values[0xA0]
   if values[0x2C]&8:
    values[0x42]=(-signed(values[0xA0],16))&0xFFFF;values[0xB4]&=~0x4000
 def service(name):calls.append((name,None));return helpers[name]!=0
 def gravity():
  if values[0xAA]==0:
   values[0xAA]=1;values[0x48]=0x16 if values[0xA2]==1 else 0x1E
   event(10 if values[0xA2]==1 else 7)
 if state=='init':
  values[0xA8]=0x100;values[0xA0]=0xF0;values[0]=states['ready'];state='ready'
 if state in ('ready','spent'):
  horizontal()
 if state=='ready':
  if values[0x2C]&0x40:
   if values[8]&0x4000:
    values[0xA6]|=1;values[0]=0x08357DD4;return values,calls
   if not values[0xA8]&0x100:
    values[0xA8]|=0x100;values[0xAA]=0;values[0x6E]=0x10
    values[0x48]=0x18;values[0x44]=0xFD80
    values[0xA8]=(values[0xA8]&0xFF00)|((values[0xA8]+1)&255)
    event(0x72);values[0]=states['boost'];return values,calls
  else:values[0xA8]&=255
 if signed(values[0x44],16)>0:
  gravity()
  if service('landing'):return values,calls
  if state=='boost':
   event(10 if values[0xA2]==1 else 7);values[0x6E]=3
   values[0]=states['ready'] if values[0xA8]&255<3 else states['spent']
 if state!='boost':
  if service('attack'):return values,calls
  if service('other'):return values,calls
 calls.append(('tick',1))
 return values,calls

def fixture(rom,state,values,helpers,states,flags=0xA0000010):
 m=Machine(rom,seed=3,flags=flags)
 for offset in range(0x118):m.put(ACTOR+offset,0,1)
 for offset,value in values.items():m.put(ACTOR+offset,value,4 if offset==0 else 1 if offset==0x6E else 2)
 m.r[4]=ACTOR;m.r[5]=PRESENT;m.r[14]=RETURN
 observed=[]
 def helper(name):
  def invoke(cpu):
   observed.append((name,None));cpu.r[0]=helpers[name]&0xFFFFFFFF
   cpu.r[8]=0xBAD00008;cpu.r[9]=0xBAD00009;cpu.cpsr=0x50000010
  return invoke
 for name,address in (('landing',LANDING),('attack',ATTACK),('other',OTHER)):m.services[address]=helper(name)
 def animation(name):
  def invoke(cpu):
   n=cpu.get(cpu.r[13]);need(cpu.get(cpu.r[13]+8)==PRESENT,'actual presentation stack argument')
   need(cpu.get(cpu.r[13]+4)==cpu.r[11],'actual source segment placeholder stack argument')
   observed.append((name,n));cpu.r[8]=0xC0DE0008;cpu.r[9]=0xC0DE0009;cpu.cpsr=0x90000010
  return invoke
 m.services[EVENT]=animation('event');m.services[TICK]=animation('tick')
 return m,observed

def state_case(rom,state,initial,helpers,states,flags=0xA0000010):
 expected,calls=source_expectation(state,initial,helpers,states)
 m,observed=fixture(rom,state,initial,helpers,states,flags)
 original=m.r[:];initial_memory=m.mem.copy()
 m.run(states[state],{RETURN})
 # The short native horizontal routine executes; only its call label is joined.
 actual=[];pending=iter(observed)
 for _,target,_ in m.calls:
  if target==HORIZONTAL:actual.append(('horizontal',None))
  elif target in (LANDING,ATTACK,OTHER,EVENT,TICK):actual.append(next(pending))
 need(actual==calls,'source-ordered service calls '+state)
 need(m.r[4:8]==original[4:8] and m.r[11:15]==original[11:15],'callback actor/presentation/SP/LR ABI '+state)
 for offset,value in expected.items():
  size=4 if offset==0 else 1 if offset==0x6E else 2
  need(m.get(ACTOR+offset,size)==value&((1<<(size*8))-1),'source field '+state+'/'+hex(offset))
  for n in range(size):initial_memory[ACTOR+offset+n]=(value>>(8*n))&255
 need(all(m.mem[address]==value for address,value in initial_memory.items() if ACTOR<=address<ACTOR+0x118),'no adjacent actor corruption')
 need(all(ACTOR<=a<ACTOR+0x118 or original[13]-0x80<=a<original[13] for a,_,_ in m.writes),'bounded actor/stack write ownership')
 return len(m.calls)

def initial_values(state):
 values={0:STATES[state],8:0,0x2C:0,0x42:0x1111,0x44:0,0x46:0x2222,0x48:0x3333,
         0x6E:0x55,0xA0:0xF0,0xA2:1,0xA6:0x80,0xA8:0x100,0xAA:0,0xB4:0x1280}
 return values

def state_cases(rom):
 count=0;zero={'landing':0,'attack':0,'other':0}
 # Signed velocity, three service early returns, lazy gravity and event choice.
 for state,velocity,phase,lazy,stop in itertools.product(('init','ready','boost','spent'),(0,1,0x7FFF,0x8000,0xFFFF),(0,1,0xFFFF),(0,1,0xFFFF),('none','landing','attack','other')):
  values=initial_values(state);values.update({0x44:velocity,0xA2:phase,0xAA:lazy})
  helpers=dict(zero)
  if stop!='none':helpers[stop]=0x80000001
  state_case(rom,state,values,helpers,STATES);count+=1
 # Release/hold, byte carry, retained high byte, evolved delegation, directional input.
 for packed,keys,evolved in itertools.product((0,1,2,3,0xFE,0xFF,0x100,0x102,0x103,0xAAFE,0xAAFF,0xABFF),(0,2,8,0xA,0x40,0x42,0x48,0x4A),(0,0x4000)):
  values=initial_values('ready');values.update({0xA8:packed,0x2C:keys,8:evolved,0x44:1})
  state_case(rom,'ready',values,zero,STATES);count+=1
 for packed in (0,1,2,3,4,0xFF,0x100,0x102,0x103,0xFF02,0xFF03):
  values=initial_values('boost');values.update({0xA8:packed,0x44:1})
  state_case(rom,'boost',values,zero,STATES);count+=1
 for keys in (0x40,0x42,0x48,0x4A):
  values=initial_values('spent');values.update({0xA8:3,0x2C:keys,0x44:1})
  state_case(rom,'spent',values,zero,STATES);count+=1
 return count

def sequence_case(rom):
 zero={'landing':0,'attack':0,'other':0};values=initial_values('init');values[0xA8]=0x19
 m,observed=fixture(rom,'init',values,zero,STATES)
 # External physics supplies velocity boundaries; no trajectory/timing is inferred.
 steps=[(0x40,1),(0,1)]
 for attempt in range(3):
  steps.extend(((0x40,1),(0x40,1)))
  if attempt<2:steps.append((0,1))
 steps.append((0x40,1))
 for keys,velocity in steps:
  state=next(k for k,v in STATES.items() if v==m.get(ACTOR))
  m.put(ACTOR+0x2C,keys,2);m.put(ACTOR+0x44,velocity,2)
  initial={off:m.get(ACTOR+off,4 if off==0 else 1 if off==0x6E else 2) for off in values}
  expected,calls=source_expectation(state,initial,zero,STATES)
  m.calls.clear();observed.clear();sp=m.r[13];m.r[14]=RETURN
  m.run(STATES[state],{RETURN});need(m.r[13]==sp,'multi-update callback stack balanced')
  actual=[];service_iter=iter(observed)
  for _,target,_ in m.calls:
   if target==HORIZONTAL:actual.append(('horizontal',None))
   elif target in (LANDING,ATTACK,OTHER,EVENT,TICK):actual.append(next(service_iter))
  need(actual==calls,'multi-update source call order')
  for off,value in expected.items():need(m.get(ACTOR+off,4 if off==0 else 1 if off==0x6E else 2)==value,'multi-update source field '+hex(off))
 need(m.get(ACTOR)==STATES['spent'] and m.get(ACTOR+0xA8,1)==3,'three relaunches exhausted and fourth press rejected')
 return len(steps)

def route_machine(rom,ident,keys,flags,callback=0x08357000):
 m=Machine(rom,seed=5,flags=flags)
 m.r[4]=ACTOR;m.r[5]=PRESENT;m.r[14]=RETURN
 m.put(ACTOR,callback);m.put(ACTOR+0x11,ident,1);m.put(ACTOR+0x2C,keys,2)
 # The common-fall prologue already owns this saved return address.
 m.put(m.r[13],RETURN)
 return m

def route_cases(before,after):
 count=0
 for hook,_,gate,skip in HOOKS:
  for ident,nzcv in itertools.product(range(256),(0,5,10,15)):
   keys=(0,0x40,0x4A,0xFFFF)[(ident+nzcv)%4]
   old=route_machine(before,ident,keys,(nzcv<<28)|0x10)
   new=route_machine(after,ident,keys,(nzcv<<28)|0x10)
   startsp=new.r[13]
   end=new.run(BASE+hook,{BASE+hook+4,RETURN})
   if ident==13:
    need(end==RETURN and new.get(ACTOR)==STATES['init'],'ID13 assigns source0577 independently of held A')
    need(new.r[13]==startsp+4 and new.r[14]==RETURN,'ID13 consumes exactly common-fall saved LR')
   else:
    old.run(BASE+hook,{BASE+hook+4})
    need(end==BASE+hook+4 and new.r[:15]==old.r[:15] and new.cpsr==old.cpsr,'non-ID13 displaced load exact ABI/flags')
    need(new.get(ACTOR)==old.get(ACTOR),'non-ID13 callback preserved')
   count+=1
  for velocity,one_shot,flag8,ident in itertools.product((0,1,0x7FFF,0x8000,0xFFFF),(0,1),(0,0x100),(12,13,14)):
   m=route_machine(after,ident,0,0xB0000010);sp=m.r[13]
   m.put(ACTOR+0x44,velocity,2);m.put(ACTOR+0xA6,one_shot,2);m.put(ACTOR+8,flag8,2)
   end=m.run(BASE+gate,{BASE+skip,BASE+hook+4,RETURN})
   eligible=signed(velocity,16)>0 and not one_shot and not flag8
   need(end==(RETURN if eligible and ident==13 else BASE+hook+4 if eligible else BASE+skip),'native outer fall gates preserved')
   need(m.r[13]==sp+(4 if eligible and ident==13 else 0),'outer gate stack ownership')
   count+=1
 return count

def source_contract(source,before,gba):
 need(sha(source)==SOURCE,'immutable source')
 need(sha(source[0x785797:0x785993])=='95AF262178FE267C49AB7DE8DC687C93BDEE5D87430F5DB08567BE75C66E3F77','complete four-state source body')
 instructions={i.address:i.mnemonic+' '+i.op_str for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(source[0x785797:0x785993],0x785797)}
 expected={0x78579E:'mov word ptr [si + 0x92], 0x100',0x7857A4:'mov word ptr [si + 0x8a], 0xf0',
           0x7857C6:'or word ptr [si + 0x90], 1',0x7857E4:'mov word ptr [si + 0x94], 0',
           0x7857EA:'mov byte ptr [si + 0x5a], 0x10',0x7857EE:'mov word ptr [si + 0x38], 0x18',
           0x7857F3:'mov word ptr [si + 0x34], 0xfd80',0x7857FC:'inc al',
           0x785819:'jmp 0x785992',0x78581C:'and word ptr [si + 0x92], 0xff',
           0x78583B:'mov word ptr [si + 0x38], 0x16',0x78584A:'mov word ptr [si + 0x38], 0x1e',
           0x7858EF:'mov byte ptr [si + 0x5a], 3',0x7858F7:'cmp al, 3',0x7858F9:'jae 0x785907',0x785992:'retf '}
 for address,text in expected.items():need(instructions[address]==text,'source semantic anchor '+hex(address))
 pattern=bytes.fromhex('c7047705c744022285');at=0;hits=[]
 while True:
  at=source.find(pattern,at)
  if at<0:break
  hits.append(at);at+=1
 need(hits==[0x7682FA,0x7684D3,0x7688DF,0x768AD1],'all four direct source initializer assignments')
 for lo,hi in ((0x35604C,0x3560A0),(0x356FDC,0x357988),(0x357988,0x357F58)):
  need(before[lo:hi]==gba[lo:hi],'retained native family provenance')
 need(word(before,0x357EE0)==0xE1C49ABA and source[0x78557B:0x785581]==bytes.fromhex('c78494000100'),'source94/nativeAA same existing02BD field writer')
 need(word(before,0x3578BC)==0xE1D48AB6 and source[0x7688CA:0x7688CF]==bytes.fromhex('f784900001'),'source90/nativeA6 common fall flag')
 op=word(before,0x627C40)
 need(op>>24==0xEA and BASE+0x627C40+8+signed(op&0xFFFFFF,24)*4==0x0835774C,'Iraira tail branches to retained launch')
 need(word(before,0x357780)==0xE28F8020 and word(before,0x357784)==0xE5848000 and BASE+0x357780+8+0x20==0x083577A8,'retained launch assigns common jump/fall callback')
 need(word(before,0x357A44)==0xE3A09002 and word(before,0x357A58)==0xE3A09040,'existing special gravity2/velocity64 fixed-point anchors')
 need(word(before,0x357DF4)==0xE3A0907E and word(before,0x357F00)==0xE3A00080,'existing special duration126/horizontal128 anchors')
 return {'source_callback_assignments':hits,'states_source_raw':[0x785797,0x7857B3,0x78588E,0x785921],
         'field_map':{'90':'A6','92':'A8','94':'AA'},'new_same_update_tick_after_relaunch':False,
         'units':'Existing special-aerial fixed-point literals retained; wall-clock trajectory parity not established.'}

def structural(before,after,manifest,audio,tables):
 need(sha(before)==BEFORE and len(before)==len(after)==0x1000000,'exact before and 16MiB extents')
 need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==sha(after),'frozen manifest identities')
 need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'whole new code reservation blank')
 need([0xD33000,0xD40000] in audio['reservations'] and tables['allocation']['remaining_tail']==[0xD3F05A,0xD40000],'nested allocation ownership')
 for entry in audio['writes']:
  if 0xD33000<=entry['offset']<0xD40000:
   at,size=entry['offset'],entry['size']
   need(sha(after[at:at+size])==entry['after_sha256'],'previous audio payload remains exact')
 for entry in tables['writes']:
  at,size=entry['offset'],entry['size']
  need(after[at:at+size]==bytes.fromhex(entry['after_hex']),'previous evolution fix remains exact')
 writes=manifest['writes'];inverse=bytearray(after);occupied=set()
 expected_starts={x[0] for x in HOOKS}|{x[1] for x in HOOKS}|{v-BASE for v in STATES.values()}
 need({w['offset'] for w in writes}==expected_starts and len(writes)==10,'only three hooks, three adapters, four callbacks')
 for w in writes:
  at,size=w['offset'],w['size'];positions=set(range(at,at+size))
  need(not occupied&positions,'disjoint exact writes');occupied|=positions
  need(at in {x[0] for x in HOOKS} and size==4 or FIRST<=at<at+size<=LIMIT,'write ownership')
  need(before[at:at+size]==bytes.fromhex(w['before_hex']) and after[at:at+size]==bytes.fromhex(w['after_hex']),'each exact before/after span')
  inverse[at:at+size]=before[at:at+size]
 need(inverse==before,'complete image inverse and no off-target changes')
 for hook,adapter,_,_ in HOOKS:
  opcode=word(after,hook);target=BASE+hook+8+signed(opcode&0xFFFFFF,24)*4
  need(opcode>>24==0xEA and target==BASE+adapter and word(before,hook)==0xE1D482BC,'unlinked hook replaces exact input load')
 scanner=types.FunctionType(reference_scanner.inbound.__code__,dict(reference_scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=reference_scanner.inbound.__defaults__)
 need(not scanner(before),'no prior whole-ROM encoded reference into reservation')
 inbound=scanner(after)
 need(all(at in occupied for _,at,_ in inbound),'only new owned code/hooks reference new reservation')
 return {'writes':len(writes),'declared_bytes':len(occupied),'changed_bytes':sum(a!=b for a,b in zip(before,after)),
         'whole_inverse':True,'prior_inbound':0,'new_inbound':len(inbound),'reservation':[FIRST,LIMIT]}

def mutation_checks(after,before):
 rejected=[];zero={'landing':0,'attack':0,'other':0}
 decoded=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(after[STATES['ready']-BASE:STATES['ready']-BASE+356],STATES['ready']))
 def find(text):
  hits=[i.address-BASE for i in decoded if i.mnemonic+' '+i.op_str==text]
  need(len(hits)==1,'unique reviewed mutation anchor '+text);return hits[0]
 def reject(name,at,opcode,check):
  broken=bytearray(after);struct.pack_into('<I',broken,at,opcode)
  try:check(bytes(broken))
  except (ValueError,AssertionError):rejected.append(name)
  else:raise ValueError('negative control escaped: '+name)
 def scenario(state,changes):
  values=initial_values(state);values.update(changes)
  return lambda rom:state_case(rom,state,values,zero,STATES)
 stores_velocity=[i.address-BASE for i in decoded if i.mnemonic=='strh' and i.op_str=='r8, [r4, #0x44]']
 need(len(stores_velocity)==1,'unique upward velocity writer')
 load=stores_velocity[0]-4;opcode=word(after,load)
 need(opcode&0xFFFFF000==0xE59F8000,'actual upward literal load')
 at=load+8+(opcode&0xFFF)
 need(word(after,at)&0xFFFF==0xFD80,'actual source upward impulse')
 reject('wrong upward impulse',at,word(after,at)^1,scenario('ready',{0x2C:0x40,0xA8:0}))
 at=find('add r8, r0, #1')
 reject('packed count increment by two',at,word(after,at)^3,scenario('ready',{0x2C:0x40,0xA8:0xAAFE}))
 at=find('orr r8, r8, #1')
 reject('missing one-shot special flag',at,0xE1A08008,scenario('ready',{0x2C:0x40,8:0x4000}))
 stores=[i.address-BASE for i in decoded if i.mnemonic=='str' and i.op_str=='r8, [r4]']
 need(len(stores)==2,'two ready callback assignments')
 tick=[i.address-BASE for i in decoded if i.mnemonic=='bl' and i.op_str=='#0x8012a84']
 need(len(tick)==1,'single ready animation tick')
 at=stores[1]+4;advance=tick[0]-16
 opcode=0xEA000000|(((advance-at-8)//4)&0xFFFFFF)
 reject('extra same-update tick after relaunch',at,opcode,scenario('ready',{0x2C:0x40,0xA8:0}))
 boost=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(after[STATES['boost']-BASE:STATES['boost']-BASE+220],STATES['boost']))
 at=next(i.address-BASE for i in boost if i.mnemonic=='cmp' and i.op_str=='r8, #3')
 reject('exhaustion after two instead of three',at,word(after,at)^1,scenario('boost',{0xA8:2,0x44:1}))
 init=STATES['init']-BASE
 at=init+8
 need(word(after,at)==0xE1C48AB8,'initial packed field store')
 reject('packed field aliases one-shot flag',at,0xE1C48AB6,scenario('init',{}))
 at=HOOKS[0][1]+12
 need(word(after,at)==0xE358000D,'selector identity comparison')
 reject('wrong character selection',at,0xE358000E,lambda rom:route_cases(before,rom))
 return rejected

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('before','after','manifest','source','gba','audio-manifest','table-manifest','report'):
  p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report required')
 before,after,source,gba=(getattr(a,n).read_bytes() for n in ('before','after','source','gba'))
 need(sha(after)=='FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD','frozen reviewed candidate')
 need(sha(gba)=='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED','immutable retail input')
 for name,pin in {'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943','verify_shoot_attack_dispatch.py':'695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698','verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}.items():
  need(sha((ROOT/'tools'/name).read_bytes())==pin,'frozen independent runner/scanner '+name)
 audio_bytes=a.audio_manifest.read_bytes();table_bytes=a.table_manifest.read_bytes()
 need(sha(audio_bytes)=='AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91' and sha(table_bytes)=='4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6','prior allocation owner identities')
 manifest_bytes=a.manifest.read_bytes();manifest=json.loads(manifest_bytes)
 proof=source_contract(source,before,gba)
 ownership=structural(before,after,manifest,json.loads(audio_bytes),json.loads(table_bytes))
 states=state_cases(after);routes=route_cases(before,after);sequence=sequence_case(after);negatives=mutation_checks(after,before)
 report=dict(status='ID13_AIR_RELAUNCH_INDEPENDENT_PASS',before_sha256=sha(before),after_sha256=sha(after),
             manifest_sha256=sha(manifest_bytes),verifier_sha256=sha(Path(__file__).read_bytes()),source=proof,allocation=ownership,
             actual_ARM_state_cases=states,actual_ARM_route_cases=routes,rejected_mutations=negatives,
             actual_ARM_sequence_updates=sequence,
             horizontal_helper_executed=True,modeled_boundaries=['landing','attack','other','event setter','animation tick'],
             production_builder_imported=False,emulator_launched=False,runtime_verified=False,
             limitations=['Shared-service ABI/returns are modeled; their full game behavior is not executed by this verifier.',
                          'Per-update fixed-point lineage is checked, not hardware or wall-clock trajectory parity.',
                          'Historical E5 crash overlap and first metadata chain remain separately unproved.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
