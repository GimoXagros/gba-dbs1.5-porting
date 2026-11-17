"""Check composed ID13 air Lua and its acknowledgement and landing guards without a game core."""

import argparse
import json
import re
import struct
import types
from pathlib import Path

import check_id14_openbus_wrapper as existing

ENTRY = 'bizhawk_probe_id13_air_relaunch.lua'
OBSERVER = 'bizhawk_observe_id13_air_relaunch.lua'
BASE = 'bizhawk_probe_id13_fall_entry.lua'
PARENT = 'bizhawk_probe_result_languages.lua'
PINS = {
    ENTRY: '348E06A1C8A71B6E83FCE13201BC550D195AE65619DA615C1E4EB2F5FA9B28AA',
    OBSERVER: '70A7342A907F31CD29FA990C3548BD6358770A5AE99AAD0C4853403E50740388',
    BASE: '57F67564C15C496D47B93FDB1A91266638E830D9D448393E6554AC5670CA438E',
    PARENT: '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
}
MOVED = {0x08357054: 0x08D3F100, 0x0835732C: 0x08D3F150, 0x083578D4: 0x08D3F1A0}
OPS = {**dict.fromkeys((0x08D3F200, 0x08D3F280, 0x08D3F500, 0x08D3F700), 0xE52DE004),
       **dict.fromkeys((0x08D3F394, 0x08D3F564, 0x08D3F768), 0xE3500000),
       0x08012874: 0xE92D403F, 0x083525C4: 0xE12FFF18}

CHECK = r'''
local INIT,READY,BOOST,SPENT=0x08D3F200,0x08D3F280,0x08D3F500,0x08D3F700
local p,q,sp=0x02011710,0x02011828,0x03007E00
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)
end
local function compose(is_candidate)
 local frame=100
 local r={R0=0,R4=p,R5=p+0xAC,R8=0,R13=sp,R14=INIT+4}
 local ram={[0x03002310]=7,[0x0300489C]=p,[0x030048A0]=q,[p-8]=2,[q-8]=2,
  [p]=INIT,[p+0x11]=13,[q+0x10]=1,[p+0x14]=p,[p+0x18]=q,[q+0x18]=p}
 local env=setmetatable({},{__index=_G})
 local files,hooks,captured,air,changed={},{},nil,nil,nil
 local domain_base={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)
  local addr=domain_base[d]+a
  return ram[addr]or hook_codes[addr]or(is_candidate and branches[addr]or branches[addr] and 0xE1D482BC)or 0
 end
 env.memory=setmetatable({read_u8=function(a,d)return rd(a,d)&255 end,read_u16_le=function(a,d)return rd(a,d)&65535 end,
  read_u32_le=rd},{__index=function(_,k)error('unexpected memory API '..k)end})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/id13-air-fixture'end}
 env.io={open=function(path,mode)
  if mode=='rb'then assert(sources[path],path);return{read=function()return sources[path]end,close=function()end}end
  assert(mode=='wb' and not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return true end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 env.event={on_bus_exec=function(fn,at,label)assert(not hooks[at]);hooks[at]=fn end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.load=function(body,name,mode,context)
  local compiled=assert(load(body,name,mode,context))
  if name=='@ID13-air-observer'then return function()air=compiled();return air end end
  if name=='@ID13-air-route'then changed=body end
  if name=='@ID13-ordinary-fall-entry'then
   assert(not captured and context.id13_air==air);captured=body;return function()end
  end
  return compiled
 end
 local entry=is_candidate and entry_name or base_name
 assert(load(sources['W:/tools/'..entry],'@reviewed-id13','t',env))()
 assert(captured)
 if is_candidate then
  local count=0;for at in pairs(hooks)do assert(branches[at]or hook_codes[at]);count=count+1 end;assert(count==12)
  local old='assert(rd(at,4)==0xE1D482BC,"reviewed original common-fall input load")'
  local new=[=[local target=({[0x08357054]=0x08D3F100,[0x0835732C]=0x08D3F150,[0x083578D4]=0x08D3F1A0})[at]
 assert(rd(at,4)==(0xEA000000|(((target-at-8)//4)&0xFFFFFF)),"reviewed ID13 fall adapter")]=]
  assert(replace(changed,new,old)==sources['W:/tools/'..base_name],'exact nested opcode-guard replacement')
 end
 return captured,air,hooks,ram,r,function(value)frame=value end,files
end

local original=compose(false)
local body=compose(true)
local inverse=replace(body,' id13_input(keys,stage,mode)\n id13_air.input(keys,stage,mode)\n joypad.set(keys)',
 ' id13_input(keys,stage,mode)\n joypad.set(keys)')
inverse=replace(inverse,' local air_outcome=id13_air.outcome()\n if air_outcome then outcome=air_outcome;capture("id13-air-end") end',
 ' if id13_outcome() then outcome="id13-eligible-fall-observed";capture("id13-fall-after") end')
inverse=replace(inverse,'id13_finish()\nid13_air.finish()\nlocal f=','id13_finish()\nlocal f=')
assert(inverse==original,'complete inverse to unchanged baseline effective body')

local function cycle(drop_event)
 local _,air,hook,ram,r,at,files=compose(true)
 local function press()
  local keys={Right=true};air.input(keys,'battle',7);assert(not keys.Right);return keys.A==true
 end
 local keys={Right=true};air.input(keys,'battle',7);assert(keys.Right and not air.outcome())
 r.R4=q;hook[INIT]();r.R4=p;ram[p+0x11]=14;hook[INIT]();ram[p+0x11]=13
 keys={Right=true};air.input(keys,'battle',7);assert(keys.Right and not air.outcome())
 hook[INIT]();ram[p]=READY
 for count=1,3 do
  at(100+count*10);ram[p+0xA8]=0x100+count-1;assert(not press(),'latch denies request')
  ram[p+0xA8]=count-1;assert(press(),'only clear ready allows A')
  at(101+count*10);assert(press(),'old counter requires holding A')
  ram[p+0xA8]=0x100+count;ram[p]=BOOST;hook[BOOST]()
  ram[sp]=0x72;ram[sp+8]=q+0xAC;hook[0x08012874]() -- Wrong presentation is ignored.
  ram[sp+8]=p+0xAC;r.R14=0x08001000;hook[0x08012874]() -- Wrong caller is ignored.
  r.R14=READY+0x30
  if drop_event~=count then hook[0x08012874]()end
  assert(not press(),'acknowledgement releases A')
  if count<3 then ram[p]=READY end
 end
 ram[p]=READY;ram[p+0xA8]=3;assert(not press(),'there is no fourth request')
 ram[p]=SPENT;hook[SPENT]()
 at(140);r.R8=0x0835620C;hook[0x083525C4]();assert(not air.outcome())
 ram[p]=r.R8;r.R0=0;hook[0x08D3F768]();at(141);hook[0x083525C4]();assert(not air.outcome())
 ram[p+0xA8]=0;ram[p+0xAA]=0x15 -- The landing helper may repurpose both fields.
 r.R0=1;hook[0x08D3F768]();hook[0x083525C4]();assert(not air.outcome()) -- Cannot finish on landing core.
 at(142);r.R8=0x0835620D;hook[0x083525C4]();assert(not air.outcome())
 r.R8=0x0835620C;hook[0x083525C4]();assert(not air.outcome()) -- Cannot finish on dispatch core.
 at(143);ram[p+6]=1;assert(not air.outcome())
 ram[p+6]=0
 assert(air.outcome()==(drop_event and 'failure:missing-relaunch-witness' or 'id13-three-relaunches-and-landing'))
 air.finish()
 local f=files['W:/build/id13-air-fixture/id13-air-relaunch.txt'];assert(f.closed and f.data:sub(-14)=='complete=true\n')
 assert(select(2,f.data:gsub('event=press%-A core=',''))==3 and select(2,f.data:gsub('event=press%-ack core=',''))==3)
 assert(select(2,f.data:gsub('event=set%-event core=',''))==(drop_event and 2 or 3))
 assert(select(2,f.data:gsub('event=landing%-return core=',''))==1)
 assert(select(2,f.data:gsub('event=ordinary%-callback core=',''))==1)
end
cycle(nil);cycle(2)
local _,air,hooks,ram,r,at=compose(true)
hooks[INIT]();at(1300);assert(not air.outcome());at(1301);assert(air.outcome()=='failure:ID13-air-deadline')
_,air,hooks,ram,r,at=compose(true)
hooks[INIT]();ram[p]=READY;local keys={};air.input(keys,'battle',7);assert(keys.A);at(161)
keys={};air.input(keys,'battle',7);assert(not keys.A and air.outcome()=='failure:button-not-acknowledged')
_,air,hooks,ram,r,at=compose(true)
hooks[INIT]();ram[p+8]=0x4000;keys={};air.input(keys,'battle',7);assert(air.outcome()=='failure:unexpected-evolution')
_,air,hooks,ram,r,at=compose(true)
hooks[INIT]();ram[0x03002310]=6;assert(air.outcome()=='failure:ID13-left-battle')
_,air,hooks,ram,r,at=compose(true)
hooks[INIT]();ram[p+0xA8]=2;hooks[SPENT]();assert(air.outcome()=='failure:unexpected-spent-count')
'''


