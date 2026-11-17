"""Focused Lua composition check; frozen Shoot write/controller suites are retained."""
import argparse
import json
import re
import struct
import types
from pathlib import Path
import check_id14_openbus_wrapper as existing

PINS={
 'bizhawk_probe_gba_shoot_entry.lua':'D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D',
 'bizhawk_gba_shoot_entry_observer.lua':'7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59',
 'bizhawk_probe_gba_collision.lua':'7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9'}
ROM='933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'

CHECK=r'''
local cases={'complete','gap','row-change','CPU','HUD','missing-HUD','missing-live','wrong-live-CPU','original-failure','bounded','wrong-ROM'}
for _,case in ipairs(cases)do
 local frame,result,live,old_activation=100,nil,true,false
 local hooks,files,queued={},{},{}
 local reg={R4=0x03002310,R5=0x0600E820};local ram={}
 local first={8,1,9,6,10}
 local rows={{5,0,3,2,4},{0,3,2,4,5},{3,2,4,5,0},{2,4,5,0,3},{4,5,0,3,2},{5,0,3,2,4},{0,3,2,4,5},{2,4,5,0,3}}
 local cpus={0,1,2,5,6,4,3,15,13,14,11}
 for i,v in ipairs(first)do ram[0x08D3FB10+i-1]=v end
 for n,t in ipairs(rows)do for i,v in ipairs(t)do ram[0x08D3FB18+(n-1)*5+i-1]=v end end
 for i,v in ipairs(cpus)do ram[0x08D3FB40+i-1]=v end
 ram[0x0808B70C]=0xE8BD4013;ram[0x080B6054]=0xE59F4048
 for i=0,15 do ram[0x080B5FEA+i*2]=0x2200+i end
 ram[0x03002310]=7;ram[0x0300231A]=0;ram[0x0300231B]=0;ram[0x0300231F]=2;ram[0x03004500]=7000;ram[0x0300232A]=0
 local api={}
 api.stopped=function()return result~=nil end
 api.live=function()return live end
 api.pair=function(boss)return 0x02011710,0x02011828 end
 api.fail=function(name)if not result then result='failure:'..name end end
 api.queue=function(name,detail,r)queued[#queued+1]=name end
 api.flush=function()if old_activation and not result then result='healthy-native-shoot-activation'end end
 api.finish=function()return result or 'bounded-no-activation'end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)
  if k=='output'then return 'W:/build/campaign-complete-test'
  elseif k=='probe_sha256'then return case=='wrong-ROM'and'wrong'or romhash end
 end}
 env.emu={framecount=function()return frame end,getregisters=function()return reg end}
 env.event={on_bus_exec=function(fn,at,name)assert(not hooks[at]);hooks[at]=fn end}
 local bases={EWRAM=0x02000000,IWRAM=0x03000000,VRAM=0x06000000,ROM=0x08000000}
 local function rd(a,d)return ram[bases[d]+a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd},{__index=function(_,k)error('unplanned memory API '..k)end})
 env.io={open=function(path,mode)
  if mode=='rb'then
   local name=path:match('([^/]+)$');assert(sources[name]);return{read=function()return sources[name]end,close=function()end}
  end
  assert(mode=='wb'or mode=='w');assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 local effective={}
 env.load=function(code,name,mode,context)
  assert(load(code,name,mode,context));effective[name]=code
  if name=='@frozen-shoot-observer-16MiB'then
   return function()
    context.event.on_bus_exec(function()old_activation=true end,0x085C8D50,'shoot-entry-activation-tail')
    return api
   end
  elseif name=='@frozen-collision-loop-16MiB'then return function()end
  elseif name=='@frozen-shoot-entry-driver'then
   assert(code==sources['bizhawk_probe_gba_shoot_entry.lua'],'driver byte exact')
   return function()
    local module=context.dofile('W:/tools/bizhawk_gba_shoot_entry_observer.lua')
    assert(context.loadfile('W:/tools/bizhawk_probe_gba_collision.lua','t',{}))
    for p=0,10 do
     frame=200+p
     ram[0x0300232E]=p;ram[0x0300232F]=(case=='row-change'and p==6)and 4 or 3
     local stage=p<5 and first[p+1]or p<10 and rows[4][p-4]or 7
     ram[0x0300231E]=stage;ram[0x0300231C]=cpus[stage+1];ram[0x0300231D]=cpus[stage+1]==0 and 1 or 0
     ram[0x02011839]=cpus[stage+1];ram[0x0201182C]=p==10 and 3 or 1
     if case=='CPU'and p==4 then ram[0x0300231C]=12 end
     if not(case=='gap'and p==2)then hooks[0x0808B70C]()end
     live=not(case=='missing-live'and p==8)
     if case=='wrong-live-CPU'and p==8 then ram[0x02011839]=7 end
     module.flush()
     if p==9 or p==10 then
      if p==9 then
       local t={0x2215,0x2214,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201}
       for i,v in ipairs(t)do ram[0x0600E80E+(i-1)*2]=v end
       if case=='HUD'then ram[0x0600E810]=0x221E end
      else for i=0,15 do ram[0x0600E800+i*2]=ram[0x080B5FEA+i*2]end end
      if not(case=='missing-HUD'and p==9)then hooks[0x080B6054]()end
      module.flush()
     end
    end
    if case=='original-failure'then api.fail('retained-observer')end
    if case~='bounded'then
     ram[0x0300231E]=11;hooks[0x085C8D50]();module.flush()
    end
    module.finish()
   end
  else error('unplanned composition '..name)end
 end
 local ok,err=pcall(assert(load(wrapper,'@campaign-wrapper','t',env)))
 if case=='wrong-ROM'then assert(not ok)else
  assert(ok,err)
  local function replace(s,old,new)local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)end
  local module=effective['@frozen-shoot-observer-16MiB']
  module=replace(module,'local PROBE="'..romhash..'"','local PROBE="D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C"')
  module=replace(module,'a+n<=0x09000000','a+n<=0x08800000')
  assert(module==sources['bizhawk_gba_shoot_entry_observer.lua'],'exact observer inverse including all authorized write guards')
  local loop=effective['@frozen-collision-loop-16MiB']
  loop=replace(loop,'dump("loaded-rom.bin","ROM",0x1000000)','dump("loaded-rom.bin","ROM",0x800000)')
  loop=replace(loop,'log("system=GBA assisted=true guest_writes=guarded-score999-and-stage7-bossHP1 input=frozen-approach-jump-no-up")','log("system=GBA guest_writes=none input=joypad-only")')
  assert(loop==sources['bizhawk_probe_gba_collision.lua'],'exact frame loop inverse')
  local done=files['W:/build/campaign-complete-test/campaign-complete-done.txt'];assert(done and done.closed)
  if case=='complete'then assert(done.data=='campaign-eleven-stages-and-healthy-shoot-activation'and #queued==24)
  elseif case=='bounded'then assert(done.data=='bounded-no-activation')
  elseif case=='original-failure'then assert(done.data=='failure:retained-observer')
  else assert(done.data:find('failure:',1,true)==1 and not done.data:find('healthy',1,true))end
  assert(files['W:/build/campaign-complete-test/campaign-complete-trace.txt'].closed)
 end
end
'''


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--report',type=Path,required=True);a=ap.parse_args()
    assert not a.report.exists(),'fresh report required'
    root=existing.ROOT
    wrapper=(root/'tools/bizhawk_probe_campaign_complete.lua').read_bytes()
    assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister|\bjoypad\.set',wrapper),'wrapper has no new guest/control/state writes'
    sources={name:(root/'tools'/name).read_bytes() for name in PINS}
    assert all(existing.sha(sources[name])==pin for name,pin in PINS.items())
    rom=(root/'build/campaign-stage-progression-v80-20261117-r2/component.gba').read_bytes()
    assert existing.sha(rom)==ROM and len(rom)==0x1000000
    assert struct.unpack_from('<I',rom,0x8B70C)[0]==0xE8BD4013 and struct.unpack_from('<I',rom,0xB6054)[0]==0xE59F4048
    setup='local wrapper='+existing.quote(wrapper)+'\nlocal romhash="'+ROM+'"\nlocal sources={'+','.join('['+existing.quote(n.encode())+']='+existing.quote(b) for n,b in sources.items())+'}\n'
    host=existing.host
    run=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=setup+CHECK))
    run('','','')
    report=dict(status='CAMPAIGN_COMPLETE_WRAPPER_AUTHOR_PASS',wrapper_sha256=existing.sha(wrapper),
        checker_sha256=existing.sha(Path(__file__).read_bytes()),frozen_dependencies=PINS,ROM_sha256=ROM,
        Lua_cases=11,exact_driver=True,exact_observer_inverse=True,exact_loop_inverse=True,
        limits=['New wrapper closures execute under Lua54 with modeled retained observer API; frozen write/controller suites are not repeated.',
                'No emulator, guest write, stage progression, real HUD, boss hit or Shoot activation observed by this check.'])
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],report['wrapper_sha256'])


if __name__=='__main__':main()
