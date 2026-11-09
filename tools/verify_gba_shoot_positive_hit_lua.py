"""Independent actual Lua54 positive-hit observer tests; no emulator launch."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys
import types

import verify_wsc_shoot_short_hard as lua_host

ROOT=Path(__file__).resolve().parents[1]
LUA_PIN='9F12E4F732607B2605CF7EA997F4D8E717B845E20A513309310057D3D257996B'
HOST_PIN='036CC0E31CB4BB3032FF9614AFA40FFADF0BADF2C8968E9575BDC239C5446E0F'

CHECK=r'''
local P,Q,AUX=0x02011710,0x02011828,0x02011940
local out,ref='W:/build/positive-independent','W:/build/healthy-reference'
local function copy(t)local n={};for k,v in pairs(t)do n[k]=v end;return n end
local function test(mode,change)
 local m={ram={},hooks={},files={},closed={},inputs={},saves={},frame=1,advances=0,bulk=0,loads=0,exits=0}
 function m.put(a,v,n)for i=0,(n or 2)-1 do m.ram[a+i]=math.floor(v/256^i)%256 end end
 function m.get(a,n)local v=0;for i=0,(n or 2)-1 do v=v+(m.ram[a+i]or 0)*256^i end;return v end
 local function actor(a,kind,index,id)
  m.put(a-0x18+0x10,2);m.put(a+4,kind);m.put(a+0x10,index,1);m.put(a+0x11,id,1);m.put(a+0x14,a,4)
 end
 actor(P,0,0,0);actor(Q,3,1,15);actor(AUX,6,2,0)
 for _,v in ipairs({{0x0300489C,P},{0x030048A0,Q},{0x03004D3C,AUX},{P+0x18,Q},{Q+0x18,P},
  {Q+0x28,AUX},{AUX+0x28,Q},{AUX+0x18,P},{Q+0xF0,0x085D0000},{Q+0xF4,0x085D1000},
  {AUX+0xF0,0x085D029C},{AUX+0xF4,0x085D1100}})do m.put(v[1],v[2],4)end
 m.put(P+0x64,4);m.put(Q+0x64,37);m.put(Q+0x68,18);m.put(Q+0x6A,9)
 m.put(P+0x34,0x0E00);m.put(Q+0x34,0x1800)
 m.put(0x03002310,7);m.put(0x0300231E,11,1);m.put(0x03004502,2);m.put(0x0300450A,6)
 for i,cb in ipairs({0x08374FF4,0x083735BC})do local h=0x02011D88+(i-1)*0x118
  m.put(h,cb,4);m.put(h+0x10,2);m.put(0x0300450C+i*4,h,4)end
 for _,raw in ipairs({0x085C0B00,0x08587100,0x08587128,0x08587150})do
  for i=0,14 do m.put(raw+8+2*i,raw%0xFFFF+i)end
 end
 m.put(0x0836EBA8,0x0836EC14,4)
 m.config={output=out,checkpoint_dir=ref,probe_sha256='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'}
 local regions={IWRAM={0x03000000,0x8000,'iwram'},EWRAM={0x02000000,0x40000,'ewram'},
  VRAM={0x06000000,0x18000,'vram'},PALRAM={0x05000000,0x400,'palette'},OAM={0x07000000,0x400,'oam'},ROM={0x08000000,0x800000,'ROM'}}
 local reference={[ref..'/healthy-activation.State']='PK\003\004fixture',
  [ref..'/healthy-activation.txt']='core=68927 input_relative=68926 stage7_consumed=true fixture'}
 for d,v in pairs(regions)do reference[ref..'/13-healthy-activation-'..v[3]..'.bin']='opaque-'..d end
 local env=setmetatable({},{__index=_G});env._G=env
 env.userdata={get=function(k)return m.config[k]end,clear=function()m.config={}end,
  set=function(k,v)m.config[k]=v end}
 local function absolute(a,n,d)local spec=assert(regions[d]);assert(a>=0 and a+n<=spec[2]);return spec[1]+a end
 env.memory=setmetatable({getmemorydomainsize=function(d)return assert(regions[d])[2]end,
  read_u8=function(a,d)return m.get(absolute(a,1,d),1)end,
  read_u16_le=function(a,d)return m.get(absolute(a,2,d),2)end,
  read_u32_le=function(a,d)return m.get(absolute(a,4,d),4)end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(not m.callback,'CPU callback bulk capture');absolute(a,n,d);m.bulk=m.bulk+1
   return mode=='bad-restore' and d=='EWRAM' and 'bad' or 'opaque-'..d
  end},{__index=function(_,k)error('unapproved memory API '..k)end})
 env.mainmemory=setmetatable({},{__index=function(_,k)error('unapproved mainmemory '..k)end})
 env.io={open=function(path,access)
  if access=='rb'then local value=reference[path]or m.files[path];if not value then return nil end
   return {read=function()return value end,close=function()end}
  end
  assert(path:find(out..'/',1,true)==1)
  if m.callback then assert(path==out..'/positive-hit-first-failure.txt','non-scalar callback IO')end
  assert(access=='wb');m.files[path]=''
  return {write=function(_,value)m.files[path]=m.files[path]..tostring(value);return true end,
   close=function()m.closed[path]=(m.closed[path]or 0)+1 end}
 end}
 env.client={screenshot=function(path)assert(not m.callback);m.files[path]='PNG'end,
  exit=function()m.exits=m.exits+1 end}
 env.savestate={load=function(path,suppress)
  assert(not m.callback and next(m.hooks)==nil and m.advances==0 and suppress==true)
  assert(path==ref..'/healthy-activation.State');m.loads=m.loads+1
  if mode=='load-false'then return false end
  m.frame=68927;m.config={output='old-output',frames=120000,boss_authorization='old-cheat'};return true
 end,save=function(path,suppress)
  assert(not m.callback and suppress==true);m.saves[#m.saves+1]=path
  if mode=='save-false' and path:find('/flash%-expired%.State$')then return false end
  m.files[path]='PK\003\004saved';return true
 end}
 m.regs={};for i=0,15 do m.regs['R'..i]=0 end
 env.event={on_bus_exec=function(fn,address,label)
  assert(m.loads==1 and m.frame==68927 and not m.hooks[address]);m.hooks[address]=fn
 end}
 function m.fire(address,r)
  for k,v in pairs(r or {})do m.regs[k]=v end;m.regs.R15=address
  m.callback=true;local ok,err=pcall(assert(m.hooks[address]),address,0,0);m.callback=false;assert(ok,err)
 end
 local function fill(raw)for i=0,14 do m.put(0x05000222+2*i,m.get(raw+8+2*i))end end
 local hit=false;local timer=0;local previous=0
 env.emu=setmetatable({getsystemid=function()return 'GBA'end,framecount=function()return m.frame end,
  getregisters=function()return copy(m.regs)end,frameadvance=function()
   assert(not m.callback);m.advances=m.advances+1;assert(m.advances<=1200,'frame ceiling');m.frame=m.frame+1
   local k=assert(m.inputs[#m.inputs]);local held=(k.A and 0x40 or 0)|(k.B and 0x80 or 0)
   m.put(0x03001302,held);m.put(0x03001306,held&(~previous));m.put(P+0x2C,held);m.put(P+0x2E,held&(~previous));previous=held
   if mode=='bad-input'then m.put(P+0x2C,held~0x40)end
   m.fire(0x08375140,{R4=P})
   if m.advances==2 then
    if mode=='legal-types' or mode=='E5' or mode=='overwrite' then
     m.put(0x030049B8,P,4)
     m.fire(0x08353C70,{R0=mode=='E5' and 0xE5 or 0x1A,R1=0x030049B8,R4=0x085D0290})
     if mode=='legal-types'then m.fire(0x08353C70,{R0=0x1B,R1=0x030049B8,R4=0x085D0290})end
     if mode=='overwrite'then m.fire(0x0836E370,{R0=0x1B,R4=0x030049B8})end
    elseif mode=='scratch'then m.put(0x03004D20,0xE5);m.fire(0x0836EB58)
    elseif mode=='dispatch'then m.fire(0x0836EBA4,{R1=36,R8=0x0836EBA8,R9=0})
    elseif mode=='death'then m.put(P+0x64,0)
    elseif mode=='root4'then m.fire(0x08373688)
    elseif mode=='owner-lost'then m.put(0x03004510,0,4)end
    if mode=='E5'then
     assert(m.files[out..'/positive-hit-first-failure.txt'] and m.closed[out..'/positive-hit-first-failure.txt']==1,'immediate closed scalar evidence before outer frame return')
     assert(not m.files[out..'/first-invalid-producer-ewram.bin'],'no bulk callback capture')
    end
   end
   if mode=='bounded' or mode=='E5' or mode=='overwrite' or mode=='scratch' or mode=='dispatch' or mode=='bad-input' then return end
   if k.B and not hit then
    m.fire(0x0836E5E4,{R4=P,R5=Q,R0=1,R8=mode=='fatal' and 0 or 36})
    m.put(Q+0x64,36);m.fire(0x0836E5E8,{R4=P,R5=Q})
    if mode~='missing-hook'then m.fire(0x0836E634,{R4=P,R5=Q})end
    m.fire(0x085CD9A0,{R4=P,R5=Q});m.put(Q+0x74,mode=='timer-bad' and 7 or 8)
    fill(0x085C0B00);for i=0,23 do m.put(0x05000000+i*0x20,0x1F)end
    if mode=='palette-bad'then m.put(0x05000222,0)end
    m.fire(0x085CDA20,{R4=P,R5=Q});hit=true;timer=8
   elseif hit and timer>0 then
    if mode=='second-hit'then m.fire(0x0836E5E4,{R4=P,R5=Q,R0=1,R8=35})end
    m.fire(0x08586C7C,{R5=Q,R8=timer-1});timer=timer-1;m.put(Q+0x74,timer)
    if timer==0 then
     m.fire(0x08587000,{R4=Q,R14=0x08586C90});fill(0x08587100)
     if mode=='expiry-palette-bad'then m.put(0x05000222,0)end
     m.fire(0x08587068,{R4=Q})
     if mode=='death-at-expiry'then m.put(P+0x64,0)end
    end
   end
  end},{__index=function(_,k)error('unapproved emu API '..k)end})
 env.joypad={set=function(keys)
  local k=copy(keys);for name,value in pairs(k)do assert(type(value)=='boolean')end
  assert(not k.Start and not k.Select and not k.Up and not k.Down and not k.R and not k.L and not k.Power)
  m.inputs[#m.inputs+1]=k
 end}
 if change then change(m,reference)end
 local ok,err=pcall(assert(load(wrapper_source,'@actual-positive-hit','t',env)))
 assert(ok,err);assert(m.exits==1 and m.loads==1)
 local last=assert(m.inputs[#m.inputs]);for _,v in pairs(last)do assert(v==false,'all supplied buttons released')end
 local marker=assert(m.files[out..'/shoot-positive-hit-done.txt'])
 if mode=='success' or mode=='legal-types'then
  assert(marker:match('^positive%-hit%-flash%-expired\nupdates=8\n$'),'positive hit+eight expiry marker')
  assert(m.advances==15,'first B at7 then eight eligible updates')
  for i=1,6 do local k=m.inputs[i];assert(k.A==(i==1)and not k.B and not k.Left and not k.Right,'initial neutral A1/release5')end
  assert(m.inputs[7].B and m.inputs[7].Right,'ordinary B80 and measured approach')
  for i=8,15 do for _,v in pairs(m.inputs[i])do assert(v==false,'release after positivehit')end end
  for _,label in ipairs({'first-positive-hit','flash-eight','flash-expired'})do assert(m.files[out..'/'..label..'.State'])end
  assert(m.config.output==out and not m.config.boss_authorization and not m.config.frames,'new userdata only after restore')
 elseif mode=='bounded'then assert(m.advances==1200 and marker:match('^failure:bounded%-no%-completion'))
 else assert(marker:match('^failure:'),'negative route cannot claim success: '..mode)end
 return m
end
test('success');test('legal-types');test('bounded')
for _,mode in ipairs({'load-false','bad-restore','bad-input','E5','overwrite','scratch','dispatch','death','root4',
 'owner-lost','fatal','missing-hook','timer-bad','palette-bad','second-hit','expiry-palette-bad','death-at-expiry','save-false'})do test(mode)end
local guards={{P-8,0},{Q-8,0},{AUX-8,0},{P+4,1},{P+0x10,1,1},{P+0x11,1,1},{P+8,0x100},
 {Q+4,1},{Q+0x10,0,1},{Q+0x11,12,1},{AUX+4,3},{P+0x14,0,4},{P+0x18,0,4},{Q+0x18,0,4},
 {Q+0x28,0,4},{AUX+0x28,0,4},{AUX+0x18,0,4},{Q+0xF0,0,4},{Q+0xF4,0,4},{AUX+0xF0,0,4},{AUX+0xF4,0,4},
 {0x03002310,9},{0x0300231E,7,1},{0x03004502,0},{0x03004529,1,1},{0x02011D88,0,4},{0x02011D98,0}}
for _,g in ipairs(guards)do local m=test('guard',function(m)m.put(g[1],g[2],g[3])end);assert(m.advances==0,'initial ownership refused before first input')end
'''

def sha(b):return hashlib.sha256(b).hexdigest().upper()

def execute(text,check=CHECK):
 fn=types.FunctionType(lua_host.lua_check.__code__,dict(lua_host.__dict__,CHECK=check),
  argdefs=lua_host.lua_check.__defaults__)
 fn(text,'','')

def preflight(host):
 code=host.read_text(encoding='utf8');prefix=code.split("\nout = root / 'build' / name",1)
 assert len(prefix)==2
 tree=ast.parse(prefix[0]);compile(code,str(host),'exec')
 forbidden={'mkdir','write_text','write_bytes','copyfile','PrivateDesktopProcess'}
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=node.func.attr if isinstance(node.func,ast.Attribute)else node.func.id if isinstance(node.func,ast.Name)else ''
   assert name not in forbidden,'preflight mutation '+name
 argv=sys.argv[:]
 try:
  sys.argv=[str(host),'bizhawk-gba-shoot-positive-hit-20261109-z']
  env={'__file__':str(host),'__name__':'__read_only_preflight__'}
  exec(compile(tree,str(host)+':read-only-prefix','exec'),env)
 finally:sys.argv=argv
 assert "splitlines()[0]"in code and "report['done_text']"in code,'host marker integration'
 return {'host_sha256':sha(host.read_bytes()),'readonly_prefix_executed':True,
  'source_core_sha256':sha(env['source_core']),'checkpoint_frame':env['parsed']['frame'],
  'paths_created':False,'process_launched':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists()
 source=ROOT/'tools/bizhawk_probe_gba_shoot_positive_hit.lua';blob=source.read_bytes();assert sha(blob)==LUA_PIN
 text=blob.decode();assert not re.search(r'\b(?:memory|mainmemory)\.write|emu\.setregister',text)
 execute(text)
 rejected=[]
 for label,old,new in (
  ('native B mask changed','keys.B and 0x80 or 0','keys.B and 0x40 or 0'),
  ('auxiliary ownership removed','and read(AUX+0x28,4)==Q','and true'),
  ('frame bound exceeded','for frame=1,1200 do','for frame=1,1201 do'),
  ('bulk capture inside callback','hit.flash=true;queue("flash-eight",r)',
   'memory.read_bytes_as_binary_string(0,0x8000,"IWRAM");hit.flash=true;queue("flash-eight",r)'),
  ('failed state export accepted','assert(savestate.save(out.."/"..name..".State",true)==true,"capture save failed")',
   'savestate.save(out.."/"..name..".State",true)')):
  assert text.count(old)==1,label+' anchor'
  try:execute(text.replace(old,new))
  except ValueError:rejected.append(label)
  else:raise AssertionError('semantic control survived '+label)
 host=ROOT/'build/run_gba_shoot_positive_hit_20261109.py';assert sha(host.read_bytes())==HOST_PIN
 host_result=preflight(host)
 report=dict(status='POSITIVE_HIT_LUA_INDEPENDENT_PASS',lua_sha256=sha(blob),verifier_sha256=sha(Path(__file__).read_bytes()),
  actual_Lua54_scenarios=48,initial_guard_cases=27,bounded_frames=1200,ordinary_success_frames=15,
  native_button_masks={'A':0x40,'B':0x80},positive_damage_and_eight_update_expiry=True,
  fault_paths=['E5','overwrite','scratch','dispatch','P1 death','root4','owner loss','fatal hit','missing hook',
   'bad timer/palette','second hit','bad expiry palette','death at expiry','save failure','load failure','RAM mismatch'],
  CPU_bulk_capture_forbidden=True,guest_write_and_register_APIs_forbidden=True,host_preflight=host_result,
  semantic_mutations_rejected=rejected,
  emulator_or_real_state_load_by_verifier=False,synthetic_payloads_not_genuine_states=True,
  actual_runtime_positive_hit_claim=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print('PASS real Lua54 success/fault/ownership routes and read-only genuine host preflight')

if __name__=='__main__':main()
