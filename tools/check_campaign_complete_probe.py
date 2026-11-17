"""Independent composed Lua check using the actual frozen driver and observer."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import types
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
ROM='933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
WRAPPER='F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF'
PINS={
 'bizhawk_probe_gba_shoot_entry.lua':'D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D',
 'bizhawk_gba_shoot_entry_observer.lua':'7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59',
 'bizhawk_probe_gba_collision.lua':'7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9'}

def sha(raw):return hashlib.sha256(raw).hexdigest().upper()
def quote(raw):return '"'+''.join(f'\\{b:03d}' for b in raw)+'"'

CHECK=r'''
local cases={'complete','gap','wrong-row','wrong-CPU','bad-HUD','missing-HUD','missing-active',
 'bad-active-CPU','early-activation','retained-type-failure','typed-refusal','bounded','missing-authorization','wrong-ROM'}
local first={8,1,9,6,10}
local rows={{5,0,3,2,4},{0,3,2,4,5},{3,2,4,5,0},{2,4,5,0,3},{4,5,0,3,2},{5,0,3,2,4},{0,3,2,4,5},{2,4,5,0,3}}
local cpus={0,1,2,5,6,4,3,15,13,14,11}
for _,case in ipairs(cases)do
 local frame,inside_hook,exited=100,false,false
 local hooks,files,closed,memory_bytes,writes,saves,input_calls={},{},{},{},{},{},{}
 local captures=0
 local regs={};for i=0,15 do regs['R'..i]=0 end
 local p,q,aux,owner=0x02010018,0x02010130,0x02010248,0x02010590
 local function put(a,v,n)for i=0,n-1 do memory_bytes[a+i]=(v>>(8*i))&255 end end
 local function get(a,n)local v=0;for i=0,n-1 do v=v|((memory_bytes[a+i]or 0)<<(8*i))end;return v end
 for _,block in ipairs(romblocks)do for i=1,#block.data do memory_bytes[block.at+i-1]=block.data:byte(i)end end
 put(0x08FFFFFF,0xA5,1)
 local function active(body,yes)put(body-0x18+0x10,yes and 2 or 0,2)end
 local function initial_pair()
  for _,body in ipairs({p,q,aux})do active(body,true)end
  put(p+4,0,2);put(q+4,1,2);put(p+0x10,0,1);put(q+0x10,1,1);put(p+0x11,0,1)
  put(p+0x14,p,4);put(q+0x14,q,4);put(p+0x18,q,4);put(q+0x18,p,4)
  put(p+0x64,100,2);put(p+0x66,0,2);put(q+0x64,200,2)
  put(0x0300489C,p,4);put(0x030048A0,q,4);put(0x03004D3C,aux,4)
  local input,battle=0x02010348,0x02010460
  put(input+0x10,2,2);put(input,0x08374FF4,4);put(battle+0x10,2,2);put(battle,0x083735BC,4)
  put(0x03004510,input,4);put(0x03004514,battle,4)
 end
 local function boss(stage)
  put(q+4,3,2);put(q+0x11,15,1);put(q+0x28,aux,4);put(aux+0x28,q,4);put(aux+0x18,p,4)
  put(aux+4,stage==7 and 3 or 6,2)
  put(q+0xF0,stage==7 and 0x0834DFE0 or 0x085D0000,4)
  put(q+0xF4,stage==7 and 0x0834E27C or 0x085D1000,4)
  put(aux+0xF0,stage==7 and 0x08341C00 or 0x085D029C,4)
  put(aux+0xF4,stage==7 and 0x08341E70 or 0x085D1100,4)
 end
 local function state(progress)
  initial_pair()
  local stage=progress<5 and first[progress+1]or progress<10 and rows[4][progress-4]or 7
  put(0x03002310,7,2);put(0x0300231A,0,1);put(0x0300231B,0,1);put(0x0300231F,2,1)
  put(0x0300232E,progress,1);put(0x0300232F,3,1);put(0x0300231E,stage,1)
  put(0x0300231C,cpus[stage+1],1);put(0x0300231D,cpus[stage+1]==0 and 1 or 0,1)
  put(q+0x11,cpus[stage+1],1);put(0x03004502,stage==7 and 2 or 0,2);put(0x03004529,0,1)
  put(0x03004500,7000,2);put(0x0300450A,0,2);put(0x0300232A,0,2)
  if stage==7 then boss(7)end
 end
 state(0)
 local function fire(at,values)
  for k,v in pairs(values or {})do regs[k]=v end
  assert(hooks[at],string.format('missing hook %08X',at));inside_hook=true;hooks[at]();inside_hook=false
 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(key)
  if key=='output'then return 'W:/build/campaign-independent'
  elseif key=='frames'then return 120000
  elseif key=='start_frame'then return 0
  elseif key=='probe_sha256'then return case=='wrong-ROM'and'bad'or romhash
  elseif key=='score_authorization'then return case=='missing-authorization'and'bad'or'user-approved-development-score999'
  elseif key=='boss_authorization'then return 'user-approved-development-boss-once-per-stage'end
 end}
 env.emu={getsystemid=function()return'GBA'end,framecount=function()return frame end,
  getregisters=function()return regs end,frameadvance=function()assert(not inside_hook);frame=frame+1 end}
 env.event={on_bus_exec=function(fn,at,name)assert(not hooks[at]);hooks[at]=fn end,on_bus_write=function()end}
 local bases={EWRAM=0x02000000,IWRAM=0x03000000,ROM=0x08000000,VRAM=0x06000000}
 env.memory={read_u8=function(a,d)return get(bases[d]+a,1)end,read_u16_le=function(a,d)return get(bases[d]+a,2)end,
  read_u32_le=function(a,d)return get(bases[d]+a,4)end,
  write_u16_le=function(a,v,d)
   assert(d=='EWRAM');a=a+0x02000000
   local stage=get(0x0300231E,1)
   assert((stage<=10 and stage~=7 and a==p+0x66 and v==999)or(stage==7 and a==q+0x64 and v==1),'frozen assisted write extent')
   writes[#writes+1]={address=a,value=v,stage=stage};put(a,v,2)
  end,
  read_bytes_as_binary_string=function(a,n,d)assert(not inside_hook,'bulk dump occurred inside CPU hook');captures=captures+1;return 'MOCK_CAPTURE'end}
 env.joypad={set=function(keys)local copy={};for k,v in pairs(keys)do copy[k]=v end;input_calls[#input_calls+1]=copy end}
 env.client={screenshot=function()assert(not inside_hook,'screenshot inside hook')end,exit=function()exited=true end}
 env.savestate={save=function(path,quiet)assert(not inside_hook);saves[#saves+1]=path;return true end}
 env.io={open=function(path,mode)
  if mode=='rb'then local name=path:match('([^/]+)$');assert(sources[name]);return{read=function()return sources[name]end,close=function()end}end
  assert(mode=='w'or mode=='wb'or mode=='a')
  if path:match('/campaign%-complete%-done.txt$')then
   assert(closed['W:/build/campaign-independent/campaign-complete-trace.txt']and
    closed['W:/build/campaign-independent/shoot-entry-done.txt'],'all prior finish outputs closed before combined marker')
  end
  local f={closed=false}
  closed[path]=false
  if mode~='a'then files[path]=''else files[path]=files[path]or''end
  function f:write(s)assert(not self.closed);files[path]=files[path]..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true;closed[path]=true end
  return f
 end}
 local effective,api={}
 local function advance(context)context.joypad.set({});context.emu.frameadvance()end
 local function hud(progress)
  if progress==9 then
   local values={0x2215,0x2214,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201}
   for i,v in ipairs(values)do put(0x0600E80E+(i-1)*2,v,2)end
   if case=='bad-HUD'then put(0x0600E810,0x221E,2)end
  else for i=0,15 do put(0x0600E800+i*2,get(0x080B5FEA+i*2,2),2)end end
  if not(case=='missing-HUD'and progress==9)then fire(0x080B6054,{R5=0x0600E820})end
 end
 local function activate(context)
  -- Model the existing native fatal-hit and scene-health writes, not probe writes.
  fire(0x0836E5E4,{R4=p,R5=q,R8=0,R0=20});put(q+0x64,0,2)
  fire(0x0836E5E8,{R4=p,R5=q});fire(0x083736B0,{R4=p,R5=q})
  put(owner+0x54,100,2);active(owner,false)
  fire(0x085C8070,{R4=owner,R0=100,R5=p});fire(0x085C8B2C,{R4=owner,R0=100})
  put(0x0300231E,11,1);boss(11);put(0x0300450A,4,2)
  local count=#writes;fire(0x08373638);assert(#writes==count,'stage11 never writes')
  fire(0x085C8D50,{R4=owner});advance(context)
 end
 local function loop(context)
  assert(api.read(0x08FFFFFF,1)==0xA5 and api.read(0x09000000,1)==-1,'actual observer16MiB bound')
  for progress=0,10 do
   state(progress)
   if case=='typed-refusal'then put(q+0x18,p+1,4)end
   if case=='wrong-row'and progress==5 then put(0x0300232F,4,1)end
   if case=='wrong-CPU'and progress==4 then put(0x0300231C,12,1)end
   if not(case=='gap'and progress==2)then fire(0x0808B70C,{R4=0x03002310})end
   if case=='missing-active'and progress==8 then active(q,false)end
   if case=='bad-active-CPU'and progress==8 then put(q+0x11,7,1)end
   fire(0x08373638)
   if case=='retained-type-failure'then fire(0x0836E370,{R0=0xE5,R4=0x030048C8})end
   if case=='early-activation'and progress==5 then fire(0x085C8D50,{R4=owner})end
   if progress>=9 then hud(progress)end
   advance(context)
   if case=='typed-refusal'then assert(#writes==0,'actual pair refusal guards assisted write');return end
  end
  if case=='bounded'then return end
  activate(context)
 end
 env.load=function(code,name,mode,context)
  local compiled=assert(load(code,name,mode,context));effective[name]=code
  if name=='@frozen-collision-loop-16MiB'then return function()loop(context)end end
  if name=='@frozen-shoot-observer-16MiB'then return function()api=compiled();return api end end
  return compiled
 end
 local ok,err=pcall(assert(load(wrapper,'@new-campaign-wrapper','t',env)))
 if case=='wrong-ROM'or case=='missing-authorization'then
  assert(not ok and not files['W:/build/campaign-independent/campaign-complete-done.txt'],'setup guards cannot be bypassed')
 else
  assert(ok,tostring(err))
  local function replace(s,old,new)local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)end
  assert(effective['@frozen-shoot-entry-driver']==sources['bizhawk_probe_gba_shoot_entry.lua'],'full actual driver unchanged')
  local observer=effective['@frozen-shoot-observer-16MiB']
  observer=replace(observer,'local PROBE="'..romhash..'"','local PROBE="D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C"')
  observer=replace(observer,'a+n<=0x09000000','a+n<=0x08800000')
  assert(observer==sources['bizhawk_gba_shoot_entry_observer.lua'],'all frozen write/typed/fatal-hit/healthy guards retained exactly')
  local code=effective['@frozen-collision-loop-16MiB']
  code=replace(code,'dump("loaded-rom.bin","ROM",0x1000000)','dump("loaded-rom.bin","ROM",0x800000)')
  code=replace(code,'log("system=GBA assisted=true guest_writes=guarded-score999-and-stage7-bossHP1 input=frozen-approach-jump-no-up")','log("system=GBA guest_writes=none input=joypad-only")')
  assert(code==sources['bizhawk_probe_gba_collision.lua'],'exact capture/log-only loop inverse')
  local done=assert(files['W:/build/campaign-independent/campaign-complete-done.txt'])
  local old=assert(files['W:/build/campaign-independent/shoot-entry-done.txt'])
  if case=='complete'then
   assert(done=='campaign-eleven-stages-and-healthy-shoot-activation'and old=='healthy-native-shoot-activation',done..' / '..old)
   assert(#writes==11 and writes[11].stage==7 and writes[11].value==1,'ten stage-score writes and single boss-HP write')
   assert(#saves==2,'retained boss and healthy checkpoints')
   local trace=files['W:/build/campaign-independent/campaign-complete-trace.txt']
   for p=0,10 do assert(trace:find('event=producer core=',1,true));assert(trace:find('progress='..p..' ',1,true))end
  elseif case=='bounded'or case=='typed-refusal'then assert(done=='bounded-no-activation'and old==done)
  elseif case=='retained-type-failure'then assert(done=='failure:invalid-overlap-type'and old==done)
  else
   local failures={gap='campaign-producer-order',['wrong-row']='campaign-rng-row-changed',
    ['wrong-CPU']='campaign-source-row-mismatch',['bad-HUD']='campaign-HUD-tile-mismatch',
    ['missing-HUD']='campaign-proof-incomplete',['missing-active']='campaign-proof-incomplete',
    ['bad-active-CPU']='campaign-proof-incomplete',['early-activation']='campaign-proof-incomplete'}
   assert(done=='failure:'..assert(failures[case])and old==done,case..': '..done)
  end
  assert(exited and #input_calls>0 and captures>0,'actual driver cleanup and outer-boundary capture')
  for _,pressed in pairs(input_calls[#input_calls])do assert(pressed==false,'final controller release')end
 end
end
'''


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 assert not a.report.exists(),'fresh report required'
 wrapper=(ROOT/'tools/bizhawk_probe_campaign_complete.lua').read_bytes()
 assert sha(wrapper)==WRAPPER,'frozen active-owner label revision'
 assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister|\bjoypad\.set',wrapper),'no new guest/input writes'
 sources={name:(ROOT/'tools'/name).read_bytes() for name in PINS}
 assert all(sha(raw)==PINS[name] for name,raw in sources.items()),'frozen original sources'
 rom=(ROOT/'build/campaign-stage-progression-v80-20261117-r2/component.gba').read_bytes();assert sha(rom)==ROM and len(rom)==0x1000000
 blocks=[(0x8B70C,4),(0xB6054,4),(0xB5FEA,32),(0xD3FB10,5),(0xD3FB18,40),(0xD3FB40,11)]
 setup='local wrapper='+quote(wrapper)+'\nlocal romhash="'+ROM+'"\nlocal sources={'+','.join('['+quote(k.encode())+']='+quote(v) for k,v in sources.items())+'}\n'
 setup+='local romblocks={'+','.join('{at='+str(0x08000000+at)+',data=string.char('+','.join(map(str,rom[at:at+size]))+')}' for at,size in blocks)+'}\n'
 run=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=setup+CHECK));run('','','')
 report=dict(status='CAMPAIGN_COMPLETE_PROBE_INDEPENDENT_PASS',wrapper_sha256=sha(wrapper),checker_sha256=sha(Path(__file__).read_bytes()),
  frozen_dependencies=PINS,ROM_sha256=ROM,Lua_cases=14,actual_driver_executed=True,actual_observer_executed=True,
  full_driver_equal=True,full_observer_inverse=True,full_loop_inverse=True,bulk_capture_only_outside_hooks=True,
  all_finish_outputs_closed_before_combined_marker=True,exact_negative_outcomes=True,
  old_complete_semantic_suites_rerun=False,emulator_launched=False,
  limitations=['Collision frame loop is a scripted boundary; actual composed frozen driver and observer execute under Lua54.',
   'Memory, native hooks, graphics, save checkpoints and input delivery are modeled; no real campaign playthrough is asserted.',
   'Positive completion remains assisted score999 and one stage7 bossHP1 with actual-game fatal hit required in runtime.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()
