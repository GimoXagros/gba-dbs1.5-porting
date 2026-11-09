"""Independent affected terminal-observer Lua54 QA; synthetic APIs, no emulator."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types
import sys

import verify_gba_shoot_positive_hit_lua as prior
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
ROM='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
LUA='964BC4E16A722D576F3CE4BF7516A1D8495967E33847ACF65515FF35C8AB5C74'
HOST='914E6A14460DB022B9ACF63C483ABF9E6CB6AFF459EC23D9A036149A6D97C4F0'
PINS='EED7348B69043191C49BFA7BE185C40717A38718DFF50FCB1A4373129BDE5E4E'

def sha(b):return hashlib.sha256(b).hexdigest().upper()

TAIL=r'''
 m.put(P,0x0835620C,4);m.put(P+0x66,123);m.put(Q+0x62,0xA55A);m.put(Q+0x66,0x5AA5)
 m.put(Q+0x34,m.get(P+0x34)+150);m.put(Q+0x36,200);m.put(Q+0xBA,1)
 m.writes={}
 env.memory.write_u16_le=function(offset,value,domain)
  assert(not m.callback and domain=='EWRAM' and offset==Q-0x02000000+0x64 and value==1,'only authorized16bitbossHPwrite')
  assert(m.advances==1 and m.get(P+0xB4)&0x4000~=0 and m.get(P+0x2C)&0x80==0,'latefreshBwriteafterturn')
  assert(#m.writes==0 and m.get(Q+0x64)==37,'single37to1attempt')
  local ledger=assert(m.files[out..'/terminal-write-ledger.txt']);assert(ledger:find('attempt_consumed=true',1,true)and ledger:find('verified=false',1,true)and m.closed[out..'/terminal-write-ledger.txt'],'ledger closed beforewrite')
  m.writes[#m.writes+1]={offset=offset,value=value,domain=domain}
  if mode=='write-throw'then error('deliberate write failure')end
  if mode~='write-false'then m.put(Q+0x64,1)end
  if mode=='neighbor-corrupt'then m.put(Q+0x66,0)end
 end
 local H=0x02010000+30*0x118;local D=H+0x118
 local fired=false;local previous=0
 local function phase(a)if mode~='missing-phase-'..string.format('%X',a)then m.fire(a,{R4=H+0x18})end end
 local function tail()
  -- Native game mutations below are fixture state changes, never observer writes.
  m.put(P+0x64,1);m.put(0x02011D88,0x08374FAC,4);m.put(0x02011EA0,0x0837354C,4)
  for _,a in ipairs({0x085CD0A0,0x085CD120,0x085CD2B0,0x085CD340,0x085CD3A0,0x085CD420,0x085CD4B0,0x085CD510,0x085CD550,0x085CD5E0,0x085CD640,0x085CD6A0,0x085CD710,0x085CD740})do phase(a)end
  m.put(Q,0x085BF200,4);m.put(AUX,0x085BF600,4)
  if mode~='missing-upper'then m.fire(0x085BF200,{R4=Q})end
  if mode~='missing-aux'then m.fire(0x085BF600,{R4=AUX})end
  m.put(P,0x0835620C,4);m.put(P+0x2C,0);m.put(P+0x2E,0);m.put(P+0x34,1000);m.put(P+0x36,1000);m.put(P+0x38,1000);m.put(P+0x3A,1000)
  for _,r in ipairs({{P,0x080D45B8,0x080D7A58,0},{Q,0x085D0000,0x085D1000,1},{AUX,0x085D029C,0x085D1100,0}})do m.put(r[1]+0xF0,r[2],4);m.put(r[1]+0xF4,r[3],4);m.put(r[1]+0xBA,r[4])end
  m.put(0x0300482A,1);m.put(0x03004830,P+0xAC,4);m.put(0x0400000A,0x1E00);m.put(0x03004712,50)
  m.put(D,0x08352268,4);m.put(D+4,0xFFFFF000,4);m.put(D+0x10,2)
  m.put(0x0300133C,D,4);m.put(0x03001344,D,4);m.put(0x03004518,D,4)
  m.put(0x03004574,1,4);m.put(0x03004578,0x08587200,4);m.put(0x0300450A,0x406)
  -- Actual initial/fatal link FIRST is preserved in this independent refusal route.
  if mode~='actual-aux-FIRST'then m.put(AUX+0x18,Q,4)end
  m.fire(0x086FF9C0)
  if mode=='actual-aux-FIRST'then
   local found=false;for _,s in pairs(m.files)do if s:find('native-guard-aux18-not-upper',1,true)then found=true end end
   -- Logs flush only after frame return, checked in final assertions.
  else
   if mode~='missing-selection'then m.fire(0x086FF6A8,{R0=0x03004574,R1=0x086FF6B4})end
   m.fire(0x086FF6E8,{R0=0x086FFE10});m.put(0x030012E0,0x086FFE10,4)
   m.fire(0x086FFE10)
   for i,o in ipairs({0,2,4,7,10,13,17,21})do
    local line=(m.get(0x03004714,1)+o)&255
    m.put(0x03004716,i-1);m.fire(0x086FFE48,{R4=0x03004710,R5=i-1,R6=o,R1=line})
    if not(mode=='missing-IRQ-match'and i==4)then m.fire(0x086FFE50,{R0=mode=='mismatched-IRQ-line'and line+1 or line,R1=line})end
    m.put(0x03004714,m.get(0x03004714)+1);m.put(0x03004716,i)
    if mode=='bad-IRQ-counter'then m.put(0x03004714,m.get(0x03004714)+1)end
    m.fire(0x086FFE74,{R5=i})
   end
   m.put(0x03004716,8);m.fire(0x086FFE84,{R0=0x030012E0,R1=0x086FFEBC});m.put(0x030012E0,0x086FFEBC,4)
   if mode~='missing-final-IRQ'then m.fire(0x086FFEBC)end
   if mode~='missing-next-scroll'then
    m.put(0x0300456E,5,1);m.fire(0x085E7434,{R5=0x0300456C});m.put(0x030012B8,5,1)
    m.put(0x04000014,mode=='bad-scroll-store'and 0 or 0xFFFD);m.fire(0x085E743C)
   end
  end
  m.put(0x0300133C,H,4)
  if mode~='missing-cleanup-entry'then m.fire(0x08340C54)end
  m.put(H+0x10,0);m.put(0x03002314,1);m.put(0x03002316,0);m.put(0x03002318,0);m.put(0x0300475E,1,1)
  if mode=='bad-triplet'then m.put(0x03002316,1)end
  if mode=='cleanup-already-mode8'then m.put(0x03002310,8)end
  m.fire(0x08340CA8)
 end
 env.emu=setmetatable({getsystemid=function()return 'GBA'end,framecount=function()return m.frame end,getregisters=function()return copy(m.regs)end,
  frameadvance=function()
   assert(not m.callback);m.advances=m.advances+1;assert(m.advances<=3000,'finite3000bound');m.frame=m.frame+1
   local k=assert(m.inputs[#m.inputs]);local held=(k.B and 0x80 or 0)|(k.Right and 2 or 0)
   m.put(0x03001302,held);m.put(0x03001306,held&(~previous));m.put(P+0x2C,held);m.put(P+0x2E,held&(~previous));previous=held
   m.fire(0x08375140,{R4=P})
   if mode=='legal-types'and m.advances==1 then
    m.put(0x030049B8,P,4);m.fire(0x08353C70,{R0=0x1A,R1=0x030049B8,R4=0x085D0290})
    m.fire(0x08353C70,{R0=0x1B,R1=0x030049B8,R4=0x085D0290})
   end
   if mode=='E5'and m.advances==1 then
    m.put(0x030049B8,P,4);m.fire(0x08353C70,{R0=0xE5,R1=0x030049B8,R4=0x085D0290})
    assert(m.files[out..'/terminal-first-failure.txt'] and m.closed[out..'/terminal-first-failure.txt']==1,'closed scalar evidence beforeframe return')
    assert(not m.files[out..'/02-invalid-producer-ewram.bin'],'no bulk callback capture');return
   end
   if mode=='negative-dispatch'and m.advances==1 then
    m.put(0x0836EB88,0x0836EC14,4);m.fire(0x0836EBA4,{R1=-16,R8=0x0836EBA8,R9=0x0836EC14});return
   end
   if mode=='death'and m.advances==1 then m.put(P+0x64,0);return end
   if mode=='root4'and m.advances==1 then m.fire(0x08373688);return end
   if mode=='bounded' or mode=='E5' or mode=='negative-dispatch'then return end
   if m.advances==1 then m.put(P+0xB4,0x4000)end
   if k.B and not fired then
    local after=mode=='negative-lethal' and 0xFFFF or 0;local damage=after==0 and 1 or 2
    m.fire(0x0836E5E4,{R4=P,R5=Q,R0=damage,R8=after});m.put(Q+0x64,mode=='bad-store'and 1 or after);m.fire(0x0836E5E8,{R4=P,R5=Q})
    m.fire(0x0836E5EC,{R4=P,R5=Q});m.fire(0x085CD960,{R4=P,R5=Q})
    m.put(Q,0x085BDD00,4);m.put(AUX,0x085BF204,4)
    if mode~='missing-fatal-pair'then m.fire(0x0836E604,{R4=P,R5=mode=='bad-fatal-aux'and Q or AUX,R0=Q})end
    m.fire(0x083736B0,{R4=P});m.fire(0x0833FD08,{R8=mode=='bad-case5'and 0 or 0x086FC300})
    m.put(H,0x085CD000,4);m.put(H+4,0xFF0,4);m.put(H+0x10,2);m.put(0x0300133C,H,4)
    m.fire(0x085CD000,{R4=H+0x18});fired=true
   elseif fired and m.advances==3 then tail()
   elseif fired and m.advances>=4 and mode~='no-mode8'then m.put(0x03002310,8)end
  end},{__index=function(_,k)error('unapproved emu API '..k)end})
 env.joypad={set=function(keys)
  local k=copy(keys);for name,value in pairs(k)do assert(type(value)=='boolean')end
  for _,name in ipairs({'A','Left','Up','Down','Start','Select','L','R','Power'})do assert(k[name]==false,'onlyordinaryRight/B')end
  m.inputs[#m.inputs+1]=k
 end}
 if mode=='bad-token'then m.config.boss_authorization='not-approved'end
 if change then change(m,reference)end
 local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))
 if mode=='bad-token'then assert(not ok and #m.writes==0 and m.loads==0);return m end
 assert(ok,err);assert(m.exits==1 and m.loads==1)
 local final=assert(m.inputs[#m.inputs]);for _,v in pairs(final)do assert(v==false,'finalreleased')end
 local marker=assert(m.files[out..'/shoot-terminal-done.txt'])
 if mode=='success' or mode=='negative-lethal' or mode=='legal-types'then
  assert(marker=='native-terminal-mode8\n','allrequiredsyntheticphasechain');assert(m.advances==4)
  assert(#m.writes==1 and m.get(P+0x64)==1 and m.get(P+0x66)==123,'nativeP1HP1allowed scoreuntouched')
  assert(m.inputs[1].Right and m.inputs[2].B and not m.inputs[2].Right)
  for i=3,#m.inputs do assert(not m.inputs[i].B and not m.inputs[i].Right)end
 elseif mode=='guard'then assert(marker:match('^failure:') and #m.writes==0 and m.advances==0)
 else assert(marker:match('^failure:'),'negativecannotclaimsuccess:'..mode)end
 if mode=='actual-aux-FIRST'then assert(m.files[out..'/terminal-trace.txt']:find('native-guard-aux18-not-upper',1,true),'actualFIRSTlinkrefusallogged')end
 if mode=='write-throw' or mode=='write-false' or mode=='neighbor-corrupt'then assert(#m.writes==1 and m.advances==1,'failedattemptnotrearmed')end
 if mode=='bounded' or mode=='no-mode8'then assert(m.advances==3000,'budgetexact')end
 if mode=='bounded'then assert(#m.writes==0,'noeligibleBnowrite')end
 assert(#m.writes<=1,'globaloneshot')
 return m
end
'''

def harness():
 text=prior.CHECK.split(' local hit=false;local timer=0;local previous=0',1)[0]
 text=text.replace("probe_sha256='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'",f"probe_sha256='{ROM}',boss_authorization='user-approved-development-boss-once-per-stage'")
 text=text.replace("local spec=assert(regions[d]);", "if d=='System Bus'then return a end;local spec=assert(regions[d]);")
 text=text.replace("return mode=='bad-restore'", "if d=='System Bus'then return 'opaque-System Bus'end;return mode=='bad-restore'")
 text=text.replace("path==out..'/positive-hit-first-failure.txt'","path==out..'/terminal-first-failure.txt'")
 text=text.replace("assert(access=='wb');m.files[path]=''", "assert(access=='wb' or access=='a');if access=='wb'then m.files[path]=''else m.files[path]=m.files[path]or ''end")
 text=text.replace("path:find('/flash%-expired%.State$')", "path:find('native%-mode8%.State$')")
 return text+TAIL

def execute(source,tests):
 code=harness()+tests
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__)
 fn(source,'','')

def preflight():
 path=ROOT/'build/run_gba_shoot_terminal_20261109.py';blob=path.read_bytes();assert sha(blob)==HOST
 pins=ROOT/'build/gba-shoot-terminal-pins-20261109.json';assert sha(pins.read_bytes())==PINS
 code=blob.decode();prefix=code.split("\nout = root / 'build' / name",1);assert len(prefix)==2
 tree=ast.parse(prefix[0]);compile(code,str(path),'exec')
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=node.func.attr if isinstance(node.func,ast.Attribute)else node.func.id if isinstance(node.func,ast.Name)else ''
   assert name not in {'mkdir','write_text','write_bytes','copyfile','PrivateDesktopProcess'},'preflightmutation'
 argv=sys.argv[:]
 try:
  sys.argv=[str(path),'bizhawk-gba-shoot-terminal-20261109-z'];env={'__file__':str(path),'__name__':'__read_only_preflight__'}
  exec(compile(tree,str(path)+':readonlyprefix','exec'),env)
 finally:sys.argv=argv
 old=(ROOT/'build/run_gba_shoot_positive_hit_aim_20261109.py').read_bytes();assert sha(old)=='50A7CDA6B589EA2FF80B0F613C118934D82CAE597980B14CA4A3EE9DAB1E31C9'
 ledger=code[code.index("ledger_path = out / 'terminal-write-ledger.txt'"):code.index("report['loaded_rom_exact']")]
 restored=code.replace(ledger,'').replace("assert report['authorized_write_verified']\n",'')
 restored=restored.replace("{'tools/bizhawk_probe_gba_shoot_terminal.lua',","{'tools/bizhawk_probe_gba_shoot_positive_hit_aim.lua', 'tools/bizhawk_probe_gba_shoot_positive_hit.lua',")
 for new,oldtext in (
  ('bizhawk-gba-shoot-terminal-20261109','bizhawk-gba-shoot-positive-hit-aim-20261109'),
  ('gba-shoot-terminal-pins-20261109','gba-shoot-positive-hit-aim-pins-20261109'),
  ('bizhawk_probe_gba_shoot_terminal.lua','bizhawk_probe_gba_shoot_positive_hit_aim.lua'),
  (" + ';boss_authorization:user-approved-development-boss-once-per-stage'",''),
  ("guest_writes_expected=[dict(actor='02011828', address='0201188C', bytes=2, before=37, after=1, count=1)]","guest_writes=[]"),
  ('genuine-healthy-Shoot-authorized-HP1-real-lethal-hit-and-native-terminal','genuine-healthy-Shoot-ordinary-aim-positive-hit-and-flash-expiry'),
  ('shoot-terminal-done.txt','shoot-positive-hit-done.txt'),('time.monotonic() + 180','time.monotonic() + 120'),
  ("report['outcome'] == 'native-terminal-mode8'","report['outcome'] == 'positive-hit-flash-expired'")):
  assert new in restored,new;restored=restored.replace(new,oldtext)
 assert restored==old.decode(),'onlyreviewedterminalhostdeltas'
 block=ledger[ledger.index("report['authorized_write_verified'] = False"):]
 template=dict(actor='02011828',address='0201188C',bytes='2',before='37',requested='1',after='1',P1HP='4',attempt_consumed='true',verified='true')
 def evaluate(values):
  report={'guest_write_ledger':None if values is None else ' '.join(k+'='+v for k,v in values.items())}
  exec(compile(block,'ledger-verification','exec'),{'report':report,'prior':env['prior']})
  return report['authorized_write_verified']
 assert evaluate(template)and not evaluate(None)
 for key in template:assert not evaluate(dict(template,**{key:'incorrect'})),key
 return dict(host_sha256=HOST,pin_file_sha256=PINS,readonly_prefix_executed=True,checkpoint_frame=env['parsed']['frame'],source_core_sha256=sha(env['source_core']),exact_parent_delta_only=True,ledger_cases=11,paths_created=False,process_launched=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 source=(ROOT/'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes();text=source.decode()
 assert sha(source)==LUA
 assert text.count('memory.write_')==1 and text.count('memory.write_u16_le(')==1 and 'emu.setregister'not in text and 'mainmemory.write'not in text
 tests="\n".join("test('"+x+"')"for x in ('success','negative-lethal','legal-types','actual-aux-FIRST','bad-token','write-throw','write-false','neighbor-corrupt','E5','negative-dispatch','death','root4','bounded','no-mode8','bad-store','bad-fatal-aux','missing-fatal-pair','bad-case5','missing-upper','missing-aux','missing-selection','missing-final-IRQ','missing-next-scroll','missing-cleanup-entry','bad-triplet','cleanup-already-mode8','missing-phase-85CD510','save-false','missing-IRQ-match','mismatched-IRQ-line','bad-IRQ-counter','bad-scroll-store'))
 execute(text,tests)
 guards="\n".join(f"test('guard',function(m)m.put({address},{value},{size})end)"for address,value,size in((0x03002310,8,2),(0x0300231E,7,1),(0x03004502,0,2),(0x03004529,1,1),(0x02011710+0x64,0,2),(0x02011828+0x64,36,2),(0x02011828+0x28,0,4),(0x02011940+0x18,0,4),(0x02011940+0x28,0,4),(0x02011D88,0,4),(0x02011D98,0,2)))
 execute(text,guards)
 mutations=(
  ('approvalmissing','assert(args.boss_authorization=="user-approved-development-boss-once-per-stage","explicit one-shot boss approval required")','-- removed approval'),
  ('wrongwritewidth','memory.write_u16_le(','memory.write_u32_le('),
  ('neighboromitted','and w(Q+0x66)==right','and true'),
  ('attemptnotconsumed',' consumed=true',' -- consumed omitted'),
  ('earlyHPwrite','if keys.B and not consumed then authorize_hp1()end','if not consumed then authorize_hp1()end'),
  ('phaseomitted','required=required and phases[a]','required=required'),
  ('IRQcounteromitted','and w(0x03004714)==(irq_pending.counter+1)&0xFFFF','and true'),
  ('scrollhardwareomitted','and w(0x04000014)==(scroll_pending-8)&0xFFFF','and true'),
  ('cleanuptripletomitted','and w(0x03002316)==0','and true'),
  ('callbackbulkcapture','fatal=need(r.R4==P','memory.read_bytes_as_binary_string(0,0x8000,"IWRAM");fatal=need(r.R4==P'),
  ('falsesaveaccepted','assert(savestate.save(out.."/"..name..".State",true)==true,"capture save failed")','savestate.save(out.."/"..name..".State",true)'),
 )
 rejected=[]
 for label,old,new in mutations:
  assert text.count(old)==1,(label,'anchor')
  try:execute(text.replace(old,new),tests)
  except ValueError:rejected.append(label)
  else:raise AssertionError('semanticcontrolsurvived:'+label)
 report=dict(status='TERMINAL_LUA_AFFECTED_QA_PASS',lua_sha256=sha(source),verifier_sha256=sha(Path(__file__).read_bytes()),actual_Lua54_scenarios=43,initial_guard_cases=11,semantic_controls_rejected=rejected,host_preflight=preflight(),synthetic_phase_success_not_runtime_proof=True,actual_initial_aux_FIRST_refuses_unmodified_native_guard=True,sole_external_guest_write='one16bitSECOND+64:37to1atfirstfreshB',bounded_frames=3000,emulator_launched=False,real_savestate_loaded=False,old_full_suite_rerun=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS actualLua54 affected terminalphases/onewrite/negativeguards')

if __name__=='__main__':main()