def literal(items):
    return '{' + ','.join(f'[{key}]={value}' for key, value in items.items()) + '}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    root = existing.ROOT
    scripts = {name: (root / 'tools' / name).read_bytes() for name in PINS}
    assert {name: existing.sha(data) for name, data in scripts.items()} == PINS
    assert all(not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister', scripts[name]) for name in (ENTRY, OBSERVER))
    rom = (root / 'build/id13-air-relaunch-v79-20261117/component.gba').read_bytes()
    assert existing.sha(rom) == 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
    branches = {at: 0xEA000000 | (((target - at - 8) // 4) & 0xFFFFFF) for at, target in MOVED.items()}
    assert all(struct.unpack_from('<I', rom, at - 0x08000000)[0] == op for at, op in (OPS | branches).items())
    sources = ','.join(f'[{existing.quote(("W:/tools/" + name).encode())}]={existing.quote(data)}' for name, data in scripts.items())
    setup = (f'local sources={{{sources}}}\nlocal entry_name="{ENTRY}"\nlocal base_name="{BASE}"\n'
             f'local hook_codes={literal(OPS)}\nlocal branches={literal(branches)}\n')
    host = existing.host
    run = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=setup + CHECK))
    run('', '', '')
    data = dict(status='ID13_AIR_PROBE_LUA_QA_PASS', dependency_sha256=PINS, candidate_sha256=existing.sha(rom),
                checker_sha256=existing.sha(Path(__file__).read_bytes()), exact_effective_inverse=True,
                branch_guards=len(branches), observer_opcode_guards=len(OPS), mocked_acknowledgements=3,
                no_fourth_request=True, permits_landing_field_reuse=True, failure_cases=6,
                actual_gameplay_verified=False, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(data['status'], existing.sha(payload))


if __name__ == '__main__':
    main()
