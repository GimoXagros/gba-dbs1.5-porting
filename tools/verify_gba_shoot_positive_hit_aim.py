"""Independent affected-policy Lua54/host delta QA; no old48-scenario rerun."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import types

import verify_gba_shoot_positive_hit_lua as previous
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
OLD='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
NEW='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
WRAPPER='00D1579B828E14AA55EEACE35A17E5BD9B203E74B0C950B34018794A8D783938'
HOST='50A7CDA6B589EA2FF80B0F613C118934D82CAE597980B14CA4A3EE9DAB1E31C9'
OLD_POLICY='''   -- Neutral jump, followed by repeated separate attack edges; no Up/Down variants.
   keys.A=(frame-1)%60==0;keys.B=frame>=7 and (frame-7)%12==0
   local dx=signed(w(Q+0x34))-signed(w(P+0x34))
   if frame>6 and math.abs(dx)>0x180 then keys.Right=dx>0;keys.Left=dx<0 end'''
POLICY='''   -- Orient while grounded and free, then one B edge at the observed crossing.
   local cb=read(P,4)
   local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(P+6)&1==0 and w(P+0x76)==0
   if ready then
    if w(P+0xB4)&0x4000==0 then keys.Right=true
    else
     local dx=signed(w(Q+0x34))-signed(w(P+0x34))
     local dy=signed(w(Q+0x36))-signed(w(P+0x36))
     local ev=w(Q+0xBA)
     keys.B=w(P+0x2C)&0x80==0 and (ev==1 or ev==4 or ev==5) and dx>=96 and dx<=384 and dy>=128 and dy<=256
    end
   end'''

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def quote(blob):return '"'+''.join('\\'+f'{x:03d}'for x in blob)+'"'
def execute(wrapper,original,expected,check):
 code='hard_source='+quote(original)+chr(10)+'assert(#hard_source=='+str(len(original))+')'+chr(10)+check
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__)
 fn(wrapper,original.decode(),expected)

def actual_composition(wrapper,original,expected):
 prefix=previous.CHECK.split("test('success');test('legal-types');test('bounded')",1)[0]
 replacements=[("probe_sha256='"+OLD+"'","probe_sha256='"+NEW+"'"),
  (' env.io={open=function(path,access)',' reference["W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua"]=hard_source'+chr(10)+' env.io={open=function(path,access)'),
  ("   if k.B and not hit then", '''   if m.advances==1 then m.put(P+0xB4,0x4000);m.put(P,0x083562B4,4)end
   if m.advances==2 then m.put(P,0x083587F0,4)end
   if m.advances==5 then m.put(P,0x083562E4,4)end
   if k.B and not hit and m.advances>=6 then''')]
 for a,b in replacements:assert prefix.count(a)==1,a;prefix=prefix.replace(a,b)
 start=prefix.index("  assert(m.advances==15,'first B at7 then eight eligible updates')")
 end=prefix.index("  for _,label in ipairs",start)
 prefix=prefix[:start]+'''  assert(m.advances==14,'recovery-gated second B at6, then8 updates')
  assert(m.inputs[1].Right and not m.inputs[1].B and not m.inputs[1].A,'turn while free')
  assert(m.inputs[2].B and not m.inputs[2].Right,'single B after actual facing flag')
  for i=3,5 do for _,v in pairs(m.inputs[i])do assert(v==false,'release through attack/recovery')end end
  assert(m.inputs[6].B,'retrigger only after ready callback returns')
  for i=7,14 do for _,v in pairs(m.inputs[i])do assert(v==false,'release after confirmed positivehit')end end
'''+prefix[end:]
 anchor=" local ok,err=pcall(assert(load(wrapper_source,'@actual-positive-hit','t',env)))"
 assert prefix.count(anchor)==1
 prefix=prefix.replace(anchor,''' m.put(P,0x0835620C,4);m.put(P+0xB4,0)
 m.put(Q+0x34,m.get(P+0x34)+150);m.put(Q+0x36,m.get(P+0x36)+200);m.put(Q+0xBA,1)
 local actual_load=load;local loads=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and kind=='t' and scope==env,'entire generated observer equals normalized9F12+exact2changes')
  loads=loads+1;return actual_load(text,name,kind,scope)
 end
'''+anchor+chr(10)+" assert(loads==1,'single generated observer load')")
 execute(wrapper,original,expected,prefix+chr(10)+"test('success');test('E5');test('save-false')"+chr(10))

MATRIX=r'''
local P,Q=0x02011710,0x02011828
local source='return function(mem) local keys={A=false,B=false,Left=false,Right=false,Up=false,Down=false,L=false,R=false,Start=false,Select=false}; local P,Q=0x02011710,0x02011828; local function read(a,n)return mem[a]or 0 end;local function w(a)return mem[a]or 0 end;local function signed(v)return v>=0x8000 and v-0x10000 or v end;'..string.char(10)..collect_source..string.char(10)..'return keys end'
local choose=assert(load(source,'@actual-policy','t',_G))()
local count=0
for _,cb in ipairs({0x0835620C,0x083562B4,0x083562E4,0x083587F0,0})do
for _,air in ipairs({0,1})do for _,freeze in ipairs({0,1})do for _,face in ipairs({0,0x4000})do
for _,held in ipairs({0,0x80})do for _,ev in ipairs({0,1,3,4,5,6})do
for _,dx in ipairs({-96,95,96,384,385})do for _,dy in ipairs({127,128,256,257})do
 local mem={[P]=cb,[P+6]=air,[P+0x76]=freeze,[P+0xB4]=face,[P+0x2C]=held,
  [P+0x34]=1000,[P+0x36]=1000,[Q+0x34]=1000+dx,[Q+0x36]=1000+dy,[Q+0xBA]=ev}
 local k=choose(mem);local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4)and air==0 and freeze==0
 local right=ready and face==0
 local attack=ready and face~=0 and held==0 and(ev==1 or ev==4 or ev==5)and dx>=96 and dx<=384 and dy>=128 and dy<=256
 assert(k.Right==right and k.B==attack,'independent ready/facing/edge/window truth table')
 for _,n in ipairs({'A','Left','Up','Down','L','R','Start','Select'})do assert(k[n]==false,'no unrequested control')end
 assert(not(k.Right and k.B),'turn then attack, no simultaneous hold');count=count+1
end end end end end end end end
assert(count==9600)
local mem={[P]=0x0835620C,[P+6]=0,[P+0x76]=0,[P+0xB4]=0x4000,[P+0x2C]=0,
 [P+0x34]=1000,[P+0x36]=1000,[Q+0x34]=1150,[Q+0x36]=1200,[Q+0xBA]=1}
assert(choose(mem).B);mem[P+0x2C]=0x80;assert(not choose(mem).B,'prior B held cannot repeat')
mem[P]=0x083587F0;mem[P+0x2C]=0;assert(not choose(mem).B,'release through full attack')
mem[P]=0x083562E4;mem[P+0x76]=1;assert(not choose(mem).B,'freeze blocks recovery trigger')
mem[P+0x76]=0;assert(choose(mem).B,'new edge after later ready recovery')
'''

def matrix(original,policy):execute('',original,policy,MATRIX)

def capture_generated(wrapper,original,expected):
 check=r'''
local calls=0;local env=setmetatable({},{__index=_G})
env.userdata={get=function()return 'NEW' end}
env.io={open=function()return{read=function()return hard_source end,close=function()end}end}
env.load=function(text,name,mode,scope)
 assert(text==collect_source and scope==env and mode=='t','exact normalized generated text')
 assert(load(text,name,mode,scope));calls=calls+1;return function()end
end
assert(load(wrapper_source,'@actual-EOL-wrapper','t',env))();assert(calls==1)
'''.replace('NEW',NEW)
 execute(wrapper,original,expected,check)

def wrapper_anchor_controls(wrapper,original):
 # Execute the wrapper on raw CRLF inputs; successful payload compilation is deliberately intercepted.
 check=r'''
local new='NEW'
local old_policy=[====[OLDPOLICY]====]
for _,mode in ipairs({'missing-rom','duplicate-rom','missing-policy','duplicate-policy'})do
 local raw=hard_source
 if mode=='missing-rom'then raw=raw:gsub('OLD',new)end
 if mode=='duplicate-rom'then raw=raw..'\r\n-- OLD'end
 if mode=='missing-policy'then raw=raw:gsub('Neutral jump','Changed comment')end
 if mode=='duplicate-policy'then raw=raw..'\r\n'..old_policy:gsub('\n','\r\n')end
 local loads=0;local env=setmetatable({},{__index=_G})
 env.userdata={get=function()return new end}
 env.io={open=function()return{read=function()return raw end,close=function()end}end}
 env.load=function()loads=loads+1;return function()end end
 assert(not pcall(assert(load(wrapper_source,'@actual-wrapper-refusal','t',env))),'nonunique literal refused')
 assert(loads==0,'refusal before payload execution')
end
'''.replace('OLDPOLICY',OLD_POLICY).replace('NEW',NEW).replace('OLD',OLD)
 execute(wrapper,original,'',check)

def host_checks():
 path=ROOT/'build/run_gba_shoot_positive_hit_aim_20261109.py'
 old=ROOT/'build/run_gba_shoot_positive_hit_rect_20261109.py'
 assert sha(path.read_bytes())==HOST and sha(old.read_bytes())=='03CAD24CCD2FCB46C5DBC5DF6F2E37BF577B1C7CEF4B91F3F5D4C49F2E6AF434'
 text=old.read_text()
 for a,b,count in(('bizhawk-gba-shoot-positive-hit-rect-20261109-','bizhawk-gba-shoot-positive-hit-aim-20261109-',1),
  ('gba-shoot-positive-hit-rect-pins-20261109.json','gba-shoot-positive-hit-aim-pins-20261109.json',1),
  ('bizhawk_probe_gba_shoot_positive_hit_rect.lua','bizhawk_probe_gba_shoot_positive_hit_aim.lua',2),
  ('genuine-healthy-Shoot-child-rectangle-repair-positive-hit-and-flash-expiry','genuine-healthy-Shoot-ordinary-aim-positive-hit-and-flash-expiry',1)):
  assert text.count(a)==count;text=text.replace(a,b)
 assert text==path.read_text(),'all other host logic unchanged'
 source=inspect.getsource(previous.preflight)
 source=source.replace("'bizhawk-gba-shoot-positive-hit-20261109-z'","'bizhawk-gba-shoot-positive-hit-aim-20261109-z'")
 namespace=dict(previous.__dict__);exec(compile(source,'@aim-run-name-only-preflight','exec'),namespace)
 return namespace['preflight'](path)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 wrapper_path=ROOT/'tools/bizhawk_probe_gba_shoot_positive_hit_aim.lua';original_path=ROOT/'tools/bizhawk_probe_gba_shoot_positive_hit.lua'
 wb,ob=wrapper_path.read_bytes(),original_path.read_bytes();assert sha(wb)==WRAPPER and sha(ob)==previous.LUA_PIN
 raw=ob.decode();normalized=raw.replace(chr(13)+chr(10),chr(10))
 assert normalized.count(OLD)==normalized.count(OLD_POLICY)==1
 effective=normalized.replace(OLD,NEW).replace(OLD_POLICY,POLICY)
 assert sha(effective.encode())=='02D6B04C6072B53C15067E9C6A3235B9B04079635E994C38222642807E2754F6'
 wrapper=wb.decode();actual_composition(wrapper,ob,effective);wrapper_anchor_controls(wrapper,ob);matrix(ob,POLICY)
 crlf=normalized.replace(chr(10),chr(13)+chr(10)).encode();capture_generated(wrapper,crlf,effective)
 negatives=[]
 for name,x,y in(('airborne gate removed','and w(P+6)&1==0',''),('freeze gate removed','and w(P+0x76)==0',''),
  ('held B edge gate removed','w(P+0x2C)&0x80==0 and ',' '),('facing flag inverted','w(P+0xB4)&0x4000==0','w(P+0xB4)&0x4000~=0'),
  ('X lower boundary widened','dx>=96','dx>=95'),('Y upper boundary widened','dy<=256','dy<=257')):
  assert POLICY.count(x)==1
  try:matrix(ob,POLICY.replace(x,y))
  except ValueError:negatives.append(name)
  else:raise AssertionError('semantic policy mutation survived '+name)
 line='source=source:gsub('+json.dumps(chr(13)+chr(10))+','+json.dumps(chr(10))+') -- Lua long-string anchors use normalized line endings.'+chr(10)
 assert wrapper.count(line)==1
 try:capture_generated(wrapper.replace(line,''),crlf,effective)
 except ValueError:negatives.append('CRLF normalization removed')
 else:raise AssertionError('raw CRLF anchor mutation survived')
 preflight=host_checks();assert sha(original_path.read_bytes())==previous.LUA_PIN and sha(wrapper_path.read_bytes())==WRAPPER
 report=dict(status='AIM_POLICY_WRAPPER_DELTA_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),
  wrapper_sha256=WRAPPER,effective_source_sha256=sha(effective.encode()),original9F12_unchanged=True,
  normalized_source_exactly_ROM_and_policy_substitutions=True,actual_file_LF_count=ob.count(bytes([10])),
  actual_file_CRLF_count=ob.count(bytes([13,10])),synthetic_CRLF_wrapper_execution=True,
  policy_matrix_cases=9600,actual_full_observer_routes=['orient/attack/recover/positivehit/eightupdateexpiry','immediateE5 scalar+outer capture','expiry save failure'],
  anchor_refusals=4,semantic_mutations_rejected=negatives,host_delta_groups=4,host_readonly_preflight=preflight,
  old48_scenarios_rerun=False,guest_write_APIs_added=False,no_A_Left_Up_Down=True,
  emulator_or_actual_state_load=False,aim_physics_or_runtime_hit_proved=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print('PASS9600 policy states;3 affected fullLua routes;4 anchors;7 controls;read-only host prefix')

if __name__=='__main__':main()
