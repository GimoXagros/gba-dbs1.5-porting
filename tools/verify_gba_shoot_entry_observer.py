"""Independent real-Lua native entry composition checks; never launches an emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import types

import verify_wsc_shoot_short_hard as lua_host

ROOT = Path(__file__).resolve().parents[1]
ROM = 'D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'

CHECK = r'''
local function copy(t)local r={};for k,v in pairs(t)do r[k]=v end;return r end
local function create(options)
 local o=options or {};local m={frame=0,ram={},hooks={},files={},closedfiles={},writes={},inputs={},captures={},callback_files=0,advances=0,exits=0}
 local first,second,aux=0x02010018,0x02010130,0x02010248
 m.first,m.second,m.aux=first,second,aux
 function m.put(a,v,n)for i=0,(n or 2)-1 do m.ram[a+i]=math.floor(v/256^i)%256 end end
 function m.get(a,n)local v=0;for i=0,(n or 2)-1 do v=v+(m.ram[a+i]or 0)*256^i end;return v end
 local function task(p,kind)
  m.put(p-0x18+0x10,2);m.put(p+4,kind);m.put(p+0x14,p,4)
 end
 task(first,0);task(second,3);task(aux,6)
 m.put(second+0x10,1,1);m.put(second+0x11,15,1)
 m.put(first+0x18,second,4);m.put(second+0x18,first,4)
 m.put(second+0x28,aux,4);m.put(aux+0x28,second,4);m.put(aux+0x18,first,4)
 m.put(first+0x64,8);m.put(second+0x64,44);m.put(first+0x66,4)
 m.put(0x0300489C,first,4);m.put(0x030048A0,second,4);m.put(0x03004D3C,aux,4)
 m.put(0x03002310,7);m.put(0x0300231E,7,1);m.put(0x0300231F,2,1)
 m.put(0x03004502,2);m.put(0x03004529,0,1);m.put(0x0300450A,4)
 for i,cb in ipairs({0x08374FF4,0x083735BC})do
  local h=0x02010000+(i+2)*0x118;m.put(h,cb,4);m.put(h+0x10,2)
  m.put(0x0300450C+i*4,h,4)
 end
 m.regs={};for i=0,15 do m.regs['R'..i]=0 end
 local configs={output='W:/build/native-entry-independent',frames=7000,start_frame=2970,
  probe_sha256=ROM,combat_profile='approach-jump',
  score_authorization='user-approved-development-score999',
  boss_authorization='user-approved-development-boss-once-per-stage'}
 for k,v in pairs(o.config or {})do configs[k]=v end
 m.config=configs
 local domains={IWRAM={0x03000000,0x8000},EWRAM={0x02000000,0x40000},
  ROM={0x08000000,0x800000},VRAM={0x06000000,0x18000},PALRAM={0x05000000,0x400},OAM={0x07000000,0x400},['System Bus']={0,0x100000000}}
 local function at(a,n,d)
  local spec=assert(domains[d],'unexpected memory domain '..tostring(d))
  assert(a%1==0 and a>=0 and a+n<=spec[2],'memory domain bounds');return spec[1]+a
 end
 local env=setmetatable({},{__index=_G});env._G=env;m.env=env
 env.userdata={get=function(k)return configs[k]end}
 env.memory={getmemorydomainsize=function(d)return assert(domains[d])[2]end,
  read_u8=function(a,d)return m.get(at(a,1,d),1)end,
  read_u16_le=function(a,d)return m.get(at(a,2,d),2)end,
  read_u32_le=function(a,d)return m.get(at(a,4,d),4)end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(not m.callback,'bulk RAM/ROM capture inside CPU callback');at(a,n,d)
   m.captures[#m.captures+1]={kind='memory',frame=m.frame,domain=d,size=n}
   return string.rep('\0',n)
  end,
  write_u16_le=function(a,v,d)
   local absolute=at(a,2,d);m.writes[#m.writes+1]={a=absolute,value=v,frame=m.frame}
   assert((absolute==first+0x66 and v==999)or(absolute==second+0x64 and v==1),'unauthorized write')
   if o.write_error then error('synthetic write failure')end;m.put(absolute,v)
  end}
 env.mainmemory=setmetatable({},{__index=function(_,k)error('unexpected mainmemory API '..k)end})
 env.emu={getsystemid=function()return 'GBA'end,framecount=function()return m.frame end,
  getregisters=function()return copy(m.regs)end,
  frameadvance=function()
   assert(not m.callback);m.advances=m.advances+1;m.frame=m.frame+1
   if o.step then o.step(m)end
  end}
 env.joypad={set=function(keys)m.inputs[#m.inputs+1]={frame=m.frame,keys=copy(keys)}end}
 local function hook(kind,fn,a,label,scope)
  assert(not m.hooks[label],'duplicate callback label');m.hooks[label]={kind=kind,fn=fn,a=a,scope=scope}
 end
 env.event={on_bus_exec=function(...)hook('exec',...)end,on_bus_write=function(...)hook('write',...)end,
  availableScopes=function()return {'System Bus'}end}
 function m.fire(a,patch)
  for k,v in pairs(patch or {})do m.regs[k]=v end;m.regs.R15=a
  m.callback=true
  local ok,err=pcall(function()for _,h in pairs(m.hooks)do if h.a==a then h.fn(a,0,0)end end end)
  m.callback=false;assert(ok,err)
 end
 local sources={['W:/tools/bizhawk_probe_gba_collision.lua']=collision_source,
  ['W:/tools/bizhawk_probe_gba_collision_producer.lua']=producer_source,
  ['W:/tools/bizhawk_gba_shoot_entry_observer.lua']=hard_source}
 env.io={open=function(p,mode)
  if m.callback then
   assert(p=='W:/build/native-entry-independent/shoot-entry-first-failure.txt','only firstfailure scalar IO inside CPU callback')
   m.callback_files=m.callback_files+1
  end
  if sources[p]then assert(mode=='rb');return{read=function()return sources[p]end,close=function()end}end
  assert(p:find('W:/build/native-entry-independent/',1,true)==1,'unexpected file '..p)
  if mode=='rb'then
   if o.existing then return{read=function()return ''end,close=function()end}end
   return nil
  end
  assert(mode=='a'or mode=='wb'or mode=='w','file mode')
  if mode~='a'then assert(not m.files[p],'snapshot overwrite');m.files[p]=''end
  return{write=function(_,s)m.files[p]=(m.files[p]or'')..tostring(s)end,close=function()m.closedfiles[p]=(m.closedfiles[p]or 0)+1 end}
 end}
 env.client={speedmode=function()end,exit=function()m.exits=m.exits+1 end,
  screenshot=function(p)assert(not m.callback,'screenshot in CPU callback');m.captures[#m.captures+1]={kind='screen',frame=m.frame};m.files[p]='PNG'end}
 env.savestate={save=function(p)assert(not m.callback,'savestate in CPU callback');m.captures[#m.captures+1]={kind='state',frame=m.frame};m.files[p]='STATE';return true end}
 env.dofile=function(p)return assert(load(assert(sources[p],'unknown dofile '..p),'@actual-'..p,'t',env))()end
 env.loadfile=function(p,mode,scope)return load(assert(sources[p],'unknown loadfile '..p),'@actual-'..p,mode,scope)end
 function m.load_module()m.module=assert(load(hard_source,'@actual-observer','t',env))();return m.module end
 function m.run()return assert(load(wrapper_source,'@actual-driver','t',env))()end
 function m.text()local all='';for p,s in pairs(m.files)do if p:match('%.txt$')then all=all..s..'\n'end end;return all end
 return m
end
'''

GUARDS = r'''
local function reject(fn,label)assert(not pcall(fn),'negative accepted: '..label)end
for _,key in ipairs({'probe_sha256','score_authorization','boss_authorization'})do
 local m=create({config={[key]='denied'}});reject(m.load_module,key);assert(#m.writes==0)
end
local function check(patch,expected,label)
 local m=create();m.load_module();patch(m);m.fire(0x08373638)
 assert(#m.writes==(expected and 1 or 0),label or 'guard')
 if expected then assert(m.writes[1].a==m.second+0x64 and m.writes[1].value==1)end
end
check(function()end,true,'validstage7')
for _,stage in ipairs({0,1,6,8,10,11,12,255})do check(function(m)m.put(0x0300231E,stage,1)end,false,'nonstage7 '..stage)end
for _,mode in ipairs({0,3,6,8,9,14,23})do check(function(m)m.put(0x03002310,mode)end,false,'mode '..mode)end
for _,d in ipairs({0,1,3,255})do check(function(m)m.put(0x0300231F,d,1)end,false,'difficulty '..d)end
for _,hp in ipairs({0,0x8000,0xFFFF})do
 check(function(m)m.put(m.first+0x64,hp)end,false,'P1HP '..hp)
 check(function(m)m.put(m.second+0x64,hp)end,false,'bossHP '..hp)
end
check(function(m)m.put(m.second+0x64,1)end,false,'alreadyHP1')
for _,v in ipairs({1,2,4,7})do check(function(m)m.put(0x03004529,v,1)end,false,'paused '..v)end
for _,kind in ipairs({0,1,3,4,255})do if kind~=2 then check(function(m)m.put(0x03004502,kind)end,false,'gamekind')end end
for _,slot in ipairs({0x0300489C,0x030048A0,0x03004D3C,0x03004510,0x03004514})do
 for _,v in ipairs({0,0x02010019,0x020138F8,0x03000018})do check(function(m)m.put(slot,v,4)end,false,'handle '..slot)end
end
for _,which in ipairs({'first','second','aux'})do
 check(function(m)m.put(m[which]-8,0)end,false,'inactive '..which)
end
for _,spec in ipairs({{'first',4,1,2},{'first',0x10,1,1},{'first',0x11,1,1},
 {'first',0x14,0,4},{'first',0x18,0,4},{'second',4,1,2},{'second',0x10,0,1},
 {'second',0x11,0,1},{'second',0x14,0,4},{'second',0x18,0,4},{'second',0x28,0,4},
 {'aux',4,3,2},{'aux',0x18,0,4},{'aux',0x28,0,4}})do
 check(function(m)m.put(m[spec[1]]+spec[2],spec[3],spec[4])end,false,'typedowner')
end
for _,g in ipairs({0x03004510,0x03004514})do
 check(function(m)m.put(m.get(g,4),0x083735BD,4)end,false,'callback')
 check(function(m)m.put(m.get(g,4)+0x10,0)end,false,'serviceinactive')
end
local m=create();m.load_module();m.fire(0x08373638);m.put(m.second+0x64,44);m.fire(0x08373638)
m.put(0x03002310,9);m.fire(0x08373638);m.put(0x03002310,7);m.fire(0x08373638)
m.put(0x0300231E,11,1);m.fire(0x08373638);m.put(0x0300231E,7,1);m.fire(0x08373638)
assert(#m.writes==1,'one lifetime stage7 write, no retry/Continue/stage11/reset rearm')
local f=create({write_error=true});f.load_module();reject(function()f.fire(0x08373638)end,'write failure')
f.fire(0x08373638);assert(#f.writes==1,'consumed before failingwrite')
'''

PRODUCERS = r'''
local function fire(m,t,dst,pc)
 m.fire(pc or 0x08353C70,{R0=t,R1=dst or 0x030049B8,R4=0x02011018})
end
local m=create();local obs=m.load_module()
for _,t in ipairs({0,0x19,0x1A,0x1B})do fire(m,t);assert(not obs.stopped(),'legal Shoot collision type '..t)end
fire(m,0xE5);assert(obs.stopped() and #m.captures==0,'firstproducer queued without bulk callback capture')
local immediate=m.files['W:/build/native-entry-independent/shoot-entry-first-failure.txt']
assert(immediate and immediate:find('type=E5',1,true)and immediate:find('R0=000000E5',1,true),'firstE5 scalar evidence immediately durable beforeouterframe')
assert(m.closedfiles['W:/build/native-entry-independent/shoot-entry-first-failure.txt']==1,'firstfailure scalar file closed beforeouterframe')
assert(m.callback_files==1,'one immediate callback failure export')
fire(m,0xFF);m.fire(0x0836E370,{R0=0xE5,R4=0x030049B8});m.regs.R0=0x1234
assert(m.files['W:/build/native-entry-independent/shoot-entry-first-failure.txt']==immediate and m.callback_files==1,'laterfailures neveroverwrite firstE5 evidence')
m.frame=1;obs.flush();local text=m.text()
assert(text:find('first-invalid-producer',1,true)and text:find('type=E5',1,true),'E5 firstwriter journal')
assert(text:find('reg R0=000000E5',1,true)and not text:find('reg R0=00001234',1,true),'frozen firstproducer registers')
assert(#m.captures>0,'deferred captures occurred');obs.finish()
assert(m.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='failure:first-invalid-producer')
for _,pc in ipairs({0x08353C70,0x08353D24,0x083776E4})do
 local n=create();local o=n.load_module();fire(n,0x1B,pc==0x08353C70 and 0x030049B8 or 0x030048C8,pc)
 assert(not o.stopped(),'legal1B at each writer')
end
local n=create();local o=n.load_module();fire(n,0x1A,0x030049B9);assert(o.stopped(),'unaligned list geometry')
local s=create();local so=s.load_module();s.put(0x03004D20,0x1B);s.fire(0x0836EB58);assert(not so.stopped(),'scratch1B legal')
s.put(0x03004D20,0xE5);s.fire(0x0836EB58);assert(so.stopped(),'scratchE5 invalid')
local d=create();local od=d.load_module();d.put(0x0836EBA8,0x0836D000,4)
d.fire(0x0836EBA4,{R1=0,R8=0x0836EBA8,R9=0x0836D000});assert(not od.stopped(),'native valid dispatch')
d.fire(0x0836EBA4,{R1=1,R8=0x0836EBA8,R9=0x0836D000});assert(od.stopped(),'bad dispatch retained')
'''

ACTIVATION = r'''
local function prepare(m,change)
 local obs=m.load_module();m.fire(0x08373638)
 if not m.nohit then m.fire(0x0836E5E4,{R4=m.first,R5=m.second,R8=0,R0=1})end
 m.put(m.second+0x64,0);if not m.nohit then m.fire(0x0836E5E8)end;m.fire(0x083736B0)
 local owner=0x020106A8;m.put(owner-8,2);m.put(owner+0x54,8)
 m.fire(0x085C8070,{R4=owner,R0=8,R5=m.first})
 m.fire(0x085C8B2C,{R4=owner,R0=8});m.put(m.first+0x64,8)
 m.put(0x0300231E,11,1);m.fire(0x085C8D50,{R4=owner});m.put(owner-8,0)
 if change then change(m,owner)end;m.frame=1;obs.flush();return obs
end
local m=create();local obs=prepare(m)
assert(obs.stopped()and m.files['W:/build/native-entry-independent/healthy-activation.State']=='STATE','healthy retired scene state')
obs.finish();assert(m.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='healthy-native-shoot-activation')
for _,change in ipairs({function(m)m.put(m.first+0x64,0)end,function(m)m.put(0x0300450A,0)end,
 function(m)m.put(0x0300231E,7,1)end,function(m,owner)m.put(owner-8,2)end,
 function(m,owner)m.put(owner+0x54,0)end,function(m)m.put(0x03004510,0,4)end})do
 local n=create();local o=prepare(n,change);assert(o.stopped()and not n.files['W:/build/native-entry-independent/healthy-activation.State'],'invalidactivation no state')
 o.finish();assert(n.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='failure:activation-contract')
end
local n=create();n.nohit=true;local o=prepare(n);o.finish()
assert(n.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='failure:activation-contract','root5 without direct matched hit refused')
'''

SCORES = r'''
for stage=0,255 do
 local m=create();m.load_module();m.put(0x0300231E,stage,1);m.put(0x03004502,0)
 m.put(m.second+4,1);m.put(m.second+0x11,1,1);m.put(m.second+0x64,8)
 m.fire(0x08373638)
 local eligible=stage<=10 and stage~=7
 assert(#m.writes==(eligible and 1 or 0),'ordinary positive stage scope '..stage)
 if eligible then
  assert(m.writes[1].a==m.first+0x66 and m.writes[1].value==999,'native scoreWORD only')
  m.fire(0x08373638);assert(#m.writes==1,'no repeat999 write')
  m.put(m.first+0x66,250);m.fire(0x08373638);assert(#m.writes==2,'postpickup restore999')
  assert(m.get(m.first+0x64)==8 and m.get(m.second+0x64)==8,'both HP preserved')
 end
end
for _,patch in ipairs({function(m)m.put(m.first+0x64,0)end,function(m)m.put(m.first+0x64,0x8000)end,
 function(m)m.put(m.second+0x64,0)end,function(m)m.put(m.first+0x18,0,4)end,
 function(m)m.put(m.second+4,3)end,function(m)m.put(0x03004502,2)end})do
 local m=create();m.load_module();m.put(0x0300231E,1,1);m.put(0x03004502,0)
 m.put(m.second+4,1);patch(m);m.fire(0x08373638);assert(#m.writes==0,'ordinary typed/live boundary')
end
'''

DRIVER = r'''
local function released(m)
 assert(m.exits==1,'driver final exit once')
 for _,v in pairs(m.inputs[#m.inputs].keys)do assert(not v,'final controller released')end
end
local n=create({config={frames=3,start_frame=0}});n.run();released(n)
assert(n.advances==3 and n.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='bounded-no-activation','bounded parent loop')
local bad=create({config={frames=20,start_frame=0},step=function(m)
 if m.frame==2 then m.fire(0x08353C70,{R0=0xE5,R1=0x030049B8,R4=0x02011018})end
end});bad.run();released(bad)
assert(bad.advances==2,'stop at first producer frame rather than old frozen budget')
assert(bad.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='failure:first-invalid-producer')
local healthy=create({config={frames=20,start_frame=0},step=function(m)
 if m.frame==1 then m.fire(0x08373638)
 elseif m.frame==2 then
  m.fire(0x0836E5E4,{R4=m.first,R5=m.second,R8=0,R0=1})
  m.put(m.second+0x64,0);m.fire(0x0836E5E8);m.fire(0x083736B0)
 elseif m.frame==3 then
  local owner=0x020106A8;m.put(owner-8,2);m.put(owner+0x54,8)
  m.fire(0x085C8070,{R4=owner,R0=8,R5=m.first})
  m.fire(0x085C8B2C,{R4=owner,R0=8});m.put(0x0300231E,11,1)
  m.put(m.second+0x64,44);m.fire(0x085C8D50,{R4=owner});m.put(owner-8,0)
 end
end});healthy.run();released(healthy)
assert(healthy.advances==3,'first healthy activation stops parent at outer frame')
assert(healthy.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='healthy-native-shoot-activation')
local title=0x020108C0
local function route(return_intro)
local last,previous={},{}
local routes={options=false,diff=false,selection=false,battle=false}
local m=create({config={frames=1800,start_frame=0},step=function(m)
 local keys=m.inputs[#m.inputs].keys
 local function edge(k)return keys[k]and not previous[k]end
 local mode=m.get(0x03002310)
 if mode==3 then
  if m.get(title,4)==0x08090C7C and edge('Start')then m.put(title,0x08090FA0,4)
  elseif m.get(title,4)==0x08090FA0 then
   local row=m.get(0x03002C5E,1)
   if edge('Down')then m.put(0x03002C5E,(row+1)%3,1)end
   if edge('Up')then m.put(0x03002C5E,(row+2)%3,1)end
   if edge('A')then
    if row==2 then routes.options=true;m.put(0x03002310,14)
    elseif row==0 then routes.selection=true;m.put(0x03002310,4)end
   end
  end
 elseif mode==14 then
  local row=m.get(0x0300473E)
  if edge('Down')then m.put(0x0300473E,(row+1)%3)end
  if row==1 and edge('Right')then m.put(0x0300231F,math.min(2,m.get(0x0300231F,1)+1),1)end
  if edge('B')then
   routes.diff=m.get(0x0300231F,1)==2;m.put(0x03002310,3)
   m.put(title,return_intro and 0x08090C7C or 0x08090FA0,4)
  end
 elseif mode>=4 and mode<=6 then
  assert(not keys.Down and not keys.Right and not keys.Left and not keys.Up,'ordinary defaultfighter0 no selection directions')
  if edge('A')then m.put(0x03002310,mode+1)end
 elseif mode==7 then
  assert(not keys.Up,'root-approved base0 profile')
  if not routes.battle then routes.battle=true;last.battle=m.frame end
  m.fire(0x08373638)
  if m.frame>=last.battle+3 then m.put(0x03002310,9)end
 end
 previous=copy(keys)
end})
m.put(0x03002310,3);m.put(0x0300231E,1,1);m.put(0x03004502,0);m.put(m.second+4,1)
m.put(0x0300231F,0,1);m.put(title,0x08090C7C,4);m.put(title+4,0x1000,4);m.put(title+0x10,2)
m.put(0x0300133C,title,4);m.run();released(m)
assert(routes.options and routes.diff and routes.selection and routes.battle,'ordinary UI reached hard2/default0/battle')
assert(#m.writes==1 and m.writes[1].a==m.first+0x66,'actual composed ordinary scoreguard reachable')
assert(m.files['W:/build/native-entry-independent/shoot-entry-done.txt']=='failure:continue-reached','Continue stops without retry')
assert(m.advances<1800,'Continue did not spin tobudget')
end
route(false);route(true)
for _,frames in ipairs({0,-1,1.5,120001})do
 local x=create({config={frames=frames}});assert(not pcall(x.run),'invalid framebudget');assert(x.advances==0)
end
local p=create();local po=p.load_module();p.put(0x0300232A,0x400);p.fire(0x0833FD04);assert(po.stopped(),'ineligible realhard2 predicate stops')
'''


def execute(driver, observer, collision, producer, check):
    source = ("local ROM='" + ROM + "'\nlocal collision_source=[==[" + collision +
              ']==]\nlocal producer_source=[==[' + producer + ']==]\n' + CHECK + check)
    fn = types.FunctionType(lua_host.lua_check.__code__, dict(lua_host.__dict__, CHECK=source),
                            argdefs=lua_host.lua_check.__defaults__)
    fn(driver, observer, '')


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'fresh output required'
    names = ['bizhawk_probe_gba_shoot_entry.lua', 'bizhawk_gba_shoot_entry_observer.lua',
             'bizhawk_probe_gba_collision.lua', 'bizhawk_probe_gba_collision_producer.lua']
    blobs = [(ROOT / 'tools' / name).read_bytes() for name in names]
    texts = [b.decode('utf-8') for b in blobs]
    groups = {'guard_matrix': GUARDS, 'first_producer_and_dispatch': PRODUCERS,
              'healthy_activation': ACTIVATION, 'ordinary_score_256_stages': SCORES,
              'real_driver_composition': DRIVER}
    for check in groups.values():
        execute(*texts, check)
    mutations = [
        (1, 'write_word(q+0x64,1,"boss"', 'write_word(q+0x66,1,"boss"', GUARDS, 'boss address'),
        (1, 'write_word(p+0x66,999,"score"', 'write_word(p+0x66,998,"score"', SCORES, 'score value'),
        (1, 'and not consumed[stage]', 'and true', GUARDS, 'one-shot guard removed'),
        (1, 'consumed[stage]=true --', 'consumed[stage]=false --', GUARDS, 'one-shot consume removed'),
        (1, 'stage<=10 and stage~=7', 'stage<=255 and stage~=7', SCORES, 'ordinary stage bound widened'),
        (1, 'word(q+4)%16~=3', 'word(q+4)%16~=1', GUARDS, 'boss kind mismatch'),
        (1, 'read(a+0x28,4)~=q', 'false', GUARDS, 'aux ownership removed'),
        (1, 'r.R0>0x1B', 'r.R0>0x19', PRODUCERS, 'legal Shoot type rejected'),
        (1, 'r.R0>0x1B', 'r.R0>0xFF', PRODUCERS, 'E5 producer accepted'),
        (1, 'scene and not active(scene.owner)', 'scene and true', ACTIVATION, 'scene retirement removed'),
        (1, 'word(p+0x64)==scene.hp', 'true', ACTIVATION, 'current health equality removed'),
        (0, 'emu.frameadvance();observer.flush()', 'emu.frameadvance()', DRIVER, 'outer flush removed'),
        (0, 'pulse("A",frame)\n elseif mode==7', 'pulse("Down",frame)\n elseif mode==7', DRIVER, 'selection directions'),
        (0, 'if cb==0x08090C7C then pulse("Start",frame)', 'if cb==0x08090C7C then pulse("A",frame)', DRIVER, 'post Options title Start omitted'),
        (1, 'if outcome then return end', 'if false then return end', PRODUCERS, 'first failure overwritten'),
        (1, 'f:close()\nend\nlocal function hook', '-- omitted close\nend\nlocal function hook', PRODUCERS, 'immediate failure file not closed'),
    ]
    rejected = []
    for index, old, new, check, label in mutations:
        assert old in texts[index], 'mutation anchor ' + label
        changed = list(texts)
        changed[index] = changed[index].replace(old, new)
        try:
            execute(*changed, check)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('semantic mutant accepted: ' + label)
    host = ROOT / 'build/run_gba_shoot_entry_20261109.py'
    host_bytes = host.read_bytes()
    assert sha(host_bytes) == '019A9E583F8A5B04E819746F1802FC808B7501378417D6436801FEBA2084C1A0', 'frozen reviewed launcher'
    compile(host_bytes, str(host), 'exec')
    config = json.loads((ROOT / 'build/bizhawk-gba-diagnostic-20261026/config.json').read_text('utf-8-sig'))
    def check_autoload(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key != 'AutoLoad' or child is False
                check_autoload(child)
        elif isinstance(value, list):
            for child in value:
                check_autoload(child)
    check_autoload(config)
    ordinary = ROOT / 'build/bizhawk-result-v73-20261109-a/battle-enter-iwram.bin'
    observed = ordinary.read_bytes()
    assert observed[0x4502:0x4504] == b'\0\0' and observed[0x2310:0x2312] == b'\x07\0'
    report = dict(status='NATIVE_ENTRY_LUA_COMPOSITION_PASS',
                  lua_host='installed BizHawk2.11.1 lua54.dll via reused ctypes runner',
                  actual_lua_groups=list(groups), semantic_mutations_rejected=rejected,
                  pins={'tools/' + name: sha(blob) for name, blob in zip(names, blobs)},
                  launcher_sha256=sha(host_bytes), verifier_sha256=sha(Path(__file__).read_bytes()),
                  ordinary_preinitialization_capture_sha256=sha(observed),
                  ordinary_game_kind=0, boss_game_kind=2, ordinary_stage_partition=256,
                  authorized_writes=['ordinary FIRST+66 WORD999', 'active stage7 SECOND+64 WORD1 once'],
                  stage11_hp_writes_disabled=True, default_fighter=0, ordinary_ui_difficulty=2,
                  base0_profile_omits_Up_by_root_approval=True,
                  CPU_callbacks_bulk_memory_savestate_screenshot_forbidden=True,
                  captures='before-instruction copied registers; later outer-frame memory',
                  emulator_launched=False, guest_memory_written=False,
                  limits=['Lua API fixtures are not actual GBA runtime',
                          'No first native Shoot arrival or E5 cause established',
                          'A CPU stall can prevent bulk outer-frame capture; immediate scalar first-failure evidence remains'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
